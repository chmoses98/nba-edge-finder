## NBA projection scorecard — last 28 days

Generated 2026-10-29T18:09:16Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 172844 across 79 games. Settled: 20915 (void/DNP 9256, stat corrections 120).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1193 (65) | 1.570 | +0.143 | — | — |  |
| assists | pf-nba-assists (challenger) | 1524 (68) | 1.299 | -0.007 | 0.883 | 79% | — |
| fga | pf-nba-fga (challenger) | 1524 (68) | 2.807 | +0.093 | 1.963 | 80% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1193 (65) | 7.349 | +1.118 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1524 (68) | 5.089 | +0.241 | 3.609 | 77% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1927 (65) | Brier 0.1621 | calib +0.031 | log loss 0.5274 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 2355 (68) | Brier 0.1071 | calib +0.055 | log loss 0.3196 | — | -0.0822 [-0.0977, -0.0672] (n=1496) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1193 (65) | 5.773 | +0.837 | — | — |  |
| points | pf-nba-points (challenger) | 1524 (68) | 4.579 | +0.196 | 3.176 | 80% | — |
| pra | pf-nba-pra (challenger) | 1524 (68) | 6.015 | +0.095 | 4.237 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1193 (65) | 2.306 | +0.244 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1524 (68) | 1.874 | -0.130 | 1.306 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1193 (65) | 1.012 | +0.104 | — | — |  |
| threes | pf-nba-threes (challenger) | 1524 (68) | 0.858 | +0.017 | 0.557 | 77% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.055 (95% CI +0.031..+0.083) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 2355 | 0.1071 |
| incumbent | 1927 | 0.1621 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 385 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1897 | 0.1261 | 0.848 | 0.779 |
| challenger | LIKELY_OUT | 7 | 0.0009 | 0.019 | 0.0 |
| challenger | UNCERTAIN | 66 | 0.197 | 0.672 | 0.712 |
| incumbent | n/a | 1927 | 0.1621 | 0.651 | 0.619 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 34 | 5.134 | -0.764 |
| E_inj | 1490 | 5.088 | +0.264 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1045 | 4.92 | +0.312 |
| new_team | True | minutes | 479 | 5.457 | +0.088 |
| new_team | False | points | 1045 | 4.703 | +0.426 |
| new_team | True | points | 479 | 4.309 | -0.304 |
| reconciled | minutes | minutes | 289 | 5.907 | -2.22 |
| reconciled | minutes+usage | minutes | 68 | 6.262 | -2.084 |
| reconciled | none | minutes | 905 | 4.759 | +0.795 |
| reconciled | usage | minutes | 262 | 5.02 | +1.648 |
| reconciled | minutes | points | 289 | 4.85 | -1.114 |
| reconciled | minutes+usage | points | 68 | 4.718 | -0.207 |
| reconciled | none | points | 905 | 4.414 | +0.532 |
| reconciled | usage | points | 262 | 4.812 | +0.585 |
