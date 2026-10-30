## NBA projection scorecard — season to date

Generated 2026-10-30T22:28:03Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 201651 across 88 games. Settled: 21859 (void/DNP 9668, stat corrections 120).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1251 (68) | 1.576 | +0.115 | — | — |  |
| assists | pf-nba-assists (challenger) | 1590 (71) | 1.314 | -0.010 | 0.895 | 79% | — |
| fga | pf-nba-fga (challenger) | 1590 (71) | 2.793 | +0.098 | 1.953 | 80% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1251 (68) | 7.243 | +1.041 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1590 (71) | 5.063 | +0.263 | 3.589 | 77% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 2017 (68) | Brier 0.1604 | calib +0.032 | log loss 0.5282 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 2457 (71) | Brier 0.1066 | calib +0.054 | log loss 0.3184 | — | -0.0808 [-0.0944, -0.0675] (n=1570) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1251 (68) | 5.764 | +0.778 | — | — |  |
| points | pf-nba-points (challenger) | 1590 (71) | 4.601 | +0.207 | 3.190 | 79% | — |
| pra | pf-nba-pra (challenger) | 1590 (71) | 6.057 | +0.098 | 4.264 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1251 (68) | 2.291 | +0.215 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1590 (71) | 1.871 | -0.127 | 1.303 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1251 (68) | 1.011 | +0.095 | — | — |  |
| threes | pf-nba-threes (challenger) | 1590 (71) | 0.862 | +0.015 | 0.559 | 77% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.054 (95% CI +0.030..+0.078) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 2457 | 0.1066 |
| incumbent | 2017 | 0.1604 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 404 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1974 | 0.1254 | 0.848 | 0.781 |
| challenger | LIKELY_OUT | 7 | 0.0009 | 0.019 | 0.0 |
| challenger | UNCERTAIN | 72 | 0.2017 | 0.675 | 0.681 |
| incumbent | n/a | 2017 | 0.1604 | 0.653 | 0.62 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 35 | 5.012 | -0.717 |
| E_inj | 1555 | 5.064 | +0.285 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1094 | 4.9 | +0.314 |
| new_team | True | minutes | 496 | 5.424 | +0.152 |
| new_team | False | points | 1094 | 4.723 | +0.439 |
| new_team | True | points | 496 | 4.332 | -0.304 |
| reconciled | minutes | minutes | 304 | 5.81 | -2.023 |
| reconciled | minutes+usage | minutes | 68 | 6.262 | -2.084 |
| reconciled | none | minutes | 946 | 4.765 | +0.791 |
| reconciled | usage | minutes | 272 | 4.967 | +1.57 |
| reconciled | minutes | points | 304 | 4.84 | -1.04 |
| reconciled | minutes+usage | points | 68 | 4.718 | -0.207 |
| reconciled | none | points | 946 | 4.46 | +0.531 |
| reconciled | usage | points | 272 | 4.797 | +0.579 |
