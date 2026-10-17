"""Minutes (opportunity) ladder, conditional on playing, plus a participation hurdle.

A  season-to-date minutes (blended with last season), EB-shrunk to the position prior
B  EWMA minutes (halflife chosen on development), EB-shrunk
C  role blend: OLS on development of EWMAs / season means / starter rates / last game (frozen)
D  C + context: rest / back-to-back, blowout risk (|expected margin| x starter rate), return from absence,
   team change (frozen OLS on development)
E  LightGBM (season walk-forward, 5-season training window) on all pregame features
E_inj  E + teammate-absence features (retrospective proxy for the injury report; see features.py)
F  non-negative stack of B, D, E fitted on development predictions only

Hurdle: P(play | candidate) with a LightGBM classifier (walk-forward) vs the EWMA participation rate.
All tuned quantities are returned in `params` and can be passed back as `frozen` (forward projector).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from pf_core import models
from .common import DEV, lgb_walkforward

ROLE = ["minutes_p_ewm3", "minutes_p_ewm8", "minutes_p_ewm20", "minutes_p_std", "minutes_p_prev",
        "start_p_ewm3", "start_p_ewm8", "start_p_std", "last_min", "last_start", "min_all_ewm10", "play01_ewm10"]
CONTEXT = ["b2b", "rest_days", "three_in_four", "opp_b2b", "exp_abs_margin", "blow_x_start", "days_since_played",
           "missed_streak", "team_changed", "games_with_team_c", "home_f"]
LGB_EXTRA = ["minutes_p_n", "minutes_p_std_n", "games_in_season", "exp_pace", "exp_margin", "age_games",
             "pts_p_ewm8", "usage_p_ewm8", "pos_c", "pos_g", "inbox01_ewm3", "play01_ewm3"]
INJ = ["out_min", "out_new_min", "out_pos_min", "out_usage"]
HURDLE = ["play01_ewm3", "play01_ewm10", "play01_std", "inbox01_ewm3", "inbox01_ewm10", "days_since_played",
          "missed_streak", "minutes_p_ewm8", "minutes_p_ewm3", "start_p_ewm8", "last_min", "b2b", "rest_days",
          "games_with_team_c", "team_changed", "exp_abs_margin", "games_in_season", "minutes_p_n", "age_games"]
LGB_PARAMS = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=200)
MODELS = ["A", "B", "C", "D", "E", "F"]


def prep(f: pd.DataFrame) -> pd.DataFrame:
    f = f.copy()
    f["blow_x_start"] = f["exp_abs_margin"] * f["start_p_ewm8"].fillna(0)
    f["games_with_team_c"] = f["games_with_team"].clip(upper=30)
    f["home_f"] = f["home"].astype(float)
    f["pos_c"] = (f["pos"] == "C").astype(float)
    f["pos_g"] = (f["pos"] == "G").astype(float)
    f["started_f"] = f["started"].astype(float)
    return f


def _fill(X: pd.DataFrame, prior: pd.Series) -> pd.DataFrame:
    X = X.copy()
    for c in X.columns:
        if c.startswith("minutes_p") or c in ("last_min", "min_all_ewm10"):
            X[c] = X[c].fillna(prior)
        else:
            X[c] = X[c].fillna(0.0)
    return X


def fit_ladder(p: pd.DataFrame, frozen: dict | None = None, final_only: bool = False,
               with_oracle: bool = True) -> tuple[pd.DataFrame, dict]:
    """p = played rows (plus, for projection, target-less rows of the season to predict)."""
    out = pd.DataFrame(index=p.index)
    dev = p["season"].isin(DEV).to_numpy() & p["minutes"].notna().to_numpy()
    y = p["minutes"].to_numpy(float)
    prior = p["prior_minutes"]
    prm: dict = dict(frozen or {})
    if "A_k" not in prm:
        prm["A_k"] = min((np.mean(np.abs(models.est_A(p, "minutes_p", prior, k).to_numpy()[dev] - y[dev])), k)
                         for k in (1, 2, 4, 8))[1]
    out["A"] = models.est_A(p, "minutes_p", prior, prm["A_k"])
    if "B_halflife" not in prm:
        _, prm["B_halflife"], prm["B_k"] = min(
            (np.mean(np.abs(models.est_B(p, "minutes_p", prior, k, h).to_numpy()[dev] - y[dev])), h, k)
            for h in (3, 8) for k in (1, 2, 4, 8))
    out["B"] = models.est_B(p, "minutes_p", prior, prm["B_k"], prm["B_halflife"])
    from sklearn.linear_model import LinearRegression
    for name, cols in (("C", ROLE), ("D", ROLE + CONTEXT)):
        X = _fill(p[cols], prior)
        if f"{name}_coef" not in prm:
            lr = LinearRegression().fit(X[dev], y[dev])
            prm[f"{name}_coef"] = dict(zip(cols, lr.coef_.tolist()))
            prm[f"{name}_intercept"] = float(lr.intercept_)
        coef = np.array([prm[f"{name}_coef"][c] for c in cols])
        out[name] = np.clip(X.to_numpy() @ coef + prm[f"{name}_intercept"], 1.0, 48.0)
    feats = ROLE + CONTEXT + LGB_EXTRA
    e = p[feats + INJ + ["started_f", "season", "minutes"]]
    out["E"] = np.clip(lgb_walkforward(e, feats, "minutes", params=LGB_PARAMS, final_only=final_only), 0.5, 48.0)
    out["E_inj"] = np.clip(lgb_walkforward(e, feats + INJ, "minutes", params=LGB_PARAMS, final_only=final_only), 0.5, 48.0)
    if with_oracle:
        out["oracle_start"] = np.clip(lgb_walkforward(e, feats + INJ + ["started_f"], "minutes", params=LGB_PARAMS,
                                                      final_only=final_only), 0.5, 48.0)
    if "F_weights" not in prm:
        m = dev & np.isfinite(out[["B", "D", "E"]].to_numpy()).all(axis=1)
        w = models.fit_stack_weights(y[m], out.loc[m, ["B", "D", "E"]].to_numpy())
        prm["F_weights"] = dict(zip(["B", "D", "E"], w.tolist()))
    w = np.array([prm["F_weights"][k] for k in ("B", "D", "E")])
    out["F"] = out[["B", "D", "E"]].to_numpy() @ w
    prm["features_E"] = feats
    return out, prm


def fit_hurdle(c: pd.DataFrame, final_only: bool = False) -> pd.Series:
    """P(play | in candidate pool), LightGBM classifier, season walk-forward."""
    d = c[HURDLE + ["season"]].copy()
    d["y_play"] = np.where(c["played"].notna(), c["played"].astype(float), np.nan) if "is_slate" not in c else \
        np.where(c["is_slate"], np.nan, c["played"].astype(float))
    pr = lgb_walkforward(d, HURDLE, "y_play", objective="binary", params=dict(n_estimators=250),
                         final_only=final_only)
    return pr.clip(0.005, 0.995)


def team_budget_normalise(df: pd.DataFrame, mean_col: str, p_col: str, budget: float = 241.5) -> pd.Series:
    """Scale each team-game's conditional minutes so that sum(p_play * E[min|play]) == budget (240 + OT)."""
    exp_total = (df[p_col] * df[mean_col]).groupby([df["game_id"], df["team"]]).transform("sum")
    scale = (budget / exp_total).clip(0.8, 1.25)
    return np.clip(df[mean_col] * scale, 0.5, 48.0)
