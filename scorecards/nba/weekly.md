## NBA projection scorecard — last 28 days

Generated 2026-11-05T05:00:18Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 284671 across 123 games. Settled: 37069 (void/DNP 15868, stat corrections 161).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 2199 (115) | 1.482 | +0.034 | — | — |  |
| assists | pf-nba-assists (challenger) | 2652 (118) | 1.304 | +0.019 | 0.882 | 79% | — |
| fga | pf-nba-fga (challenger) | 2652 (118) | 2.730 | +0.221 | 1.903 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 2199 (115) | 6.366 | +0.552 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 2652 (118) | 4.881 | +0.583 | 3.446 | 78% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 3421 (115) | Brier 0.1400 | calib +0.027 | log loss 0.4688 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 4089 (118) | Brier 0.0982 | calib +0.036 | log loss 0.2928 | — | -0.0690 [-0.0795, -0.0593] (n=2764) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 2199 (115) | 5.387 | +0.481 | — | — |  |
| points | pf-nba-points (challenger) | 2652 (118) | 4.525 | +0.368 | 3.135 | 80% | — |
| pra | pf-nba-pra (challenger) | 2652 (118) | 5.911 | +0.337 | 4.134 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 2199 (115) | 2.139 | +0.165 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 2652 (118) | 1.825 | -0.047 | 1.262 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 2199 (115) | 0.993 | +0.041 | — | — |  |
| threes | pf-nba-threes (challenger) | 2652 (118) | 0.877 | +0.013 | 0.570 | 77% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.036 (95% CI +0.019..+0.053) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 4089 | 0.0982 |
| incumbent | 3421 | 0.14 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 733 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 3224 | 0.1149 | 0.845 | 0.796 |
| challenger | LIKELY_OUT | 11 | 0.0006 | 0.014 | 0.0 |
| challenger | UNCERTAIN | 121 | 0.2564 | 0.621 | 0.719 |
| incumbent | n/a | 3421 | 0.14 | 0.67 | 0.643 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 57 | 5.269 | -1.357 |
| E_inj | 2595 | 4.873 | +0.626 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 2101 | 4.729 | +0.615 |
| new_team | True | minutes | 551 | 5.461 | +0.461 |
| new_team | False | points | 2101 | 4.579 | +0.502 |
| new_team | True | points | 551 | 4.322 | -0.144 |
| reconciled | minutes | minutes | 349 | 5.716 | -1.949 |
| reconciled | minutes+usage | minutes | 123 | 5.933 | -0.779 |
| reconciled | none | minutes | 1759 | 4.677 | +0.975 |
| reconciled | usage | minutes | 421 | 4.734 | +1.443 |
| reconciled | minutes | points | 349 | 4.887 | -0.935 |
| reconciled | minutes+usage | points | 123 | 4.289 | +0.326 |
| reconciled | none | points | 1759 | 4.442 | +0.548 |
| reconciled | usage | points | 421 | 4.645 | +0.706 |
