## NBA projection scorecard — last 7 days

Generated 2026-11-14T03:16:47Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 418309 across 188 games. Settled: 56315 (void/DNP 22568, stat corrections 255).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 968 (44) | 1.319 | -0.010 | — | — |  |
| assists | pf-nba-assists (challenger) | 993 (44) | 1.317 | +0.096 | 0.882 | 79% | — |
| fga | pf-nba-fga (challenger) | 993 (44) | 2.492 | +0.330 | 1.735 | 84% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 968 (44) | 4.907 | +0.565 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 993 (44) | 4.402 | +0.811 | 3.140 | 83% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1307 (44) | Brier 0.1261 | calib -0.034 | log loss 0.4234 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1532 (44) | Brier 0.0839 | calib +0.002 | log loss 0.2664 | — | -0.0462 [-0.0607, -0.0297] (n=1274) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 968 (44) | 4.540 | +0.263 | — | — |  |
| points | pf-nba-points (challenger) | 993 (44) | 4.333 | +0.484 | 2.997 | 82% | — |
| pra | pf-nba-pra (challenger) | 993 (44) | 5.729 | +0.686 | 3.950 | 79% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 968 (44) | 1.859 | +0.283 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 993 (44) | 1.791 | +0.168 | 1.224 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 968 (44) | 0.865 | -0.033 | — | — |  |
| threes | pf-nba-threes (challenger) | 993 (44) | 0.820 | -0.012 | 0.538 | 83% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1532 | 0.0839 |
| incumbent | 1307 | 0.1261 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 312 | 0.0032 | 0.0 | 0.003 |
| challenger | LIKELY_ACTIVE | 1167 | 0.0952 | 0.83 | 0.823 |
| challenger | LIKELY_OUT | 1 | 0.0 | 0.004 | 0.0 |
| challenger | UNCERTAIN | 52 | 0.3166 | 0.562 | 0.615 |
| incumbent | n/a | 1307 | 0.1261 | 0.706 | 0.741 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 19 | 4.72 | -0.121 |
| E_inj | 974 | 4.396 | +0.83 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 977 | 4.407 | +0.807 |
| new_team | True | minutes | 16 | 4.108 | +1.057 |
| new_team | False | points | 977 | 4.353 | +0.476 |
| new_team | True | points | 16 | 3.086 | +0.973 |
| reconciled | minutes | minutes | 72 | 5.33 | +0.986 |
| reconciled | minutes+usage | minutes | 25 | 3.341 | +1.726 |
| reconciled | none | minutes | 726 | 4.316 | +0.719 |
| reconciled | usage | minutes | 170 | 4.531 | +0.999 |
| reconciled | minutes | points | 72 | 4.74 | +0.412 |
| reconciled | minutes+usage | points | 25 | 3.651 | -0.167 |
| reconciled | none | points | 726 | 4.268 | +0.404 |
| reconciled | usage | points | 170 | 4.536 | +0.951 |
