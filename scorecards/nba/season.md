## NBA projection scorecard — season to date

Generated 2026-10-22T00:14:25Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 41063 across 16 games. Settled: 924 (void/DNP 440, stat corrections 0).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 51 (3) | 1.975 | +1.398 | — | — |  |
| assists | pf-nba-assists (challenger) | 68 (3) | 1.276 | -0.061 | 0.881 | 78% | — |
| fga | pf-nba-fga (challenger) | 68 (3) | 2.848 | -0.905 | 2.035 | 71% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 51 (3) | 10.107 | +9.953 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 68 (3) | 5.391 | -0.876 | 3.620 | 75% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 90 (3) | Brier 0.2454 | calib -0.078 | log loss 0.6839 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 103 (3) | Brier 0.1154 | calib +0.089 | log loss 0.3444 | — | -0.1813 [-0.2288, -0.1331] (n=63) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 51 (3) | 7.648 | +6.661 | — | — |  |
| points | pf-nba-points (challenger) | 68 (3) | 4.349 | -0.461 | 3.051 | 79% | — |
| pra | pf-nba-pra (challenger) | 68 (3) | 5.502 | -0.571 | 3.905 | 79% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 51 (3) | 2.660 | +2.131 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 68 (3) | 1.882 | -0.227 | 1.273 | 78% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 51 (3) | 1.274 | +0.710 | — | — |  |
| threes | pf-nba-threes (challenger) | 68 (3) | 0.907 | -0.115 | 0.609 | 76% | — |

**Drift checks**

- assists: **INSUFFICIENT** — 68 settled forecasts (< 100)
- fga: **INSUFFICIENT** — 68 settled forecasts (< 100)
- minutes: **INSUFFICIENT** — 68 settled forecasts (< 100)
- participation: **OK** — within expectations
- points: **INSUFFICIENT** — 68 settled forecasts (< 100)
- pra: **INSUFFICIENT** — 68 settled forecasts (< 100)
- rebounds: **INSUFFICIENT** — 68 settled forecasts (< 100)
- threes: **INSUFFICIENT** — 68 settled forecasts (< 100)

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 103 | 0.1154 |
| incumbent | 90 | 0.2454 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 14 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 85 | 0.1382 | 0.867 | 0.753 |
| challenger | UNCERTAIN | 4 | 0.0343 | 0.863 | 1.0 |
| incumbent | n/a | 90 | 0.2454 | 0.489 | 0.567 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 4 | 4.142 | -2.667 |
| E_inj | 64 | 5.469 | -0.765 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 54 | 5.239 | -1.029 |
| new_team | True | minutes | 14 | 5.977 | -0.289 |
| new_team | False | points | 54 | 4.292 | -0.102 |
| new_team | True | points | 14 | 4.565 | -1.842 |
| reconciled | minutes | minutes | 35 | 5.7 | -1.214 |
| reconciled | minutes+usage | minutes | 9 | 6.093 | -3.34 |
| reconciled | none | minutes | 24 | 4.677 | +0.539 |
| reconciled | minutes | points | 35 | 4.316 | -0.516 |
| reconciled | minutes+usage | points | 9 | 3.887 | -0.456 |
| reconciled | none | points | 24 | 4.569 | -0.381 |
