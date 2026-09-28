"""Canonical ingestion records and the adapter interface for matchup-grade source data.

Built now, before a suitable source exists, so that when one does the work is wiring rather than
design. The audit in ``docs/research/MATCHUP_SOURCE_AUDIT.md`` explains why nothing is wired to a
live source yet.

Two rules carried over from the delta archive, for the same reasons:

* **Raw records are preserved alongside normalised ones.** A normalisation bug found in six months
  is recoverable if the source payload is still there and unrecoverable if it is not.
* **Identity is explicit.** Every record carries the source's own ids AND, separately, the mapped
  project ids, with the mapping's confidence. Silently merging the two is how a player-identity bug
  becomes a modelling conclusion.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from pydantic import Field

from nba_edge.schemas.core import Strict


class ShotZone(StrEnum):
    RIM = "rim"
    PAINT_NON_RIM = "paint_non_rim"
    MIDRANGE = "midrange"
    CORNER_THREE = "corner_three"
    ABOVE_BREAK_THREE = "above_break_three"
    UNKNOWN = "unknown"


class ShotType(StrEnum):
    PULLUP = "pullup"
    CATCH_AND_SHOOT = "catch_and_shoot"
    DRIVE = "drive"
    POST = "post"
    PUTBACK = "putback"
    TRANSITION = "transition"
    UNKNOWN = "unknown"


class IdentityMapping(Strict):
    """A source id and what we mapped it to, with how sure we are."""

    source_id: str
    mapped_player_id: int | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    method: str | None = None


class RawSourceRecord(Strict):
    """The source's own payload, kept verbatim next to whatever we derived from it."""

    source: str
    source_version: str | None = None
    fetched_at_utc: datetime
    game_id: str | None = None
    payload_sha256: str
    payload: dict[str, Any] = Field(default_factory=dict)


class PossessionRecord(Strict):
    game_id: str
    period: int
    possession_index: int
    start_clock_seconds: float | None = None
    end_clock_seconds: float | None = None
    offense_team_id: int | None = None
    defense_team_id: int | None = None
    points: int | None = None
    outcome: str | None = None
    offense_lineup: tuple[int, ...] = ()
    defense_lineup: tuple[int, ...] = ()
    source: str = "unknown"


class SubstitutionRecord(Strict):
    game_id: str
    period: int
    clock_seconds: float | None = None
    team_id: int | None = None
    player_in_id: int | None = None
    player_out_id: int | None = None
    source: str = "unknown"


class LineupStintRecord(Strict):
    """One interval with a fixed five on each side. The unit lineup research is actually built on."""

    game_id: str
    period: int
    stint_index: int
    start_clock_seconds: float | None = None
    end_clock_seconds: float | None = None
    seconds: float | None = None
    possessions: int | None = None
    home_lineup: tuple[int, ...] = ()
    away_lineup: tuple[int, ...] = ()
    home_points: int | None = None
    away_points: int | None = None
    source: str = "unknown"
    source_version: str | None = None
    ingested_at_utc: datetime | None = None

    @property
    def lineups_are_complete(self) -> bool:
        """Five a side. A stint that fails this must be quarantined, never silently used."""
        return len(self.home_lineup) == 5 and len(self.away_lineup) == 5


class ShotAttemptRecord(Strict):
    """A shot, with the defender only when the source actually identifies one."""

    game_id: str
    period: int
    clock_seconds: float | None = None
    shooter_player_id: int | None = None
    # None means the source did not identify a defender -- never "nobody was guarding".
    defender_player_id: int | None = None
    defender_distance_ft: float | None = None
    zone: ShotZone = ShotZone.UNKNOWN
    shot_type: ShotType = ShotType.UNKNOWN
    x: float | None = None
    y: float | None = None
    value: int | None = None
    made: bool | None = None
    assister_player_id: int | None = None
    source: str = "unknown"


class FreeThrowRecord(Strict):
    game_id: str
    period: int
    clock_seconds: float | None = None
    shooter_player_id: int | None = None
    fouler_player_id: int | None = None
    made: bool | None = None
    source: str = "unknown"


class TurnoverRecord(Strict):
    game_id: str
    period: int
    clock_seconds: float | None = None
    player_id: int | None = None
    forced_by_player_id: int | None = None
    kind: str | None = None
    source: str = "unknown"


@runtime_checkable
class MatchupSourceAdapter(Protocol):
    """What a usable matchup source must be able to answer.

    Every method may legitimately return an empty sequence: a source that has play-by-play but no
    defender attribution implements ``shots`` without defender ids rather than inventing them.
    ``available()`` is how a source declares what it can actually do, so the pipeline can record
    "this source cannot supply defenders" instead of discovering it as silently missing data.
    """

    name: str

    def available(self) -> dict[str, bool]:
        """Capability flags, e.g. {"possessions": True, "defenders": False}."""
        ...

    def raw(self, game_id: str) -> list[RawSourceRecord]: ...
    def possessions(self, game_id: str) -> list[PossessionRecord]: ...
    def substitutions(self, game_id: str) -> list[SubstitutionRecord]: ...
    def stints(self, game_id: str) -> list[LineupStintRecord]: ...
    def shots(self, game_id: str) -> list[ShotAttemptRecord]: ...
    def free_throws(self, game_id: str) -> list[FreeThrowRecord]: ...
    def turnovers(self, game_id: str) -> list[TurnoverRecord]: ...


CAPABILITIES = (
    "possessions", "substitutions", "stints", "shots", "defenders",
    "shot_zones", "shot_types", "free_throws", "turnovers", "play_types",
)


def capability_report(adapter: MatchupSourceAdapter) -> dict[str, Any]:
    """What a source can do, as a record rather than as folklore."""
    have = adapter.available()
    return {
        "source": adapter.name,
        "capabilities": {c: bool(have.get(c, False)) for c in CAPABILITIES},
        "missing": sorted(c for c in CAPABILITIES if not have.get(c, False)),
    }


def quarantine_stints(stints: list[LineupStintRecord]) -> tuple[list[LineupStintRecord], list[dict[str, Any]]]:
    """Split stints into usable and quarantined, with a reason for each rejection.

    Bad games are quarantined explicitly rather than silently included -- a lineup that is not five
    a side will produce plausible-looking per-lineup rates that are simply wrong.
    """
    good: list[LineupStintRecord] = []
    bad: list[dict[str, Any]] = []
    for s in stints:
        reasons = []
        if not s.lineups_are_complete:
            reasons.append(f"lineup sizes home={len(s.home_lineup)} away={len(s.away_lineup)}, expected 5/5")
        if len(set(s.home_lineup)) != len(s.home_lineup) or len(set(s.away_lineup)) != len(s.away_lineup):
            reasons.append("duplicate player within a lineup")
        if s.seconds is not None and s.seconds < 0:
            reasons.append(f"negative duration {s.seconds}")
        if reasons:
            bad.append({"game_id": s.game_id, "period": s.period, "stint_index": s.stint_index,
                        "reasons": reasons})
        else:
            good.append(s)
    return good, bad
