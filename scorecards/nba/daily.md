## NBA projection scorecard — last 7 days

Generated 2026-11-10T02:16:13Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 355541 across 160 games. Settled: 46282 (void/DNP 19258, stat corrections 235).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 890 (42) | 1.418 | -0.009 | — | — |  |
| assists | pf-nba-assists (challenger) | 947 (42) | 1.377 | +0.112 | 0.919 | 79% | — |
| fga | pf-nba-fga (challenger) | 947 (42) | 2.592 | +0.354 | 1.803 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 890 (42) | 5.336 | +0.486 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 947 (42) | 4.649 | +1.042 | 3.272 | 81% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1256 (42) | Brier 0.1110 | calib -0.013 | log loss 0.3786 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1465 (42) | Brier 0.0787 | calib +0.006 | log loss 0.2380 | — | -0.0516 [-0.0642, -0.0398] (n=1140) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 890 (42) | 4.792 | +0.261 | — | — |  |
| points | pf-nba-points (challenger) | 947 (42) | 4.382 | +0.555 | 3.027 | 80% | — |
| pra | pf-nba-pra (challenger) | 947 (42) | 5.726 | +0.688 | 4.010 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 890 (42) | 1.999 | +0.145 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 947 (42) | 1.885 | +0.065 | 1.289 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 890 (42) | 0.905 | +0.045 | — | — |  |
| threes | pf-nba-threes (challenger) | 947 (42) | 0.858 | +0.074 | 0.552 | 81% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.555 (95% CI +0.213..+0.913) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1465 | 0.0787 |
| incumbent | 1256 | 0.111 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 305 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1114 | 0.0931 | 0.834 | 0.819 |
| challenger | LIKELY_OUT | 1 | 0.0 | 0.001 | 0.0 |
| challenger | UNCERTAIN | 45 | 0.2576 | 0.593 | 0.778 |
| incumbent | n/a | 1256 | 0.111 | 0.696 | 0.709 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 25 | 6.106 | -2.058 |
| E_inj | 922 | 4.61 | +1.126 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 923 | 4.658 | +1.04 |
| new_team | True | minutes | 24 | 4.306 | +1.132 |
| new_team | False | points | 923 | 4.402 | +0.521 |
| new_team | True | points | 24 | 3.619 | +1.835 |
| reconciled | minutes | minutes | 46 | 5.483 | +0.916 |
| reconciled | minutes+usage | minutes | 33 | 6.347 | -0.531 |
| reconciled | none | minutes | 740 | 4.5 | +1.134 |
| reconciled | usage | minutes | 128 | 4.777 | +0.961 |
| reconciled | minutes | points | 46 | 4.055 | +0.717 |
| reconciled | minutes+usage | points | 33 | 4.063 | -0.534 |
| reconciled | none | points | 740 | 4.397 | +0.587 |
| reconciled | usage | points | 128 | 4.5 | +0.588 |
