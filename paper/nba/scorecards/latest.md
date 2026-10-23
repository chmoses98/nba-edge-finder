# NBA paper-system scorecard (research only)

_generated 2026-10-23T11:07:02Z · window 7 d · prospective_only=True · nothing here is a bet recommendation_

> **INSUFFICIENT_SAMPLE: 28 games with evidence in this window (the preregistered minimum for a value verdict is 40 games and 200 independent decisions); nothing below is a finding**

## Sample (independent units)

- forecast settlements: 7051 rows over 16 games / 717 player-games; team games 16
- paper decisions: {'n_games': 28, 'n_player_games': 315, 'n_theses': 1298, 'n_decisions': 443208, 'n_contracts': 7451}; settled 132361

**Integrity counters** (excluded / dropped records): decisions_raw=493793, paper_settlements_raw=132361, decisions_bad_identity_excluded=42479, decisions_invalid_price_excluded=8106

## Projection accuracy

**Minutes (conditional on playing; bias = pred - actual)**

| model | n (games) | MAE | bias [95% CI] |
|---|---|---|---|
| challenger | 367 (16) | 5.73 | -0.35 [-1.79, +0.88] |
| incumbent | 208 (15) | 11.13 | +10.84 [+9.06, +12.36] |
| naive_prior_mean | 22 (2) | 2.55 | +0.00 |

Paired challenger - incumbent on 208 player-games: MAE diff -6.10 [-7.44, -4.82]; bias diff -10.74 [-12.03, -8.99] (negative = challenger better)

**Participation Brier**

| model | n | Brier [95% CI] | mean p | played |
|---|---|---|---|---|
| challenger | 553 | +0.1206 [+0.0870, +0.1570] | 0.727 | 0.664 |
| incumbent | 439 | +0.2413 [+0.2285, +0.2496] | 0.493 | 0.474 |

**Player stats, conditional on playing**

| family | n | MAE | bias [95% CI] | CRPS | 80% cover | vs incumbent MAE diff |
|---|---|---|---|---|---|---|
| assists | 367 | 1.35 | -0.05 [-0.30, +0.20] | +0.924 | 77% | -0.769 [-0.984, -0.587] |
| fga | 367 | 2.94 | -0.18 [-0.60, +0.23] | +2.076 | 77% | n/a |
| points | 367 | 4.62 | -0.18 [-0.94, +0.58] | +3.214 | 80% | -3.597 [-4.766, -2.621] |
| pra | 367 | 5.96 | -0.30 [-1.40, +0.77] | +4.220 | 78% | n/a |
| rebounds | 367 | 1.82 | -0.17 [-0.47, +0.09] | +1.268 | 81% | -1.126 [-1.412, -0.828] |
| threes | 367 | 0.82 | +0.10 [-0.02, +0.21] | +0.521 | 79% | -0.428 [-0.561, -0.313] |

**Participation vs production (points)**: unconditional error +0.07 [-0.23, +0.43]; participation component MSE 3.33, conditional-production component MSE 25.08

**Team**: team points bias +4.21 [+0.24, +8.34], MAE 10.49

## Market performance

**Model vs market mid** (16 games, 211 player-games, 4941 contracts): Brier diff (model - market) +0.0050 [-0.0026, +0.0129]; one contract/thesis/horizon: +0.0049 [-0.0098, +0.0210]
  - T-90: +0.0093 [+0.0004, +0.0183] (n_contracts 4846)
  - T-60: +0.0087 [-0.0002, +0.0181] (n_contracts 4877)
  - T-30: +0.0093 [+0.0003, +0.0183] (n_contracts 4888)
  - T-10: +0.0094 [+0.0018, +0.0175] (n_contracts 4897)
  - LAST_VALID: +0.0087 [+0.0012, +0.0168] (n_contracts 4913)

| strategy | all candidates: n / ROI | selected (1/thesis): n / games / ROI [95% CI] | verdict | CLV cents (valid closes) |
|---|---|---|---|---|
| PF_ALL_CANDIDATES_V1 | 130818 / -0.115 | no trades | n/a | n/a |
| PF_EDGE_STRICT_V1 | 194 / -0.199 | 65 / 15 / -0.116 [-0.473, +0.208] | INSUFFICIENT_SAMPLE | +0.22 [-0.70, +1.34] |
| PF_EDGE_V1 | 1349 / -0.046 | 228 / 16 / -0.035 [-0.206, +0.131] | INSUFFICIENT_SAMPLE | -0.04 [-0.71, +0.63] |

Benchmarks: NO_BET_V1 ROI 0 by definition; MARKET_ONLY_V1 = quote mid (scored above); control SHADOW_PURE_PREREG_V1 is read from nba-shadow-pure by the weekly report.

**Price discovery** (share of OPEN->close Brier improvement achieved by horizon): T-90: 0.52, T-60: 0.69, T-30: 0.90, T-10: 0.94, LAST_VALID: 1.00

**Liquidity**: median spread 0.03, quality gate passed 0.8074944495586722, displayed size >= 1: 0.13494341257378026

## Segments (cells below the minimum sample are suppressed)

- minutes bias by minutes_bucket: 12-20: +0.17 [-1.52, +1.73] (n=137); 20-28: -1.66 [-3.42, -0.03] (n=137); <12: +1.65 [-2.09, +4.59] (n=39); >28: +0.25 [-1.94, +2.38] (n=54)
- minutes bias by role_proxy: bench(<18 pred min): +0.39 [-1.51, +2.01] (n=142); rotation(18-28): -1.14 [-2.90, +0.49] (n=171); starter-like(>28): +0.25 [-1.94, +2.38] (n=54)
- minutes bias by injury_status: LIKELY_ACTIVE: -0.40 [-1.91, +0.84] (n=348) (1 suppressed)
- minutes bias by freshness: <2h: -0.35 [-1.79, +0.88] (n=367)
- points bias by minutes_bucket: 12-20: +0.22 [-0.73, +1.17] (n=137); 20-28: -0.87 [-2.18, +0.47] (n=137); <12: +0.13 [-1.03, +1.24] (n=39); >28: +0.36 [-1.75, +2.79] (n=54)
- points bias by role_proxy: bench(<18 pred min): +0.20 [-0.60, +0.92] (n=142); rotation(18-28): -0.66 [-1.77, +0.47] (n=171); starter-like(>28): +0.36 [-1.75, +2.79] (n=54)
- points bias by injury_status: LIKELY_ACTIVE: -0.26 [-1.06, +0.52] (n=348) (1 suppressed)
- points bias by freshness: <2h: -0.18 [-0.94, +0.58] (n=367)
- selected_trades by side: NO: ROI -0.057 (n=705, games=16); YES: ROI -0.120 (n=137, games=15)
- selected_trades by price_range: 0.0-0.2: ROI +0.485 (n=45, games=10); 0.2-0.4: ROI -0.057 (n=358, games=16); 0.4-0.6: ROI -0.125 (n=474, games=16); 0.6-0.8: ROI +0.423 (n=49, games=14) (1 suppressed)
- selected_trades by horizon: LIVE: ROI -0.081 (n=261, games=16); T-10: ROI -0.057 (n=106, games=16); T-30: ROI -0.053 (n=160, games=16); T-60: ROI -0.058 (n=159, games=16); T-90: ROI -0.064 (n=156, games=16)
- selected_trades by family: game_total: ROI +0.092 (n=57, games=12); player_assists: ROI -0.004 (n=228, games=15); player_points: ROI -0.016 (n=237, games=16); player_pra: ROI +0.002 (n=150, games=16); player_rebounds: ROI -0.262 (n=67, games=14); player_threes: ROI +0.023 (n=49, games=11) (3 suppressed)
- all_candidates by side: NO: ROI -0.068 (n=65409, games=16); YES: ROI -0.184 (n=65409, games=16)
- all_candidates by price_range: 0.0-0.2: ROI -0.369 (n=24195, games=16); 0.2-0.4: ROI -0.200 (n=24513, games=16); 0.4-0.6: ROI -0.104 (n=23328, games=16); 0.6-0.8: ROI -0.095 (n=22454, games=16); 0.8-1.0: ROI -0.090 (n=36328, games=16)
- all_candidates by horizon: LAST_VALID: ROI -0.101 (n=9880, games=16); LIVE: ROI -0.130 (n=81706, games=16); T-10: ROI -0.086 (n=9848, games=16); T-30: ROI -0.085 (n=9830, games=16); T-60: ROI -0.088 (n=9808, games=16); T-90: ROI -0.087 (n=9746, games=16)
- all_candidates by family: game_spread: ROI -0.065 (n=15708, games=16); game_total: ROI -0.067 (n=13804, games=16); game_winner: ROI -0.070 (n=952, games=16); player_assists: ROI -0.129 (n=15702, games=16); player_points: ROI -0.113 (n=17908, games=16); player_pra: ROI -0.197 (n=7574, games=16); player_rebounds: ROI -0.150 (n=19816, games=16); player_threes: ROI -0.124 (n=21268, games=16); team_total: ROI -0.094 (n=18086, games=16)

## By day

- 2026-10-20: 3 games, 130 player-games, minutes MAE +5.39, bias -0.88
- 2026-10-21: 11 games, 510 player-games, minutes MAE +6.12, bias -0.51
- 2026-10-22: 2 games, 77 player-games, minutes MAE +3.99, bias +1.37
