# Issue #53 - capture reliability: why the market stream has holes, and what would close them (research only; analysis + tooling, no behaviour change)

Both sealed studies choose a board from the capture ticks on `data-archive`; a hole in that stream removes games from **both** lanes. This note explains the 57-minute hole behind game
`espn:401909867`, audits every gap in the recent archive, ranks the causes with evidence, and proposes fixes. Nothing in this PR changes the capture worker, a workflow, a protocol, a
threshold or a ledger. Tool: `nba/paper/capture_audit.py` (stdlib, read-only, commit-history only); output: `results/issue53_capture/capture_gaps.{md,json}`; tests:
`tests/test_issue53_capture_audit.py`.

## 1. Game 401909867 (tip 2026-10-26T01:00Z; decision instant 00:00Z)

| time (UTC) | event |
|---|---|
| 22:55:40 | last tick of capture worker `40216046475`; its commit lands 22:59:10 |
| 23:00:41 | that worker re-dispatches its successor (run `40242791150`) - the run is created but **pending** in the single `conductor-archive` concurrency group |
| 23:04:02 / 23:04:05 | the worker commits `retired after 40 cycles` and its job ends, releasing the group |
| 23:04:07 | the successor's **job is created** (queued for a hosted runner) |
| **23:51:49** | the successor's job **starts** - 47 min 42 s later |
| 23:52:46 | first commit of the successor (`acquired lease`); its first tick is 23:52:47 |
| 00:01:11 | that tick is committed |

So there was no board between 22:55:40 and 23:52:47 (57 min). The control's sealed board for the game was the 23:52:47 tick, committed 00:01:11, after the decision instant -> `NO_TRADE`
(`BOARD_COMMITTED_AFTER_CHECKPOINT`); t60a needs a tick committed by 00:00:00 inside an 1800 s gap -> none exists -> `NO_TRADE` (`NO_BOARD_COMMITTED_BY_DECISION`). **Neither rule can recover
a game whose archive has no usable tick**; the lanes differ only on games that have a committed board.

## 2. Audit of the recent archive (2026-10-20 .. 10-26; 802 market ticks; gaps over 20 min)

| kind | count | minutes | what it is |
|---|---|---|---|
| HANDOVER | 9 | 370 | end of one worker's job to the start of the next; **8 of 9 dominated by the successor waiting for a hosted runner (15-63 min)**, 1 by the retire tail (10.7 min) |
| CAPTURE_GAP_IN_LOOP | 1 | 60 | 2026-10-22 07:05 -> 08:05: three consecutive capture cycles (07:20, 07:35, 07:50) produced no market file (`capture_failed 3` in that worker's status) |

* **Not Kalshi, not scheduling.** Inside a worker's loop the cadence is regular: one episode of 3 failed cycles in 805 cycles (0.4%), over 6.5 days, all other cycles succeeded
  (`n_capture_failed 0` in 30 of 31 shift statuses). Cron is not involved: the workers renew themselves (no gap is attributable to a cron wake that did not come).
* **The dominant cause is the platform's hosted-runner queue at each worker handover.** The single concurrency group (`conductor-archive`) admits the successor only after the predecessor's job
  ends; its job then waits for a runner. Successor wait (predecessor's `retired` commit -> successor's first commit; includes ~1.5 min of job setup): median 1.3 min, **p90 24.4 min, max 63.1 min;
  25% of handovers wait more than 15 min** (n = 32). The worker's own design note assumed "queue-to-running 2-7 s"; that holds three times out of four and fails the fourth. Job timestamps
  confirm it (`created_at` 23:04:07 -> `started_at` 23:51:49 for the run above).
* **The retire tail adds 1-11 min** (median 3.0): the last cycle's due jobs, the lease release, the evidence dashboard and the final push happen before the job - and so the group - is released.
* **Publication delay is structural, not a fault.** A cycle is capture -> due jobs (`app_export` and `research_export` every cycle, `simulate`/`context`/`matchup_shadow` periodically) -> **one push at the end**.
  A tick is therefore visible only after its cycle's jobs finish: commit lag median **214 s**, p90 433 s, max 825 s (n = 802), 217-244 s in a typical cycle and 480-500 s in the cycles that also run
  `context` / `matchup_shadow` / `evaluate`. This is why the strict control loses about half of its games (`BOARD_COMMITTED_AFTER_CHECKPOINT`).

## 3. Fixes, ranked by evidence (none applied here)

| # | change | evidence it addresses | effect | risk / approval |
|---|---|---|---|---|
| 1 | **Seal-chain keeper** in `nba-ticker` (separate PR): dispatch the seal workflow when no run of it is queued/in progress | the seal chain exits when idle and is restarted only by cron (~4% delivery) or by hand | no manual starts; single-writer unchanged (the workflow's own group) | low; draft, needs approval to merge |
| 2 | **Retry a failed capture inside the cycle** (2 retries, 30 s / 60 s) and shorten the next wait after a failure (separate PR) | the only in-loop episode: 3 consecutive failures = a 60 min hole | caps an outage at ~1.5 min instead of 15 min per failure | low; only acts after a failure |
| 3 | **Publish the capture before the cycle's due jobs** (separate PR, flag `CAPTURE_PUSH_FIRST`, **default off**) | commit lag median 214 s is the cycle's job time | lag falls to roughly the push time (tens of seconds) | **research-design change**: the control would lose far fewer games (its latency exclusions are this lag) and the control-vs-t60a contrast shrinks. Owner decision, see 4 |
| 4 | **Pre-warm the successor** (design only): a successor outside the group acquires a runner while the predecessor still runs and waits on the lease release | 8 of 9 gaps are runner waits | removes the wait (the runner is already up) | highest: moves single-writer enforcement from the group to the lease for the overlap; needs a canary; not proposed without approval |
| 5 | A watchdog finding when no committed tick exists for 20 min inside an active window (suggestion) | the 57 min hole was invisible until a seal came out empty | earlier alert only | small |

None of 1-5 changes a protocol, threshold, probability, cost or exposure rule.

## 4. What the lag fix would mean for the two studies (decision for the owner)

The control's *only* difference from t60a is the board rule, and its coverage loss is the commit lag. If the capture is published before the due jobs (fix 3), the lag drops from ~214 s to well under
a minute, the control would lose a game only when its latest tick is younger than the new lag (roughly 5-10% instead of ~50% with 5-7 minute spacing), and the paired comparison would then measure
the availability rule under a much smaller latency regime than the one the control was preregistered in. Recommended handling if approved: apply it at a recorded instant, report both lanes
before / after separately (each seal records the commit time of its board, so the regime is observable per seal), and keep the preregistered rules untouched. Until approved, the flag stays off.

## 5. Reproduce

`PYTHONPATH=research/projection_foundation python -m nba.paper.capture_audit --repo <clone with origin/data-archive> --since 2026-10-20 --out results/issue53_capture`
