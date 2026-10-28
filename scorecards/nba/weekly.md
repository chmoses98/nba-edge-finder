## NBA projection scorecard — last 28 days

Generated 2026-10-28T03:03:36Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 151134 across 68 games. Settled: 16898 (void/DNP 7480, stat corrections 86).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 943 (52) | 1.605 | +0.236 | — | — |  |
| assists | pf-nba-assists (challenger) | 1248 (55) | 1.297 | -0.010 | 0.884 | 79% | — |
| fga | pf-nba-fga (challenger) | 1248 (55) | 2.845 | +0.054 | 1.990 | 79% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 943 (52) | 7.844 | +1.785 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1248 (55) | 5.240 | +0.261 | 3.718 | 76% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1543 (52) | Brier 0.1711 | calib +0.028 | log loss 0.5569 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1904 (55) | Brier 0.1098 | calib +0.053 | log loss 0.3290 | — | -0.0884 [-0.1066, -0.0716] (n=1180) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 943 (52) | 5.983 | +1.228 | — | — |  |
| points | pf-nba-points (challenger) | 1248 (55) | 4.581 | +0.136 | 3.185 | 79% | — |
| pra | pf-nba-pra (challenger) | 1248 (55) | 6.148 | +0.017 | 4.332 | 76% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 943 (52) | 2.387 | +0.342 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1248 (55) | 1.878 | -0.146 | 1.310 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 943 (52) | 1.024 | +0.159 | — | — |  |
| threes | pf-nba-threes (challenger) | 1248 (55) | 0.847 | +0.021 | 0.551 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.053 (95% CI +0.025..+0.083) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1904 | 0.1098 |
| incumbent | 1543 | 0.1711 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 301 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1542 | 0.1288 | 0.851 | 0.783 |
| challenger | LIKELY_OUT | 6 | 0.001 | 0.022 | 0.0 |
| challenger | UNCERTAIN | 55 | 0.1881 | 0.67 | 0.745 |
| incumbent | n/a | 1543 | 0.1711 | 0.639 | 0.611 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 32 | 5.139 | -0.768 |
| E_inj | 1216 | 5.243 | +0.288 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 858 | 5.066 | +0.323 |
| new_team | True | minutes | 390 | 5.623 | +0.125 |
| new_team | False | points | 858 | 4.726 | +0.35 |
| new_team | True | points | 390 | 4.262 | -0.335 |
| reconciled | minutes | minutes | 252 | 6.135 | -2.457 |
| reconciled | minutes+usage | minutes | 58 | 6.574 | -2.177 |
| reconciled | none | minutes | 730 | 4.819 | +1.002 |
| reconciled | usage | minutes | 208 | 5.261 | +1.633 |
| reconciled | minutes | points | 252 | 4.916 | -1.425 |
| reconciled | minutes+usage | points | 58 | 4.719 | -0.212 |
| reconciled | none | points | 730 | 4.394 | +0.63 |
| reconciled | usage | points | 208 | 4.794 | +0.392 |
