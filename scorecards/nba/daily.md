## NBA projection scorecard — last 7 days

Generated 2026-10-30T01:52:02Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 184467 across 81 games. Settled: 20915 (void/DNP 9256, stat corrections 120).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 985 (50) | 1.454 | -0.172 | — | — |  |
| assists | pf-nba-assists (challenger) | 1157 (52) | 1.283 | +0.009 | 0.870 | 80% | — |
| fga | pf-nba-fga (challenger) | 1157 (52) | 2.763 | +0.181 | 1.927 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 985 (50) | 6.550 | -0.935 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1157 (52) | 4.887 | +0.427 | 3.470 | 78% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1488 (50) | Brier 0.1387 | calib +0.035 | log loss 0.4841 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1802 (52) | Brier 0.1030 | calib +0.052 | log loss 0.2998 | — | -0.0682 [-0.0839, -0.0546] (n=1221) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 985 (50) | 5.257 | -0.461 | — | — |  |
| points | pf-nba-points (challenger) | 1157 (52) | 4.565 | +0.314 | 3.163 | 79% | — |
| pra | pf-nba-pra (challenger) | 1157 (52) | 6.035 | +0.221 | 4.242 | 76% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 985 (50) | 2.162 | -0.217 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1157 (52) | 1.891 | -0.116 | 1.318 | 78% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 985 (50) | 0.952 | -0.058 | — | — |  |
| threes | pf-nba-threes (challenger) | 1157 (52) | 0.871 | -0.008 | 0.568 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.052 (95% CI +0.026..+0.079) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1802 | 0.103 |
| incumbent | 1488 | 0.1387 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 298 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1453 | 0.1196 | 0.842 | 0.777 |
| challenger | LIKELY_OUT | 5 | 0.0012 | 0.023 | 0.0 |
| challenger | UNCERTAIN | 46 | 0.2578 | 0.582 | 0.609 |
| incumbent | n/a | 1488 | 0.1387 | 0.697 | 0.662 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 15 | 5.081 | -2.481 |
| E_inj | 1142 | 4.884 | +0.466 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 790 | 4.841 | +0.46 |
| new_team | True | minutes | 367 | 4.984 | +0.358 |
| new_team | False | points | 790 | 4.732 | +0.525 |
| new_team | True | points | 367 | 4.206 | -0.14 |
| reconciled | minutes | minutes | 167 | 5.246 | -1.61 |
| reconciled | minutes+usage | minutes | 59 | 6.287 | -1.893 |
| reconciled | none | minutes | 712 | 4.726 | +0.661 |
| reconciled | usage | minutes | 219 | 4.759 | +1.848 |
| reconciled | minutes | points | 167 | 4.695 | -0.612 |
| reconciled | minutes+usage | points | 59 | 4.844 | -0.169 |
| reconciled | none | points | 712 | 4.413 | +0.488 |
| reconciled | usage | points | 219 | 4.887 | +0.586 |
