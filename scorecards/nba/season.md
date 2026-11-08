## NBA projection scorecard — season to date

Generated 2026-11-08T22:59:46Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 335372 across 154 games. Settled: 44207 (void/DNP 18605, stat corrections 209).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 2660 (137) | 1.488 | +0.021 | — | — |  |
| assists | pf-nba-assists (challenger) | 3139 (140) | 1.328 | +0.029 | 0.898 | 79% | — |
| fga | pf-nba-fga (challenger) | 3139 (140) | 2.704 | +0.221 | 1.884 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 2660 (137) | 6.225 | +0.498 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 3139 (140) | 4.874 | +0.619 | 3.434 | 78% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 4078 (137) | Brier 0.1357 | calib +0.022 | log loss 0.4553 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 4856 (140) | Brier 0.0941 | calib +0.032 | log loss 0.2816 | — | -0.0666 [-0.0763, -0.0574] (n=3370) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 2660 (137) | 5.301 | +0.460 | — | — |  |
| points | pf-nba-points (challenger) | 3139 (140) | 4.522 | +0.422 | 3.130 | 80% | — |
| pra | pf-nba-pra (challenger) | 3139 (140) | 5.912 | +0.387 | 4.138 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 2660 (137) | 2.115 | +0.136 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 3139 (140) | 1.836 | -0.057 | 1.272 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 2660 (137) | 0.980 | +0.039 | — | — |  |
| threes | pf-nba-threes (challenger) | 3139 (140) | 0.876 | +0.022 | 0.569 | 77% | — |

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
| challenger | 4856 | 0.0941 |
| incumbent | 4078 | 0.1357 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 902 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 3802 | 0.1111 | 0.843 | 0.8 |
| challenger | LIKELY_OUT | 12 | 0.0005 | 0.013 | 0.0 |
| challenger | UNCERTAIN | 140 | 0.2477 | 0.621 | 0.707 |
| incumbent | n/a | 4078 | 0.1357 | 0.674 | 0.652 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 67 | 5.383 | -1.917 |
| E_inj | 3072 | 4.862 | +0.674 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 2576 | 4.751 | +0.644 |
| new_team | True | minutes | 563 | 5.435 | +0.503 |
| new_team | False | points | 2576 | 4.574 | +0.534 |
| new_team | True | points | 563 | 4.287 | -0.091 |
| reconciled | minutes | minutes | 395 | 5.689 | -1.615 |
| reconciled | minutes+usage | minutes | 134 | 6.277 | -0.917 |
| reconciled | none | minutes | 2137 | 4.638 | +0.97 |
| reconciled | usage | minutes | 473 | 4.86 | +1.335 |
| reconciled | minutes | points | 395 | 4.79 | -0.743 |
| reconciled | minutes+usage | points | 134 | 4.291 | +0.351 |
| reconciled | none | points | 2137 | 4.446 | +0.571 |
| reconciled | usage | points | 473 | 4.71 | +0.742 |
