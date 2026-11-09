## NBA projection scorecard — last 7 days

Generated 2026-11-09T03:37:50Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 345654 across 154 games. Settled: 45609 (void/DNP 19024, stat corrections 209).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1085 (52) | 1.405 | -0.005 | — | — |  |
| assists | pf-nba-assists (challenger) | 1165 (52) | 1.361 | +0.120 | 0.909 | 80% | — |
| fga | pf-nba-fga (challenger) | 1165 (52) | 2.567 | +0.304 | 1.787 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1085 (52) | 5.356 | +0.269 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1165 (52) | 4.600 | +0.948 | 3.237 | 81% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1556 (52) | Brier 0.1113 | calib -0.002 | log loss 0.3770 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1809 (52) | Brier 0.0788 | calib +0.008 | log loss 0.2386 | — | -0.0544 [-0.0677, -0.0404] (n=1392) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1085 (52) | 4.842 | +0.269 | — | — |  |
| points | pf-nba-points (challenger) | 1165 (52) | 4.382 | +0.613 | 3.028 | 81% | — |
| pra | pf-nba-pra (challenger) | 1165 (52) | 5.672 | +0.720 | 3.961 | 78% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1085 (52) | 1.969 | +0.103 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1165 (52) | 1.828 | +0.036 | 1.258 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1085 (52) | 0.925 | +0.020 | — | — |  |
| threes | pf-nba-threes (challenger) | 1165 (52) | 0.870 | +0.055 | 0.563 | 80% | — |

**Drift checks**

- assists: **ALERT** — bias +0.120 (95% CI +0.036..+0.211) exceeds 5% of the mean
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.613 (95% CI +0.307..+0.898) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1809 | 0.0788 |
| incumbent | 1556 | 0.1113 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 381 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1371 | 0.0934 | 0.837 | 0.818 |
| challenger | LIKELY_OUT | 1 | 0.0 | 0.001 | 0.0 |
| challenger | UNCERTAIN | 56 | 0.2605 | 0.585 | 0.768 |
| incumbent | n/a | 1556 | 0.1113 | 0.695 | 0.697 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 31 | 5.849 | -1.921 |
| E_inj | 1134 | 4.566 | +1.027 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1134 | 4.597 | +0.937 |
| new_team | True | minutes | 31 | 4.716 | +1.373 |
| new_team | False | points | 1134 | 4.397 | +0.6 |
| new_team | True | points | 31 | 3.8 | +1.111 |
| reconciled | minutes | minutes | 67 | 5.809 | -0.094 |
| reconciled | minutes+usage | minutes | 26 | 7.075 | -2.251 |
| reconciled | none | minutes | 877 | 4.434 | +1.092 |
| reconciled | usage | minutes | 195 | 4.602 | +1.085 |
| reconciled | minutes | points | 67 | 4.452 | +0.337 |
| reconciled | minutes+usage | points | 26 | 4.273 | -0.352 |
| reconciled | none | points | 877 | 4.36 | +0.624 |
| reconciled | usage | points | 195 | 4.469 | +0.787 |
