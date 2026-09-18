"""Closing-line value (CLV) and point-in-time filtering of market observations.

Price convention: every price passed here is the YES price in cents (0-100), which is how Kalshi quotes.
A NO position is therefore held at ``100 - yes_price``. CLV is positive when the line moved in the position's
favour between entry and close.

"Closing" means the last observation STRICTLY before tip. Anything observed at or after tip is in-game
information and must never leak into pregame evaluation.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime
from typing import Any

from nba_edge.schemas.market import Side
from nba_edge.timeutil import parse_iso

_OBSERVED_KEYS = ("observed_at_utc", "observed_at", "_observed_at_utc")


def _side(side: Side | str) -> Side:
    return side if isinstance(side, Side) else Side(str(side).strip().lower())


def clv_cents(entry_price_cents: float, close_price_cents: float, side: Side | str) -> float:
    """Closing-line value in cents for a position entered at ``entry`` (YES price) and closing at ``close``.

    YES: ``close - entry``. NO: ``entry - close`` (the NO price rose iff the YES price fell).
    """
    for name, v in (("entry", entry_price_cents), ("close", close_price_cents)):
        if not 0 <= v <= 100:
            raise ValueError(f"{name} price must be in [0, 100] cents, got {v}")
    delta = float(close_price_cents - entry_price_cents)
    return delta if _side(side) == Side.YES else -delta


def clv_prob(entry_price_cents: float, close_price_cents: float, side: Side | str) -> float:
    """CLV as a probability difference in [-1, 1] (cents / 100)."""
    return clv_cents(entry_price_cents, close_price_cents, side) / 100.0


def observed_at(obs: Any) -> datetime:
    """Extract the observation instant from a MarketSnapshot-like object or a dict (must be tz-aware)."""
    if isinstance(obs, dict):
        for k in _OBSERVED_KEYS:
            if obs.get(k) is not None:
                v = obs[k]
                break
        else:
            raise KeyError(f"observation lacks one of {_OBSERVED_KEYS}")
    else:
        v = obs.observed_at_utc
    if isinstance(v, str):
        v = parse_iso(v)
    if v.tzinfo is None:
        raise ValueError("observation timestamp must be timezone-aware")
    return v


def _check_tip(tip_utc: datetime) -> None:
    if tip_utc.tzinfo is None:
        raise ValueError("tip_utc must be timezone-aware")


def pregame_filter(observations: Iterable[Any], tip_utc: datetime) -> tuple[list[Any], int]:
    """Keep observations strictly before tip; return ``(kept, dropped_count)``. Equal-to-tip is dropped."""
    _check_tip(tip_utc)
    kept: list[Any] = []
    dropped = 0
    for obs in observations:
        if observed_at(obs) < tip_utc:
            kept.append(obs)
        else:
            dropped += 1
    return kept, dropped


def closing_snapshot(observations: Sequence[Any], tip_utc: datetime) -> Any | None:
    """The latest observation strictly before tip, or None if there is none. Ties keep the last in input order."""
    kept, _ = pregame_filter(observations, tip_utc)
    if not kept:
        return None
    best = kept[0]
    for obs in kept[1:]:
        if observed_at(obs) >= observed_at(best):
            best = obs
    return best
