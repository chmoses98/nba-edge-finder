"""All-market, point-in-time postmortem (issue #95). READ-ONLY over the archive; writes only a derived view.

Universe: every Kalshi ticker observed for an ET-date slate (union of contracts, predictions, settlements and the
pre-tip boards). Every ticker is either GRADED or carries exactly one ungraded reason; the reconciliation
``universe == graded + sum(ungraded)`` is asserted. An evaluation with eligible inputs but zero graded rows is
``BLOCKED`` (exit 3), never success.

Point in time: a prediction joins the newest archived board at or before ``predicted_at`` and strictly before tip;
late predictions/boards are refused and counted. Missing quotes or model probabilities are never filled from later data.
Economics: hypothetical taker P&L at the captured ask, with the exact Kalshi taker fee charged once. Nothing here is a
fill. Actual-fill CLV needs fill evidence the archive does not hold and is reported as n=0.
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from nba_edge.archive.delta import DeltaChainError
from nba_edge.archive.ledger import Ledger, entry_observed_at
from nba_edge.archive.reconstruct import reconstruct_at
from nba_edge.kalshi.fees import taker_fee_cents
from nba_edge.timeutil import parse_iso

HORIZONS = (("<1h", 0.0, 1.0), ("1-3h", 1.0, 3.0), ("3-6h", 3.0, 6.0), ("6-24h", 6.0, 24.0), (">24h", 24.0, 1e9))
PRICE_BINS = ((0, 10), (10, 25), (25, 40), (40, 60), (60, 75), (75, 90), (90, 101))
MAX_PASS_LOOKBACK_H = 30.0
MIN_CLUSTERS_FOR_CI = 5
EXIT_OK, EXIT_BLOCKED = 0, 3


# ---- pure helpers (unit-tested) ---------------------------------------------------------------------


def quote_cents(row: dict[str, Any] | None) -> dict[str, float | None]:
    """Executable quotes in cents from a board row: ``_quote_cents`` > ``*_dollars`` > legacy cent ints.

    Prices outside the open interval (0, 100) are not executable and become ``None`` (a 0/100 ask is a placeholder).
    """
    out: dict[str, float | None] = {k: None for k in ("yes_bid", "yes_ask", "no_bid", "no_ask")}
    if not row:
        return out
    q = row.get("_quote_cents") or {}
    for k in out:
        v: float | None = None
        if q.get(k) is not None:
            v = float(q[k])
        elif row.get(f"{k}_dollars") not in (None, ""):
            try:
                v = float(row[f"{k}_dollars"]) * 100.0
            except (TypeError, ValueError):
                v = None
        elif row.get(k) is not None:
            try:
                v = float(row[k])
            except (TypeError, ValueError):
                v = None
        out[k] = v if v is not None and 0.0 < v < 100.0 else None
    return out


def side_ask(q: dict[str, float | None], side: str) -> float | None:
    """Executable ask for taking ``side``; derived from the opposite bid only when it is a complementary quote."""
    direct = q.get(f"{side}_ask")
    if direct is not None:
        return direct
    other = q.get("no_bid" if side == "yes" else "yes_bid")
    return None if other is None else 100.0 - other


def midpoint(q: dict[str, float | None]) -> float | None:
    """Yes-side midpoint, only from a valid two-sided pair (bid < ask)."""
    b, a = q.get("yes_bid"), q.get("yes_ask")
    return (b + a) / 2.0 if b is not None and a is not None and b < a else None


def fee_dollars_per_contract(price_cents: float) -> float:
    """Exact taker fee charged once, amortised from a 100-contract order (the per-order ceiling is not per-contract)."""
    p = int(round(price_cents))
    return taker_fee_cents(p, 100) / 100.0 / 100.0


def hypothetical_pnl(side: str, price_cents: float, outcome_yes: bool) -> float:
    """Per-contract P&L, dollars, of taking ``side`` at ``price_cents`` after the exact fee, once."""
    won = outcome_yes if side == "yes" else not outcome_yes
    return (1.0 if won else 0.0) - price_cents / 100.0 - fee_dollars_per_contract(price_cents)


def breakeven_prob(price_cents: float) -> float:
    return price_cents / 100.0 + fee_dollars_per_contract(price_cents)


def horizon_bucket(hours_to_tip: float) -> str:
    for name, lo, hi in HORIZONS:
        if lo <= hours_to_tip < hi:
            return name
    return ">24h"


def price_bin(p: float) -> str:
    c = p * 100.0
    for lo, hi in PRICE_BINS:
        if lo <= c < hi:
            return f"{lo}-{min(hi, 100)}"
    return "90-100"


def cluster_bootstrap_mean(values: list[float], clusters: list[str], n_boot: int = 2000, seed: int = 7) -> dict[str, Any]:
    """Mean with a game-clustered bootstrap 95% interval (resamples games, not rows)."""
    if not values:
        return {"n": 0, "n_clusters": 0, "mean": None, "ci95": None}
    by: dict[str, list[float]] = defaultdict(list)
    for v, c in zip(values, clusters, strict=True):
        by[c].append(v)
    groups = [np.array(x) for x in by.values()]
    mean = float(np.mean(values))
    if len(groups) < MIN_CLUSTERS_FOR_CI:
        return {"n": len(values), "n_clusters": len(groups), "mean": mean, "ci95": None}
    rng = np.random.default_rng(seed)
    sums = np.array([g.sum() for g in groups])
    cnt = np.array([len(g) for g in groups])
    idx = rng.integers(0, len(groups), size=(n_boot, len(groups)))
    means = sums[idx].sum(axis=1) / cnt[idx].sum(axis=1)
    return {"n": len(values), "n_clusters": len(groups), "mean": mean,
            "ci95": [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]}


def cluster_bootstrap_ratio(num: list[float], den: list[float], clusters: list[str], n_boot: int = 2000, seed: int = 7) -> dict[str, Any]:
    """Pooled ratio sum(num)/sum(den) (e.g. net P&L / total stake) with a game-clustered bootstrap 95% interval."""
    if not num or sum(den) <= 0:
        return {"n": len(num), "n_clusters": 0, "mean": None, "ci95": None}
    a: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])
    for n_, d_, c in zip(num, den, clusters, strict=True):
        a[c][0] += n_
        a[c][1] += d_
    arr = np.array(list(a.values()))
    ratio = float(arr[:, 0].sum() / arr[:, 1].sum())
    if len(arr) < MIN_CLUSTERS_FOR_CI:
        return {"n": len(num), "n_clusters": len(arr), "mean": ratio, "ci95": None}
    idx = np.random.default_rng(seed).integers(0, len(arr), size=(n_boot, len(arr)))
    boots = arr[:, 0][idx].sum(axis=1) / arr[:, 1][idx].sum(axis=1)
    return {"n": len(num), "n_clusters": len(arr), "mean": ratio, "ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]}


def skill_flag(delta_brier: float | None, ci: list[float] | None, n_clusters: int) -> str:
    """Colour code of (market Brier - model Brier): positive = model better. Green only when the CI excludes 0."""
    if delta_brier is None:
        return "⚪"
    if ci is None or n_clusters < MIN_CLUSTERS_FOR_CI:
        return "🟡" if delta_brier > 0 else "🔴"
    if ci[0] > 0:
        return "🟢"
    if ci[1] < 0:
        return "🔴"
    return "🟡"


# ---- loading ---------------------------------------------------------------------------------------


@dataclass
class Game:
    game_id: str
    away: str
    home: str
    tip: datetime
    date_code: str  # e.g. 26NOV08


def _latest(rows, key):  # newest row per key by _observed_at_utc
    best: dict[str, dict[str, Any]] = {}
    for r in rows:
        k = r.get(key)
        if k and (k not in best or str(r.get("_observed_at_utc") or "") >= str(best[k].get("_observed_at_utc") or "")):
            best[k] = r
    return best


def load_games(ledger: Ledger, date_et: str) -> list[Game]:
    """Games by ET game date (not by UTC partition)."""
    sched = _latest(ledger.iter_rows("context/schedule"), "game_id")
    d = datetime.strptime(date_et, "%Y-%m-%d")
    code = d.strftime("%y%b%d").upper()
    out = []
    for gid, g in sched.items():
        if g.get("game_date_et") != date_et:
            continue
        tip_s = g.get("actual_tip_utc") or g.get("start_time_utc")
        if not tip_s:
            continue
        out.append(Game(gid, str(g.get("away_tricode")), str(g.get("home_tricode")), parse_iso(tip_s), code))
    return sorted(out, key=lambda g: g.tip)


def _ticker_game(ticker: str, games: list[Game]) -> Game | None:
    for g in games:
        if f"{g.date_code}{g.away}{g.home}" in ticker:
            return g
    return None


def classify_family(ticker: str) -> str:
    series = ticker.split("-")[0]
    return f"unmapped:{series}"


# ---- the audit -------------------------------------------------------------------------------------


def audit_date(archive: Path, date_et: str, out_dir: Path, now: datetime | None = None) -> dict[str, Any]:
    ledger = Ledger(Path(archive))
    games = load_games(ledger, date_et)
    game_ids = {g.game_id for g in games}
    by_id = {g.game_id: g for g in games}
    if not games:
        return _blocked(out_dir, date_et, "no games with this ET game date in the archived schedule")

    contracts = {t: r for t, r in _latest(ledger.iter_rows("contracts"), "ticker").items() if r.get("game_id") in game_ids}
    preds_all = [p for p in ledger.iter_rows("predictions") if p.get("game_id") in game_ids]
    settle_rows: dict[str, dict[str, Any]] = {}
    for r in ledger.iter_rows("settlements"):
        tk = r.get("ticker")
        if not tk or r.get("game_id") not in game_ids:
            continue
        prev = settle_rows.get(tk)
        rank = (0 if r.get("engine_version") == "kalshi" else 1, int(r.get("box_stat_correction_version") or 0), str(r.get("settled_at_utc")))
        if prev is None or rank >= prev["_rank"]:
            settle_rows[tk] = {**r, "_rank": rank}

    # pass times -> boards at/before each pass (strictly pre-tip), plus the closing board per game
    ticks = sorted({entry_observed_at(e) for e in ledger.manifest() if e.kind in ("kalshi/markets", "kalshi/markets_delta")})
    board_cache: dict[datetime, dict[str, dict[str, Any]]] = {}
    board_obs: dict[datetime, str] = {}

    def board_at(t: datetime) -> tuple[dict[str, dict[str, Any]], str] | None:
        if t not in board_cache:
            try:
                rec = reconstruct_at(ledger.root, t)
            except (DeltaChainError, KeyError, ValueError, FileNotFoundError):
                return None
            board_cache[t] = {r["ticker"]: r for r in rec.rows if r.get("ticker")}
            board_obs[t] = rec.observed_at_utc
        return board_cache[t], board_obs[t]

    def tick_before(limit: datetime, strict: bool) -> datetime | None:
        c = [t for t in ticks if (t < limit if strict else t <= limit)]
        return c[-1] if c else None

    # board universe per game (closing board)
    closing: dict[str, tuple[dict[str, dict[str, Any]], str] | None] = {}
    universe: dict[str, dict[str, Any]] = {}
    for g in games:
        ct = tick_before(g.tip, strict=True)
        closing[g.game_id] = board_at(ct) if ct else None
        if closing[g.game_id]:
            for tk in closing[g.game_id][0]:
                if _ticker_game(tk, [g]):
                    universe.setdefault(tk, {"game_id": g.game_id})
    for tk, c in contracts.items():
        universe.setdefault(tk, {"game_id": c["game_id"]})
    for p in preds_all:
        if p.get("ticker"):
            universe.setdefault(p["ticker"], {"game_id": p["game_id"]})
    for tk, s in settle_rows.items():
        universe.setdefault(tk, {"game_id": s["game_id"]})
    for tk, u in universe.items():
        c = contracts.get(tk)
        u.update(
            ticker=tk, family=(c or {}).get("family") or classify_family(tk), scope=(c or {}).get("scope"), stat=(c or {}).get("stat"),
            period=(c or {}).get("period"), threshold=(c or {}).get("threshold"), comparator=(c or {}).get("comparator"),
            support=(c or {}).get("support") or "NO_CONTRACT_ROW", in_contracts=c is not None,
            on_closing_board=bool(closing[u["game_id"]] and tk in closing[u["game_id"]][0]),
        )

    # horizon rows
    refused = {"prediction_at_or_after_tip": 0, "no_model_probability": 0, "no_board_before_prediction": 0}
    rows: list[dict[str, Any]] = []
    for p in preds_all:
        tk, g = p.get("ticker"), by_id.get(p.get("game_id"))
        if not tk or g is None or not p.get("predicted_at_utc"):
            continue
        pa = parse_iso(p["predicted_at_utc"])
        if pa >= g.tip:
            refused["prediction_at_or_after_tip"] += 1
            continue
        hrs = (g.tip - pa).total_seconds() / 3600.0
        if hrs > MAX_PASS_LOOKBACK_H:
            continue
        pm = p.get("p_data_only")
        if pm is None or not (0.0 <= float(pm) <= 1.0):
            refused["no_model_probability"] += 1
            continue
        bt = tick_before(min(pa, g.tip), strict=False)
        bt = bt if bt is not None and bt < g.tip else None
        b = board_at(bt) if bt else None
        if b is None:
            refused["no_board_before_prediction"] += 1
            q = quote_cents(None)
            q_obs = None
        else:
            q, q_obs = quote_cents(b[0].get(tk)), b[1]
        rows.append({"ticker": tk, "game_id": g.game_id, "family": universe[tk]["family"], "predicted_at_utc": p["predicted_at_utc"],
                     "hours_to_tip": round(hrs, 3), "horizon": horizon_bucket(hrs), "p_model": float(pm), "quote_observed_at_utc": q_obs,
                     "yes_bid": q["yes_bid"], "yes_ask": q["yes_ask"], "no_bid": q["no_bid"], "no_ask": q["no_ask"],
                     "threshold": universe[tk]["threshold"], "support": universe[tk]["support"], "gate": p.get("gate"),
                     "model_version": p.get("model_version"), "legacy_p_market_present": p.get("p_market") is not None})

    # grade + economics
    outcome_of = {}
    for tk, s in settle_rows.items():
        if s.get("outcome") in ("YES", "NO"):
            outcome_of[tk] = s["outcome"] == "YES"
    for r in rows:
        y = outcome_of.get(r["ticker"])
        r["outcome_yes"] = None if y is None else int(y)
        mid = midpoint({k: r[k] for k in ("yes_bid", "yes_ask", "no_bid", "no_ask")})
        r["p_market_mid"] = None if mid is None else mid / 100.0
        qd = {k: r[k] for k in ("yes_bid", "yes_ask", "no_bid", "no_ask")}
        ya, na = side_ask(qd, "yes"), side_ask(qd, "no")
        r["yes_ask_eff"], r["no_ask_eff"] = ya, na
        # selection: the side the MODEL prefers after exact fees at the captured ask (a hypothetical, not a fill)
        best = None
        for side, ask, p_side in (("yes", ya, r["p_model"]), ("no", na, 1.0 - r["p_model"])):
            if ask is None:
                continue
            ev = p_side - breakeven_prob(ask)
            if best is None or ev > best[2]:
                best = (side, ask, ev)
        r["pick_side"], r["pick_ask"], r["pick_ev_model"] = (best if best else (None, None, None))
        if best and y is not None:
            r["pick_pnl"] = hypothetical_pnl(best[0], best[1], y)
            r["pick_stake"] = best[1] / 100.0 + fee_dollars_per_contract(best[1])
        else:
            r["pick_pnl"] = r["pick_stake"] = None
        r["pick_positive_ev"] = bool(best and best[2] > 0)

    # closing benchmarks (strictly pre-tip last board) for CLV
    for r in rows:
        cb = closing.get(r["game_id"])
        crow = quote_cents(cb[0].get(r["ticker"])) if cb else quote_cents(None)
        cmid = midpoint(crow)
        r["close_observed_at_utc"] = cb[1] if cb else None
        if r["pick_side"]:
            side = r["pick_side"]
            cask = side_ask(crow, side)
            r["clv_quoted_exec"] = None if cask is None else (cask - r["pick_ask"]) / 100.0  # close ask minus entry ask: >0 = price rose after entry
            emid = midpoint({k: r[k] for k in ("yes_bid", "yes_ask", "no_bid", "no_ask")})
            if cmid is None or emid is None:
                r["clv_selection"] = None
            else:
                r["clv_selection"] = ((cmid - emid) if side == "yes" else (emid - cmid)) / 100.0
        else:
            r["clv_quoted_exec"] = r["clv_selection"] = None

    # universe accounting
    last_pred_by_ticker = {}
    for r in sorted(rows, key=lambda r: r["predicted_at_utc"]):
        last_pred_by_ticker[r["ticker"]] = r
    n_pred_by_ticker = defaultdict(int)
    for p in preds_all:
        n_pred_by_ticker[p.get("ticker")] += 1
    reason_counts: dict[str, int] = defaultdict(int)
    for tk, u in universe.items():
        s = settle_rows.get(tk)
        u["n_predictions_all_horizons"] = n_pred_by_ticker.get(tk, 0)
        if tk in outcome_of and tk in last_pred_by_ticker:
            u["status"], u["ungraded_reason"] = "GRADED", ""
        else:
            if tk not in outcome_of:
                o = s.get("outcome") if s else None
                reason = "no_settlement_record"
                if o:
                    why = str(s.get("reason") or "").split("(")[0].strip().lower()
                    why = "_".join(why.replace("'", "").split())[:40]
                    reason = f"settlement_{str(o).lower()}:{why}" if why else f"settlement_{str(o).lower()}"
            elif n_pred_by_ticker.get(tk, 0) == 0:
                reason = "no_model_forecast"
            else:
                reason = "no_valid_pretip_forecast"
            if u["support"] not in ("BUILDABLE", "NO_CONTRACT_ROW") and n_pred_by_ticker.get(tk, 0) == 0:
                reason = f"unsupported_{str(u['support']).lower()}" if tk not in outcome_of else reason
            u["status"], u["ungraded_reason"] = "UNGRADED", reason
        u["settlement_outcome"] = (settle_rows.get(tk) or {}).get("outcome")
        u["settlement_value"] = (settle_rows.get(tk) or {}).get("value")
        reason_counts[u["ungraded_reason"] or "graded"] += 1
    graded = sum(1 for u in universe.values() if u["status"] == "GRADED")
    assert graded + sum(v for k, v in reason_counts.items() if k != "graded") == len(universe)

    report = _rollups(date_et, games, universe, rows, last_pred_by_ticker, reason_counts, refused, graded, now)
    _write(out_dir, date_et, universe, rows, report)
    return report


# ---- rollups ----------------------------------------------------------------------------------------


def _family_table(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    groups: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        if r["outcome_yes"] is not None:
            groups[r[key]].append(r)
    table = []
    for k, rs in sorted(groups.items(), key=lambda kv: str(kv[0])):
        y = np.array([r["outcome_yes"] for r in rs], float)
        pm = np.array([r["p_model"] for r in rs], float)
        b_model = float(np.mean((pm - y) ** 2))
        both = [r for r in rs if r["p_market_mid"] is not None]
        yb = np.array([r["outcome_yes"] for r in both], float)
        d = [(r["p_market_mid"] - r["outcome_yes"]) ** 2 - (r["p_model"] - r["outcome_yes"]) ** 2 for r in both]
        dci = cluster_bootstrap_mean(d, [r["game_id"] for r in both])
        picks = [r for r in rs if r["pick_positive_ev"] and r["pick_pnl"] is not None]
        roi = cluster_bootstrap_ratio([r["pick_pnl"] for r in picks], [r["pick_stake"] for r in picks], [r["game_id"] for r in picks])
        clv_q = [r["clv_quoted_exec"] for r in picks if r["clv_quoted_exec"] is not None]
        clv_s = [r["clv_selection"] for r in picks if r["clv_selection"] is not None]
        table.append({
            key: k, "n": len(rs), "n_games": len({r["game_id"] for r in rs}), "mean_p_model": float(pm.mean()), "base_rate": float(y.mean()),
            "brier_model": b_model, "n_with_market": len(both),
            "brier_model_on_market_rows": float(np.mean([(r["p_model"] - r["outcome_yes"]) ** 2 for r in both])) if both else None,
            "brier_market_mid": float(np.mean((np.array([r["p_market_mid"] for r in both]) - yb) ** 2)) if both else None,
            "market_minus_model_brier": dci, "skill": skill_flag(dci["mean"], dci["ci95"], dci["n_clusters"]),
            "n_positive_ev_picks": len(picks), "pick_roi_after_fee": roi,
            "pick_hit_rate": float(np.mean([1.0 if r["pick_pnl"] > 0 else 0.0 for r in picks])) if picks else None,
            "clv_quoted_exec_mean": float(np.mean(clv_q)) if clv_q else None, "n_clv_quoted_exec": len(clv_q),
            "clv_selection_mean": float(np.mean(clv_s)) if clv_s else None, "n_clv_selection": len(clv_s),
            "clv_actual_fill_n": 0,
        })
    return table


def _rollups(date_et, games, universe, rows, last_pred, reason_counts, refused, graded, now) -> dict[str, Any]:
    final_rows = list(last_pred.values())  # one (latest pre-tip) forecast per ticker: no pseudo-replication in headline numbers
    eligible = len(universe)
    status = "OK"
    blockers: list[str] = []
    n_settled_inputs = sum(1 for u in universe.values() if u["settlement_outcome"] in ("YES", "NO"))
    if eligible and n_settled_inputs and graded == 0:
        status = "BLOCKED"
        blockers.append(f"{n_settled_inputs} settled tickers exist but 0 were graded (no valid pre-tip forecast join)")
    if not rows:
        status = "BLOCKED"
        blockers.append("zero pre-tip forecast rows joined")
    no_quote = sum(1 for r in final_rows if r["yes_ask_eff"] is None and r["no_ask_eff"] is None)
    if final_rows and no_quote == len(final_rows):
        blockers.append("no executable quote joined to any forecast: quote-dependent ROI/CLV/market baselines unavailable")
    return {
        "date_et": date_et, "status": status, "blockers": blockers, "generated_at_utc": (now or datetime.now(UTC)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "games": [{"game_id": g.game_id, "matchup": f"{g.away}@{g.home}", "tip_utc": g.tip.strftime("%Y-%m-%dT%H:%M:%SZ")} for g in games],
        "coverage": {"universe": eligible, "graded": graded, "ungraded_by_reason": {k: v for k, v in sorted(reason_counts.items()) if k != "graded"},
                     "by_family_universe": dict(sorted(_count(u["family"] for u in universe.values()).items())),
                     "pretip_forecast_rows": len(rows), "refused": refused, "forecast_rows_without_any_executable_quote": no_quote},
        "headline_latest_pretip_by_family": _family_table(final_rows, "family"),
        "by_horizon": _family_table(rows, "horizon"),
        "by_game": _family_table(final_rows, "game_id"),
        "by_price_bin": _family_table([{**r, "price_bin": price_bin(r["p_model"])} for r in final_rows], "price_bin"),
        "not_evaluated": ["injury-status and participation splits (needs injury snapshot join per horizon)", "actual-fill CLV (no fill evidence in archive)",
                          "multiple-comparison control (descriptive only; no promotion claims)"],
    }


def _count(it):
    out: dict[str, int] = defaultdict(int)
    for x in it:
        out[str(x)] += 1
    return out


def _blocked(out_dir: Path, date_et: str, why: str) -> dict[str, Any]:
    rep = {"date_et": date_et, "status": "BLOCKED", "blockers": [why], "coverage": {"universe": 0, "graded": 0}}
    out_dir = Path(out_dir) / date_et
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(json.dumps(rep, indent=1))
    return rep


def _fmt(v, nd=4):
    return "" if v is None else (f"{v:.{nd}f}" if isinstance(v, float) else str(v))


def render_markdown(rep: dict[str, Any]) -> str:
    c = rep["coverage"]
    lines = [f"# NBA all-market audit — {rep['date_et']} (ET) — **{rep['status']}**", "", "RESEARCH_ONLY. Hypothetical taker economics; no fills.", ""]
    for b in rep.get("blockers", []):
        lines.append(f"- **BLOCKER:** {b}")
    lines += ["", "## Coverage", f"universe **{c['universe']}** = graded **{c['graded']}** + ungraded **{c['universe'] - c['graded']}**", ""]
    for k, v in c.get("ungraded_by_reason", {}).items():
        lines.append(f"- ungraded `{k}`: {v}")
    lines += [f"- refused: {c.get('refused')}", "", "## Family performance (latest pre-tip forecast per ticker; 🟢 model beats market CI>0, 🟡 inconclusive, 🔴 market better, ⚪ no market)", "",
              "| family | n | games | p̄ | base | Brier model | Brier mkt | mkt−model (95% CI) | skill | +EV picks | ROI after fee (95% CI) | CLV exec | CLV sel |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for t in rep.get("headline_latest_pretip_by_family", []):
        d, r = t["market_minus_model_brier"], t["pick_roi_after_fee"]
        dci = f"{_fmt(d['mean'])} {d['ci95'] and [round(x, 3) for x in d['ci95']] or ''}"
        rci = f"{_fmt(r['mean'])} {r['ci95'] and [round(x, 3) for x in r['ci95']] or ''}"
        lines.append(f"| {t['family']} | {t['n']} | {t['n_games']} | {_fmt(t['mean_p_model'], 3)} | {_fmt(t['base_rate'], 3)} | {_fmt(t['brier_model'])} | {_fmt(t['brier_market_mid'])} | {dci} | {t['skill']} | {t['n_positive_ev_picks']} | {rci} | {_fmt(t['clv_quoted_exec_mean'])} | {_fmt(t['clv_selection_mean'])} |")
    for title, key, col in (("By time before tip (all horizons; rows are NOT independent)", "by_horizon", "horizon"), ("By game", "by_game", "game_id"), ("By model-probability bin", "by_price_bin", "price_bin")):
        lines += ["", f"## {title}", "", f"| {col} | n | Brier model | Brier mkt | skill | +EV picks | ROI |", "|---|---|---|---|---|---|---|"]
        for t in rep.get(key, []):
            lines.append(f"| {t[col]} | {t['n']} | {_fmt(t['brier_model'])} | {_fmt(t['brier_market_mid'])} | {t['skill']} | {t['n_positive_ev_picks']} | {_fmt(t['pick_roi_after_fee']['mean'])} |")
    lines += ["", "## Not evaluated", *[f"- {x}" for x in rep["not_evaluated"]], ""]
    return "\n".join(lines)


def _write(out_dir: Path, date_et: str, universe, rows, report) -> None:
    d = Path(out_dir) / date_et
    d.mkdir(parents=True, exist_ok=True)
    for name, data in (("universe.csv", list(universe.values())), ("horizon_rows.csv", rows)):
        if not data:
            continue
        cols = sorted({k for r in data for k in r})
        with open(d / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(sorted(data, key=lambda r: (str(r.get("ticker")), str(r.get("predicted_at_utc")))))
    clean = json.loads(json.dumps(report, default=lambda o: None if isinstance(o, float) and math.isnan(o) else str(o)))
    (d / "report.json").write_text(json.dumps(clean, indent=1, sort_keys=True))
    (d / "report.md").write_text(render_markdown(report))


def run_audit(archive: Path, dates: list[str], out_dir: Path) -> int:
    worst = EXIT_OK
    for d in dates:
        rep = audit_date(archive, d, out_dir)
        c = rep["coverage"]
        print(f"audit-markets {d}: {rep['status']} universe={c['universe']} graded={c['graded']}")
        if rep["status"] != "OK":
            worst = EXIT_BLOCKED
            for b in rep["blockers"]:
                print(f"  BLOCKED: {b}")
    return worst
