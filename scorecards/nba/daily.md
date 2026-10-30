## NBA projection scorecard — last 7 days

Generated 2026-10-30T18:18:37Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 193247 across 87 games. Settled: 21859 (void/DNP 9668, stat corrections 120).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1043 (53) | 1.468 | -0.187 | — | — |  |
| assists | pf-nba-assists (challenger) | 1223 (55) | 1.303 | +0.004 | 0.886 | 80% | — |
| fga | pf-nba-fga (challenger) | 1223 (55) | 2.748 | +0.182 | 1.916 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1043 (53) | 6.466 | -0.913 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1223 (55) | 4.865 | +0.446 | 3.452 | 78% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1578 (53) | Brier 0.1379 | calib +0.036 | log loss 0.4875 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1904 (55) | Brier 0.1026 | calib +0.051 | log loss 0.2994 | — | -0.0673 [-0.0822, -0.0561] (n=1295) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1043 (53) | 5.275 | -0.459 | — | — |  |
| points | pf-nba-points (challenger) | 1223 (55) | 4.595 | +0.323 | 3.183 | 79% | — |
| pra | pf-nba-pra (challenger) | 1223 (55) | 6.088 | +0.218 | 4.277 | 76% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1043 (53) | 2.151 | -0.226 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1223 (55) | 1.886 | -0.113 | 1.314 | 78% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1043 (53) | 0.954 | -0.060 | — | — |  |
| threes | pf-nba-threes (challenger) | 1223 (55) | 0.875 | -0.010 | 0.570 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.051 (95% CI +0.022..+0.073) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1904 | 0.1026 |
| incumbent | 1578 | 0.1379 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 317 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1530 | 0.1189 | 0.842 | 0.78 |
| challenger | LIKELY_OUT | 5 | 0.0012 | 0.023 | 0.0 |
| challenger | UNCERTAIN | 52 | 0.2573 | 0.596 | 0.577 |
| incumbent | n/a | 1578 | 0.1379 | 0.697 | 0.661 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 16 | 4.818 | -2.272 |
| E_inj | 1207 | 4.865 | +0.482 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 839 | 4.819 | +0.454 |
| new_team | True | minutes | 384 | 4.963 | +0.428 |
| new_team | False | points | 839 | 4.757 | +0.537 |
| new_team | True | points | 384 | 4.241 | -0.147 |
| reconciled | minutes | minutes | 182 | 5.139 | -1.331 |
| reconciled | minutes+usage | minutes | 59 | 6.287 | -1.893 |
| reconciled | none | minutes | 753 | 4.734 | +0.663 |
| reconciled | usage | minutes | 229 | 4.708 | +1.747 |
| reconciled | minutes | points | 182 | 4.69 | -0.529 |
| reconciled | minutes+usage | points | 59 | 4.844 | -0.169 |
| reconciled | none | points | 753 | 4.469 | +0.489 |
| reconciled | usage | points | 229 | 4.866 | +0.579 |
