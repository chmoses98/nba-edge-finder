"""NBA Projection Foundation walk-forward: compute stages -> evaluation -> gate -> results.

Run from research/projection_foundation:
    python -m nba.run_walkforward            # uses cached stages in .cache/ when present
    python -m nba.run_walkforward --force    # recompute every model stage
Outputs: results/backtest_raw.json (every number the report quotes), then nba.summarize builds
results/summary.json (CONTRACT schema), results/experiments/*.json and results/tables_nba.md.
Prerequisite for incumbent comparisons: python -m nba.incumbent 2023 2024 2025 2026 (cached parquet).
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np
import pandas as pd

from . import backtest as B, data, gate_eval, inventory, pipeline
from .common import FAMILIES, MINUTES_RUNGS

RESULTS = data.PF_DIR / "results"


def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else round(float(o), 6)
    if isinstance(o, np.ndarray):
        return _jsonable(o.tolist())
    if isinstance(o, (pd.Timestamp,)):
        return o.isoformat()
    return o


def gate_family(f, fam_res, fam, best_min_col, inj_status, n_max=15000, seed=0):
    col, gkey, rungs = FAMILIES[fam] if fam != "minutes" else ("minutes", "minutes", MINUTES_RUNGS)
    P = fam_res["P"]
    played = f[f["played"]]
    mh = gate_eval.history_matrix(played, "minutes", 10)
    sh = gate_eval.history_matrix(played, col, 10)
    pos = pd.Series(np.arange(len(played)), index=played.index)
    out = {}
    rng = np.random.default_rng(seed)
    for split in ("validation", "holdout"):
        idx = np.where((P["split"] == split).to_numpy())[0]
        if len(idx) > n_max:
            idx = np.sort(rng.choice(idx, n_max, replace=False))
        S = P.iloc[idx]
        d = fam_res["dist_for"](fam_res["chosen_dist"], idx)
        mean = d.mean
        pi = pos.loc[S.index].to_numpy()
        ist = [inj_status.get((g, p)) for g, p in zip(S["game_id"], S["pid"])]
        ist = [("ACTIVE" if s in ("AVAILABLE", "PROBABLE") else s) if s is not None else
               ("ACTIVE" if (g in inj_status.get("_games", set())) else None) for s, g in zip(ist, S["game_id"])]
        st = gate_eval.run_gate(S, gkey, mean, d, rungs, S[best_min_col].to_numpy(), mh[pi], sh[pi],
                                opp_factor=S["s_opp_factor"].to_numpy(), opp_n=S["s_opp_n"].to_numpy(),
                                injury_status=ist, model_n=S["minutes_p_n"].fillna(0).to_numpy())
        st["status_x"] = gate_eval.status_excluding(st["checks"])
        y = S[col].to_numpy()
        summ, err = gate_eval.summarise(st, y, mean, d.crps(y))
        out[split] = {"summary": summ, "error_by_status": err}
    return out


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    t0 = time.time()
    ctx = pipeline.run_compute(force="--force" in argv)
    f, mp, best_min = ctx["f"], ctx["mp"], ctx["best_min"]
    inc = B.load_incumbent()
    f = B.attach(f, inc)
    raw = {"best_minutes_model": best_min, "minutes_params": ctx["mprm"], "team_params": ctx["tprm"]}
    pipeline.log("eval minutes")
    mres = B.eval_minutes(f, mp, best_min)
    raw["minutes"] = {k: v for k, v in mres.items() if k in ("rows", "comparisons", "segments")}
    raw["unconditional"] = B.eval_unconditional(f, mp, best_min, mres["dist_params"])
    # budget normalisation experiment (development + validation)
    C = f[f["season"] >= B.FIRST_SCORED].copy()
    C["p_play"], C["m"] = mp.loc[C.index, "p_play"], mp.loc[C.index, best_min]
    C["m_norm"] = __import__("nba.minutes", fromlist=["x"]).team_budget_normalise(C, "m", "p_play")
    bn = {}
    for split in ("development", "validation"):
        S = C[(C["split"] == split) & C["played"]]
        y = S["minutes"].to_numpy()
        bn[split] = B.diff_ci(np.abs(S["m_norm"].to_numpy() - y), np.abs(S["m"].to_numpy() - y), S["game_id"].to_numpy())
    raw["budget_normalisation"] = bn
    pipeline.log("eval families")
    fam_res = {}
    for fam in FAMILIES:
        col = FAMILIES[fam][0]
        sp, sprm = ctx["stats"][col]
        r = B.eval_family(f, fam, sp, mres["dist_params"], best_min)
        r["params"] = sprm
        fam_res[fam] = r
        raw[fam] = {k: v for k, v in r.items() if k not in ("crps", "P_index", "nbp", "fams", "min_res", "scen_scale",
                                                        "dist_for", "P")}
        pipeline.log(f"  {fam}: best={r['best']} dist={r['chosen_dist']}")
    pipeline.log("eval team")
    tres = B.eval_team(ctx["team"])
    raw["team_points"] = {"rows": tres["rows"], "best": tres["best"]}
    pts_best = fam_res["points"]["best"]
    raw["reconciliation"] = B.reconciliation(f, mp, ctx["stats"]["pts"][0][pts_best], tres["T"], tres["best"])
    pipeline.log("injury PIT study")
    raw["injury_pit"] = B.injury_pit_study(f, mp, ctx["stats"]["pts"][0], best_min)
    pipeline.log("root cause")
    raw["root_cause"] = B.root_cause(f, mp, best_min, ctx["t"])
    # conditioning effect on points: conditional (played) vs unconditional (candidate pool) error
    pc = {}
    sp = ctx["stats"]["pts"][0]
    for split in ("validation", "holdout"):
        S = f[(f["split"] == split)]
        pr = sp.loc[S.index, pts_best].to_numpy()
        pp = mp.loc[S.index, "p_play"].to_numpy()
        yy = S["pts_act"].to_numpy()
        pl = S["played"].to_numpy()
        pc[split] = {"conditional_mae": round(float(np.mean(np.abs(pr[pl] - yy[pl]))), 3),
                     "unconditional_mae_hurdle_mean": round(float(np.mean(np.abs(pp * pr - yy))), 3),
                     "unconditional_mae_assume_plays": round(float(np.mean(np.abs(pr - yy))), 3),
                     "share_rows_not_played": round(float(1 - pl.mean()), 4)}
    raw["conditioning_effect_points"] = pc
    pipeline.log("gate")
    from . import injury
    st, games = injury.snapshot_status("t_minus_60")
    inj = {(g, p): s for g, p, s in zip(st["game_id"], st["pid"], st["inj_status"])}
    inj["_games"] = set(games["game_id"])
    raw["gate"] = {fam: gate_family(f, fam_res[fam], fam, "min_best", inj) for fam in FAMILIES}
    raw["frozen"] = {
        "best_minutes_model": best_min, "minutes_params": ctx["mprm"], "minutes_dist": mres["dist_params"][best_min],
        "team": {"best": tres["best"], "dist": tres["prm"][tres["best"]], "params": ctx["tprm"]},
        "families": {fam: {"best": r["best"], "dist": r["chosen_dist"], "params": r["params"],
                           "dist_params": r["fams"].get(r["chosen_dist"]), "min_res": r["min_res"],
                           "alpha_given_minutes": r["alpha_given_minutes"]} for fam, r in fam_res.items()}}
    raw["inventory"] = inventory.build(data.load_box(), None)
    raw["inventory_candidate_rows"] = int(len(f))
    raw["inventory_absent_rows"] = int((~f["in_box"]).sum())
    raw["runtime_s"] = round(time.time() - t0, 1)
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "backtest_raw.json").write_text(json.dumps(_jsonable(raw), indent=1))
    pipeline.log(f"wrote backtest_raw.json ({raw['runtime_s']}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
