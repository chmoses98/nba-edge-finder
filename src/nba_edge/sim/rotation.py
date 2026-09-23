"""Rotation membership and conditional minutes: two separate questions, modelled separately.

The previous minutes model asked one question -- "how many minutes does this player average?" -- and
then water-filled any deficit across every available player in proportion to headroom. That is the
wrong shape for basketball and it showed up as a measurable defect: against 7,386 real team-games
the simulator put 11.83 players over 5 minutes where reality has 9.93, gave only 2.13 players 28+
minutes where reality has 3.98, and sent 81% of minutes to its top eight where reality sends 90%.
Total minutes were right; the *distribution* was flat. Starters were starved, and because player
props are listed almost entirely on starters, every prop "over" was under-priced.

The fix is to model what coaches actually do. A coach picks a rotation of roughly nine or ten, plays
them, and goes deeper only when forced. So:

    P(in rotation tonight)          -- a membership question
    minutes | in rotation           -- a completely different, conditional question

A player with a 5% chance of cracking the rotation must NOT receive 5% of a rotation player's
minutes in every draw. He must play zero in 95% of draws and real rotation minutes in 5%. Those two
produce the same mean and entirely different distributions, and the distribution is what a prop
settles against.

Depth is *promotion under pressure*, not dilution. When enough rotation players are unavailable that
the remaining ones cannot cover 240 minutes within their caps, the next-most-likely players are
promoted in order. That is when deep bench minutes are real, and only then.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import numpy as np

# "In the rotation" needs a threshold, and any threshold is a modelling choice rather than a fact.
# 10 minutes is used because it matches how rotations actually look in the data: across 7,386
# team-games the mean count of players at 10+ minutes is 9.12, which is a coach's nine-man rotation.
# The 5-minute mark (9.93 players) also captures end-of-half cameos that are not rotation minutes.
ROTATION_MIN = 10.0

# How many players actually clear that bar, measured over 7,386 real team-games (2023-24..2025-26).
# The distribution is remarkably tight -- mean 9.12, sd 0.97, and 91% of team-games fall between 8
# and 10 -- because coaches play a nine-man rotation almost regardless of circumstance. That is a
# structural fact about basketball, so the model draws the rotation SIZE from it rather than hoping
# independent Bernoulli draws happen to land there. They do not: leaving it to chance produced 7.66
# players at 10+ minutes against a real 9.12, i.e. it swapped the old model's dilution for the
# opposite error.
ROTATION_SIZE_PMF: dict[int, float] = {7: 0.028, 8: 0.219, 9: 0.439, 10: 0.252, 11: 0.046, 12: 0.012}


class Role(StrEnum):
    STARTER = "starter"
    PRIMARY_BENCH = "primary_bench"
    DEEP_BENCH = "deep_bench"
    FRINGE = "fringe"  # on the active roster, effectively out of the rotation


@dataclass
class RotationProfile:
    """What we believe about one player's role tonight, estimated point-in-time."""

    nba_id: int
    p_rotation: float  # P(reaches rotation minutes | available)
    rot_min_mean: float  # expected minutes GIVEN in the rotation -- never a blend with zeros
    rot_min_sd: float
    role: Role
    n_games: int = 0  # trailing games this rests on; small n means the prior dominates


def classify_role(p_rotation: float, rot_min_mean: float, p_start: float) -> Role:
    """Coarse labels for reporting and for promotion order. Not used as a hard gate anywhere."""
    if p_start >= 0.5 and p_rotation >= 0.5:
        return Role.STARTER
    if p_rotation >= 0.55:
        return Role.PRIMARY_BENCH
    if p_rotation >= 0.2:
        return Role.DEEP_BENCH
    return Role.FRINGE


def draw_rotation_minutes(
    rng: np.random.Generator,
    profiles: list[RotationProfile],
    played: np.ndarray,
    caps: np.ndarray,
    total_minutes: np.ndarray,
    *,
    garbage_mean: float = 3.0,
) -> np.ndarray:
    """Draw a minutes matrix (n_draws, n_players) that sums to ``total_minutes`` per draw.

    Rotation membership is drawn first, then minutes conditional on it. Scaling to the team total
    happens **within the rotation**, so a night where a star sits redistributes his minutes to the
    other rotation players rather than sprinkling them over the whole bench. Players outside the
    rotation get a short garbage-time draw, which is why the tail of the minutes distribution is not
    identically zero.
    """
    n, k = played.shape
    p_rot = np.array([p.p_rotation for p in profiles], dtype=float)
    mu = np.array([p.rot_min_mean for p in profiles], dtype=float)
    sd = np.array([max(p.rot_min_sd, 1.0) for p in profiles], dtype=float)

    # Pick the rotation as a SET of a realistic size, not as k independent coin flips.
    #
    # Gumbel-top-k: adding Gumbel noise to log-odds and taking the top k draws a size-k subset with
    # probabilities ordered by p_rotation. So a 0.87 player is usually in and occasionally out, a
    # 0.37 player is usually out and occasionally in -- player-level uncertainty is preserved -- while
    # the rotation still comes out nine deep the way real ones do.
    sizes = np.array(sorted(ROTATION_SIZE_PMF))
    probs = np.array([ROTATION_SIZE_PMF[s] for s in sizes], dtype=float)
    target = rng.choice(sizes, size=n, p=probs / probs.sum())
    n_avail = played.sum(axis=1)
    target = np.minimum(target, n_avail)  # a short-handed team cannot field a full rotation

    logit = np.log(np.clip(p_rot, 1e-6, 1 - 1e-6) / (1 - np.clip(p_rot, 1e-6, 1 - 1e-6)))
    gumbel = -np.log(-np.log(np.clip(rng.random((n, k)), 1e-12, 1.0)))
    score = np.where(played, logit[None, :] + gumbel, -np.inf)
    order = np.argsort(-score, axis=1)
    ranks = np.empty_like(order)
    np.put_along_axis(ranks, order, np.arange(k)[None, :].repeat(n, axis=0), axis=1)
    in_rot = (ranks < target[:, None]) & played

    # Promotion under pressure: even a full-size rotation can be unable to cover the night within its
    # caps when several regulars are out. Then, and only then, the next-most-likely players are added.
    capacity = np.where(in_rot, caps, 0.0).sum(axis=1)
    short = capacity < total_minutes
    if short.any():
        for j in np.argsort(-p_rot):
            if not short.any():
                break
            add = short & played[:, j] & ~in_rot[:, j]
            if not add.any():
                continue
            in_rot[add, j] = True
            capacity = capacity + np.where(add, caps[j], 0.0)
            short = capacity < total_minutes

    raw = np.clip(rng.normal(mu[None, :], sd[None, :], (n, k)), ROTATION_MIN * 0.5, caps[None, :])
    minutes = np.where(in_rot, raw, 0.0)

    # Garbage time for the non-rotation available players: mostly nothing, occasionally a few minutes.
    bench = played & ~in_rot
    if bench.any():
        gt = rng.exponential(garbage_mean, (n, k)) * (rng.random((n, k)) < 0.35)
        minutes = np.where(bench, np.minimum(gt, 9.0), minutes)

    # Scale to the team total using the ROTATION only, so the bench cameo minutes above are preserved
    # rather than being inflated to soak up a deficit.
    rot_sum = np.where(in_rot, minutes, 0.0).sum(axis=1)
    bench_sum = np.where(bench, minutes, 0.0).sum(axis=1)
    target = np.maximum(total_minutes - bench_sum, 1.0)
    scale = np.where(rot_sum > 0, target / np.maximum(rot_sum, 1e-9), 1.0)
    minutes = np.where(in_rot, minutes * scale[:, None], minutes)

    # Scaling can push a player past his cap; give the excess back to the other rotation players and
    # repeat. Two passes converge in practice and the residual is corrected below.
    for _ in range(3):
        over = minutes > caps[None, :]
        if not over.any():
            break
        excess = np.where(over, minutes - caps[None, :], 0.0).sum(axis=1)
        minutes = np.minimum(minutes, caps[None, :])
        room = np.where(in_rot & (minutes < caps[None, :]), caps[None, :] - minutes, 0.0)
        room_sum = room.sum(axis=1)
        share = np.where(room_sum[:, None] > 0, room / np.maximum(room_sum[:, None], 1e-9), 0.0)
        minutes = minutes + share * excess[:, None]

    resid = total_minutes - minutes.sum(axis=1)
    room = np.where(in_rot & (minutes < caps[None, :]), caps[None, :] - minutes, 0.0)
    room_sum = room.sum(axis=1)
    share = np.where(room_sum[:, None] > 0, room / np.maximum(room_sum[:, None], 1e-9), 0.0)
    minutes = np.maximum(minutes + share * resid[:, None], 0.0)
    return minutes


# --- point-in-time estimation -------------------------------------------------------------------


def estimate_profile(
    minutes_history: np.ndarray,
    weights: np.ndarray,
    p_start: float,
    *,
    prior_p_rotation: float = 0.35,
    prior_weight: float = 0.8,
    prior_min_mean: float = 16.0,
) -> RotationProfile:
    """Estimate (p_rotation, minutes | rotation) from a player's trailing minutes.

    ``minutes_history`` is one entry per TEAM game in the window, with 0 for games the player did not
    appear in -- that zero is the signal for rotation membership and must not be dropped. Weights are
    the same exponential weights the rest of the feature layer uses, so recency is handled
    consistently.

    The two estimates use different samples on purpose. Membership is estimated over every team game
    (a player who sat six of the last ten is a 40% rotation player). Conditional minutes are
    estimated only over the games he was actually IN the rotation, because averaging in his zeros
    would reintroduce exactly the blending this model exists to avoid.
    """
    m = np.asarray(minutes_history, dtype=float)
    w = np.asarray(weights, dtype=float)
    if m.size == 0:
        return RotationProfile(0, prior_p_rotation, prior_min_mean, 6.0, Role.FRINGE, 0)

    in_rot = m >= ROTATION_MIN
    wsum = w.sum()
    # Shrink membership toward the prior: three games is not evidence of a settled role, and an
    # unshrunk 1.0 would make a fringe call-up a permanent starter.
    p_rot = float((w[in_rot].sum() + prior_p_rotation * prior_weight) / (wsum + prior_weight))

    if in_rot.any():
        wr = w[in_rot]
        mr = m[in_rot]
        mean = float((wr * mr).sum() / wr.sum())
        var = float((wr * (mr - mean) ** 2).sum() / wr.sum())
        sd = float(np.sqrt(max(var, 4.0)))
    else:
        mean, sd = prior_min_mean, 6.0

    return RotationProfile(
        nba_id=0,
        p_rotation=float(np.clip(p_rot, 0.01, 0.99)),
        rot_min_mean=float(np.clip(mean, ROTATION_MIN, 40.0)),
        rot_min_sd=float(np.clip(sd, 2.0, 10.0)),
        role=classify_role(p_rot, mean, p_start),
        n_games=int(m.size),
    )
