## NBA projection scorecard — season to date

Generated 2026-10-26T22:09:15Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 127368 across 56 games. Settled: 12908 (void/DNP 6026, stat corrections 49).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 696 (40) | 1.686 | +0.347 | — | — |  |
| assists | pf-nba-assists (challenger) | 965 (43) | 1.328 | -0.026 | 0.906 | 79% | — |
| fga | pf-nba-fga (challenger) | 965 (43) | 2.819 | -0.001 | 1.976 | 80% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 696 (40) | 8.247 | +2.346 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 965 (43) | 5.260 | +0.197 | 3.726 | 75% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1183 (40) | Brier 0.1838 | calib +0.034 | log loss 0.6028 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1490 (43) | Brier 0.1146 | calib +0.063 | log loss 0.3445 | — | -0.0946 [-0.1172, -0.0708] (n=884) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 696 (40) | 6.261 | +1.600 | — | — |  |
| points | pf-nba-points (challenger) | 965 (43) | 4.638 | +0.011 | 3.229 | 79% | — |
| pra | pf-nba-pra (challenger) | 965 (43) | 6.152 | -0.137 | 4.368 | 75% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 696 (40) | 2.403 | +0.514 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 965 (43) | 1.851 | -0.163 | 1.294 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 696 (40) | 1.045 | +0.197 | — | — |  |
| threes | pf-nba-threes (challenger) | 965 (43) | 0.839 | +0.012 | 0.547 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.063 (95% CI +0.029..+0.095) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1490 | 0.1146 |
| incumbent | 1183 | 0.1838 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 235 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1211 | 0.1359 | 0.851 | 0.771 |
| challenger | LIKELY_OUT | 5 | 0.0012 | 0.026 | 0.0 |
| challenger | UNCERTAIN | 39 | 0.1571 | 0.733 | 0.795 |
| incumbent | n/a | 1183 | 0.1838 | 0.622 | 0.588 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 26 | 4.97 | -0.04 |
| E_inj | 939 | 5.268 | +0.204 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 666 | 5.016 | +0.218 |
| new_team | True | minutes | 299 | 5.803 | +0.151 |
| new_team | False | points | 666 | 4.752 | +0.208 |
| new_team | True | points | 299 | 4.385 | -0.43 |
| reconciled | minutes | minutes | 203 | 6.268 | -2.907 |
| reconciled | minutes+usage | minutes | 48 | 6.683 | -2.298 |
| reconciled | none | minutes | 539 | 4.782 | +1.03 |
| reconciled | usage | minutes | 175 | 5.174 | +1.919 |
| reconciled | minutes | points | 203 | 4.993 | -1.619 |
| reconciled | minutes+usage | points | 48 | 4.947 | -0.382 |
| reconciled | none | points | 539 | 4.482 | +0.487 |
| reconciled | usage | points | 175 | 4.622 | +0.542 |
