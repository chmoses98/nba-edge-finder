# NBA paper-system scorecard (research only)

_generated 2026-10-26T11:17:29Z · window 7 d · prospective_only=True · nothing here is a bet recommendation_

## Sample (independent units)

- forecast settlements: 18934 rows over 43 games / 1789 player-games; team games 43
- paper decisions: {'n_games': 52, 'n_player_games': 574, 'n_theses': 2365, 'n_decisions': 856140, 'n_contracts': 13360}; settled 286113

**Integrity counters** (excluded / dropped records): decisions_raw=971245, paper_settlements_raw=286113, decisions_bad_identity_excluded=91261, decisions_invalid_price_excluded=23844

## Projection accuracy

**Minutes (conditional on playing; bias = pred - actual)**

| model | n (games) | MAE | bias [95% CI] |
|---|---|---|---|
| challenger | 965 (43) | 5.26 | +0.20 [-0.53, +0.88] |
| incumbent | 696 (40) | 8.25 | +2.35 [+0.64, +4.08] |
| naive_prior_mean | 569 (29) | 4.77 | -0.69 [-1.38, -0.02] |

Paired challenger - incumbent on 696 player-games: MAE diff -3.32 [-4.10, -2.60]; bias diff -2.16 [-3.91, -0.51] (negative = challenger better)

**Participation Brier**

| model | n | Brier [95% CI] | mean p | played |
|---|---|---|---|---|
| challenger | 1490 | +0.1146 [+0.0983, +0.1324] | 0.711 | 0.648 |
| incumbent | 1183 | +0.1838 [+0.1662, +0.2024] | 0.622 | 0.588 |

**Player stats, conditional on playing**

| family | n | MAE | bias [95% CI] | CRPS | 80% cover | vs incumbent MAE diff |
|---|---|---|---|---|---|---|
| assists | 965 | 1.33 | -0.03 [-0.15, +0.11] | +0.906 | 79% | -0.322 [-0.435, -0.220] |
| fga | 965 | 2.82 | -0.00 [-0.25, +0.22] | +1.976 | 80% | n/a |
| points | 965 | 4.64 | +0.01 [-0.41, +0.42] | +3.229 | 79% | -1.504 [-2.032, -1.022] |
| pra | 965 | 6.15 | -0.14 [-0.76, +0.48] | +4.368 | 75% | n/a |
| rebounds | 965 | 1.85 | -0.16 [-0.33, -0.01] | +1.294 | 81% | -0.521 [-0.683, -0.374] |
| threes | 965 | 0.84 | +0.01 [-0.05, +0.08] | +0.547 | 78% | -0.170 [-0.238, -0.110] |

**Participation vs production (points)**: unconditional error +0.16 [-0.02, +0.36]; participation component MSE 2.80, conditional-production component MSE 23.94

**Team**: team points bias +2.04 [-0.58, +4.78], MAE 9.62

## Market performance

**Model vs market mid** (43 games, 556 player-games, 12689 contracts): Brier diff (model - market) +0.0058 [+0.0012, +0.0105]; one contract/thesis/horizon: +0.0085 [+0.0006, +0.0166]
  - T-90: +0.0077 [+0.0029, +0.0126] (n_contracts 12110)
  - T-60: +0.0074 [+0.0029, +0.0122] (n_contracts 12462)
  - T-30: +0.0081 [+0.0037, +0.0127] (n_contracts 12533)
  - T-10: +0.0083 [+0.0041, +0.0130] (n_contracts 12588)
  - LAST_VALID: +0.0078 [+0.0034, +0.0121] (n_contracts 12573)

| strategy | all candidates: n / ROI | selected (1/thesis): n / games / ROI [95% CI] | verdict | CLV cents (valid closes) |
|---|---|---|---|---|
| PF_ALL_CANDIDATES_V1 | 282620 / -0.109 | no trades | n/a | n/a |
| PF_EDGE_STRICT_V1 | 568 / -0.172 | 189 / 41 / -0.148 [-0.346, +0.043] | INSUFFICIENT_SAMPLE | -0.47 [-0.97, +0.01] |
| PF_EDGE_V1 | 2925 / -0.114 | 549 / 43 / -0.115 [-0.211, -0.021] | NO_EVIDENCE_OF_VALUE | -0.61 [-1.10, -0.14] |

Benchmarks: NO_BET_V1 ROI 0 by definition; MARKET_ONLY_V1 = quote mid (scored above); control SHADOW_PURE_PREREG_V1 is read from nba-shadow-pure by the weekly report.

**Price discovery** (share of OPEN->close Brier improvement achieved by horizon): T-90: 0.68, T-60: 0.77, T-30: 0.94, T-10: 0.95, LAST_VALID: 1.00

**Liquidity**: median spread 0.03, quality gate passed 0.8516469269044782, displayed size >= 1: 0.11180531221529189

## Segments (cells below the minimum sample are suppressed)

- minutes bias by minutes_bucket: 12-20: +0.64 [-0.30, +1.59] (n=284); 20-28: -0.70 [-1.78, +0.41] (n=336); <12: +1.61 [-0.10, +3.23] (n=120); >28: +0.22 [-1.06, +1.47] (n=225)
- minutes bias by role_proxy: bench(<18 pred min): +0.96 [-0.17, +2.01] (n=327); rotation(18-28): -0.42 [-1.37, +0.57] (n=413); starter-like(>28): +0.22 [-1.06, +1.47] (n=225)
- minutes bias by injury_status: LIKELY_ACTIVE: +0.21 [-0.51, +0.90] (n=934); UNCERTAIN: -0.34 [-2.77, +2.23] (n=31)
- minutes bias by freshness: <2h: +0.14 [-0.58, +0.87] (n=919) (1 suppressed)
- points bias by minutes_bucket: 12-20: +0.50 [-0.15, +1.17] (n=284); 20-28: -0.54 [-1.27, +0.18] (n=336); <12: +0.36 [-0.33, +0.94] (n=120); >28: +0.03 [-1.22, +1.22] (n=225)
- points bias by role_proxy: bench(<18 pred min): +0.30 [-0.21, +0.79] (n=327); rotation(18-28): -0.23 [-0.84, +0.36] (n=413); starter-like(>28): +0.03 [-1.22, +1.22] (n=225)
- points bias by injury_status: LIKELY_ACTIVE: -0.02 [-0.44, +0.40] (n=934); UNCERTAIN: +0.79 [-0.96, +2.72] (n=31)
- points bias by freshness: <2h: +0.02 [-0.42, +0.44] (n=919) (1 suppressed)
- selected_trades by side: NO: ROI -0.071 (n=1594, games=43); YES: ROI -0.240 (n=619, games=40)
- selected_trades by price_range: 0.0-0.2: ROI +0.245 (n=86, games=22); 0.2-0.4: ROI -0.143 (n=868, games=43); 0.4-0.6: ROI -0.136 (n=1269, games=43); 0.6-0.8: ROI +0.120 (n=145, games=34) (1 suppressed)
- selected_trades by horizon: LIVE: ROI -0.105 (n=627, games=43); T-10: ROI -0.131 (n=282, games=43); T-30: ROI -0.118 (n=440, games=43); T-60: ROI -0.094 (n=441, games=43); T-90: ROI -0.123 (n=423, games=42)
- selected_trades by family: game_spread: ROI -0.364 (n=126, games=25); game_total: ROI -0.305 (n=154, games=33); player_assists: ROI -0.070 (n=504, games=41); player_points: ROI -0.094 (n=718, games=43); player_pra: ROI +0.063 (n=319, games=41); player_rebounds: ROI -0.409 (n=139, games=32); player_threes: ROI +0.051 (n=123, games=27); team_total: ROI -0.246 (n=110, games=21) (1 suppressed)
- all_candidates by side: NO: ROI -0.082 (n=141310, games=43); YES: ROI -0.146 (n=141310, games=43)
- all_candidates by price_range: 0.0-0.2: ROI -0.384 (n=51886, games=43); 0.2-0.4: ROI -0.216 (n=54157, games=43); 0.4-0.6: ROI -0.108 (n=51057, games=43); 0.6-0.8: ROI -0.080 (n=49670, games=43); 0.8-1.0: ROI -0.075 (n=75850, games=43)
- all_candidates by horizon: LAST_VALID: ROI -0.099 (n=25338, games=43); LIVE: ROI -0.122 (n=157178, games=43); T-10: ROI -0.089 (n=25368, games=43); T-30: ROI -0.088 (n=25254, games=43); T-60: ROI -0.092 (n=25108, games=43); T-90: ROI -0.092 (n=24374, games=42)
- all_candidates by family: game_spread: ROI -0.066 (n=34584, games=43); game_total: ROI -0.069 (n=30450, games=43); game_winner: ROI -0.069 (n=2368, games=43); player_assists: ROI -0.120 (n=33572, games=43); player_points: ROI -0.106 (n=39168, games=43); player_pra: ROI -0.194 (n=16606, games=43); player_rebounds: ROI -0.139 (n=43908, games=43); player_threes: ROI -0.116 (n=42066, games=43); team_total: ROI -0.089 (n=39898, games=43)

## By day

- 2026-10-20: 3 games, 130 player-games, minutes MAE +5.39, bias -0.88
- 2026-10-21: 11 games, 510 player-games, minutes MAE +6.12, bias -0.51
- 2026-10-22: 2 games, 77 player-games, minutes MAE +3.99, bias +1.37
- 2026-10-23: 12 games, 480 player-games, minutes MAE +5.21, bias +0.94
- 2026-10-24: 8 games, 322 player-games, minutes MAE +4.99, bias -0.26
- 2026-10-25: 7 games, 270 player-games, minutes MAE +4.54, bias +0.66
