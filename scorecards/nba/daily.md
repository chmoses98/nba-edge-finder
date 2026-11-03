## NBA projection scorecard — last 7 days

Generated 2026-11-03T02:36:17Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 253066 across 107 games. Settled: 28966 (void/DNP 12519, stat corrections 155).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 809 (41) | 1.421 | -0.186 | — | — |  |
| assists | pf-nba-assists (challenger) | 915 (41) | 1.314 | -0.011 | 0.888 | 80% | — |
| fga | pf-nba-fga (challenger) | 915 (41) | 2.705 | +0.311 | 1.874 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 809 (41) | 5.344 | -0.653 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 915 (41) | 4.590 | +0.763 | 3.206 | 82% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1218 (41) | Brier 0.1170 | calib +0.033 | log loss 0.4059 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1420 (41) | Brier 0.0891 | calib +0.026 | log loss 0.2639 | — | -0.0551 [-0.0661, -0.0444] (n=1013) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 809 (41) | 5.112 | -0.239 | — | — |  |
| points | pf-nba-points (challenger) | 915 (41) | 4.617 | +0.502 | 3.172 | 79% | — |
| pra | pf-nba-pra (challenger) | 915 (41) | 5.861 | +0.471 | 4.060 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 809 (41) | 1.977 | -0.049 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 915 (41) | 1.778 | +0.006 | 1.220 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 809 (41) | 1.009 | -0.084 | — | — |  |
| threes | pf-nba-threes (challenger) | 915 (41) | 0.930 | -0.025 | 0.606 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1420 | 0.0891 |
| incumbent | 1218 | 0.117 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 272 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1103 | 0.1017 | 0.842 | 0.809 |
| challenger | LIKELY_OUT | 5 | 0.0 | 0.005 | 0.0 |
| challenger | UNCERTAIN | 40 | 0.3601 | 0.597 | 0.575 |
| incumbent | n/a | 1218 | 0.117 | 0.697 | 0.664 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 8 | 5.656 | -4.326 |
| E_inj | 907 | 4.581 | +0.808 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 751 | 4.513 | +0.67 |
| new_team | True | minutes | 164 | 4.944 | +1.189 |
| new_team | False | points | 751 | 4.668 | +0.545 |
| new_team | True | points | 164 | 4.384 | +0.305 |
| reconciled | minutes | minutes | 76 | 4.103 | -0.163 |
| reconciled | minutes+usage | minutes | 50 | 5.517 | +1.239 |
| reconciled | none | minutes | 673 | 4.635 | +0.829 |
| reconciled | usage | minutes | 116 | 4.25 | +0.779 |
| reconciled | minutes | points | 76 | 4.674 | +0.568 |
| reconciled | minutes+usage | points | 50 | 3.803 | +1.369 |
| reconciled | none | points | 673 | 4.651 | +0.387 |
| reconciled | usage | points | 116 | 4.736 | +0.753 |
