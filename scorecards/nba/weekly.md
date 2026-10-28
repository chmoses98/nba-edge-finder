## NBA projection scorecard — last 28 days

Generated 2026-10-28T23:18:38Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 165803 across 71 games. Settled: 17196 (void/DNP 7630, stat corrections 104).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 962 (53) | 1.604 | +0.221 | — | — |  |
| assists | pf-nba-assists (challenger) | 1268 (56) | 1.301 | -0.006 | 0.885 | 79% | — |
| fga | pf-nba-fga (challenger) | 1268 (56) | 2.835 | +0.064 | 1.984 | 79% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 962 (53) | 7.785 | +1.729 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1268 (56) | 5.200 | +0.267 | 3.690 | 76% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1571 (53) | Brier 0.1696 | calib +0.028 | log loss 0.5522 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1939 (56) | Brier 0.1093 | calib +0.054 | log loss 0.3274 | — | -0.0874 [-0.1066, -0.0701] (n=1200) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 962 (53) | 5.973 | +1.152 | — | — |  |
| points | pf-nba-points (challenger) | 1268 (56) | 4.577 | +0.116 | 3.184 | 79% | — |
| pra | pf-nba-pra (challenger) | 1268 (56) | 6.128 | +0.024 | 4.318 | 76% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 962 (53) | 2.372 | +0.350 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1268 (56) | 1.874 | -0.125 | 1.306 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 962 (53) | 1.026 | +0.147 | — | — |  |
| threes | pf-nba-threes (challenger) | 1268 (56) | 0.849 | +0.015 | 0.553 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.054 (95% CI +0.026..+0.084) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1939 | 0.1093 |
| incumbent | 1571 | 0.1696 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 307 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1570 | 0.1284 | 0.85 | 0.781 |
| challenger | LIKELY_OUT | 6 | 0.001 | 0.022 | 0.0 |
| challenger | UNCERTAIN | 56 | 0.1848 | 0.675 | 0.75 |
| incumbent | n/a | 1571 | 0.1696 | 0.64 | 0.612 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 32 | 5.139 | -0.768 |
| E_inj | 1236 | 5.202 | +0.294 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 870 | 5.033 | +0.329 |
| new_team | True | minutes | 398 | 5.566 | +0.133 |
| new_team | False | points | 870 | 4.718 | +0.315 |
| new_team | True | points | 398 | 4.267 | -0.319 |
| reconciled | minutes | minutes | 252 | 6.135 | -2.457 |
| reconciled | minutes+usage | minutes | 58 | 6.574 | -2.177 |
| reconciled | none | minutes | 740 | 4.79 | +0.989 |
| reconciled | usage | minutes | 218 | 5.149 | +1.619 |
| reconciled | minutes | points | 252 | 4.916 | -1.425 |
| reconciled | minutes+usage | points | 58 | 4.719 | -0.212 |
| reconciled | none | points | 740 | 4.391 | +0.622 |
| reconciled | usage | points | 218 | 4.775 | +0.267 |
