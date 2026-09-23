"""Kalshi NBA market capture job: snapshot every NBA market (all series in the catalog, plus a live series
re-scan so new families are not missed) into the append-only ledger.

Pregame vs post-tip labelling is NOT done here: snapshots are frozen with their observation time, and the
evaluation layer labels them later against the authoritative tip time. That keeps capture dumb and immutable.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from nba_edge.archive.ledger import Ledger
from nba_edge.archive.status import status_age_minutes
from nba_edge.config import settings
from nba_edge.kalshi.client import KalshiClient, KalshiError
from nba_edge.kalshi.discovery import is_nba_series
from nba_edge.kalshi.normalize import orderbook_levels, quote_cents
from nba_edge.kalshi.ontology import Ontology, Support, classify_market
from nba_edge.log import get_logger, kv
from nba_edge.timeutil import iso, utcnow

log = get_logger(__name__)


def nba_series_tickers(client: KalshiClient, catalog_dir: Path) -> list[str]:
    tickers: set[str] = set()
    summ = catalog_dir / "discovery_summary.json"
    if summ.exists():
        try:
            for s in json.loads(summ.read_text()).get("nba_series", []):
                tickers.add(s["ticker"])
        except (json.JSONDecodeError, KeyError) as e:
            log.warning(kv(event="catalog_unreadable", err=str(e)))
    try:
        for s in client.iter_series():
            ok, _ = is_nba_series(s)
            if ok:
                tickers.add(s["ticker"])
    except KalshiError as e:
        log.warning(kv(event="series_rescan_failed", err=str(e)[:200]))
    return sorted(tickers)


def snapshot_markets(client: KalshiClient, series: list[str], statuses: list[str], ontology: Ontology) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for st in series:
        for status in statuses:
            try:
                for m in client.iter_markets(series_ticker=st, status=status, max_pages=20):
                    tk = m.get("ticker")
                    if not tk or tk in seen:
                        continue
                    seen.add(tk)
                    m.setdefault("series_ticker", st)
                    cls = classify_market(m, ontology)
                    m["_family"] = cls.family
                    m["_support"] = str(cls.support)
                    m["_quote_cents"] = quote_cents(m)  # canonical cents view; raw dollar fields kept verbatim
                    rows.append(m)
            except KalshiError as e:
                log.warning(kv(event="capture_series_error", series=st, status=status, err=str(e)[:160]))
                rows.append({"_error": str(e)[:300], "series_ticker": st, "status_requested": status})
    return rows


LIVE_STATUSES = {"open", "active"}  # Kalshi's filter param says 'open'; the market object says 'active'


_SUPPORT_RANK = {
    Support.MODELABLE: 0, Support.BUILDABLE: 1, Support.RESEARCH: 2, Support.UNRESOLVED: 2, Support.UNMODELABLE: 3,
}
_UNKNOWN_SUPPORT_RANK = 2


def _priority(m: dict[str, Any]) -> tuple[int, int, str]:
    """Modelable families first, then quoted markets, then earliest expected expiration."""
    q = m.get("_quote_cents") or {}
    quoted = 0 if (q.get("yes_bid") or q.get("yes_ask")) else 1
    raw = m.get("_support")
    # Support.parse accepts names persisted before the MODELABLE rename, so archived rows keep
    # ranking correctly. An unrecognised state used to fall silently to rank 2, which is how a
    # future rename would quietly demote every modelable market without anyone noticing.
    state = Support.parse(raw)
    if state is None:
        log.warning(kv(event="unknown_support_state", support=str(raw), ticker=str(m.get("ticker"))))
        rank = _UNKNOWN_SUPPORT_RANK
    else:
        rank = _SUPPORT_RANK[state]
    return (rank, quoted, str(m.get("expected_expiration_time") or m.get("close_time") or "9999"))


def snapshot_orderbooks(client: KalshiClient, markets: list[dict[str, Any]], max_books: int) -> list[dict[str, Any]]:
    cands = [m for m in markets if m.get("status") in LIVE_STATUSES and m.get("ticker")]
    cands.sort(key=_priority)
    out = []
    for m in cands[:max_books]:
        try:
            body = client.get_orderbook(m["ticker"], depth=10)
            lv = orderbook_levels(body)
            out.append({"ticker": m["ticker"], "yes": lv["yes"], "no": lv["no"], "raw": body})
        except KalshiError as e:
            out.append({"ticker": m["ticker"], "_error": str(e)[:200]})
    return out


def run_capture(out_root: Path, statuses: list[str], with_orderbook: bool, max_orderbooks: int = 400, series_filter: list[str] | None = None) -> int:
    cfg = settings()
    onto = Ontology.load()
    client = KalshiClient(cfg)
    ledger = Ledger(out_root)
    t0 = utcnow()
    series = series_filter or nba_series_tickers(client, cfg.catalog_dir)
    log.info(kv(event="capture_start", series=len(series), statuses=",".join(statuses)))
    markets = snapshot_markets(client, series, statuses, onto)
    entry = ledger.append_rows("kalshi/markets", markets, observed_at=t0, meta={"series": series, "statuses": statuses, "requests": client.request_count})
    log.info(kv(event="capture_markets_written", path=entry.path, rows=entry.rows))
    if with_orderbook:
        books = snapshot_orderbooks(client, markets, max_orderbooks)
        e2 = ledger.append_rows("kalshi/orderbooks", books, observed_at=t0, meta={"n": len(books)})
        log.info(kv(event="capture_books_written", path=e2.path, rows=e2.rows))
    # tiny status file (overwritten on purpose: it's a pointer, not an observation)
    by_support = _count(markets, "_support")
    status = {"last_capture_utc": iso(t0), "n_markets": entry.rows, "n_series": len(series), "requests": client.request_count, "run_id": ledger.run_id,
              "by_status": _count(markets, "status"), "by_support": by_support, "by_family": _count(markets, "_family")}
    status["alarms"] = capture_alarms(markets, by_support, client, onto)
    status["notes"] = capture_notes(markets, max_orderbooks if with_orderbook else None)
    status["alarm"] = bool(status["alarms"])
    (out_root / "STATUS_capture.json").write_text(json.dumps(status, indent=1))
    print(json.dumps(status, indent=1))
    if status["alarm"]:
        for a in status["alarms"]:
            log.warning(kv(event="capture_alarm", detail=a))
    return 0


def capture_alarms(markets: list[dict[str, Any]], by_support: dict[str, int], client: KalshiClient, onto: Ontology) -> list[str]:
    """Everything this capture knows it did not fully account for.

    The coverage invariant is "every market DISCOVERED is ACCOUNTED FOR", and until now a breach of
    it was completely silent: an unknown series classifies UNRESOLVED and nothing failed, warned or
    alerted, the only trace being a ``by_support`` bucket that nothing ever read back. A brand-new
    Kalshi series -- precisely the event the ontology exists to survive -- would have appeared,
    counted as UNRESOLVED and been ignored. These alarms are surfaced by the conductor workflow.
    """
    alarms: list[str] = []
    n_unresolved = by_support.get(str(Support.UNRESOLVED), 0)
    if n_unresolved:
        fams = sorted({str(m.get("series_ticker")) for m in markets if m.get("_support") == str(Support.UNRESOLVED)})
        alarms.append(f"{n_unresolved} market(s) classified UNRESOLVED across series {fams}: the ontology does not describe something on the board")
    missing_class = [m.get("ticker") for m in markets if not m.get("_family") or not m.get("_support")]
    if missing_class:
        alarms.append(f"{len(missing_class)} captured market(s) carry no family/support at all, e.g. {missing_class[:3]}")
    unknown_series = sorted({str(m.get("series_ticker")) for m in markets if m.get("series_ticker") and onto.family_for_series(str(m.get("series_ticker"))) is None})
    if unknown_series:
        alarms.append(f"series on the board with no ontology entry: {unknown_series}")
    if client.truncations:
        alarms.append(f"pagination stopped with a live cursor (results we did not see): {client.truncations[:5]}")
    return alarms


def capture_notes(markets: list[dict[str, Any]], max_orderbooks: int | None) -> list[str]:
    """Expected, configured truncation. Worth recording; never a reason to fail the run.

    Order-book depth is sampled on purpose: the workflow passes ``--max-orderbooks 300`` and
    ``snapshot_orderbooks`` takes the highest-priority markets. Hitting that cap is the cap doing its
    job, not a coverage-invariant breach -- the market universe is still captured in full, only the
    depth snapshots are a sample.

    This started life as an alarm, and the conductor went red every single day at the 16:00 UTC
    capture as a result (3,463 live markets against a cap of 300). A daily red run on an unattended
    workflow teaches people to ignore alarms, which costs more than the alarm was ever worth. The
    genuine breaches -- UNRESOLVED markets, unclassified markets, unknown series, and *pagination*
    truncation, which silently drops markets from the universe -- stay in ``capture_alarms``.
    """
    notes: list[str] = []
    if max_orderbooks is not None:
        live = sum(1 for m in markets if m.get("status") in LIVE_STATUSES and m.get("ticker"))
        if live > max_orderbooks:
            notes.append(f"order books sampled by priority: {live} live markets, cap {max_orderbooks}")
    return notes


def _count(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    c: dict[str, int] = {}
    for r in rows:
        k = str(r.get(key))
        c[k] = c.get(k, 0) + 1
    return dict(sorted(c.items()))


def last_capture_age_minutes(out_root: Path) -> float | None:
    """Re-exported from ``nba_edge.archive.status``; see that module for why it lives there."""
    return status_age_minutes(out_root / "STATUS_capture.json", "last_capture_utc")
