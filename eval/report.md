# Evaluation report (2026-11-13T04:30:14Z)

rows=1648891 pregame=1648891 new_this_run=24422

## game_spread

n=137265 pregame=137265 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 137265 | 0.2033 | 0.6081 | 0.0963 | -0.2980 | -0.0025 |
| MARKET_BASELINE | 1687 | 0.1784 | 0.5559 | 0.0755 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 5590 | 0.2064 | 0.4282 | -0.0076 |
| DATA_ONLY | 1-6h | 33457 | 0.2053 | -0.4121 | -0.0100 |
| DATA_ONLY | 6-24h | 98218 | 0.2025 | -0.2938 | 0.0004 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 33 | 0.3245 | - | - |
| MARKET_BASELINE | 1-6h | 456 | 0.1664 | - | - |
| MARKET_BASELINE | 6-24h | 1198 | 0.1789 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## game_total

n=119437 pregame=119437 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 119437 | 0.1785 | 0.5338 | 0.0152 | -0.2323 | -0.0297 |
| MARKET_BASELINE | 1508 | 0.1756 | 0.5337 | 0.2324 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 4862 | 0.1782 | -0.1635 | -0.0074 |
| DATA_ONLY | 1-6h | 29101 | 0.1788 | -0.2741 | -0.0183 |
| DATA_ONLY | 6-24h | 85474 | 0.1784 | -0.2169 | -0.0347 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 29 | 0.0682 | - | - |
| MARKET_BASELINE | 1-6h | 406 | 0.1794 | - | - |
| MARKET_BASELINE | 6-24h | 1073 | 0.1770 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## game_winner

n=8954 pregame=8954 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 8954 | 0.2434 | 0.7096 | 0.1101 | -0.5540 | 0.0072 |
| MARKET_BASELINE | 104 | 0.0723 | 0.3077 | 0.2625 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 364 | 0.2342 | 0.6113 | -0.0050 |
| DATA_ONLY | 1-6h | 2178 | 0.2454 | -0.5763 | -0.0089 |
| DATA_ONLY | 6-24h | 6412 | 0.2433 | -0.5953 | 0.0136 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 2 | 0.1122 | - | - |
| MARKET_BASELINE | 1-6h | 28 | 0.0753 | - | - |
| MARKET_BASELINE | 6-24h | 74 | 0.0701 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## period_spread

n=263590 pregame=263590 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 263590 | 0.1742 | 0.5261 | 0.0513 | -0.0960 | -0.0343 |
| MARKET_BASELINE | 3225 | 0.1520 | 0.4686 | 0.0278 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 12315 | 0.1764 | 0.2345 | -0.0237 |
| DATA_ONLY | 1-6h | 71512 | 0.1748 | -0.1298 | -0.0279 |
| DATA_ONLY | 6-24h | 179763 | 0.1738 | -0.0967 | -0.0391 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 90 | 0.2188 | - | - |
| MARKET_BASELINE | 1-6h | 1260 | 0.1484 | - | - |
| MARKET_BASELINE | 6-24h | 1875 | 0.1512 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## period_team_total

n=65802 pregame=65802 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 65802 | 0.1861 | 0.5546 | 0.0432 | -0.0760 | -0.0869 |
| MARKET_BASELINE | 772 | 0.1829 | 0.5412 | 0.2316 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 2860 | 0.1867 | 0.0737 | -0.0334 |
| DATA_ONLY | 1-6h | 17138 | 0.1862 | -0.1707 | -0.0492 |
| DATA_ONLY | 6-24h | 45804 | 0.1861 | -0.0250 | -0.1158 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 22 | 0.1646 | - | - |
| MARKET_BASELINE | 1-6h | 308 | 0.1684 | - | - |
| MARKET_BASELINE | 6-24h | 442 | 0.1938 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## period_total

n=260386 pregame=260386 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 260386 | 0.1727 | 0.5226 | 0.0419 | -0.2256 | -0.0525 |
| MARKET_BASELINE | 3320 | 0.1281 | 0.4091 | 0.1673 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 12250 | 0.1729 | -0.4378 | -0.0308 |
| DATA_ONLY | 1-6h | 71403 | 0.1724 | -0.2899 | -0.0334 |
| DATA_ONLY | 6-24h | 176733 | 0.1728 | -0.1829 | -0.0655 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 90 | 0.0812 | - | - |
| MARKET_BASELINE | 1-6h | 1251 | 0.1216 | - | - |
| MARKET_BASELINE | 6-24h | 1979 | 0.1343 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## period_winner

n=39398 pregame=39398 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 39398 | 0.2439 | 0.6817 | 0.0385 | -0.0526 | -0.0706 |
| MARKET_BASELINE | 590 | 0.1985 | 0.5878 | 0.1813 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 1602 | 0.2384 | 0.2211 | -0.0175 |
| DATA_ONLY | 1-6h | 9536 | 0.2439 | -0.0680 | -0.0304 |
| DATA_ONLY | 6-24h | 28260 | 0.2442 | -0.0538 | -0.0872 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 12 | 0.1801 | - | - |
| MARKET_BASELINE | 1-6h | 158 | 0.2020 | - | - |
| MARKET_BASELINE | 6-24h | 420 | 0.1977 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_assists

n=100659 pregame=100659 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 100081 | 0.1571 | 0.4816 | 0.0636 | -0.1449 | -0.0190 |
| MARKET_BASELINE | 1579 | 0.1879 | 0.5658 | 0.0974 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 5105 | 0.1521 | 0.0305 | -0.0147 |
| DATA_ONLY | 1-6h | 28261 | 0.1568 | -0.1605 | -0.0031 |
| DATA_ONLY | 6-24h | 66715 | 0.1577 | -0.1449 | -0.0281 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 55 | 0.1636 | - | - |
| MARKET_BASELINE | 1-6h | 542 | 0.1843 | - | - |
| MARKET_BASELINE | 6-24h | 982 | 0.1913 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_blocks

n=18108 pregame=18108 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 18060 | 0.2052 | 0.6062 | 0.0957 | -0.0051 | -0.0332 |
| MARKET_BASELINE | 271 | 0.2025 | 0.6016 | 0.1241 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 1265 | 0.1860 | -0.1232 | -0.0180 |
| DATA_ONLY | 1-6h | 6397 | 0.2003 | -0.0166 | -0.0181 |
| DATA_ONLY | 6-24h | 10398 | 0.2106 | 0.0150 | -0.0506 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 10 | 0.1688 | - | - |
| MARKET_BASELINE | 1-6h | 135 | 0.2038 | - | - |
| MARKET_BASELINE | 6-24h | 126 | 0.2038 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_double_double

n=17813 pregame=17813 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 17742 | 0.1348 | 0.5221 | 0.0557 | -0.1707 | -0.0304 |
| MARKET_BASELINE | 427 | 0.1247 | 0.3885 | 0.1128 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 991 | 0.1167 | -0.3431 | -0.0127 |
| DATA_ONLY | 1-6h | 5475 | 0.1277 | -0.1974 | -0.0179 |
| DATA_ONLY | 6-24h | 11276 | 0.1399 | -0.1540 | -0.0382 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 13 | 0.0168 | - | - |
| MARKET_BASELINE | 1-6h | 149 | 0.1306 | - | - |
| MARKET_BASELINE | 6-24h | 265 | 0.1267 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_points

n=116038 pregame=116038 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 115275 | 0.2158 | 0.7534 | 0.0806 | -0.0244 | -0.0223 |
| MARKET_BASELINE | 1766 | 0.1740 | 0.5303 | 0.0639 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 5661 | 0.2114 | 0.0617 | -0.0082 |
| DATA_ONLY | 1-6h | 31900 | 0.2131 | -0.0550 | -0.0082 |
| DATA_ONLY | 6-24h | 77714 | 0.2173 | -0.0102 | -0.0309 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 52 | 0.1545 | - | - |
| MARKET_BASELINE | 1-6h | 619 | 0.1777 | - | - |
| MARKET_BASELINE | 6-24h | 1095 | 0.1729 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_pra

n=63859 pregame=63859 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 63539 | 0.2650 | 0.9557 | 0.1211 | 0.0063 | -0.0466 |
| MARKET_BASELINE | 1395 | 0.2305 | 0.6550 | 0.0708 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 3474 | 0.2519 | 0.0897 | -0.0182 |
| DATA_ONLY | 1-6h | 18946 | 0.2591 | -0.0150 | -0.0229 |
| DATA_ONLY | 6-24h | 41119 | 0.2688 | 0.0133 | -0.0631 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 56 | 0.2248 | - | - |
| MARKET_BASELINE | 1-6h | 512 | 0.2222 | - | - |
| MARKET_BASELINE | 6-24h | 827 | 0.2360 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_rebounds

n=131634 pregame=131634 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 130920 | 0.2018 | 0.6804 | 0.0650 | -0.1592 | -0.0270 |
| MARKET_BASELINE | 1936 | 0.1811 | 0.5349 | 0.0657 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 6650 | 0.1948 | 0.0382 | -0.0132 |
| DATA_ONLY | 1-6h | 36930 | 0.1974 | -0.2109 | -0.0105 |
| DATA_ONLY | 6-24h | 87340 | 0.2043 | -0.1440 | -0.0372 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 71 | 0.2115 | - | - |
| MARKET_BASELINE | 1-6h | 678 | 0.1778 | - | - |
| MARKET_BASELINE | 6-24h | 1187 | 0.1811 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_steals

n=38099 pregame=38099 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 37883 | 0.1948 | 0.5766 | 0.0620 | 0.0115 | -0.0253 |
| MARKET_BASELINE | 576 | 0.1684 | 0.5095 | 0.1020 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 2385 | 0.1927 | 0.1455 | -0.0165 |
| DATA_ONLY | 1-6h | 13001 | 0.1927 | -0.0136 | -0.0132 |
| DATA_ONLY | 6-24h | 22497 | 0.1963 | 0.0287 | -0.0382 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 17 | 0.1553 | - | - |
| MARKET_BASELINE | 1-6h | 283 | 0.1652 | - | - |
| MARKET_BASELINE | 6-24h | 276 | 0.1726 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_threes

n=139136 pregame=139136 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 138311 | 0.1696 | 0.5282 | 0.0369 | -0.0499 | -0.0199 |
| MARKET_BASELINE | 1874 | 0.1486 | 0.4591 | 0.0609 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 6888 | 0.1700 | -0.0830 | -0.0132 |
| DATA_ONLY | 1-6h | 38410 | 0.1701 | -0.0662 | -0.0104 |
| DATA_ONLY | 6-24h | 93013 | 0.1694 | -0.0378 | -0.0260 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 61 | 0.1429 | - | - |
| MARKET_BASELINE | 1-6h | 682 | 0.1541 | - | - |
| MARKET_BASELINE | 6-24h | 1131 | 0.1456 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_triple_double

n=6277 pregame=6277 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 6227 | 0.0187 | 0.1165 | 0.0069 | -0.0361 | -0.0082 |
| MARKET_BASELINE | 45 | 0.1288 | 0.5436 | 0.1076 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 348 | 0.0097 | 0.8411 | -0.0050 |
| DATA_ONLY | 1-6h | 1979 | 0.0171 | -0.0203 | -0.0029 |
| DATA_ONLY | 6-24h | 3900 | 0.0203 | -0.0395 | -0.0133 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 1 | 0.0012 | - | - |
| MARKET_BASELINE | 1-6h | 21 | 0.0469 | - | - |
| MARKET_BASELINE | 6-24h | 23 | 0.2090 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## team_total

n=122436 pregame=122436 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 122436 | 0.1746 | 0.5265 | 0.0188 | -0.0341 | -0.0211 |
| MARKET_BASELINE | 1976 | 0.2382 | 0.6887 | 0.2162 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 4940 | 0.1714 | 0.2884 | -0.0091 |
| DATA_ONLY | 1-6h | 29602 | 0.1742 | -0.0979 | -0.0130 |
| DATA_ONLY | 6-24h | 87894 | 0.1750 | -0.0217 | -0.0246 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 38 | 0.2873 | - | - |
| MARKET_BASELINE | 1-6h | 532 | 0.2276 | - | - |
| MARKET_BASELINE | 6-24h | 1406 | 0.2409 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

