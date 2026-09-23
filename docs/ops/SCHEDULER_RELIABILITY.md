# Scheduler reliability: can GitHub cron support a 5–10 minute capture objective?

**No. Not by a factor of about twenty.** Measured, not assumed, by `scripts/schedule_audit.py`,
which reads the Actions API and matches delivered scheduled runs to nominal cron slots. Raw records
append to `docs/ops/schedule_audit.jsonl`.

## Measurement (2026-09-19 01:07 → 2026-09-23 11:09, main, `conductor.yml`)

The conductor declares `*/10 * * * *`.

| metric | value |
|---|---:|
| expected slots | 636 |
| delivered | 29 |
| missing | **607** |
| **delivery rate** | **4.6%** |
| median delay | 4.2 min |
| p90 delay | 9.3 min |
| max delay | 9.7 min |
| **effective interval** | **219 min** |
| longest gap between runs | **357 min** |
| conclusions | 26 success, 3 failure |

## The failure is omission, not lateness — and that changes the fix

Every delivered run arrived **within 9.7 minutes** of its nominal slot; the median was 4.2. When
GitHub fires, it is punctual.

It simply does not fire. It drops roughly **19 out of every 20 slots**, leaving an effective
interval of **3.7 hours** against a declared 10 minutes, with a worst observed gap of **5.95 hours**.

This matters because the obvious remedies are aimed at the wrong failure. Wider delay tolerance,
retry-on-late, or an age-based trigger (which the conductor already uses, and which is why nothing
has silently rotted) all address *lateness*. None of them produce a run that GitHub never started.

## Preseason reliability requirement

The capture objective is a market snapshot every 5–10 minutes while a game tips within 36 hours.
Stated as a testable requirement, to be measured over a rolling 7-day preseason window by this same
audit:

1. **≥ 95% of intended capture intervals ≤ 12 minutes.**
2. **No gap > 30 minutes** during an active window.
3. **≥ 99% of delivered runs conclude non-`failure`** (see the open item below).

Current GitHub-native cron scores **4.6%** on (1) and shows a **357-minute** worst gap against (2).
It fails both by a wide margin. This is a pre-existing property of the platform, not a regression
introduced by any change in this project.

## The simplest thing that could work, and it is still GitHub-native

**Capture in a loop inside one run, rather than once per run.**

A scheduled run enters a bounded loop that captures every 10 minutes and exits before the 6-hour job
limit — say 5.5 hours of coverage per run. The cron then only has to deliver *a* run occasionally
rather than 144 punctually.

The measurement says this works, and says so with a thin margin worth stating: the worst observed
gap between delivered runs is **357 minutes**, and a 5.5-hour (330-minute) loop does **not** span
it. Two changes close that:

- run the loop to ~5.75 hours, and
- let runs overlap (a constant concurrency group with `cancel-in-progress: false` queues rather than
  drops), so a newly delivered run extends coverage instead of replacing it.

At the observed delivery rate this yields roughly 6–7 runs a day × 5.75 hours ≈ 36+ hours of
coverage per 24 hours, i.e. redundant overlap rather than gaps.

Costs and limits, stated plainly: billed minutes rise from ~2 min/wake to continuous runner time
during active windows, which is the real price of this approach and should be scoped to the
in-season active window only, not run year-round. Capture must also be idempotent under overlap —
the archive ledger is content-hashed and append-only, so duplicate snapshots are already harmless.

**Alternatives deliberately not taken yet.** An external cron service (cron-job.org and similar have
free tiers) or a self-hosted runner would both give true 10-minute cadence, but each adds an
operational dependency outside the repository. The in-run loop needs none, so it should be tried and
measured first. Revisit only if it is measured to fail the requirement above.

## Open item found by this audit

Three of the 29 delivered runs failed, all in the 16:00 UTC hour — the off-season daily capture
slot. The cause is not the scheduler: it is this project's own coverage alarm treating a
**deliberately configured** order-book cap as an invariant breach:

```
##[warning]order books truncated: 3463 live markets but max_orderbooks=300
##[error]1 alarm(s)
```

The workflow passes `--max-orderbooks 300` on purpose, so truncating to it is the cap working, not
the market universe going unaccounted for. Filed and fixed separately; a daily red run teaches
people to ignore alarms, which is worse than having none.
