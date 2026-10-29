## NBA projection scorecard — last 28 days

Generated 2026-10-29T02:03:35Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 168604 across 71 games. Settled: 18373 (void/DNP 8249, stat corrections 104).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1036 (57) | 1.600 | +0.179 | — | — |  |
| assists | pf-nba-assists (challenger) | 1347 (60) | 1.311 | -0.005 | 0.891 | 79% | — |
| fga | pf-nba-fga (challenger) | 1347 (60) | 2.830 | +0.098 | 1.978 | 79% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1036 (57) | 7.633 | +1.489 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1347 (60) | 5.154 | +0.254 | 3.662 | 76% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1689 (57) | Brier 0.1661 | calib +0.030 | log loss 0.5404 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 2075 (60) | Brier 0.1091 | calib +0.058 | log loss 0.3263 | — | -0.0842 [-0.1000, -0.0685] (n=1295) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1036 (57) | 5.873 | +1.055 | — | — |  |
| points | pf-nba-points (challenger) | 1347 (60) | 4.574 | +0.161 | 3.178 | 79% | — |
| pra | pf-nba-pra (challenger) | 1347 (60) | 6.077 | +0.082 | 4.280 | 76% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1036 (57) | 2.343 | +0.317 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1347 (60) | 1.871 | -0.105 | 1.300 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1036 (57) | 1.018 | +0.137 | — | — |  |
| threes | pf-nba-threes (challenger) | 1347 (60) | 0.852 | +0.021 | 0.555 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.058 (95% CI +0.032..+0.086) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 2075 | 0.1091 |
| incumbent | 1689 | 0.1661 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 328 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1678 | 0.1273 | 0.849 | 0.776 |
| challenger | LIKELY_OUT | 6 | 0.001 | 0.022 | 0.0 |
| challenger | UNCERTAIN | 63 | 0.2007 | 0.676 | 0.714 |
| incumbent | n/a | 1689 | 0.1661 | 0.643 | 0.613 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 34 | 5.134 | -0.764 |
| E_inj | 1313 | 5.154 | +0.281 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 921 | 4.97 | +0.313 |
| new_team | True | minutes | 426 | 5.551 | +0.128 |
| new_team | False | points | 921 | 4.689 | +0.374 |
| new_team | True | points | 426 | 4.327 | -0.299 |
| reconciled | minutes | minutes | 252 | 6.135 | -2.457 |
| reconciled | minutes+usage | minutes | 58 | 6.574 | -2.177 |
| reconciled | none | minutes | 819 | 4.753 | +0.898 |
| reconciled | usage | minutes | 218 | 5.149 | +1.619 |
| reconciled | minutes | points | 252 | 4.916 | -1.425 |
| reconciled | minutes+usage | points | 58 | 4.719 | -0.212 |
| reconciled | none | points | 819 | 4.406 | +0.647 |
| reconciled | usage | points | 218 | 4.775 | +0.267 |
