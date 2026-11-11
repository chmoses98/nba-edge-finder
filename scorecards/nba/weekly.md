## NBA projection scorecard — last 28 days

Generated 2026-11-11T19:36:25Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 383676 across 173 games. Settled: 51054 (void/DNP 20608, stat corrections 255).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 3117 (157) | 1.448 | +0.022 | — | — |  |
| assists | pf-nba-assists (challenger) | 3606 (160) | 1.317 | +0.038 | 0.889 | 79% | — |
| fga | pf-nba-fga (challenger) | 3606 (160) | 2.685 | +0.253 | 1.870 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 3117 (157) | 6.016 | +0.550 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 3606 (160) | 4.805 | +0.676 | 3.389 | 79% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 4671 (157) | Brier 0.1355 | calib +0.011 | log loss 0.4557 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 5556 (160) | Brier 0.0926 | calib +0.026 | log loss 0.2802 | — | -0.0656 [-0.0740, -0.0568] (n=3944) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 3117 (157) | 5.196 | +0.436 | — | — |  |
| points | pf-nba-points (challenger) | 3606 (160) | 4.495 | +0.423 | 3.110 | 80% | — |
| pra | pf-nba-pra (challenger) | 3606 (160) | 5.867 | +0.429 | 4.100 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 3117 (157) | 2.073 | +0.169 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 3606 (160) | 1.824 | -0.017 | 1.259 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 3117 (157) | 0.966 | +0.029 | — | — |  |
| threes | pf-nba-threes (challenger) | 3606 (160) | 0.871 | +0.017 | 0.566 | 78% | — |

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
| challenger | 5556 | 0.0926 |
| incumbent | 4671 | 0.1355 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 1041 | 0.001 | 0.0 | 0.001 |
| challenger | LIKELY_ACTIVE | 4332 | 0.1077 | 0.842 | 0.806 |
| challenger | LIKELY_OUT | 13 | 0.0005 | 0.013 | 0.0 |
| challenger | UNCERTAIN | 170 | 0.2741 | 0.596 | 0.665 |
| incumbent | n/a | 4671 | 0.1355 | 0.678 | 0.667 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 75 | 5.2 | -1.4 |
| E_inj | 3531 | 4.796 | +0.72 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 3036 | 4.691 | +0.716 |
| new_team | True | minutes | 570 | 5.408 | +0.463 |
| new_team | False | points | 3036 | 4.539 | +0.519 |
| new_team | True | points | 570 | 4.26 | -0.086 |
| reconciled | minutes | minutes | 432 | 5.656 | -1.403 |
| reconciled | minutes+usage | minutes | 159 | 5.815 | -0.501 |
| reconciled | none | minutes | 2449 | 4.588 | +0.958 |
| reconciled | usage | minutes | 566 | 4.809 | +1.374 |
| reconciled | minutes | points | 432 | 4.759 | -0.67 |
| reconciled | minutes+usage | points | 159 | 4.19 | +0.269 |
| reconciled | none | points | 2449 | 4.442 | +0.539 |
| reconciled | usage | points | 566 | 4.608 | +0.801 |
