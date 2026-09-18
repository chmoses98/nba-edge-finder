"""Research question: which distribution family fits player counting stats conditional on a point forecast?

Using prior-games EWM means as the point forecast (mu) for pts/reb/ast/fg3m, compare Poisson, negative binomial
(dispersion fitted per stat on the training seasons), and a normal approximation, by out-of-sample log score and
by threshold calibration at mu+{-5,0,+5} (pts) etc. Run: ``python -m nba_edge.research.player_dist_study``.
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
from scipy import stats

from nba_edge.config import REPO_ROOT
from nba_edge.data.history import load_player_games

STATS = {"pts": (-5, 0, 5), "reb": (-2, 0, 2), "ast": (-2, 0, 2), "fg3m": (-1, 0, 1)}


def fit_nb_dispersion(mu: np.ndarray, y: np.ndarray) -> float:
    """Method-of-moments overdispersion alpha in Var = mu + alpha*mu^2 (clipped >= 1e-4)."""
    resid = (y - mu) ** 2 - mu
    denom = np.maximum(mu**2, 1e-9)
    return float(max(np.sum(resid) / np.sum(denom), 1e-4))


def nb_pmf(k: np.ndarray, mu: np.ndarray, alpha: float) -> np.ndarray:
    r = 1.0 / alpha
    p = r / (r + mu)
    return stats.nbinom.pmf(k, r, p)


def study(pg: pd.DataFrame, train_seasons: list[str], test_seasons: list[str], halflife: float = 10.0, min_prior: int = 10) -> dict:
    pg = pg[(pg["season_type"] == "regular") & (pg["played"])].sort_values(["nba_id", "season", "game_date_et"]).copy()
    out = {"train": train_seasons, "test": test_seasons}
    for stat, offsets in STATS.items():
        g = pg.groupby(["nba_id", "season"])[stat]
        mu = g.transform(lambda s: s.shift(1).ewm(halflife=halflife).mean())
        n_prior = g.cumcount()
        df = pg.assign(mu=mu, n_prior=n_prior).dropna(subset=["mu"])
        df = df[df["n_prior"] >= min_prior]
        tr = df[df["season"].isin(train_seasons)]
        te = df[df["season"].isin(test_seasons)]
        if tr.empty or te.empty:
            out[stat] = {"error": "insufficient data"}
            continue
        alpha = fit_nb_dispersion(tr["mu"].to_numpy(), tr[stat].to_numpy())
        y = te[stat].to_numpy().astype(int)
        m = np.maximum(te["mu"].to_numpy(), 0.05)
        ll_pois = float(np.mean(np.log(np.maximum(stats.poisson.pmf(y, m), 1e-12))))
        ll_nb = float(np.mean(np.log(np.maximum(nb_pmf(y, m, alpha), 1e-12))))
        sd_norm = np.sqrt(m + alpha * m**2)
        ll_norm = float(np.mean(np.log(np.maximum(stats.norm.cdf(y + 0.5, m, sd_norm) - stats.norm.cdf(y - 0.5, m, sd_norm), 1e-12))))
        thr = {}
        for off in offsets:
            t = np.rint(m + off) + 0.5
            emp = (y > t).astype(float)
            p_pois = 1 - stats.poisson.cdf(np.floor(t), m)
            p_nb = 1 - stats.nbinom.cdf(np.floor(t), 1 / alpha, (1 / alpha) / (1 / alpha + m))
            p_norm = 1 - stats.norm.cdf(t, m, sd_norm)
            thr[f"mu{off:+d}"] = {"empirical": float(emp.mean()), "poisson": float(p_pois.mean()), "negbin": float(p_nb.mean()), "normal": float(p_norm.mean()),
                                  "brier_poisson": float(np.mean((p_pois - emp) ** 2)), "brier_negbin": float(np.mean((p_nb - emp) ** 2)), "brier_normal": float(np.mean((p_norm - emp) ** 2))}
        out[stat] = {"n_test": int(len(te)), "nb_alpha": alpha, "log_score": {"poisson": ll_pois, "negbin": ll_nb, "normal_discretised": ll_norm}, "thresholds": thr}
    return out


def main() -> int:
    hist = REPO_ROOT / "data" / "history"
    seasons = sorted({p.stem.split("_")[-1] for p in (hist / "espn").glob("player_games_*.parquet")})
    pg = load_player_games(hist, seasons)
    train, test = seasons[:-1], seasons[-1:]
    rep = study(pg, train, test)
    out = REPO_ROOT / "docs" / "research" / "player_dist_study.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, indent=1))
    for stat in STATS:
        if "log_score" in rep.get(stat, {}):
            print(stat, "alpha", round(rep[stat]["nb_alpha"], 4), {k: round(v, 4) for k, v in rep[stat]["log_score"].items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
