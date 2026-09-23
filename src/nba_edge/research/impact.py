"""How much does a team's efficiency actually change when a player is unavailable?

The simulator has never had an empirical answer. ``impact_ppp`` exists in PlayerParams, defaults to
0.0, and nothing populates it -- so ruling out a 29.7-ppg star moved the team's expected points by
0.68 (measured), and every family stayed at RESEARCH authority partly because of it.

What the data allows, and what it does not
------------------------------------------
Real RAPM needs stint-level lineup data: who was on the floor for each possession. This project has
game-level box scores, so that is not available and claiming RAPM would be wrong. What IS available
is each player's minutes in each game, which supports a **minutes-share ridge APM**:

    off_ppp(team, game) ~ intercept + opponent_def + home + b2b + sum_i share[i,g] * beta_off[i]

where ``share[i,g]`` is player i's fraction of his team's minutes in that game. Because the shares
sum to 1 by construction, beta is identified only up to a constant, and ridge resolves that by
shrinking toward zero -- which gives exactly the interpretation the simulator needs: **beta_i is
player i's efficiency contribution relative to the minutes-weighted average player**, i.e. what the
team loses per possession when his minutes go to someone ordinary instead.

That pairs with the rotation model rather than duplicating it. The rotation model decides WHO
absorbs a missing player's minutes; this decides what that substitution costs in efficiency. The
opportunity layer already moves shot volume around, so this must not also move volume or the same
effect would be counted twice -- it moves efficiency only.

Regularisation is not optional here. With ~600 players over a few thousand team-games, and stars
whose minutes shares barely vary, an unregularised fit hands enormous unstable coefficients to
low-minute players who happened to appear in a few blowouts. The ridge penalty is deliberately
strong and the resulting spread is reported, so the shrinkage can be seen rather than trusted.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# Priors on how large a single player's per-possession effect can plausibly be. A superstar is worth
# a few points per 100 possessions relative to an average player; anything far beyond that is the
# fit chasing noise, and it is clipped with a count rather than silently.
MAX_ABS_IMPACT_PPP = 0.06  # ~6 points per 100 possessions


@dataclass
class ImpactModel:
    off: dict[int, float] = field(default_factory=dict)  # per-possession offensive impact
    deff: dict[int, float] = field(default_factory=dict)  # per-possession defensive impact (positive = worse for opponent)
    n_games: dict[int, int] = field(default_factory=dict)
    alpha: float = 0.0
    n_team_games: int = 0
    n_players: int = 0
    clipped: int = 0

    def total(self, nba_id: int) -> float:
        """Offense plus defense: what the simulator uses as a single availability effect."""
        return self.off.get(nba_id, 0.0) + self.deff.get(nba_id, 0.0)


def build_design(
    team_games: pd.DataFrame, player_games: pd.DataFrame, min_player_games: int = 15
) -> tuple[np.ndarray, np.ndarray, list[int], pd.DataFrame]:
    """Proper APM structure: each team-game row carries BOTH teams.

    For a row where team A scored against team B, the response is A's points per possession, A's
    players enter as offensive columns and B's players enter as defensive columns. Opponent quality
    is therefore controlled by construction rather than by a summary statistic -- which matters,
    because an earlier version of this model omitted opponent controls entirely and consequently
    handed high coefficients to role players on strong teams: it was measuring "plays for a good
    team", not "is good".

    Columns are ``[off_0..off_m, def_0..def_m, home]``. Players below ``min_player_games`` pool into
    a single replacement column per side; estimating a personal effect from six appearances is how a
    fit produces a +12-points-per-100 twelfth man.
    """
    pg = player_games.copy()
    pg["minutes"] = pd.to_numeric(pg["minutes"], errors="coerce").fillna(0.0)
    pg = pg[pg["minutes"] > 0]

    counts = pg.groupby("nba_id").size()
    keep = sorted(int(p) for p in counts[counts >= min_player_games].index)
    idx = {p: i for i, p in enumerate(keep)}
    n_p = len(keep) + 1  # +1 replacement bucket
    n_cols = 2 * n_p + 1  # offence block, defence block, home

    tgm = team_games.dropna(subset=["possessions"]).copy()
    tgm = tgm[tgm["possessions"] > 50].reset_index(drop=True)
    row_of = {(g, int(t)): i for i, (g, t) in enumerate(zip(tgm["game_id"], tgm["team_id"], strict=True))}

    tot = pg.groupby(["game_id", "team_id"])["minutes"].transform("sum")
    pg = pg.assign(_share=pg["minutes"] / tot.replace(0, np.nan))

    # Precompute each row's opponent row once. Searching row_of per player-game would be O(rows)
    # inside a loop over ~100k player-games.
    opp_row_of = {
        (g, int(t)): row_of.get((g, int(o)))
        for g, t, o in zip(tgm["game_id"], tgm["team_id"], tgm["opp_team_id"], strict=True)
    }

    X = np.zeros((len(tgm), n_cols), dtype=np.float32)
    for gid, tid, pid, share in zip(pg["game_id"], pg["team_id"], pg["nba_id"], pg["_share"], strict=True):
        if not np.isfinite(share):
            continue
        col = idx.get(int(pid), n_p - 1)
        r_off = row_of.get((gid, int(tid)))
        if r_off is not None:
            X[r_off, col] += float(share)  # his offence, in the row where his team scores
        r_def = opp_row_of.get((gid, int(tid)))
        if r_def is not None:
            X[r_def, n_p + col] += float(share)  # his defence, in the row where the opponent scores

    X[:, -1] = tgm["home"].astype(float).to_numpy()
    y = (tgm["pts"] / tgm["possessions"]).to_numpy(dtype=float)
    return X, y, keep, tgm


def _ridge(X: np.ndarray, y: np.ndarray, alpha: float) -> np.ndarray:
    """Centred ridge with an unpenalised intercept."""
    xm, ym = X.mean(axis=0), y.mean()
    Xc, yc = X - xm, y - ym
    n_f = Xc.shape[1]
    A = Xc.T @ Xc + alpha * np.eye(n_f)
    return np.linalg.solve(A, Xc.T @ yc)


def fit_impact(
    team_games: pd.DataFrame,
    player_games: pd.DataFrame,
    *,
    alpha: float = 250.0,
    min_player_games: int = 15,
) -> ImpactModel:
    """Fit offensive and defensive per-possession impacts in one regression.

    Caller is responsible for point-in-time slicing: pass only games strictly before the cutoff.
    """
    X, y, keep, tgm = build_design(team_games, player_games, min_player_games)
    if len(tgm) < 200 or not keep:
        return ImpactModel(alpha=alpha, n_team_games=len(tgm), n_players=len(keep))

    beta = _ridge(X, y, alpha)
    n_p = len(keep) + 1

    counts = player_games.groupby("nba_id").size().to_dict()
    clipped = 0
    o: dict[int, float] = {}
    d: dict[int, float] = {}
    for p, i in idx_items(keep):
        vo_raw = float(beta[i])
        # A defensive coefficient is the effect on the OPPONENT's scoring, so a good defender has a
        # negative one. Flip it so that positive always means "helps his own team" and the two can
        # simply be added; without the flip a strong two-way player would cancel himself out.
        vd_raw = -float(beta[n_p + i])
        vo = float(np.clip(vo_raw, -MAX_ABS_IMPACT_PPP, MAX_ABS_IMPACT_PPP))
        vd = float(np.clip(vd_raw, -MAX_ABS_IMPACT_PPP, MAX_ABS_IMPACT_PPP))
        clipped += int(abs(vo_raw) > MAX_ABS_IMPACT_PPP) + int(abs(vd_raw) > MAX_ABS_IMPACT_PPP)
        o[p], d[p] = vo, vd

    return ImpactModel(
        off=o, deff=d, n_games={p: int(counts.get(p, 0)) for p in keep},
        alpha=alpha, n_team_games=len(tgm), n_players=len(keep), clipped=clipped,
    )


def idx_items(keep: list[int]):
    return ((p, i) for i, p in enumerate(keep))


def summarize(m: ImpactModel) -> str:
    if not m.off:
        return "impact model is EMPTY (insufficient data)"
    tot = np.array([m.total(p) for p in m.off])
    q = np.quantile(tot, [0.01, 0.25, 0.5, 0.75, 0.99])
    return (
        f"players {m.n_players}, team-games {m.n_team_games}, alpha {m.alpha:g}, clipped {m.clipped}\n"
        f"total impact per possession: p1 {q[0]:+.4f}  p25 {q[1]:+.4f}  med {q[2]:+.4f}  "
        f"p75 {q[3]:+.4f}  p99 {q[4]:+.4f}\n"
        f"equivalent per 100 possessions: p1 {q[0]*100:+.2f}  med {q[2]*100:+.2f}  p99 {q[4]*100:+.2f}"
    )
