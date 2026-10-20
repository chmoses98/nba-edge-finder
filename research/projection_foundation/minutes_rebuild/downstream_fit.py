"""Phase 3 downstream: refit the frozen stat ladders (same frozen hyper-parameters, no retuning) with the candidate's minutes forecast as `min_col`.
Variants: jrm = JRM minutes (no availability info); frozen_inj = E_inj minutes; jrm_set = JRM given the eligible set.  Frozen baseline = cached stats_*.parquet."""
import sys, json, time
sys.path.insert(0, ".."); sys.path.insert(0, ".")
import numpy as np, pandas as pd
from nba import pipeline, minutes as M, stats as S
from nba.common import FAMILIES
def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)
frozen = json.load(open("../results/frozen_params.json"))
f, _ = pipeline.stage_features(); f = pipeline.with_targets(f)
mp = pd.read_parquet("../.cache/minutes_preds.parquet")
R = pd.concat([pd.read_parquet("../.cache/jrm_pred_u3.parquet"), pd.read_parquet("../.cache/jrm_pred_holdout.parquet")])
f = f.join(mp[["E", "E_inj"]]).join(R[["m_jrm", "m_jrm_or"]])
variants = sys.argv[1].split(",") if len(sys.argv) > 1 else ["jrm", "frozen_inj", "jrm_set"]
colmap = {"jrm": "m_jrm", "frozen_inj": "E_inj", "jrm_set": "m_jrm_or"}
for v in variants:
    f["_min"] = f[colmap[v]].astype(float)
    for fam, (col, gkey, rungs) in FAMILIES.items():
        out, _ = S.fit_family(f, col, "_min", M.INJ, frozen=frozen["families"][fam]["params"])
        out.to_parquet(f"../.cache/ds_{v}_{col}.parquet")
        log(f"{v} {col} done")
