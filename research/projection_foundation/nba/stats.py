"""Stat-family ladder (conditional on playing -- the frame Kalshi player props settle in).

A  season-to-date per-game mean (blended with last season), EB-shrunk to the position prior
B  EWMA per-game mean, EB-shrunk
C  pregame minutes forecast x per-minute rate (EWMA sums, EB-shrunk in *minutes* units to the position rate)
D  C x opponent factor^beta_opp x pace factor^beta_pace. The opponent factor is the defence's PIT
   "allowed vs expected" ratio for the player's position group (sum actual / sum C-expectation over the
   defence's earlier games, EWMA-weighted, shrunk toward 1). Because the expectation is player-specific, a
   defence that faced weak scorers is not credited for low raw totals (the schedule adjustment).
E  LightGBM (Poisson objective, walk-forward by season) on pregame features incl. C, factors and context
E_inj  E + teammate-absence features (retrospective proxy for injury reports)
F  non-negative stack of A..E fitted on development predictions only
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from pf_core import models
from .common import DEV, lgb_walkforward

K_GRID = (2, 5, 10, 20)
LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=200)


def opponent_factor(p: pd.DataFrame, stat: str, pred_col: str, halflife: float = 20.0) -> pd.DataFrame:
    """PIT ratio for (opponent, position): returns columns r (raw EWMA ratio) and n (games) per row,
    using only the defence's games on strictly earlier dates."""
    obs = p[stat].notna()
    q = p.assign(_a=p[stat].where(obs), _e=p[pred_col].where(obs))
    g = (q.groupby(["opp", "pos", "date"], sort=True)
         .agg(a=("_a", "sum"), e=("_e", "sum"), k=("_a", "count")).reset_index())
    g.loc[g["k"] == 0, ["a", "e"]] = np.nan          # dates with no observed player-games (e.g. the slate)
    g = g.sort_values(["opp", "pos", "date"])
    grp = g.groupby(["opp", "pos"], sort=False)
    ea = grp["a"].transform(lambda s: s.ewm(halflife=halflife, ignore_na=True).mean().shift(1))
    ee = grp["e"].transform(lambda s: s.ewm(halflife=halflife, ignore_na=True).mean().shift(1))
    g["opp_r"] = ea / ee
    seen = (g["k"] > 0).astype(float)
    g["opp_n"] = np.minimum(seen.groupby([g["opp"], g["pos"]]).cumsum() - seen, 2.9 * halflife)
    out = p[["opp", "pos", "date"]].merge(g[["opp", "pos", "date", "opp_r", "opp_n"]], on=["opp", "pos", "date"], how="left")
    out.index = p.index
    return out[["opp_r", "opp_n"]]


def shrink_factor(r, n, k) -> np.ndarray:
    r = np.nan_to_num(np.asarray(r, float), nan=1.0)
    n = np.nan_to_num(np.asarray(n, float))
    return (n * r + k) / (n + k)


def fit_family(p: pd.DataFrame, stat: str, min_col: str, inj_feats: list[str], frozen: dict | None = None,
               final_only: bool = False) -> tuple[pd.DataFrame, dict]:
    """p: played rows with features and a pregame minutes forecast `min_col`. Returns columns A..F, E_inj and the
    components (rate, opp_factor, pace_adj). Tuned values go to `prm` and can be passed back as `frozen`."""
    y = p[stat].to_numpy(float)
    dev = p["season"].isin(DEV).to_numpy() & np.isfinite(y)
    col = f"{stat}_p"
    prior = p[f"prior_{stat}"]
    prm: dict = dict(frozen or {})
    out = pd.DataFrame(index=p.index)

    def pick(fn, grid):
        best = None
        for g in grid:
            v = fn(*g).to_numpy() if isinstance(g, tuple) else fn(g).to_numpy()
            mae = np.mean(np.abs(v[dev] - y[dev]))
            if best is None or mae < best[0]:
                best = (mae, g)
        return best[1]

    if "A_k" not in prm:
        prm["A_k"] = pick(lambda k: models.est_A(p, col, prior, k), K_GRID)
    out["A"] = models.est_A(p, col, prior, prm["A_k"])
    if "B_halflife" not in prm:
        prm["B_halflife"], prm["B_k"] = pick(lambda h, k: models.est_B(p, col, prior, k, h),
                                             [(h, k) for h in (3, 8, 20) for k in K_GRID])
    out["B"] = models.est_B(p, col, prior, prm["B_k"], prm["B_halflife"])
    prior_rate = p[f"prior_rate_{stat}"]
    mins = p[min_col].to_numpy(float)
    if "C_rate_halflife" not in prm:
        prm["C_rate_halflife"], prm["C_k_minutes"] = pick(
            lambda h, k: models.ratio_rate(p, col, "minutes_p", h, prior_rate, k) * mins,
            [(h, k) for h in (8, 20) for k in (30, 100, 300)])
    rate = models.ratio_rate(p, col, "minutes_p", prm["C_rate_halflife"], prior_rate, prm["C_k_minutes"])
    out["rate"] = rate
    out["C"] = rate * mins
    tmp = p.assign(_C=out["C"].to_numpy())
    of = opponent_factor(tmp, stat, "_C")
    if "D_opp_k_games" not in prm:
        best = None
        for k in (5, 10, 20, 40):
            fac = shrink_factor(of["opp_r"], of["opp_n"], k)
            b = models.fit_opponent_beta(y[dev], out["C"].to_numpy()[dev], np.log(fac[dev]))
            mu = out["C"].to_numpy() * fac ** b
            mae = np.mean(np.abs(mu[dev] - y[dev]))
            if best is None or mae < best[0]:
                best = (mae, k, b)
        prm["D_opp_k_games"], prm["D_beta_opp"] = best[1], float(best[2])
    fac = shrink_factor(of["opp_r"], of["opp_n"], prm["D_opp_k_games"])
    pace = p["pace_factor"].fillna(1.0).to_numpy()
    if "D_beta_pace" not in prm:
        prm["D_beta_pace"] = float(models.fit_opponent_beta(
            y[dev], (out["C"].to_numpy() * fac ** prm["D_beta_opp"])[dev], np.log(pace[dev])))
    out["opp_factor"] = fac ** prm["D_beta_opp"]
    out["opp_factor_raw"] = fac
    out["opp_n"] = of["opp_n"].fillna(0).to_numpy()
    out["pace_adj"] = pace ** prm["D_beta_pace"]
    out["D"] = out["C"] * out["opp_factor"] * out["pace_adj"]
    feats = [f"{col}_ewm3", f"{col}_ewm8", f"{col}_ewm20", f"{col}_std", f"{col}_prev", f"{col}_n",
             "minutes_p_ewm8", "start_p_ewm8", "usage_p_ewm8", "fga_p_ewm8", "fg3a_p_ewm8", "fta_p_ewm8",
             "b2b", "rest_days", "exp_pace", "exp_pts", "exp_margin", "exp_abs_margin", "home_f", "pos_c", "pos_g",
             "days_since_played", "missed_streak", "games_with_team_c"]
    e = p[feats].copy()
    e["min_hat"] = mins
    e["rate_hat"] = rate.to_numpy()
    e["C_hat"] = out["C"].to_numpy()
    e["opp_factor"] = out["opp_factor_raw"].to_numpy()
    e["opp_n"] = out["opp_n"].to_numpy()
    e["pace_factor"] = pace
    ef = list(e.columns)
    for c_ in inj_feats:
        e[c_] = p[c_].to_numpy()
    e[stat] = y
    e["season"] = p["season"].to_numpy()
    out["E"] = lgb_walkforward(e, ef, stat, objective="poisson", params=LGB, final_only=final_only)
    out["E_inj"] = lgb_walkforward(e, ef + inj_feats, stat, objective="poisson", params=LGB, final_only=final_only)
    if "F_weights" not in prm:
        m = dev & out["E"].notna().to_numpy()
        w = models.fit_stack_weights(y[m], out.loc[m, ["A", "B", "C", "D", "E"]].to_numpy())
        prm["F_weights"] = dict(zip("ABCDE", w.tolist()))
    w = np.array([prm["F_weights"][k] for k in "ABCDE"])
    out["F"] = out[["A", "B", "C", "D", "E"]].to_numpy() @ w
    prm["E_features"] = ef
    return out, prm
