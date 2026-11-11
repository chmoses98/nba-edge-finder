## NBA projection scorecard — season to date

Generated 2026-11-11T04:03:42Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 376111 across 170 games. Settled: 49724 (void/DNP 20319, stat corrections 239).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 3028 (153) | 1.458 | +0.019 | — | — |  |
| assists | pf-nba-assists (challenger) | 3516 (156) | 1.324 | +0.038 | 0.893 | 79% | — |
| fga | pf-nba-fga (challenger) | 3516 (156) | 2.695 | +0.251 | 1.876 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 3028 (153) | 6.051 | +0.541 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 3516 (156) | 4.810 | +0.668 | 3.390 | 79% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 4555 (153) | Brier 0.1361 | calib +0.012 | log loss 0.4573 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 5417 (156) | Brier 0.0931 | calib +0.026 | log loss 0.2815 | — | -0.0663 [-0.0754, -0.0579] (n=3829) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 3028 (153) | 5.218 | +0.441 | — | — |  |
| points | pf-nba-points (challenger) | 3516 (156) | 4.509 | +0.424 | 3.117 | 80% | — |
| pra | pf-nba-pra (challenger) | 3516 (156) | 5.888 | +0.434 | 4.112 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 3028 (153) | 2.080 | +0.162 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 3516 (156) | 1.828 | -0.015 | 1.261 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 3028 (153) | 0.968 | +0.032 | — | — |  |
| threes | pf-nba-threes (challenger) | 3516 (156) | 0.872 | +0.020 | 0.566 | 77% | — |

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
| challenger | 5417 | 0.0931 |
| incumbent | 4555 | 0.1361 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 1010 | 0.001 | 0.0 | 0.001 |
| challenger | LIKELY_ACTIVE | 4229 | 0.1084 | 0.841 | 0.805 |
| challenger | LIKELY_OUT | 13 | 0.0005 | 0.013 | 0.0 |
| challenger | UNCERTAIN | 165 | 0.2705 | 0.603 | 0.679 |
| incumbent | n/a | 4555 | 0.1361 | 0.677 | 0.665 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 74 | 5.236 | -1.453 |
| E_inj | 3442 | 4.8 | +0.714 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 2948 | 4.693 | +0.705 |
| new_team | True | minutes | 568 | 5.413 | +0.48 |
| new_team | False | points | 2948 | 4.555 | +0.522 |
| new_team | True | points | 568 | 4.269 | -0.081 |
| reconciled | minutes | minutes | 421 | 5.62 | -1.476 |
| reconciled | minutes+usage | minutes | 147 | 6.11 | -0.662 |
| reconciled | none | minutes | 2393 | 4.582 | +0.961 |
| reconciled | usage | minutes | 555 | 4.83 | +1.385 |
| reconciled | minutes | points | 421 | 4.73 | -0.717 |
| reconciled | minutes+usage | points | 147 | 4.27 | +0.221 |
| reconciled | none | points | 2393 | 4.455 | +0.553 |
| reconciled | usage | points | 555 | 4.637 | +0.788 |
