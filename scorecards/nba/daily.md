## NBA projection scorecard — last 7 days

Generated 2026-10-31T22:09:41Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 212764 across 92 games. Settled: 25450 (void/DNP 11074, stat corrections 135).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 998 (51) | 1.466 | -0.197 | — | — |  |
| assists | pf-nba-assists (challenger) | 1183 (53) | 1.300 | +0.007 | 0.880 | 81% | — |
| fga | pf-nba-fga (challenger) | 1183 (53) | 2.715 | +0.218 | 1.889 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 998 (51) | 5.868 | -0.901 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1183 (53) | 4.684 | +0.539 | 3.295 | 80% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1520 (51) | Brier 0.1311 | calib +0.039 | log loss 0.4674 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1835 (53) | Brier 0.0979 | calib +0.038 | log loss 0.2865 | — | -0.0675 [-0.0810, -0.0552] (n=1246) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 998 (51) | 5.113 | -0.391 | — | — |  |
| points | pf-nba-points (challenger) | 1183 (53) | 4.483 | +0.409 | 3.117 | 81% | — |
| pra | pf-nba-pra (challenger) | 1183 (53) | 5.972 | +0.315 | 4.169 | 78% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 998 (51) | 2.082 | -0.200 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1183 (53) | 1.859 | -0.092 | 1.293 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 998 (51) | 0.966 | -0.074 | — | — |  |
| threes | pf-nba-threes (challenger) | 1183 (53) | 0.895 | -0.020 | 0.580 | 80% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.038 (95% CI +0.013..+0.062) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1835 | 0.0979 |
| incumbent | 1520 | 0.1311 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 321 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1453 | 0.1135 | 0.841 | 0.791 |
| challenger | LIKELY_OUT | 8 | 0.0008 | 0.016 | 0.0 |
| challenger | UNCERTAIN | 53 | 0.2792 | 0.589 | 0.623 |
| incumbent | n/a | 1520 | 0.1311 | 0.695 | 0.657 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 16 | 4.777 | -2.536 |
| E_inj | 1167 | 4.683 | +0.581 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 861 | 4.632 | +0.564 |
| new_team | True | minutes | 322 | 4.825 | +0.473 |
| new_team | False | points | 861 | 4.66 | +0.54 |
| new_team | True | points | 322 | 4.011 | +0.059 |
| reconciled | minutes | minutes | 132 | 4.826 | -0.662 |
| reconciled | minutes+usage | minutes | 56 | 5.075 | +0.023 |
| reconciled | none | minutes | 804 | 4.643 | +0.547 |
| reconciled | usage | minutes | 191 | 4.647 | +1.49 |
| reconciled | minutes | points | 132 | 4.534 | -0.105 |
| reconciled | minutes+usage | points | 56 | 3.443 | +1.251 |
| reconciled | none | points | 804 | 4.457 | +0.448 |
| reconciled | usage | points | 191 | 4.864 | +0.351 |
