"""Read-only view of the preregistered control (`SHADOW_PURE_PREREG_V1`: the frozen V1 simulator evaluated by `nba-shadow-pure`).

The control is NOT run, re-implemented or modified here. This module only reads the newest `value_scorecard` record the shadow store wrote
(`scorecards/value/dt=*/...jsonl.gz` on the `nba-shadow-pure` branch) and reports the primary arm's verdict next to the paper candidates,
so the weekly report can compare strategies against the control on the same footing (and quote the control's own evidence thresholds).
"""
from __future__ import annotations

import glob
import gzip
import json
import os
from typing import Any

PRIMARY_ARM = "sim_rotation/pretip/conditional"


def latest(shadow_dir: str | None) -> dict[str, Any]:
    if not shadow_dir or not os.path.isdir(shadow_dir):
        return {"status": "NO_DATA", "reason": "nba-shadow-pure checkout not mounted", "strategy_id": "SHADOW_PURE_PREREG_V1"}
    files = sorted(glob.glob(os.path.join(shadow_dir, "scorecards", "value", "dt=*", "*.jsonl.gz")))
    if not files:
        return {"status": "NO_DATA", "reason": "no value_scorecard records on the shadow branch", "strategy_id": "SHADOW_PURE_PREREG_V1"}
    rec = None
    with gzip.open(files[-1], "rt") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
    if not rec:
        return {"status": "NO_DATA", "reason": "empty value_scorecard file", "strategy_id": "SHADOW_PURE_PREREG_V1"}
    ev = (rec.get("evaluations") or {})
    prim = ev.get(PRIMARY_ARM) or next((v for v in ev.values() if v.get("eligible_for_independent_value_verdict")), None)
    out: dict[str, Any] = {"status": "OK", "strategy_id": "SHADOW_PURE_PREREG_V1", "evaluated_at": rec.get("evaluated_at"),
                           "source_file": os.path.relpath(files[-1], shadow_dir), "n_arms": len(ev)}
    if prim is None:
        return {**out, "status": "NO_DATA", "reason": "no eligible primary arm in the record"}
    rep = prim.get("report") or {}
    out.update({"arm": prim.get("arm"), "capture_window": prim.get("capture_window"), "n_decisions": prim.get("n_decisions"),
                "n_games": prim.get("n_games"), "verdict": prim.get("verdict"), "verdict_reasons": prim.get("verdict_reasons"),
                "preregistration_sha256": (rep.get("preregistration") or {}).get("sha256"),
                "thresholds": (rep.get("verdict") or {}).get("thresholds"),
                "roi": (rep.get("decisions_summary") or {}).get("roi") or rep.get("roi"),
                "note": "read-only view of the preregistered control; dry-run diagnostic; no wagering authority"})
    return out
