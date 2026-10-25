"""The long-lived, self-renewing sealer of the Issue #53 sealed pre-tip ledger (RESEARCH ONLY). Standard library only: the heavy work happens in subprocesses.

Why a chain and not a 5-minute cron. This repository MEASURED its scheduled-workflow delivery: `*/10` produced 34 runs against 864 expected (3.9%), with gaps of 2-3 hours
(`capture_worker.yml`, `nba-ticker.yml`). A seal window is 40 minutes wide, so a cron-driven sealer would simply miss most games. The pattern that works here is a job that
owns the cadence itself and dispatches its successor (`workflow_dispatch` is exempt from recursion suppression); cron is demoted to a bootstrap of last resort.

One run (this module, up to ~335 minutes):
  1. loop every `interval_s`: mount the ledger (fresh) and the schedule context (depth-1, ~1 s); evaluate the gate IN PROCESS (`seal_windows`, no dependency installed);
  2. a window is OPEN -> mount the boards / forecasts, run `exec_seal seal`; a window CLOSED UNSEALED -> `exec_seal watch` writes the MISSED marker (red run);
  3. live runs only: export the new files and publish them through the Git Data API (`ledger_remote`: server-side commit time, fast-forward only, additions only), then
     verify durability and the deadline against the SERVER commit time;
  4. HANDOVER AT A QUIET MOMENT. Measured (2026-10-22/23): the successor is dispatched ~30 min before the end but cannot start before its predecessor finishes (one concurrency
     group), and then waits for a hosted runner for up to 18+ minutes; dispatching earlier changes nothing. So the gap cannot be shortened, only placed: after `retire_after_min`
     the chain retires - dispatching the successor and ending - at the first QUIET moment (no seal window open or closing unsealed, none opening within `quiet_lead_min`); if no
     quiet moment comes it dispatches by `successor_at_min` (so the pending run exists) and ends at the hard cap `max_minutes` (the hosted-job limit is 360 min). Stop also as soon as nothing is open, closing or opening
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
from datetime import datetime, timedelta, timezone
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
        self.m = os.path.join(a.work, "m")
        self.lanes = [x for x in str(getattr(a, "lanes", "control")).split(",") if x]
        bad = [x for x in self.lanes if x not in SW.LANES]
        if bad or not self.lanes:
            raise SystemExit(f"unknown lane(s) {bad}: choose from {sorted(SW.LANES)}")
        # one worktree, one study, one report per lane; the control lane keeps its original file names
        self.dirs = {ln: os.path.join(a.work, "seals" if ln == "control" else f"seals_{ln}") for ln in self.lanes}
        self.news = {ln: os.path.join(a.work, "new" if ln == "control" else f"new_{ln}") for ln in self.lanes}
        self.studies = {ln: SW.load_study(SW.lane_study_path(ln)) for ln in self.lanes}
        self.seals = self.dirs[self.lanes[0]]              # first lane (the control by default); kept for callers that think in one lane
        self.new = self.news[self.lanes[0]]
        self.study = self.studies[self.lanes[0]]
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
        steps = []
        for ln in self.lanes:
            if self.a.dry_run:                                              # a rehearsal runs on an EMPTY ledger: it neither reads nor depends on the real one
                shutil.rmtree(self.dirs[ln], ignore_errors=True)
                os.makedirs(self.dirs[ln])
                self.run(["git", "init", "-q", self.dirs[ln]], env=clean_env(), cwd=self.a.repo_root)
            else:
                steps.append(["mount_seals", self.dirs[ln], SW.lane_branch(ln)])
        steps.append(["mount_context", self.m] + ([self.a.now] if (self.a.dry_run and self.a.now) else []))
        for step in steps:
            r = self.run(["bash", CI, *step], env=clean_env(), cwd=self.a.repo_root)
            if getattr(r, "returncode", 1) != 0:
                self.err(f"mount failed: {step[0]} (rc={getattr(r, 'returncode', '?')})")
                return False
        return True

    def gate(self, lane: str | None = None) -> dict[str, Any]:
        lane = lane or self.lanes[0]
        return SW.gate(os.path.join(self.m, "data-archive"), self.dirs[lane], self.now(), self.studies[lane], self.a.horizon_h)

    def seal_args(self, lane: str) -> list[str]:
        d = os.path.join(self.m, "data-archive")
        return ["--archive", os.path.join(self.m, "projection-data"), "--market", d, "--context", d, "--board-repo", d, "--seals", self.dirs[lane], "--code-repo", self.a.repo_root,
                "--lane", lane]

    def report(self, lane: str) -> str:
        return os.path.join(self.work, "seal_report.json" if lane == "control" else f"seal_report_{lane}.json")

    def seal(self, lanes: list[str]) -> None:
        r = self.run(["bash", CI, "mount_inputs", self.m] + ([self.a.now] if (self.a.dry_run and self.a.now) else []), env=clean_env(), cwd=self.a.repo_root)
        if getattr(r, "returncode", 1) != 0:
            self.err(f"mount_inputs failed (rc={getattr(r, 'returncode', '?')}); retried on the next iteration while the window is open")
            return
        for ln in lanes:
            cmd = ["-m", "nba.paper.exec_seal", "seal", *self.seal_args(ln), "--out", self.report(ln), *self.now_arg()] + (["--dry-run"] if self.a.dry_run else [])
            r = self.py(*cmd)
            if getattr(r, "returncode", 1) != 0:
                self.err(f"exec_seal seal [{ln}] rc={getattr(r, 'returncode', '?')} (a game that errored is retried on the next iteration; none is sealed half-done)")

    def watch(self, lane: str) -> None:
        d = os.path.join(self.m, "data-archive")
        cmd = ["-m", "nba.paper.exec_seal", "watch", "--context", d, "--seals", self.dirs[lane], "--lane", lane, *self.now_arg()] + (["--dry-run"] if self.a.dry_run else [])
        r = self.py(*cmd)
        rc = getattr(r, "returncode", 1)
        if rc == 3:
            self.missed.append(f"{lane}@{self.now().isoformat()}")
            self.err(f"[{lane}] a seal window closed unsealed: MISSED marker written (the game is uncounted, never sealed late)")
        elif rc != 0:
            self.err(f"exec_seal watch [{lane}] rc={rc}")

    def publish(self, lane: str) -> None:
        news = self.news[lane]
        shutil.rmtree(news, ignore_errors=True)                             # never re-publish a previous iteration's leftovers
        r = self.py(LEDGER_REMOTE, "export", "--seals", self.dirs[lane], "--dir", news)
        if getattr(r, "returncode", 1) != 0:
            self.err(f"export [{lane}] refused (rc={getattr(r, 'returncode', '?')}): the worktree holds changes that are not additions")
            return
        out = os.path.join(self.work, "publish.json" if lane == "control" else f"publish_{lane}.json")
        r = self.py(LEDGER_REMOTE, "publish", "--dir", news, "--report", self.report(lane), "--out", out, "--repo", self.a.repo, "--branch", SW.lane_branch(lane), token=True)
        rc = getattr(r, "returncode", 1)
        if os.path.exists(out):
            try:
                self.published.append(json.load(open(out)))
            except ValueError:
                pass
        if rc == 0:
            return
        self.err({1: f"publish [{lane}]: NOT DURABLE or API error", 5: f"publish [{lane}]: a seal was committed after its pre-tip deadline (uncounted)"}.get(rc, f"publish [{lane}] rc={rc}"))

    def iteration(self) -> dict[str, Any] | None:
        for ln in self.lanes:
            try:
                os.remove(self.report(ln))                                  # the deadline check must only ever see THIS iteration's seals
            except OSError:
                pass
        if not self.mount():
            return None
        stamp = {ln: (not self.a.dry_run and SW.enabled_utc(self.dirs[ln]) is None) for ln in self.lanes}
        for ln in self.lanes:
            if stamp[ln]:
                SW.mark_enabled(self.dirs[ln], self.now())                  # the first live iteration enables a lane's ledger: windows that opened before it are BEFORE_ENABLED, never MISSED
        gates = {ln: self.gate(ln) for ln in self.lanes}
        for ln, g in gates.items():
            self.say(f"[{ln}] gate active={g['active']} due={g['due']} needs_watch={g['needs_watch']} next_open={g['next_window_opens_utc']} counts={g['counts']}")
        due = [ln for ln in self.lanes if gates[ln]["due"]]
        if due:
            self.seal(due)
        for ln in self.lanes:
            if gates[ln]["needs_watch"]:
                self.watch(ln)
        if not self.a.dry_run:
            for ln in self.lanes:
                if stamp[ln] or gates[ln]["due"] or gates[ln]["needs_watch"]:
                    self.publish(ln)
        return {"active": any(g["active"] for g in gates.values()), "due": bool(due), "needs_watch": any(g["needs_watch"] for g in gates.values()),
                "next_window_opens_utc": min((g["next_window_opens_utc"] for g in gates.values() if g["next_window_opens_utc"]), default=None),
                "counts": {ln: g["counts"] for ln, g in gates.items()}}

    # -------------------------------------------------------------------------------------------------- the chain
    def dispatch_successor(self) -> None:
        r = self.run(["gh", "workflow", "run", self.a.workflow_file, "--ref", self.a.default_branch, "-f", "dry_run=false"], env=token_env(), cwd=self.a.repo_root)
        if getattr(r, "returncode", 1) == 0:
            self.say("successor dispatched")
            self.successor_sent = True
        else:
            self.err("could not dispatch the successor (the cron bootstrap and the queued runs are the fallback)")

    def quiet(self, g: dict[str, Any]) -> bool:
        """No lane has a window open or closed-unsealed, and none opens within `quiet_lead_min`: a runner-queue delay of the successor cannot cost a game."""
        if any(c.get("OPEN") or c.get("WINDOW_CLOSED_UNSEALED") for c in (g.get("counts") or {}).values()):
            return False
        nxt = g.get("next_window_opens_utc")
        return not nxt or SW.parse_ts(nxt) - self.now() >= timedelta(minutes=self.a.quiet_lead_min)

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
            needed = g is None or g["active"]
            if elapsed_min >= self.a.max_minutes:
                if needed and not self.successor_sent:
                    self.dispatch_successor()                              # last chance to leave a pending run (cron bootstrap is the only other fallback)
                self.say("lifetime reached: chain ends")
                break
            quiet = g is not None and self.quiet(g)
            if needed and not self.successor_sent and (elapsed_min >= self.a.successor_at_min or (elapsed_min >= self.a.retire_after_min and quiet)):
                self.dispatch_successor()
            if self.successor_sent and elapsed_min >= self.a.retire_after_min and quiet:
                self.say("quiet moment (no seal window open, closing or imminent): handing over to the successor")
                break
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
    ap.add_argument("--max-minutes", type=float, default=335.0, help="hard cap (the hosted-job limit is 360 min)")
    ap.add_argument("--successor-at-min", type=float, default=315.0, help="latest moment to dispatch the successor so a pending run exists before the hard cap")
    ap.add_argument("--retire-after-min", type=float, default=240.0, help="from here on, hand over at the first quiet moment")
    ap.add_argument("--quiet-lead-min", type=float, default=45.0, help="a moment is quiet if no window is open and the next one opens at least this many minutes away")
    ap.add_argument("--horizon-h", type=float, default=6.0)
    ap.add_argument("--default-branch", default=os.environ.get("DEFAULT_BRANCH", "main"))
    ap.add_argument("--workflow-file", default="exec-shadow-seal.yml")
    ap.add_argument("--lanes", default="control", help="comma list of sealing lanes to run: control (strict T-60) and/or t45 (availability study; needs owner approval to be enabled live)")
    a = ap.parse_args(argv)
    if a.now and not a.dry_run:
        print("::error::--now is accepted only with --dry-run (a live chain uses the wall clock)", file=sys.stderr)
        return 2
    os.makedirs(a.work, exist_ok=True)
    return Chain(a).run_chain()


if __name__ == "__main__":
    sys.exit(main())
