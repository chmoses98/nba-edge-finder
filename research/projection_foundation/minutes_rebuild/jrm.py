"""Joint rotation model (JRM): depth-aware, team-conserving NBA minutes.

Root cause it addresses (see PHASE1_ROOT_CAUSE.md): the frozen ladder forecasts every player's participation and conditional minutes
from his OWN history. Minutes are a share of a fixed 240 + OT, so a player's minutes depend on WHO ELSE is available (depth chart),
and the independent marginals do not add up once the roster is healthy or deeper than the history they were learnt on.

Structure (all heads LightGBM, season walk-forward, window 5, like the frozen engine):
  q_i      P(eligible) = P(on the active list and not injury-out); target = in_box and not an injury DNP.
  pi_i(E)  P(plays | eligible, E)           E = the set of eligible teammates (incl. i)
  mu_i(E)  E[minutes | plays, E]            features: own role features + SET features (rank of the player's level in E, sum of the
                                            levels above him, sum over E, |E|, share of the set's capacity, depth counts).
  Conservation: for every scenario E, sum_{i in E} pi_i mu_i is projected on T = 241.5 with a variance-weighted residual allocation
  (the BLUE under a sum constraint: low-variance players -- established starters -- absorb little, volatile fringe players absorb most).
  Scenarios E^s ~ Bernoulli(q) (active list capped at 15 by level). Outputs: p_i = E_s[e_i pi_i], u_i = E_s[e_i pi_i mu_i*],
  E[min | play] = u_i / p_i, and the scenario mixture gives the distribution.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import lightgbm as lgb

from nba import minutes as M
from nba.common import lgb_walkforward

import os as _os2
LEVEL = _os2.environ.get("JRM_LEVEL", "E")        # v1 used the linear role blend D (commit 6af0202); v2 uses the LightGBM marginal E, falling back to D where E does not exist (pre-2017)
T_BUDGET = 241.5
ACTIVE_CAP = 15
import json as _json, os as _os
_LS = _json.load(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "jrm_list_size.json")))
LIST_SIZES = np.array([int(k) for k in _LS]); LIST_P = np.array([_LS[k] for k in _LS]); LIST_P = LIST_P / LIST_P.sum()
OWN = M.ROLE + M.CONTEXT + M.LGB_EXTRA
SETF = ["rank_e", "s_above", "s_e", "n_e", "share_e", "s_top5", "s_top8", "cnt20", "cnt10", "s_above_rel", "lvl_gap_next", "l_set"]
LGB = dict(objective="regression", learning_rate=0.05, n_estimators=300, num_leaves=31, min_child_samples=200, subsample=0.8,
           subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0, verbose=-1, n_jobs=4)


def eligible_flag(f: pd.DataFrame) -> pd.Series:
    reason = f["dnp_reason"].fillna("").str.upper()
    out = (~f["in_box"]) | (f["dnp"] & ~reason.str.contains("COACH") & (reason != ""))
    return ~out


def prepare(f: pd.DataFrame, mp: pd.DataFrame) -> pd.DataFrame:
    """f: pipeline.with_targets(features) frame; mp: minutes ladder predictions (D = role blend, used as the level)."""
    f = M.prep(f)
    f = f.join(mp[["A", "B", "D", "E", "E_inj", "F", "p_play"]])
    f["elig"] = eligible_flag(f)
    f["lvl"] = (f["E"].fillna(f["D"]) if LEVEL == "E" else f["D"]).clip(2.0, 40.0)
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
    # level of the next eligible player below (gap)
    nxt = np.zeros_like(lm)
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
    for (gid, team), g in e.groupby(["game_id", "team"], sort=False):
        g = g.sort_values("lvl", ascending=False, kind="stable")
        l = g["lvl"].to_numpy()
        feats = set_features(l, np.ones((1, len(l)), bool))
        d = pd.DataFrame({k: v[0] for k, v in feats.items()}, index=g.index)
        parts.append(d)
    return pd.concat(parts)


def fit_heads(train: pd.DataFrame, seed: int = 0):
    X = OWN + ["lvl"] + SETF
    pi = lgb.LGBMClassifier(**{**LGB, "objective": "binary", "random_state": seed}).fit(train[X], train["y_play"])
    pl = train[train["played"]]
    mu = lgb.LGBMRegressor(**{**LGB, "random_state": seed}).fit(pl[X], pl["minutes"])
    return pi, mu, X


def allocate(u: np.ndarray, w: np.ndarray, total: float = T_BUDGET) -> np.ndarray:
    """Variance-weighted residual allocation of (total - sum u) over the eligible players of one scenario; keep u >= 0."""
    d = total - u.sum(axis=-1, keepdims=True)
    adj = u + d * w / np.maximum(w.sum(axis=-1, keepdims=True), 1e-9)
    return np.clip(adj, 0.0, 48.0)


def weights(pi: np.ndarray, mu: np.ndarray, kind: str) -> np.ndarray:
    """Allocation weights = variance of the unconditional minutes pi*min:  pi*(c mu)^2 + pi(1-pi) mu^2  (c = 0.27, the dev CV of minutes)."""
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


def predict_season(fs: pd.DataFrame, q: np.ndarray, heads, S: int = 24, seed: int = 0, alloc: str = "var",
                   chunk_groups: int = 800) -> pd.DataFrame:
    """Scenario inference for the pool rows `fs` of one season. Returns p, u, m (=E[min|play]) per row plus diagnostics."""
    pi_m, mu_m, X = heads
    rng = np.random.default_rng(seed)
    own = fs[OWN + ["lvl"]].to_numpy(np.float32)
    gkeys = fs.groupby(["game_id", "team"], sort=False).indices
    keys = list(gkeys.keys())
    n = len(fs)
    sum_p = np.zeros(n)
    sum_u = np.zeros(n)
    sum_u_raw = np.zeros(n)
    team_raw_ratio = []          # per group: mean over scenarios of sum(pi*mu)/T before allocation
    for c0 in range(0, len(keys), chunk_groups):
        pos_l, sc_l, g_l, set_l = [], [], [], []
        for gi, k in enumerate(keys[c0:c0 + chunk_groups], start=c0):
            idx = gkeys[k]
            order = idx[np.argsort(-fs["lvl"].to_numpy()[idx], kind="stable")]
            l = fs["lvl"].to_numpy()[order]
            qq = q[order]
            # stratified (Latin-hypercube) uniforms per player: each player's inclusion rate is exact to +-1/S instead of binomial noise
            ranks = np.argsort(rng.random((S, len(order))), axis=0)
            mask = ((ranks + rng.random((S, len(order)))) / S) < qq[None, :]
            cs = np.cumsum(mask, axis=1)
            cap = rng.choice(LIST_SIZES, size=S, p=LIST_P)   # active-list size of a fully healthy team (empirical: 13 / 14 / 15, rarely 12)
            mask &= cs <= cap[:, None]                       # keep the highest levels
            sf = set_features(l, mask)
            s_idx, j_idx = np.nonzero(mask)
            pos_l.append(order[j_idx]); sc_l.append(s_idx + gi * S)
            g_l.append(np.full(len(j_idx), gi)); set_l.append(np.column_stack([sf[c][s_idx, j_idx] for c in SETF]))
        if not pos_l:
            continue
        pos = np.concatenate(pos_l); sc = np.concatenate(sc_l); Xs = np.vstack(set_l)
        Xm = np.hstack([own[pos], Xs]).astype(np.float64)
        cols = OWN + ["lvl"] + SETF
        Xdf = pd.DataFrame(Xm, columns=cols)[X]
        pi = pi_m.predict_proba(Xdf)[:, 1]
        mu = np.clip(mu_m.predict(Xdf), 0.5, 46.0)
        u = pi * mu
        w = weights(pi, mu, alloc)
        # per-scenario sums
        uniq, inv = np.unique(sc, return_inverse=True)
        tot = np.bincount(inv, weights=u); wsum = np.bincount(inv, weights=w)
        ua = u if alloc == "none" else waterfill(u, w, inv, len(uniq))
        np.add.at(sum_p, pos, pi / S)
        np.add.at(sum_u, pos, ua / S)
        np.add.at(sum_u_raw, pos, u / S)
        team_raw_ratio.append(pd.Series(tot / T_BUDGET, index=uniq).groupby(uniq // S).mean())
    out = pd.DataFrame({"p_jrm": sum_p, "u_jrm": sum_u, "u_raw_jrm": sum_u_raw}, index=fs.index)
    # a player never sampled as eligible (p ~ 0) has no scenario evidence on his minutes: fall back to his role level
    out["m_jrm"] = np.where(sum_p > 1e-6, sum_u / np.maximum(sum_p, 1e-6), fs["lvl"].to_numpy())
    out["m_raw_jrm"] = np.where(sum_p > 1e-6, sum_u_raw / np.maximum(sum_p, 1e-6), fs["lvl"].to_numpy())
    return out
