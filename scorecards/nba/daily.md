## NBA projection scorecard — last 7 days

Generated 2026-11-01T00:51:08Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 216306 across 92 games. Settled: 25744 (void/DNP 11232, stat corrections 135).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 924 (47) | 1.457 | -0.185 | — | — |  |
| assists | pf-nba-assists (challenger) | 1097 (49) | 1.305 | +0.017 | 0.884 | 81% | — |
| fga | pf-nba-fga (challenger) | 1097 (49) | 2.725 | +0.266 | 1.892 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 924 (47) | 5.788 | -0.857 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1097 (49) | 4.705 | +0.633 | 3.301 | 81% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1402 (47) | Brier 0.1295 | calib +0.037 | log loss 0.4528 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1697 (49) | Brier 0.0947 | calib +0.034 | log loss 0.2784 | — | -0.0689 [-0.0836, -0.0557] (n=1152) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 924 (47) | 5.100 | -0.316 | — | — |  |
| points | pf-nba-points (challenger) | 1097 (49) | 4.526 | +0.470 | 3.137 | 80% | — |
| pra | pf-nba-pra (challenger) | 1097 (49) | 6.000 | +0.414 | 4.180 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 924 (47) | 2.078 | -0.159 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1097 (49) | 1.864 | -0.063 | 1.290 | 79% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 924 (47) | 0.970 | -0.066 | — | — |  |
| threes | pf-nba-threes (challenger) | 1097 (49) | 0.897 | -0.009 | 0.580 | 80% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.034 (95% CI +0.011..+0.055) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1697 | 0.0947 |
| incumbent | 1402 | 0.1295 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 302 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1335 | 0.1089 | 0.842 | 0.798 |
| challenger | LIKELY_OUT | 8 | 0.0008 | 0.016 | 0.0 |
| challenger | UNCERTAIN | 52 | 0.2967 | 0.574 | 0.615 |
| incumbent | n/a | 1402 | 0.1295 | 0.696 | 0.659 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 14 | 5.081 | -2.979 |
| E_inj | 1083 | 4.7 | +0.68 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 811 | 4.665 | +0.597 |
| new_team | True | minutes | 286 | 4.818 | +0.735 |
| new_team | False | points | 811 | 4.678 | +0.542 |
| new_team | True | points | 286 | 4.096 | +0.266 |
| reconciled | minutes | minutes | 113 | 4.783 | -0.142 |
| reconciled | minutes+usage | minutes | 56 | 5.075 | +0.023 |
| reconciled | none | minutes | 749 | 4.707 | +0.58 |
| reconciled | usage | minutes | 179 | 4.532 | +1.534 |
| reconciled | minutes | points | 113 | 4.593 | +0.14 |
| reconciled | minutes+usage | points | 56 | 3.443 | +1.251 |
| reconciled | none | points | 749 | 4.509 | +0.485 |
| reconciled | usage | points | 179 | 4.895 | +0.368 |
