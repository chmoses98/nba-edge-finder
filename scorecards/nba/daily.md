## NBA projection scorecard — last 7 days

Generated 2026-10-24T01:38:16Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 83362 across 36 games. Settled: 5608 (void/DNP 2807, stat corrections 1).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 270 (18) | 1.985 | +1.180 | — | — |  |
| assists | pf-nba-assists (challenger) | 439 (19) | 1.347 | -0.085 | 0.926 | 78% | — |
| fga | pf-nba-fga (challenger) | 439 (19) | 2.878 | -0.129 | 2.032 | 78% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 270 (18) | 10.092 | +8.399 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 439 (19) | 5.621 | -0.042 | 3.982 | 72% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 529 (18) | Brier 0.2232 | calib +0.017 | log loss 0.6340 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 656 (19) | Brier 0.1193 | calib +0.056 | log loss 0.3753 | — | -0.1228 [-0.1614, -0.0842] (n=352) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 270 (18) | 7.497 | +5.390 | — | — |  |
| points | pf-nba-points (challenger) | 439 (19) | 4.661 | -0.051 | 3.239 | 80% | — |
| pra | pf-nba-pra (challenger) | 439 (19) | 6.033 | -0.239 | 4.265 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 270 (18) | 2.808 | +1.816 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 439 (19) | 1.817 | -0.195 | 1.261 | 82% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 270 (18) | 1.199 | +0.658 | — | — |  |
| threes | pf-nba-threes (challenger) | 439 (19) | 0.811 | +0.091 | 0.519 | 80% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **ALERT** — CRPS 3.982 is 117% of the historical holdout (3.392)
- participation: **ALERT** — bias +0.056 (95% CI +0.005..+0.116) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 656 | 0.1193 |
| incumbent | 529 | 0.2232 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 102 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 532 | 0.145 | 0.862 | 0.789 |
| challenger | LIKELY_OUT | 2 | 0.0001 | 0.01 | 0.0 |
| challenger | UNCERTAIN | 20 | 0.0572 | 0.879 | 0.95 |
| incumbent | n/a | 529 | 0.2232 | 0.528 | 0.51 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 19 | 5.175 | +0.593 |
| E_inj | 420 | 5.641 | -0.07 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 303 | 5.101 | +0.106 |
| new_team | True | minutes | 136 | 6.779 | -0.371 |
| new_team | False | points | 303 | 4.631 | +0.329 |
| new_team | True | points | 136 | 4.727 | -0.899 |
| reconciled | minutes | minutes | 142 | 6.702 | -3.199 |
| reconciled | minutes+usage | minutes | 9 | 6.093 | -3.34 |
| reconciled | none | minutes | 232 | 4.783 | +1.666 |
| reconciled | usage | minutes | 56 | 6.27 | +1.42 |
| reconciled | minutes | points | 142 | 5.162 | -1.956 |
| reconciled | minutes+usage | points | 9 | 3.887 | -0.456 |
| reconciled | none | points | 232 | 4.396 | +0.821 |
| reconciled | usage | points | 56 | 4.609 | +1.232 |
