"""Distribution families on the integer lattice and minutes-uncertainty propagation.

Families compared (parameters fitted on development out-of-sample residuals, then frozen):
  poisson, nb (NB2 with dispersion binned by the mean), normal (discretised, SD binned by the mean),
  empirical (quantile mapping of development ratio residuals y/mu, binned by the mean),
  mixture: sum over minutes scenarios m_q (development minutes residual quantiles around the minutes forecast)
           of NB(rate * m_q, alpha_given_minutes) -- the stat distribution *given* minutes is
           over-dispersed less than the marginal one, and minutes uncertainty is propagated explicitly.
"""
from __future__ import annotations

import numpy as np

from pf_core import dists, models

N_SCEN = 20


def fit_all(y_dev, mu_dev, K: int) -> dict:
    return {
        "poisson": {"kind": "poisson", "K": K},
        "nb": dict(models.fit_dist_params("nb_binned", y_dev, mu_dev), K=K),
        "normal": models.fit_dist_params("normal_binned", y_dev, mu_dev, lo=0, K=K, floor_at=0),
        "empirical": models.fit_dist_params("empirical_ratio", y_dev, mu_dev, K=K),
    }


def make(params: dict, mu) -> dists.DistBatch:
    return models.make_dist(params, np.maximum(np.asarray(mu, float), 0.05))


def fit_minutes_resid(y_min_dev, mhat_dev, K: int = 61) -> dict:
    """Empirical conditional-minutes distribution around the forecast (additive residuals, binned)."""
    return models.fit_dist_params("empirical_resid", y_min_dev, mhat_dev, K=K, n_bins=8)


def minutes_scenarios(min_params: dict, mhat) -> np.ndarray:
    """(n, N_SCEN) minutes scenarios = forecast + residual quantiles of the forecast's bin."""
    mhat = np.asarray(mhat, float)
    b = np.digitize(mhat, np.array(min_params["edges"]))
    S = np.array(min_params["samples"])          # (bins, m) sorted quantiles
    m = S.shape[1]
    idx = (np.arange(N_SCEN) + 0.5) / N_SCEN * m
    Q = S[:, idx.astype(int)]
    return np.clip(mhat[:, None] + Q[b], 0.5, 58.0)


def fit_alpha_given_minutes(y_dev, rate_dev, minutes_actual_dev) -> float:
    """NB2 dispersion of the stat when minutes are known (rate x actual minutes as the mean)."""
    return dists.fit_nb_alpha(y_dev, np.asarray(rate_dev) * np.asarray(minutes_actual_dev))


def mixture(rate, scen: np.ndarray, alpha: float, K: int, scale=None, chunk: int = 4000) -> dists.DistBatch:
    """Equal-weight mixture over minutes scenarios of NB(rate * m_q * scale, alpha)."""
    rate = np.asarray(rate, float)
    sc = np.ones_like(rate) if scale is None else np.asarray(scale, float)
    n = len(rate)
    P = np.zeros((n, K))
    for s in range(0, n, chunk):
        e = min(n, s + chunk)
        mu = (rate[s:e, None] * scen[s:e] * sc[s:e, None]).ravel()
        d = dists.negbin(mu, alpha, K)
        P[s:e] = d.P.reshape(e - s, scen.shape[1], K).mean(axis=1)
    return dists.DistBatch(0, P)
