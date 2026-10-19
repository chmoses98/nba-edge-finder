"""Statistics for the paper system: game-clustered uncertainty, proper scores, calibration, multiple-testing and independence helpers.

Conventions
  * the independent unit is the GAME (cluster). Contracts, snapshots, YES/NO complements and ladder rungs of one player-game are
    never independent; every interval here resamples whole games (2,000 replicates, seed 20261020).
  * bias = prediction - actual (positive = over-projection); loss differences are A - B (negative = A better).
  * every function is NaN-safe and returns an explicit "n_obs": 0 / NaN result on empty input rather than raising.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as sps

from pf_core import metrics as pfm
from pf_core.dists import DistBatch

SEED = 20261020
N_BOOT = 2000
MIN_CELL_GAMES = 8            # a segment cell with fewer games is flagged, not printed as a number
MIN_CELL_N = 30
NAN = float("nan")


def _f(x) -> float | None:
    """JSON-safe float: NaN/inf -> None."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _codes(clusters) -> np.ndarray:
    cl = pd.factorize(np.asarray(clusters, dtype=object))[0]
    if (cl < 0).any():
        cl = cl.copy()
        miss = cl < 0
        cl[miss] = cl.max() + 1 + np.arange(miss.sum())
    return cl


def counts(df: pd.DataFrame) -> dict[str, int]:
    """Independent-unit counts of a frame (columns are optional): games, player-games, theses, decisions, contracts."""
    def nu(*cols):
        cols = [c for c in cols if c in df.columns]
        return int(df[cols].drop_duplicates().shape[0]) if cols and len(df) else 0
    return {"n_games": int(df["game_id"].nunique()) if "game_id" in df.columns and len(df) else 0,
            "n_player_games": nu("game_id", "entity_id") if "entity_id" in df.columns else 0,
            "n_theses": int(df["thesis_id"].nunique()) if "thesis_id" in df.columns and len(df) else 0,
            "n_decisions": int(df["decision_id"].nunique()) if "decision_id" in df.columns and len(df) else int(len(df)),
            "n_contracts": int(df["ticker"].nunique()) if "ticker" in df.columns and len(df) else 0}


# ------------------------------------------------------------------------------------------------ cluster bootstrap
def cluster_mean(values, clusters, n_boot: int = N_BOOT, seed: int = SEED) -> dict[str, Any]:
    """Mean with a game-cluster bootstrap 95% CI, SE and z. NaN values are dropped (with their cluster ids)."""
    v = np.asarray(values, float)
    cl = np.asarray(clusters, dtype=object)
    ok = np.isfinite(v)
    v, cl = v[ok], cl[ok]
    if len(v) == 0:
        return {"mean": None, "ci95": [None, None], "se": None, "z": None, "n_obs": 0, "n_clusters": 0}
    r = pfm.cluster_bootstrap_diff(v, np.zeros_like(v), cl, n_boot=n_boot, seed=seed)
    return {"mean": _f(r["mean_diff"]), "ci95": [_f(x) for x in r["ci95"]], "se": _f(r["se"]), "z": _f(r["z"]),
            "n_obs": int(r["n_obs"]), "n_clusters": int(r["n_clusters"])}


def cluster_diff(a, b, clusters, n_boot: int = N_BOOT, seed: int = SEED) -> dict[str, Any]:
    """Mean of (a - b), paired, game-clustered. Negative = A better when a, b are losses."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    return cluster_mean(a - b, clusters, n_boot, seed)


def cluster_ratio(num, den, clusters, n_boot: int = N_BOOT, seed: int = SEED) -> dict[str, Any]:
    """Ratio of sums sum(num)/sum(den) (e.g. ROI = net P&L / capital at risk) with a game-cluster bootstrap CI."""
    num, den = np.asarray(num, float), np.asarray(den, float)
    ok = np.isfinite(num) & np.isfinite(den)
    num, den, cl = num[ok], den[ok], _codes(np.asarray(clusters, dtype=object)[ok])
    if len(num) == 0 or den.sum() <= 0:
        return {"ratio": None, "ci95": [None, None], "n_obs": int(len(num)), "n_clusters": 0}
    k = cl.max() + 1
    sn, sd = np.bincount(cl, weights=num, minlength=k), np.bincount(cl, weights=den, minlength=k)
    idx = np.random.default_rng(seed).integers(0, k, size=(n_boot, k))
    d = sd[idx].sum(axis=1)
    boot = np.where(d > 0, sn[idx].sum(axis=1) / np.where(d > 0, d, 1), np.nan)
    boot = boot[np.isfinite(boot)]
    ci = [_f(np.quantile(boot, 0.025)), _f(np.quantile(boot, 0.975))] if len(boot) else [None, None]
    return {"ratio": _f(sn.sum() / sd.sum()), "ci95": ci, "n_obs": int(len(num)), "n_clusters": int(k)}


def cluster_p(mean: float | None, se: float | None) -> float | None:
    """Two-sided normal p-value from a clustered mean and SE (None when undefined)."""
    if mean is None or not se or se <= 0:
        return None
    return float(2 * sps.norm.sf(abs(mean / se)))


# ------------------------------------------------------------------------------------------------ proper scores
def brier(p, o) -> np.ndarray:
    return (np.asarray(p, float) - np.asarray(o, float)) ** 2


def log_loss(p, o, eps: float = 1e-6) -> np.ndarray:
    p = np.clip(np.asarray(p, float), eps, 1 - eps)
    o = np.asarray(o, float)
    return -(o * np.log(p) + (1 - o) * np.log(1 - p))


def pmf_matrix(los, probs) -> DistBatch:
    """Per-row integer pmfs (lo + list of probabilities) -> one DistBatch on a common lattice (rows with no pmf become uniform-free: dropped by caller)."""
    los = [int(x) for x in los]
    pr = [list(map(float, p)) for p in probs]
    lo = min(los)
    hi = max(a + len(p) for a, p in zip(los, pr))
    P = np.zeros((len(pr), hi - lo))
    for i, (a, p) in enumerate(zip(los, pr)):
        P[i, a - lo:a - lo + len(p)] = p
    return DistBatch(lo, P)


def crps_from_pmf(los, probs, y) -> np.ndarray:
    return pmf_matrix(los, probs).crps(np.asarray(y, float))


def central_coverage(los, probs, y, level: float, seed: int = 0) -> dict[str, float | None]:
    """Coverage of the central `level` interval: randomised-PIT coverage (exactly `level` under calibration) and the integer-range coverage."""
    if len(los) == 0:
        return {"pit_cover": None, "range_cover": None}
    d = pmf_matrix(los, probs)
    y = np.asarray(y, float)
    a = (1 - level) / 2
    pit = d.pit(y, np.random.default_rng(seed))
    lo, hi = d.interval(level)
    return {"pit_cover": _f(np.mean((pit >= a) & (pit <= 1 - a))), "range_cover": _f(np.mean((y >= lo) & (y <= hi)))}


def pit_var_ratio(los, probs, y, seed: int = 0) -> float | None:
    """var(PIT)/(1/12): >1 overconfident (too narrow), <1 underconfident."""
    if len(los) < 2:
        return None
    pit = pmf_matrix(los, probs).pit(np.asarray(y, float), np.random.default_rng(seed))
    return _f(np.var(pit) / (1 / 12))


def wilson(k: float, n: float, z: float = 1.96) -> list[float | None]:
    if n <= 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [_f(max(0.0, c - h)), _f(min(1.0, c + h))]


def calibration(p, o, clusters=None, bins: int = 10, min_bin_n: int = 20) -> dict[str, Any]:
    """Reliability table + ECE. Per-bin interval: Wilson on the effective sample (n_clusters-limited when clusters are given) so that
    many contracts of one game do not make a bin look more certain than it is. Bins below `min_bin_n` are flagged, not scored."""
    p, o = np.asarray(p, float), np.asarray(o, float)
    ok = np.isfinite(p) & np.isfinite(o)
    p, o = p[ok], o[ok]
    cl = None if clusters is None else np.asarray(clusters, dtype=object)[ok]
    if len(p) == 0:
        return {"status": "NO_DATA", "bins": [], "ece": None, "n": 0}
    edges = np.linspace(0, 1, bins + 1)
    b = np.clip(np.digitize(p, edges) - 1, 0, bins - 1)
    rows, tot, acc = [], 0, 0.0
    for i in range(bins):
        m = b == i
        n = int(m.sum())
        if not n:
            continue
        ng = int(pd.Series(cl[m]).nunique()) if cl is not None else n
        n_eff = min(n, ng) if cl is not None else n
        hr = float(o[m].mean())
        row = {"bin": f"{edges[i]:.1f}-{edges[i + 1]:.1f}", "n": n, "n_games": ng, "mean_p": float(p[m].mean()), "hit_rate": hr,
               "ci95": wilson(hr * n_eff, n_eff), "insufficient": n < min_bin_n}
        rows.append(row)
        if n >= min_bin_n:
            tot += n
            acc += n * abs(row["mean_p"] - hr)
    return {"status": "OK", "bins": rows, "ece": _f(acc / tot) if tot else None, "n": int(len(p))}


# ------------------------------------------------------------------------------------------------ multiple testing
def holm(pvals: list[float | None], alpha: float = 0.05) -> list[dict[str, Any]]:
    """Holm-Bonferroni step-down. None p-values are never rejected and do not count toward m. Returns adjusted p and rejection per input."""
    idx = [i for i, p in enumerate(pvals) if p is not None]
    m = len(idx)
    out = [{"p": p, "p_holm": None, "reject": False} for p in pvals]
    order = sorted(idx, key=lambda i: pvals[i])
    run = 0.0
    for rank, i in enumerate(order):
        adj = min(1.0, (m - rank) * pvals[i])
        run = max(run, adj)
        out[i]["p_holm"] = run
        out[i]["reject"] = run < alpha
    return out


def benjamini_hochberg(pvals: list[float | None], q: float = 0.10) -> list[dict[str, Any]]:
    idx = [i for i, p in enumerate(pvals) if p is not None]
    m = len(idx)
    out = [{"p": p, "q_bh": None, "reject": False} for p in pvals]
    order = sorted(idx, key=lambda i: pvals[i], reverse=True)
    run = 1.0
    for j, i in enumerate(order):
        rank = m - j
        run = min(run, pvals[i] * m / rank)
        out[i]["q_bh"] = min(1.0, run)
        out[i]["reject"] = out[i]["q_bh"] <= q
    return out


# ------------------------------------------------------------------------------------------------ independence + power
def collapse_units(df: pd.DataFrame, unit_cols: list[str], score_col: str, ascending: bool = False,
                   tie_col: str | None = None, tie_ascending: bool = True) -> pd.DataFrame:
    """One row per independent unit (e.g. thesis_id + horizon): the row with the best `score_col` (ties by `tie_col`, then decision_id
    for determinism). Used before any selected-trade inference so ladder rungs / both sides of one thesis cannot count as separate events."""
    if df.empty:
        return df
    cols, asc = [score_col], [ascending]
    if tie_col:
        cols.append(tie_col)
        asc.append(tie_ascending)
    if "decision_id" in df.columns:
        cols.append("decision_id")
        asc.append(True)
    return df.sort_values(cols, ascending=asc, kind="mergesort").drop_duplicates(unit_cols, keep="first").reset_index(drop=True)


def games_needed(effect: float | None, sd_per_game: float | None, alpha: float = 0.05, power: float = 0.8) -> int | None:
    """Games required to detect `effect` (per-game mean units) at two-sided alpha with the given power, given the per-game SD of that mean."""
    if not effect or not sd_per_game or sd_per_game <= 0 or abs(effect) < 1e-12:
        return None
    z = sps.norm.ppf(1 - alpha / 2) + sps.norm.ppf(power)
    return int(math.ceil((z * sd_per_game / abs(effect)) ** 2))


def per_game_sd(values, clusters) -> float | None:
    """SD across games of the per-game mean (the unit the bootstrap resamples)."""
    v = pd.Series(np.asarray(values, float))
    g = v.groupby(np.asarray(clusters, dtype=object)).mean().dropna()
    return _f(g.std(ddof=1)) if len(g) > 1 else None


def sign_consistency(values, days) -> dict[str, Any]:
    """Repeatability across days: share of days whose mean has the sign of the overall mean."""
    s = pd.Series(np.asarray(values, float), index=pd.Index(np.asarray(days, dtype=object))).dropna()
    if s.empty:
        return {"n_days": 0, "share_same_sign": None}
    byd = s.groupby(level=0).mean()
    tot = s.mean()
    if tot == 0:
        return {"n_days": int(len(byd)), "share_same_sign": None}
    return {"n_days": int(len(byd)), "share_same_sign": _f(np.mean(np.sign(byd.to_numpy()) == np.sign(tot)))}


def cell(values, clusters, extra: dict | None = None, min_games: int = MIN_CELL_GAMES, min_n: int = MIN_CELL_N) -> dict[str, Any]:
    """A segment cell: clustered mean, or an explicit suppression when too thin to print a number."""
    v = np.asarray(values, float)
    ng = int(pd.Series(np.asarray(clusters, dtype=object)[np.isfinite(v)]).nunique()) if len(v) else 0
    base = {"n": int(np.isfinite(v).sum()), "n_games": ng, **(extra or {})}
    if base["n"] < min_n or ng < min_games:
        return {**base, "suppressed": True, "reason": f"INSUFFICIENT_SAMPLE (needs n>={min_n} and games>={min_games})"}
    return {**base, "suppressed": False, **cluster_mean(v, clusters)}


def cluster_group_diff(values, mask_a, mask_b, clusters, n_boot: int = N_BOOT, seed: int = SEED) -> dict[str, Any]:
    """mean(values | A) - mean(values | B) with a game-cluster bootstrap CI (both group means are recomputed in every resample)."""
    v = np.asarray(values, float)
    ma, mb = np.asarray(mask_a, bool) & np.isfinite(v), np.asarray(mask_b, bool) & np.isfinite(v)
    if ma.sum() == 0 or mb.sum() == 0:
        return {"diff": None, "ci95": [None, None], "se": None, "n_a": int(ma.sum()), "n_b": int(mb.sum())}
    cl = _codes(clusters)
    k = cl.max() + 1
    sa, na = np.bincount(cl, weights=np.where(ma, v, 0.0), minlength=k), np.bincount(cl, weights=ma.astype(float), minlength=k)
    sb, nb = np.bincount(cl, weights=np.where(mb, v, 0.0), minlength=k), np.bincount(cl, weights=mb.astype(float), minlength=k)
    idx = np.random.default_rng(seed).integers(0, k, size=(n_boot, k))
    da, db = na[idx].sum(axis=1), nb[idx].sum(axis=1)
    ok = (da > 0) & (db > 0)
    boot = (sa[idx].sum(axis=1)[ok] / da[ok]) - (sb[idx].sum(axis=1)[ok] / db[ok])
    est = sa.sum() / na.sum() - sb.sum() / nb.sum()
    if len(boot) < 10:
        return {"diff": _f(est), "ci95": [None, None], "se": None, "n_a": int(ma.sum()), "n_b": int(mb.sum())}
    return {"diff": _f(est), "ci95": [_f(np.quantile(boot, 0.025)), _f(np.quantile(boot, 0.975))], "se": _f(boot.std(ddof=1)),
            "n_a": int(ma.sum()), "n_b": int(mb.sum())}
