"""Evaluation of the cached compute stages -> CONTRACT.md summary pieces.

Frames
  conditional   played rows (minutes > 0): the frame Kalshi player props settle in (a DNP settles at a fair
                price, not as a zero) and the frame the incumbent reports. Conditioning on "played" uses
                post-game information; its effect is quantified against the unconditional frame.
  unconditional candidate pool (absent / DNP = 0) with the participation hurdle.
Scored seasons: development 2016-17..2021-22 (LightGBM needs >= 1 earlier season and the windowed walk-forward
starts at 2016-17), validation 2022-23..2023-24, holdout 2024-25..2025-26 (frozen candidates only).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from pf_core import dists, metrics, models
from . import data, distributions as D
from .common import FAMILIES, MINUTES_RUNGS, SUPPORT_K, split_of
from .evaluate import diff_ci, model_row, segment_bias

MIN_NAMES = {"A": "A_season_avg_shrunk", "B": "B_ewma_shrunk", "C": "C_role_blend", "D": "D_role_plus_context",
             "E": "E_lightgbm", "F": "F_stack", "E_inj": "E_inj_lightgbm_teammate_absence_proxy",
             "oracle_start": "ORACLE_knows_starters"}
STAT_NAMES = {"A": "A_season_avg_shrunk", "B": "B_ewma_shrunk", "C": "C_minutes_x_rate", "D": "D_opp_adjusted",
              "E": "E_lightgbm", "F": "F_stack", "E_inj": "E_inj_lightgbm_teammate_absence_proxy"}
FIRST_SCORED = 2017


def load_incumbent() -> pd.DataFrame:
    fr = [pd.read_parquet(p) for p in sorted((data.PF_DIR / ".cache").glob("incumbent_*.parquet"))]
    inc = pd.concat(fr, ignore_index=True) if fr else pd.DataFrame(columns=["game_id", "pid"])
    return inc.drop(columns=["season"], errors="ignore").add_prefix("inc_").rename(
        columns={"inc_game_id": "game_id", "inc_pid": "pid"})


def attach(f: pd.DataFrame, inc: pd.DataFrame) -> pd.DataFrame:
    f = f.copy()
    f["split"] = f["season"].map(split_of)
    m = f[["game_id", "pid"]].merge(inc, on=["game_id", "pid"], how="left")
    m.index = f.index
    for c in inc.columns:
        if c not in ("game_id", "pid"):
            f[c] = m[c]
    return f


def _nb_params(y_dev, mu_dev, K):
    return dict(models.fit_dist_params("nb_binned", y_dev, mu_dev), K=K)


# ------------------------------------------------------------------------------------------------ minutes
def eval_minutes(f: pd.DataFrame, mp: pd.DataFrame, best: str) -> dict:
    P = f[f["played"] & (f["season"] >= FIRST_SCORED)].copy()
    for k in mp.columns:
        P[f"m_{k}"] = mp.loc[P.index, k]
    y = P["minutes"].to_numpy()
    dev = (P["split"] == "development").to_numpy()
    K = SUPPORT_K["minutes"]
    prm = {k: models.fit_dist_params("empirical_resid", y[dev], P[f"m_{k}"].to_numpy()[dev], K=K, n_bins=8)
           for k in MIN_NAMES}
    out = {"rows": [], "holdout": {}, "dist_params": prm}
    crps = {}
    for k in MIN_NAMES:
        crps[k] = models.make_dist(prm[k], P[f"m_{k}"].to_numpy()).crps(y)
    P_inc = P["inc_minutes_crps"].to_numpy() if "inc_minutes_crps" in P else np.full(len(P), np.nan)
    for split in ("development", "validation", "holdout"):
        s = (P["split"] == split).to_numpy()
        ks = list(MIN_NAMES) if split != "holdout" else ["A", best, "E_inj", "oracle_start"]
        for k in dict.fromkeys(ks):
            dist = models.make_dist(prm[k], P[f"m_{k}"].to_numpy()[s])
            inc_loss = P_inc[s] if split != "development" else None
            verdict = "baseline" if k == "A" else ("best" if k == best else ("oracle" if k == "oracle_start" else ""))
            r = model_row(MIN_NAMES[k], split, y[s], P[f"m_{k}"].to_numpy()[s], P["game_id"].to_numpy()[s], dist,
                          MINUTES_RUNGS, base_loss=crps["A"][s], inc_loss=inc_loss, loss=crps[k][s], verdict=verdict)
            out["rows"].append(r)
        if split != "development":
            mi = s & np.isfinite(P_inc)
            pm = metrics.point_metrics(y[mi], P["inc_minutes_mean"].to_numpy()[mi])
            out["rows"].append({"model": "incumbent_sim_rotation", "split": split, "n_obs": int(mi.sum()),
                                "n_clusters": int(P["game_id"][mi].nunique()), "mae": round(pm["mae"], 4),
                                "rmse": round(pm["rmse"], 4), "bias": round(pm["bias"], 4),
                                "crps": round(float(np.nanmean(P_inc[mi])), 4), "log_score": round(float(np.nanmean(P["inc_minutes_logs"].to_numpy()[mi])), 4),
                                "cover_50": _cov(P["inc_minutes_pit"].to_numpy()[mi], 0.5),
                                "cover_80": _cov(P["inc_minutes_pit"].to_numpy()[mi], 0.8),
                                "cover_90": _cov(P["inc_minutes_pit"].to_numpy()[mi], 0.9),
                                "pit_var_ratio": round(float(np.var(P["inc_minutes_pit"].to_numpy()[mi]) * 12), 4),
                                "vs_baseline": diff_ci(P_inc[mi], crps["A"][mi], P["game_id"].to_numpy()[mi]),
                                "vs_incumbent": None, "verdict": "incumbent"})
    # point comparisons (MAE) for the narrative, val + holdout
    cmp = {}
    for split in ("validation", "holdout"):
        s = (P["split"] == split).to_numpy()
        ae = {k: np.abs(P[f"m_{k}"].to_numpy() - y) for k in MIN_NAMES}
        si = s & np.isfinite(P_inc)
        cmp[split] = {
            "best_vs_B_mae": diff_ci(ae[best][s], ae["B"][s], P["game_id"].to_numpy()[s]),
            "E_inj_vs_best_mae": diff_ci(ae["E_inj"][s], ae[best][s], P["game_id"].to_numpy()[s]),
            "oracle_start_vs_E_inj_mae": diff_ci(ae["oracle_start"][s], ae["E_inj"][s], P["game_id"].to_numpy()[s]),
            "best_vs_incumbent_mae": diff_ci(ae[best][si], np.abs(P["inc_minutes_mean"].to_numpy() - y)[si], P["game_id"].to_numpy()[si]),
            "best_vs_incumbent_crps": diff_ci(crps[best][si], P_inc[si], P["game_id"].to_numpy()[si]),
        }
    out["comparisons"] = cmp
    # bias by role / predicted-minutes bucket (validation)
    V = P[P["split"] == "validation"].copy()
    V["role"] = np.where(V["start_p_ewm8"].fillna(0) >= 0.5, "starter-role", "bench-role")
    V["bucket"] = pd.cut(V[f"m_{best}"], [0, 12, 20, 28, 34, 60], labels=["<12", "12-20", "20-28", "28-34", "34+"])
    V["m_inc"] = V["inc_minutes_mean"]
    out["segments"] = {k: segment_bias(V.dropna(subset=["m_inc"]) if k == "inc" else V, ["role", "bucket"], "minutes", f"m_{k}")
                       for k in ("B", best, "inc")}
    out["crps"] = crps
    out["P_index"] = P.index
    return out


def _cov(pit, lvl):
    pit = pit[np.isfinite(pit)]
    a = (1 - lvl) / 2
    return round(float(np.mean((pit >= a) & (pit <= 1 - a))), 4) if len(pit) else None


def eval_unconditional(f: pd.DataFrame, mp: pd.DataFrame, best: str, min_prm: dict) -> dict:
    """Candidate pool incl. absent / DNP rows: hurdle + conditional minutes; vs incumbent's unconditional mean."""
    C = f[f["season"] >= FIRST_SCORED].copy()
    C["p_play"] = mp.loc[C.index, "p_play"]
    C["m_best"] = mp.loc[C.index, best]
    C["m_B"] = mp.loc[C.index, "B"]
    y = C["min_act0"].to_numpy()
    yb = C["played"].astype(float).to_numpy()
    base_p = C["play01_ewm10"].fillna(C["play01_ewm10"].mean()).clip(0.01, 0.99).to_numpy()
    res = {}
    for split in ("development", "validation", "holdout"):
        s = (C["split"] == split).to_numpy()
        g = C["game_id"].to_numpy()[s]
        mean = (C["p_play"] * C["m_best"]).to_numpy()[s]
        base = (base_p * C["m_B"].to_numpy())[s]
        cond = models.make_dist(min_prm[best], C["m_best"].to_numpy()[s])
        hd = dists.hurdle(1 - C["p_play"].to_numpy()[s], cond)
        cr = hd.crps(y[s])
        r = {"n": int(s.sum()), "play_rate": round(float(yb[s].mean()), 4),
             "hurdle_brier": round(float(np.mean((C['p_play'].to_numpy()[s] - yb[s]) ** 2)), 4),
             "baseline_brier_ewm_participation": round(float(np.mean((base_p[s] - yb[s]) ** 2)), 4),
             "hurdle_ece": round(metrics.ece(C["p_play"].to_numpy()[s], yb[s]), 4),
             "mae": round(float(np.mean(np.abs(mean - y[s]))), 3), "bias": round(float(np.mean(mean - y[s])), 3),
             "mae_baseline_ewm": round(float(np.mean(np.abs(base - y[s]))), 3),
             "crps_hurdle": round(float(cr.mean()), 3),
             "cover_80": round(float(metrics.dist_metrics(y[s], hd)["cover_80"]), 4),
             "mae_vs_baseline": diff_ci(np.abs(mean - y[s]), np.abs(base - y[s]), g)}
        if split != "development":
            si = np.isfinite(C["inc_p_play"].to_numpy()[s])
            im = C["inc_min_uncond"].to_numpy()[s]
            ip = C["inc_p_play"].to_numpy()[s]
            r["incumbent"] = {"n": int(si.sum()), "mae": round(float(np.mean(np.abs(im[si] - y[s][si]))), 3),
                              "bias": round(float(np.mean(im[si] - y[s][si])), 3),
                              "brier": round(float(np.mean((ip[si] - yb[s][si]) ** 2)), 4),
                              "ours_mae_same_rows": round(float(np.mean(np.abs(mean[si] - y[s][si]))), 3),
                              "ours_brier_same_rows": round(float(np.mean((C['p_play'].to_numpy()[s][si] - yb[s][si]) ** 2)), 4),
                              "mae_diff": diff_ci(np.abs(mean[si] - y[s][si]), np.abs(im[si] - y[s][si]), g[si]),
                              "rows_not_projected_by_incumbent": int((~si).sum()),
                              "played_rows_not_projected_by_incumbent": int(((~si) & (yb[s] > 0)).sum())}
            r["calibration_table"] = metrics.calibration_table(C["p_play"].to_numpy()[s], yb[s], 10)
        res[split] = r
    return res


# ------------------------------------------------------------------------------------------------ stats
def eval_family(f: pd.DataFrame, fam: str, sp: pd.DataFrame, min_prm: dict, best_min: str) -> dict:
    col, gate_key, rungs = FAMILIES[fam]
    P = f[f["played"] & (f["season"] >= FIRST_SCORED)].copy()
    for k in ["A", "B", "C", "D", "E", "F", "E_inj", "rate", "opp_factor", "opp_factor_raw", "opp_n", "pace_adj"]:
        P[f"s_{k}"] = sp.loc[P.index, k]
    P["m_best"] = P["min_best"]
    y = P[col].to_numpy()
    K = SUPPORT_K[col]
    dev = (P["split"] == "development").to_numpy()
    keys = ["A", "B", "C", "D", "E", "F", "E_inj"]
    nbp = {k: _nb_params(y[dev], P[f"s_{k}"].to_numpy()[dev], K) for k in keys}
    crps = {k: models.make_dist(nbp[k], P[f"s_{k}"].to_numpy()).crps(y) for k in keys}
    val = (P["split"] == "validation").to_numpy()
    best = min(["A", "B", "C", "D", "E", "F"], key=lambda k: crps[k][val].mean())
    # distribution families for the best mean (fitted on development, compared on validation)
    mu = P[f"s_{best}"].to_numpy()
    fams = D.fit_all(y[dev], mu[dev], K)
    min_res = D.fit_minutes_resid(P["minutes"].to_numpy()[dev], P["m_best"].to_numpy()[dev])
    rate = P["s_rate"].to_numpy()
    alpha_w = D.fit_alpha_given_minutes(y[dev], rate[dev], P["minutes"].to_numpy()[dev])
    scen = D.minutes_scenarios(min_res, P["m_best"].to_numpy())
    scale = mu / np.maximum(rate * scen.mean(axis=1), 1e-6)       # anchor the mixture mean at the best mean

    def dist_for(name, idx):
        if name in fams:
            return D.make(fams[name], mu[idx])
        if name == "mixture":
            return D.mixture(rate[idx], scen[idx], alpha_w, K, scale[idx])
        if name == "single_minutes_nb":                          # ignores minutes uncertainty
            return dists.negbin(np.maximum(mu[idx], 0.05), alpha_w, K)
        raise ValueError(name)

    dist_cmp = {}
    for split in ("validation",):
        s = np.where((P["split"] == split).to_numpy())[0]
        for name in list(fams) + ["mixture", "single_minutes_nb"]:
            d = dist_for(name, s)
            dm = metrics.dist_metrics(y[s], d, thresholds=rungs)
            dist_cmp[name] = {"crps": round(dm["crps"], 4), "log_score": round(dm["log_score"], 4),
                              "cover_50": round(dm["cover_50"], 4), "cover_80": round(dm["cover_80"], 4),
                              "cover_90": round(dm["cover_90"], 4), "pit_var_ratio": round(dm["pit_var_ratio"], 4),
                              "pit_deciles": dm["pit_deciles"],
                              "mean_rung_brier": round(float(np.mean([v["brier"] for v in dm["thresholds"].values()])), 5),
                              "rungs": {k: {"brier": round(v["brier"], 5), "mean_p": round(v["mean_p"], 4),
                                            "hit_rate": round(v["hit_rate"], 4)} for k, v in dm["thresholds"].items()}}
    chosen = min(dist_cmp, key=lambda n: (dist_cmp[n]["log_score"]))
    out = {"family": fam, "col": col, "best": best, "chosen_dist": chosen, "dist_compare_validation": dist_cmp,
           "alpha_given_minutes": alpha_w, "nb_alpha_marginal": fams["nb"]["alphas"], "rows": [], "holdout": {}}
    inc_crps = P.get(f"inc_{col}_crps", pd.Series(np.nan, index=P.index)).to_numpy()
    for split in ("development", "validation", "holdout"):
        s = (P["split"] == split).to_numpy()
        ks = keys if split != "holdout" else list(dict.fromkeys(["A", best, "E_inj"]))
        for k in ks:
            if k == best:
                d = dist_for(chosen, np.where(s)[0])
                loss = d.crps(y[s])
            else:
                d = models.make_dist(nbp[k], P[f"s_{k}"].to_numpy()[s])
                loss = crps[k][s]
            r = model_row(STAT_NAMES[k] + (f"+{chosen}" if k == best else ""), split, y[s], P[f"s_{k}"].to_numpy()[s],
                          P["game_id"].to_numpy()[s], d, rungs, base_loss=crps["A"][s],
                          inc_loss=inc_crps[s] if split != "development" else None, loss=loss,
                          verdict="baseline" if k == "A" else ("best" if k == best else ""))
            out["rows"].append(r)
        if split != "development" and np.isfinite(inc_crps[s]).any():
            mi = s & np.isfinite(inc_crps)
            pit = P[f"inc_{col}_pit"].to_numpy()[mi]
            pm = metrics.point_metrics(y[mi], P[f"inc_{col}_mean"].to_numpy()[mi])
            th = {}
            for kk in rungs:
                pk = P[f"inc_{col}_pge{kk}"].to_numpy()[mi]
                o = (y[mi] >= kk).astype(float)
                th[str(kk)] = {"brier": round(float(np.mean((pk - o) ** 2)), 5), "mean_p": round(float(pk.mean()), 4),
                               "hit_rate": round(float(o.mean()), 4)}
            out["rows"].append({"model": "incumbent_sim", "split": split, "n_obs": int(mi.sum()),
                                "n_clusters": int(P["game_id"][mi].nunique()), "mae": round(pm["mae"], 4),
                                "rmse": round(pm["rmse"], 4), "bias": round(pm["bias"], 4),
                                "crps": round(float(np.mean(inc_crps[mi])), 4),
                                "log_score": round(float(np.mean(P[f"inc_{col}_logs"].to_numpy()[mi])), 4),
                                "cover_50": _cov(pit, 0.5), "cover_80": _cov(pit, 0.8), "cover_90": _cov(pit, 0.9),
                                "pit_var_ratio": round(float(np.var(pit) * 12), 4), "thresholds": th,
                                "vs_baseline": diff_ci(inc_crps[mi], crps["A"][mi], P["game_id"].to_numpy()[mi]),
                                "vs_incumbent": None, "verdict": "incumbent"})
            # same-rows rung Brier for our best
            d = dist_for(chosen, np.where(mi)[0])
            ours = {}
            for kk in rungs:
                pk = d.prob_ge(kk)
                o = (y[mi] >= kk).astype(float)
                ours[str(kk)] = round(float(np.mean((pk - o) ** 2)), 5)
            out[f"rung_brier_same_rows_{split}"] = {"ours": ours, "incumbent": {k: v["brier"] for k, v in th.items()}}
    # opponent adjustment
    oa = {}
    for split in ("validation", "holdout"):
        s = (P["split"] == split).to_numpy()
        g = P["game_id"].to_numpy()[s]
        oa[split] = {"D_vs_C_crps": diff_ci(crps["D"][s], crps["C"][s], g),
                     "D_vs_C_mae": diff_ci(np.abs(P["s_D"].to_numpy()[s] - y[s]), np.abs(P["s_C"].to_numpy()[s] - y[s]), g),
                     "factor_sd": round(float(np.std(P["s_opp_factor"].to_numpy()[s])), 4),
                     "factor_p05_p95": [round(float(np.quantile(P["s_opp_factor"].to_numpy()[s], q)), 4) for q in (0.05, 0.95)],
                     "pace_adj_sd": round(float(np.std(P["s_pace_adj"].to_numpy()[s])), 4)}
    out["opponent"] = oa
    s = (P["split"] == "validation").to_numpy()
    g = P["game_id"].to_numpy()[s]
    out["E_inj_vs_best_val"] = diff_ci(crps["E_inj"][s], crps[best][s], g)
    out["crps"] = crps
    out["P_index"] = P.index
    out["nbp"] = nbp
    out["fams"], out["min_res"], out["scen_scale"] = fams, min_res, None
    out["dist_for"] = dist_for
    out["P"] = P
    return out


# ------------------------------------------------------------------------------------------------ team
TEAM_NAMES = {"A": "A_season_avg_shrunk", "B": "B_ewma_shrunk", "C": "C_pace_x_efficiency_ridge",
              "D": "D_ratings_plus_rest"}


def eval_team(tt: pd.DataFrame) -> dict:
    from .team import K, LO
    T = tt[tt["season"] >= FIRST_SCORED].copy()
    T["split"] = T["season"].map(split_of)
    y = T["pts"].to_numpy(float)
    dev = (T["split"] == "development").to_numpy()
    prm = {k: models.fit_dist_params("normal_binned", y[dev], T[k].to_numpy()[dev], lo=LO, K=K, n_bins=4)
           for k in TEAM_NAMES}
    crps = {k: models.make_dist(prm[k], T[k].to_numpy()).crps(y) for k in TEAM_NAMES}
    val = (T["split"] == "validation").to_numpy()
    best = min(TEAM_NAMES, key=lambda k: crps[k][val].mean())
    rows = []
    for split in ("development", "validation", "holdout"):
        s = (T["split"] == split).to_numpy()
        for k in (TEAM_NAMES if split != "holdout" else dict.fromkeys(["A", best])):
            d = models.make_dist(prm[k], T[k].to_numpy()[s])
            rows.append(model_row(TEAM_NAMES[k], split, y[s], T[k].to_numpy()[s], T["game_id"].to_numpy()[s], d,
                                  [100, 110, 120, 130], base_loss=crps["A"][s], loss=crps[k][s],
                                  verdict="baseline" if k == "A" else ("best" if k == best else "")))
    return {"rows": rows, "best": best, "prm": prm, "T": T}


def reconciliation(f: pd.DataFrame, mp: pd.DataFrame, pts_pred: pd.Series, T: pd.DataFrame, team_best: str) -> dict:
    """Sum over the candidate pool of P(play) x E[pts | play] vs the team-points projection."""
    from pf_core import gate
    C = f[f["season"] >= FIRST_SCORED][["game_id", "team", "season", "split"]].copy()
    C["exp_pts_player"] = mp.loc[C.index, "p_play"].to_numpy() * pts_pred.loc[C.index].to_numpy()
    s = C.groupby(["game_id", "team"]).agg(player_sum=("exp_pts_player", "sum"), split=("split", "first")).reset_index()
    s = s.merge(T[["game_id", "team", "pts", team_best]], on=["game_id", "team"])
    s["ratio"] = s["player_sum"] / s[team_best]
    out = {}
    for split, g in s.groupby("split"):
        st = [gate.team_reconciliation(a, b, "player points vs team points")["status"] for a, b in zip(g["player_sum"], g[team_best])]
        out[split] = {"n_team_games": int(len(g)), "ratio_mean": round(float(g["ratio"].mean()), 4),
                      "ratio_p05_p95": [round(float(g["ratio"].quantile(q)), 4) for q in (0.05, 0.95)],
                      "status_counts": pd.Series(st).value_counts().to_dict(),
                      "mae_player_sum_vs_actual": round(float((g["player_sum"] - g["pts"]).abs().mean()), 3),
                      "bias_player_sum": round(float((g["player_sum"] - g["pts"]).mean()), 3),
                      "mae_team_model_vs_actual": round(float((g[team_best] - g["pts"]).abs().mean()), 3),
                      "mae_normalised_blend": round(float((0.5 * g["player_sum"] + 0.5 * g[team_best] - g["pts"]).abs().mean()), 3)}
    return out


# ------------------------------------------------------------------------------------------------ PIT injuries (2025-26)
def injury_pit_study(f: pd.DataFrame, mp: pd.DataFrame, pts_sp: pd.DataFrame, best_min: str) -> dict:
    """2025-26 only. (1) how well the archived T-60 report predicts absence; (2) hurdle + report status,
    recalibrated on the first half of the season and tested on the second; (3) minutes / points LightGBM
    trained (2020-21..2024-25) on the retrospective proxy, scored on 2025-26 with proxy vs PIT inputs."""
    import lightgbm as lgb
    from sklearn.linear_model import LogisticRegression
    from . import injury, minutes as M
    st, games = injury.snapshot_status("t_minus_60")
    H = f[f["season"] == 2026].copy()
    H = injury.pit_absence(H, st, games)
    H.index = f.index[f["season"] == 2026]
    H = H[H["has_snapshot"]]
    res = {"n_candidate_rows": int(len(H)), "n_games": int(H["game_id"].nunique())}
    tab = H.groupby("inj_status").agg(n=("pid", "size"), absent_from_box=("in_box", lambda s: float((~s).mean())),
                                      played=("played", "mean")).round(4)
    res["status_vs_outcome"] = tab.reset_index().to_dict("records")
    out_flag = H["inj_status"].isin(["OUT", "DOUBTFUL"])
    absent = ~H["in_box"]
    res["out_or_doubtful_precision_absent"] = round(float(absent[out_flag].mean()), 4)
    res["absent_recall_by_out_or_doubtful"] = round(float(out_flag[absent].mean()), 4)
    # (2) hurdle recalibration
    H["p_play"] = mp.loc[H.index, "p_play"].clip(0.01, 0.99)
    lg = np.log(H["p_play"] / (1 - H["p_play"]))
    X = pd.concat([lg.rename("logit")] + [(H["inj_status"] == s).astype(float).rename(s)
                                          for s in ("OUT", "DOUBTFUL", "QUESTIONABLE", "PROBABLE", "AVAILABLE")], axis=1)
    yb = H["played"].astype(float)
    cut = pd.Timestamp("2026-01-15")
    tr, te = (H["date"] < cut).to_numpy(), (H["date"] >= cut).to_numpy()
    lr = LogisticRegression(C=10.0, max_iter=500).fit(X[tr], yb[tr])
    p_adj = lr.predict_proba(X)[:, 1]
    g = H["game_id"].to_numpy()
    res["hurdle_second_half"] = {
        "n": int(te.sum()), "brier_hurdle": round(float(np.mean((H["p_play"].to_numpy()[te] - yb[te]) ** 2)), 4),
        "brier_hurdle_plus_report": round(float(np.mean((p_adj[te] - yb[te]) ** 2)), 4),
        "diff": diff_ci((p_adj[te] - yb[te]) ** 2, (H["p_play"].to_numpy()[te] - yb[te]) ** 2, g[te])}
    # unconditional minutes with the report-aware hurdle
    mb = mp.loc[H.index, best_min].to_numpy()
    y0 = H["min_act0"].to_numpy()
    res["unconditional_minutes_second_half"] = {
        "mae_hurdle": round(float(np.mean(np.abs(H["p_play"].to_numpy()[te] * mb[te] - y0[te]))), 3),
        "mae_hurdle_plus_report": round(float(np.mean(np.abs(p_adj[te] * mb[te] - y0[te]))), 3),
        "diff": diff_ci(np.abs(p_adj[te] * mb[te] - y0[te]), np.abs(H["p_play"].to_numpy()[te] * mb[te] - y0[te]), g[te])}
    # (3) proxy vs PIT teammate-absence inputs
    feats = M.ROLE + M.CONTEXT + M.LGB_EXTRA
    trn = f[(f["season"] >= 2021) & (f["season"] <= 2025) & f["played"]]
    mdl = lgb.LGBMRegressor(objective="regression", learning_rate=0.05, n_estimators=300, num_leaves=31,
                            min_child_samples=200, subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                            verbose=-1, n_jobs=2).fit(trn[feats + M.INJ], trn["minutes"])
    Hp = H[H["played"]]
    Xp = Hp[feats + M.INJ].copy()
    Xpit = Xp.copy()
    for c in M.INJ:
        Xpit[c] = Hp[f"{c}_pit"]
    y = Hp["minutes"].to_numpy()
    gp = Hp["game_id"].to_numpy()
    e_proxy, e_pit = mdl.predict(Xp), mdl.predict(Xpit)
    e_none = mp.loc[Hp.index, "E"].to_numpy()
    res["minutes_played_rows"] = {
        "n": int(len(Hp)), "mae_E_no_injury_info": round(float(np.mean(np.abs(e_none - y))), 3),
        "mae_E_inj_proxy_inputs": round(float(np.mean(np.abs(e_proxy - y))), 3),
        "mae_E_inj_PIT_report_inputs": round(float(np.mean(np.abs(e_pit - y))), 3),
        "pit_vs_none": diff_ci(np.abs(e_pit - y), np.abs(e_none - y), gp),
        "pit_vs_proxy": diff_ci(np.abs(e_pit - y), np.abs(e_proxy - y), gp),
        "corr_out_min_proxy_vs_pit": round(float(np.corrcoef(Hp["out_min"], Hp["out_min_pit"])[0, 1]), 4)}
    return res


# ------------------------------------------------------------------------------------------------ root cause
def root_cause(f: pd.DataFrame, mp: pd.DataFrame, best: str, team_ctx: pd.DataFrame) -> dict:
    """Large minutes misses (|err| >= 10) on development and validation, tagged by retrospective causes."""
    P = f[f["played"] & (f["season"] >= FIRST_SCORED)].copy()
    P["m"] = mp.loc[P.index, best]
    P["err"] = P["m"] - P["minutes"]
    nxt = f.sort_values(["pid", "date"]).groupby("pid")["played"].shift(-1)
    P["missed_next"] = (nxt.reindex(P.index) == False)  # noqa: E712
    tc = team_ctx[["game_id", "team", "n_ot", "margin"]]
    P = P.merge(tc, on=["game_id", "team"], how="left").set_index(P.index)
    tags = {
        "blowout_final_margin_ge_20": P["margin"].abs() >= 20,
        "early_exit_then_missed_next_game": (P["minutes"] < 0.5 * P["m"]) & P["missed_next"],
        "foul_trouble_5plus_pf": P["pf_act"] >= 5 if "pf_act" in P else P["pf"] >= 5,
        "new_teammate_absence_ge_25min": P["out_new_min"] >= 25,
        "return_from_absence_3plus_games": P["missed_streak"] >= 3,
        "role_change_start_vs_usual": P["started"] != (P["start_p_ewm8"].fillna(0) >= 0.5),
        "overtime": P["n_ot"] > 0,
        "back_to_back": P["b2b"] == 1,
        "new_team": P["games_with_team"] < 5,
    }
    out = {}
    for split in ("development", "validation"):
        S = P[P["split"] == split]
        big = S["err"].abs() >= 10
        rows = []
        tot_ae = S["err"].abs().sum()
        for name, m in tags.items():
            mm = m.reindex(S.index).fillna(False).astype(bool)
            rows.append({"pattern": name, "freq_all": round(float(mm.mean()), 4), "freq_big_miss": round(float(mm[big].mean()), 4),
                         "lift": round(float(mm[big].mean() / max(mm.mean(), 1e-9)), 2),
                         "mae_when_present": round(float(S["err"][mm].abs().mean()), 3),
                         "mae_when_absent": round(float(S["err"][~mm].abs().mean()), 3),
                         "bias_when_present": round(float(S["err"][mm].mean()), 3),
                         "share_of_total_abs_error": round(float(S["err"][mm].abs().sum() / tot_ae), 4)})
        out[split] = {"n": int(len(S)), "big_miss_rate": round(float(big.mean()), 4),
                      "big_miss_share_of_abs_error": round(float(S["err"][big].abs().sum() / tot_ae), 4), "tags": rows}
    # fixes tested: injury proxy on new-absence rows, blowout-risk context on high expected-margin rows,
    # team-minutes budget normalisation
    fx = {}
    for split in ("development", "validation"):
        S = P[P["split"] == split]
        g = S["game_id"].to_numpy()
        y = S["minutes"].to_numpy()
        ae = lambda c: np.abs(mp.loc[S.index, c].to_numpy() - y)  # noqa: E731
        na = (S["out_new_min"] >= 25).to_numpy()
        hm = (S["exp_abs_margin"] >= 9).to_numpy()
        fx[split] = {
            "E_inj_vs_E_on_new_absence_rows": diff_ci(ae("E_inj")[na], ae("E")[na], g[na]),
            "D_vs_C_on_high_expected_margin_rows": diff_ci(ae("D")[hm], ae("C")[hm], g[hm]),
            "E_vs_B_on_high_expected_margin_rows": diff_ci(ae("E")[hm], ae("B")[hm], g[hm])}
    out["fix_tests"] = fx
    return out
