"""Normalized shot events from ESPN play-by-play.

**What this data is, stated once so no later code has to guess:** ESPN supplies the *location of a
play*, and nothing about who was defending it. A shot chart is a description of the shooter. The
source audit measured that every endpoint carrying defender attribution is unreachable from this
project's egress, so a defender effect cannot be derived here by any amount of processing.

``DEFENDER_ATTRIBUTION_AVAILABLE = False`` exists so that assumption is a value a test can assert
against rather than a sentence in a docstring somebody skims. If a future source does supply
defender ids, that constant changes and the change is visible in a diff.

**Coordinates are not trusted until validated.** ``ShotEvent`` stores raw ``x``/``y`` exactly as the
source gave them plus a ``coordinate_valid`` flag, and deliberately carries no zone. Zones are
assigned by :mod:`nba_edge.shotprofile.court`, which depends on a court transform measured by
``scripts/probe_shot_coordinates.py`` and documented in ``docs/research/ESPN_SHOT_COORDINATES.md``.
Keeping the two apart means a normalized event is still correct even if the geometry is later found
to be wrong.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from pydantic import field_validator, model_validator

from nba_edge.schemas.core import Strict

# v2 adds the season-type triplet (season_type / espn_season_type / season_type_source) to every row.
# The schema version describes the row SHAPE; the ingest version describes the code path that produced it,
# so a backfilled row keeps its original ingest version and only its schema version moves forward.
SHOT_EVENT_SCHEMA_VERSION = "shotevent/2"
INGEST_VERSION = "espn-pbp/2"

# ESPN encodes "no location recorded" as an int32-derived sentinel (-2147483648/10 and neighbours),
# not as null. Anything beyond court-plausible bounds is missing data, never a position.
SENTINEL_ABS = 100_000.0

# Measured, not assumed: no reachable source attributes a defender to a shot. See
# docs/research/MATCHUP_SOURCE_AUDIT.md -- every stats.nba.com matchup endpoint times out at a
# 180-second budget with a passing control.
DEFENDER_ATTRIBUTION_AVAILABLE = False

_FT_RE = re.compile(r"free throw", re.I)
_MADE_RE = re.compile(r"\bmakes\b", re.I)
_MISS_RE = re.compile(r"\bmisses\b", re.I)


def coordinate_is_usable(x: Any, y: Any) -> bool:
    """A coordinate is usable only if BOTH axes are finite and court-plausible.

    Counting the presence of a ``coordinate`` key is not the same as counting a location: a probe
    run reported 434/434 play events "with_coordinate" where the values were the sentinel. This
    function is what the difference looks like in code.
    """
    for v in (x, y):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return False
        if v != v or abs(v) >= SENTINEL_ABS:  # NaN, inf, or sentinel
            return False
    return True


class ShotEvent(Strict):
    """One play-by-play event that ESPN marks as a shooting play.

    Raw and normalized fields only. No zone, no distance in feet, no defender -- each of those is
    either a geometry question this schema deliberately does not answer, or a fact no reachable
    source supplies.
    """

    # identity
    game_id: str
    event_id: str
    sequence: int | None = None

    # when
    event_time_utc: datetime | None = None
    period: int | None = None
    clock_display: str | None = None
    clock_seconds_remaining: float | None = None

    # who
    shooter_player_id: int | None = None
    shooter_name: str | None = None
    team_id: int | None = None
    opponent_team_id: int | None = None
    is_home: bool | None = None

    # where -- raw, exactly as the source gave it
    x: float | None = None
    y: float | None = None
    coordinate_valid: bool = False

    # what
    shot_made: bool | None = None
    points_value: int | None = None
    is_free_throw: bool = False
    is_shooting_play: bool = False
    event_type: str | None = None
    event_text: str | None = None

    # provenance
    source: str = "espn/summary"
    source_observed_at_utc: datetime | None = None
    ingest_version: str = INGEST_VERSION
    schema_version: str = SHOT_EVENT_SCHEMA_VERSION

    @field_validator("x", "y")
    @classmethod
    def _finite(cls, v: float | None) -> float | None:
        if v is None:
            return None
        if v != v or abs(v) == float("inf"):
            raise ValueError("coordinate must be a finite number or None")
        return v

    @model_validator(mode="after")
    def _coordinate_flag_matches_the_coordinate(self) -> ShotEvent:
        """``coordinate_valid`` may never claim more than the values support.

        A True flag over a sentinel is the single most damaging thing this schema could permit: it
        would put a shot at a plausible-looking place on the floor with nothing to mark it as
        fabricated.
        """
        if self.coordinate_valid and not coordinate_is_usable(self.x, self.y):
            raise ValueError("coordinate_valid=True but x/y are missing or a sentinel")
        return self

    @model_validator(mode="after")
    def _free_throws_have_no_floor_location(self) -> ShotEvent:
        """A free throw is taken from a fixed spot and is not a field-goal location.

        Letting one through with ``coordinate_valid`` would pull every high-volume foul-drawer's
        shot profile toward the line, which reads as a real basketball finding rather than a bug.
        """
        if self.is_free_throw and self.coordinate_valid:
            raise ValueError("a free throw must not carry a usable field-goal coordinate")
        return self

    @property
    def is_field_goal_attempt(self) -> bool:
        return self.is_shooting_play and not self.is_free_throw

    @property
    def usable_for_zone(self) -> bool:
        """Only a field-goal attempt with a real location can be assigned a zone."""
        return self.is_field_goal_attempt and self.coordinate_valid


def clock_to_seconds(display: str | None) -> float | None:
    """``"9:47"`` -> 587.0. Returns None rather than guessing at an unfamiliar format."""
    if not isinstance(display, str):
        return None
    parts = display.strip().split(":")
    try:
        if len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        if len(parts) == 1:
            return float(parts[0])
    except ValueError:
        return None
    return None


def _shot_made(play: dict[str, Any], text: str) -> bool | None:
    """Made/missed, preferring the structured flag and falling back to ESPN's own wording.

    ``scoringPlay`` is authoritative when True. False is NOT evidence of a miss on its own -- it is
    also False for every non-shot event -- so the text is consulted before returning a verdict, and
    None is returned when neither says anything.
    """
    if play.get("scoringPlay") is True:
        return True
    if _MADE_RE.search(text):
        return True
    if _MISS_RE.search(text):
        return False
    if play.get("scoringPlay") is False and play.get("shootingPlay") is True:
        return False
    return None


def parse_play(
    play: dict[str, Any],
    *,
    game_id: str,
    home_team_id: int | None,
    away_team_id: int | None,
    observed_at_utc: datetime | None = None,
) -> ShotEvent | None:
    """One ESPN play -> a ``ShotEvent``, or None if it is not a shot attempt.

    Returns None for every non-shooting event. A rebound carries a coordinate too, and counting one
    as an attempt would inflate rim rates for exactly the players who crash the glass.
    """
    if not isinstance(play, dict):
        return None
    text = str(play.get("text") or "")
    type_text = str((play.get("type") or {}).get("text") or "")
    is_ft = bool(_FT_RE.search(text) or _FT_RE.search(type_text))
    shooting = bool(play.get("shootingPlay"))

    if not shooting and not is_ft:
        return None

    coord = play.get("coordinate")
    raw_x = coord.get("x") if isinstance(coord, dict) else None
    raw_y = coord.get("y") if isinstance(coord, dict) else None
    valid = coordinate_is_usable(raw_x, raw_y) and not is_ft

    team_id = None
    t = play.get("team")
    if isinstance(t, dict) and t.get("id") is not None:
        try:
            team_id = int(t["id"])
        except (TypeError, ValueError):
            team_id = None

    opponent = None
    is_home = None
    if team_id is not None and home_team_id is not None and away_team_id is not None:
        if team_id == home_team_id:
            opponent, is_home = away_team_id, True
        elif team_id == away_team_id:
            opponent, is_home = home_team_id, False

    shooter_id = shooter_name = None
    for part in play.get("participants") or []:
        if not isinstance(part, dict):
            continue
        if part.get("type") in (None, "scorer", "shooter"):
            ath = part.get("athlete")
            if isinstance(ath, dict) and ath.get("id") is not None:
                try:
                    # Negative ids mark an ESPN-sourced player, matching the convention the rest of
                    # the project uses for provisional identities.
                    shooter_id = -int(ath["id"])
                    shooter_name = ath.get("displayName") or ath.get("fullName")
                except (TypeError, ValueError):
                    pass
                break

    sv = play.get("scoreValue")
    points_value = sv if isinstance(sv, int) and not isinstance(sv, bool) else None
    if is_ft and points_value in (None, 0):
        points_value = 1

    period = None
    per = play.get("period")
    if isinstance(per, dict) and isinstance(per.get("number"), int):
        period = per["number"]

    clock_display = None
    clk = play.get("clock")
    if isinstance(clk, dict):
        clock_display = clk.get("displayValue")

    return ShotEvent(
        game_id=game_id,
        event_id=str(play.get("id") or ""),
        sequence=int(play["sequenceNumber"]) if str(play.get("sequenceNumber") or "").isdigit() else None,
        period=period,
        clock_display=clock_display,
        clock_seconds_remaining=clock_to_seconds(clock_display),
        shooter_player_id=shooter_id,
        shooter_name=shooter_name,
        team_id=team_id,
        opponent_team_id=opponent,
        is_home=is_home,
        x=float(raw_x) if valid else None,
        y=float(raw_y) if valid else None,
        coordinate_valid=valid,
        shot_made=_shot_made(play, text),
        points_value=points_value,
        is_free_throw=is_ft,
        is_shooting_play=shooting,
        event_type=type_text or None,
        event_text=text or None,
        source_observed_at_utc=observed_at_utc,
    )


def parse_summary(
    payload: dict[str, Any], *, game_id: str, observed_at_utc: datetime | None = None
) -> list[ShotEvent]:
    """Every shot attempt in one ESPN summary payload, in source order."""
    plays = payload.get("plays")
    if not isinstance(plays, list):
        return []

    home_id = away_id = None
    comps = (payload.get("header") or {}).get("competitions") or []
    if comps and isinstance(comps[0], dict):
        for c in comps[0].get("competitors") or []:
            if not isinstance(c, dict):
                continue
            try:
                tid = int(c["id"])
            except (KeyError, TypeError, ValueError):
                continue
            if c.get("homeAway") == "home":
                home_id = tid
            elif c.get("homeAway") == "away":
                away_id = tid

    out = []
    for p in plays:
        ev = parse_play(p, game_id=game_id, home_team_id=home_id, away_team_id=away_id,
                        observed_at_utc=observed_at_utc)
        if ev is not None:
            out.append(ev)
    return out
