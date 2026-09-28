# Capture architecture: evidence, experiments, and the decision

**Status:** implemented, not yet proven in production. The acceptance test (Phase 5) cannot run
until the 2026-27 preseason opens on **2026-10-03**, which is the first NBA game in the archive's
schedule. See [Open risks](#open-risks) for what remains unproven.

---

## 1. The problem, restated from measurement

GitHub's scheduler does not deliver. Measured on this repository's own Actions history over
2026-09-18 → 2026-09-24:

| quantity | value |
|---|---|
| `conductor` scheduled runs delivered | **34** |
| expected at `*/10` over the same window | ~864 |
| delivery rate | **~3.9%** |
| observed gaps between consecutive "10-minute" wakes | **2h18m**, **3h09m** |
| queue delay once a run *is* created (`conductor/run`, n=39) | median 14s, p90 25s, max 49s |

The second and third rows are the important pair. When a run happens it is **prompt** — the median
queue delay is fourteen seconds. The failure is that the run mostly does not happen at all.

**The dominant failure is omission, not lateness.** No cron expression fixes an omission rate. The
cadence has to come from inside a process we control.

## 2. Measured overhead (Phase 2)

From 39 `conductor/run` jobs and 93 `ci/test` jobs, per-step:

| step | median | p90 | max |
|---|---|---|---|
| Set up job | 1s | 1s | 2s |
| `actions/checkout@v4` | 2s | 3s | 3s |
| `actions/setup-python@v5` | 3s | 5s | 6s |
| `pip install -e .` | **17s** | 19s | **21s** |
| archive worktree checkout | 1s | 2s | 2s |
| **fixed overhead subtotal** | **~26s** | — | **~33s** |
| queue delay before any of it | 14s | 25s | 49s |
| `nba capture` itself | — | **181s** | **186s** |

Under the old design every single wake paid ~26–33s of setup plus ~14–49s of queueing to deliver
one capture. A long-lived worker pays that **once per five hours** instead of once per capture.

**Repository is public, so Actions minutes are free and unmetered** (confirmed: every run's
`billable.UBUNTU.total_ms` is `0`). Cost is therefore *not* a constraint on worker lifetime, which
materially changes the design — and the Phase 6 ranking below.

## 3. Experiments

All run against this repository with a disposable rig (`chainlab`), not assumed from documentation.
`docs.github.com` is denied by this build environment's network policy, so where official docs were
unreachable the behaviour was measured directly instead.

### E0 — where a dispatchable workflow must live

| dispatch | result |
|---|---|
| `chainlab.yml`, present only on a feature branch | **404 Not Found** |
| `conductor.yml`, present on `main`, `ref` = feature branch | **204**, run created on the feature branch |

**Finding.** `workflow_dispatch` resolves the workflow by a file that must exist on the **default
branch**; `ref` then selects which branch's *content* executes. The control run rules out "the
token lacks `actions: write`" as the explanation for the 404.

**Consequence.** `capture_worker.yml` cannot renew itself until it is merged to `main`. A feature
branch cannot test the chain.

### E1 — can a run dispatch its own successor?

This is the make-or-break question: GitHub suppresses events raised by `GITHUB_TOKEN` to prevent
recursive workflow loops. If that applied to `workflow_dispatch`, the design would be impossible.

Chain of three links, each dispatching the next with `GITHUB_TOKEN` and `permissions: actions: write`:

| link | run | created | job started | conclusion |
|---|---|---|---|---|
| 1 | 35953093889 | 03:50:07 | 03:50:12 | success |
| 2 | 35953102168 | 03:50:14 | 03:50:19 | success |
| 3 | 35953111083 | 03:50:21 | 03:50:26 | success |

**Finding.** The recursion suppression explicitly **exempts** `workflow_dispatch` and
`repository_dispatch`. A run can dispatch its own successor and the successor really runs.
Handover measured at **~7s** from the parent's dispatch call to the successor's job starting
(parent completed :16 → successor job started :19).

### E2 — concurrency semantics, and the hazard that shaped the design

One holder `A` occupied the concurrency group for 240s. Two "watchdogs" were queued behind it, then
`A` dispatched its own successor `B`:

| run | role | queued | outcome |
|---|---|---|---|
| A | holder | 03:52:48 | **success** — ran alone throughout |
| W1 | watchdog | 03:53:30 | **cancelled** (superseded by W2) |
| W2 | watchdog | 03:54:11 | **cancelled** (superseded by B) |
| B | A's successor | 03:56:56 | **ran** |

**Findings.**
1. At most **one run in progress** per group. Two writers never coexisted. This is a genuine
   platform-level single-writer guarantee.
2. At most **one run pending** per group. Queueing a third cancels the previously pending one.
   Three queued runs collapsed to exactly one — **a successor storm is impossible by construction.**
3. The **last dispatch wins** the pending slot.

Finding 3 is the dangerous one. A successor queued early can be cancelled by *any* later dispatch
into the group — including a watchdog cron. That would be fatal if the watchdog were a different
workflow.

**The resolution:** the watchdog dispatches *this same workflow*. The single pending slot then
always contains a worker, and it does not matter who put it there. Cancellation becomes a
substitution rather than a break.

### E3 — how long can a run stay pending?

A holder occupied the group for 70 minutes with a successor queued behind it at t+75s.

| | |
|---|---|
| holder ran | 04:01:14 → 05:11:31 (70.3 min) |
| successor queued | 04:02:27 |
| successor job started | 05:11:35 |
| **time waiting in the concurrency queue** | **69.1 min** |
| **handover, holder-finish → successor-start** | **4 s** |
| successor conclusion | success |

**Finding.** A queued run survives at least ~69 minutes in a concurrency group without being
cancelled or expiring, and starts within seconds of the group clearing. Early dispatch is
therefore sound as crash insurance: a worker that dies at any point leaves a successor that starts
almost immediately.

*A measurement trap worth recording.* The **job**-level API reports this successor as pending for
only 0.1 minutes, because the job object is not created until the run is dequeued. Only the
**run**-level `created_at` shows the real 69-minute wait. Reading the job timestamps would have
produced a confident and completely wrong conclusion.

This does not remove the need for the retirement re-dispatch (§4): E2 showed a pending run can
still be *superseded* by a later queued run, which is a different failure from expiring.

## 4. The design

One long-lived run owns the cadence; cron is demoted to a bootstrap of last resort.

```
worker starts
  ├─ acquire lease (fail-closed if another worker is genuinely live)
  ├─ dispatch successor EARLY            ← crash insurance: if we die, a worker is already queued
  ├─ loop until planned exit:
  │    ├─ capture on the tiered cadence (15m far → 10m → 7m → 5m inside T-30m)
  │    ├─ run whatever the conductor would have decided to run
  │    ├─ heartbeat the lease with the promise "next capture at T"
  │    └─ sleep to the next tick, scheduled from cycle START (so overruns degrade, not compound)
  ├─ retire at 300 min, re-dispatch the successor (E2: the early one may have been superseded)
  └─ release the lease explicitly, so the next worker need not wait for it to expire
```

**Lifetime (Phase 2).** Planned **300 min**; workflow `timeout-minutes: 330`; documented platform
cap 360 min. The timeout sits 30 minutes above the planned exit and 30 minutes below the cap, and
is **never** the rollover mechanism — measured worst-case retirement cost is under a minute
(dispatch 1s + handover ~7s), so the backstop is roughly 30× the cost of the thing it insures.

**Why the worker is a superset of the conductor.** It holds the `conductor-archive` concurrency
group for hours, so every scheduled conductor run queues behind it and is superseded (E2). If the
worker did not run `context`/`simulate`/`settle`/`evaluate`/`discover` itself, those jobs would
silently stop for as long as a worker was alive. It reuses `conductor.decide_now()` rather than
reimplementing the cadence rules.

**Ownership (Phase 3), in two layers.**

| layer | what it guarantees | what it cannot do |
|---|---|---|
| `concurrency: conductor-archive` | never two runs in progress (E2) | invisible after the fact; no reach outside the group |
| `LEASE_capture.json` on the archive | evidence, cross-workflow reach, fail-closed refusal | advisory only; not a platform guarantee |

The lease carries worker id, generation, heartbeat, the holder's own promised next-capture time,
planned exit, successor nonce, and an explicit release. Two details are load-bearing:

* **Expiry is relative to the holder's own promise**, not a fixed TTL. A fixed 30-minute TTL would
  set the recovery hole equal to the TTL and guarantee failure against the "no gap > 30 min"
  criterion the first time a worker died.
* **A successor nonce.** The dispatch API returns 204 with no body, so a parent cannot learn its
  successor's run id — but it can name it in advance. Without this, a worker that crashes mid-life
  leaves a lease that still *looks* alive, its successor fails closed within seconds, and the chain
  dies exactly when it was supposed to heal itself. `tests/test_worker_race.py` contains both the
  recovery test and its control.

## 5. Phase 6 — fallback options, ranked

| # | option | reliability | operational burden | cost | secrets / security | failure recovery | cadence precision |
|---|---|---|---|---|---|---|---|
| **1** | **GitHub-native chained dispatch** *(chosen)* | cadence is internal, so the ~3.9% cron delivery rate no longer gates it; E1/E2 verified | none beyond this repo | **free** (public repo, 0 billable ms) | no new secrets; `GITHUB_TOKEN` only, scoped to this repo | early dispatch + retirement re-dispatch + cron bootstrap | seconds, set by `sleep` inside the run |
| 2 | External scheduler → `workflow_dispatch` | depends on a third party; removes GitHub's omission problem but adds theirs | small | free tiers exist | **requires a PAT or App key held off-GitHub** — a real escalation | external retry | ~1 min |
| 3 | Self-hosted runner / always-on worker | highest, if the host is reliable | ongoing: patching, disk, monitoring, uptime | small but non-zero | runner token on a machine you own; wider blast radius | must be built | sub-second |
| 4 | Cloud scheduler (EventBridge / Cloud Scheduler) | very high | account, IAM, billing | small | cloud credentials off-GitHub | managed retry | ~1 min |

Option 1 is chosen because it removes the measured failure (omission) without introducing an
off-GitHub credential, and because free unmetered minutes on a public repository make a 24/7 chain
affordable. The brief's guidance applies directly: *"Do not build an elaborate cloud platform
unless required. The capture dataset is more valuable than architectural elegance."*

**Escalate to option 2 or 3 if** the preseason acceptance test fails — specifically if the chain
breaks more than once, or if `pct_within_12min` stays below 95% for reasons other than a bug.

## Open risks

1. **The chain is unproven in production.** E1/E2 prove the primitives; they do not prove five
   hours of real capture. The acceptance test is the proof, and it cannot run before 2026-10-03.
2. **`capture_worker.yml` must be merged to `main` before it can renew itself** (E0). Until then
   the chain cannot start at all.
3. **The 6-hour job cap was not re-verified.** `docs.github.com` is denied by this environment's
   network policy and a six-hour probe was not worth the wall-clock. The design is built not to
   depend on the exact figure: the worker retires on its own clock an hour beneath it.
4. **If the chain ever dies completely, recovery depends on cron** — the very thing that delivers
   ~3.9%. Expected recovery is on the order of a couple of hours, which would breach the 30-minute
   gap criterion. This is mitigated (early dispatch, retirement re-dispatch, and E2's guarantee
   that a pending slot is only ever *replaced*, never emptied) but not eliminated.
5. **E3 is unresolved at the time of writing.**
