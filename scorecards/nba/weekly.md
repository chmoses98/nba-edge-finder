## NBA projection scorecard — last 28 days

Generated 2026-11-01T00:51:08Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 216306 across 92 games. Settled: 25744 (void/DNP 11232, stat corrections 135).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1488 (80) | 1.554 | +0.074 | — | — |  |
| assists | pf-nba-assists (challenger) | 1865 (83) | 1.309 | -0.001 | 0.890 | 79% | — |
| fga | pf-nba-fga (challenger) | 1865 (83) | 2.769 | +0.170 | 1.934 | 80% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1488 (80) | 6.884 | +0.804 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1865 (83) | 4.999 | +0.414 | 3.525 | 78% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 2375 (80) | Brier 0.1519 | calib +0.032 | log loss 0.5070 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 2874 (83) | Brier 0.1037 | calib +0.047 | log loss 0.3091 | — | -0.0755 [-0.0892, -0.0642] (n=1863) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1488 (80) | 5.616 | +0.660 | — | — |  |
| points | pf-nba-points (challenger) | 1865 (83) | 4.567 | +0.306 | 3.170 | 79% | — |
| pra | pf-nba-pra (challenger) | 1865 (83) | 6.030 | +0.235 | 4.227 | 77% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1488 (80) | 2.228 | +0.197 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1865 (83) | 1.849 | -0.090 | 1.283 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1488 (80) | 1.005 | +0.065 | — | — |  |
| threes | pf-nba-threes (challenger) | 1865 (83) | 0.863 | +0.012 | 0.559 | 77% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.047 (95% CI +0.027..+0.068) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 2874 | 0.1037 |
| incumbent | 2375 | 0.1519 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 482 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 2299 | 0.1213 | 0.847 | 0.786 |
| challenger | LIKELY_OUT | 10 | 0.0006 | 0.015 | 0.0 |
| challenger | UNCERTAIN | 83 | 0.2311 | 0.649 | 0.687 |
| incumbent | n/a | 2375 | 0.1519 | 0.659 | 0.627 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 37 | 4.964 | -0.901 |
| E_inj | 1828 | 4.999 | +0.44 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1342 | 4.83 | +0.442 |
| new_team | True | minutes | 523 | 5.431 | +0.34 |
| new_team | False | points | 1342 | 4.662 | +0.492 |
| new_team | True | points | 523 | 4.325 | -0.173 |
| reconciled | minutes | minutes | 316 | 5.737 | -1.918 |
| reconciled | minutes+usage | minutes | 94 | 6.021 | -1.065 |
| reconciled | none | minutes | 1173 | 4.729 | +0.876 |
| reconciled | usage | minutes | 282 | 4.953 | +1.596 |
| reconciled | minutes | points | 316 | 4.85 | -0.99 |
| reconciled | minutes+usage | points | 94 | 4.184 | +0.471 |
| reconciled | none | points | 1173 | 4.462 | +0.566 |
| reconciled | usage | points | 282 | 4.817 | +0.62 |
