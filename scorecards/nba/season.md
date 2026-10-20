## NBA projection scorecard — season to date

Generated 2026-10-20T22:41:49Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 18783 across 14 games. Settled: 309 (void/DNP 151, stat corrections 0).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 18 (1) | 1.798 | +0.881 | — | — |  |
| assists | pf-nba-assists (challenger) | 22 (1) | 1.220 | -0.422 | 0.917 | 86% | — |
| fga | pf-nba-fga (challenger) | 22 (1) | 3.114 | -0.885 | 2.125 | 73% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 18 (1) | 11.329 | +11.158 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 22 (1) | 4.137 | -0.915 | 3.100 | 82% | — |
| participation | nba_sim_rotation_v1 (incumbent) | 30 (1) | 0.495 | -0.111 | 0.246 | 67% |  |
| participation | pf-nba-participation (challenger) | 35 (1) | 0.175 | +0.115 | 0.098 | 77% | -0.1905 [-0.1905, -0.1905] (n=22) |
| points | nba_sim_rotation_v1 (incumbent) | 18 (1) | 7.103 | +5.790 | — | — |  |
| points | pf-nba-points (challenger) | 22 (1) | 5.691 | -1.320 | 4.005 | 68% | — |
| pra | pf-nba-pra (challenger) | 22 (1) | 5.865 | -1.514 | 4.493 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 18 (1) | 2.838 | +2.464 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 22 (1) | 1.638 | +0.180 | 1.148 | 86% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 18 (1) | 1.045 | +0.542 | — | — |  |
| threes | pf-nba-threes (challenger) | 22 (1) | 1.011 | -0.316 | 0.728 | 77% | — |

**Drift checks**

- assists: **INSUFFICIENT** — 22 settled forecasts (< 100)
- fga: **INSUFFICIENT** — 22 settled forecasts (< 100)
- minutes: **INSUFFICIENT** — 22 settled forecasts (< 100)
- participation: **INSUFFICIENT** — 35 settled forecasts (< 100)
- points: **INSUFFICIENT** — 22 settled forecasts (< 100)
- pra: **INSUFFICIENT** — 22 settled forecasts (< 100)
- rebounds: **INSUFFICIENT** — 22 settled forecasts (< 100)
- threes: **INSUFFICIENT** — 22 settled forecasts (< 100)

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 35 | 0.0983 |
| incumbent | 30 | 0.2458 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 5 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 30 | 0.1147 | 0.867 | 0.733 |
| incumbent | n/a | 30 | 0.2458 | 0.489 | 0.6 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E_inj | 22 | 4.137 | -0.915 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 18 | 4.439 | -0.501 |
| new_team | True | minutes | 4 | 2.777 | -2.777 |
| new_team | False | points | 18 | 5.257 | -0.495 |
| new_team | True | points | 4 | 7.643 | -5.033 |
| reconciled | minutes | minutes | 11 | 3.887 | -2.258 |
| reconciled | none | minutes | 11 | 4.386 | +0.428 |
| reconciled | minutes | points | 11 | 5.999 | -1.91 |
| reconciled | none | points | 11 | 5.383 | -0.73 |
