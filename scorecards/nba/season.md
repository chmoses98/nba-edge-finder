## NBA projection scorecard — season to date

Generated 2026-11-08T12:28:53Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 329390 across 146 games. Settled: 43920 (void/DNP 18440, stat corrections 209).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 2642 (136) | 1.488 | +0.024 | — | — |  |
| assists | pf-nba-assists (challenger) | 3120 (139) | 1.328 | +0.030 | 0.898 | 79% | — |
| fga | pf-nba-fga (challenger) | 3120 (139) | 2.706 | +0.223 | 1.886 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 2642 (136) | 6.238 | +0.513 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 3120 (139) | 4.881 | +0.632 | 3.439 | 78% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 4048 (136) | Brier 0.1356 | calib +0.021 | log loss 0.4551 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 4822 (139) | Brier 0.0940 | calib +0.031 | log loss 0.2809 | — | -0.0670 [-0.0761, -0.0580] (n=3340) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 2642 (136) | 5.304 | +0.477 | — | — |  |
| points | pf-nba-points (challenger) | 3120 (139) | 4.524 | +0.426 | 3.132 | 80% | — |
| pra | pf-nba-pra (challenger) | 3120 (139) | 5.913 | +0.399 | 4.138 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 2642 (136) | 2.118 | +0.139 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 3120 (139) | 1.837 | -0.055 | 1.271 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 2642 (136) | 0.982 | +0.039 | — | — |  |
| threes | pf-nba-threes (challenger) | 3120 (139) | 0.878 | +0.022 | 0.570 | 77% | — |

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
| challenger | 4822 | 0.094 |
| incumbent | 4048 | 0.1356 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 896 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 3777 | 0.111 | 0.844 | 0.8 |
| challenger | LIKELY_OUT | 12 | 0.0005 | 0.013 | 0.0 |
| challenger | UNCERTAIN | 137 | 0.2466 | 0.621 | 0.715 |
| incumbent | n/a | 4048 | 0.1356 | 0.674 | 0.653 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 67 | 5.383 | -1.917 |
| E_inj | 3053 | 4.87 | +0.688 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 2558 | 4.759 | +0.659 |
| new_team | True | minutes | 562 | 5.439 | +0.509 |
| new_team | False | points | 2558 | 4.576 | +0.541 |
| new_team | True | points | 562 | 4.289 | -0.097 |
| reconciled | minutes | minutes | 395 | 5.689 | -1.615 |
| reconciled | minutes+usage | minutes | 134 | 6.277 | -0.917 |
| reconciled | none | minutes | 2118 | 4.647 | +0.992 |
| reconciled | usage | minutes | 473 | 4.86 | +1.335 |
| reconciled | minutes | points | 395 | 4.79 | -0.743 |
| reconciled | minutes+usage | points | 134 | 4.291 | +0.351 |
| reconciled | none | points | 2118 | 4.448 | +0.578 |
| reconciled | usage | points | 473 | 4.71 | +0.742 |
