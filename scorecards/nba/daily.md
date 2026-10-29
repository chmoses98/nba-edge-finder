## NBA projection scorecard — last 7 days

Generated 2026-10-29T23:11:25Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 179195 across 81 games. Settled: 20915 (void/DNP 9256, stat corrections 120).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1002 (51) | 1.460 | -0.145 | — | — |  |
| assists | pf-nba-assists (challenger) | 1183 (53) | 1.289 | +0.028 | 0.872 | 80% | — |
| fga | pf-nba-fga (challenger) | 1183 (53) | 2.747 | +0.187 | 1.916 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1002 (51) | 6.532 | -0.867 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1183 (53) | 4.874 | +0.461 | 3.463 | 78% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1518 (51) | Brier 0.1392 | calib +0.035 | log loss 0.4842 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1836 (53) | Brier 0.1026 | calib +0.050 | log loss 0.2988 | — | -0.0689 [-0.0833, -0.0555] (n=1242) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1002 (51) | 5.273 | -0.367 | — | — |  |
| points | pf-nba-points (challenger) | 1183 (53) | 4.556 | +0.367 | 3.154 | 80% | — |
| pra | pf-nba-pra (challenger) | 1183 (53) | 6.035 | +0.298 | 4.234 | 76% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1002 (51) | 2.170 | -0.204 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1183 (53) | 1.899 | -0.112 | 1.322 | 79% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1002 (51) | 0.953 | -0.050 | — | — |  |
| threes | pf-nba-threes (challenger) | 1183 (53) | 0.868 | -0.003 | 0.565 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.050 (95% CI +0.023..+0.075) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1836 | 0.1026 |
| incumbent | 1518 | 0.1392 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 303 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1482 | 0.1191 | 0.843 | 0.779 |
| challenger | LIKELY_OUT | 5 | 0.0012 | 0.023 | 0.0 |
| challenger | UNCERTAIN | 46 | 0.2578 | 0.582 | 0.609 |
| incumbent | n/a | 1518 | 0.1392 | 0.695 | 0.66 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 15 | 5.081 | -2.481 |
| E_inj | 1168 | 4.871 | +0.499 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 808 | 4.807 | +0.483 |
| new_team | True | minutes | 375 | 5.019 | +0.414 |
| new_team | False | points | 808 | 4.736 | +0.577 |
| new_team | True | points | 375 | 4.168 | -0.085 |
| reconciled | minutes | minutes | 167 | 5.246 | -1.61 |
| reconciled | minutes+usage | minutes | 59 | 6.287 | -1.893 |
| reconciled | none | minutes | 738 | 4.711 | +0.707 |
| reconciled | usage | minutes | 219 | 4.759 | +1.848 |
| reconciled | minutes | points | 167 | 4.695 | -0.612 |
| reconciled | minutes+usage | points | 59 | 4.844 | -0.169 |
| reconciled | none | points | 738 | 4.404 | +0.567 |
| reconciled | usage | points | 219 | 4.887 | +0.586 |
