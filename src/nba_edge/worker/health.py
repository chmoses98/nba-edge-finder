"""Grade one worker shift: HEALTHY / DEGRADED / FAILED / NOT_APPLICABLE.

Why this exists. The worker deliberately never dies on a bad capture or a bad job -- one transient
API error must not become a multi-hour hole in the archive. But it also exited 0 unconditionally,
so a shift in which EVERY capture failed, settlement failed on every retry, or the final archive
push was rejected finished as a green run indistinguishable from a quiet off-season shift. Its
"preserve the archive if the final push failed" step was unreachable for the same reason.

The verdict is computed from the shift's own record (``WorkerResult``), never from the calendar,
and never from the absence of a file:

* NOT_APPLICABLE -- the worker stood down (fail-closed lease), or nothing was due all shift
  (the conductor's schedule/calendar evidence said no capture and no job). Success.
* HEALTHY        -- every due capture and job succeeded and the archive was published. Success.
* DEGRADED       -- the shift's primary work was done but something nonfatal is worth recording:
  a failure that later RECOVERED_AFTER_RETRY, a research/optional job failing, a failure that hit
  the end of the shift before its retry budget was spent, or coverage alarms on a capture this
  shift made. Success, with warnings.
* FAILED         -- something actionable is broken after bounded recovery: a required stream is
  still failing at the end of the shift after ``RETRY_BUDGET`` consecutive attempts, the final
  archive push failed (the shift's data is not published), or every successor dispatch was
  rejected (the self-renewing chain is broken). The ONLY state that turns the run red.
"""

from __future__ import annotations

from typing import Any

HEALTHY = "HEALTHY"
DEGRADED = "DEGRADED"
FAILED = "FAILED"
NOT_APPLICABLE = "NOT_APPLICABLE"

# Consecutive failed attempts, still failing at the end of the shift, before a REQUIRED stream is
# called broken. In season the worker retries every cadence tick (5-15 min), off-season the daily
# capture slot yields four attempts in its hour, and every age-gated job is re-attempted each tick
# until it succeeds -- so three is an initial attempt plus two genuine retries. Fewer than that at
# the end of a shift is DEGRADED, and the successor's first ticks are the remaining retries.
RETRY_BUDGET = 3

# Streams whose persistent failure means production evidence is not being produced. Everything else
# the worker runs is research or bookkeeping: its failure is recorded, never fatal.
REQUIRED_STREAMS = ("capture", "context", "simulate", "settle")
OPTIONAL_STREAMS = ("matchup_shadow", "evaluate", "discover")


def _attempts(cycles: list[dict[str, Any]], stream: str) -> list[bool]:
    """Ordered outcomes (True = ok) of every attempt at ``stream`` this shift."""
    out: list[bool] = []
    for c in cycles:
        if stream == "capture":
            if c.get("captured"):
                out.append(bool(c.get("capture_ok")))
            continue
        if stream in (c.get("jobs_run") or []):
            out.append(True)
        elif stream in (c.get("jobs_failed") or []):
            out.append(False)
    return out


def _trailing_failures(outcomes: list[bool]) -> int:
    n = 0
    for ok in reversed(outcomes):
        if ok:
            break
        n += 1
    return n


def classify_shift(
    result: dict[str, Any],
    *,
    final_push_ok: bool | None = None,
    capture_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the shift's health block. ``result`` is ``WorkerResult`` as a dict.

    ``final_push_ok`` is the retirement push (None = not attempted yet / not applicable).
    ``capture_status`` is STATUS_capture.json; its alarms count only when THIS worker wrote it, so a
    stale file left by an earlier run can never colour a shift that captured nothing.
    """
    worker_id = str(result.get("worker_id", ""))
    cycles = list(result.get("cycles") or [])
    failed: list[str] = []
    degraded: list[str] = []
    streams: dict[str, dict[str, Any]] = {}

    if result.get("fail_closed"):
        return {
            "state": NOT_APPLICABLE,
            "disposition": "STOOD_DOWN",
            "reasons": [f"stood down: {result.get('exit_reason', 'fail-closed')}"],
            "failures": [],
            "warnings": [],
            "streams": {},
            "retry_budget": RETRY_BUDGET,
        }

    any_work = False
    for stream in REQUIRED_STREAMS + OPTIONAL_STREAMS:
        outcomes = _attempts(cycles, stream)
        if not outcomes:
            continue
        any_work = True
        n_ok = sum(outcomes)
        n_fail = len(outcomes) - n_ok
        trailing = _trailing_failures(outcomes)
        if n_fail == 0:
            disposition = "OK"
        elif trailing == 0:
            disposition = "RECOVERED_AFTER_RETRY"
        elif trailing >= RETRY_BUDGET:
            disposition = "FAILED_AFTER_RETRY"
        else:
            disposition = "FAILING_RETRY_PENDING"
        streams[stream] = {
            "attempts": len(outcomes),
            "ok": n_ok,
            "failed": n_fail,
            "trailing_failures": trailing,
            "disposition": disposition,
        }
        if n_fail == 0:
            continue
        msg = (
            f"{stream}: {n_fail}/{len(outcomes)} attempt(s) failed, "
            f"{trailing} consecutive at shift end ({disposition})"
        )
        if stream in REQUIRED_STREAMS and disposition == "FAILED_AFTER_RETRY":
            failed.append(msg)
        else:
            degraded.append(msg)

    # Publication. Mid-shift push failures are recovered by any later successful push (each push
    # carries every unpublished commit); the retirement push has nothing after it.
    pushes = [bool(c.get("push_ok")) for c in cycles]
    if final_push_ok is not None:
        pushes.append(final_push_ok)
    if pushes:
        n_fail = pushes.count(False)
        streams["push"] = {"attempts": len(pushes), "ok": len(pushes) - n_fail, "failed": n_fail}
        if final_push_ok is False:
            failed.append("archive push failed at retirement: this shift's snapshot is not on the archive branch")
        elif n_fail and pushes[-1]:
            degraded.append(f"push: {n_fail}/{len(pushes)} push(es) failed, recovered by a later push")
        elif n_fail and _trailing_failures(pushes) >= RETRY_BUDGET:
            failed.append(f"push: last {_trailing_failures(pushes)} archive pushes failed")
        elif n_fail:
            degraded.append(f"push: {n_fail}/{len(pushes)} push(es) failed")

    # The self-renewing chain. Each dispatch is one API call; the worker tries early and again at
    # retirement, so two rejections with none accepted means the chain cannot renew itself and only
    # the ~4%-delivery cron bootstrap is left. A worker run without a dispatcher (local, or
    # --no-successor) makes no attempts and is not judged on this.
    attempts = int(result.get("successor_dispatch_attempts") or 0)
    if attempts and not result.get("successor_dispatched"):
        if attempts >= 2:
            failed.append(f"successor dispatch rejected on all {attempts} attempts: the worker chain cannot renew")
        else:
            degraded.append("successor dispatch rejected; retirement will re-attempt")

    if capture_status and str(capture_status.get("run_id", "")) == worker_id and worker_id:
        for a in capture_status.get("alarms") or []:
            degraded.append(f"coverage alarm: {a}")

    if failed:
        state, disposition = FAILED, "FAILED_AFTER_RETRY"
    elif degraded:
        state = DEGRADED
        recovered = any(s.get("disposition") == "RECOVERED_AFTER_RETRY" for s in streams.values())
        disposition = "RECOVERED_AFTER_RETRY" if recovered else "DEGRADED"
    elif any_work:
        state, disposition = HEALTHY, "OK"
    else:
        state, disposition = NOT_APPLICABLE, "NO_WORK"
    reasons = failed + degraded
    if state == NOT_APPLICABLE:
        reasons = ["no capture or job was due this shift (schedule/calendar evidence: nothing in window)"]
    return {
        "state": state,
        "disposition": disposition,
        "reasons": reasons,
        "failures": failed,
        "warnings": degraded,
        "streams": streams,
        "retry_budget": RETRY_BUDGET,
    }


def render_summary(health: dict[str, Any], result: dict[str, Any]) -> str:
    """Markdown for $GITHUB_STEP_SUMMARY."""
    lines = [
        f"### capture-worker shift: **{health['state']}** ({health['disposition']})",
        "",
        f"worker `{result.get('worker_id')}` generation {result.get('generation')} -- "
        f"{result.get('n_cycles', len(result.get('cycles') or []))} cycle(s), exit: {result.get('exit_reason')}",
        "",
    ]
    if health.get("streams"):
        lines += ["| stream | attempts | ok | failed | disposition |", "|---|---|---|---|---|"]
        for name, s in health["streams"].items():
            lines.append(
                f"| {name} | {s.get('attempts')} | {s.get('ok')} | {s.get('failed')} | {s.get('disposition', '')} |"
            )
        lines.append("")
    for r in health.get("reasons") or []:
        lines.append(f"- {r}")
    return "\n".join(lines) + "\n"


def annotations(health: dict[str, Any]) -> list[str]:
    """GitHub workflow commands: ::error for each failure, ::warning for each nonfatal finding."""
    title = f"capture-worker {health['state']}"
    return [f"::error title={title}::{r}" for r in health.get("failures") or []] + [
        f"::warning title={title}::{r}" for r in health.get("warnings") or []
    ]
