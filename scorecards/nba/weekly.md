## NBA projection scorecard — last 28 days

Generated 2026-10-23T23:56:33Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 79621 across 36 games. Settled: 4901 (void/DNP 2610, stat corrections 1).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 227 (16) | 2.057 | +1.452 | — | — |  |
| assists | pf-nba-assists (challenger) | 387 (17) | 1.350 | -0.087 | 0.928 | 78% | — |
| fga | pf-nba-fga (challenger) | 387 (17) | 2.964 | -0.247 | 2.095 | 77% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 227 (16) | 10.893 | +9.702 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 387 (17) | 5.741 | -0.538 | 4.048 | 73% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 469 (16) | Brier 0.2369 | calib +0.023 | log loss 0.6694 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 588 (17) | Brier 0.1261 | calib +0.075 | log loss 0.3975 | — | -0.1295 [-0.1715, -0.0883] (n=302) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 227 (16) | 8.107 | +6.194 | — | — |  |
| points | pf-nba-points (challenger) | 387 (17) | 4.681 | -0.317 | 3.258 | 80% | — |
| pra | pf-nba-pra (challenger) | 387 (17) | 6.020 | -0.503 | 4.275 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 227 (16) | 2.968 | +2.172 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 387 (17) | 1.836 | -0.206 | 1.280 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 227 (16) | 1.272 | +0.778 | — | — |  |
| threes | pf-nba-threes (challenger) | 387 (17) | 0.820 | +0.075 | 0.527 | 79% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **ALERT** — CRPS 4.048 is 119% of the historical holdout (3.392)
- participation: **ALERT** — bias +0.075 (95% CI +0.016..+0.127) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 588 | 0.1261 |
| incumbent | 469 | 0.2369 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 88 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 478 | 0.1528 | 0.865 | 0.77 |
| challenger | LIKELY_OUT | 2 | 0.0001 | 0.01 | 0.0 |
| challenger | UNCERTAIN | 20 | 0.0572 | 0.879 | 0.95 |
| incumbent | n/a | 469 | 0.2369 | 0.507 | 0.484 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 19 | 5.175 | +0.593 |
| E_inj | 368 | 5.77 | -0.596 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 267 | 5.21 | -0.312 |
| new_team | True | minutes | 120 | 6.923 | -1.04 |
| new_team | False | points | 267 | 4.619 | +0.074 |
| new_team | True | points | 120 | 4.82 | -1.185 |
| reconciled | minutes | minutes | 142 | 6.702 | -3.199 |
| reconciled | minutes+usage | minutes | 9 | 6.093 | -3.34 |
| reconciled | none | minutes | 193 | 4.882 | +1.29 |
| reconciled | usage | minutes | 43 | 6.346 | +0.63 |
| reconciled | minutes | points | 142 | 5.162 | -1.956 |
| reconciled | minutes+usage | points | 9 | 3.887 | -0.456 |
| reconciled | none | points | 193 | 4.422 | +0.697 |
| reconciled | usage | points | 43 | 4.428 | +0.577 |
