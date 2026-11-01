## NBA projection scorecard — last 7 days

Generated 2026-11-01T01:37:59Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 217217 across 92 games. Settled: 26083 (void/DNP 11361, stat corrections 135).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 927 (47) | 1.454 | -0.173 | — | — |  |
| assists | pf-nba-assists (challenger) | 1100 (49) | 1.313 | +0.034 | 0.885 | 80% | — |
| fga | pf-nba-fga (challenger) | 1100 (49) | 2.733 | +0.319 | 1.894 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 927 (47) | 5.734 | -0.771 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1100 (49) | 4.699 | +0.714 | 3.300 | 81% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1402 (47) | Brier 0.1284 | calib +0.034 | log loss 0.4481 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1698 (49) | Brier 0.0934 | calib +0.031 | log loss 0.2750 | — | -0.0674 [-0.0810, -0.0552] (n=1154) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 927 (47) | 5.069 | -0.246 | — | — |  |
| points | pf-nba-points (challenger) | 1100 (49) | 4.523 | +0.560 | 3.124 | 79% | — |
| pra | pf-nba-pra (challenger) | 1100 (49) | 6.014 | +0.541 | 4.183 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 927 (47) | 2.069 | -0.138 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1100 (49) | 1.868 | -0.044 | 1.290 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 927 (47) | 0.961 | -0.049 | — | — |  |
| threes | pf-nba-threes (challenger) | 1100 (49) | 0.892 | +0.008 | 0.575 | 80% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.560 (95% CI +0.245..+0.919) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1698 | 0.0934 |
| incumbent | 1402 | 0.1284 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 306 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1332 | 0.1075 | 0.843 | 0.802 |
| challenger | LIKELY_OUT | 8 | 0.0008 | 0.016 | 0.0 |
| challenger | UNCERTAIN | 52 | 0.2967 | 0.574 | 0.615 |
| incumbent | n/a | 1402 | 0.1284 | 0.696 | 0.661 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 14 | 5.081 | -2.979 |
| E_inj | 1086 | 4.694 | +0.761 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 819 | 4.651 | +0.695 |
| new_team | True | minutes | 281 | 4.841 | +0.769 |
| new_team | False | points | 819 | 4.658 | +0.642 |
| new_team | True | points | 281 | 4.131 | +0.32 |
| reconciled | minutes | minutes | 113 | 4.783 | -0.142 |
| reconciled | minutes+usage | minutes | 56 | 5.075 | +0.023 |
| reconciled | none | minutes | 763 | 4.682 | +0.671 |
| reconciled | usage | minutes | 168 | 4.595 | +1.715 |
| reconciled | minutes | points | 113 | 4.593 | +0.14 |
| reconciled | minutes+usage | points | 56 | 3.443 | +1.251 |
| reconciled | none | points | 763 | 4.5 | +0.578 |
| reconciled | usage | points | 168 | 4.941 | +0.528 |
