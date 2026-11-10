## NBA projection scorecard — last 7 days

Generated 2026-11-10T19:53:46Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 362979 across 167 games. Settled: 48985 (void/DNP 20160, stat corrections 239).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1008 (47) | 1.395 | -0.021 | — | — |  |
| assists | pf-nba-assists (challenger) | 1063 (47) | 1.370 | +0.107 | 0.917 | 79% | — |
| fga | pf-nba-fga (challenger) | 1063 (47) | 2.577 | +0.338 | 1.796 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1008 (47) | 5.317 | +0.461 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1063 (47) | 4.614 | +0.958 | 3.261 | 81% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1405 (47) | Brier 0.1182 | calib -0.021 | log loss 0.4030 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1640 (47) | Brier 0.0801 | calib -0.002 | log loss 0.2508 | — | -0.0532 [-0.0659, -0.0398] (n=1297) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1008 (47) | 4.747 | +0.290 | — | — |  |
| points | pf-nba-points (challenger) | 1063 (47) | 4.386 | +0.562 | 3.035 | 80% | — |
| pra | pf-nba-pra (challenger) | 1063 (47) | 5.715 | +0.702 | 4.007 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1008 (47) | 1.978 | +0.148 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1063 (47) | 1.868 | +0.081 | 1.278 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1008 (47) | 0.897 | +0.032 | — | — |  |
| threes | pf-nba-threes (challenger) | 1063 (47) | 0.852 | +0.058 | 0.548 | 82% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.562 (95% CI +0.225..+0.847) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1640 | 0.0801 |
| incumbent | 1405 | 0.1182 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 343 | 0.0029 | 0.0 | 0.003 |
| challenger | LIKELY_ACTIVE | 1236 | 0.0912 | 0.832 | 0.829 |
| challenger | LIKELY_OUT | 2 | 0.0 | 0.003 | 0.0 |
| challenger | UNCERTAIN | 59 | 0.2988 | 0.561 | 0.644 |
| incumbent | n/a | 1405 | 0.1182 | 0.696 | 0.717 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 23 | 5.542 | -2.763 |
| E_inj | 1040 | 4.594 | +1.04 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1042 | 4.62 | +0.961 |
| new_team | True | minutes | 21 | 4.308 | +0.814 |
| new_team | False | points | 1042 | 4.406 | +0.528 |
| new_team | True | points | 21 | 3.406 | +2.236 |
| reconciled | minutes | minutes | 59 | 5.346 | +1.216 |
| reconciled | minutes+usage | minutes | 33 | 6.347 | -0.531 |
| reconciled | none | minutes | 808 | 4.438 | +1.011 |
| reconciled | usage | minutes | 163 | 4.874 | +0.904 |
| reconciled | minutes | points | 59 | 4.02 | +0.288 |
| reconciled | minutes+usage | points | 33 | 4.063 | -0.534 |
| reconciled | none | points | 808 | 4.41 | +0.583 |
| reconciled | usage | points | 163 | 4.467 | +0.776 |
