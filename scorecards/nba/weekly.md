## NBA projection scorecard — last 28 days

Generated 2026-11-13T03:05:46Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 404318 across 183 games. Settled: 54703 (void/DNP 21910, stat corrections 255).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 3359 (168) | 1.436 | +0.021 | — | — |  |
| assists | pf-nba-assists (challenger) | 3853 (171) | 1.314 | +0.043 | 0.886 | 79% | — |
| fga | pf-nba-fga (challenger) | 3853 (171) | 2.671 | +0.270 | 1.860 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 3359 (168) | 5.912 | +0.552 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 3853 (171) | 4.767 | +0.701 | 3.362 | 80% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 4997 (168) | Brier 0.1355 | calib +0.008 | log loss 0.4545 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 5940 (171) | Brier 0.0922 | calib +0.024 | log loss 0.2793 | — | -0.0643 [-0.0723, -0.0557] (n=4269) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 3359 (168) | 5.131 | +0.410 | — | — |  |
| points | pf-nba-points (challenger) | 3853 (171) | 4.481 | +0.423 | 3.099 | 80% | — |
| pra | pf-nba-pra (challenger) | 3853 (171) | 5.853 | +0.456 | 4.082 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 3359 (168) | 2.055 | +0.191 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 3853 (171) | 1.822 | +0.010 | 1.255 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 3359 (168) | 0.957 | +0.020 | — | — |  |
| threes | pf-nba-threes (challenger) | 3853 (171) | 0.868 | +0.012 | 0.564 | 78% | — |

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
| challenger | 5940 | 0.0922 |
| incumbent | 4997 | 0.1355 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 1122 | 0.0009 | 0.0 | 0.001 |
| challenger | LIKELY_ACTIVE | 4622 | 0.1075 | 0.841 | 0.807 |
| challenger | LIKELY_OUT | 13 | 0.0005 | 0.013 | 0.0 |
| challenger | UNCERTAIN | 183 | 0.2723 | 0.599 | 0.678 |
| incumbent | n/a | 4997 | 0.1355 | 0.68 | 0.672 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 80 | 5.195 | -1.299 |
| E_inj | 3773 | 4.758 | +0.744 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 3278 | 4.656 | +0.738 |
| new_team | True | minutes | 575 | 5.397 | +0.493 |
| new_team | False | points | 3278 | 4.521 | +0.514 |
| new_team | True | points | 575 | 4.253 | -0.093 |
| reconciled | minutes | minutes | 445 | 5.668 | -1.299 |
| reconciled | minutes+usage | minutes | 159 | 5.815 | -0.501 |
| reconciled | none | minutes | 2652 | 4.553 | +0.955 |
| reconciled | usage | minutes | 597 | 4.766 | +1.385 |
| reconciled | minutes | points | 445 | 4.775 | -0.649 |
| reconciled | minutes+usage | points | 159 | 4.19 | +0.269 |
| reconciled | none | points | 2652 | 4.408 | +0.528 |
| reconciled | usage | points | 597 | 4.664 | +0.799 |
