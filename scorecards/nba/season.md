## NBA projection scorecard — season to date

Generated 2026-11-02T03:39:33Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 234897 across 107 games. Settled: 27974 (void/DNP 12186, stat corrections 155).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1627 (87) | 1.543 | +0.060 | — | — |  |
| assists | pf-nba-assists (challenger) | 2020 (90) | 1.312 | -0.001 | 0.891 | 79% | — |
| fga | pf-nba-fga (challenger) | 2020 (90) | 2.795 | +0.185 | 1.948 | 80% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1627 (87) | 6.786 | +0.736 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 2020 (90) | 5.003 | +0.429 | 3.527 | 78% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 2583 (87) | Brier 0.1486 | calib +0.032 | log loss 0.4952 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 3116 (90) | Brier 0.1016 | calib +0.045 | log loss 0.3028 | — | -0.0735 [-0.0849, -0.0616] (n=2043) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1627 (87) | 5.611 | +0.629 | — | — |  |
| points | pf-nba-points (challenger) | 2020 (90) | 4.611 | +0.326 | 3.193 | 79% | — |
| pra | pf-nba-pra (challenger) | 2020 (90) | 6.053 | +0.264 | 4.239 | 76% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1627 (87) | 2.201 | +0.191 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 2020 (90) | 1.840 | -0.075 | 1.276 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1627 (87) | 1.012 | +0.061 | — | — |  |
| threes | pf-nba-threes (challenger) | 2020 (90) | 0.875 | +0.012 | 0.569 | 77% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.045 (95% CI +0.022..+0.064) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 3116 | 0.1016 |
| incumbent | 2583 | 0.1486 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 534 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 2482 | 0.1188 | 0.847 | 0.79 |
| challenger | LIKELY_OUT | 11 | 0.0006 | 0.014 | 0.0 |
| challenger | UNCERTAIN | 89 | 0.2437 | 0.651 | 0.674 |
| incumbent | n/a | 2583 | 0.1486 | 0.662 | 0.63 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 39 | 5.112 | -1.253 |
| E_inj | 1981 | 5.0 | +0.462 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1489 | 4.84 | +0.432 |
| new_team | True | minutes | 531 | 5.458 | +0.422 |
| new_team | False | points | 1489 | 4.714 | +0.505 |
| new_team | True | points | 531 | 4.321 | -0.175 |
| reconciled | minutes | minutes | 328 | 5.664 | -1.926 |
| reconciled | minutes+usage | minutes | 94 | 6.021 | -1.065 |
| reconciled | none | minutes | 1305 | 4.777 | +0.875 |
| reconciled | usage | minutes | 293 | 4.941 | +1.559 |
| reconciled | minutes | points | 328 | 4.86 | -0.963 |
| reconciled | minutes+usage | points | 94 | 4.184 | +0.471 |
| reconciled | none | points | 1305 | 4.539 | +0.565 |
| reconciled | usage | points | 293 | 4.79 | +0.66 |
