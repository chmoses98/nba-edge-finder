## NBA projection scorecard — last 7 days

Generated 2026-11-11T03:05:15Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 373586 across 170 games. Settled: 49373 (void/DNP 20226, stat corrections 239).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1035 (48) | 1.386 | -0.012 | — | — |  |
| assists | pf-nba-assists (challenger) | 1090 (48) | 1.361 | +0.110 | 0.911 | 80% | — |
| fga | pf-nba-fga (challenger) | 1090 (48) | 2.566 | +0.333 | 1.791 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1035 (48) | 5.273 | +0.499 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1090 (48) | 4.597 | +0.928 | 3.251 | 82% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1434 (48) | Brier 0.1196 | calib -0.025 | log loss 0.4066 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1675 (48) | Brier 0.0816 | calib -0.002 | log loss 0.2547 | — | -0.0544 [-0.0682, -0.0397] (n=1326) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1035 (48) | 4.718 | +0.321 | — | — |  |
| points | pf-nba-points (challenger) | 1090 (48) | 4.363 | +0.560 | 3.019 | 80% | — |
| pra | pf-nba-pra (challenger) | 1090 (48) | 5.677 | +0.701 | 3.980 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1035 (48) | 1.968 | +0.150 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1090 (48) | 1.863 | +0.077 | 1.272 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1035 (48) | 0.895 | +0.030 | — | — |  |
| threes | pf-nba-threes (challenger) | 1090 (48) | 0.851 | +0.053 | 0.548 | 81% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.560 (95% CI +0.233..+0.836) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1675 | 0.0816 |
| incumbent | 1434 | 0.1196 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 345 | 0.0029 | 0.0 | 0.003 |
| challenger | LIKELY_ACTIVE | 1268 | 0.0924 | 0.832 | 0.829 |
| challenger | LIKELY_OUT | 2 | 0.0 | 0.003 | 0.0 |
| challenger | UNCERTAIN | 60 | 0.3069 | 0.554 | 0.65 |
| incumbent | n/a | 1434 | 0.1196 | 0.696 | 0.722 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 24 | 5.391 | -2.568 |
| E_inj | 1066 | 4.579 | +1.007 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1068 | 4.606 | +0.932 |
| new_team | True | minutes | 22 | 4.14 | +0.749 |
| new_team | False | points | 1068 | 4.384 | +0.525 |
| new_team | True | points | 22 | 3.355 | +2.238 |
| reconciled | minutes | minutes | 72 | 5.159 | +0.813 |
| reconciled | minutes+usage | minutes | 33 | 6.347 | -0.531 |
| reconciled | none | minutes | 822 | 4.422 | +1.002 |
| reconciled | usage | minutes | 163 | 4.874 | +0.904 |
| reconciled | minutes | points | 72 | 3.965 | +0.338 |
| reconciled | minutes+usage | points | 33 | 4.063 | -0.534 |
| reconciled | none | points | 822 | 4.39 | +0.58 |
| reconciled | usage | points | 163 | 4.467 | +0.776 |
