## NBA projection scorecard — last 7 days

Generated 2026-10-23T16:04:02Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 61040 across 29 games. Settled: 4601 (void/DNP 2450, stat corrections 1).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 208 (15) | 2.118 | +1.632 | — | — |  |
| assists | pf-nba-assists (challenger) | 367 (16) | 1.348 | -0.054 | 0.924 | 77% | — |
| fga | pf-nba-fga (challenger) | 367 (16) | 2.943 | -0.184 | 2.076 | 77% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 208 (15) | 11.134 | +10.839 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 367 (16) | 5.725 | -0.345 | 4.045 | 74% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 439 (15) | Brier 0.2413 | calib +0.019 | log loss 0.6743 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 553 (16) | Brier 0.1206 | calib +0.064 | log loss 0.3841 | — | -0.1443 [-0.1863, -0.0975] (n=275) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 208 (15) | 8.215 | +6.983 | — | — |  |
| points | pf-nba-points (challenger) | 367 (16) | 4.623 | -0.176 | 3.214 | 80% | — |
| pra | pf-nba-pra (challenger) | 367 (16) | 5.955 | -0.301 | 4.220 | 78% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 208 (15) | 2.992 | +2.424 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 367 (16) | 1.820 | -0.175 | 1.268 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 208 (15) | 1.297 | +0.870 | — | — |  |
| threes | pf-nba-threes (challenger) | 367 (16) | 0.818 | +0.097 | 0.521 | 79% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **ALERT** — CRPS 4.045 is 119% of the historical holdout (3.392)
- participation: **ALERT** — bias +0.064 (95% CI +0.012..+0.119) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 553 | 0.1206 |
| incumbent | 439 | 0.2413 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 87 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 444 | 0.1477 | 0.866 | 0.784 |
| challenger | LIKELY_OUT | 2 | 0.0001 | 0.01 | 0.0 |
| challenger | UNCERTAIN | 20 | 0.0572 | 0.879 | 0.95 |
| incumbent | n/a | 439 | 0.2413 | 0.493 | 0.474 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 19 | 5.175 | +0.593 |
| E_inj | 348 | 5.755 | -0.396 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 255 | 5.163 | -0.148 |
| new_team | True | minutes | 112 | 7.004 | -0.794 |
| new_team | False | points | 255 | 4.613 | +0.117 |
| new_team | True | points | 112 | 4.644 | -0.844 |
| reconciled | minutes | minutes | 122 | 6.812 | -3.055 |
| reconciled | minutes+usage | minutes | 9 | 6.093 | -3.34 |
| reconciled | none | minutes | 193 | 4.882 | +1.29 |
| reconciled | usage | minutes | 43 | 6.346 | +0.63 |
| reconciled | minutes | points | 122 | 5.063 | -1.803 |
| reconciled | minutes+usage | points | 9 | 3.887 | -0.456 |
| reconciled | none | points | 193 | 4.422 | +0.697 |
| reconciled | usage | points | 43 | 4.428 | +0.577 |
