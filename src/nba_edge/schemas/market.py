from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field

from nba_edge.schemas.core import Strict


class Side(StrEnum):
    YES = "yes"
    NO = "no"


class MarketSnapshot(Strict):
    """One observation of one Kalshi market at one instant. Prices in cents (0-100) as Kalshi reports."""
    ticker: str
    event_ticker: str
    series_ticker: str
    observed_at_utc: datetime
    status: str
    title: str
    yes_sub_title: str | None = None
    no_sub_title: str | None = None
    market_type: str | None = None
    strike_type: str | None = None
    floor_strike: float | None = None
    cap_strike: float | None = None
    custom_strike: dict[str, Any] | None = None
    yes_bid: int | None = None
    yes_ask: int | None = None
    no_bid: int | None = None
    no_ask: int | None = None
    last_price: int | None = None
    volume: int | None = None
    volume_24h: int | None = None
    open_interest: int | None = None
    liquidity: int | None = None
    open_time_utc: datetime | None = None
    close_time_utc: datetime | None = None
    expected_expiration_utc: datetime | None = None
    result: str | None = None
    rules_primary: str | None = None
    orderbook_yes: list[list[int]] | None = None  # [[price_cents, qty], ...] bids on YES
    orderbook_no: list[list[int]] | None = None  # bids on NO
    raw: dict[str, Any] = Field(default_factory=dict)


class Contract(Strict):
    """Our semantic reading of a market: what quantity, what threshold, what side means what."""
    ticker: str
    family: str
    scope: str  # game | player | season | other
    stat: str | None
    period: str
    game_id: str | None = None
    team_id: int | None = None  # the team the YES side refers to (winner/spread/team total)
    nba_id: int | None = None
    threshold: float | None = None  # YES iff stat >= threshold (we normalise 'over X' to >= X+0.5 semantics explicitly)
    comparator: str | None = None  # 'ge' | 'gt' | 'le' | 'lt' | 'eq' | 'in_range'
    upper: float | None = None  # for ranges
    support: str = "UNRESOLVED"
    semantics_confidence: str = "low"
    notes: list[str] = Field(default_factory=list)
    entity_name: str | None = None  # player display name as Kalshi prints it (identity resolution input)
    kalshi_entity_uuid: str | None = None  # Kalshi's stable player/team uuid from custom_strike
