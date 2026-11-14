## NBA projection scorecard — last 7 days

Generated 2026-11-14T01:33:14Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 416629 across 188 games. Settled: 55671 (void/DNP 22306, stat corrections 255).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 964 (44) | 1.328 | -0.018 | — | — |  |
| assists | pf-nba-assists (challenger) | 993 (44) | 1.327 | +0.089 | 0.889 | 79% | — |
| fga | pf-nba-fga (challenger) | 993 (44) | 2.505 | +0.360 | 1.745 | 83% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 964 (44) | 4.866 | +0.531 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 993 (44) | 4.417 | +0.866 | 3.147 | 82% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1306 (44) | Brier 0.1244 | calib -0.033 | log loss 0.4177 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1533 (44) | Brier 0.0800 | calib -0.002 | log loss 0.2542 | — | -0.0489 [-0.0633, -0.0333] (n=1269) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 964 (44) | 4.527 | +0.189 | — | — |  |
| points | pf-nba-points (challenger) | 993 (44) | 4.307 | +0.458 | 2.986 | 82% | — |
| pra | pf-nba-pra (challenger) | 993 (44) | 5.660 | +0.688 | 3.918 | 79% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 964 (44) | 1.855 | +0.302 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 993 (44) | 1.785 | +0.198 | 1.218 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 964 (44) | 0.868 | -0.043 | — | — |  |
| threes | pf-nba-threes (challenger) | 993 (44) | 0.820 | -0.017 | 0.538 | 81% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **ALERT** — bias +0.198 (95% CI +0.051..+0.345) exceeds 5% of the mean
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1533 | 0.08 |
| incumbent | 1306 | 0.1244 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 320 | 0.0031 | 0.0 | 0.003 |
| challenger | LIKELY_ACTIVE | 1160 | 0.0904 | 0.83 | 0.829 |
| challenger | LIKELY_OUT | 1 | 0.0 | 0.004 | 0.0 |
| challenger | UNCERTAIN | 52 | 0.3224 | 0.543 | 0.596 |
| incumbent | n/a | 1306 | 0.1244 | 0.705 | 0.738 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 18 | 4.418 | +0.51 |
| E_inj | 975 | 4.417 | +0.872 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 977 | 4.422 | +0.862 |
| new_team | True | minutes | 16 | 4.108 | +1.057 |
| new_team | False | points | 977 | 4.327 | +0.449 |
| new_team | True | points | 16 | 3.086 | +0.973 |
| reconciled | minutes | minutes | 72 | 5.33 | +0.986 |
| reconciled | minutes+usage | minutes | 25 | 3.341 | +1.726 |
| reconciled | none | minutes | 737 | 4.347 | +0.762 |
| reconciled | usage | minutes | 159 | 4.497 | +1.158 |
| reconciled | minutes | points | 72 | 4.74 | +0.412 |
| reconciled | minutes+usage | points | 25 | 3.651 | -0.167 |
| reconciled | none | points | 737 | 4.239 | +0.36 |
| reconciled | usage | points | 159 | 4.526 | +1.03 |
