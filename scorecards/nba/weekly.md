## NBA projection scorecard — last 28 days

Generated 2026-11-09T01:57:16Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 343707 across 154 games. Settled: 44502 (void/DNP 18786, stat corrections 209).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 2679 (138) | 1.485 | +0.021 | — | — |  |
| assists | pf-nba-assists (challenger) | 3158 (141) | 1.328 | +0.030 | 0.897 | 79% | — |
| fga | pf-nba-fga (challenger) | 3158 (141) | 2.705 | +0.209 | 1.886 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 2679 (138) | 6.214 | +0.486 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 3158 (141) | 4.870 | +0.609 | 3.430 | 79% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 4108 (138) | Brier 0.1353 | calib +0.022 | log loss 0.4541 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 4893 (141) | Brier 0.0940 | calib +0.033 | log loss 0.2814 | — | -0.0662 [-0.0753, -0.0575] (n=3399) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 2679 (138) | 5.306 | +0.443 | — | — |  |
| points | pf-nba-points (challenger) | 3158 (141) | 4.530 | +0.405 | 3.138 | 80% | — |
| pra | pf-nba-pra (challenger) | 3158 (141) | 5.922 | +0.368 | 4.146 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 2679 (138) | 2.116 | +0.132 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 3158 (141) | 1.838 | -0.060 | 1.273 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 2679 (138) | 0.981 | +0.036 | — | — |  |
| threes | pf-nba-threes (challenger) | 3158 (141) | 0.878 | +0.020 | 0.571 | 77% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.033 (95% CI +0.018..+0.048) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 4893 | 0.094 |
| incumbent | 4108 | 0.1353 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 907 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 3834 | 0.111 | 0.843 | 0.798 |
| challenger | LIKELY_OUT | 12 | 0.0005 | 0.013 | 0.0 |
| challenger | UNCERTAIN | 140 | 0.2477 | 0.621 | 0.707 |
| incumbent | n/a | 4108 | 0.1353 | 0.674 | 0.652 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 67 | 5.383 | -1.917 |
| E_inj | 3091 | 4.859 | +0.664 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 2595 | 4.747 | +0.632 |
| new_team | True | minutes | 563 | 5.435 | +0.503 |
| new_team | False | points | 2595 | 4.583 | +0.513 |
| new_team | True | points | 563 | 4.287 | -0.091 |
| reconciled | minutes | minutes | 395 | 5.689 | -1.615 |
| reconciled | minutes+usage | minutes | 134 | 6.277 | -0.917 |
| reconciled | none | minutes | 2156 | 4.635 | +0.953 |
| reconciled | usage | minutes | 473 | 4.86 | +1.335 |
| reconciled | minutes | points | 395 | 4.79 | -0.743 |
| reconciled | minutes+usage | points | 134 | 4.291 | +0.351 |
| reconciled | none | points | 2156 | 4.458 | +0.545 |
| reconciled | usage | points | 473 | 4.71 | +0.742 |
