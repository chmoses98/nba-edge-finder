"""Proper scoring rules and calibration diagnostics for binary probability forecasts.

All functions accept any sequence of floats (lists, tuples, numpy arrays). ``p`` are forecast probabilities in
[0, 1]; ``y`` are realized outcomes in {0, 1}. Empty inputs raise ``ValueError`` rather than returning NaN so
callers cannot silently average over nothing.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

ArrayLike = Sequence[float] | np.ndarray


def _as_arrays(p: ArrayLike, y: ArrayLike) -> tuple[np.ndarray, np.ndarray]:
    pa = np.asarray(p, dtype=float).ravel()
    ya = np.asarray(y, dtype=float).ravel()
    if pa.shape != ya.shape:
        raise ValueError(f"p and y must have the same length ({pa.size} vs {ya.size})")
    if pa.size == 0:
        raise ValueError("empty input")
    if np.any((pa < 0) | (pa > 1)):
        raise ValueError("probabilities must lie in [0, 1]")
    if np.any((ya != 0) & (ya != 1)):
        raise ValueError("outcomes must be 0 or 1")
    return pa, ya


def brier(p: ArrayLike, y: ArrayLike) -> float:
    """Mean squared error between forecast and outcome. 0 is perfect; a constant 0.5 forecast scores 0.25."""
    pa, ya = _as_arrays(p, y)
    return float(np.mean((pa - ya) ** 2))


def log_loss(p: ArrayLike, y: ArrayLike, eps: float = 1e-6) -> float:
    """Mean negative log-likelihood with forecasts clipped to [eps, 1 - eps] so 0/1 forecasts stay finite."""
    pa, ya = _as_arrays(p, y)
    pc = np.clip(pa, eps, 1.0 - eps)
    return float(-np.mean(ya * np.log(pc) + (1.0 - ya) * np.log(1.0 - pc)))


def _bin_edges(bins: int) -> np.ndarray:
    if bins < 1:
        raise ValueError("bins must be >= 1")
    return np.linspace(0.0, 1.0, bins + 1)


def _bin_index(pa: np.ndarray, bins: int) -> np.ndarray:
    """Equal-width bins on [0, 1]; p == 1.0 falls in the last bin."""
    return np.minimum((pa * bins).astype(int), bins - 1)


def calibration_table(p: ArrayLike, y: ArrayLike, bins: int = 10) -> list[dict[str, Any]]:
    """Reliability table with equal-width bins. Empty bins are kept (n=0, means None) so ``sum(n) == len(p)``."""
    pa, ya = _as_arrays(p, y)
    edges = _bin_edges(bins)
    idx = _bin_index(pa, bins)
    rows: list[dict[str, Any]] = []
    for b in range(bins):
        mask = idx == b
        n = int(mask.sum())
        mean_p = float(pa[mask].mean()) if n else None
        mean_y = float(ya[mask].mean()) if n else None
        gap = (mean_y - mean_p) if n else None
        rows.append(
            {"bin_lo": float(edges[b]), "bin_hi": float(edges[b + 1]), "n": n, "mean_p": mean_p, "mean_y": mean_y, "gap": gap}
        )
    return rows


def ece(p: ArrayLike, y: ArrayLike, bins: int = 10) -> float:
    """Expected calibration error: n-weighted mean absolute gap between mean forecast and hit rate per bin."""
    pa, ya = _as_arrays(p, y)
    idx = _bin_index(pa, bins)
    total = 0.0
    for b in range(bins):
        mask = idx == b
        if mask.any():
            total += mask.sum() * abs(float(ya[mask].mean()) - float(pa[mask].mean()))
    return float(total / pa.size)


def _logit(x: np.ndarray, eps: float) -> np.ndarray:
    xc = np.clip(x, eps, 1.0 - eps)
    return np.log(xc / (1.0 - xc))


def reliability_slope_intercept(p: ArrayLike, y: ArrayLike, eps: float = 1e-6, max_iter: int = 50) -> tuple[float, float]:
    """Logistic recalibration (Cox): fit ``y ~ sigmoid(a + b * logit(p))`` by Newton's method.

    Returns ``(slope b, intercept a)``. Perfect calibration is (1, 0); slope < 1 means over-confident forecasts.
    A tiny ridge term keeps the fit finite when outcomes are separable.
    """
    pa, ya = _as_arrays(p, y)
    x = _logit(pa, eps)
    X = np.column_stack([np.ones_like(x), x])
    beta = np.array([0.0, 1.0])
    ridge = 1e-6 * np.eye(2)
    for _ in range(max_iter):
        mu = 1.0 / (1.0 + np.exp(-(X @ beta)))
        w = mu * (1.0 - mu)
        grad = X.T @ (ya - mu) - ridge @ beta
        hess = (X * w[:, None]).T @ X + ridge
        step = np.linalg.solve(hess, grad)
        beta = beta + step
        if np.max(np.abs(step)) < 1e-10:
            break
    return float(beta[1]), float(beta[0])


def sharpness(p: ArrayLike) -> float:
    """How far forecasts sit from 0.5, scaled to [0, 1]: ``4 * mean((p - 0.5)^2)``. 0 = always 0.5, 1 = always 0/1."""
    pa = np.asarray(p, dtype=float).ravel()
    if pa.size == 0:
        raise ValueError("empty input")
    return float(4.0 * np.mean((pa - 0.5) ** 2))


def brier_skill_score(p: ArrayLike, y: ArrayLike, p_ref: ArrayLike) -> float:
    """``1 - brier(p) / brier(p_ref)``. Positive means ``p`` beats the reference (e.g. the market's implied
    probability). Returns 0.0 if both are perfect and ``-inf`` if only the reference is."""
    ours = brier(p, y)
    ref = brier(p_ref, y)
    if ref == 0.0:
        return 0.0 if ours == 0.0 else float("-inf")
    return float(1.0 - ours / ref)


def summary_metrics(p: ArrayLike, y: ArrayLike, bins: int = 10) -> dict[str, Any]:
    """Compact JSON-serializable bundle used by ``metrics_by_group`` and the authority ledger."""
    pa, ya = _as_arrays(p, y)
    slope, intercept = reliability_slope_intercept(pa, ya)
    return {
        "n": int(pa.size),
        "mean_p": float(pa.mean()),
        "mean_y": float(ya.mean()),
        "brier": brier(pa, ya),
        "log_loss": log_loss(pa, ya),
        "ece": ece(pa, ya, bins),
        "sharpness": sharpness(pa),
        "reliability_slope": slope,
        "reliability_intercept": intercept,
    }


def metrics_by_group(records: Sequence[dict[str, Any]], group_key: str, p_key: str, y_key: str) -> dict[Any, dict[str, Any]]:
    """Group dict records by ``record[group_key]`` and compute ``summary_metrics`` per group.

    Records missing the probability or outcome (None) are skipped.
    """
    groups: dict[Any, tuple[list[float], list[float]]] = {}
    for r in records:
        pv, yv = r.get(p_key), r.get(y_key)
        if pv is None or yv is None:
            continue
        ps, ys = groups.setdefault(r.get(group_key), ([], []))
        ps.append(float(pv))
        ys.append(float(yv))
    return {g: summary_metrics(ps, ys) for g, (ps, ys) in groups.items()}
