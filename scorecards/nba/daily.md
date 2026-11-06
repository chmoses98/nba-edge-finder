## NBA projection scorecard — last 7 days

Generated 2026-11-06T01:46:11Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 290954 across 132 games. Settled: 38034 (void/DNP 16257, stat corrections 167).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1034 (51) | 1.366 | -0.062 | — | — |  |
| assists | pf-nba-assists (challenger) | 1154 (51) | 1.302 | +0.068 | 0.873 | 80% | — |
| fga | pf-nba-fga (challenger) | 1154 (51) | 2.633 | +0.381 | 1.827 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1034 (51) | 5.313 | -0.079 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1154 (51) | 4.679 | +0.995 | 3.277 | 81% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1524 (51) | Brier 0.1111 | calib +0.017 | log loss 0.3852 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1774 (51) | Brier 0.0857 | calib +0.012 | log loss 0.2550 | — | -0.0539 [-0.0643, -0.0420] (n=1296) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1034 (51) | 4.927 | +0.145 | — | — |  |
| points | pf-nba-points (challenger) | 1154 (51) | 4.445 | +0.651 | 3.068 | 80% | — |
| pra | pf-nba-pra (challenger) | 1154 (51) | 5.749 | +0.709 | 3.976 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1034 (51) | 1.956 | +0.061 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1154 (51) | 1.774 | +0.038 | 1.213 | 82% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1034 (51) | 0.972 | -0.015 | — | — |  |
| threes | pf-nba-threes (challenger) | 1154 (51) | 0.902 | +0.025 | 0.586 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.651 (95% CI +0.333..+0.959) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1774 | 0.0857 |
| incumbent | 1524 | 0.1111 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 353 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1364 | 0.0992 | 0.839 | 0.815 |
| challenger | LIKELY_OUT | 4 | 0.0001 | 0.006 | 0.0 |
| challenger | UNCERTAIN | 53 | 0.3167 | 0.559 | 0.792 |
| incumbent | n/a | 1524 | 0.1111 | 0.695 | 0.678 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 25 | 6.208 | -3.302 |
| E_inj | 1129 | 4.645 | +1.09 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1086 | 4.632 | +0.865 |
| new_team | True | minutes | 68 | 5.431 | +3.079 |
| new_team | False | points | 1086 | 4.459 | +0.616 |
| new_team | True | points | 68 | 4.226 | +1.221 |
| reconciled | minutes | minutes | 70 | 5.2 | -0.646 |
| reconciled | minutes+usage | minutes | 66 | 6.293 | +0.286 |
| reconciled | none | minutes | 869 | 4.578 | +1.144 |
| reconciled | usage | minutes | 149 | 4.308 | +1.21 |
| reconciled | minutes | points | 70 | 4.717 | -0.052 |
| reconciled | minutes+usage | points | 66 | 3.851 | +0.925 |
| reconciled | none | points | 869 | 4.482 | +0.638 |
| reconciled | usage | points | 149 | 4.368 | +0.938 |
