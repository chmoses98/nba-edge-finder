"""Normalise Kalshi market objects to the internal cents convention.

Kalshi's API (both live and historical hosts, observed 2026-09-18) reports prices as dollar strings
(``yes_bid_dollars='0.5300'``), sizes/volumes as fixed-point strings (``volume_fp='5679.29'``) and keeps legacy
integer-cent fields only on older payloads. Internally we use integer cents (1..99) for prices and floats for
sizes. ``market_to_cents`` returns a *new* dict with the canonical keys filled from whichever representation is
present; the raw object is never mutated (the archive stores what Kalshi said).
"""

from __future__ import annotations

from typing import Any

PRICE_KEYS = ("yes_bid", "yes_ask", "no_bid", "no_ask", "last_price", "previous_price", "previous_yes_bid", "previous_yes_ask", "settlement_value")
SIZE_KEYS = {"volume": "volume_fp", "volume_24h": "volume_24h_fp", "open_interest": "open_interest_fp", "yes_bid_size": "yes_bid_size_fp", "yes_ask_size": "yes_ask_size_fp"}


def _to_cents(v: Any) -> int | None:
    if v is None or v == "":
        return None
    try:
        return int(round(float(v) * 100))
    except (TypeError, ValueError):
        return None


def _to_float(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def market_to_cents(m: dict[str, Any]) -> dict[str, Any]:
    out = dict(m)
    for k in PRICE_KEYS:
        if out.get(k) is None and m.get(f"{k}_dollars") is not None:
            out[k] = _to_cents(m[f"{k}_dollars"])
        elif out.get(k) is not None:
            try:
                out[k] = int(out[k])
            except (TypeError, ValueError):
                out[k] = None
    for k, fp in SIZE_KEYS.items():
        if out.get(k) is None and m.get(fp) is not None:
            out[k] = _to_float(m[fp])
    if out.get("liquidity") is None and m.get("liquidity_dollars") is not None:
        out["liquidity"] = _to_cents(m["liquidity_dollars"])
    return out


def quote_cents(m: dict[str, Any]) -> dict[str, int | None]:
    """Just the four executable quotes + last price, in cents (None when absent or degenerate 0/100)."""
    c = market_to_cents(m)
    q = {k: c.get(k) for k in ("yes_bid", "yes_ask", "no_bid", "no_ask", "last_price")}
    for k in ("yes_bid", "no_bid"):
        if q[k] == 0:
            q[k] = None
    for k in ("yes_ask", "no_ask"):
        if q[k] == 100:
            q[k] = None
    return q


def _level_cents(level: Any) -> tuple[int, float] | None:
    """A level is [price, qty] with price in cents (int) or dollars (str/float <= 1), or a dict with price/quantity keys."""
    if isinstance(level, dict):
        price = level.get("price") or level.get("price_dollars") or level.get("yes_price") or level.get("no_price")
        qty = level.get("quantity") or level.get("count") or level.get("size") or level.get("quantity_fp") or 0
    elif isinstance(level, (list, tuple)) and len(level) >= 2:
        price, qty = level[0], level[1]
    else:
        return None
    try:
        pf = float(price)
        q = float(qty)
    except (TypeError, ValueError):
        return None
    cents = int(round(pf * 100)) if pf <= 1.0 and not float(pf).is_integer() or (isinstance(price, str) and "." in price) else int(round(pf))
    if isinstance(price, str) and "." in price:
        cents = int(round(pf * 100))
    return cents, q


def orderbook_levels(body: dict[str, Any]) -> dict[str, list[list[float]]]:
    """Normalise an order-book response to {'yes': [[price_cents, qty], ...], 'no': [...]} (bids, best first)."""
    ob = body.get("orderbook") if isinstance(body.get("orderbook"), dict) else body
    out: dict[str, list[list[float]]] = {"yes": [], "no": []}
    for side in ("yes", "no"):
        raw = ob.get(side)
        if raw is None:
            raw = ob.get(f"{side}_dollars")
        if raw is None:
            raw = ob.get(f"{side}_levels")
        for lv in raw or []:
            parsed = _level_cents(lv)
            if parsed is not None:
                out[side].append([parsed[0], parsed[1]])
        out[side].sort(key=lambda x: -x[0])
    return out
