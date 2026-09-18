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
- CLV is reported for a hypothetical YES bought at the prediction-time ``market_yes_ask`` and a hypothetical NO
  bought at ``market_no_ask``; the per-view "signed" CLV picks the side the view favoured versus the market.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from nba_edge.archive.ledger import Ledger
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
HOUR_BUCKETS = (("<1h", 0.0, 1.0), ("1-6h", 1.0, 6.0), ("6-24h", 6.0, 24.0), (">24h", 24.0, float("inf")))
_OBS_KEYS = ("ticker", "yes_bid", "yes_ask", "no_bid", "no_ask", "last_price", "status", "result", "_family", "_observed_at_utc")


# ---- loading --------------------------------------------------------------------------------------


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


def observations_by_ticker(ledger: Ledger, tickers: set[str]) -> dict[str, list[dict[str, Any]]]:
    """Slim market observations for the tickers of interest, in observation order."""
    out: dict[str, list[dict[str, Any]]] = {}
    for row in ledger.iter_rows("kalshi/markets"):
        tk = row.get("ticker")
        if tk not in tickers or not row.get("_observed_at_utc"):
            continue
        out.setdefault(tk, []).append({k: row.get(k) for k in _OBS_KEYS})
    for obs in out.values():
        obs.sort(key=lambda o: o["_observed_at_utc"])
    return out


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
        "entry_no_ask": no_ask,
        "close_prob": None if close_c is None else close_c / 100.0,
        "close_observed_at_utc": None if closing is None else closing.get("_observed_at_utc"),
        "clv_yes_prob": clv_yes,
        "clv_no_prob": clv_no,
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
    else:
        out["n_with_clv"], out["clv_mean"] = 0, None
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


def market_only_report(settlements: dict[str, SettlementRecord], tips: dict[str, datetime], obs: dict[str, list[dict[str, Any]]], families: dict[str, str]) -> dict[str, Any]:
    """How well-calibrated is Kalshi's own closing price? Computed over market-only (engine 'kalshi') YES/NO
    settlements. Closing = last observation strictly before tip when the game is known, else the last
    observation while the market was still 'open'."""
    by_family: dict[str, tuple[list[float], list[int]]] = {}
    n_no_close = 0
    for tk, rec in settlements.items():
        if rec.engine_version != KALSHI_ENGINE_VERSION or rec.outcome not in (SettlementOutcome.YES, SettlementOutcome.NO):
            continue
        observations = obs.get(tk, [])
        tip = tips.get(rec.game_id) if rec.game_id else None
        closing = closing_snapshot(observations, tip) if tip is not None else _last_open(observations)
        c = close_price_cents(closing)
        if c is None:
            n_no_close += 1
            continue
        fam = families.get(tk) or "unknown"
        for k in (fam, "ALL"):
            ps, ys = by_family.setdefault(k, ([], []))
            ps.append(c / 100.0)
            ys.append(1 if rec.outcome == SettlementOutcome.YES else 0)
    return {"n_without_close": n_no_close, "families": {k: _metrics(ps, ys) for k, (ps, ys) in sorted(by_family.items())}}


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
    ledger = Ledger(out_root)

    settlements = best_settlements(ledger)
    tips = tip_times(ledger)
    predictions = list(ledger.iter_rows("predictions"))
    tickers = set(settlements)
    obs = observations_by_ticker(ledger, tickers)
    families_by_ticker = {tk: str(o[-1].get("_family") or "") for tk, o in obs.items() if o}

    existing_rows = list(ledger.iter_rows("evaluations"))
    seen = {(r.get("prediction_id"), r.get("settlement_key")) for r in existing_rows}
    new_rows: list[dict[str, Any]] = []
    n_skipped = {"unsettled": 0, "no_tip": 0, "invalid": 0}
    for pred in predictions:
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
        row = build_evaluation_row(pred, rec, tip, obs.get(tk, []))
        if row is None:
            n_skipped["invalid"] += 1
            continue
        key = (row["prediction_id"], row["settlement_key"])
        if key in seen:
            continue
        seen.add(key)
        new_rows.append(row)
    if new_rows:
        e = ledger.append_rows("evaluations", new_rows, observed_at=now, meta={"n": len(new_rows)})
        log.info(kv(event="evaluations_written", path=e.path, rows=e.rows))

    all_rows = existing_rows + new_rows
    report = build_report(all_rows, now, len(new_rows))
    report["skipped"] = n_skipped
    market_only = market_only_report(settlements, tips, obs, families_by_ticker)
    eval_dir = out_root / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)
    (eval_dir / "report.json").write_text(json.dumps(report, indent=1, default=str))
    (eval_dir / "report.md").write_text(report_markdown(report))
    (eval_dir / "market_only.json").write_text(json.dumps(market_only, indent=1, default=str))
    status = {
        "evaluated_at_utc": iso(now), "n_rows": len(all_rows), "n_pregame": report["n_pregame"], "n_new_rows": len(new_rows),
        "families": sorted(report["families"]), "skipped": n_skipped, "run_id": ledger.run_id,
    }
    (out_root / "STATUS_evaluate.json").write_text(json.dumps(status, indent=1, default=str))
    print(json.dumps(status, indent=1, default=str))
    return 0
