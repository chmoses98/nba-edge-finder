## NBA projection scorecard — last 28 days

Generated 2026-11-01T17:35:20Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 218817 across 92 games. Settled: 27389 (void/DNP 11871, stat corrections 155).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1590 (85) | 1.539 | +0.062 | — | — |  |
| assists | pf-nba-assists (challenger) | 1981 (88) | 1.307 | -0.002 | 0.889 | 79% | — |
| fga | pf-nba-fga (challenger) | 1981 (88) | 2.803 | +0.183 | 1.954 | 80% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1590 (85) | 6.813 | +0.798 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1981 (88) | 5.015 | +0.456 | 3.540 | 78% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 2525 (85) | Brier 0.1497 | calib +0.031 | log loss 0.4989 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 3047 (88) | Brier 0.1023 | calib +0.044 | log loss 0.3052 | — | -0.0746 [-0.0882, -0.0638] (n=1990) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1590 (85) | 5.624 | +0.629 | — | — |  |
| points | pf-nba-points (challenger) | 1981 (88) | 4.617 | +0.318 | 3.199 | 79% | — |
| pra | pf-nba-pra (challenger) | 1981 (88) | 6.064 | +0.260 | 4.246 | 76% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1590 (85) | 2.204 | +0.191 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1981 (88) | 1.840 | -0.074 | 1.276 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1590 (85) | 1.010 | +0.064 | — | — |  |
| threes | pf-nba-threes (challenger) | 1981 (88) | 0.872 | +0.013 | 0.567 | 77% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.044 (95% CI +0.024..+0.064) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 3047 | 0.1023 |
| incumbent | 2525 | 0.1497 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 516 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 2432 | 0.1194 | 0.846 | 0.79 |
| challenger | LIKELY_OUT | 11 | 0.0006 | 0.014 | 0.0 |
| challenger | UNCERTAIN | 88 | 0.2442 | 0.653 | 0.682 |
| incumbent | n/a | 2525 | 0.1497 | 0.661 | 0.63 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 39 | 5.112 | -1.253 |
| E_inj | 1942 | 5.013 | +0.49 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1451 | 4.857 | +0.476 |
| new_team | True | minutes | 530 | 5.447 | +0.401 |
| new_team | False | points | 1451 | 4.724 | +0.5 |
| new_team | True | points | 530 | 4.325 | -0.18 |
| reconciled | minutes | minutes | 328 | 5.664 | -1.926 |
| reconciled | minutes+usage | minutes | 94 | 6.021 | -1.065 |
| reconciled | none | minutes | 1266 | 4.789 | +0.93 |
| reconciled | usage | minutes | 293 | 4.941 | +1.559 |
| reconciled | minutes | points | 328 | 4.86 | -0.963 |
| reconciled | minutes+usage | points | 94 | 4.184 | +0.471 |
| reconciled | none | points | 1266 | 4.546 | +0.56 |
| reconciled | usage | points | 293 | 4.79 | +0.66 |
