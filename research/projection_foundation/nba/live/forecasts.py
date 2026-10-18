"""Projection rows -> challenger forecast-archive records, and the NBA segment checks of the prospective scorecard."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from pf_core import prospective as pr

from .. import MODEL_ID
from ..common import FAMILIES

CHALLENGER_FAMILIES = list(FAMILIES) + ["minutes"]
EPS = 1e-7


def trim_pmf(lo: int, probs, eps: float = EPS) -> tuple[int, list[float]]:
    """Drop numerically-zero tails (archive size) and renormalise; the lattice start moves with `lo`."""
    p = np.asarray(probs, float)
    p = np.where(np.isfinite(p) & (p > 0), p, 0.0)
    keep = np.where(p > eps)[0]
    if len(keep) == 0:
        return lo, [1.0]
    a, b = keep[0], keep[-1]
    q = p[a:b + 1]
    q = q / q.sum()
    return int(lo + a), [round(float(x), 7) for x in q]


def challenger_records(res: dict, version: str | None = None) -> list[dict[str, Any]]:
    """One forecast per (player, family) plus a `participation` forecast (P(play) as a two-point pmf) per player-game.

    Confirmed-out players keep only the participation forecast: their conditional stat lines can never settle (void)."""
    gen = res["generated_utc"]
    start = {g["game_id"]: g["start_utc"] for g in res["games"]}
    recs, part_done = [], set()
    ver = version or res["model"]["version"]
    for p in res["players"]:
        pa = p["participation"]
        base = {"sport": "NBA", "model_id": f"{MODEL_ID}-{p['family']}", "model_role": "challenger", "model_version": ver,
                "game_id": p["game_id"], "game_start_utc": start[p["game_id"]], "entity_id": p["player_id"],
                "entity_name": p["name"], "team": p["team"], "generated_utc": gen, "data_asof_utc": p["data_asof_utc"],
                "gate_status": p["gate"]["status"], "readiness": p["readiness"], "tags": p.get("_tags"),
                "participation": {k: pa[k] for k in ("status", "certainty", "source", "captured_utc", "p_play", "designation",
                                                     "implicit") if k in pa}}
        key = (p["game_id"], p["player_id"])
        if key not in part_done:
            part_done.add(key)
            pp = float(pa["p_play"])
            recs.append({**base, "model_id": f"{MODEL_ID}-participation", "family": "participation", "mean": pp, "lo": 0,
                         "probs": [1 - pp, pp]})
        if pa["status"] == "CONFIRMED_OUT":
            continue
        pm = p["_pmf"]
        lo, probs = trim_pmf(pm["lo"], pm["probs"])
        recs.append({**base, "family": p["family"], "mean": float(p["mean"]), "lo": lo, "probs": probs})
    return recs


# ------------------------------------------------------------------------------------------------ NBA segment checks
def _brier(g: pd.DataFrame) -> float:
    return float(np.mean((g["mean"].to_numpy(float) - g["actual"].to_numpy(float)) ** 2))


def segments(root: str, since_utc: str | None = None) -> dict[str, Any]:
    """Sport-specific checks on settled forecasts (descriptive, challenger vs incumbent where both exist)."""
    s = pr.load_settlements(root, "NBA")
    f = pr.load_forecasts(root, "NBA")
    out: dict[str, Any] = {"n_settled": int(len(s))}
    if s.empty:
        return out
    if since_utc:
        s = s[pd.to_datetime(s["game_start_utc"], utc=True) >= pd.Timestamp(since_utc)]
    s = s[~s["void"].astype(bool)].copy()
    if s.empty:
        return out
    ftag = f.set_index("forecast_id")["tags"] if "tags" in f else pd.Series(dtype=object)
    s["tags"] = s["forecast_id"].map(ftag)
    s["pstatus"] = s["participation"].map(lambda d: (d or {}).get("status") if isinstance(d, dict) else None)
    s["pcert"] = s["participation"].map(lambda d: (d or {}).get("certainty") if isinstance(d, dict) else None)
    part = s[s["family"] == "participation"]
    if len(part):
        rows = []
        for (role, seg), g in part.groupby(["model_role", part["pstatus"].fillna("n/a")]):
            rows.append({"model_role": role, "participation_status": seg, "n": int(len(g)), "brier": round(_brier(g), 4),
                         "mean_p": round(float(g["mean"].mean()), 3), "played_rate": round(float(g["actual"].mean()), 3)})
        tot = [{"model_role": r, "n": int(len(g)), "brier": round(_brier(g), 4)} for r, g in part.groupby("model_role")]
        out["participation_brier"] = {"overall": tot, "by_status": rows,
                                      "study_reference": "2025-26 held-out: hurdle 0.132 -> report-aware 0.087"}
    mins = s[(s["family"] == "minutes") & (s["model_role"] == "challenger")]
    if len(mins):
        mins = mins.assign(model=mins["tags"].map(lambda t: (t or {}).get("minutes_model") if isinstance(t, dict) else None))
        out["minutes_by_model"] = [{"minutes_model": k, "n": int(len(g)), "mae": round(float(np.mean(np.abs(g["mean"] - g["actual"]))), 3),
                                    "bias": round(float(np.mean(g["mean"] - g["actual"])), 3)} for k, g in mins.groupby(mins["model"].fillna("n/a"))]
    ch = s[(s["model_role"] == "challenger") & s["family"].isin(["points", "minutes"])].copy()
    if len(ch):
        ch["new_team"] = ch["tags"].map(lambda t: bool((t or {}).get("new_team")) if isinstance(t, dict) else None)
        ch["reconciled"] = ch["tags"].map(lambda t: (t or {}).get("reconciled", "none") if isinstance(t, dict) else None)
        seg = []
        for col in ("new_team", "reconciled"):
            for (fam, v), g in ch.groupby(["family", col], dropna=False):
                seg.append({"segment": col, "value": str(v), "family": fam, "n": int(len(g)),
                            "mae": round(float(np.mean(np.abs(g["mean"] - g["actual"]))), 3),
                            "bias": round(float(np.mean(g["mean"] - g["actual"])), 3)})
        out["early_season_and_reconciliation"] = seg
    return out


def segments_markdown(seg: dict[str, Any]) -> str:
    lines = ["", "### NBA segment checks", ""]
    if "participation_brier" in seg:
        pb = seg["participation_brier"]
        lines += ["**Participation Brier** (P(play) vs played; " + pb["study_reference"] + ")", "",
                  "| Model | n | Brier |", "|---|---|---|"]
        lines += [f"| {r['model_role']} | {r['n']} | {r['brier']} |" for r in pb["overall"]]
        lines += ["", "| Model | Participation status | n | Brier | mean p | played |", "|---|---|---|---|---|---|"]
        lines += [f"| {r['model_role']} | {r['participation_status']} | {r['n']} | {r['brier']} | {r['mean_p']} | {r['played_rate']} |"
                  for r in pb["by_status"]]
    if "minutes_by_model" in seg:
        lines += ["", "**Challenger minutes by model**", "", "| Minutes model | n | MAE | Bias |", "|---|---|---|---|"]
        lines += [f"| {r['minutes_model']} | {r['n']} | {r['mae']} | {r['bias']:+} |" for r in seg["minutes_by_model"]]
    if "early_season_and_reconciliation" in seg:
        lines += ["", "**New-team / reconciled segments**", "", "| Segment | Value | Family | n | MAE | Bias |", "|---|---|---|---|---|---|"]
        lines += [f"| {r['segment']} | {r['value']} | {r['family']} | {r['n']} | {r['mae']} | {r['bias']:+} |"
                  for r in seg["early_season_and_reconciliation"]]
    if len(lines) == 3:
        lines.append("_No settled forecasts yet._")
    return "\n".join(lines) + "\n"
