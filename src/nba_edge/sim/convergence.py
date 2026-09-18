"""Convergence-driven simulation count.

We keep doubling batches until the Monte Carlo standard error of the *least stable* monitored probability is below
``target_se`` and the change between successive estimates is below ``target_delta``. Monitored quantities are
chosen to be Kalshi-relevant: P(home win), P(total > median), P(margin > ±k) for the spread ladder, and the
top scorers' points ladders. The result records n_sims used and the achieved SEs so predictions can carry them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from nba_edge.sim.engine import concat_results, simulate_batch
from nba_edge.sim.params import GameParams
from nba_edge.sim.result import SimResult


@dataclass
class ConvergenceReport:
    n_sims: int
    converged: bool
    max_se: float
    max_delta: float
    monitored: dict[str, float] = field(default_factory=dict)
    history: list[dict[str, float]] = field(default_factory=list)


def _monitored(res: SimResult, top_players: int = 4) -> dict[str, float]:
    m = res.margin
    t = res.total
    out = {"p_home": float((m > 0).mean())}
    med_t = float(np.median(t))
    for k in (-10.5, -5.5, -2.5, 2.5, 5.5, 10.5):
        out[f"p_margin_gt_{k}"] = float((m > k).mean())
    for k in (-10, -5, 5, 10):
        out[f"p_total_gt_{med_t + k:.1f}"] = float((t > med_t + k).mean())
    stars = sorted(res.players.values(), key=lambda p: -float(p.stats["pts"].mean()))[:top_players]
    for ps in stars:
        pts = ps.stats["pts"]
        mu = float(pts.mean())
        for k in (-5, 0, 5):
            thr = round(mu + k) + 0.5
            out[f"p_{ps.nba_id}_pts_gt_{thr}"] = float((pts > thr).mean())
    return out


def simulate_until_converged(gp: GameParams, seed: int, target_se: float = 0.004, target_delta: float = 0.006, min_sims: int = 20000, max_sims: int = 200000, batch: int = 20000) -> tuple[SimResult, ConvergenceReport]:
    rng = np.random.default_rng(seed)
    parts: list[SimResult] = []
    prev: dict[str, float] | None = None
    history: list[dict[str, float]] = []
    n = 0
    converged = False
    max_se = max_delta = float("nan")
    cur = None
    while n < max_sims:
        parts.append(simulate_batch(gp, batch, rng))
        n += batch
        cur = concat_results(parts, seed) if len(parts) > 1 else parts[0]
        mon = _monitored(cur)
        history.append(mon)
        se = max(np.sqrt(p * (1 - p) / n) for p in mon.values())
        delta = max(abs(mon[k] - prev[k]) for k in mon if k in prev) if prev else float("inf")
        prev = mon
        max_se, max_delta = float(se), float(delta)
        if n >= min_sims and se <= target_se and delta <= target_delta:
            converged = True
            break
    cur.seed = seed
    cur.n_sims = n
    cur.diagnostics = {"ot_rate": float((cur.n_ot > 0).mean()), "margin_sd": float(cur.margin.std()), "total_sd": float(cur.total.std()), "poss_mean": float(cur.possessions.mean())}
    return cur, ConvergenceReport(n, converged, max_se, max_delta, prev or {}, history)
