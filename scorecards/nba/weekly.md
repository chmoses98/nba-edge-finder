## NBA projection scorecard — last 28 days

Generated 2026-11-06T05:02:42Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 295081 across 132 games. Settled: 38393 (void/DNP 16315, stat corrections 167).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 2287 (119) | 1.485 | +0.032 | — | — |  |
| assists | pf-nba-assists (challenger) | 2741 (122) | 1.310 | +0.018 | 0.886 | 79% | — |
| fga | pf-nba-fga (challenger) | 2741 (122) | 2.736 | +0.218 | 1.905 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 2287 (119) | 6.375 | +0.525 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 2741 (122) | 4.905 | +0.562 | 3.460 | 78% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 3541 (119) | Brier 0.1392 | calib +0.025 | log loss 0.4657 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 4230 (122) | Brier 0.0977 | calib +0.036 | log loss 0.2914 | — | -0.0686 [-0.0786, -0.0582] (n=2869) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 2287 (119) | 5.388 | +0.485 | — | — |  |
| points | pf-nba-points (challenger) | 2741 (122) | 4.540 | +0.382 | 3.139 | 80% | — |
| pra | pf-nba-pra (challenger) | 2741 (122) | 5.924 | +0.339 | 4.142 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 2287 (119) | 2.142 | +0.152 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 2741 (122) | 1.833 | -0.056 | 1.267 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 2287 (119) | 0.992 | +0.043 | — | — |  |
| threes | pf-nba-threes (challenger) | 2741 (122) | 0.878 | +0.017 | 0.570 | 77% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.036 (95% CI +0.018..+0.056) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 4230 | 0.0977 |
| incumbent | 3541 | 0.1392 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 759 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 3335 | 0.1146 | 0.845 | 0.795 |
| challenger | LIKELY_OUT | 11 | 0.0006 | 0.014 | 0.0 |
| challenger | UNCERTAIN | 125 | 0.2504 | 0.625 | 0.728 |
| incumbent | n/a | 3541 | 0.1392 | 0.671 | 0.646 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 60 | 5.51 | -1.794 |
| E_inj | 2681 | 4.892 | +0.615 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 2187 | 4.767 | +0.586 |
| new_team | True | minutes | 554 | 5.453 | +0.469 |
| new_team | False | points | 2187 | 4.597 | +0.512 |
| new_team | True | points | 554 | 4.312 | -0.13 |
| reconciled | minutes | minutes | 359 | 5.769 | -1.913 |
| reconciled | minutes+usage | minutes | 134 | 6.277 | -0.917 |
| reconciled | none | minutes | 1827 | 4.675 | +0.955 |
| reconciled | usage | minutes | 421 | 4.734 | +1.443 |
| reconciled | minutes | points | 359 | 4.824 | -0.907 |
| reconciled | minutes+usage | points | 134 | 4.291 | +0.351 |
| reconciled | none | points | 1827 | 4.478 | +0.563 |
| reconciled | usage | points | 421 | 4.645 | +0.706 |
