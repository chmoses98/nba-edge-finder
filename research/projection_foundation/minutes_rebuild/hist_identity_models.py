"""Phase 1 (history, models): state-consistency of the FROZEN minutes models.
 R_present(t) = sum over players who played of the model's E[min|play] / realised team minutes
 (i.e. the model is told the truth about who is present; if it were state-consistent this would average 1 in every health state)."""
import numpy as np, pandas as pd
f = pd.read_parquet("../.cache/features.parquet", columns=["game_id","team","season","date","pid","played","minutes","games_in_season","minutes_p_ewm8","team_changed"])
mp = pd.read_parquet("../.cache/minutes_preds.parquet")
f = f.join(mp[["E","E_inj","F","B","A","p_play"]])
f = f[(f.season >= 2017)]
f["act"] = f["minutes"].where(f["played"], 0).fillna(0)
f["lvl"] = f["minutes_p_ewm8"].fillna(0)
f["rank"] = f.groupby(["game_id","team"])["lvl"].rank(ascending=False, method="first")
res = {}
g = f.groupby(["game_id","team"])
t = pd.DataFrame({"season": g["season"].first(), "gis": g["games_in_season"].first(), "act": g["act"].sum()})
for k in ["A","B","E","E_inj","F"]:
    t[f"pres_{k}"] = f[f.played].groupby(["game_id","team"])[k].sum()
    t[f"pool_{k}"] = (f["p_play"] * f[k]).groupby([f["game_id"], f["team"]]).sum()
t["top9"] = f[f["rank"] <= 9].groupby(["game_id","team"])["played"].mean()
t = t.dropna(subset=["pres_E"])
def tab(by, cols):
    return t.groupby(by, observed=True).apply(lambda x: pd.Series({"n": len(x), **{c: (x[c] / x["act"]).mean() for c in cols}})).round(3)
t["top9_bin"] = pd.cut(t.top9, [0, .6, .78, .9, 1.01], labels=["<=6/9", "7/9", "8/9", "9/9"])
t["gis_bin"] = pd.cut(t.gis, [-1, 0, 4, 14, 40, 200], labels=["opener", "g2-5", "g6-15", "g16-41", "g42+"])
print("sum over PRESENT players of E[min|play] / realised team minutes   (state-consistent model => 1.0 everywhere)")
print(tab("top9_bin", ["pres_A","pres_B","pres_E","pres_E_inj","pres_F"]))
print(tab("gis_bin", ["pres_E","pres_E_inj"]))
print("\nsum over POOL of p_hurdle*E[min|play] / realised team minutes (the quantity the live gate tests):")
print(tab("gis_bin", ["pool_E","pool_E_inj"]))
# magnitude of required scaling: |ratio-1| envelopes
for k in ["pres_E_inj","pool_E"]:
    r = t[k] / t["act"]
    print(k, "p05/p50/p95: %.3f %.3f %.3f" % tuple(r.quantile([.05,.5,.95])), "share outside 0.88-1.12: %.3f" % ((r<.88)|(r>1.12)).mean())
t.to_parquet("hist_team_identity_models.parquet")
