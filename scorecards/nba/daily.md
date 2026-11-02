## NBA projection scorecard — last 7 days

Generated 2026-11-02T03:39:33Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 234897 across 107 games. Settled: 27974 (void/DNP 12186, stat corrections 155).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 931 (47) | 1.436 | -0.155 | — | — |  |
| assists | pf-nba-assists (challenger) | 1055 (47) | 1.298 | +0.021 | 0.878 | 81% | — |
| fga | pf-nba-fga (challenger) | 1055 (47) | 2.773 | +0.355 | 1.923 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 931 (47) | 5.693 | -0.467 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1055 (47) | 4.767 | +0.641 | 3.345 | 80% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1400 (47) | Brier 0.1189 | calib +0.030 | log loss 0.4043 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1626 (47) | Brier 0.0897 | calib +0.028 | log loss 0.2646 | — | -0.0574 [-0.0675, -0.0462] (n=1159) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 931 (47) | 5.125 | -0.097 | — | — |  |
| points | pf-nba-points (challenger) | 1055 (47) | 4.586 | +0.614 | 3.160 | 79% | — |
| pra | pf-nba-pra (challenger) | 1055 (47) | 5.962 | +0.631 | 4.121 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 931 (47) | 2.051 | -0.050 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1055 (47) | 1.830 | +0.005 | 1.259 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 931 (47) | 0.988 | -0.040 | — | — |  |
| threes | pf-nba-threes (challenger) | 1055 (47) | 0.909 | +0.011 | 0.590 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.614 (95% CI +0.292..+0.952) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1626 | 0.0897 |
| incumbent | 1400 | 0.1189 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 299 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1271 | 0.1025 | 0.843 | 0.807 |
| challenger | LIKELY_OUT | 6 | 0.0 | 0.004 | 0.0 |
| challenger | UNCERTAIN | 50 | 0.3112 | 0.586 | 0.58 |
| incumbent | n/a | 1400 | 0.1189 | 0.695 | 0.665 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 13 | 5.396 | -3.679 |
| E_inj | 1042 | 4.759 | +0.695 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 823 | 4.698 | +0.605 |
| new_team | True | minutes | 232 | 5.013 | +0.77 |
| new_team | False | points | 823 | 4.684 | +0.745 |
| new_team | True | points | 232 | 4.24 | +0.153 |
| reconciled | minutes | minutes | 125 | 4.683 | -0.332 |
| reconciled | minutes+usage | minutes | 46 | 5.331 | +0.222 |
| reconciled | none | minutes | 766 | 4.773 | +0.765 |
| reconciled | usage | minutes | 118 | 4.597 | +1.027 |
| reconciled | minutes | points | 125 | 4.643 | +0.101 |
| reconciled | minutes+usage | points | 46 | 3.389 | +1.36 |
| reconciled | none | points | 766 | 4.579 | +0.619 |
| reconciled | usage | points | 118 | 5.039 | +0.835 |
