## NBA projection scorecard — last 7 days

Generated 2026-11-08T18:14:57Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 331926 across 149 games. Settled: 43920 (void/DNP 18440, stat corrections 209).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1052 (51) | 1.412 | -0.034 | — | — |  |
| assists | pf-nba-assists (challenger) | 1139 (51) | 1.365 | +0.086 | 0.913 | 81% | — |
| fga | pf-nba-fga (challenger) | 1139 (51) | 2.538 | +0.294 | 1.767 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1052 (51) | 5.369 | +0.082 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1139 (51) | 4.649 | +0.938 | 3.262 | 81% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1523 (51) | Brier 0.1122 | calib +0.005 | log loss 0.3824 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1775 (51) | Brier 0.0797 | calib +0.010 | log loss 0.2394 | — | -0.0557 [-0.0702, -0.0435] (n=1350) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1052 (51) | 4.820 | +0.247 | — | — |  |
| points | pf-nba-points (challenger) | 1139 (51) | 4.363 | +0.614 | 3.015 | 82% | — |
| pra | pf-nba-pra (challenger) | 1139 (51) | 5.651 | +0.641 | 3.951 | 78% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1052 (51) | 1.988 | +0.062 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1139 (51) | 1.832 | -0.020 | 1.263 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1052 (51) | 0.938 | +0.002 | — | — |  |
| threes | pf-nba-threes (challenger) | 1139 (51) | 0.888 | +0.039 | 0.576 | 80% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.614 (95% CI +0.275..+0.900) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1775 | 0.0797 |
| incumbent | 1523 | 0.1122 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 380 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1345 | 0.096 | 0.839 | 0.819 |
| challenger | LIKELY_OUT | 1 | 0.0 | 0.001 | 0.0 |
| challenger | UNCERTAIN | 49 | 0.2509 | 0.563 | 0.776 |
| incumbent | n/a | 1523 | 0.1122 | 0.696 | 0.691 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 28 | 5.76 | -2.842 |
| E_inj | 1111 | 4.621 | +1.034 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1107 | 4.63 | +0.899 |
| new_team | True | minutes | 32 | 5.317 | +2.289 |
| new_team | False | points | 1107 | 4.383 | +0.595 |
| new_team | True | points | 32 | 3.683 | +1.27 |
| reconciled | minutes | minutes | 67 | 5.809 | -0.094 |
| reconciled | minutes+usage | minutes | 40 | 6.878 | -0.57 |
| reconciled | none | minutes | 852 | 4.437 | +1.084 |
| reconciled | usage | minutes | 180 | 4.726 | +0.969 |
| reconciled | minutes | points | 67 | 4.452 | +0.337 |
| reconciled | minutes+usage | points | 40 | 4.541 | +0.068 |
| reconciled | none | points | 852 | 4.302 | +0.606 |
| reconciled | usage | points | 180 | 4.58 | +0.875 |
