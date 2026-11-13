## NBA projection scorecard — last 7 days

Generated 2026-11-13T17:14:05Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 407973 across 183 games. Settled: 55671 (void/DNP 22306, stat corrections 255).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1111 (51) | 1.351 | -0.008 | — | — |  |
| assists | pf-nba-assists (challenger) | 1150 (51) | 1.337 | +0.093 | 0.897 | 78% | — |
| fga | pf-nba-fga (challenger) | 1150 (51) | 2.513 | +0.347 | 1.755 | 84% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1111 (51) | 4.985 | +0.518 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1150 (51) | 4.480 | +0.930 | 3.173 | 82% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1516 (51) | Brier 0.1240 | calib -0.030 | log loss 0.4188 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1778 (51) | Brier 0.0779 | calib -0.004 | log loss 0.2467 | — | -0.0524 [-0.0653, -0.0370] (n=1461) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1111 (51) | 4.612 | +0.192 | — | — |  |
| points | pf-nba-points (challenger) | 1150 (51) | 4.375 | +0.457 | 3.037 | 82% | — |
| pra | pf-nba-pra (challenger) | 1150 (51) | 5.758 | +0.654 | 3.999 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1111 (51) | 1.884 | +0.264 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1150 (51) | 1.807 | +0.157 | 1.237 | 79% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1111 (51) | 0.876 | -0.034 | — | — |  |
| threes | pf-nba-threes (challenger) | 1150 (51) | 0.834 | -0.005 | 0.549 | 82% | — |

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
| challenger | 1778 | 0.0779 |
| incumbent | 1516 | 0.124 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 378 | 0.0026 | 0.0 | 0.003 |
| challenger | LIKELY_ACTIVE | 1342 | 0.0889 | 0.83 | 0.834 |
| challenger | LIKELY_OUT | 2 | 0.0 | 0.003 | 0.0 |
| challenger | UNCERTAIN | 56 | 0.3245 | 0.54 | 0.554 |
| incumbent | n/a | 1516 | 0.124 | 0.703 | 0.733 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 18 | 4.418 | +0.51 |
| E_inj | 1132 | 4.481 | +0.937 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1128 | 4.487 | +0.92 |
| new_team | True | minutes | 22 | 4.124 | +1.439 |
| new_team | False | points | 1128 | 4.404 | +0.443 |
| new_team | True | points | 22 | 2.882 | +1.161 |
| reconciled | minutes | minutes | 72 | 5.33 | +0.986 |
| reconciled | minutes+usage | minutes | 25 | 3.341 | +1.726 |
| reconciled | none | minutes | 852 | 4.374 | +0.835 |
| reconciled | usage | minutes | 201 | 4.77 | +1.213 |
| reconciled | minutes | points | 72 | 4.74 | +0.412 |
| reconciled | minutes+usage | points | 25 | 3.651 | -0.167 |
| reconciled | none | points | 852 | 4.28 | +0.329 |
| reconciled | usage | points | 201 | 4.736 | +1.092 |
