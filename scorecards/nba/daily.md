## NBA projection scorecard — last 7 days

Generated 2026-11-10T02:57:33Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 357170 across 160 games. Settled: 47596 (void/DNP 19752, stat corrections 235).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 976 (46) | 1.399 | -0.033 | — | — |  |
| assists | pf-nba-assists (challenger) | 1036 (46) | 1.370 | +0.090 | 0.915 | 79% | — |
| fga | pf-nba-fga (challenger) | 1036 (46) | 2.597 | +0.342 | 1.807 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 976 (46) | 5.319 | +0.426 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1036 (46) | 4.664 | +0.963 | 3.281 | 81% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1375 (46) | Brier 0.1133 | calib -0.014 | log loss 0.3953 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1607 (46) | Brier 0.0804 | calib +0.004 | log loss 0.2504 | — | -0.0510 [-0.0644, -0.0391] (n=1256) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 976 (46) | 4.806 | +0.202 | — | — |  |
| points | pf-nba-points (challenger) | 1036 (46) | 4.398 | +0.499 | 3.039 | 80% | — |
| pra | pf-nba-pra (challenger) | 1036 (46) | 5.743 | +0.624 | 4.027 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 976 (46) | 1.980 | +0.155 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1036 (46) | 1.866 | +0.081 | 1.276 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 976 (46) | 0.912 | +0.031 | — | — |  |
| threes | pf-nba-threes (challenger) | 1036 (46) | 0.860 | +0.063 | 0.554 | 81% | — |

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
| challenger | 1607 | 0.0804 |
| incumbent | 1375 | 0.1133 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 333 | 0.003 | 0.0 | 0.003 |
| challenger | LIKELY_ACTIVE | 1211 | 0.0911 | 0.834 | 0.822 |
| challenger | LIKELY_OUT | 2 | 0.0 | 0.003 | 0.0 |
| challenger | UNCERTAIN | 61 | 0.2928 | 0.548 | 0.672 |
| incumbent | n/a | 1375 | 0.1133 | 0.695 | 0.71 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 27 | 5.828 | -1.937 |
| E_inj | 1009 | 4.633 | +1.04 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1011 | 4.67 | +0.967 |
| new_team | True | minutes | 25 | 4.433 | +0.787 |
| new_team | False | points | 1011 | 4.419 | +0.466 |
| new_team | True | points | 25 | 3.55 | +1.837 |
| reconciled | minutes | minutes | 46 | 5.483 | +0.916 |
| reconciled | minutes+usage | minutes | 33 | 6.347 | -0.531 |
| reconciled | none | minutes | 819 | 4.524 | +1.044 |
| reconciled | usage | minutes | 138 | 4.819 | +0.851 |
| reconciled | minutes | points | 46 | 4.055 | +0.717 |
| reconciled | minutes+usage | points | 33 | 4.063 | -0.534 |
| reconciled | none | points | 819 | 4.429 | +0.534 |
| reconciled | usage | points | 138 | 4.406 | +0.465 |
