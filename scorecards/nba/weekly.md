## NBA projection scorecard — last 28 days

Generated 2026-11-05T01:39:04Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 284182 across 123 games. Settled: 33459 (void/DNP 14458, stat corrections 161).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1969 (104) | 1.500 | +0.034 | — | — |  |
| assists | pf-nba-assists (challenger) | 2402 (107) | 1.306 | +0.003 | 0.885 | 79% | — |
| fga | pf-nba-fga (challenger) | 2402 (107) | 2.752 | +0.213 | 1.916 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1969 (104) | 6.495 | +0.545 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 2402 (107) | 4.919 | +0.532 | 3.461 | 78% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 3091 (104) | Brier 0.1440 | calib +0.030 | log loss 0.4820 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 3709 (107) | Brier 0.0987 | calib +0.039 | log loss 0.2946 | — | -0.0728 [-0.0830, -0.0623] (n=2474) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1969 (104) | 5.489 | +0.497 | — | — |  |
| points | pf-nba-points (challenger) | 2402 (107) | 4.571 | +0.361 | 3.161 | 80% | — |
| pra | pf-nba-pra (challenger) | 2402 (107) | 5.978 | +0.302 | 4.171 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1969 (104) | 2.144 | +0.161 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 2402 (107) | 1.814 | -0.063 | 1.257 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1969 (104) | 1.007 | +0.035 | — | — |  |
| threes | pf-nba-threes (challenger) | 2402 (107) | 0.882 | +0.007 | 0.575 | 77% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.039 (95% CI +0.021..+0.057) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 3709 | 0.0987 |
| incumbent | 3091 | 0.144 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 660 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 2933 | 0.1159 | 0.846 | 0.794 |
| challenger | LIKELY_OUT | 11 | 0.0006 | 0.014 | 0.0 |
| challenger | UNCERTAIN | 105 | 0.2497 | 0.632 | 0.695 |
| incumbent | n/a | 3091 | 0.144 | 0.667 | 0.637 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 50 | 5.162 | -0.917 |
| E_inj | 2352 | 4.914 | +0.562 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1856 | 4.758 | +0.55 |
| new_team | True | minutes | 546 | 5.464 | +0.469 |
| new_team | False | points | 1856 | 4.649 | +0.519 |
| new_team | True | points | 546 | 4.306 | -0.175 |
| reconciled | minutes | minutes | 349 | 5.716 | -1.949 |
| reconciled | minutes+usage | minutes | 114 | 6.041 | -0.701 |
| reconciled | none | minutes | 1559 | 4.673 | +0.933 |
| reconciled | usage | minutes | 380 | 4.858 | +1.534 |
| reconciled | minutes | points | 349 | 4.887 | -0.935 |
| reconciled | minutes+usage | points | 114 | 4.33 | +0.44 |
| reconciled | none | points | 1559 | 4.48 | +0.544 |
| reconciled | usage | points | 380 | 4.727 | +0.78 |
