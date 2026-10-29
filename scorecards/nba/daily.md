## NBA projection scorecard — last 7 days

Generated 2026-10-29T22:22:28Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 176023 across 81 games. Settled: 20915 (void/DNP 9256, stat corrections 120).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1002 (51) | 1.460 | -0.145 | — | — |  |
| assists | pf-nba-assists (challenger) | 1202 (54) | 1.288 | +0.041 | 0.871 | 82% | — |
| fga | pf-nba-fga (challenger) | 1202 (54) | 2.750 | +0.183 | 1.920 | 81% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1002 (51) | 6.532 | -0.867 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1202 (54) | 4.853 | +0.463 | 3.448 | 79% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1518 (51) | Brier 0.1392 | calib +0.035 | log loss 0.4842 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1870 (54) | Brier 0.1025 | calib +0.051 | log loss 0.2986 | — | -0.0689 [-0.0833, -0.0555] (n=1242) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1002 (51) | 5.273 | -0.367 | — | — |  |
| points | pf-nba-points (challenger) | 1202 (54) | 4.548 | +0.376 | 3.148 | 79% | — |
| pra | pf-nba-pra (challenger) | 1202 (54) | 6.018 | +0.320 | 4.220 | 76% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1002 (51) | 2.170 | -0.204 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1202 (54) | 1.894 | -0.113 | 1.319 | 79% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1002 (51) | 0.953 | -0.050 | — | — |  |
| threes | pf-nba-threes (challenger) | 1202 (54) | 0.864 | +0.005 | 0.562 | 80% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.051 (95% CI +0.023..+0.080) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1870 | 0.1025 |
| incumbent | 1518 | 0.1392 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 310 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1508 | 0.1192 | 0.842 | 0.778 |
| challenger | LIKELY_OUT | 5 | 0.0012 | 0.023 | 0.0 |
| challenger | UNCERTAIN | 47 | 0.2523 | 0.59 | 0.617 |
| incumbent | n/a | 1518 | 0.1392 | 0.695 | 0.66 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 16 | 4.838 | -2.252 |
| E_inj | 1186 | 4.853 | +0.499 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 821 | 4.783 | +0.496 |
| new_team | True | minutes | 381 | 5.005 | +0.391 |
| new_team | False | points | 821 | 4.724 | +0.578 |
| new_team | True | points | 381 | 4.168 | -0.061 |
| reconciled | minutes | minutes | 167 | 5.246 | -1.61 |
| reconciled | minutes+usage | minutes | 59 | 6.287 | -1.893 |
| reconciled | none | minutes | 748 | 4.7 | +0.7 |
| reconciled | usage | minutes | 228 | 4.696 | +1.814 |
| reconciled | minutes | points | 167 | 4.695 | -0.612 |
| reconciled | minutes+usage | points | 59 | 4.844 | -0.169 |
| reconciled | none | points | 748 | 4.406 | +0.583 |
| reconciled | usage | points | 228 | 4.829 | +0.559 |
