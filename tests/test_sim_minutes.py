"""Tests for the minutes model (nba_edge.sim.minutes): water-filling, starter selection, blowout rotation."""

from __future__ import annotations

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra import numpy as hnp

from nba_edge.sim.minutes import apply_blowout, draw_availability, draw_minutes, draw_starters, water_fill
from nba_edge.sim.params import LEAGUE, PlayerParams
from tests.conftest import ROSTER_SPECS, make_roster

TOL = 1e-6


def _players(p_play: float = 1.0) -> list[PlayerParams]:
    pls = make_roster(1, 1000)
    for p in pls:
        p.p_play = p_play
    return pls


# ---------------------------------------------------------------------------------------------------------------
# water_fill
# ---------------------------------------------------------------------------------------------------------------


def test_water_fill_sums_to_total_and_respects_caps():
    caps = np.array([42.0, 42.0, 42.0, 42.0, 40.0, 36.0])  # sum 244 >= 240: feasible
    raw = np.array([
        [36.0, 34.0, 32.0, 30.0, 28.0, 20.0],  # sum 180 -> deficit 60
        [40.0, 40.0, 40.0, 40.0, 36.0, 30.0],  # sum 226 -> deficit 14
        [42.0, 40.0, 40.0, 40.0, 36.0, 30.0],  # sum 228 -> deficit 16, total 244 = feasible max -> all at caps
        [45.0, 45.0, 45.0, 45.0, 45.0, 45.0],  # sum 270 -> surplus, scaled down (raw above caps on purpose)
    ])
    total = np.array([240.0, 240.0, 244.0, 240.0])
    m = water_fill(raw, caps, total)
    assert m.shape == raw.shape
    np.testing.assert_allclose(m.sum(axis=1), total, atol=TOL)
    assert np.all(m <= caps[None, :] + 1e-9)
    assert np.all(m >= 0.0)
    np.testing.assert_allclose(m[2], caps, atol=TOL)  # feasible max: everybody at cap


def test_water_fill_unavailable_players_stay_zero():
    caps = np.full(6, 42.0)
    raw = np.array([[36.0, 0.0, 32.0, 0.0, 28.0, 20.0], [0.0, 30.0, 30.0, 30.0, 0.0, 30.0]])
    total = np.array([150.0, 160.0])
    m = water_fill(raw, caps, total)
    assert np.all(m[raw == 0] == 0.0)
    np.testing.assert_allclose(m.sum(axis=1), total, atol=TOL)


def test_water_fill_deficit_redistributes_by_headroom():
    """Deficit is shared in proportion to (cap - raw), so near-capped players absorb little and deep bench absorbs
    most. The zero-raw player absorbs nothing."""
    caps = np.array([42.0, 40.0, 40.0, 40.0])
    raw = np.array([[40.0, 20.0, 10.0, 0.0]])  # headroom 2, 20, 30, (0: unavailable)
    total = np.array([100.0])  # deficit 30
    m = water_fill(raw, caps, total)
    added = m[0] - raw[0]
    head = np.array([2.0, 20.0, 30.0])
    np.testing.assert_allclose(added[:3], head / head.sum() * 30.0, atol=TOL)
    assert added[3] == 0.0
    assert added[0] < added[1] < added[2]
    np.testing.assert_allclose(m.sum(), 100.0, atol=TOL)


def test_water_fill_surplus_scales_proportionally():
    caps = np.full(4, 42.0)
    raw = np.array([[40.0, 30.0, 20.0, 10.0]])  # sum 100
    m = water_fill(raw, caps, np.array([50.0]))
    np.testing.assert_allclose(m[0], raw[0] * 0.5, atol=TOL)


def test_water_fill_zero_total_zeroes_row():
    caps = np.full(3, 42.0)
    m = water_fill(np.array([[30.0, 20.0, 10.0]]), caps, np.array([0.0]))
    np.testing.assert_allclose(m, 0.0, atol=TOL)


def test_water_fill_infeasible_total_never_exceeds_caps():
    """If total > sum(caps of available players) the row cannot sum to total; caps must still hold."""
    caps = np.full(4, 42.0)
    raw = np.array([[40.0, 0.0, 0.0, 0.0]])
    m = water_fill(raw, caps, np.array([120.0]))
    assert np.all(m <= caps[None, :] + 1e-9)
    assert np.all(m[raw == 0] == 0.0)
    assert m.sum() < 120.0


@st.composite
def _feasible_rows(draw):
    k = draw(st.integers(min_value=1, max_value=15))
    n = draw(st.integers(min_value=1, max_value=6))
    caps = draw(hnp.arrays(np.float64, (k,), elements=st.floats(1.0, 48.0, allow_nan=False, allow_infinity=False)))
    raw = draw(hnp.arrays(np.float64, (n, k), elements=st.floats(0.0, 48.0, allow_nan=False, allow_infinity=False)))
    # ~30 % of entries unavailable (exactly zero), the rest within caps
    mask = draw(hnp.arrays(np.bool_, (n, k), elements=st.booleans()))
    raw = np.where(mask, 0.0, np.minimum(raw, caps[None, :]))
    avail_cap = np.where(raw > 0, caps[None, :], 0.0).sum(axis=1)
    fracs = draw(hnp.arrays(np.float64, (n,), elements=st.floats(0.0, 1.0, allow_nan=False, allow_infinity=False)))
    total = fracs * avail_cap  # feasible: 0 <= total <= sum of available caps
    return raw, caps, total


@given(_feasible_rows())
@settings(max_examples=300, deadline=None)
def test_water_fill_property_feasible_rows(data):
    raw, caps, total = data
    m = water_fill(raw, caps, total)
    assert m.shape == raw.shape
    assert np.all(np.isfinite(m))
    assert np.all(m >= -1e-12), "no negative minutes"
    assert np.all(m <= caps[None, :] + 1e-9), "caps respected"
    assert np.all(m[raw == 0.0] == 0.0), "unavailable stay zero"
    np.testing.assert_allclose(m.sum(axis=1), total, atol=1e-6, rtol=1e-9)
    # water_fill's early exit is batch-wide (it stops only when *every* row is within 1e-6 of its total), so the
    # no-op guarantee is: if all rows already sum to their totals, the output is the input, bit for bit. A single
    # already-balanced row alongside rows that need work may legitimately be re-scaled (still summing to total).
    if np.all(np.abs(raw.sum(axis=1) - total) < 1e-7):
        np.testing.assert_array_equal(m, raw)


# ---------------------------------------------------------------------------------------------------------------
# availability / starters / minutes
# ---------------------------------------------------------------------------------------------------------------


def test_draw_availability_matches_p_play():
    rng = np.random.default_rng(0)
    pls = _players()
    pls[3].p_play = 0.0
    pls[5].p_play = 0.5
    played = draw_availability(rng, pls, 40_000)
    assert played.shape == (40_000, len(pls)) and played.dtype == np.bool_
    assert played[:, 3].sum() == 0
    assert played[:, 0].all()
    assert abs(played[:, 5].mean() - 0.5) < 0.02


def test_draw_starters_exactly_five_when_five_available():
    rng = np.random.default_rng(1)
    pls = _players()
    n = 20_000
    played = rng.random((n, len(pls))) < 0.7  # random availability, sometimes fewer than 5
    started = draw_starters(rng, pls, played)
    n_avail = played.sum(axis=1)
    n_start = started.sum(axis=1)
    assert np.all(n_start[n_avail >= 5] == 5)
    assert np.all(n_start[n_avail < 5] == n_avail[n_avail < 5]), "when <5 available, everyone available starts"
    assert not (started & ~played).any(), "nobody starts without playing"
    assert (n_avail < 5).any(), "test should cover the <5 branch"


def test_draw_starters_all_available_prefers_high_p_start():
    rng = np.random.default_rng(2)
    pls = _players()
    played = np.ones((20_000, len(pls)), dtype=bool)
    started = draw_starters(rng, pls, played)
    assert np.all(started.sum(axis=1) == 5)
    rate = started.mean(axis=0)
    assert rate[:5].min() > 0.95, "the five nominal starters start the vast majority of the time"
    assert rate[5:].max() < 0.05
    assert rate[10:].max() == 0.0, "p_start=0 players never start when >=5 others are available"


def test_draw_minutes_sums_to_total_and_zero_for_absent():
    rng = np.random.default_rng(3)
    pls = _players()
    pls[1].p_play = 0.0
    pls[6].p_play = 0.5
    n = 20_000
    played = draw_availability(rng, pls, n)
    total = np.full(n, LEAGUE["regulation_minutes"])
    m = draw_minutes(rng, pls, played, total)
    np.testing.assert_allclose(m.sum(axis=1), 240.0, atol=TOL)
    assert np.all(m[~played] == 0.0)
    # the 0.5-minute floor is applied to the raw draw *before* water-filling, so surplus rows can scale it down;
    # the guarantee that survives renormalisation is strictly positive minutes for everyone who plays
    assert np.all(m[played] > 0.0), "anyone who plays gets positive minutes"
    assert np.all(m <= np.array([p.min_cap for p in pls])[None, :] + 1e-9)
    # a starter's mean lands near its min_mean scaled by the team renormalisation, not wildly off
    means = m.mean(axis=0)
    assert 30 < means[0] < 40
    # when player 6 (20 mpg) is out, the others' minutes are higher than when he plays
    out6 = ~played[:, 6]
    assert m[out6][:, :5].sum(axis=1).mean() > m[~out6][:, :5].sum(axis=1).mean()


# ---------------------------------------------------------------------------------------------------------------
# apply_blowout
# ---------------------------------------------------------------------------------------------------------------


def _rotation(n_rows: int) -> tuple[np.ndarray, np.ndarray]:
    mins = np.array([[spec[0] for spec in ROSTER_SPECS]] * n_rows, dtype=float)
    started = np.zeros_like(mins, dtype=bool)
    started[:, :5] = True
    return mins, started


def test_apply_blowout_only_touches_blowout_rows_and_keeps_totals():
    mins, started = _rotation(5)
    mins_before = mins.copy()
    margin = np.array([0.0, 17.9, 18.0, -18.0, -30.0])  # threshold is |margin| >= 18
    out = apply_blowout(mins, started, margin)
    np.testing.assert_array_equal(mins, mins_before)  # input untouched
    np.testing.assert_allclose(out.sum(axis=1), mins.sum(axis=1), atol=TOL)
    np.testing.assert_array_equal(out[0], mins[0])
    np.testing.assert_array_equal(out[1], mins[1])
    for r in (2, 3, 4):
        delta = out[r] - mins[r]
        assert np.all(delta[started[r]] < 0), "starters give minutes"
        assert np.all(delta[~started[r] & (mins[r] > 0)] > 0), "bench (with minutes) receives"
        np.testing.assert_allclose(delta[started[r]], -mins[r][started[r]] * LEAGUE["blowout_starter_cut"], atol=TOL)
        # bench receives in proportion to its own minutes
        bench = ~started[r]
        share = mins[r][bench] / mins[r][bench].sum()
        np.testing.assert_allclose(delta[bench], share * -delta[started[r]].sum(), atol=TOL)
    assert np.all(out >= 0.0)


def test_apply_blowout_no_bench_leaves_row_unchanged():
    mins = np.array([[40.0, 40.0, 40.0, 40.0, 40.0, 0.0]])
    started = np.array([[True, True, True, True, True, False]])
    out = apply_blowout(mins, started, np.array([25.0]))
    np.testing.assert_array_equal(out, mins)


def test_apply_blowout_does_not_touch_absent_players():
    mins, started = _rotation(2)
    mins[:, 9:] = 0.0  # deep bench absent
    out = apply_blowout(mins, started, np.array([20.0, -20.0]))
    assert np.all(out[:, 9:] == 0.0)
    np.testing.assert_allclose(out.sum(axis=1), mins.sum(axis=1), atol=TOL)


def test_apply_blowout_no_blowouts_is_identity():
    mins, started = _rotation(3)
    out = apply_blowout(mins, started, np.array([1.0, -5.0, 17.0]))
    np.testing.assert_array_equal(out, mins)
