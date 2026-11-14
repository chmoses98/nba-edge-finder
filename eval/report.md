# Evaluation report (2026-11-14T12:32:47Z)

rows=1750576 pregame=1750576 new_this_run=0

## game_spread

n=143370 pregame=143370 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 143370 | 0.2037 | 0.6086 | 0.0975 | -0.3221 | -0.0107 |
| MARKET_BASELINE | 7709 | 0.1652 | 0.5101 | 0.0496 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 5887 | 0.2069 | -0.3469 | -0.0084 |
| DATA_ONLY | 1-6h | 34876 | 0.2057 | -0.3411 | -0.0107 |
| DATA_ONLY | 6-24h | 102607 | 0.2029 | -0.3144 | -0.0109 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 330 | 0.1574 | - | - |
| MARKET_BASELINE | 1-6h | 1861 | 0.1643 | - | - |
| MARKET_BASELINE | 6-24h | 5518 | 0.1660 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## game_total

n=124802 pregame=124802 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 124802 | 0.1772 | 0.5302 | 0.0138 | -0.0965 | -0.0192 |
| MARKET_BASELINE | 6873 | 0.1482 | 0.4550 | 0.0573 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 5123 | 0.1766 | -0.0138 | -0.0088 |
| DATA_ONLY | 1-6h | 30348 | 0.1775 | -0.1213 | -0.0148 |
| DATA_ONLY | 6-24h | 89331 | 0.1771 | -0.0927 | -0.0213 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 290 | 0.1369 | - | - |
| MARKET_BASELINE | 1-6h | 1653 | 0.1492 | - | - |
| MARKET_BASELINE | 6-24h | 4930 | 0.1485 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## game_winner

n=9324 pregame=9324 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 9324 | 0.2457 | 0.7145 | 0.1112 | -0.4301 | -0.0072 |
| MARKET_BASELINE | 474 | 0.1817 | 0.5363 | 0.2544 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 382 | 0.2391 | -0.4206 | -0.0070 |
| DATA_ONLY | 1-6h | 2264 | 0.2470 | -0.4275 | -0.0109 |
| DATA_ONLY | 6-24h | 6678 | 0.2457 | -0.4315 | -0.0060 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 20 | 0.2178 | - | - |
| MARKET_BASELINE | 1-6h | 114 | 0.1719 | - | - |
| MARKET_BASELINE | 6-24h | 340 | 0.1828 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## period_spread

n=279801 pregame=279801 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 279801 | 0.1739 | 0.5255 | 0.0525 | -0.1158 | -0.0390 |
| MARKET_BASELINE | 18398 | 0.1546 | 0.4756 | 0.0173 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 13125 | 0.1759 | -0.1006 | -0.0258 |
| DATA_ONLY | 1-6h | 75382 | 0.1745 | -0.1275 | -0.0292 |
| DATA_ONLY | 6-24h | 191294 | 0.1736 | -0.1123 | -0.0440 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 900 | 0.1531 | - | - |
| MARKET_BASELINE | 1-6h | 5130 | 0.1489 | - | - |
| MARKET_BASELINE | 6-24h | 12368 | 0.1570 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## period_team_total

n=69806 pregame=69806 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 69806 | 0.1859 | 0.5541 | 0.0400 | -0.0735 | -0.0927 |
| MARKET_BASELINE | 4591 | 0.1732 | 0.5227 | 0.0452 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 3058 | 0.1859 | -0.1098 | -0.0310 |
| DATA_ONLY | 1-6h | 18084 | 0.1859 | -0.1204 | -0.0412 |
| DATA_ONLY | 6-24h | 48664 | 0.1859 | -0.0537 | -0.1178 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 220 | 0.1558 | - | - |
| MARKET_BASELINE | 1-6h | 1254 | 0.1652 | - | - |
| MARKET_BASELINE | 6-24h | 3117 | 0.1776 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## period_total

n=276532 pregame=276532 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 276532 | 0.1720 | 0.5210 | 0.0429 | -0.0493 | -0.0450 |
| MARKET_BASELINE | 19103 | 0.1524 | 0.4695 | 0.0376 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 13060 | 0.1721 | -0.0411 | -0.0233 |
| DATA_ONLY | 1-6h | 75273 | 0.1718 | -0.0960 | -0.0308 |
| DATA_ONLY | 6-24h | 188199 | 0.1721 | -0.0328 | -0.0520 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 898 | 0.1506 | - | - |
| MARKET_BASELINE | 1-6h | 5090 | 0.1454 | - | - |
| MARKET_BASELINE | 6-24h | 13115 | 0.1552 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## period_winner

n=41542 pregame=41542 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 41542 | 0.2439 | 0.6815 | 0.0410 | -0.0703 | -0.0549 |
| MARKET_BASELINE | 2734 | 0.2198 | 0.6310 | 0.0734 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 1706 | 0.2396 | -0.0607 | -0.0200 |
| DATA_ONLY | 1-6h | 10034 | 0.2437 | -0.0729 | -0.0300 |
| DATA_ONLY | 6-24h | 29802 | 0.2442 | -0.0700 | -0.0653 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 116 | 0.2324 | - | - |
| MARKET_BASELINE | 1-6h | 656 | 0.2177 | - | - |
| MARKET_BASELINE | 6-24h | 1962 | 0.2197 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_assists

n=107173 pregame=107173 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 106595 | 0.1573 | 0.4823 | 0.0619 | -0.0502 | -0.0185 |
| MARKET_BASELINE | 7838 | 0.1660 | 0.5060 | 0.0426 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 5480 | 0.1520 | -0.0568 | -0.0084 |
| DATA_ONLY | 1-6h | 29931 | 0.1567 | -0.0658 | -0.0054 |
| DATA_ONLY | 6-24h | 71184 | 0.1579 | -0.0436 | -0.0248 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 418 | 0.1479 | - | - |
| MARKET_BASELINE | 1-6h | 2180 | 0.1623 | - | - |
| MARKET_BASELINE | 6-24h | 5240 | 0.1691 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_blocks

n=19559 pregame=19559 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 19511 | 0.2022 | 0.5977 | 0.0911 | 0.0240 | -0.0376 |
| MARKET_BASELINE | 1550 | 0.1898 | 0.5597 | 0.0315 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 1387 | 0.1858 | -0.1188 | -0.0245 |
| DATA_ONLY | 1-6h | 6936 | 0.1972 | -0.0012 | -0.0231 |
| DATA_ONLY | 6-24h | 11188 | 0.2074 | 0.0609 | -0.0509 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 126 | 0.1721 | - | - |
| MARKET_BASELINE | 1-6h | 622 | 0.1803 | - | - |
| MARKET_BASELINE | 6-24h | 802 | 0.1999 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_double_double

n=19523 pregame=19523 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 19452 | 0.1314 | 0.5037 | 0.0505 | -0.0442 | -0.0209 |
| MARKET_BASELINE | 2075 | 0.1044 | 0.3376 | 0.0644 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 1096 | 0.1151 | -0.0172 | -0.0123 |
| DATA_ONLY | 1-6h | 5953 | 0.1251 | -0.0827 | -0.0090 |
| DATA_ONLY | 6-24h | 12403 | 0.1359 | -0.0291 | -0.0270 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 108 | 0.0975 | - | - |
| MARKET_BASELINE | 1-6h | 613 | 0.1031 | - | - |
| MARKET_BASELINE | 6-24h | 1354 | 0.1056 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_points

n=123558 pregame=123558 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 122795 | 0.2147 | 0.7439 | 0.0780 | -0.0859 | -0.0191 |
| MARKET_BASELINE | 9204 | 0.1792 | 0.5369 | 0.0440 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 6115 | 0.2097 | -0.0815 | -0.0048 |
| DATA_ONLY | 1-6h | 33900 | 0.2121 | -0.0946 | -0.0069 |
| DATA_ONLY | 6-24h | 82780 | 0.2162 | -0.0825 | -0.0254 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 506 | 0.1705 | - | - |
| MARKET_BASELINE | 1-6h | 2613 | 0.1780 | - | - |
| MARKET_BASELINE | 6-24h | 6085 | 0.1805 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_pra

n=69389 pregame=69389 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 69069 | 0.2619 | 0.9321 | 0.1161 | -0.0360 | -0.0399 |
| MARKET_BASELINE | 6815 | 0.2187 | 0.6290 | 0.0418 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 3822 | 0.2492 | -0.0566 | -0.0137 |
| DATA_ONLY | 1-6h | 20437 | 0.2567 | -0.0577 | -0.0162 |
| DATA_ONLY | 6-24h | 44810 | 0.2653 | -0.0248 | -0.0530 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 404 | 0.2083 | - | - |
| MARKET_BASELINE | 1-6h | 1992 | 0.2132 | - | - |
| MARKET_BASELINE | 6-24h | 4419 | 0.2221 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_rebounds

n=140449 pregame=140449 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 139735 | 0.1988 | 0.6669 | 0.0603 | -0.0798 | -0.0243 |
| MARKET_BASELINE | 10672 | 0.1516 | 0.4652 | 0.0415 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 7153 | 0.1923 | -0.0758 | -0.0112 |
| DATA_ONLY | 1-6h | 39232 | 0.1948 | -0.1199 | -0.0111 |
| DATA_ONLY | 6-24h | 93350 | 0.2010 | -0.0637 | -0.0308 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 574 | 0.1536 | - | - |
| MARKET_BASELINE | 1-6h | 2976 | 0.1493 | - | - |
| MARKET_BASELINE | 6-24h | 7122 | 0.1523 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_steals

n=40378 pregame=40378 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 40162 | 0.1944 | 0.5758 | 0.0554 | 0.0067 | -0.0273 |
| MARKET_BASELINE | 2783 | 0.1860 | 0.5514 | 0.0510 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 2570 | 0.1932 | 0.0172 | -0.0171 |
| DATA_ONLY | 1-6h | 13808 | 0.1925 | -0.0042 | -0.0124 |
| DATA_ONLY | 6-24h | 23784 | 0.1957 | 0.0128 | -0.0395 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 202 | 0.1985 | - | - |
| MARKET_BASELINE | 1-6h | 1083 | 0.1826 | - | - |
| MARKET_BASELINE | 6-24h | 1498 | 0.1867 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_threes

n=148933 pregame=148933 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 148108 | 0.1690 | 0.5256 | 0.0351 | -0.0295 | -0.0241 |
| MARKET_BASELINE | 11250 | 0.1589 | 0.4850 | 0.0256 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 7448 | 0.1689 | -0.0430 | -0.0116 |
| DATA_ONLY | 1-6h | 40948 | 0.1695 | -0.0464 | -0.0144 |
| DATA_ONLY | 6-24h | 99712 | 0.1688 | -0.0215 | -0.0292 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 601 | 0.1537 | - | - |
| MARKET_BASELINE | 1-6h | 3168 | 0.1561 | - | - |
| MARKET_BASELINE | 6-24h | 7481 | 0.1605 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_triple_double

n=6971 pregame=6971 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 6921 | 0.0206 | 0.1170 | 0.0098 | -0.0337 | -0.0071 |
| MARKET_BASELINE | 374 | 0.0809 | 0.2819 | 0.0553 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 390 | 0.0132 | -0.0938 | -0.0067 |
| DATA_ONLY | 1-6h | 2175 | 0.0187 | -0.0445 | -0.0010 |
| DATA_ONLY | 6-24h | 4356 | 0.0222 | -0.0252 | -0.0097 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 15 | 0.1074 | - | - |
| MARKET_BASELINE | 1-6h | 104 | 0.0733 | - | - |
| MARKET_BASELINE | 6-24h | 255 | 0.0824 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## team_total

n=129466 pregame=129466 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 129466 | 0.1741 | 0.5253 | 0.0167 | -0.1064 | -0.0213 |
| MARKET_BASELINE | 9006 | 0.1656 | 0.5035 | 0.0487 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 5282 | 0.1709 | -0.1039 | -0.0087 |
| DATA_ONLY | 1-6h | 31236 | 0.1737 | -0.1257 | -0.0148 |
| DATA_ONLY | 6-24h | 92948 | 0.1745 | -0.1000 | -0.0242 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 380 | 0.1519 | - | - |
| MARKET_BASELINE | 1-6h | 2166 | 0.1655 | - | - |
| MARKET_BASELINE | 6-24h | 6460 | 0.1664 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

