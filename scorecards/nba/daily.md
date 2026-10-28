## NBA projection scorecard — last 7 days

Generated 2026-10-28T23:18:38Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 165803 across 71 games. Settled: 17196 (void/DNP 7630, stat corrections 104).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 885 (48) | 1.563 | +0.116 | — | — |  |
| assists | pf-nba-assists (challenger) | 1160 (51) | 1.295 | +0.018 | 0.877 | 80% | — |
| fga | pf-nba-fga (challenger) | 1160 (51) | 2.828 | +0.153 | 1.977 | 80% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 885 (48) | 7.580 | +1.012 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1160 (51) | 5.149 | +0.453 | 3.665 | 76% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1424 (48) | Brier 0.1615 | calib +0.034 | log loss 0.5378 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1765 (51) | Brier 0.1062 | calib +0.048 | log loss 0.3175 | — | -0.0821 [-0.1025, -0.0633] (n=1095) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 885 (48) | 5.797 | +0.683 | — | — |  |
| points | pf-nba-points (challenger) | 1160 (51) | 4.563 | +0.240 | 3.166 | 80% | — |
| pra | pf-nba-pra (challenger) | 1160 (51) | 6.154 | +0.171 | 4.319 | 75% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 885 (48) | 2.335 | +0.174 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1160 (51) | 1.868 | -0.117 | 1.306 | 79% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 885 (48) | 1.000 | +0.093 | — | — |  |
| threes | pf-nba-threes (challenger) | 1160 (51) | 0.844 | +0.026 | 0.548 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.048 (95% CI +0.017..+0.076) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1765 | 0.1062 |
| incumbent | 1424 | 0.1615 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 281 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1429 | 0.1242 | 0.848 | 0.787 |
| challenger | LIKELY_OUT | 6 | 0.001 | 0.022 | 0.0 |
| challenger | UNCERTAIN | 49 | 0.2027 | 0.653 | 0.714 |
| incumbent | n/a | 1424 | 0.1615 | 0.656 | 0.621 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 25 | 4.974 | -0.61 |
| E_inj | 1135 | 5.153 | +0.476 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 788 | 5.005 | +0.535 |
| new_team | True | minutes | 372 | 5.453 | +0.279 |
| new_team | False | points | 788 | 4.764 | +0.405 |
| new_team | True | points | 372 | 4.137 | -0.11 |
| reconciled | minutes | minutes | 196 | 6.081 | -2.441 |
| reconciled | minutes+usage | minutes | 49 | 6.662 | -1.964 |
| reconciled | none | minutes | 697 | 4.78 | +1.071 |
| reconciled | usage | minutes | 218 | 5.149 | +1.619 |
| reconciled | minutes | points | 196 | 4.981 | -1.437 |
| reconciled | minutes+usage | points | 49 | 4.872 | -0.167 |
| reconciled | none | points | 697 | 4.357 | +0.732 |
| reconciled | usage | points | 218 | 4.775 | +0.267 |
