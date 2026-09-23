"""The rotation model exists to fix a measured distributional defect, so the tests are about shape."""

from __future__ import annotations

import numpy as np
import pytest

from nba_edge.sim.rotation import (
    ROTATION_MIN,
    Role,
    RotationProfile,
    classify_role,
    draw_rotation_minutes,
    estimate_profile,
)


def _profiles(spec):
    return [RotationProfile(nba_id=i, p_rotation=p, rot_min_mean=m, rot_min_sd=s,
                            role=classify_role(p, m, 1.0 if p > 0.8 else 0.0))
            for i, (p, m, s) in enumerate(spec)]


def _team(n_rot=9, n_fringe=6):
    spec = [(0.98, 33.0, 4.0)] * 5 + [(0.90, 20.0, 5.0)] * (n_rot - 5) + [(0.05, 12.0, 5.0)] * n_fringe
    return _profiles(spec)


def test_a_fringe_player_plays_rarely_not_a_little_every_night():
    """The central claim: 5% rotation odds must mean 95% zeros, not 5% of a rotation load nightly.

    A blended mean gets the average right and the distribution wrong, and a prop settles against the
    distribution.
    """
    rng = np.random.default_rng(0)
    profiles = _team()
    n, k = 20_000, len(profiles)
    played = np.ones((n, k), dtype=bool)
    caps = np.full(k, 42.0)
    m = draw_rotation_minutes(rng, profiles, played, caps, np.full(n, 240.0))

    fringe = m[:, -1]
    assert (fringe == 0).mean() > 0.5, "a fringe player must be absent from most draws"
    starter = m[:, 0]
    assert starter.mean() > 25.0, f"starters must carry real minutes, got {starter.mean():.1f}"


def test_team_minutes_are_conserved_every_draw():
    rng = np.random.default_rng(1)
    profiles = _team()
    n, k = 5_000, len(profiles)
    played = np.ones((n, k), dtype=bool)
    m = draw_rotation_minutes(rng, profiles, played, np.full(k, 42.0), np.full(n, 240.0))
    assert np.abs(m.sum(axis=1) - 240.0).max() < 1e-6

    ot = np.full(n, 265.0)  # one overtime
    m2 = draw_rotation_minutes(rng, profiles, played, np.full(k, 48.0), ot)
    assert np.abs(m2.sum(axis=1) - 265.0).max() < 1e-6


def test_minutes_concentrate_the_way_real_rotations_do():
    """Against 7,386 real team-games the top eight take ~90% of minutes; the old model gave 81%."""
    rng = np.random.default_rng(2)
    profiles = _team()
    n, k = 10_000, len(profiles)
    m = draw_rotation_minutes(rng, profiles, np.ones((n, k), dtype=bool), np.full(k, 42.0), np.full(n, 240.0))
    top8 = np.sort(m, axis=1)[:, ::-1][:, :8].sum(axis=1) / m.sum(axis=1)
    assert top8.mean() > 0.85, f"top-8 share {top8.mean():.3f} is too flat"
    assert (m >= 28).sum(axis=1).mean() > 3.0, "too few heavy-minute players"
    assert (m >= 5).sum(axis=1).mean() < 11.0, "too many players given real minutes"


def test_depth_is_promotion_under_pressure_not_routine_dilution():
    """Fringe players should play when the team is short-handed -- and essentially only then."""
    rng = np.random.default_rng(3)
    profiles = _team()
    n, k = 4_000, len(profiles)
    caps = np.full(k, 40.0)

    healthy = np.ones((n, k), dtype=bool)
    m_healthy = draw_rotation_minutes(rng, profiles, healthy, caps, np.full(n, 240.0))

    shorthanded = healthy.copy()
    shorthanded[:, :4] = False  # four rotation players out
    m_short = draw_rotation_minutes(rng, profiles, shorthanded, caps, np.full(n, 240.0))

    fringe_healthy = m_healthy[:, -6:].mean()
    fringe_short = m_short[:, -6:].mean()
    assert fringe_short > fringe_healthy * 2, (
        f"fringe minutes must rise when the rotation is thin: {fringe_healthy:.2f} -> {fringe_short:.2f}"
    )
    assert np.abs(m_short.sum(axis=1) - 240.0).max() < 1e-6


def test_nobody_exceeds_their_cap():
    rng = np.random.default_rng(4)
    profiles = _team()
    n, k = 5_000, len(profiles)
    caps = np.linspace(30.0, 42.0, k)
    m = draw_rotation_minutes(rng, profiles, np.ones((n, k), dtype=bool), caps, np.full(n, 240.0))
    assert (m <= caps[None, :] + 1e-6).all()
    assert (m >= -1e-9).all()


def test_membership_and_conditional_minutes_use_different_samples():
    """A player who sat half the window is a 50% rotation player who plays FULL minutes when he plays."""
    w = np.ones(10)
    hist = np.array([0, 0, 0, 0, 0, 30, 32, 28, 31, 29], dtype=float)
    p = estimate_profile(hist, w, p_start=1.0)
    assert 0.35 < p.p_rotation < 0.65, f"membership ~50%, got {p.p_rotation:.2f}"
    assert p.rot_min_mean > 25.0, (
        f"conditional minutes must ignore the zeros, got {p.rot_min_mean:.1f} -- "
        "averaging them in is the blending this model exists to avoid"
    )


def test_short_history_is_shrunk_toward_the_prior():
    """Two good games is not evidence of a settled role."""
    strong = estimate_profile(np.array([30.0, 30.0]), np.ones(2), p_start=1.0)
    assert strong.p_rotation < 0.85, "an unshrunk 1.0 would make a call-up a permanent starter"
    settled = estimate_profile(np.full(25, 30.0), np.ones(25), p_start=1.0)
    assert settled.p_rotation > strong.p_rotation, "more evidence must move the estimate further"


def test_roles_are_labelled_sensibly():
    assert classify_role(0.95, 33.0, 0.9) is Role.STARTER
    assert classify_role(0.80, 22.0, 0.0) is Role.PRIMARY_BENCH
    assert classify_role(0.30, 14.0, 0.0) is Role.DEEP_BENCH
    assert classify_role(0.05, 12.0, 0.0) is Role.FRINGE


def test_rotation_threshold_is_a_stated_choice():
    assert ROTATION_MIN == pytest.approx(10.0)
