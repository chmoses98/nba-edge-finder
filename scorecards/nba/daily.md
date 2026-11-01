## NBA projection scorecard — last 7 days

Generated 2026-11-01T19:46:50Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 222937 across 103 games. Settled: 27389 (void/DNP 11871, stat corrections 155).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 991 (50) | 1.435 | -0.154 | — | — |  |
| assists | pf-nba-assists (challenger) | 1171 (52) | 1.302 | +0.035 | 0.880 | 80% | — |
| fga | pf-nba-fga (challenger) | 1171 (52) | 2.783 | +0.304 | 1.928 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 991 (50) | 5.721 | -0.562 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1171 (52) | 4.749 | +0.696 | 3.340 | 81% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1492 (50) | Brier 0.1248 | calib +0.031 | log loss 0.4310 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1800 (52) | Brier 0.0928 | calib +0.029 | log loss 0.2734 | — | -0.0640 [-0.0766, -0.0525] (n=1229) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 991 (50) | 5.121 | -0.157 | — | — |  |
| points | pf-nba-points (challenger) | 1171 (52) | 4.585 | +0.563 | 3.165 | 79% | — |
| pra | pf-nba-pra (challenger) | 1171 (52) | 6.012 | +0.575 | 4.180 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 991 (50) | 2.045 | -0.111 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1171 (52) | 1.848 | -0.020 | 1.278 | 79% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 991 (50) | 0.978 | -0.043 | — | — |  |
| threes | pf-nba-threes (challenger) | 1171 (52) | 0.905 | +0.003 | 0.586 | 80% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.563 (95% CI +0.271..+0.841) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1800 | 0.0928 |
| incumbent | 1492 | 0.1248 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 321 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1416 | 0.1056 | 0.841 | 0.804 |
| challenger | LIKELY_OUT | 8 | 0.0004 | 0.01 | 0.0 |
| challenger | UNCERTAIN | 55 | 0.3192 | 0.582 | 0.6 |
| incumbent | n/a | 1492 | 0.1248 | 0.695 | 0.664 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 16 | 5.428 | -3.577 |
| E_inj | 1155 | 4.74 | +0.755 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 891 | 4.695 | +0.653 |
| new_team | True | minutes | 280 | 4.922 | +0.832 |
| new_team | False | points | 891 | 4.732 | +0.636 |
| new_team | True | points | 280 | 4.116 | +0.329 |
| reconciled | minutes | minutes | 125 | 4.683 | -0.332 |
| reconciled | minutes+usage | minutes | 56 | 5.075 | +0.023 |
| reconciled | none | minutes | 822 | 4.784 | +0.746 |
| reconciled | usage | minutes | 168 | 4.517 | +1.442 |
| reconciled | minutes | points | 125 | 4.643 | +0.101 |
| reconciled | minutes+usage | points | 56 | 3.443 | +1.251 |
| reconciled | none | points | 822 | 4.613 | +0.572 |
| reconciled | usage | points | 168 | 4.783 | +0.629 |
