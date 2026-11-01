## NBA projection scorecard — last 28 days

Generated 2026-11-01T23:38:14Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 227289 across 107 games. Settled: 27674 (void/DNP 12026, stat corrections 155).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1608 (86) | 1.543 | +0.058 | — | — |  |
| assists | pf-nba-assists (challenger) | 2000 (89) | 1.311 | -0.004 | 0.891 | 79% | — |
| fga | pf-nba-fga (challenger) | 2000 (89) | 2.797 | +0.178 | 1.950 | 80% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1608 (86) | 6.805 | +0.769 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 2000 (89) | 5.007 | +0.442 | 3.532 | 78% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 2553 (86) | Brier 0.1490 | calib +0.032 | log loss 0.4965 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 3081 (89) | Brier 0.1021 | calib +0.045 | log loss 0.3043 | — | -0.0738 [-0.0870, -0.0631] (n=2017) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1608 (86) | 5.621 | +0.624 | — | — |  |
| points | pf-nba-points (challenger) | 2000 (89) | 4.618 | +0.319 | 3.199 | 79% | — |
| pra | pf-nba-pra (challenger) | 2000 (89) | 6.060 | +0.256 | 4.244 | 76% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1608 (86) | 2.207 | +0.191 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 2000 (89) | 1.844 | -0.075 | 1.279 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1608 (86) | 1.011 | +0.063 | — | — |  |
| threes | pf-nba-threes (challenger) | 2000 (89) | 0.873 | +0.013 | 0.568 | 77% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.045 (95% CI +0.024..+0.065) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 3081 | 0.1021 |
| incumbent | 2553 | 0.149 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 523 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 2459 | 0.1192 | 0.846 | 0.789 |
| challenger | LIKELY_OUT | 11 | 0.0006 | 0.014 | 0.0 |
| challenger | UNCERTAIN | 88 | 0.2442 | 0.653 | 0.682 |
| incumbent | n/a | 2553 | 0.149 | 0.661 | 0.63 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 39 | 5.112 | -1.253 |
| E_inj | 1961 | 5.005 | +0.476 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1470 | 4.848 | +0.457 |
| new_team | True | minutes | 530 | 5.447 | +0.401 |
| new_team | False | points | 1470 | 4.723 | +0.499 |
| new_team | True | points | 530 | 4.325 | -0.18 |
| reconciled | minutes | minutes | 328 | 5.664 | -1.926 |
| reconciled | minutes+usage | minutes | 94 | 6.021 | -1.065 |
| reconciled | none | minutes | 1285 | 4.78 | +0.902 |
| reconciled | usage | minutes | 293 | 4.941 | +1.559 |
| reconciled | minutes | points | 328 | 4.86 | -0.963 |
| reconciled | minutes+usage | points | 94 | 4.184 | +0.471 |
| reconciled | none | points | 1285 | 4.549 | +0.558 |
| reconciled | usage | points | 293 | 4.79 | +0.66 |
