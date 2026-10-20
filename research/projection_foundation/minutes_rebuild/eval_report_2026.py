"""2025-26 with archived PIT official reports: the live recipe vs JRM-with-report.  Second half of the season only (calibrations fitted on the first half)."""
import sys, json
sys.path.insert(0, ".."); sys.path.insert(0, ".")
import numpy as np, pandas as pd, lightgbm as lgb
from sklearn.linear_model import LogisticRegression
from nba import pipeline, minutes as M, injury
from nba.live import participation as PART
from nba.evaluate import diff_ci
from pf_core import models
from nba import minutes_jrm as jrm
f, _ = pipeline.stage_features(); f = pipeline.with_targets(f)
mp = pd.read_parquet("../.cache/minutes_preds.parquet"); f = jrm.prepare(f, mp)
f["q"] = pd.read_parquet("../.cache/jrm_q.parquet")["q"]
sets = pd.read_parquet("../.cache/jrm_train_sets.parquet"); ft = f.join(sets)
s = 2026
H0 = ft[ft.season == s].copy()
st, games = injury.snapshot_status("t_minus_60")
H = injury.pit_absence(H0, st, games); H.index = H0.index
H = H[H.has_snapshot].copy()
cut = pd.Timestamp("2026-01-15")
tr_h = H[H.date < cut]; te_h = H[H.date >= cut].copy()
# frozen live recipe: E_inj with PIT inputs (model trained 2021-2025), p = report-recalibrated hurdle (calibration fitted on the first half)
feats = M.ROLE + M.CONTEXT + M.LGB_EXTRA
trn = f[(f.season >= 2021) & (f.season <= 2025) & f.played]
mdl = lgb.LGBMRegressor(objective="regression", learning_rate=0.05, n_estimators=300, num_leaves=31, min_child_samples=200, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, verbose=-1, n_jobs=4).fit(trn[feats + M.INJ], trn["minutes"])
def Xpit(x):
    X = x[feats + M.INJ].copy()
    for c in M.INJ: X[c] = x[f"{c}_pit"]
    return X
te_h["m_frozen"] = np.clip(mdl.predict(Xpit(te_h)), 0.5, 48)
lg = lambda p: np.log(np.clip(p, .01, .99) / (1 - np.clip(p, .01, .99)))
def design(x, base):
    return pd.concat([lg(x[base]).rename("logit")] + [(x["inj_status"] == k).astype(float).rename(k) for k in ("OUT", "DOUBTFUL", "QUESTIONABLE", "PROBABLE", "AVAILABLE")], axis=1)
lrp = LogisticRegression(C=10, max_iter=500).fit(design(tr_h, "p_play"), tr_h["played"].astype(float))
te_h["p_frozen"] = lrp.predict_proba(design(te_h, "p_play"))[:, 1]
# JRM with the report: eligibility head calibrated on the first half (OUT / DOUBTFUL fixed at their empirical rates)
Xq = lambda x: design(x, "q").drop(columns=["OUT", "DOUBTFUL"])
fixed = {k: float(tr_h.loc[tr_h.inj_status == k, "elig"].mean()) for k in ("OUT", "DOUBTFUL")}
keep = ~tr_h.inj_status.isin(["OUT", "DOUBTFUL"])
lrq = LogisticRegression(C=10, max_iter=500).fit(Xq(tr_h)[keep], tr_h.loc[keep, "elig"].astype(float))
q_rep = lrq.predict_proba(Xq(te_h))[:, 1]
for k, v in fixed.items(): q_rep = np.where(te_h.inj_status == k, v, q_rep)
te_h["q_rep"] = q_rep
tr = ft[(ft.season < s) & (ft.season >= s - 5) & ft.elig & ft["rank_e"].notna()]
heads = jrm.fit_heads(tr)
# scenario inference needs whole team-games: predict on the second-half team-games of the 2026 pool
cur = ft[(ft.season == s) & ft.game_id.isin(set(te_h.game_id))].copy()
cur["q_rep"] = te_h["q_rep"].reindex(cur.index)
cur["q_rep"] = cur["q_rep"].fillna(cur["q"])
out = jrm.predict_season(cur, cur["q_rep"].to_numpy(), heads, S=64, alloc="uniform", seed=3)
te = te_h.join(out[["p_jrm", "u_jrm", "m_jrm"]])
te["y0"] = te["min_act0"].fillna(0)
P = te[te.played]; y = P.minutes.to_numpy()
print("2025-26 second half, official PIT reports:  n team-games %d, player rows %d, played rows %d" % (te.groupby(["game_id", "team"]).ngroups, len(te), len(P)))
dev_mask = None
def row(name, m):
    e = m - y; return "%-34s MAE %.3f RMSE %.3f bias %+.3f" % (name, np.abs(e).mean(), np.sqrt((e ** 2).mean()), e.mean())
print(row("frozen live recipe (E_inj PIT)", P.m_frozen.to_numpy())); print(row("JRM with report", P.m_jrm.to_numpy()))
d1 = diff_ci(np.abs(P.m_jrm.to_numpy() - y), np.abs(P.m_frozen.to_numpy() - y), P.game_id.to_numpy()); print("dMAE JRM-report vs frozen-live: %+.4f [%+.4f, %+.4f]" % (d1["mean_diff"], *d1["ci95"]))
for lab, m in (("starters", P.start_p_ewm8.fillna(0) >= .5), ("bench", P.start_p_ewm8.fillna(0) < .5)):
    x = P[m]; print("  %-8s n=%5d  frozen MAE %.3f bias %+.3f | JRM-report MAE %.3f bias %+.3f" % (lab, len(x), (x.m_frozen - x.minutes).abs().mean(), (x.m_frozen - x.minutes).mean(), (x.m_jrm - x.minutes).abs().mean(), (x.m_jrm - x.minutes).mean()))
print("P(play) Brier: frozen %.4f  JRM %.4f" % (((te.p_frozen - te.played) ** 2).mean(), ((te.p_jrm - te.played) ** 2).mean()))
te["pm_f"] = te.p_frozen * te.m_frozen
g = te.groupby(["game_id", "team"]); act = g.y0.sum()
for lab, v in (("frozen live recipe sum(p*m)", g.pm_f.sum()), ("JRM sum", g.u_jrm.sum())):
    r = v / act; print("team sum / realised: %-28s mean %.3f sd %.3f outside .88-1.12: %.3f" % (lab, r.mean(), r.std(), ((r < .88) | (r > 1.12)).mean()))
u = te.y0; print("unconditional MAE of p*m: frozen %.3f  JRM %.3f" % ((te.pm_f - u).abs().mean(), (te.u_jrm - u).abs().mean()))
