# Stat-refit challenger R1: forward evaluation (freeze e115652)

Eligible snapshots: 14; rows 4734.

Settled games 20; played player-games 458.

**INSUFFICIENT for a verdict** (minimum 30 settled games and 500 played player-games). Everything below is descriptive.

## Per family (conditional on playing): P0 frozen as published, P1 JRM + existing stat models, P2 challenger R1

| family | n | P0 MAE / bias | P1 MAE / bias | P2 MAE / bias | ΔMAE P2−P0 [95% CI] | ΔMAE P2−P1 [95% CI] | rung Brier P0 / P1 / P2 | ΔBrier P2−P0 [95% CI] |
|---|---:|---|---|---|---|---|---|---|
| points | 458 | 4.381 / +0.310 | 4.384 / +0.528 | 4.259 / +0.642 | -0.122 [-0.254, +0.016] | -0.125 [-0.241, +0.002] | 0.0787 / 0.0790 / 0.0794 | +0.0007 [-0.0021, +0.0033] |
| rebounds | 458 | 1.953 / -0.078 | 1.926 / +0.052 | 1.911 / +0.031 | -0.042 [-0.084, +0.003] | -0.015 [-0.044, +0.016] | 0.1150 / 0.1123 / 0.1122 | -0.0029 [-0.0058, -0.0000] |
| assists | 458 | 1.282 / +0.077 | 1.285 / +0.138 | 1.235 / +0.095 | -0.047 [-0.081, -0.012] | -0.050 [-0.079, -0.019] | 0.0950 / 0.0946 / 0.0931 | -0.0019 [-0.0047, +0.0010] |
| threes | 458 | 0.894 / -0.011 | 0.896 / +0.024 | 0.891 / +0.042 | -0.003 [-0.015, +0.010] | -0.005 [-0.019, +0.007] | 0.1333 / 0.1333 / 0.1322 | -0.0011 [-0.0032, +0.0010] |
| pra | 458 | 6.055 / +0.330 | 6.060 / +0.716 | 5.884 / +0.808 | -0.171 [-0.362, +0.053] | -0.176 [-0.331, -0.013] | 0.0921 / 0.0918 / 0.0910 | -0.0012 [-0.0041, +0.0020] |
| fga | 458 | 2.790 / +0.108 | 2.837 / +0.278 | 2.739 / +0.318 | -0.051 [-0.162, +0.055] | -0.098 [-0.192, -0.008] | 0.0864 / 0.0876 / 0.0870 | +0.0006 [-0.0025, +0.0038] |

## Pre-registered criteria

| family | 1 accuracy non-inferiority (upper ΔMAE < +2% of P0 MAE) | 2 bias (\|bias P2\| ≤ 5% of mean and ≤ \|bias P0\| + 2%) | 3 rung Brier (upper Δ < +0.003) |
|---|---|---|---|
| points | PASS (upper +0.016 vs 0.088) | FAIL (bias +0.642, P0 +0.310, mean 10.01) | FAIL (+0.0007 [-0.0021, +0.0033]) |
| rebounds | PASS (upper +0.003 vs 0.039) | PASS (bias +0.031, P0 -0.078, mean 3.91) | PASS (-0.0029 [-0.0058, -0.0000]) |
| assists | PASS (upper -0.012 vs 0.026) | PASS (bias +0.095, P0 +0.077, mean 2.30) | PASS (-0.0019 [-0.0047, +0.0010]) |
| threes | PASS (upper +0.010 vs 0.018) | FAIL (bias +0.042, P0 -0.011, mean 1.19) | PASS (-0.0011 [-0.0032, +0.0010]) |
| pra | PASS (upper +0.053 vs 0.121) | FAIL (bias +0.808, P0 +0.330, mean 16.23) | PASS (-0.0012 [-0.0041, +0.0020]) |
| fga | PASS (upper +0.055 vs 0.056) | FAIL (bias +0.318, P0 +0.108, mean 7.83) | FAIL (+0.0006 [-0.0025, +0.0038]) |

**No verdict (INSUFFICIENT or monitoring run).** Criteria above are descriptive.
