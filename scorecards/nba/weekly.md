## NBA projection scorecard — last 28 days

Generated 2026-11-10T02:57:33Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 357170 across 160 games. Settled: 47596 (void/DNP 19752, stat corrections 235).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 2884 (147) | 1.469 | +0.018 | — | — |  |
| assists | pf-nba-assists (challenger) | 3370 (150) | 1.325 | +0.031 | 0.894 | 79% | — |
| fga | pf-nba-fga (challenger) | 3370 (150) | 2.704 | +0.242 | 1.883 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 2884 (147) | 6.127 | +0.523 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 3370 (150) | 4.843 | +0.645 | 3.411 | 79% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 4376 (147) | Brier 0.1349 | calib +0.016 | log loss 0.4546 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 5210 (150) | Brier 0.0933 | calib +0.029 | log loss 0.2819 | — | -0.0654 [-0.0735, -0.0573] (n=3653) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 2884 (147) | 5.268 | +0.429 | — | — |  |
| points | pf-nba-points (challenger) | 3370 (150) | 4.521 | +0.411 | 3.127 | 80% | — |
| pra | pf-nba-pra (challenger) | 3370 (150) | 5.907 | +0.402 | 4.131 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 2884 (147) | 2.092 | +0.156 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 3370 (150) | 1.829 | -0.027 | 1.264 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 2884 (147) | 0.976 | +0.034 | — | — |  |
| threes | pf-nba-threes (challenger) | 3370 (150) | 0.876 | +0.021 | 0.569 | 77% | — |

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
| challenger | 5210 | 0.0933 |
| incumbent | 4376 | 0.1349 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 972 | 0.001 | 0.0 | 0.001 |
| challenger | LIKELY_ACTIVE | 4063 | 0.1089 | 0.842 | 0.802 |
| challenger | LIKELY_OUT | 13 | 0.0005 | 0.013 | 0.0 |
| challenger | UNCERTAIN | 162 | 0.2643 | 0.604 | 0.679 |
| incumbent | n/a | 4376 | 0.1349 | 0.675 | 0.659 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 73 | 5.282 | -1.499 |
| E_inj | 3297 | 4.833 | +0.693 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 2804 | 4.725 | +0.677 |
| new_team | True | minutes | 566 | 5.424 | +0.489 |
| new_team | False | points | 2804 | 4.57 | +0.511 |
| new_team | True | points | 566 | 4.28 | -0.086 |
| reconciled | minutes | minutes | 395 | 5.689 | -1.615 |
| reconciled | minutes+usage | minutes | 147 | 6.11 | -0.662 |
| reconciled | none | minutes | 2319 | 4.618 | +0.95 |
| reconciled | usage | minutes | 509 | 4.842 | +1.388 |
| reconciled | minutes | points | 395 | 4.79 | -0.743 |
| reconciled | minutes+usage | points | 147 | 4.27 | +0.221 |
| reconciled | none | points | 2319 | 4.471 | +0.549 |
| reconciled | usage | points | 509 | 4.616 | +0.732 |
