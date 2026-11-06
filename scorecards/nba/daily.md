## NBA projection scorecard — last 7 days

Generated 2026-11-06T05:02:42Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 295081 across 132 games. Settled: 38393 (void/DNP 16315, stat corrections 167).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1036 (51) | 1.374 | -0.069 | — | — |  |
| assists | pf-nba-assists (challenger) | 1151 (51) | 1.305 | +0.056 | 0.875 | 80% | — |
| fga | pf-nba-fga (challenger) | 1151 (51) | 2.657 | +0.384 | 1.838 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1036 (51) | 5.327 | -0.098 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1151 (51) | 4.688 | +0.976 | 3.280 | 80% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1524 (51) | Brier 0.1112 | calib +0.015 | log loss 0.3830 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1773 (51) | Brier 0.0854 | calib +0.012 | log loss 0.2540 | — | -0.0540 [-0.0663, -0.0425] (n=1299) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1036 (51) | 4.935 | +0.131 | — | — |  |
| points | pf-nba-points (challenger) | 1151 (51) | 4.455 | +0.624 | 3.069 | 81% | — |
| pra | pf-nba-pra (challenger) | 1151 (51) | 5.741 | +0.671 | 3.973 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1036 (51) | 1.963 | +0.075 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1151 (51) | 1.782 | +0.042 | 1.218 | 82% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1036 (51) | 0.969 | -0.020 | — | — |  |
| threes | pf-nba-threes (challenger) | 1151 (51) | 0.901 | +0.020 | 0.585 | 79% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.624 (95% CI +0.299..+0.928) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1773 | 0.0854 |
| incumbent | 1524 | 0.1112 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 355 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1361 | 0.0989 | 0.84 | 0.815 |
| challenger | LIKELY_OUT | 4 | 0.0001 | 0.006 | 0.0 |
| challenger | UNCERTAIN | 53 | 0.3167 | 0.559 | 0.792 |
| incumbent | n/a | 1524 | 0.1112 | 0.695 | 0.68 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 25 | 6.208 | -3.302 |
| E_inj | 1126 | 4.654 | +1.071 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1093 | 4.634 | +0.859 |
| new_team | True | minutes | 58 | 5.698 | +3.181 |
| new_team | False | points | 1093 | 4.472 | +0.584 |
| new_team | True | points | 58 | 4.146 | +1.364 |
| reconciled | minutes | minutes | 55 | 5.542 | -1.308 |
| reconciled | minutes+usage | minutes | 66 | 6.293 | +0.286 |
| reconciled | none | minutes | 881 | 4.578 | +1.131 |
| reconciled | usage | minutes | 149 | 4.308 | +1.21 |
| reconciled | minutes | points | 55 | 4.74 | -0.174 |
| reconciled | minutes+usage | points | 66 | 3.851 | +0.925 |
| reconciled | none | points | 881 | 4.498 | +0.598 |
| reconciled | usage | points | 149 | 4.368 | +0.938 |
