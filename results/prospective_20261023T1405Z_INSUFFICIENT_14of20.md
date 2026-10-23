> **Status 2026-10-23T14:05Z: INSUFFICIENT.** 21 games have eligible pre-tip snapshots, but only 14 have settled: the other 7 are the 2026-10-23 evening games (23:00Z / 20:00Z / 00:00Z tips), which have not been played. The pre-registered minimum (20 settled games) is not met, so no pre-registered conclusion is drawn; the numbers below are descriptive. The evaluation will be re-run, unchanged, once those games are in the outcomes archive.
>
> **Evaluator correction, disclosed.** The first execution of this script read the `participated` flag of the *participation* outcome rows, which is True on every row (the outcome is that row's `actual`), so every archived player counted as having played. That inflated the minutes errors and made the participation scores meaningless. The script was corrected (commit "evaluate_prospective: read the participation outcome from `actual`") before anything below was written; no forecast, rule or threshold changed. The corrected run is the one reported here.

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

## 2. Sample

Eligible games 21; settled 14; archived player rows of settled games 482 (played 326); rows with no outcome record treated as did-not-play: 0. Frozen comparator found for 326 of 326 played rows; established simulator for 176.

**INSUFFICIENT**: the pre-registered minimum is 20 settled games with eligible pre-tip rows and about 300 played player-games (have 14 / 326). Everything below is descriptive and no conclusion is drawn.

## 3. Minutes (played players, conditional on playing)

### 3a. JRM vs frozen foundation (same feed, identical rows)

n = 326 player-games in 14 games

| engine | MAE | RMSE | bias | CRPS | 80% coverage | PIT variance (uniform = 1) |
|---|---:|---:|---:|---:|---:|---:|
| JRM | 5.210 | 6.813 | +0.069 | 3.7493 | 0.761 | 1.059 |
| frozen (as published) | 5.819 | 7.343 | -0.472 | 4.1227 | 0.739 | 1.190 |

Paired JRM − frozen, game-clustered 95% CI: ΔMAE -0.610 [-1.033, -0.197]; ΔCRPS -0.373 [-0.696, -0.072]

Calibration of the central intervals (nominal 50% / 80% / 90%): JRM 0.500 / 0.761 / 0.893; frozen 0.420 / 0.739 / 0.831.

### 3b. Starters and rotation (the pre-registered guard is the first row)

| group | n | JRM MAE | frozen MAE | JRM bias | frozen bias | paired ΔMAE JRM − frozen [95% CI] |
|---|---:|---:|---:|---:|---:|---|
| established rotation (JRM rank ≤ 8 and p ≥ 0.5) — GUARD | 223 | 4.835 | 5.529 | +0.272 | -1.415 | -0.694 [-1.226, -0.205] |
| actual starters | 140 | 5.036 | 6.142 | -1.843 | -4.183 | -1.106 [-2.020, -0.265] |
| actual non-starters | 186 | 5.341 | 5.576 | +1.507 | +2.322 | -0.236 [-0.603, +0.164] |
| everyone else (rank > 8 or p < 0.5) | 103 | 6.023 | 6.448 | -0.370 | +1.570 | -0.426 [-0.873, +0.048] |

### 3c. Pre-registered decision rules

- Primary (ΔMAE JRM − frozen as published after its gate, n = 326): -0.610 [-1.033, -0.197] → **SUPPORTED**
- Guard (established rotation, CI upper < +0.25): -0.694 [-1.226, -0.205], n = 223 → **PASS**
- Coherence (SD of team-sum ÷ realised team minutes over 28 team-games: JRM 0.004, frozen 0.047) → **PASS**
- Minimum sample: 14 games / 326 played player-games → **INSUFFICIENT**

**Pre-registered verdict: INSUFFICIENT — no conclusion.**

### 3d. JRM vs frozen vs established simulator (rows where all three exist)

n = 176 player-games in 13 games. CRPS here is the quantile approximation at the simulator's seven levels, identical for all three.

| engine | MAE | bias | quantile-CRPS | P10–P90 coverage |
|---|---:|---:|---:|---:|
| JRM | 4.527 | +0.831 | 2.6683 | 0.830 |
| frozen | 5.012 | +0.146 | 2.8560 | 0.818 |
| established (sim_rotation) | 11.320 | +11.016 | 6.9841 | 0.472 |

Paired differences (game-clustered 95% CI): ΔMAE JRM − frozen -0.485 [-0.996, +0.057], ΔCRPS -0.188 [-0.429, +0.057]; ΔMAE JRM − established (sim_rotation) -6.793 [-8.031, -5.423], ΔCRPS -4.316 [-5.160, -3.406]

## 4. Participation (every archived player of a settled game; outcome = appeared in the box score)

| engine | n | Brier | log loss | mean p | observed rate | accuracy at 0.5 |
|---|---:|---:|---:|---:|---:|---:|
| JRM (rows with both) | 482 | 0.1220 | 0.3909 | 0.663 | 0.676 | 0.828 |
| frozen (rows with both) | 482 | 0.1188 | 0.3795 | 0.732 | 0.676 | 0.836 |
| JRM (rows with all three) | 232 | 0.1100 | 0.3722 | 0.775 | 0.759 | 0.849 |
| frozen (rows with all three) | 232 | 0.1045 | 0.3715 | 0.815 | 0.759 | 0.871 |
| established (rows with all three) | 232 | 0.2457 | 0.6823 | 0.502 | 0.759 | 0.466 |

The simulator is the PURE independent baseline: it has no injury or availability input, its participation_probability is a near-constant (about 0.49 for every player in the archive), so its participation row is a reference floor, not a competing availability model.

Reliability (probability bin → mean predicted / observed rate / n):

| bin | JRM | frozen |
|---|---|---|
| [0.00, 0.05) | 0.01 / 0.06 / 88 | 0.00 / 0.00 / 74 |
| [0.05, 0.20) | 0.15 / 0.58 / 12 | — |
| [0.20, 0.50) | 0.36 / 0.55 / 33 | 0.44 / 0.36 / 11 |
| [0.50, 0.80) | 0.67 / 0.69 / 96 | 0.69 / 0.61 / 116 |
| [0.80, 0.95) | 0.89 / 0.75 / 87 | 0.90 / 0.81 / 100 |
| [0.95, 1.00) | 0.98 / 0.99 / 166 | 0.98 / 0.94 / 181 |

## 5. Downstream statistics (played players, conditional on playing; descriptive)

The JRM engine column is the full projection engine run with `PF_NBA_MINUTES_ENGINE=jrm` on the same feed (archived with the snapshot); the frozen column is the same engine with the frozen minutes, i.e. the published values. Only the minutes input differs. The simulator is compared where it has a pre-tip forecast.

| statistic | n | JRM engine MAE | frozen MAE | JRM bias | frozen bias | paired ΔMAE JRM − frozen [95% CI] | simulator MAE (its rows) | JRM / frozen MAE on those rows |
|---|---:|---:|---:|---:|---:|---|---:|---|
| points | 326 | 4.601 | 4.527 | +0.593 | -0.155 | +0.074 [-0.064, +0.212] | 8.328 (n=176) | 4.771 / 4.505 |
| rebounds | 326 | 1.794 | 1.819 | +0.081 | -0.183 | -0.025 [-0.074, +0.020] | 3.112 (n=176) | 1.852 / 1.871 |
| assists | 326 | 1.355 | 1.328 | +0.089 | -0.062 | +0.028 [+0.006, +0.052] | 2.142 (n=176) | 1.371 / 1.313 |
| threes | 326 | 0.818 | 0.799 | +0.207 | +0.124 | +0.019 [-0.003, +0.040] | 1.329 (n=176) | 0.908 / 0.861 |
| pra | 326 | 5.931 | 5.888 | +0.925 | -0.294 | +0.043 [-0.210, +0.276] | — | — |
| fga | 326 | 3.007 | 2.928 | +0.472 | -0.107 | +0.080 [-0.012, +0.195] | — | — |

Note: the engine document is produced by a separate Monte-Carlo run from the one that writes `minutes_given_play_jrm` (the pre-registered minutes quantity), so engine minutes and the scored minutes differ by sampling noise (mean absolute difference below).
 0.16 min over 326 rows.

---
Generated by evaluate_prospective.py. Verdict line: INSUFFICIENT — no conclusion. This is research output: it activates nothing and promotes no projection family.
