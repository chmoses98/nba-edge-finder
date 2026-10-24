# NBA paper-system scorecard (research only)

_generated 2026-10-24T11:12:21Z · window 7 d · prospective_only=True · nothing here is a bet recommendation_

> **INSUFFICIENT_SAMPLE: 36 games with evidence in this window (the preregistered minimum for a value verdict is 40 games and 200 independent decisions); nothing below is a finding**

## Sample (independent units)

- forecast settlements: 12482 rows over 28 games / 1197 player-games; team games 28
- paper decisions: {'n_games': 36, 'n_player_games': 383, 'n_theses': 1576, 'n_decisions': 644700, 'n_contracts': 8577}; settled 217275

**Integrity counters** (excluded / dropped records): decisions_raw=726843, paper_settlements_raw=217275, decisions_bad_identity_excluded=65883, decisions_invalid_price_excluded=16260

## Projection accuracy

**Minutes (conditional on playing; bias = pred - actual)**

| model | n (games) | MAE | bias [95% CI] |
|---|---|---|---|
| challenger | 642 (28) | 5.50 | +0.20 [-0.87, +1.12] |
| incumbent | 453 (27) | 9.18 | +4.83 [+2.68, +7.16] |
| naive_prior_mean | 266 (14) | 4.64 | +0.09 [-0.75, +0.94] |

Paired challenger - incumbent on 453 player-games: MAE diff -4.06 [-5.12, -3.10]; bias diff -4.41 [-6.83, -2.14] (negative = challenger better)

**Participation Brier**

| model | n | Brier [95% CI] | mean p | played |
|---|---|---|---|---|
| challenger | 971 | +0.1133 [+0.0910, +0.1364] | 0.722 | 0.661 |
| incumbent | 795 | +0.1931 [+0.1692, +0.2147] | 0.586 | 0.570 |

**Player stats, conditional on playing**

| family | n | MAE | bias [95% CI] | CRPS | 80% cover | vs incumbent MAE diff |
|---|---|---|---|---|---|---|
| assists | 642 | 1.32 | +0.00 [-0.17, +0.17] | +0.901 | 79% | -0.408 [-0.570, -0.261] |
| fga | 642 | 2.86 | +0.03 [-0.27, +0.33] | +2.011 | 78% | n/a |
| points | 642 | 4.68 | +0.11 [-0.44, +0.66] | +3.242 | 79% | -1.940 [-2.758, -1.229] |
| pra | 642 | 6.09 | +0.10 [-0.70, +0.90] | +4.298 | 75% | n/a |
| rebounds | 642 | 1.84 | -0.10 [-0.28, +0.08] | +1.271 | 81% | -0.713 [-0.930, -0.513] |
| threes | 642 | 0.79 | +0.07 [-0.01, +0.15] | +0.513 | 80% | -0.245 [-0.340, -0.163] |

**Participation vs production (points)**: unconditional error +0.22 [-0.01, +0.49]; participation component MSE 2.69, conditional-production component MSE 24.86

**Team**: team points bias +3.62 [+0.80, +6.82], MAE 9.93

## Market performance

**Model vs market mid** (28 games, 373 player-games, 8534 contracts): Brier diff (model - market) +0.0061 [+0.0005, +0.0121]; one contract/thesis/horizon: +0.0083 [-0.0030, +0.0201]
  - T-90: +0.0092 [+0.0023, +0.0156] (n_contracts 8392)
  - T-60: +0.0087 [+0.0022, +0.0150] (n_contracts 8431)
  - T-30: +0.0092 [+0.0029, +0.0157] (n_contracts 8457)
  - T-10: +0.0092 [+0.0036, +0.0151] (n_contracts 8473)
  - LAST_VALID: +0.0087 [+0.0029, +0.0146] (n_contracts 8468)

| strategy | all candidates: n / ROI | selected (1/thesis): n / games / ROI [95% CI] | verdict | CLV cents (valid closes) |
|---|---|---|---|---|
| PF_ALL_CANDIDATES_V1 | 214748 / -0.110 | no trades | n/a | n/a |
| PF_EDGE_STRICT_V1 | 365 / -0.113 | 117 / 26 / -0.068 [-0.326, +0.198] | INSUFFICIENT_SAMPLE | -0.24 [-0.90, +0.50] |
| PF_EDGE_V1 | 2162 / -0.100 | 377 / 28 / -0.093 [-0.215, +0.032] | INSUFFICIENT_SAMPLE | -0.53 [-1.15, +0.05] |

Benchmarks: NO_BET_V1 ROI 0 by definition; MARKET_ONLY_V1 = quote mid (scored above); control SHADOW_PURE_PREREG_V1 is read from nba-shadow-pure by the weekly report.

**Price discovery** (share of OPEN->close Brier improvement achieved by horizon): T-90: 0.65, T-60: 0.77, T-30: 0.93, T-10: 0.95, LAST_VALID: 1.00

**Liquidity**: median spread 0.02, quality gate passed 0.8486738017682643, displayed size >= 1: 0.11244299674267101

## Segments (cells below the minimum sample are suppressed)

- minutes bias by minutes_bucket: 12-20: +0.43 [-0.78, +1.62] (n=209); 20-28: -1.12 [-2.38, +0.17] (n=222); <12: +2.26 [-0.15, +4.34] (n=78); >28: +0.85 [-0.92, +2.57] (n=133)
- minutes bias by role_proxy: bench(<18 pred min): +1.09 [-0.33, +2.42] (n=231); rotation(18-28): -0.84 [-2.08, +0.30] (n=278); starter-like(>28): +0.85 [-0.92, +2.57] (n=133)
- minutes bias by injury_status: LIKELY_ACTIVE: +0.19 [-0.92, +1.12] (n=621) (1 suppressed)
- minutes bias by freshness: <2h: +0.20 [-0.87, +1.12] (n=642)
- points bias by minutes_bucket: 12-20: +0.46 [-0.24, +1.20] (n=209); 20-28: -0.66 [-1.66, +0.27] (n=222); <12: +0.39 [-0.54, +1.17] (n=78); >28: +0.69 [-0.89, +2.18] (n=133)
- points bias by role_proxy: bench(<18 pred min): +0.36 [-0.24, +0.92] (n=231); rotation(18-28): -0.37 [-1.20, +0.43] (n=278); starter-like(>28): +0.69 [-0.89, +2.18] (n=133)
- points bias by injury_status: LIKELY_ACTIVE: +0.06 [-0.52, +0.64] (n=621) (1 suppressed)
- points bias by freshness: <2h: +0.11 [-0.44, +0.66] (n=642)
- selected_trades by side: NO: ROI -0.052 (n=1104, games=28); YES: ROI -0.178 (n=362, games=25)
- selected_trades by price_range: 0.0-0.2: ROI +0.072 (n=67, games=16); 0.2-0.4: ROI -0.059 (n=633, games=28); 0.4-0.6: ROI -0.121 (n=821, games=28); 0.6-0.8: ROI +0.197 (n=72, games=23) (1 suppressed)
- selected_trades by horizon: LIVE: ROI -0.079 (n=442, games=28); T-10: ROI -0.108 (n=183, games=28); T-30: ROI -0.053 (n=282, games=28); T-60: ROI -0.066 (n=281, games=28); T-90: ROI -0.106 (n=278, games=28)
- selected_trades by family: game_spread: ROI -0.463 (n=65, games=14); game_total: ROI -0.211 (n=97, games=21); player_assists: ROI +0.011 (n=354, games=27); player_points: ROI -0.038 (n=479, games=28); player_pra: ROI -0.050 (n=232, games=27); player_rebounds: ROI -0.359 (n=98, games=22); player_threes: ROI +0.154 (n=77, games=16); team_total: ROI -0.376 (n=62, games=14) (1 suppressed)
- all_candidates by side: NO: ROI -0.062 (n=107374, games=28); YES: ROI -0.177 (n=107374, games=28)
- all_candidates by price_range: 0.0-0.2: ROI -0.390 (n=39862, games=28); 0.2-0.4: ROI -0.217 (n=40653, games=28); 0.4-0.6: ROI -0.105 (n=38585, games=28); 0.6-0.8: ROI -0.084 (n=37543, games=28); 0.8-1.0: ROI -0.075 (n=58105, games=28)
- all_candidates by horizon: LAST_VALID: ROI -0.095 (n=16990, games=28); LIVE: ROI -0.124 (n=130036, games=28); T-10: ROI -0.084 (n=17000, games=28); T-30: ROI -0.082 (n=16968, games=28); T-60: ROI -0.086 (n=16916, games=28); T-90: ROI -0.086 (n=16838, games=28)
- all_candidates by family: game_spread: ROI -0.066 (n=26090, games=28); game_total: ROI -0.068 (n=22968, games=28); game_winner: ROI -0.069 (n=1584, games=28); player_assists: ROI -0.122 (n=25624, games=28); player_points: ROI -0.109 (n=29772, games=28); player_pra: ROI -0.186 (n=12424, games=28); player_rebounds: ROI -0.141 (n=33512, games=28); player_threes: ROI -0.118 (n=32680, games=28); team_total: ROI -0.088 (n=30094, games=28)

## By day

- 2026-10-20: 3 games, 130 player-games, minutes MAE +5.39, bias -0.88
- 2026-10-21: 11 games, 510 player-games, minutes MAE +6.12, bias -0.51
- 2026-10-22: 2 games, 77 player-games, minutes MAE +3.99, bias +1.37
- 2026-10-23: 12 games, 480 player-games, minutes MAE +5.21, bias +0.94
