"""Tip-aware handover placement: pure planner properties + wiring (off by default, never worse than nominal, never outside the safe band)."""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

import pytest

from nba_edge.worker import plan
from nba_edge.worker.run import TIP_AWARE_ENV, Worker

D = datetime(2026, 10, 21, tzinfo=UTC)
SLATE = [D + timedelta(hours=h, minutes=m) for h, m in ((23, 0), (23, 30), (24, 0), (25, 30), (26, 0))]  # evening ET slate in UTC


def handover(start, exit_at):
    h0 = exit_at - timedelta(minutes=plan.RETIREMENT_RESERVE_MINUTES)
    return h0, h0 + timedelta(minutes=plan.HANDOVER_GUARD_MINUTES)


def test_no_tips_is_exactly_nominal():
    s = D + timedelta(hours=7)
    assert plan.tip_aware_exit(s, []) == plan.planned_exit(s)


def test_nominal_handover_inside_a_window_is_moved_clear_of_it_and_stays_in_band():
    start = D + timedelta(hours=17)  # nominal exit lands 22:00Z, inside the first window; an earlier exit (<= 21:23Z) clears it
    nominal = plan.planned_exit(start)
    w = plan.critical_windows(SLATE)
    assert plan._overlap_minutes(*handover(start, nominal), w) > 0
    chosen = plan.tip_aware_exit(start, SLATE)
    assert plan._overlap_minutes(*handover(start, chosen), w) == 0
    assert timedelta(minutes=plan.TIP_AWARE_MIN_LIFETIME_MINUTES) <= chosen - start <= timedelta(minutes=plan.TIP_AWARE_MAX_LIFETIME_MINUTES)


def test_when_no_exit_in_the_band_can_clear_a_window_the_overlap_is_minimised_not_ignored():
    start = D + timedelta(hours=18, minutes=40)  # the whole band sits inside a 4-hour merged slate window
    w = plan.critical_windows(SLATE)
    chosen = plan.tip_aware_exit(start, SLATE)
    best = min(plan._overlap_minutes(*handover(start, start + timedelta(minutes=m)), w) for m in range(210, 313))
    assert plan._overlap_minutes(*handover(start, chosen), w) == pytest.approx(best)


def test_clear_nominal_is_kept():
    start = D + timedelta(hours=7)
    assert plan.tip_aware_exit(start, SLATE) == plan.planned_exit(start)


def test_never_worse_than_nominal_and_never_outside_the_backstop_over_many_starts():
    rng = random.Random(7)
    w = plan.critical_windows(SLATE)
    for _ in range(300):
        start = D + timedelta(minutes=rng.randint(0, 36 * 60))
        chosen = plan.tip_aware_exit(start, SLATE)
        nominal = plan.planned_exit(start)
        assert plan._overlap_minutes(*handover(start, chosen), w) <= plan._overlap_minutes(*handover(start, nominal), w) + 1e-9
        assert plan.TIP_AWARE_MIN_LIFETIME_MINUTES <= (chosen - start).total_seconds() / 60 <= plan.TIP_AWARE_MAX_LIFETIME_MINUTES
    assert plan.TIP_AWARE_MAX_LIFETIME_MINUTES + 18 <= 330  # workflow timeout-minutes backstop


def test_windows_merge_and_cover_t_minus_75_to_t_plus_5():
    w = plan.critical_windows([D + timedelta(hours=1), D + timedelta(hours=1, minutes=30)])
    assert w == [(D - timedelta(minutes=15), D + timedelta(hours=1, minutes=35))]


# ---- wiring -----------------------------------------------------------------------------------


def make(tmp_path, schedule, lifetime=None, now=None):
    t = now or (D + timedelta(hours=18, minutes=40))
    return Worker(data_root=tmp_path / "d", archive_root=tmp_path / "a", worker_id="w", now_fn=lambda: t, schedule_fn=lambda: schedule, lifetime_minutes=lifetime), t


def sched(tips):
    return [{"start_time_utc": t.isoformat().replace("+00:00", "Z")} for t in tips]


def test_flag_off_keeps_the_nominal_lifetime(tmp_path, monkeypatch):
    monkeypatch.delenv(TIP_AWARE_ENV, raising=False)
    w, t = make(tmp_path, sched(SLATE))
    assert w._exit_for(t) == plan.planned_exit(t)


def test_flag_on_places_the_exit_but_an_explicit_lifetime_override_wins(tmp_path, monkeypatch):
    monkeypatch.setenv(TIP_AWARE_ENV, "1")
    w, t = make(tmp_path, sched(SLATE))
    assert w._exit_for(t) == plan.tip_aware_exit(t, SLATE) != plan.planned_exit(t)
    w2, t2 = make(tmp_path, sched(SLATE), lifetime=60.0)
    assert w2._exit_for(t2) == plan.planned_exit(t2, 60.0)


def test_flag_on_falls_back_to_nominal_when_the_schedule_cannot_be_read(tmp_path, monkeypatch):
    monkeypatch.setenv(TIP_AWARE_ENV, "1")
    w, t = make(tmp_path, [])
    assert w._exit_for(t) == plan.planned_exit(t)

    def boom():
        raise RuntimeError("bad snapshot")

    w.schedule_fn = boom
    assert w._exit_for(t) == plan.planned_exit(t)


@pytest.mark.parametrize("v", ["", "0", "off", "no"])
def test_only_explicit_truthy_values_enable_it(tmp_path, monkeypatch, v):
    monkeypatch.setenv(TIP_AWARE_ENV, v)
    w, t = make(tmp_path, sched(SLATE))
    assert w._exit_for(t) == plan.planned_exit(t)
