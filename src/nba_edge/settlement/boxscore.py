"""Final box score model used for settlement.

Period keys follow the NBA CDN convention: ``'1Q'..'4Q'`` for regulation quarters and ``'OT1', 'OT2', ...``
for overtime periods. Each value is ``(home_pts, away_pts)`` for that period alone.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from nba_edge.schemas.core import GameStatus, Strict

QUARTERS = ("1Q", "2Q", "3Q", "4Q")
PERIODS = ("FULL", "REG", "1H", "2H", *QUARTERS)


class PlayerLine(Strict):
    """One player's final line. ``played`` False means DNP; counting stats are then 0 by convention."""

    nba_id: int
    team_id: int
    name: str
    played: bool
    started: bool = False
    minutes: float = 0.0
    pts: int = 0
    reb: int = 0
    ast: int = 0
    fg3m: int = 0
    stl: int = 0
    blk: int = 0
    tov: int = 0
    dnp_reason: str | None = None


class FinalBoxScore(Strict):
    """Frozen snapshot of a game's final box score as fetched from a source at ``fetched_at_utc``.

    ``stat_correction_version`` increments when the league issues a stat correction after the game;
    settlement records key on it so corrections append new records rather than rewriting old ones.
    """

    game_id: str
    status: GameStatus
    home_team_id: int
    away_team_id: int
    home_pts: int
    away_pts: int
    period_scores: dict[str, tuple[int, int]] = Field(default_factory=dict)
    n_ot: int = 0
    players: list[PlayerLine] = Field(default_factory=list)
    source: str = "nba_cdn_boxscore"
    fetched_at_utc: datetime
    actual_tip_utc: datetime | None = None
    is_final: bool = False
    stat_correction_version: int = 0

    @field_validator("fetched_at_utc", "actual_tip_utc")
    @classmethod
    def _aware(cls, v: datetime | None) -> datetime | None:
        if v is not None and v.tzinfo is None:
            raise ValueError("datetime must be timezone-aware")
        return v

    @field_validator("period_scores")
    @classmethod
    def _period_keys(cls, v: dict[str, tuple[int, int]]) -> dict[str, tuple[int, int]]:
        for k in v:
            if k not in QUARTERS and not (k.startswith("OT") and k[2:].isdigit()):
                raise ValueError(f"bad period key {k!r}; expected 1Q..4Q or OTn")
        return v

    @model_validator(mode="after")
    def _teams_distinct(self) -> FinalBoxScore:
        if self.home_team_id == self.away_team_id:
            raise ValueError("home and away team ids must differ")
        return self

    def team_index(self, team_id: int) -> int:
        """0 for home, 1 for away; KeyError otherwise."""
        if team_id == self.home_team_id:
            return 0
        if team_id == self.away_team_id:
            return 1
        raise KeyError(f"team {team_id} not in game {self.game_id}")

    def opponent_of(self, team_id: int) -> int:
        return self.away_team_id if self.team_index(team_id) == 0 else self.home_team_id

    def player(self, nba_id: int) -> PlayerLine | None:
        for p in self.players:
            if p.nba_id == nba_id:
                return p
        return None

    def has_period_scores(self, keys: tuple[str, ...]) -> bool:
        return all(k in self.period_scores for k in keys)


def _sum_periods(box: FinalBoxScore, keys: tuple[str, ...], idx: int) -> int:
    missing = [k for k in keys if k not in box.period_scores]
    if missing:
        raise KeyError(f"period scores missing {missing} for game {box.game_id}")
    return sum(box.period_scores[k][idx] for k in keys)


def period_points(box: FinalBoxScore, team_id: int, period: str) -> int:
    """Points scored by ``team_id`` in ``period``.

    ``FULL`` is the final score (includes OT). ``REG`` is the four regulation quarters. Quarters and halves
    EXCLUDE overtime (Kalshi period-market rules). Raises ``KeyError`` when the needed period scores are
    absent or the team is not in the game, and ``ValueError`` for an unknown period.
    """
    idx = box.team_index(team_id)
    p = period.upper()
    if p == "FULL":
        return box.home_pts if idx == 0 else box.away_pts
    if p == "REG":
        return _sum_periods(box, QUARTERS, idx)
    if p in QUARTERS:
        return _sum_periods(box, (p,), idx)
    if p == "1H":
        return _sum_periods(box, ("1Q", "2Q"), idx)
    if p == "2H":
        return _sum_periods(box, ("3Q", "4Q"), idx)
    raise ValueError(f"unknown period {period!r}")
