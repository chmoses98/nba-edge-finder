## NBA projection scorecard — last 28 days

Generated 2026-11-13T17:14:05Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 407973 across 183 games. Settled: 55671 (void/DNP 22306, stat corrections 255).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 3423 (171) | 1.441 | +0.017 | — | — |  |
| assists | pf-nba-assists (challenger) | 3918 (174) | 1.318 | +0.040 | 0.889 | 79% | — |
| fga | pf-nba-fga (challenger) | 3918 (174) | 2.670 | +0.262 | 1.859 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 3423 (171) | 5.919 | +0.537 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 3918 (174) | 4.783 | +0.678 | 3.376 | 79% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 5087 (171) | Brier 0.1345 | calib +0.008 | log loss 0.4509 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 6043 (174) | Brier 0.0917 | calib +0.024 | log loss 0.2778 | — | -0.0631 [-0.0712, -0.0551] (n=4357) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 3423 (171) | 5.131 | +0.399 | — | — |  |
| points | pf-nba-points (challenger) | 3918 (174) | 4.491 | +0.412 | 3.108 | 80% | — |
| pra | pf-nba-pra (challenger) | 3918 (174) | 5.871 | +0.442 | 4.094 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 3423 (171) | 2.056 | +0.191 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 3918 (174) | 1.825 | +0.010 | 1.257 | 81% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 3423 (171) | 0.955 | +0.019 | — | — |  |
| threes | pf-nba-threes (challenger) | 3918 (174) | 0.866 | +0.011 | 0.564 | 78% | — |

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
| challenger | 6043 | 0.0917 |
| incumbent | 5087 | 0.1345 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 1143 | 0.0009 | 0.0 | 0.001 |
| challenger | LIKELY_ACTIVE | 4704 | 0.107 | 0.841 | 0.807 |
| challenger | LIKELY_OUT | 13 | 0.0005 | 0.013 | 0.0 |
| challenger | UNCERTAIN | 183 | 0.2723 | 0.599 | 0.678 |
| incumbent | n/a | 5087 | 0.1345 | 0.681 | 0.673 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 80 | 5.195 | -1.299 |
| E_inj | 3838 | 4.774 | +0.719 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 3342 | 4.676 | +0.708 |
| new_team | True | minutes | 576 | 5.402 | +0.506 |
| new_team | False | points | 3342 | 4.532 | +0.497 |
| new_team | True | points | 576 | 4.258 | -0.08 |
| reconciled | minutes | minutes | 445 | 5.668 | -1.299 |
| reconciled | minutes+usage | minutes | 159 | 5.815 | -0.501 |
| reconciled | none | minutes | 2692 | 4.584 | +0.915 |
| reconciled | usage | minutes | 622 | 4.746 | +1.369 |
| reconciled | minutes | points | 445 | 4.775 | -0.649 |
| reconciled | minutes+usage | points | 159 | 4.19 | +0.269 |
| reconciled | none | points | 2692 | 4.42 | +0.499 |
| reconciled | usage | points | 622 | 4.675 | +0.831 |
