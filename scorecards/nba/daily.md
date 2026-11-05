## NBA projection scorecard — last 7 days

Generated 2026-11-05T01:39:04Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 284182 across 123 games. Settled: 33459 (void/DNP 14458, stat corrections 161).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 792 (40) | 1.395 | -0.116 | — | — |  |
| assists | pf-nba-assists (challenger) | 899 (40) | 1.318 | +0.029 | 0.888 | 81% | — |
| fga | pf-nba-fga (challenger) | 899 (40) | 2.668 | +0.430 | 1.843 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 792 (40) | 5.202 | -0.418 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 899 (40) | 4.651 | +1.081 | 3.221 | 80% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1192 (40) | Brier 0.1150 | calib +0.031 | log loss 0.4087 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1391 (40) | Brier 0.0846 | calib +0.012 | log loss 0.2522 | — | -0.0593 [-0.0737, -0.0448] (n=998) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 792 (40) | 5.076 | -0.054 | — | — |  |
| points | pf-nba-points (challenger) | 899 (40) | 4.572 | +0.683 | 3.144 | 81% | — |
| pra | pf-nba-pra (challenger) | 899 (40) | 5.913 | +0.685 | 4.059 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 792 (40) | 1.901 | +0.007 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 899 (40) | 1.716 | +0.029 | 1.178 | 83% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 792 (40) | 1.004 | -0.069 | — | — |  |
| threes | pf-nba-threes (challenger) | 899 (40) | 0.927 | -0.003 | 0.606 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **ALERT** — bias +0.430 (95% CI +0.174..+0.668) exceeds 5% of the mean
- minutes: **ALERT** — bias +1.081 (95% CI +0.581..+1.541) exceeds 5% of the mean
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.683 (95% CI +0.317..+1.034) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1391 | 0.0846 |
| incumbent | 1192 | 0.115 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 285 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1063 | 0.0983 | 0.84 | 0.821 |
| challenger | LIKELY_OUT | 4 | 0.0001 | 0.006 | 0.0 |
| challenger | UNCERTAIN | 39 | 0.3389 | 0.564 | 0.667 |
| incumbent | n/a | 1192 | 0.115 | 0.695 | 0.664 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 16 | 5.222 | -1.244 |
| E_inj | 883 | 4.641 | +1.123 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 821 | 4.569 | +0.877 |
| new_team | True | minutes | 78 | 5.523 | +3.226 |
| new_team | False | points | 821 | 4.604 | +0.707 |
| new_team | True | points | 78 | 4.233 | +0.427 |
| reconciled | minutes | minutes | 60 | 4.795 | -0.641 |
| reconciled | minutes+usage | minutes | 46 | 5.715 | +1.345 |
| reconciled | none | minutes | 654 | 4.554 | +1.123 |
| reconciled | usage | minutes | 139 | 4.696 | +1.537 |
| reconciled | minutes | points | 60 | 5.065 | -0.071 |
| reconciled | minutes+usage | points | 46 | 3.756 | +1.396 |
| reconciled | none | points | 654 | 4.57 | +0.559 |
| reconciled | usage | points | 139 | 4.642 | +1.354 |
