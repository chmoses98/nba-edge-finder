## NBA projection scorecard — season to date

Generated 2026-11-09T03:37:50Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 345654 across 154 games. Settled: 45609 (void/DNP 19024, stat corrections 209).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 2754 (141) | 1.482 | +0.029 | — | — |  |
| assists | pf-nba-assists (challenger) | 3235 (144) | 1.327 | +0.037 | 0.896 | 79% | — |
| fga | pf-nba-fga (challenger) | 3235 (144) | 2.704 | +0.223 | 1.884 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 2754 (141) | 6.186 | +0.543 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 3235 (144) | 4.850 | +0.644 | 3.418 | 79% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 4197 (141) | Brier 0.1346 | calib +0.019 | log loss 0.4512 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 4997 (144) | Brier 0.0930 | calib +0.030 | log loss 0.2789 | — | -0.0660 [-0.0751, -0.0575] (n=3482) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 2754 (141) | 5.295 | +0.464 | — | — |  |
| points | pf-nba-points (challenger) | 3235 (144) | 4.525 | +0.417 | 3.131 | 80% | — |
| pra | pf-nba-pra (challenger) | 3235 (144) | 5.912 | +0.405 | 4.135 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 2754 (141) | 2.109 | +0.150 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 3235 (144) | 1.836 | -0.040 | 1.270 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 2754 (141) | 0.979 | +0.039 | — | — |  |
| threes | pf-nba-threes (challenger) | 3235 (144) | 0.876 | +0.022 | 0.569 | 77% | — |

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
| challenger | 4997 | 0.093 |
| incumbent | 4197 | 0.1346 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 930 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 3910 | 0.1096 | 0.843 | 0.801 |
| challenger | LIKELY_OUT | 12 | 0.0005 | 0.013 | 0.0 |
| challenger | UNCERTAIN | 145 | 0.2502 | 0.625 | 0.71 |
| incumbent | n/a | 4197 | 0.1346 | 0.675 | 0.656 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 70 | 5.438 | -1.549 |
| E_inj | 3165 | 4.837 | +0.692 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 2671 | 4.729 | +0.674 |
| new_team | True | minutes | 564 | 5.426 | +0.501 |
| new_team | False | points | 2671 | 4.576 | +0.525 |
| new_team | True | points | 564 | 4.285 | -0.096 |
| reconciled | minutes | minutes | 395 | 5.689 | -1.615 |
| reconciled | minutes+usage | minutes | 134 | 6.277 | -0.917 |
| reconciled | none | minutes | 2218 | 4.625 | +0.981 |
| reconciled | usage | minutes | 488 | 4.806 | +1.37 |
| reconciled | minutes | points | 395 | 4.79 | -0.743 |
| reconciled | minutes+usage | points | 134 | 4.291 | +0.351 |
| reconciled | none | points | 2218 | 4.462 | +0.562 |
| reconciled | usage | points | 488 | 4.662 | +0.71 |
