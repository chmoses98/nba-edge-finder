"""Settlement job: fetch final box scores for finished games and settle every contract we captured.

Archive contract (all kinds are append-only JSONL.gz in the ledger rooted at ``out_root``):

* reads  ``context/schedule`` (Game rows), ``contracts`` (Contract rows keyed by ticker with ``game_id``),
         ``predictions`` (ContractPrediction rows), ``kalshi/markets`` (raw Kalshi market dicts with
         ``_observed_at_utc`` and ``result``), ``boxscores`` and ``settlements`` (our own earlier output)
* writes ``boxscores`` (FinalBoxScore rows), ``settlements`` (SettlementRecord rows + ``ticker``/``game_id``)
         and the pointer file ``STATUS_settle.json`` (overwritten on purpose: a pointer, not an observation)

Rules
- A game is a candidate once its tip is older than ``SETTLE_GRACE`` (2.5h), it is not postponed/cancelled in
  the latest schedule row, it has at least one prediction or contract row, and we do not already hold a FINAL
  box score for it. Holding a final box short-circuits the network fetch but contracts are still settled
  against it, so contract rows that arrive after the box was archived are picked up on the next run.
- Kalshi's ``result`` (newest observation with a non-empty value) is passed to the engine which never lets it
  override our computed outcome; disagreements are surfaced in the status file.
- Tickers with a Kalshi result but no Contract row get a market-only record (``engine_version='kalshi'``,
  reason ``kalshi_result_only``) so market calibration / CLV research covers the whole universe.
- Everything is idempotent: settlement records are keyed by ``idempotency_key`` and a re-run with no new data
  appends nothing (no empty files are written either).

Network is injectable (``fetch_box``); the default routes ``espn:<id>`` to the ESPN summary and 10-digit NBA
game ids to the NBA CDN box score.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from nba_edge.archive.ledger import Ledger
from nba_edge.kalshi.ticker import parse_ticker
from nba_edge.log import get_logger, kv
from nba_edge.schemas.core import GameStatus
from nba_edge.schemas.market import Contract
from nba_edge.settlement.boxscore import FinalBoxScore
from nba_edge.settlement.engine import (
    DISAGREE_PREFIX,
    SettlementOutcome,
    SettlementRecord,
    _kalshi_outcome,
    idempotency_key,
    settle_many,
)
from nba_edge.timeutil import iso, parse_iso, utcnow

log = get_logger(__name__)

SETTLE_GRACE = timedelta(hours=2, minutes=30)
KALSHI_ENGINE_VERSION = "kalshi"
MARKET_ONLY_REASON = "kalshi_result_only"
_SKIP_STATUSES = {GameStatus.POSTPONED.value, GameStatus.CANCELLED.value}

FetchBox = Callable[[str], FinalBoxScore]


# ---- row helpers ---------------------------------------------------------------------------------


def strip_meta(row: dict[str, Any]) -> dict[str, Any]:
    """Drop ledger stamps (``_observed_at_utc``, ``_run_id``, ...) so rows can be fed back into strict models."""
    return {k: v for k, v in row.items() if not k.startswith("_")}


def coerce(model: type, row: dict[str, Any]):
    """Build a strict pydantic model from a ledger row, ignoring unknown keys (forward-compatible)."""
    fields = model.model_fields
    return model(**{k: v for k, v in strip_meta(row).items() if k in fields})


def observed_at_of(row: dict[str, Any]) -> datetime | None:
    v = row.get("_observed_at_utc") or row.get("observed_at_utc")
    if not v:
        return None
    try:
        return parse_iso(v)
    except ValueError:
        return None


def latest_by(rows: Iterable[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    """Newest row (by ``_observed_at_utc``) per ``row[key]``; rows without the key are ignored."""
    out: dict[str, tuple[datetime, dict[str, Any]]] = {}
    floor = datetime.min.replace(tzinfo=UTC)
    for r in rows:
        k = r.get(key)
        if not k:
            continue
        ts = observed_at_of(r) or floor
        prev = out.get(k)
        if prev is None or ts >= prev[0]:
            out[k] = (ts, r)
    return {k: v[1] for k, v in out.items()}


def latest_schedule(ledger: Ledger) -> dict[str, dict[str, Any]]:
    """Latest schedule row per game_id across every archived snapshot (a snapshot only covers a window)."""
    return latest_by(ledger.iter_rows("context/schedule"), "game_id")


def load_contracts(ledger: Ledger) -> dict[str, Contract]:
    """Latest Contract per ticker. Rows that fail validation are logged and skipped."""
    out: dict[str, Contract] = {}
    for tk, row in latest_by(ledger.iter_rows("contracts"), "ticker").items():
        try:
            out[tk] = coerce(Contract, row)
        except (TypeError, ValueError) as e:
            log.warning(kv(event="contract_row_invalid", ticker=tk, err=str(e)[:120]))
    return out


def load_settlements(ledger: Ledger) -> dict[str, SettlementRecord]:
    out: dict[str, SettlementRecord] = {}
    for row in ledger.iter_rows("settlements"):
        try:
            rec = coerce(SettlementRecord, row)
        except (TypeError, ValueError) as e:
            log.warning(kv(event="settlement_row_invalid", ticker=row.get("ticker"), err=str(e)[:120]))
            continue
        out[rec.idempotency_key] = rec
    return out


def load_final_boxes(ledger: Ledger) -> dict[str, FinalBoxScore]:
    """Latest FINAL box per game_id (highest stat_correction_version, then latest fetch)."""
    out: dict[str, FinalBoxScore] = {}
    for row in ledger.iter_rows("boxscores"):
        try:
            box = coerce(FinalBoxScore, row)
        except (TypeError, ValueError) as e:
            log.warning(kv(event="boxscore_row_invalid", game_id=row.get("game_id"), err=str(e)[:120]))
            continue
        if not box.is_final:
            continue
        prev = out.get(box.game_id)
        if prev is None or (box.stat_correction_version, box.fetched_at_utc) >= (prev.stat_correction_version, prev.fetched_at_utc):
            out[box.game_id] = box
    return out


def kalshi_results(ledger: Ledger) -> tuple[dict[str, str], dict[str, str]]:
    """``(result_by_ticker, family_by_ticker)`` from the newest kalshi/markets observation carrying a non-empty
    ``result``. Family comes from the same observation (``_family`` stamped by capture)."""
    newest: dict[str, tuple[datetime, str, str]] = {}
    for row in ledger.iter_rows("kalshi/markets"):
        tk, res = row.get("ticker"), row.get("result")
        if not tk or not res:
            continue
        ts = observed_at_of(row)
        if ts is None:
            continue
        prev = newest.get(tk)
        if prev is None or ts >= prev[0]:
            newest[tk] = (ts, str(res), str(row.get("_family") or ""))
    return {k: v[1] for k, v in newest.items()}, {k: v[2] for k, v in newest.items()}


def game_ids_with_activity(ledger: Ledger, contracts: dict[str, Contract]) -> set[str]:
    ids = {c.game_id for c in contracts.values() if c.game_id}
    for row in ledger.iter_rows("predictions"):
        if row.get("game_id"):
            ids.add(str(row["game_id"]))
    return ids


# ---- ticker -> game resolution (for market-only rows) ----------------------------------------------


def _schedule_index(schedule: dict[str, dict[str, Any]]) -> dict[tuple[str, str, str], str]:
    idx: dict[tuple[str, str, str], str] = {}
    for gid, g in schedule.items():
        d, h, a = g.get("game_date_et"), g.get("home_tricode"), g.get("away_tricode")
        if d and h and a:
            idx[(str(d), str(a).upper(), str(h).upper())] = gid
    return idx


def resolve_game_id(ticker: str, schedule_index: dict[tuple[str, str, str], str]) -> str:
    """Best-effort game id for a ticker without a Contract: event suffix date + away/home vs the schedule."""
    p = parse_ticker(ticker)
    if p.game_date is None or not p.away_tricode or not p.home_tricode:
        return ""
    return schedule_index.get((p.game_date.isoformat(), p.away_tricode, p.home_tricode), "")


# ---- box fetching ---------------------------------------------------------------------------------


def default_fetch_box(game_id: str) -> FinalBoxScore:
    """Route a schedule game id to the right box-score source. Imported lazily to keep the job importable
    without touching the HTTP stack."""
    from nba_edge.data.boxscore import fetch_espn_summary, fetch_nba_cdn_boxscore

    if game_id.startswith("espn:"):
        return fetch_espn_summary(game_id[len("espn:"):], ttl_s=None)
    if len(game_id) == 10 and game_id.isdigit():
        return fetch_nba_cdn_boxscore(game_id, ttl_s=None)
    raise ValueError(f"no box-score source for game id {game_id!r}")


# ---- market-only settlement --------------------------------------------------------------------------


def market_only_record(ticker: str, result: str, game_id: str, now: datetime) -> SettlementRecord:
    # Share the engine's map rather than repeating it: this copy also lacked "scalar", so a market
    # Kalshi had voided was recorded as UNSETTLEABLE "unrecognised result" instead of VOID.
    outcome = _kalshi_outcome(result) or SettlementOutcome.UNSETTLEABLE
    reason = MARKET_ONLY_REASON if outcome != SettlementOutcome.UNSETTLEABLE else f"{MARKET_ONLY_REASON}: unrecognised result {result!r}"
    return SettlementRecord(
        ticker=ticker, game_id=game_id, outcome=outcome, value=None, reason=reason, settled_at_utc=now, box_source="kalshi",
        box_stat_correction_version=0, engine_version=KALSHI_ENGINE_VERSION,
        idempotency_key=idempotency_key(ticker, game_id, KALSHI_ENGINE_VERSION, 0),
    )


def _record_row(rec: SettlementRecord) -> dict[str, Any]:
    return rec.model_dump(mode="json") | {"ticker": rec.ticker, "game_id": rec.game_id}


# ---- job ----------------------------------------------------------------------------------------


def run_settle(out_root: Path, data_root: Path, fetch_box: FetchBox | None = None, now: datetime | None = None) -> int:
    """Settle finished games. ``out_root`` is the archive root; ``data_root`` is the code data dir (catalog),
    unused by settlement itself but kept for CLI symmetry."""
    out_root = Path(out_root)
    now = now or utcnow()
    fetch_box = fetch_box or default_fetch_box
    ledger = Ledger(out_root)

    schedule = latest_schedule(ledger)
    contracts = load_contracts(ledger)
    existing = load_settlements(ledger)
    boxes = load_final_boxes(ledger)
    results, families = kalshi_results(ledger)
    active = game_ids_with_activity(ledger, contracts)
    contracts_by_game: dict[str, list[Contract]] = {}
    for c in contracts.values():
        if c.game_id:
            contracts_by_game.setdefault(c.game_id, []).append(c)

    cutoff = now - SETTLE_GRACE
    new_boxes: list[FinalBoxScore] = []
    new_records: list[SettlementRecord] = []
    errors: list[dict[str, str]] = []
    n_checked = n_not_final = 0

    for gid, g in sorted(schedule.items()):
        if gid not in active or str(g.get("status") or "") in _SKIP_STATUSES:
            continue
        try:
            tip = parse_iso(str(g["start_time_utc"]))
        except (KeyError, ValueError):
            continue
        if tip >= cutoff:
            continue
        n_checked += 1
        box = boxes.get(gid)
        if box is None:
            try:
                box = fetch_box(gid)
            except Exception as e:  # noqa: BLE001 - one game failing must not stop the job
                log.warning(kv(event="box_fetch_failed", game_id=gid, err=f"{type(e).__name__}: {e}"[:160]))
                errors.append({"game_id": gid, "error": f"{type(e).__name__}: {e}"[:200]})
                continue
            if not box.is_final:
                n_not_final += 1
                log.info(kv(event="box_not_final", game_id=gid, status=box.status.value))
                continue
            new_boxes.append(box)
            boxes[gid] = box
        recs = settle_many(contracts_by_game.get(gid, []), box, existing, kalshi_results=results, now=now)
        for rec in recs:
            if rec.idempotency_key not in existing:
                existing[rec.idempotency_key] = rec
                new_records.append(rec)

    # market-only universe: Kalshi result present, no Contract row for the ticker
    sched_idx = _schedule_index(schedule)
    n_market_only = 0
    for tk, res in sorted(results.items()):
        if tk in contracts:
            continue
        rec = market_only_record(tk, res, resolve_game_id(tk, sched_idx), now)
        if rec.idempotency_key in existing:
            continue
        existing[rec.idempotency_key] = rec
        new_records.append(rec)
        n_market_only += 1

    if new_boxes:
        e = ledger.append_rows("boxscores", [b.model_dump(mode="json") for b in new_boxes], observed_at=now, meta={"n": len(new_boxes)})
        log.info(kv(event="boxscores_written", path=e.path, rows=e.rows))
    if new_records:
        e = ledger.append_rows("settlements", [_record_row(r) for r in new_records], observed_at=now, meta={"n": len(new_records), "n_market_only": n_market_only})
        log.info(kv(event="settlements_written", path=e.path, rows=e.rows))

    disagreements = sorted({r.ticker for r in existing.values() if r.reason.startswith(DISAGREE_PREFIX)})
    status = {
        "settled_at_utc": iso(now),
        "n_games_checked": n_checked,
        "n_boxes": len(new_boxes),
        "n_boxes_not_final": n_not_final,
        "n_new_settlements": len(new_records),
        "n_unsettleable": sum(r.outcome == SettlementOutcome.UNSETTLEABLE for r in new_records),
        "n_market_only": n_market_only,
        "n_settlements_total": len(existing),
        "disagreements": disagreements,
        "errors": errors,
        "run_id": ledger.run_id,
        "families_seen": sorted({f for f in families.values() if f}),
    }
    (out_root / "STATUS_settle.json").write_text(json.dumps(status, indent=1, default=str))
    print(json.dumps(status, indent=1, default=str))
    return 0
