## NBA projection scorecard — last 7 days

Generated 2026-11-08T03:13:38Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 326441 across 146 games. Settled: 42027 (void/DNP 17679, stat corrections 209).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 930 (45) | 1.391 | -0.027 | — | — |  |
| assists | pf-nba-assists (challenger) | 1011 (45) | 1.335 | +0.081 | 0.892 | 81% | — |
| fga | pf-nba-fga (challenger) | 1011 (45) | 2.561 | +0.345 | 1.776 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 930 (45) | 5.393 | +0.127 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1011 (45) | 4.636 | +0.994 | 3.245 | 81% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1344 (45) | Brier 0.1135 | calib +0.002 | log loss 0.3841 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1567 (45) | Brier 0.0809 | calib +0.009 | log loss 0.2433 | — | -0.0581 [-0.0713, -0.0441] (n=1179) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 930 (45) | 4.894 | +0.250 | — | — |  |
| points | pf-nba-points (challenger) | 1011 (45) | 4.410 | +0.580 | 3.042 | 81% | — |
| pra | pf-nba-pra (challenger) | 1011 (45) | 5.653 | +0.626 | 3.943 | 78% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 930 (45) | 1.996 | +0.085 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1011 (45) | 1.825 | +0.019 | 1.250 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 930 (45) | 0.951 | +0.001 | — | — |  |
| threes | pf-nba-threes (challenger) | 1011 (45) | 0.901 | +0.031 | 0.586 | 80% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.580 (95% CI +0.264..+0.893) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1567 | 0.0809 |
| incumbent | 1344 | 0.1135 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 326 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1194 | 0.096 | 0.838 | 0.817 |
| challenger | LIKELY_OUT | 1 | 0.0 | 0.001 | 0.0 |
| challenger | UNCERTAIN | 46 | 0.2655 | 0.544 | 0.761 |
| incumbent | n/a | 1344 | 0.1135 | 0.694 | 0.692 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 25 | 5.895 | -2.943 |
| E_inj | 986 | 4.604 | +1.094 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 981 | 4.615 | +0.961 |
| new_team | True | minutes | 30 | 5.298 | +2.069 |
| new_team | False | points | 981 | 4.432 | +0.563 |
| new_team | True | points | 30 | 3.688 | +1.114 |
| reconciled | minutes | minutes | 45 | 6.242 | -0.389 |
| reconciled | minutes+usage | minutes | 40 | 6.878 | -0.57 |
| reconciled | none | minutes | 756 | 4.42 | +1.104 |
| reconciled | usage | minutes | 170 | 4.641 | +1.237 |
| reconciled | minutes | points | 45 | 4.212 | -0.058 |
| reconciled | minutes+usage | points | 40 | 4.541 | +0.068 |
| reconciled | none | points | 756 | 4.369 | +0.564 |
| reconciled | usage | points | 170 | 4.616 | +0.939 |
