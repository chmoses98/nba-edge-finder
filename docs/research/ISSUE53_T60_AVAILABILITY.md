# Issue #53 - T-60 availability study (research only; PRIMARY new experiment; dormant until a separate activation change)

**Status.** Code, protocol, docs and results merged (PRs #55, #57). The activation change (this PR, draft until reviewed) lists `t60a` in `SEAL_LANES`; before it merges the sealing chain runs only the `control` lane (`SEAL_LANES: "control"`). No model, rule, stake,
wagering authority or production default changes. The strict T-60 control (`ISSUE53_EXEC_SHADOW_V1`, `exec_shadow_config_v2.json`, sha256 `f84e4067436e2515ea7f35f7417a4e9e66ad69f62ae66ea004a7c6c23244c3e8`)
is byte-identical, keeps its ledger branch (`exec-shadow-seals`), its start (2026-10-24T06:00Z) and its evidence counts. The T-45 study (`ISSUE53_T45_AVAILABILITY.md`) stays inactive and exploratory;
it is not part of the primary comparison.

## 1. What changes, and only what changes

The control requires the **latest tick observed** at or before the T-60 checkpoint D to also be **committed** to the capture branch by D. The measured commit lag (median 211 s, min 188 s, p90 331 s,
max 502 s) makes that a coin flip that does not depend on the checkpoint minute (see `ISSUE53_T45_AVAILABILITY.md`, section 1). The availability study keeps the checkpoint (T-60) and changes the
board-selection rule only:

| | control (strict) | `t60a` (this study) |
|---|---|---|
| decision instant D | tip - 60 min | tip - 60 min |
| board | the latest tick observed at/before D, **and it must be committed by D** | the latest tick **observed AND committed** at/before D (within the 1800 s gap) |
| 900 s quote-age guard, min EV 0.06, PASS-only, p_play >= 0.85, spread <= 0.06, ask side, displayed size, 1 c slippage, whole-order fee, one expression per thesis, exposure caps, settlement | as frozen | **identical** (pinned by test, key by key) |
| study / strategy id | `ISSUE53_EXEC_SHADOW_V1` / `PF_EDGE_STRICT_T60_EXEC_V1` | `ISSUE53_EXEC_SHADOW_T60_AVAIL_V1` / `PF_EDGE_STRICT_T60_AVAIL_V1` |
| ledger | `exec-shadow-seals` (append-only) | `exec-shadow-seals-t60a` (append-only, created by the first publish) |
| version / evidence counts | 2.0.1 / own | 1.0.0 / own (200 decisions, 40 games, positive lower bound under both clustered bootstraps) |
| prospective start | 2026-10-24T06:00Z | **2026-10-27T06:00Z** (a future instant; moved later and versioned if activation slips; no backfill) |
| seal window | D + 600 s .. tip - 600 s | identical |

Protocol file: `research/projection_foundation/nba/paper/exec_shadow_config_t60a_v1.json`; lane table: `nba/paper/seal_windows.py` (`LANES["t60a"]`). Every field is a copy of the control except the ones
named in the file's `differs_from_control_only_in` list; `tests/test_issue53_t60a.py` compares the two files key by key.

**Superset property (tested end to end).** Whenever the control's latest observed tick is committed by D, the availability rule picks the *same tick* and therefore makes the *same selections*. The two
studies differ only on games the control loses to archive latency. This makes the paired comparison exact: the common games must agree contract for contract (`paired.identical_selections_on_common_games`),
and every difference comes from the recovered games.

**No lookahead.** Selection reads only commits dated at or before D; a test makes the rule ignore a board committed one second after D. The seal is computed after D + 600 s and before tip - 600 s.
**Counted iff** (verified offline, post game): all the control's conditions, plus the sealed board was committed at/before D and is the latest tick observed *and* committed at/before D in the FINAL archive
(`BOARD_NOT_COMMITTED_BY_DECISION`, `NOT_LATEST_COMMITTED_TICK_AT_DECISION`, `LATEST_COMMITTED_TICK_UNVERIFIED`). A seal written before the prospective start is a burn-in seal and stays uncounted
(`BEFORE_PROSPECTIVE_START`).

## 2. Reuse, not a new scheduler

One workflow, one chain, one publisher, one concurrency group. The study is a **lane**: `--lanes control[,t60a]` in `seal_chain.py`, `--lane` in `exec_seal.py`, a branch argument in `exec_seal_ci.sh`, a
row in `seal_windows.LANES`. Enabling it is adding `t60a` to `SEAL_LANES`: one extra sealer call per open window in the same running chain, no extra job. The PR rehearsal now runs both lanes dry
(`REHEARSAL_LANES: "control,t60a"`) on real archived data; the watchdog reads the `t60a` ledger best-effort for window / MISSED findings (`--seals-t60a`). The control's seal is pinned by a golden test
(seal id, candidate hash and normalised body hash unchanged).

## 3. The chain handover gap (investigation and fix)

**Measured.** The chain is one long job; its successor is dispatched before it ends but sits in the single concurrency group until the predecessor finishes, and then waits for a hosted runner.

| handover | runner requested (predecessor released the group) | job starts | gap |
|---|---|---|---|
| Oct 22 (run 6 -> 8; job 120088545592) | 21:05:17Z (job requested) | 21:23:28Z | 18 min 11 s |
| Oct 23 (run 12 -> 14; job 120604497192) | 19:08:56Z (job requested) | 19:16:40Z | 7 min 44 s |
| cold start by manual dispatch (run 12; job 120457612324) | 14:04:15Z (job requested) | 14:27:17Z | 23 min 2 s |

**Does earlier dispatch help?** No. A concurrent successor cannot start while the predecessor holds the group, so dispatching it earlier only lengthens the time it is "pending" (run 14 was created
18:38Z, was released at 19:08:56Z and started 19:16:40Z; run 8 likewise waited 30 minutes in the group and then 18 minutes for a runner). The part that costs sealing time is the *runner queue after the predecessor ends* (8-23 min, outside our control), and it is not shortened by dispatching earlier. Cancelling the
predecessor to let the successor start would interrupt the running control, which was ruled out, and a second concurrent chain would double the cost and publish twice.

**Fix (narrow, tested).** Choose *when* to hand over so that the unavoidable gap falls in dead time: the chain runs at least `--retire-after-min 240`, then retires at the first **quiet moment** -
no lane has a window open or closed-and-unsealed (waiting for its MISSED marker), and no window opens within `--quiet-lead-min 45` - dispatching its successor and ending after the current iteration
has sealed and durably published. Safety bounds: the successor is queued at the latest by 315 min, the hard cap is 335 min (job timeout 350), and if the dispatch fails the chain keeps running to the cap
as before (cron bootstrap remains the fallback). Cost is unchanged (the same one chain, a run that is 5-80 minutes shorter than the maximum; no extra runs). The new watchdog finding
`SEAL_CHAIN_STALLED` raises when no run of the chain is executing and the oldest queued run has waited 10 minutes or more (a queued run otherwise counts as 'alive' for the dead-man check and would hide exactly
this gap), so a bad runner queue is visible instead of silent. Tests
(`tests/test_issue53_chain.py`) cover: hand over at the first quiet moment and never inside or just before a window, a quiet chain still runs the minimum, no quiet moment -> successor by 315 and end at the
cap, a failed dispatch, nothing to hand over, and the monitor finding.

Residual risk: a runner queue that runs into an *opening* window. It is bounded by the 45-minute lead (observed queues: 8-23 min) and is alerted, not hidden.

## 4. Activation is a separate change

The activation PR changes exactly one setting, `SEAL_LANES: "control"` -> `"control,t60a"` (plus the test that pins it). It stays a draft until the owner reviews it; nothing is merged or activated before that.

Readiness shown before activation: (1) the pretip dry rehearsal of both lanes on a runner on real archived data, publishing nothing (PR #57 CI); (2) an offline, read-only verification of t60a seals built from archived data: `verify_seal` / `evaluate` and the settlement join run against a scratch ledger, nothing published, no archive written, no historical result counted as prospective (`results/issue53_t60a/offline_verification.md`).

To be verified **after** activation (burn-in seals before 2026-10-27T06:00Z are uncounted by rule, `BEFORE_PROSPECTIVE_START`): the first real publication bootstraps `exec-shadow-seals-t60a` through the Git Data API (server commit time, fast-forward only, additions only, deadline against the server time); the seals are immutable (write-once paths); `verify_seal` / `evaluate` and the settlement join behave as in the offline run. If activation slips past 2026-10-27T06:00Z the protocol is versioned and the start moved to a later future instant before any countable seal.

## 5. Comparison, measured on the archive so far

`python -m nba.paper.compare_lanes --archive <projection-data> --market <data-archive> --repo <git repo> --out results/issue53_t60a [--include-t45]`; output in `results/issue53_t60a/lane_comparison.{md,json}`.
Reported per lane and side by side: coverage and exclusions, decision instants usable (games sharing a tip share a board, so the independent unit is the instant), predicted EV, CLV, settled P&L, quote age at
decision, ask drift after D, selection overlap, **paired per-game differences** on the same games (with a seeded, game-clustered bootstrap once at least eight games exist), and **projection accuracy on every
eligible game** (`accuracy_all_games`: TRADED, NO_TRADE, latency-excluded and unsealed games all stay in the denominator; nothing in the sealing path gates the forecast scorecard).

Retrospective reconstruction, 16 regular-season games 2026-10-20..23 (11 distinct decision instants; uncounted, descriptive; archives as of 2026-10-23T19:47Z):

| | control (T-60 strict) | `t60a` (T-60 availability) |
|---|---|---|
| games with a decision evaluated | 6 / 16 (38%) | **16 / 16 (100%)** |
| decision instants usable | 5 / 11 | **11 / 11** |
| excluded by archive latency | 10 | 0 |
| games traded / trades | 5 / 18 | 11 / 42 |
| mean predicted EV per trade | 0.156 | 0.168 |
| settled net P&L (ROI on outlay) | -$0.62 (-7.2%) | +$0.36 (+1.8%) |
| mean CLV, cents | -1.14 | +0.63 |
| quote age at decision, median / p90 | 724 s / 724 s* | 557 s / 724 s |
| mean ask drift after D, cents (share adverse) | -0.11 (5.6%) | +1.07 (14.3%) |

\* the control's few usable games share boards (games that tip together share one board).

**Paired, same games.** Both lanes evaluated 6 games: on all 6 the two studies chose the identical board and the identical 18 contracts (the superset property holds on real data), with identical P&L (-$0.62) and CLV
(-1.14 c). The control evaluated no game that `t60a` did not. All the difference comes from the **10 games the control loses to archive latency**: 24 trades, +$0.98, CLV +1.96 c. The per-game mean
difference in net P&L (`t60a` minus control, 16 games) is +$0.06 with a seeded game-clustered bootstrap interval of [-$0.21, +$0.33]: no evidence of anything, as expected from 16 games.

**Projection accuracy.** Scored on all 16 eligible games (3,122 challenger forecasts) whatever the lane did: control status TRADED 5, EVALUATED_NO_TRADE 1, EXCLUDED_ARCHIVE_LATENCY 10; `t60a` TRADED 11,
EVALUATED_NO_TRADE 5. A latency exclusion, a NO_TRADE or a missing board never removes a game from the accuracy evaluation.

**Expected improvement in research coverage.** Games evaluated 6 -> 16 of 16 (about 2.7x); decision instants (the independent unit) 5 -> 11 of 11; decisions per evaluated game are unchanged on the
common games by construction. If those ratios held, the 200-decision / 40-game minimum, which needs about 25 days under the control at roughly 7.5 games a day, would take on the order of 10 days under
`t60a` (very wide uncertainty: 11 independent instants). The exploratory T-45 lane gives the same coverage (16 / 16) and is shown only in its own section of the full output.


## 6. What the numbers can and cannot say

* Coverage and exclusions are mechanics and are reliable; P&L, ROI and CLV over a handful of games are anecdotes and **not** evidence of an edge or of a cost of the rule.
* Archival quotes are displayed quotes: nothing here shows that an order would have filled at the sealed price or size. The real, measured cost of the rule is quote age at D (the 900 s guard bounds it)
  and the ask drift to the next board, both reported.
* Both studies use the same archive and the same forecasts; the recovered games are the only difference, so the two results are strongly dependent and are never pooled or added.
* The T-45 study is exploratory and inactive; it is included in the comparison output only with `--include-t45`, in its own section.
