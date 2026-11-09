## NBA projection scorecard — last 7 days

Generated 2026-11-09T19:41:09Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 351470 across 156 games. Settled: 46282 (void/DNP 19258, stat corrections 235).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1129 (54) | 1.395 | -0.008 | — | — |  |
| assists | pf-nba-assists (challenger) | 1211 (54) | 1.355 | +0.112 | 0.904 | 80% | — |
| fga | pf-nba-fga (challenger) | 1211 (54) | 2.576 | +0.355 | 1.791 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1129 (54) | 5.316 | +0.287 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1211 (54) | 4.590 | +0.978 | 3.229 | 81% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1616 (54) | Brier 0.1129 | calib -0.004 | log loss 0.3799 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1880 (54) | Brier 0.0798 | calib +0.008 | log loss 0.2408 | — | -0.0548 [-0.0672, -0.0423] (n=1447) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1129 (54) | 4.816 | +0.254 | — | — |  |
| points | pf-nba-points (challenger) | 1211 (54) | 4.375 | +0.626 | 3.018 | 81% | — |
| pra | pf-nba-pra (challenger) | 1211 (54) | 5.666 | +0.733 | 3.950 | 78% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1129 (54) | 1.957 | +0.113 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1211 (54) | 1.822 | +0.048 | 1.251 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1129 (54) | 0.918 | +0.021 | — | — |  |
| threes | pf-nba-threes (challenger) | 1211 (54) | 0.868 | +0.058 | 0.561 | 80% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.626 (95% CI +0.358..+0.906) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1880 | 0.0798 |
| incumbent | 1616 | 0.1129 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 395 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1427 | 0.0947 | 0.835 | 0.818 |
| challenger | LIKELY_OUT | 1 | 0.0 | 0.001 | 0.0 |
| challenger | UNCERTAIN | 57 | 0.2607 | 0.583 | 0.772 |
| incumbent | n/a | 1616 | 0.1129 | 0.695 | 0.699 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 32 | 5.672 | -1.866 |
| E_inj | 1179 | 4.561 | +1.056 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1179 | 4.589 | +0.967 |
| new_team | True | minutes | 32 | 4.635 | +1.396 |
| new_team | False | points | 1179 | 4.39 | +0.611 |
| new_team | True | points | 32 | 3.803 | +1.198 |
| reconciled | minutes | minutes | 67 | 5.809 | -0.094 |
| reconciled | minutes+usage | minutes | 39 | 6.178 | -0.847 |
| reconciled | none | minutes | 899 | 4.411 | +1.078 |
| reconciled | usage | minutes | 206 | 4.677 | +1.238 |
| reconciled | minutes | points | 67 | 4.452 | +0.337 |
| reconciled | minutes+usage | points | 39 | 4.199 | -0.605 |
| reconciled | none | points | 899 | 4.362 | +0.633 |
| reconciled | usage | points | 206 | 4.437 | +0.923 |
