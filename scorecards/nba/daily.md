## NBA projection scorecard — last 7 days

Generated 2026-11-01T23:38:14Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 227289 across 107 games. Settled: 27674 (void/DNP 12026, stat corrections 155).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 929 (47) | 1.435 | -0.157 | — | — |  |
| assists | pf-nba-assists (challenger) | 1055 (47) | 1.294 | +0.019 | 0.877 | 80% | — |
| fga | pf-nba-fga (challenger) | 1055 (47) | 2.783 | +0.330 | 1.931 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 929 (47) | 5.732 | -0.489 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1055 (47) | 4.775 | +0.667 | 3.350 | 80% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1400 (47) | Brier 0.1200 | calib +0.031 | log loss 0.4081 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1626 (47) | Brier 0.0912 | calib +0.029 | log loss 0.2689 | — | -0.0592 [-0.0695, -0.0488] (n=1156) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 929 (47) | 5.139 | -0.140 | — | — |  |
| points | pf-nba-points (challenger) | 1055 (47) | 4.601 | +0.590 | 3.175 | 79% | — |
| pra | pf-nba-pra (challenger) | 1055 (47) | 5.976 | +0.589 | 4.134 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 929 (47) | 2.052 | -0.077 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1055 (47) | 1.831 | -0.011 | 1.261 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 929 (47) | 0.982 | -0.037 | — | — |  |
| threes | pf-nba-threes (challenger) | 1055 (47) | 0.903 | +0.014 | 0.586 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.590 (95% CI +0.223..+0.970) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1626 | 0.0912 |
| incumbent | 1400 | 0.12 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 293 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1275 | 0.1038 | 0.842 | 0.804 |
| challenger | LIKELY_OUT | 7 | 0.0004 | 0.011 | 0.0 |
| challenger | UNCERTAIN | 51 | 0.3115 | 0.579 | 0.588 |
| incumbent | n/a | 1400 | 0.12 | 0.695 | 0.664 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 13 | 5.396 | -3.679 |
| E_inj | 1042 | 4.767 | +0.722 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 817 | 4.725 | +0.64 |
| new_team | True | minutes | 238 | 4.947 | +0.76 |
| new_team | False | points | 817 | 4.712 | +0.722 |
| new_team | True | points | 238 | 4.22 | +0.135 |
| reconciled | minutes | minutes | 125 | 4.683 | -0.332 |
| reconciled | minutes+usage | minutes | 46 | 5.331 | +0.222 |
| reconciled | none | minutes | 766 | 4.784 | +0.802 |
| reconciled | usage | minutes | 118 | 4.597 | +1.027 |
| reconciled | minutes | points | 125 | 4.643 | +0.101 |
| reconciled | minutes+usage | points | 46 | 3.389 | +1.36 |
| reconciled | none | points | 766 | 4.6 | +0.585 |
| reconciled | usage | points | 118 | 5.039 | +0.835 |
