## NBA projection scorecard — last 7 days

Generated 2026-11-14T12:08:04Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 419203 across 188 games. Settled: 58543 (void/DNP 23502, stat corrections 255).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1114 (51) | 1.322 | -0.036 | — | — |  |
| assists | pf-nba-assists (challenger) | 1143 (51) | 1.322 | +0.070 | 0.890 | 79% | — |
| fga | pf-nba-fga (challenger) | 1143 (51) | 2.543 | +0.250 | 1.767 | 84% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1114 (51) | 5.027 | +0.431 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1143 (51) | 4.538 | +0.743 | 3.235 | 82% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1511 (51) | Brier 0.1265 | calib -0.030 | log loss 0.4327 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1776 (51) | Brier 0.0825 | calib +0.002 | log loss 0.2613 | — | -0.0469 [-0.0604, -0.0328] (n=1476) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1114 (51) | 4.656 | +0.167 | — | — |  |
| points | pf-nba-points (challenger) | 1143 (51) | 4.439 | +0.386 | 3.071 | 81% | — |
| pra | pf-nba-pra (challenger) | 1143 (51) | 5.842 | +0.510 | 4.044 | 78% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1114 (51) | 1.862 | +0.232 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1143 (51) | 1.781 | +0.120 | 1.225 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1114 (51) | 0.885 | -0.035 | — | — |  |
| threes | pf-nba-threes (challenger) | 1143 (51) | 0.841 | -0.017 | 0.551 | 82% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1776 | 0.0825 |
| incumbent | 1511 | 0.1265 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 375 | 0.0027 | 0.0 | 0.003 |
| challenger | LIKELY_ACTIVE | 1338 | 0.0938 | 0.833 | 0.826 |
| challenger | LIKELY_OUT | 1 | 0.0 | 0.004 | 0.0 |
| challenger | UNCERTAIN | 62 | 0.3224 | 0.534 | 0.613 |
| incumbent | n/a | 1511 | 0.1265 | 0.708 | 0.737 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 20 | 4.532 | -0.163 |
| E_inj | 1123 | 4.538 | +0.759 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1122 | 4.543 | +0.731 |
| new_team | True | minutes | 21 | 4.311 | +1.383 |
| new_team | False | points | 1122 | 4.457 | +0.358 |
| new_team | True | points | 21 | 3.498 | +1.889 |
| reconciled | minutes | minutes | 82 | 5.326 | +0.653 |
| reconciled | minutes+usage | minutes | 25 | 3.341 | +1.726 |
| reconciled | none | minutes | 856 | 4.49 | +0.684 |
| reconciled | usage | minutes | 180 | 4.575 | +0.928 |
| reconciled | minutes | points | 82 | 4.878 | +0.074 |
| reconciled | minutes+usage | points | 25 | 3.651 | -0.167 |
| reconciled | none | points | 856 | 4.398 | +0.324 |
| reconciled | usage | points | 180 | 4.546 | +0.902 |
