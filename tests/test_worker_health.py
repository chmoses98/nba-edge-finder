"""The capture worker's shift verdict: green for no-work and recovered shifts, red only when broken.

Before this, `nba worker` exited 0 unconditionally. A shift in which every capture failed, or
settlement failed on every retry, or the final archive push was rejected, finished exactly as green
as a quiet off-season shift -- and the workflow's "preserve the archive if the final push failed"
step could never fire. These tests drive whole simulated shifts against a fake clock and fake
commands; nothing depends on the real calendar, the network, or committed archive data.
"""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import yaml

from nba_edge.cli import publish_worker_health
from nba_edge.worker import health as H
from nba_edge.worker import lease as L
from nba_edge.worker.run import Worker

T0 = datetime(2026, 10, 3, 18, 0, tzinfo=UTC)
TIP = datetime(2026, 10, 3, 23, 0, tzinfo=UTC)
SLATE = [{"start_time_utc": TIP.isoformat().replace("+00:00", "Z")}]
WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "capture_worker.yml"


class Clock:
    def __init__(self, start: datetime) -> None:
        self.t = start

    def now(self) -> datetime:
        return self.t

    def sleep(self, s: float) -> None:
        self.t += timedelta(seconds=s)


def shift(
    tmp_path,
    *,
    capture_rcs=None,
    job_rcs=None,
    final_push_rc=0,
    schedule=SLATE,
    decision=None,
    dispatch=None,
    worker_id="run-1",
    lifetime=60.0,
):
    """Run one simulated shift. ``capture_rcs`` is consumed per capture attempt (last value repeats)."""
    clock = Clock(T0)
    capture_rcs = list(capture_rcs or [0])
    job_rcs = job_rcs or {}
    calls: list[list[str]] = []

    def run_fn(cmd, timeout):
        calls.append(cmd)
        if cmd[:2] == ["nba", "capture"]:
            clock.t += timedelta(seconds=60)
            return (capture_rcs.pop(0) if len(capture_rcs) > 1 else capture_rcs[0]), "capture"
        if cmd[0] == "bash" and cmd[1].endswith("archive_push.sh"):
            return (final_push_rc if "retired after" in cmd[-1] else 0), "push"
        if cmd[0] == "nba" and cmd[1] in job_rcs:
            return job_rcs[cmd[1]], f"{cmd[1]} output"
        return 0, ""

    archive = tmp_path / "archive"
    archive.mkdir(parents=True, exist_ok=True)
    w = Worker(
        data_root=tmp_path / "data",
        archive_root=archive,
        worker_id=worker_id,
        now_fn=clock.now,
        sleep_fn=clock.sleep,
        run_fn=run_fn,
        dispatch_fn=dispatch,
        schedule_fn=lambda: schedule,
        # Always explicit: the default reads the REAL clock, which would make these tests depend on
        # the date they happen to run.
        decide_fn=lambda: dict(decision or {}),
        lifetime_minutes=lifetime,
    )
    res = w.run()
    return res, archive, calls


# -- green: nothing to do ------------------------------------------------------------------------


def test_an_offseason_shift_with_nothing_due_is_not_applicable_and_green(tmp_path):
    res, archive, calls = shift(tmp_path, schedule=[], decision={})
    assert res.cycles and not any(c.captured for c in res.cycles)
    assert res.health["state"] == H.NOT_APPLICABLE
    assert res.health["disposition"] == "NO_WORK"
    status = json.loads((archive / "STATUS_worker.json").read_text())
    assert status["health"]["state"] == H.NOT_APPLICABLE, "the verdict is persisted in the existing status"


def test_a_fail_closed_stand_down_is_not_applicable(tmp_path):
    archive = tmp_path / "archive"
    archive.mkdir(parents=True)
    L.write_lease(
        archive,
        L.heartbeat(L.takeover(None, "other", T0), T0, expected_next_capture_at=T0 + timedelta(minutes=10)),
    )
    res, _, _ = shift(tmp_path, worker_id="run-2")
    assert res.fail_closed is True
    assert res.health["state"] == H.NOT_APPLICABLE
    assert res.health["disposition"] == "STOOD_DOWN"


def test_a_clean_slate_shift_is_healthy(tmp_path):
    res, _, _ = shift(tmp_path)
    assert any(c.captured for c in res.cycles)
    assert res.health["state"] == H.HEALTHY
    assert res.health["streams"]["capture"]["failed"] == 0


# -- yellow: recorded, never red -----------------------------------------------------------------


def test_a_transient_capture_failure_that_recovers_is_degraded_not_failed(tmp_path):
    res, _, _ = shift(tmp_path, capture_rcs=[1, 0])
    assert res.health["state"] == H.DEGRADED
    assert res.health["disposition"] == "RECOVERED_AFTER_RETRY"
    assert res.health["streams"]["capture"]["disposition"] == "RECOVERED_AFTER_RETRY"
    assert res.health["failures"] == []


def test_a_failure_at_shift_end_before_the_retry_budget_is_spent_is_degraded(tmp_path):
    res0, _, _ = shift(tmp_path / "probe")
    n = sum(1 for c in res0.cycles if c.captured)
    assert n > H.RETRY_BUDGET, "the scenario needs enough attempts to be meaningful"
    rcs = [0] * (n - (H.RETRY_BUDGET - 1)) + [1] * (H.RETRY_BUDGET - 1)
    res, _, _ = shift(tmp_path / "real", capture_rcs=rcs)
    cap = res.health["streams"]["capture"]
    assert cap["trailing_failures"] == H.RETRY_BUDGET - 1
    assert cap["disposition"] == "FAILING_RETRY_PENDING"
    assert res.health["state"] == H.DEGRADED


def test_a_research_job_failing_every_tick_is_degraded_never_failed(tmp_path):
    res, _, _ = shift(tmp_path, decision={"matchup_shadow": True}, job_rcs={"matchup-shadow": 2})
    assert all("matchup_shadow" in c.jobs_failed for c in res.cycles)
    assert res.health["streams"]["matchup_shadow"]["disposition"] == "FAILED_AFTER_RETRY"
    assert res.health["state"] == H.DEGRADED, "research must never turn the capture worker red"


def test_coverage_alarms_from_this_shifts_capture_are_degraded(tmp_path):
    archive = tmp_path / "archive"
    archive.mkdir(parents=True)
    (archive / "STATUS_capture.json").write_text(
        json.dumps({"run_id": "run-1", "alarms": ["series on the board with no ontology entry: ['KXNEW']"]})
    )
    res, _, _ = shift(tmp_path)
    assert res.health["state"] == H.DEGRADED
    assert any("KXNEW" in w for w in res.health["warnings"])


def test_a_stale_capture_status_from_another_run_cannot_colour_this_shift(tmp_path):
    archive = tmp_path / "archive"
    archive.mkdir(parents=True)
    (archive / "STATUS_capture.json").write_text(
        json.dumps({"run_id": "some-earlier-run", "alarms": ["series on the board with no ontology entry"]})
    )
    res, _, _ = shift(tmp_path, schedule=[], decision={})
    assert res.health["state"] == H.NOT_APPLICABLE


# -- red: actionable after bounded recovery ------------------------------------------------------


def test_capture_failing_on_every_attempt_is_failed(tmp_path):
    res, _, _ = shift(tmp_path, capture_rcs=[1])
    assert res.health["streams"]["capture"]["attempts"] >= H.RETRY_BUDGET
    assert res.health["state"] == H.FAILED
    assert any(f.startswith("capture:") for f in res.health["failures"])


def test_settlement_failing_on_every_retry_is_failed_and_recorded(tmp_path):
    res, archive, _ = shift(tmp_path, decision={"settle": True}, job_rcs={"settle": 5})
    assert all(c.jobs_failed == ["settle"] for c in res.cycles), "the failed job is now recorded"
    assert res.health["state"] == H.FAILED
    status = json.loads((archive / "STATUS_worker.json").read_text())
    assert status["health"]["state"] == H.FAILED
    assert status["cycles"][0]["jobs_failed"] == ["settle"]


def test_a_rejected_final_push_is_failed_and_the_local_status_says_so(tmp_path):
    res, archive, _ = shift(tmp_path, final_push_rc=4)
    assert res.final_push_ok is False
    assert res.health["state"] == H.FAILED
    assert any("retirement" in f for f in res.health["failures"])
    local = json.loads((archive / "STATUS_worker.json").read_text())
    assert local["final_push_ok"] is False and local["health"]["state"] == H.FAILED


def test_a_published_status_is_graded_as_published(tmp_path):
    """Every copy of STATUS_worker.json that reaches the branch was carried by a successful push."""
    res, archive, _ = shift(tmp_path)
    status = json.loads((archive / "STATUS_worker.json").read_text())
    assert status["final_push_ok"] is True and status["health"]["state"] == res.health["state"]


def test_a_chain_that_cannot_renew_is_failed(tmp_path):
    res, _, _ = shift(tmp_path, dispatch=lambda token: False)
    assert res.successor_dispatch_attempts == 2
    assert res.successor_dispatched is False
    assert res.health["state"] == H.FAILED


def test_a_worker_without_a_dispatcher_is_not_judged_on_renewal(tmp_path):
    res, _, _ = shift(tmp_path, dispatch=None)
    assert res.successor_dispatch_attempts == 0
    assert res.health["state"] == H.HEALTHY


# -- surfacing ------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "health,final,state,push",
    [
        ({"state": "FAILED", "disposition": "FAILED_AFTER_RETRY", "failures": ["capture: x"],
          "warnings": [], "reasons": ["capture: x"], "streams": {}}, False, "FAILED", "failed"),
        ({"state": "DEGRADED", "disposition": "DEGRADED", "failures": [], "warnings": ["w"],
          "reasons": ["w"], "streams": {}}, True, "DEGRADED", "ok"),
        ({"state": "NOT_APPLICABLE", "disposition": "STOOD_DOWN", "failures": [], "warnings": [],
          "reasons": ["stood down"], "streams": {}}, None, "NOT_APPLICABLE", "skipped"),
    ],
)
def test_publish_writes_summary_outputs_and_annotations(tmp_path, capsys, health, final, state, push):
    out, summ = tmp_path / "out", tmp_path / "summary"
    result = {"worker_id": "w", "generation": 1, "exit_reason": "x", "cycles": [], "health": health,
              "final_push_ok": final}
    got = publish_worker_health(result, {"GITHUB_OUTPUT": str(out), "GITHUB_STEP_SUMMARY": str(summ)})
    assert got == state
    assert f"health_state={state}" in out.read_text() and f"final_push={push}" in out.read_text()
    assert state in summ.read_text()
    printed = capsys.readouterr().out
    assert ("::error" in printed) == (state == "FAILED")
    assert ("::warning" in printed) == (state == "DEGRADED")


# -- the workflow: one enforcement point, mapped to the verdict ----------------------------------


def _steps():
    return yaml.safe_load(WORKFLOW.read_text())["jobs"]["worker"]["steps"]


@pytest.mark.parametrize(
    "state,rc",
    [("HEALTHY", 0), ("NOT_APPLICABLE", 0), ("DEGRADED", 0), ("FAILED", 1), ("", 1), ("bogus", 1)],
)
def test_the_enforcement_step_fails_only_for_failed_or_a_missing_verdict(tmp_path, state, rc):
    step = next(s for s in _steps() if s.get("name") == "Enforce shift health")
    script = tmp_path / "enforce.sh"
    script.write_text(step["run"])
    r = subprocess.run(["bash", str(script)], env={"HEALTH_STATE": state, "PATH": "/usr/bin:/bin"},
                       capture_output=True, text=True)
    assert r.returncode == rc, r.stdout + r.stderr


def test_the_worker_step_reports_and_exactly_one_step_enforces():
    steps = _steps()
    worker = next(s for s in steps if s.get("name") == "Run the worker")
    assert worker.get("id") == "worker" and worker.get("continue-on-error") is not True
    enforce = [s for s in steps if "health_state" in str(s.get("env", ""))]
    assert len(enforce) == 1, "one enforcement point, not a cascade of red steps"
    assert "steps.worker.outcome == 'success'" in enforce[0]["if"], (
        "a crashed worker is already red; enforcing again would double-report it"
    )
    preserve = next(s for s in steps if str(s.get("name", "")).startswith("Preserve the archive"))
    assert "final_push == 'failed'" in preserve["if"], "the artifact must survive a rejected final push"
    assert preserve["if"].strip() != "failure()", "bare failure() can never see a reported push failure"
