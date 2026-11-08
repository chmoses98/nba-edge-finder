## NBA projection scorecard — last 7 days

Generated 2026-11-08T00:22:02Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 322619 across 146 games. Settled: 41685 (void/DNP 17569, stat corrections 209).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 928 (45) | 1.392 | -0.034 | — | — |  |
| assists | pf-nba-assists (challenger) | 1010 (45) | 1.333 | +0.071 | 0.892 | 80% | — |
| fga | pf-nba-fga (challenger) | 1010 (45) | 2.575 | +0.350 | 1.785 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 928 (45) | 5.419 | +0.051 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1010 (45) | 4.683 | +0.967 | 3.276 | 80% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1344 (45) | Brier 0.1147 | calib +0.004 | log loss 0.3870 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1568 (45) | Brier 0.0806 | calib +0.007 | log loss 0.2421 | — | -0.0596 [-0.0751, -0.0448] (n=1179) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 928 (45) | 4.885 | +0.178 | — | — |  |
| points | pf-nba-points (challenger) | 1010 (45) | 4.423 | +0.557 | 3.049 | 81% | — |
| pra | pf-nba-pra (challenger) | 1010 (45) | 5.682 | +0.595 | 3.965 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 928 (45) | 1.998 | +0.094 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1010 (45) | 1.828 | +0.019 | 1.252 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 928 (45) | 0.962 | -0.016 | — | — |  |
| threes | pf-nba-threes (challenger) | 1010 (45) | 0.910 | +0.023 | 0.592 | 77% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.557 (95% CI +0.231..+0.810) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1568 | 0.0806 |
| incumbent | 1344 | 0.1147 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 333 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1187 | 0.0958 | 0.839 | 0.821 |
| challenger | LIKELY_OUT | 1 | 0.0 | 0.001 | 0.0 |
| challenger | UNCERTAIN | 47 | 0.2699 | 0.539 | 0.766 |
| incumbent | n/a | 1344 | 0.1147 | 0.694 | 0.69 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 26 | 5.888 | -3.043 |
| E_inj | 984 | 4.651 | +1.073 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 977 | 4.65 | +0.911 |
| new_team | True | minutes | 33 | 5.66 | +2.625 |
| new_team | False | points | 977 | 4.45 | +0.537 |
| new_team | True | points | 33 | 3.639 | +1.149 |
| reconciled | minutes | minutes | 45 | 6.242 | -0.389 |
| reconciled | minutes+usage | minutes | 40 | 6.878 | -0.57 |
| reconciled | none | minutes | 744 | 4.48 | +1.075 |
| reconciled | usage | minutes | 181 | 4.641 | +1.199 |
| reconciled | minutes | points | 45 | 4.212 | -0.058 |
| reconciled | minutes+usage | points | 40 | 4.541 | +0.068 |
| reconciled | none | points | 744 | 4.39 | +0.516 |
| reconciled | usage | points | 181 | 4.584 | +0.985 |
