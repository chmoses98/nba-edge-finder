"""Kalshi NBA market capture job: snapshot every NBA market (all series in the catalog, plus a live series
re-scan so new families are not missed) into the append-only ledger.

Pregame vs post-tip labelling is NOT done here: snapshots are frozen with their observation time, and the
evaluation layer labels them later against the authoritative tip time. That keeps capture dumb and immutable.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from nba_edge.archive.book_policy import POLICY_ID as BOOK_POLICY_ID
from nba_edge.archive.book_policy import TICK_SECONDS, Selection, select_books
from nba_edge.archive.delta import ORDERBOOK_CHECKPOINT_KIND, ORDERBOOK_DELTA_KIND
from nba_edge.archive.ledger import Ledger
from nba_edge.archive.reconstruct import DEFAULT_CHECKPOINT_EVERY, write_board
from nba_edge.archive.status import status_age_minutes
from nba_edge.config import settings
from nba_edge.kalshi.client import KalshiClient, KalshiError
from nba_edge.kalshi.discovery import is_nba_series
from nba_edge.kalshi.normalize import orderbook_levels, quote_cents
from nba_edge.kalshi.ontology import Ontology, Support, classify_market
from nba_edge.log import get_logger, kv
from nba_edge.timeutil import iso, parse_iso, utcnow

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


# ---- which series to LIST this tick ---------------------------------------------------------------------------------------------------
# 171 of the 300 queried series had no market at all on the 2026-10-24 board, yet each costs two list requests (open, unopened) every tick:
# 342 of ~582 requests, ~68 s of a ~134 s market read. Because a tick is stamped at its START, that wasted time is data that is older than
# its stamp is honest about. A series is skipped ONLY when the previous tick read it successfully and found it empty; every skipped series is
# still probed on a deterministic rotation, so none is ignored for more than EMPTY_SERIES_PROBE_EVERY ticks, and any series the daily
# catalog shows as live, any series new to the universe, and every series after an incomplete or stale previous tick is probed at once.
EMPTY_SERIES_PROBE_EVERY = 6
PREVIOUS_STATUS_MAX_AGE_MIN = 45.0
SERIES_PROBE_POLICY = "skip-known-empty-v1"


def catalog_live_series(catalog_dir: Path) -> set[str]:
    try:
        d = json.loads((catalog_dir / "discovery_summary.json").read_text())
        return {r["ticker"] for r in d.get("nba_series", []) if sum((r.get("counts_by_status") or {}).get(s, 0) for s in ("open", "unopened")) > 0}
    except (OSError, ValueError, KeyError):
        return set()


def plan_series_probe(series: list[str], prev_status: dict[str, Any] | None, catalog_live: set[str], now: datetime,
                      every: int = EMPTY_SERIES_PROBE_EVERY) -> tuple[list[str], list[str], str]:
    """(series to list now, series skipped as known-empty, reason). Deterministic in its inputs; safe default is to list everything."""
    full = (list(series), [], "")
    st = (prev_status or {}).get("series_state") or {}
    last = (prev_status or {}).get("last_capture_utc")
    if not st or not last:
        return (*full[:2], "no previous series state: listing every series")
    try:
        age_min = (now - parse_iso(last)).total_seconds() / 60.0
    except ValueError:
        return (*full[:2], "unreadable previous capture time: listing every series")
    if age_min > PREVIOUS_STATUS_MAX_AGE_MIN or age_min < 0:
        return (*full[:2], f"previous tick is {age_min:.0f} min old: listing every series")
    if (prev_status or {}).get("n_fetch_errors"):
        return (*full[:2], "previous tick was incomplete: listing every series")
    empty_ok = set(st.get("empty_ok") or [])
    tick = int(now.timestamp() // TICK_SECONDS)
    probe, skipped = [], []
    for sr in series:
        known_empty = sr in empty_ok
        due = int(hashlib.sha256(sr.encode()).hexdigest(), 16) % every == tick % every
        if known_empty and not due and sr not in catalog_live:
            skipped.append(sr)
        else:
            probe.append(sr)
    return probe, skipped, f"{len(skipped)} series read successfully and empty on the previous tick are skipped; each is re-listed every {every} ticks"


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


# Share of requested order books that may fail before the shift verdict calls it a collection problem. A single 5xx
# on one of ~300 requests is noise (the client already retries); a fifth of them failing means the book stream is broken.
BOOK_ERROR_ALARM_FRACTION = 0.20
ORDERBOOK_POLICY_ID = "priority-v1"  # the original deterministic ordering; replaced by nba_edge.archive.book_policy

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


def snapshot_orderbooks(client: KalshiClient, markets: list[dict[str, Any]], max_books: int, selection: Selection | None = None) -> list[dict[str, Any]]:
    """Fetch order books. With a ``selection`` (nba_edge.archive.book_policy) exactly those markets are requested, in policy order, and each
    row records why it was chosen; without one the original priority ordering is used (kept for callers and replays that pin it)."""
    if selection is not None:
        cands = list(selection.markets)
    else:
        cands = [m for m in markets if m.get("status") in LIVE_STATUSES and m.get("ticker")]
        cands.sort(key=_priority)
        cands = cands[:max_books]
    out = []
    for m in cands:
        why = selection.reasons.get(m["ticker"]) if selection is not None else None
        try:
            body = client.get_orderbook(m["ticker"], depth=10)
            lv = orderbook_levels(body)
            row = {"ticker": m["ticker"], "yes": lv["yes"], "no": lv["no"], "raw": body}
        except KalshiError as e:
            row = {"ticker": m["ticker"], "_error": str(e)[:200]}
        if why:
            row["_selected_by"] = why
        out.append(row)
    return out


def run_capture(out_root: Path, statuses: list[str], with_orderbook: bool, max_orderbooks: int = 400, series_filter: list[str] | None = None,
                delta_encode: bool = True, checkpoint_every: int = DEFAULT_CHECKPOINT_EVERY, probe_all_series: bool = False) -> int:
    cfg = settings()
    onto = Ontology.load()
    client = KalshiClient(cfg)
    ledger = Ledger(out_root)
    t0 = utcnow()
    series = series_filter or nba_series_tickers(client, cfg.catalog_dir)
    prev_status = None
    try:
        prev_status = json.loads((out_root / "STATUS_capture.json").read_text())
    except (OSError, ValueError):
        pass
    if probe_all_series or series_filter:
        probe, skipped, probe_reason = list(series), [], "listing every series (explicit)"
    else:
        probe, skipped, probe_reason = plan_series_probe(series, prev_status, catalog_live_series(cfg.catalog_dir), t0)
    log.info(kv(event="capture_start", series=len(series), probed=len(probe), skipped_empty=len(skipped), statuses=",".join(statuses)))
    markets = snapshot_markets(client, probe, statuses, onto)
    markets_done = utcnow()
    fetch_errors = [r for r in markets if "_error" in r]
    # `observed_at` (t0) is the instant this capture STARTED. The markets were read over the following
    # minutes and the books after that, so a consumer deciding at checkpoint C must not treat a tick stamped
    # t0 <= C as "all information is from before C". The three instants are recorded next to each other so a
    # point-in-time reader can use the conservative one (fetch end) instead of guessing; nothing historical is
    # rewritten -- older ticks simply lack these keys and are bounded by their manifest `written_at_utc`.
    market_meta = {"series": series, "statuses": statuses, "requests": client.request_count,
                   "series_probe": {"policy": SERIES_PROBE_POLICY, "n_probed": len(probe), "n_skipped_empty": len(skipped),
                                    "skipped_sha256": hashlib.sha256("\n".join(sorted(skipped)).encode()).hexdigest() if skipped else None, "reason": probe_reason},
                   "capture_started_utc": iso(t0), "markets_fetched_utc": iso(markets_done),
                   "complete": not fetch_errors, "n_fetch_errors": len(fetch_errors),
                   "fetch_errors": [{k: e.get(k) for k in ("series_ticker", "status_requested", "_error")} for e in fetch_errors[:25]]}
    # Delta encoding writes a full CHECKPOINT periodically and only the changed markets/fields in
    # between. Measured on real boards: a delta is ~1.8% of a full snapshot four minutes later.
    # Checkpoints reuse the existing `kalshi/markets` kind, so every board already on the archive is
    # a valid base and nothing is migrated or rewritten. `--full-snapshots` disables it entirely and
    # restores the old behaviour exactly.
    if delta_encode:
        written = write_board(ledger, markets, observed_at=t0, checkpoint_every=checkpoint_every, meta=market_meta)
        n_markets = written["n_markets"]
        log.info(kv(event="capture_markets_written", path=written["path"], encoding=written["encoding"], bytes=written["bytes"]))
    else:
        entry = ledger.append_rows("kalshi/markets", markets, observed_at=t0, meta={**market_meta, "encoding": "checkpoint"})
        written = {"encoding": "checkpoint", "path": entry.path, "bytes": (out_root / entry.path).stat().st_size, "n_markets": entry.rows}
        n_markets = entry.rows
        log.info(kv(event="capture_markets_written", path=entry.path, rows=entry.rows))
    books_written = None
    if with_orderbook:
        selection = select_books(markets, now=t0, max_books=max_orderbooks)
        policy = BOOK_POLICY_ID
        if not selection.markets and any(m.get("status") in LIVE_STATUSES for m in markets):
            # No live market carried a usable tip time (an API change would look exactly like this). Fall back to the original ordering
            # rather than record no books at all, and say so.
            selection, policy = None, ORDERBOOK_POLICY_ID + "-fallback"
        books = snapshot_orderbooks(client, markets, max_orderbooks, selection)
        books_meta = {"n": len(books), "n_errors": sum(1 for b in books if "_error" in b),
                      "capture_started_utc": iso(t0), "books_fetched_utc": iso(utcnow()),
                      "selection_policy": policy, "selection": None if selection is None else selection.summary}
        if delta_encode:
            books_written = write_board(
                ledger, books, observed_at=t0, checkpoint_every=checkpoint_every, meta=books_meta,
                checkpoint_kind=ORDERBOOK_CHECKPOINT_KIND, delta_kind=ORDERBOOK_DELTA_KIND,
            )
        else:
            e2 = ledger.append_rows(ORDERBOOK_CHECKPOINT_KIND, books, observed_at=t0, meta=books_meta)
            books_written = {"encoding": "checkpoint", "path": e2.path, "bytes": (out_root / e2.path).stat().st_size, "n_markets": e2.rows}
        log.info(kv(event="capture_books_written", path=books_written["path"], encoding=books_written["encoding"]))
    # tiny status file (overwritten on purpose: it's a pointer, not an observation)
    by_support = _count(markets, "_support")
    status = {"last_capture_utc": iso(t0), "n_markets": n_markets, "n_series": len(series), "requests": client.request_count, "run_id": ledger.run_id,
              "markets_written": written, "orderbooks_written": books_written,
              "by_status": _count(markets, "status"), "by_support": by_support, "by_family": _count(markets, "_family")}
    # Collection integrity and ontology debt are different questions and are reported separately. `alarms` keeps the
    # union for existing readers; the worker's shift verdict reads `collection_alarms` only.
    status["collection_alarms"] = collection_alarms(markets, client, books if with_orderbook else None)
    status["classification_alarms"] = classification_alarms(markets, by_support, onto)
    status["alarms"] = status["collection_alarms"] + status["classification_alarms"]
    status["notes"] = capture_notes(markets, max_orderbooks if with_orderbook else None)
    status["alarm"] = bool(status["alarms"])
    status["observation_window"] = {"capture_started_utc": iso(t0), "markets_fetched_utc": iso(markets_done),
                                    "books_fetched_utc": books_meta["books_fetched_utc"] if with_orderbook else None}
    status["n_fetch_errors"] = len(fetch_errors)
    seen_series = {m.get("series_ticker") for m in markets if m.get("ticker")}
    failed_series = {m.get("series_ticker") for m in markets if "_error" in m}
    status["series_state"] = {
        "policy": SERIES_PROBE_POLICY,
        "nonempty": sorted(seen_series & set(probe)),
        # empty AND read successfully this tick; a series skipped this tick stays empty_ok (nothing new was learned about it)
        "empty_ok": sorted(((set(probe) - seen_series - failed_series) | set(skipped)) & set(series)),
    }
    status["series_probe"] = {"n_universe": len(series), "n_probed": len(probe), "n_skipped_empty": len(skipped), "reason": probe_reason, "skipped": sorted(skipped)}
    if with_orderbook:
        status["orderbook_policy"] = {"policy": books_meta["selection_policy"], "n": books_meta["n"], "n_errors": books_meta["n_errors"],
                                      "selection": books_meta["selection"]}
    (out_root / "STATUS_capture.json").write_text(json.dumps(status, indent=1))
    print(json.dumps(status, indent=1))
    if status["alarm"]:
        for a in status["alarms"]:
            log.warning(kv(event="capture_alarm", detail=a))
    return 0


def collection_alarms(markets: list[dict[str, Any]], client: KalshiClient, books: list[dict[str, Any]] | None = None) -> list[str]:
    """Things that mean the BOARD is missing data we asked for. These are operational failures of collection."""
    alarms: list[str] = []
    errs = [m for m in markets if "_error" in m]
    if errs:
        first = [f"{e.get('series_ticker')}/{e.get('status_requested')}" for e in errs[:5]]
        alarms.append(f"{len(errs)} series/status fetch(es) failed, so that part of the board is MISSING from this snapshot, e.g. {first}")
    if client.truncations:
        alarms.append(f"pagination stopped with a live cursor (results we did not see): {client.truncations[:5]}")
    unclassified = [m.get("ticker") for m in markets if m.get("ticker") and (not m.get("_family") or not m.get("_support"))]
    if unclassified:
        alarms.append(f"{len(unclassified)} captured market(s) carry no family/support at all, e.g. {unclassified[:3]}")
    if books:
        bad = sum(1 for b in books if "_error" in b)
        if bad and bad / len(books) > BOOK_ERROR_ALARM_FRACTION:
            alarms.append(f"{bad}/{len(books)} order-book requests failed (> {BOOK_ERROR_ALARM_FRACTION:.0%})")
    return alarms


def classification_alarms(markets: list[dict[str, Any]], by_support: dict[str, int], onto: Ontology) -> list[str]:
    """Ontology debt: markets that were CAPTURED fine but that the ontology does not (yet) describe."""
    alarms: list[str] = []
    n_unresolved = by_support.get(str(Support.UNRESOLVED), 0)
    if n_unresolved:
        fams = sorted({str(m.get("series_ticker")) for m in markets if m.get("_support") == str(Support.UNRESOLVED)})
        alarms.append(f"{n_unresolved} market(s) classified UNRESOLVED across series {fams}: the ontology does not describe something on the board")
    unknown_series = sorted({str(m.get("series_ticker")) for m in markets if m.get("series_ticker") and onto.family_for_series(str(m.get("series_ticker"))) is None})
    if unknown_series:
        alarms.append(f"series on the board with no ontology entry: {unknown_series}")
    return alarms


def capture_alarms(markets: list[dict[str, Any]], by_support: dict[str, int], client: KalshiClient, onto: Ontology) -> list[str]:
    """Everything this capture knows it did not fully account for.

    The coverage invariant is "every market DISCOVERED is ACCOUNTED FOR", and until now a breach of
    it was completely silent: an unknown series classifies UNRESOLVED and nothing failed, warned or
    alerted, the only trace being a ``by_support`` bucket that nothing ever read back. A brand-new
    Kalshi series -- precisely the event the ontology exists to survive -- would have appeared,
    counted as UNRESOLVED and been ignored. These alarms are surfaced by the conductor workflow.
    """
    return classification_alarms(markets, by_support, onto) + collection_alarms(markets, client)


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
            notes.append(f"order books sampled by policy {BOOK_POLICY_ID}: {live} live markets, cap {max_orderbooks}")
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
