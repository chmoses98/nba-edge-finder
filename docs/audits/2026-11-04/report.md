# NBA all-market audit — 2026-11-04 (ET) — **OK**

RESEARCH_ONLY. Hypothetical taker economics; no fills.


## Coverage
universe **12179** = graded **8307** + ungraded **3872**

- ungraded `no_settlement_record`: 92
- ungraded `settlement_unsettleable:dnp:_consult_kalshi_rules/result`: 30
- ungraded `settlement_unsettleable:player_not_in_box_score`: 126
- ungraded `settlement_unsettleable:semantics_not_proven`: 98
- ungraded `settlement_unsettleable:semantics_not_proven|points_leader_no_model_probability`: 199
- ungraded `settlement_unsettleable:semantics_not_proven|protected_prop_needs_period_participation`: 2900
- ungraded `settlement_unsettleable:semantics_not_proven|race_to_no_model_probability`: 84
- ungraded `settlement_unsettleable:semantics_not_proven|scalar_payout_formula_not_binary`: 134
- ungraded `settlement_unsettleable:semantics_not_proven|win_margin_bucket_settleable_from_final_score_no_model_probability`: 112
- ungraded `settlement_unsettleable:tie_semantics_unknown`: 10
- ungraded `settlement_unsettleable:unsupported_player_stat_stocks`: 87
- refused: {'prediction_at_or_after_tip': 0, 'no_model_probability': 58739, 'no_board_before_prediction': 0}

## Family performance (latest pre-tip forecast per ticker; 🟢 model beats market, 🔴 market beats model — both only when the game-clustered CI excludes 0 and BH q<0.10 across families; 🟡 inconclusive; ⚪ no market)

| family | n | games | p̄ | base | Brier model | Brier mkt | mkt−model (95% CI) | q(BH) | skill | +EV picks | ROI after fee (95% CI) | CLV exec | CLV sel |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| game_spread | 462 | 14 | 0.341 | 0.219 | 0.1598 | 0.1399 | -0.0240 [-0.077, 0.028] | 0.488 | 🟡 | 406 | 0.0654 [-0.2, 0.363] | -0.0008 | 0.0004 |
| game_total | 406 | 14 | 0.483 | 0.466 | 0.1440 | 0.1109 | -0.0331 [-0.053, -0.016] | 0.009 | 🔴 | 338 | -0.3877 [-0.59, -0.206] | -0.0033 | -0.0024 |
| game_winner | 28 | 14 | 0.500 | 0.500 | 0.2028 | 0.1913 | -0.0115 [-0.093, 0.063] | 0.836 | 🟡 | 26 | 0.1430 [-0.248, 0.54] | 0.0004 | 0.0004 |
| period_spread | 1260 | 14 | 0.306 | 0.252 | 0.1775 | 0.1724 | -0.0077 [-0.017, 0.0] | 0.142 | 🟡 | 826 | -0.1020 [-0.253, 0.05] | -0.0064 | 0.0001 |
| period_team_total | 308 | 14 | 0.509 | 0.539 | 0.1870 | 0.1869 | -0.0035 [-0.027, 0.017] | 0.832 | 🟡 | 133 | -0.0403 [-0.379, 0.329] | -0.0147 | 0.0016 |
| period_total | 1260 | 14 | 0.489 | 0.475 | 0.1818 | 0.1683 | -0.0170 [-0.034, 0.002] | 0.142 | 🟡 | 773 | -0.2725 [-0.591, 0.073] | -0.0056 | 0.0031 |
| period_winner | 158 | 14 | 0.485 | 0.500 | 0.2501 | 0.2459 | -0.0042 [-0.022, 0.021] | 0.722 | 🟡 | 92 | -0.0221 [-0.235, 0.26] | -0.0053 | 0.0007 |
| player_assists | 544 | 14 | 0.363 | 0.399 | 0.1519 | 0.1541 | -0.0087 [-0.02, 0.003] | 0.215 | 🟡 | 320 | -0.0406 [-0.176, 0.094] | 0.0012 | 0.0030 |
| player_blocks | 140 | 14 | 0.278 | 0.421 | 0.2350 | 0.2209 | -0.0226 [-0.055, 0.001] | 0.142 | 🟡 | 69 | -0.2071 [-0.57, 0.038] | 0.0043 | 0.0041 |
| player_double_double | 168 | 14 | 0.117 | 0.143 | 0.0887 | 0.1024 | -0.0061 [-0.011, -0.001] | 0.109 | 🟡 | 86 | -0.0371 [-0.121, 0.059] | -0.0005 | 0.0081 |
| player_points | 660 | 14 | 0.359 | 0.380 | 0.1663 | 0.1522 | -0.0177 [-0.029, -0.006] | 0.043 | 🔴 | 500 | -0.1213 [-0.22, -0.023] | 0.0019 | 0.0022 |
| player_pra | 481 | 14 | 0.457 | 0.478 | 0.2213 | 0.2039 | -0.0163 [-0.037, 0.005] | 0.206 | 🟡 | 275 | -0.0997 [-0.272, 0.056] | 0.0004 | 0.0023 |
| player_rebounds | 793 | 14 | 0.463 | 0.470 | 0.1740 | 0.1700 | -0.0089 [-0.018, 0.0] | 0.142 | 🟡 | 522 | -0.0513 [-0.162, 0.048] | -0.0011 | -0.0015 |
| player_steals | 257 | 14 | 0.349 | 0.362 | 0.1773 | 0.1723 | -0.0065 [-0.018, 0.004] | 0.272 | 🟡 | 117 | -0.1311 [-0.33, -0.001] | 0.0068 | 0.0053 |
| player_threes | 794 | 14 | 0.342 | 0.341 | 0.1542 | 0.1649 | -0.0117 [-0.021, -0.003] | 0.043 | 🔴 | 445 | -0.1630 [-0.246, -0.082] | 0.0005 | 0.0022 |
| player_triple_double | 56 | 14 | 0.011 | 0.036 | 0.0277 | 0.0980 | -0.0210 [-0.051, 0.001] | 0.272 | 🟡 | 12 | -0.0362 [-0.163, 0.025] | 0.0008 | 0.0025 |
| team_total | 532 | 14 | 0.489 | 0.476 | 0.1506 | 0.1215 | -0.0292 [-0.051, -0.009] | 0.017 | 🔴 | 400 | -0.1536 [-0.361, 0.06] | -0.0059 | -0.0014 |

## By time before tip (all horizons; rows are NOT independent)

| horizon | n | Brier model | Brier mkt | skill | +EV picks | ROI |
|---|---|---|---|---|---|---|
| 1-3h | 13831 | 0.1724 | 0.1652 | 🔴 | 8823 | -0.1079 |
| 3-6h | 24091 | 0.1726 | 0.1657 | 🔴 | 14652 | -0.1177 |
| 6-24h | 98554 | 0.1724 | 0.1714 | 🔴 | 48019 | -0.1237 |
| <1h | 4733 | 0.1723 | 0.1666 | 🟡 | 3249 | -0.0836 |

## By game

| game_id | n | Brier model | Brier mkt | skill | +EV picks | ROI |
|---|---|---|---|---|---|---|
| espn:401909922 | 607 | 0.1816 | 0.1691 | 🟡 | 447 | -0.1504 |
| espn:401909923 | 605 | 0.1415 | 0.1525 | 🟡 | 381 | 0.0016 |
| espn:401909924 | 649 | 0.2008 | 0.1747 | 🟡 | 458 | -0.1447 |
| espn:401909925 | 596 | 0.1931 | 0.1620 | 🟡 | 431 | -0.2404 |
| espn:401909926 | 597 | 0.1432 | 0.1771 | 🟡 | 452 | 0.2713 |
| espn:401909927 | 540 | 0.1736 | 0.1638 | 🟡 | 344 | -0.1844 |
| espn:401909928 | 552 | 0.1739 | 0.1630 | 🟡 | 378 | -0.1958 |
| espn:401909929 | 587 | 0.1686 | 0.1685 | 🟡 | 358 | -0.0996 |
| espn:401909930 | 582 | 0.1498 | 0.1563 | 🟡 | 344 | 0.0549 |
| espn:401909931 | 555 | 0.1581 | 0.1670 | 🟡 | 278 | 0.1283 |
| espn:401909932 | 586 | 0.1954 | 0.1665 | 🟡 | 372 | -0.4147 |
| espn:401909933 | 622 | 0.1952 | 0.1680 | 🟡 | 374 | -0.3406 |
| espn:401909934 | 548 | 0.1437 | 0.1244 | 🟡 | 351 | -0.3311 |
| espn:401909935 | 681 | 0.1719 | 0.1647 | 🟡 | 372 | -0.0738 |

## By model-probability bin

| price_bin | n | Brier model | Brier mkt | skill | +EV picks | ROI |
|---|---|---|---|---|---|---|
| 0-10 | 1080 | 0.0573 | 0.0698 | 🟡 | 481 | -0.0001 |
| 10-25 | 1917 | 0.1388 | 0.1322 | 🔴 | 1200 | -0.1481 |
| 25-40 | 1587 | 0.2081 | 0.1961 | 🔴 | 1131 | -0.0925 |
| 40-60 | 1615 | 0.2460 | 0.2224 | 🔴 | 1172 | -0.1725 |
| 60-75 | 1029 | 0.2163 | 0.1884 | 🔴 | 717 | -0.2111 |
| 75-90 | 838 | 0.1490 | 0.1335 | 🟡 | 487 | -0.1592 |
| 90-100 | 241 | 0.0797 | 0.0805 | 🟡 | 152 | -0.0101 |

## Not evaluated
- injury-status and participation splits (needs injury snapshot join per horizon)
- actual-fill CLV (no fill evidence in archive)
- multiple-comparison control (descriptive only; no promotion claims)
