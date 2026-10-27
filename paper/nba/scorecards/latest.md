# NBA paper-system scorecard (research only)

_generated 2026-10-27T11:12:15Z · window 7 d · prospective_only=True · nothing here is a bet recommendation_

## Sample (independent units)

- forecast settlements: 23006 rows over 52 games / 2149 player-games; team games 52
- paper decisions: {'n_games': 56, 'n_player_games': 688, 'n_theses': 2848, 'n_decisions': 1003074, 'n_contracts': 15943}; settled 337105

**Integrity counters** (excluded / dropped records): decisions_raw=1135027, paper_settlements_raw=337105, decisions_bad_identity_excluded=107659, decisions_invalid_price_excluded=24294

## Projection accuracy

**Minutes (conditional on playing; bias = pred - actual)**

| model | n (games) | MAE | bias [95% CI] |
|---|---|---|---|
| challenger | 1175 (52) | 5.29 | +0.23 [-0.42, +0.87] |
| incumbent | 880 (49) | 7.95 | +1.93 [+0.48, +3.42] |
| naive_prior_mean | 769 (38) | 4.87 | -0.49 [-1.15, +0.11] |

Paired challenger - incumbent on 880 player-games: MAE diff -2.94 [-3.60, -2.36]; bias diff -1.64 [-3.13, -0.26] (negative = challenger better)

**Participation Brier**

| model | n | Brier [95% CI] | mean p | played |
|---|---|---|---|---|
| challenger | 1800 | +0.1099 [+0.0955, +0.1254] | 0.709 | 0.653 |
| incumbent | 1453 | +0.1739 [+0.1576, +0.1898] | 0.635 | 0.606 |

**Player stats, conditional on playing**

| family | n | MAE | bias [95% CI] | CRPS | 80% cover | vs incumbent MAE diff |
|---|---|---|---|---|---|---|
| assists | 1175 | 1.30 | -0.01 [-0.12, +0.11] | +0.888 | 79% | -0.290 [-0.386, -0.207] |
| fga | 1175 | 2.83 | +0.06 [-0.17, +0.27] | +1.987 | 80% | n/a |
| points | 1175 | 4.58 | +0.14 [-0.25, +0.50] | +3.192 | 79% | -1.310 [-1.788, -0.883] |
| pra | 1175 | 6.16 | +0.01 [-0.52, +0.56] | +4.351 | 75% | n/a |
| rebounds | 1175 | 1.89 | -0.17 [-0.32, -0.01] | +1.322 | 80% | -0.465 [-0.606, -0.342] |
| threes | 1175 | 0.84 | +0.02 [-0.04, +0.08] | +0.548 | 78% | -0.141 [-0.197, -0.092] |

**Participation vs production (points)**: unconditional error +0.21 [+0.04, +0.39]; participation component MSE 2.78, conditional-production component MSE 23.85

**Team**: team points bias +2.13 [-0.26, +4.38], MAE 9.71

## Market performance

**Model vs market mid** (52 games, 672 player-games, 15381 contracts): Brier diff (model - market) +0.0064 [+0.0023, +0.0105]; one contract/thesis/horizon: +0.0098 [+0.0028, +0.0169]
  - T-90: +0.0079 [+0.0035, +0.0121] (n_contracts 14727)
  - T-60: +0.0079 [+0.0036, +0.0122] (n_contracts 14814)
  - T-30: +0.0084 [+0.0040, +0.0125] (n_contracts 15211)
  - T-10: +0.0084 [+0.0046, +0.0124] (n_contracts 14965)
  - LAST_VALID: +0.0082 [+0.0043, +0.0122] (n_contracts 15258)

| strategy | all candidates: n / ROI | selected (1/thesis): n / games / ROI [95% CI] | verdict | CLV cents (valid closes) |
|---|---|---|---|---|
| PF_ALL_CANDIDATES_V1 | 332962 / -0.106 | no trades | n/a | n/a |
| PF_EDGE_STRICT_V1 | 699 / -0.191 | 228 / 50 / -0.152 [-0.331, +0.010] | NO_EVIDENCE_OF_VALUE | -0.44 [-0.91, +0.06] |
| PF_EDGE_V1 | 3444 / -0.117 | 659 / 52 / -0.122 [-0.207, -0.041] | NO_EVIDENCE_OF_VALUE | -0.47 [-0.89, -0.05] |

Benchmarks: NO_BET_V1 ROI 0 by definition; MARKET_ONLY_V1 = quote mid (scored above); control SHADOW_PURE_PREREG_V1 is read from nba-shadow-pure by the weekly report.

**Price discovery** (share of OPEN->close Brier improvement achieved by horizon): T-90: 0.67, T-60: 0.76, T-30: 0.93, T-10: 0.95, LAST_VALID: 1.00

**Liquidity**: median spread 0.03, quality gate passed 0.8539290221858008, displayed size >= 1: 0.10992110253082026

## Segments (cells below the minimum sample are suppressed)

- minutes bias by minutes_bucket: 12-20: +0.85 [-0.04, +1.70] (n=338); 20-28: -0.76 [-1.65, +0.14] (n=403); <12: +1.27 [-0.34, +2.85] (n=156); >28: +0.32 [-0.81, +1.54] (n=278)
- minutes bias by role_proxy: bench(<18 pred min): +0.98 [-0.03, +1.99] (n=405); rotation(18-28): -0.45 [-1.29, +0.38] (n=492); starter-like(>28): +0.32 [-0.81, +1.54] (n=278)
- minutes bias by injury_status: LIKELY_ACTIVE: +0.25 [-0.42, +0.90] (n=1138); UNCERTAIN: -0.33 [-2.62, +2.01] (n=37)
- minutes bias by freshness: <2h: +0.18 [-0.47, +0.79] (n=1129) (1 suppressed)
- points bias by minutes_bucket: 12-20: +0.71 [+0.12, +1.30] (n=338); 20-28: -0.46 [-1.13, +0.17] (n=403); <12: +0.27 [-0.41, +0.84] (n=156); >28: +0.26 [-0.81, +1.25] (n=278)
- points bias by role_proxy: bench(<18 pred min): +0.43 [-0.02, +0.84] (n=405); rotation(18-28): -0.16 [-0.72, +0.37] (n=492); starter-like(>28): +0.26 [-0.81, +1.25] (n=278)
- points bias by injury_status: LIKELY_ACTIVE: +0.11 [-0.29, +0.49] (n=1138); UNCERTAIN: +1.26 [-0.29, +2.88] (n=37)
- points bias by freshness: <2h: +0.15 [-0.23, +0.53] (n=1129) (1 suppressed)
- selected_trades by side: NO: ROI -0.079 (n=1830, games=52); YES: ROI -0.221 (n=841, games=49)
- selected_trades by price_range: 0.0-0.2: ROI +0.177 (n=108, games=27); 0.2-0.4: ROI -0.197 (n=1043, games=52); 0.4-0.6: ROI -0.121 (n=1535, games=52); 0.6-0.8: ROI +0.103 (n=167, games=42) (1 suppressed)
- selected_trades by horizon: LIVE: ROI -0.102 (n=757, games=52); T-10: ROI -0.126 (n=336, games=51); T-30: ROI -0.125 (n=535, games=52); T-60: ROI -0.122 (n=525, games=51); T-90: ROI -0.128 (n=518, games=51)
- selected_trades by family: game_spread: ROI -0.226 (n=161, games=31); game_total: ROI -0.264 (n=200, games=41); game_winner: ROI +0.070 (n=38, games=24); player_assists: ROI -0.070 (n=550, games=47); player_points: ROI -0.094 (n=864, games=52); player_pra: ROI -0.001 (n=407, games=50); player_rebounds: ROI -0.462 (n=161, games=38); player_threes: ROI -0.002 (n=143, games=31); team_total: ROI -0.222 (n=160, games=28)
- all_candidates by side: NO: ROI -0.079 (n=166481, games=52); YES: ROI -0.145 (n=166481, games=52)
- all_candidates by price_range: 0.0-0.2: ROI -0.386 (n=61879, games=52); 0.2-0.4: ROI -0.206 (n=63775, games=52); 0.4-0.6: ROI -0.105 (n=59956, games=52); 0.6-0.8: ROI -0.080 (n=58562, games=52); 0.8-1.0: ROI -0.072 (n=88790, games=52)
- all_candidates by horizon: LAST_VALID: ROI -0.097 (n=30810, games=52); LIVE: ROI -0.119 (n=181592, games=52); T-10: ROI -0.087 (n=30224, games=51); T-30: ROI -0.089 (n=30712, games=52); T-60: ROI -0.091 (n=29914, games=51); T-90: ROI -0.090 (n=29710, games=51)
- all_candidates by family: game_spread: ROI -0.067 (n=40590, games=52); game_total: ROI -0.069 (n=35728, games=52); game_winner: ROI -0.069 (n=2832, games=52); player_assists: ROI -0.116 (n=39720, games=52); player_points: ROI -0.102 (n=45908, games=52); player_pra: ROI -0.190 (n=19420, games=52); player_rebounds: ROI -0.134 (n=51656, games=52); player_threes: ROI -0.111 (n=50294, games=52); team_total: ROI -0.089 (n=46814, games=52)

## By day

- 2026-10-20: 3 games, 130 player-games, minutes MAE +5.39, bias -0.88
- 2026-10-21: 11 games, 510 player-games, minutes MAE +6.12, bias -0.51
- 2026-10-22: 2 games, 77 player-games, minutes MAE +3.99, bias +1.37
- 2026-10-23: 12 games, 480 player-games, minutes MAE +5.21, bias +0.94
- 2026-10-24: 8 games, 322 player-games, minutes MAE +4.99, bias -0.26
- 2026-10-25: 7 games, 270 player-games, minutes MAE +4.54, bias +0.66
- 2026-10-26: 9 games, 360 player-games, minutes MAE +5.44, bias +0.37
