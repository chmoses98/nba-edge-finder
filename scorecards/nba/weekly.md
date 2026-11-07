## NBA projection scorecard — last 28 days

Generated 2026-11-07T00:35:35Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 308655 across 139 games. Settled: 38772 (void/DNP 16396, stat corrections 185).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 2312 (120) | 1.484 | +0.029 | — | — |  |
| assists | pf-nba-assists (challenger) | 2768 (123) | 1.310 | +0.018 | 0.886 | 79% | — |
| fga | pf-nba-fga (challenger) | 2768 (123) | 2.735 | +0.227 | 1.902 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 2312 (120) | 6.368 | +0.546 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 2768 (123) | 4.908 | +0.573 | 3.460 | 78% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 3571 (120) | Brier 0.1389 | calib +0.024 | log loss 0.4646 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 4265 (123) | Brier 0.0975 | calib +0.035 | log loss 0.2908 | — | -0.0685 [-0.0781, -0.0585] (n=2896) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 2312 (120) | 5.380 | +0.499 | — | — |  |
| points | pf-nba-points (challenger) | 2768 (123) | 4.540 | +0.393 | 3.137 | 80% | — |
| pra | pf-nba-pra (challenger) | 2768 (123) | 5.917 | +0.354 | 4.134 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 2312 (120) | 2.138 | +0.156 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 2768 (123) | 1.832 | -0.051 | 1.265 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 2312 (120) | 0.993 | +0.044 | — | — |  |
| threes | pf-nba-threes (challenger) | 2768 (123) | 0.880 | +0.018 | 0.570 | 77% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.035 (95% CI +0.018..+0.053) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 4265 | 0.0975 |
| incumbent | 3571 | 0.1389 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 765 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 3362 | 0.1142 | 0.845 | 0.796 |
| challenger | LIKELY_OUT | 11 | 0.0006 | 0.014 | 0.0 |
| challenger | UNCERTAIN | 127 | 0.2493 | 0.625 | 0.732 |
| incumbent | n/a | 3571 | 0.1389 | 0.671 | 0.647 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 62 | 5.421 | -1.825 |
| E_inj | 2706 | 4.897 | +0.628 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 2214 | 4.772 | +0.599 |
| new_team | True | minutes | 554 | 5.453 | +0.469 |
| new_team | False | points | 2214 | 4.596 | +0.524 |
| new_team | True | points | 554 | 4.312 | -0.13 |
| reconciled | minutes | minutes | 373 | 5.734 | -1.74 |
| reconciled | minutes+usage | minutes | 134 | 6.277 | -0.917 |
| reconciled | none | minutes | 1840 | 4.681 | +0.952 |
| reconciled | usage | minutes | 421 | 4.734 | +1.443 |
| reconciled | minutes | points | 373 | 4.781 | -0.854 |
| reconciled | minutes+usage | points | 134 | 4.291 | +0.351 |
| reconciled | none | points | 1840 | 4.485 | +0.578 |
| reconciled | usage | points | 421 | 4.645 | +0.706 |
