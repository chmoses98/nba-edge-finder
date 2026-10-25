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

Eligible games 41; settled 34; archived player rows of settled games 1175 (played 771); rows with no outcome record treated as did-not-play: 0. Frozen comparator found for 771 of 771 played rows; established simulator for 568.

## 3. Minutes (played players, conditional on playing)

### 3a. JRM vs frozen foundation (same feed, identical rows)

n = 771 player-games in 34 games

| engine | MAE | RMSE | bias | CRPS | 80% coverage | PIT variance (uniform = 1) |
|---|---:|---:|---:|---:|---:|---:|
| JRM | 4.995 | 6.496 | +0.056 | 3.5586 | 0.773 | 1.025 |
| frozen (as published) | 5.735 | 7.331 | +0.596 | 4.1264 | 0.713 | 1.188 |

Paired JRM − frozen, game-clustered 95% CI: ΔMAE -0.741 [-1.050, -0.424]; ΔCRPS -0.568 [-0.827, -0.306]

Calibration of the central intervals (nominal 50% / 80% / 90%): JRM 0.507 / 0.773 / 0.895; frozen 0.445 / 0.713 / 0.818.

### 3b. Starters and rotation (the pre-registered guard is the first row)

| group | n | JRM MAE | frozen MAE | JRM bias | frozen bias | paired ΔMAE JRM − frozen [95% CI] |
|---|---:|---:|---:|---:|---:|---|
| established rotation (JRM rank ≤ 8 and p ≥ 0.5) — GUARD | 539 | 4.605 | 5.514 | -0.041 | -0.049 | -0.909 [-1.391, -0.432] |
| actual starters | 340 | 4.732 | 6.146 | -1.174 | -1.356 | -1.414 [-2.182, -0.658] |
| actual non-starters | 431 | 5.202 | 5.411 | +1.027 | +2.136 | -0.210 [-0.466, +0.058] |
| everyone else (rank > 8 or p < 0.5) | 232 | 5.899 | 6.248 | +0.283 | +2.095 | -0.350 [-0.811, +0.143] |

### 3c. Pre-registered decision rules

- Primary (ΔMAE JRM − frozen as published after its gate, n = 771): -0.741 [-1.050, -0.424] → **SUPPORTED**
- Guard (established rotation, CI upper < +0.25): -0.909 [-1.391, -0.432], n = 539 → **PASS**
- Coherence (SD of team-sum ÷ realised team minutes over 68 team-games: JRM 0.016, frozen 0.068) → **PASS**
- Minimum sample: 34 games / 771 played player-games → **MET**

**Pre-registered verdict: PASS.**

### 3d. JRM vs frozen vs established simulator (rows where all three exist)

n = 568 player-games in 33 games. CRPS here is the quantile approximation at the simulator's seven levels, identical for all three.

| engine | MAE | bias | quantile-CRPS | P10–P90 coverage |
|---|---:|---:|---:|---:|
| JRM | 4.692 | +0.217 | 2.7148 | 0.822 |
| frozen | 5.482 | +0.964 | 3.2564 | 0.752 |
| established (sim_rotation) | 8.552 | +2.691 | 4.9598 | 0.650 |

Paired differences (game-clustered 95% CI): ΔMAE JRM − frozen -0.790 [-1.244, -0.403], ΔCRPS -0.542 [-0.873, -0.272]; ΔMAE JRM − established (sim_rotation) -3.860 [-4.754, -3.018], ΔCRPS -2.245 [-2.863, -1.713]

## 4. Participation (every archived player of a settled game; outcome = appeared in the box score)

| engine | n | Brier | log loss | mean p | observed rate | accuracy at 0.5 |
|---|---:|---:|---:|---:|---:|---:|
| JRM (rows with both) | 1175 | 0.1177 | 0.3731 | 0.658 | 0.656 | 0.824 |
| frozen (rows with both) | 1175 | 0.1280 | 0.3937 | 0.697 | 0.656 | 0.809 |
| JRM (rows with all three) | 718 | 0.0915 | 0.3032 | 0.794 | 0.791 | 0.862 |
| frozen (rows with all three) | 718 | 0.1030 | 0.3354 | 0.804 | 0.791 | 0.868 |
| established (rows with all three) | 718 | 0.1703 | 0.5566 | 0.676 | 0.791 | 0.727 |

The simulator is the PURE independent baseline: it has no injury or availability input, its participation_probability is a near-constant (about 0.49 for every player in the archive), so its participation row is a reference floor, not a competing availability model.

Reliability (probability bin → mean predicted / observed rate / n):

| bin | JRM | frozen |
|---|---|---|
| [0.00, 0.05) | 0.01 / 0.06 / 189 | 0.00 / 0.01 / 156 |
| [0.05, 0.20) | 0.14 / 0.37 / 35 | 0.15 / 0.40 / 5 |
| [0.20, 0.50) | 0.37 / 0.41 / 121 | 0.42 / 0.38 / 107 |
| [0.50, 0.80) | 0.67 / 0.60 / 242 | 0.65 / 0.60 / 311 |
| [0.80, 0.95) | 0.88 / 0.82 / 177 | 0.90 / 0.75 / 171 |
| [0.95, 1.00) | 0.98 / 0.99 / 411 | 0.98 / 0.96 / 425 |

## 5. Downstream statistics (played players, conditional on playing; descriptive)

The JRM engine column is the full projection engine run with `PF_NBA_MINUTES_ENGINE=jrm` on the same feed (archived with the snapshot); the frozen column is the same engine with the frozen minutes, i.e. the published values. Only the minutes input differs. The simulator is compared where it has a pre-tip forecast.

| statistic | n | JRM engine MAE | frozen MAE | JRM bias | frozen bias | paired ΔMAE JRM − frozen [95% CI] | simulator MAE (its rows) | JRM / frozen MAE on those rows |
|---|---:|---:|---:|---:|---:|---|---:|---|
| points | 771 | 4.673 | 4.866 | +0.407 | +0.457 | -0.194 [-0.465, +0.021] | 6.395 (n=568) | 4.892 / 5.107 |
| rebounds | 771 | 1.813 | 1.890 | +0.046 | +0.020 | -0.077 [-0.136, -0.022] | 2.477 (n=568) | 1.877 / 1.968 |
| assists | 771 | 1.326 | 1.318 | +0.050 | +0.047 | +0.008 [-0.027, +0.038] | 1.696 (n=568) | 1.371 / 1.358 |
| threes | 771 | 0.823 | 0.827 | +0.090 | +0.081 | -0.004 [-0.022, +0.013] | 1.061 (n=568) | 0.885 / 0.885 |
| pra | 771 | 6.127 | 6.482 | +0.573 | +0.598 | -0.355 [-0.794, -0.012] | — | — |
| fga | 771 | 2.879 | 3.040 | +0.378 | +0.418 | -0.161 [-0.380, +0.019] | — | — |

Note: the engine document is produced by a separate Monte-Carlo run from the one that writes `minutes_given_play_jrm` (the pre-registered minutes quantity), so engine minutes and the scored minutes differ by sampling noise (mean absolute difference below).
 0.17 min over 771 rows.

---
Generated by evaluate_prospective.py. Verdict line: PASS. This is research output: it activates nothing and promotes no projection family.
