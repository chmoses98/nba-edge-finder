import sys
import numpy as np, pandas as pd
tag = sys.argv[1]; seasons = [int(x) for x in sys.argv[2].split(",")]
f = pd.read_parquet("../.cache/features.parquet", columns=["game_id","team","season","pid","played","minutes","in_box","dnp","dnp_reason","start_p_ewm8","games_in_season","team_changed","minutes_p_n","minutes_p_ewm8","missed_streak"])
mp = pd.read_parquet("../.cache/minutes_preds.parquet")
R = pd.read_parquet(f"../.cache/jrm_pred_{tag}.parquet")
d = f.join(mp[["E","E_inj","F","B","A","p_play"]]).join(R, how="inner")
d = d[d.season.isin(seasons)]
d["act"] = d.minutes.where(d.played, 0).fillna(0)
P = d[d.played].copy(); y = P.minutes
def line(name, m, sub=None):
    s = P if sub is None else sub
    yy = s.minutes; mm = m.loc[s.index]
    return dict(model=name, n=len(s), mae=(mm-yy).abs().mean(), rmse=np.sqrt(((mm-yy)**2).mean()), bias=(mm-yy).mean())
print("== F1: pregame, no availability information beyond history (conditional frame, seasons %s)" % seasons)
print(pd.DataFrame([line("A", P.A), line("B", P.B), line("E (frozen best)", P.E), line("F", P.F), line("JRM", P.m_jrm), line("JRM no-alloc", P.m_raw_jrm)]).round(3).to_string(index=False))
print("\n== F2: eligible set known (E_inj uses the retrospective absence proxy; JRM uses the realised eligible set)")
print(pd.DataFrame([line("E_inj", P.E_inj), line("JRM|eligible set", P.m_jrm_or), line("JRM|set no-alloc", P.m_raw_jrm_or)]).round(3).to_string(index=False))
# state subgroup: top-9 availability
f2 = d.copy()
f2["lvl"] = f2.minutes_p_ewm8.fillna(0)
f2["rank"] = f2.groupby(["game_id","team"])["lvl"].rank(ascending=False, method="first")
top9 = f2[f2["rank"]<=9].groupby(["game_id","team"])["played"].mean().rename("top9")
P = P.join(f2[["rank"]]).join(top9, on=["game_id","team"])
P["state"] = pd.cut(P.top9, [0,.7,.9,1.01], labels=["<=6/9 present","7-8/9","9/9 full health"])
print("\nby health state (F1: E vs JRM):")
for s, x in P.groupby("state", observed=True):
    print("%-16s n=%6d  E mae %.3f bias %+.3f | JRM mae %.3f bias %+.3f | E_inj %.3f %+.3f | JRM|set %.3f %+.3f" % (s, len(x), (x.E-x.minutes).abs().mean(), (x.E-x.minutes).mean(), (x.m_jrm-x.minutes).abs().mean(), (x.m_jrm-x.minutes).mean(), (x.E_inj-x.minutes).abs().mean(), (x.E_inj-x.minutes).mean(), (x.m_jrm_or-x.minutes).abs().mean(), (x.m_jrm_or-x.minutes).mean()))
P["role"] = np.where(P.start_p_ewm8.fillna(0) >= .5, "starter-role", "bench-role")
print("\nby role:")
for s, x in P.groupby("role"):
    print("%-13s n=%6d  E mae %.3f bias %+.3f | JRM mae %.3f bias %+.3f | E_inj %.3f %+.3f | JRM|set %.3f %+.3f" % (s, len(x), (x.E-x.minutes).abs().mean(), (x.E-x.minutes).mean(), (x.m_jrm-x.minutes).abs().mean(), (x.m_jrm-x.minutes).mean(), (x.E_inj-x.minutes).abs().mean(), (x.E_inj-x.minutes).mean(), (x.m_jrm_or-x.minutes).abs().mean(), (x.m_jrm_or-x.minutes).mean()))
P["rk"] = pd.cut(P["rank"], [0,5,8,10,20], labels=["rank1-5","6-8","9-10","11+"])
print("\nby level rank in the pool:")
for s, x in P.groupby("rk", observed=True):
    print("%-8s n=%6d  E mae %.3f bias %+.3f | JRM mae %.3f bias %+.3f" % (s, len(x), (x.E-x.minutes).abs().mean(), (x.E-x.minutes).mean(), (x.m_jrm-x.minutes).abs().mean(), (x.m_jrm-x.minutes).mean()))
# conservation
g = d.groupby(["game_id","team"])
t = pd.DataFrame({"act": g.act.sum(), "jrm": g.u_jrm.sum(), "jrm_set": g.u_jrm_or.sum(), "E": (d.p_play*d.E).groupby([d.game_id,d.team]).sum(), "season": g.season.first(), "gis": g.games_in_season.first()})
print("\nteam conservation: sum over pool of p*E[min|play] / realised")
for c in ["E","jrm","jrm_set"]:
    r = t[c]/t.act
    print("  %-8s mean %.3f sd %.3f p05 %.3f p95 %.3f outside .88-1.12: %.3f" % (c, r.mean(), r.std(), r.quantile(.05), r.quantile(.95), ((r<.88)|(r>1.12)).mean()))
op = t[t.gis==0]
print("  openers n=%d: E %.3f(sd %.3f)  jrm %.3f(sd %.3f)" % (len(op), (op.E/op.act).mean(), (op.E/op.act).std(), (op.jrm/op.act).mean(), (op.jrm/op.act).std()))
pp = d[d.p_play.notna()]
print("Brier P(play): hurdle %.4f  JRM %.4f (eligibility unknown) " % (((pp.p_play-pp.played)**2).mean(), ((pp.p_jrm-pp.played)**2).mean()))
