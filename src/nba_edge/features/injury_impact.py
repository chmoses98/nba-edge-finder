"""Point-in-time *candidate* estimates of injury effects on team scoring efficiency.

This is a game-level, opponent-adjusted on/off proxy, NOT possession-level RAPM.
It is deliberately shadow-only: the earlier leaguewide minutes-share ridge experiment
was worse on holdout than the team-only baseline. Do not authorize bets from this.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from nba_edge.sim.params import LEAGUE, PlayerParams


@dataclass(frozen=True)
class InjuryImpact:
    player_id: int
    impact_ppp: float  # points per possession from presence vs absence, after shrinkage
    baseline: float  # historical probability of appearing, already reflected in team rating
    on_games: int
    off_games: int
    n_team_games: int


def estimate_team_injury_impacts(
    team_id: int,
    team_games: pd.DataFrame,
    player_games: pd.DataFrame,
    cutoff_date: str,
    players: list[PlayerParams],
    ratings: dict[int, tuple[float, float, float]],
    *,
    max_history: int = 80,
    half_life: float = 30.0,
    ridge: float = 3.0,
    min_contrast: int = 4,
) -> dict[int, InjuryImpact]:
    """Estimate offensive availability effects using only games BEFORE cutoff.

    Fit recent team points/possession after opponent defensive and home adjustments
    against centred player attendance, with ridge shrinkage to zero. No effect is
    inferred without independent on/off observations. Players missing together almost
    always are marked unidentifiable rather than being assigned arbitrary impact.
    Baselines use the same recency weights, to prevent treating a long-term absence
    already included in the team's rating as new negative news.
    """
    if not players or team_games.empty or player_games.empty:
        return {}
    needed_t = {"team_id", "game_id", "game_date_et", "possessions", "pts", "opp_team_id", "home"}
    needed_p = {"team_id", "game_id", "game_date_et", "nba_id", "minutes"}
    if not needed_t.issubset(team_games.columns) or not needed_p.issubset(player_games.columns):
        return {}

    tg = team_games.loc[
        (team_games["team_id"] == team_id) & (team_games["game_date_et"] < cutoff_date)
    ].copy()
    pg = player_games.loc[
        (player_games["team_id"] == team_id) & (player_games["game_date_et"] < cutoff_date)
    ].copy()
    if "season_type" in tg:
        tg = tg.loc[tg["season_type"] != "preseason"]
    if "season_type" in pg:
        pg = pg.loc[pg["season_type"] != "preseason"]
    tg["possessions"] = pd.to_numeric(tg["possessions"], errors="coerce")
    tg = tg.loc[(tg["possessions"] > 50) & tg["pts"].notna()]
    tg = tg.sort_values(["game_date_et", "game_id"]).drop_duplicates("game_id", keep="last").tail(max_history)
    if len(tg) < 30:
        return {}

    pg = pg.loc[pg["game_id"].isin(tg["game_id"])]
    pg["minutes"] = pd.to_numeric(pg["minutes"], errors="coerce").fillna(0.0)
    # Missing/incomplete box scores must not be interpreted as players being out.
    n_active = pg.loc[pg["minutes"] > 0].groupby("game_id")["nba_id"].nunique()
    tg = tg.loc[tg["game_id"].map(n_active).fillna(0) >= 8].copy()
    if len(tg) < 30:
        return {}

    candidates = [p for p in players if p.min_mean >= 18.0]
    if not candidates:
        return {}
    ids = [p.nba_id for p in candidates]
    seen = pg.groupby(["game_id", "nba_id"])["minutes"].max().unstack(fill_value=0)
    seen = seen.reindex(index=tg["game_id"], columns=ids, fill_value=0)
    X = (seen.to_numpy(dtype=float) >= 8.0).astype(float)
    n = len(tg)
    ages = np.arange(n - 1, -1, -1)
    w = 0.5 ** (ages / half_life)
    w /= np.mean(w)

    on = X.sum(axis=0).astype(int)
    off = n - on
    valid = (on >= min_contrast) & (off >= min_contrast)
    if not valid.any():
        return {}

    # Players always absent together (or exact replacements for each other)
    # cannot be separated by game-level data. Fail closed on those columns.
    centered = X - np.average(X, axis=0, weights=w)
    for i in np.flatnonzero(valid):
        for j in range(i + 1, X.shape[1]):
            if not valid[j]:
                continue
            denom = np.sqrt(np.sum(w * centered[:, i] ** 2) * np.sum(w * centered[:, j] ** 2))
            if denom > 0 and abs(np.sum(w * centered[:, i] * centered[:, j]) / denom) > 0.95:
                valid[i] = False
                valid[j] = False
    if not valid.any():
        return {}

    opponent = tg["opp_team_id"].astype(int).to_numpy()
    opponent_def = np.array([ratings.get(t, (LEAGUE["ppp"], LEAGUE["ppp"], 0.0))[1] for t in opponent])
    home_edge = np.where(tg["home"].astype(bool).to_numpy(), 1.0, -1.0) * LEAGUE["home_ppp_edge"] / 2
    y = tg["pts"].to_numpy(dtype=float) / tg["possessions"].to_numpy(dtype=float)
    y -= opponent_def - LEAGUE["ppp"] + home_edge
    use = np.flatnonzero(valid)
    Z = centered[:, use]
    zy = y - np.average(y, weights=w)
    zw = Z * np.sqrt(w)[:, None]
    # Do not extrapolate beyond the observed data. Ridge is a research prior, not proof.
    beta = np.linalg.solve(zw.T @ zw + ridge * np.eye(len(use)), zw.T @ (zy * np.sqrt(w)))
    result: dict[int, InjuryImpact] = {}
    for k, b in zip(use, beta, strict=True):
        baseline = float(np.average(X[:, k], weights=w))
        result[ids[k]] = InjuryImpact(
            player_id=ids[k],
            impact_ppp=float(np.clip(b, -0.08, 0.08)),
            baseline=baseline,
            on_games=int(on[k]),
            off_games=int(off[k]),
            n_team_games=n,
        )
    return result
