"""Phase 1 (history): replay the LIVE publication recipe on 2025-26 (archived PIT reports): report-recalibrated p x report-aware minutes,
then the live team test sum(p*m)/241.5.  Shows whether the 0.76-0.88 live scales are a property of the recipe or of the opening-night inputs."""
import json, sys
import numpy as np, pandas as pd
sys.path.insert(0, "..")
import lightgbm as lgb
from nba import minutes as M, injury
from nba.live import participation as PART
f = pd.read_parquet("../.cache/features.parquet")
mp = pd.read_parquet("../.cache/minutes_preds.parquet")
f = M.prep(f)
f = f.join(mp[["E", "E_inj", "p_play"]])
st, games = injury.snapshot_status("t_minus_60")
H = f[f.season == 2026].copy()
H = injury.pit_absence(H, st, games); H.index = f.index[f.season == 2026]
H = H[H.has_snapshot].copy()
feats = M.ROLE + M.CONTEXT + M.LGB_EXTRA
trn = f[(f.season >= 2021) & (f.season <= 2025) & f.played]
mdl = lgb.LGBMRegressor(objective="regression", learning_rate=0.05, n_estimators=300, num_leaves=31, min_child_samples=200,
                        subsample=0.8, subsample_freq=1, colsample_bytree=0.8, verbose=-1, n_jobs=4).fit(trn[feats + M.INJ], trn["minutes"])
X = H[feats + M.INJ].copy()
for c in M.INJ: X[c] = H[f"{c}_pit"]
H["m_pit"] = np.clip(mdl.predict(X), 0.5, 48)
calib = PART.load_calibration()
cls = H["inj_status"].replace({"AVAILABLE": "AVAILABLE"}).tolist()
H["p_cal"] = PART.calibrated_p_play(H["p_play"].to_numpy(), cls, calib)
H["act"] = H["minutes"].where(H["played"], 0).fillna(0)
H["pm"] = H["p_cal"] * H["m_pit"]
g = H.groupby(["game_id", "team"])
t = pd.DataFrame({"gis": g["games_in_season"].first(), "act": g["act"].sum(), "M": g["pm"].sum(), "sum_p": g["p_cal"].sum(),
                  "n_pool": g.size()})
t["ratio"] = t.M / 241.5
t["gis_bin"] = pd.cut(t.gis, [-1, 0, 4, 14, 40, 200], labels=["opener", "g2-5", "g6-15", "g16-41", "g42+"])
print("2025-26, live recipe: sum_pool p_cal * m_pit / 241.5   (n team-games = %d)" % len(t))
print(t.groupby("gis_bin", observed=True).agg(n=("ratio","size"), ratio=("ratio","mean"), p05=("ratio", lambda s: s.quantile(.05)), p95=("ratio", lambda s: s.quantile(.95)),
      sum_p=("sum_p","mean"), pool=("n_pool","mean"), out_of_12=("ratio", lambda s: ((s-1).abs()>.12).mean())).round(3))
print("overall outside 0.88-1.12: %.3f ; mean ratio %.3f ; scale needed >=10%% (|r-1|>.1): %.3f" % (((t.ratio<.88)|(t.ratio>1.12)).mean(), t.ratio.mean(), ((t.ratio-1).abs()>.10).mean()))
t.to_parquet("hist_live_recipe_2026.parquet")

# ---- by rotation rank (rank by conditional minutes among players with p>0.05)
H["rk"] = H[H.p_cal > 0.05].groupby(["game_id", "team"])["m_pit"].rank(ascending=False, method="first")
hr = H[H.rk.notna()].groupby("rk").agg(n=("pm", "size"), hist_pm=("pm", "mean"), hist_p=("p_cal", "mean"), hist_act=("act", "mean"))
live = pd.read_csv("phase1_players.csv")
live = live[live.p > 0.05].copy()
live["rk"] = live.groupby("team")["m"].rank(ascending=False, method="first")
live["pm"] = live.p * live.m
lr = live.groupby("rk").agg(live_pm=("pm", "mean"), live_p=("p", "mean"))
cmp_ = hr.join(lr)[["hist_p", "live_p", "hist_pm", "live_pm", "hist_act"]].round(2)
cmp_["live_minus_hist_pm"] = (cmp_.live_pm - cmp_.hist_pm).round(2)
print("\nmean p*m by rotation rank: 2025-26 replay (hist) vs 2026-27 live slate; hist_act = realised minutes")
print(cmp_.head(18).to_string())
print("sum over ranks (live-hist) =", round((cmp_.live_pm - cmp_.hist_pm).fillna(0).sum(), 1))
print("excess by rank group: ranks1-8: %.1f  ranks9-11: %.1f  ranks12+: %.1f" % tuple(
    (cmp_.live_minus_hist_pm.fillna(0)[(cmp_.index >= a) & (cmp_.index <= b)]).sum() for a, b in ((1, 8), (9, 11), (12, 30))))
