## NBA projection scorecard — last 7 days

Generated 2026-11-05T13:33:27Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 285031 across 123 games. Settled: 38034 (void/DNP 16257, stat corrections 167).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1070 (53) | 1.380 | -0.084 | — | — |  |
| assists | pf-nba-assists (challenger) | 1192 (53) | 1.313 | +0.053 | 0.884 | 80% | — |
| fga | pf-nba-fga (challenger) | 1192 (53) | 2.640 | +0.370 | 1.832 | 83% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1070 (53) | 5.328 | -0.142 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1192 (53) | 4.689 | +0.954 | 3.285 | 80% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1584 (53) | Brier 0.1116 | calib +0.020 | log loss 0.3926 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1841 (53) | Brier 0.0869 | calib +0.015 | log loss 0.2587 | — | -0.0529 [-0.0645, -0.0425] (n=1345) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1070 (53) | 4.974 | +0.100 | — | — |  |
| points | pf-nba-points (challenger) | 1192 (53) | 4.488 | +0.616 | 3.098 | 80% | — |
| pra | pf-nba-pra (challenger) | 1192 (53) | 5.800 | +0.646 | 4.017 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1070 (53) | 1.958 | +0.039 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1192 (53) | 1.775 | +0.033 | 1.216 | 82% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1070 (53) | 0.972 | -0.020 | — | — |  |
| threes | pf-nba-threes (challenger) | 1192 (53) | 0.905 | +0.020 | 0.587 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.616 (95% CI +0.316..+0.910) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1841 | 0.0869 |
| incumbent | 1584 | 0.1116 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 365 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1413 | 0.1003 | 0.839 | 0.812 |
| challenger | LIKELY_OUT | 4 | 0.0001 | 0.006 | 0.0 |
| challenger | UNCERTAIN | 59 | 0.3102 | 0.573 | 0.746 |
| incumbent | n/a | 1584 | 0.1116 | 0.695 | 0.676 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 26 | 6.003 | -3.142 |
| E_inj | 1166 | 4.66 | +1.045 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1117 | 4.639 | +0.823 |
| new_team | True | minutes | 75 | 5.427 | +2.902 |
| new_team | False | points | 1117 | 4.498 | +0.591 |
| new_team | True | points | 75 | 4.335 | +0.987 |
| reconciled | minutes | minutes | 70 | 5.2 | -0.646 |
| reconciled | minutes+usage | minutes | 66 | 6.293 | +0.286 |
| reconciled | none | minutes | 897 | 4.606 | +1.101 |
| reconciled | usage | minutes | 159 | 4.263 | +1.105 |
| reconciled | minutes | points | 70 | 4.717 | -0.052 |
| reconciled | minutes+usage | points | 66 | 3.851 | +0.925 |
| reconciled | none | points | 897 | 4.538 | +0.594 |
| reconciled | usage | points | 159 | 4.371 | +0.906 |
