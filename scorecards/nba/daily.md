## NBA projection scorecard — last 7 days

Generated 2026-10-28T02:04:35Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 148221 across 68 games. Settled: 15878 (void/DNP 7128, stat corrections 86).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 829 (46) | 1.606 | +0.197 | — | — |  |
| assists | pf-nba-assists (challenger) | 1107 (49) | 1.304 | -0.006 | 0.888 | 79% | — |
| fga | pf-nba-fga (challenger) | 1107 (49) | 2.833 | +0.116 | 1.984 | 80% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 829 (46) | 7.823 | +1.437 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1107 (49) | 5.286 | +0.296 | 3.761 | 75% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1363 (46) | Brier 0.1692 | calib +0.036 | log loss 0.5593 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1697 (49) | Brier 0.1096 | calib +0.055 | log loss 0.3291 | — | -0.0854 [-0.1054, -0.0665] (n=1041) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 829 (46) | 5.899 | +0.997 | — | — |  |
| points | pf-nba-points (challenger) | 1107 (49) | 4.596 | +0.179 | 3.200 | 79% | — |
| pra | pf-nba-pra (challenger) | 1107 (49) | 6.200 | +0.051 | 4.379 | 75% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 829 (46) | 2.388 | +0.264 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1107 (49) | 1.893 | -0.161 | 1.325 | 79% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 829 (46) | 1.003 | +0.131 | — | — |  |
| threes | pf-nba-threes (challenger) | 1107 (49) | 0.838 | +0.028 | 0.545 | 79% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **WATCH** — CRPS 111% of historical holdout
- participation: **ALERT** — bias +0.055 (95% CI +0.023..+0.089) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1697 | 0.1096 |
| incumbent | 1363 | 0.1692 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 271 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1374 | 0.1296 | 0.85 | 0.782 |
| challenger | LIKELY_OUT | 6 | 0.001 | 0.022 | 0.0 |
| challenger | UNCERTAIN | 46 | 0.1734 | 0.684 | 0.717 |
| incumbent | n/a | 1363 | 0.1692 | 0.645 | 0.608 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 27 | 5.094 | -0.133 |
| E_inj | 1080 | 5.29 | +0.306 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 750 | 5.102 | +0.365 |
| new_team | True | minutes | 357 | 5.67 | +0.15 |
| new_team | False | points | 750 | 4.75 | +0.411 |
| new_team | True | points | 357 | 4.272 | -0.308 |
| reconciled | minutes | minutes | 217 | 6.205 | -2.658 |
| reconciled | minutes+usage | minutes | 49 | 6.662 | -1.964 |
| reconciled | none | minutes | 644 | 4.872 | +1.004 |
| reconciled | usage | minutes | 197 | 5.281 | +1.796 |
| reconciled | minutes | points | 217 | 5.012 | -1.572 |
| reconciled | minutes+usage | points | 49 | 4.872 | -0.167 |
| reconciled | none | points | 644 | 4.399 | +0.696 |
| reconciled | usage | points | 197 | 4.715 | +0.504 |
