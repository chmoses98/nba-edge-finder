"""Lineup events, and the windows around them where a matchup effect would be visible if it exists.

Section 12 of the research brief asks for the residual test to be run *especially* around lineup
confirmation, late scratches, starter changes and major assignment changes. That is not decoration:
those are the moments when a matchup-aware model and the market can legitimately disagree, because
the news has landed but the price may not have absorbed it yet. Averaged over a season they are a
few percent of observations and any signal in them is invisible.

Everything here is derived from the **prospectively captured** ``matchup/context`` stream, never
from hindsight. A "late scratch" is a player who appears in one captured rotation and is absent from
a later one; it is not a player we know afterwards did not play. The difference matters: the second
definition would label games using information that did not exist at prediction time, which is the
exact leak the whole arm is built to avoid.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

from nba_edge.matchup.schemas import GameMatchupContext, LineupConfidence

EVENTS_VERSION = "matchup-events/1"

# How close to tip a change has to land to count as "late". Chosen to match the horizon at which
# starting lineups are conventionally reported (about 30 minutes before tip) with headroom, not
# tuned against any outcome.
LATE_WINDOW = timedelta(hours=2)


class LineupEventKind(StrEnum):
    """What changed between two consecutive captures of the same game."""

    LINEUP_CONFIRMED = "lineup_confirmed"
    STARTER_CHANGE = "starter_change"
    LATE_SCRATCH = "late_scratch"
    ROTATION_ADDITION = "rotation_addition"
    ASSIGNMENT_SHIFT = "assignment_shift"


@dataclass(frozen=True)
class LineupEvent:
    """One observed change, with the instant it became knowable.

    ``observed_at_utc`` is when the LATER capture saw it -- the first moment a forecaster could have
    acted on it. Using the earlier capture's time would date the news before anyone could know it.
    """

    game_id: str
    kind: LineupEventKind
    observed_at_utc: datetime
    tip_utc: datetime | None
    player_ids: tuple[int, ...] = ()
    detail: str = ""
    events_version: str = EVENTS_VERSION

    @property
    def minutes_before_tip(self) -> float | None:
        if self.tip_utc is None:
            return None
        return round((self.tip_utc - self.observed_at_utc).total_seconds() / 60.0, 2)

    @property
    def is_late(self) -> bool:
        """Did this land inside the late window? Unknown tip means unknown, never True."""
        if self.tip_utc is None:
            return False
        return timedelta(0) <= (self.tip_utc - self.observed_at_utc) <= LATE_WINDOW


def _confirmed(c: GameMatchupContext) -> bool:
    return c.lineup_confidence is LineupConfidence.CONFIRMED


def diff_contexts(before: GameMatchupContext, after: GameMatchupContext) -> list[LineupEvent]:
    """Events implied by two consecutive captures of the same game.

    Raises when the two describe different games: silently comparing across games would invent
    scratches out of roster differences between unrelated teams.
    """
    if before.game_id != after.game_id:
        raise ValueError(
            f"cannot diff captures of different games: {before.game_id} vs {after.game_id}"
        )
    if after.observed_at_utc < before.observed_at_utc:
        raise ValueError("captures must be ordered: `after` is older than `before`")

    out: list[LineupEvent] = []
    at, tip = after.observed_at_utc, after.tip_utc

    def add(kind: LineupEventKind, ids: tuple[int, ...] = (), detail: str = "") -> None:
        out.append(LineupEvent(game_id=after.game_id, kind=kind, observed_at_utc=at,
                               tip_utc=tip, player_ids=ids, detail=detail))

    if _confirmed(after) and not _confirmed(before):
        add(LineupEventKind.LINEUP_CONFIRMED,
            detail=f"{before.lineup_confidence.value} -> {after.lineup_confidence.value}")

    for side in ("home", "away"):
        b = set(getattr(before, f"expected_{side}_starters"))
        a = set(getattr(after, f"expected_{side}_starters"))
        # Only a real swap counts. Going from "unknown" (empty) to a named five is the lineup being
        # reported for the first time, which is a confirmation, not a change of starter.
        if b and a and b != a:
            add(LineupEventKind.STARTER_CHANGE, tuple(sorted(a ^ b)), f"{side}: {sorted(b ^ a)}")

        rb = set(getattr(before, f"expected_{side}_rotation"))
        ra = set(getattr(after, f"expected_{side}_rotation"))
        if rb and ra:
            gone, new = rb - ra, ra - rb
            if gone:
                add(LineupEventKind.LATE_SCRATCH, tuple(sorted(gone)), f"{side}: dropped")
            if new:
                add(LineupEventKind.ROTATION_ADDITION, tuple(sorted(new)), f"{side}: added")

    # A material change in who is expected to guard whom.
    bx = {e.offensive_player_id: e for e in before.exposures}
    for e in after.exposures:
        prev = bx.get(e.offensive_player_id)
        if prev is None:
            continue
        top_b = max(prev.shares, key=lambda s: s.share, default=None)
        top_a = max(e.shares, key=lambda s: s.share, default=None)
        if top_b is None or top_a is None:
            continue
        if (top_b.ref, top_b.defender_player_id) != (top_a.ref, top_a.defender_player_id):
            add(LineupEventKind.ASSIGNMENT_SHIFT, (e.offensive_player_id,),
                f"primary exposure {top_b.ref.value} -> {top_a.ref.value}")
    return out


def events_for_game(contexts: Sequence[GameMatchupContext]) -> list[LineupEvent]:
    """Every event implied by a game's capture history, in observation order."""
    ordered = sorted(contexts, key=lambda c: c.observed_at_utc)
    out: list[LineupEvent] = []
    for b, a in zip(ordered, ordered[1:], strict=False):
        out.extend(diff_contexts(b, a))
    return out


def window_labels(
    events: Sequence[LineupEvent], *, decision_at: datetime, game_id: str
) -> dict[str, Any]:
    """Which event windows a forecast made at ``decision_at`` sits inside.

    Strictly causal: only events already observed at the decision instant are counted. An event that
    became knowable afterwards cannot label a forecast that preceded it, however tempting it is to
    say "this was the late-scratch game".
    """
    seen = [e for e in events if e.game_id == game_id and e.observed_at_utc <= decision_at]
    kinds = {e.kind.value for e in seen}
    late = {e.kind.value for e in seen if e.is_late}
    return {
        "game_id": game_id,
        "decision_at_utc": decision_at.isoformat(),
        "n_events_knowable": len(seen),
        "kinds": sorted(kinds),
        "late_kinds": sorted(late),
        "any_event": bool(kinds),
        "any_late_event": bool(late),
        "events_version": EVENTS_VERSION,
    }


def stratify(
    observations: Sequence[Any], events: Sequence[LineupEvent],
    *, decision_attr: str = "tip_utc", game_attr: str = "game_id",
) -> dict[str, list[Any]]:
    """Split observations into event strata, so a residual test can be run inside each.

    The ``no_event`` stratum is reported alongside the others on purpose. An effect that appears
    only in the event windows is interesting; one that appears everywhere equally is more likely a
    property of the model than of the news.
    """
    out: dict[str, list[Any]] = {"all": list(observations), "no_event": [],
                                 "any_event": [], "any_late_event": []}
    for kind in LineupEventKind:
        out[kind.value] = []
    for o in observations:
        lab = window_labels(events, decision_at=getattr(o, decision_attr),
                            game_id=getattr(o, game_attr))
        if lab["any_event"]:
            out["any_event"].append(o)
            for k in lab["kinds"]:
                out[k].append(o)
        else:
            out["no_event"].append(o)
        if lab["any_late_event"]:
            out["any_late_event"].append(o)
    return out
