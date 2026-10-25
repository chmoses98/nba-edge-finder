"""Downstream diagnosis: reproduce what the LIVE publisher (nba/project.py) does to the stat ladders and compare it with the backtest recipe.

In nba.project.project_slate the minutes input of the stat ladders is `min_best`, taken from M.fit_ladder(final_only=True): it is finite ONLY for the slate season, NaN for every
earlier season (probe: scratchpad/diag/probe_nan.py). The stat LightGBM (E, E_inj) is therefore trained with the minutes features (min_hat, C_hat) all-missing and served with them
present, and opponent_factor() sees no finite C in history. The backtest (downstream_fit.py) trains with the minutes forecast finite on every historical row.

Modes (test season s, training seasons s-5..s-1, strictly earlier; hyper-parameters frozen):
  L_frozen    live recipe, minutes input = frozen E for season s only (history NaN)        -> what production does today
  L_jrm       live recipe, minutes input = JRM m_jrm for season s only (history NaN)       -> "JRM minutes + existing stat models" as published
  H_mismatch  history-consistent training with the FROZEN minutes E, served with JRM m_jrm -> the 'trained on the old minutes distribution' hypothesis
  H_frozen / H_jrm are the cached backtest runs (stats_*.parquet E / ds_jrm_*_v2.parquet), not recomputed here.
python downstream_live_recipe.py MODE FAMILY[,FAMILY..]
"""
import sys, json, time
sys.path.insert(0, ".."); sys.path.insert(0, ".")
import numpy as np, pandas as pd
from nba import pipeline, minutes as M, stats as S
from nba.common import FAMILIES, VAL, HOLDOUT
def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

mode = sys.argv[1]; fams = sys.argv[2].split(",") if len(sys.argv) > 2 else list(FAMILIES)
frozen = json.load(open("../results/frozen_params.json"))
f, _ = pipeline.stage_features(); f = pipeline.with_targets(f)
mp = pd.read_parquet("../.cache/minutes_preds.parquet")
R = pd.concat([pd.read_parquet("../.cache/jrm_pred_v2dev.parquet"), pd.read_parquet("../.cache/jrm_pred_v2hold.parquet")])
f = f.join(mp[["E"]]).join(R[["m_jrm"]])
TEST = sorted(VAL + HOLDOUT)

# ---- mismatch machinery: train the LightGBM on the frame built with the OLD minutes, predict on the frame built with the NEW minutes
_alt: list = []
_orig_lgb = S.lgb_walkforward
def _capture(df, features, target, **kw):
    _alt.append(df.copy())
    return _orig_lgb(df, features, target, **kw)
def _mismatch(df, features, target, objective="regression", params=None, window=5, first_pred=2017, final_only=False):
    import lightgbm as lgb
    k = _mismatch.k; _mismatch.k += 1
    tr_src = _alt[k]
    p = dict(objective=objective, learning_rate=0.05, n_estimators=300, num_leaves=31, min_child_samples=200, subsample=0.8, subsample_freq=1,
             colsample_bytree=0.8, reg_lambda=1.0, verbose=-1, n_jobs=1); p.update(params or {})
    pred = pd.Series(np.nan, index=df.index)
    s = sorted(df["season"].unique())[-1]
    tr = tr_src[(tr_src["season"] < s) & (tr_src["season"] >= s - window) & tr_src[target].notna()]
    m = lgb.LGBMRegressor(**p).fit(tr[features], tr[target])
    te = df["season"] == s
    pred.loc[te] = m.predict(df.loc[te, features])
    return pred

for fam in fams:
    col = FAMILIES[fam][0]; prm = frozen["families"][fam]["params"]
    parts = []
    for s in TEST:
        t0 = time.time()
        p = f[f["season"] <= s].copy()
        cur = (p["season"] == s).to_numpy()
        if mode in ("L_frozen", "L_jrm"):
            src = "E" if mode == "L_frozen" else "m_jrm"
            p["_min"] = np.where(cur, p[src].astype(float), np.nan)
            out, _ = S.fit_family(p, col, "_min", M.INJ, frozen=prm, final_only=True)
        elif mode == "H_mismatch":
            _alt.clear()
            S.lgb_walkforward = _capture
            p["_min"] = p["E"].astype(float)
            S.fit_family(p, col, "_min", M.INJ, frozen=prm, final_only=True)            # frames with the old minutes (history + season s)
            S.lgb_walkforward = _mismatch; _mismatch.k = 0
            p["_min"] = np.where(cur, p["m_jrm"].astype(float), p["E"].astype(float))     # serve JRM minutes in season s, keep the old minutes in history
            out, _ = S.fit_family(p, col, "_min", M.INJ, frozen=prm, final_only=True)
            S.lgb_walkforward = _orig_lgb
        else:
            raise SystemExit("mode")
        parts.append(out.loc[cur, ["A", "B", "C", "D", "E", "E_inj", "F", "opp_factor", "opp_n"]])
        log(f"{mode} {fam} season {s} done ({time.time() - t0:.0f}s, rows {cur.sum()})")
    pd.concat(parts).to_parquet(f"../.cache/dl_{mode}_{col}.parquet")
