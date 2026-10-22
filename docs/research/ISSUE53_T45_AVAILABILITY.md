# Issue #53 - T-45 availability study (research only; PROPOSED, not activated)

**Status.** Draft. Nothing here is enabled: the sealing chain still runs only the `control` lane (`SEAL_LANES: "control"`). No model, rule, stake, wagering authority or production
default changes; the strict T-60 study (`ISSUE53_EXEC_SHADOW_V1`, `exec_shadow_config_v2.json`, sha256 `f84e4067...`) is byte-identical and keeps its own ledger branch
(`exec-shadow-seals`), start (2026-10-24T06:00Z) and evidence counts. No evidence is backfilled: the new study's prospective start is **2026-10-27T06:00Z** and, if approval is later,
it is amended (versioned) before any countable seal exists.

## 1. Diagnosis: four clocks (`nba/paper/latency_diag.py`, `results/issue53_t45/latency_diagnosis.{md,json}`)

| clock | meaning | measured |
|---|---|---|
| OBSERVED | capture tick stamp (the capture worker finished its Kalshi fetch) | ticks every 5-15 min in game hours (p10 300 s, median 600 s, p90 900 s), uniform phase |
| COMMITTED | git commit time of the commit that added the tick's file to `data-archive` | **lag after OBSERVED: min 188 s, median 211 s, p90 331 s, max 502 s** (377 live ticks, 2026-10-18..22) |
| VISIBLE | when a sealer can read it | >= COMMITTED; bounded by the chain's 90 s poll (not recorded anywhere) |
| DECISION | the instant D at which an order could really be placed | tip - offset |

The control rule ("the latest tick OBSERVED at/before D must also be COMMITTED at/before D, no fallback") fails whenever the latest tick is younger than its own ~211 s lag. With
5-15 minute spacing and a uniform phase that is a coin flip **that does not depend on the checkpoint minute**:

| offset | games with a usable board, control rule | same games, availability rule (latest tick COMMITTED by D, age <= 900 s) |
|---|---|---|
| T-60 | 5 / 14 | 14 / 14 |
| T-45 | 5 / 14 | 14 / 14 |
| T-30, T-35, T-40, T-50, T-55 | 5, 5, 3, 5, 3 / 14 | 13, 13, 11, 13, 11 / 14 |

So **T-45 by itself does not recover anything** (T-60 and T-45 are identical under the control rule); the recovery comes from the board rule. The study therefore changes exactly two
things relative to the control - the decision instant (T-45) and the board rule - and a retrospective matched pair (below) separates the two.

Why T-45: it was the offset the owner asked to investigate; the diagnosis shows T-60 and T-45 are equivalent for coverage, T-45 puts the order one quarter hour closer to tip while the
decision stays well inside the pre-tip sealing window, and the offset was fixed **before any T-45 outcome existed** (not tuned on P&L).

## 2. The preregistered study (`nba/paper/exec_shadow_config_t45_v1.json`, v1.0.0)

* study `ISSUE53_EXEC_SHADOW_T45_AVAIL_V1`, strategy `PF_EDGE_STRICT_T45_AVAIL_V1`, own ledger branch `exec-shadow-seals-t45`, own start, own evidence counts (200 decisions / 40 games, positive
  lower bound under both clustered bootstraps), own verdicts; **never pooled** with the control.
* every numeric rule, threshold, cost and exposure cap is copied verbatim from the control (pinned by a test): min EV 0.06, PASS-only, p_play >= 0.85, spread <= 0.06, ask side, displayed
  size, 1 cent slippage, whole-order fee, one expression per thesis, the same caps, `max_quote_age_s` 900.
* board rule `latest_committed_by_decision`: the latest tick committed to the capture branch AND observed at/before D (within the 1800 s gap); nothing committed after D is ever read; a
  board older than 900 s makes every candidate stale; forecasts must be generated, archived and committed at/before D (as in the control). No grace window, no later horizon.
* sealing: the same sealer and chain. The window opens D + 300 s (the board is chosen from commits dated <= D, so no capture-lag wait is needed; 300 s only lets a commit dated just before D
  be pushed and visible) and closes tip - 600 s (30 minutes, ~20 polls). Seals are published through the same Git Data API publisher to `exec-shadow-seals-t45`.
* counted iff (verified offline, post-game): all the control's conditions with the T-45 window, **plus** the sealed board was committed at/before D and is the latest tick observed AND
  committed at/before D in the FINAL archive (`NOT_LATEST_COMMITTED_TICK_AT_DECISION`, `BOARD_NOT_COMMITTED_BY_DECISION`). A commit dated <= D but pushed late would change the final
  archive's answer and the seal is then uncounted rather than silently accepted.
* **no lookahead**, by construction and by verification: selection reads only commits dated <= D; the seal is computed after D and before tip - 10 min; a test makes the rule ignore any
  board committed one second after D.

## 3. Reuse, not a new scheduler

One workflow, one chain, one publisher. The change is a **lane**: `--lanes control[,t45]` in `seal_chain.py`, `--lane` in `exec_seal.py`, a branch argument in `exec_seal_ci.sh`, a lane table in
`seal_windows.py`. `SEAL_LANES` stays `control`; the PR's dry rehearsal runs **both** lanes on real archived data (no publication). Activation = adding `t45` to `SEAL_LANES` in an approved PR
(a one-line change; the lane is then sealed by the same running chain: one extra sealer call per open window, no extra job or scheduler). The watchdog's dead-man check also reads the T-45 ledger's window / MISSED findings.
The control's behaviour is pinned by a golden test (same seal id, candidate hash and normalised body hash as before the change).

## 4. Projection accuracy is independent of lanes

Forecast accuracy (`pf_core.prospective` scorecard: CRPS / Brier / MAE / calibration) is computed on **every game with settled forecasts**, regardless of trade decision, market, seal or lane
(`compare_lanes.accuracy_all_games`). TRADED, NO_TRADE, excluded-for-latency and unsealed games are all in the denominator (tested); in the current archive that is 14 games and 2,739 challenger
forecasts, against 4-9 games with a trade. Nothing in the sealing path gates or filters the existing forecast scoring.

## 5. Comparison without mixing (`nba/paper/compare_lanes.py`, `results/issue53_t45/lane_comparison.{md,json}`)

Per lane, side by side: coverage and exclusions (by archive latency / no data / evaluated-no-trade), decision instants usable, predicted EV, CLV, settled P&L, hit rate, board age and ask
drift after D, and the overlap of selections. Prospective, counted evidence will be read only from each lane's own sealed ledger (`--seals-control`, `--seals-t45`). Until then every row is a
labelled **retrospective reconstruction** (the lane's sealer run over past games with the lane's commit-time filters; uncounted) and two **matched comparators** that change one thing
at a time (T-60 + availability, T-45 + control rule).

Retrospective result, 14 regular-season games 2026-10-20..22 (9 distinct decision instants; games that tip together share a board, so coverage is clustered):

| | control (T-60, strict) | T-45 availability | comparator T-60 + availability | comparator T-45 + strict |
|---|---|---|---|---|
| games with a decision evaluated | 5 / 14 | 14 / 14 | 14 / 14 | 5 / 14 |
| decision instants usable | 4 / 9 | 9 / 9 | 9 / 9 | 4 / 9 |
| excluded by archive latency | 9 | 0 | 0 | 9 |
| games traded / trades | 4 / 15 | 9 / 36 | 9 / 36 | 4 / 15 |
| mean predicted EV per trade | 0.165 | 0.177 | 0.179 | 0.171 |
| settled net P&L (ROI on outlay) | +$0.80 (11.1%) | -$1.61 (-9.7%) | +$0.40 (2.4%) | +$0.97 (13.8%) |
| mean CLV, cents | -1.03 | +0.06 | +0.96 | -1.27 |
| board age at decision, median / p90 | 724 s / 724 s* | 497 s / 724 s | 557 s / 724 s | 724 s / 724 s* |
| mean ask drift after D, cents | +0.07 | +0.61 | +1.36 | +1.40 |

\* four traded control games share one tip time, hence one board.

**Reading.** The matched comparators show the coverage gain comes from the board rule, not the offset (T-60 + availability = T-45 + availability = 14/14; the strict rule is 5/14 at both
offsets). Coverage and exclusions are mechanics and are reliable; the P&L, ROI and CLV columns are anecdotes of 4-9 games and **must not be read as an edge or as a cost of the rule**
(the extra T-45 games happened to lose money; the control's few games happened to win). The cost of the rule that is real and measured is board age: ~8 minutes at the decision instant
(median 497 s) against a control that can only trade the boards that happened to be young, and an ask that moved a mean 0.6 cent (83% of trades not adversely) before the next board.

## 6. Expected improvement in research coverage

| measure | strict control | T-45 availability |
|---|---|---|
| usable decision instants (retrospective) | 4 / 9 (44%; Wilson 95% 19-73%) | 9 / 9 (100%; Wilson 95% 70-100%) |
| games with a decision evaluated | 36% (5 / 14) | 100% (14 / 14) |
| decisions per game (retrospective) | 1.07 | 2.57 |
| games with a trade | 29% | 64% |

If those ratios held (they come from 9 independent instants), the 200-decision / 40-game minimum, at ~7.5 games per day, would take **roughly 25 days under the control and roughly 10 days under
T-45 (about 2.4x faster)**; the 40-game traded minimum ~19 vs ~8 days. These are order-of-magnitude figures with very wide intervals; they say the control can take most of a season to
reach its minimum, not when either will.

## 7. Risks and limits

* **Two changes at once** (offset and rule) - separated only retrospectively by the matched comparators.
* **Older quotes**: the board is a median ~8 minutes old at D; the 900 s guard, the displayed-size rule, 1 cent slippage and the drift diagnostic bound but do not remove that. A live fill is not
  observable here: this is a shadow study.
* **Visibility lag**: a commit dated <= D that becomes visible after D + 300 s makes the seal fail verification (uncounted). The expected loss is small and measurable (every seal records the
  commit time and tick).
* **Same archive, same model**: both lanes use the same forecasts; the lanes differ only in the board and the instant, so their results are strongly correlated and cannot be added.
* **Branch creation**: `exec-shadow-seals-t45` is created by the first publish after activation; the self-test workflow already proved the bootstrap path on a throw-away branch.
* **Prospective start** 2026-10-27T06:00Z is a placeholder for the approval date: if activation is later than the start, the protocol is versioned and a new later start set before any
  countable seal.

## 8. Approval checklist (nothing below has been done)

1. Merge this PR (adds code, protocol, docs, results; `SEAL_LANES` unchanged).
2. Approve the protocol as written (or amend: offset, guard, start) - no value is changed after approval without a new version.
3. Activate: a one-line PR changing `SEAL_LANES: "control"` to `"control,t45"` (and, if needed, the start date); the burn-in seals before the start are uncounted by rule.
4. After activation: confirm the first publish created `exec-shadow-seals-t45`, verify server timestamps as for the control, and keep reporting lost opportunities separately.
