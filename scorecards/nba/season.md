## NBA projection scorecard — season to date

Generated 2026-11-01T01:37:59Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 217217 across 92 games. Settled: 26083 (void/DNP 11361, stat corrections 135).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1509 (81) | 1.550 | +0.076 | — | — |  |
| assists | pf-nba-assists (challenger) | 1889 (84) | 1.310 | +0.007 | 0.889 | 79% | — |
| fga | pf-nba-fga (challenger) | 1889 (84) | 2.771 | +0.185 | 1.934 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1509 (81) | 6.853 | +0.794 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1889 (84) | 4.994 | +0.439 | 3.522 | 78% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 2405 (81) | Brier 0.1513 | calib +0.032 | log loss 0.5046 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 2910 (84) | Brier 0.1029 | calib +0.046 | log loss 0.3069 | — | -0.0755 [-0.0885, -0.0636] (n=1888) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1509 (81) | 5.599 | +0.661 | — | — |  |
| points | pf-nba-points (challenger) | 1889 (84) | 4.569 | +0.326 | 3.168 | 79% | — |
| pra | pf-nba-pra (challenger) | 1889 (84) | 6.040 | +0.268 | 4.231 | 76% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1509 (81) | 2.220 | +0.197 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1889 (84) | 1.848 | -0.083 | 1.281 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1509 (81) | 1.001 | +0.071 | — | — |  |
| threes | pf-nba-threes (challenger) | 1889 (84) | 0.861 | +0.018 | 0.557 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.046 (95% CI +0.023..+0.066) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 2910 | 0.1029 |
| incumbent | 2405 | 0.1513 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 493 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 2324 | 0.1206 | 0.847 | 0.788 |
| challenger | LIKELY_OUT | 10 | 0.0006 | 0.015 | 0.0 |
| challenger | UNCERTAIN | 83 | 0.2311 | 0.649 | 0.687 |
| incumbent | n/a | 2405 | 0.1513 | 0.659 | 0.627 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 37 | 4.964 | -0.901 |
| E_inj | 1852 | 4.995 | +0.465 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1365 | 4.822 | +0.468 |
| new_team | True | minutes | 524 | 5.444 | +0.363 |
| new_team | False | points | 1365 | 4.663 | +0.514 |
| new_team | True | points | 524 | 4.327 | -0.164 |
| reconciled | minutes | minutes | 316 | 5.737 | -1.918 |
| reconciled | minutes+usage | minutes | 94 | 6.021 | -1.065 |
| reconciled | none | minutes | 1197 | 4.727 | +0.906 |
| reconciled | usage | minutes | 282 | 4.953 | +1.596 |
| reconciled | minutes | points | 316 | 4.85 | -0.99 |
| reconciled | minutes+usage | points | 94 | 4.184 | +0.471 |
| reconciled | none | points | 1197 | 4.467 | +0.593 |
| reconciled | usage | points | 282 | 4.817 | +0.62 |
