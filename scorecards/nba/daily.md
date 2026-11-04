## NBA projection scorecard — last 7 days

Generated 2026-11-04T23:27:32Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 282511 across 123 games. Settled: 33459 (void/DNP 14458, stat corrections 161).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 933 (47) | 1.389 | -0.127 | — | — |  |
| assists | pf-nba-assists (challenger) | 1055 (47) | 1.299 | +0.013 | 0.878 | 81% | — |
| fga | pf-nba-fga (challenger) | 1055 (47) | 2.654 | +0.359 | 1.836 | 83% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 933 (47) | 5.231 | -0.503 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1055 (47) | 4.619 | +0.886 | 3.205 | 81% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1402 (47) | Brier 0.1174 | calib +0.031 | log loss 0.4117 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1634 (47) | Brier 0.0855 | calib +0.015 | log loss 0.2543 | — | -0.0603 [-0.0725, -0.0490] (n=1179) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 933 (47) | 5.063 | -0.122 | — | — |  |
| points | pf-nba-points (challenger) | 1055 (47) | 4.566 | +0.617 | 3.139 | 80% | — |
| pra | pf-nba-pra (challenger) | 1055 (47) | 5.851 | +0.584 | 4.032 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 933 (47) | 1.923 | -0.013 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1055 (47) | 1.742 | -0.009 | 1.202 | 82% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 933 (47) | 0.996 | -0.077 | — | — |  |
| threes | pf-nba-threes (challenger) | 1055 (47) | 0.921 | -0.011 | 0.600 | 77% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.617 (95% CI +0.259..+0.955) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1634 | 0.0855 |
| incumbent | 1402 | 0.1174 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 332 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1255 | 0.1005 | 0.841 | 0.818 |
| challenger | LIKELY_OUT | 5 | 0.0 | 0.005 | 0.0 |
| challenger | UNCERTAIN | 42 | 0.3232 | 0.565 | 0.667 |
| incumbent | n/a | 1402 | 0.1174 | 0.696 | 0.665 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 16 | 5.222 | -1.244 |
| E_inj | 1039 | 4.609 | +0.919 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 935 | 4.55 | +0.784 |
| new_team | True | minutes | 120 | 5.156 | +1.679 |
| new_team | False | points | 935 | 4.609 | +0.662 |
| new_team | True | points | 120 | 4.23 | +0.268 |
| reconciled | minutes | minutes | 97 | 4.627 | -0.627 |
| reconciled | minutes+usage | minutes | 56 | 5.489 | +0.829 |
| reconciled | none | minutes | 740 | 4.585 | +0.972 |
| reconciled | usage | minutes | 162 | 4.467 | +1.419 |
| reconciled | minutes | points | 97 | 4.814 | +0.338 |
| reconciled | minutes+usage | points | 56 | 3.926 | +1.115 |
| reconciled | none | points | 740 | 4.561 | +0.429 |
| reconciled | usage | points | 162 | 4.663 | +1.472 |
