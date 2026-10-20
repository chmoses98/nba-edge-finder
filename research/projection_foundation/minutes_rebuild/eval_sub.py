import sys
import numpy as np, pandas as pd
sys.path.insert(0, ".."); sys.path.insert(0, ".")
tag = sys.argv[1]; seasons = [int(x) for x in sys.argv[2].split(",")]
f = pd.read_parquet("../.cache/features.parquet", columns=["game_id","team","season","pid","played","minutes","in_box","dnp","dnp_reason","start_p_ewm8","games_in_season","team_changed","games_with_team","minutes_p_n","minutes_p_ewm8"])
from nba import minutes_jrm as jrm
f["elig"] = jrm.eligible_flag(f)
mp = pd.read_parquet("../.cache/minutes_preds.parquet")
R = pd.read_parquet(f"../.cache/jrm_pred_{tag}.parquet")
d = f.join(mp[["E","E_inj","p_play"]]).join(R, how="inner")
d = d[d.season.isin(seasons)].copy()
d["act"] = d.minutes.where(d.played, 0).fillna(0)
d["newish"] = ((d.team_changed == 1) | (d.games_with_team < 5)) & d.elig
d["nohist"] = d.minutes_p_n.fillna(0) < 3
g = d.groupby(["game_id","team"])
t = pd.DataFrame({"act": g.act.sum(), "n_elig": g.elig.sum(), "n_new": g.newish.sum(), "n_nohist": (d.nohist & d.elig).groupby([d.game_id,d.team]).sum(), "gis": g.games_in_season.first(),
                  "E": (d.p_play*d.E).groupby([d.game_id,d.team]).sum(), "jrm": g.u_jrm.sum()})
d = d.join(t[["n_elig","n_new","n_nohist","gis"]], on=["game_id","team"])
P = d[d.played].copy()
def show(name, col, bins, labels):
    P["b"] = pd.cut(P[col], bins, labels=labels)
    tt = t.copy(); tt["b"] = pd.cut(tt[col], bins, labels=labels)
    print(f"\n{name}")
    print("%-10s %7s | %-24s | %-24s | %-24s | %s" % ("group","n","E mae/bias","JRM mae/bias","E_inj | JRM|set mae/bias", "team sum/realised  E(sd) JRM(sd)  [n team-games]"))
    for b, x in P.groupby("b", observed=True):
        q = tt[tt.b == b]
        print("%-10s %7d | %5.3f %+6.3f           | %5.3f %+6.3f           | %5.3f %+5.2f | %5.3f %+5.2f | %.3f(%.3f) %.3f(%.3f) [%d]" % (
            b, len(x), (x.E-x.minutes).abs().mean(), (x.E-x.minutes).mean(), (x.m_jrm-x.minutes).abs().mean(), (x.m_jrm-x.minutes).mean(),
            (x.E_inj-x.minutes).abs().mean(), (x.E_inj-x.minutes).mean(), (x.m_jrm_or-x.minutes).abs().mean(), (x.m_jrm_or-x.minutes).mean(),
            (q.E/q.act).mean(), (q.E/q.act).std(), (q.jrm/q.act).mean(), (q.jrm/q.act).std(), len(q)))
show("eligible players per team-game (depth of the available roster)", "n_elig", [0,10,12,14,30], ["<=10","11-12","13-14","15+"])
show("new-to-team players among the eligible (roster turnover)", "n_new", [-1,0,1,3,30], ["0","1","2-3","4+"])
show("players with <3 career games among the eligible", "n_nohist", [-1,0,1,30], ["0","1","2+"])
show("games into the season", "gis", [-1,0,4,14,200], ["opener","g2-5","g6-15","g16+"])
