## NBA projection scorecard — season to date

Generated 2026-10-31T03:36:08Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 205159 across 88 games. Settled: 24463 (void/DNP 10673, stat corrections 135).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1407 (76) | 1.563 | +0.084 | — | — |  |
| assists | pf-nba-assists (challenger) | 1777 (79) | 1.306 | -0.005 | 0.888 | 79% | — |
| fga | pf-nba-fga (challenger) | 1777 (79) | 2.762 | +0.136 | 1.931 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1407 (76) | 7.002 | +0.865 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1777 (79) | 5.009 | +0.344 | 3.537 | 77% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 2255 (76) | Brier 0.1540 | calib +0.033 | log loss 0.5144 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 2734 (79) | Brier 0.1040 | calib +0.049 | log loss 0.3101 | — | -0.0770 [-0.0913, -0.0640] (n=1766) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1407 (76) | 5.663 | +0.672 | — | — |  |
| points | pf-nba-points (challenger) | 1777 (79) | 4.566 | +0.263 | 3.166 | 79% | — |
| pra | pf-nba-pra (challenger) | 1777 (79) | 6.025 | +0.167 | 4.225 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1407 (76) | 2.261 | +0.189 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1777 (79) | 1.860 | -0.109 | 1.291 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1407 (76) | 1.001 | +0.079 | — | — |  |
| threes | pf-nba-threes (challenger) | 1777 (79) | 0.856 | +0.018 | 0.554 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.049 (95% CI +0.027..+0.069) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 2734 | 0.104 |
| incumbent | 2255 | 0.154 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 456 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 2194 | 0.1221 | 0.848 | 0.787 |
| challenger | LIKELY_OUT | 9 | 0.0007 | 0.016 | 0.0 |
| challenger | UNCERTAIN | 75 | 0.2177 | 0.67 | 0.667 |
| incumbent | n/a | 2255 | 0.154 | 0.657 | 0.624 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 35 | 5.012 | -0.717 |
| E_inj | 1742 | 5.009 | +0.365 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1262 | 4.847 | +0.38 |
| new_team | True | minutes | 515 | 5.404 | +0.257 |
| new_team | False | points | 1262 | 4.679 | +0.468 |
| new_team | True | points | 515 | 4.288 | -0.239 |
| reconciled | minutes | minutes | 304 | 5.81 | -2.023 |
| reconciled | minutes+usage | minutes | 94 | 6.021 | -1.065 |
| reconciled | none | minutes | 1107 | 4.713 | +0.812 |
| reconciled | usage | minutes | 272 | 4.967 | +1.57 |
| reconciled | minutes | points | 304 | 4.84 | -1.04 |
| reconciled | minutes+usage | points | 94 | 4.184 | +0.471 |
| reconciled | none | points | 1107 | 4.466 | +0.526 |
| reconciled | usage | points | 272 | 4.797 | +0.579 |
