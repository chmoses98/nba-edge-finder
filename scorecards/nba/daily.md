## NBA projection scorecard — last 7 days

Generated 2026-11-03T00:59:30Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 251643 across 107 games. Settled: 28664 (void/DNP 12385, stat corrections 155).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 833 (42) | 1.421 | -0.172 | — | — |  |
| assists | pf-nba-assists (challenger) | 947 (42) | 1.305 | -0.004 | 0.880 | 81% | — |
| fga | pf-nba-fga (challenger) | 947 (42) | 2.734 | +0.380 | 1.892 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 833 (42) | 5.427 | -0.449 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 947 (42) | 4.678 | +0.845 | 3.281 | 82% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1248 (42) | Brier 0.1175 | calib +0.029 | log loss 0.4066 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1459 (42) | Brier 0.0880 | calib +0.022 | log loss 0.2613 | — | -0.0564 [-0.0667, -0.0478] (n=1036) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 833 (42) | 5.151 | -0.128 | — | — |  |
| points | pf-nba-points (challenger) | 947 (42) | 4.662 | +0.564 | 3.202 | 80% | — |
| pra | pf-nba-pra (challenger) | 947 (42) | 5.969 | +0.584 | 4.127 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 833 (42) | 1.986 | +0.002 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 947 (42) | 1.796 | +0.046 | 1.231 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 833 (42) | 1.004 | -0.068 | — | — |  |
| threes | pf-nba-threes (challenger) | 947 (42) | 0.923 | -0.017 | 0.602 | 77% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.564 (95% CI +0.127..+0.942) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1459 | 0.088 |
| incumbent | 1248 | 0.1175 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 277 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1135 | 0.101 | 0.841 | 0.812 |
| challenger | LIKELY_OUT | 6 | 0.0 | 0.004 | 0.0 |
| challenger | UNCERTAIN | 41 | 0.3368 | 0.593 | 0.61 |
| incumbent | n/a | 1248 | 0.1175 | 0.697 | 0.667 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 10 | 5.031 | -3.407 |
| E_inj | 937 | 4.675 | +0.891 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 768 | 4.573 | +0.782 |
| new_team | True | minutes | 179 | 5.131 | +1.119 |
| new_team | False | points | 768 | 4.723 | +0.665 |
| new_team | True | points | 179 | 4.403 | +0.128 |
| reconciled | minutes | minutes | 91 | 4.523 | +0.074 |
| reconciled | minutes+usage | minutes | 50 | 5.517 | +1.239 |
| reconciled | none | minutes | 710 | 4.698 | +0.885 |
| reconciled | usage | minutes | 96 | 4.244 | +1.075 |
| reconciled | minutes | points | 91 | 4.71 | +0.248 |
| reconciled | minutes+usage | points | 50 | 3.803 | +1.369 |
| reconciled | none | points | 710 | 4.679 | +0.491 |
| reconciled | usage | points | 96 | 4.943 | +0.98 |
