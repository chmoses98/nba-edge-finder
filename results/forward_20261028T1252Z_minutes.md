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

## 2. Sample

Eligible games 66; settled 54; archived player rows of settled games 1867 (played 1229); rows with no outcome record treated as did-not-play: 0. Frozen comparator found for 1229 of 1229 played rows; established simulator for 931.

## 3. Minutes (played players, conditional on playing)

### 3a. JRM vs frozen foundation (same feed, identical rows)

n = 1229 player-games in 54 games

| engine | MAE | RMSE | bias | CRPS | 80% coverage | PIT variance (uniform = 1) |
|---|---:|---:|---:|---:|---:|---:|
| JRM | 4.831 | 6.359 | +0.100 | 3.4603 | 0.794 | 0.986 |
| frozen (as published) | 5.404 | 6.986 | +0.548 | 3.8710 | 0.747 | 1.110 |

Paired JRM − frozen, game-clustered 95% CI: ΔMAE -0.573 [-0.796, -0.364]; ΔCRPS -0.411 [-0.599, -0.244]

Calibration of the central intervals (nominal 50% / 80% / 90%): JRM 0.524 / 0.794 / 0.899; frozen 0.471 / 0.747 / 0.846.

### 3b. Starters and rotation (the pre-registered guard is the first row)

| group | n | JRM MAE | frozen MAE | JRM bias | frozen bias | paired ΔMAE JRM − frozen [95% CI] |
|---|---:|---:|---:|---:|---:|---|
| established rotation (JRM rank ≤ 8 and p ≥ 0.5) — GUARD | 855 | 4.558 | 5.245 | +0.115 | +0.047 | -0.687 [-1.033, -0.389] |
| actual starters | 540 | 4.633 | 5.645 | -0.908 | -1.172 | -1.012 [-1.508, -0.559] |
| actual non-starters | 689 | 4.987 | 5.216 | +0.890 | +1.896 | -0.229 [-0.420, -0.023] |
| everyone else (rank > 8 or p < 0.5) | 374 | 5.457 | 5.769 | +0.066 | +1.693 | -0.312 [-0.653, +0.063] |

### 3c. Pre-registered decision rules

- Primary (ΔMAE JRM − frozen as published after its gate, n = 1229): -0.573 [-0.796, -0.364] → **SUPPORTED**
- Guard (established rotation, CI upper < +0.25): -0.687 [-1.033, -0.389], n = 855 → **PASS**
- Coherence (SD of team-sum ÷ realised team minutes over 108 team-games: JRM 0.022, frozen 0.063) → **PASS**
- Minimum sample: 54 games / 1229 played player-games → **MET**

**Pre-registered verdict: PASS.**

### 3d. JRM vs frozen vs established simulator (rows where all three exist)

n = 931 player-games in 51 games. CRPS here is the quantile approximation at the simulator's seven levels, identical for all three.

| engine | MAE | bias | quantile-CRPS | P10–P90 coverage |
|---|---:|---:|---:|---:|
| JRM | 4.591 | +0.244 | 2.6901 | 0.839 |
| frozen | 5.201 | +0.769 | 3.0800 | 0.783 |
| established (sim_rotation) | 7.715 | +1.467 | 4.4381 | 0.699 |

Paired differences (game-clustered 95% CI): ΔMAE JRM − frozen -0.610 [-0.921, -0.348], ΔCRPS -0.390 [-0.604, -0.208]; ΔMAE JRM − established (sim_rotation) -3.124 [-3.739, -2.603], ΔCRPS -1.748 [-2.182, -1.394]

## 4. Participation (every archived player of a settled game; outcome = appeared in the box score)

| engine | n | Brier | log loss | mean p | observed rate | accuracy at 0.5 |
|---|---:|---:|---:|---:|---:|---:|
| JRM (rows with both) | 1867 | 0.1100 | 0.3423 | 0.656 | 0.658 | 0.833 |
| frozen (rows with both) | 1867 | 0.1172 | 0.3555 | 0.697 | 0.658 | 0.823 |
| JRM (rows with all three) | 1157 | 0.0798 | 0.2622 | 0.799 | 0.805 | 0.882 |
| frozen (rows with all three) | 1157 | 0.0852 | 0.2784 | 0.811 | 0.805 | 0.889 |
| established (rows with all three) | 1157 | 0.1566 | 0.5152 | 0.710 | 0.805 | 0.768 |

The simulator is the PURE independent baseline: it has no injury or availability input, its participation_probability is a near-constant (about 0.49 for every player in the archive), so its participation row is a reference floor, not a competing availability model.

Reliability (probability bin → mean predicted / observed rate / n):

| bin | JRM | frozen |
|---|---|---|
| [0.00, 0.05) | 0.01 / 0.04 / 313 | 0.00 / 0.00 / 266 |
| [0.05, 0.20) | 0.14 / 0.37 / 59 | 0.15 / 0.22 / 9 |
| [0.20, 0.50) | 0.37 / 0.44 / 204 | 0.42 / 0.37 / 147 |
| [0.50, 0.80) | 0.66 / 0.59 / 333 | 0.65 / 0.58 / 467 |
| [0.80, 0.95) | 0.88 / 0.83 / 235 | 0.90 / 0.76 / 255 |
| [0.95, 1.00) | 0.98 / 0.99 / 723 | 0.98 / 0.98 / 723 |

## 5. Downstream statistics (played players, conditional on playing; descriptive)

The JRM engine column is the full projection engine run with `PF_NBA_MINUTES_ENGINE=jrm` on the same feed (archived with the snapshot); the frozen column is the same engine with the frozen minutes, i.e. the published values. Only the minutes input differs. The simulator is compared where it has a pre-tip forecast.

| statistic | n | JRM engine MAE | frozen MAE | JRM bias | frozen bias | paired ΔMAE JRM − frozen [95% CI] | simulator MAE (its rows) | JRM / frozen MAE on those rows |
|---|---:|---:|---:|---:|---:|---|---:|---|
| points | 1229 | 4.565 | 4.685 | +0.452 | +0.402 | -0.120 [-0.286, +0.006] | 5.917 (n=931) | 4.716 / 4.850 |
| rebounds | 1229 | 1.856 | 1.914 | +0.048 | -0.017 | -0.059 [-0.099, -0.023] | 2.376 (n=931) | 1.906 / 1.978 |
| assists | 1229 | 1.311 | 1.305 | +0.082 | +0.058 | +0.006 [-0.018, +0.027] | 1.594 (n=931) | 1.353 / 1.343 |
| threes | 1229 | 0.850 | 0.852 | +0.065 | +0.047 | -0.002 [-0.013, +0.009] | 1.023 (n=931) | 0.897 / 0.895 |
| pra | 1229 | 6.101 | 6.320 | +0.626 | +0.498 | -0.219 [-0.479, -0.018] | — | — |
| fga | 1229 | 2.864 | 2.947 | +0.339 | +0.300 | -0.083 [-0.221, +0.029] | — | — |

Note: the engine document is produced by a separate Monte-Carlo run from the one that writes `minutes_given_play_jrm` (the pre-registered minutes quantity), so engine minutes and the scored minutes differ by sampling noise (mean absolute difference below).
 0.20 min over 1229 rows.

---
Generated by evaluate_prospective.py. Verdict line: PASS. This is research output: it activates nothing and promotes no projection family.
