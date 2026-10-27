# Prospective evaluation of the archived pre-tip forecasts (joint rotation model v2, uniform allocation)

## 1. Eligibility of the archive

| snapshot | archived | branch commit (independent clock) | scored | eligible rows / in file | reason |
|---|---|---|---|---:|---|
| jrm_v1/20261020T223327Z_jrm_v1.json.gz | 2026-10-20T22:33:27Z | 2026-10-20T22:33:41Z | no | 0 / 448 | F1 version None is not the validated v2; F1 design_frozen_at is not the v2 freeze commit; F1 allocation not recorded (the file predates the field: variance-weighted variant, ERRATA.md); F3 research/projection_foundation/minutes_rebuild/jrm.py@6af0202: level E False, default uniform False |
| jrm_v2/20261020T230246Z_jrm_v2.json.gz | 2026-10-20T23:02:46Z | 2026-10-20T23:02:51Z | no | 0 / 414 | F1 allocation not recorded (the file predates the field: variance-weighted variant, ERRATA.md); F3 research/projection_foundation/minutes_rebuild/jrm.py@9c232cf: level E True, default uniform False |
| jrm_v2_uniform/20261020T230949Z_jrm_v2.json.gz | 2026-10-20T23:09:49Z | 2026-10-20T23:09:49Z | YES | 414 / 414 | all rules satisfied |
| jrm_v2_uniform/20261021T000501Z_jrm_v2.json.gz | 2026-10-21T00:05:01Z | 2026-10-21T00:05:21Z | YES | 414 / 414 | all rules satisfied |
| jrm_v2_uniform/20261021T200553Z_jrm_v2.json.gz | 2026-10-21T20:05:53Z | 2026-10-21T20:05:53Z | YES | 414 / 414 | all rules satisfied |
| jrm_v2_uniform/20261021T221532Z_jrm_v2.json.gz | 2026-10-21T22:15:32Z | 2026-10-21T22:15:32Z | YES | 448 / 448 | all rules satisfied |
| jrm_v2_uniform/20261022T150614Z_jrm_v2.json.gz | 2026-10-22T15:06:14Z | 2026-10-22T15:06:14Z | YES | 68 / 68 | all rules satisfied |
| jrm_v2_uniform/20261022T200500Z_jrm_v2.json.gz | 2026-10-22T20:05:00Z | 2026-10-22T20:05:00Z | YES | 309 / 309 | all rules satisfied |
| jrm_v2_uniform/20261022T221530Z_jrm_v2.json.gz | 2026-10-22T22:15:30Z | 2026-10-22T22:15:30Z | YES | 309 / 309 | all rules satisfied |
| jrm_v2_uniform/20261023T170507Z_jrm_v2.json.gz | 2026-10-23T17:05:07Z | 2026-10-23T17:05:07Z | YES | 450 / 450 | all rules satisfied |
| jrm_v2_uniform/20261023T191505Z_jrm_v2.json.gz | 2026-10-23T19:15:05Z | 2026-10-23T19:15:06Z | YES | 588 / 588 | all rules satisfied |
| jrm_v2_uniform/20261023T221652Z_jrm_v2.json.gz | 2026-10-23T22:16:52Z | 2026-10-23T22:16:53Z | YES | 658 / 658 | all rules satisfied |
| jrm_v2_uniform/20261025T015950Z_jrm_v2.json.gz | 2026-10-25T01:59:50Z | 2026-10-25T01:59:50Z | YES | 243 / 278 | all rules satisfied |
| jrm_v2_uniform/20261025T154243Z_jrm_v2.json.gz | 2026-10-25T15:42:43Z | 2026-10-25T15:42:44Z | YES | 243 / 243 | all rules satisfied |
| jrm_v2_uniform/20261025T214300Z_jrm_v2.json.gz | 2026-10-25T21:43:00Z | 2026-10-25T21:43:00Z | YES | 482 / 482 | all rules satisfied |
| jrm_v2_uniform/20261025T224243Z_jrm_v2.json.gz | 2026-10-25T22:42:43Z | 2026-10-25T22:42:43Z | YES | 482 / 482 | all rules satisfied |
| jrm_v2_uniform/20261026T001501Z_jrm_v2.json.gz | 2026-10-26T00:15:01Z | 2026-10-26T00:15:02Z | YES | 345 / 345 | all rules satisfied |
| jrm_v2_uniform/20261026T014246Z_jrm_v2.json.gz | 2026-10-26T01:42:46Z | 2026-10-26T01:42:47Z | YES | 310 / 310 | all rules satisfied |
| jrm_v2_uniform/20261026T154230Z_jrm_v2.json.gz | 2026-10-26T15:42:30Z | 2026-10-26T15:42:30Z | YES | 310 / 310 | all rules satisfied |
| jrm_v2_uniform/20261026T214718Z_jrm_v2.json.gz | 2026-10-26T21:47:18Z | 2026-10-26T21:47:19Z | YES | 414 / 414 | all rules satisfied |
| jrm_v2_uniform/20261026T224125Z_jrm_v2.json.gz | 2026-10-26T22:41:25Z | 2026-10-26T22:41:26Z | YES | 449 / 449 | all rules satisfied |
| jrm_v2_uniform/20261027T001344Z_jrm_v2.json.gz | 2026-10-27T00:13:44Z | 2026-10-27T00:13:44Z | YES | 245 / 245 | all rules satisfied |
| jrm_v2_uniform/20261027T014037Z_jrm_v2.json.gz | 2026-10-27T01:40:37Z | 2026-10-27T01:40:37Z | YES | 174 / 174 | all rules satisfied |

## 2. Sample

Eligible games 54; settled 50; archived player rows of settled games 1728 (played 1136); rows with no outcome record treated as did-not-play: 0. Frozen comparator found for 1136 of 1136 played rows; established simulator for 849.

## 3. Minutes (played players, conditional on playing)

### 3a. JRM vs frozen foundation (same feed, identical rows)

n = 1136 player-games in 50 games

| engine | MAE | RMSE | bias | CRPS | 80% coverage | PIT variance (uniform = 1) |
|---|---:|---:|---:|---:|---:|---:|
| JRM | 4.893 | 6.441 | +0.107 | 3.5073 | 0.787 | 1.001 |
| frozen (as published) | 5.520 | 7.105 | +0.535 | 3.9545 | 0.735 | 1.138 |

Paired JRM − frozen, game-clustered 95% CI: ΔMAE -0.626 [-0.853, -0.424]; ΔCRPS -0.447 [-0.634, -0.283]

Calibration of the central intervals (nominal 50% / 80% / 90%): JRM 0.516 / 0.787 / 0.897; frozen 0.463 / 0.735 / 0.839.

### 3b. Starters and rotation (the pre-registered guard is the first row)

| group | n | JRM MAE | frozen MAE | JRM bias | frozen bias | paired ΔMAE JRM − frozen [95% CI] |
|---|---:|---:|---:|---:|---:|---|
| established rotation (JRM rank ≤ 8 and p ≥ 0.5) — GUARD | 792 | 4.587 | 5.327 | +0.128 | +0.017 | -0.741 [-1.109, -0.454] |
| actual starters | 500 | 4.675 | 5.763 | -0.939 | -1.238 | -1.088 [-1.636, -0.654] |
| actual non-starters | 636 | 5.065 | 5.328 | +0.929 | +1.929 | -0.263 [-0.464, -0.041] |
| everyone else (rank > 8 or p < 0.5) | 344 | 5.600 | 5.962 | +0.058 | +1.729 | -0.363 [-0.730, +0.025] |

### 3c. Pre-registered decision rules

- Primary (ΔMAE JRM − frozen as published after its gate, n = 1136): -0.626 [-0.853, -0.424] → **SUPPORTED**
- Guard (established rotation, CI upper < +0.25): -0.741 [-1.109, -0.454], n = 792 → **PASS**
- Coherence (SD of team-sum ÷ realised team minutes over 100 team-games: JRM 0.019, frozen 0.063) → **PASS**
- Minimum sample: 50 games / 1136 played player-games → **MET**

**Pre-registered verdict: PASS.**

### 3d. JRM vs frozen vs established simulator (rows where all three exist)

n = 849 player-games in 47 games. CRPS here is the quantile approximation at the simulator's seven levels, identical for all three.

| engine | MAE | bias | quantile-CRPS | P10–P90 coverage |
|---|---:|---:|---:|---:|
| JRM | 4.643 | +0.285 | 2.7169 | 0.833 |
| frozen | 5.320 | +0.795 | 3.1405 | 0.771 |
| established (sim_rotation) | 7.885 | +1.650 | 4.5320 | 0.690 |

Paired differences (game-clustered 95% CI): ΔMAE JRM − frozen -0.676 [-0.998, -0.400], ΔCRPS -0.424 [-0.648, -0.226]; ΔMAE JRM − established (sim_rotation) -3.242 [-3.936, -2.674], ΔCRPS -1.815 [-2.286, -1.437]

## 4. Participation (every archived player of a settled game; outcome = appeared in the box score)

| engine | n | Brier | log loss | mean p | observed rate | accuracy at 0.5 |
|---|---:|---:|---:|---:|---:|---:|
| JRM (rows with both) | 1728 | 0.1105 | 0.3446 | 0.656 | 0.657 | 0.833 |
| frozen (rows with both) | 1728 | 0.1192 | 0.3618 | 0.699 | 0.657 | 0.821 |
| JRM (rows with all three) | 1061 | 0.0808 | 0.2665 | 0.796 | 0.800 | 0.880 |
| frozen (rows with all three) | 1061 | 0.0875 | 0.2855 | 0.809 | 0.800 | 0.886 |
| established (rows with all three) | 1061 | 0.1606 | 0.5298 | 0.703 | 0.800 | 0.760 |

The simulator is the PURE independent baseline: it has no injury or availability input, its participation_probability is a near-constant (about 0.49 for every player in the archive), so its participation row is a reference floor, not a competing availability model.

Reliability (probability bin → mean predicted / observed rate / n):

| bin | JRM | frozen |
|---|---|---|
| [0.00, 0.05) | 0.01 / 0.04 / 289 | 0.00 / 0.00 / 244 |
| [0.05, 0.20) | 0.14 / 0.38 / 53 | 0.14 / 0.29 / 7 |
| [0.20, 0.50) | 0.37 / 0.43 / 187 | 0.42 / 0.36 / 137 |
| [0.50, 0.80) | 0.66 / 0.59 / 315 | 0.65 / 0.58 / 437 |
| [0.80, 0.95) | 0.88 / 0.83 / 227 | 0.90 / 0.76 / 243 |
| [0.95, 1.00) | 0.98 / 0.99 / 657 | 0.98 / 0.98 / 660 |

## 5. Downstream statistics (played players, conditional on playing; descriptive)

The JRM engine column is the full projection engine run with `PF_NBA_MINUTES_ENGINE=jrm` on the same feed (archived with the snapshot); the frozen column is the same engine with the frozen minutes, i.e. the published values. Only the minutes input differs. The simulator is compared where it has a pre-tip forecast.

| statistic | n | JRM engine MAE | frozen MAE | JRM bias | frozen bias | paired ΔMAE JRM − frozen [95% CI] | simulator MAE (its rows) | JRM / frozen MAE on those rows |
|---|---:|---:|---:|---:|---:|---|---:|---|
| points | 1136 | 4.570 | 4.704 | +0.491 | +0.440 | -0.134 [-0.310, +0.006] | 5.943 (n=849) | 4.719 / 4.872 |
| rebounds | 1136 | 1.874 | 1.935 | +0.019 | -0.049 | -0.061 [-0.105, -0.024] | 2.409 (n=849) | 1.926 / 2.002 |
| assists | 1136 | 1.311 | 1.304 | +0.087 | +0.062 | +0.006 [-0.018, +0.029] | 1.614 (n=849) | 1.352 / 1.342 |
| threes | 1136 | 0.841 | 0.843 | +0.072 | +0.053 | -0.002 [-0.014, +0.009] | 1.015 (n=849) | 0.887 / 0.885 |
| pra | 1136 | 6.127 | 6.378 | +0.649 | +0.519 | -0.252 [-0.532, -0.032] | — | — |
| fga | 1136 | 2.868 | 2.962 | +0.343 | +0.305 | -0.094 [-0.246, +0.028] | — | — |

Note: the engine document is produced by a separate Monte-Carlo run from the one that writes `minutes_given_play_jrm` (the pre-registered minutes quantity), so engine minutes and the scored minutes differ by sampling noise (mean absolute difference below).
 0.17 min over 1136 rows.

---
Generated by evaluate_prospective.py. Verdict line: PASS. This is research output: it activates nothing and promotes no projection family.
