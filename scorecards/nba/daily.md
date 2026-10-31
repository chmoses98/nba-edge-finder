## NBA projection scorecard — last 7 days

Generated 2026-10-31T10:57:42Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 206419 across 88 games. Settled: 25100 (void/DNP 10964, stat corrections 135).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 995 (51) | 1.471 | -0.212 | — | — |  |
| assists | pf-nba-assists (challenger) | 1178 (53) | 1.303 | -0.010 | 0.883 | 80% | — |
| fga | pf-nba-fga (challenger) | 1178 (53) | 2.726 | +0.192 | 1.899 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 995 (51) | 5.906 | -0.974 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1178 (53) | 4.706 | +0.432 | 3.309 | 80% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1520 (51) | Brier 0.1316 | calib +0.041 | log loss 0.4685 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1834 (53) | Brier 0.1000 | calib +0.043 | log loss 0.2917 | — | -0.0665 [-0.0802, -0.0539] (n=1246) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 995 (51) | 5.176 | -0.471 | — | — |  |
| points | pf-nba-points (challenger) | 1178 (53) | 4.536 | +0.356 | 3.148 | 80% | — |
| pra | pf-nba-pra (challenger) | 1178 (53) | 6.019 | +0.222 | 4.209 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 995 (51) | 2.093 | -0.216 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1178 (53) | 1.870 | -0.107 | 1.300 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 995 (51) | 0.975 | -0.084 | — | — |  |
| threes | pf-nba-threes (challenger) | 1178 (53) | 0.902 | -0.023 | 0.584 | 80% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.043 (95% CI +0.021..+0.067) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1834 | 0.1 |
| incumbent | 1520 | 0.1316 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 317 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1456 | 0.1158 | 0.842 | 0.786 |
| challenger | LIKELY_OUT | 8 | 0.0008 | 0.016 | 0.0 |
| challenger | UNCERTAIN | 53 | 0.2792 | 0.589 | 0.623 |
| incumbent | n/a | 1520 | 0.1316 | 0.696 | 0.655 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 16 | 4.777 | -2.536 |
| E_inj | 1162 | 4.705 | +0.473 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 848 | 4.641 | +0.48 |
| new_team | True | minutes | 330 | 4.874 | +0.309 |
| new_team | False | points | 848 | 4.717 | +0.483 |
| new_team | True | points | 330 | 4.07 | +0.031 |
| reconciled | minutes | minutes | 132 | 4.826 | -0.662 |
| reconciled | minutes+usage | minutes | 66 | 5.654 | -0.354 |
| reconciled | none | minutes | 789 | 4.621 | +0.425 |
| reconciled | usage | minutes | 191 | 4.647 | +1.49 |
| reconciled | minutes | points | 132 | 4.534 | -0.105 |
| reconciled | minutes+usage | points | 66 | 3.991 | +0.998 |
| reconciled | none | points | 789 | 4.502 | +0.381 |
| reconciled | usage | points | 191 | 4.864 | +0.351 |
