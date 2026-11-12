## NBA projection scorecard — season to date

Generated 2026-11-12T04:07:36Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 391903 across 174 games. Settled: 53395 (void/DNP 21461, stat corrections 255).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 3272 (164) | 1.441 | +0.021 | — | — |  |
| assists | pf-nba-assists (challenger) | 3765 (167) | 1.315 | +0.040 | 0.887 | 79% | — |
| fga | pf-nba-fga (challenger) | 3765 (167) | 2.676 | +0.274 | 1.864 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 3272 (164) | 5.958 | +0.574 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 3765 (167) | 4.780 | +0.702 | 3.372 | 80% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 4879 (164) | Brier 0.1352 | calib +0.009 | log loss 0.4532 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 5801 (167) | Brier 0.0927 | calib +0.025 | log loss 0.2805 | — | -0.0642 [-0.0730, -0.0556] (n=4151) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 3272 (164) | 5.155 | +0.439 | — | — |  |
| points | pf-nba-points (challenger) | 3765 (167) | 4.485 | +0.435 | 3.104 | 80% | — |
| pra | pf-nba-pra (challenger) | 3765 (167) | 5.856 | +0.465 | 4.086 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 3272 (164) | 2.066 | +0.188 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 3765 (167) | 1.825 | +0.010 | 1.258 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 3272 (164) | 0.959 | +0.027 | — | — |  |
| threes | pf-nba-threes (challenger) | 3765 (167) | 0.868 | +0.017 | 0.564 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 5801 | 0.0927 |
| incumbent | 4879 | 0.1352 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 1084 | 0.0009 | 0.0 | 0.001 |
| challenger | LIKELY_ACTIVE | 4527 | 0.1078 | 0.841 | 0.805 |
| challenger | LIKELY_OUT | 13 | 0.0005 | 0.013 | 0.0 |
| challenger | UNCERTAIN | 177 | 0.2742 | 0.595 | 0.678 |
| incumbent | n/a | 4879 | 0.1352 | 0.679 | 0.671 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 78 | 5.194 | -1.277 |
| E_inj | 3687 | 4.771 | +0.744 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 3193 | 4.67 | +0.745 |
| new_team | True | minutes | 572 | 5.392 | +0.462 |
| new_team | False | points | 3193 | 4.524 | +0.532 |
| new_team | True | points | 572 | 4.263 | -0.105 |
| reconciled | minutes | minutes | 432 | 5.656 | -1.403 |
| reconciled | minutes+usage | minutes | 159 | 5.815 | -0.501 |
| reconciled | none | minutes | 2586 | 4.572 | +0.966 |
| reconciled | usage | minutes | 588 | 4.771 | +1.413 |
| reconciled | minutes | points | 432 | 4.759 | -0.67 |
| reconciled | minutes+usage | points | 159 | 4.19 | +0.269 |
| reconciled | none | points | 2586 | 4.418 | +0.548 |
| reconciled | usage | points | 588 | 4.657 | +0.799 |
