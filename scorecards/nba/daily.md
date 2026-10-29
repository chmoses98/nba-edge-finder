## NBA projection scorecard — last 7 days

Generated 2026-10-29T02:03:35Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 168604 across 71 games. Settled: 18373 (void/DNP 8249, stat corrections 104).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 854 (44) | 1.484 | -0.140 | — | — |  |
| assists | pf-nba-assists (challenger) | 1049 (47) | 1.307 | +0.037 | 0.883 | 82% | — |
| fga | pf-nba-fga (challenger) | 1049 (47) | 2.796 | +0.218 | 1.948 | 80% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 854 (44) | 6.792 | -0.639 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1049 (47) | 4.952 | +0.534 | 3.528 | 78% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1307 (44) | Brier 0.1422 | calib +0.036 | log loss 0.4968 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1624 (47) | Brier 0.1029 | calib +0.052 | log loss 0.3006 | — | -0.0710 [-0.0884, -0.0558] (n=1054) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 854 (44) | 5.330 | -0.245 | — | — |  |
| points | pf-nba-points (challenger) | 1049 (47) | 4.539 | +0.362 | 3.144 | 80% | — |
| pra | pf-nba-pra (challenger) | 1049 (47) | 6.113 | +0.317 | 4.283 | 75% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 854 (44) | 2.204 | -0.167 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1049 (47) | 1.902 | -0.089 | 1.319 | 79% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 854 (44) | 0.954 | -0.025 | — | — |  |
| threes | pf-nba-threes (challenger) | 1049 (47) | 0.855 | +0.012 | 0.558 | 80% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.052 (95% CI +0.025..+0.080) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1624 | 0.1029 |
| incumbent | 1307 | 0.1422 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 262 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1314 | 0.1184 | 0.843 | 0.778 |
| challenger | LIKELY_OUT | 4 | 0.0015 | 0.028 | 0.0 |
| challenger | UNCERTAIN | 44 | 0.2614 | 0.591 | 0.614 |
| incumbent | n/a | 1307 | 0.1422 | 0.689 | 0.653 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 16 | 4.838 | -2.252 |
| E_inj | 1033 | 4.954 | +0.577 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 711 | 4.842 | +0.545 |
| new_team | True | minutes | 338 | 5.183 | +0.511 |
| new_team | False | points | 711 | 4.706 | +0.545 |
| new_team | True | points | 338 | 4.187 | -0.025 |
| reconciled | minutes | minutes | 130 | 5.5 | -1.896 |
| reconciled | minutes+usage | minutes | 49 | 6.662 | -1.964 |
| reconciled | none | minutes | 673 | 4.73 | +0.807 |
| reconciled | usage | minutes | 197 | 4.924 | +1.826 |
| reconciled | minutes | points | 130 | 4.777 | -1.071 |
| reconciled | minutes+usage | points | 49 | 4.872 | -0.167 |
| reconciled | none | points | 673 | 4.406 | +0.73 |
| reconciled | usage | points | 197 | 4.754 | +0.182 |
