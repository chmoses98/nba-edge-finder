# Evaluation report (2026-11-13T16:40:56Z)

rows=1658696 pregame=1658696 new_this_run=0

## game_spread

n=137892 pregame=137892 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 137892 | 0.2029 | 0.6069 | 0.0959 | -0.3190 | -0.0040 |
| MARKET_BASELINE | 2304 | 0.1504 | 0.4805 | 0.0728 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 5623 | 0.2058 | 0.2657 | -0.0050 |
| DATA_ONLY | 1-6h | 33589 | 0.2049 | -0.4170 | -0.0081 |
| DATA_ONLY | 6-24h | 98680 | 0.2020 | -0.3162 | -0.0025 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 66 | 0.1993 | - | - |
| MARKET_BASELINE | 1-6h | 588 | 0.1455 | - | - |
| MARKET_BASELINE | 6-24h | 1650 | 0.1502 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## game_total

n=119988 pregame=119988 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 119988 | 0.1788 | 0.5345 | 0.0148 | -0.2742 | -0.0268 |
| MARKET_BASELINE | 2059 | 0.1759 | 0.5275 | 0.0979 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 4891 | 0.1787 | -0.3383 | -0.0075 |
| DATA_ONLY | 1-6h | 29217 | 0.1791 | -0.3009 | -0.0166 |
| DATA_ONLY | 6-24h | 85880 | 0.1787 | -0.2629 | -0.0312 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 58 | 0.1226 | - | - |
| MARKET_BASELINE | 1-6h | 522 | 0.1790 | - | - |
| MARKET_BASELINE | 6-24h | 1479 | 0.1769 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## game_winner

n=8992 pregame=8992 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 8992 | 0.2438 | 0.7103 | 0.1072 | -1.1322 | 0.0097 |
| MARKET_BASELINE | 142 | 0.0809 | 0.3298 | 0.2787 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 366 | 0.2348 | -0.7106 | 0.0000 |
| DATA_ONLY | 1-6h | 2186 | 0.2457 | -1.0068 | -0.0058 |
| DATA_ONLY | 6-24h | 6440 | 0.2437 | -1.2027 | 0.0156 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 4 | 0.1122 | - | - |
| MARKET_BASELINE | 1-6h | 36 | 0.0835 | - | - |
| MARKET_BASELINE | 6-24h | 102 | 0.0788 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## period_spread

n=265030 pregame=265030 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 265030 | 0.1740 | 0.5256 | 0.0517 | -0.1097 | -0.0346 |
| MARKET_BASELINE | 4495 | 0.1442 | 0.4487 | 0.0296 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 12405 | 0.1761 | 0.0913 | -0.0246 |
| DATA_ONLY | 1-6h | 71872 | 0.1747 | -0.1396 | -0.0276 |
| DATA_ONLY | 6-24h | 180753 | 0.1736 | -0.1076 | -0.0395 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 180 | 0.1682 | - | - |
| MARKET_BASELINE | 1-6h | 1620 | 0.1414 | - | - |
| MARKET_BASELINE | 6-24h | 2695 | 0.1442 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## period_team_total

n=66154 pregame=66154 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 66154 | 0.1859 | 0.5539 | 0.0428 | -0.1173 | -0.0776 |
| MARKET_BASELINE | 1042 | 0.1606 | 0.4922 | 0.1813 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 2882 | 0.1863 | -0.0975 | -0.0315 |
| DATA_ONLY | 1-6h | 17226 | 0.1859 | -0.2245 | -0.0423 |
| DATA_ONLY | 6-24h | 46046 | 0.1858 | -0.0566 | -0.1042 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 44 | 0.1298 | - | - |
| MARKET_BASELINE | 1-6h | 396 | 0.1493 | - | - |
| MARKET_BASELINE | 6-24h | 602 | 0.1703 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## period_total

n=261826 pregame=261826 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 261826 | 0.1728 | 0.5226 | 0.0414 | -0.1628 | -0.0399 |
| MARKET_BASELINE | 4638 | 0.1399 | 0.4388 | 0.0939 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 12340 | 0.1729 | -0.2994 | -0.0313 |
| DATA_ONLY | 1-6h | 71763 | 0.1725 | -0.2266 | -0.0241 |
| DATA_ONLY | 6-24h | 177723 | 0.1729 | -0.1236 | -0.0494 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 178 | 0.1149 | - | - |
| MARKET_BASELINE | 1-6h | 1605 | 0.1321 | - | - |
| MARKET_BASELINE | 6-24h | 2855 | 0.1459 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## period_winner

n=39588 pregame=39588 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 39588 | 0.2440 | 0.6818 | 0.0389 | -0.0714 | -0.0692 |
| MARKET_BASELINE | 780 | 0.2068 | 0.6047 | 0.1374 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 1612 | 0.2385 | 0.0471 | -0.0168 |
| DATA_ONLY | 1-6h | 9576 | 0.2440 | -0.0793 | -0.0295 |
| DATA_ONLY | 6-24h | 28400 | 0.2443 | -0.0731 | -0.0853 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 22 | 0.2043 | - | - |
| MARKET_BASELINE | 1-6h | 198 | 0.2083 | - | - |
| MARKET_BASELINE | 6-24h | 560 | 0.2063 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_assists

n=101325 pregame=101325 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 100747 | 0.1573 | 0.4821 | 0.0634 | -0.0953 | -0.0215 |
| MARKET_BASELINE | 2218 | 0.1885 | 0.5679 | 0.0944 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 5142 | 0.1524 | 0.0187 | -0.0118 |
| DATA_ONLY | 1-6h | 28409 | 0.1569 | -0.1239 | -0.0043 |
| DATA_ONLY | 6-24h | 67196 | 0.1579 | -0.0886 | -0.0304 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 92 | 0.1734 | - | - |
| MARKET_BASELINE | 1-6h | 690 | 0.1852 | - | - |
| MARKET_BASELINE | 6-24h | 1436 | 0.1911 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_blocks

n=18153 pregame=18153 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 18105 | 0.2053 | 0.6062 | 0.0956 | -0.0267 | -0.0317 |
| MARKET_BASELINE | 312 | 0.1985 | 0.5910 | 0.1359 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 1282 | 0.1859 | -0.1703 | -0.0227 |
| DATA_ONLY | 1-6h | 6425 | 0.2004 | -0.0414 | -0.0182 |
| DATA_ONLY | 6-24h | 10398 | 0.2106 | 0.0150 | -0.0506 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 26 | 0.1617 | - | - |
| MARKET_BASELINE | 1-6h | 160 | 0.2003 | - | - |
| MARKET_BASELINE | 6-24h | 126 | 0.2038 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_double_double

n=18002 pregame=18002 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 17931 | 0.1336 | 0.5176 | 0.0551 | -0.1694 | -0.0249 |
| MARKET_BASELINE | 597 | 0.0947 | 0.3095 | 0.0866 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 1006 | 0.1152 | -0.3134 | -0.0124 |
| DATA_ONLY | 1-6h | 5527 | 0.1267 | -0.1994 | -0.0145 |
| DATA_ONLY | 6-24h | 11398 | 0.1386 | -0.1511 | -0.0313 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 25 | 0.0156 | - | - |
| MARKET_BASELINE | 1-6h | 201 | 0.1003 | - | - |
| MARKET_BASELINE | 6-24h | 371 | 0.0970 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_points

n=116846 pregame=116846 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 116083 | 0.2152 | 0.7509 | 0.0797 | -0.0397 | -0.0214 |
| MARKET_BASELINE | 2551 | 0.1555 | 0.4824 | 0.0496 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 5711 | 0.2106 | -0.0129 | -0.0072 |
| DATA_ONLY | 1-6h | 32088 | 0.2126 | -0.0651 | -0.0073 |
| DATA_ONLY | 6-24h | 78284 | 0.2166 | -0.0280 | -0.0291 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 102 | 0.1296 | - | - |
| MARKET_BASELINE | 1-6h | 804 | 0.1621 | - | - |
| MARKET_BASELINE | 6-24h | 1645 | 0.1539 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_pra

n=64427 pregame=64427 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 64107 | 0.2640 | 0.9515 | 0.1200 | 0.0026 | -0.0442 |
| MARKET_BASELINE | 1940 | 0.2091 | 0.6068 | 0.0671 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 3508 | 0.2510 | 0.0401 | -0.0146 |
| DATA_ONLY | 1-6h | 19082 | 0.2584 | -0.0224 | -0.0203 |
| DATA_ONLY | 6-24h | 41517 | 0.2677 | 0.0131 | -0.0593 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 90 | 0.1937 | - | - |
| MARKET_BASELINE | 1-6h | 648 | 0.2062 | - | - |
| MARKET_BASELINE | 6-24h | 1202 | 0.2118 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_rebounds

n=132723 pregame=132723 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 132009 | 0.2016 | 0.6789 | 0.0642 | -0.1684 | -0.0268 |
| MARKET_BASELINE | 2984 | 0.1679 | 0.5050 | 0.0606 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 6711 | 0.1946 | -0.0552 | -0.0116 |
| DATA_ONLY | 1-6h | 37174 | 0.1972 | -0.2109 | -0.0094 |
| DATA_ONLY | 6-24h | 88124 | 0.2040 | -0.1562 | -0.0361 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 132 | 0.1788 | - | - |
| MARKET_BASELINE | 1-6h | 922 | 0.1682 | - | - |
| MARKET_BASELINE | 6-24h | 1930 | 0.1671 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_steals

n=38157 pregame=38157 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 37941 | 0.1948 | 0.5766 | 0.0619 | 0.0184 | -0.0244 |
| MARKET_BASELINE | 632 | 0.1712 | 0.5162 | 0.0951 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 2409 | 0.1926 | 0.0789 | -0.0161 |
| DATA_ONLY | 1-6h | 13035 | 0.1927 | 0.0010 | -0.0133 |
| DATA_ONLY | 6-24h | 22497 | 0.1963 | 0.0287 | -0.0382 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 41 | 0.1764 | - | - |
| MARKET_BASELINE | 1-6h | 315 | 0.1692 | - | - |
| MARKET_BASELINE | 6-24h | 276 | 0.1726 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_threes

n=140146 pregame=140146 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 139321 | 0.1694 | 0.5276 | 0.0366 | -0.0440 | -0.0229 |
| MARKET_BASELINE | 2855 | 0.1457 | 0.4498 | 0.0446 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 6953 | 0.1697 | -0.0651 | -0.0117 |
| DATA_ONLY | 1-6h | 38645 | 0.1699 | -0.0663 | -0.0115 |
| DATA_ONLY | 6-24h | 93723 | 0.1692 | -0.0310 | -0.0294 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 124 | 0.1405 | - | - |
| MARKET_BASELINE | 1-6h | 912 | 0.1495 | - | - |
| MARKET_BASELINE | 6-24h | 1819 | 0.1441 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_triple_double

n=6289 pregame=6289 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 6239 | 0.0187 | 0.1162 | 0.0069 | -0.0361 | -0.0082 |
| MARKET_BASELINE | 45 | 0.1288 | 0.5436 | 0.1076 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 354 | 0.0095 | 0.8411 | -0.0050 |
| DATA_ONLY | 1-6h | 1985 | 0.0170 | -0.0203 | -0.0029 |
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

n=123158 pregame=123158 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 123158 | 0.1747 | 0.5266 | 0.0185 | -0.0925 | -0.0222 |
| MARKET_BASELINE | 2698 | 0.2119 | 0.6186 | 0.1158 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 4978 | 0.1715 | 0.0731 | -0.0069 |
| DATA_ONLY | 1-6h | 29754 | 0.1743 | -0.1374 | -0.0118 |
| DATA_ONLY | 6-24h | 88426 | 0.1751 | -0.0835 | -0.0265 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 76 | 0.2143 | - | - |
| MARKET_BASELINE | 1-6h | 684 | 0.2084 | - | - |
| MARKET_BASELINE | 6-24h | 1938 | 0.2130 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

