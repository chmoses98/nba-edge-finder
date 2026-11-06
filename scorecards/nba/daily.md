## NBA projection scorecard — last 7 days

Generated 2026-11-06T03:53:03Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 293018 across 132 games. Settled: 38034 (void/DNP 16257, stat corrections 167).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1012 (50) | 1.361 | -0.063 | — | — |  |
| assists | pf-nba-assists (challenger) | 1126 (50) | 1.293 | +0.061 | 0.868 | 80% | — |
| fga | pf-nba-fga (challenger) | 1126 (50) | 2.649 | +0.379 | 1.838 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1012 (50) | 5.343 | -0.119 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1126 (50) | 4.701 | +0.965 | 3.293 | 80% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1494 (50) | Brier 0.1110 | calib +0.018 | log loss 0.3835 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1739 (50) | Brier 0.0865 | calib +0.014 | log loss 0.2568 | — | -0.0530 [-0.0643, -0.0415] (n=1271) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1012 (50) | 4.939 | +0.130 | — | — |  |
| points | pf-nba-points (challenger) | 1126 (50) | 4.452 | +0.624 | 3.073 | 81% | — |
| pra | pf-nba-pra (challenger) | 1126 (50) | 5.728 | +0.674 | 3.966 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1012 (50) | 1.957 | +0.064 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1126 (50) | 1.774 | +0.038 | 1.214 | 82% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1012 (50) | 0.971 | -0.015 | — | — |  |
| threes | pf-nba-threes (challenger) | 1126 (50) | 0.902 | +0.023 | 0.586 | 79% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.624 (95% CI +0.316..+0.922) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1739 | 0.0865 |
| incumbent | 1494 | 0.111 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 346 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1336 | 0.1 | 0.839 | 0.811 |
| challenger | LIKELY_OUT | 4 | 0.0001 | 0.006 | 0.0 |
| challenger | UNCERTAIN | 53 | 0.3167 | 0.559 | 0.792 |
| incumbent | n/a | 1494 | 0.111 | 0.695 | 0.677 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 25 | 6.208 | -3.302 |
| E_inj | 1101 | 4.667 | +1.062 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1068 | 4.647 | +0.844 |
| new_team | True | minutes | 58 | 5.698 | +3.181 |
| new_team | False | points | 1068 | 4.468 | +0.584 |
| new_team | True | points | 58 | 4.146 | +1.364 |
| reconciled | minutes | minutes | 55 | 5.542 | -1.308 |
| reconciled | minutes+usage | minutes | 66 | 6.293 | +0.286 |
| reconciled | none | minutes | 856 | 4.593 | +1.12 |
| reconciled | usage | minutes | 149 | 4.308 | +1.21 |
| reconciled | minutes | points | 55 | 4.74 | -0.174 |
| reconciled | minutes+usage | points | 66 | 3.851 | +0.925 |
| reconciled | none | points | 856 | 4.494 | +0.598 |
| reconciled | usage | points | 149 | 4.368 | +0.938 |
