# NBA paper-system scorecard (research only)

_generated 2026-10-25T11:14:26Z · window 7 d · prospective_only=True · nothing here is a bet recommendation_

## Sample (independent units)

- forecast settlements: 16118 rows over 36 games / 1519 player-games; team games 36
- paper decisions: {'n_games': 43, 'n_player_games': 483, 'n_theses': 2005, 'n_decisions': 760920, 'n_contracts': 11430}; settled 255305

**Integrity counters** (excluded / dropped records): decisions_raw=862849, paper_settlements_raw=255305, decisions_bad_identity_excluded=80389, decisions_invalid_price_excluded=21540

## Projection accuracy

**Minutes (conditional on playing; bias = pred - actual)**

| model | n (games) | MAE | bias [95% CI] |
|---|---|---|---|
| challenger | 810 (36) | 5.40 | +0.11 [-0.73, +0.91] |
| incumbent | 599 (35) | 8.62 | +3.05 [+1.14, +5.05] |
| naive_prior_mean | 424 (22) | 4.81 | -0.67 [-1.46, +0.15] |

Paired challenger - incumbent on 599 player-games: MAE diff -3.60 [-4.49, -2.79]; bias diff -2.87 [-4.87, -1.04] (negative = challenger better)

**Participation Brier**

| model | n | Brier [95% CI] | mean p | played |
|---|---|---|---|---|
| challenger | 1247 | +0.1160 [+0.0970, +0.1351] | 0.715 | 0.650 |
| incumbent | 1033 | +0.1856 [+0.1664, +0.2040] | 0.611 | 0.580 |

**Player stats, conditional on playing**

| family | n | MAE | bias [95% CI] | CRPS | 80% cover | vs incumbent MAE diff |
|---|---|---|---|---|---|---|
| assists | 810 | 1.31 | -0.06 [-0.21, +0.10] | +0.901 | 79% | -0.362 [-0.495, -0.243] |
| fga | 810 | 2.83 | +0.01 [-0.25, +0.26] | +1.993 | 79% | n/a |
| points | 810 | 4.66 | -0.03 [-0.51, +0.45] | +3.247 | 79% | -1.647 [-2.273, -1.093] |
| pra | 810 | 6.14 | -0.20 [-0.92, +0.50] | +4.341 | 75% | n/a |
| rebounds | 810 | 1.83 | -0.15 [-0.33, +0.02] | +1.273 | 82% | -0.589 [-0.779, -0.422] |
| threes | 810 | 0.82 | +0.03 [-0.05, +0.10] | +0.538 | 79% | -0.190 [-0.269, -0.124] |

**Participation vs production (points)**: unconditional error +0.14 [-0.07, +0.35]; participation component MSE 2.74, conditional-production component MSE 24.18

**Team**: team points bias +1.67 [-1.21, +4.57], MAE 9.60

## Market performance

**Model vs market mid** (36 games, 471 player-games, 10733 contracts): Brier diff (model - market) +0.0059 [+0.0008, +0.0114]; one contract/thesis/horizon: +0.0083 [-0.0009, +0.0181]
  - T-90: +0.0082 [+0.0029, +0.0138] (n_contracts 10518)
  - T-60: +0.0079 [+0.0024, +0.0132] (n_contracts 10568)
  - T-30: +0.0084 [+0.0030, +0.0140] (n_contracts 10619)
  - T-10: +0.0084 [+0.0035, +0.0136] (n_contracts 10654)
  - LAST_VALID: +0.0079 [+0.0031, +0.0128] (n_contracts 10637)

| strategy | all candidates: n / ROI | selected (1/thesis): n / games / ROI [95% CI] | verdict | CLV cents (valid closes) |
|---|---|---|---|---|
| PF_ALL_CANDIDATES_V1 | 252220 / -0.109 | no trades | n/a | n/a |
| PF_EDGE_STRICT_V1 | 483 / -0.116 | 155 / 34 / -0.104 [-0.329, +0.110] | INSUFFICIENT_SAMPLE | -0.41 [-0.94, +0.18] |
| PF_EDGE_V1 | 2602 / -0.107 | 473 / 36 / -0.115 [-0.222, -0.005] | INSUFFICIENT_SAMPLE | -0.61 [-1.14, -0.09] |

Benchmarks: NO_BET_V1 ROI 0 by definition; MARKET_ONLY_V1 = quote mid (scored above); control SHADOW_PURE_PREREG_V1 is read from nba-shadow-pure by the weekly report.

**Price discovery** (share of OPEN->close Brier improvement achieved by horizon): T-90: 0.68, T-60: 0.79, T-30: 0.94, T-10: 0.95, LAST_VALID: 1.00

**Liquidity**: median spread 0.03, quality gate passed 0.8529017505125375, displayed size >= 1: 0.11080665510171897

## Segments (cells below the minimum sample are suppressed)

- minutes bias by minutes_bucket: 12-20: +0.60 [-0.50, +1.72] (n=248); 20-28: -1.01 [-2.20, +0.12] (n=283); <12: +1.79 [-0.23, +3.58] (n=98); >28: +0.27 [-1.16, +1.73] (n=181)
- minutes bias by role_proxy: bench(<18 pred min): +0.97 [-0.27, +2.18] (n=279); rotation(18-28): -0.66 [-1.72, +0.34] (n=350); starter-like(>28): +0.27 [-1.16, +1.73] (n=181)
- minutes bias by injury_status: LIKELY_ACTIVE: +0.11 [-0.75, +0.92] (n=783) (1 suppressed)
- minutes bias by freshness: <2h: +0.11 [-0.73, +0.91] (n=810)
- points bias by minutes_bucket: 12-20: +0.48 [-0.20, +1.18] (n=248); 20-28: -0.76 [-1.57, +0.05] (n=283); <12: +0.34 [-0.43, +1.06] (n=98); >28: +0.19 [-1.16, +1.46] (n=181)
- points bias by role_proxy: bench(<18 pred min): +0.28 [-0.25, +0.79] (n=279); rotation(18-28): -0.40 [-1.10, +0.27] (n=350); starter-like(>28): +0.19 [-1.16, +1.46] (n=181)
- points bias by injury_status: LIKELY_ACTIVE: -0.06 [-0.56, +0.42] (n=783) (1 suppressed)
- points bias by freshness: <2h: -0.03 [-0.51, +0.45] (n=810)
- selected_trades by side: NO: ROI -0.074 (n=1378, games=36); YES: ROI -0.134 (n=509, games=33)
- selected_trades by price_range: 0.0-0.2: ROI +0.268 (n=84, games=20); 0.2-0.4: ROI -0.108 (n=760, games=36); 0.4-0.6: ROI -0.110 (n=1074, games=36); 0.6-0.8: ROI +0.102 (n=117, games=29) (1 suppressed)
- selected_trades by horizon: LIVE: ROI -0.104 (n=553, games=36); T-10: ROI -0.084 (n=236, games=36); T-30: ROI -0.074 (n=368, games=36); T-60: ROI -0.060 (n=367, games=36); T-90: ROI -0.108 (n=363, games=36)
- selected_trades by family: game_spread: ROI -0.307 (n=105, games=20); game_total: ROI -0.213 (n=136, games=26); player_assists: ROI +0.007 (n=437, games=34); player_points: ROI -0.102 (n=614, games=36); player_pra: ROI +0.049 (n=289, games=34); player_rebounds: ROI -0.416 (n=108, games=27); player_threes: ROI +0.048 (n=98, games=22); team_total: ROI -0.291 (n=91, games=18) (1 suppressed)
- all_candidates by side: NO: ROI -0.086 (n=126110, games=36); YES: ROI -0.142 (n=126110, games=36)
- all_candidates by price_range: 0.0-0.2: ROI -0.387 (n=46385, games=36); 0.2-0.4: ROI -0.231 (n=48244, games=36); 0.4-0.6: ROI -0.108 (n=45406, games=36); 0.6-0.8: ROI -0.076 (n=44337, games=36); 0.8-1.0: ROI -0.074 (n=67848, games=36)
- all_candidates by horizon: LAST_VALID: ROI -0.098 (n=21398, games=36); LIVE: ROI -0.123 (n=145630, games=36); T-10: ROI -0.087 (n=21432, games=36); T-30: ROI -0.086 (n=21358, games=36); T-60: ROI -0.090 (n=21252, games=36); T-90: ROI -0.091 (n=21150, games=36)
- all_candidates by family: game_spread: ROI -0.066 (n=30690, games=36); game_total: ROI -0.068 (n=27028, games=36); game_winner: ROI -0.069 (n=2016, games=36); player_assists: ROI -0.121 (n=30050, games=36); player_points: ROI -0.107 (n=35146, games=36); player_pra: ROI -0.190 (n=14724, games=36); player_rebounds: ROI -0.141 (n=39382, games=36); player_threes: ROI -0.118 (n=37770, games=36); team_total: ROI -0.087 (n=35414, games=36)

## By day

- 2026-10-20: 3 games, 130 player-games, minutes MAE +5.39, bias -0.88
- 2026-10-21: 11 games, 510 player-games, minutes MAE +6.12, bias -0.51
- 2026-10-22: 2 games, 77 player-games, minutes MAE +3.99, bias +1.37
- 2026-10-23: 12 games, 480 player-games, minutes MAE +5.21, bias +0.94
- 2026-10-24: 8 games, 322 player-games, minutes MAE +4.99, bias -0.26
