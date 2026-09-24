"""Ownership and cadence rules for the self-renewing capture worker.

These are the Phase 3 safety proofs. Each names the corruption it forbids, because a test called
``test_lease_2`` teaches a future reader nothing about why the rule exists.
"""

from __future__ import annotations

import ast
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from nba_edge.worker import lease as L
from nba_edge.worker import plan as P

T0 = datetime(2026, 10, 3, 18, 0, tzinfo=UTC)


def _lease(**kw):
    base = L.takeover(None, "worker-A", T0)
    return L.heartbeat(base, T0, **kw)


# -- the cheap-watchdog invariant ---------------------------------------------------------------


@pytest.mark.parametrize("module", ["lease", "plan"])
def test_worker_decision_modules_stay_stdlib_only(module):
    """A watchdog must be able to read the lease without paying ``pip install -e .``.

    Measured on this repo: the install is 17-21s and ~690MB. Paying that to parse one JSON file is
    what made the old conductor expensive, and the same trap is one careless import away here.
    """
    src = Path(f"src/nba_edge/worker/{module}.py").read_text()
    imported = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imported.add(node.module.split(".")[0])
    third_party = imported - {"nba_edge", "json", "dataclasses", "datetime", "pathlib", "__future__"}
    assert not third_party, f"{module}.py must stay stdlib-only, but imports {sorted(third_party)}"


# -- two workers must never both believe they are primary ---------------------------------------


def test_a_live_lease_blocks_a_second_worker():
    live = _lease(expected_next_capture_at=T0 + timedelta(minutes=10))
    ok, why = L.may_write(live, "worker-B", T0 + timedelta(minutes=1))
    assert ok is False
    assert "worker-A" in why


def test_an_expired_lease_may_be_taken_over():
    """Expiry is relative to the holder's OWN promise, not a fixed TTL."""
    stale = _lease(expected_next_capture_at=T0 + timedelta(minutes=10))
    just_before = T0 + timedelta(minutes=10 + L.STALE_GRACE_MINUTES - 0.1)
    just_after = T0 + timedelta(minutes=10 + L.STALE_GRACE_MINUTES + 0.1)
    assert L.may_write(stale, "worker-B", just_before)[0] is False
    assert L.may_write(stale, "worker-B", just_after)[0] is True


def test_a_designated_successor_takes_over_a_still_fresh_lease():
    """The crash-recovery path: a parent that dies leaves a lease that still looks alive.

    Without the token the successor would fail closed within seconds of starting and the chain
    would die exactly when it was supposed to heal itself.
    """
    live = _lease(expected_next_capture_at=T0 + timedelta(minutes=10), successor_token="nonce-xyz")
    assert L.may_write(live, "worker-B", T0 + timedelta(seconds=5))[0] is False
    ok, why = L.may_write(live, "worker-B", T0 + timedelta(seconds=5), successor_token="nonce-xyz")
    assert ok is True
    assert "designated successor" in why


def test_a_wrong_successor_token_is_refused():
    live = _lease(expected_next_capture_at=T0 + timedelta(minutes=10), successor_token="nonce-xyz")
    assert L.may_write(live, "worker-B", T0, successor_token="not-the-token")[0] is False


def test_takeover_increments_generation_and_records_who_was_superseded():
    prev = _lease(expected_next_capture_at=T0)
    nxt = L.takeover(prev, "worker-B", T0 + timedelta(hours=1))
    assert nxt.generation == prev.generation + 1
    assert nxt.superseded_worker_id == "worker-A"
    assert nxt.successor_token is None, "a fresh lease must not inherit the old successor nonce"


def test_an_unreadable_lease_is_not_silently_treated_as_ownership(tmp_path):
    (tmp_path / L.LEASE_FILENAME).write_text("{ this is not json")
    assert L.read_lease(tmp_path) is None


def test_lease_round_trips_through_disk(tmp_path):
    original = _lease(expected_next_capture_at=T0 + timedelta(minutes=10), successor_token="abc")
    L.write_lease(tmp_path, original)
    assert L.read_lease(tmp_path) == original


# -- successor storms -----------------------------------------------------------------------


def test_a_chain_that_respawns_too_fast_refuses_to_dispatch():
    young = L.takeover(None, "worker-A", T0)
    thrash, why = L.thrashing(young, T0 + timedelta(minutes=1))
    assert thrash is True and "refusing" in why
    healthy, _ = L.thrashing(young, T0 + timedelta(minutes=L.MIN_GENERATION_INTERVAL_MINUTES + 1))
    assert healthy is False


# -- cadence ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "hours,expected",
    [
        (None, P.CADENCE_FAR_SECONDS),
        (12.0, P.CADENCE_FAR_SECONDS),
        (6.01, P.CADENCE_FAR_SECONDS),
        (5.0, P.CADENCE_NEAR_SECONDS),
        (1.6, P.CADENCE_NEAR_SECONDS),
        (1.5, P.CADENCE_TIGHT_SECONDS),
        (0.6, P.CADENCE_TIGHT_SECONDS),
        (0.5, P.CADENCE_FINAL_SECONDS),
        (0.05, P.CADENCE_FINAL_SECONDS),
    ],
)
def test_cadence_tightens_as_tip_approaches(hours, expected):
    assert P.cadence_seconds(hours) == expected


def test_cadence_never_exceeds_the_twelve_minute_acceptance_target_inside_six_hours():
    """Phase 5 requires >=95% of intervals <=12 min. Anything inside T-6h must clear that."""
    for hours in (6.0, 3.0, 1.0, 0.4):
        assert P.cadence_seconds(hours) <= 12 * 60


def test_active_window_opens_before_and_closes_after_tip():
    tip = datetime(2026, 10, 3, 23, 0, tzinfo=UTC)
    assert P.in_active_window(tip - timedelta(hours=P.WINDOW_OPEN_HOURS_BEFORE_TIP - 0.1), [tip])[0]
    assert not P.in_active_window(tip - timedelta(hours=P.WINDOW_OPEN_HOURS_BEFORE_TIP + 0.5), [tip])[0]
    assert P.in_active_window(tip + timedelta(hours=P.WINDOW_CLOSE_HOURS_AFTER_TIP - 0.1), [tip])[0]
    assert not P.in_active_window(tip + timedelta(hours=P.WINDOW_CLOSE_HOURS_AFTER_TIP + 0.5), [tip])[0]


def test_an_empty_slate_is_not_an_active_window():
    assert P.in_active_window(T0, [])[0] is False


def test_unparseable_schedule_rows_are_dropped_not_fatal():
    rows = [{"start_time_utc": "2026-10-03T23:00:00Z"}, {"start_time_utc": "garbage"}, {}]
    assert P.tip_times(rows) == [datetime(2026, 10, 3, 23, 0, tzinfo=UTC)]


# -- retirement must never become a timeout kill ------------------------------------------


def test_retirement_reserves_room_for_the_cycle_it_is_about_to_start():
    exit_at = T0 + timedelta(minutes=P.RETIREMENT_RESERVE_MINUTES + 5)
    assert P.should_retire(T0, exit_at, next_cycle_cost_seconds=0) is False
    # The same instant, but knowing the next cycle costs six minutes, is a retirement.
    assert P.should_retire(T0, exit_at, next_cycle_cost_seconds=6 * 60) is True


def test_planned_lifetime_leaves_headroom_under_the_platform_cap():
    """The timeout must be a backstop, never the rollover mechanism (brief, Phase 2)."""
    assert P.PLANNED_LIFETIME_MINUTES <= 300
    assert P.PLANNED_LIFETIME_MINUTES + P.RETIREMENT_RESERVE_MINUTES < 330, (
        "must finish before the workflow timeout"
    )
    assert 330 < 360, "and the workflow timeout must sit under the documented 6h platform cap"


def test_a_released_lease_is_immediately_available_to_anyone():
    """A retiring worker's last promise still points into the future; release must override it."""
    retired = _lease(expected_next_capture_at=T0 + timedelta(minutes=15), released_at=T0)
    ok, why = L.may_write(retired, "worker-B", T0 + timedelta(seconds=1))
    assert ok is True and "released" in why


def test_release_beats_a_promise_that_has_not_yet_expired():
    not_released = _lease(expected_next_capture_at=T0 + timedelta(minutes=15))
    assert L.may_write(not_released, "worker-B", T0 + timedelta(seconds=1))[0] is False
