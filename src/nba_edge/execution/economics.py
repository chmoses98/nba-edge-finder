"""Fee-adjusted economics of one binary contract given a fair probability and a market snapshot.

Conventions
- Prices are Kalshi cents (1..99 executable). ``yes_bid`` / ``yes_ask`` / ``no_bid`` / ``no_ask`` may be
  ``None``; when the book is consistent ``no_ask = 100 - yes_bid`` and ``no_bid = 100 - yes_ask``, so a
  missing side is derived from the other. A bid of 0 or an ask of 100 means "no resting order" and is
  treated as missing.
- Two *expressions* of a view exist: buy YES at ``yes_ask`` (fair prob ``p``) or buy NO at ``no_ask`` (fair
  prob ``1 - p``). Both are evaluated; :attr:`ContractEconomics.best_side` is the higher fee-adjusted EV if
  it is positive and no blocking flag (missing quote, stale quote) is raised.
- Per-contract EV in dollars, taker fee charged at trade::

      EV = p_side * (1 - q) - (1 - p_side) * q - fee(q)  =  p_side - q - fee(q)

  with ``q = price / 100`` and ``fee`` the continuous quadratic fee (see :mod:`nba_edge.kalshi.fees`).
- A single binary market carries no overround to remove: the only "vig" is the bid/ask spread, so
  :func:`market_implied_probability` reports the midpoint plus the bid and ask probabilities and nothing
  is de-vigged.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from nba_edge.kalshi.fees import DEFAULT_SCHEDULE, FeeSchedule, fee_per_contract_dollars
from nba_edge.kalshi.normalize import market_to_cents

MIN_EXECUTABLE_CENTS = 1
MAX_EXECUTABLE_CENTS = 99


@dataclass(frozen=True)
class EconomicsConfig:
    """Thresholds and parameters for :func:`compute_economics`."""

    min_edge: float = 0.0  # minimum fee-adjusted EV per contract (dollars) for bet_up_to / best_side
    kelly_multiplier: float = 0.25  # fractional Kelly
    wide_spread_cents: int = 6  # spread strictly greater than this is flagged
    max_age_min: float = 15.0  # quotes older than this are stale
    min_liquidity_cents: int = 10_000  # Kalshi ``liquidity`` (cents) below this is thin
    min_volume: int = 10  # ``volume`` below this is thin
    taker: bool = True  # price as a taker (cross the spread); False uses maker fees


DEFAULT_CONFIG = EconomicsConfig()


@dataclass(frozen=True)
class Quotes:
    """Normalised two-sided book after deriving missing sides from the YES/NO identity."""

    yes_bid: int | None
    yes_ask: int | None
    no_bid: int | None
    no_ask: int | None

    @property
    def spread_cents(self) -> int | None:
        if self.yes_bid is None or self.yes_ask is None:
            return None
        return self.yes_ask - self.yes_bid


@dataclass(frozen=True)
class MarketImplied:
    """Market-implied probability of YES. No de-vig is applied (single binary market, spread only)."""

    p_mid: float | None
    p_market_bid: float | None
    p_market_ask: float | None
    source: str  # "mid" | "last" | "none"


@dataclass(frozen=True)
class SideEconomics:
    """Economics of buying one side (YES or NO) at its ask."""

    side: str  # "yes" | "no"
    p_fair: float  # fair probability that this side pays out
    price_cents: int | None
    implied_prob: float | None  # price / 100
    gross_edge: float | None  # p_fair - implied_prob
    fee_per_contract: float | None  # dollars, continuous quadratic fee at price
    ev_per_contract: float | None  # dollars, after fee
    roi: float | None  # ev_per_contract / price in dollars
    bet_up_to_cents: int | None  # max price with EV >= min_edge; None if no price qualifies
    kelly_full: float | None  # fraction of bankroll, 0 when EV <= 0
    kelly_fraction: float | None  # kelly_full * config.kelly_multiplier

    @property
    def executable(self) -> bool:
        return self.price_cents is not None


@dataclass
class ContractEconomics:
    """Both expressions of a contract plus quote-quality flags and a recommendation."""

    p_fair: float
    se: float
    quotes: Quotes
    market: MarketImplied
    yes: SideEconomics
    no: SideEconomics
    spread_cents: int | None
    wide_spread: bool
    no_quote: bool
    stale: bool
    thin: bool
    best_side: str | None  # "yes" | "no" | None
    reasons: list[str] = field(default_factory=list)

    def side(self, name: str) -> SideEconomics:
        if name == "yes":
            return self.yes
        if name == "no":
            return self.no
        raise ValueError(f"unknown side {name!r}")

    @property
    def best(self) -> SideEconomics | None:
        return self.side(self.best_side) if self.best_side else None


# ---- quotes ----------------------------------------------------------------------------------------


def _as_mapping(snapshot: Any) -> Mapping[str, Any]:
    if isinstance(snapshot, Mapping):
        return snapshot
    if hasattr(snapshot, "model_dump"):
        return snapshot.model_dump()
    raise TypeError(f"snapshot must be a mapping or pydantic model, got {type(snapshot).__name__}")


def _executable(price: Any) -> int | None:
    """Return the price as an int if it is an executable quote, else None (0 bid / 100 ask == empty)."""
    if price is None:
        return None
    try:
        p = int(price)
    except (TypeError, ValueError):
        return None
    return p if MIN_EXECUTABLE_CENTS <= p <= MAX_EXECUTABLE_CENTS else None


def _complement(price: int | None) -> int | None:
    return None if price is None else 100 - price


def normalize_quotes(snapshot: Any) -> Quotes:
    """Read the four quote fields and fill any missing side from ``no_ask = 100 - yes_bid`` etc.

    Explicit quotes win over derived ones; derivation only fills gaps.
    """
    snap = market_to_cents(_as_mapping(snapshot))
    yes_bid = _executable(snap.get("yes_bid"))
    yes_ask = _executable(snap.get("yes_ask"))
    no_bid = _executable(snap.get("no_bid"))
    no_ask = _executable(snap.get("no_ask"))
    if yes_bid is None:
        yes_bid = _complement(no_ask)
    if yes_ask is None:
        yes_ask = _complement(no_bid)
    if no_ask is None:
        no_ask = _complement(yes_bid)
    if no_bid is None:
        no_bid = _complement(yes_ask)
    return Quotes(yes_bid=yes_bid, yes_ask=yes_ask, no_bid=no_bid, no_ask=no_ask)


def market_implied_probability(snapshot: Any) -> MarketImplied:
    """Midpoint of yes_bid/yes_ask when both exist, else ``last_price``, else None.

    Also returns the bid- and ask-implied probabilities. There is deliberately no de-vig step: a single
    binary market has no overround beyond the spread itself.
    """
    snap = market_to_cents(_as_mapping(snapshot))
    q = normalize_quotes(snap)
    p_bid = None if q.yes_bid is None else q.yes_bid / 100.0
    p_ask = None if q.yes_ask is None else q.yes_ask / 100.0
    if p_bid is not None and p_ask is not None:
        return MarketImplied(p_mid=(p_bid + p_ask) / 2.0, p_market_bid=p_bid, p_market_ask=p_ask, source="mid")
    last = _executable(snap.get("last_price"))
    if last is not None:
        return MarketImplied(p_mid=last / 100.0, p_market_bid=p_bid, p_market_ask=p_ask, source="last")
    return MarketImplied(p_mid=None, p_market_bid=p_bid, p_market_ask=p_ask, source="none")


# ---- per-side math -----------------------------------------------------------------------------------


def ev_per_contract(p_side: float, price_cents: int | float, schedule: FeeSchedule, taker: bool = True) -> float:
    """Fee-adjusted expected value in dollars of buying one contract of a side with fair prob ``p_side``."""
    q = float(price_cents) / 100.0
    fee = fee_per_contract_dollars(price_cents, schedule, taker=taker)
    return p_side * (1.0 - q) - (1.0 - p_side) * q - fee


def kelly_fraction(p_side: float, price_cents: int | float, schedule: FeeSchedule, taker: bool = True) -> float:
    """Full Kelly fraction of bankroll for a binary bought at ``price`` with fee charged at trade.

    Cost per contract is ``q + fee``; a win returns 1. Kelly is ``EV / (1 - q - fee)``, clipped at zero.
    """
    q = float(price_cents) / 100.0
    fee = fee_per_contract_dollars(price_cents, schedule, taker=taker)
    net_win = 1.0 - q - fee
    if net_win <= 0.0:
        return 0.0
    ev = p_side * net_win - (1.0 - p_side) * (q + fee)
    return max(0.0, ev / net_win)


def bet_up_to_cents(
    p_side: float, schedule: FeeSchedule = DEFAULT_SCHEDULE, min_edge: float = 0.0, taker: bool = True
) -> int | None:
    """Highest integer price (1..99) at which fee-adjusted EV per contract is still >= ``min_edge``.

    EV is monotone decreasing in price on 1..99, so a downward scan returns the first qualifying price.
    Returns None when no price qualifies.
    """
    for c in range(MAX_EXECUTABLE_CENTS, MIN_EXECUTABLE_CENTS - 1, -1):
        if ev_per_contract(p_side, c, schedule, taker=taker) >= min_edge:
            return c
    return None


def side_economics(
    side: str,
    p_side: float,
    price_cents: int | None,
    schedule: FeeSchedule = DEFAULT_SCHEDULE,
    config: EconomicsConfig = DEFAULT_CONFIG,
) -> SideEconomics:
    """Economics of buying ``side`` at ``price_cents`` given the fair probability that the side wins."""
    up_to = bet_up_to_cents(p_side, schedule, config.min_edge, taker=config.taker)
    if price_cents is None:
        return SideEconomics(side, p_side, None, None, None, None, None, None, up_to, None, None)
    q = price_cents / 100.0
    fee = fee_per_contract_dollars(price_cents, schedule, taker=config.taker)
    ev = ev_per_contract(p_side, price_cents, schedule, taker=config.taker)
    k = kelly_fraction(p_side, price_cents, schedule, taker=config.taker)
    return SideEconomics(
        side=side,
        p_fair=p_side,
        price_cents=price_cents,
        implied_prob=q,
        gross_edge=p_side - q,
        fee_per_contract=fee,
        ev_per_contract=ev,
        roi=ev / q,
        bet_up_to_cents=up_to,
        kelly_full=k,
        kelly_fraction=k * config.kelly_multiplier,
    )


# ---- flags -------------------------------------------------------------------------------------------


def _is_stale(observed_at: datetime | None, now: datetime | None, max_age_min: float) -> bool:
    if observed_at is None:
        return False
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=UTC)
    now = now or datetime.now(UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    return (now - observed_at).total_seconds() > max_age_min * 60.0


def _is_thin(snap: Mapping[str, Any], config: EconomicsConfig) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    liquidity = snap.get("liquidity")
    volume = snap.get("volume")
    if liquidity is not None and liquidity < config.min_liquidity_cents:
        reasons.append(f"thin: liquidity {liquidity}c < {config.min_liquidity_cents}c")
    if volume is not None and volume < config.min_volume:
        reasons.append(f"thin: volume {volume} < {config.min_volume}")
    return bool(reasons), reasons


def _pick_best(yes: SideEconomics, no: SideEconomics, min_edge: float) -> SideEconomics | None:
    """Side with the highest fee-adjusted EV, provided that EV is > 0 and >= ``min_edge``."""
    candidates = [
        s
        for s in (yes, no)
        if s.ev_per_contract is not None and s.ev_per_contract > 0.0 and s.ev_per_contract >= min_edge
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda s: s.ev_per_contract or 0.0)


# ---- entry point -------------------------------------------------------------------------------------


def compute_economics(
    snapshot: Any,
    p_fair: float,
    se: float = 0.0,
    *,
    schedule: FeeSchedule = DEFAULT_SCHEDULE,
    config: EconomicsConfig = DEFAULT_CONFIG,
    observed_at: datetime | None = None,
    now: datetime | None = None,
) -> ContractEconomics:
    """Evaluate buying YES at ``yes_ask`` and buying NO at ``no_ask`` for fair ``P(YES) = p_fair``.

    ``observed_at`` (or ``observed_at_utc`` on the snapshot) drives the ``stale`` flag; ``now`` defaults to the
    current UTC time and exists for deterministic tests.
    """
    if not 0.0 <= p_fair <= 1.0:
        raise ValueError(f"p_fair must be in [0, 1], got {p_fair}")
    snap = _as_mapping(snapshot)
    quotes = normalize_quotes(snap)
    market = market_implied_probability(snap)
    yes = side_economics("yes", p_fair, quotes.yes_ask, schedule, config)
    no = side_economics("no", 1.0 - p_fair, quotes.no_ask, schedule, config)

    reasons: list[str] = []
    no_quote = quotes.yes_ask is None or quotes.no_ask is None
    if no_quote:
        missing = [s for s, px in (("yes_ask", quotes.yes_ask), ("no_ask", quotes.no_ask)) if px is None]
        reasons.append(f"no_quote: missing {', '.join(missing)}")
    spread = quotes.spread_cents
    wide = spread is not None and spread > config.wide_spread_cents
    if wide:
        reasons.append(f"wide_spread: {spread}c > {config.wide_spread_cents}c")
    observed = observed_at if observed_at is not None else snap.get("observed_at_utc")
    stale = _is_stale(observed, now, config.max_age_min)
    if stale:
        reasons.append(f"stale: quote older than {config.max_age_min:g} min")
    thin, thin_reasons = _is_thin(snap, config)
    reasons.extend(thin_reasons)

    best = None if stale else _pick_best(yes, no, config.min_edge)
    if best is not None:
        reasons.append(f"best_side={best.side}: ev {best.ev_per_contract:.4f}/contract")
    elif not stale:
        reasons.append("no_edge: no side has fee-adjusted EV above min_edge")

    return ContractEconomics(
        p_fair=p_fair,
        se=se,
        quotes=quotes,
        market=market,
        yes=yes,
        no=no,
        spread_cents=spread,
        wide_spread=wide,
        no_quote=no_quote,
        stale=stale,
        thin=thin,
        best_side=None if best is None else best.side,
        reasons=reasons,
    )
