## NBA projection scorecard — last 7 days

Generated 2026-10-29T00:44:40Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 167604 across 71 games. Settled: 17196 (void/DNP 7630, stat corrections 104).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 812 (42) | 1.502 | -0.040 | — | — |  |
| assists | pf-nba-assists (challenger) | 1022 (45) | 1.286 | +0.046 | 0.870 | 80% | — |
| fga | pf-nba-fga (challenger) | 1022 (45) | 2.782 | +0.203 | 1.941 | 80% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 812 (42) | 7.189 | +0.039 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1022 (45) | 4.969 | +0.672 | 3.532 | 78% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1249 (42) | Brier 0.1493 | calib +0.029 | log loss 0.5165 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1558 (45) | Brier 0.1004 | calib +0.042 | log loss 0.2944 | — | -0.0796 [-0.0990, -0.0638] (n=998) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 812 (42) | 5.502 | +0.071 | — | — |  |
| points | pf-nba-points (challenger) | 1022 (45) | 4.499 | +0.351 | 3.122 | 80% | — |
| pra | pf-nba-pra (challenger) | 1022 (45) | 6.094 | +0.324 | 4.271 | 76% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 812 (42) | 2.262 | -0.047 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1022 (45) | 1.873 | -0.094 | 1.304 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 812 (42) | 0.973 | +0.020 | — | — |  |
| threes | pf-nba-threes (challenger) | 1022 (45) | 0.852 | +0.022 | 0.553 | 80% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **ALERT** — bias +0.042 (95% CI +0.013..+0.068) exceeds 5% of the mean
- points: **OK** — within expectations
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1558 | 0.1004 |
| incumbent | 1249 | 0.1493 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 255 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1258 | 0.1165 | 0.844 | 0.791 |
| challenger | LIKELY_OUT | 4 | 0.0015 | 0.028 | 0.0 |
| challenger | UNCERTAIN | 41 | 0.2409 | 0.599 | 0.659 |
| incumbent | n/a | 1249 | 0.1493 | 0.679 | 0.65 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 17 | 5.058 | -0.94 |
| E_inj | 1005 | 4.968 | +0.699 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 695 | 4.887 | +0.717 |
| new_team | True | minutes | 327 | 5.144 | +0.578 |
| new_team | False | points | 695 | 4.692 | +0.541 |
| new_team | True | points | 327 | 4.089 | -0.053 |
| reconciled | minutes | minutes | 130 | 5.5 | -1.896 |
| reconciled | minutes+usage | minutes | 49 | 6.662 | -1.964 |
| reconciled | none | minutes | 646 | 4.748 | +1.037 |
| reconciled | usage | minutes | 197 | 4.924 | +1.826 |
| reconciled | minutes | points | 130 | 4.777 | -1.071 |
| reconciled | minutes+usage | points | 49 | 4.872 | -0.167 |
| reconciled | none | points | 646 | 4.337 | +0.728 |
| reconciled | usage | points | 197 | 4.754 | +0.182 |
