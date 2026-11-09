## NBA projection scorecard — last 7 days

Generated 2026-11-09T00:40:46Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 341298 across 154 games. Settled: 44207 (void/DNP 18605, stat corrections 209).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1033 (50) | 1.401 | -0.040 | — | — |  |
| assists | pf-nba-assists (challenger) | 1119 (50) | 1.356 | +0.085 | 0.909 | 79% | — |
| fga | pf-nba-fga (challenger) | 1119 (50) | 2.540 | +0.285 | 1.769 | 83% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1033 (50) | 5.343 | +0.122 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1119 (50) | 4.641 | +0.962 | 3.265 | 81% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1495 (50) | Brier 0.1134 | calib +0.004 | log loss 0.3865 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1740 (50) | Brier 0.0808 | calib +0.009 | log loss 0.2438 | — | -0.0560 [-0.0697, -0.0426] (n=1327) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1033 (50) | 4.812 | +0.193 | — | — |  |
| points | pf-nba-points (challenger) | 1119 (50) | 4.362 | +0.595 | 3.016 | 82% | — |
| pra | pf-nba-pra (challenger) | 1119 (50) | 5.658 | +0.608 | 3.957 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1033 (50) | 1.979 | +0.049 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1119 (50) | 1.828 | -0.025 | 1.264 | 79% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1033 (50) | 0.928 | +0.003 | — | — |  |
| threes | pf-nba-threes (challenger) | 1119 (50) | 0.878 | +0.042 | 0.569 | 80% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.595 (95% CI +0.264..+0.899) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1740 | 0.0808 |
| incumbent | 1495 | 0.1134 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 368 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1320 | 0.0966 | 0.837 | 0.818 |
| challenger | LIKELY_OUT | 1 | 0.0 | 0.001 | 0.0 |
| challenger | UNCERTAIN | 51 | 0.2547 | 0.569 | 0.765 |
| incumbent | n/a | 1495 | 0.1134 | 0.695 | 0.691 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 28 | 5.76 | -2.842 |
| E_inj | 1091 | 4.612 | +1.059 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1087 | 4.629 | +0.936 |
| new_team | True | minutes | 32 | 5.053 | +1.845 |
| new_team | False | points | 1087 | 4.381 | +0.574 |
| new_team | True | points | 32 | 3.714 | +1.301 |
| reconciled | minutes | minutes | 67 | 5.809 | -0.094 |
| reconciled | minutes+usage | minutes | 40 | 6.878 | -0.57 |
| reconciled | none | minutes | 832 | 4.421 | +1.119 |
| reconciled | usage | minutes | 180 | 4.726 | +0.969 |
| reconciled | minutes | points | 67 | 4.452 | +0.337 |
| reconciled | minutes+usage | points | 40 | 4.541 | +0.068 |
| reconciled | none | points | 832 | 4.299 | +0.58 |
| reconciled | usage | points | 180 | 4.58 | +0.875 |
