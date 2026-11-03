## NBA projection scorecard — last 7 days

Generated 2026-11-03T11:57:48Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 253066 across 107 games. Settled: 33459 (void/DNP 14458, stat corrections 161).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1089 (55) | 1.398 | -0.153 | — | — |  |
| assists | pf-nba-assists (challenger) | 1227 (55) | 1.310 | +0.014 | 0.883 | 80% | — |
| fga | pf-nba-fga (challenger) | 1227 (55) | 2.675 | +0.362 | 1.847 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1089 (55) | 5.315 | -0.575 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1227 (55) | 4.562 | +0.823 | 3.182 | 82% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1638 (55) | Brier 0.1175 | calib +0.031 | log loss 0.4067 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1909 (55) | Brier 0.0881 | calib +0.023 | log loss 0.2613 | — | -0.0582 [-0.0696, -0.0488] (n=1370) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1089 (55) | 5.076 | -0.172 | — | — |  |
| points | pf-nba-points (challenger) | 1227 (55) | 4.560 | +0.571 | 3.132 | 80% | — |
| pra | pf-nba-pra (challenger) | 1227 (55) | 5.804 | +0.578 | 3.999 | 78% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1089 (55) | 1.934 | -0.009 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1227 (55) | 1.740 | +0.034 | 1.194 | 82% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1089 (55) | 0.998 | -0.069 | — | — |  |
| threes | pf-nba-threes (challenger) | 1227 (55) | 0.921 | -0.006 | 0.600 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.571 (95% CI +0.264..+0.880) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1909 | 0.0881 |
| incumbent | 1638 | 0.1175 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 375 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1474 | 0.1018 | 0.841 | 0.808 |
| challenger | LIKELY_OUT | 5 | 0.0 | 0.005 | 0.0 |
| challenger | UNCERTAIN | 55 | 0.3292 | 0.571 | 0.655 |
| incumbent | n/a | 1638 | 0.1175 | 0.696 | 0.665 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 19 | 5.472 | -1.664 |
| E_inj | 1208 | 4.547 | +0.862 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1052 | 4.488 | +0.763 |
| new_team | True | minutes | 175 | 5.002 | +1.181 |
| new_team | False | points | 1052 | 4.595 | +0.628 |
| new_team | True | points | 175 | 4.354 | +0.231 |
| reconciled | minutes | minutes | 97 | 4.627 | -0.627 |
| reconciled | minutes+usage | minutes | 56 | 5.489 | +0.829 |
| reconciled | none | minutes | 891 | 4.529 | +0.892 |
| reconciled | usage | minutes | 183 | 4.403 | +1.253 |
| reconciled | minutes | points | 97 | 4.814 | +0.338 |
| reconciled | minutes+usage | points | 56 | 3.926 | +1.115 |
| reconciled | none | points | 891 | 4.536 | +0.458 |
| reconciled | usage | points | 183 | 4.74 | +1.078 |
