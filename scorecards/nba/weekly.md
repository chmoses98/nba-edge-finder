## NBA projection scorecard — last 28 days

Generated 2026-10-26T01:04:50Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 114836 across 52 games. Settled: 11345 (void/DNP 5341, stat corrections 47).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 599 (35) | 1.712 | +0.421 | — | — |  |
| assists | pf-nba-assists (challenger) | 857 (38) | 1.321 | -0.037 | 0.903 | 78% | — |
| fga | pf-nba-fga (challenger) | 857 (38) | 2.832 | +0.032 | 1.992 | 79% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 599 (35) | 8.620 | +3.049 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 857 (38) | 5.363 | +0.174 | 3.806 | 74% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1033 (35) | Brier 0.1856 | calib +0.031 | log loss 0.5970 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1318 (38) | Brier 0.1147 | calib +0.064 | log loss 0.3467 | — | -0.0917 [-0.1151, -0.0698] (n=761) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 599 (35) | 6.456 | +1.930 | — | — |  |
| points | pf-nba-points (challenger) | 857 (38) | 4.687 | -0.046 | 3.266 | 78% | — |
| pra | pf-nba-pra (challenger) | 857 (38) | 6.188 | -0.156 | 4.383 | 75% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 599 (35) | 2.466 | +0.690 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 857 (38) | 1.846 | -0.120 | 1.287 | 82% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 599 (35) | 1.064 | +0.241 | — | — |  |
| threes | pf-nba-threes (challenger) | 857 (38) | 0.837 | +0.012 | 0.546 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **WATCH** — CRPS 112% of historical holdout
- participation: **ALERT** — bias +0.064 (95% CI +0.027..+0.098) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1318 | 0.1147 |
| incumbent | 1033 | 0.1856 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 205 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1075 | 0.1364 | 0.851 | 0.771 |
| challenger | LIKELY_OUT | 4 | 0.0009 | 0.02 | 0.0 |
| challenger | UNCERTAIN | 34 | 0.1313 | 0.756 | 0.824 |
| incumbent | n/a | 1033 | 0.1856 | 0.611 | 0.58 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 24 | 4.84 | +0.5 |
| E_inj | 833 | 5.378 | +0.165 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 590 | 5.11 | +0.265 |
| new_team | True | minutes | 267 | 5.923 | -0.025 |
| new_team | False | points | 590 | 4.766 | +0.221 |
| new_team | True | points | 267 | 4.513 | -0.634 |
| reconciled | minutes | minutes | 203 | 6.268 | -2.907 |
| reconciled | minutes+usage | minutes | 38 | 7.416 | -2.667 |
| reconciled | none | minutes | 468 | 4.79 | +1.266 |
| reconciled | usage | minutes | 148 | 5.405 | +1.68 |
| reconciled | minutes | points | 203 | 4.993 | -1.619 |
| reconciled | minutes+usage | points | 38 | 5.277 | -0.679 |
| reconciled | none | points | 468 | 4.495 | +0.549 |
| reconciled | usage | points | 148 | 4.723 | +0.394 |
