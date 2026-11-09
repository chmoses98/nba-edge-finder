# NBA all-market audit — 2026-11-08 (ET) — **OK**

RESEARCH_ONLY. Hypothetical taker economics; no fills.


## Coverage
universe **6271** = graded **4112** + ungraded **2159**

- ungraded `no_settlement_record`: 25
- ungraded `settlement_unsettleable:player_not_in_box_score`: 90
- ungraded `settlement_unsettleable:semantics_not_proven`: 49
- ungraded `settlement_unsettleable:semantics_not_proven|points_leader_no_model_probability`: 92
- ungraded `settlement_unsettleable:semantics_not_proven|protected_prop_needs_period_participation`: 1691
- ungraded `settlement_unsettleable:semantics_not_proven|race_to_no_model_probability`: 42
- ungraded `settlement_unsettleable:semantics_not_proven|scalar_payout_formula_not_binary`: 68
- ungraded `settlement_unsettleable:semantics_not_proven|win_margin_bucket_settleable_from_final_score_no_model_probability`: 56
- ungraded `settlement_unsettleable:tie_semantics_unknown`: 6
- ungraded `settlement_unsettleable:unsupported_player_stat_stocks`: 40
- refused: {'prediction_at_or_after_tip': 0, 'no_model_probability': 29066, 'no_board_before_prediction': 0}

## Family performance (latest pre-tip forecast per ticker; 🟢 model beats market, 🔴 market beats model — both only when the game-clustered CI excludes 0 and BH q<0.10 across families; 🟡 inconclusive; ⚪ no market)

| family | n | games | p̄ | base | Brier model | Brier mkt | mkt−model (95% CI) | q(BH) | skill | +EV picks | ROI after fee (95% CI) | CLV exec | CLV sel |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| game_spread | 231 | 7 | 0.363 | 0.329 | 0.1298 | 0.1616 | 0.0295 [-0.011, 0.073] | 0.489 | 🟡 | 196 | 0.3822 [-0.115, 0.814] | -0.0021 | -0.0003 |
| game_total | 203 | 7 | 0.517 | 0.552 | 0.1808 | 0.1510 | -0.0298 [-0.075, 0.02] | 0.489 | 🟡 | 193 | -0.0236 [-0.39, 0.478] | -0.0055 | -0.0044 |
| game_winner | 14 | 7 | 0.500 | 0.500 | 0.1023 | 0.1369 | 0.0345 [-0.008, 0.088] | 0.469 | 🟡 | 12 | 0.4231 [0.05, 0.991] | 0.0025 | 0.0025 |
| period_spread | 630 | 7 | 0.309 | 0.214 | 0.1332 | 0.1297 | -0.0035 [-0.019, 0.016] | 0.712 | 🟡 | 476 | -0.0332 [-0.479, 0.447] | -0.0029 | -0.0005 |
| period_team_total | 154 | 7 | 0.449 | 0.494 | 0.1685 | 0.1530 | -0.0155 [-0.045, 0.01] | 0.489 | 🟡 | 86 | -0.2283 [-0.601, 0.135] | -0.0114 | -0.0004 |
| period_total | 630 | 7 | 0.497 | 0.541 | 0.1633 | 0.1478 | -0.0136 [-0.041, 0.014] | 0.489 | 🟡 | 463 | -0.1099 [-0.481, 0.288] | -0.0030 | 0.0019 |
| period_winner | 78 | 7 | 0.485 | 0.500 | 0.1793 | 0.1935 | 0.0143 [0.0, 0.034] | 0.208 | 🟡 | 38 | 0.4129 [-0.029, 0.707] | -0.0053 | -0.0017 |
| player_assists | 301 | 7 | 0.349 | 0.389 | 0.1407 | 0.1384 | -0.0037 [-0.017, 0.009] | 0.712 | 🟡 | 197 | -0.0793 [-0.235, 0.102] | 0.0005 | 0.0005 |
| player_blocks | 63 | 7 | 0.298 | 0.286 | 0.1899 | 0.1966 | 0.0067 [-0.031, 0.037] | 0.712 | 🟡 | 40 | 0.1205 [-0.119, 0.392] | 0.0068 | 0.0039 |
| player_double_double | 76 | 7 | 0.116 | 0.118 | 0.0772 | 0.0678 | -0.0094 [-0.027, 0.007] | 0.489 | 🟡 | 50 | -0.0822 [-0.289, 0.102] | -0.0022 | 0.0056 |
| player_points | 314 | 7 | 0.363 | 0.373 | 0.1992 | 0.1728 | -0.0264 [-0.054, -0.0] | 0.208 | 🟡 | 272 | -0.0272 [-0.199, 0.146] | 0.0004 | -0.0003 |
| player_pra | 257 | 7 | 0.469 | 0.506 | 0.2237 | 0.2084 | -0.0154 [-0.047, 0.01] | 0.489 | 🟡 | 212 | 0.0464 [-0.101, 0.187] | 0.0058 | 0.0002 |
| player_rebounds | 372 | 7 | 0.462 | 0.409 | 0.1555 | 0.1457 | -0.0098 [-0.018, -0.002] | 0.119 | 🟡 | 280 | 0.0277 [-0.055, 0.111] | 0.0006 | 0.0026 |
| player_steals | 124 | 7 | 0.352 | 0.395 | 0.1880 | 0.1863 | -0.0017 [-0.02, 0.017] | 0.856 | 🟡 | 78 | -0.0005 [-0.244, 0.155] | 0.0213 | 0.0116 |
| player_threes | 369 | 7 | 0.361 | 0.371 | 0.1570 | 0.1570 | -0.0026 [-0.008, 0.002] | 0.489 | 🟡 | 270 | -0.0097 [-0.111, 0.084] | 0.0029 | 0.0026 |
| player_triple_double | 30 | 7 | 0.008 | 0.000 | 0.0004 | 0.0010 | 0.0005 [0.0, 0.002] | 0.208 | 🟡 | 24 | 0.0098 [0.004, 0.019] | -0.0004 | -0.0008 |
| team_total | 266 | 7 | 0.517 | 0.549 | 0.1567 | 0.1477 | -0.0090 [-0.043, 0.026] | 0.712 | 🟡 | 213 | 0.0045 [-0.269, 0.37] | -0.0029 | -0.0026 |

## By time before tip (all horizons; rows are NOT independent)

| horizon | n | Brier model | Brier mkt | skill | +EV picks | ROI |
|---|---|---|---|---|---|---|
| 1-3h | 7539 | 0.1600 | 0.1552 | 🟡 | 5597 | 0.0307 |
| 3-6h | 11968 | 0.1595 | 0.1523 | 🟡 | 8211 | -0.0145 |
| 6-24h | 42100 | 0.1597 | 0.1560 | 🟡 | 22874 | -0.0476 |
| <1h | 4112 | 0.1595 | 0.1521 | 🟡 | 3100 | 0.0049 |

## By game

| game_id | n | Brier model | Brier mkt | skill | +EV picks | ROI |
|---|---|---|---|---|---|---|
| espn:401909945 | 585 | 0.1528 | 0.1202 | 🟡 | 426 | -0.2727 |
| espn:401909946 | 617 | 0.1756 | 0.1896 | 🟡 | 442 | 0.2553 |
| espn:401909947 | 556 | 0.1447 | 0.1185 | 🟡 | 421 | -0.1656 |
| espn:401909948 | 571 | 0.1551 | 0.1672 | 🟡 | 433 | 0.1980 |
| espn:401909949 | 588 | 0.1504 | 0.1425 | 🟡 | 451 | 0.0812 |
| espn:401909950 | 625 | 0.1539 | 0.1794 | 🟡 | 484 | 0.3340 |
| espn:401909951 | 570 | 0.1833 | 0.1426 | 🟡 | 443 | -0.4477 |

## By model-probability bin

| price_bin | n | Brier model | Brier mkt | skill | +EV picks | ROI |
|---|---|---|---|---|---|---|
| 0-10 | 511 | 0.0569 | 0.0514 | 🟡 | 315 | -0.0002 |
| 10-25 | 955 | 0.1228 | 0.1146 | 🟡 | 757 | -0.0357 |
| 25-40 | 765 | 0.1987 | 0.1922 | 🟡 | 610 | 0.0300 |
| 40-60 | 821 | 0.2491 | 0.2345 | 🟡 | 661 | 0.0468 |
| 60-75 | 508 | 0.1983 | 0.1912 | 🟡 | 389 | 0.0121 |
| 75-90 | 424 | 0.1079 | 0.1011 | 🟡 | 285 | -0.0672 |
| 90-100 | 128 | 0.0512 | 0.0564 | 🟡 | 83 | 0.0492 |

## Not evaluated
- injury-status and participation splits (needs injury snapshot join per horizon)
- actual-fill CLV (no fill evidence in archive)
- multiple-comparison control (descriptive only; no promotion claims)
