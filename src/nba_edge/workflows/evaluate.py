"""Evaluation job: join predictions x settlements x schedule x market observations into per-prediction
evaluation rows, then compute calibration / Brier / CLV / authority reports.

Archive contract (ledger rooted at ``out_root``):

* reads  ``predictions`` (ContractPrediction rows), ``settlements`` (SettlementRecord rows), ``context/schedule``
         (Game rows: ``start_time_utc`` is the scheduled tip), ``boxscores`` (``actual_tip_utc`` overrides the
         schedule when present), ``kalshi/markets`` (observations with ``_observed_at_utc``) and ``evaluations``
         (our own earlier output, for dedupe)
* writes ``evaluations`` (append-only; deduped on ``(prediction_id, settlement_key)``), the derived reports
         ``eval/report.json``, ``eval/report.md``, ``eval/market_only.json`` (overwritten: reports are derived,
         not observations) and the pointer ``STATUS_evaluate.json``

Leak rules
- ``pregame`` is recomputed here from the authoritative tip: the prediction instant AND the market observation
  it used must both be strictly before tip. Only pregame rows enter any metric or the authority ledger.
- The closing snapshot is the last market observation STRICTLY before tip (``evaluation.clv.closing_snapshot``).
- ``clv_yes_prob`` / ``clv_no_prob`` (and every ``clv_mean``) are QUOTED-EXECUTION CLV: close midpoint minus the
  prediction-time executable ASK of the side (``market_yes_ask`` / ``market_no_ask``), pre-fee. They INCLUDE the
  half-spread paid on entry, so a market that never moves still scores about minus half the spread. They are not
  selection CLV and not actual-fill CLV, and no fee is applied anywhere in this module. Their meaning is unchanged
  (authority gates read them) and they are re-exposed under the explicit names ``quoted_execution_clv_*``.
- ``selection_clv_*`` (additive, clv-canonical/1) is close midpoint minus the prediction-time MIDPOINT of the same
  side: no spread, no fee. It is only produced when the close is a two-sided midpoint
  (``close_price_source == "mid"``); a last-trade fallback is a trade print, not a midpoint, and is flagged.
"""

from __future__ import annotations

import bisect
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from nba_edge.archive.delta import DeltaChainError
from nba_edge.archive.ledger import Ledger, entry_observed_at
from nba_edge.archive.reconstruct import iter_market_rows, reconstruct_at
from nba_edge.evaluation.authority import AuthorityLedger, EvaluationRow
from nba_edge.evaluation.clv import closing_snapshot, clv_prob
from nba_edge.evaluation.metrics import (
    brier,
    brier_skill_score,
    calibration_table,
    ece,
    log_loss,
    reliability_slope_intercept,
    sharpness,
)
from nba_edge.log import get_logger, kv
from nba_edge.schemas.prediction import View
from nba_edge.settlement.engine import SettlementOutcome, SettlementRecord
from nba_edge.timeutil import iso, parse_iso, utcnow
from nba_edge.workflows.settle import KALSHI_ENGINE_VERSION, coerce, latest_schedule

log = get_logger(__name__)

VIEW_PROB_KEY = {View.DATA_ONLY: "p_data_only", View.MARKET_BASELINE: "p_market", View.HYBRID: "p_hybrid"}
DEFAULT_MAX_NEW_ROWS = 150_000  # per run; the first historical backfill drains over several runs instead of one over-budget run
DEFAULT_BUDGET_S = 600.0
_REPORT_KEYS = ("ticker", "family", "y", "pregame", "p_data_only", "p_market", "p_hybrid", "p_production", "clv_yes_prob", "clv_no_prob",
                "selection_clv_yes_prob", "selection_clv_no_prob", "hours_before_tip")
HOUR_BUCKETS = (("<1h", 0.0, 1.0), ("1-6h", 1.0, 6.0), ("6-24h", 6.0, 24.0), (">24h", 24.0, float("inf")))
_OBS_KEYS = ("ticker", "yes_bid", "yes_ask", "no_bid", "no_ask", "last_price", "status", "result", "_family", "_observed_at_utc")


# ---- loading --------------------------------------------------------------------------------------


def iter_rows_newest_first(ledger: Ledger, kind: str):
    """Rows of ``kind`` by day partition, newest day first (recent evidence is evaluated first when a backlog exists)."""
    base = ledger.root / kind
    if not base.exists():
        return
    for part in sorted(base.glob("dt=*"), reverse=True):
        d = part.name[3:]
        yield from ledger.iter_rows(kind, dt_from=d, dt_to=d)


def _dt(v: Any) -> datetime | None:
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v
    try:
        return parse_iso(str(v))
    except ValueError:
        return None


def _rank(rec: SettlementRecord) -> tuple[int, int, datetime]:
    return (0 if rec.engine_version == KALSHI_ENGINE_VERSION else 1, rec.box_stat_correction_version, rec.settled_at_utc)


def best_settlements(ledger: Ledger) -> dict[str, SettlementRecord]:
    """One record per ticker: engine records beat market-only ones, then newest stat correction, then newest."""
    best: dict[str, SettlementRecord] = {}
    for row in ledger.iter_rows("settlements"):
        try:
            rec = coerce(SettlementRecord, row)
        except (TypeError, ValueError):
            continue
        prev = best.get(rec.ticker)
        if prev is None or _rank(rec) >= _rank(prev):
            best[rec.ticker] = rec
    return best


def tip_times(ledger: Ledger) -> dict[str, datetime]:
    """Authoritative tip per game_id: box ``actual_tip_utc`` when archived, else the schedule ``start_time_utc``."""
    tips: dict[str, datetime] = {}
    for gid, g in latest_schedule(ledger).items():
        t = _dt(g.get("actual_tip_utc")) or _dt(g.get("start_time_utc"))
        if t is not None:
            tips[gid] = t
    for row in ledger.iter_rows("boxscores"):
        gid, t = row.get("game_id"), _dt(row.get("actual_tip_utc"))
        if gid and t is not None:
            tips[str(gid)] = t
    return tips


def _slim(row: dict[str, Any]) -> dict[str, Any]:
    """The fields evaluation reads from a market row, in cents.

    Boards captured since the Kalshi API moved to dollar strings carry ``yes_bid_dollars`` etc. and the cents view only
    under ``_quote_cents``; reading the bare ``yes_bid`` key therefore returned None for every closing quote and made
    the closing price (and so CLV and Kalshi's own calibration) permanently empty.
    """
    q = row.get("_quote_cents") or {}
    out = {k: row.get(k) for k in _OBS_KEYS}
    for k in ("yes_bid", "yes_ask", "no_bid", "no_ask", "last_price"):
        if out.get(k) is None and q.get(k) is not None:
            out[k] = q[k]
    return out


# How many ticks before the last pre-tip tick a ticker may be searched for when it was absent from that board (a
# market that is briefly paused disappears from the open list for a tick or two). The observation keeps its own
# `_observed_at_utc`, so the age of the close is never hidden.
CLOSING_LOOKBACK_TICKS = 12


def closing_observations(ledger: Ledger, wanted: dict[datetime, set[str]]) -> dict[str, list[dict[str, Any]]]:
    """For each tip, each wanted ticker's row on the last board observed STRICTLY before that tip.

    Replaces a pass over every tick of the archive (``observations_by_ticker``: 2,336 ticks x ~7,000 rows = 16M row
    visits, 8.6 minutes on the 2026-10-24 archive and linear in archive size, against a 15-minute job budget) with one
    reconstruction per distinct tip. Closing is the only observation evaluation uses: ``closing_snapshot`` returns the
    last observation strictly before tip and ``market_only_report`` uses the same.
    """
    ticks = sorted({entry_observed_at(e) for e in ledger.manifest() if e.kind in ("kalshi/markets", "kalshi/markets_delta")})
    out: dict[str, list[dict[str, Any]]] = {}
    for tip, tickers in wanted.items():
        before = [t for t in ticks if t < tip]
        remaining = set(tickers)
        for at in reversed(before[-CLOSING_LOOKBACK_TICKS:]):
            if not remaining:
                break
            try:
                rec = reconstruct_at(ledger.root, at)
            except DeltaChainError:
                continue
            for row in rec.rows:
                tk = row.get("ticker")
                if tk in remaining:
                    remaining.discard(tk)
                    slim = _slim(row)
                    slim["_observed_at_utc"] = rec.observed_at_utc
                    out.setdefault(tk, []).append(slim)
    return out


def observations_by_ticker(ledger: Ledger, tickers: set[str]) -> dict[str, list[dict[str, Any]]]:
    """Every observation of the tickers of interest, in observation order (full-archive pass; kept for research use)."""
    out: dict[str, list[dict[str, Any]]] = {}
    # Every TICK. The benchmark is "the raw executable price at the final valid pre-tip snapshot";
    # if delta-encoded ticks were invisible here, that instant would silently move earlier and the
    # frozen benchmark methodology would change without anyone editing it.
    for row in iter_market_rows(ledger):
        tk = row.get("ticker")
        if tk not in tickers or not row.get("_observed_at_utc"):
            continue
        out.setdefault(tk, []).append(_slim(row))
    for obs in out.values():
        obs.sort(key=lambda o: o["_observed_at_utc"])
    return out


def close_price_source(obs: dict[str, Any] | None) -> str | None:
    """``"mid"`` for a two-sided quote, ``"last_trade"`` when only a trade print exists, else None."""
    if obs is None:
        return None
    b, a = obs.get("yes_bid"), obs.get("yes_ask")
    if b is not None and a is not None and 0 <= b <= 100 and 0 <= a <= 100:
        return "mid"
    lp = obs.get("last_price")
    return "last_trade" if lp is not None and 0 <= lp <= 100 else None


def entry_mid_cents(bid: Any, ask: Any) -> float | None:
    """Midpoint of a two-sided quote (cents), None for a missing/one-sided/invalid book."""
    if bid is None or ask is None:
        return None
    try:
        b, a = float(bid), float(ask)
    except (TypeError, ValueError):
        return None
    return (b + a) / 2.0 if 0 <= b <= a <= 100 else None


def close_price_cents(obs: dict[str, Any] | None) -> float | None:
    """Mid of yes_bid/yes_ask, falling back to last_price. None when the snapshot carries no price."""
    if obs is None:
        return None
    b, a = obs.get("yes_bid"), obs.get("yes_ask")
    if b is not None and a is not None and 0 <= b <= 100 and 0 <= a <= 100:
        return (float(b) + float(a)) / 2.0
    lp = obs.get("last_price")
    if lp is not None and 0 <= lp <= 100:
        return float(lp)
    return None


# A pre-tip quote older than this when the forecast was made is not "the market at forecast time"; it is left unpriced.
PIT_QUOTE_MAX_AGE_S = 20 * 60


def pit_quote_fill(ledger: Ledger, pending: list[tuple[dict[str, Any], SettlementRecord, datetime]], deadline: float | None = None,
                   deferred_indices: set[int] | None = None,
                   ) -> tuple[dict[int, dict[str, Any]], dict[str, int]]:
    """Point-in-time Kalshi quotes for predictions whose own quote fields are empty (legacy simulator rows).

    For each such prediction the board used is the last tick at or before ``predicted_at_utc`` AND strictly before tip,
    reconstructed through the verified checkpoint+delta chain. Quotes older than ``PIT_QUOTE_MAX_AGE_S``, broken chains,
    absent tickers and one-sided books stay unpriced (fail closed): no later quote and no invented price is ever used.
    Returns ({index into pending: quote fields}, counters). When a runtime deadline defers
    a quote lookup, deferred_indices receives those prediction indexes; callers MUST
    retry rather than commit a permanently unpriced evaluation row.
    """
    stats = {"needs_quote": 0, "filled": 0, "no_board": 0, "stale": 0, "ticker_absent": 0, "one_sided": 0, "chain_error": 0, "deferred": 0}
    ticks = sorted({entry_observed_at(e) for e in ledger.manifest() if e.kind in ("kalshi/markets", "kalshi/markets_delta")})
    by_tick: dict[datetime, list[int]] = {}
    for i, (pred, _rec, tip) in enumerate(pending):
        if pred.get("p_market") is not None or pred.get("market_yes_ask") is not None:
            continue
        stats["needs_quote"] += 1
        pa = _dt(pred.get("predicted_at_utc"))
        if pa is None:
            stats["no_board"] += 1
            continue
        k = bisect.bisect_right(ticks, pa) - 1
        while k >= 0 and ticks[k] >= tip:
            k -= 1
        if k < 0:
            stats["no_board"] += 1
            continue
        if (pa - ticks[k]).total_seconds() > PIT_QUOTE_MAX_AGE_S:
            stats["stale"] += 1
            continue
        by_tick.setdefault(ticks[k], []).append(i)
    out: dict[int, dict[str, Any]] = {}
    for at, idxs in sorted(by_tick.items()):
        if deadline is not None and time.monotonic() > deadline:
            stats["deferred"] += len(idxs)
            if deferred_indices is not None:
                deferred_indices.update(idxs)
            continue
        try:
            rec = reconstruct_at(ledger.root, at)
        except DeltaChainError:
            stats["chain_error"] += len(idxs)
            continue
        board = {r.get("ticker"): _slim(r) for r in rec.rows}
        for i in idxs:
            q = board.get(pending[i][0].get("ticker"))
            if q is None:
                stats["ticker_absent"] += 1
                continue
            mid = entry_mid_cents(q.get("yes_bid"), q.get("yes_ask"))
            if mid is None or q.get("no_ask") is None or q.get("no_bid") is None:
                stats["one_sided"] += 1
                continue
            out[i] = {"market_yes_bid": q["yes_bid"], "market_yes_ask": q["yes_ask"], "market_no_bid": q["no_bid"], "market_no_ask": q["no_ask"],
                      "p_market": mid / 100.0, "market_observed_at_utc": rec.observed_at_utc, "quote_source": "PIT_BOARD_RECONSTRUCTED"}
            stats["filled"] += 1
    return out, stats


# ---- row construction ------------------------------------------------------------------------------


def _hours_bucket(h: float | None) -> str | None:
    if h is None:
        return None
    for name, lo, hi in HOUR_BUCKETS:
        if lo <= h < hi:
            return name
    return None


def build_evaluation_row(pred: dict[str, Any], rec: SettlementRecord, tip: datetime, observations: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Join one prediction with its settlement (YES/NO only), tip and market observations."""
    if rec.outcome not in (SettlementOutcome.YES, SettlementOutcome.NO):
        return None
    predicted_at = _dt(pred.get("predicted_at_utc"))
    if predicted_at is None:
        return None
    mkt_at = _dt(pred.get("market_observed_at_utc"))
    pregame = predicted_at < tip and (mkt_at is None or mkt_at < tip)
    closing = closing_snapshot(observations, tip)
    close_c = close_price_cents(closing)
    yes_ask, no_ask = pred.get("market_yes_ask"), pred.get("market_no_ask")
    clv_yes = clv_no = None
    if close_c is not None:
        if yes_ask is not None and 0 <= yes_ask <= 100:
            clv_yes = clv_prob(float(yes_ask), close_c, "yes")
        if no_ask is not None and 0 <= no_ask <= 100:
            clv_no = clv_prob(100.0 - float(no_ask), close_c, "no")
    src = close_price_source(closing)
    sel_yes = sel_no = None
    ymid = entry_mid_cents(pred.get("market_yes_bid"), yes_ask)
    if close_c is not None and src == "mid" and ymid is not None:
        sel_yes = (close_c - ymid) / 100.0          # YES axis; NO is the mirror image
        sel_no = -sel_yes
    hours = (tip - predicted_at).total_seconds() / 3600.0
    return {
        "prediction_id": pred.get("prediction_id"),
        "settlement_key": rec.idempotency_key,
        "ticker": rec.ticker,
        "game_id": pred.get("game_id") or rec.game_id,
        "family": pred.get("family"),
        "model_version": pred.get("model_version"),
        "predicted_at_utc": iso(predicted_at),
        "tip_utc": iso(tip),
        "pregame": bool(pregame),
        "y": 1 if rec.outcome == SettlementOutcome.YES else 0,
        "p_data_only": pred.get("p_data_only"),
        "p_market": pred.get("p_market"),
        "p_hybrid": pred.get("p_hybrid"),
        "p_production": pred.get("p_production"),
        "entry_yes_ask": yes_ask,
        "market_observed_at_utc": pred.get("market_observed_at_utc"),
        "quote_source": pred.get("quote_source"),
        "entry_no_ask": no_ask,
        "close_prob": None if close_c is None else close_c / 100.0,
        "close_observed_at_utc": None if closing is None else closing.get("_observed_at_utc"),
        "clv_yes_prob": clv_yes,
        "clv_no_prob": clv_no,
        "clv_basis": "quoted_execution: close_mid - entry_ask, pre-fee, includes entry half-spread",
        "quoted_execution_clv_yes_prob": clv_yes,
        "quoted_execution_clv_no_prob": clv_no,
        "selection_clv_yes_prob": sel_yes,
        "selection_clv_no_prob": sel_no,
        "close_price_source": src,
        "hours_before_tip": hours,
        "settlement_engine": rec.engine_version,
    }


def signed_clv(row: dict[str, Any], p: float | None) -> float | None:
    """CLV for the side a probability ``p`` favours versus the market (``p_market``, else 0.5)."""
    if p is None:
        return None
    ref = row.get("p_market")
    ref = 0.5 if ref is None else float(ref)
    return row.get("clv_yes_prob") if p > ref else row.get("clv_no_prob")


def signed_selection_clv(row: dict[str, Any], p: float | None) -> float | None:
    """Selection CLV (close mid - entry mid, no spread, no fee) for the side ``p`` favours versus the market."""
    if p is None:
        return None
    ref = row.get("p_market")
    ref = 0.5 if ref is None else float(ref)
    return row.get("selection_clv_yes_prob") if p > ref else row.get("selection_clv_no_prob")


# ---- metrics --------------------------------------------------------------------------------------


def _metrics(p: list[float], y: list[int], bins: int = 10, with_table: bool = True) -> dict[str, Any]:
    if not p:
        return {"n": 0}
    pa, ya = np.asarray(p, dtype=float), np.asarray(y, dtype=float)
    out: dict[str, Any] = {
        "n": int(pa.size), "mean_p": float(pa.mean()), "mean_y": float(ya.mean()), "brier": brier(pa, ya), "log_loss": log_loss(pa, ya),
        "ece": ece(pa, ya, bins), "sharpness": sharpness(pa),
    }
    try:
        slope, intercept = reliability_slope_intercept(pa, ya)
        out["reliability_slope"], out["reliability_intercept"] = _finite(slope), _finite(intercept)
    except (ValueError, FloatingPointError, np.linalg.LinAlgError):
        out["reliability_slope"] = out["reliability_intercept"] = None
    if with_table:
        out["calibration_table"] = calibration_table(pa, ya, bins)
    return out


def _finite(x: float) -> float | None:
    return float(x) if np.isfinite(x) else None


def _mean(xs: list[float]) -> float | None:
    return float(np.mean(xs)) if xs else None


def view_metrics(rows: list[dict[str, Any]], view: View) -> dict[str, Any]:
    """Metrics for one model view over pregame rows that carry that probability."""
    key = VIEW_PROB_KEY[view]
    used = [r for r in rows if r.get(key) is not None]
    p = [float(r[key]) for r in used]
    y = [int(r["y"]) for r in used]
    out = _metrics(p, y)
    out["view"] = view.value
    if view != View.MARKET_BASELINE:
        mkt = [r for r in used if r.get("p_market") is not None]
        if mkt:
            pm = [float(r["p_market"]) for r in mkt]
            out["n_with_market"] = len(mkt)
            out["brier_market"] = brier(pm, [int(r["y"]) for r in mkt])
            out["brier_skill_vs_market"] = _finite(brier_skill_score([float(r[key]) for r in mkt], [int(r["y"]) for r in mkt], pm))
        else:
            out["n_with_market"], out["brier_market"], out["brier_skill_vs_market"] = 0, None, None
        clvs = [c for c in (signed_clv(r, float(r[key])) for r in used) if c is not None]
        out["n_with_clv"], out["clv_mean"] = len(clvs), _mean(clvs)
        out["clv_mean_basis"] = "quoted_execution (close_mid - entry_ask; pre-fee; includes half-spread)"
        sels = [c for c in (signed_selection_clv(r, float(r[key])) for r in used) if c is not None]
        out["n_with_selection_clv"], out["selection_clv_mean"] = len(sels), _mean(sels)
    else:
        out["n_with_clv"], out["clv_mean"] = 0, None
        out["n_with_selection_clv"], out["selection_clv_mean"] = 0, None
    out["by_hours_bucket"] = _by_hours(used, key)
    out["by_prob_bucket"] = _by_prob(used, key)
    return out


def _by_hours(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, _, _ in HOUR_BUCKETS:
        sub = [r for r in rows if _hours_bucket(r.get("hours_before_tip")) == name]
        m = _metrics([float(r[key]) for r in sub], [int(r["y"]) for r in sub], with_table=False)
        mkt = [r for r in sub if r.get("p_market") is not None]
        m["brier_skill_vs_market"] = (
            _finite(brier_skill_score([float(r[key]) for r in mkt], [int(r["y"]) for r in mkt], [float(r["p_market"]) for r in mkt])) if mkt and key != "p_market" else None
        )
        m["clv_mean"] = _mean([c for c in (signed_clv(r, float(r[key])) for r in sub) if c is not None]) if key != "p_market" else None
        out[name] = m
    return out


def _by_prob(rows: list[dict[str, Any]], key: str, bins: int = 10) -> list[dict[str, Any]]:
    out = []
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        sub = [r for r in rows if lo <= float(r[key]) < hi or (b == bins - 1 and float(r[key]) == 1.0)]
        p, y = [float(r[key]) for r in sub], [int(r["y"]) for r in sub]
        out.append({"bin_lo": lo, "bin_hi": hi, "n": len(sub), "mean_p": _mean(p), "mean_y": _mean([float(v) for v in y]), "brier": brier(p, y) if p else None})
    return out


def _authority_p(r: dict[str, Any]) -> float | None:
    for k in ("p_production", "p_hybrid", "p_data_only"):
        if r.get(k) is not None:
            return float(r[k])
    return None


def authority_rows(rows: list[dict[str, Any]]) -> list[EvaluationRow]:
    out = []
    for r in rows:
        p = _authority_p(r)
        if p is None or not r.get("pregame"):
            continue
        out.append(EvaluationRow(family=str(r.get("family")), ticker=str(r["ticker"]), p=p, y=int(r["y"]), p_market=r.get("p_market"), clv=signed_clv(r, p), pregame=True))
    return out


def build_report(rows: list[dict[str, Any]], now: datetime, n_new: int) -> dict[str, Any]:
    pregame = [r for r in rows if r.get("pregame")]
    families = sorted({str(r.get("family")) for r in rows})
    ledger = AuthorityLedger(authority_rows(pregame))
    auth = ledger.report()
    fam_reports: dict[str, Any] = {}
    for fam in families:
        fr = [r for r in pregame if str(r.get("family")) == fam]
        fam_reports[fam] = {
            "n": sum(str(r.get("family")) == fam for r in rows),
            "n_pregame": len(fr),
            "n_post_tip_excluded": sum(str(r.get("family")) == fam for r in rows) - len(fr),
            "views": {v.value: view_metrics(fr, v) for v in VIEW_PROB_KEY},
            "authority": auth.get(fam, {"family": fam, "n_settled_predictions": 0, "stage": "RESEARCH"}),
        }
    return {
        "evaluated_at_utc": iso(now),
        "n_rows": len(rows),
        "n_pregame": len(pregame),
        "n_new_rows": n_new,
        "families": fam_reports,
        "overall": {"views": {v.value: view_metrics(pregame, v) for v in VIEW_PROB_KEY}},
        "authority": auth,
    }


# ---- market-only calibration --------------------------------------------------------------------------


def market_close_entries(settlements: dict[str, SettlementRecord], tips: dict[str, datetime], obs: dict[str, list[dict[str, Any]]], families: dict[str, str],
                         only: set[str] | None = None) -> dict[str, list[Any]]:
    """``ticker -> [close_prob | None, y, family]`` for market-only (engine 'kalshi') YES/NO settlements. Closing = last
    observation strictly before tip when the game is known, else the last observation while the market was still 'open'."""
    out: dict[str, list[Any]] = {}
    for tk, rec in settlements.items():
        if only is not None and tk not in only:
            continue
        if rec.engine_version != KALSHI_ENGINE_VERSION or rec.outcome not in (SettlementOutcome.YES, SettlementOutcome.NO):
            continue
        observations = obs.get(tk, [])
        tip = tips.get(rec.game_id) if rec.game_id else None
        closing = closing_snapshot(observations, tip) if tip is not None else _last_open(observations)
        c = close_price_cents(closing)
        out[tk] = [None if c is None else c / 100.0, 1 if rec.outcome == SettlementOutcome.YES else 0, families.get(tk) or "unknown"]
    return out


def market_only_from_entries(entries: dict[str, list[Any]]) -> dict[str, Any]:
    by_family: dict[str, tuple[list[float], list[int]]] = {}
    n_no_close = 0
    for c, y, fam in entries.values():
        if c is None:
            n_no_close += 1
            continue
        for k in (fam, "ALL"):
            ps, ys = by_family.setdefault(k, ([], []))
            ps.append(c)
            ys.append(y)
    return {"n_without_close": n_no_close, "families": {k: _metrics(ps, ys) for k, (ps, ys) in sorted(by_family.items())}}


def market_only_report(settlements: dict[str, SettlementRecord], tips: dict[str, datetime], obs: dict[str, list[dict[str, Any]]], families: dict[str, str]) -> dict[str, Any]:
    """How well-calibrated is Kalshi's own closing price? (uncached; ``run_evaluate`` caches per ticker)."""
    return market_only_from_entries(market_close_entries(settlements, tips, obs, families))


def _last_open(observations: list[dict[str, Any]]) -> dict[str, Any] | None:
    opened = [o for o in observations if o.get("status") == "open"]
    return opened[-1] if opened else None


# ---- markdown ---------------------------------------------------------------------------------------


def _fmt(x: Any, nd: int = 4) -> str:
    if x is None:
        return "-"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def report_markdown(report: dict[str, Any]) -> str:
    lines = [f"# Evaluation report ({report['evaluated_at_utc']})", "",
             f"rows={report['n_rows']} pregame={report['n_pregame']} new_this_run={report['n_new_rows']}", ""]
    for fam, fr in report["families"].items():
        a = fr["authority"]
        lines += [f"## {fam}", "", f"n={fr['n']} pregame={fr['n_pregame']} excluded_post_tip={fr['n_post_tip_excluded']} authority={a.get('stage')}", "",
                  "| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |", "|---|---|---|---|---|---|---|"]
        for v, m in fr["views"].items():
            lines.append(f"| {v} | {m.get('n', 0)} | {_fmt(m.get('brier'))} | {_fmt(m.get('log_loss'))} | {_fmt(m.get('ece'))} | {_fmt(m.get('brier_skill_vs_market'))} | {_fmt(m.get('clv_mean'))} |")
        lines.append("")
        lines += ["| view | bucket | n | brier | skill_vs_market | clv_mean |", "|---|---|---|---|---|---|"]
        for v, m in fr["views"].items():
            for b, bm in m.get("by_hours_bucket", {}).items():
                lines.append(f"| {v} | {b} | {bm.get('n', 0)} | {_fmt(bm.get('brier'))} | {_fmt(bm.get('brier_skill_vs_market'))} | {_fmt(bm.get('clv_mean'))} |")
        lines.append("")
    return "\n".join(lines) + "\n"


# ---- job ------------------------------------------------------------------------------------------


def run_evaluate(out_root: Path, data_root: Path, now: datetime | None = None) -> int:
    out_root = Path(out_root)
    now = now or utcnow()
    # Fail closed on the mistake that made this job a silent no-op in production: pointing --out at the reports directory
    # (<archive>/eval) instead of the ledger root. An empty ledger evaluates 0 rows and "succeeds", which looks identical
    # to "nothing is settled yet".
    parent_manifest = out_root.parent / "manifest.jsonl"
    if out_root.name == "eval" and not (out_root / "manifest.jsonl").exists() and parent_manifest.exists():
        print(f"evaluate: --out {out_root} is the reports directory, not the ledger root; the ledger is {out_root.parent}")
        return 2
    ledger = Ledger(out_root)
    max_new = int(os.environ.get("NBA_EVAL_MAX_NEW_ROWS", DEFAULT_MAX_NEW_ROWS))
    budget_s = float(os.environ.get("NBA_EVAL_BUDGET_S", DEFAULT_BUDGET_S))
    t0 = time.monotonic()

    settlements = best_settlements(ledger)
    tips = tip_times(ledger)
    # Streamed, never listed: 2M predictions / 1.4M evaluations do not fit in memory as dicts (the unbounded version was OOM-killed).
    seen: set[tuple[Any, Any]] = set()
    report_rows: list[dict[str, Any]] = []
    for r in ledger.iter_rows("evaluations"):
        seen.add((r.get("prediction_id"), r.get("settlement_key")))
        report_rows.append({k: r.get(k) for k in _REPORT_KEYS})

    # Pass 1 (no market data), NEWEST partitions first: which (prediction, settlement) pairs are new? At most ``max_new`` are taken per
    # run; the remainder is a backlog that later runs drain (idempotent via ``seen``), so one run never exceeds its time budget.
    pending: list[tuple[dict[str, Any], SettlementRecord, datetime]] = []
    n_skipped = {"unsettled": 0, "no_tip": 0, "invalid": 0}
    n_eligible = 0  # predictions with a YES/NO settlement and a known tip: if these exist, an empty evaluation is an error
    backlog = 0
    wanted: dict[datetime, set[str]] = {}
    for pred in iter_rows_newest_first(ledger, "predictions"):
        tk = pred.get("ticker")
        rec = settlements.get(tk) if tk else None
        if rec is None or rec.outcome not in (SettlementOutcome.YES, SettlementOutcome.NO):
            n_skipped["unsettled"] += 1
            continue
        gid = pred.get("game_id") or rec.game_id
        tip = tips.get(str(gid)) if gid else None
        if tip is None:
            n_skipped["no_tip"] += 1
            continue
        n_eligible += 1
        if (pred.get("prediction_id"), rec.idempotency_key) in seen:
            continue
        if len(pending) >= max_new or time.monotonic() - t0 > budget_s * 0.35:
            backlog += 1
            continue
        pending.append((pred, rec, tip))
        wanted.setdefault(tip, set()).add(tk)

    # Market-only closes are cached per ticker (a close never changes once the game has tipped), so only newly settled tickers
    # cost a board reconstruction.
    cache_path = out_root / "eval" / "market_close_cache.json"
    try:
        cache: dict[str, list[Any]] = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    except (OSError, ValueError):
        cache = {}
    market_only_tickers = {
        tk for tk, rec in settlements.items()
        if rec.engine_version == KALSHI_ENGINE_VERSION and rec.outcome in (SettlementOutcome.YES, SettlementOutcome.NO) and tk not in cache
    }
    n_market_deferred = 0
    for tk in sorted(market_only_tickers):
        rec = settlements[tk]
        t = tips.get(rec.game_id) if rec.game_id else None
        if t is not None:
            if time.monotonic() - t0 > budget_s * 0.6:
                market_only_tickers.discard(tk)  # over budget: stays uncached, picked up by the next run
                n_market_deferred += 1
                continue
            wanted.setdefault(t, set()).add(tk)
    obs = closing_observations(ledger, wanted)
    no_tip = {tk for tk in market_only_tickers if not (settlements[tk].game_id and tips.get(settlements[tk].game_id))}
    if no_tip:  # market-only settlements of games with no known tip are closed on "last open observation": needs the full history
        obs.update(observations_by_ticker(ledger, no_tip))
    families_by_ticker = {tk: str(o[-1].get("_family") or "") for tk, o in obs.items() if o}
    cache.update(market_close_entries(settlements, tips, obs, families_by_ticker, only=market_only_tickers))

    deferred_indices: set[int] = set()
    fills, quote_stats = pit_quote_fill(ledger, pending, deadline=t0 + budget_s * 0.8,
                                       deferred_indices=deferred_indices)
    new_rows: list[dict[str, Any]] = []
    for i, (pred, rec, tip) in enumerate(pending):
        if i in deferred_indices:
            # This prediction has not had its PIT market quote checked. Do NOT append
            # a permanently unpriced row: leave its key unseen so the next run retries it.
            backlog += 1
            continue
        if i in fills:
            pred = {**pred, **fills[i]}
        tk = pred.get("ticker")
        row = build_evaluation_row(pred, rec, tip, obs.get(tk, []))
        if row is None:
            n_skipped["invalid"] += 1
            continue
        key = (row["prediction_id"], row["settlement_key"])
        if key in seen:
            continue
        seen.add(key)
        new_rows.append(row)
        report_rows.append({k: row.get(k) for k in _REPORT_KEYS})
    if new_rows:
        e = ledger.append_rows("evaluations", new_rows, observed_at=now, meta={"n": len(new_rows)})
        log.info(kv(event="evaluations_written", path=e.path, rows=e.rows))

    report = build_report(report_rows, now, len(new_rows))
    report["skipped"] = n_skipped
    report["pit_quote_fill"] = quote_stats
    n_mkt = sum(1 for r in report_rows if r.get("p_market") is not None)
    report["n_rows_with_market_baseline"] = n_mkt
    market_only = market_only_from_entries(cache)
    eval_dir = out_root / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache))
    (eval_dir / "report.json").write_text(json.dumps(report, indent=1, default=str))
    (eval_dir / "report.md").write_text(report_markdown(report))
    (eval_dir / "market_only.json").write_text(json.dumps(market_only, indent=1, default=str))
    complete = backlog == 0 and n_market_deferred == 0
    status = {
        "evaluated_at_utc": iso(now), "n_rows": len(report_rows), "n_pregame": report["n_pregame"], "n_new_rows": len(new_rows),
        "families": sorted(report["families"]), "skipped": n_skipped, "run_id": ledger.run_id,
        "n_eligible_settled_predictions": n_eligible, "backlog_remaining": backlog, "market_closes_deferred": n_market_deferred,
        "complete": complete, "quote_fills_deferred": len(deferred_indices),
        "elapsed_s": round(time.monotonic() - t0, 1),
    }
    (out_root / "STATUS_evaluate.json").write_text(json.dumps(status, indent=1, default=str))
    print(json.dumps(status, indent=1, default=str))
    if report_rows and n_mkt == 0:
        print(f"evaluate: WARNING - {len(report_rows)} evaluation rows but ZERO carry a market baseline; market-vs-model comparisons are unavailable ({quote_stats})")
    if n_eligible > 0 and len(report_rows) == 0:
        # Never a silent success: settled, tipped predictions exist but nothing was evaluated.
        print(f"evaluate: FAILED - {n_eligible} eligible settled predictions but 0 evaluation rows")
        return 3
    return 0
