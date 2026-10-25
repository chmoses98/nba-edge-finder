## NBA projection scorecard — last 28 days

Generated 2026-10-25T15:45:32Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 104254 across 43 games. Settled: 10945 (void/DNP 5173, stat corrections 47).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 599 (35) | 1.712 | +0.421 | — | — |  |
| assists | pf-nba-assists (challenger) | 810 (36) | 1.315 | -0.055 | 0.901 | 79% | — |
| fga | pf-nba-fga (challenger) | 810 (36) | 2.833 | +0.006 | 1.993 | 79% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 599 (35) | 8.620 | +3.049 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 810 (36) | 5.399 | +0.109 | 3.830 | 73% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1033 (35) | Brier 0.1856 | calib +0.031 | log loss 0.5970 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1247 (36) | Brier 0.1160 | calib +0.066 | log loss 0.3511 | — | -0.0917 [-0.1151, -0.0698] (n=761) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 599 (35) | 6.456 | +1.930 | — | — |  |
| points | pf-nba-points (challenger) | 810 (36) | 4.664 | -0.035 | 3.247 | 79% | — |
| pra | pf-nba-pra (challenger) | 810 (36) | 6.138 | -0.196 | 4.341 | 75% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 599 (35) | 2.466 | +0.690 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 810 (36) | 1.827 | -0.153 | 1.273 | 82% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 599 (35) | 1.064 | +0.241 | — | — |  |
| threes | pf-nba-threes (challenger) | 810 (36) | 0.825 | +0.026 | 0.538 | 79% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **WATCH** — CRPS 113% of historical holdout
- participation: **ALERT** — bias +0.066 (95% CI +0.030..+0.104) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1247 | 0.116 |
| incumbent | 1033 | 0.1856 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 195 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1016 | 0.1385 | 0.853 | 0.771 |
| challenger | LIKELY_OUT | 3 | 0.0012 | 0.025 | 0.0 |
| challenger | UNCERTAIN | 33 | 0.1192 | 0.77 | 0.818 |
| incumbent | n/a | 1033 | 0.1856 | 0.611 | 0.58 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 23 | 4.892 | +0.363 |
| E_inj | 787 | 5.413 | +0.101 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 560 | 5.115 | +0.194 |
| new_team | True | minutes | 250 | 6.034 | -0.082 |
| new_team | False | points | 560 | 4.71 | +0.284 |
| new_team | True | points | 250 | 4.56 | -0.75 |
| reconciled | minutes | minutes | 203 | 6.268 | -2.907 |
| reconciled | minutes+usage | minutes | 38 | 7.416 | -2.667 |
| reconciled | none | minutes | 444 | 4.796 | +1.272 |
| reconciled | usage | minutes | 125 | 5.512 | +1.717 |
| reconciled | minutes | points | 203 | 4.993 | -1.619 |
| reconciled | minutes+usage | points | 38 | 5.277 | -0.679 |
| reconciled | none | points | 444 | 4.423 | +0.537 |
| reconciled | usage | points | 125 | 4.798 | +0.702 |
