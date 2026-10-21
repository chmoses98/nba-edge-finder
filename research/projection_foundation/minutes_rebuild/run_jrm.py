"""Walk-forward run of the joint rotation model on the cached frozen-engine frame.  python run_jrm.py SEASONS [--alloc var] [--S 24] [--tag x]"""
import sys, time, json
sys.path.insert(0, ".."); sys.path.insert(0, ".")
import numpy as np, pandas as pd
from nba import pipeline, minutes as M
from nba.common import lgb_walkforward
from nba import minutes_jrm as jrm

args = sys.argv[1:]
seasons = [int(x) for x in args[0].split(",")]
alloc = args[args.index("--alloc") + 1] if "--alloc" in args else "var"
S = int(args[args.index("--S") + 1]) if "--S" in args else 24
tag = args[args.index("--tag") + 1] if "--tag" in args else f"{alloc}"
def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

f, _ = pipeline.stage_features()
f = pipeline.with_targets(f)
mp = pd.read_parquet("../.cache/minutes_preds.parquet")
f = jrm.prepare(f, mp)
log(f"frame {f.shape}")
# eligibility head (walk-forward)
qf = f[M.HURDLE + ["lvl", "season"]].copy()
qf["y"] = f["elig"].astype(float)
f["q"] = lgb_walkforward(qf, M.HURDLE + ["lvl"], "y", objective="binary", params=dict(n_estimators=250)).clip(0.005, 0.995)
log("q head done")
tr_path = f"../.cache/jrm_train_sets_{jrm.LEVEL}.parquet"
try:
    sets = pd.read_parquet(tr_path)
except Exception:
    sets = jrm.build_training(f); sets.to_parquet(tr_path)
log(f"training set features {sets.shape}")
ft = f.join(sets)
res = []
for s in seasons:
    tr = ft[(ft.season < s) & (ft.season >= s - 5) & ft.elig & ft["rank_e"].notna() & (ft.season >= 2016)]
    heads = jrm.fit_heads(tr)
    cur = ft[ft.season == s]
    out = jrm.predict_season(cur, cur["q"].to_numpy(), heads, S=S, alloc="uniform", seed=s)
    orc = jrm.predict_season(cur, cur["elig"].to_numpy(float), heads, S=1, alloc="uniform", seed=s)      # eligible set known (report / box)
    out = out.join(orc[["p_jrm", "u_jrm", "m_jrm", "m_raw_jrm"]].add_suffix("_or"))
    res.append(out)
    log(f"season {s}: {len(cur)} rows, train {len(tr)}")
R = pd.concat(res)
R.to_parquet(f"../.cache/jrm_pred_{tag}.parquet")
f[["q"]].to_parquet(f"../.cache/jrm_q_{jrm.LEVEL}.parquet")
log("saved")
