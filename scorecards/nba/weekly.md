## NBA projection scorecard — last 28 days

Generated 2026-11-09T12:05:28Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 347088 across 154 games. Settled: 46282 (void/DNP 19258, stat corrections 209).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 2798 (143) | 1.477 | +0.027 | — | — |  |
| assists | pf-nba-assists (challenger) | 3281 (146) | 1.325 | +0.035 | 0.894 | 79% | — |
| fga | pf-nba-fga (challenger) | 3281 (146) | 2.705 | +0.243 | 1.884 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 2798 (143) | 6.157 | +0.546 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 3281 (146) | 4.843 | +0.659 | 3.412 | 79% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 4257 (143) | Brier 0.1349 | calib +0.018 | log loss 0.4513 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 5068 (146) | Brier 0.0932 | calib +0.030 | log loss 0.2792 | — | -0.0660 [-0.0751, -0.0570] (n=3537) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 2798 (143) | 5.278 | +0.455 | — | — |  |
| points | pf-nba-points (challenger) | 3281 (146) | 4.520 | +0.424 | 3.126 | 80% | — |
| pra | pf-nba-pra (challenger) | 3281 (146) | 5.907 | +0.414 | 4.129 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 2798 (143) | 2.102 | +0.153 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 3281 (146) | 1.834 | -0.035 | 1.267 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 2798 (143) | 0.976 | +0.039 | — | — |  |
| threes | pf-nba-threes (challenger) | 3281 (146) | 0.875 | +0.023 | 0.568 | 78% | — |

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
| challenger | 5068 | 0.0932 |
| incumbent | 4257 | 0.1349 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 944 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 3966 | 0.1099 | 0.842 | 0.801 |
| challenger | LIKELY_OUT | 12 | 0.0005 | 0.013 | 0.0 |
| challenger | UNCERTAIN | 146 | 0.2503 | 0.624 | 0.712 |
| incumbent | n/a | 4257 | 0.1349 | 0.675 | 0.657 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 71 | 5.364 | -1.529 |
| E_inj | 3210 | 4.832 | +0.708 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 2716 | 4.723 | +0.692 |
| new_team | True | minutes | 565 | 5.42 | +0.504 |
| new_team | False | points | 2716 | 4.569 | +0.531 |
| new_team | True | points | 565 | 4.284 | -0.089 |
| reconciled | minutes | minutes | 395 | 5.689 | -1.615 |
| reconciled | minutes+usage | minutes | 147 | 6.11 | -0.662 |
| reconciled | none | minutes | 2240 | 4.614 | +0.976 |
| reconciled | usage | minutes | 499 | 4.832 | +1.427 |
| reconciled | minutes | points | 395 | 4.79 | -0.743 |
| reconciled | minutes+usage | points | 147 | 4.27 | +0.221 |
| reconciled | none | points | 2240 | 4.461 | +0.567 |
| reconciled | usage | points | 499 | 4.644 | +0.768 |
