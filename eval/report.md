# Evaluation report (2026-11-14T04:03:26Z)

rows=1705026 pregame=1705026 new_this_run=46330

## game_spread

n=140796 pregame=140796 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 140796 | 0.2043 | 0.6104 | 0.0979 | -0.4405 | -0.0081 |
| MARKET_BASELINE | 5170 | 0.1657 | 0.5127 | 0.0485 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 5788 | 0.2077 | -0.2976 | -0.0085 |
| DATA_ONLY | 1-6h | 34249 | 0.2062 | -0.4774 | -0.0111 |
| DATA_ONLY | 6-24h | 100759 | 0.2034 | -0.4381 | -0.0070 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 231 | 0.1809 | - | - |
| MARKET_BASELINE | 1-6h | 1243 | 0.1629 | - | - |
| MARKET_BASELINE | 6-24h | 3696 | 0.1657 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## game_total

n=122540 pregame=122540 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 122540 | 0.1782 | 0.5328 | 0.0147 | -0.1545 | -0.0196 |
| MARKET_BASELINE | 4611 | 0.1590 | 0.4798 | 0.0530 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 5036 | 0.1779 | -0.1064 | -0.0090 |
| DATA_ONLY | 1-6h | 29797 | 0.1786 | -0.1782 | -0.0147 |
| DATA_ONLY | 6-24h | 87707 | 0.1781 | -0.1492 | -0.0219 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 203 | 0.1398 | - | - |
| MARKET_BASELINE | 1-6h | 1102 | 0.1610 | - | - |
| MARKET_BASELINE | 6-24h | 3306 | 0.1596 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## game_winner

n=9168 pregame=9168 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 9168 | 0.2472 | 0.7188 | 0.1115 | -0.5611 | -0.0021 |
| MARKET_BASELINE | 318 | 0.1983 | 0.5842 | 0.2479 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 376 | 0.2398 | -0.5053 | -0.0064 |
| DATA_ONLY | 1-6h | 2226 | 0.2489 | -0.5399 | -0.0100 |
| DATA_ONLY | 6-24h | 6566 | 0.2471 | -0.5722 | 0.0008 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 14 | 0.2370 | - | - |
| MARKET_BASELINE | 1-6h | 76 | 0.1957 | - | - |
| MARKET_BASELINE | 6-24h | 228 | 0.1968 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## period_spread

n=272833 pregame=272833 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 272833 | 0.1742 | 0.5260 | 0.0523 | -0.1503 | -0.0385 |
| MARKET_BASELINE | 11825 | 0.1508 | 0.4622 | 0.0226 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 12855 | 0.1762 | -0.0959 | -0.0270 |
| DATA_ONLY | 1-6h | 73672 | 0.1748 | -0.1576 | -0.0298 |
| DATA_ONLY | 6-24h | 186306 | 0.1738 | -0.1518 | -0.0432 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 630 | 0.1562 | - | - |
| MARKET_BASELINE | 1-6h | 3420 | 0.1472 | - | - |
| MARKET_BASELINE | 6-24h | 7775 | 0.1519 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## period_team_total

n=68090 pregame=68090 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 68090 | 0.1863 | 0.5548 | 0.0395 | -0.1264 | -0.0908 |
| MARKET_BASELINE | 2913 | 0.1728 | 0.5222 | 0.0366 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 2992 | 0.1868 | -0.1491 | -0.0330 |
| DATA_ONLY | 1-6h | 17666 | 0.1863 | -0.1850 | -0.0419 |
| DATA_ONLY | 6-24h | 47432 | 0.1863 | -0.1015 | -0.1167 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 154 | 0.1608 | - | - |
| MARKET_BASELINE | 1-6h | 836 | 0.1629 | - | - |
| MARKET_BASELINE | 6-24h | 1923 | 0.1781 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## period_total

n=269603 pregame=269603 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 269603 | 0.1726 | 0.5223 | 0.0413 | -0.0552 | -0.0449 |
| MARKET_BASELINE | 12269 | 0.1563 | 0.4795 | 0.0303 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 12790 | 0.1727 | -0.0795 | -0.0237 |
| DATA_ONLY | 1-6h | 73563 | 0.1723 | -0.1065 | -0.0305 |
| DATA_ONLY | 6-24h | 183250 | 0.1727 | -0.0338 | -0.0524 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 628 | 0.1497 | - | - |
| MARKET_BASELINE | 1-6h | 3389 | 0.1488 | - | - |
| MARKET_BASELINE | 6-24h | 8252 | 0.1599 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## period_winner

n=40644 pregame=40644 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 40644 | 0.2447 | 0.6832 | 0.0427 | -0.0944 | -0.0601 |
| MARKET_BASELINE | 1836 | 0.2274 | 0.6473 | 0.0807 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 1672 | 0.2396 | -0.0700 | -0.0217 |
| DATA_ONLY | 1-6h | 9816 | 0.2446 | -0.0923 | -0.0325 |
| DATA_ONLY | 6-24h | 29156 | 0.2450 | -0.0967 | -0.0718 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 82 | 0.2329 | - | - |
| MARKET_BASELINE | 1-6h | 438 | 0.2282 | - | - |
| MARKET_BASELINE | 6-24h | 1316 | 0.2268 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_assists

n=104009 pregame=104009 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 103431 | 0.1572 | 0.4820 | 0.0637 | -0.0872 | -0.0211 |
| MARKET_BASELINE | 4811 | 0.1651 | 0.5027 | 0.0513 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 5345 | 0.1521 | -0.0660 | -0.0090 |
| DATA_ONLY | 1-6h | 29127 | 0.1567 | -0.1063 | -0.0059 |
| DATA_ONLY | 6-24h | 68959 | 0.1578 | -0.0807 | -0.0291 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 290 | 0.1465 | - | - |
| MARKET_BASELINE | 1-6h | 1402 | 0.1618 | - | - |
| MARKET_BASELINE | 6-24h | 3119 | 0.1683 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_blocks

n=18634 pregame=18634 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 18586 | 0.2054 | 0.6068 | 0.0932 | -0.0426 | -0.0297 |
| MARKET_BASELINE | 771 | 0.2046 | 0.6015 | 0.0672 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 1328 | 0.1873 | -0.1742 | -0.0261 |
| DATA_ONLY | 1-6h | 6581 | 0.2004 | -0.0494 | -0.0141 |
| DATA_ONLY | 6-24h | 10677 | 0.2108 | -0.0170 | -0.0431 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 71 | 0.1833 | - | - |
| MARKET_BASELINE | 1-6h | 313 | 0.1959 | - | - |
| MARKET_BASELINE | 6-24h | 387 | 0.2154 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_double_double

n=18685 pregame=18685 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 18614 | 0.1346 | 0.5173 | 0.0552 | -0.0850 | -0.0222 |
| MARKET_BASELINE | 1271 | 0.1277 | 0.4003 | 0.0626 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 1060 | 0.1164 | -0.0647 | -0.0120 |
| DATA_ONLY | 1-6h | 5729 | 0.1274 | -0.1205 | -0.0109 |
| DATA_ONLY | 6-24h | 11825 | 0.1397 | -0.0704 | -0.0289 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 77 | 0.0980 | - | - |
| MARKET_BASELINE | 1-6h | 400 | 0.1205 | - | - |
| MARKET_BASELINE | 6-24h | 794 | 0.1341 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_points

n=120221 pregame=120221 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 119458 | 0.2145 | 0.7462 | 0.0776 | -0.0766 | -0.0190 |
| MARKET_BASELINE | 5884 | 0.1658 | 0.5049 | 0.0517 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 5958 | 0.2096 | -0.0401 | -0.0032 |
| DATA_ONLY | 1-6h | 32979 | 0.2119 | -0.0890 | -0.0064 |
| DATA_ONLY | 6-24h | 80521 | 0.2160 | -0.0745 | -0.0261 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 349 | 0.1645 | - | - |
| MARKET_BASELINE | 1-6h | 1692 | 0.1656 | - | - |
| MARKET_BASELINE | 6-24h | 3843 | 0.1660 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_pra

n=66527 pregame=66527 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 66207 | 0.2627 | 0.9416 | 0.1178 | 0.0171 | -0.0389 |
| MARKET_BASELINE | 3979 | 0.2184 | 0.6287 | 0.0594 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 3690 | 0.2498 | -0.0068 | -0.0122 |
| DATA_ONLY | 1-6h | 19688 | 0.2572 | -0.0017 | -0.0172 |
| DATA_ONLY | 6-24h | 42829 | 0.2663 | 0.0288 | -0.0528 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 272 | 0.2121 | - | - |
| MARKET_BASELINE | 1-6h | 1243 | 0.2145 | - | - |
| MARKET_BASELINE | 6-24h | 2464 | 0.2211 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_rebounds

n=136470 pregame=136470 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 135756 | 0.2001 | 0.6729 | 0.0618 | -0.0971 | -0.0249 |
| MARKET_BASELINE | 6713 | 0.1552 | 0.4747 | 0.0455 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 6979 | 0.1932 | -0.0817 | -0.0107 |
| DATA_ONLY | 1-6h | 38192 | 0.1960 | -0.1363 | -0.0117 |
| DATA_ONLY | 6-24h | 90585 | 0.2025 | -0.0814 | -0.0321 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 400 | 0.1560 | - | - |
| MARKET_BASELINE | 1-6h | 1936 | 0.1539 | - | - |
| MARKET_BASELINE | 6-24h | 4377 | 0.1557 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_steals

n=39159 pregame=39159 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 38943 | 0.1951 | 0.5773 | 0.0606 | 0.0076 | -0.0263 |
| MARKET_BASELINE | 1598 | 0.1935 | 0.5699 | 0.0562 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 2500 | 0.1932 | 0.0389 | -0.0192 |
| DATA_ONLY | 1-6h | 13353 | 0.1931 | -0.0043 | -0.0111 |
| DATA_ONLY | 6-24h | 23090 | 0.1965 | 0.0111 | -0.0388 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 132 | 0.2035 | - | - |
| MARKET_BASELINE | 1-6h | 628 | 0.1891 | - | - |
| MARKET_BASELINE | 6-24h | 838 | 0.1952 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_threes

n=144607 pregame=144607 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 143782 | 0.1692 | 0.5264 | 0.0362 | -0.0122 | -0.0245 |
| MARKET_BASELINE | 7113 | 0.1581 | 0.4835 | 0.0402 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 7260 | 0.1694 | -0.0391 | -0.0121 |
| DATA_ONLY | 1-6h | 39815 | 0.1697 | -0.0381 | -0.0152 |
| DATA_ONLY | 6-24h | 96707 | 0.1690 | 0.0014 | -0.0297 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 424 | 0.1542 | - | - |
| MARKET_BASELINE | 1-6h | 2058 | 0.1556 | - | - |
| MARKET_BASELINE | 6-24h | 4631 | 0.1596 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## player_triple_double

n=6538 pregame=6538 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 6488 | 0.0220 | 0.1245 | 0.0108 | -0.0471 | -0.0094 |
| MARKET_BASELINE | 177 | 0.1684 | 0.5541 | 0.1571 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 373 | 0.0138 | -0.1060 | -0.0110 |
| DATA_ONLY | 1-6h | 2058 | 0.0198 | -0.0586 | -0.0012 |
| DATA_ONLY | 6-24h | 4057 | 0.0238 | -0.0385 | -0.0133 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 10 | 0.1590 | - | - |
| MARKET_BASELINE | 1-6h | 55 | 0.1365 | - | - |
| MARKET_BASELINE | 6-24h | 112 | 0.1850 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

## team_total

n=126502 pregame=126502 excluded_post_tip=0 authority=SHADOW

| view | n | brier | log_loss | ece | skill_vs_market | clv_mean |
|---|---|---|---|---|---|---|
| DATA_ONLY | 126502 | 0.1751 | 0.5275 | 0.0183 | -0.1655 | -0.0199 |
| MARKET_BASELINE | 6042 | 0.1782 | 0.5333 | 0.0757 | - | - |
| HYBRID | 0 | - | - | - | - | - |

| view | bucket | n | brier | skill_vs_market | clv_mean |
|---|---|---|---|---|---|
| DATA_ONLY | <1h | 5168 | 0.1722 | -0.1370 | -0.0077 |
| DATA_ONLY | 1-6h | 30514 | 0.1746 | -0.1926 | -0.0140 |
| DATA_ONLY | 6-24h | 90820 | 0.1754 | -0.1582 | -0.0226 |
| DATA_ONLY | >24h | 0 | - | - | - |
| MARKET_BASELINE | <1h | 266 | 0.1684 | - | - |
| MARKET_BASELINE | 1-6h | 1444 | 0.1773 | - | - |
| MARKET_BASELINE | 6-24h | 4332 | 0.1791 | - | - |
| MARKET_BASELINE | >24h | 0 | - | - | - |
| HYBRID | <1h | 0 | - | - | - |
| HYBRID | 1-6h | 0 | - | - | - |
| HYBRID | 6-24h | 0 | - | - | - |
| HYBRID | >24h | 0 | - | - | - |

