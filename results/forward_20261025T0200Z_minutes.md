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

## 2. Sample

Eligible games 41; settled 27; archived player rows of settled games 933 (played 621); rows with no outcome record treated as did-not-play: 7. Frozen comparator found for 621 of 621 played rows; established simulator for 440.

## 3. Minutes (played players, conditional on playing)

### 3a. JRM vs frozen foundation (same feed, identical rows)

n = 621 player-games in 27 games

| engine | MAE | RMSE | bias | CRPS | 80% coverage | PIT variance (uniform = 1) |
|---|---:|---:|---:|---:|---:|---:|
| JRM | 5.012 | 6.501 | +0.119 | 3.5711 | 0.770 | 1.029 |
| frozen (as published) | 5.591 | 7.140 | +0.243 | 3.9847 | 0.726 | 1.160 |

Paired JRM − frozen, game-clustered 95% CI: ΔMAE -0.579 [-0.827, -0.322]; ΔCRPS -0.414 [-0.618, -0.213]

Calibration of the central intervals (nominal 50% / 80% / 90%): JRM 0.510 / 0.770 / 0.900; frozen 0.452 / 0.726 / 0.834.

### 3b. Starters and rotation (the pre-registered guard is the first row)

| group | n | JRM MAE | frozen MAE | JRM bias | frozen bias | paired ΔMAE JRM − frozen [95% CI] |
|---|---:|---:|---:|---:|---:|---|
| established rotation (JRM rank ≤ 8 and p ≥ 0.5) — GUARD | 430 | 4.687 | 5.297 | +0.155 | -0.621 | -0.610 [-0.931, -0.288] |
| actual starters | 270 | 4.803 | 5.807 | -1.041 | -2.299 | -1.004 [-1.529, -0.501] |
| actual non-starters | 351 | 5.172 | 5.425 | +1.011 | +2.198 | -0.252 [-0.522, +0.054] |
| everyone else (rank > 8 or p < 0.5) | 191 | 5.743 | 6.253 | +0.036 | +2.187 | -0.509 [-0.985, -0.009] |

### 3c. Pre-registered decision rules

- Primary (ΔMAE JRM − frozen as published after its gate, n = 621): -0.579 [-0.827, -0.322] → **SUPPORTED**
- Guard (established rotation, CI upper < +0.25): -0.610 [-0.931, -0.288], n = 430 → **PASS**
- Coherence (SD of team-sum ÷ realised team minutes over 54 team-games: JRM 0.004, frozen 0.057) → **PASS**
- Minimum sample: 27 games / 621 played player-games → **MET**

**Pre-registered verdict: PASS.**

### 3d. JRM vs frozen vs established simulator (rows where all three exist)

n = 440 player-games in 26 games. CRPS here is the quantile approximation at the simulator's seven levels, identical for all three.

| engine | MAE | bias | quantile-CRPS | P10–P90 coverage |
|---|---:|---:|---:|---:|
| JRM | 4.722 | +0.398 | 2.7353 | 0.818 |
| frozen | 5.215 | +0.565 | 3.0431 | 0.773 |
| established (sim_rotation) | 9.042 | +4.145 | 5.3027 | 0.614 |

Paired differences (game-clustered 95% CI): ΔMAE JRM − frozen -0.493 [-0.774, -0.218], ΔCRPS -0.308 [-0.523, -0.126]; ΔMAE JRM − established (sim_rotation) -4.319 [-5.352, -3.370], ΔCRPS -2.567 [-3.250, -1.944]

## 4. Participation (every archived player of a settled game; outcome = appeared in the box score)

| engine | n | Brier | log loss | mean p | observed rate | accuracy at 0.5 |
|---|---:|---:|---:|---:|---:|---:|
| JRM (rows with both) | 933 | 0.1095 | 0.3430 | 0.661 | 0.666 | 0.833 |
| frozen (rows with both) | 933 | 0.1156 | 0.3550 | 0.721 | 0.666 | 0.831 |
| JRM (rows with all three) | 550 | 0.0835 | 0.2739 | 0.805 | 0.800 | 0.875 |
| frozen (rows with all three) | 550 | 0.0889 | 0.2984 | 0.835 | 0.800 | 0.891 |
| established (rows with all three) | 550 | 0.1727 | 0.5340 | 0.649 | 0.800 | 0.696 |

The simulator is the PURE independent baseline: it has no injury or availability input, its participation_probability is a near-constant (about 0.49 for every player in the archive), so its participation row is a reference floor, not a competing availability model.

Reliability (probability bin → mean predicted / observed rate / n):

| bin | JRM | frozen |
|---|---|---|
| [0.00, 0.05) | 0.01 / 0.05 / 161 | 0.00 / 0.00 / 133 |
| [0.05, 0.20) | 0.13 / 0.40 / 30 | 0.14 / 0.33 / 3 |
| [0.20, 0.50) | 0.36 / 0.47 / 89 | 0.43 / 0.31 / 54 |
| [0.50, 0.80) | 0.67 / 0.59 / 161 | 0.67 / 0.58 / 213 |
| [0.80, 0.95) | 0.89 / 0.81 / 129 | 0.90 / 0.74 / 148 |
| [0.95, 1.00) | 0.98 / 0.99 / 363 | 0.98 / 0.97 / 382 |

## 5. Downstream statistics (played players, conditional on playing; descriptive)

The JRM engine column is the full projection engine run with `PF_NBA_MINUTES_ENGINE=jrm` on the same feed (archived with the snapshot); the frozen column is the same engine with the frozen minutes, i.e. the published values. Only the minutes input differs. The simulator is compared where it has a pre-tip forecast.

| statistic | n | JRM engine MAE | frozen MAE | JRM bias | frozen bias | paired ΔMAE JRM − frozen [95% CI] | simulator MAE (its rows) | JRM / frozen MAE on those rows |
|---|---:|---:|---:|---:|---:|---|---:|---|
| points | 621 | 4.672 | 4.690 | +0.626 | +0.273 | -0.017 [-0.148, +0.093] | 6.669 (n=440) | 4.881 / 4.855 |
| rebounds | 621 | 1.822 | 1.863 | +0.105 | -0.055 | -0.041 [-0.086, -0.003] | 2.585 (n=440) | 1.882 / 1.921 |
| assists | 621 | 1.328 | 1.314 | +0.137 | +0.025 | +0.014 [-0.019, +0.044] | 1.722 (n=440) | 1.363 / 1.339 |
| threes | 621 | 0.795 | 0.791 | +0.133 | +0.094 | +0.004 [-0.010, +0.018] | 1.077 (n=440) | 0.853 / 0.842 |
| pra | 621 | 6.077 | 6.158 | +1.008 | +0.331 | -0.081 [-0.322, +0.110] | — | — |
| fga | 621 | 2.921 | 2.912 | +0.479 | +0.207 | +0.009 [-0.105, +0.103] | — | — |

Note: the engine document is produced by a separate Monte-Carlo run from the one that writes `minutes_given_play_jrm` (the pre-registered minutes quantity), so engine minutes and the scored minutes differ by sampling noise (mean absolute difference below).
 0.17 min over 621 rows.

---
Generated by evaluate_prospective.py. Verdict line: PASS. This is research output: it activates nothing and promotes no projection family.
