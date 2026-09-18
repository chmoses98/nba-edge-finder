"""Minutes model: availability -> minutes distribution per player, coherent with the team's total minutes.

Algorithm (vectorised over draws):
1. Availability draws: play_i ~ Bernoulli(p_play_i), independent across players (correlated availability, e.g. a
   team resting several starters together, is a known limitation and flagged in docs).
2. Raw minutes for available players: m_i ~ Normal(min_mean_i, min_sd_i * dispersion_i), clipped to [0, cap_i].
3. Water-filling renormalisation so that sum_i m_i == total_minutes (240 + 25/OT). Deficits (when a heavy-minute
   player is out) are redistributed proportionally to each remaining player's *headroom* (cap - m), so the
   redistribution is logical: rotation players absorb minutes first, deep bench absorbs the remainder. Surpluses
   are scaled down proportionally.
4. Blowout adjustment (applied after the game score is known): when |margin| >= blowout_margin, starters give up
   a share of their minutes to bench players in that draw.
5. Starter draws: start_i ~ Bernoulli(p_start_i) conditional on playing; the five highest p_start available players
   are forced to start if fewer than five drew 'start' (so lineups are always five deep when >=5 are available).
"""

from __future__ import annotations

import numpy as np

from nba_edge.sim.params import LEAGUE, PlayerParams


def draw_availability(rng: np.random.Generator, players: list[PlayerParams], n: int) -> np.ndarray:
    p = np.array([pl.p_play for pl in players], dtype=float)
    return rng.random((n, len(players))) < p[None, :]


def draw_starters(rng: np.random.Generator, players: list[PlayerParams], played: np.ndarray) -> np.ndarray:
    p = np.array([pl.p_start for pl in players], dtype=float)
    n, k = played.shape
    started = (rng.random((n, k)) < p[None, :]) & played
    # enforce exactly five starters where possible: rank available players by p_start (+ tiny noise for ties)
    score = np.where(played, p[None, :] + 1e-3 * rng.random((n, k)), -1.0)
    order = np.argsort(-score, axis=1)
    top5 = np.zeros_like(started)
    rows = np.arange(n)[:, None]
    top5[rows, order[:, :5]] = True
    top5 &= played
    n_started = started.sum(axis=1)
    fix = n_started != 5
    started[fix] = top5[fix]
    return started


def water_fill(raw: np.ndarray, caps: np.ndarray, total: np.ndarray, iters: int = 6, stickiness: np.ndarray | None = None) -> np.ndarray:
    """Scale minutes so each row sums to ``total`` without exceeding per-player caps (rows: draws, cols: players).
    Zero entries (unavailable players) stay zero. ``stickiness`` in [0, 1) (e.g. 0.7 * p_start) makes surplus
    minutes come off low-stickiness (bench) players first instead of proportionally off everyone."""
    avail = raw > 0
    m = np.minimum(raw, np.where(avail, caps[None, :], 0.0))
    give_w = (1.0 - stickiness)[None, :] if stickiness is not None else np.ones((1, raw.shape[1]))
    for _ in range(iters):
        s = m.sum(axis=1)
        deficit = total - s
        if np.all(np.abs(deficit) < 1e-6):
            break
        head = np.where(avail, np.maximum(caps[None, :] - m, 0.0), 0.0)
        # rows needing more minutes: distribute deficit by headroom; rows with surplus: scale down proportionally
        need = deficit > 0
        head_sum = head.sum(axis=1)
        share = np.where((head_sum > 0)[:, None], head / np.maximum(head_sum, 1e-9)[:, None], 0.0)
        m = np.where(need[:, None], m + share * deficit[:, None], m)
        surplus = deficit < 0
        if surplus.any():
            cut_w = m * give_w
            cut_sum = cut_w.sum(axis=1)
            cut = np.where((surplus & (cut_sum > 0))[:, None], cut_w / np.maximum(cut_sum, 1e-9)[:, None] * (-deficit)[:, None], 0.0)
            m = np.maximum(m - cut, 0.0)
        m = np.minimum(m, np.where(avail, caps[None, :], 0.0))
    return m


def draw_minutes(rng: np.random.Generator, players: list[PlayerParams], played: np.ndarray, total_minutes: np.ndarray) -> np.ndarray:
    n, k = played.shape
    mean = np.array([pl.min_mean for pl in players])
    sd = np.array([pl.min_sd * pl.minutes_dispersion for pl in players])
    caps = np.array([pl.min_cap for pl in players])
    raw = rng.normal(mean[None, :], sd[None, :], size=(n, k))
    raw = np.clip(raw, 0.0, caps[None, :])
    raw = np.where(played, np.maximum(raw, 0.5), 0.0)  # anyone who plays gets at least 30 seconds
    stick = np.clip(0.7 * np.array([pl.p_start for pl in players]), 0.0, 0.95)
    return water_fill(raw, caps, total_minutes, stickiness=stick)


def apply_blowout(minutes: np.ndarray, started: np.ndarray, margin: np.ndarray, blowout_margin: float = LEAGUE["blowout_margin"], starter_cut: float = LEAGUE["blowout_starter_cut"]) -> np.ndarray:
    """In blowout draws, move a share of starters' minutes to the bench (same team). Team total unchanged."""
    m = minutes.copy()
    blow = np.abs(margin) >= blowout_margin
    if not blow.any():
        return m
    starters = started & (m > 0)
    bench = (~started) & (m > 0)
    give = np.where(starters, m * starter_cut, 0.0)
    give_total = give.sum(axis=1)
    bench_w = np.where(bench, m, 0.0)
    bench_sum = bench_w.sum(axis=1)
    can = blow & (bench_sum > 0)
    add = np.where(can[:, None], bench_w / np.maximum(bench_sum, 1e-9)[:, None] * give_total[:, None], 0.0)
    m = np.where(can[:, None], m - give + add, m)
    return m
