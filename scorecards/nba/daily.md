## NBA projection scorecard — last 7 days

Generated 2026-10-28T03:03:36Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 151134 across 68 games. Settled: 16898 (void/DNP 7480, stat corrections 86).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 892 (49) | 1.584 | +0.170 | — | — |  |
| assists | pf-nba-assists (challenger) | 1180 (52) | 1.298 | -0.007 | 0.884 | 78% | — |
| fga | pf-nba-fga (challenger) | 1180 (52) | 2.845 | +0.109 | 1.987 | 80% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 892 (49) | 7.714 | +1.318 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1180 (52) | 5.231 | +0.327 | 3.723 | 76% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1453 (49) | Brier 0.1665 | calib +0.034 | log loss 0.5490 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1801 (52) | Brier 0.1095 | calib +0.051 | log loss 0.3281 | — | -0.0831 [-0.1017, -0.0662] (n=1117) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 892 (49) | 5.888 | +0.918 | — | — |  |
| points | pf-nba-points (challenger) | 1180 (52) | 4.595 | +0.171 | 3.193 | 78% | — |
| pra | pf-nba-pra (challenger) | 1180 (52) | 6.185 | +0.051 | 4.356 | 75% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 892 (49) | 2.372 | +0.239 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1180 (52) | 1.878 | -0.141 | 1.312 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 892 (49) | 1.010 | +0.128 | — | — |  |
| threes | pf-nba-threes (challenger) | 1180 (52) | 0.844 | +0.029 | 0.548 | 79% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.051 (95% CI +0.024..+0.079) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1801 | 0.1095 |
| incumbent | 1453 | 0.1665 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 287 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1457 | 0.1283 | 0.85 | 0.784 |
| challenger | LIKELY_OUT | 6 | 0.001 | 0.022 | 0.0 |
| challenger | UNCERTAIN | 51 | 0.2002 | 0.655 | 0.725 |
| incumbent | n/a | 1453 | 0.1665 | 0.648 | 0.614 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 28 | 5.281 | -0.497 |
| E_inj | 1152 | 5.23 | +0.347 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 804 | 5.054 | +0.414 |
| new_team | True | minutes | 376 | 5.61 | +0.14 |
| new_team | False | points | 804 | 4.755 | +0.381 |
| new_team | True | points | 376 | 4.251 | -0.279 |
| reconciled | minutes | minutes | 217 | 6.205 | -2.658 |
| reconciled | minutes+usage | minutes | 49 | 6.662 | -1.964 |
| reconciled | none | minutes | 706 | 4.824 | +1.018 |
| reconciled | usage | minutes | 208 | 5.261 | +1.633 |
| reconciled | minutes | points | 217 | 5.012 | -1.572 |
| reconciled | minutes+usage | points | 49 | 4.872 | -0.167 |
| reconciled | none | points | 706 | 4.388 | +0.664 |
| reconciled | usage | points | 208 | 4.794 | +0.392 |
