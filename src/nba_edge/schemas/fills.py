"""Canonical placed-bet / fill records for future integration with the cross-sport Kalshi fill importer.
Kept deliberately close to Kalshi's own fill/order vocabulary so the external ledger maps 1:1."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import Field

from nba_edge.schemas.core import Strict


class FillAction(StrEnum):
    BUY = "buy"
    SELL = "sell"


class Fill(Strict):
    fill_id: str
    order_id: str | None
    ticker: str
    ts_utc: datetime
    action: FillAction
    side: str  # yes | no
    price_cents: int
    count: int
    fee_cents: int = 0
    is_taker: bool | None = None
    source: str = "kalshi"


class Position(Strict):
    ticker: str
    side: str
    net_contracts: int
    avg_price_cents: float
    total_fees_cents: int
    fills: list[Fill] = Field(default_factory=list)
    as_of_utc: datetime
