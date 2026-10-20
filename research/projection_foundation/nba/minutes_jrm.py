"""Joint rotation model (JRM): depth-aware, team-conserving NBA minutes and participation (research only, authority: none).

Why it exists (research/projection_foundation/minutes_rebuild/PHASE1_ROOT_CAUSE.md): the frozen ladder forecasts every player's participation and
conditional minutes from his OWN history and then adds them up. Minutes are a share of a fixed 240 + OT, so a player's minutes depend on WHO ELSE
is available (the depth chart). Independent marginals, learnt on mixed teammate-health states and on a candidate pool of players who were in the
box score, over-count the rotation fringe on a healthy, deeper, rebuilt roster; a uniform scale then cuts established starters to compensate.

Structure (LightGBM heads, season walk-forward with a five-season window, like the frozen engine; nothing tuned on 2024-25 / 2025-26):
  level_i   the player's role level = the frozen marginal forecast E[min | play] (falls back to the linear role blend D where E does not exist)
  q_i       P(eligible) = P(on the active list and not injury-out); target = in the box score and not an injury DNP. Report-calibrated with the
            official designation (OUT / DOUBTFUL are near-deterministic and use their empirical rates).
  pi_i(E)   P(plays | eligible, E)         E = the set of eligible teammates (incl. i)
  mu_i(E)   E[minutes | plays, E]          own role features + SET features: rank of the level inside E, sum of the levels above, sum over E, |E|,
                                           share of the set's capacity, depth counts.
  Scenarios E^s are drawn from q with stratified (Latin-hypercube) uniforms; the active list is capped at its empirical size for a healthy team
  (13 / 14 / 15), keeping the highest levels. In every scenario sum_{i in E} pi_i mu_i is projected onto T = 241.5 (240 + expected overtime) with an
  equal-minutes residual allocation under the bounds [0, 48] (water-filling); selected on development / validation (starter error equals or beats the
  frozen engine, variance-weighted and proportional rules shave starters more).
  Outputs: p_i = E_s[e_i pi_i], u_i = E_s[e_i pi_i mu_i*] (sum over a team = 241.5 exactly), E[min | play] = u_i / p_i.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from . import minutes as M
from .common import lgb_walkforward

ASSETS = Path(__file__).resolve().parents[1] / "results" / "jrm"   # frozen calibrations (development / 2025-26 PIT reports only)
LEVEL = os.environ.get("JRM_LEVEL", "E")      # "D" reproduces v1 (commit 6af0202); v2 uses the LightGBM marginal E (falls back to D before 2017)
VERSION = "jrm-0.1"
T_BUDGET = 241.5
_LS = json.load(open(ASSETS / "list_size.json"))
LIST_SIZES = np.array([int(k) for k in _LS])
LIST_P = np.array([_LS[k] for k in _LS])
LIST_P = LIST_P / LIST_P.sum()
OWN = M.ROLE + M.CONTEXT + M.LGB_EXTRA
SETF = ["rank_e", "s_above", "s_e", "n_e", "share_e", "s_top5", "s_top8", "cnt20", "cnt10", "s_above_rel", "lvl_gap_next", "l_set"]
LGB = dict(objective="regression", learning_rate=0.05, n_estimators=300, num_leaves=31, min_child_samples=200, subsample=0.8,
           subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0, verbose=-1, n_jobs=4)
CALIB_CLASSES = ("QUESTIONABLE", "PROBABLE", "AVAILABLE")


def eligible_flag(f: pd.DataFrame) -> pd.Series:
    """On the active list and not injury-out: in the box score and not a DNP with a non-coach's-decision reason."""
    reason = f["dnp_reason"].fillna("").str.upper()
    out = (~f["in_box"]) | (f["dnp"] & ~reason.str.contains("COACH") & (reason != ""))
    return ~out


def role_level(f: pd.DataFrame) -> pd.Series:
    return (f["E"].fillna(f["D"]) if LEVEL == "E" else f["D"]).clip(2.0, 40.0)


def prepare(f: pd.DataFrame, mp: pd.DataFrame) -> pd.DataFrame:
    """f: pipeline.with_targets(features) frame; mp: minutes ladder predictions (A, B, D, E, E_inj, F, p_play)."""
    f = M.prep(f)
    f = f.join(mp[["A", "B", "D", "E", "E_inj", "F", "p_play"]])
    f["elig"] = eligible_flag(f)
    f["lvl"] = role_level(f)
    f["y_play"] = f["played"].astype(float)
    return f


def set_features(l: np.ndarray, mask: np.ndarray) -> dict[str, np.ndarray]:
    """l: (n,) levels sorted DESC; mask: (S, n) bool eligible. Returns feature arrays of shape (S, n) (valid where mask)."""
    lm = np.where(mask, l[None, :], 0.0)
    cm = np.cumsum(lm, axis=1)
    cnt = np.cumsum(mask, axis=1)
    s_e = cm[:, -1:]
    n_e = cnt[:, -1:]
    s_above = cm - lm
    top5 = np.where(cnt <= 5, lm, 0.0).sum(axis=1, keepdims=True)
    top8 = np.where(cnt <= 8, lm, 0.0).sum(axis=1, keepdims=True)
    cnt20 = (mask & (l[None, :] >= 20)).sum(axis=1, keepdims=True)
    cnt10 = (mask & (l[None, :] >= 10)).sum(axis=1, keepdims=True)
    nxt = np.zeros_like(lm)                              # level of the next eligible player below (gap)
    nxt[:, :-1] = np.where(mask[:, 1:], l[None, 1:], 0.0)
    shape = mask.shape
    return {"rank_e": cnt.astype(float), "s_above": s_above, "s_e": np.broadcast_to(s_e, shape), "n_e": np.broadcast_to(n_e, shape).astype(float),
            "share_e": lm / np.maximum(s_e, 1e-6), "s_top5": np.broadcast_to(top5, shape), "s_top8": np.broadcast_to(top8, shape),
            "cnt20": np.broadcast_to(cnt20, shape).astype(float), "cnt10": np.broadcast_to(cnt10, shape).astype(float),
            "s_above_rel": s_above / np.maximum(s_e, 1e-6), "lvl_gap_next": l[None, :] - nxt, "l_set": np.broadcast_to(l[None, :], shape)}


def build_training(f: pd.DataFrame) -> pd.DataFrame:
    """Eligible rows with SET features computed from the realised eligible set (one scenario)."""
    parts = []
    e = f[f["elig"] == 1]
    for _, g in e.groupby(["game_id", "team"], sort=False):
        g = g.sort_values("lvl", ascending=False, kind="stable")
        feats = set_features(g["lvl"].to_numpy(), np.ones((1, len(g)), bool))
        parts.append(pd.DataFrame({k: v[0] for k, v in feats.items()}, index=g.index))
    return pd.concat(parts)


def fit_heads(train: pd.DataFrame, seed: int = 0):
    X = OWN + ["lvl"] + SETF
    pi = lgb.LGBMClassifier(**{**LGB, "objective": "binary", "random_state": seed}).fit(train[X], train["y_play"])
    pl = train[train["played"]]
    mu = lgb.LGBMRegressor(**{**LGB, "random_state": seed}).fit(pl[X], pl["minutes"])
    return pi, mu, X


def weights(pi: np.ndarray, mu: np.ndarray, kind: str) -> np.ndarray:
    """Residual-allocation weights. 'uniform' (default): equal minutes per eligible player; 'prop': proportional to pi*mu; 'var': variance of pi*min."""
    if kind == "uniform":
        return np.ones_like(mu)
    if kind == "prop":
        return pi * mu + 1e-6
    return pi * (0.27 * mu) ** 2 + pi * (1 - pi) * mu ** 2 + 1e-6


def waterfill(u: np.ndarray, w: np.ndarray, inv: np.ndarray, n_sc: int, total: float = T_BUDGET, passes: int = 8) -> np.ndarray:
    """Residual allocation per scenario with bounds [0, 48]: players that hit a bound are frozen and the remaining residual goes to the rest."""
    ua = u.copy()
    free = np.ones_like(u, dtype=bool)
    for _ in range(passes):
        tot = np.bincount(inv, weights=ua, minlength=n_sc)
        d = total - tot
        if np.all(np.abs(d) < 1e-6):
            break
        we = np.where(free, w, 0.0)
        ws = np.bincount(inv, weights=we, minlength=n_sc)
        ok = ws > 0
        step = np.where(ok[inv], d[inv] * we / np.maximum(ws[inv], 1e-12), 0.0)
        ua = np.clip(ua + step, 0.0, 48.0)
        free = free & (ua > 0.0) & (ua < 48.0)
    return ua


def predict_season(fs: pd.DataFrame, q: np.ndarray, heads, S: int = 24, seed: int = 0, alloc: str = "uniform", chunk_groups: int = 800) -> pd.DataFrame:
    """Scenario inference for the pool rows `fs` (whole team-games). Returns p_jrm, u_jrm (conserved), u_raw_jrm, m_jrm (= E[min | play]), m_raw_jrm."""
    pi_m, mu_m, X = heads
    rng = np.random.default_rng(seed)
    own = fs[OWN + ["lvl"]].to_numpy(np.float32)
    lvl = fs["lvl"].to_numpy()
    gkeys = fs.groupby(["game_id", "team"], sort=False).indices
    keys = list(gkeys.keys())
    n = len(fs)
    sum_p, sum_u, sum_u_raw = np.zeros(n), np.zeros(n), np.zeros(n)
    for c0 in range(0, len(keys), chunk_groups):
        pos_l, sc_l, set_l = [], [], []
        for gi, k in enumerate(keys[c0:c0 + chunk_groups], start=c0):
            idx = gkeys[k]
            order = idx[np.argsort(-lvl[idx], kind="stable")]
            l = lvl[order]
            qq = q[order]
            # stratified (Latin-hypercube) uniforms per player: each player's inclusion rate is exact to +-1/S instead of binomial noise
            ranks = np.argsort(rng.random((S, len(order))), axis=0)
            mask = ((ranks + rng.random((S, len(order)))) / S) < qq[None, :]
            cs = np.cumsum(mask, axis=1)
            cap = rng.choice(LIST_SIZES, size=S, p=LIST_P)   # active-list size of a fully healthy team (empirical: 13 / 14 / 15, rarely 12)
            mask &= cs <= cap[:, None]                       # keep the highest levels
            sf = set_features(l, mask)
            s_idx, j_idx = np.nonzero(mask)
            pos_l.append(order[j_idx])
            sc_l.append(s_idx + gi * S)
            set_l.append(np.column_stack([sf[c][s_idx, j_idx] for c in SETF]))
        if not pos_l:
            continue
        pos, sc, Xs = np.concatenate(pos_l), np.concatenate(sc_l), np.vstack(set_l)
        Xdf = pd.DataFrame(np.hstack([own[pos], Xs]).astype(np.float64), columns=OWN + ["lvl"] + SETF)[X]
        pi = pi_m.predict_proba(Xdf)[:, 1]
        mu = np.clip(mu_m.predict(Xdf), 0.5, 46.0)
        u = pi * mu
        uniq, inv = np.unique(sc, return_inverse=True)
        ua = u if alloc == "none" else waterfill(u, weights(pi, mu, alloc), inv, len(uniq))
        np.add.at(sum_p, pos, pi / S)
        np.add.at(sum_u, pos, ua / S)
        np.add.at(sum_u_raw, pos, u / S)
    out = pd.DataFrame({"p_jrm": sum_p, "u_jrm": sum_u, "u_raw_jrm": sum_u_raw}, index=fs.index)
    # a player never sampled as eligible (p ~ 0) has no scenario evidence on his minutes: fall back to his role level
    out["m_jrm"] = np.where(sum_p > 1e-6, sum_u / np.maximum(sum_p, 1e-6), lvl)
    out["m_raw_jrm"] = np.where(sum_p > 1e-6, sum_u_raw / np.maximum(sum_p, 1e-6), lvl)
    return out


# ------------------------------------------------------------------------------------------------ live (forward) entry point
def load_q_calibration() -> dict:
    return json.load(open(ASSETS / "q_calibration.json"))


def readiness() -> dict:
    """Readiness of the minutes family under this engine, from the study's original READY rules (results/jrm/readiness.json)."""
    return json.load(open(ASSETS / "readiness.json"))


def minutes_dist_params() -> dict:
    """Empirical conditional-minutes residual distribution around the JRM forecast (fitted on 2017-18..2021-22 walk-forward predictions)."""
    return json.load(open(ASSETS / "minutes_dist.json"))


def calibrate_q(q_head: np.ndarray, classes: list, calib: dict | None = None) -> np.ndarray:
    """Report-aware eligibility. classes: per row, one of OUT / DOUBTFUL / QUESTIONABLE / PROBABLE / AVAILABLE / STARTER_CONFIRMED / None
    (nba.live.participation). None keeps the history-only head."""
    calib = calib or load_q_calibration()
    q = np.clip(np.asarray(q_head, float), 0.005, 0.995)
    z = np.log(q / (1 - q)) * calib["coef"]["logit"] + calib["intercept"]
    for k in CALIB_CLASSES:
        z = z + calib["coef"][k] * np.array([c == k for c in classes], float)
    out = 1.0 / (1.0 + np.exp(-z))
    out[np.array([c is None for c in classes])] = q[np.array([c is None for c in classes])]
    out[np.array([c == "STARTER_CONFIRMED" for c in classes])] = 0.995
    for k, v in calib["fixed"].items():
        out[np.array([c == k for c in classes])] = v
    return out


def slate_minutes(f: pd.DataFrame, classes: list, slate_season: int, S: int = 400, seed: int = 7, window: int = 5) -> pd.DataFrame:
    """JRM participation + conditional minutes for the slate rows of `f` (history + slate, as built by nba.project.project_slate).

    f must carry the frozen ladder columns E and D, the point-in-time features, `is_slate`, `played`, `minutes` (NaN unless played) and the
    box-score status columns. `classes` is aligned with the slate rows in f's order. Returns a frame indexed like the slate rows."""
    f = f.copy()
    slate = f["is_slate"].to_numpy(bool)
    f["elig"] = eligible_flag(f).astype(float).where(~f["is_slate"], np.nan)
    f["lvl"] = role_level(f)
    f["y_play"] = f["played"].astype(float)
    qf = f[M.HURDLE + ["lvl", "season"]].copy()
    qf["y"] = f["elig"]
    q_head = lgb_walkforward(qf, M.HURDLE + ["lvl"], "y", objective="binary", params=dict(n_estimators=250), final_only=True).clip(0.005, 0.995)
    hist = f[~slate & (f["season"] >= slate_season - window) & (f["season"] < slate_season)]
    tr = hist.join(build_training(hist), how="inner")
    heads = fit_heads(tr[tr["elig"] == 1])
    F = f[slate].copy()
    F["q"] = calibrate_q(q_head[slate].to_numpy(), list(classes))
    out = predict_season(F, F["q"].to_numpy(), heads, S=S, seed=seed)
    out["q"] = F["q"]
    out["lvl"] = F["lvl"]
    return out
