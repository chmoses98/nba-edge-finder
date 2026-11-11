## NBA projection scorecard — last 7 days

Generated 2026-11-11T22:39:26Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 386996 across 174 games. Settled: 51054 (void/DNP 20608, stat corrections 255).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1148 (53) | 1.359 | +0.000 | — | — |  |
| assists | pf-nba-assists (challenger) | 1204 (53) | 1.339 | +0.108 | 0.898 | 80% | — |
| fga | pf-nba-fga (challenger) | 1204 (53) | 2.550 | +0.335 | 1.779 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1148 (53) | 5.194 | +0.559 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1204 (53) | 4.577 | +0.964 | 3.244 | 82% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1580 (53) | Brier 0.1188 | calib -0.028 | log loss 0.4041 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1847 (53) | Brier 0.0802 | calib -0.002 | log loss 0.2513 | — | -0.0534 [-0.0675, -0.0403] (n=1470) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1148 (53) | 4.694 | +0.329 | — | — |  |
| points | pf-nba-points (challenger) | 1204 (53) | 4.344 | +0.546 | 3.009 | 80% | — |
| pra | pf-nba-pra (challenger) | 1204 (53) | 5.647 | +0.680 | 3.958 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1148 (53) | 1.952 | +0.184 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1204 (53) | 1.843 | +0.074 | 1.263 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1148 (53) | 0.894 | +0.017 | — | — |  |
| threes | pf-nba-threes (challenger) | 1204 (53) | 0.850 | +0.038 | 0.549 | 81% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.546 (95% CI +0.295..+0.794) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1847 | 0.0802 |
| incumbent | 1580 | 0.1188 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 381 | 0.0026 | 0.0 | 0.003 |
| challenger | LIKELY_ACTIVE | 1399 | 0.0907 | 0.834 | 0.832 |
| challenger | LIKELY_OUT | 2 | 0.0 | 0.003 | 0.0 |
| challenger | UNCERTAIN | 65 | 0.3134 | 0.539 | 0.615 |
| incumbent | n/a | 1580 | 0.1188 | 0.699 | 0.727 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 25 | 5.277 | -2.364 |
| E_inj | 1179 | 4.562 | +1.034 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1180 | 4.586 | +0.977 |
| new_team | True | minutes | 24 | 4.147 | +0.334 |
| new_team | False | points | 1180 | 4.367 | +0.518 |
| new_team | True | points | 24 | 3.203 | +1.924 |
| reconciled | minutes | minutes | 83 | 5.406 | +0.893 |
| reconciled | minutes+usage | minutes | 45 | 5.244 | +0.003 |
| reconciled | none | minutes | 890 | 4.439 | +1.001 |
| reconciled | usage | minutes | 186 | 4.708 | +1.048 |
| reconciled | minutes | points | 83 | 4.222 | +0.443 |
| reconciled | minutes+usage | points | 45 | 3.837 | -0.163 |
| reconciled | none | points | 890 | 4.376 | +0.53 |
| reconciled | usage | points | 186 | 4.365 | +0.843 |
