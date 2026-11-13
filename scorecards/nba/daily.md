## NBA projection scorecard — last 7 days

Generated 2026-11-13T03:05:46Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 404318 across 183 games. Settled: 54703 (void/DNP 21910, stat corrections 255).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1047 (48) | 1.331 | +0.001 | — | — |  |
| assists | pf-nba-assists (challenger) | 1085 (48) | 1.323 | +0.108 | 0.886 | 78% | — |
| fga | pf-nba-fga (challenger) | 1085 (48) | 2.509 | +0.381 | 1.751 | 84% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1047 (48) | 4.907 | +0.566 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1085 (48) | 4.406 | +1.028 | 3.113 | 83% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1426 (48) | Brier 0.1270 | calib -0.031 | log loss 0.4293 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1675 (48) | Brier 0.0788 | calib -0.006 | log loss 0.2499 | — | -0.0552 [-0.0700, -0.0406] (n=1373) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1047 (48) | 4.581 | +0.214 | — | — |  |
| points | pf-nba-points (challenger) | 1085 (48) | 4.333 | +0.500 | 3.003 | 82% | — |
| pra | pf-nba-pra (challenger) | 1085 (48) | 5.690 | +0.718 | 3.950 | 78% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1047 (48) | 1.873 | +0.268 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1085 (48) | 1.798 | +0.163 | 1.230 | 80% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1047 (48) | 0.877 | -0.034 | — | — |  |
| threes | pf-nba-threes (challenger) | 1085 (48) | 0.838 | -0.003 | 0.550 | 82% | — |

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
| challenger | 1675 | 0.0788 |
| incumbent | 1426 | 0.127 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 357 | 0.0028 | 0.0 | 0.003 |
| challenger | LIKELY_ACTIVE | 1260 | 0.0896 | 0.83 | 0.837 |
| challenger | LIKELY_OUT | 2 | 0.0 | 0.003 | 0.0 |
| challenger | UNCERTAIN | 56 | 0.3245 | 0.54 | 0.554 |
| incumbent | n/a | 1426 | 0.127 | 0.703 | 0.734 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 18 | 4.418 | +0.51 |
| E_inj | 1067 | 4.406 | +1.036 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 1064 | 4.415 | +1.026 |
| new_team | True | minutes | 21 | 3.94 | +1.128 |
| new_team | False | points | 1064 | 4.365 | +0.492 |
| new_team | True | points | 21 | 2.688 | +0.885 |
| reconciled | minutes | minutes | 72 | 5.33 | +0.986 |
| reconciled | minutes+usage | minutes | 25 | 3.341 | +1.726 |
| reconciled | none | minutes | 812 | 4.262 | +0.962 |
| reconciled | usage | minutes | 176 | 4.841 | +1.248 |
| reconciled | minutes | points | 72 | 4.74 | +0.412 |
| reconciled | minutes+usage | points | 25 | 3.651 | -0.167 |
| reconciled | none | points | 812 | 4.236 | +0.415 |
| reconciled | usage | points | 176 | 4.71 | +1.021 |
