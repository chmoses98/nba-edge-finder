## NBA projection scorecard — last 7 days

Generated 2026-11-09T01:57:16Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 343707 across 154 games. Settled: 44502 (void/DNP 18786, stat corrections 209).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1029 (50) | 1.402 | -0.035 | — | — |  |
| assists | pf-nba-assists (challenger) | 1112 (50) | 1.360 | +0.097 | 0.911 | 80% | — |
| fga | pf-nba-fga (challenger) | 1112 (50) | 2.548 | +0.253 | 1.781 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1029 (50) | 5.331 | +0.093 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1112 (50) | 4.595 | +0.869 | 3.233 | 80% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1495 (50) | Brier 0.1119 | calib +0.007 | log loss 0.3826 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1740 (50) | Brier 0.0813 | calib +0.013 | log loss 0.2455 | — | -0.0539 [-0.0672, -0.0415] (n=1330) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1029 (50) | 4.821 | +0.165 | — | — |  |
| points | pf-nba-points (challenger) | 1112 (50) | 4.372 | +0.560 | 3.031 | 81% | — |
| pra | pf-nba-pra (challenger) | 1112 (50) | 5.682 | +0.588 | 3.977 | 78% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1029 (50) | 1.985 | +0.037 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1112 (50) | 1.835 | -0.022 | 1.268 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1029 (50) | 0.925 | +0.001 | — | — |  |
| threes | pf-nba-threes (challenger) | 1112 (50) | 0.874 | +0.042 | 0.567 | 81% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.560 (95% CI +0.245..+0.888) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1740 | 0.0813 |
| incumbent | 1495 | 0.1119 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 363 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1325 | 0.097 | 0.835 | 0.81 |
| challenger | LIKELY_OUT | 1 | 0.0 | 0.001 | 0.0 |
| challenger | UNCERTAIN | 51 | 0.2547 | 0.569 | 0.765 |
| incumbent | n/a | 1495 | 0.1119 | 0.695 | 0.688 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 28 | 5.76 | -2.842 |
| E_inj | 1084 | 4.565 | +0.965 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1081 | 4.586 | +0.849 |
| new_team | True | minutes | 31 | 4.895 | +1.584 |
| new_team | False | points | 1081 | 4.388 | +0.538 |
| new_team | True | points | 31 | 3.794 | +1.303 |
| reconciled | minutes | minutes | 67 | 5.809 | -0.094 |
| reconciled | minutes+usage | minutes | 26 | 7.075 | -2.251 |
| reconciled | none | minutes | 839 | 4.393 | +1.022 |
| reconciled | usage | minutes | 180 | 4.726 | +0.969 |
| reconciled | minutes | points | 67 | 4.452 | +0.337 |
| reconciled | minutes+usage | points | 26 | 4.273 | -0.352 |
| reconciled | none | points | 839 | 4.324 | +0.538 |
| reconciled | usage | points | 180 | 4.58 | +0.875 |
