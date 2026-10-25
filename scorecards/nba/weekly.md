## NBA projection scorecard — last 28 days

Generated 2026-10-25T00:30:07Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 100772 across 43 games. Settled: 8525 (void/DNP 3957, stat corrections 33).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 453 (27) | 1.752 | +0.716 | — | — |  |
| assists | pf-nba-assists (challenger) | 642 (28) | 1.319 | +0.000 | 0.901 | 79% | — |
| fga | pf-nba-fga (challenger) | 642 (28) | 2.859 | +0.034 | 2.011 | 78% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 453 (27) | 9.184 | +4.829 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 642 (28) | 5.505 | +0.205 | 3.901 | 72% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 795 (27) | Brier 0.1931 | calib +0.017 | log loss 0.5894 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 971 (28) | Brier 0.1133 | calib +0.061 | log loss 0.3488 | — | -0.0943 [-0.1295, -0.0642] (n=569) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 453 (27) | 6.740 | +3.172 | — | — |  |
| points | pf-nba-points (challenger) | 642 (28) | 4.681 | +0.112 | 3.242 | 79% | — |
| pra | pf-nba-pra (challenger) | 642 (28) | 6.087 | +0.099 | 4.298 | 75% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 453 (27) | 2.593 | +1.068 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 642 (28) | 1.837 | -0.098 | 1.271 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 453 (27) | 1.078 | +0.398 | — | — |  |
| threes | pf-nba-threes (challenger) | 642 (28) | 0.793 | +0.069 | 0.513 | 80% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **ALERT** — CRPS 3.901 is 115% of the historical holdout (3.392)
- participation: **ALERT** — bias +0.061 (95% CI +0.017..+0.106) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 971 | 0.1133 |
| incumbent | 795 | 0.1931 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 149 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 794 | 0.1344 | 0.857 | 0.782 |
| challenger | LIKELY_OUT | 2 | 0.0001 | 0.01 | 0.0 |
| challenger | UNCERTAIN | 26 | 0.1255 | 0.791 | 0.808 |
| incumbent | n/a | 795 | 0.1931 | 0.586 | 0.57 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 20 | 5.038 | +0.685 |
| E_inj | 622 | 5.52 | +0.189 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 451 | 5.165 | +0.183 |
| new_team | True | minutes | 191 | 6.308 | +0.257 |
| new_team | False | points | 451 | 4.646 | +0.404 |
| new_team | True | points | 191 | 4.764 | -0.576 |
| reconciled | minutes | minutes | 184 | 6.391 | -2.82 |
| reconciled | minutes+usage | minutes | 28 | 6.887 | -2.74 |
| reconciled | none | minutes | 349 | 4.876 | +1.675 |
| reconciled | usage | minutes | 81 | 5.723 | +1.76 |
| reconciled | minutes | points | 184 | 5.077 | -1.625 |
| reconciled | minutes+usage | points | 28 | 4.641 | -0.771 |
| reconciled | none | points | 349 | 4.486 | +0.866 |
| reconciled | usage | points | 81 | 4.64 | +1.117 |
