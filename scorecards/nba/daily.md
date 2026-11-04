## NBA projection scorecard — last 7 days

Generated 2026-11-04T01:30:02Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 266036 across 121 games. Settled: 33459 (void/DNP 14458, stat corrections 161).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1026 (52) | 1.404 | -0.151 | — | — |  |
| assists | pf-nba-assists (challenger) | 1154 (52) | 1.316 | +0.016 | 0.887 | 80% | — |
| fga | pf-nba-fga (challenger) | 1154 (52) | 2.652 | +0.384 | 1.835 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1026 (52) | 5.255 | -0.595 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1154 (52) | 4.571 | +0.824 | 3.184 | 82% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1548 (52) | Brier 0.1170 | calib +0.033 | log loss 0.4075 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1805 (52) | Brier 0.0870 | calib +0.024 | log loss 0.2583 | — | -0.0586 [-0.0701, -0.0483] (n=1294) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1026 (52) | 5.035 | -0.174 | — | — |  |
| points | pf-nba-points (challenger) | 1154 (52) | 4.560 | +0.605 | 3.135 | 80% | — |
| pra | pf-nba-pra (challenger) | 1154 (52) | 5.795 | +0.611 | 3.997 | 78% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1026 (52) | 1.920 | -0.005 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1154 (52) | 1.745 | +0.026 | 1.200 | 82% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1026 (52) | 0.992 | -0.078 | — | — |  |
| threes | pf-nba-threes (challenger) | 1154 (52) | 0.920 | -0.009 | 0.600 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.605 (95% CI +0.280..+0.973) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1805 | 0.087 |
| incumbent | 1548 | 0.117 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 359 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1391 | 0.1015 | 0.84 | 0.807 |
| challenger | LIKELY_OUT | 5 | 0.0 | 0.005 | 0.0 |
| challenger | UNCERTAIN | 50 | 0.3175 | 0.589 | 0.64 |
| incumbent | n/a | 1548 | 0.117 | 0.696 | 0.663 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 18 | 5.203 | -1.183 |
| E_inj | 1136 | 4.561 | +0.856 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 998 | 4.494 | +0.745 |
| new_team | True | minutes | 156 | 5.065 | +1.329 |
| new_team | False | points | 998 | 4.582 | +0.664 |
| new_team | True | points | 156 | 4.415 | +0.227 |
| reconciled | minutes | minutes | 97 | 4.627 | -0.627 |
| reconciled | minutes+usage | minutes | 56 | 5.489 | +0.829 |
| reconciled | none | minutes | 829 | 4.544 | +0.872 |
| reconciled | usage | minutes | 172 | 4.372 | +1.414 |
| reconciled | minutes | points | 97 | 4.814 | +0.338 |
| reconciled | minutes+usage | points | 56 | 3.926 | +1.115 |
| reconciled | none | points | 829 | 4.555 | +0.468 |
| reconciled | usage | points | 172 | 4.647 | +1.25 |
