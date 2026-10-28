"""Capture reliability (Issue #53 audit): an OFF-by-default switch that publishes the capture before the cycle's slow jobs (lag ~214 s -> tens of seconds). Default behaviour is pinned unchanged."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import yaml

from nba_edge.worker.run import Worker

T0 = datetime(2026, 10, 3, 18, 0, tzinfo=UTC)
TIP = datetime(2026, 10, 3, 23, 0, tzinfo=UTC)
SCHEDULE = [{"start_time_utc": TIP.isoformat().replace("+00:00", "Z")}]
ROOT = Path(__file__).resolve().parents[1]


class Clock:
    def __init__(self, t):
        self.t = t

    def now(self):
        return self.t

    def sleep(self, s):
        self.t += timedelta(seconds=s)


def make(tmp_path, clock, *, capture_rcs=(0,), push_rcs=None, push_first=None, job_cost=200.0):
    """A worker whose commands are recorded in order: ('capture',) / ('job', name) / ('push', subject)."""
    log: list[tuple] = []
    caps = list(capture_rcs)
    pushes = list(push_rcs or [])

    def run_fn(cmd, timeout):
        if cmd[:2] == ["nba", "capture"]:
            log.append(("capture",))
            clock.t += timedelta(seconds=180)
            return (caps.pop(0) if len(caps) > 1 else caps[0]), "out"
        if cmd[0] == "bash" and cmd[1].endswith("archive_push.sh"):
            log.append(("push", cmd[4]))
            return (pushes.pop(0) if pushes else 0), ""
        log.append(("job", cmd[1]))
        clock.t += timedelta(seconds=job_cost / 2)
        return 0, ""

    (tmp_path / "archive").mkdir(parents=True, exist_ok=True)
    w = Worker(data_root=tmp_path / "data", archive_root=tmp_path / "archive", worker_id="run-1", now_fn=clock.now, sleep_fn=clock.sleep, run_fn=run_fn,
               schedule_fn=lambda: SCHEDULE, decide_fn=lambda: {}, lifetime_minutes=60.0, push_capture_first=push_first)
    return w, log


def one_cycle(w, clock):
    return w._one_cycle(clock.now())


def test_default_is_unchanged_one_push_after_the_jobs(tmp_path):
    clock = Clock(T0)
    w, log = make(tmp_path, clock)
    rec = one_cycle(w, clock)
    kinds = [e[0] for e in log]
    assert kinds[0] == "capture" and kinds[-1] == "push" and kinds.count("push") == 1                  # capture -> jobs -> one push at the end (today's behaviour)
    assert log[-1][1].startswith("capture: run-1 at ") and rec.capture_pushed_first is False


def test_push_first_publishes_the_capture_before_the_slow_jobs_and_keeps_one_capture_commit_per_tick(tmp_path):
    clock = Clock(T0)
    w, log = make(tmp_path, clock, push_first=True)
    rec = one_cycle(w, clock)
    assert log[0] == ("capture",) and log[1][0] == "push" and log[1][1].startswith("capture: run-1 at ")
    assert [e[0] for e in log[2:-1]] == ["job", "job"]                                                  # app_export, research_export run after the early push
    assert log[-1][0] == "push" and log[-1][1].startswith("cycle: run-1 at ")                          # the closing push never repeats the capture subject
    assert sum(1 for e in log if e[0] == "push" and e[1].startswith("capture:")) == 1
    assert rec.capture_pushed_first is True and rec.push_ok is True


def test_push_first_is_not_used_after_a_failed_capture_or_a_failed_early_push(tmp_path):
    clock = Clock(T0)
    w, log = make(tmp_path, clock, capture_rcs=(1,), push_first=True)
    rec = one_cycle(w, clock)
    assert [e for e in log if e[0] == "push"] == [("push", log[-1][1])] and log[-1][1].startswith("capture: ")        # a failed capture publishes nothing early
    assert rec.capture_ok is False and rec.capture_pushed_first is False
    clock2 = Clock(T0)
    w2, log2 = make(tmp_path / "b", clock2, push_rcs=[1, 0], push_first=True)                            # the early push fails -> the end-of-cycle push carries everything under the capture subject
    rec2 = one_cycle(w2, clock2)
    assert rec2.capture_pushed_first is False and log2[-1][1].startswith("capture: ") and rec2.push_ok is True


def test_the_workflow_passes_the_switch_and_defaults_it_off():
    wf = yaml.safe_load((ROOT / ".github/workflows/capture_worker.yml").read_text())
    env = next(s for s in wf["jobs"]["worker"]["steps"] if s.get("id") == "worker")["env"]
    assert env["CAPTURE_PUSH_FIRST"] == "${{ vars.CAPTURE_PUSH_FIRST || '0' }}"
    assert wf["concurrency"]["group"] == "conductor-archive" and wf["concurrency"]["cancel-in-progress"] is False        # single-writer enforcement untouched


def test_the_env_var_is_the_default_source_of_the_switch(tmp_path, monkeypatch):
    monkeypatch.setenv("CAPTURE_PUSH_FIRST", "1")
    assert Worker(data_root=tmp_path, archive_root=tmp_path, worker_id="x").push_capture_first is True
    monkeypatch.setenv("CAPTURE_PUSH_FIRST", "0")
    assert Worker(data_root=tmp_path, archive_root=tmp_path, worker_id="x").push_capture_first is False
    monkeypatch.delenv("CAPTURE_PUSH_FIRST")
    assert Worker(data_root=tmp_path, archive_root=tmp_path, worker_id="x").push_capture_first is False
