# Stat-refit challenger R1: forward evaluation (freeze e115652)

Eligible snapshots: 11; rows 3697.

Settled games 16; played player-games 365.

**INSUFFICIENT for a verdict** (minimum 30 settled games and 500 played player-games). Everything below is descriptive.

## Per family (conditional on playing): P0 frozen as published, P1 JRM + existing stat models, P2 challenger R1

| family | n | P0 MAE / bias | P1 MAE / bias | P2 MAE / bias | ΔMAE P2−P0 [95% CI] | ΔMAE P2−P1 [95% CI] | rung Brier P0 / P1 / P2 | ΔBrier P2−P0 [95% CI] |
|---|---:|---|---|---|---|---|---|---|
| points | 365 | 4.362 / +0.405 | 4.352 / +0.667 | 4.207 / +0.795 | -0.155 [-0.301, +0.013] | -0.145 [-0.270, +0.009] | 0.0777 / 0.0779 / 0.0785 | +0.0007 [-0.0020, +0.0041] |
| rebounds | 365 | 2.028 / -0.190 | 2.002 / -0.034 | 1.990 / -0.029 | -0.037 [-0.091, +0.017] | -0.011 [-0.048, +0.027] | 0.1225 / 0.1195 / 0.1192 | -0.0033 [-0.0066, +0.0003] |
| assists | 365 | 1.274 / +0.094 | 1.277 / +0.166 | 1.229 / +0.139 | -0.046 [-0.078, -0.004] | -0.049 [-0.079, -0.013] | 0.0943 / 0.0936 / 0.0921 | -0.0022 [-0.0052, +0.0013] |
| threes | 365 | 0.878 / -0.009 | 0.880 / +0.035 | 0.879 / +0.055 | +0.000 [-0.014, +0.016] | -0.001 [-0.015, +0.013] | 0.1334 / 0.1333 / 0.1325 | -0.0009 [-0.0032, +0.0019] |
| pra | 365 | 6.168 / +0.354 | 6.130 / +0.811 | 5.919 / +0.951 | -0.249 [-0.466, -0.009] | -0.211 [-0.394, -0.008] | 0.0947 / 0.0940 / 0.0927 | -0.0020 [-0.0052, +0.0015] |
| fga | 365 | 2.797 / +0.071 | 2.845 / +0.274 | 2.747 / +0.318 | -0.050 [-0.173, +0.054] | -0.098 [-0.202, -0.011] | 0.0867 / 0.0878 / 0.0873 | +0.0006 [-0.0029, +0.0037] |

## Pre-registered criteria

| family | 1 accuracy non-inferiority (upper ΔMAE < +2% of P0 MAE) | 2 bias (\|bias P2\| ≤ 5% of mean and ≤ \|bias P0\| + 2%) | 3 rung Brier (upper Δ < +0.003) |
|---|---|---|---|
| points | PASS (upper +0.013 vs 0.087) | FAIL (bias +0.795, P0 +0.405, mean 9.95) | FAIL (+0.0007 [-0.0020, +0.0041]) |
| rebounds | PASS (upper +0.017 vs 0.041) | PASS (bias -0.029, P0 -0.190, mean 3.97) | PASS (-0.0033 [-0.0066, +0.0003]) |
| assists | PASS (upper -0.004 vs 0.025) | FAIL (bias +0.139, P0 +0.094, mean 2.26) | PASS (-0.0022 [-0.0052, +0.0013]) |
| threes | PASS (upper +0.016 vs 0.018) | FAIL (bias +0.055, P0 -0.009, mean 1.18) | PASS (-0.0009 [-0.0032, +0.0019]) |
| pra | PASS (upper -0.009 vs 0.123) | FAIL (bias +0.951, P0 +0.354, mean 16.18) | PASS (-0.0020 [-0.0052, +0.0015]) |
| fga | PASS (upper +0.054 vs 0.056) | FAIL (bias +0.318, P0 +0.071, mean 7.89) | FAIL (+0.0006 [-0.0029, +0.0037]) |

**No verdict (INSUFFICIENT or monitoring run).** Criteria above are descriptive.
