"""The self-renewing capture worker: one long-lived run that captures on a cadence and hands over.

Architecture, and why it is this shape rather than the obvious one:

GitHub's scheduler does not deliver. Measured on this repository over six days, ``*/10`` cron
produced 34 conductor runs against 864 expected (~3.9%), with observed gaps of 2h18m and 3h09m
between consecutive "ten-minute" wakes. The dominant failure is OMISSION, not lateness, so no
amount of cron tuning fixes it. The fix is to stop asking cron for cadence: one long-lived run
owns the cadence internally, and cron is demoted to a bootstrap of last resort.

Every structural decision below is backed by a chainlab experiment run against this repository:

  E0  A workflow file that exists only on a non-default branch is NOT dispatchable (404), while
      the same token dispatches a file present on the default branch (204). => The worker workflow
      must be merged to main before it can renew itself at all.
  E1  A run CAN dispatch its own successor with GITHUB_TOKEN (``actions: write``), and the
      successor really runs. GitHub's recursion suppression does not extend to workflow_dispatch.
      Handover measured at ~7s from parent dispatch to successor job start.
  E2  Within one concurrency group GitHub keeps at most one run IN PROGRESS and at most one run
      PENDING; queueing a third cancels the previously pending one. Three queued runs collapsed to
      exactly one, and two writers never coexisted.

E2 is the load-bearing one. It means a successor queued early can be cancelled by a watchdog that
fires later -- which would be fatal if the watchdog were a different workflow. So the watchdog
dispatches THIS SAME workflow: the single pending slot then always holds a worker, and it does not
matter who put it there. Cancellation becomes a substitution rather than a break.

Ownership is therefore enforced in two layers. The concurrency group is the real guarantee (E2:
never two in progress). The lease is the evidence, the cross-workflow reach, and the fail-closed
check -- see ``worker/lease.py``.
"""

from __future__ import annotations

import json
import secrets
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from nba_edge.timeutil import iso, utcnow
from nba_edge.worker import lease as lease_mod
from nba_edge.worker.plan import (
    plan_cycle,
    planned_exit,
    should_retire,
    tip_times,
)

ARCHIVE_BRANCH = "data-archive"


@dataclass
class CycleRecord:
    """What one iteration actually did -- the raw material for the Phase 4 cadence report."""

    started_at: str
    jobs_run: list[str]
    captured: bool
    capture_ok: bool
    push_ok: bool
    duration_s: float
    cadence_s: float
    hours_to_next_tip: float | None
    reason: str


@dataclass
class WorkerResult:
    worker_id: str
    generation: int
    exit_reason: str
    cycles: list[CycleRecord] = field(default_factory=list)
    successor_dispatched: bool = False
    fail_closed: bool = False

    def to_json(self) -> str:
        return (
            json.dumps(
                {
                    "worker_id": self.worker_id,
                    "generation": self.generation,
                    "exit_reason": self.exit_reason,
                    "successor_dispatched": self.successor_dispatched,
                    "fail_closed": self.fail_closed,
                    "n_cycles": len(self.cycles),
                    "n_captured": sum(1 for c in self.cycles if c.captured),
                    "n_capture_failed": sum(1 for c in self.cycles if c.captured and not c.capture_ok),
                    "cycles": [vars(c) for c in self.cycles],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )


def _default_run(cmd: list[str], timeout: float) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "")[-4000:] + (p.stderr or "")[-4000:]
    except subprocess.TimeoutExpired:
        return 124, f"timeout after {timeout}s: {' '.join(cmd)}"
    except OSError as e:  # noqa: BLE001 - a missing binary must not kill the worker
        return 127, f"{e}"


def dispatch_successor_via_api(repo: str, ref: str, token: str, workflow: str, successor_token: str) -> bool:
    """Queue the next worker. Returns True only on GitHub's 204 (accepted).

    204 means ACCEPTED, not "a run exists" -- E2 showed an accepted dispatch can still lose its
    pending slot to a later one. The caller must verify, not trust this boolean alone.
    """
    import urllib.error
    import urllib.request

    body = json.dumps({"ref": ref, "inputs": {"successor_token": successor_token}}).encode()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/dispatches",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status == 204
    except urllib.error.HTTPError as e:
        print(f"worker: successor dispatch failed HTTP {e.code}: {e.read()[:300]!r}")
        return False
    except OSError as e:
        print(f"worker: successor dispatch failed: {e}")
        return False


class Worker:
    """One long-lived capture run.

    Every side effect is injected so the race and rollover tests can drive a whole simulated
    lifetime -- takeovers, crashes, fail-closed refusals -- without a runner or a network.
    """

    def __init__(
        self,
        *,
        data_root: Path,
        archive_root: Path,
        worker_id: str,
        successor_token: str | None = None,
        now_fn: Callable[[], datetime] = utcnow,
        sleep_fn: Callable[[float], None] = time.sleep,
        run_fn: Callable[[list[str], float], tuple[int, str]] = _default_run,
        dispatch_fn: Callable[[str], bool] | None = None,
        schedule_fn: Callable[[], list[dict]] | None = None,
        decide_fn: Callable[[], dict] | None = None,
        lifetime_minutes: float | None = None,
    ) -> None:
        self.data_root = Path(data_root)
        self.archive_root = Path(archive_root)
        self.worker_id = worker_id
        self.successor_token = successor_token
        self.now = now_fn
        self.sleep = sleep_fn
        self.run_cmd = run_fn
        self.dispatch_fn = dispatch_fn
        self.schedule_fn = schedule_fn or self._read_schedule
        self.decide_fn = decide_fn or self._decide
        self.lifetime_minutes = lifetime_minutes
        self.result: WorkerResult | None = None

    # -- archive I/O -------------------------------------------------------------------------
    def _read_schedule(self) -> list[dict]:
        from nba_edge.archive.ledger import Ledger

        try:
            from nba_edge.workflows.conductor import _latest_schedule

            return _latest_schedule(Ledger(self.archive_root))
        except Exception as e:  # noqa: BLE001 - a bad snapshot must degrade, not crash the worker
            print(f"worker: could not read schedule ({e}); treating slate as unknown")
            return []

    def _decide(self) -> dict:
        """The conductor's own decision, reused rather than reimplemented."""
        try:
            from nba_edge.workflows.conductor import decide_now

            return decide_now(self.data_root)
        except Exception as e:  # noqa: BLE001 - a bad breadcrumb must not stop capture
            print(f"worker: could not read the conductor decision ({e}); capture-only this cycle")
            return {}

    def _push(self, message: str) -> bool:
        script = Path(__file__).resolve().parents[3] / "scripts" / "archive_push.sh"
        if not script.exists():
            print(f"worker: push script missing at {script}")
            return False
        rc, out = self.run_cmd(["bash", str(script), str(self.archive_root), ARCHIVE_BRANCH, message], 300)
        if rc != 0:
            print(f"worker: archive push failed rc={rc}: {out[-600:]}")
        return rc == 0

    # -- lifecycle ---------------------------------------------------------------------------
    def acquire(self) -> tuple[bool, str, int]:
        """Take the lease, or refuse to run. Returns (ok, reason, generation)."""
        now = self.now()
        current = lease_mod.read_lease(self.archive_root)
        ok, why = lease_mod.may_write(current, self.worker_id, now, successor_token=self.successor_token)
        if not ok:
            return False, why, current.generation if current else 0
        new = lease_mod.takeover(current, self.worker_id, now)
        exit_at = planned_exit(now, self.lifetime_minutes) if self.lifetime_minutes else planned_exit(now)
        new = lease_mod.heartbeat(new, now, planned_exit_at=exit_at, note=why)
        lease_mod.write_lease(self.archive_root, new)
        return True, why, new.generation

    def run(self) -> WorkerResult:
        started = self.now()
        exit_at = (
            planned_exit(started, self.lifetime_minutes) if self.lifetime_minutes else planned_exit(started)
        )

        ok, why, gen = self.acquire()
        res = WorkerResult(worker_id=self.worker_id, generation=gen, exit_reason="")
        self.result = res
        if not ok:
            # Fail closed. Exit 0, not an error: another worker legitimately owns the archive and
            # the correct behaviour is to stand down quietly rather than to race it.
            res.exit_reason = f"fail-closed: {why}"
            res.fail_closed = True
            print(f"worker: {res.exit_reason}")
            return res
        print(f"worker {self.worker_id} generation {gen} acquired lease ({why}); planned exit {iso(exit_at)}")
        self._push(f"worker: {self.worker_id} gen {gen} acquired lease")

        # Queue the successor NOW rather than at retirement. A crash at any later point then still
        # leaves a worker in the pending slot, which starts the instant this run leaves the group.
        # E2 says a later dispatch can cancel it -- that is why retirement re-verifies below.
        self._dispatch_successor(res, "early (crash insurance)")

        last_cost = 0.0
        while True:
            now = self.now()
            if should_retire(now, exit_at, last_cost):
                res.exit_reason = f"planned retirement at {iso(now)} (exit_at {iso(exit_at)})"
                break
            rec = self._one_cycle(now)
            res.cycles.append(rec)
            last_cost = rec.duration_s
            now2 = self.now()
            sleep_s = max(0.0, rec.cadence_s - (now2 - now).total_seconds())
            if should_retire(now2, exit_at, sleep_s):
                res.exit_reason = "planned retirement before next cadence tick"
                break
            if sleep_s:
                self.sleep(sleep_s)

        self._retire(res, exit_at)
        return res

    def _one_cycle(self, now: datetime) -> CycleRecord:
        tips = tip_times(self.schedule_fn())
        cyc = plan_cycle(now, tips)
        captured = capture_ok = push_ok = False
        if cyc.should_capture:
            captured = True
            rc, out = self.run_cmd(
                ["nba", "capture", "--out", str(self.archive_root), "--orderbook", "--max-orderbooks", "300"],
                600,
            )
            capture_ok = rc == 0
            if not capture_ok:
                # One bad capture must never end the worker. The archive is append-only and the
                # next tick is minutes away; dying here would convert a transient API error into a
                # multi-hour hole, which is precisely the failure this design exists to remove.
                print(f"worker: capture failed rc={rc}: {out[-600:]}")

        # The worker owns the archive's concurrency group for hours, so every scheduled conductor
        # run queues behind it and is cancelled (E2). Whatever the conductor would have decided to
        # do, the worker must therefore do itself -- otherwise simulate/settle/evaluate/discover
        # silently stop for as long as a worker is alive. Each is age-gated by decide(), so this is
        # the same cadence they had before, not extra work.
        jobs_run = self._run_due_jobs()

        cur = lease_mod.read_lease(self.archive_root)
        if cur is not None:
            ok, why = lease_mod.may_write(
                cur, self.worker_id, self.now(), successor_token=self.successor_token
            )
            if not ok:
                print(f"worker: lost the lease mid-flight ({why}); not writing mutable state")
            else:
                lease_mod.write_lease(
                    self.archive_root,
                    lease_mod.heartbeat(
                        cur,
                        self.now(),
                        last_capture_at=self.now() if capture_ok else None,
                        expected_next_capture_at=cyc.next_cycle_at,
                    ),
                )
        push_ok = self._push(f"capture: {self.worker_id} at {iso(now)}")
        return CycleRecord(
            started_at=iso(now),
            jobs_run=jobs_run,
            captured=captured,
            capture_ok=capture_ok,
            push_ok=push_ok,
            duration_s=(self.now() - now).total_seconds(),
            cadence_s=cyc.cadence_seconds,
            hours_to_next_tip=cyc.hours_to_next_tip,
            reason=cyc.reason,
        )

    # The slow jobs, in dependency order, with the command each runs and how long it may take.
    # Ordered deliberately: context before simulate (a simulation wants the freshest roster), and
    # settle before evaluate (evaluation scores what settlement just resolved).
    SLOW_JOBS = (
        ("context", ["nba", "context", "--out", "ARCHIVE"], 600.0),
        ("simulate", ["nba", "simulate", "--data", "DATA", "--out", "ARCHIVE"], 2400.0),
        ("settle", ["nba", "settle", "--data", "DATA", "--out", "ARCHIVE"], 1200.0),
        ("evaluate", ["nba", "evaluate", "--data", "DATA", "--out", "ARCHIVE/eval"], 900.0),
        (
            "discover",
            [
                "nba",
                "discover",
                "--out",
                "ARCHIVE/catalog",
                "--statuses",
                "open,unopened",
                "--max-pages",
                "10",
            ],
            1200.0,
        ),
    )

    def _run_due_jobs(self) -> list[str]:
        decision = self.decide_fn() or {}
        done = []
        for name, template, budget in self.SLOW_JOBS:
            if not decision.get(name):
                continue
            cmd = [
                part.replace("ARCHIVE", str(self.archive_root)).replace("DATA", str(self.data_root))
                for part in template
            ]
            rc, out = self.run_cmd(cmd, budget)
            if rc == 0:
                done.append(name)
            else:
                # Same reasoning as a failed capture: one bad job must never end the worker.
                print(f"worker: job {name} failed rc={rc}: {out[-400:]}")
        return done

    def _dispatch_successor(self, res: WorkerResult, label: str) -> None:
        if self.dispatch_fn is None:
            print(f"worker: no dispatcher configured; skipping successor ({label})")
            return
        now = self.now()
        cur = lease_mod.read_lease(self.archive_root)
        thrash, why = lease_mod.thrashing(cur, now)
        if thrash and res.successor_dispatched:
            print(f"worker: refusing successor -- {why}")
            return
        token = secrets.token_hex(16)
        if not self.dispatch_fn(token):
            print(f"worker: successor dispatch NOT accepted ({label})")
            return
        res.successor_dispatched = True
        if cur is not None:
            lease_mod.write_lease(
                self.archive_root,
                lease_mod.heartbeat(cur, now, successor_token=token, successor_dispatched_at=now),
            )
        print(f"worker: successor dispatched {label}, token {token[:8]}...")

    def _retire(self, res: WorkerResult, exit_at: datetime) -> None:
        """Hand over. Re-dispatch, because E2 says the early successor may have been cancelled.

        Re-dispatching unconditionally is correct rather than wasteful: a duplicate dispatch
        collapses into the single pending slot (E2), so the cost of being wrong in this direction
        is nothing, while the cost of being wrong in the other direction is a broken chain.
        """
        self._dispatch_successor(res, "at retirement (re-verify)")
        cur = lease_mod.read_lease(self.archive_root)
        if cur is not None and cur.worker_id == self.worker_id:
            lease_mod.write_lease(
                self.archive_root,
                lease_mod.heartbeat(
                    cur, self.now(), released_at=self.now(), note=f"retired: {res.exit_reason}"
                ),
            )
        (self.archive_root / "STATUS_worker.json").write_text(res.to_json())
        self._push(f"worker: {self.worker_id} retired after {len(res.cycles)} cycles")
        print(f"worker: {res.exit_reason}")
