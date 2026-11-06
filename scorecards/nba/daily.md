## NBA projection scorecard — last 7 days

Generated 2026-11-06T12:21:19Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 296689 across 132 games. Settled: 38772 (void/DNP 16396, stat corrections 167).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1061 (52) | 1.375 | -0.072 | — | — |  |
| assists | pf-nba-assists (challenger) | 1178 (52) | 1.305 | +0.054 | 0.874 | 80% | — |
| fga | pf-nba-fga (challenger) | 1178 (52) | 2.656 | +0.401 | 1.834 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1061 (52) | 5.336 | -0.038 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1178 (52) | 4.700 | +0.992 | 3.286 | 80% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1554 (52) | Brier 0.1111 | calib +0.012 | log loss 0.3820 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1808 (52) | Brier 0.0850 | calib +0.011 | log loss 0.2533 | — | -0.0541 [-0.0666, -0.0415] (n=1326) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1061 (52) | 4.927 | +0.170 | — | — |  |
| points | pf-nba-points (challenger) | 1178 (52) | 4.457 | +0.644 | 3.066 | 81% | — |
| pra | pf-nba-pra (challenger) | 1178 (52) | 5.728 | +0.699 | 3.960 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1061 (52) | 1.958 | +0.087 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1178 (52) | 1.780 | +0.052 | 1.214 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1061 (52) | 0.972 | -0.016 | — | — |  |
| threes | pf-nba-threes (challenger) | 1178 (52) | 0.904 | +0.023 | 0.586 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **ALERT** — bias +0.401 (95% CI +0.181..+0.593) exceeds 5% of the mean
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.644 (95% CI +0.331..+0.931) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1808 | 0.085 |
| incumbent | 1554 | 0.1111 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 361 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1388 | 0.0984 | 0.84 | 0.817 |
| challenger | LIKELY_OUT | 4 | 0.0001 | 0.006 | 0.0 |
| challenger | UNCERTAIN | 55 | 0.3116 | 0.559 | 0.8 |
| incumbent | n/a | 1554 | 0.1111 | 0.695 | 0.683 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 27 | 5.951 | -3.26 |
| E_inj | 1151 | 4.67 | +1.091 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1120 | 4.648 | +0.878 |
| new_team | True | minutes | 58 | 5.698 | +3.181 |
| new_team | False | points | 1120 | 4.473 | +0.607 |
| new_team | True | points | 58 | 4.146 | +1.364 |
| reconciled | minutes | minutes | 69 | 5.397 | -0.497 |
| reconciled | minutes+usage | minutes | 66 | 6.293 | +0.286 |
| reconciled | none | minutes | 894 | 4.594 | +1.122 |
| reconciled | usage | minutes | 149 | 4.308 | +1.21 |
| reconciled | minutes | points | 69 | 4.525 | -0.034 |
| reconciled | minutes+usage | points | 66 | 3.851 | +0.925 |
| reconciled | none | points | 894 | 4.511 | +0.627 |
| reconciled | usage | points | 149 | 4.368 | +0.938 |
