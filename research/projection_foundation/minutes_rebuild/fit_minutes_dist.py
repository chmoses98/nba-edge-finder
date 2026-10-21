"""Empirical conditional-minutes residual distribution around the JRM forecast, fitted on DEV (2018-22) walk-forward predictions only."""
import sys, json
sys.path.insert(0, ".."); sys.path.insert(0, ".")
import numpy as np, pandas as pd
from pf_core import models
from nba import minutes_jrm as jrm
f = pd.read_parquet("../.cache/features.parquet", columns=["season","played","minutes"])
R = pd.read_parquet("../.cache/jrm_pred_u.parquet")
d = f.join(R, how="inner")
dev = d[(d.season <= 2022) & d.played & d.m_jrm.notna()]
prm = models.fit_dist_params("empirical_resid", dev.minutes.to_numpy(), dev.m_jrm.to_numpy(), K=61, n_bins=8)
json.dump(prm, open(jrm.ASSETS / "minutes_dist.json", "w"), default=float)
print("fitted on", len(dev), "rows; edges", np.round(prm["edges"], 1))
