## NBA projection scorecard — season to date

Generated 2026-11-05T21:31:21Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 288443 across 132 games. Settled: 38034 (void/DNP 16257, stat corrections 167).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 2263 (118) | 1.480 | +0.036 | — | — |  |
| assists | pf-nba-assists (challenger) | 2716 (121) | 1.305 | +0.020 | 0.884 | 79% | — |
| fga | pf-nba-fga (challenger) | 2716 (121) | 2.733 | +0.215 | 1.905 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 2263 (118) | 6.393 | +0.522 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 2716 (121) | 4.913 | +0.554 | 3.467 | 78% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 3511 (118) | Brier 0.1393 | calib +0.026 | log loss 0.4666 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 4196 (121) | Brier 0.0983 | calib +0.037 | log loss 0.2929 | — | -0.0683 [-0.0787, -0.0587] (n=2841) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 2263 (118) | 5.395 | +0.488 | — | — |  |
| points | pf-nba-points (challenger) | 2716 (121) | 4.539 | +0.380 | 3.142 | 80% | — |
| pra | pf-nba-pra (challenger) | 2716 (121) | 5.921 | +0.337 | 4.140 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 2263 (118) | 2.141 | +0.147 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 2716 (121) | 1.831 | -0.059 | 1.266 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 2263 (118) | 0.993 | +0.046 | — | — |  |
| threes | pf-nba-threes (challenger) | 2716 (121) | 0.879 | +0.019 | 0.570 | 77% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.037 (95% CI +0.021..+0.056) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 4196 | 0.0983 |
| incumbent | 3511 | 0.1393 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 750 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 3310 | 0.1151 | 0.844 | 0.793 |
| challenger | LIKELY_OUT | 11 | 0.0006 | 0.014 | 0.0 |
| challenger | UNCERTAIN | 125 | 0.2504 | 0.625 | 0.728 |
| incumbent | n/a | 3511 | 0.1393 | 0.671 | 0.645 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 60 | 5.51 | -1.794 |
| E_inj | 2656 | 4.9 | +0.607 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 2162 | 4.775 | +0.576 |
| new_team | True | minutes | 554 | 5.453 | +0.469 |
| new_team | False | points | 2162 | 4.597 | +0.511 |
| new_team | True | points | 554 | 4.312 | -0.13 |
| reconciled | minutes | minutes | 359 | 5.769 | -1.913 |
| reconciled | minutes+usage | minutes | 134 | 6.277 | -0.917 |
| reconciled | none | minutes | 1802 | 4.683 | +0.947 |
| reconciled | usage | minutes | 421 | 4.734 | +1.443 |
| reconciled | minutes | points | 359 | 4.824 | -0.907 |
| reconciled | minutes+usage | points | 134 | 4.291 | +0.351 |
| reconciled | none | points | 1802 | 4.476 | +0.563 |
| reconciled | usage | points | 421 | 4.645 | +0.706 |
