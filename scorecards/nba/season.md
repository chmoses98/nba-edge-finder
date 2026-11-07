## NBA projection scorecard — season to date

Generated 2026-11-07T12:15:45Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 313427 across 139 games. Settled: 41685 (void/DNP 17569, stat corrections 185).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 2498 (129) | 1.485 | +0.029 | — | — |  |
| assists | pf-nba-assists (challenger) | 2968 (132) | 1.316 | +0.024 | 0.890 | 79% | — |
| fga | pf-nba-fga (challenger) | 2968 (132) | 2.724 | +0.236 | 1.896 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 2498 (129) | 6.301 | +0.531 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 2968 (132) | 4.894 | +0.620 | 3.444 | 79% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 3839 (129) | Brier 0.1375 | calib +0.021 | log loss 0.4603 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 4580 (132) | Brier 0.0953 | calib +0.032 | log loss 0.2847 | — | -0.0687 [-0.0781, -0.0588] (n=3142) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 2498 (129) | 5.356 | +0.469 | — | — |  |
| points | pf-nba-points (challenger) | 2968 (132) | 4.545 | +0.393 | 3.144 | 80% | — |
| pra | pf-nba-pra (challenger) | 2968 (132) | 5.924 | +0.366 | 4.143 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 2498 (129) | 2.130 | +0.154 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 2968 (132) | 1.836 | -0.044 | 1.268 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 2498 (129) | 0.989 | +0.039 | — | — |  |
| threes | pf-nba-threes (challenger) | 2968 (132) | 0.882 | +0.018 | 0.573 | 77% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.032 (95% CI +0.017..+0.050) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 4580 | 0.0953 |
| incumbent | 3839 | 0.1375 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 838 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 3597 | 0.112 | 0.844 | 0.799 |
| challenger | LIKELY_OUT | 12 | 0.0005 | 0.013 | 0.0 |
| challenger | UNCERTAIN | 133 | 0.2519 | 0.616 | 0.707 |
| incumbent | n/a | 3839 | 0.1375 | 0.672 | 0.651 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 63 | 5.345 | -1.785 |
| E_inj | 2905 | 4.884 | +0.672 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 2408 | 4.767 | +0.651 |
| new_team | True | minutes | 560 | 5.439 | +0.49 |
| new_team | False | points | 2408 | 4.604 | +0.51 |
| new_team | True | points | 560 | 4.291 | -0.11 |
| reconciled | minutes | minutes | 373 | 5.734 | -1.74 |
| reconciled | minutes+usage | minutes | 134 | 6.277 | -0.917 |
| reconciled | none | minutes | 1998 | 4.659 | +0.974 |
| reconciled | usage | minutes | 463 | 4.831 | +1.441 |
| reconciled | minutes | points | 373 | 4.781 | -0.854 |
| reconciled | minutes+usage | points | 134 | 4.291 | +0.351 |
| reconciled | none | points | 1998 | 4.476 | +0.544 |
| reconciled | usage | points | 463 | 4.726 | +0.762 |
