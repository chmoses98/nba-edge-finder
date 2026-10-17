"""Historical check of the team reconciliation gate on the study's cached out-of-sample predictions (validation + holdout).

    python -m nba.live.reconcile_eval            # reads .cache/*.parquet written by nba.pipeline; ~1 min, ~2 GB

Question 1: how often does the gate act on ordinary (historical) rosters?  (it should be rare)
Question 2: when it acts, are player-level errors lower after normalising minutes / points to the team projection?
Players are the candidate pool of the study (P(play) x E[minutes | play], P(play) x E[points | play]) and the scored frame
is conditional on playing, exactly like the stat families. Nothing is fitted here."""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from .. import data
from ..common import split_of
from . import reconcile as REC

C = data.PF_DIR / ".cache"
FIRST_SCORED = 2017


def main() -> int:
    f = pd.read_parquet(C / "features.parquet", columns=["game_id", "team", "season", "pid", "played", "minutes", "pts"])
    mp = pd.read_parquet(C / "minutes_preds.parquet", columns=["E", "p_play"])
    sp = pd.read_parquet(C / "stats_pts.parquet", columns=["E"])
    tt = pd.read_parquet(C / "team_preds.parquet", columns=["game_id", "team", "D"])
    f = f[f["season"] >= FIRST_SCORED].copy()
    f["split"] = f["season"].map(split_of)
    f = f[f["split"].isin(["validation", "holdout"])]
    f["p_play"], f["m"], f["pts_hat"] = mp.loc[f.index, "p_play"], mp.loc[f.index, "E"], sp.loc[f.index, "E"]
    f = f.dropna(subset=["p_play", "m", "pts_hat"])
    team = {(g, t): d for g, t, d in zip(tt["game_id"], tt["team"], tt["D"])}
    out = {"n_team_games": 0}
    recs, scales = [], []
    for split, g in f.groupby("split"):
        df = pd.DataFrame({"game_id": g["game_id"], "team": g["team"], "p_play": g["p_play"], "minutes": g["m"], "pts": g["pts_hat"]})
        sc, rc = REC.reconcile(df, team)
        r = pd.DataFrame(rc)
        r["split"] = split
        recs.append(r)
        g = g.assign(min_scale=sc["min_scale"], usage_scale=sc["usage_scale"])
        scales.append(g)
    R = pd.concat(recs)
    G = pd.concat(scales)
    R["acted"] = R["action"] != "none"
    out["n_team_games"] = int(len(R))
    out["minutes_ratio_percentiles"] = {str(q): round(float((R["minutes_sum_raw"] / REC.BUDGET).quantile(q)), 3) for q in (0.01, 0.05, 0.5, 0.95, 0.99)}
    out["points_ratio_percentiles"] = {str(q): round(float(R["ratio_raw"].quantile(q)), 3) for q in (0.01, 0.05, 0.5, 0.95, 0.99)}
    out["gate_acted_share"] = round(float(R["acted"].mean()), 4)
    out["status_after"] = R["status"].value_counts().to_dict()
    out["action_counts"] = R["action"].value_counts().to_dict()
    # player-level error on rows of team-games where the gate acted (played players only, conditional frame)
    act = R[R["acted"]][["game_id", "team"]]
    sub = G.merge(act, on=["game_id", "team"]).query("played")
    if len(sub):
        raw = sub["pts_hat"].to_numpy()
        adj = sub["pts_hat"].to_numpy() * sub["min_scale"].to_numpy() * sub["usage_scale"].to_numpy()
        y = sub["pts"].to_numpy()
        out["acted_rows"] = {"n_player_games": int(len(sub)), "n_team_games": int(len(act)),
                             "mae_raw": round(float(np.mean(np.abs(raw - y))), 4), "mae_reconciled": round(float(np.mean(np.abs(adj - y))), 4),
                             "bias_raw": round(float(np.mean(raw - y)), 4), "bias_reconciled": round(float(np.mean(adj - y)), 4)}
        # game-clustered paired bootstrap on the absolute-error difference
        from pf_core.metrics import cluster_bootstrap_diff
        out["acted_rows"]["mae_diff_ci"] = cluster_bootstrap_diff(np.abs(adj - y), np.abs(raw - y), sub["game_id"].to_numpy(), n_boot=500)
    # minutes
    sm = G.merge(act, on=["game_id", "team"]).query("played")
    if len(sm):
        m_raw, m_adj, ym = sm["m"].to_numpy(), sm["m"].to_numpy() * sm["min_scale"].to_numpy(), sm["minutes"].to_numpy()
        out["acted_rows"]["minutes_mae_raw"] = round(float(np.mean(np.abs(m_raw - ym))), 4)
        out["acted_rows"]["minutes_mae_reconciled"] = round(float(np.mean(np.abs(m_adj - ym))), 4)
    print(json.dumps(out, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
