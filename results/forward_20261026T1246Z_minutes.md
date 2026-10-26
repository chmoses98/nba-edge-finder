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

## 2. Sample

Eligible games 50; settled 41; archived player rows of settled games 1418 (played 926); rows with no outcome record treated as did-not-play: 0. Frozen comparator found for 926 of 926 played rows; established simulator for 665.

## 3. Minutes (played players, conditional on playing)

### 3a. JRM vs frozen foundation (same feed, identical rows)

n = 926 player-games in 41 games

| engine | MAE | RMSE | bias | CRPS | 80% coverage | PIT variance (uniform = 1) |
|---|---:|---:|---:|---:|---:|---:|
| JRM | 4.875 | 6.384 | +0.070 | 3.4870 | 0.788 | 0.995 |
| frozen (as published) | 5.535 | 7.105 | +0.607 | 3.9680 | 0.737 | 1.140 |

Paired JRM − frozen, game-clustered 95% CI: ΔMAE -0.660 [-0.928, -0.397]; ΔCRPS -0.481 [-0.720, -0.261]

Calibration of the central intervals (nominal 50% / 80% / 90%): JRM 0.523 / 0.788 / 0.896; frozen 0.462 / 0.737 / 0.836.

### 3b. Starters and rotation (the pre-registered guard is the first row)

| group | n | JRM MAE | frozen MAE | JRM bias | frozen bias | paired ΔMAE JRM − frozen [95% CI] |
|---|---:|---:|---:|---:|---:|---|
| established rotation (JRM rank ≤ 8 and p ≥ 0.5) — GUARD | 650 | 4.528 | 5.343 | +0.056 | +0.052 | -0.816 [-1.246, -0.443] |
| actual starters | 410 | 4.687 | 5.883 | -1.007 | -1.212 | -1.195 [-1.834, -0.646] |
| actual non-starters | 516 | 5.023 | 5.258 | +0.925 | +2.052 | -0.234 [-0.453, -0.004] |
| everyone else (rank > 8 or p < 0.5) | 276 | 5.691 | 5.985 | +0.103 | +1.914 | -0.293 [-0.691, +0.128] |

### 3c. Pre-registered decision rules

- Primary (ΔMAE JRM − frozen as published after its gate, n = 926): -0.660 [-0.928, -0.397] → **SUPPORTED**
- Guard (established rotation, CI upper < +0.25): -0.816 [-1.246, -0.443], n = 650 → **PASS**
- Coherence (SD of team-sum ÷ realised team minutes over 82 team-games: JRM 0.015, frozen 0.065) → **PASS**
- Minimum sample: 41 games / 926 played player-games → **MET**

**Pre-registered verdict: PASS.**

### 3d. JRM vs frozen vs established simulator (rows where all three exist)

n = 665 player-games in 38 games. CRPS here is the quantile approximation at the simulator's seven levels, identical for all three.

| engine | MAE | bias | quantile-CRPS | P10–P90 coverage |
|---|---:|---:|---:|---:|
| JRM | 4.596 | +0.153 | 2.6815 | 0.832 |
| frozen | 5.320 | +0.852 | 3.1507 | 0.768 |
| established (sim_rotation) | 8.171 | +2.007 | 4.7165 | 0.671 |

Paired differences (game-clustered 95% CI): ΔMAE JRM − frozen -0.725 [-1.135, -0.380], ΔCRPS -0.469 [-0.756, -0.228]; ΔMAE JRM − established (sim_rotation) -3.576 [-4.370, -2.834], ΔCRPS -2.035 [-2.559, -1.560]

## 4. Participation (every archived player of a settled game; outcome = appeared in the box score)

| engine | n | Brier | log loss | mean p | observed rate | accuracy at 0.5 |
|---|---:|---:|---:|---:|---:|---:|
| JRM (rows with both) | 1418 | 0.1153 | 0.3614 | 0.656 | 0.653 | 0.829 |
| frozen (rows with both) | 1418 | 0.1244 | 0.3795 | 0.696 | 0.653 | 0.812 |
| JRM (rows with all three) | 841 | 0.0878 | 0.2903 | 0.793 | 0.791 | 0.869 |
| frozen (rows with all three) | 841 | 0.0967 | 0.3147 | 0.802 | 0.791 | 0.873 |
| established (rows with all three) | 841 | 0.1707 | 0.5677 | 0.689 | 0.791 | 0.734 |

The simulator is the PURE independent baseline: it has no injury or availability input, its participation_probability is a near-constant (about 0.49 for every player in the archive), so its participation row is a reference floor, not a competing availability model.

Reliability (probability bin → mean predicted / observed rate / n):

| bin | JRM | frozen |
|---|---|---|
| [0.00, 0.05) | 0.01 / 0.05 / 234 | 0.00 / 0.01 / 197 |
| [0.05, 0.20) | 0.14 / 0.37 / 43 | 0.14 / 0.33 / 6 |
| [0.20, 0.50) | 0.37 / 0.41 / 152 | 0.42 / 0.38 / 123 |
| [0.50, 0.80) | 0.66 / 0.60 / 271 | 0.65 / 0.59 / 365 |
| [0.80, 0.95) | 0.88 / 0.81 / 196 | 0.90 / 0.75 / 199 |
| [0.95, 1.00) | 0.98 / 0.98 / 522 | 0.98 / 0.97 / 528 |

## 5. Downstream statistics (played players, conditional on playing; descriptive)

The JRM engine column is the full projection engine run with `PF_NBA_MINUTES_ENGINE=jrm` on the same feed (archived with the snapshot); the frozen column is the same engine with the frozen minutes, i.e. the published values. Only the minutes input differs. The simulator is compared where it has a pre-tip forecast.

| statistic | n | JRM engine MAE | frozen MAE | JRM bias | frozen bias | paired ΔMAE JRM − frozen [95% CI] | simulator MAE (its rows) | JRM / frozen MAE on those rows |
|---|---:|---:|---:|---:|---:|---|---:|---|
| points | 926 | 4.635 | 4.805 | +0.374 | +0.422 | -0.170 [-0.382, +0.002] | 6.200 (n=665) | 4.812 / 5.010 |
| rebounds | 926 | 1.836 | 1.906 | +0.022 | -0.021 | -0.069 [-0.122, -0.022] | 2.411 (n=665) | 1.875 / 1.961 |
| assists | 926 | 1.336 | 1.332 | +0.066 | +0.060 | +0.005 [-0.026, +0.031] | 1.671 (n=665) | 1.381 / 1.372 |
| threes | 926 | 0.837 | 0.841 | +0.068 | +0.058 | -0.004 [-0.019, +0.009] | 1.042 (n=665) | 0.885 / 0.884 |
| pra | 926 | 6.128 | 6.435 | +0.509 | +0.526 | -0.307 [-0.629, -0.036] | — | — |
| fga | 926 | 2.859 | 2.988 | +0.301 | +0.339 | -0.130 [-0.318, +0.020] | — | — |

Note: the engine document is produced by a separate Monte-Carlo run from the one that writes `minutes_given_play_jrm` (the pre-registered minutes quantity), so engine minutes and the scored minutes differ by sampling noise (mean absolute difference below).
 0.16 min over 926 rows.

---
Generated by evaluate_prospective.py. Verdict line: PASS. This is research output: it activates nothing and promotes no projection family.
