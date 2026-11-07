## NBA projection scorecard — last 28 days

Generated 2026-11-07T04:08:56Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 312173 across 139 games. Settled: 41061 (void/DNP 17285, stat corrections 185).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 2459 (127) | 1.485 | +0.031 | — | — |  |
| assists | pf-nba-assists (challenger) | 2925 (130) | 1.315 | +0.023 | 0.889 | 79% | — |
| fga | pf-nba-fga (challenger) | 2925 (130) | 2.725 | +0.229 | 1.898 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 2459 (127) | 6.332 | +0.539 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 2925 (130) | 4.907 | +0.614 | 3.453 | 78% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 3781 (127) | Brier 0.1380 | calib +0.022 | log loss 0.4624 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 4510 (130) | Brier 0.0957 | calib +0.033 | log loss 0.2859 | — | -0.0690 [-0.0782, -0.0597] (n=3088) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 2459 (127) | 5.368 | +0.482 | — | — |  |
| points | pf-nba-points (challenger) | 2925 (130) | 4.554 | +0.396 | 3.149 | 80% | — |
| pra | pf-nba-pra (challenger) | 2925 (130) | 5.942 | +0.359 | 4.154 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 2459 (127) | 2.134 | +0.148 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 2925 (130) | 1.838 | -0.053 | 1.270 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 2459 (127) | 0.989 | +0.043 | — | — |  |
| threes | pf-nba-threes (challenger) | 2925 (130) | 0.882 | +0.021 | 0.573 | 77% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.033 (95% CI +0.016..+0.049) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 4510 | 0.0957 |
| incumbent | 3781 | 0.138 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 823 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 3544 | 0.1124 | 0.844 | 0.799 |
| challenger | LIKELY_OUT | 12 | 0.0005 | 0.013 | 0.0 |
| challenger | UNCERTAIN | 131 | 0.2525 | 0.621 | 0.71 |
| incumbent | n/a | 3781 | 0.138 | 0.672 | 0.65 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 62 | 5.421 | -1.825 |
| E_inj | 2863 | 4.896 | +0.667 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 2365 | 4.781 | +0.644 |
| new_team | True | minutes | 560 | 5.439 | +0.49 |
| new_team | False | points | 2365 | 4.616 | +0.516 |
| new_team | True | points | 560 | 4.291 | -0.11 |
| reconciled | minutes | minutes | 373 | 5.734 | -1.74 |
| reconciled | minutes+usage | minutes | 134 | 6.277 | -0.917 |
| reconciled | none | minutes | 1955 | 4.674 | +0.973 |
| reconciled | usage | minutes | 463 | 4.831 | +1.441 |
| reconciled | minutes | points | 373 | 4.781 | -0.854 |
| reconciled | minutes+usage | points | 134 | 4.291 | +0.351 |
| reconciled | none | points | 1955 | 4.488 | +0.552 |
| reconciled | usage | points | 463 | 4.726 | +0.762 |
