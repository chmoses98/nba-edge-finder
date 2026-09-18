"""Kalshi trading fees.

Kalshi charges a fee on every *trade* (not on settlement). For the standard "quadratic" schedule the fee on an
order of ``C`` contracts filled at price ``P`` dollars (``price_cents / 100``) is::

    fee_dollars = multiplier * C * P * (1 - P)
    fee_cents   = ceil(fee_dollars * 100)          # rounded UP to the next cent, on the whole order

with ``multiplier = 0.07`` for taker orders and ``0.0175`` for resting (maker) orders on the general schedule.
Because rounding happens once per order, ten contracts at 50c cost 18c (ceil 17.5), not 10 x 2c.

Series can carry their own ``fee_type`` / ``fee_multiplier``. The public API is not explicit about the unit of
``fee_multiplier`` so :meth:`FeeSchedule.from_series` applies a documented heuristic and records which
interpretation it used in :attr:`FeeSchedule.source`.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

BASE_TAKER_MULTIPLIER = 0.07
BASE_MAKER_MULTIPLIER = 0.0175
MAKER_TO_TAKER_RATIO = BASE_MAKER_MULTIPLIER / BASE_TAKER_MULTIPLIER  # 0.25

# ``fee_multiplier`` values strictly below this are read as an absolute per-trade rate (0.07 == 7%).
# Values in [ABSOLUTE_RATE_CEILING, MULTIPLE_OF_BASE_CEILING] are read as multiples of the base 0.07.
ABSOLUTE_RATE_CEILING = 0.25
MULTIPLE_OF_BASE_CEILING = 2.0

_FLOAT_TOLERANCE_DIGITS = 9


@dataclass(frozen=True)
class FeeSchedule:
    """Fee parameters for one series (or the general schedule when ``series_ticker`` is None).

    ``source`` documents where the multipliers came from:
    ``"default"``, ``"series:multiple_of_base"``, ``"series:absolute_rate"`` or
    ``"default:ignored_out_of_range"``.
    """

    taker_multiplier: float = BASE_TAKER_MULTIPLIER
    maker_multiplier: float = BASE_MAKER_MULTIPLIER
    fee_type: str = "quadratic"
    series_ticker: str | None = None
    source: str = "default"

    @classmethod
    def from_series(cls, series: Mapping[str, Any] | None) -> FeeSchedule:
        """Build a schedule from a Kalshi series object (``fee_type``, ``fee_multiplier``, ``ticker``).

        Heuristic for ``fee_multiplier`` (documented because the API does not state its unit):

        * ``None`` / missing / non-positive  -> general schedule (0.07 / 0.0175), ``source="default"``.
        * ``0 < value < 0.25``               -> an absolute taker rate such as ``0.07`` or ``0.035``; the maker
          rate is scaled by the same 1:4 ratio as the general schedule. ``source="series:absolute_rate"``.
        * ``0.25 <= value <= 2.0``           -> a multiple of the base rate (``1.0`` == general schedule,
          ``0.5`` == half fees, ``2.0`` == double). ``source="series:multiple_of_base"``.
        * ``value > 2.0``                    -> neither interpretation is credible; fall back to the general
          schedule and flag it via ``source="default:ignored_out_of_range"`` so it shows up in reports.
        """
        if not series:
            return cls()
        ticker = series.get("ticker") or series.get("series_ticker")
        fee_type = str(series.get("fee_type") or "quadratic")
        raw = series.get("fee_multiplier")
        try:
            value = float(raw) if raw is not None else None
        except (TypeError, ValueError):
            value = None
        if value is None or value <= 0 or math.isnan(value):
            return cls(fee_type=fee_type, series_ticker=ticker, source="default")
        if value < ABSOLUTE_RATE_CEILING:
            return cls(
                taker_multiplier=value,
                maker_multiplier=value * MAKER_TO_TAKER_RATIO,
                fee_type=fee_type,
                series_ticker=ticker,
                source="series:absolute_rate",
            )
        if value <= MULTIPLE_OF_BASE_CEILING:
            return cls(
                taker_multiplier=BASE_TAKER_MULTIPLIER * value,
                maker_multiplier=BASE_MAKER_MULTIPLIER * value,
                fee_type=fee_type,
                series_ticker=ticker,
                source="series:multiple_of_base",
            )
        return cls(fee_type=fee_type, series_ticker=ticker, source="default:ignored_out_of_range")

    def multiplier(self, taker: bool = True) -> float:
        return self.taker_multiplier if taker else self.maker_multiplier


DEFAULT_SCHEDULE = FeeSchedule()


def _validate(price_cents: int, contracts: int) -> None:
    if not 0 <= price_cents <= 100:
        raise ValueError(f"price_cents must be in [0, 100], got {price_cents}")
    if contracts < 0:
        raise ValueError(f"contracts must be non-negative, got {contracts}")


def _order_fee_cents(price_cents: int, contracts: int, multiplier: float) -> int:
    """Whole-order fee in cents, rounded up to the next cent.

    Only the quadratic formula is implemented; any other ``fee_type`` is priced with it as well (the standard
    schedule is the only one Kalshi documents publicly), which is the conservative choice for NBA series.
    """
    _validate(price_cents, contracts)
    if contracts == 0:
        return 0
    p = price_cents / 100.0
    raw = multiplier * contracts * p * (1.0 - p) * 100.0
    # Guard against binary float noise (e.g. 17.500000000000004) pushing an exact half-cent up a whole cent.
    return math.ceil(round(raw, _FLOAT_TOLERANCE_DIGITS))


def taker_fee_cents(price_cents: int, contracts: int, schedule: FeeSchedule = DEFAULT_SCHEDULE) -> int:
    """Fee for an order that crosses the spread (takes liquidity), in cents, on the whole order."""
    return _order_fee_cents(price_cents, contracts, schedule.taker_multiplier)


def maker_fee_cents(price_cents: int, contracts: int, schedule: FeeSchedule = DEFAULT_SCHEDULE) -> int:
    """Fee for a resting order that gets filled (provides liquidity), in cents, on the whole order."""
    return _order_fee_cents(price_cents, contracts, schedule.maker_multiplier)


def fee_per_contract_dollars(
    price_cents: int | float, schedule: FeeSchedule = DEFAULT_SCHEDULE, taker: bool = True
) -> float:
    """Continuous (un-rounded) fee per contract in dollars: ``multiplier * P * (1 - P)``.

    Used for expected-value math where the per-order ceiling would introduce an artificial size dependence.
    For real orders use :func:`taker_fee_cents` / :func:`maker_fee_cents`.
    """
    p = float(price_cents) / 100.0
    if not 0.0 <= p <= 1.0:
        raise ValueError(f"price_cents must be in [0, 100], got {price_cents}")
    return schedule.multiplier(taker) * p * (1.0 - p)
