# Stat-refit challenger R1: forward evaluation (freeze e115652)

Eligible snapshots: 19; rows 6494.

Settled games 32; played player-games 714.

## Per family (conditional on playing): P0 frozen as published, P1 JRM + existing stat models, P2 challenger R1

| family | n | P0 MAE / bias | P1 MAE / bias | P2 MAE / bias | ΔMAE P2−P0 [95% CI] | ΔMAE P2−P1 [95% CI] | rung Brier P0 / P1 / P2 | ΔBrier P2−P0 [95% CI] |
|---|---:|---|---|---|---|---|---|---|
| points | 714 | 4.457 / +0.415 | 4.446 / +0.515 | 4.322 / +0.618 | -0.135 [-0.242, -0.020] | -0.124 [-0.228, -0.009] | 0.0825 / 0.0826 / 0.0821 | -0.0004 [-0.0025, +0.0019] |
| rebounds | 714 | 1.930 / -0.109 | 1.917 / +0.040 | 1.905 / +0.030 | -0.025 [-0.056, +0.008] | -0.012 [-0.033, +0.010] | 0.1151 / 0.1131 / 0.1131 | -0.0019 [-0.0042, +0.0002] |
| assists | 714 | 1.285 / +0.046 | 1.288 / +0.106 | 1.251 / +0.093 | -0.034 [-0.063, -0.004] | -0.037 [-0.061, -0.011] | 0.0953 / 0.0950 / 0.0936 | -0.0017 [-0.0041, +0.0005] |
| threes | 714 | 0.897 / +0.004 | 0.897 / +0.032 | 0.888 / +0.044 | -0.009 [-0.021, +0.003] | -0.009 [-0.023, +0.006] | 0.1340 / 0.1339 / 0.1322 | -0.0018 [-0.0033, +0.0000] |
| pra | 714 | 5.849 / +0.370 | 5.861 / +0.636 | 5.696 / +0.762 | -0.152 [-0.306, +0.013] | -0.165 [-0.292, -0.041] | 0.0902 / 0.0902 / 0.0889 | -0.0013 [-0.0036, +0.0010] |
| fga | 714 | 2.749 / +0.157 | 2.772 / +0.239 | 2.683 / +0.283 | -0.066 [-0.150, +0.015] | -0.089 [-0.165, -0.017] | 0.0868 / 0.0876 / 0.0865 | -0.0002 [-0.0028, +0.0023] |

## Pre-registered criteria

| family | 1 accuracy non-inferiority (upper ΔMAE < +2% of P0 MAE) | 2 bias (\|bias P2\| ≤ 5% of mean and ≤ \|bias P0\| + 2%) | 3 rung Brier (upper Δ < +0.003) |
|---|---|---|---|
| points | PASS (upper -0.020 vs 0.089) | FAIL (bias +0.618, P0 +0.415, mean 10.16) | PASS (-0.0004 [-0.0025, +0.0019]) |
| rebounds | PASS (upper +0.008 vs 0.039) | PASS (bias +0.030, P0 -0.109, mean 3.98) | PASS (-0.0019 [-0.0042, +0.0002]) |
| assists | PASS (upper -0.004 vs 0.026) | FAIL (bias +0.093, P0 +0.046, mean 2.36) | PASS (-0.0017 [-0.0041, +0.0005]) |
| threes | PASS (upper +0.003 vs 0.018) | FAIL (bias +0.044, P0 +0.004, mean 1.18) | PASS (-0.0018 [-0.0033, +0.0000]) |
| pra | PASS (upper +0.013 vs 0.117) | FAIL (bias +0.762, P0 +0.370, mean 16.50) | PASS (-0.0013 [-0.0036, +0.0010]) |
| fga | PASS (upper +0.015 vs 0.055) | PASS (bias +0.283, P0 +0.157, mean 7.96) | PASS (-0.0002 [-0.0028, +0.0023]) |

**Pre-registered verdict for criteria 1-3 (criterion 4, the minutes rules, is evaluated by evaluate_prospective.py on the same games): FAIL.**
