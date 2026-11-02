## NBA projection scorecard — last 7 days

Generated 2026-11-02T12:07:30Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 237597 across 107 games. Settled: 28664 (void/DNP 12385, stat corrections 155).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 973 (49) | 1.423 | -0.160 | — | — |  |
| assists | pf-nba-assists (challenger) | 1105 (49) | 1.290 | +0.005 | 0.873 | 81% | — |
| fga | pf-nba-fga (challenger) | 1105 (49) | 2.749 | +0.332 | 1.906 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 973 (49) | 5.638 | -0.441 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1105 (49) | 4.757 | +0.713 | 3.339 | 80% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1458 (49) | Brier 0.1195 | calib +0.028 | log loss 0.4074 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1698 (49) | Brier 0.0893 | calib +0.026 | log loss 0.2644 | — | -0.0585 [-0.0690, -0.0493] (n=1206) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 973 (49) | 5.110 | -0.130 | — | — |  |
| points | pf-nba-points (challenger) | 1105 (49) | 4.577 | +0.564 | 3.154 | 79% | — |
| pra | pf-nba-pra (challenger) | 1105 (49) | 5.956 | +0.546 | 4.116 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 973 (49) | 2.054 | -0.057 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1105 (49) | 1.832 | -0.014 | 1.261 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 973 (49) | 0.992 | -0.054 | — | — |  |
| threes | pf-nba-threes (challenger) | 1105 (49) | 0.915 | -0.005 | 0.595 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.564 (95% CI +0.247..+0.886) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1698 | 0.0893 |
| incumbent | 1458 | 0.1195 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 314 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1328 | 0.1024 | 0.843 | 0.81 |
| challenger | LIKELY_OUT | 6 | 0.0 | 0.004 | 0.0 |
| challenger | UNCERTAIN | 50 | 0.3112 | 0.586 | 0.58 |
| incumbent | n/a | 1458 | 0.1195 | 0.696 | 0.667 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 13 | 5.396 | -3.679 |
| E_inj | 1092 | 4.749 | +0.766 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 871 | 4.681 | +0.681 |
| new_team | True | minutes | 234 | 5.039 | +0.832 |
| new_team | False | points | 871 | 4.673 | +0.67 |
| new_team | True | points | 234 | 4.221 | +0.169 |
| reconciled | minutes | minutes | 125 | 4.683 | -0.332 |
| reconciled | minutes+usage | minutes | 60 | 5.607 | +0.766 |
| reconciled | none | minutes | 802 | 4.728 | +0.826 |
| reconciled | usage | minutes | 118 | 4.597 | +1.027 |
| reconciled | minutes | points | 125 | 4.643 | +0.101 |
| reconciled | minutes+usage | points | 60 | 3.774 | +1.241 |
| reconciled | none | points | 802 | 4.559 | +0.545 |
| reconciled | usage | points | 118 | 5.039 | +0.835 |
