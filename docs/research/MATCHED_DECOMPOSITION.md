# W1-C: matched player-game decomposition — the ~20% low bias is an observation-choice artifact

**Preregistration:** `docs/research/PREREG_W1_NBA_DECOMPOSITION.md`, committed alone as
`5f50cb3b0251d1176cadc67fdbae3511bad1f233` and pushed before the holdout was collected.
**Holdout:** every 2025-26 regular-season game 2026-02-01..2026-04-12 — **501 games, 14,763 eligible
player-games, 73,815 player-game-stat rows per arm** (one per statistic, never one per ladder rung).
**Champion:** frozen `NBA_BASELINE_2026_PRESEASON_V1` (digest `5a4cbda0…193be78`), unchanged.
**Inputs:** committed ESPN box history only, rows dated strictly before the game date. No market
file is read by any forecasting arm (proven by rerun below).

## Verdicts

| question | answer |
|---|---|
| Does the ~20% counting-stat low bias persist on the complete eligible holdout population? | **No.** Champion Σpred/Σactual: points **1.007 [0.999, 1.014]**, rebounds 1.056, assists 0.979, threes 1.026. The same forecasts look 16–25% low only in frames selected on the outcome (actually played: 0.838; actually ≥28 min: 0.747) or on market listing (0.896). |
| Where is the residual error? | Offsetting channels: participation over-forecast (F 1.053), minutes given play slightly low (0.979), per-minute rate low (0.977 points, 0.953 assists) and **compressed** toward league rates (top own-usage tercile 0.962, bottom 1.012). |
| One preregistered correction (`RATE_PRIOR_5`, rate prior mass 60 → 5 minutes) | **REJECTED — strict criteria applied (2026-10-11 review). Not promoted.** Points ΔMAE −0.0118 [−0.0156, −0.0075] and exact ΔCRPS −0.0040 [−0.0063, −0.0013] pass the MAE/CRPS wording of rule 4, but threes p10–p90 coverage (−0.0012 unc / −0.0020 cond) and threes bias (+0.0007 / +0.0012) worsen with CIs excluding zero, the gate's 3-quantile ΔCRPS CI spans zero, and it over-corrects the bottom usage tercile. Under the strict any-metric reading adopted at review it fails. Findings are kept as research evidence; the champion is unchanged. |
| Blanket multiplier? | **NO PROMOTION.** A +20% multiplier would turn a ~1.00 full-population ratio into ~1.20. |
| Injury R1 (stint/lineup impact) | **BLOCKED_DATA** — `LINEUP_FEASIBILITY_R1.md`. `impact_ppp` stays 0. |

Champion vs EWM-5 on the full population: the champion wins on unconditional MAE/CRPS for minutes,
points, rebounds and assists (threes MAE tie). **Conditional on actually playing, EWM-5 has the lower
MAE on minutes, points, rebounds and threes** — the same mean-vs-mixture trade-off `MINUTES_MODEL.md`
reported, now measured per statistic.

## Why the old numbers said "20% low"

`ROTATION_CONSUMPTION_TRACE.md` dates every earlier figure. The headline prop numbers were measured
on the pre-rotation simulator, on market-listed populations, with ladder rungs pooled. Two further
effects show up here on identical rows:

1. **Selecting on the outcome.** Restricting to players who actually played (or played ≥28 minutes)
   keeps the games where participation and minutes came out high; any honest forecast is low there.
   EWM-5 looks 23–30% low in those frames too.
2. **Selecting by listing.** Prop contracts are listed for players the book expects to play, using
   injury and lineup news after this model's cutoff (the PURE model has no injury report). Listed
   player-games are 10% under-forecast for that reason, not because of a production-rate error.
3. **Scoring semantics.** The simulator's `played` array is availability, not appearance. Scoring its
   conditional forecast against the box score's "played" without the minutes>0 condition makes it look
   ~11% low (first DEV pass). The scorecard conditions simulator arms on appearance.

## Holdout scorecard
### Final stats and minutes, one row per player-game-stat (holdout)

| stat | frame | n | actual mean | arm | MAE | RMSE | bias | CRPS | p10–p90 cov | Brier@t_ref |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| minutes | unc | 14763 | 15.934 | ewm5 | 8.1179 | 10.34 | -1.0174 | 5.2139 | 0.8246 | 0.2142 |
| minutes | unc | 14763 | 15.934 | sim_rotation | 7.3815 | 10.08 | +0.4280 | 5.0591 | 0.8185 | 0.2065 |
| minutes | unc | 14763 | 15.934 | sim_challenger | 7.3821 | 10.08 | +0.4284 | 5.0599 | 0.8181 | 0.2067 |
| minutes | unc | 14763 | 15.934 | sim_waterfill | 7.6828 | 9.8091 | +0.4200 | 5.3800 | 0.6357 | 0.2337 |
| minutes | cond | 10290 | 22.860 | ewm5 | 5.1741 | 6.6777 | -0.9675 | 3.6897 | 0.7383 | 0.2365 |
| minutes | cond | 10290 | 22.860 | sim_rotation | 5.5351 | 7.1699 | -0.3504 | 3.9447 | 0.8125 | 0.2383 |
| minutes | cond | 10290 | 22.860 | sim_challenger | 5.5359 | 7.1712 | -0.3497 | 3.9458 | 0.8124 | 0.2385 |
| minutes | cond | 10290 | 22.860 | sim_waterfill | 5.8705 | 7.4232 | -3.2541 | 4.2630 | 0.6446 | 0.3024 |
| points | unc | 14763 | 7.661 | ewm5 | 5.0423 | 6.8883 | -0.3517 | 3.4190 | 0.8433 | 0.2038 |
| points | unc | 14763 | 7.661 | sim_rotation | 4.8669 | 6.7344 | +0.0510 | 3.2974 | 0.8435 | 0.1986 |
| points | unc | 14763 | 7.661 | sim_challenger | 4.8551 | 6.7298 | +0.0502 | 3.2935 | 0.8432 | 0.1983 |
| points | unc | 14763 | 7.661 | sim_waterfill | 5.0138 | 6.6777 | +0.0491 | 3.3525 | 0.7988 | 0.1996 |
| points | cond | 10290 | 10.991 | ewm5 | 4.7317 | 6.2064 | -0.3412 | 3.4181 | 0.7282 | 0.2421 |
| points | cond | 10290 | 10.991 | sim_rotation | 4.8064 | 6.2775 | -0.4866 | 3.3953 | 0.8450 | 0.2397 |
| points | cond | 10290 | 10.991 | sim_challenger | 4.7845 | 6.2559 | -0.4879 | 3.3857 | 0.8465 | 0.2390 |
| points | cond | 10290 | 10.991 | sim_waterfill | 4.8111 | 6.4072 | -1.7702 | 3.4678 | 0.7979 | 0.2484 |
| rebounds | unc | 14763 | 2.869 | ewm5 | 1.9634 | 2.7106 | -0.0882 | 1.3211 | 0.8962 | 0.2074 |
| rebounds | unc | 14763 | 2.869 | sim_rotation | 1.9412 | 2.7031 | +0.1593 | 1.3081 | 0.8685 | 0.2070 |
| rebounds | unc | 14763 | 2.869 | sim_challenger | 1.9347 | 2.7022 | +0.1602 | 1.3065 | 0.8675 | 0.2068 |
| rebounds | unc | 14763 | 2.869 | sim_waterfill | 1.9688 | 2.6516 | +0.1590 | 1.3075 | 0.8344 | 0.2037 |
| rebounds | cond | 10290 | 4.115 | ewm5 | 1.9290 | 2.5554 | -0.0343 | 1.3543 | 0.8546 | 0.2379 |
| rebounds | cond | 10290 | 4.115 | sim_rotation | 1.9773 | 2.5997 | +0.0482 | 1.3796 | 0.8722 | 0.2412 |
| rebounds | cond | 10290 | 4.115 | sim_challenger | 1.9688 | 2.5913 | +0.0483 | 1.3766 | 0.8741 | 0.2410 |
| rebounds | cond | 10290 | 4.115 | sim_waterfill | 1.9076 | 2.5927 | -0.4879 | 1.3612 | 0.8425 | 0.2378 |
| assists | unc | 14763 | 1.786 | ewm5 | 1.3427 | 1.9526 | -0.0767 | 0.8912 | 0.9086 | 0.1867 |
| assists | unc | 14763 | 1.786 | sim_rotation | 1.3052 | 1.9222 | -0.0377 | 0.8725 | 0.8869 | 0.1832 |
| assists | unc | 14763 | 1.786 | sim_challenger | 1.3014 | 1.9199 | -0.0384 | 0.8720 | 0.8853 | 0.1831 |
| assists | unc | 14763 | 1.786 | sim_waterfill | 1.3397 | 1.9076 | -0.0393 | 0.8812 | 0.8703 | 0.1833 |
| assists | cond | 10290 | 2.562 | ewm5 | 1.4009 | 1.9115 | -0.0569 | 0.9690 | 0.8842 | 0.2241 |
| assists | cond | 10290 | 2.562 | sim_rotation | 1.4106 | 1.9416 | -0.1757 | 0.9789 | 0.8892 | 0.2239 |
| assists | cond | 10290 | 2.562 | sim_challenger | 1.4048 | 1.9326 | -0.1770 | 0.9768 | 0.8874 | 0.2237 |
| assists | cond | 10290 | 2.562 | sim_waterfill | 1.3959 | 1.9766 | -0.4689 | 0.9936 | 0.8573 | 0.2287 |
| threes | unc | 14763 | 0.883 | ewm5 | 0.7927 | 1.1863 | -0.0380 | 0.5128 | 0.9287 | 0.1844 |
| threes | unc | 14763 | 0.883 | sim_rotation | 0.7947 | 1.1699 | +0.0233 | 0.5054 | 0.9270 | 0.1824 |
| threes | unc | 14763 | 0.883 | sim_challenger | 0.7934 | 1.1697 | +0.0240 | 0.5049 | 0.9259 | 0.1821 |
| threes | unc | 14763 | 0.883 | sim_waterfill | 0.8147 | 1.1650 | +0.0171 | 0.5053 | 0.9264 | 0.1815 |
| threes | cond | 10290 | 1.267 | ewm5 | 0.9077 | 1.2746 | -0.0305 | 0.6115 | 0.9190 | 0.2117 |
| threes | cond | 10290 | 1.267 | sim_rotation | 0.9241 | 1.2616 | -0.0284 | 0.6094 | 0.9282 | 0.2130 |
| threes | cond | 10290 | 1.267 | sim_challenger | 0.9221 | 1.2603 | -0.0272 | 0.6084 | 0.9261 | 0.2125 |
| threes | cond | 10290 | 1.267 | sim_waterfill | 0.9073 | 1.2737 | -0.1877 | 0.6115 | 0.9088 | 0.2116 |

### Paired deltas, game-clustered 95% CI (501 games)

| stat | frame | comparison | ΔMAE | CI | ΔCRPS | CI | ΔBrier@t_ref | CI |
|---|---|---|---:|---|---:|---|---:|---|
| minutes | unc | sim_rotation − ewm5 | -0.7364 | [-0.8041, -0.6688] | -0.1548 | [-0.2080, -0.1060] | -0.0077 | [-0.0104, -0.0051] |
| minutes | unc | sim_waterfill − sim_rotation | +0.3013 | [+0.2221, +0.3795] | +0.3209 | [+0.2515, +0.3885] | +0.0271 | [+0.0226, +0.0315] |
| minutes | unc | sim_challenger − sim_rotation | +0.0005 | [-0.0005, +0.0015] | +0.0008 | [+0.0001, +0.0015] | +0.0001 | [+0.0001, +0.0002] |
| minutes | cond | sim_rotation − ewm5 | +0.3610 | [+0.2955, +0.4263] | +0.2550 | [+0.2039, +0.3002] | +0.0018 | [-0.0017, +0.0055] |
| minutes | cond | sim_waterfill − sim_rotation | +0.3355 | [+0.2498, +0.4268] | +0.3183 | [+0.2521, +0.3878] | +0.0641 | [+0.0574, +0.0707] |
| minutes | cond | sim_challenger − sim_rotation | +0.0009 | [-0.0007, +0.0025] | +0.0012 | [+0.0000, +0.0023] | +0.0002 | [+0.0000, +0.0003] |
| points | unc | sim_rotation − ewm5 | -0.1754 | [-0.2058, -0.1436] | -0.1216 | [-0.1460, -0.0975] | -0.0052 | [-0.0069, -0.0034] |
| points | unc | sim_waterfill − sim_rotation | +0.1469 | [+0.1096, +0.1829] | +0.0551 | [+0.0270, +0.0835] | +0.0010 | [-0.0011, +0.0028] |
| points | unc | sim_challenger − sim_rotation | -0.0118 | [-0.0156, -0.0075] | -0.0040 | [-0.0063, -0.0013] | -0.0003 | [-0.0006, -0.0001] |
| points | cond | sim_rotation − ewm5 | +0.0747 | [+0.0341, +0.1143] | -0.0227 | [-0.0536, +0.0039] | -0.0024 | [-0.0049, +0.0000] |
| points | cond | sim_waterfill − sim_rotation | +0.0047 | [-0.0351, +0.0486] | +0.0724 | [+0.0468, +0.1017] | +0.0087 | [+0.0062, +0.0115] |
| points | cond | sim_challenger − sim_rotation | -0.0219 | [-0.0278, -0.0155] | -0.0096 | [-0.0135, -0.0054] | -0.0007 | [-0.0011, -0.0002] |
| rebounds | unc | sim_rotation − ewm5 | -0.0223 | [-0.0351, -0.0097] | -0.0130 | [-0.0231, -0.0037] | -0.0003 | [-0.0023, +0.0015] |
| rebounds | unc | sim_waterfill − sim_rotation | +0.0276 | [+0.0137, +0.0409] | -0.0006 | [-0.0114, +0.0100] | -0.0033 | [-0.0057, -0.0011] |
| rebounds | unc | sim_challenger − sim_rotation | -0.0065 | [-0.0086, -0.0043] | -0.0016 | [-0.0029, -0.0002] | -0.0003 | [-0.0006, +0.0001] |
| rebounds | cond | sim_rotation − ewm5 | +0.0483 | [+0.0307, +0.0642] | +0.0253 | [+0.0140, +0.0361] | +0.0033 | [+0.0007, +0.0058] |
| rebounds | cond | sim_waterfill − sim_rotation | -0.0698 | [-0.0851, -0.0539] | -0.0184 | [-0.0293, -0.0074] | -0.0034 | [-0.0060, -0.0010] |
| rebounds | cond | sim_challenger − sim_rotation | -0.0086 | [-0.0122, -0.0047] | -0.0030 | [-0.0054, -0.0006] | -0.0002 | [-0.0009, +0.0005] |
| assists | unc | sim_rotation − ewm5 | -0.0375 | [-0.0454, -0.0298] | -0.0186 | [-0.0247, -0.0127] | -0.0036 | [-0.0051, -0.0021] |
| assists | unc | sim_waterfill − sim_rotation | +0.0345 | [+0.0256, +0.0427] | +0.0087 | [+0.0022, +0.0154] | +0.0002 | [-0.0014, +0.0017] |
| assists | unc | sim_challenger − sim_rotation | -0.0038 | [-0.0054, -0.0022] | -0.0006 | [-0.0016, +0.0005] | -0.0001 | [-0.0004, +0.0003] |
| assists | cond | sim_rotation − ewm5 | +0.0097 | [-0.0011, +0.0224] | +0.0099 | [+0.0026, +0.0178] | -0.0003 | [-0.0024, +0.0020] |
| assists | cond | sim_waterfill − sim_rotation | -0.0147 | [-0.0233, -0.0058] | +0.0147 | [+0.0081, +0.0219] | +0.0048 | [+0.0028, +0.0069] |
| assists | cond | sim_challenger − sim_rotation | -0.0058 | [-0.0088, -0.0032] | -0.0020 | [-0.0039, -0.0004] | -0.0001 | [-0.0007, +0.0005] |
| threes | unc | sim_rotation − ewm5 | +0.0020 | [-0.0023, +0.0060] | -0.0075 | [-0.0106, -0.0045] | -0.0020 | [-0.0036, -0.0004] |
| threes | unc | sim_waterfill − sim_rotation | +0.0200 | [+0.0161, +0.0239] | -0.0001 | [-0.0029, +0.0030] | -0.0009 | [-0.0026, +0.0007] |
| threes | unc | sim_challenger − sim_rotation | -0.0013 | [-0.0020, -0.0007] | -0.0005 | [-0.0009, +0.0000] | -0.0003 | [-0.0005, -0.0001] |
| threes | cond | sim_rotation − ewm5 | +0.0163 | [+0.0099, +0.0225] | -0.0020 | [-0.0065, +0.0020] | +0.0013 | [-0.0009, +0.0034] |
| threes | cond | sim_waterfill − sim_rotation | -0.0167 | [-0.0217, -0.0119] | +0.0021 | [-0.0010, +0.0056] | -0.0014 | [-0.0030, +0.0002] |
| threes | cond | sim_challenger − sim_rotation | -0.0019 | [-0.0030, -0.0010] | -0.0010 | [-0.0017, -0.0002] | -0.0005 | [-0.0009, -0.0002] |

### Participation (all 14,763 eligible player-games)

Actual play rate 0.697, actual ≥10-min rate 0.6136.

| arm | mean P(play) | Brier P(play) | mean P(≥10 min) | Brier P(≥10 min) |
|---|---:|---:|---:|---:|
| ewm5 | 0.6805 | 0.166 | 0.5998 | 0.1587 |
| sim_rotation | 0.7045 | 0.1523 | 0.6097 | 0.152 |
| sim_challenger | 0.7045 | 0.1523 | 0.6097 | 0.152 |
| sim_waterfill | 0.8676 | 0.1893 | 0.7162 | 0.1539 |

- brier_play: sim_rotation − ewm5 = -0.0137 [-0.0163, -0.0111]
- brier_10min: sim_rotation − ewm5 = -0.0067 [-0.0086, -0.0049]
- brier_play: sim_waterfill − sim_rotation = +0.0371 [+0.0322, +0.0420]
- brier_10min: sim_waterfill − sim_rotation = +0.0020 [-0.0006, +0.0045]
- brier_play: sim_challenger − sim_rotation = +0.0000 [+0.0000, +0.0000]
- brier_10min: sim_challenger − sim_rotation = +0.0000 [-0.0000, +0.0000]

### Decomposition, full eligible population: Σpred/Σactual = F_participation × F_minutes|play × F_rate

| arm | stat | ratio | F_participation | F_minutes\|play | F_rate |
|---|---|---|---|---|---|
| ewm5 | points | 0.954 [0.946, 0.962] | 0.985 [0.975, 0.995] | 0.957 [0.949, 0.964] | 1.013 [1.003, 1.023] |
| ewm5 | rebounds | 0.969 [0.959, 0.979] | 0.977 [0.968, 0.987] | 0.959 [0.951, 0.966] | 1.035 [1.025, 1.046] |
| ewm5 | assists | 0.957 [0.945, 0.970] | 0.979 [0.968, 0.990] | 0.957 [0.949, 0.964] | 1.022 [1.007, 1.037] |
| ewm5 | threes | 0.957 [0.939, 0.975] | 0.981 [0.970, 0.991] | 0.956 [0.948, 0.964] | 1.021 [1.002, 1.040] |
| sim_rotation | points | 1.007 [0.999, 1.014] | 1.053 [1.044, 1.063] | 0.979 [0.971, 0.986] | 0.977 [0.969, 0.985] |
| sim_rotation | rebounds | 1.056 [1.045, 1.066] | 1.043 [1.034, 1.053] | 0.984 [0.975, 0.991] | 1.029 [1.020, 1.039] |
| sim_rotation | assists | 0.979 [0.967, 0.992] | 1.051 [1.041, 1.061] | 0.977 [0.970, 0.984] | 0.953 [0.941, 0.966] |
| sim_rotation | threes | 1.026 [1.008, 1.044] | 1.050 [1.040, 1.060] | 0.985 [0.977, 0.993] | 0.993 [0.975, 1.010] |
| sim_challenger | points | 1.007 [0.999, 1.014] | 1.053 [1.044, 1.063] | 0.978 [0.970, 0.985] | 0.977 [0.969, 0.985] |
| sim_challenger | rebounds | 1.056 [1.045, 1.067] | 1.044 [1.034, 1.054] | 0.984 [0.975, 0.991] | 1.029 [1.020, 1.039] |
| sim_challenger | assists | 0.979 [0.967, 0.991] | 1.051 [1.041, 1.062] | 0.976 [0.969, 0.983] | 0.954 [0.941, 0.967] |
| sim_challenger | threes | 1.027 [1.008, 1.045] | 1.050 [1.039, 1.060] | 0.984 [0.976, 0.992] | 0.995 [0.977, 1.012] |
| sim_waterfill | points | 1.006 [0.999, 1.014] | 1.200 [1.187, 1.213] | 0.858 [0.851, 0.865] | 0.978 [0.970, 0.986] |
| sim_waterfill | rebounds | 1.055 [1.045, 1.066] | 1.197 [1.185, 1.210] | 0.859 [0.852, 0.866] | 1.026 [1.017, 1.037] |
| sim_waterfill | assists | 0.978 [0.966, 0.991] | 1.197 [1.184, 1.211] | 0.858 [0.851, 0.865] | 0.953 [0.940, 0.965] |
| sim_waterfill | threes | 1.019 [1.000, 1.038] | 1.197 [1.184, 1.209] | 0.858 [0.850, 0.865] | 0.993 [0.976, 1.011] |

### Per played minute, predicted/actual (actually-played rows, actual-minute weighted)

| arm | fga | fg3a | fta | tov | usage | pts | reb | ast | fg3m | pts/shooting poss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ewm5 | 1.020 [1.013, 1.028] | 1.024 [1.013, 1.034] | 1.010 [0.988, 1.032] | 1.030 [1.009, 1.050] | 1.020 [1.014, 1.027] | 1.013 [1.003, 1.023] | 1.035 [1.025, 1.046] | 1.022 [1.007, 1.037] | 1.021 [1.002, 1.040] | 0.993 [0.986, 1.001] |
| sim_rotation | 0.965 [0.960, 0.971] | 0.969 [0.959, 0.979] | 0.947 [0.928, 0.967] | 1.040 [1.020, 1.060] | 0.973 [0.967, 0.978] | 0.977 [0.969, 0.985] | 1.029 [1.020, 1.039] | 0.953 [0.941, 0.966] | 0.993 [0.975, 1.010] | 1.015 [1.008, 1.022] |
| sim_challenger | 0.966 [0.960, 0.972] | 0.971 [0.961, 0.981] | 0.948 [0.929, 0.968] | 1.040 [1.020, 1.060] | 0.973 [0.968, 0.979] | 0.977 [0.969, 0.985] | 1.029 [1.020, 1.039] | 0.954 [0.941, 0.967] | 0.995 [0.977, 1.012] | 1.015 [1.008, 1.022] |
| sim_waterfill | 0.967 [0.961, 0.973] | 0.970 [0.960, 0.981] | 0.949 [0.930, 0.969] | 1.037 [1.016, 1.056] | 0.974 [0.968, 0.979] | 0.978 [0.970, 0.986] | 1.026 [1.017, 1.037] | 0.953 [0.940, 0.965] | 0.993 [0.976, 1.011] | 1.015 [1.008, 1.022] |

By the arm's own pre-tip FGA-per-minute tercile (points / FGA / assists):

| arm | low | mid | high |
|---|---|---|---|
| ewm5 | 0.916 / 0.936 / 0.966 | 0.999 / 1.005 / 1.033 | 1.058 / 1.062 / 1.041 |
| sim_rotation | 1.012 / 1.014 / 0.962 | 0.978 / 0.960 / 0.980 | 0.962 / 0.949 / 0.934 |
| sim_challenger | 0.978 / 0.980 / 0.938 | 0.976 / 0.959 / 0.985 | 0.977 / 0.965 / 0.943 |
| sim_waterfill | 1.014 / 1.015 / 0.959 | 0.974 / 0.957 / 0.977 | 0.966 / 0.953 / 0.936 |

### Observation choice: Σ unconditional forecast / Σ actual, points (and minutes)

| frame | n | ewm5 pts | sim_rotation pts | sim_rotation minutes |
|---|---:|---|---|---|
| A full eligible population (pre-tip) | 14763 | 0.954 [0.946, 0.962] | 1.007 [0.999, 1.014] | 1.027 [1.023, 1.031] |
| B predicted starters (pre-tip) | 5707 | 1.010 [0.990, 1.030] | 1.013 [0.994, 1.032] | 1.042 [1.023, 1.060] |
| C sim predicts >=28 min given play (pre-tip) | 3211 | 1.006 [0.986, 1.027] | 1.046 [1.025, 1.067] | 1.077 [1.059, 1.096] |
| D actually played (outcome-selected) | 10290 | 0.766 [0.754, 0.777] | 0.838 [0.827, 0.848] | 0.858 [0.850, 0.865] |
| E actually >=28 min (outcome-selected) | 3637 | 0.705 [0.692, 0.719] | 0.747 [0.734, 0.759] | 0.775 [0.764, 0.784] |
| F has a listed player-prop contract (selection by listing; diagnostic only) | 3146 | 0.862 [0.845, 0.878] | 0.896 [0.880, 0.914] | 0.934 [0.919, 0.949] |
| G listed AND actually played (selection by listing + outcome) | 2980 | 0.819 [0.806, 0.833] | 0.851 [0.836, 0.866] | 0.888 [0.877, 0.899] |

### Strata depth (pre-tip): decomposition ratio for points

| stratum | ewm5 | sim_rotation | sim_challenger |
|---|---|---|---|
| pred_starter (p_start>=0.5) | 1.010 | 1.013 | 1.016 |
| pred_bench (p_start<0.5) | 0.873 | 0.998 | 0.993 |
| usage_low (ewm5 FGA/min<0.292) | 0.830 | 0.999 | 0.963 |
| usage_mid | 0.924 | 1.020 | 1.017 |
| usage_high (ewm5 FGA/min>=0.392) | 1.014 | 1.001 | 1.014 |

`t_ref` = the fixed-ladder rung nearest the EWM-5 conditional mean, the same for every arm. The CRPS
column is the exact sample CRPS (2,000 draws). The shared gate's 3-quantile CRPS approximation has
a points ΔCRPS for the challenger of −0.0027 with CI [−0.0064, +0.0009], so the CRPS gain is not
robust to the approximation. The preregistered metric is the exact one.

The challenger moves two other metrics with CIs excluding zero: threes p10–p90 coverage −0.0012 (unc) /
−0.0020 (cond), and threes mean bias +0.0007 / +0.0012. Rule 4 is written on MAE and CRPS; under that literal wording the challenger passed. At review (2026-10-11) the
stricter any-metric reading was applied, so the final verdict is **REJECTED** (see Verdicts). For future NBA
experiments, rule 4 should state explicitly that coverage and bias regressions with CIs excluding zero also fail.

## DEV (descriptive; `w1_nba/scorecard_dev.json`)

1,599 games, 46,713 player-games (2024-25: 30,984; 2025-26: 15,729). The champion's points ratio is
1.000 [0.996, 1.004]. Its decomposition is 1.034 × 0.979 × 0.989, and its own-usage tercile rates
(points) are 1.038 / 0.995 / 0.967. The holdout pattern was already present on DEV.

## Reproduce

```
OUT=$SCRATCH/nba/hold
python scripts/nba_matched_decomposition.py collect --window holdout --player-prior-minutes 5 \
    --arms ewm5,sim_rotation,sim_waterfill --out $OUT                                     # ~10 min, 1 CPU
python scripts/nba_listed_population_diagnostic.py --out $OUT/listed.parquet             # diagnostic keys only
python scripts/nba_matched_decomposition.py report --window holdout --out $OUT \
    --usage-cuts 0.2920,0.3922 --listed $OUT/listed.parquet --json docs/research/w1_nba/scorecard_holdout.json
python scripts/nba_matched_decomposition.py sidecars --window holdout --out $OUT \
    --arms ewm5,sim_rotation,sim_challenger [--schema v1] [--sample-games 20 --dest docs/research/w1_nba/sidecars_sample]
python scripts/nba_pure_mutation_test.py --work $SCRATCH/nba/mutation --games 20 --sims 600 \
    --kit $KIT/scripts/prop_projection_gate.py --json docs/research/w1_nba/pure_mutation_test.json
```

Seeds are sha256(game_id). Full sidecars are about 3 MB gzip per arm and conditionality. They are
regenerated by the command above, and a 20-game sample is committed in `w1_nba/sidecars_sample/`.

## Limits

- There is no point-in-time injury history, so every arm uses the participation proxy. The listing
  frame shows what that costs.
- `ROTATION_SIZE_PMF` and the rotation validation used 2023-24..2025-26, which includes the holdout
  season. That is pre-existing champion contamination, disclosed here and not fixed.
- The simulator's 3PA is derived as three_share × FGA, because the engine does not export 3PA.
- 28 holdout rows (14 player-games, counted on both teams) were excluded. These are players eligible for
  both teams after a trade between the opponents. In these games the champion's `SimResult.players`,
  which is keyed by player id alone, lets one team's copy overwrite the other's. This is a real defect,
  and it is reported rather than fixed here.
- Non-eligible participants (call-ups, returns from long absence) account for 2.5% of holdout minutes
  and 2.2% of points. They are excluded from the population and counted.
