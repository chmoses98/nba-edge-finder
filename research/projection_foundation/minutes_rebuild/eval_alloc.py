import sys
sys.path.insert(0, ".."); sys.path.insert(0, ".")
import numpy as np, pandas as pd
f = pd.read_parquet("../.cache/features.parquet", columns=["game_id","team","season","pid","played","minutes","start_p_ewm8","games_in_season"])
mp = pd.read_parquet("../.cache/minutes_preds.parquet")
R = pd.read_parquet("../.cache/jrm_pred_alloc.parquet")
d = f.join(mp[["E","p_play"]]).join(R, how="inner")
for label, ss in (("DEV 2018-22", range(2018, 2023)), ("VAL 2023-24", [2023, 2024])):
    x = d[d.season.isin(ss)]; P = x[x.played].copy(); P["role"] = np.where(P.start_p_ewm8.fillna(0) >= .5, "S", "B")
    x = x.assign(act=x.minutes.where(x.played, 0).fillna(0))
    print(label, "n=%d" % len(P))
    for name, col, ucol in (("E (frozen)", "E", None), ("none", "m_raw_jrm", "u_raw_jrm"), ("uniform", "m_jrm_uniform", "u_jrm_uniform"), ("prop", "m_jrm_prop", "u_jrm_prop"), ("var", "m_jrm", "u_jrm")):
        e = P[col] - P.minutes
        S_ = P[P.role == "S"]; B_ = P[P.role == "B"]
        tsum = (x.p_play*x.E if ucol is None else x[ucol]).groupby([x.game_id, x.team]).sum() / x.groupby(["game_id","team"]).act.sum()
        print("  %-11s MAE %.4f bias %+.3f | starters MAE %.4f bias %+.3f | bench MAE %.4f bias %+.3f | team-sum sd %.4f" % (
            name, e.abs().mean(), e.mean(), (S_[col]-S_.minutes).abs().mean(), (S_[col]-S_.minutes).mean(), (B_[col]-B_.minutes).abs().mean(), (B_[col]-B_.minutes).mean(), tsum.std()))
