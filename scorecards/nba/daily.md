## NBA projection scorecard — last 7 days

Generated 2026-11-07T03:09:15Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 310414 across 139 games. Settled: 39402 (void/DNP 16659, stat corrections 185).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 905 (44) | 1.373 | -0.072 | — | — |  |
| assists | pf-nba-assists (challenger) | 990 (44) | 1.322 | +0.042 | 0.888 | 81% | — |
| fga | pf-nba-fga (challenger) | 990 (44) | 2.663 | +0.369 | 1.841 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 905 (44) | 5.474 | +0.015 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 990 (44) | 4.779 | +0.979 | 3.363 | 79% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1316 (44) | Brier 0.1145 | calib +0.007 | log loss 0.3839 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1531 (44) | Brier 0.0821 | calib +0.009 | log loss 0.2470 | — | -0.0594 [-0.0745, -0.0461] (n=1136) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 905 (44) | 4.921 | +0.165 | — | — |  |
| points | pf-nba-points (challenger) | 990 (44) | 4.476 | +0.575 | 3.086 | 81% | — |
| pra | pf-nba-pra (challenger) | 990 (44) | 5.723 | +0.587 | 3.981 | 78% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 905 (44) | 1.953 | +0.086 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 990 (44) | 1.776 | +0.030 | 1.218 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 905 (44) | 0.968 | -0.006 | — | — |  |
| threes | pf-nba-threes (challenger) | 990 (44) | 0.913 | +0.025 | 0.596 | 79% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.575 (95% CI +0.250..+0.873) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1531 | 0.0821 |
| incumbent | 1316 | 0.1145 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 319 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1158 | 0.0956 | 0.841 | 0.821 |
| challenger | LIKELY_OUT | 2 | 0.0001 | 0.006 | 0.0 |
| challenger | UNCERTAIN | 52 | 0.2886 | 0.568 | 0.75 |
| incumbent | n/a | 1316 | 0.1145 | 0.695 | 0.688 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 26 | 6.112 | -3.317 |
| E_inj | 964 | 4.743 | +1.095 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 956 | 4.727 | +0.905 |
| new_team | True | minutes | 34 | 6.252 | +3.056 |
| new_team | False | points | 956 | 4.488 | +0.561 |
| new_team | True | points | 34 | 4.132 | +0.959 |
| reconciled | minutes | minutes | 57 | 5.714 | -0.753 |
| reconciled | minutes+usage | minutes | 40 | 6.878 | -0.57 |
| reconciled | none | minutes | 733 | 4.657 | +1.139 |
| reconciled | usage | minutes | 160 | 4.479 | +1.247 |
| reconciled | minutes | points | 57 | 4.401 | -0.101 |
| reconciled | minutes+usage | points | 40 | 4.541 | +0.068 |
| reconciled | none | points | 733 | 4.486 | +0.551 |
| reconciled | usage | points | 160 | 4.444 | +1.051 |
