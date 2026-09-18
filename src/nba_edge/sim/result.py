"""The joint simulated universe for one game. Everything downstream (contract pricing, ladders, correlation,
best-expression) reads from these arrays so related contracts are priced from the SAME draws.

Conventions
- axis 0 is always the simulation index (n_sims).
- ``period_pts`` has shape (n_sims, 2, 4 + max_ot): index 0 = home, 1 = away; periods 0..3 are quarters, 4.. are OT
  periods (zeros if no OT in that draw).
- Player arrays are keyed by nba_id; ``played`` False => all counting stats are 0 and minutes 0 for that draw.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

STAT_KEYS = ("pts", "reb", "ast", "fg3m", "stl", "blk", "tov", "fga", "fta", "oreb", "dreb", "min")


@dataclass
class PlayerSim:
    nba_id: int
    team_id: int
    name: str
    played: np.ndarray  # bool (n,)
    started: np.ndarray  # bool (n,)
    stats: dict[str, np.ndarray]  # each (n,), keys in STAT_KEYS ('min' is float minutes)

    def stat(self, key: str) -> np.ndarray:
        if key == "pra":
            return self.stats["pts"] + self.stats["reb"] + self.stats["ast"]
        if key == "pr":
            return self.stats["pts"] + self.stats["reb"]
        if key == "pa":
            return self.stats["pts"] + self.stats["ast"]
        if key == "ra":
            return self.stats["reb"] + self.stats["ast"]
        if key == "double_double":
            cats = np.stack([self.stats[k] >= 10 for k in ("pts", "reb", "ast", "stl", "blk")], axis=1)
            return (cats.sum(axis=1) >= 2).astype(float)
        if key == "triple_double":
            cats = np.stack([self.stats[k] >= 10 for k in ("pts", "reb", "ast", "stl", "blk")], axis=1)
            return (cats.sum(axis=1) >= 3).astype(float)
        return self.stats[key]


@dataclass
class SimResult:
    game_id: str
    home_team_id: int
    away_team_id: int
    n_sims: int
    seed: int
    sim_version: str
    home_pts: np.ndarray  # int (n,)
    away_pts: np.ndarray
    period_pts: np.ndarray  # int (n, 2, 4+max_ot)
    n_ot: np.ndarray  # int (n,)
    possessions: np.ndarray  # float (n,) per-team possessions (regulation + OT)
    players: dict[int, PlayerSim] = field(default_factory=dict)
    diagnostics: dict[str, float] = field(default_factory=dict)

    # ---- derived team quantities -------------------------------------------------------------
    @property
    def margin(self) -> np.ndarray:  # home - away
        return self.home_pts - self.away_pts

    @property
    def total(self) -> np.ndarray:
        return self.home_pts + self.away_pts

    def team_pts(self, team_id: int, period: str = "FULL") -> np.ndarray:
        idx = 0 if team_id == self.home_team_id else 1
        if team_id not in (self.home_team_id, self.away_team_id):
            raise KeyError(f"team {team_id} not in game {self.game_id}")
        return self._period_slice(period)[:, idx]

    def team_margin(self, team_id: int, period: str = "FULL") -> np.ndarray:
        sl = self._period_slice(period)
        m = sl[:, 0] - sl[:, 1]
        return m if team_id == self.home_team_id else -m

    def period_total(self, period: str = "FULL") -> np.ndarray:
        sl = self._period_slice(period)
        return sl[:, 0] + sl[:, 1]

    def _period_slice(self, period: str) -> np.ndarray:
        """(n, 2) points for the requested period. FULL includes OT; quarters/halves exclude OT (Kalshi rules)."""
        p = period.upper()
        if p == "FULL":
            return np.stack([self.home_pts, self.away_pts], axis=1)
        if p in ("1Q", "2Q", "3Q", "4Q"):
            q = int(p[0]) - 1
            return self.period_pts[:, :, q]
        if p == "1H":
            return self.period_pts[:, :, 0:2].sum(axis=2)
        if p == "2H":
            return self.period_pts[:, :, 2:4].sum(axis=2)
        if p == "REG":
            return self.period_pts[:, :, 0:4].sum(axis=2)
        raise ValueError(f"unknown period {period}")
