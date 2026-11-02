## NBA projection scorecard — last 28 days

Generated 2026-11-02T12:07:30Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 237597 across 107 games. Settled: 28664 (void/DNP 12385, stat corrections 155).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1669 (89) | 1.532 | +0.051 | — | — |  |
| assists | pf-nba-assists (challenger) | 2070 (92) | 1.308 | -0.009 | 0.888 | 79% | — |
| fga | pf-nba-fga (challenger) | 2070 (92) | 2.781 | +0.177 | 1.939 | 80% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1669 (89) | 6.726 | +0.721 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 2070 (92) | 4.991 | +0.473 | 3.519 | 78% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 2641 (89) | Brier 0.1483 | calib +0.031 | log loss 0.4950 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 3188 (92) | Brier 0.1011 | calib +0.043 | log loss 0.3018 | — | -0.0738 [-0.0858, -0.0616] (n=2090) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1669 (89) | 5.590 | +0.591 | — | — |  |
| points | pf-nba-points (challenger) | 2070 (92) | 4.605 | +0.306 | 3.189 | 79% | — |
| pra | pf-nba-pra (challenger) | 2070 (92) | 6.048 | +0.228 | 4.234 | 76% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1669 (89) | 2.199 | +0.181 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 2070 (92) | 1.841 | -0.083 | 1.276 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1669 (89) | 1.014 | +0.051 | — | — |  |
| threes | pf-nba-threes (challenger) | 2070 (92) | 0.879 | +0.003 | 0.573 | 77% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.043 (95% CI +0.022..+0.062) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 3188 | 0.1011 |
| incumbent | 2641 | 0.1483 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 549 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 2539 | 0.1184 | 0.846 | 0.792 |
| challenger | LIKELY_OUT | 11 | 0.0006 | 0.014 | 0.0 |
| challenger | UNCERTAIN | 89 | 0.2437 | 0.651 | 0.674 |
| incumbent | n/a | 2641 | 0.1483 | 0.663 | 0.632 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 39 | 5.112 | -1.253 |
| E_inj | 2031 | 4.989 | +0.506 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1537 | 4.826 | +0.48 |
| new_team | True | minutes | 533 | 5.467 | +0.45 |
| new_team | False | points | 1537 | 4.707 | +0.47 |
| new_team | True | points | 533 | 4.313 | -0.167 |
| reconciled | minutes | minutes | 328 | 5.664 | -1.926 |
| reconciled | minutes+usage | minutes | 108 | 6.085 | -0.596 |
| reconciled | none | minutes | 1341 | 4.75 | +0.908 |
| reconciled | usage | minutes | 293 | 4.941 | +1.559 |
| reconciled | minutes | points | 328 | 4.86 | -0.963 |
| reconciled | minutes+usage | points | 108 | 4.295 | +0.52 |
| reconciled | none | points | 1341 | 4.528 | +0.522 |
| reconciled | usage | points | 293 | 4.79 | +0.66 |
