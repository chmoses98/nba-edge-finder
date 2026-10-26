## NBA projection scorecard — last 28 days

Generated 2026-10-26T02:08:02Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 117148 across 52 games. Settled: 12340 (void/DNP 5674, stat corrections 47).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 663 (38) | 1.708 | +0.368 | — | — |  |
| assists | pf-nba-assists (challenger) | 926 (41) | 1.336 | -0.033 | 0.913 | 79% | — |
| fga | pf-nba-fga (challenger) | 926 (41) | 2.817 | +0.034 | 1.975 | 80% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 663 (38) | 8.299 | +2.696 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 926 (41) | 5.271 | +0.231 | 3.738 | 75% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1123 (38) | Brier 0.1824 | calib +0.028 | log loss 0.5887 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1420 (41) | Brier 0.1136 | calib +0.061 | log loss 0.3424 | — | -0.0905 [-0.1154, -0.0670] (n=838) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 663 (38) | 6.314 | +1.746 | — | — |  |
| points | pf-nba-points (challenger) | 926 (41) | 4.651 | +0.012 | 3.238 | 78% | — |
| pra | pf-nba-pra (challenger) | 926 (41) | 6.164 | -0.102 | 4.374 | 75% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 663 (38) | 2.415 | +0.617 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 926 (41) | 1.848 | -0.125 | 1.288 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 663 (38) | 1.055 | +0.208 | — | — |  |
| threes | pf-nba-threes (challenger) | 926 (41) | 0.839 | +0.009 | 0.547 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **WATCH** — CRPS 110% of historical holdout
- participation: **ALERT** — bias +0.061 (95% CI +0.025..+0.097) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1420 | 0.1136 |
| incumbent | 1123 | 0.1824 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 222 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1160 | 0.1352 | 0.851 | 0.774 |
| challenger | LIKELY_OUT | 4 | 0.0009 | 0.02 | 0.0 |
| challenger | UNCERTAIN | 34 | 0.1313 | 0.756 | 0.824 |
| incumbent | n/a | 1123 | 0.1824 | 0.619 | 0.59 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 24 | 4.84 | +0.5 |
| E_inj | 902 | 5.283 | +0.224 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 643 | 5.02 | +0.265 |
| new_team | True | minutes | 283 | 5.842 | +0.153 |
| new_team | False | points | 643 | 4.743 | +0.241 |
| new_team | True | points | 283 | 4.443 | -0.507 |
| reconciled | minutes | minutes | 203 | 6.268 | -2.907 |
| reconciled | minutes+usage | minutes | 48 | 6.683 | -2.298 |
| reconciled | none | minutes | 500 | 4.765 | +1.157 |
| reconciled | usage | minutes | 175 | 5.174 | +1.919 |
| reconciled | minutes | points | 203 | 4.993 | -1.619 |
| reconciled | minutes+usage | points | 48 | 4.947 | -0.382 |
| reconciled | none | points | 500 | 4.494 | +0.527 |
| reconciled | usage | points | 175 | 4.622 | +0.542 |
