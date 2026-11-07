## NBA projection scorecard — last 7 days

Generated 2026-11-07T00:03:21Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 305537 across 139 games. Settled: 38772 (void/DNP 16396, stat corrections 185).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 905 (44) | 1.361 | -0.055 | — | — |  |
| assists | pf-nba-assists (challenger) | 991 (44) | 1.317 | +0.057 | 0.882 | 81% | — |
| fga | pf-nba-fga (challenger) | 991 (44) | 2.686 | +0.390 | 1.851 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 905 (44) | 5.381 | +0.050 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 991 (44) | 4.729 | +0.984 | 3.323 | 80% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1316 (44) | Brier 0.1132 | calib +0.007 | log loss 0.3791 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1531 (44) | Brier 0.0858 | calib +0.012 | log loss 0.2564 | — | -0.0554 [-0.0692, -0.0431] (n=1130) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 905 (44) | 4.940 | +0.231 | — | — |  |
| points | pf-nba-points (challenger) | 991 (44) | 4.493 | +0.627 | 3.086 | 80% | — |
| pra | pf-nba-pra (challenger) | 991 (44) | 5.724 | +0.690 | 3.971 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 905 (44) | 1.947 | +0.104 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 991 (44) | 1.781 | +0.054 | 1.219 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 905 (44) | 0.980 | -0.011 | — | — |  |
| threes | pf-nba-threes (challenger) | 991 (44) | 0.921 | +0.020 | 0.600 | 79% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **ALERT** — bias +0.390 (95% CI +0.163..+0.608) exceeds 5% of the mean
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.627 (95% CI +0.355..+0.894) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1531 | 0.0858 |
| incumbent | 1316 | 0.1132 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 309 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1168 | 0.0994 | 0.839 | 0.812 |
| challenger | LIKELY_OUT | 2 | 0.0001 | 0.005 | 0.0 |
| challenger | UNCERTAIN | 52 | 0.2949 | 0.56 | 0.827 |
| incumbent | n/a | 1316 | 0.1132 | 0.695 | 0.688 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 27 | 5.951 | -3.26 |
| E_inj | 964 | 4.695 | +1.103 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 952 | 4.673 | +0.89 |
| new_team | True | minutes | 39 | 6.099 | +3.274 |
| new_team | False | points | 952 | 4.487 | +0.599 |
| new_team | True | points | 39 | 4.634 | +1.313 |
| reconciled | minutes | minutes | 69 | 5.397 | -0.497 |
| reconciled | minutes+usage | minutes | 40 | 6.878 | -0.57 |
| reconciled | none | minutes | 733 | 4.634 | +1.163 |
| reconciled | usage | minutes | 149 | 4.308 | +1.21 |
| reconciled | minutes | points | 69 | 4.525 | -0.034 |
| reconciled | minutes+usage | points | 40 | 4.541 | +0.068 |
| reconciled | none | points | 733 | 4.512 | +0.656 |
| reconciled | usage | points | 149 | 4.368 | +0.938 |
