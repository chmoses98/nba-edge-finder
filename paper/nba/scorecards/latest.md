# NBA paper-system scorecard (research only)

_generated 2026-10-30T11:12:20Z · window 7 d · prospective_only=True · nothing here is a bet recommendation_

## Sample (independent units)

- forecast settlements: 24476 rows over 55 games / 2187 player-games; team games 55
- paper decisions: {'n_games': 65, 'n_player_games': 736, 'n_theses': 2998, 'n_decisions': 957330, 'n_contracts': 17221}; settled 314828

**Integrity counters** (excluded / dropped records): decisions_raw=1301058, paper_settlements_raw=379806, decisions_bad_identity_excluded=105198, decisions_invalid_price_excluded=23712, paper_settlements_orphaned=64978

## Projection accuracy

**Minutes (conditional on playing; bias = pred - actual)**

| model | n (games) | MAE | bias [95% CI] |
|---|---|---|---|
| challenger | 1223 (55) | 4.86 | +0.45 [-0.09, +0.94] |
| incumbent | 1043 (53) | 6.47 | -0.91 [-1.50, -0.33] |
| naive_prior_mean | 805 (42) | 5.19 | -0.64 [-1.28, -0.01] |

Paired challenger - incumbent on 1043 player-games: MAE diff -1.70 [-2.00, -1.39]; bias diff +1.22 [+0.81, +1.63] (negative = challenger better)

**Participation Brier**

| model | n | Brier [95% CI] | mean p | played |
|---|---|---|---|---|
| challenger | 1904 | +0.1026 [+0.0916, +0.1138] | 0.693 | 0.642 |
| incumbent | 1578 | +0.1379 [+0.1277, +0.1491] | 0.697 | 0.661 |

**Player stats, conditional on playing**

| family | n | MAE | bias [95% CI] | CRPS | 80% cover | vs incumbent MAE diff |
|---|---|---|---|---|---|---|
| assists | 1223 | 1.30 | +0.00 [-0.10, +0.10] | +0.886 | 80% | -0.106 [-0.152, -0.062] |
| fga | 1223 | 2.75 | +0.18 [-0.02, +0.37] | +1.916 | 81% | n/a |
| points | 1223 | 4.59 | +0.32 [+0.02, +0.63] | +3.183 | 79% | -0.519 [-0.717, -0.309] |
| pra | 1223 | 6.09 | +0.22 [-0.25, +0.67] | +4.277 | 76% | n/a |
| rebounds | 1223 | 1.89 | -0.11 [-0.27, +0.03] | +1.314 | 78% | -0.224 [-0.290, -0.159] |
| threes | 1223 | 0.87 | -0.01 [-0.06, +0.05] | +0.570 | 78% | -0.044 [-0.069, -0.021] |

**Participation vs production (points)**: unconditional error +0.31 [+0.14, +0.47]; participation component MSE 2.80, conditional-production component MSE 23.09

**Team**: team points bias +1.62 [-0.76, +4.13], MAE 10.07

## Market performance

**Model vs market mid** (55 games, 711 player-games, 16121 contracts): Brier diff (model - market) +0.0076 [+0.0041, +0.0114]; one contract/thesis/horizon: +0.0124 [+0.0075, +0.0179]
  - T-90: +0.0079 [+0.0045, +0.0115] (n_contracts 15426)
  - T-60: +0.0082 [+0.0048, +0.0117] (n_contracts 15541)
  - T-30: +0.0084 [+0.0050, +0.0116] (n_contracts 15973)
  - T-10: +0.0084 [+0.0051, +0.0115] (n_contracts 15737)
  - LAST_VALID: +0.0084 [+0.0051, +0.0118] (n_contracts 16019)

| strategy | all candidates: n / ROI | selected (1/thesis): n / games / ROI [95% CI] | verdict | CLV cents (valid closes) |
|---|---|---|---|---|
| PF_ALL_CANDIDATES_V1 | 310840 / -0.103 | no trades | n/a | n/a |
| PF_EDGE_STRICT_V1 | 818 / -0.191 | 263 / 54 / -0.170 [-0.326, -0.019] | NO_EVIDENCE_OF_VALUE | -0.68 [-1.06, -0.28] |
| PF_EDGE_V1 | 3170 / -0.171 | 654 / 55 / -0.125 [-0.202, -0.050] | NO_EVIDENCE_OF_VALUE | -0.29 [-0.76, +0.21] |

Benchmarks: NO_BET_V1 ROI 0 by definition; MARKET_ONLY_V1 = quote mid (scored above); control SHADOW_PURE_PREREG_V1 is read from nba-shadow-pure by the weekly report.

**Price discovery** (share of OPEN->close Brier improvement achieved by horizon): T-90: 0.95, T-60: 0.88, T-30: 0.93, T-10: 0.93, LAST_VALID: 1.00

**Liquidity**: median spread 0.03, quality gate passed 0.8534643226473629, displayed size >= 1: 0.09598257654100467

## Segments (cells below the minimum sample are suppressed)

- minutes bias by minutes_bucket: 12-20: +1.22 [+0.47, +1.87] (n=301); 20-28: -0.03 [-0.89, +0.86] (n=391); <12: +0.89 [-0.50, +2.19] (n=171); >28: +0.11 [-0.85, +1.12] (n=360)
- minutes bias by role_proxy: bench(<18 pred min): +1.03 [+0.14, +2.00] (n=385); rotation(18-28): +0.23 [-0.51, +1.02] (n=478); starter-like(>28): +0.11 [-0.85, +1.12] (n=360)
- minutes bias by injury_status: LIKELY_ACTIVE: +0.47 [-0.09, +0.96] (n=1193); UNCERTAIN: -0.50 [-2.90, +1.63] (n=30)
- minutes bias by freshness: <2h: +0.41 [-0.12, +0.92] (n=1177) (1 suppressed)
- points bias by minutes_bucket: 12-20: +0.86 [+0.26, +1.44] (n=301); 20-28: +0.11 [-0.47, +0.69] (n=391); <12: +0.25 [-0.46, +0.82] (n=171); >28: +0.15 [-0.71, +1.01] (n=360)
- points bias by role_proxy: bench(<18 pred min): +0.44 [-0.02, +0.89] (n=385); rotation(18-28): +0.36 [-0.09, +0.82] (n=478); starter-like(>28): +0.15 [-0.71, +1.01] (n=360)
- points bias by injury_status: LIKELY_ACTIVE: +0.30 [+0.00, +0.61] (n=1193); UNCERTAIN: +1.04 [-0.74, +2.81] (n=30)
- points bias by freshness: <2h: +0.34 [+0.02, +0.66] (n=1177) (1 suppressed)
- selected_trades by side: NO: ROI -0.072 (n=1637, games=55); YES: ROI -0.285 (n=1218, games=53)
- selected_trades by price_range: 0.0-0.2: ROI -0.120 (n=85, games=28); 0.2-0.4: ROI -0.232 (n=1101, games=55); 0.4-0.6: ROI -0.152 (n=1612, games=55); 0.6-0.8: ROI -0.002 (n=200, games=43) (1 suppressed)
- selected_trades by horizon: LIVE: ROI -0.104 (n=782, games=55); T-10: ROI -0.158 (n=354, games=54); T-30: ROI -0.177 (n=582, games=55); T-60: ROI -0.172 (n=572, games=54); T-90: ROI -0.175 (n=565, games=54)
- selected_trades by family: game_spread: ROI -0.256 (n=200, games=37); game_total: ROI -0.257 (n=215, games=43); game_winner: ROI -0.132 (n=61, games=40); player_assists: ROI -0.112 (n=513, games=50); player_points: ROI -0.098 (n=1033, games=55); player_pra: ROI -0.022 (n=351, games=51); player_rebounds: ROI -0.430 (n=155, games=36); player_threes: ROI -0.205 (n=147, games=33); team_total: ROI -0.299 (n=201, games=32)
- all_candidates by side: NO: ROI -0.086 (n=155420, games=55); YES: ROI -0.126 (n=155420, games=55)
- all_candidates by price_range: 0.0-0.2: ROI -0.340 (n=57525, games=55); 0.2-0.4: ROI -0.199 (n=60471, games=55); 0.4-0.6: ROI -0.113 (n=56590, games=55); 0.6-0.8: ROI -0.078 (n=54800, games=55); 0.8-1.0: ROI -0.068 (n=81454, games=55)
- all_candidates by horizon: LAST_VALID: ROI -0.095 (n=32278, games=55); LIVE: ROI -0.116 (n=152298, games=55); T-10: ROI -0.086 (n=31714, games=54); T-30: ROI -0.089 (n=32182, games=55); T-60: ROI -0.090 (n=31314, games=54); T-90: ROI -0.091 (n=31054, games=54)
- all_candidates by family: game_spread: ROI -0.078 (n=39650, games=55); game_total: ROI -0.089 (n=34942, games=55); game_winner: ROI -0.068 (n=2924, games=55); player_assists: ROI -0.104 (n=35916, games=55); player_points: ROI -0.093 (n=41806, games=55); player_pra: ROI -0.175 (n=17728, games=55); player_rebounds: ROI -0.119 (n=47604, games=55); player_threes: ROI -0.101 (n=45614, games=55); team_total: ROI -0.100 (n=44656, games=55)

## By day

- 2026-10-23: 12 games, 480 player-games, minutes MAE +5.21, bias +0.94
- 2026-10-24: 8 games, 322 player-games, minutes MAE +4.99, bias -0.26
- 2026-10-25: 7 games, 270 player-games, minutes MAE +4.54, bias +0.66
- 2026-10-26: 9 games, 360 player-games, minutes MAE +5.44, bias +0.37
- 2026-10-27: 4 games, 161 player-games, minutes MAE +4.05, bias +0.77
- 2026-10-28: 12 games, 476 player-games, minutes MAE +4.53, bias +0.11
- 2026-10-29: 3 games, 118 player-games, minutes MAE +4.48, bias +0.77
