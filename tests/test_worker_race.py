"""Simulated worker lifetimes: takeover, crash recovery, storms, and fail-closed writes.

The Phase 3 brief names five corruptions to prevent. Each has a test here that drives a whole
worker lifetime against a fake clock, so a regression shows up as a failing scenario rather than
as a silently broken invariant in production five hours into a night slate.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from nba_edge.worker import lease as L
from nba_edge.worker.run import Worker

T0 = datetime(2026, 10, 3, 18, 0, tzinfo=UTC)
TIP = datetime(2026, 10, 3, 23, 0, tzinfo=UTC)
SCHEDULE = [{"start_time_utc": TIP.isoformat().replace("+00:00", "Z")}]


class FakeClock:
    """A clock the test drives. Sleeping and running commands both advance it."""

    def __init__(self, start: datetime) -> None:
        self.t = start

    def now(self) -> datetime:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.t += timedelta(seconds=seconds)


def make_worker(
    tmp_path,
    clock,
    worker_id="run-1",
    *,
    capture_rc=0,
    capture_cost=180.0,
    dispatched=None,
    schedule=None,
    successor_token=None,
    lifetime=60.0,
):
    calls = []

    def run_fn(cmd, timeout):
        calls.append(cmd)
        if cmd[:2] == ["nba", "capture"]:
            clock.t += timedelta(seconds=capture_cost)
            return capture_rc, "capture output"
        return 0, ""

    def dispatch_fn(token):
        if dispatched is not None:
            dispatched.append(token)
        return True

    w = Worker(
        data_root=tmp_path / "data",
        archive_root=tmp_path / "archive",
        worker_id=worker_id,
        successor_token=successor_token,
        now_fn=clock.now,
        sleep_fn=clock.sleep,
        run_fn=run_fn,
        dispatch_fn=dispatch_fn if dispatched is not None else None,
        schedule_fn=lambda: SCHEDULE if schedule is None else schedule,
        lifetime_minutes=lifetime,
    )
    w._calls = calls
    (tmp_path / "archive").mkdir(parents=True, exist_ok=True)
    return w


# -- 1. two workers must never both believe they are primary ------------------------------------


def test_a_second_worker_fails_closed_and_writes_nothing(tmp_path):
    clock = FakeClock(T0)
    first = make_worker(tmp_path, clock, "run-1", lifetime=30.0)
    first.run()
    held = L.read_lease(tmp_path / "archive")
    assert held.worker_id == "run-1"

    # Install a genuinely LIVE lease for run-1: still promising, and explicitly not released.
    # (Reusing the retired lease here would test nothing -- release makes it available on purpose.)
    clock2 = FakeClock(T0 + timedelta(minutes=1))
    L.write_lease(
        tmp_path / "archive",
        L.heartbeat(
            L.takeover(None, "run-1", clock2.now()),
            clock2.now(),
            expected_next_capture_at=clock2.now() + timedelta(minutes=10),
        ),
    )
    second = make_worker(tmp_path, clock2, "run-2")
    res = second.run()

    assert res.fail_closed is True
    assert "fail-closed" in res.exit_reason
    assert res.cycles == [], "a fail-closed worker must not capture at all"
    assert L.read_lease(tmp_path / "archive").worker_id == "run-1", "the lease must not change hands"
    assert not any(c[:2] == ["nba", "capture"] for c in second._calls)


# -- 2. a crashed worker's chain heals itself ---------------------------------------------------


def test_the_designated_successor_recovers_a_chain_whose_parent_crashed(tmp_path):
    """The parent dies mid-life, so its lease still looks alive. The successor must still start."""
    archive = tmp_path / "archive"
    archive.mkdir(parents=True, exist_ok=True)
    crashed = L.heartbeat(
        L.takeover(None, "run-1", T0),
        T0,
        expected_next_capture_at=T0 + timedelta(minutes=10),  # a promise it will never keep
        successor_token="nonce-1",
    )
    L.write_lease(archive, crashed)

    # Seconds later -- far from stale -- the successor starts and presents its nonce.
    clock2 = FakeClock(T0 + timedelta(seconds=20))
    successor = make_worker(tmp_path, clock2, "run-2", successor_token="nonce-1", lifetime=30.0)
    res = successor.run()

    assert res.fail_closed is False
    assert L.read_lease(archive).worker_id == "run-2"
    assert L.read_lease(archive).generation == crashed.generation + 1
    assert res.cycles, "the recovered worker must actually capture"


def test_without_the_nonce_the_same_successor_would_have_failed_closed(tmp_path):
    """The control for the test above: this is what the token is buying us."""
    archive = tmp_path / "archive"
    archive.mkdir(parents=True, exist_ok=True)
    L.write_lease(
        archive,
        L.heartbeat(
            L.takeover(None, "run-1", T0),
            T0,
            expected_next_capture_at=T0 + timedelta(minutes=10),
            successor_token="nonce-1",
        ),
    )
    clock2 = FakeClock(T0 + timedelta(seconds=20))
    res = make_worker(tmp_path, clock2, "run-2", successor_token=None, lifetime=30.0).run()
    assert res.fail_closed is True


# -- 3. no recursive dispatch outside an active window ------------------------------------------


def test_outside_the_active_window_the_worker_captures_nothing(tmp_path):
    """A worker on an empty slate must not capture -- and so cannot spin a storm of successors."""
    clock = FakeClock(T0)
    dispatched: list[str] = []
    w = make_worker(tmp_path, clock, "run-1", dispatched=dispatched, schedule=[], lifetime=30.0)
    res = w.run()
    assert res.cycles, "it still ticks"
    assert not any(c.captured for c in res.cycles), "but it captures nothing off-slate"
    assert not any(c[:2] == ["nba", "capture"] for c in w._calls)


def test_a_worker_dispatches_at_most_two_successors_in_a_whole_lifetime(tmp_path):
    """Once early (crash insurance) and once at retirement (E2 re-verify). Never a storm."""
    clock = FakeClock(T0)
    dispatched: list[str] = []
    res = make_worker(tmp_path, clock, "run-1", dispatched=dispatched, lifetime=45.0).run()
    assert res.successor_dispatched is True
    assert len(dispatched) <= 2, f"dispatched {len(dispatched)} successors: {dispatched}"
    assert len(set(dispatched)) == len(dispatched), "each dispatch must carry a fresh nonce"


# -- 4. a transient failure must not end the worker ---------------------------------------------


def test_a_failing_capture_does_not_kill_the_loop(tmp_path):
    """Dying on a bad capture turns a transient API error into a multi-hour hole in the archive."""
    clock = FakeClock(T0)
    w = make_worker(tmp_path, clock, "run-1", capture_rc=1, lifetime=45.0)
    res = w.run()
    assert len(res.cycles) > 1, "the worker kept going after the failure"
    assert all(c.captured and not c.capture_ok for c in res.cycles)
    assert res.exit_reason.startswith("planned retirement")


# -- 5. retirement is planned, never a timeout --------------------------------------------------


def test_the_worker_retires_on_its_own_clock_before_its_deadline(tmp_path):
    clock = FakeClock(T0)
    lifetime = 60.0
    res = make_worker(tmp_path, clock, "run-1", lifetime=lifetime).run()
    assert "retirement" in res.exit_reason
    assert clock.now() <= T0 + timedelta(minutes=lifetime), (
        "the worker must stop before its planned exit, not after"
    )


def test_retirement_records_a_worker_status_artifact(tmp_path):
    clock = FakeClock(T0)
    res = make_worker(tmp_path, clock, "run-1", lifetime=45.0).run()
    status = json.loads((tmp_path / "archive" / "STATUS_worker.json").read_text())
    assert status["worker_id"] == "run-1"
    assert status["n_cycles"] == len(res.cycles)
    assert status["fail_closed"] is False


def test_cadence_tightens_as_the_worker_approaches_tip_off(tmp_path):
    """End-to-end: a lifetime that spans T-6h must show the cadence stepping down."""
    clock = FakeClock(TIP - timedelta(hours=6, minutes=30))
    res = make_worker(tmp_path, clock, "run-1", lifetime=400.0, capture_cost=60.0).run()
    cadences = [c.cadence_s for c in res.cycles]
    assert cadences[0] == 900.0, "starts on the far cadence"
    assert min(cadences) <= 300.0, "and reaches the final-30-minutes cadence"
    assert cadences == sorted(cadences, reverse=True), "cadence must only tighten, never loosen"


# -- 6. the worker must be a superset of the conductor, not a competitor ------------------------


def test_the_worker_runs_the_conductor_jobs_that_are_due(tmp_path):
    """The worker holds the archive concurrency group for hours; scheduled conductor runs queue
    behind it and are cancelled (E2). So whatever the conductor would have done, it must do."""
    clock = FakeClock(T0)
    w = make_worker(tmp_path, clock, "run-1", lifetime=30.0)
    w.decide_fn = lambda: {
        "context": True,
        "simulate": True,
        "settle": False,
        "evaluate": False,
        "discover": False,
    }
    res = w.run()
    ran = {part for cmd in w._calls for part in cmd[:2]}
    assert ["nba", "context"] in [c[:2] for c in w._calls]
    assert ["nba", "simulate"] in [c[:2] for c in w._calls]
    assert ["nba", "settle"] not in [c[:2] for c in w._calls], "jobs that are not due must not run"
    assert "nba" in ran
    assert all("context" in c.jobs_run and "simulate" in c.jobs_run for c in res.cycles)


def test_a_worker_that_fails_closed_runs_no_expensive_simulation(tmp_path):
    """Duplicate expensive simulations are one of the corruptions Phase 3 names explicitly."""
    clock = FakeClock(T0)
    archive = tmp_path / "archive"
    archive.mkdir(parents=True, exist_ok=True)
    L.write_lease(
        archive,
        L.heartbeat(L.takeover(None, "other", T0), T0, expected_next_capture_at=T0 + timedelta(minutes=10)),
    )
    w = make_worker(tmp_path, clock, "run-2", lifetime=30.0)
    w.decide_fn = lambda: {"simulate": True}
    res = w.run()
    assert res.fail_closed is True
    assert not any(c[:2] == ["nba", "simulate"] for c in w._calls)


def test_a_failing_slow_job_does_not_kill_the_worker(tmp_path):
    clock = FakeClock(T0)
    w = make_worker(tmp_path, clock, "run-1", lifetime=45.0)
    w.decide_fn = lambda: {"simulate": True}

    def run_fn(cmd, timeout):
        w._calls.append(cmd)
        if cmd[:2] == ["nba", "capture"]:
            clock.t += timedelta(seconds=180)
            return 0, ""
        if cmd[:2] == ["nba", "simulate"]:
            return 3, "simulate blew up"
        return 0, ""

    w.run_cmd = run_fn
    res = w.run()
    assert len(res.cycles) > 1
    assert all(c.jobs_run == [] for c in res.cycles), "the failed job is not recorded as done"


def test_a_retired_worker_releases_the_lease_for_its_successor(tmp_path):
    clock = FakeClock(T0)
    make_worker(tmp_path, clock, "run-1", lifetime=30.0).run()
    assert clock.now() > T0
    final = L.read_lease(tmp_path / "archive")
    assert final.released_at, "retirement must release the lease"
    # A watchdog bootstrap holding no successor nonce can take over immediately.
    assert L.may_write(final, "watchdog-run", clock.now())[0] is True


def test_retirement_writes_the_evidence_dashboard(tmp_path):
    """Phase 12 asks for a daily artifact; a ~5h handover cadence produces ~5 a day."""
    import json as _json

    clock = FakeClock(T0)
    make_worker(tmp_path, clock, "run-1", lifetime=30.0).run()
    report = _json.loads((tmp_path / "archive" / "EVIDENCE_HEALTH.json").read_text())
    assert "markets" in report and "stint_data" in report


def test_the_worker_pushes_to_the_branch_the_environment_names(tmp_path, monkeypatch):
    """The workflow declares `env: ARCHIVE_BRANCH`; a bare constant made that decorative.

    This is not hypothetical: a rehearsal aimed at a throwaway branch wrote to the real archive
    because the worker ignored the variable the workflow set.
    """
    from nba_edge.worker import run as R

    monkeypatch.setenv("ARCHIVE_BRANCH", "data-archive-scratch")
    clock = FakeClock(T0)
    w = make_worker(tmp_path, clock, "run-1", lifetime=30.0)
    w.run()
    push_calls = [c for c in w._calls if c and c[0] == "bash"]
    assert push_calls, "the worker must have attempted a push"
    assert all("data-archive-scratch" in c for c in push_calls), push_calls[0]

    monkeypatch.delenv("ARCHIVE_BRANCH")
    assert R.archive_branch() == R.DEFAULT_ARCHIVE_BRANCH


def test_the_worker_runs_the_same_commands_the_conductor_does():
    """The worker replaced the conductor's scheduled runs, so it must invoke the same things.

    conductor.yml's invocations are production-proven -- they captured every snapshot on the
    archive. If someone changes a flag there (say the order-book cap) and the worker keeps the old
    one, the two diverge silently and the difference only shows up in the data months later.
    """
    import re
    from pathlib import Path

    from nba_edge.worker.run import Worker

    yaml_text = Path(".github/workflows/conductor.yml").read_text()
    conductor = {}
    for m in re.finditer(r"\bnba (capture|context|simulate|settle|evaluate|discover)\b([^\n]*)", yaml_text):
        conductor[m.group(1)] = f"nba {m.group(1)}{m.group(2)}".strip()

    rendered = {
        name: " ".join(p.replace("ARCHIVE", "data/archive").replace("DATA", "data") for p in tmpl)
        for name, tmpl, _ in Worker.SLOW_JOBS
    }
    # Derived from the worker's own constant, NOT restated here. An earlier version of this test
    # hardcoded the capture string and so compared conductor.yml against a copy of itself -- it
    # passed happily while the worker used a different order-book cap.
    rendered["capture"] = " ".join(
        p.replace("ARCHIVE", "data/archive") for p in Worker.CAPTURE_CMD
    )

    assert set(conductor) == set(rendered), (
        f"conductor.yml has {sorted(conductor)}, worker has {sorted(rendered)}"
    )
    for job, expected in sorted(conductor.items()):
        assert rendered[job] == expected, f"{job}: worker runs {rendered[job]!r}, conductor runs {expected!r}"
