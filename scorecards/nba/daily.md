## NBA projection scorecard — last 7 days

Generated 2026-11-12T00:30:48Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 389557 across 174 games. Settled: 51054 (void/DNP 20608, stat corrections 255).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1042 (48) | 1.365 | -0.004 | — | — |  |
| assists | pf-nba-assists (challenger) | 1089 (48) | 1.350 | +0.105 | 0.905 | 79% | — |
| fga | pf-nba-fga (challenger) | 1089 (48) | 2.566 | +0.343 | 1.786 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1042 (48) | 5.118 | +0.480 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1089 (48) | 4.553 | +0.956 | 3.220 | 82% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1430 (48) | Brier 0.1212 | calib -0.030 | log loss 0.4115 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1672 (48) | Brier 0.0795 | calib -0.006 | log loss 0.2507 | — | -0.0548 [-0.0696, -0.0424] (n=1337) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1042 (48) | 4.680 | +0.300 | — | — |  |
| points | pf-nba-points (challenger) | 1089 (48) | 4.350 | +0.568 | 3.014 | 81% | — |
| pra | pf-nba-pra (challenger) | 1089 (48) | 5.667 | +0.735 | 3.965 | 78% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1042 (48) | 1.911 | +0.181 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1089 (48) | 1.819 | +0.087 | 1.243 | 79% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1042 (48) | 0.890 | +0.005 | — | — |  |
| threes | pf-nba-threes (challenger) | 1089 (48) | 0.843 | +0.035 | 0.546 | 81% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.568 (95% CI +0.263..+0.851) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1672 | 0.0795 |
| incumbent | 1430 | 0.1212 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 350 | 0.0029 | 0.0 | 0.003 |
| challenger | LIKELY_ACTIVE | 1257 | 0.089 | 0.832 | 0.835 |
| challenger | LIKELY_OUT | 2 | 0.0 | 0.003 | 0.0 |
| challenger | UNCERTAIN | 63 | 0.3167 | 0.536 | 0.619 |
| incumbent | n/a | 1430 | 0.1212 | 0.698 | 0.729 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 24 | 5.245 | -2.21 |
| E_inj | 1065 | 4.537 | +1.027 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1067 | 4.563 | +0.959 |
| new_team | True | minutes | 22 | 4.061 | +0.828 |
| new_team | False | points | 1067 | 4.382 | +0.537 |
| new_team | True | points | 22 | 2.789 | +2.047 |
| reconciled | minutes | minutes | 83 | 5.406 | +0.893 |
| reconciled | minutes+usage | minutes | 36 | 5.415 | +0.447 |
| reconciled | none | minutes | 806 | 4.388 | +0.96 |
| reconciled | usage | minutes | 164 | 4.741 | +1.08 |
| reconciled | minutes | points | 83 | 4.222 | +0.443 |
| reconciled | minutes+usage | points | 36 | 3.852 | +0.075 |
| reconciled | none | points | 806 | 4.37 | +0.521 |
| reconciled | usage | points | 164 | 4.428 | +0.967 |
