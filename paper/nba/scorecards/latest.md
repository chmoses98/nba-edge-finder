# NBA paper-system scorecard (research only)

_generated 2026-10-29T11:18:35Z · window 7 d · prospective_only=True · nothing here is a bet recommendation_

## Sample (independent units)

- forecast settlements: 23844 rows over 54 games / 2146 player-games; team games 54
- paper decisions: {'n_games': 57, 'n_player_games': 713, 'n_theses': 2910, 'n_decisions': 927468, 'n_contracts': 16251}; settled 310973

**Integrity counters** (excluded / dropped records): decisions_raw=1385670, paper_settlements_raw=411722, decisions_bad_identity_excluded=101713, decisions_invalid_price_excluded=25296, paper_settlements_orphaned=100749

## Projection accuracy

**Minutes (conditional on playing; bias = pred - actual)**

| model | n (games) | MAE | bias [95% CI] |
|---|---|---|---|
| challenger | 1202 (54) | 4.85 | +0.46 [-0.03, +0.98] |
| incumbent | 1002 (51) | 6.53 | -0.87 [-1.51, -0.24] |
| naive_prior_mean | 789 (40) | 5.19 | -0.77 [-1.38, -0.15] |

Paired challenger - incumbent on 1002 player-games: MAE diff -1.78 [-2.08, -1.48]; bias diff +1.17 [+0.73, +1.60] (negative = challenger better)

**Participation Brier**

| model | n | Brier [95% CI] | mean p | played |
|---|---|---|---|---|
| challenger | 1870 | +0.1025 [+0.0911, +0.1144] | 0.694 | 0.643 |
| incumbent | 1518 | +0.1392 [+0.1284, +0.1506] | 0.695 | 0.660 |

**Player stats, conditional on playing**

| family | n | MAE | bias [95% CI] | CRPS | 80% cover | vs incumbent MAE diff |
|---|---|---|---|---|---|---|
| assists | 1202 | 1.29 | +0.04 [-0.07, +0.15] | +0.871 | 82% | -0.121 [-0.163, -0.080] |
| fga | 1202 | 2.75 | +0.18 [-0.02, +0.38] | +1.920 | 81% | n/a |
| points | 1202 | 4.55 | +0.38 [+0.05, +0.70] | +3.148 | 79% | -0.541 [-0.739, -0.333] |
| pra | 1202 | 6.02 | +0.32 [-0.15, +0.78] | +4.220 | 76% | n/a |
| rebounds | 1202 | 1.89 | -0.11 [-0.27, +0.03] | +1.319 | 79% | -0.235 [-0.298, -0.171] |
| threes | 1202 | 0.86 | +0.00 [-0.05, +0.06] | +0.562 | 80% | -0.048 [-0.073, -0.024] |

**Participation vs production (points)**: unconditional error +0.35 [+0.17, +0.52]; participation component MSE 2.78, conditional-production component MSE 22.81

**Team**: team points bias +2.19 [-0.43, +4.79], MAE 10.37

## Market performance

**Model vs market mid** (54 games, 696 player-games, 15796 contracts): Brier diff (model - market) +0.0072 [+0.0034, +0.0110]; one contract/thesis/horizon: +0.0115 [+0.0064, +0.0171]
  - T-90: +0.0074 [+0.0037, +0.0111] (n_contracts 15097)
  - T-60: +0.0078 [+0.0040, +0.0116] (n_contracts 15204)
  - T-30: +0.0082 [+0.0047, +0.0116] (n_contracts 15624)
  - T-10: +0.0082 [+0.0048, +0.0119] (n_contracts 15385)
  - LAST_VALID: +0.0080 [+0.0045, +0.0115] (n_contracts 15666)

| strategy | all candidates: n / ROI | selected (1/thesis): n / games / ROI [95% CI] | verdict | CLV cents (valid closes) |
|---|---|---|---|---|
| PF_ALL_CANDIDATES_V1 | 307046 / -0.104 | no trades | n/a | n/a |
| PF_EDGE_STRICT_V1 | 798 / -0.208 | 256 / 53 / -0.188 [-0.349, -0.021] | NO_EVIDENCE_OF_VALUE | -0.69 [-1.09, -0.27] |
| PF_EDGE_V1 | 3129 / -0.162 | 639 / 54 / -0.127 [-0.207, -0.043] | NO_EVIDENCE_OF_VALUE | -0.30 [-0.80, +0.16] |

Benchmarks: NO_BET_V1 ROI 0 by definition; MARKET_ONLY_V1 = quote mid (scored above); control SHADOW_PURE_PREREG_V1 is read from nba-shadow-pure by the weekly report.

**Price discovery** (share of OPEN->close Brier improvement achieved by horizon): T-90: -0.21, T-60: 0.15, T-30: -0.03, T-10: -0.18, LAST_VALID: 1.00

**Liquidity**: median spread 0.03, quality gate passed 0.8557039164693553, displayed size >= 1: 0.09811551449753522

## Segments (cells below the minimum sample are suppressed)

- minutes bias by minutes_bucket: 12-20: +1.19 [+0.46, +1.86] (n=299); 20-28: -0.06 [-0.90, +0.84] (n=386); <12: +1.09 [-0.33, +2.47] (n=167); >28: +0.12 [-0.89, +1.15] (n=350)
- minutes bias by role_proxy: bench(<18 pred min): +1.15 [+0.23, +2.05] (n=380); rotation(18-28): +0.16 [-0.54, +0.92] (n=472); starter-like(>28): +0.12 [-0.89, +1.15] (n=350)
- minutes bias by injury_status: LIKELY_ACTIVE: +0.49 [-0.02, +1.00] (n=1173) (1 suppressed)
- minutes bias by freshness: <2h: +0.42 [-0.11, +0.93] (n=1156) (1 suppressed)
- points bias by minutes_bucket: 12-20: +0.96 [+0.36, +1.55] (n=299); 20-28: +0.09 [-0.52, +0.67] (n=386); <12: +0.28 [-0.40, +0.85] (n=167); >28: +0.24 [-0.64, +1.13] (n=350)
- points bias by role_proxy: bench(<18 pred min): +0.54 [+0.06, +0.98] (n=380); rotation(18-28): +0.35 [-0.14, +0.80] (n=472); starter-like(>28): +0.24 [-0.64, +1.13] (n=350)
- points bias by injury_status: LIKELY_ACTIVE: +0.35 [+0.03, +0.67] (n=1173) (1 suppressed)
- points bias by freshness: <2h: +0.40 [+0.06, +0.73] (n=1156) (1 suppressed)
- selected_trades by side: NO: ROI -0.069 (n=1649, games=54); YES: ROI -0.307 (n=1144, games=52)
- selected_trades by price_range: 0.0-0.2: ROI -0.106 (n=84, games=27); 0.2-0.4: ROI -0.204 (n=1087, games=54); 0.4-0.6: ROI -0.168 (n=1575, games=54); 0.6-0.8: ROI -0.007 (n=192, games=43) (1 suppressed)
- selected_trades by horizon: LIVE: ROI -0.114 (n=762, games=54); T-10: ROI -0.167 (n=347, games=53); T-30: ROI -0.180 (n=572, games=54); T-60: ROI -0.172 (n=559, games=53); T-90: ROI -0.166 (n=553, games=53)
- selected_trades by family: game_spread: ROI -0.272 (n=205, games=38); game_total: ROI -0.239 (n=210, games=42); game_winner: ROI -0.254 (n=56, games=37); player_assists: ROI -0.048 (n=491, games=49); player_points: ROI -0.117 (n=1010, games=54); player_pra: ROI -0.068 (n=336, games=50); player_rebounds: ROI -0.420 (n=160, games=37); player_threes: ROI -0.196 (n=144, games=33); team_total: ROI -0.291 (n=202, games=33)
- all_candidates by side: NO: ROI -0.077 (n=153523, games=54); YES: ROI -0.140 (n=153523, games=54)
- all_candidates by price_range: 0.0-0.2: ROI -0.338 (n=56416, games=54); 0.2-0.4: ROI -0.200 (n=59966, games=54); 0.4-0.6: ROI -0.113 (n=56056, games=54); 0.6-0.8: ROI -0.078 (n=54270, games=54); 0.8-1.0: ROI -0.069 (n=80338, games=54)
- all_candidates by horizon: LAST_VALID: ROI -0.096 (n=31572, games=54); LIVE: ROI -0.117 (n=151944, games=54); T-10: ROI -0.086 (n=31010, games=53); T-30: ROI -0.089 (n=31484, games=54); T-60: ROI -0.090 (n=30640, games=53); T-90: ROI -0.091 (n=30396, games=53)
- all_candidates by family: game_spread: ROI -0.076 (n=39062, games=54); game_total: ROI -0.086 (n=34452, games=54); game_winner: ROI -0.068 (n=2856, games=54); player_assists: ROI -0.106 (n=35432, games=54); player_points: ROI -0.094 (n=41550, games=54); player_pra: ROI -0.181 (n=17672, games=54); player_rebounds: ROI -0.122 (n=47014, games=54); player_threes: ROI -0.103 (n=44880, games=54); team_total: ROI -0.099 (n=44128, games=54)

## By day

- 2026-10-22: 2 games, 77 player-games, minutes MAE +3.99, bias +1.37
- 2026-10-23: 12 games, 480 player-games, minutes MAE +5.21, bias +0.94
- 2026-10-24: 8 games, 322 player-games, minutes MAE +4.99, bias -0.26
- 2026-10-25: 7 games, 270 player-games, minutes MAE +4.54, bias +0.66
- 2026-10-26: 9 games, 360 player-games, minutes MAE +5.44, bias +0.37
- 2026-10-27: 4 games, 161 player-games, minutes MAE +4.05, bias +0.77
- 2026-10-28: 12 games, 476 player-games, minutes MAE +4.53, bias +0.11
