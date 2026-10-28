## NBA projection scorecard — last 7 days

Generated 2026-10-28T15:37:48Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 156184 across 68 games. Settled: 17196 (void/DNP 7630, stat corrections 104).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 911 (50) | 1.584 | +0.155 | — | — |  |
| assists | pf-nba-assists (challenger) | 1200 (53) | 1.302 | -0.003 | 0.885 | 78% | — |
| fga | pf-nba-fga (challenger) | 1200 (53) | 2.834 | +0.118 | 1.981 | 80% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 911 (50) | 7.655 | +1.269 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1200 (53) | 5.190 | +0.332 | 3.694 | 76% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1481 (50) | Brier 0.1650 | calib +0.034 | log loss 0.5442 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1836 (53) | Brier 0.1090 | calib +0.052 | log loss 0.3264 | — | -0.0822 [-0.1021, -0.0648] (n=1137) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 911 (50) | 5.879 | +0.844 | — | — |  |
| points | pf-nba-points (challenger) | 1200 (53) | 4.590 | +0.148 | 3.192 | 78% | — |
| pra | pf-nba-pra (challenger) | 1200 (53) | 6.163 | +0.058 | 4.341 | 75% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 911 (50) | 2.356 | +0.250 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1200 (53) | 1.874 | -0.119 | 1.308 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 911 (50) | 1.012 | +0.115 | — | — |  |
| threes | pf-nba-threes (challenger) | 1200 (53) | 0.846 | +0.022 | 0.549 | 79% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.052 (95% CI +0.024..+0.081) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1836 | 0.109 |
| incumbent | 1481 | 0.165 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 293 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1485 | 0.1278 | 0.85 | 0.782 |
| challenger | LIKELY_OUT | 6 | 0.001 | 0.022 | 0.0 |
| challenger | UNCERTAIN | 52 | 0.1964 | 0.661 | 0.731 |
| incumbent | n/a | 1481 | 0.165 | 0.649 | 0.615 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 28 | 5.281 | -0.497 |
| E_inj | 1172 | 5.187 | +0.352 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 816 | 5.019 | +0.419 |
| new_team | True | minutes | 384 | 5.551 | +0.148 |
| new_team | False | points | 816 | 4.746 | +0.342 |
| new_team | True | points | 384 | 4.256 | -0.264 |
| reconciled | minutes | minutes | 217 | 6.205 | -2.658 |
| reconciled | minutes+usage | minutes | 49 | 6.662 | -1.964 |
| reconciled | none | minutes | 716 | 4.793 | +1.004 |
| reconciled | usage | minutes | 218 | 5.149 | +1.619 |
| reconciled | minutes | points | 217 | 5.012 | -1.572 |
| reconciled | minutes+usage | points | 49 | 4.872 | -0.167 |
| reconciled | none | points | 716 | 4.386 | +0.655 |
| reconciled | usage | points | 218 | 4.775 | +0.267 |
