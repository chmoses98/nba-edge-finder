## NBA projection scorecard — season to date

Generated 2026-11-08T03:55:27Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 328136 across 146 games. Settled: 42957 (void/DNP 18123, stat corrections 209).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 2579 (133) | 1.486 | +0.024 | — | — |  |
| assists | pf-nba-assists (challenger) | 3055 (136) | 1.323 | +0.026 | 0.894 | 79% | — |
| fga | pf-nba-fga (challenger) | 3055 (136) | 2.713 | +0.227 | 1.890 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 2579 (133) | 6.238 | +0.533 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 3055 (136) | 4.867 | +0.643 | 3.429 | 79% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 3958 (133) | Brier 0.1363 | calib +0.022 | log loss 0.4564 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 4719 (136) | Brier 0.0945 | calib +0.032 | log loss 0.2827 | — | -0.0677 [-0.0765, -0.0586] (n=3255) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 2579 (133) | 5.337 | +0.484 | — | — |  |
| points | pf-nba-points (challenger) | 3055 (136) | 4.543 | +0.417 | 3.143 | 80% | — |
| pra | pf-nba-pra (challenger) | 3055 (136) | 5.921 | +0.392 | 4.141 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 2579 (133) | 2.123 | +0.143 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 3055 (136) | 1.834 | -0.050 | 1.268 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 2579 (133) | 0.983 | +0.041 | — | — |  |
| threes | pf-nba-threes (challenger) | 3055 (136) | 0.879 | +0.021 | 0.571 | 77% | — |

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
| challenger | 4719 | 0.0945 |
| incumbent | 3958 | 0.1363 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 871 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 3699 | 0.1115 | 0.844 | 0.799 |
| challenger | LIKELY_OUT | 12 | 0.0005 | 0.013 | 0.0 |
| challenger | UNCERTAIN | 137 | 0.2466 | 0.621 | 0.715 |
| incumbent | n/a | 3958 | 0.1363 | 0.673 | 0.652 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 67 | 5.383 | -1.917 |
| E_inj | 2988 | 4.856 | +0.7 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 2493 | 4.738 | +0.673 |
| new_team | True | minutes | 562 | 5.439 | +0.509 |
| new_team | False | points | 2493 | 4.6 | +0.533 |
| new_team | True | points | 562 | 4.289 | -0.097 |
| reconciled | minutes | minutes | 383 | 5.679 | -1.62 |
| reconciled | minutes+usage | minutes | 134 | 6.277 | -0.917 |
| reconciled | none | minutes | 2075 | 4.635 | +0.983 |
| reconciled | usage | minutes | 463 | 4.831 | +1.441 |
| reconciled | minutes | points | 383 | 4.819 | -0.744 |
| reconciled | minutes+usage | points | 134 | 4.291 | +0.351 |
| reconciled | none | points | 2075 | 4.468 | +0.558 |
| reconciled | usage | points | 463 | 4.726 | +0.762 |
