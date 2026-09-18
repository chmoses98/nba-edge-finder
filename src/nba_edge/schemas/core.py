from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SeasonType(StrEnum):
    PRESEASON = "preseason"
    REGULAR = "regular"
    PLAYIN = "playin"
    PLAYOFFS = "playoffs"
    ALLSTAR = "allstar"
    OTHER = "other"


def season_type_from_game_id(game_id: str) -> SeasonType:
    """NBA game ids: '00' league + season-type digit + 2-digit season + 5-digit sequence.
    Third character: 1 preseason, 2 regular, 3 all-star, 4 playoffs, 5 play-in (observed since 2020)."""
    if len(game_id) != 10 or not game_id.isdigit():
        return SeasonType.OTHER
    return {"1": SeasonType.PRESEASON, "2": SeasonType.REGULAR, "3": SeasonType.ALLSTAR, "4": SeasonType.PLAYOFFS, "5": SeasonType.PLAYIN}.get(game_id[2], SeasonType.OTHER)


class GameStatus(StrEnum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    FINAL = "final"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    UNKNOWN = "unknown"


class Game(Strict):
    game_id: str
    season: str  # '2026-27'
    season_type: SeasonType
    game_date_et: str  # YYYY-MM-DD
    start_time_utc: datetime  # scheduled tip (authoritative for PIT cutoffs until actual tip known)
    actual_tip_utc: datetime | None = None
    home_team_id: int
    away_team_id: int
    home_tricode: str
    away_tricode: str
    status: GameStatus = GameStatus.SCHEDULED
    arena: str | None = None
    neutral_site: bool = False
    source: str = "nba_cdn_schedule"

    @field_validator("start_time_utc", "actual_tip_utc")
    @classmethod
    def _aware(cls, v: datetime | None) -> datetime | None:
        if v is not None and v.tzinfo is None:
            raise ValueError("datetime must be timezone-aware")
        return v

    @property
    def effective_tip_utc(self) -> datetime:
        return self.actual_tip_utc or self.start_time_utc


class InjuryStatus(StrEnum):
    AVAILABLE = "available"
    PROBABLE = "probable"
    QUESTIONABLE = "questionable"
    DOUBTFUL = "doubtful"
    OUT = "out"
    UNKNOWN = "unknown"


class InjuryEntry(Strict):
    game_id: str | None
    game_date_et: str
    team_id: int
    nba_id: int | None
    player_name_raw: str
    status: InjuryStatus
    reason: str | None = None
    report_time_utc: datetime
    source: str


class Provenance(Strict):
    """Attached to every derived artifact: what produced it and from which inputs."""
    produced_at_utc: datetime
    producer: str  # module/function
    code_version: str  # git sha or package version
    model_version: str | None = None
    inputs: dict[str, Any] = Field(default_factory=dict)  # e.g. {"schedule_snapshot": "...", "injury_snapshot": "..."}
    data_cutoff_utc: datetime | None = None  # nothing after this instant was used
