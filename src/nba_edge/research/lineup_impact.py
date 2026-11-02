"""Certified-stint adjusted plus-minus candidate for lineup-aware injury response.

Uses possession-level five-on-five lineup variation, unlike the failed box-score
minutes-share APM. Fit is strictly historical; output is shadow-only until a held-out
prediction test demonstrates a positive gain. This is regularised observational APM,
not a causal estimate of an individual player's value.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix, diags, vstack
from scipy.sparse.linalg import lsqr

from nba_edge.sim.params import LEAGUE


@dataclass
class LineupImpactModel:
    offense: dict[int, float] = field(default_factory=dict)
    defense: dict[int, float] = field(default_factory=dict)
    n_games: int = 0
    n_stints: int = 0
    training_cutoff: str = ""
    n_players: int = 0

    def offensive_absence_ppp(self, player_id: int) -> float:
        return self.offense.get(int(player_id), 0.0)

    def defensive_absence_ppp(self, player_id: int) -> float:
        return self.defense.get(int(player_id), 0.0)


def fit_lineup_impact(
    stints: pd.DataFrame,
    team_games: pd.DataFrame,
    cutoff_date: str,
    *,
    player_ridge: float = 30.0,
    team_ridge: float = 1.0,
    min_player_seconds: float = 3600.0,
    min_games: int = 100,
) -> LineupImpactModel:
    """Fit offence and defence from two PPP observations per certified stint.

    Positive offence coefficient raises own scoring; positive defence coefficient
    lowers opposing scoring. Five players share a possession, hence individual
    full-game absence terms are normalised by five. We control for team identity
    on both sides, use only certified five-man reconstructions, and bound effects
    to +/-0.06 PPP. This does NOT imply they are validated predictions.
    """
    empty = LineupImpactModel(training_cutoff=cutoff_date)
    if stints.empty or team_games.empty:
        return empty
    colsh = [f"home_p{i}" for i in range(1, 6)]
    colsa = [f"away_p{i}" for i in range(1, 6)]
    needed = {"game_id", "certified", "home_pts", "away_pts", "home_poss", "away_poss", "seconds", *colsh, *colsa}
    if not needed.issubset(stints.columns):
        return empty
    must = {"game_id", "team_id", "opp_team_id", "home", "game_date_et"}
    if not must.issubset(team_games.columns):
        return empty
    tg = team_games[(team_games["home"] == True) & (team_games["game_date_et"] < cutoff_date)].copy()  # noqa: E712
    if "season_type" in tg:
        tg = tg[tg["season_type"] != "preseason"]
    tg = tg.sort_values("game_date_et").drop_duplicates("game_id", keep="last")
    meta = {str(r.game_id): (int(r.team_id), int(r.opp_team_id)) for r in tg.itertuples()}
    s = stints[(stints["certified"] == True) & stints["game_id"].astype(str).isin(meta)].copy()  # noqa: E712
    s = s[(s["home_poss"] > 0) | (s["away_poss"] > 0)]
    if s.empty or s["game_id"].nunique() < min_games:
        return empty
    for col in colsh + colsa:
        s = s[s[col].notna()]
    if s.empty:
        return empty

    # Only identifiable, substantially-used players get individual coefficients.
    secs: dict[int, float] = {}
    for col in colsh + colsa:
        vals = s.groupby(col)["seconds"].sum()
        for pid, sec in vals.items():
            secs[int(pid)] = secs.get(int(pid), 0.0) + float(sec)
    ids = sorted(p for p, seconds in secs.items() if seconds >= min_player_seconds)
    if len(ids) < 10:
        return empty
    player_idx = {p: i for i, p in enumerate(ids)}
    teams = sorted({t for pair in meta.values() for t in pair})
    team_idx = {t: i for i, t in enumerate(teams)}
    p, t = len(ids), len(teams)
    # offense player | defense player | offense team FE | opposing defense team FE | home indicator
    dim = 2 * p + 2 * t + 1
    entries_r: list[int] = []
    entries_c: list[int] = []
    entries_v: list[float] = []
    target: list[float] = []
    weights: list[float] = []

    def add(r: int, c: int, v: float) -> None:
        entries_r.append(r)
        entries_c.append(c)
        entries_v.append(v)

    for v in s.itertuples(index=False):
        home, away = meta[str(v.game_id)]
        hplayers = [int(getattr(v, col)) for col in colsh]
        aplayers = [int(getattr(v, col)) for col in colsa]
        for own, opp, own_ids, opp_ids, points, poss, home_indicator in (
            (home, away, hplayers, aplayers, v.home_pts, v.home_poss, 1.0),
            (away, home, aplayers, hplayers, v.away_pts, v.away_poss, -1.0),
        ):
            if poss <= 0:
                continue
            row = len(target)
            target.append(float(points) / float(poss) - LEAGUE["ppp"])
            weights.append(float(poss))
            for player in own_ids:
                j = player_idx.get(player)
                if j is not None:
                    add(row, j, 0.2)
            for player in opp_ids:
                j = player_idx.get(player)
                if j is not None:
                    add(row, p + j, -0.2)
            add(row, 2 * p + team_idx[own], 1.0)
            add(row, 2 * p + t + team_idx[opp], 1.0)
            add(row, dim - 1, home_indicator)

    if not target:
        return empty
    a = coo_matrix((entries_v, (entries_r, entries_c)), shape=(len(target), dim)).tocsr()
    w = np.sqrt(np.array(weights, dtype=float))
    penalty = np.full(dim, player_ridge, dtype=float)
    penalty[2 * p:2 * p + 2 * t] = team_ridge
    penalty[-1] = team_ridge
    # Ridge in weighted least squares, sparse to keep the fit practical.
    augmented = vstack([a.multiply(w[:, None]), diags(np.sqrt(penalty))], format="csr")
    y = np.concatenate([np.array(target) * w, np.zeros(dim)])
    beta = lsqr(augmented, y, atol=1e-6, btol=1e-6, iter_lim=400)[0]
    # A player affects only one of five positions on the floor. Do not assign
    # the whole 5-man lineup coefficient to his individual availability.
    return LineupImpactModel(
        offense={pid: float(np.clip(beta[i] / 5.0, -0.06, 0.06)) for pid, i in player_idx.items()},
        defense={pid: float(np.clip(beta[p + i] / 5.0, -0.06, 0.06)) for pid, i in player_idx.items()},
        n_games=int(s["game_id"].nunique()), n_stints=len(s),
        training_cutoff=cutoff_date, n_players=p,
    )
