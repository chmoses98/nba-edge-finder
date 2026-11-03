## NBA projection scorecard — last 7 days

Generated 2026-11-03T02:09:33Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 252365 across 107 games. Settled: 28664 (void/DNP 12385, stat corrections 155).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 789 (40) | 1.427 | -0.190 | — | — |  |
| assists | pf-nba-assists (challenger) | 895 (40) | 1.315 | -0.010 | 0.889 | 80% | — |
| fga | pf-nba-fga (challenger) | 895 (40) | 2.713 | +0.335 | 1.875 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 789 (40) | 5.355 | -0.628 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 895 (40) | 4.597 | +0.794 | 3.212 | 82% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1188 (40) | Brier 0.1170 | calib +0.033 | log loss 0.4069 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1388 (40) | Brier 0.0896 | calib +0.026 | log loss 0.2653 | — | -0.0546 [-0.0658, -0.0448] (n=986) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 789 (40) | 5.132 | -0.228 | — | — |  |
| points | pf-nba-points (challenger) | 895 (40) | 4.637 | +0.521 | 3.185 | 78% | — |
| pra | pf-nba-pra (challenger) | 895 (40) | 5.901 | +0.507 | 4.079 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 789 (40) | 1.972 | -0.032 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 895 (40) | 1.774 | +0.024 | 1.216 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 789 (40) | 1.009 | -0.076 | — | — |  |
| threes | pf-nba-threes (challenger) | 895 (40) | 0.928 | -0.018 | 0.605 | 79% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.521 (95% CI +0.157..+0.887) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1388 | 0.0896 |
| incumbent | 1188 | 0.117 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 264 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1080 | 0.1026 | 0.84 | 0.807 |
| challenger | LIKELY_OUT | 5 | 0.0 | 0.005 | 0.0 |
| challenger | UNCERTAIN | 39 | 0.348 | 0.589 | 0.59 |
| incumbent | n/a | 1188 | 0.117 | 0.697 | 0.664 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 8 | 5.656 | -4.326 |
| E_inj | 887 | 4.588 | +0.84 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 733 | 4.513 | +0.71 |
| new_team | True | minutes | 162 | 4.977 | +1.175 |
| new_team | False | points | 733 | 4.693 | +0.572 |
| new_team | True | points | 162 | 4.381 | +0.29 |
| reconciled | minutes | minutes | 76 | 4.103 | -0.163 |
| reconciled | minutes+usage | minutes | 50 | 5.517 | +1.239 |
| reconciled | none | minutes | 673 | 4.635 | +0.829 |
| reconciled | usage | minutes | 96 | 4.244 | +1.075 |
| reconciled | minutes | points | 76 | 4.674 | +0.568 |
| reconciled | minutes+usage | points | 50 | 3.803 | +1.369 |
| reconciled | none | points | 673 | 4.651 | +0.387 |
| reconciled | usage | points | 96 | 4.943 | +0.98 |
