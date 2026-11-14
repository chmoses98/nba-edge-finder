## NBA projection scorecard — last 28 days

Generated 2026-11-14T03:16:47Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 418309 across 188 games. Settled: 56315 (void/DNP 22568, stat corrections 255).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 3466 (173) | 1.439 | +0.019 | — | — |  |
| assists | pf-nba-assists (challenger) | 3961 (176) | 1.317 | +0.042 | 0.888 | 79% | — |
| fga | pf-nba-fga (challenger) | 3961 (176) | 2.666 | +0.260 | 1.856 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 3466 (173) | 5.912 | +0.541 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 3961 (176) | 4.770 | +0.668 | 3.368 | 80% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 5146 (173) | Brier 0.1346 | calib +0.007 | log loss 0.4509 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 6112 (176) | Brier 0.0924 | calib +0.025 | log loss 0.2801 | — | -0.0622 [-0.0703, -0.0545] (n=4416) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 3466 (173) | 5.128 | +0.411 | — | — |  |
| points | pf-nba-points (challenger) | 3961 (176) | 4.491 | +0.416 | 3.107 | 80% | — |
| pra | pf-nba-pra (challenger) | 3961 (176) | 5.875 | +0.446 | 4.095 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 3466 (173) | 2.054 | +0.190 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 3961 (176) | 1.825 | +0.009 | 1.257 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 3466 (173) | 0.954 | +0.019 | — | — |  |
| threes | pf-nba-threes (challenger) | 3961 (176) | 0.866 | +0.011 | 0.564 | 78% | — |

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
| challenger | 6112 | 0.0924 |
| incumbent | 5146 | 0.1346 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 1150 | 0.0009 | 0.0 | 0.001 |
| challenger | LIKELY_ACTIVE | 4764 | 0.1079 | 0.84 | 0.805 |
| challenger | LIKELY_OUT | 13 | 0.0005 | 0.013 | 0.0 |
| challenger | UNCERTAIN | 185 | 0.2701 | 0.601 | 0.681 |
| incumbent | n/a | 5146 | 0.1346 | 0.681 | 0.674 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 82 | 5.2 | -1.4 |
| E_inj | 3879 | 4.761 | +0.712 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 3385 | 4.663 | +0.696 |
| new_team | True | minutes | 576 | 5.402 | +0.506 |
| new_team | False | points | 3385 | 4.531 | +0.501 |
| new_team | True | points | 576 | 4.258 | -0.08 |
| reconciled | minutes | minutes | 445 | 5.668 | -1.299 |
| reconciled | minutes+usage | minutes | 159 | 5.815 | -0.501 |
| reconciled | none | minutes | 2724 | 4.567 | +0.906 |
| reconciled | usage | minutes | 633 | 4.751 | +1.322 |
| reconciled | minutes | points | 445 | 4.775 | -0.649 |
| reconciled | minutes+usage | points | 159 | 4.19 | +0.269 |
| reconciled | none | points | 2724 | 4.42 | +0.506 |
| reconciled | usage | points | 633 | 4.675 | +0.813 |
