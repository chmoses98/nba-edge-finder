# NBA paper-system scorecard (research only)

_generated 2026-10-22T11:04:15Z · window 7 d · prospective_only=True · nothing here is a bet recommendation_

> **INSUFFICIENT_SAMPLE: 16 games with evidence in this window (the preregistered minimum for a value verdict is 40 games and 200 independent decisions); nothing below is a finding**

## Sample (independent units)

- forecast settlements: 6327 rows over 14 games / 640 player-games; team games 14
- paper decisions: {'n_games': 16, 'n_player_games': 212, 'n_theses': 893, 'n_decisions': 360306, 'n_contracts': 4922}; settled 116508

**Integrity counters** (excluded / dropped records): decisions_raw=400089, paper_settlements_raw=116508, decisions_bad_identity_excluded=35973, decisions_invalid_price_excluded=3810

## Projection accuracy

**Minutes (conditional on playing; bias = pred - actual)**

| model | n (games) | MAE | bias [95% CI] |
|---|---|---|---|
| challenger | 322 (14) | 5.97 | -0.59 [-2.03, +0.69] |
| incumbent | 191 (14) | 11.64 | +11.53 [+10.44, +12.73] |

Paired challenger - incumbent on 191 player-games: MAE diff -6.43 [-7.63, -5.19]; bias diff -11.52 [-12.27, -10.83] (negative = challenger better)

**Participation Brier**

| model | n | Brier [95% CI] | mean p | played |
|---|---|---|---|---|
| challenger | 485 | +0.1249 [+0.0870, +0.1640] | 0.732 | 0.664 |
| incumbent | 409 | +0.2470 [+0.2437, +0.2510] | 0.486 | 0.467 |

**Player stats, conditional on playing**

| family | n | MAE | bias [95% CI] | CRPS | 80% cover | vs incumbent MAE diff |
|---|---|---|---|---|---|---|
| assists | 322 | 1.34 | -0.18 [-0.39, +0.02] | +0.929 | 78% | -0.813 [-1.038, -0.642] |
| fga | 322 | 3.02 | -0.24 [-0.72, +0.22] | +2.124 | 79% | n/a |
| points | 322 | 4.70 | -0.47 [-1.17, +0.24] | +3.279 | 78% | -3.844 [-5.039, -2.899] |
| pra | 322 | 6.00 | -0.74 [-1.76, +0.33] | +4.299 | 76% | n/a |
| rebounds | 322 | 1.80 | -0.19 [-0.53, +0.09] | +1.255 | 82% | -1.196 [-1.479, -0.911] |
| threes | 322 | 0.84 | +0.06 [-0.06, +0.19] | +0.537 | 79% | -0.454 [-0.597, -0.336] |

**Participation vs production (points)**: unconditional error -0.11 [-0.35, +0.16]; participation component MSE 3.53, conditional-production component MSE 25.80

**Team**: team points bias +2.37 [-1.05, +5.52], MAE 9.56

## Market performance

**Model vs market mid** (14 games, 182 player-games, 4272 contracts): Brier diff (model - market) +0.0071 [-0.0009, +0.0152]; one contract/thesis/horizon: +0.0084 [-0.0088, +0.0251]
  - T-90: +0.0123 [+0.0030, +0.0206] (n_contracts 4217)
  - T-60: +0.0115 [+0.0022, +0.0203] (n_contracts 4248)
  - T-30: +0.0114 [+0.0013, +0.0206] (n_contracts 4256)
  - T-10: +0.0116 [+0.0038, +0.0201] (n_contracts 4261)
  - LAST_VALID: +0.0110 [+0.0028, +0.0197] (n_contracts 4272)

| strategy | all candidates: n / ROI | selected (1/thesis): n / games / ROI [95% CI] | verdict | CLV cents (valid closes) |
|---|---|---|---|---|
| PF_ALL_CANDIDATES_V1 | 115134 / -0.115 | no trades | n/a | n/a |
| PF_EDGE_STRICT_V1 | 166 / -0.163 | 54 / 13 / -0.055 [-0.456, +0.285] | INSUFFICIENT_SAMPLE | +0.38 [-0.78, +1.71] |
| PF_EDGE_V1 | 1208 / -0.097 | 201 / 14 / -0.096 [-0.259, +0.058] | INSUFFICIENT_SAMPLE | -0.20 [-0.93, +0.53] |

Benchmarks: NO_BET_V1 ROI 0 by definition; MARKET_ONLY_V1 = quote mid (scored above); control SHADOW_PURE_PREREG_V1 is read from nba-shadow-pure by the weekly report.

**Price discovery** (share of OPEN->close Brier improvement achieved by horizon): T-90: 0.74, T-60: 0.83, T-30: 0.96, T-10: 0.97, LAST_VALID: 1.00

**Liquidity**: median spread 0.02, quality gate passed 0.8282376646517127, displayed size >= 1: 0.1275832209288771

## Segments (cells below the minimum sample are suppressed)

- minutes bias by minutes_bucket: 12-20: -0.13 [-1.85, +1.55] (n=124); 20-28: -1.76 [-3.64, -0.07] (n=125); <12: +1.04 [-3.51, +4.42] (n=34); >28: +0.30 [-2.78, +3.03] (n=39)
- minutes bias by role_proxy: bench(<18 pred min): -0.04 [-2.00, +1.81] (n=126); rotation(18-28): -1.25 [-3.12, +0.36] (n=157); starter-like(>28): +0.30 [-2.78, +3.03] (n=39)
- minutes bias by injury_status: LIKELY_ACTIVE: -0.65 [-2.15, +0.68] (n=304) (1 suppressed)
- minutes bias by freshness: <2h: -0.59 [-2.03, +0.69] (n=322)
- points bias by minutes_bucket: 12-20: -0.01 [-0.96, +0.95] (n=124); 20-28: -1.11 [-2.48, +0.23] (n=125); <12: -0.06 [-1.41, +1.14] (n=34); >28: -0.28 [-2.07, +1.59] (n=39)
- points bias by role_proxy: bench(<18 pred min): +0.03 [-0.83, +0.81] (n=126); rotation(18-28): -0.93 [-2.08, +0.20] (n=157); starter-like(>28): -0.28 [-2.07, +1.59] (n=39)
- points bias by injury_status: LIKELY_ACTIVE: -0.57 [-1.28, +0.17] (n=304) (1 suppressed)
- points bias by freshness: <2h: -0.47 [-1.17, +0.24] (n=322)
- selected_trades by side: NO: ROI -0.089 (n=621, games=14); YES: ROI -0.116 (n=116, games=13)
- selected_trades by price_range: 0.0-0.2: ROI +0.485 (n=45, games=10); 0.2-0.4: ROI -0.090 (n=303, games=14); 0.4-0.6: ROI -0.158 (n=422, games=14); 0.6-0.8: ROI +0.456 (n=42, games=12) (1 suppressed)
- selected_trades by horizon: LIVE: ROI -0.124 (n=230, games=14); T-10: ROI -0.070 (n=93, games=14); T-30: ROI -0.064 (n=138, games=14); T-60: ROI -0.093 (n=140, games=14); T-90: ROI -0.083 (n=136, games=14)
- selected_trades by family: game_total: ROI -0.036 (n=52, games=11); player_assists: ROI -0.193 (n=197, games=13); player_points: ROI +0.102 (n=209, games=14); player_pra: ROI -0.041 (n=141, games=14); player_rebounds: ROI -0.309 (n=61, games=12); player_threes: ROI +0.244 (n=34, games=9) (3 suppressed)
- all_candidates by side: NO: ROI -0.092 (n=57567, games=14); YES: ROI -0.150 (n=57567, games=14)
- all_candidates by price_range: 0.0-0.2: ROI -0.404 (n=21409, games=14); 0.2-0.4: ROI -0.206 (n=21446, games=14); 0.4-0.6: ROI -0.103 (n=20499, games=14); 0.6-0.8: ROI -0.096 (n=19622, games=14); 0.8-1.0: ROI -0.086 (n=32158, games=14)
- all_candidates by horizon: LAST_VALID: ROI -0.103 (n=8598, games=14); LIVE: ROI -0.129 (n=72356, games=14); T-10: ROI -0.087 (n=8576, games=14); T-30: ROI -0.087 (n=8566, games=14); T-60: ROI -0.090 (n=8550, games=14); T-90: ROI -0.088 (n=8488, games=14)
- all_candidates by family: game_spread: ROI -0.065 (n=13992, games=14); game_total: ROI -0.067 (n=12296, games=14); game_winner: ROI -0.070 (n=848, games=14); player_assists: ROI -0.131 (n=13720, games=14); player_points: ROI -0.114 (n=15622, games=14); player_pra: ROI -0.196 (n=6402, games=14); player_rebounds: ROI -0.152 (n=17408, games=14); player_threes: ROI -0.125 (n=18736, games=14); team_total: ROI -0.093 (n=16110, games=14)

## By day

- 2026-10-20: 3 games, 130 player-games, minutes MAE +5.39, bias -0.88
- 2026-10-21: 11 games, 510 player-games, minutes MAE +6.12, bias -0.51
