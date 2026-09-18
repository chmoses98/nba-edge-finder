"""Season simulator (interface + v0.1 implementation) for season-long Kalshi families.

Futures are NOT priced from the one-game engine. This module simulates the remainder of a regular season from
team strengths, the remaining schedule and current records, producing win-total distributions and standings
probabilities. It is deliberately simpler than the game engine: each remaining game is a normal-approximation
draw of the margin with a shared strength uncertainty per team per season draw (so a team's games are positively
correlated through its true-strength uncertainty — critical for win-total tails).

Not modelled yet (RESEARCH): injuries over the season, trades, tanking, rest, play-in/playoff series, tiebreakers
(seeds use win% with random tie-breaks), NBA Cup.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

SEASON_SIM_VERSION = "season-sim-0.1.0"
MARGIN_SD = 13.5
HOME_EDGE = 2.6  # points


@dataclass
class TeamStrength:
    team_id: int
    conference: str  # East | West
    rating: float  # net points per game vs average opponent on neutral floor
    rating_sd: float = 2.5  # uncertainty about true strength (drives win-total dispersion)
    wins: int = 0
    losses: int = 0


@dataclass
class SeasonResult:
    n_sims: int
    seed: int
    team_ids: list[int]
    wins: np.ndarray  # (n, teams) final regular-season wins
    conf_rank: np.ndarray  # (n, teams) 1 = best in conference
    version: str = SEASON_SIM_VERSION
    meta: dict[str, float] = field(default_factory=dict)

    def idx(self, team_id: int) -> int:
        return self.team_ids.index(team_id)

    def p_wins_ge(self, team_id: int, k: float) -> float:
        return float((self.wins[:, self.idx(team_id)] >= k).mean())

    def p_conf_rank_le(self, team_id: int, k: int) -> float:
        return float((self.conf_rank[:, self.idx(team_id)] <= k).mean())

    def p_playoffs_direct(self, team_id: int) -> float:
        return self.p_conf_rank_le(team_id, 6)

    def p_playin(self, team_id: int) -> float:
        r = self.conf_rank[:, self.idx(team_id)]
        return float(((r >= 7) & (r <= 10)).mean())


def simulate_season(teams: list[TeamStrength], remaining: list[tuple[int, int]], n_sims: int, seed: int) -> SeasonResult:
    """``remaining``: list of (home_team_id, away_team_id) games still to play."""
    rng = np.random.default_rng(seed)
    ids = [t.team_id for t in teams]
    pos = {tid: i for i, tid in enumerate(ids)}
    base = np.array([t.rating for t in teams])
    sd = np.array([t.rating_sd for t in teams])
    wins = np.tile(np.array([t.wins for t in teams], dtype=np.int64), (n_sims, 1))
    true_rating = base[None, :] + rng.normal(0.0, 1.0, (n_sims, len(ids))) * sd[None, :]
    if remaining:
        h = np.array([pos[g[0]] for g in remaining])
        a = np.array([pos[g[1]] for g in remaining])
        mu = true_rating[:, h] - true_rating[:, a] + HOME_EDGE  # (n, games)
        margin = mu + rng.normal(0.0, MARGIN_SD, mu.shape)
        home_win = margin > 0
        # ties impossible in basketball; a zero margin is resolved by the sign of noise (measure-zero event)
        np.add.at(wins, (np.repeat(np.arange(n_sims), len(h)), np.tile(h, n_sims)), home_win.ravel().astype(np.int64))
        np.add.at(wins, (np.repeat(np.arange(n_sims), len(a)), np.tile(a, n_sims)), (~home_win).ravel().astype(np.int64))
    conf = np.array([t.conference for t in teams])
    conf_rank = np.zeros_like(wins)
    for c in np.unique(conf):
        cols = np.where(conf == c)[0]
        w = wins[:, cols] + rng.random((n_sims, len(cols))) * 1e-3  # random tie-break
        order = np.argsort(-w, axis=1)
        ranks = np.empty_like(order)
        rows = np.arange(n_sims)[:, None]
        ranks[rows, order] = np.arange(1, len(cols) + 1)[None, :]
        conf_rank[:, cols] = ranks
    return SeasonResult(n_sims, seed, ids, wins, conf_rank, meta={"margin_sd": MARGIN_SD, "home_edge": HOME_EDGE})
