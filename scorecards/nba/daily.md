## NBA projection scorecard — last 7 days

Generated 2026-11-08T03:55:27Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 328136 across 146 games. Settled: 42957 (void/DNP 18123, stat corrections 209).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 989 (48) | 1.400 | -0.037 | — | — |  |
| assists | pf-nba-assists (challenger) | 1074 (48) | 1.353 | +0.078 | 0.904 | 81% | — |
| fga | pf-nba-fga (challenger) | 1074 (48) | 2.548 | +0.308 | 1.772 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 989 (48) | 5.314 | +0.106 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1074 (48) | 4.596 | +0.987 | 3.223 | 82% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1433 (48) | Brier 0.1127 | calib +0.005 | log loss 0.3815 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1672 (48) | Brier 0.0803 | calib +0.010 | log loss 0.2417 | — | -0.0568 [-0.0696, -0.0444] (n=1265) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 989 (48) | 4.875 | +0.251 | — | — |  |
| points | pf-nba-points (challenger) | 1074 (48) | 4.407 | +0.598 | 3.040 | 81% | — |
| pra | pf-nba-pra (challenger) | 1074 (48) | 5.658 | +0.635 | 3.948 | 78% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 989 (48) | 1.993 | +0.066 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1074 (48) | 1.823 | -0.004 | 1.252 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 989 (48) | 0.939 | +0.004 | — | — |  |
| threes | pf-nba-threes (challenger) | 1074 (48) | 0.891 | +0.038 | 0.579 | 80% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.598 (95% CI +0.305..+0.911) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1672 | 0.0803 |
| incumbent | 1433 | 0.1127 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 355 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1267 | 0.0963 | 0.839 | 0.818 |
| challenger | LIKELY_OUT | 1 | 0.0 | 0.001 | 0.0 |
| challenger | UNCERTAIN | 49 | 0.2509 | 0.563 | 0.776 |
| incumbent | n/a | 1433 | 0.1127 | 0.695 | 0.69 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 28 | 5.76 | -2.842 |
| E_inj | 1046 | 4.565 | +1.089 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1042 | 4.574 | +0.947 |
| new_team | True | minutes | 32 | 5.317 | +2.289 |
| new_team | False | points | 1042 | 4.429 | +0.578 |
| new_team | True | points | 32 | 3.683 | +1.27 |
| reconciled | minutes | minutes | 55 | 5.767 | +0.2 |
| reconciled | minutes+usage | minutes | 40 | 6.878 | -0.57 |
| reconciled | none | minutes | 809 | 4.394 | +1.065 |
| reconciled | usage | minutes | 170 | 4.641 | +1.237 |
| reconciled | minutes | points | 55 | 4.577 | +0.562 |
| reconciled | minutes+usage | points | 40 | 4.541 | +0.068 |
| reconciled | none | points | 809 | 4.345 | +0.556 |
| reconciled | usage | points | 170 | 4.616 | +0.939 |
