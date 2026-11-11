## NBA projection scorecard — last 28 days

Generated 2026-11-11T03:05:15Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 373586 across 170 games. Settled: 49373 (void/DNP 20226, stat corrections 239).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 3004 (152) | 1.461 | +0.018 | — | — |  |
| assists | pf-nba-assists (challenger) | 3492 (155) | 1.323 | +0.036 | 0.893 | 79% | — |
| fga | pf-nba-fga (challenger) | 3492 (155) | 2.694 | +0.250 | 1.877 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 3004 (152) | 6.074 | +0.529 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 3492 (155) | 4.818 | +0.655 | 3.395 | 79% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 4525 (152) | Brier 0.1363 | calib +0.013 | log loss 0.4581 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 5384 (155) | Brier 0.0934 | calib +0.026 | log loss 0.2822 | — | -0.0664 [-0.0755, -0.0568] (n=3800) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 3004 (152) | 5.223 | +0.437 | — | — |  |
| points | pf-nba-points (challenger) | 3492 (155) | 4.506 | +0.423 | 3.117 | 80% | — |
| pra | pf-nba-pra (challenger) | 3492 (155) | 5.884 | +0.427 | 4.111 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 3004 (152) | 2.083 | +0.157 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 3492 (155) | 1.829 | -0.020 | 1.262 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 3004 (152) | 0.969 | +0.033 | — | — |  |
| threes | pf-nba-threes (challenger) | 3492 (155) | 0.872 | +0.021 | 0.566 | 77% | — |

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
| challenger | 5384 | 0.0934 |
| incumbent | 4525 | 0.1363 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 1005 | 0.001 | 0.0 | 0.001 |
| challenger | LIKELY_ACTIVE | 4201 | 0.1088 | 0.842 | 0.805 |
| challenger | LIKELY_OUT | 13 | 0.0005 | 0.013 | 0.0 |
| challenger | UNCERTAIN | 165 | 0.2705 | 0.603 | 0.679 |
| incumbent | n/a | 4525 | 0.1363 | 0.677 | 0.664 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 74 | 5.236 | -1.453 |
| E_inj | 3418 | 4.809 | +0.701 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 2924 | 4.703 | +0.69 |
| new_team | True | minutes | 568 | 5.413 | +0.48 |
| new_team | False | points | 2924 | 4.552 | +0.521 |
| new_team | True | points | 568 | 4.269 | -0.081 |
| reconciled | minutes | minutes | 421 | 5.62 | -1.476 |
| reconciled | minutes+usage | minutes | 147 | 6.11 | -0.662 |
| reconciled | none | minutes | 2381 | 4.586 | +0.957 |
| reconciled | usage | minutes | 543 | 4.863 | +1.345 |
| reconciled | minutes | points | 421 | 4.73 | -0.717 |
| reconciled | minutes+usage | points | 147 | 4.27 | +0.221 |
| reconciled | none | points | 2381 | 4.449 | +0.556 |
| reconciled | usage | points | 543 | 4.649 | +0.779 |
