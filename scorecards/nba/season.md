## NBA projection scorecard — season to date

Generated 2026-10-31T15:40:54Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 208445 across 89 games. Settled: 25100 (void/DNP 10964, stat corrections 135).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1448 (78) | 1.559 | +0.078 | — | — |  |
| assists | pf-nba-assists (challenger) | 1820 (81) | 1.308 | -0.006 | 0.889 | 79% | — |
| fga | pf-nba-fga (challenger) | 1820 (81) | 2.773 | +0.137 | 1.938 | 80% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1448 (78) | 6.932 | +0.842 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1820 (81) | 4.988 | +0.352 | 3.518 | 78% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 2315 (78) | Brier 0.1527 | calib +0.033 | log loss 0.5100 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 2805 (81) | Brier 0.1046 | calib +0.049 | log loss 0.3115 | — | -0.0752 [-0.0888, -0.0623] (n=1815) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1448 (78) | 5.665 | +0.669 | — | — |  |
| points | pf-nba-points (challenger) | 1820 (81) | 4.587 | +0.270 | 3.181 | 79% | — |
| pra | pf-nba-pra (challenger) | 1820 (81) | 6.043 | +0.179 | 4.240 | 76% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1448 (78) | 2.249 | +0.186 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1820 (81) | 1.858 | -0.104 | 1.290 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1448 (78) | 1.007 | +0.066 | — | — |  |
| threes | pf-nba-threes (challenger) | 1820 (81) | 0.864 | +0.009 | 0.559 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.049 (95% CI +0.027..+0.072) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 2805 | 0.1046 |
| incumbent | 2315 | 0.1527 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 466 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 2250 | 0.1224 | 0.847 | 0.785 |
| challenger | LIKELY_OUT | 10 | 0.0006 | 0.015 | 0.0 |
| challenger | UNCERTAIN | 79 | 0.2286 | 0.655 | 0.684 |
| incumbent | n/a | 2315 | 0.1527 | 0.658 | 0.625 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 36 | 4.922 | -0.747 |
| E_inj | 1784 | 4.989 | +0.374 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1299 | 4.823 | +0.377 |
| new_team | True | minutes | 521 | 5.4 | +0.29 |
| new_team | False | points | 1299 | 4.692 | +0.455 |
| new_team | True | points | 521 | 4.325 | -0.192 |
| reconciled | minutes | minutes | 316 | 5.737 | -1.918 |
| reconciled | minutes+usage | minutes | 94 | 6.021 | -1.065 |
| reconciled | none | minutes | 1138 | 4.699 | +0.808 |
| reconciled | usage | minutes | 272 | 4.967 | +1.57 |
| reconciled | minutes | points | 316 | 4.85 | -0.99 |
| reconciled | minutes+usage | points | 94 | 4.184 | +0.471 |
| reconciled | none | points | 1138 | 4.497 | +0.53 |
| reconciled | usage | points | 272 | 4.797 | +0.579 |
