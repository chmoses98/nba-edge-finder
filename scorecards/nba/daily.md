## NBA projection scorecard — last 7 days

Generated 2026-11-05T05:00:18Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 284671 across 123 games. Settled: 37069 (void/DNP 15868, stat corrections 161).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1006 (50) | 1.378 | -0.096 | — | — |  |
| assists | pf-nba-assists (challenger) | 1128 (50) | 1.311 | +0.053 | 0.881 | 80% | — |
| fga | pf-nba-fga (challenger) | 1128 (50) | 2.627 | +0.394 | 1.823 | 83% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1006 (50) | 5.201 | -0.119 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1128 (50) | 4.601 | +1.045 | 3.227 | 81% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1494 (50) | Brier 0.1114 | calib +0.021 | log loss 0.3931 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1734 (50) | Brier 0.0861 | calib +0.011 | log loss 0.2563 | — | -0.0535 [-0.0659, -0.0415] (n=1268) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1006 (50) | 4.928 | +0.059 | — | — |  |
| points | pf-nba-points (challenger) | 1128 (50) | 4.453 | +0.600 | 3.079 | 80% | — |
| pra | pf-nba-pra (challenger) | 1128 (50) | 5.770 | +0.663 | 3.996 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1006 (50) | 1.941 | +0.071 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1128 (50) | 1.758 | +0.066 | 1.204 | 82% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1006 (50) | 0.971 | -0.033 | — | — |  |
| threes | pf-nba-threes (challenger) | 1128 (50) | 0.903 | +0.008 | 0.588 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **ALERT** — bias +0.394 (95% CI +0.172..+0.611) exceeds 5% of the mean
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.600 (95% CI +0.242..+0.920) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1734 | 0.0861 |
| incumbent | 1494 | 0.1114 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 348 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1327 | 0.099 | 0.841 | 0.82 |
| challenger | LIKELY_OUT | 4 | 0.0001 | 0.006 | 0.0 |
| challenger | UNCERTAIN | 55 | 0.3278 | 0.559 | 0.727 |
| incumbent | n/a | 1494 | 0.1114 | 0.695 | 0.673 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 23 | 5.469 | -2.234 |
| E_inj | 1105 | 4.583 | +1.113 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1056 | 4.54 | +0.915 |
| new_team | True | minutes | 72 | 5.492 | +2.945 |
| new_team | False | points | 1056 | 4.456 | +0.578 |
| new_team | True | points | 72 | 4.412 | +0.925 |
| reconciled | minutes | minutes | 60 | 4.795 | -0.641 |
| reconciled | minutes+usage | minutes | 55 | 5.526 | +0.835 |
| reconciled | none | minutes | 854 | 4.591 | +1.166 |
| reconciled | usage | minutes | 159 | 4.263 | +1.105 |
| reconciled | minutes | points | 60 | 5.065 | -0.071 |
| reconciled | minutes+usage | points | 55 | 3.759 | +0.985 |
| reconciled | none | points | 854 | 4.47 | +0.565 |
| reconciled | usage | points | 159 | 4.371 | +0.906 |
