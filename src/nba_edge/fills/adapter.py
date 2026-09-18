"""Canonical fill ingestion for Kalshi fills (the seam the cross-sport importer will use).

* ``normalize_kalshi_fill``       raw Kalshi fill dict -> ``Fill`` (tolerant to missing fields; strict on side/action)
* ``route_fills``                 split fills into NBA (series in the ontology) vs ``routed_elsewhere``
* ``positions_from_fills``        net buys/sells per (ticker, side) with an average entry price
* ``import_fills_jsonl``          append normalised fills to ledger kind ``fills`` deduped by ``fill_id``
* ``match_fills_to_predictions``  join each fill to the latest prediction that was live when it happened

Price convention: ``Fill.price_cents`` is the price paid for the side actually traded (YES price for a YES
fill, NO price for a NO fill), in cents.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from collections.abc import Iterable, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from nba_edge.archive.ledger import Ledger
from nba_edge.kalshi.ontology import Ontology
from nba_edge.kalshi.ticker import split_ticker
from nba_edge.log import get_logger, kv
from nba_edge.schemas.fills import Fill, FillAction, Position
from nba_edge.timeutil import iso, parse_iso, utcnow

log = get_logger(__name__)

_SIDES = {"yes", "no"}
_ONTOLOGY: Ontology | None = None


def _ontology(onto: Ontology | None = None) -> Ontology:
    global _ONTOLOGY
    if onto is not None:
        return onto
    if _ONTOLOGY is None:
        _ONTOLOGY = Ontology.load()
    return _ONTOLOGY


def is_nba_ticker(ticker: str, ontology: Ontology | None = None) -> bool:
    """True when the ticker's series maps to a family in the NBA market ontology."""
    series, _, _ = split_ticker(ticker or "")
    return bool(series) and _ontology(ontology).family_for_series(series) is not None


# ---- normalisation ----------------------------------------------------------------------------------


def _cents(v: Any) -> int | None:
    """Kalshi sends cents as ints, occasionally as strings; ``*_dollars`` fields are decimal strings."""
    if v is None or v == "":
        return None
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return None


def _dollars_to_cents(v: Any) -> int | None:
    if v is None or v == "":
        return None
    try:
        return int(round(float(v) * 100))
    except (TypeError, ValueError):
        return None


def _ts(raw: dict[str, Any]) -> datetime:
    for k in ("created_time", "created_at", "ts", "ts_utc", "time"):
        v = raw.get(k)
        if v:
            try:
                return parse_iso(str(v))
            except ValueError as e:
                raise ValueError(f"fill timestamp {k}={v!r} unparseable") from e
    raise ValueError("fill has no timestamp (created_time)")


def _synthetic_id(raw: dict[str, Any], ts: datetime) -> str:
    key = "|".join(str(raw.get(k, "")) for k in ("order_id", "ticker", "action", "side", "yes_price", "no_price", "price", "count")) + "|" + iso(ts)
    return "synthetic:" + hashlib.sha256(key.encode()).hexdigest()[:24]


def normalize_kalshi_fill(raw: dict[str, Any]) -> Fill:
    """Kalshi fill object -> ``Fill``. Raises ``ValueError`` on unknown ``side``/``action`` or when the ticker,
    timestamp or price cannot be determined; every other field is optional."""
    ticker = raw.get("ticker")
    if not ticker:
        raise ValueError("fill has no ticker")
    action = str(raw.get("action") or "").strip().lower()
    if action not in (FillAction.BUY.value, FillAction.SELL.value):
        raise ValueError(f"unknown fill action {raw.get('action')!r}")
    side = str(raw.get("side") or "").strip().lower()
    if side not in _SIDES:
        raise ValueError(f"unknown fill side {raw.get('side')!r}")
    ts = _ts(raw)
    if side == "yes":
        price = _cents(raw.get("yes_price"))
        price = price if price is not None else _dollars_to_cents(raw.get("yes_price_dollars"))
    else:
        price = _cents(raw.get("no_price"))
        price = price if price is not None else _dollars_to_cents(raw.get("no_price_dollars"))
    if price is None:
        price = _cents(raw.get("price"))
    if price is None:
        raise ValueError("fill has no price (yes_price / no_price / price)")
    if not 0 <= price <= 100:
        raise ValueError(f"fill price {price} outside 0..100 cents")
    fill_id = raw.get("trade_id") or raw.get("fill_id") or raw.get("id") or _synthetic_id(raw, ts)
    fee = _cents(raw.get("fee_cents"))
    if fee is None:
        fee = _dollars_to_cents(raw.get("fee_dollars")) or _cents(raw.get("fee")) or 0
    is_taker = raw.get("is_taker")
    return Fill(
        fill_id=str(fill_id), order_id=(str(raw["order_id"]) if raw.get("order_id") else None), ticker=str(ticker), ts_utc=ts,
        action=FillAction(action), side=side, price_cents=int(price), count=int(_cents(raw.get("count")) or 0), fee_cents=int(fee),
        is_taker=None if is_taker is None else bool(is_taker), source=str(raw.get("source") or "kalshi"),
    )


def route_fills(fills: Iterable[Fill], ontology: Ontology | None = None) -> tuple[list[Fill], list[Fill]]:
    """``(nba, routed_elsewhere)``: only tickers whose series is in the NBA ontology are ours."""
    nba: list[Fill] = []
    other: list[Fill] = []
    for f in fills:
        (nba if is_nba_ticker(f.ticker, ontology) else other).append(f)
    return nba, other


# ---- positions --------------------------------------------------------------------------------------


def position_key(ticker: str, side: str) -> str:
    return f"{ticker}:{side}"


def positions_from_fills(fills: Sequence[Fill], as_of: datetime | None = None, warnings: list[str] | None = None, strict: bool = False) -> dict[str, Position]:
    """Net open positions per ``ticker:side`` from fills at or before ``as_of``.

    Buys add contracts at their price; sells reduce ``net_contracts`` at the running average (average entry
    price is unchanged by a partial sell). A sell larger than the open quantity is clipped and reported in
    ``warnings`` (or raises ``ValueError`` when ``strict``). Positions that net to zero are still returned
    (with ``net_contracts=0``) so realised trades stay visible.
    """
    as_of = as_of or utcnow()
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    warnings = warnings if warnings is not None else []
    groups: dict[str, list[Fill]] = {}
    for f in fills:
        if f.ts_utc <= as_of:
            groups.setdefault(position_key(f.ticker, f.side), []).append(f)
    out: dict[str, Position] = {}
    for key, fs in groups.items():
        fs.sort(key=lambda f: (f.ts_utc, f.fill_id))
        net, cost, fees = 0, 0.0, 0
        for f in fs:
            fees += f.fee_cents
            if f.action == FillAction.BUY:
                net += f.count
                cost += f.price_cents * f.count
            else:
                if f.count > net:
                    msg = f"{key}: sell of {f.count} exceeds open {net} at {iso(f.ts_utc)} (fill {f.fill_id}); clipped"
                    if strict:
                        raise ValueError(msg)
                    warnings.append(msg)
                    log.warning(kv(event="fill_oversell", key=key, fill_id=f.fill_id))
                sold = min(f.count, net)
                avg = cost / net if net else 0.0
                cost -= avg * sold
                net -= sold
        out[key] = Position(
            ticker=fs[0].ticker, side=fs[0].side, net_contracts=net, avg_price_cents=(cost / net) if net else 0.0, total_fees_cents=fees, fills=list(fs), as_of_utc=as_of,
        )
    return out


# ---- ledger import ----------------------------------------------------------------------------------


def _read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                obj = json.loads(line)
                if isinstance(obj, dict) and isinstance(obj.get("fills"), list):
                    yield from obj["fills"]
                elif isinstance(obj, dict):
                    yield obj


def _to_fill(obj: dict[str, Any]) -> Fill:
    """Accept both raw Kalshi shapes and already-normalised ``Fill`` rows (e.g. our own ledger rows)."""
    if "fill_id" in obj and "ts_utc" in obj and "price_cents" in obj:
        return Fill(**{k: v for k, v in obj.items() if k in Fill.model_fields})
    return normalize_kalshi_fill(obj)


def existing_fill_ids(ledger: Ledger) -> set[str]:
    return {str(r["fill_id"]) for r in ledger.iter_rows("fills") if r.get("fill_id")}


def import_fills_jsonl(
    path: Path, ledger: Ledger, routed_elsewhere: list[Fill] | None = None, rejected: list[dict[str, str]] | None = None,
    ontology: Ontology | None = None, now: datetime | None = None,
) -> int:
    """Append NBA fills from a JSONL(.gz) file to ledger kind ``fills``, deduping by ``fill_id`` against rows
    already archived (and within the file). Non-NBA fills are collected in ``routed_elsewhere``; rows that fail
    normalisation land in ``rejected`` with a reason. Returns the number of rows appended."""
    path = Path(path)
    seen = existing_fill_ids(ledger)
    new_rows: list[dict[str, Any]] = []
    for obj in _read_jsonl(path):
        try:
            fill = _to_fill(obj)
        except (ValueError, TypeError) as e:
            if rejected is not None:
                rejected.append({"raw": json.dumps(obj, default=str)[:300], "reason": str(e)[:200]})
            log.warning(kv(event="fill_rejected", reason=str(e)[:120]))
            continue
        if not is_nba_ticker(fill.ticker, ontology):
            if routed_elsewhere is not None:
                routed_elsewhere.append(fill)
            continue
        if fill.fill_id in seen:
            continue
        seen.add(fill.fill_id)
        new_rows.append(fill.model_dump(mode="json"))
    if new_rows:
        e = ledger.append_rows("fills", new_rows, observed_at=now or utcnow(), meta={"source_file": path.name, "n": len(new_rows)})
        log.info(kv(event="fills_written", path=e.path, rows=e.rows))
    return len(new_rows)


# ---- matching ----------------------------------------------------------------------------------------


def _pred_dict(p: Any) -> dict[str, Any]:
    return p if isinstance(p, dict) else p.model_dump(mode="json")


def _pred_ts(p: dict[str, Any]) -> datetime | None:
    v = p.get("predicted_at_utc")
    if v is None:
        return None
    return v if isinstance(v, datetime) else parse_iso(str(v))


def implied_edge(fill: Fill, p_yes: float | None) -> float | None:
    """Model edge in probability units for the side traded: buys gain when the model's side probability exceeds
    the price paid, sells gain when it is below."""
    if p_yes is None:
        return None
    p_side = p_yes if fill.side == "yes" else 1.0 - p_yes
    price = fill.price_cents / 100.0
    return (p_side - price) if fill.action == FillAction.BUY else (price - p_side)


def match_fills_to_predictions(fills: Iterable[Fill], predictions: Iterable[Any], ontology: Ontology | None = None) -> dict[str, list[dict[str, Any]]]:
    """Join fills to the latest prediction (by ``predicted_at_utc <= fill.ts_utc``) for the same ticker.

    Returns ``{"matched": [...], "unmatched": [...], "routed_elsewhere": [...]}``. Each matched row carries the
    prediction id, ``p_production`` at that time, the price paid and the implied edge.
    """
    by_ticker: dict[str, list[tuple[datetime, dict[str, Any]]]] = {}
    for p in predictions:
        d = _pred_dict(p)
        ts = _pred_ts(d)
        if ts is None or not d.get("ticker"):
            continue
        by_ticker.setdefault(str(d["ticker"]), []).append((ts, d))
    for lst in by_ticker.values():
        lst.sort(key=lambda t: t[0])

    nba, other = route_fills(fills, ontology)
    matched: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    for f in nba:
        cands = by_ticker.get(f.ticker)
        if not cands:
            unmatched.append({"fill_id": f.fill_id, "ticker": f.ticker, "reason": "no_prediction_for_ticker"})
            continue
        live = [d for ts, d in cands if ts <= f.ts_utc]
        if not live:
            unmatched.append({"fill_id": f.fill_id, "ticker": f.ticker, "reason": "no_prediction_before_fill"})
            continue
        d = live[-1]
        p = d.get("p_production")
        matched.append({
            "fill_id": f.fill_id, "ticker": f.ticker, "prediction_id": d.get("prediction_id"), "predicted_at_utc": iso(_pred_ts(d)), "fill_ts_utc": iso(f.ts_utc),
            "action": f.action.value, "side": f.side, "count": f.count, "price_cents": f.price_cents, "p_production": p, "p_market": d.get("p_market"),
            "implied_edge": implied_edge(f, None if p is None else float(p)), "family": d.get("family"), "model_version": d.get("model_version"),
        })
    return {
        "matched": matched, "unmatched": unmatched,
        "routed_elsewhere": [{"fill_id": f.fill_id, "ticker": f.ticker, "reason": "series_not_in_nba_ontology"} for f in other],
    }
