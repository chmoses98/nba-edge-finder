"""Opponent-adjusted team ratings for ONE set of games (a single season, or the games of a season to date).

Same strength-of-schedule iteration as ``features.build.opponent_adjusted_ratings`` (points per possession, half the league home edge removed,
opponent strength removed, shrunk to the league mean with a small prior mass), but every game counts equally and only the games passed in are
used. The existing function is an exponentially-weighted rating over ALL stored seasons (it already leans on last season, with no roster
adjustment); this one is the current-season-only measurement the blend needs, kept separate so raw current evidence is never mixed with prior data.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from nba_edge.sim.params import LEAGUE

PRIOR_GAMES = 4.0   # same league-mean prior mass as BuildConfig.team_prior_games
N_ITER = 12


@dataclass(frozen=True)
class Adj:
    off: float      # adjusted points per 100 possessions scored, vs the league
    dfn: float      # adjusted points per 100 possessions allowed (lower is better)
    n: int          # games
    @property
    def net(self) -> float:
        return self.off - self.dfn


def league_ppp(games: pd.DataFrame) -> float:
    g = games[games["possessions"] > 0]
    return float((g["pts"] / g["possessions"]).mean()) if len(g) else float(LEAGUE["ppp"])


def adjusted(games: pd.DataFrame, prior_games: float = PRIOR_GAMES, n_iter: int = N_ITER, lg: float | None = None) -> dict[int, Adj]:
    """team_id -> Adj (per 100 possessions). ``games`` are team-game rows (regular season only, the caller filters)."""
    g = games[games["possessions"] > 0]
    if g.empty:
        return {}
    lg = league_ppp(g) if lg is None else lg
    home_adj = LEAGUE["home_ppp_edge"] / 2.0
    teams = sorted(set(g["team_id"]) | set(g["opp_team_id"]))
    off = {t: lg for t in teams}
    dfn = {t: lg for t in teams}
    by = {t: s for t, s in g.groupby("team_id")}
    for _ in range(n_iter):
        no, nd = {}, {}
        for t, s in by.items():
            poss = s["possessions"].to_numpy(float)
            hc = np.where(s["home"].to_numpy(bool), home_adj, -home_adj)
            opp = s["opp_team_id"].to_numpy()
            o_raw = s["pts"].to_numpy(float) / poss - hc - np.array([dfn[o] - lg for o in opp])
            d_raw = s["opp_pts"].to_numpy(float) / poss + hc - np.array([off[o] - lg for o in opp])
            n = len(s)
            no[t] = (o_raw.sum() + prior_games * lg) / (n + prior_games)
            nd[t] = (d_raw.sum() + prior_games * lg) / (n + prior_games)
        off.update(no)
        dfn.update(nd)
    return {t: Adj(100 * (off[t] - lg), 100 * (dfn[t] - lg), len(by[t]) if t in by else 0) for t in teams}


def game_margin_variance(games: pd.DataFrame, ratings: dict[int, Adj] | None = None) -> float:
    """Per-game noise variance (points per 100 possessions, squared): the variance of what a game adds that the two teams' adjusted ratings and
    home court do not explain. With no ratings given they are fitted on these games."""
    g = games[games["possessions"] > 0]
    ratings = ratings if ratings is not None else adjusted(g)
    actual = 100 * (g["pts"] - g["opp_pts"]) / g["possessions"]
    mine = g["team_id"].map(lambda t: ratings[t].net if t in ratings else 0.0)
    theirs = g["opp_team_id"].map(lambda t: ratings[t].net if t in ratings else 0.0)
    hc = np.where(g["home"].to_numpy(bool), 1.0, -1.0) * 100 * LEAGUE["home_ppp_edge"]
    resid = actual - (mine - theirs + hc)
    n_teams = max(1, g["team_id"].nunique())
    dof = max(1.0, len(g) - n_teams / 2)   # one fitted rating per team shared by its games, counted once per game pair
    return float((resid ** 2).sum() / dof)
