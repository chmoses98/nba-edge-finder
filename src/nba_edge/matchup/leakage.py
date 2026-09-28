"""Point-in-time guards for matchup data.

Matchup inputs are unusually easy to leak with, because the most informative version of them --
confirmed starters, actual defensive assignments -- only exists *after* the moment a forecast would
have been made. A model trained or evaluated on those is measuring hindsight, and it will look
excellent until it is asked to predict something.

So the rules are enforced here rather than left to each caller:

* a context may inform a decision only if it was observed at or before that decision's instant;
* a context counts as pregame only if it was observed strictly before tip;
* when several contexts qualify, the newest qualifying one wins -- never the newest overall.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from nba_edge.matchup.schemas import GameMatchupContext


class MatchupLeakageError(RuntimeError):
    """A matchup record was used at an instant it could not have been known at."""


def is_knowable_at(context: GameMatchupContext, decision_at: datetime) -> bool:
    return context.observed_at_utc <= decision_at


def is_pregame(context: GameMatchupContext, tip_utc: datetime | None = None) -> bool:
    """Strictly before tip. Equality is not pregame: a context stamped at tip already saw it."""
    tip = tip_utc or context.tip_utc
    if tip is None:
        return False
    return context.observed_at_utc < tip


def assert_usable(context: GameMatchupContext, decision_at: datetime,
                  tip_utc: datetime | None = None, *, require_pregame: bool = True) -> None:
    """Fail closed if a context could not have been known, or is not pregame when required."""
    if not is_knowable_at(context, decision_at):
        raise MatchupLeakageError(
            f"matchup context for {context.game_id} was observed at {context.observed_at_utc.isoformat()}, "
            f"after the decision instant {decision_at.isoformat()}; using it would leak the future"
        )
    if require_pregame:
        tip = tip_utc or context.tip_utc
        if tip is None:
            raise MatchupLeakageError(
                f"matchup context for {context.game_id} carries no tip time, so it cannot be shown "
                f"to be pregame; refusing rather than assuming"
            )
        if not is_pregame(context, tip):
            raise MatchupLeakageError(
                f"matchup context for {context.game_id} was observed at {context.observed_at_utc.isoformat()}, "
                f"at or after tip {tip.isoformat()}; it is not pregame"
            )


def latest_knowable(contexts: Iterable[GameMatchupContext], decision_at: datetime,
                    *, require_pregame: bool = True,
                    tip_utc: datetime | None = None) -> GameMatchupContext | None:
    """The newest context that was already observable at ``decision_at``.

    Filters first and maximises second. Maximising first and filtering after is the classic way this
    goes wrong: it silently returns nothing when the newest context is in the future, instead of the
    best one that actually existed.
    """
    eligible = []
    for c in contexts:
        if not is_knowable_at(c, decision_at):
            continue
        if require_pregame and not is_pregame(c, tip_utc or c.tip_utc):
            continue
        eligible.append(c)
    return max(eligible, key=lambda c: c.observed_at_utc) if eligible else None
