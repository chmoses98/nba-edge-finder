"""Report-aware eligibility calibration (same recipe as nba/live/participation_calibration.json, but the target is ELIGIBLE = on the active list and
not injury-out, and the base is the eligibility head q): logistic regression on logit(q) + official-report status dummies, 2025-26 pool rows with a
certified T-60 snapshot (unlisted == AVAILABLE).  Also reports the first-half-fit / second-half-test Brier."""
import sys, json
sys.path.insert(0, ".."); sys.path.insert(0, ".")
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from nba import injury
from nba import minutes_jrm as jrm
f = pd.read_parquet("../.cache/features.parquet", columns=["game_id","team","season","date","pid","played","in_box","dnp","dnp_reason","usage_p_ewm8","minutes_p_ewm8","missed_streak","last_min","pos"])
f["elig"] = jrm.eligible_flag(f)
f = f.join(pd.read_parquet("../.cache/jrm_q.parquet"))
H = f[f.season == 2026].copy()
st, games = injury.snapshot_status("t_minus_60")
H2 = injury.pit_absence(H, st, games); H2.index = H.index
H = H2[H2.has_snapshot].copy()
q = H["q"].clip(0.01, 0.99)
X = pd.concat([np.log(q/(1-q)).rename("logit")] + [(H["inj_status"] == s).astype(float).rename(s) for s in ("OUT","DOUBTFUL","QUESTIONABLE","PROBABLE","AVAILABLE")], axis=1)
y = H["elig"].astype(float)
cut = pd.Timestamp("2026-01-15")
tr, te = (H["date"] < cut).to_numpy(), (H["date"] >= cut).to_numpy()
lr = LogisticRegression(C=10.0, max_iter=500).fit(X[tr], y[tr])
p2 = lr.predict_proba(X[te])[:, 1]
oo = H["inj_status"].isin(["OUT", "DOUBTFUL"]).to_numpy()[te]
p2 = np.where(oo, np.where(H["inj_status"].to_numpy()[te] == "OUT", y[H["inj_status"] == "OUT"].mean(), y[H["inj_status"] == "DOUBTFUL"].mean()), p2)
print("eligibility Brier, second half: head only %.4f  head + report %.4f  (n=%d)" % (((q[te]-y[te])**2).mean(), ((p2-y[te])**2).mean(), te.sum()))
fixed = {k: float(y[H["inj_status"] == k].mean()) for k in ("OUT", "DOUBTFUL")}
keep = ~H["inj_status"].isin(["OUT", "DOUBTFUL"]).to_numpy()
X = X.drop(columns=["OUT", "DOUBTFUL"])
lr = LogisticRegression(C=10.0, max_iter=500).fit(X[keep], y[keep])
cal = {"fixed": fixed, "recipe": "LogisticRegression(C=10) on logit(q_head) + status dummies; target = eligible (active list and not injury-out)", "n_rows": int(len(H)),
       "intercept": float(lr.intercept_[0]), "coef": dict(zip(["logit","QUESTIONABLE","PROBABLE","AVAILABLE"], map(float, lr.coef_[0])))}
json.dump(cal, open(jrm.ASSETS / "q_calibration.json", "w"), indent=1)
print(json.dumps(cal))
print(H.groupby("inj_status").elig.agg(["size","mean"]).round(3))
