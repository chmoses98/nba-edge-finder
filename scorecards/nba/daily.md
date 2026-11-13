## NBA projection scorecard — last 7 days

Generated 2026-11-13T02:25:14Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 402248 across 183 games. Settled: 54351 (void/DNP 21810, stat corrections 255).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1048 (48) | 1.337 | +0.008 | — | — |  |
| assists | pf-nba-assists (challenger) | 1088 (48) | 1.323 | +0.110 | 0.886 | 80% | — |
| fga | pf-nba-fga (challenger) | 1088 (48) | 2.520 | +0.398 | 1.756 | 83% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1048 (48) | 4.959 | +0.630 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1088 (48) | 4.421 | +1.029 | 3.127 | 84% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1426 (48) | Brier 0.1252 | calib -0.032 | log loss 0.4235 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1676 (48) | Brier 0.0785 | calib -0.005 | log loss 0.2490 | — | -0.0543 [-0.0703, -0.0392] (n=1370) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1048 (48) | 4.601 | +0.278 | — | — |  |
| points | pf-nba-points (challenger) | 1088 (48) | 4.344 | +0.535 | 3.011 | 80% | — |
| pra | pf-nba-pra (challenger) | 1088 (48) | 5.666 | +0.763 | 3.931 | 78% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1048 (48) | 1.870 | +0.271 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1088 (48) | 1.789 | +0.169 | 1.223 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1048 (48) | 0.882 | -0.027 | — | — |  |
| threes | pf-nba-threes (challenger) | 1088 (48) | 0.841 | +0.002 | 0.551 | 83% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **ALERT** — bias +0.398 (95% CI +0.196..+0.574) exceeds 5% of the mean
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.535 (95% CI +0.231..+0.822) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1676 | 0.0785 |
| incumbent | 1426 | 0.1252 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 354 | 0.0028 | 0.0 | 0.003 |
| challenger | LIKELY_ACTIVE | 1265 | 0.0887 | 0.831 | 0.836 |
| challenger | LIKELY_OUT | 2 | 0.0 | 0.003 | 0.0 |
| challenger | UNCERTAIN | 55 | 0.3348 | 0.526 | 0.545 |
| incumbent | n/a | 1426 | 0.1252 | 0.703 | 0.735 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 18 | 4.142 | +0.447 |
| E_inj | 1070 | 4.426 | +1.039 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1069 | 4.436 | +1.039 |
| new_team | True | minutes | 19 | 3.585 | +0.477 |
| new_team | False | points | 1069 | 4.375 | +0.532 |
| new_team | True | points | 19 | 2.651 | +0.658 |
| reconciled | minutes | minutes | 86 | 5.248 | +1.264 |
| reconciled | minutes+usage | minutes | 25 | 3.341 | +1.726 |
| reconciled | none | minutes | 801 | 4.274 | +0.934 |
| reconciled | usage | minutes | 176 | 4.841 | +1.248 |
| reconciled | minutes | points | 86 | 4.568 | +0.429 |
| reconciled | minutes+usage | points | 25 | 3.651 | -0.167 |
| reconciled | none | points | 801 | 4.262 | +0.461 |
| reconciled | usage | points | 176 | 4.71 | +1.021 |
