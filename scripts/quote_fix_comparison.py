"""Old-vs-corrected (§5.14) pricing on ARCHIVED slates. Read-only: nothing is written to the archive.

For one slate pass per ET date it reconstructs the Kalshi board at the pass's market timestamp, then re-derives the market-relative
fields from the *stored* model probability (p_data_only, mc_se are NOT recomputed, so the delta is purely the quote handling):
p_market -> p_hybrid -> economics (EV, best side, bet-up-to) -> gate. "old" is what the archive actually holds (no quote read).

    python scripts/quote_fix_comparison.py ARCHIVE_ROOT [--out report.md] [--json summary.json]
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np

from nba_edge.archive.reconstruct import reconstruct_at
from nba_edge.execution.economics import EconomicsConfig, compute_economics, market_implied_probability
from nba_edge.kalshi.contracts import build_contract
from nba_edge.kalshi.fees import DEFAULT_SCHEDULE
from nba_edge.kalshi.ontology import Ontology
from nba_edge.timeutil import parse_iso
from nba_edge.workflows.simulate import HYBRID_MARKET_WEIGHT, HYBRID_WEIGHT_BY_SCOPE, STALE_MARKET_MIN, _hybrid, market_snapshot

KEEP_GATES = {"UNSUPPORTED", "CANNOT_TRUST_INPUTS"}


def pick_passes(root: Path) -> list[Path]:
    out = []
    for d in sorted((root / "slates").glob("dt=*")):
        passes = sorted(p for p in d.iterdir() if (p / "slate.json").exists())
        if passes:
            best = max(passes, key=lambda p: (p / "slate.json").stat().st_size)
            out.append(best)
    return out


def reprice(root: Path, pass_dir: Path, onto: Ontology) -> list[dict]:
    from nba_edge.archive.ledger import Ledger  # noqa: F401  (import kept local: reconstruct_at needs only the root)

    slate = json.loads((pass_dir / "slate.json").read_text())
    now = parse_iso(slate["generated_at_utc"])
    ts = max((c.get("market_ts") for c in slate["contracts"] if c.get("market_ts")), default=None)
    if ts is None:
        return []
    board = reconstruct_at(root, parse_iso(ts))
    by_ticker = {m["ticker"]: m for m in board.rows}
    rows = []
    for c in slate["contracts"]:
        m = by_ticker.get(c["ticker"])
        if m is None:
            continue
        m = dict(m)
        scope = build_contract(m, onto).scope
        snap = market_snapshot(m)
        p_mkt = market_implied_probability(snap).p_mid
        p_data = c["p_data_only"]
        p_h = _hybrid(p_data, p_mkt, HYBRID_WEIGHT_BY_SCOPE.get(scope, HYBRID_MARKET_WEIGHT))
        p_used = p_h if p_h is not None else p_data
        obs = parse_iso(m["_observed_at_utc"]) if m.get("_observed_at_utc") else None
        econ = compute_economics(snap, p_used, c.get("mc_se") or 0.0, schedule=DEFAULT_SCHEDULE, config=EconomicsConfig(max_age_min=STALE_MARKET_MIN), observed_at=obs, now=now) if p_used is not None else None
        if c["gate"] in KEEP_GATES:
            gate, best = c["gate"], None
        elif econ is None or econ.best_side is None:
            gate, best = "NO_EDGE", None
        else:
            gate, best = "OK", econ.best_side
        rows.append({
            "date": slate["date_et"], "pass": pass_dir.name, "ticker": c["ticker"], "family": c["family"], "scope": scope,
            "old_gate": c["gate"], "new_gate": gate, "old_quote": any(c.get(k) is not None for k in ("yes_bid", "yes_ask", "no_bid", "no_ask")),
            "new_quote": any(snap.get(k) is not None for k in ("yes_bid", "yes_ask", "no_bid", "no_ask")),
            "old_p_market": c["p_market"], "new_p_market": p_mkt, "p_data": p_data, "old_p_hybrid": c["p_hybrid"], "new_p_hybrid": p_h,
            "old_best": c["best_side"], "new_best": best, "new_ev": None if econ is None or best is None else (econ.yes.ev_per_contract if best == "yes" else econ.no.ev_per_contract),
            "new_ask": None if best is None else snap["yes_ask" if best == "yes" else "no_ask"],
        })
    return rows


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    gained = [r for r in rows if r["new_quote"] and not r["old_quote"]]
    trans = Counter((r["old_gate"], r["new_gate"]) for r in rows)
    recs = [r for r in rows if r["new_gate"] == "OK"]
    d = [abs(r["new_p_hybrid"] - r["p_data"]) for r in rows if r["new_p_hybrid"] is not None and r["p_data"] is not None]
    return {
        "passes": len({(r["date"], r["pass"]) for r in rows}), "contracts": n, "old_with_quote": sum(r["old_quote"] for r in rows), "new_with_quote": sum(r["new_quote"] for r in rows),
        "gained_quote": len(gained), "new_p_market_defined": sum(r["new_p_market"] is not None for r in rows), "old_p_market_defined": sum(r["old_p_market"] is not None for r in rows),
        "gate_transitions": {f"{a}->{b}": v for (a, b), v in sorted(trans.items())}, "recommendations_old": sum(r["old_best"] is not None for r in rows), "recommendations_new": len(recs),
        "new_rec_by_family": dict(Counter(r["family"] for r in recs).most_common(15)),
        "new_rec_by_side": dict(Counter(r["new_best"] for r in recs)),
        "ev_new_rec_quantiles": None if not recs else {str(q): round(float(np.quantile([r["new_ev"] for r in recs], q)), 4) for q in (0.1, 0.5, 0.9, 0.99)},
        "abs_shift_hybrid_vs_data_median": None if not d else round(float(np.median(d)), 4),
        "model_vs_market_by_scope": {
            sc: {"n": len(x), "median_abs_p_data_minus_p_market": round(float(np.median(x)), 4), "share_over_0.25": round(float(np.mean(np.array(x) > 0.25)), 3)}
            for sc in sorted({r["scope"] for r in rows})
            if (x := [abs(r["p_data"] - r["new_p_market"]) for r in rows if r["scope"] == sc and r["p_data"] is not None and r["new_p_market"] is not None])
        },
        "recs_with_abs_gap_over_0.25": sum(abs(r["p_data"] - r["new_p_market"]) > 0.25 for r in recs if r["new_p_market"] is not None and r["p_data"] is not None),
        "unquoted_by_family_new": dict(Counter(r["family"] for r in rows if not r["new_quote"]).most_common(10)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("archive_root", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()
    onto = Ontology.load()
    rows = []
    for p in pick_passes(a.archive_root):
        rows += reprice(a.archive_root, p, onto)
    s = summarize(rows)
    top = sorted((r for r in rows if r["new_gate"] == "OK"), key=lambda r: -(r["new_ev"] or -9))[:15]
    s["top_new_recommendations"] = [{k: r[k] for k in ("date", "ticker", "new_best", "new_ask", "p_data", "new_p_market", "new_p_hybrid", "new_ev")} for r in top]
    if a.json:
        a.json.write_text(json.dumps(s, indent=1, default=str))
    md = ["# §5.14 quote fix: old vs corrected on archived slates", "", "```json", json.dumps(s, indent=1, default=str), "```", ""]
    (a.out.write_text("\n".join(md)) if a.out else print("\n".join(md)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
