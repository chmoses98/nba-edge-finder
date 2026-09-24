# Handoff — capture reliability, model freeze, and the granular-data audit

Generated 2026-09-24. This wave was **data infrastructure, not model improvement**. No predictive
parameter was tuned, no feature added, no authority promoted.

---

### A. Main SHA, start and finish

| | |
|---|---|
| start | `250a7b33a408b3016bf10e8c644b18cce8cb289d` |
| finish | `250a7b33a408b3016bf10e8c644b18cce8cb289d` — **unchanged** |

Nothing was pushed to `main`. All work is on branches behind pull requests.

### B. Pull requests

| PR | branch | contents |
|---|---|---|
| **#6** | `claude/baseline-freeze` | the tamper-evident model freeze (Phase 0) |
| **#7** | `claude/capture-worker` | self-renewing worker, capture-health, evidence dashboard, docs (Phases 1–4, 10–14) |

Merge **#6 first**: #7's dashboard recomputes the frozen digest.

Two disposable experiment branches also exist — `claude/chainlab-probe` and `claude/source-probe`.
They carry throwaway rigs that temporarily overwrite `probe.yml` / `history.yml` and **must not be
merged**; delete them once the findings here are accepted.

### C. Frozen baseline

```
NBA_BASELINE_2026_PRESEASON_V1
5a4cbda0b973d1e4d6289557b99372e4735ebe3146fa76e8f0b6ca833193be78
```

Verified intact at handoff. Covers 27 league constants, the feature builder (`rating_scale = 1.9`),
the rotation model, player defaults and pricing weights. It hashes **live values read from the
code**, not a version string — because `MODEL_VERSION` does not change when `rating_scale` does,
which is exactly the drift it must catch. Proved tamper-evident by tuning 1.9 → 2.1 and watching
the suite fail, then restoring.

### D. Capture architecture, and why

One long-lived run owns the cadence; cron is demoted to a bootstrap of last resort. Driven by the
measurement that **34 of ~864** expected conductor wakes were delivered over six days (**~3.9%**),
with gaps of 2h18m and 3h09m — while the median queue delay for a run that *does* happen is 14s.
The failure is omission, not lateness, so no cron expression addresses it.

Lifetime **300 min** planned / **330 min** workflow timeout / **360 min** platform cap, so the
timeout is a backstop and never the rollover mechanism.

### E. Proof the successor rollover works

**E1**: a three-link chain, each link dispatching the next with `GITHUB_TOKEN` and
`permissions: actions: write`; all three ran. GitHub's recursion suppression — which blocks
push-triggered loops — explicitly exempts `workflow_dispatch`. Handover measured at **~7s** from the
parent's dispatch to the successor's job starting.

**E0** constrains where it can work: a workflow that exists only on a feature branch is **not**
dispatchable (404), while the same token dispatches one present on `main` (204). **PR #7 must be
merged before the chain can renew itself at all.**

### F. Duplicate-worker and race tests

**E2** (live): within one concurrency group GitHub keeps at most **one in-progress** and at most
**one pending** run; queueing a third cancels the previously pending one. Three queued runs
collapsed to exactly one, and two writers never coexisted. A successor storm is impossible by
construction — but an early-queued successor *can* be superseded, which is why the watchdog
dispatches the same workflow (so the pending slot always holds a worker) and why retirement
re-dispatches unconditionally.

`tests/test_worker_race.py` drives whole simulated lifetimes: a second worker fails closed and
writes nothing; a crashed parent's chain heals via the successor nonce **and its control**, showing
what the nonce buys; no capture happens off-slate; at most two dispatches per lifetime; a failing
capture or slow job does not end the worker; retirement releases the lease.

### G. Measured live capture cadence

**Not measurable yet, and this must not be glossed.** The archive holds **6** market snapshots
(2026-09-18 → 2026-09-22) and **zero completed games** — the 2026-27 season has not started. The
instrument (`nba capture-health`) is built and tested and currently returns `n_games = 0` with
verdict **FAIL**, which is the correct reading: an empty archive is not a pass.

### H. Does the preseason acceptance test pass?

**Cannot be run yet.** The first NBA game in the archive's schedule is **2026-10-03T23:00:00Z**
(preseason opener); the regular season starts 2026-10-20. That is the window — about 17 days — and
it opens 9 days after this handoff. `nba capture-health --gate` returns the verdict without prose.

### I. Fallback recommendation

**Stay with GitHub-native chained dispatch.** It removes the measured failure without introducing an
off-GitHub credential, and the repository is **public, so Actions minutes are free and unmetered**
(every run's `billable.UBUNTU.total_ms` is 0) — which is what makes a 24/7 chain affordable at all.
Escalate to an external scheduler or a self-hosted runner only if the preseason acceptance test
fails for reasons other than a bug. Full ranking in `CAPTURE_ARCHITECTURE.md` §5.

### J. Data-source audit

See `SOURCE_AUDIT_GRANULAR.md`. Headline: **`stats.nba.com/stats/gamerotation` — the ideal stint
source, giving exact stint start/end per player with no reconstruction — times out from GitHub
runners.** `cdn.nba.com` returns 403. `pbpstats`' lineup endpoint works (200, 180 KB, 2.6s).
`hoopR-data` has the right shape (NBA-Stats PBP in a GitHub repo, unrate-limited and reproducible)
but stops at **2022-23** and stores no lineups — it derives them by scraping the host that is
blocked.

The first run of this probe was **wrong**, and the method note in that doc explains why: it spoofed
a browser UA and reported blocks for everything including a known-good control. Negative
reachability results without a passing control are worthless.

### K. Stint coverage

**Zero. No stint dataset was built**, deliberately. Three conditions must hold and at most one does:
period-start lineups (not just substitutions), current-season latency, and verified identity
mapping. Building on top of an unvalidated source would have produced exactly the silently-wrong
dataset the brief warns against.

### L. Data-quality results

Not applicable — there is no stint dataset to quality-check. The validation *design* (five players
per side, lineup minutes reconciling to game minutes, scores reconciling, explicit quarantine rather
than silent inclusion) is recorded for when a source qualifies.

### M. Prospective context coverage

Captured point-in-time today: Kalshi market board, order-book depth (sampled by priority, cap 300),
ESPN injuries, rosters, schedule — 34 snapshots each of injuries/rosters/schedule. **Two real gaps**:
projected vs **confirmed** starters are not distinguished, and simulation output is not stamped with
the frozen baseline id. Both are named in the daily dashboard rather than omitted.

### N. Daily evidence-health artifact

`nba evidence-health` writes `EVIDENCE_HEALTH.json`; the worker refreshes it at every handover
(~5×/day). Every section reports `ok | empty | absent` **with a reason**, so a board of zeros cannot
be mistaken for a board of data. It recomputes the frozen digest live and reports
`frozen_parameters_intact`.

### O. Authority

**RESEARCH, unchanged.** No authority was promoted; `evaluate` was not run in this wave. The
standing result is preserved as found: **the market beats the model in all eight families.**

### P. Next five tasks

1. **Merge #6 then #7.** Per E0 the worker cannot renew itself until `capture_worker.yml` is on
   `main`, and the preseason window opens 2026-10-03.
2. **Delta-encode the market archive.** Measured: only **9 of 2,818** markets (0.32%) changed in
   four minutes, yet the tiered cadence still projects ~4.9 GB/season — a floor, against GitHub's
   ~1 GB recommendation. Re-measure the in-season change rate before fixing the format.
3. **Run the preseason acceptance test** from 2026-10-03 and report the verdict without
   rationalising it. If it fails, escalate per §I rather than explaining it away.
4. **Settle whether pbpstats' bulk endpoints are slow or blocked**, then validate one game
   end-to-end before any stint ingestion.
5. **Distinguish confirmed from projected starters**, and stamp simulation output with the baseline
   id so every prediction is attributable to the parameters that produced it.

### Observations recorded, not acted on

- `evaluate.py` treats a row with an unknown market-observation time as pregame
  (`mkt_at is None or mkt_at < tip`). That is fail-*open* inside an otherwise fail-closed system.
  Left untouched because the benchmark methodology is part of the freeze; worth a decision.
- The archived `STATUS_capture.json` carries an order-book truncation **alarm**, but that was
  reclassified as a *note* on 2026-09-23, ~18h after that snapshot was written. It is stale, not a
  live defect, and clears on the next capture.
