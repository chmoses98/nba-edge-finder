"""Shared constants: chronological splits, families, Kalshi-like threshold rungs."""
from __future__ import annotations

# hoopR season = calendar year in which the season ends (2023 == 2022-23)
BURN_IN = [2015]                                   # history only, never scored
DEV = [2016, 2017, 2018, 2019, 2020, 2021, 2022]   # 2015-16 .. 2021-22: iterate freely
VAL = [2023, 2024]                                 # 2022-23, 2023-24: select models
HOLDOUT = [2025, 2026]                             # 2024-25, 2025-26: frozen candidates, run once


def split_of(season: int) -> str:
    if season in DEV:
        return "development"
    if season in VAL:
        return "validation"
    if season in HOLDOUT:
        return "holdout"
    return "burn_in"


SPLITS_TEXT = {
    "development": "2015-16..2021-22 regular seasons (2014-15 used only as burn-in history)",
    "validation": "2022-23 and 2023-24 regular seasons (model selection)",
    "holdout": "2024-25 and 2025-26 regular seasons (evaluated once for frozen candidates; 2025-26 also has "
               "archived point-in-time injury reports)",
}

# family -> (box column, gate family key, Kalshi-like rungs P(X >= k))
FAMILIES = {
    "points": ("pts", "points", [10, 15, 20, 25, 30]),
    "rebounds": ("reb", "rebounds", [4, 6, 8, 10]),
    "assists": ("ast", "assists", [2, 4, 6, 8]),
    "threes": ("fg3m", "threes", [1, 2, 3, 4]),
    "pra": ("pra", "pra", [15, 20, 25, 30, 35, 40]),
    "fga": ("fga", "fga", [5, 10, 15, 20]),
}
MINUTES_RUNGS = [10, 20, 25, 30, 35]
SUPPORT_K = {"pts": 75, "reb": 32, "ast": 26, "fg3m": 15, "pra": 110, "fga": 45, "minutes": 61}


def lgb_walkforward(df, features, target, objective="regression", params=None, window=5, first_pred=2017,
                    final_only=False):
    """Season-block walk-forward LightGBM: for each season s >= first_pred, train on seasons
    [s-window, s-1] (rows with a non-missing target) and predict season s. `final_only` predicts only the last
    season present (used by the forward projector). Returns a Series aligned to df.index (NaN elsewhere).
    pf_core.models.lgbm_walkforward trains on *all* earlier blocks; the window bounds compute on a shared box
    and lets the model follow league drift (pace/3PA inflation)."""
    import lightgbm as lgb
    import numpy as np
    import pandas as pd
    p = dict(objective=objective, learning_rate=0.05, n_estimators=300, num_leaves=31, min_child_samples=200,
             subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0, verbose=-1, n_jobs=2)
    p.update(params or {})
    pred = pd.Series(np.nan, index=df.index)
    seasons = sorted(df["season"].unique())
    targets = [seasons[-1]] if final_only else [s for s in seasons if s >= first_pred]
    for s in targets:
        tr = df[(df["season"] < s) & (df["season"] >= s - window) & df[target].notna()]
        if len(tr) < 1000:
            continue
        m = lgb.LGBMRegressor(**p) if objective != "binary" else lgb.LGBMClassifier(**p)
        m.fit(tr[features], tr[target])
        te = df["season"] == s
        if objective == "binary":
            pred.loc[te] = m.predict_proba(df.loc[te, features])[:, 1]
        else:
            pred.loc[te] = m.predict(df.loc[te, features])
    return pred
