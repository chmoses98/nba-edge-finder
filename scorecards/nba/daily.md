## NBA projection scorecard — last 7 days

Generated 2026-10-23T01:41:03Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 55661 across 28 games. Settled: 4103 (void/DNP 2224, stat corrections 1).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 191 (14) | 2.142 | +1.652 | — | — |  |
| assists | pf-nba-assists (challenger) | 322 (14) | 1.339 | -0.182 | 0.929 | 78% | — |
| fga | pf-nba-fga (challenger) | 322 (14) | 3.017 | -0.245 | 2.124 | 79% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 191 (14) | 11.637 | +11.533 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 322 (14) | 5.967 | -0.585 | 4.209 | 72% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 409 (14) | Brier 0.2470 | calib +0.019 | log loss 0.6879 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 485 (14) | Brier 0.1249 | calib +0.068 | log loss 0.4007 | — | -0.1471 [-0.1857, -0.1046] (n=254) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 191 (14) | 8.396 | +7.150 | — | — |  |
| points | pf-nba-points (challenger) | 322 (14) | 4.696 | -0.475 | 3.279 | 78% | — |
| pra | pf-nba-pra (challenger) | 322 (14) | 6.004 | -0.743 | 4.299 | 76% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 191 (14) | 3.021 | +2.592 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 322 (14) | 1.799 | -0.194 | 1.255 | 82% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 191 (14) | 1.321 | +0.914 | — | — |  |
| threes | pf-nba-threes (challenger) | 322 (14) | 0.837 | +0.064 | 0.537 | 79% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **WATCH** — CRPS 111% of historical holdout
- minutes: **ALERT** — 80% range caught 72% of outcomes (expected ~80%); CRPS 4.209 is 124% of the historical holdout (3.392)
- participation: **ALERT** — bias +0.068 (95% CI +0.011..+0.127) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 485 | 0.1249 |
| incumbent | 409 | 0.247 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 75 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 389 | 0.1528 | 0.87 | 0.781 |
| challenger | LIKELY_OUT | 2 | 0.0001 | 0.01 | 0.0 |
| challenger | UNCERTAIN | 19 | 0.0601 | 0.874 | 0.947 |
| incumbent | n/a | 409 | 0.247 | 0.486 | 0.467 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 18 | 5.397 | +0.56 |
| E_inj | 304 | 6.001 | -0.653 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 224 | 5.423 | -0.364 |
| new_team | True | minutes | 98 | 7.211 | -1.09 |
| new_team | False | points | 224 | 4.626 | -0.135 |
| new_team | True | points | 98 | 4.856 | -1.251 |
| reconciled | minutes | minutes | 122 | 6.812 | -3.055 |
| reconciled | minutes+usage | minutes | 9 | 6.093 | -3.34 |
| reconciled | none | minutes | 157 | 5.039 | +1.25 |
| reconciled | usage | minutes | 34 | 7.189 | +0.534 |
| reconciled | minutes | points | 122 | 5.063 | -1.803 |
| reconciled | minutes+usage | points | 9 | 3.887 | -0.456 |
| reconciled | none | points | 157 | 4.456 | +0.291 |
| reconciled | usage | points | 34 | 4.696 | +0.753 |
