## NBA projection scorecard — last 7 days

Generated 2026-11-12T02:05:30Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 390940 across 174 games. Settled: 51054 (void/DNP 20608, stat corrections 255).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 918 (42) | 1.368 | -0.007 | — | — |  |
| assists | pf-nba-assists (challenger) | 954 (42) | 1.353 | +0.091 | 0.909 | 79% | — |
| fga | pf-nba-fga (challenger) | 954 (42) | 2.559 | +0.343 | 1.778 | 83% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 918 (42) | 5.177 | +0.545 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 954 (42) | 4.592 | +0.934 | 3.229 | 83% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1250 (42) | Brier 0.1232 | calib -0.035 | log loss 0.4199 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1467 (42) | Brier 0.0768 | calib -0.004 | log loss 0.2453 | — | -0.0575 [-0.0722, -0.0442] (n=1180) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 918 (42) | 4.741 | +0.327 | — | — |  |
| points | pf-nba-points (challenger) | 954 (42) | 4.410 | +0.576 | 3.043 | 81% | — |
| pra | pf-nba-pra (challenger) | 954 (42) | 5.746 | +0.684 | 4.004 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 918 (42) | 1.916 | +0.180 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 954 (42) | 1.820 | +0.063 | 1.249 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 918 (42) | 0.899 | -0.002 | — | — |  |
| threes | pf-nba-threes (challenger) | 954 (42) | 0.855 | +0.028 | 0.555 | 82% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.576 (95% CI +0.288..+0.824) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1467 | 0.0768 |
| incumbent | 1250 | 0.1232 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 308 | 0.0032 | 0.0 | 0.003 |
| challenger | LIKELY_ACTIVE | 1108 | 0.0867 | 0.833 | 0.838 |
| challenger | LIKELY_OUT | 2 | 0.0 | 0.003 | 0.0 |
| challenger | UNCERTAIN | 49 | 0.3176 | 0.536 | 0.531 |
| incumbent | n/a | 1250 | 0.1232 | 0.7 | 0.734 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 18 | 4.983 | -1.535 |
| E_inj | 936 | 4.584 | +0.982 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 935 | 4.606 | +0.942 |
| new_team | True | minutes | 19 | 3.873 | +0.521 |
| new_team | False | points | 935 | 4.45 | +0.556 |
| new_team | True | points | 19 | 2.439 | +1.581 |
| reconciled | minutes | minutes | 83 | 5.406 | +0.893 |
| reconciled | minutes+usage | minutes | 36 | 5.415 | +0.447 |
| reconciled | none | minutes | 690 | 4.36 | +0.914 |
| reconciled | usage | minutes | 145 | 5.026 | +1.176 |
| reconciled | minutes | points | 83 | 4.222 | +0.443 |
| reconciled | minutes+usage | points | 36 | 3.852 | +0.075 |
| reconciled | none | points | 690 | 4.443 | +0.513 |
| reconciled | usage | points | 145 | 4.501 | +1.077 |
