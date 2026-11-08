## NBA projection scorecard — season to date

Generated 2026-11-08T03:13:38Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 326441 across 146 games. Settled: 42027 (void/DNP 17679, stat corrections 209).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 2520 (130) | 1.485 | +0.029 | — | — |  |
| assists | pf-nba-assists (challenger) | 2992 (133) | 1.317 | +0.026 | 0.890 | 79% | — |
| fga | pf-nba-fga (challenger) | 2992 (133) | 2.721 | +0.238 | 1.894 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 2520 (130) | 6.289 | +0.551 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 2992 (133) | 4.887 | +0.638 | 3.440 | 79% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 3869 (130) | Brier 0.1371 | calib +0.021 | log loss 0.4591 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 4614 (133) | Brier 0.0951 | calib +0.032 | log loss 0.2842 | — | -0.0685 [-0.0774, -0.0591] (n=3169) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 2520 (130) | 5.355 | +0.489 | — | — |  |
| points | pf-nba-points (challenger) | 2992 (133) | 4.547 | +0.407 | 3.146 | 80% | — |
| pra | pf-nba-pra (challenger) | 2992 (133) | 5.925 | +0.383 | 4.144 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 2520 (130) | 2.127 | +0.152 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 2992 (133) | 1.835 | -0.043 | 1.267 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 2520 (130) | 0.989 | +0.041 | — | — |  |
| threes | pf-nba-threes (challenger) | 2992 (133) | 0.882 | +0.019 | 0.573 | 77% | — |

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
| challenger | 4614 | 0.0951 |
| incumbent | 3869 | 0.1371 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 842 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 3626 | 0.1117 | 0.843 | 0.799 |
| challenger | LIKELY_OUT | 12 | 0.0005 | 0.013 | 0.0 |
| challenger | UNCERTAIN | 134 | 0.2515 | 0.615 | 0.709 |
| incumbent | n/a | 3869 | 0.1371 | 0.672 | 0.651 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 64 | 5.418 | -1.913 |
| E_inj | 2928 | 4.875 | +0.693 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 2432 | 4.759 | +0.672 |
| new_team | True | minutes | 560 | 5.439 | +0.49 |
| new_team | False | points | 2432 | 4.606 | +0.526 |
| new_team | True | points | 560 | 4.291 | -0.11 |
| reconciled | minutes | minutes | 373 | 5.734 | -1.74 |
| reconciled | minutes+usage | minutes | 134 | 6.277 | -0.917 |
| reconciled | none | minutes | 2022 | 4.651 | +0.995 |
| reconciled | usage | minutes | 463 | 4.831 | +1.441 |
| reconciled | minutes | points | 373 | 4.781 | -0.854 |
| reconciled | minutes+usage | points | 134 | 4.291 | +0.351 |
| reconciled | none | points | 2022 | 4.48 | +0.561 |
| reconciled | usage | points | 463 | 4.726 | +0.762 |
