## NBA projection scorecard — season to date

Generated 2026-11-10T23:49:26Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 370858 across 170 games. Settled: 48985 (void/DNP 20160, stat corrections 239).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 2977 (151) | 1.465 | +0.016 | — | — |  |
| assists | pf-nba-assists (challenger) | 3465 (154) | 1.326 | +0.035 | 0.895 | 79% | — |
| fga | pf-nba-fga (challenger) | 3465 (154) | 2.699 | +0.251 | 1.879 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 2977 (151) | 6.096 | +0.516 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 3465 (154) | 4.825 | +0.663 | 3.400 | 79% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 4496 (151) | Brier 0.1359 | calib +0.014 | log loss 0.4573 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 5349 (154) | Brier 0.0930 | calib +0.027 | log loss 0.2812 | — | -0.0661 [-0.0747, -0.0575] (n=3771) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 2977 (151) | 5.238 | +0.427 | — | — |  |
| points | pf-nba-points (challenger) | 3465 (154) | 4.514 | +0.423 | 3.122 | 80% | — |
| pra | pf-nba-pra (challenger) | 3465 (154) | 5.897 | +0.425 | 4.121 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 2977 (151) | 2.088 | +0.157 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 3465 (154) | 1.831 | -0.019 | 1.263 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 2977 (151) | 0.970 | +0.034 | — | — |  |
| threes | pf-nba-threes (challenger) | 3465 (154) | 0.873 | +0.022 | 0.566 | 77% | — |

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
| challenger | 5349 | 0.093 |
| incumbent | 4496 | 0.1359 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 1003 | 0.001 | 0.0 | 0.001 |
| challenger | LIKELY_ACTIVE | 4169 | 0.1085 | 0.842 | 0.805 |
| challenger | LIKELY_OUT | 13 | 0.0005 | 0.013 | 0.0 |
| challenger | UNCERTAIN | 164 | 0.2674 | 0.606 | 0.677 |
| incumbent | n/a | 4496 | 0.1359 | 0.676 | 0.662 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 73 | 5.282 | -1.499 |
| E_inj | 3392 | 4.816 | +0.709 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 2898 | 4.709 | +0.698 |
| new_team | True | minutes | 567 | 5.421 | +0.482 |
| new_team | False | points | 2898 | 4.562 | +0.522 |
| new_team | True | points | 567 | 4.273 | -0.085 |
| reconciled | minutes | minutes | 408 | 5.662 | -1.491 |
| reconciled | minutes+usage | minutes | 147 | 6.11 | -0.662 |
| reconciled | none | minutes | 2367 | 4.593 | +0.959 |
| reconciled | usage | minutes | 543 | 4.863 | +1.345 |
| reconciled | minutes | points | 408 | 4.762 | -0.758 |
| reconciled | minutes+usage | points | 147 | 4.27 | +0.221 |
| reconciled | none | points | 2367 | 4.456 | +0.557 |
| reconciled | usage | points | 543 | 4.649 | +0.779 |
