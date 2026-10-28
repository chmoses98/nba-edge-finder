## NBA projection scorecard — last 7 days

Generated 2026-10-28T00:39:30Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 145070 across 68 games. Settled: 15878 (void/DNP 7128, stat corrections 86).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 848 (47) | 1.614 | +0.231 | — | — |  |
| assists | pf-nba-assists (challenger) | 1134 (50) | 1.301 | +0.001 | 0.885 | 80% | — |
| fga | pf-nba-fga (challenger) | 1134 (50) | 2.833 | +0.106 | 1.986 | 80% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 848 (47) | 7.874 | +1.631 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1134 (50) | 5.305 | +0.310 | 3.768 | 75% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1393 (47) | Brier 0.1708 | calib +0.033 | log loss 0.5620 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1731 (50) | Brier 0.1084 | calib +0.052 | log loss 0.3260 | — | -0.0883 [-0.1088, -0.0691] (n=1062) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 848 (47) | 5.940 | +1.126 | — | — |  |
| points | pf-nba-points (challenger) | 1134 (50) | 4.576 | +0.183 | 3.186 | 79% | — |
| pra | pf-nba-pra (challenger) | 1134 (50) | 6.180 | +0.078 | 4.358 | 75% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 848 (47) | 2.406 | +0.316 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1134 (50) | 1.898 | -0.152 | 1.326 | 78% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 848 (47) | 1.015 | +0.143 | — | — |  |
| threes | pf-nba-threes (challenger) | 1134 (50) | 0.839 | +0.027 | 0.545 | 79% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **WATCH** — CRPS 111% of historical holdout
- participation: **ALERT** — bias +0.052 (95% CI +0.025..+0.082) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1731 | 0.1084 |
| incumbent | 1393 | 0.1708 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 276 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1400 | 0.1282 | 0.85 | 0.784 |
| challenger | LIKELY_OUT | 6 | 0.001 | 0.022 | 0.0 |
| challenger | UNCERTAIN | 49 | 0.1655 | 0.693 | 0.735 |
| incumbent | n/a | 1393 | 0.1708 | 0.641 | 0.609 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 30 | 4.864 | -0.202 |
| E_inj | 1104 | 5.317 | +0.324 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 772 | 5.119 | +0.335 |
| new_team | True | minutes | 362 | 5.702 | +0.257 |
| new_team | False | points | 772 | 4.725 | +0.397 |
| new_team | True | points | 362 | 4.258 | -0.273 |
| reconciled | minutes | minutes | 231 | 6.265 | -2.425 |
| reconciled | minutes+usage | minutes | 49 | 6.662 | -1.964 |
| reconciled | none | minutes | 657 | 4.873 | +0.997 |
| reconciled | usage | minutes | 197 | 5.281 | +1.796 |
| reconciled | minutes | points | 231 | 4.927 | -1.43 |
| reconciled | minutes+usage | points | 49 | 4.872 | -0.167 |
| reconciled | none | points | 657 | 4.388 | +0.681 |
| reconciled | usage | points | 197 | 4.715 | +0.504 |
