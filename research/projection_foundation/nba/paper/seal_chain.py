"""The long-lived, self-renewing sealer of the Issue #53 sealed pre-tip ledger (RESEARCH ONLY). Standard library only: the heavy work happens in subprocesses.

Why a chain and not a 5-minute cron. This repository MEASURED its scheduled-workflow delivery: `*/10` produced 34 runs against 864 expected (3.9%), with gaps of 2-3 hours
(`capture_worker.yml`, `nba-ticker.yml`). A seal window is 40 minutes wide, so a cron-driven sealer would simply miss most games. The pattern that works here is a job that
owns the cadence itself and dispatches its successor (`workflow_dispatch` is exempt from recursion suppression); cron is demoted to a bootstrap of last resort.

One run (this module, ~280 minutes):
  1. loop every `interval_s`: mount the ledger (fresh) and the schedule context (depth-1, ~1 s); evaluate the gate IN PROCESS (`seal_windows`, no dependency installed);
  2. a window is OPEN -> mount the boards / forecasts, run `exec_seal seal`; a window CLOSED UNSEALED -> `exec_seal watch` writes the MISSED marker (red run);
  3. live runs only: export the new files and publish them through the Git Data API (`ledger_remote`: server-side commit time, fast-forward only, additions only), then
     verify durability and the deadline against the SERVER commit time;
  4. after `successor_at_min` dispatch the successor (only if the gate says the chain is still needed); stop at `max_minutes`, or as soon as nothing is open, closing or opening
     within the horizon (an idle day costs only a delivered cron's ~15 s gate).
Dry runs (pull requests, manual dry dispatch) perform exactly one iteration and never publish or dispatch.

The publish token (`PUBLISH_TOKEN`) is handed ONLY to `ledger_remote publish` / `gh workflow run`; the sealing subprocesses never see it.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Any, Callable

try:
    from . import seal_windows as SW
except ImportError:                    # run as a script path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import seal_windows as SW  # type: ignore

UTC = timezone.utc
HERE = os.path.dirname(os.path.abspath(__file__))
PF = os.path.abspath(os.path.join(HERE, "..", ".."))
CI = os.path.join(PF, "scripts", "exec_seal_ci.sh")
LEDGER_REMOTE = os.path.join(HERE, "ledger_remote.py")
TOKEN_VAR = "PUBLISH_TOKEN"


def sh(cmd: list[str], *, env: dict | None = None, cwd: str | None = None, capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, env=env, cwd=cwd, text=True, capture_output=capture)


def clean_env() -> dict[str, str]:
    """Environment of every subprocess that is NOT the publisher: no token."""
    return {k: v for k, v in os.environ.items() if k not in (TOKEN_VAR, "GH_TOKEN", "GITHUB_TOKEN")}


def token_env() -> dict[str, str]:
    e = clean_env()
    e["GH_TOKEN"] = os.environ.get(TOKEN_VAR, "")
    return e


class Chain:
    def __init__(self, a: argparse.Namespace, *, run: Callable = sh, clock: Callable[[], datetime] | None = None, sleep: Callable[[float], None] = time.sleep,
                 mono: Callable[[], float] = time.monotonic):
        self.a, self.run, self.sleep, self.mono = a, run, sleep, mono
        self.clock = clock or (lambda: datetime.now(UTC).replace(microsecond=0))
        self.work = a.work
        self.seals = os.path.join(a.work, "seals")
        self.m = os.path.join(a.work, "m")
        self.new = os.path.join(a.work, "new")
        self.study = SW.load_study()
        self.errors: list[str] = []
        self.missed: list[str] = []
        self.published: list[dict] = []
        self.successor_sent = False
        self.log: list[str] = []

    # -------------------------------------------------------------------------------------------------- helpers
    def say(self, msg: str) -> None:
        line = f"{self.clock().strftime('%H:%M:%SZ')} {msg}"
        self.log.append(line)
        print(line, flush=True)

    def now(self) -> datetime:
        return SW.parse_ts(self.a.now) if (self.a.dry_run and self.a.now) else self.clock()

    def now_arg(self) -> list[str]:
        return ["--now", self.a.now] if (self.a.dry_run and self.a.now) else []

    def py(self, *args: str, token: bool = False) -> subprocess.CompletedProcess:
        return self.run([sys.executable, *args], env=token_env() if token else clean_env(), cwd=PF)

    def err(self, msg: str) -> None:
        self.errors.append(msg)
        print(f"::error::{msg}", flush=True)

    # -------------------------------------------------------------------------------------------------- one iteration
    def mount(self) -> bool:
        if self.a.dry_run:                                                  # a rehearsal runs on an EMPTY ledger: it neither reads nor depends on the real one
            shutil.rmtree(self.seals, ignore_errors=True)
            os.makedirs(self.seals)
            self.run(["git", "init", "-q", self.seals], env=clean_env(), cwd=self.a.repo_root)
            steps = [["mount_context", self.m] + ([self.a.now] if self.a.now else [])]
        else:
            steps = [["mount_seals", self.seals], ["mount_context", self.m]]
        for step in steps:
            r = self.run(["bash", CI, *step], env=clean_env(), cwd=self.a.repo_root)
            if getattr(r, "returncode", 1) != 0:
                self.err(f"mount failed: {step[0]} (rc={getattr(r, 'returncode', '?')})")
                return False
        return True

    def gate(self) -> dict[str, Any]:
        return SW.gate(os.path.join(self.m, "data-archive"), self.seals, self.now(), self.study, self.a.horizon_h)

    def seal_args(self) -> list[str]:
        d = os.path.join(self.m, "data-archive")
        return ["--archive", os.path.join(self.m, "projection-data"), "--market", d, "--context", d, "--board-repo", d, "--seals", self.seals, "--code-repo", self.a.repo_root]

    def seal(self) -> None:
        r = self.run(["bash", CI, "mount_inputs", self.m] + ([self.a.now] if (self.a.dry_run and self.a.now) else []), env=clean_env(), cwd=self.a.repo_root)
        if getattr(r, "returncode", 1) != 0:
            self.err(f"mount_inputs failed (rc={getattr(r, 'returncode', '?')}); retried on the next iteration while the window is open")
            return
        rep = os.path.join(self.work, "seal_report.json")
        cmd = ["-m", "nba.paper.exec_seal", "seal", *self.seal_args(), "--out", rep, *self.now_arg()] + (["--dry-run"] if self.a.dry_run else [])
        r = self.py(*cmd)
        if getattr(r, "returncode", 1) != 0:
            self.err(f"exec_seal seal rc={getattr(r, 'returncode', '?')} (a game that errored is retried on the next iteration; none is sealed half-done)")

    def watch(self) -> None:
        d = os.path.join(self.m, "data-archive")
        cmd = ["-m", "nba.paper.exec_seal", "watch", "--context", d, "--seals", self.seals, *self.now_arg()] + (["--dry-run"] if self.a.dry_run else [])
        r = self.py(*cmd)
        rc = getattr(r, "returncode", 1)
        if rc == 3:
            self.missed.append(self.now().isoformat())
            self.err("a seal window closed unsealed: MISSED marker written (the game is uncounted, never sealed late)")
        elif rc != 0:
            self.err(f"exec_seal watch rc={rc}")

    def publish(self) -> None:
        shutil.rmtree(self.new, ignore_errors=True)                         # never re-publish a previous iteration's leftovers
        r = self.py(LEDGER_REMOTE, "export", "--seals", self.seals, "--dir", self.new)
        if getattr(r, "returncode", 1) != 0:
            self.err(f"export refused (rc={getattr(r, 'returncode', '?')}): the worktree holds changes that are not additions")
            return
        out = os.path.join(self.work, "publish.json")
        report = os.path.join(self.work, "seal_report.json")
        r = self.py(LEDGER_REMOTE, "publish", "--dir", self.new, "--report", report, "--out", out, "--repo", self.a.repo, token=True)
        rc = getattr(r, "returncode", 1)
        if os.path.exists(out):
            try:
                self.published.append(json.load(open(out)))
            except ValueError:
                pass
        if rc == 0:
            return
        self.err({1: "publish: NOT DURABLE or API error", 5: "publish: a seal was committed after its pre-tip deadline (uncounted)"}.get(rc, f"publish rc={rc}"))

    def iteration(self) -> dict[str, Any] | None:
        try:
            os.remove(os.path.join(self.work, "seal_report.json"))         # the deadline check must only ever see THIS iteration's seals
        except OSError:
            pass
        if not self.mount():
            return None
        stamp = not self.a.dry_run and SW.enabled_utc(self.seals) is None
        if stamp:
            SW.mark_enabled(self.seals, self.now())                        # the first live iteration enables the ledger: windows that opened before it are BEFORE_ENABLED, never MISSED
        g = self.gate()
        self.say(f"gate active={g['active']} due={g['due']} needs_watch={g['needs_watch']} next_open={g['next_window_opens_utc']} counts={g['counts']}")
        if g["due"]:
            self.seal()
        if g["needs_watch"]:
            self.watch()
        if not self.a.dry_run and (stamp or g["due"] or g["needs_watch"]):
            self.publish()
        return g

    # -------------------------------------------------------------------------------------------------- the chain
    def dispatch_successor(self) -> None:
        r = self.run(["gh", "workflow", "run", self.a.workflow_file, "--ref", self.a.default_branch, "-f", "dry_run=false"], env=token_env(), cwd=self.a.repo_root)
        if getattr(r, "returncode", 1) == 0:
            self.say("successor dispatched")
            self.successor_sent = True
        else:
            self.err("could not dispatch the successor (the cron bootstrap and the queued runs are the fallback)")

    def run_chain(self) -> int:
        start = self.mono()
        n = 0
        while True:
            n += 1
            g = self.iteration()
            elapsed_min = (self.mono() - start) / 60.0
            if self.a.dry_run:
                break                                                      # a rehearsal is exactly one iteration
            if g is not None and not g["active"]:
                self.say("nothing open, closing or opening within the horizon: chain ends (the next delivered cron restarts it)")
                break
            if elapsed_min >= self.a.max_minutes:
                self.say("lifetime reached: chain ends")
                break
            if not self.successor_sent and elapsed_min >= self.a.successor_at_min and (g is None or g["active"]):
                self.dispatch_successor()
            self.sleep(self.a.interval_s)
        self.say(f"iterations={n} errors={len(self.errors)} missed={len(self.missed)} published={len([p for p in self.published if p.get('status') == 'PUBLISHED'])}")
        return 1 if self.errors else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work", required=True, help="scratch directory (RUNNER_TEMP)")
    ap.add_argument("--repo-root", default=os.getcwd())
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--now", default=None, help="dry runs only")
    ap.add_argument("--interval-s", type=float, default=90.0)
    ap.add_argument("--max-minutes", type=float, default=280.0)
    ap.add_argument("--successor-at-min", type=float, default=250.0)
    ap.add_argument("--horizon-h", type=float, default=6.0)
    ap.add_argument("--default-branch", default=os.environ.get("DEFAULT_BRANCH", "main"))
    ap.add_argument("--workflow-file", default="exec-shadow-seal.yml")
    a = ap.parse_args(argv)
    if a.now and not a.dry_run:
        print("::error::--now is accepted only with --dry-run (a live chain uses the wall clock)", file=sys.stderr)
        return 2
    os.makedirs(a.work, exist_ok=True)
    return Chain(a).run_chain()


if __name__ == "__main__":
    sys.exit(main())
