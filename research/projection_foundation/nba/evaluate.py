"""Evaluation helpers producing CONTRACT.md model rows (game-clustered bootstrap CIs via pf_core.metrics)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from pf_core import metrics
from pf_core.dists import DistBatch

N_BOOT = 1000


def model_row(name: str, split: str, y, mean, clusters, dist: DistBatch | None = None, thresholds=None,
              base_loss=None, inc_loss=None, loss=None, verdict: str = "") -> dict:
    """One `families[].models[]` row. `loss` is the per-row loss used in comparisons (CRPS if a distribution
    exists, else absolute error); base_loss / inc_loss are the same loss for the baseline / incumbent on the
    same rows (None -> comparison omitted)."""
    y = np.asarray(y, float)
    pm = metrics.point_metrics(y, mean)
    row = {"model": name, "split": split, "n_obs": int(len(y)), "n_clusters": int(pd.Series(clusters).nunique()),
           "mae": round(pm["mae"], 4), "rmse": round(pm["rmse"], 4), "bias": round(pm["bias"], 4),
           "crps": None, "log_score": None, "cover_50": None, "cover_80": None, "cover_90": None,
           "pit_var_ratio": None}
    if dist is not None:
        dm = metrics.dist_metrics(y, dist, thresholds=thresholds)
        row.update({"crps": round(dm["crps"], 4), "log_score": round(dm["log_score"], 4),
                    "cover_50": round(dm["cover_50"], 4), "cover_80": round(dm["cover_80"], 4),
                    "cover_90": round(dm["cover_90"], 4), "pit_var_ratio": round(dm["pit_var_ratio"], 4)})
        if thresholds:
            row["thresholds"] = {k: {kk: round(vv, 4) for kk, vv in v.items()} for k, v in dm["thresholds"].items()}
    if loss is None:
        loss = dist.crps(y) if dist is not None else np.abs(np.asarray(mean, float) - y)
    row["vs_baseline"] = _cmp(loss, base_loss, clusters)
    row["vs_incumbent"] = _cmp(loss, inc_loss, clusters) if inc_loss is not None else None
    row["verdict"] = verdict
    return row


def _cmp(loss, other, clusters):
    if other is None:
        return {"mean_diff": 0.0, "ci95": [0.0, 0.0]}
    loss = np.asarray(loss, float)
    other = np.asarray(other, float)
    ok = np.isfinite(loss) & np.isfinite(other)
    r = metrics.cluster_bootstrap_diff(loss[ok], other[ok], np.asarray(clusters)[ok], n_boot=N_BOOT)
    return {"mean_diff": round(r["mean_diff"], 4), "ci95": [round(r["ci95"][0], 4), round(r["ci95"][1], 4)],
            "n_obs": r["n_obs"]}


def diff_ci(loss_a, loss_b, clusters) -> dict:
    return _cmp(loss_a, loss_b, clusters)


def segment_bias(df: pd.DataFrame, by, y_col: str, pred_col: str, min_n: int = 200) -> list[dict]:
    rows = metrics.segment_table(df, by, y_col, pred_col, min_n=min_n)
    return [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()} for r in rows]
