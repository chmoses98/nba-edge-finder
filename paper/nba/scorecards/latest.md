# NBA paper-system scorecard (research only)

_generated 2026-10-28T11:15:27Z · window 7 d · prospective_only=True · nothing here is a bet recommendation_

## Sample (independent units)

- forecast settlements: 23462 rows over 53 games / 2180 player-games; team games 53
- paper decisions: {'n_games': 65, 'n_player_games': 714, 'n_theses': 2944, 'n_decisions': 1012032, 'n_contracts': 17069}; settled 332637

**Integrity counters** (excluded / dropped records): decisions_raw=1229775, paper_settlements_raw=358160, decisions_bad_identity_excluded=105324, decisions_invalid_price_excluded=26382, paper_settlements_orphaned=25523

## Projection accuracy

**Minutes (conditional on playing; bias = pred - actual)**

| model | n (games) | MAE | bias [95% CI] |
|---|---|---|---|
| challenger | 1200 (53) | 5.19 | +0.33 [-0.31, +0.91] |
| incumbent | 911 (50) | 7.65 | +1.27 [-0.03, +2.58] |
| naive_prior_mean | 788 (39) | 4.93 | -0.53 [-1.11, +0.12] |

Paired challenger - incumbent on 911 player-games: MAE diff -2.73 [-3.36, -2.16]; bias diff -0.85 [-2.12, +0.28] (negative = challenger better)

**Participation Brier**

| model | n | Brier [95% CI] | mean p | played |
|---|---|---|---|---|
| challenger | 1836 | +0.1090 [+0.0942, +0.1240] | 0.706 | 0.654 |
| incumbent | 1481 | +0.1650 [+0.1490, +0.1805] | 0.649 | 0.615 |

**Player stats, conditional on playing**

| family | n | MAE | bias [95% CI] | CRPS | 80% cover | vs incumbent MAE diff |
|---|---|---|---|---|---|---|
| assists | 1200 | 1.30 | -0.00 [-0.12, +0.11] | +0.885 | 78% | -0.252 [-0.338, -0.172] |
| fga | 1200 | 2.83 | +0.12 [-0.09, +0.32] | +1.981 | 80% | n/a |
| points | 1200 | 4.59 | +0.15 [-0.21, +0.51] | +3.192 | 78% | -1.174 [-1.587, -0.804] |
| pra | 1200 | 6.16 | +0.06 [-0.49, +0.58] | +4.341 | 75% | n/a |
| rebounds | 1200 | 1.87 | -0.12 [-0.28, +0.03] | +1.308 | 80% | -0.435 [-0.564, -0.321] |
| threes | 1200 | 0.85 | +0.02 [-0.04, +0.09] | +0.549 | 79% | -0.128 [-0.180, -0.081] |

**Participation vs production (points)**: unconditional error +0.21 [+0.05, +0.39]; participation component MSE 2.84, conditional-production component MSE 23.80

**Team**: team points bias +1.43 [-1.01, +3.91], MAE 9.98

## Market performance

**Model vs market mid** (53 games, 687 player-games, 15676 contracts): Brier diff (model - market) +0.0077 [+0.0036, +0.0119]; one contract/thesis/horizon: +0.0112 [+0.0048, +0.0180]
  - T-90: +0.0089 [+0.0047, +0.0131] (n_contracts 15018)
  - T-60: +0.0090 [+0.0049, +0.0131] (n_contracts 15103)
  - T-30: +0.0094 [+0.0053, +0.0133] (n_contracts 15514)
  - T-10: +0.0095 [+0.0056, +0.0135] (n_contracts 15267)
  - LAST_VALID: +0.0093 [+0.0056, +0.0130] (n_contracts 15551)

| strategy | all candidates: n / ROI | selected (1/thesis): n / games / ROI [95% CI] | verdict | CLV cents (valid closes) |
|---|---|---|---|---|
| PF_ALL_CANDIDATES_V1 | 328522 / -0.106 | no trades | n/a | n/a |
| PF_EDGE_STRICT_V1 | 744 / -0.245 | 242 / 52 / -0.206 [-0.374, -0.041] | NO_EVIDENCE_OF_VALUE | -0.70 [-1.14, -0.27] |
| PF_EDGE_V1 | 3371 / -0.166 | 660 / 53 / -0.149 [-0.231, -0.067] | NO_EVIDENCE_OF_VALUE | -0.52 [-0.97, -0.11] |

Benchmarks: NO_BET_V1 ROI 0 by definition; MARKET_ONLY_V1 = quote mid (scored above); control SHADOW_PURE_PREREG_V1 is read from nba-shadow-pure by the weekly report.

**Price discovery** (share of OPEN->close Brier improvement achieved by horizon): T-90: 0.86, T-60: 0.78, T-30: 0.99, T-10: 0.98, LAST_VALID: 1.00

**Liquidity**: median spread 0.03, quality gate passed 0.8411858518307721, displayed size >= 1: 0.09152378580914437

## Segments (cells below the minimum sample are suppressed)

- minutes bias by minutes_bucket: 12-20: +0.84 [-0.06, +1.72] (n=334); 20-28: -0.43 [-1.36, +0.48] (n=405); <12: +1.09 [-0.45, +2.48] (n=162); >28: +0.38 [-0.76, +1.55] (n=299)
- minutes bias by role_proxy: bench(<18 pred min): +0.96 [-0.05, +1.92] (n=404); rotation(18-28): -0.21 [-1.10, +0.58] (n=497); starter-like(>28): +0.38 [-0.76, +1.55] (n=299)
- minutes bias by injury_status: LIKELY_ACTIVE: +0.34 [-0.31, +0.92] (n=1162); UNCERTAIN: +0.14 [-2.20, +2.46] (n=38)
- minutes bias by freshness: <2h: +0.29 [-0.35, +0.87] (n=1154) (1 suppressed)
- points bias by minutes_bucket: 12-20: +0.81 [+0.20, +1.42] (n=334); 20-28: -0.44 [-1.14, +0.20] (n=405); <12: +0.29 [-0.36, +0.89] (n=162); >28: +0.13 [-0.95, +1.11] (n=299)
- points bias by role_proxy: bench(<18 pred min): +0.52 [+0.04, +0.96] (n=404); rotation(18-28): -0.14 [-0.73, +0.38] (n=497); starter-like(>28): +0.13 [-0.95, +1.11] (n=299)
- points bias by injury_status: LIKELY_ACTIVE: +0.11 [-0.26, +0.47] (n=1162); UNCERTAIN: +1.36 [-0.35, +3.07] (n=38)
- points bias by freshness: <2h: +0.16 [-0.22, +0.51] (n=1154) (1 suppressed)
- selected_trades by side: NO: ROI -0.134 (n=1813, games=53); YES: ROI -0.275 (n=924, games=50)
- selected_trades by price_range: 0.0-0.2: ROI +0.018 (n=107, games=28); 0.2-0.4: ROI -0.261 (n=1085, games=53); 0.4-0.6: ROI -0.167 (n=1555, games=53); 0.6-0.8: ROI +0.017 (n=166, games=43) (1 suppressed)
- selected_trades by horizon: LIVE: ROI -0.146 (n=772, games=53); T-10: ROI -0.190 (n=340, games=52); T-30: ROI -0.191 (n=552, games=53); T-60: ROI -0.182 (n=541, games=52); T-90: ROI -0.190 (n=532, games=52)
- selected_trades by family: game_spread: ROI -0.253 (n=184, games=35); game_total: ROI -0.350 (n=196, games=41); game_winner: ROI -0.013 (n=42, games=27); player_assists: ROI -0.115 (n=575, games=49); player_points: ROI -0.129 (n=875, games=53); player_pra: ROI -0.088 (n=397, games=50); player_rebounds: ROI -0.447 (n=163, games=37); player_threes: ROI -0.168 (n=146, games=34); team_total: ROI -0.276 (n=173, games=31)
- all_candidates by side: NO: ROI -0.094 (n=164261, games=53); YES: ROI -0.122 (n=164261, games=53)
- all_candidates by price_range: 0.0-0.2: ROI -0.378 (n=61012, games=53); 0.2-0.4: ROI -0.209 (n=63053, games=53); 0.4-0.6: ROI -0.107 (n=59217, games=53); 0.6-0.8: ROI -0.077 (n=57708, games=53); 0.8-1.0: ROI -0.072 (n=87532, games=53)
- all_candidates by horizon: LAST_VALID: ROI -0.096 (n=31396, games=53); LIVE: ROI -0.119 (n=174196, games=53); T-10: ROI -0.087 (n=30828, games=52); T-30: ROI -0.088 (n=31318, games=53); T-60: ROI -0.090 (n=30492, games=52); T-90: ROI -0.090 (n=30292, games=52)
- all_candidates by family: game_spread: ROI -0.067 (n=39988, games=53); game_total: ROI -0.070 (n=35206, games=53); game_winner: ROI -0.068 (n=2856, games=53); player_assists: ROI -0.116 (n=39082, games=53); player_points: ROI -0.103 (n=45378, games=53); player_pra: ROI -0.187 (n=18744, games=53); player_rebounds: ROI -0.133 (n=51382, games=53); player_threes: ROI -0.111 (n=49850, games=53); team_total: ROI -0.089 (n=46036, games=53)

## By day

- 2026-10-21: 11 games, 510 player-games, minutes MAE +6.12, bias -0.51
- 2026-10-22: 2 games, 77 player-games, minutes MAE +3.99, bias +1.37
- 2026-10-23: 12 games, 480 player-games, minutes MAE +5.21, bias +0.94
- 2026-10-24: 8 games, 322 player-games, minutes MAE +4.99, bias -0.26
- 2026-10-25: 7 games, 270 player-games, minutes MAE +4.54, bias +0.66
- 2026-10-26: 9 games, 360 player-games, minutes MAE +5.44, bias +0.37
- 2026-10-27: 4 games, 161 player-games, minutes MAE +4.05, bias +0.77
