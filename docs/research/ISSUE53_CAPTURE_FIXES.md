# Issue #53 - capture worker: publish-before-jobs switch (research only; OFF by default)

Context: `ISSUE53_CAPTURE_RELIABILITY.md`. Every cycle the capture worker does capture -> due jobs (`app_export` and `research_export` every cycle, others periodically) -> **one push**. A tick is therefore
visible on `data-archive` only after the jobs finish: commit lag median 214 s, p90 433 s, max 825 s over 802 ticks. That lag is the entire loss of the strict control (`BOARD_COMMITTED_AFTER_CHECKPOINT`).

## Change
* `Worker(push_capture_first=...)` / env `CAPTURE_PUSH_FIRST=1`: after a **successful** capture the worker pushes immediately (subject `capture: <run> at <tick>`, exactly as today), then runs the due jobs, then
  pushes again with subject `cycle: <run> at <tick>` (so there is still exactly one `capture:` commit per tick, which the audit and the sealed ledgers' board-commit index rely on). A failed capture or a
  failed early push falls back to today's single end-of-cycle push. `CycleRecord.capture_pushed_first` records it per cycle.
* `capture_worker.yml` passes `CAPTURE_PUSH_FIRST: ${{ vars.CAPTURE_PUSH_FIRST || '0' }}`: **merging this changes nothing**; the owner enables it by setting the repository variable to `1` and disables it by
  setting it back to `0` (no code change either way). Concurrency group, lease, cadence, retirement, health model and push script are untouched.

## Why it is gated (read before enabling)
It shortens the commit lag the preregistered studies are measured against. The strict control would then lose far fewer games (its exclusions *are* this lag), and the control-vs-t60a contrast would shrink.
It does not alter any protocol, threshold, probability, cost or exposure rule, and each seal records the commit time of its board, so before/after seals can be reported separately. Recommended: enable at a recorded instant
and stratify; or leave off until the first evidence checkpoints.

## Tests (`tests/test_worker_capture_reliability.py`, 5)
Default behaviour pinned (one push, after the jobs, `capture:` subject); with the switch: capture -> early push -> jobs -> closing `cycle:` push, exactly one `capture:` commit per tick; no early push after a failed
capture; early push failure falls back; the workflow passes the switch with default `'0'` and keeps the concurrency group; the env var is the default source of the switch. Existing worker tests unchanged
(`test_outside_the_active_window_the_worker_captures_nothing` fails identically on `main`; unrelated).

## Not changed
Retry cadence after a failed capture: the one in-loop episode (2026-10-22, three consecutive failures) was **three hangs to the 600 s budget**, i.e. an upstream outage; retrying sooner would save at most ~13 min
of a 60 min hole and would change the health model's attempt-based retry budget, so it is not proposed. The pre-warmed-successor design (the fix for the runner-queue handover gaps) is described in the audit doc and
is not implemented.
