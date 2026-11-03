## NBA projection scorecard — last 7 days

Generated 2026-11-03T23:38:45Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 262638 across 121 games. Settled: 33459 (void/DNP 14458, stat corrections 161).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1069 (54) | 1.400 | -0.148 | — | — |  |
| assists | pf-nba-assists (challenger) | 1206 (54) | 1.311 | +0.019 | 0.883 | 81% | — |
| fga | pf-nba-fga (challenger) | 1206 (54) | 2.663 | +0.389 | 1.838 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1069 (54) | 5.263 | -0.527 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1206 (54) | 4.533 | +0.876 | 3.160 | 82% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1608 (54) | Brier 0.1168 | calib +0.031 | log loss 0.4050 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1874 (54) | Brier 0.0872 | calib +0.021 | log loss 0.2587 | — | -0.0584 [-0.0709, -0.0474] (n=1344) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1069 (54) | 5.035 | -0.144 | — | — |  |
| points | pf-nba-points (challenger) | 1206 (54) | 4.528 | +0.610 | 3.111 | 81% | — |
| pra | pf-nba-pra (challenger) | 1206 (54) | 5.768 | +0.628 | 3.976 | 78% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1069 (54) | 1.929 | -0.007 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1206 (54) | 1.740 | +0.037 | 1.194 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1069 (54) | 0.995 | -0.073 | — | — |  |
| threes | pf-nba-threes (challenger) | 1206 (54) | 0.916 | -0.005 | 0.596 | 79% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **ALERT** — bias +0.389 (95% CI +0.203..+0.608) exceeds 5% of the mean
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.610 (95% CI +0.311..+0.958) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1874 | 0.0872 |
| incumbent | 1608 | 0.1168 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 369 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1446 | 0.1006 | 0.84 | 0.81 |
| challenger | LIKELY_OUT | 5 | 0.0 | 0.005 | 0.0 |
| challenger | UNCERTAIN | 54 | 0.3311 | 0.572 | 0.648 |
| incumbent | n/a | 1608 | 0.1168 | 0.695 | 0.665 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 18 | 5.203 | -1.183 |
| E_inj | 1188 | 4.523 | +0.908 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1037 | 4.469 | +0.78 |
| new_team | True | minutes | 169 | 4.927 | +1.467 |
| new_team | False | points | 1037 | 4.564 | +0.648 |
| new_team | True | points | 169 | 4.307 | +0.374 |
| reconciled | minutes | minutes | 97 | 4.627 | -0.627 |
| reconciled | minutes+usage | minutes | 56 | 5.489 | +0.829 |
| reconciled | none | minutes | 881 | 4.494 | +0.94 |
| reconciled | usage | minutes | 172 | 4.372 | +1.414 |
| reconciled | minutes | points | 97 | 4.814 | +0.338 |
| reconciled | minutes+usage | points | 56 | 3.926 | +1.115 |
| reconciled | none | points | 881 | 4.511 | +0.483 |
| reconciled | usage | points | 172 | 4.647 | +1.25 |
