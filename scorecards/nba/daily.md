## NBA projection scorecard — last 7 days

Generated 2026-11-07T18:26:15Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 315956 across 142 games. Settled: 41685 (void/DNP 17569, stat corrections 209).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1050 (51) | 1.383 | -0.038 | — | — |  |
| assists | pf-nba-assists (challenger) | 1148 (51) | 1.329 | +0.072 | 0.891 | 80% | — |
| fga | pf-nba-fga (challenger) | 1148 (51) | 2.647 | +0.395 | 1.830 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1050 (51) | 5.431 | +0.103 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1148 (51) | 4.745 | +1.046 | 3.326 | 80% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1524 (51) | Brier 0.1144 | calib +0.005 | log loss 0.3848 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1775 (51) | Brier 0.0805 | calib +0.006 | log loss 0.2423 | — | -0.0597 [-0.0725, -0.0475] (n=1327) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1050 (51) | 4.929 | +0.193 | — | — |  |
| points | pf-nba-points (challenger) | 1148 (51) | 4.477 | +0.589 | 3.085 | 81% | — |
| pra | pf-nba-pra (challenger) | 1148 (51) | 5.735 | +0.663 | 3.990 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1050 (51) | 1.964 | +0.109 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1148 (51) | 1.801 | +0.050 | 1.233 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1050 (51) | 0.964 | -0.000 | — | — |  |
| threes | pf-nba-threes (challenger) | 1148 (51) | 0.911 | +0.033 | 0.595 | 79% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **ALERT** — bias +0.395 (95% CI +0.180..+0.595) exceeds 5% of the mean
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.589 (95% CI +0.325..+0.898) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1775 | 0.0805 |
| incumbent | 1524 | 0.1144 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 372 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1347 | 0.0946 | 0.838 | 0.823 |
| challenger | LIKELY_OUT | 2 | 0.0001 | 0.006 | 0.0 |
| challenger | UNCERTAIN | 54 | 0.2859 | 0.558 | 0.741 |
| incumbent | n/a | 1524 | 0.1144 | 0.694 | 0.689 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 27 | 5.91 | -3.17 |
| E_inj | 1121 | 4.717 | +1.147 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1109 | 4.702 | +0.971 |
| new_team | True | minutes | 39 | 5.96 | +3.174 |
| new_team | False | points | 1109 | 4.5 | +0.575 |
| new_team | True | points | 39 | 3.845 | +0.974 |
| reconciled | minutes | minutes | 57 | 5.714 | -0.753 |
| reconciled | minutes+usage | minutes | 40 | 6.878 | -0.57 |
| reconciled | none | minutes | 860 | 4.605 | +1.193 |
| reconciled | usage | minutes | 191 | 4.637 | +1.257 |
| reconciled | minutes | points | 57 | 4.401 | -0.101 |
| reconciled | minutes+usage | points | 40 | 4.541 | +0.068 |
| reconciled | none | points | 860 | 4.447 | +0.562 |
| reconciled | usage | points | 191 | 4.624 | +1.024 |
