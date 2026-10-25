## NBA projection scorecard — last 28 days

Generated 2026-10-25T02:27:58Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 102513 across 43 games. Settled: 9416 (void/DNP 4402, stat corrections 33).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 508 (30) | 1.714 | +0.610 | — | — |  |
| assists | pf-nba-assists (challenger) | 703 (31) | 1.308 | +0.001 | 0.892 | 79% | — |
| fga | pf-nba-fga (challenger) | 703 (31) | 2.842 | +0.033 | 1.998 | 79% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 508 (30) | 8.942 | +4.033 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 703 (31) | 5.499 | +0.050 | 3.902 | 73% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 883 (30) | Brier 0.1884 | calib +0.022 | log loss 0.5873 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1072 (31) | Brier 0.1177 | calib +0.070 | log loss 0.3574 | — | -0.0870 [-0.1200, -0.0597] (n=641) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 508 (30) | 6.635 | +2.610 | — | — |  |
| points | pf-nba-points (challenger) | 703 (31) | 4.671 | +0.051 | 3.241 | 79% | — |
| pra | pf-nba-pra (challenger) | 703 (31) | 6.099 | -0.023 | 4.308 | 75% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 508 (30) | 2.535 | +0.876 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 703 (31) | 1.834 | -0.143 | 1.276 | 82% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 508 (30) | 1.085 | +0.313 | — | — |  |
| threes | pf-nba-threes (challenger) | 703 (31) | 0.816 | +0.043 | 0.532 | 79% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **ALERT** — CRPS 3.902 is 115% of the historical holdout (3.392)
- participation: **ALERT** — bias +0.070 (95% CI +0.029..+0.111) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1072 | 0.1177 |
| incumbent | 883 | 0.1884 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 158 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 884 | 0.1385 | 0.856 | 0.769 |
| challenger | LIKELY_OUT | 2 | 0.0001 | 0.01 | 0.0 |
| challenger | UNCERTAIN | 28 | 0.1313 | 0.779 | 0.821 |
| incumbent | n/a | 883 | 0.1884 | 0.597 | 0.575 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 21 | 4.953 | +0.497 |
| E_inj | 682 | 5.516 | +0.037 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 485 | 5.155 | +0.141 |
| new_team | True | minutes | 218 | 6.266 | -0.152 |
| new_team | False | points | 485 | 4.649 | +0.356 |
| new_team | True | points | 218 | 4.72 | -0.628 |
| reconciled | minutes | minutes | 194 | 6.374 | -2.915 |
| reconciled | minutes+usage | minutes | 38 | 7.416 | -2.667 |
| reconciled | none | minutes | 390 | 4.831 | +1.435 |
| reconciled | usage | minutes | 81 | 5.723 | +1.76 |
| reconciled | minutes | points | 194 | 5.051 | -1.621 |
| reconciled | minutes+usage | points | 38 | 5.277 | -0.679 |
| reconciled | none | points | 390 | 4.43 | +0.732 |
| reconciled | usage | points | 81 | 4.64 | +1.117 |
