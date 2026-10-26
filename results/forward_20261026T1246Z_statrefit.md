# Stat-refit challenger R1: forward evaluation (freeze e115652)

Eligible snapshots: 6; rows 2105.

Settled games 7; played player-games 155.

**INSUFFICIENT for a verdict** (minimum 30 settled games and 500 played player-games). Everything below is descriptive.

## Per family (conditional on playing): P0 frozen as published, P1 JRM + existing stat models, P2 challenger R1

| family | n | P0 MAE / bias | P1 MAE / bias | P2 MAE / bias | ΔMAE P2−P0 [95% CI] | ΔMAE P2−P1 [95% CI] | rung Brier P0 / P1 / P2 | ΔBrier P2−P0 [95% CI] |
|---|---:|---|---|---|---|---|---|---|
| points | 155 | 4.503 / +0.249 | 4.448 / +0.207 | 4.370 / +0.685 | -0.133 [-0.376, +0.105] | -0.079 [-0.298, +0.115] | 0.0779 / 0.0773 / 0.0786 | +0.0007 [-0.0043, +0.0053] |
| rebounds | 155 | 1.978 / -0.216 | 1.949 / -0.094 | 1.981 / -0.094 | +0.003 [-0.070, +0.077] | +0.032 [-0.002, +0.075] | 0.1242 / 0.1227 / 0.1248 | +0.0006 [-0.0051, +0.0056] |
| assists | 155 | 1.398 / +0.128 | 1.387 / +0.150 | 1.347 / +0.116 | -0.051 [-0.096, +0.005] | -0.041 [-0.081, +0.009] | 0.1029 / 0.1012 / 0.1011 | -0.0017 [-0.0069, +0.0029] |
| threes | 155 | 0.911 / -0.058 | 0.907 / -0.043 | 0.912 / +0.008 | +0.001 [-0.016, +0.019] | +0.005 [-0.002, +0.014] | 0.1360 / 0.1347 / 0.1345 | -0.0015 [-0.0043, +0.0016] |
| pra | 155 | 6.225 / +0.171 | 6.144 / +0.194 | 6.038 / +0.796 | -0.187 [-0.350, +0.002] | -0.107 [-0.315, +0.099] | 0.0984 / 0.0973 / 0.0975 | -0.0008 [-0.0054, +0.0038] |
| fga | 155 | 2.731 / -0.039 | 2.757 / -0.069 | 2.754 / +0.191 | +0.023 [-0.115, +0.123] | -0.003 [-0.116, +0.081] | 0.0830 / 0.0855 / 0.0875 | +0.0045 [+0.0010, +0.0077] |

## Pre-registered criteria

| family | 1 accuracy non-inferiority (upper ΔMAE < +2% of P0 MAE) | 2 bias (\|bias P2\| ≤ 5% of mean and ≤ \|bias P0\| + 2%) | 3 rung Brier (upper Δ < +0.003) |
|---|---|---|---|
| points | FAIL (upper +0.105 vs 0.090) | FAIL (bias +0.685, P0 +0.249, mean 10.11) | FAIL (+0.0007 [-0.0043, +0.0053]) |
| rebounds | FAIL (upper +0.077 vs 0.040) | PASS (bias -0.094, P0 -0.216, mean 3.95) | FAIL (+0.0006 [-0.0051, +0.0056]) |
| assists | PASS (upper +0.005 vs 0.028) | FAIL (bias +0.116, P0 +0.128, mean 2.27) | PASS (-0.0017 [-0.0069, +0.0029]) |
| threes | FAIL (upper +0.019 vs 0.018) | PASS (bias +0.008, P0 -0.058, mean 1.19) | PASS (-0.0015 [-0.0043, +0.0016]) |
| pra | PASS (upper +0.002 vs 0.124) | FAIL (bias +0.796, P0 +0.171, mean 16.34) | FAIL (-0.0008 [-0.0054, +0.0038]) |
| fga | FAIL (upper +0.123 vs 0.055) | PASS (bias +0.191, P0 -0.039, mean 7.99) | FAIL (+0.0045 [+0.0010, +0.0077]) |

**No verdict (INSUFFICIENT or monitoring run).** Criteria above are descriptive.
