## NBA projection scorecard — season to date

Generated 2026-10-27T23:15:06Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 141912 across 68 games. Settled: 15878 (void/DNP 7128, stat corrections 86).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 880 (49) | 1.627 | +0.267 | — | — |  |
| assists | pf-nba-assists (challenger) | 1175 (52) | 1.302 | -0.009 | 0.888 | 79% | — |
| fga | pf-nba-fga (challenger) | 1175 (52) | 2.834 | +0.057 | 1.987 | 80% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 880 (49) | 7.955 | +1.931 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1175 (52) | 5.292 | +0.228 | 3.753 | 75% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1453 (49) | Brier 0.1739 | calib +0.029 | log loss 0.5670 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1800 (52) | Brier 0.1099 | calib +0.057 | log loss 0.3299 | — | -0.0909 [-0.1068, -0.0717] (n=1104) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 880 (49) | 6.000 | +1.326 | — | — |  |
| points | pf-nba-points (challenger) | 1175 (52) | 4.582 | +0.142 | 3.192 | 79% | — |
| pra | pf-nba-pra (challenger) | 1175 (52) | 6.159 | +0.015 | 4.351 | 75% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 880 (49) | 2.404 | +0.372 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1175 (52) | 1.892 | -0.165 | 1.322 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 880 (49) | 1.019 | +0.165 | — | — |  |
| threes | pf-nba-threes (challenger) | 1175 (52) | 0.842 | +0.020 | 0.548 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **WATCH** — CRPS 111% of historical holdout
- participation: **ALERT** — bias +0.057 (95% CI +0.029..+0.086) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1800 | 0.1099 |
| incumbent | 1453 | 0.1739 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 285 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1459 | 0.1301 | 0.851 | 0.78 |
| challenger | LIKELY_OUT | 6 | 0.001 | 0.022 | 0.0 |
| challenger | UNCERTAIN | 50 | 0.1623 | 0.699 | 0.74 |
| incumbent | n/a | 1453 | 0.1739 | 0.635 | 0.606 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 31 | 4.972 | -0.46 |
| E_inj | 1144 | 5.3 | +0.246 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 804 | 5.112 | +0.271 |
| new_team | True | minutes | 371 | 5.682 | +0.133 |
| new_team | False | points | 804 | 4.72 | +0.377 |
| new_team | True | points | 371 | 4.283 | -0.366 |
| reconciled | minutes | minutes | 252 | 6.135 | -2.457 |
| reconciled | minutes+usage | minutes | 58 | 6.574 | -2.177 |
| reconciled | none | minutes | 668 | 4.865 | +0.987 |
| reconciled | usage | minutes | 197 | 5.281 | +1.796 |
| reconciled | minutes | points | 252 | 4.916 | -1.425 |
| reconciled | minutes+usage | points | 58 | 4.719 | -0.212 |
| reconciled | none | points | 668 | 4.405 | +0.657 |
| reconciled | usage | points | 197 | 4.715 | +0.504 |
