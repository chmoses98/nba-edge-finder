## NBA projection scorecard — last 7 days

Generated 2026-11-04T19:20:41Z. Research only; nothing here is a betting signal.

Archived pregame forecasts: 278715 across 121 games. Settled: 33459 (void/DNP 14458, stat corrections 161).

| Stat | Model | n (games) | MAE | Bias | CRPS | 80% range caught | vs incumbent (CRPS) |
|---|---|---|---|---|---|---|---|
| assists | nba_sim_rotation_v1 (incumbent) | 1007 (51) | 1.401 | -0.144 | — | — |  |
| assists | pf-nba-assists (challenger) | 1134 (51) | 1.312 | +0.013 | 0.886 | 80% | — |
| fga | pf-nba-fga (challenger) | 1134 (51) | 2.661 | +0.379 | 1.840 | 82% | — |
| minutes | nba_sim_rotation_v1 (incumbent) | 1007 (51) | 5.263 | -0.587 | — | — |  |
| minutes | pf-nba-minutes (challenger) | 1134 (51) | 4.604 | +0.827 | 3.205 | 81% | — |
| participation (yes/no) | nba_sim_rotation_v1 (incumbent) | 1520 (51) | Brier 0.1176 | calib +0.033 | log loss 0.4095 | — |  |
| participation (yes/no) | pf-nba-participation (challenger) | 1770 (51) | Brier 0.0871 | calib +0.023 | log loss 0.2587 | — | -0.0591 [-0.0706, -0.0489] (n=1274) (Brier) |
| points | nba_sim_rotation_v1 (incumbent) | 1007 (51) | 5.027 | -0.128 | — | — |  |
| points | pf-nba-points (challenger) | 1134 (51) | 4.564 | +0.636 | 3.135 | 80% | — |
| pra | pf-nba-pra (challenger) | 1134 (51) | 5.810 | +0.613 | 4.007 | 78% | — |
| rebounds | nba_sim_rotation_v1 (incumbent) | 1007 (51) | 1.926 | -0.019 | — | — |  |
| rebounds | pf-nba-rebounds (challenger) | 1134 (51) | 1.747 | +0.006 | 1.202 | 82% | — |
| threes | nba_sim_rotation_v1 (incumbent) | 1007 (51) | 0.989 | -0.071 | — | — |  |
| threes | pf-nba-threes (challenger) | 1134 (51) | 0.919 | -0.002 | 0.599 | 78% | — |

**Drift checks**

- assists: **OK** — within expectations
- fga: **OK** — within expectations
- minutes: **OK** — within expectations
- participation: **OK** — within expectations
- points: **ALERT** — bias +0.636 (95% CI +0.361..+0.970) exceeds 5% of the mean
- pra: **OK** — within expectations
- rebounds: **OK** — within expectations
- threes: **OK** — within expectations

### NBA segment checks

**Participation Brier** (P(play) vs played; 2025-26 held-out: hurdle 0.132 -> report-aware 0.087)

| Model | n | Brier |
|---|---|---|
| challenger | 1770 | 0.0871 |
| incumbent | 1520 | 0.1176 |

| Model | Participation status | n | Brier | mean p | played |
|---|---|---|---|---|---|
| challenger | CONFIRMED_OUT | 353 | 0.0 | 0.0 | 0.0 |
| challenger | LIKELY_ACTIVE | 1363 | 0.1014 | 0.841 | 0.809 |
| challenger | LIKELY_OUT | 5 | 0.0 | 0.005 | 0.0 |
| challenger | UNCERTAIN | 49 | 0.3239 | 0.582 | 0.633 |
| incumbent | n/a | 1520 | 0.1176 | 0.696 | 0.662 |

**Challenger minutes by model**

| Minutes model | n | MAE | Bias |
|---|---|---|---|
| E | 18 | 5.203 | -1.183 |
| E_inj | 1116 | 4.594 | +0.86 |

**New-team / reconciled segments**

| Segment | Value | Family | n | MAE | Bias |
|---|---|---|---|---|---|
| new_team | False | minutes | 986 | 4.516 | +0.745 |
| new_team | True | minutes | 148 | 5.188 | +1.373 |
| new_team | False | points | 986 | 4.587 | +0.699 |
| new_team | True | points | 148 | 4.411 | +0.214 |
| reconciled | minutes | minutes | 97 | 4.627 | -0.627 |
| reconciled | minutes+usage | minutes | 56 | 5.489 | +0.829 |
| reconciled | none | minutes | 819 | 4.568 | +0.882 |
| reconciled | usage | minutes | 162 | 4.467 | +1.419 |
| reconciled | minutes | points | 97 | 4.814 | +0.338 |
| reconciled | minutes+usage | points | 56 | 3.926 | +1.115 |
| reconciled | none | points | 819 | 4.559 | +0.473 |
| reconciled | usage | points | 162 | 4.663 | +1.472 |
