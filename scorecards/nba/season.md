## NBA projection scorecard — season to date

Generated 2026-10-27T02:30:21Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 132940 across 56 games. Settled: 14491 (void/DNP 6688, stat corrections 49).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 792 (45) | 1.658 | +0.293 | — | — |  |
| assists | pf-nba-assists (challenger) | 1077 (48) | 1.316 | -0.019 | 0.899 | 79% | — |
| fga | pf-nba-fga (challenger) | 1077 (48) | 2.839 | +0.013 | 1.990 | 80% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 792 (45) | 8.131 | +1.975 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1077 (48) | 5.284 | +0.148 | 3.748 | 75% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1333 (45) | Brier 0.1780 | calib +0.036 | log loss 0.5821 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1659 (48) | Brier 0.1134 | calib +0.063 | log loss 0.3396 | — | -0.0929 [-0.1138, -0.0732] (n=1001) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 792 (45) | 6.148 | +1.345 | — | — |  |
| points | pf-nba-points (challenger) | 1077 (48) | 4.606 | +0.060 | 3.216 | 79% | — |
| pra | pf-nba-pra (challenger) | 1077 (48) | 6.141 | -0.093 | 4.353 | 75% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 792 (45) | 2.411 | +0.405 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1077 (48) | 1.867 | -0.176 | 1.306 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 792 (45) | 1.035 | +0.164 | — | — |  |
| threes | pf-nba-threes (challenger) | 1077 (48) | 0.846 | +0.009 | 0.552 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **WATCH** — CRPS 110% of historical holdout
- participation: **ALERT** — bias +0.063 (95% CI +0.030..+0.092) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1659 | 0.1134 |
| incumbent | 1333 | 0.178 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 259 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1352 | 0.1342 | 0.851 | 0.772 |
| challenger | LIKELY_OUT | 5 | 0.0012 | 0.026 | 0.0 |
| challenger | UNCERTAIN | 43 | 0.1565 | 0.716 | 0.767 |
| incumbent | n/a | 1333 | 0.178 | 0.63 | 0.594 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 28 | 5.215 | -0.637 |
| E_inj | 1049 | 5.286 | +0.169 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 738 | 5.08 | +0.163 |
| new_team | True | minutes | 339 | 5.728 | +0.116 |
| new_team | False | points | 738 | 4.74 | +0.231 |
| new_team | True | points | 339 | 4.315 | -0.311 |
| reconciled | minutes | minutes | 213 | 6.307 | -2.989 |
| reconciled | minutes+usage | minutes | 58 | 6.574 | -2.177 |
| reconciled | none | minutes | 609 | 4.804 | +0.934 |
| reconciled | usage | minutes | 197 | 5.281 | +1.796 |
| reconciled | minutes | points | 213 | 5.015 | -1.604 |
| reconciled | minutes+usage | points | 58 | 4.719 | -0.212 |
| reconciled | none | points | 609 | 4.418 | +0.525 |
| reconciled | usage | points | 197 | 4.715 | +0.504 |
