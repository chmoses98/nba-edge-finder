## NBA projection scorecard — last 28 days

Generated 2026-11-07T03:09:15Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 310414 across 139 games. Settled: 39402 (void/DNP 16659, stat corrections 185).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 2353 (122) | 1.488 | +0.021 | — | — |  |
| assists | pf-nba-assists (challenger) | 2810 (125) | 1.313 | +0.011 | 0.889 | 79% | — |
| fga | pf-nba-fga (challenger) | 2810 (125) | 2.734 | +0.218 | 1.904 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 2353 (122) | 6.371 | +0.524 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 2810 (125) | 4.914 | +0.573 | 3.463 | 78% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 3631 (122) | Brier 0.1388 | calib +0.023 | log loss 0.4643 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 4336 (125) | Brier 0.0967 | calib +0.035 | log loss 0.2887 | — | -0.0691 [-0.0797, -0.0590] (n=2951) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 2353 (122) | 5.379 | +0.475 | — | — |  |
| points | pf-nba-points (challenger) | 2810 (125) | 4.548 | +0.377 | 3.148 | 80% | — |
| pra | pf-nba-pra (challenger) | 2810 (125) | 5.930 | +0.323 | 4.149 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 2353 (122) | 2.135 | +0.147 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 2810 (125) | 1.829 | -0.057 | 1.265 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 2353 (122) | 0.992 | +0.039 | — | — |  |
| threes | pf-nba-threes (challenger) | 2810 (125) | 0.881 | +0.015 | 0.572 | 77% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.035 (95% CI +0.017..+0.052) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 4336 | 0.0967 |
| incumbent | 3631 | 0.1388 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 785 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 3408 | 0.1133 | 0.845 | 0.797 |
| challenger | LIKELY_OUT | 12 | 0.0005 | 0.013 | 0.0 |
| challenger | UNCERTAIN | 131 | 0.2525 | 0.621 | 0.71 |
| incumbent | n/a | 3631 | 0.1388 | 0.671 | 0.648 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 62 | 5.421 | -1.825 |
| E_inj | 2748 | 4.903 | +0.627 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 2255 | 4.782 | +0.601 |
| new_team | True | minutes | 555 | 5.452 | +0.459 |
| new_team | False | points | 2255 | 4.606 | +0.5 |
| new_team | True | points | 555 | 4.313 | -0.121 |
| reconciled | minutes | minutes | 373 | 5.734 | -1.74 |
| reconciled | minutes+usage | minutes | 134 | 6.277 | -0.917 |
| reconciled | none | minutes | 1871 | 4.683 | +0.938 |
| reconciled | usage | minutes | 432 | 4.787 | +1.451 |
| reconciled | minutes | points | 373 | 4.781 | -0.854 |
| reconciled | minutes+usage | points | 134 | 4.291 | +0.351 |
| reconciled | none | points | 1871 | 4.493 | +0.538 |
| reconciled | usage | points | 432 | 4.666 | +0.754 |
