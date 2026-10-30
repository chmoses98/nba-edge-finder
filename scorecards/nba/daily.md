## NBA projection scorecard — last 7 days

Generated 2026-10-30T22:28:03Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 201651 across 88 games. Settled: 21859 (void/DNP 9668, stat corrections 120).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1024 (52) | 1.470 | -0.181 | — | — |  |
| assists | pf-nba-assists (challenger) | 1203 (54) | 1.302 | +0.015 | 0.884 | 80% | — |
| fga | pf-nba-fga (challenger) | 1203 (54) | 2.738 | +0.209 | 1.908 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1024 (52) | 6.433 | -0.879 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1203 (54) | 4.845 | +0.521 | 3.442 | 79% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1548 (52) | Brier 0.1372 | calib +0.035 | log loss 0.4854 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1869 (54) | Brier 0.1005 | calib +0.047 | log loss 0.2935 | — | -0.0692 [-0.0828, -0.0576] (n=1268) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1024 (52) | 5.245 | -0.423 | — | — |  |
| points | pf-nba-points (challenger) | 1203 (54) | 4.575 | +0.376 | 3.168 | 80% | — |
| pra | pf-nba-pra (challenger) | 1203 (54) | 6.069 | +0.292 | 4.260 | 76% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1024 (52) | 2.140 | -0.219 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1203 (54) | 1.882 | -0.101 | 1.310 | 79% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1024 (52) | 0.953 | -0.057 | — | — |  |
| threes | pf-nba-threes (challenger) | 1203 (54) | 0.875 | -0.004 | 0.569 | 79% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.047 (95% CI +0.018..+0.070) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1869 | 0.1005 |
| incumbent | 1548 | 0.1372 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 316 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1496 | 0.1166 | 0.842 | 0.784 |
| challenger | LIKELY_OUT | 5 | 0.0012 | 0.023 | 0.0 |
| challenger | UNCERTAIN | 52 | 0.2573 | 0.596 | 0.577 |
| incumbent | n/a | 1548 | 0.1372 | 0.697 | 0.661 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 16 | 4.818 | -2.272 |
| E_inj | 1187 | 4.846 | +0.559 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 827 | 4.799 | +0.516 |
| new_team | True | minutes | 376 | 4.946 | +0.532 |
| new_team | False | points | 827 | 4.757 | +0.558 |
| new_team | True | points | 376 | 4.176 | -0.023 |
| reconciled | minutes | minutes | 162 | 5.028 | -0.991 |
| reconciled | minutes+usage | minutes | 59 | 6.287 | -1.893 |
| reconciled | none | minutes | 753 | 4.734 | +0.663 |
| reconciled | usage | minutes | 229 | 4.708 | +1.747 |
| reconciled | minutes | points | 162 | 4.557 | -0.237 |
| reconciled | minutes+usage | points | 59 | 4.844 | -0.169 |
| reconciled | none | points | 753 | 4.469 | +0.489 |
| reconciled | usage | points | 229 | 4.866 | +0.579 |
