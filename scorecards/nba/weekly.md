## NBA projection scorecard — last 28 days

Generated 2026-10-31T23:00:30Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 215395 across 92 games. Settled: 25450 (void/DNP 11074, stat corrections 135).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1470 (79) | 1.554 | +0.086 | — | — |  |
| assists | pf-nba-assists (challenger) | 1845 (82) | 1.308 | +0.005 | 0.888 | 79% | — |
| fga | pf-nba-fga (challenger) | 1845 (82) | 2.776 | +0.160 | 1.938 | 80% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1470 (79) | 6.910 | +0.844 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1845 (82) | 5.001 | +0.395 | 3.527 | 78% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 2345 (79) | Brier 0.1522 | calib +0.032 | log loss 0.5082 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 2840 (82) | Brier 0.1040 | calib +0.048 | log loss 0.3098 | — | -0.0752 [-0.0886, -0.0628] (n=1839) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1470 (79) | 5.633 | +0.690 | — | — |  |
| points | pf-nba-points (challenger) | 1845 (82) | 4.571 | +0.302 | 3.171 | 79% | — |
| pra | pf-nba-pra (challenger) | 1845 (82) | 6.037 | +0.235 | 4.232 | 76% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1470 (79) | 2.236 | +0.192 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1845 (82) | 1.852 | -0.095 | 1.286 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1470 (79) | 1.003 | +0.069 | — | — |  |
| threes | pf-nba-threes (challenger) | 1845 (82) | 0.861 | +0.011 | 0.558 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.048 (95% CI +0.024..+0.069) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 2840 | 0.104 |
| incumbent | 2345 | 0.1522 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 474 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 2277 | 0.1218 | 0.847 | 0.787 |
| challenger | LIKELY_OUT | 10 | 0.0006 | 0.015 | 0.0 |
| challenger | UNCERTAIN | 79 | 0.2286 | 0.655 | 0.684 |
| incumbent | n/a | 2345 | 0.1522 | 0.659 | 0.627 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 36 | 4.922 | -0.747 |
| E_inj | 1809 | 5.002 | +0.418 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1322 | 4.831 | +0.417 |
| new_team | True | minutes | 523 | 5.431 | +0.34 |
| new_team | False | points | 1322 | 4.668 | +0.491 |
| new_team | True | points | 523 | 4.325 | -0.173 |
| reconciled | minutes | minutes | 316 | 5.737 | -1.918 |
| reconciled | minutes+usage | minutes | 94 | 6.021 | -1.065 |
| reconciled | none | minutes | 1163 | 4.726 | +0.867 |
| reconciled | usage | minutes | 272 | 4.967 | +1.57 |
| reconciled | minutes | points | 316 | 4.85 | -0.99 |
| reconciled | minutes+usage | points | 94 | 4.184 | +0.471 |
| reconciled | none | points | 1163 | 4.474 | +0.575 |
| reconciled | usage | points | 272 | 4.797 | +0.579 |
