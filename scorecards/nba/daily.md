## NBA projection scorecard — last 7 days

Generated 2026-11-10T01:30:50Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 353912 across 160 games. Settled: 46282 (void/DNP 19258, stat corrections 235).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 909 (43) | 1.411 | -0.014 | — | — |  |
| assists | pf-nba-assists (challenger) | 967 (43) | 1.373 | +0.112 | 0.917 | 79% | — |
| fga | pf-nba-fga (challenger) | 967 (43) | 2.599 | +0.353 | 1.806 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 909 (43) | 5.312 | +0.454 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 967 (43) | 4.635 | +1.042 | 3.263 | 81% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1286 (43) | Brier 0.1103 | calib -0.011 | log loss 0.3761 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1499 (43) | Brier 0.0795 | calib +0.007 | log loss 0.2403 | — | -0.0506 [-0.0635, -0.0374] (n=1164) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 909 (43) | 4.779 | +0.251 | — | — |  |
| points | pf-nba-points (challenger) | 967 (43) | 4.368 | +0.556 | 3.017 | 81% | — |
| pra | pf-nba-pra (challenger) | 967 (43) | 5.716 | +0.690 | 4.001 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 909 (43) | 1.996 | +0.136 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 967 (43) | 1.882 | +0.063 | 1.288 | 79% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 909 (43) | 0.899 | +0.046 | — | — |  |
| threes | pf-nba-threes (challenger) | 967 (43) | 0.853 | +0.077 | 0.549 | 80% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.556 (95% CI +0.203..+0.864) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **ALERT** — bias +0.077 (95% CI +0.011..+0.141) exceeds 5% of the mean

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1499 | 0.0795 |
| incumbent | 1286 | 0.1103 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 311 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1141 | 0.0935 | 0.834 | 0.816 |
| challenger | LIKELY_OUT | 1 | 0.0 | 0.001 | 0.0 |
| challenger | UNCERTAIN | 46 | 0.2719 | 0.581 | 0.783 |
| incumbent | n/a | 1286 | 0.1103 | 0.696 | 0.707 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 25 | 6.106 | -2.058 |
| E_inj | 942 | 4.596 | +1.124 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 943 | 4.644 | +1.04 |
| new_team | True | minutes | 24 | 4.306 | +1.132 |
| new_team | False | points | 943 | 4.388 | +0.523 |
| new_team | True | points | 24 | 3.619 | +1.835 |
| reconciled | minutes | minutes | 46 | 5.483 | +0.916 |
| reconciled | minutes+usage | minutes | 33 | 6.347 | -0.531 |
| reconciled | none | minutes | 760 | 4.486 | +1.131 |
| reconciled | usage | minutes | 128 | 4.777 | +0.961 |
| reconciled | minutes | points | 46 | 4.055 | +0.717 |
| reconciled | minutes+usage | points | 33 | 4.063 | -0.534 |
| reconciled | none | points | 760 | 4.379 | +0.588 |
| reconciled | usage | points | 128 | 4.5 | +0.588 |
