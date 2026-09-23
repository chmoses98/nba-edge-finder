"""The scheduler audit decides whether a 5-10 minute capture objective is reachable, so it has to be
right about what counts as a delivered slot."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from nba_edge.ops.schedule_audit import audit, cron_slots


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


def _run(rid: int, created: str, started: str | None = None, conclusion: str = "success") -> dict:
    return {"id": rid, "created_at": created, "run_started_at": started or created, "conclusion": conclusion}


def test_cron_slots_expands_step_and_range():
    s = cron_slots("*/10 * * * *", _dt("2026-01-01T00:00"), _dt("2026-01-01T01:00"))
    assert [t.minute for t in s] == [0, 10, 20, 30, 40, 50, 0]
    assert len(cron_slots("0 * * * *", _dt("2026-01-01T00:00"), _dt("2026-01-02T00:00"))) == 25
    assert len(cron_slots("0 16 * * *", _dt("2026-01-01T00:00"), _dt("2026-01-08T00:00"))) == 7


def test_cron_reader_refuses_what_it_does_not_understand():
    # Silently mis-expanding a field would corrupt every number downstream, so refuse instead.
    for bad in ("*/10 * * *", "*/10 * * * * *", "99 * * * *", "5/10 * * * *"):
        with pytest.raises(ValueError):
            cron_slots(bad, _dt("2026-01-01T00:00"), _dt("2026-01-01T01:00"))


def test_a_slot_with_no_run_is_missing_not_merely_late():
    start, end = _dt("2026-01-01T00:00"), _dt("2026-01-01T01:00")
    runs = [_run(1, "2026-01-01T00:02:00Z"), _run(2, "2026-01-01T00:31:00Z")]
    a = audit("*/10 * * * *", runs, start, end)
    assert a.expected == 7 and a.delivered == 2 and a.missing == 5
    assert a.delivery_rate == pytest.approx(2 / 7)
    assert [s.nominal_utc for s in a.slots if not s.delivered][:2] == [
        "2026-01-01T00:10:00Z", "2026-01-01T00:20:00Z"
    ]


def test_one_run_cannot_credit_two_slots():
    """A burst of catch-up runs must not paper over the slots they were catching up on."""
    start, end = _dt("2026-01-01T00:00"), _dt("2026-01-01T01:00")
    # three runs all arriving after the 00:50 slot: they cannot retroactively satisfy 00:10-00:40
    runs = [_run(i, f"2026-01-01T00:5{i}:00Z") for i in (1, 2, 3)]
    a = audit("*/10 * * * *", runs, start, end)
    assert a.delivered == 1, "only the 00:50 slot is satisfied"
    assert a.missing == 6


def test_delay_and_queue_time_are_different_measurements():
    """Scheduler lateness and runner busyness are distinct problems with distinct remedies."""
    a = audit(
        "*/10 * * * *",
        [_run(1, "2026-01-01T00:05:00Z", started="2026-01-01T00:08:00Z")],
        _dt("2026-01-01T00:00"), _dt("2026-01-01T00:10"),
    )
    got = next(s for s in a.slots if s.delivered)
    assert got.delay_s == 300.0, "5 min late to be created"
    assert got.queue_s == 180.0, "a further 3 min waiting for a runner"


def test_effective_interval_reports_what_actually_happened():
    """The headline number: a */10 cron delivering hourly has an effective interval of 60, not 10."""
    start, end = _dt("2026-01-01T00:00"), _dt("2026-01-01T06:00")
    runs = [_run(i, f"2026-01-01T0{i}:00:00Z") for i in range(6)]
    a = audit("*/10 * * * *", runs, start, end)
    assert a.effective_interval_min == pytest.approx(60.0)
    assert a.longest_gap_min == pytest.approx(60.0)
    assert a.delivery_rate < 0.2


def test_conclusions_are_counted_so_a_red_run_is_not_a_delivered_success():
    a = audit(
        "*/10 * * * *",
        [_run(1, "2026-01-01T00:00:00Z", conclusion="failure"),
         _run(2, "2026-01-01T00:10:00Z", conclusion="success")],
        _dt("2026-01-01T00:00"), _dt("2026-01-01T00:10"),
    )
    assert a.conclusions == {"failure": 1, "success": 1}
