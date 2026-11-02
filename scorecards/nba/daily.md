## NBA projection scorecard — last 7 days

Generated 2026-11-02T23:25:09Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 248435 across 107 games. Settled: 28664 (void/DNP 12385, stat corrections 155).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 935 (47) | 1.423 | -0.166 | — | — |  |
| assists | pf-nba-assists (challenger) | 1065 (47) | 1.296 | +0.001 | 0.876 | 80% | — |
| fga | pf-nba-fga (challenger) | 1065 (47) | 2.720 | +0.373 | 1.885 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 935 (47) | 5.549 | -0.341 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1065 (47) | 4.709 | +0.822 | 3.304 | 81% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1398 (47) | Brier 0.1195 | calib +0.027 | log loss 0.4086 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1633 (47) | Brier 0.0883 | calib +0.021 | log loss 0.2620 | — | -0.0589 [-0.0697, -0.0493] (n=1158) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 935 (47) | 5.096 | -0.108 | — | — |  |
| points | pf-nba-points (challenger) | 1065 (47) | 4.573 | +0.583 | 3.144 | 81% | — |
| pra | pf-nba-pra (challenger) | 1065 (47) | 5.937 | +0.588 | 4.102 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 935 (47) | 2.033 | -0.021 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1065 (47) | 1.822 | +0.013 | 1.249 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 935 (47) | 0.995 | -0.057 | — | — |  |
| threes | pf-nba-threes (challenger) | 1065 (47) | 0.911 | -0.005 | 0.592 | 80% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.583 (95% CI +0.235..+0.960) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1633 | 0.0883 |
| incumbent | 1398 | 0.1195 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 306 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1272 | 0.1013 | 0.842 | 0.814 |
| challenger | LIKELY_OUT | 6 | 0.0 | 0.004 | 0.0 |
| challenger | UNCERTAIN | 49 | 0.3128 | 0.589 | 0.592 |
| incumbent | n/a | 1398 | 0.1195 | 0.696 | 0.669 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 13 | 5.396 | -3.679 |
| E_inj | 1052 | 4.701 | +0.877 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 844 | 4.644 | +0.765 |
| new_team | True | minutes | 221 | 4.957 | +1.037 |
| new_team | False | points | 844 | 4.681 | +0.7 |
| new_team | True | points | 221 | 4.163 | +0.139 |
| reconciled | minutes | minutes | 115 | 4.473 | +0.043 |
| reconciled | minutes+usage | minutes | 50 | 5.517 | +1.239 |
| reconciled | none | minutes | 793 | 4.716 | +0.89 |
| reconciled | usage | minutes | 107 | 4.531 | +0.958 |
| reconciled | minutes | points | 115 | 4.572 | +0.224 |
| reconciled | minutes+usage | points | 50 | 3.803 | +1.369 |
| reconciled | none | points | 793 | 4.571 | +0.554 |
| reconciled | usage | points | 107 | 4.95 | +0.816 |
