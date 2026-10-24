> **Status 2026-10-24T12:35Z: minimum met (26 settled games, 601 played player-games). Pre-registered verdict: PASS.** This is the second execution of the unchanged pre-registered evaluation (the first, 2026-10-23, was INSUFFICIENT at 14 of 20 games: `results/prospective_20261023T1405Z_INSUFFICIENT_14of20.md`). 8 of the 34 games with eligible pre-tip rows had not settled yet. The only code change between the two runs is the measurement fix disclosed in the first report (read the participation outcome from `actual`); no forecast, rule or threshold changed. Downstream statistics are descriptive and are NOT part of the pre-registered verdict.

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

## 2. Sample

Eligible games 34; settled 26; archived player rows of settled games 899 (played 601); rows with no outcome record treated as did-not-play: 0. Frozen comparator found for 601 of 601 played rows; established simulator for 421.

## 3. Minutes (played players, conditional on playing)

### 3a. JRM vs frozen foundation (same feed, identical rows)

n = 601 player-games in 26 games

| engine | MAE | RMSE | bias | CRPS | 80% coverage | PIT variance (uniform = 1) |
|---|---:|---:|---:|---:|---:|---:|
| JRM | 4.956 | 6.454 | +0.081 | 3.5381 | 0.779 | 1.011 |
| frozen (as published) | 5.512 | 7.019 | +0.019 | 3.9145 | 0.732 | 1.146 |

Paired JRM − frozen, game-clustered 95% CI: ΔMAE -0.556 [-0.813, -0.291]; ΔCRPS -0.376 [-0.570, -0.171]

Calibration of the central intervals (nominal 50% / 80% / 90%): JRM 0.519 / 0.779 / 0.903; frozen 0.458 / 0.732 / 0.839.

### 3b. Starters and rotation (the pre-registered guard is the first row)

| group | n | JRM MAE | frozen MAE | JRM bias | frozen bias | paired ΔMAE JRM − frozen [95% CI] |
|---|---:|---:|---:|---:|---:|---|
| established rotation (JRM rank ≤ 8 and p ≥ 0.5) — GUARD | 414 | 4.615 | 5.169 | +0.167 | -0.930 | -0.554 [-0.897, -0.239] |
| actual starters | 260 | 4.743 | 5.671 | -1.029 | -2.714 | -0.928 [-1.478, -0.417] |
| actual non-starters | 341 | 5.119 | 5.391 | +0.926 | +2.102 | -0.272 [-0.562, +0.026] |
| everyone else (rank > 8 or p < 0.5) | 187 | 5.713 | 6.272 | -0.110 | +2.119 | -0.559 [-1.018, -0.010] |

### 3c. Pre-registered decision rules

- Primary (ΔMAE JRM − frozen as published after its gate, n = 601): -0.556 [-0.813, -0.291] → **SUPPORTED**
- Guard (established rotation, CI upper < +0.25): -0.554 [-0.897, -0.239], n = 414 → **PASS**
- Coherence (SD of team-sum ÷ realised team minutes over 52 team-games: JRM 0.004, frozen 0.052) → **PASS**
- Minimum sample: 26 games / 601 played player-games → **MET**

**Pre-registered verdict: PASS.**

### 3d. JRM vs frozen vs established simulator (rows where all three exist)

n = 421 player-games in 25 games. CRPS here is the quantile approximation at the simulator's seven levels, identical for all three.

| engine | MAE | bias | quantile-CRPS | P10–P90 coverage |
|---|---:|---:|---:|---:|
| JRM | 4.636 | +0.374 | 2.6959 | 0.827 |
| frozen | 5.084 | +0.270 | 2.9356 | 0.784 |
| established (sim_rotation) | 9.114 | +4.446 | 5.3734 | 0.606 |

Paired differences (game-clustered 95% CI): ΔMAE JRM − frozen -0.448 [-0.719, -0.166], ΔCRPS -0.240 [-0.380, -0.087]; ΔMAE JRM − established (sim_rotation) -4.477 [-5.528, -3.525], ΔCRPS -2.678 [-3.386, -2.047]

## 4. Participation (every archived player of a settled game; outcome = appeared in the box score)

| engine | n | Brier | log loss | mean p | observed rate | accuracy at 0.5 |
|---|---:|---:|---:|---:|---:|---:|
| JRM (rows with both) | 899 | 0.1085 | 0.3402 | 0.662 | 0.669 | 0.835 |
| frozen (rows with both) | 899 | 0.1144 | 0.3510 | 0.729 | 0.669 | 0.829 |
| JRM (rows with all three) | 526 | 0.0821 | 0.2691 | 0.807 | 0.800 | 0.876 |
| frozen (rows with all three) | 526 | 0.0864 | 0.2908 | 0.846 | 0.800 | 0.888 |
| established (rows with all three) | 526 | 0.1751 | 0.5417 | 0.644 | 0.800 | 0.692 |

The simulator is the PURE independent baseline: it has no injury or availability input, its participation_probability is a near-constant (about 0.49 for every player in the archive), so its participation row is a reference floor, not a competing availability model.

Reliability (probability bin → mean predicted / observed rate / n):

| bin | JRM | frozen |
|---|---|---|
| [0.00, 0.05) | 0.01 / 0.05 / 157 | 0.00 / 0.00 / 129 |
| [0.05, 0.20) | 0.13 / 0.40 / 30 | 0.14 / 0.33 / 3 |
| [0.20, 0.50) | 0.36 / 0.48 / 85 | 0.43 / 0.34 / 44 |
| [0.50, 0.80) | 0.67 / 0.60 / 147 | 0.67 / 0.54 / 193 |
| [0.80, 0.95) | 0.89 / 0.79 / 117 | 0.90 / 0.74 / 148 |
| [0.95, 1.00) | 0.98 / 0.99 / 363 | 0.98 / 0.97 / 382 |

## 5. Downstream statistics (played players, conditional on playing; descriptive)

The JRM engine column is the full projection engine run with `PF_NBA_MINUTES_ENGINE=jrm` on the same feed (archived with the snapshot); the frozen column is the same engine with the frozen minutes, i.e. the published values. Only the minutes input differs. The simulator is compared where it has a pre-tip forecast.

| statistic | n | JRM engine MAE | frozen MAE | JRM bias | frozen bias | paired ΔMAE JRM − frozen [95% CI] | simulator MAE (its rows) | JRM / frozen MAE on those rows |
|---|---:|---:|---:|---:|---:|---|---:|---|
| points | 601 | 4.643 | 4.611 | +0.607 | +0.100 | +0.032 [-0.053, +0.117] | 6.675 (n=421) | 4.839 / 4.741 |
| rebounds | 601 | 1.820 | 1.841 | +0.096 | -0.115 | -0.021 [-0.053, +0.013] | 2.615 (n=421) | 1.879 / 1.889 |
| assists | 601 | 1.328 | 1.301 | +0.138 | -0.013 | +0.027 [+0.008, +0.050] | 1.734 (n=421) | 1.365 / 1.323 |
| threes | 601 | 0.786 | 0.779 | +0.129 | +0.076 | +0.007 [-0.006, +0.022] | 1.074 (n=421) | 0.841 / 0.825 |
| pra | 601 | 6.043 | 6.033 | +0.996 | +0.055 | +0.011 [-0.136, +0.145] | — | — |
| fga | 601 | 2.894 | 2.837 | +0.451 | +0.056 | +0.057 [-0.002, +0.126] | — | — |

Note: the engine document is produced by a separate Monte-Carlo run from the one that writes `minutes_given_play_jrm` (the pre-registered minutes quantity), so engine minutes and the scored minutes differ by sampling noise (mean absolute difference below).
 0.17 min over 601 rows.

---
Generated by evaluate_prospective.py. Verdict line: PASS. This is research output: it activates nothing and promotes no projection family.
