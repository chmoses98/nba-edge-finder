"""NBA participation and prop-ladder calibration (RESEARCH_ONLY). Preregistered in
``docs/research/PREREG_NBA_CALIBRATION.md``; this module implements exactly the methods and rules written there.

* :func:`ridge_platt_fit` / :func:`ridge_platt_apply`: ``logit p' = a + b * logit(clip(p))``, penalised toward the
  identity map, ``lambda = 10``. A fitted ``b <= 0.05`` falls back to the identity (ladders stay monotone).
* :func:`build_units`: one participation unit per projected player-game and one prop unit per rung of a player who
  played, from the archived shadow store and the PIT availability overlay (#104).
* :func:`walk_forward`: for each ET game date, fit only on units whose outcome was observed before that date's
  earliest ``as_of``, and apply to that date.
* :func:`evaluate`: the four preregistered variants, metrics, subgroups, the market comparison and the decision rules.
"""

from __future__ import annotations

import math
import os
from collections import defaultdict
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from nba_edge.availability.overlay import AvailabilityIndex, apply_overlay
from nba_edge.research.availability_replay import (
    _read,
    calibration_slope,
    load_availability,
    load_outcomes,
    load_projections,
    load_team_tricodes,
)

ET = ZoneInfo("America/New_York")
LAMBDA = 10.0
EPS_PART, EPS_PROP, EPS_SCORE = 0.01, 0.005, 0.005
FAMILIES = ("points", "rebounds", "assists", "threes")
CONFIRMED_AVAILABLE = ("unlisted", "available")
FIRST_EVAL_DATE = "2026-10-27"
WINDOW_B_START = "2026-11-01"
MIN_SUBGROUP = 300
VARIANTS = ("baseline", "injury_only", "calibration_only", "combined")


# ---------------------------------------------------------------------------- ridge-Platt
def _logit(p: np.ndarray, eps: float) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype=float), eps, 1 - eps)
    return np.log(p / (1 - p))


def ridge_platt_fit(p, y, eps: float, lam: float = LAMBDA, iters: int = 100) -> tuple[float, float]:
    """Penalised logistic recalibration toward (a, b) = (0, 1). Returns the identity for empty input."""
    x = _logit(p, eps)
    y = np.asarray(y, dtype=float)
    if x.size == 0:
        return 0.0, 1.0
    X = np.column_stack([np.ones_like(x), x])
    w = np.array([0.0, 1.0])
    prior = np.array([0.0, 1.0])
    for _ in range(iters):
        mu = 1 / (1 + np.exp(-(X @ w)))
        g = X.T @ (y - mu) - 2 * lam * (w - prior)
        H = (X * (mu * (1 - mu))[:, None]).T @ X + 2 * lam * np.eye(2)
        step = np.linalg.solve(H, g)
        w = w + step
        if np.abs(step).max() < 1e-10:
            break
    a, b = float(w[0]), float(w[1])
    return (0.0, 1.0) if b <= 0.05 else (a, b)


def ridge_platt_apply(p, ab: tuple[float, float], eps: float) -> np.ndarray:
    a, b = ab
    return 1 / (1 + np.exp(-(a + b * _logit(p, eps))))


# ---------------------------------------------------------------------------- metrics
def brier(p, y) -> float:
    return float(np.mean((np.asarray(p) - np.asarray(y)) ** 2))


def log_loss(p, y, eps: float = EPS_SCORE) -> float:
    p = np.clip(np.asarray(p, dtype=float), eps, 1 - eps)
    y = np.asarray(y, dtype=float)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def ece(p, y, bins: int = 10) -> float:
    p, y = np.asarray(p, dtype=float), np.asarray(y, dtype=float)
    idx = np.minimum((p * bins).astype(int), bins - 1)
    tot = 0.0
    for k in range(bins):
        m = idx == k
        if m.any():
            tot += m.sum() * abs(p[m].mean() - y[m].mean())
    return float(tot / max(len(p), 1))


def summary(p, y) -> dict[str, Any]:
    p, y = np.asarray(p, dtype=float), np.asarray(y, dtype=float)
    if p.size == 0:
        return {"n": 0}
    a, b = calibration_slope(np.clip(p, 1e-4, 1 - 1e-4), y) if 0 < y.mean() < 1 else (math.nan, math.nan)
    return {"n": int(p.size), "brier": round(brier(p, y), 5), "log_loss": round(log_loss(p, y), 5),
            "ece": round(ece(p, y), 5), "slope": round(b, 3), "intercept": round(a, 3),
            "mean_p": round(float(p.mean()), 4), "rate": round(float(y.mean()), 4)}


def paired_delta(df: pd.DataFrame, a: str, b: str, ycol: str = "y", n_boot: int = 2000, seed: int = 11) -> dict[str, Any]:
    """Δ Brier (a − b) on identical units, game-clustered bootstrap 95% CI."""
    d = (df[a] - df[ycol]) ** 2 - (df[b] - df[ycol]) ** 2
    g = df["game_id"].to_numpy()
    sums = pd.Series(d.to_numpy()).groupby(g).sum()
    cnts = pd.Series(np.ones(len(d))).groupby(g).sum()
    if len(sums) == 0:
        return {"n": 0}
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(sums), size=(n_boot, len(sums)))
    S, C = sums.to_numpy(), cnts.to_numpy()
    est = S[idx].sum(axis=1) / C[idx].sum(axis=1)
    return {"n": int(len(d)), "games": int(len(sums)), "delta": round(float(d.mean()), 5),
            "ci95": [round(float(np.quantile(est, 0.025)), 5), round(float(np.quantile(est, 0.975)), 5)]}


# ---------------------------------------------------------------------------- units
def _et_date(kickoff: str) -> str:
    return datetime.fromisoformat(kickoff.replace("Z", "+00:00")).astimezone(ET).date().isoformat()


def load_market(shadow_root: str) -> dict[tuple, float]:
    """(game, player, stat, as_of, rung) -> Kalshi yes mid, for listings live at the projection's as_of."""
    out = {}
    for r in _read(os.path.join(shadow_root, "market/listings/dt=*/*.jsonl.gz")):
        if r.get("record") != "market_listing" or not r.get("listed_by_as_of"):
            continue
        yb, ya = r.get("yes_bid_cents"), r.get("yes_ask_cents")
        if not yb or not ya or ya < yb:
            continue
        out[(r["game_id"], str(r["player_id"]), r["statistic"], r["pure_as_of"], float(r["at_least"]))] = (yb + ya) / 200.0
    return out


def build_units(shadow_root: str, avail_root: str, teams_csv: str, arms=("sim_rotation", "ewm5"),
                min_kickoff: str = "2026-10-19") -> tuple[pd.DataFrame, pd.DataFrame]:
    idx = AvailabilityIndex(load_availability(avail_root))
    tri = load_team_tricodes(teams_csv)
    outcomes = load_outcomes(shadow_root)
    market = load_market(shadow_root)
    game_obs: dict[str, str] = {}
    for (g, _, _), o in outcomes.items():
        game_obs[g] = max(game_obs.get(g, ""), o["observed_at"])
    part, props = [], []
    for arm in arms:
        rows = [r for r in load_projections(shadow_root, arm)
                if r["game_id"] in game_obs and r["kickoff"][:10] >= min_kickoff and r.get("x_season_phase") == "REGULAR_SEASON"]
        batches: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for r in rows:
            batches[(r["as_of"], r["game_id"])].append(r)
        for (as_of, gid), batch in batches.items():
            _, dec = apply_overlay(batch, idx, tri)
            date = _et_date(batch[0]["kickoff"])
            for r in batch:
                pid, st = str(r["player_id"]), r["statistic"]
                d = dec.get((gid, pid))
                if d is None:
                    continue
                om = outcomes.get((gid, pid, "minutes"))
                played = bool(om and om["played"])
                obs = om["observed_at"] if om else game_obs[gid]
                base = dict(arm=arm, slot=r.get("x_slot"), game_id=gid, player_id=pid, date=date, as_of=as_of,
                            outcome_observed_at=obs, status=d.status.status, status_source=d.status.source,
                            suppressed=d.suppressed)
                if not r["conditional_on_playing"] and st == "minutes":
                    part.append(dict(base, p_base=float(r["participation_probability"]), p_overlay=float(d.p_new),
                                     y=1.0 if played else 0.0))
                elif r["conditional_on_playing"] and st in FAMILIES and played:
                    o = outcomes.get((gid, pid, st))
                    if o is None:
                        continue
                    for t in r["projection"]["thresholds"]:
                        rung = float(t["at_least"])
                        props.append(dict(base, family=st, rung=rung, p_base=float(t["probability"]),
                                          y=1.0 if float(o["actual"]) >= rung else 0.0,
                                          market=market.get((gid, pid, st, as_of, rung))))
    return pd.DataFrame(part), pd.DataFrame(props)


# ---------------------------------------------------------------------------- walk-forward
def walk_forward(units: pd.DataFrame, pcol: str, groups: list[str], fit_mask: pd.Series, apply_mask: pd.Series,
                 eps: float, first_date: str = FIRST_EVAL_DATE) -> tuple[pd.Series, list[dict]]:
    """Calibrated probabilities for rows of dates >= first_date (NaN before). Each date's maps are fitted only on
    ``fit_mask`` rows whose outcome was observed before that date's earliest as_of."""
    out = pd.Series(np.nan, index=units.index)
    fits = []
    for date in sorted(units.loc[units.date >= first_date, "date"].unique()):
        day = units.date == date
        cutoff = units.loc[day, "as_of"].min()
        train = units[fit_mask & (units.outcome_observed_at < cutoff)]
        for key, sub in units[day & apply_mask].groupby(groups):
            key = key if isinstance(key, tuple) else (key,)
            tr = train
            for gcol, gv in zip(groups, key):
                tr = tr[tr[gcol] == gv]
            ab = ridge_platt_fit(tr[pcol].to_numpy(), tr["y"].to_numpy(), eps)
            out.loc[sub.index] = ridge_platt_apply(sub[pcol].to_numpy(), ab, eps)
            fits.append(dict(date=date, group=dict(zip(groups, key)), n_train=int(len(tr)), a=round(ab[0], 4), b=round(ab[1], 4)))
    return out, fits


def freeze(units: pd.DataFrame, pcol: str, groups: list[str], fit_mask: pd.Series, eps: float) -> dict[str, Any]:
    maps = {}
    for key, tr in units[fit_mask].groupby(groups):
        key = key if isinstance(key, tuple) else (key,)
        a, b = ridge_platt_fit(tr[pcol].to_numpy(), tr["y"].to_numpy(), eps)
        maps["|".join(map(str, key))] = {"a": round(a, 6), "b": round(b, 6), "n": int(len(tr))}
    return {"groups": groups, "eps": eps, "lambda": LAMBDA, "maps": maps}


# ---------------------------------------------------------------------------- evaluation
def add_variants(part: pd.DataFrame, props: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    part, props = part.copy(), props.copy()
    fits: dict[str, list] = {}
    every = pd.Series(True, index=part.index)
    part["baseline"] = part["p_base"]
    part["injury_only"] = part["p_overlay"]
    part["calibration_only"], fits["P1_calibration_only"] = walk_forward(
        part, "p_base", ["arm", "slot"], every, every, EPS_PART)
    conf = part["status"].isin(CONFIRMED_AVAILABLE)
    cal, fits["P1_combined"] = walk_forward(part, "p_overlay", ["arm", "slot"], conf, conf, EPS_PART)
    part["combined"] = np.where(conf, cal, part["p_overlay"])
    part.loc[part.date < FIRST_EVAL_DATE, "combined"] = np.nan

    allp = pd.Series(True, index=props.index)
    props["baseline"] = props["injury_only"] = props["p_base"]
    p2, fits["P2"] = walk_forward(props, "p_base", ["arm", "family"], allp, allp, EPS_PROP)
    props["calibration_only"] = props["combined"] = p2
    return part, props, fits


def _window(df: pd.DataFrame, w: str) -> pd.DataFrame:
    df = df[df.date >= FIRST_EVAL_DATE]
    if w == "A":
        return df[df.date < WINDOW_B_START]
    if w == "B":
        return df[df.date >= WINDOW_B_START]
    return df


def _subgroups(df: pd.DataFrame, by: list[str], with_col: str, without_col: str) -> list[dict]:
    out = []
    for key, g in df.groupby(by):
        key = key if isinstance(key, tuple) else (key,)
        s_w, s_wo = summary(g[with_col], g.y), summary(g[without_col], g.y)
        out.append({"group": dict(zip(by, key)), "n": int(len(g)), "with": s_w, "without": s_wo,
                    "delta_brier": paired_delta(g, with_col, without_col)})
    return out


def decide(df: pd.DataFrame, with_col: str, without_col: str, subgroup_sets: list[list[str]]) -> dict[str, Any]:
    """Apply the preregistered decision rules to one calibrator (with_col vs without_col) on the pooled window."""
    overall = paired_delta(df, with_col, without_col)
    reasons = []
    if not overall.get("ci95") or overall["ci95"][1] >= 0:
        reasons.append(f"rule 1: overall Δ Brier {overall.get('delta')} CI {overall.get('ci95')} does not exclude 0 below")
    subs = []
    for by in subgroup_sets:
        for s in _subgroups(df, by, with_col, without_col):
            subs.append(s)
            if s["n"] < MIN_SUBGROUP:
                continue
            ci = s["delta_brier"]["ci95"]
            if ci[0] > 0:
                reasons.append(f"rule 2: harm in {s['group']} Δ {s['delta_brier']['delta']} CI {ci}")
            sw, swo = s["with"]["slope"], s["without"]["slope"]
            if swo >= 0.80 and sw < 0.80:
                reasons.append(f"rule 3: false confidence in {s['group']} slope {swo} -> {sw}")
            if s["with"]["ece"] - s["without"]["ece"] > 0.01:
                reasons.append(f"rule 3: ECE worse in {s['group']} {s['without']['ece']} -> {s['with']['ece']}")
    return {"verdict": "ADOPTED" if not reasons else "REJECTED", "reasons": reasons, "overall": overall, "subgroups": subs}


def evaluate(part: pd.DataFrame, props: pd.DataFrame) -> dict[str, Any]:
    part, props, fits = add_variants(part, props)
    rep: dict[str, Any] = {"n_units": {"participation": int(len(part)), "props": int(len(props))}, "windows": {}}
    for w in ("A", "B", "pooled"):
        P, R = _window(part, w), _window(props, w)
        res: dict[str, Any] = {"participation_units": int(len(P)), "prop_units": int(len(R)),
                               "games": int(P.game_id.nunique())}
        res["participation"] = {
            f"{slot}|{arm}": {v: summary(g[v], g.y) for v in VARIANTS} for (slot, arm), g in P.groupby(["slot", "arm"])}
        res["participation_by_status"] = {
            f"{slot}|{st}": {v: summary(g[v], g.y) for v in VARIANTS}
            for (slot, st), g in P[P.arm == "sim_rotation"].groupby(["slot", "status"])}
        res["participation_deltas"] = {
            f"{slot}|{arm}": {f"{v}-baseline": paired_delta(g, v, "baseline") for v in VARIANTS[1:]}
            | {"combined-injury_only": paired_delta(g, "combined", "injury_only")}
            for (slot, arm), g in P.groupby(["slot", "arm"])}
        res["props"] = {
            f"{slot}|{arm}|{fam}": {v: summary(g[v], g.y) for v in ("baseline", "calibration_only")}
            | {"delta": paired_delta(g, "calibration_only", "baseline")}
            for (slot, arm, fam), g in R.groupby(["slot", "arm", "family"])}
        M = R[R.market.notna()]
        res["market"] = {
            f"{slot}|{arm}|{fam}": {"n": int(len(g)), "games": int(g.game_id.nunique()),
                                    "market": summary(g.market, g.y), "baseline": summary(g.baseline, g.y),
                                    "calibrated": summary(g.calibration_only, g.y),
                                    "baseline-market": paired_delta(g, "baseline", "market"),
                                    "calibrated-market": paired_delta(g, "calibration_only", "market")}
            for (slot, arm, fam), g in M.groupby(["slot", "arm", "family"])}
        res["market_pooled"] = {f"{slot}|{arm}": {"n": int(len(g)), "baseline-market": paired_delta(g, "baseline", "market"),
                                                  "calibrated-market": paired_delta(g, "calibration_only", "market"),
                                                  "market": summary(g.market, g.y), "calibrated": summary(g.calibration_only, g.y),
                                                  "baseline": summary(g.baseline, g.y)}
                                for (slot, arm), g in M.groupby(["slot", "arm"])}
        res["coverage"] = {"prop_rungs_scored": int(len(R)),
                           "prop_rungs_not_issued_under_overlay_but_played": int(R.suppressed.sum()),
                           "participation_units": int(len(P)), "suppressed_units": int(P.suppressed.sum())}
        rep["windows"][w] = res
    pooled_P, pooled_R = _window(part, "pooled"), _window(props, "pooled")
    rep["decisions"] = {
        "P1_calibration_only (vs baseline)": decide(pooled_P, "calibration_only", "baseline", [["slot", "arm"], ["slot", "status"]]),
        "P1_combined (vs injury_only)": decide(pooled_P, "combined", "injury_only", [["slot", "arm"], ["slot", "status"]]),
        "P2_props (vs baseline)": decide(pooled_R, "calibration_only", "baseline", [["slot", "arm"], ["slot", "family"], ["arm", "family"]]),
    }
    rep["walk_forward_fits_last"] = {k: v[-8:] for k, v in fits.items()}
    return rep
