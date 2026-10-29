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
| jrm_v2_uniform/20261027T154342Z_jrm_v2.json.gz | 2026-10-27T15:43:42Z | 2026-10-27T15:43:42Z | YES | 139 / 139 | all rules satisfied |
| jrm_v2_uniform/20261028T001414Z_jrm_v2.json.gz | 2026-10-28T00:14:14Z | 2026-10-28T00:14:15Z | YES | 449 / 449 | all rules satisfied |
| jrm_v2_uniform/20261028T014137Z_jrm_v2.json.gz | 2026-10-28T01:41:37Z | 2026-10-28T01:41:38Z | YES | 449 / 449 | all rules satisfied |
| jrm_v2_uniform/20261028T154545Z_jrm_v2.json.gz | 2026-10-28T15:45:45Z | 2026-10-28T15:45:45Z | YES | 414 / 414 | all rules satisfied |
| jrm_v2_uniform/20261028T214346Z_jrm_v2.json.gz | 2026-10-28T21:43:46Z | 2026-10-28T21:43:46Z | YES | 482 / 482 | all rules satisfied |
| jrm_v2_uniform/20261028T224217Z_jrm_v2.json.gz | 2026-10-28T22:42:17Z | 2026-10-28T22:42:18Z | YES | 517 / 517 | all rules satisfied |
| jrm_v2_uniform/20261029T001117Z_jrm_v2.json.gz | 2026-10-29T00:11:17Z | 2026-10-29T00:11:17Z | YES | 209 / 209 | all rules satisfied |
| jrm_v2_uniform/20261029T014039Z_jrm_v2.json.gz | 2026-10-29T01:40:39Z | 2026-10-29T01:40:39Z | YES | 138 / 138 | all rules satisfied |

## 2. Sample

Eligible games 69; settled 66; archived player rows of settled games 2282 (played 1485); rows with no outcome record treated as did-not-play: 0. Frozen comparator found for 1485 of 1485 played rows; established simulator for 1162.

## 3. Minutes (played players, conditional on playing)

### 3a. JRM vs frozen foundation (same feed, identical rows)

n = 1485 player-games in 66 games

| engine | MAE | RMSE | bias | CRPS | 80% coverage | PIT variance (uniform = 1) |
|---|---:|---:|---:|---:|---:|---:|
| JRM | 4.732 | 6.220 | +0.054 | 3.3889 | 0.801 | 0.966 |
| frozen (as published) | 5.256 | 6.790 | +0.446 | 3.7596 | 0.758 | 1.085 |

Paired JRM − frozen, game-clustered 95% CI: ΔMAE -0.524 [-0.721, -0.337]; ΔCRPS -0.371 [-0.526, -0.227]

Calibration of the central intervals (nominal 50% / 80% / 90%): JRM 0.531 / 0.801 / 0.903; frozen 0.481 / 0.758 / 0.861.

### 3b. Starters and rotation (the pre-registered guard is the first row)

| group | n | JRM MAE | frozen MAE | JRM bias | frozen bias | paired ΔMAE JRM − frozen [95% CI] |
|---|---:|---:|---:|---:|---:|---|
| established rotation (JRM rank ≤ 8 and p ≥ 0.5) — GUARD | 1046 | 4.463 | 5.059 | +0.101 | +0.006 | -0.596 [-0.890, -0.348] |
| actual starters | 660 | 4.617 | 5.468 | -0.812 | -1.098 | -0.851 [-1.289, -0.476] |
| actual non-starters | 825 | 4.825 | 5.087 | +0.747 | +1.681 | -0.262 [-0.436, -0.078] |
| everyone else (rank > 8 or p < 0.5) | 439 | 5.374 | 5.727 | -0.056 | +1.494 | -0.352 [-0.664, -0.029] |

### 3c. Pre-registered decision rules

- Primary (ΔMAE JRM − frozen as published after its gate, n = 1485): -0.524 [-0.721, -0.337] → **SUPPORTED**
- Guard (established rotation, CI upper < +0.25): -0.596 [-0.890, -0.348], n = 1046 → **PASS**
- Coherence (SD of team-sum ÷ realised team minutes over 132 team-games: JRM 0.022, frozen 0.061) → **PASS**
- Minimum sample: 66 games / 1485 played player-games → **MET**

**Pre-registered verdict: PASS.**

### 3d. JRM vs frozen vs established simulator (rows where all three exist)

n = 1162 player-games in 63 games. CRPS here is the quantile approximation at the simulator's seven levels, identical for all three.

| engine | MAE | bias | quantile-CRPS | P10–P90 coverage |
|---|---:|---:|---:|---:|
| JRM | 4.513 | +0.174 | 2.6453 | 0.842 |
| frozen | 5.043 | +0.589 | 2.9718 | 0.798 |
| established (sim_rotation) | 7.282 | +0.891 | 4.1891 | 0.719 |

Paired differences (game-clustered 95% CI): ΔMAE JRM − frozen -0.530 [-0.764, -0.318], ΔCRPS -0.327 [-0.499, -0.180]; ΔMAE JRM − established (sim_rotation) -2.769 [-3.274, -2.295], ΔCRPS -1.544 [-1.869, -1.240]

## 4. Participation (every archived player of a settled game; outcome = appeared in the box score)

| engine | n | Brier | log loss | mean p | observed rate | accuracy at 0.5 |
|---|---:|---:|---:|---:|---:|---:|
| JRM (rows with both) | 2282 | 0.1035 | 0.3278 | 0.653 | 0.651 | 0.846 |
| frozen (rows with both) | 2282 | 0.1139 | 0.3443 | 0.694 | 0.651 | 0.825 |
| JRM (rows with all three) | 1453 | 0.0747 | 0.2493 | 0.796 | 0.800 | 0.891 |
| frozen (rows with all three) | 1453 | 0.0818 | 0.2665 | 0.810 | 0.800 | 0.891 |
| established (rows with all three) | 1453 | 0.1502 | 0.4928 | 0.720 | 0.800 | 0.783 |

The simulator is the PURE independent baseline: it has no injury or availability input, its participation_probability is a near-constant (about 0.49 for every player in the archive), so its participation row is a reference floor, not a competing availability model.

Reliability (probability bin → mean predicted / observed rate / n):

| bin | JRM | frozen |
|---|---|---|
| [0.00, 0.05) | 0.01 / 0.04 / 393 | 0.00 / 0.00 / 341 |
| [0.05, 0.20) | 0.14 / 0.32 / 71 | 0.15 / 0.18 / 11 |
| [0.20, 0.50) | 0.37 / 0.38 / 253 | 0.42 / 0.36 / 181 |
| [0.50, 0.80) | 0.65 / 0.59 / 389 | 0.65 / 0.55 / 550 |
| [0.80, 0.95) | 0.89 / 0.84 / 269 | 0.90 / 0.78 / 299 |
| [0.95, 1.00) | 0.98 / 0.99 / 907 | 0.98 / 0.98 / 900 |

## 5. Downstream statistics (played players, conditional on playing; descriptive)

The JRM engine column is the full projection engine run with `PF_NBA_MINUTES_ENGINE=jrm` on the same feed (archived with the snapshot); the frozen column is the same engine with the frozen minutes, i.e. the published values. Only the minutes input differs. The simulator is compared where it has a pre-tip forecast.

| statistic | n | JRM engine MAE | frozen MAE | JRM bias | frozen bias | paired ΔMAE JRM − frozen [95% CI] | simulator MAE (its rows) | JRM / frozen MAE on those rows |
|---|---:|---:|---:|---:|---:|---|---:|---|
| points | 1485 | 4.564 | 4.670 | +0.459 | +0.437 | -0.106 [-0.240, +0.004] | 5.723 (n=1162) | 4.715 / 4.830 |
| rebounds | 1485 | 1.863 | 1.910 | +0.043 | -0.043 | -0.046 [-0.081, -0.015] | 2.310 (n=1162) | 1.912 / 1.967 |
| assists | 1485 | 1.308 | 1.302 | +0.077 | +0.046 | +0.006 [-0.013, +0.022] | 1.561 (n=1162) | 1.352 / 1.343 |
| threes | 1485 | 0.858 | 0.860 | +0.062 | +0.044 | -0.002 [-0.012, +0.007] | 1.009 (n=1162) | 0.907 / 0.906 |
| pra | 1485 | 5.998 | 6.175 | +0.603 | +0.488 | -0.177 [-0.401, -0.003] | — | — |
| fga | 1485 | 2.828 | 2.900 | +0.310 | +0.291 | -0.072 [-0.190, +0.020] | — | — |

Note: the engine document is produced by a separate Monte-Carlo run from the one that writes `minutes_given_play_jrm` (the pre-registered minutes quantity), so engine minutes and the scored minutes differ by sampling noise (mean absolute difference below).
 0.19 min over 1485 rows.

---
Generated by evaluate_prospective.py. Verdict line: PASS. This is research output: it activates nothing and promotes no projection family.
