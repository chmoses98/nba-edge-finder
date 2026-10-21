"""Phase 1 (history): does sum_i p_i * m_i (marginal conditional minutes x participation, both point-in-time) conserve 240+OT,
and how does it depend on roster health? Uses only PIT features (EWMAs lagged one game)."""
import numpy as np, pandas as pd
f = pd.read_parquet("../.cache/features.parquet", columns=["game_id","team","season","date","pid","played","minutes","in_box",
      "minutes_p_ewm8","minutes_p_ewm20","play01_ewm10","games_in_season","team_changed","games_with_team","minutes_p_n"])
f = f[f.season >= 2017]
f["m"] = f["minutes_p_ewm8"].fillna(f["minutes_p_ewm20"])
f["p"] = f["play01_ewm10"].fillna(0.5).clip(0.01, 0.99)
f["pm"] = f["p"] * f["m"].fillna(0)
f["a"] = f["minutes"].where(f["played"], 0).fillna(0)
g = f.groupby(["game_id", "team"])
t = pd.DataFrame({
    "season": g["season"].first(), "gis": g["games_in_season"].first(),
    "S_pm": g["pm"].sum(),                                  # analogue of the live 'M_raw' (all candidates)
    "S_act": g["a"].sum(),                                  # realised team minutes (240 + OT)
    "n_played": g["played"].sum(),
})
# capacity of the players who actually played (sum of their marginal conditional minutes)
f["m_pl"] = np.where(f["played"], f["m"].fillna(0), 0.0)
t["S_present"] = f.groupby(["game_id", "team"])["m_pl"].sum()
# 'full health': share of the team's top-9 (by prior level in the pool) that played
f["rank"] = g["m"].rank(ascending=False, method="first")
top = f[f["rank"] <= 9].groupby(["game_id", "team"])["played"].mean()
t["top9_avail"] = top
t["ratio_pm"] = t.S_pm / 241.5
t["ratio_present"] = t.S_present / t.S_act
print("overall ratio sum(p*m)/241.5 : mean %.3f  p05 %.3f p50 %.3f p95 %.3f" % ((t.ratio_pm.mean(),) + tuple(t.ratio_pm.quantile([.05,.5,.95]))))
print("\nby games into season (all players, pool):")
t["gis_bin"] = pd.cut(t.gis, [-1, 0, 4, 14, 40, 200], labels=["opener", "g2-5", "g6-15", "g16-41", "g42+"])
print(t.groupby("gis_bin", observed=True).agg(n=("ratio_pm", "size"), ratio_pm=("ratio_pm", "mean"), p05=("ratio_pm", lambda s: s.quantile(.05)), p95=("ratio_pm", lambda s: s.quantile(.95))).round(3))
print("\nsum of present players' marginal conditional minutes / actual team minutes, by availability of the top-9:")
t["top9_bin"] = pd.cut(t.top9_avail, [0, .6, .78, .9, 1.01], labels=["<=5/9 .. 6/9", "7/9", "8/9", "9/9 (full health)"])
print(t.groupby("top9_bin", observed=True).agg(n=("ratio_present", "size"), mean_ratio=("ratio_present", "mean"), p05=("ratio_present", lambda s: s.quantile(.05)), p95=("ratio_present", lambda s: s.quantile(.95))).round(3))
t.to_parquet("hist_team_identity.parquet")
