## NBA projection scorecard — last 7 days

Generated 2026-11-12T04:07:36Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 391903 across 174 games. Settled: 53395 (void/DNP 21461, stat corrections 255).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1009 (46) | 1.353 | -0.012 | — | — |  |
| assists | pf-nba-assists (challenger) | 1049 (46) | 1.340 | +0.093 | 0.897 | 79% | — |
| fga | pf-nba-fga (challenger) | 1049 (46) | 2.528 | +0.427 | 1.757 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1009 (46) | 4.981 | +0.691 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1049 (46) | 4.434 | +1.085 | 3.128 | 84% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1368 (46) | Brier 0.1246 | calib -0.035 | log loss 0.4188 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1605 (46) | Brier 0.0780 | calib -0.008 | log loss 0.2482 | — | -0.0551 [-0.0718, -0.0413] (n=1310) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1009 (46) | 4.615 | +0.330 | — | — |  |
| points | pf-nba-points (challenger) | 1049 (46) | 4.344 | +0.578 | 3.006 | 81% | — |
| pra | pf-nba-pra (challenger) | 1049 (46) | 5.688 | +0.797 | 3.947 | 78% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1009 (46) | 1.898 | +0.279 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1049 (46) | 1.810 | +0.187 | 1.236 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1009 (46) | 0.884 | -0.016 | — | — |  |
| threes | pf-nba-threes (challenger) | 1049 (46) | 0.840 | +0.013 | 0.549 | 81% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **ALERT** — bias +0.427 (95% CI +0.233..+0.593) exceeds 5% of the mean
- minutes: **ALERT** — bias +1.085 (95% CI +0.726..+1.436) exceeds 5% of the mean
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.578 (95% CI +0.325..+0.845) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1605 | 0.078 |
| incumbent | 1368 | 0.1246 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 334 | 0.003 | 0.0 | 0.003 |
| challenger | LIKELY_ACTIVE | 1217 | 0.0879 | 0.83 | 0.838 |
| challenger | LIKELY_OUT | 2 | 0.0 | 0.003 | 0.0 |
| challenger | UNCERTAIN | 52 | 0.3312 | 0.523 | 0.558 |
| incumbent | n/a | 1368 | 0.1246 | 0.702 | 0.738 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 18 | 4.142 | +0.447 |
| E_inj | 1031 | 4.439 | +1.096 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1031 | 4.45 | +1.1 |
| new_team | True | minutes | 18 | 3.522 | +0.241 |
| new_team | False | points | 1031 | 4.372 | +0.577 |
| new_team | True | points | 18 | 2.761 | +0.657 |
| reconciled | minutes | minutes | 73 | 5.102 | +1.108 |
| reconciled | minutes+usage | minutes | 25 | 3.341 | +1.726 |
| reconciled | none | minutes | 784 | 4.316 | +1.009 |
| reconciled | usage | minutes | 167 | 4.864 | +1.337 |
| reconciled | minutes | points | 73 | 4.44 | +0.495 |
| reconciled | minutes+usage | points | 25 | 3.651 | -0.167 |
| reconciled | none | points | 784 | 4.284 | +0.513 |
| reconciled | usage | points | 167 | 4.688 | +1.032 |
