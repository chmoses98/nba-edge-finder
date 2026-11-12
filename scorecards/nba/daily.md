## NBA projection scorecard — last 7 days

Generated 2026-11-12T13:50:16Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 392623 across 174 games. Settled: 54351 (void/DNP 21810, stat corrections 255).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1072 (49) | 1.350 | +0.000 | — | — |  |
| assists | pf-nba-assists (challenger) | 1113 (49) | 1.334 | +0.104 | 0.892 | 79% | — |
| fga | pf-nba-fga (challenger) | 1113 (49) | 2.530 | +0.402 | 1.758 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1072 (49) | 4.952 | +0.634 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1113 (49) | 4.413 | +1.039 | 3.118 | 83% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1456 (49) | Brier 0.1251 | calib -0.033 | log loss 0.4222 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1710 (49) | Brier 0.0775 | calib -0.007 | log loss 0.2463 | — | -0.0552 [-0.0684, -0.0414] (n=1398) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1072 (49) | 4.605 | +0.275 | — | — |  |
| points | pf-nba-points (challenger) | 1113 (49) | 4.351 | +0.536 | 3.008 | 81% | — |
| pra | pf-nba-pra (challenger) | 1113 (49) | 5.680 | +0.758 | 3.939 | 78% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1072 (49) | 1.878 | +0.277 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1113 (49) | 1.797 | +0.171 | 1.227 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1072 (49) | 0.882 | -0.032 | — | — |  |
| threes | pf-nba-threes (challenger) | 1113 (49) | 0.841 | -0.001 | 0.551 | 81% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **ALERT** — bias +0.402 (95% CI +0.219..+0.577) exceeds 5% of the mean
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.536 (95% CI +0.287..+0.802) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1710 | 0.0775 |
| incumbent | 1456 | 0.1251 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 363 | 0.0028 | 0.0 | 0.003 |
| challenger | LIKELY_ACTIVE | 1290 | 0.0877 | 0.832 | 0.84 |
| challenger | LIKELY_OUT | 2 | 0.0 | 0.003 | 0.0 |
| challenger | UNCERTAIN | 55 | 0.3348 | 0.526 | 0.545 |
| incumbent | n/a | 1456 | 0.1251 | 0.703 | 0.736 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 18 | 4.142 | +0.447 |
| E_inj | 1095 | 4.418 | +1.049 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1094 | 4.428 | +1.049 |
| new_team | True | minutes | 19 | 3.585 | +0.477 |
| new_team | False | points | 1094 | 4.38 | +0.534 |
| new_team | True | points | 19 | 2.651 | +0.658 |
| reconciled | minutes | minutes | 86 | 5.248 | +1.264 |
| reconciled | minutes+usage | minutes | 25 | 3.341 | +1.726 |
| reconciled | none | minutes | 826 | 4.268 | +0.95 |
| reconciled | usage | minutes | 176 | 4.841 | +1.248 |
| reconciled | minutes | points | 86 | 4.568 | +0.429 |
| reconciled | minutes+usage | points | 25 | 3.651 | -0.167 |
| reconciled | none | points | 826 | 4.273 | +0.465 |
| reconciled | usage | points | 176 | 4.71 | +1.021 |
