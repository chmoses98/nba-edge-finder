# Evaluation report (2026-11-14T05:50:22Z)

rows=1738931 pregame=1738931 new_this_run=33905

## game_spread

n=142710 pregame=142710 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 142710 | 0.2039 | 0.6092 | 0.0968 | -0.3143 | -0.0090 |
| MARKET_BASELINE | 7052 | 0.1701 | 0.5243 | 0.0477 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 5854 | 0.2071 | -0.3309 | -0.0076 |
| DATA_ONLY | 1-6h | 34744 | 0.2058 | -0.3360 | -0.0091 |
| DATA_ONLY | 6-24h | 102112 | 0.2031 | -0.3060 | -0.0090 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 297 | 0.1634 | - | - |
| MARKET_BASELINE | 1-6h | 1729 | 0.1682 | - | - |
| MARKET_BASELINE | 6-24h | 5026 | 0.1711 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## game_total

n=124222 pregame=124222 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 124222 | 0.1776 | 0.5312 | 0.0141 | -0.0960 | -0.0198 |
| MARKET_BASELINE | 6293 | 0.1550 | 0.4708 | 0.0602 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 5094 | 0.1771 | -0.0085 | -0.0087 |
| DATA_ONLY | 1-6h | 30232 | 0.1779 | -0.1222 | -0.0149 |
| DATA_ONLY | 6-24h | 88896 | 0.1775 | -0.0918 | -0.0221 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 261 | 0.1439 | - | - |
| MARKET_BASELINE | 1-6h | 1537 | 0.1548 | - | - |
| MARKET_BASELINE | 6-24h | 4495 | 0.1557 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## game_winner

n=9284 pregame=9284 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 9284 | 0.2444 | 0.7116 | 0.1084 | -0.5322 | -0.0037 |
| MARKET_BASELINE | 434 | 0.1513 | 0.4700 | 0.2182 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 380 | 0.2374 | -0.4824 | -0.0061 |
| DATA_ONLY | 1-6h | 2256 | 0.2458 | -0.5061 | -0.0088 |
| DATA_ONLY | 6-24h | 6648 | 0.2442 | -0.5445 | -0.0018 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 18 | 0.1898 | - | - |
| MARKET_BASELINE | 1-6h | 106 | 0.1470 | - | - |
| MARKET_BASELINE | 6-24h | 310 | 0.1506 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## period_spread

n=278001 pregame=278001 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 278001 | 0.1737 | 0.5250 | 0.0529 | -0.1369 | -0.0386 |
| MARKET_BASELINE | 16703 | 0.1475 | 0.4584 | 0.0293 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 13035 | 0.1757 | -0.1185 | -0.0254 |
| DATA_ONLY | 1-6h | 75022 | 0.1743 | -0.1431 | -0.0290 |
| DATA_ONLY | 6-24h | 189944 | 0.1733 | -0.1356 | -0.0437 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 810 | 0.1467 | - | - |
| MARKET_BASELINE | 1-6h | 4770 | 0.1442 | - | - |
| MARKET_BASELINE | 6-24h | 11123 | 0.1490 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## period_team_total

n=69366 pregame=69366 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 69366 | 0.1858 | 0.5537 | 0.0402 | -0.0696 | -0.0927 |
| MARKET_BASELINE | 4153 | 0.1712 | 0.5187 | 0.0542 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 3036 | 0.1857 | -0.1232 | -0.0308 |
| DATA_ONLY | 1-6h | 17996 | 0.1858 | -0.1276 | -0.0406 |
| DATA_ONLY | 6-24h | 48334 | 0.1858 | -0.0440 | -0.1189 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 198 | 0.1502 | - | - |
| MARKET_BASELINE | 1-6h | 1166 | 0.1623 | - | - |
| MARKET_BASELINE | 6-24h | 2789 | 0.1764 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## period_total

n=274797 pregame=274797 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 274797 | 0.1720 | 0.5208 | 0.0430 | -0.0727 | -0.0433 |
| MARKET_BASELINE | 17378 | 0.1467 | 0.4560 | 0.0446 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 12970 | 0.1720 | -0.0769 | -0.0224 |
| DATA_ONLY | 1-6h | 74913 | 0.1717 | -0.1191 | -0.0298 |
| DATA_ONLY | 6-24h | 186914 | 0.1720 | -0.0550 | -0.0502 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 808 | 0.1429 | - | - |
| MARKET_BASELINE | 1-6h | 4733 | 0.1408 | - | - |
| MARKET_BASELINE | 6-24h | 11837 | 0.1494 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## period_winner

n=41302 pregame=41302 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 41302 | 0.2436 | 0.6809 | 0.0396 | -0.0778 | -0.0562 |
| MARKET_BASELINE | 2494 | 0.2131 | 0.6172 | 0.1027 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 1694 | 0.2392 | -0.0633 | -0.0203 |
| DATA_ONLY | 1-6h | 9986 | 0.2435 | -0.0772 | -0.0301 |
| DATA_ONLY | 6-24h | 29622 | 0.2439 | -0.0789 | -0.0671 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 104 | 0.2268 | - | - |
| MARKET_BASELINE | 1-6h | 608 | 0.2124 | - | - |
| MARKET_BASELINE | 6-24h | 1782 | 0.2125 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_assists

n=106286 pregame=106286 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 105708 | 0.1572 | 0.4822 | 0.0618 | -0.0538 | -0.0191 |
| MARKET_BASELINE | 7033 | 0.1642 | 0.5011 | 0.0383 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 5433 | 0.1519 | -0.0601 | -0.0087 |
| DATA_ONLY | 1-6h | 29743 | 0.1566 | -0.0675 | -0.0057 |
| DATA_ONLY | 6-24h | 70532 | 0.1578 | -0.0477 | -0.0257 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 375 | 0.1447 | - | - |
| MARKET_BASELINE | 1-6h | 2008 | 0.1610 | - | - |
| MARKET_BASELINE | 6-24h | 4650 | 0.1671 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_blocks

n=19431 pregame=19431 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 19383 | 0.2021 | 0.5975 | 0.0908 | 0.0319 | -0.0383 |
| MARKET_BASELINE | 1422 | 0.1887 | 0.5568 | 0.0433 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 1379 | 0.1856 | -0.1190 | -0.0251 |
| DATA_ONLY | 1-6h | 6904 | 0.1971 | 0.0042 | -0.0237 |
| DATA_ONLY | 6-24h | 11100 | 0.2073 | 0.0738 | -0.0524 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 118 | 0.1707 | - | - |
| MARKET_BASELINE | 1-6h | 590 | 0.1796 | - | - |
| MARKET_BASELINE | 6-24h | 714 | 0.1993 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_double_double

n=19291 pregame=19291 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 19220 | 0.1326 | 0.5083 | 0.0521 | -0.0651 | -0.0199 |
| MARKET_BASELINE | 1858 | 0.1106 | 0.3563 | 0.0625 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 1084 | 0.1160 | -0.0339 | -0.0110 |
| DATA_ONLY | 1-6h | 5905 | 0.1258 | -0.0961 | -0.0086 |
| DATA_ONLY | 6-24h | 12231 | 0.1373 | -0.0534 | -0.0260 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 98 | 0.1024 | - | - |
| MARKET_BASELINE | 1-6h | 569 | 0.1074 | - | - |
| MARKET_BASELINE | 6-24h | 1191 | 0.1128 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_points

n=122684 pregame=122684 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 121921 | 0.2150 | 0.7454 | 0.0784 | -0.1064 | -0.0193 |
| MARKET_BASELINE | 8339 | 0.1771 | 0.5301 | 0.0441 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 6062 | 0.2101 | -0.1061 | -0.0041 |
| DATA_ONLY | 1-6h | 33692 | 0.2124 | -0.1151 | -0.0071 |
| DATA_ONLY | 6-24h | 82167 | 0.2164 | -0.1026 | -0.0259 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 453 | 0.1687 | - | - |
| MARKET_BASELINE | 1-6h | 2405 | 0.1765 | - | - |
| MARKET_BASELINE | 6-24h | 5481 | 0.1780 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_pra

n=68579 pregame=68579 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 68259 | 0.2628 | 0.9369 | 0.1179 | -0.0754 | -0.0402 |
| MARKET_BASELINE | 6023 | 0.2164 | 0.6233 | 0.0328 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 3779 | 0.2501 | -0.0894 | -0.0126 |
| DATA_ONLY | 1-6h | 20265 | 0.2573 | -0.0824 | -0.0163 |
| DATA_ONLY | 6-24h | 44215 | 0.2665 | -0.0710 | -0.0540 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 361 | 0.2067 | - | - |
| MARKET_BASELINE | 1-6h | 1820 | 0.2120 | - | - |
| MARKET_BASELINE | 6-24h | 3842 | 0.2193 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_rebounds

n=139406 pregame=139406 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 138692 | 0.1991 | 0.6683 | 0.0608 | -0.1040 | -0.0226 |
| MARKET_BASELINE | 9639 | 0.1482 | 0.4568 | 0.0529 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 7098 | 0.1925 | -0.0946 | -0.0105 |
| DATA_ONLY | 1-6h | 39012 | 0.1950 | -0.1369 | -0.0103 |
| DATA_ONLY | 6-24h | 92582 | 0.2013 | -0.0906 | -0.0290 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 519 | 0.1507 | - | - |
| MARKET_BASELINE | 1-6h | 2756 | 0.1470 | - | - |
| MARKET_BASELINE | 6-24h | 6364 | 0.1485 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_steals

n=40242 pregame=40242 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 40026 | 0.1946 | 0.5762 | 0.0561 | -0.0025 | -0.0281 |
| MARKET_BASELINE | 2647 | 0.1860 | 0.5515 | 0.0489 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 2561 | 0.1934 | 0.0096 | -0.0184 |
| DATA_ONLY | 1-6h | 13772 | 0.1926 | -0.0105 | -0.0131 |
| DATA_ONLY | 6-24h | 23693 | 0.1959 | 0.0016 | -0.0405 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 193 | 0.1994 | - | - |
| MARKET_BASELINE | 1-6h | 1047 | 0.1829 | - | - |
| MARKET_BASELINE | 6-24h | 1407 | 0.1865 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_threes

n=147753 pregame=147753 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 146928 | 0.1692 | 0.5263 | 0.0356 | -0.0489 | -0.0242 |
| MARKET_BASELINE | 10124 | 0.1580 | 0.4827 | 0.0214 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 7384 | 0.1692 | -0.0652 | -0.0117 |
| DATA_ONLY | 1-6h | 40692 | 0.1697 | -0.0640 | -0.0149 |
| DATA_ONLY | 6-24h | 98852 | 0.1690 | -0.0411 | -0.0292 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 541 | 0.1519 | - | - |
| MARKET_BASELINE | 1-6h | 2912 | 0.1558 | - | - |
| MARKET_BASELINE | 6-24h | 6671 | 0.1594 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_triple_double

n=6871 pregame=6871 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 6821 | 0.0209 | 0.1187 | 0.0100 | -0.0340 | -0.0074 |
| MARKET_BASELINE | 337 | 0.0897 | 0.3109 | 0.0634 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 385 | 0.0133 | -0.0939 | -0.0069 |
| DATA_ONLY | 1-6h | 2155 | 0.0189 | -0.0447 | -0.0006 |
| DATA_ONLY | 6-24h | 4281 | 0.0226 | -0.0256 | -0.0102 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 13 | 0.1239 | - | - |
| MARKET_BASELINE | 1-6h | 96 | 0.0794 | - | - |
| MARKET_BASELINE | 6-24h | 228 | 0.0922 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## team_total

n=128706 pregame=128706 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 128706 | 0.1746 | 0.5263 | 0.0172 | -0.1003 | -0.0208 |
| MARKET_BASELINE | 8246 | 0.1731 | 0.5218 | 0.0543 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 5244 | 0.1714 | -0.0943 | -0.0079 |
| DATA_ONLY | 1-6h | 31084 | 0.1741 | -0.1220 | -0.0145 |
| DATA_ONLY | 6-24h | 92378 | 0.1749 | -0.0933 | -0.0237 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 342 | 0.1597 | - | - |
| MARKET_BASELINE | 1-6h | 2014 | 0.1715 | - | - |
| MARKET_BASELINE | 6-24h | 5890 | 0.1744 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

