## NBA projection scorecard — last 7 days

Generated 2026-10-31T02:53:48Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 203405 across 88 games. Settled: 24463 (void/DNP 10673, stat corrections 120).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 954 (49) | 1.473 | -0.216 | — | — |  |
| assists | pf-nba-assists (challenger) | 1135 (51) | 1.299 | -0.007 | 0.881 | 80% | — |
| fga | pf-nba-fga (challenger) | 1135 (51) | 2.707 | +0.193 | 1.886 | 83% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 954 (49) | 5.966 | -1.018 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1135 (51) | 4.728 | +0.423 | 3.331 | 80% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1460 (49) | Brier 0.1327 | calib +0.042 | log loss 0.4736 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1763 (51) | Brier 0.0989 | calib +0.042 | log loss 0.2888 | — | -0.0687 [-0.0831, -0.0563] (n=1197) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 954 (49) | 5.152 | -0.516 | — | — |  |
| points | pf-nba-points (challenger) | 1135 (51) | 4.500 | +0.349 | 3.123 | 80% | — |
| pra | pf-nba-pra (challenger) | 1135 (51) | 5.990 | +0.205 | 4.184 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 954 (49) | 2.103 | -0.228 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1135 (51) | 1.874 | -0.115 | 1.302 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 954 (49) | 0.965 | -0.072 | — | — |  |
| threes | pf-nba-threes (challenger) | 1135 (51) | 0.893 | -0.011 | 0.577 | 80% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.042 (95% CI +0.017..+0.068) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1763 | 0.0989 |
| incumbent | 1460 | 0.1327 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 307 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1400 | 0.1152 | 0.842 | 0.79 |
| challenger | LIKELY_OUT | 7 | 0.0009 | 0.018 | 0.0 |
| challenger | UNCERTAIN | 49 | 0.2666 | 0.605 | 0.592 |
| incumbent | n/a | 1460 | 0.1327 | 0.696 | 0.653 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 15 | 4.977 | -2.586 |
| E_inj | 1120 | 4.725 | +0.463 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 811 | 4.671 | +0.489 |
| new_team | True | minutes | 324 | 4.87 | +0.257 |
| new_team | False | points | 811 | 4.697 | +0.504 |
| new_team | True | points | 324 | 4.007 | -0.04 |
| reconciled | minutes | minutes | 120 | 4.919 | -0.8 |
| reconciled | minutes+usage | minutes | 66 | 5.654 | -0.354 |
| reconciled | none | minutes | 758 | 4.637 | +0.415 |
| reconciled | usage | minutes | 191 | 4.647 | +1.49 |
| reconciled | minutes | points | 120 | 4.476 | -0.144 |
| reconciled | minutes+usage | points | 66 | 3.991 | +0.998 |
| reconciled | none | points | 758 | 4.457 | +0.37 |
| reconciled | usage | points | 191 | 4.864 | +0.351 |
