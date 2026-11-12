## NBA projection scorecard — season to date

Generated 2026-11-12T16:43:43Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 393586 across 174 games. Settled: 54351 (void/DNP 21810, stat corrections 255).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 3335 (167) | 1.438 | +0.024 | — | — |  |
| assists | pf-nba-assists (challenger) | 3829 (170) | 1.314 | +0.044 | 0.886 | 79% | — |
| fga | pf-nba-fga (challenger) | 3829 (170) | 2.674 | +0.269 | 1.863 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 3335 (167) | 5.930 | +0.558 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 3829 (170) | 4.768 | +0.695 | 3.365 | 80% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 4967 (167) | Brier 0.1352 | calib +0.009 | log loss 0.4536 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 5906 (170) | Brier 0.0923 | calib +0.025 | log loss 0.2794 | — | -0.0640 [-0.0726, -0.0559] (n=4239) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 3335 (167) | 5.141 | +0.420 | — | — |  |
| points | pf-nba-points (challenger) | 3829 (170) | 4.484 | +0.426 | 3.103 | 80% | — |
| pra | pf-nba-pra (challenger) | 3829 (170) | 5.851 | +0.459 | 4.082 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 3335 (167) | 2.057 | +0.189 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 3829 (170) | 1.821 | +0.008 | 1.255 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 3335 (167) | 0.957 | +0.021 | — | — |  |
| threes | pf-nba-threes (challenger) | 3829 (170) | 0.868 | +0.013 | 0.565 | 78% | — |

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
| challenger | 5906 | 0.0923 |
| incumbent | 4967 | 0.1352 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 1113 | 0.0009 | 0.0 | 0.001 |
| challenger | LIKELY_ACTIVE | 4600 | 0.1074 | 0.841 | 0.806 |
| challenger | LIKELY_OUT | 13 | 0.0005 | 0.013 | 0.0 |
| challenger | UNCERTAIN | 180 | 0.2762 | 0.595 | 0.672 |
| incumbent | n/a | 4967 | 0.1352 | 0.68 | 0.671 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 78 | 5.194 | -1.277 |
| E_inj | 3751 | 4.759 | +0.736 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 3256 | 4.658 | +0.735 |
| new_team | True | minutes | 573 | 5.391 | +0.469 |
| new_team | False | points | 3256 | 4.524 | +0.519 |
| new_team | True | points | 573 | 4.257 | -0.103 |
| reconciled | minutes | minutes | 445 | 5.668 | -1.299 |
| reconciled | minutes+usage | minutes | 159 | 5.815 | -0.501 |
| reconciled | none | minutes | 2628 | 4.553 | +0.948 |
| reconciled | usage | minutes | 597 | 4.766 | +1.385 |
| reconciled | minutes | points | 445 | 4.775 | -0.649 |
| reconciled | minutes+usage | points | 159 | 4.19 | +0.269 |
| reconciled | none | points | 2628 | 4.412 | +0.532 |
| reconciled | usage | points | 597 | 4.664 | +0.799 |
