## NBA projection scorecard — last 7 days

Generated 2026-11-07T21:55:57Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 319382 across 146 games. Settled: 41685 (void/DNP 17569, stat corrections 209).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1028 (50) | 1.387 | -0.051 | — | — |  |
| assists | pf-nba-assists (challenger) | 1123 (50) | 1.331 | +0.055 | 0.894 | 80% | — |
| fga | pf-nba-fga (challenger) | 1123 (50) | 2.639 | +0.362 | 1.828 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1028 (50) | 5.430 | +0.085 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1123 (50) | 4.718 | +0.990 | 3.307 | 80% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1494 (50) | Brier 0.1143 | calib +0.005 | log loss 0.3852 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1740 (50) | Brier 0.0810 | calib +0.007 | log loss 0.2436 | — | -0.0595 [-0.0726, -0.0462] (n=1303) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1028 (50) | 4.959 | +0.153 | — | — |  |
| points | pf-nba-points (challenger) | 1123 (50) | 4.501 | +0.543 | 3.098 | 80% | — |
| pra | pf-nba-pra (challenger) | 1123 (50) | 5.737 | +0.580 | 3.998 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1028 (50) | 1.977 | +0.098 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1123 (50) | 1.810 | +0.040 | 1.239 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1028 (50) | 0.970 | -0.005 | — | — |  |
| threes | pf-nba-threes (challenger) | 1123 (50) | 0.917 | +0.030 | 0.598 | 77% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.543 (95% CI +0.239..+0.803) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1740 | 0.081 |
| incumbent | 1494 | 0.1143 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 364 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1320 | 0.0951 | 0.838 | 0.82 |
| challenger | LIKELY_OUT | 2 | 0.0001 | 0.006 | 0.0 |
| challenger | UNCERTAIN | 54 | 0.2859 | 0.558 | 0.741 |
| incumbent | n/a | 1494 | 0.1143 | 0.694 | 0.688 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 27 | 5.91 | -3.17 |
| E_inj | 1096 | 4.689 | +1.092 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1086 | 4.69 | +0.935 |
| new_team | True | minutes | 37 | 5.548 | +2.611 |
| new_team | False | points | 1086 | 4.525 | +0.535 |
| new_team | True | points | 37 | 3.807 | +0.781 |
| reconciled | minutes | minutes | 57 | 5.714 | -0.753 |
| reconciled | minutes+usage | minutes | 40 | 6.878 | -0.57 |
| reconciled | none | minutes | 835 | 4.565 | +1.123 |
| reconciled | usage | minutes | 191 | 4.637 | +1.257 |
| reconciled | minutes | points | 57 | 4.401 | -0.101 |
| reconciled | minutes+usage | points | 40 | 4.541 | +0.068 |
| reconciled | none | points | 835 | 4.478 | +0.5 |
| reconciled | usage | points | 191 | 4.624 | +1.024 |
