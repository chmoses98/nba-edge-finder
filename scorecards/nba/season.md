## NBA projection scorecard — season to date

Generated 2026-11-14T12:08:04Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 419203 across 188 games. Settled: 58543 (void/DNP 23502, stat corrections 255).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 3612 (180) | 1.435 | +0.009 | — | — |  |
| assists | pf-nba-assists (challenger) | 4111 (183) | 1.318 | +0.037 | 0.890 | 79% | — |
| fga | pf-nba-fga (challenger) | 4111 (183) | 2.674 | +0.240 | 1.861 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 3612 (180) | 5.908 | +0.500 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 4111 (183) | 4.795 | +0.654 | 3.386 | 79% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 5350 (180) | Brier 0.1344 | calib +0.007 | log loss 0.4525 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 6356 (183) | Brier 0.0917 | calib +0.024 | log loss 0.2781 | — | -0.0617 [-0.0699, -0.0543] (n=4618) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 3612 (180) | 5.140 | +0.376 | — | — |  |
| points | pf-nba-points (challenger) | 4111 (183) | 4.515 | +0.391 | 3.123 | 80% | — |
| pra | pf-nba-pra (challenger) | 4111 (183) | 5.901 | +0.406 | 4.116 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 3612 (180) | 2.047 | +0.178 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 4111 (183) | 1.821 | +0.002 | 1.256 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 3612 (180) | 0.957 | +0.016 | — | — |  |
| threes | pf-nba-threes (challenger) | 4111 (183) | 0.871 | +0.009 | 0.567 | 78% | — |

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
| challenger | 6356 | 0.0917 |
| incumbent | 5350 | 0.1344 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 1213 | 0.0008 | 0.0 | 0.001 |
| challenger | LIKELY_ACTIVE | 4935 | 0.1071 | 0.841 | 0.806 |
| challenger | LIKELY_OUT | 13 | 0.0005 | 0.013 | 0.0 |
| challenger | UNCERTAIN | 195 | 0.2743 | 0.59 | 0.677 |
| incumbent | n/a | 5350 | 0.1344 | 0.682 | 0.675 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 83 | 5.149 | -1.394 |
| E_inj | 4028 | 4.788 | +0.697 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 3530 | 4.696 | +0.676 |
| new_team | True | minutes | 581 | 5.398 | +0.523 |
| new_team | False | points | 3530 | 4.557 | +0.462 |
| new_team | True | points | 581 | 4.262 | -0.038 |
| reconciled | minutes | minutes | 455 | 5.66 | -1.309 |
| reconciled | minutes+usage | minutes | 159 | 5.815 | -0.501 |
| reconciled | none | minutes | 2854 | 4.608 | +0.887 |
| reconciled | usage | minutes | 643 | 4.759 | +1.297 |
| reconciled | minutes | points | 455 | 4.799 | -0.687 |
| reconciled | minutes+usage | points | 159 | 4.19 | +0.269 |
| reconciled | none | points | 2854 | 4.452 | +0.478 |
| reconciled | usage | points | 643 | 4.675 | +0.801 |
