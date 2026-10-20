"""Phase 1: exact additive decomposition of the live-slate team-minutes overshoot  sum p*E[min|play] - 241.5.

  M_raw - 241.5 = A (roster turnover) + B (availability conditioning) + C (conditional-minutes drift) + D (players without NBA history)
with H = sum_i total_minutes_last_season_i / 82 over the CURRENT roster (history players only):
  A = H - 241.5          carried-over minutes of arrivals not removed for departures (last season's identity: a roster sums to ~241.5)
  B = sum_hist (p_i - g_i/82) * mh_i      live participation probability vs last season's games-played share
  C = sum_hist  p_i * (m_i - mh_i)        model's E[min|play] vs the player's own last-season minutes when playing
  D = sum_nohist p_i * m_i                players with no regular-season NBA minutes last season (rookies / returning / two-way)
Usage: python phase1_decomposition.py FEED.json [HOOPR_DIR]
"""
import json, sys
import numpy as np, pandas as pd

feed = json.load(open(sys.argv[1]))
hoopr = sys.argv[2] if len(sys.argv) > 2 else "../.cache/hoopr"
box = pd.read_parquet(f"{hoopr}/player_box_2026.parquet")
box = box[(box["season_type"] == 2) & box["athlete_id"].notna()].copy()
box["minutes"] = pd.to_numeric(box["minutes"], errors="coerce").fillna(0)
box["played"] = (box["minutes"] > 0) & ~box["did_not_play"].fillna(False).astype(bool)
last = box[box["played"]].groupby("athlete_id").agg(tm=("minutes", "sum"), g=("minutes", "size"))
scale = {(r["team"]): r["minutes_scale"] for r in feed["reconciliation"]}
rows = []
for p in feed["players"]:
    if p["family"] != "minutes":
        continue
    pid = int(str(p["player_id"]).split(":")[-1])
    s = scale.get(p["team"], 1.0)
    m_pre = p["mean"] / s if s else p["mean"]
    pp = p["participation"]["p_play"]
    L = last.loc[pid] if pid in last.index else None
    rows.append(dict(team=p["team"], pid=pid, name=p["name"], p=pp, m=m_pre, status=p["participation"]["status"],
                     tm=0.0 if L is None else L["tm"], g=0 if L is None else L["g"]))
d = pd.DataFrame(rows)
d["has_hist"] = d["g"] >= 1
d["mh"] = np.where(d["g"] > 0, d["tm"] / d["g"].clip(lower=1), 0.0)
out = []
for t, x in d.groupby("team"):
    M = (x.p * x.m).sum()
    h = x[x["has_hist"]]
    H = h.tm.sum() / 82.0
    A = H - 241.5
    B = ((h.p - h.g / 82.0) * h.mh).sum()
    C = (h.p * (h.m - h.mh)).sum()
    D = (x[~x["has_hist"]].p * x[~x["has_hist"]].m).sum()
    out.append(dict(team=t, M_raw=M, H=H, A_turnover=A, B_avail=B, C_minutes=C, D_nohist=D, check=A + B + C + D + 241.5 - M,
                    n=len(x), n_nohist=int((~x["has_hist"]).sum())))
r = pd.DataFrame(out).round(1).sort_values("M_raw", ascending=False)
pd.set_option("display.width", 200)
print(r.to_string(index=False))
tot = r[["M_raw", "H", "A_turnover", "B_avail", "C_minutes", "D_nohist"]].mean().round(1)
print("\nmean over teams:", tot.to_dict())
print("mean overshoot M_raw-241.5 =", round((r.M_raw - 241.5).mean(), 1))
d.to_csv("phase1_players.csv", index=False)
