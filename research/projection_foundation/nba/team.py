"""Team points: pace x efficiency (schedule-adjusted ridge ratings, refit weekly on earlier blocks only).

A  team season-to-date points (blended with last season), EB-shrunk to the PIT league mean
B  EWMA points, EB-shrunk
C  expected pace (team + opponent pace ratings) x expected efficiency (offence + opponent defence + home)
D  C + linear rest/back-to-back adjustment fitted on development (frozen)
Distribution: discretised normal, residual SD binned by the mean (fitted on development).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from pf_core import models, pit
from .common import DEV

LO, K = 50, 130


def fit_team(t: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    t = pit.sort_chrono(t.copy(), "team", "date", "game_id")
    t = pit.lagged_features(t, "team", ["pts"], halflives=(10,), season_col="season")
    t["_all"] = "league"
    burn = t["season"] == t["season"].min()
    # explicit burn-in fallback (pf_core 1.0.0 default = whole-sample mean, a look-ahead); first date only
    t["prior_pts"] = models.group_prior_pit(t, ["_all"], "date", "pts", fallback=float(t.loc[burn, "pts"].mean()))
    dev = t["season"].isin(DEV).to_numpy()
    y = t["pts"].to_numpy(float)
    best = None
    for k in (2, 5, 10, 20):
        a = models.est_A(t, "pts", t["prior_pts"], k).to_numpy()
        e = np.nanmean(np.abs(a[dev] - y[dev]))
        best = min(best, (e, k)) if best else (e, k)
    t["A"] = models.est_A(t, "pts", t["prior_pts"], best[1])
    kA = best[1]
    best = None
    for k in (2, 5, 10, 20):
        b = models.est_B(t, "pts", t["prior_pts"], k, 10).to_numpy()
        e = np.nanmean(np.abs(b[dev] - y[dev]))
        best = min(best, (e, k)) if best else (e, k)
    t["B"] = models.est_B(t, "pts", t["prior_pts"], best[1], 10)
    t["C"] = t["exp_pts"].fillna(t["B"])
    X = t[["b2b", "opp_b2b", "rest_days", "opp_rest_days", "three_in_four"]].fillna(0.0)
    lr = LinearRegression().fit(X[dev], (y - t["C"].to_numpy())[dev])
    t["D"] = t["C"] + lr.predict(X)
    prm = {"A_k": kA, "B_k": best[1], "D_coef": dict(zip(X.columns, np.round(lr.coef_, 3).tolist())),
           "D_intercept": round(float(lr.intercept_), 3)}
    return t, prm
