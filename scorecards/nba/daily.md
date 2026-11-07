## NBA projection scorecard — last 7 days

Generated 2026-11-07T04:08:56Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 312173 across 139 games. Settled: 41061 (void/DNP 17285, stat corrections 185).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1011 (49) | 1.379 | -0.037 | — | — |  |
| assists | pf-nba-assists (challenger) | 1105 (49) | 1.325 | +0.071 | 0.889 | 80% | — |
| fga | pf-nba-fga (challenger) | 1105 (49) | 2.647 | +0.381 | 1.831 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1011 (49) | 5.473 | +0.106 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1105 (49) | 4.774 | +1.046 | 3.347 | 80% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1466 (49) | Brier 0.1147 | calib +0.004 | log loss 0.3872 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1705 (49) | Brier 0.0810 | calib +0.006 | log loss 0.2438 | — | -0.0600 [-0.0733, -0.0489] (n=1273) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1011 (49) | 4.942 | +0.214 | — | — |  |
| points | pf-nba-points (challenger) | 1105 (49) | 4.499 | +0.604 | 3.097 | 81% | — |
| pra | pf-nba-pra (challenger) | 1105 (49) | 5.775 | +0.655 | 4.014 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1011 (49) | 1.969 | +0.093 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1105 (49) | 1.805 | +0.030 | 1.237 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1011 (49) | 0.964 | +0.010 | — | — |  |
| threes | pf-nba-threes (challenger) | 1105 (49) | 0.912 | +0.040 | 0.595 | 79% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.604 (95% CI +0.322..+0.896) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1705 | 0.081 |
| incumbent | 1466 | 0.1147 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 357 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1294 | 0.0951 | 0.839 | 0.824 |
| challenger | LIKELY_OUT | 2 | 0.0001 | 0.006 | 0.0 |
| challenger | UNCERTAIN | 52 | 0.2886 | 0.568 | 0.75 |
| incumbent | n/a | 1466 | 0.1147 | 0.694 | 0.69 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 26 | 6.112 | -3.317 |
| E_inj | 1079 | 4.742 | +1.151 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1066 | 4.731 | +0.968 |
| new_team | True | minutes | 39 | 5.96 | +3.174 |
| new_team | False | points | 1066 | 4.523 | +0.591 |
| new_team | True | points | 39 | 3.845 | +0.974 |
| reconciled | minutes | minutes | 57 | 5.714 | -0.753 |
| reconciled | minutes+usage | minutes | 40 | 6.878 | -0.57 |
| reconciled | none | minutes | 817 | 4.638 | +1.202 |
| reconciled | usage | minutes | 191 | 4.637 | +1.257 |
| reconciled | minutes | points | 57 | 4.401 | -0.101 |
| reconciled | minutes+usage | points | 40 | 4.541 | +0.068 |
| reconciled | none | points | 817 | 4.475 | +0.582 |
| reconciled | usage | points | 191 | 4.624 | +1.024 |
