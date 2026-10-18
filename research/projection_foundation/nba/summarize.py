"""results/backtest_raw.json -> results/summary.json (CONTRACT schema), results/frozen_params.json,
results/experiments/*.json (pf_core.registry records) and results/tables_nba.md.

Decision rules are fixed here (written before the holdout was scored):
  * a model "beats" another when the 95% game-clustered bootstrap CI of the paired loss difference is
    entirely below 0 (CRPS for distributions, absolute error for point comparisons);
  * readiness (holdout, frozen best model):
      READY              beats baseline A and the incumbent, cover_80 in [0.76, 0.84], pit_var_ratio in
                         [0.85, 1.15], |bias| <= 5% of the mean outcome;
      SHADOW VALIDATION  beats baseline and incumbent but a calibration criterion fails, or no incumbent exists
                         and it beats the baseline with calibration inside the bands;
      NEEDS IMPROVEMENT  does not beat the baseline or the incumbent;
      INSUFFICIENT DATA  fewer than 2,000 holdout observations.
"""
from __future__ import annotations

import json
import subprocess
import time

from pf_core import VERSION
from pf_core.registry import ExperimentRecord, md_table, write_record
from . import data
from .common import FAMILIES, SPLITS_TEXT

R = data.PF_DIR / "results"


def beats(c):
    return c is not None and c.get("ci95") is not None and c["ci95"][1] < 0


def worse(c):
    return c is not None and c.get("ci95") is not None and c["ci95"][0] > 0


def fmt_ci(c, nd=3):
    if not c:
        return "n/a"
    return f"{c['mean_diff']:+.{nd}f} [{c['ci95'][0]:+.{nd}f}, {c['ci95'][1]:+.{nd}f}]"


def readiness(h, mean_actual, has_inc=True):
    if h is None or h.get("n_obs", 0) < 2000:
        return "INSUFFICIENT DATA", "fewer than 2,000 holdout observations"
    b_ok = beats(h.get("vs_baseline"))
    i_ok = beats(h.get("vs_incumbent")) if has_inc else None
    cal = (h.get("cover_80") is not None and 0.76 <= h["cover_80"] <= 0.84 and 0.85 <= h["pit_var_ratio"] <= 1.15
           and abs(h["bias"]) <= 0.05 * max(mean_actual, 1e-6))
    calmsg = (f"holdout cover_80 {h.get('cover_80')}, PIT variance ratio {h.get('pit_var_ratio')}, bias {h['bias']:+.3f}")
    if not b_ok:
        return "NEEDS IMPROVEMENT", f"does not beat the season-average baseline on holdout ({fmt_ci(h.get('vs_baseline'))}); {calmsg}"
    if has_inc and not i_ok:
        return "NEEDS IMPROVEMENT", f"does not beat the incumbent on holdout ({fmt_ci(h.get('vs_incumbent'))}); {calmsg}"
    if cal and has_inc:
        return "READY", (f"beats baseline ({fmt_ci(h['vs_baseline'])}) and incumbent ({fmt_ci(h['vs_incumbent'])}) in "
                         f"holdout CRPS; {calmsg}. Conditional on playing; needs the live injury feed for participation.")
    if cal and not has_inc:
        return "SHADOW VALIDATION", f"beats baseline ({fmt_ci(h['vs_baseline'])}); no incumbent for this family; {calmsg}"
    return "SHADOW VALIDATION", f"beats baseline and incumbent but calibration is outside the bands: {calmsg}"


def _pick(rows, split, prefix):
    for r in rows:
        if r["split"] == split and r["model"].startswith(prefix):
            return r
    return None


def family_entry(fam, raw_f, unit, opp_family, population, has_inc=True):
    rows = raw_f["rows"]
    best = raw_f["best"]
    best_name = next(r["model"] for r in rows if r["split"] == "validation" and r.get("verdict") == "best")
    h = next((r for r in rows if r["split"] == "holdout" and r["model"] == best_name), None)
    rd, why = readiness(h, h["mean_actual"], has_inc) if h else ("INSUFFICIENT DATA", "no holdout rows")
    models_out = []
    for r in rows:
        m = {k: r.get(k) for k in ("model", "split", "n_obs", "n_clusters", "mae", "rmse", "bias", "crps", "log_score",
                                   "cover_50", "cover_80", "cover_90", "pit_var_ratio")}
        m["vs_baseline"] = {k: r["vs_baseline"][k] for k in ("mean_diff", "ci95")} if r.get("vs_baseline") else None
        m["vs_incumbent"] = ({k: r["vs_incumbent"][k] for k in ("mean_diff", "ci95")} if r.get("vs_incumbent") else None)
        v = r.get("verdict") or ""
        if not v:
            if r["split"] != "development" and worse(r.get("vs_baseline")):
                v = "rejected"
            elif r["model"].startswith("ORACLE"):
                v = "oracle (not pregame)"
            else:
                v = "competitive" if beats(r.get("vs_baseline")) else "rejected"
        m["verdict"] = v
        models_out.append(m)
    hold = None
    if h:
        hold = {"model": h["model"], "n_obs": h["n_obs"], "mae": h["mae"], "crps": h["crps"], "bias": h["bias"],
                "cover_80": h["cover_80"], "vs_baseline": {k: h["vs_baseline"][k] for k in ("mean_diff", "ci95")},
                "vs_incumbent": ({k: h["vs_incumbent"][k] for k in ("mean_diff", "ci95")} if h.get("vs_incumbent") else None)}
    return {"family": fam, "unit": unit, "opportunity_family": opp_family, "population": population,
            "models": models_out, "best_model": best_name, "holdout": hold, "readiness": rd, "readiness_reason": why}


def main() -> int:
    raw = json.loads((R / "backtest_raw.json").read_text())
    fams = []
    # minutes (the opportunity family)
    mrows = raw["minutes"]["rows"]
    mraw = {"rows": mrows, "best": raw["best_minutes_model"]}
    fams.append(family_entry("minutes", mraw, "player-game (played)", None,
                             "players who played (minutes > 0), regular season; 2016-17..2025-26 scored",
                             ))
    for fam in FAMILIES:
        fr = raw[fam]
        pops = "players who played (prop frame: Kalshi settles DNP at a fair price), regular season"
        fams.append(family_entry(fam, fr, "player-game (played)", "minutes", pops))
    for e in fams:
        h = e["holdout"]
        if not h:
            continue
        r = [r for r in (raw["minutes"]["rows"] if e["family"] == "minutes" else raw[e["family"]]["rows"])
             if r["split"] == "holdout" and r["model"] == h["model"]][0]
        e["readiness"], e["readiness_reason"] = readiness(r, r["mean_actual"], has_inc=h["vs_incumbent"] is not None)
    tr = raw["team_points"]
    fams.append(family_entry("team_points", {"rows": tr["rows"], "best": tr["best"]}, "team-game", None,
                             "all regular-season team-games", has_inc=False))
    th = [r for r in tr["rows"] if r["split"] == "holdout" and r.get("verdict") == "best"][0]
    fams[-1]["readiness"], fams[-1]["readiness_reason"] = readiness(th, th["mean_actual"], has_inc=False)
    raw["_families"] = fams
    from .summary_text import build_summary  # narrative pieces (experiments, investigations, priorities)
    summary = build_summary(raw, fams)
    summary.update({"schema": "sift.projection_foundation.sport_summary.v1", "sport": "NBA",
                    "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "code_sha": _sha(), "pf_core_version": VERSION, "splits": SPLITS_TEXT})
    order = ["schema", "sport", "generated_utc", "code_sha", "pf_core_version", "splits", "inventory", "families",
             "experiments", "error_investigations", "opponent_adjustment", "opportunity", "calibration",
             "failed_experiments", "gate", "priorities"]
    full_exps = summary.get("experiments_full", summary["experiments"])
    summary = {k: summary[k] for k in order}
    (R / "summary.json").write_text(json.dumps(summary, indent=1))
    # frozen parameters for the forward projector
    fz = raw["frozen"]
    by = {e["family"]: e for e in fams}
    for fam in FAMILIES:
        fz["families"][fam].update({"readiness": by[fam]["readiness"], "readiness_reason": by[fam]["readiness_reason"],
                                    "model_name": by[fam]["best_model"]})
    fz["team"].update({"readiness": by["team_points"]["readiness"], "readiness_reason": by["team_points"]["readiness_reason"],
                       "model_name": by["team_points"]["best_model"]})
    fz["minutes_readiness"] = {"readiness": by["minutes"]["readiness"], "readiness_reason": by["minutes"]["readiness_reason"],
                               "model_name": by["minutes"]["best_model"]}
    (R / "frozen_params.json").write_text(json.dumps(fz, indent=1))
    # experiment records
    exp_dir = R / "experiments"
    for e in fams:
        for m in e["models"]:
            if m["split"] == "development":
                continue
            rec = ExperimentRecord(
                experiment_id=f"nba_{e['family']}_{m['model'].split('+')[0]}_{m['split']}", sport="NBA", family=e["family"],
                model=m["model"], model_version="pf-nba-1", question=f"How accurate is {m['model']} for {e['family']}?",
                hypothesis="ladder rung improves on the season-average baseline", split=m["split"],
                train_period="walk-forward: all seasons before the scored season (LightGBM: previous 5 seasons)",
                eval_period=SPLITS_TEXT[m["split"]], features=[], hyperparameters={},
                data_provenance=["ESPN box scores via sportsdataverse mirror (hoopR) 2014-15..2025-26",
                                 "data/history/espn (repo) 2023-24..2025-26"],
                n_obs=int(m["n_obs"]), n_independent=int(m["n_obs"]), n_clusters=int(m["n_clusters"]),
                point={k: m[k] for k in ("mae", "rmse", "bias")},
                distribution={k: m[k] for k in ("crps", "log_score", "cover_50", "cover_80", "cover_90", "pit_var_ratio")},
                vs_baseline=m["vs_baseline"] or {}, vs_incumbent=m["vs_incumbent"] or {},
                limitations=["regular season only", "conditional on playing (player families)"], verdict=m["verdict"])
            write_record(rec, str(exp_dir))
    for x in full_exps:
        rec = ExperimentRecord(
            experiment_id=x["id"], sport="NBA", family=x.get("family", "multi"), model=x["id"], model_version="pf-nba-1",
            question=x["question"], hypothesis=x["hypothesis"], split=x.get("split", "validation"),
            train_period="walk-forward", eval_period=x["data"], features=[], hyperparameters={"method": x["method"]},
            data_provenance=[x["data"]], n_obs=int(x.get("n_obs", 0)), n_independent=int(x.get("n_obs", 0)),
            n_clusters=int(x.get("n_clusters", 0)), point={"result": x["result"]},
            limitations=[x["interpretation"]], verdict=x["decision"])
        write_record(rec, str(exp_dir))
    # markdown tables for the report
    lines = []
    for e in fams:
        lines.append(f"### {e['family']}  (best: {e['best_model']}; readiness {e['readiness']})\n")
        rows = []
        for m in e["models"]:
            rows.append({"model": m["model"], "split": m["split"], "n": m["n_obs"], "MAE": m["mae"], "RMSE": m["rmse"],
                         "bias": m["bias"], "CRPS": m["crps"], "cover80": m["cover_80"], "PITvar": m["pit_var_ratio"],
                         "vs A (CRPS)": fmt_ci(m["vs_baseline"]), "vs incumbent": fmt_ci(m["vs_incumbent"]),
                         "verdict": m["verdict"]})
        lines.append(md_table(rows, list(rows[0].keys())))
    (R / "tables_nba.md").write_text("\n".join(lines))
    print(json.dumps({e["family"]: [e["best_model"], e["readiness"]] for e in fams}, indent=1))
    return 0


def _sha() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(data.ROOT), "rev-parse", "HEAD"], text=True).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
