## NBA projection scorecard — last 7 days

Generated 2026-11-11T04:03:42Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 376111 across 170 games. Settled: 49724 (void/DNP 20319, stat corrections 239).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1059 (49) | 1.379 | -0.008 | — | — |  |
| assists | pf-nba-assists (challenger) | 1114 (49) | 1.361 | +0.116 | 0.910 | 79% | — |
| fga | pf-nba-fga (challenger) | 1114 (49) | 2.570 | +0.334 | 1.791 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1059 (49) | 5.225 | +0.533 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1114 (49) | 4.574 | +0.963 | 3.236 | 82% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1464 (49) | Brier 0.1193 | calib -0.027 | log loss 0.4050 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1708 (49) | Brier 0.0809 | calib -0.003 | log loss 0.2529 | — | -0.0543 [-0.0681, -0.0412] (n=1355) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1059 (49) | 4.715 | +0.335 | — | — |  |
| points | pf-nba-points (challenger) | 1114 (49) | 4.375 | +0.560 | 3.022 | 80% | — |
| pra | pf-nba-pra (challenger) | 1114 (49) | 5.695 | +0.716 | 3.984 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1059 (49) | 1.962 | +0.163 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1114 (49) | 1.858 | +0.089 | 1.269 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1059 (49) | 0.894 | +0.026 | — | — |  |
| threes | pf-nba-threes (challenger) | 1114 (49) | 0.851 | +0.047 | 0.548 | 81% | — |

**Drift checks**

- assists: **ALERT** — bias +0.116 (95% CI +0.012..+0.208) exceeds 5% of the mean
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.560 (95% CI +0.282..+0.837) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1708 | 0.0809 |
| incumbent | 1464 | 0.1193 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 350 | 0.0029 | 0.0 | 0.003 |
| challenger | LIKELY_ACTIVE | 1296 | 0.0917 | 0.831 | 0.829 |
| challenger | LIKELY_OUT | 2 | 0.0 | 0.003 | 0.0 |
| challenger | UNCERTAIN | 60 | 0.3069 | 0.554 | 0.65 |
| incumbent | n/a | 1464 | 0.1193 | 0.696 | 0.723 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 24 | 5.391 | -2.568 |
| E_inj | 1090 | 4.556 | +1.041 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1092 | 4.583 | +0.967 |
| new_team | True | minutes | 22 | 4.14 | +0.749 |
| new_team | False | points | 1092 | 4.396 | +0.526 |
| new_team | True | points | 22 | 3.355 | +2.238 |
| reconciled | minutes | minutes | 72 | 5.159 | +0.813 |
| reconciled | minutes+usage | minutes | 33 | 6.347 | -0.531 |
| reconciled | none | minutes | 834 | 4.413 | +1.014 |
| reconciled | usage | minutes | 175 | 4.769 | +1.062 |
| reconciled | minutes | points | 72 | 3.965 | +0.338 |
| reconciled | minutes+usage | points | 33 | 4.063 | -0.534 |
| reconciled | none | points | 834 | 4.409 | +0.572 |
| reconciled | usage | points | 175 | 4.44 | +0.803 |
