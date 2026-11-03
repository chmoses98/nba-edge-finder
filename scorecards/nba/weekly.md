## NBA projection scorecard — last 28 days

Generated 2026-11-03T02:36:17Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 253066 across 107 games. Settled: 28966 (void/DNP 12519, stat corrections 155).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1689 (90) | 1.528 | +0.050 | — | — |  |
| assists | pf-nba-assists (challenger) | 2090 (93) | 1.307 | -0.010 | 0.888 | 79% | — |
| fga | pf-nba-fga (challenger) | 2090 (93) | 2.777 | +0.168 | 1.937 | 80% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1689 (90) | 6.704 | +0.693 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 2090 (93) | 4.985 | +0.462 | 3.514 | 78% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 2671 (90) | Brier 0.1480 | calib +0.031 | log loss 0.4935 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 3220 (93) | Brier 0.1008 | calib +0.043 | log loss 0.3008 | — | -0.0738 [-0.0851, -0.0625] (n=2117) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1689 (90) | 5.575 | +0.576 | — | — |  |
| points | pf-nba-points (challenger) | 2090 (93) | 4.597 | +0.300 | 3.183 | 79% | — |
| pra | pf-nba-pra (challenger) | 2090 (93) | 6.029 | +0.214 | 4.224 | 76% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1689 (90) | 2.199 | +0.170 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 2090 (93) | 1.842 | -0.090 | 1.277 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1689 (90) | 1.014 | +0.046 | — | — |  |
| threes | pf-nba-threes (challenger) | 2090 (93) | 0.880 | -0.000 | 0.574 | 77% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.043 (95% CI +0.024..+0.062) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 3220 | 0.1008 |
| incumbent | 2671 | 0.148 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 557 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 2562 | 0.1178 | 0.847 | 0.792 |
| challenger | LIKELY_OUT | 11 | 0.0006 | 0.014 | 0.0 |
| challenger | UNCERTAIN | 90 | 0.2502 | 0.653 | 0.667 |
| incumbent | n/a | 2671 | 0.148 | 0.663 | 0.632 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 39 | 5.112 | -1.253 |
| E_inj | 2051 | 4.982 | +0.495 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1555 | 4.823 | +0.464 |
| new_team | True | minutes | 535 | 5.455 | +0.457 |
| new_team | False | points | 1555 | 4.695 | +0.458 |
| new_team | True | points | 535 | 4.314 | -0.16 |
| reconciled | minutes | minutes | 328 | 5.664 | -1.926 |
| reconciled | minutes+usage | minutes | 108 | 6.085 | -0.596 |
| reconciled | none | minutes | 1341 | 4.75 | +0.908 |
| reconciled | usage | minutes | 313 | 4.899 | +1.419 |
| reconciled | minutes | points | 328 | 4.86 | -0.963 |
| reconciled | minutes+usage | points | 108 | 4.295 | +0.52 |
| reconciled | none | points | 1341 | 4.528 | +0.522 |
| reconciled | usage | points | 313 | 4.723 | +0.596 |
