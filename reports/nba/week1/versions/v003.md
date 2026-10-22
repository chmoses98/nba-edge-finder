# NBA research report: week 1 (2026-10-20 .. 2026-10-26 ET)

**Status: PRELIMINARY** (version 3, generated 2026-10-22T11:07:28Z). Research / paper only.

> PRELIMINARY: the week is not over or settlements/outcomes are incomplete; numbers will change.
> SAMPLE SIZE: 16 independent games in this report. Week-1 evidence cannot establish profitability: the preregistered control needs >= 200 independent decisions across >= 40 games with positive clustered lower confidence bounds before any VALIDATED_VALUE language is allowed.
> NO BETTING AUTHORITY: nothing in this report authorises a wager, a stake change or a model promotion. All trades are paper.

| independent games | player-games | theses | decisions | contracts |
|---|---|---|---|---|
| 16 | 640 | 893 | 360306 | 4922 |

## 1. Data integrity

### Data integrity (2026-10-20 .. 2026-10-26 ET)

- games scheduled: **38** (36 not yet covered by a projection slot (30 h window)), started: 0, fully complete evidence: **0**
- missing evidence counts: none
- pregame slots expected 5, executed/covered 5, missed: none

| game | tip (UTC) | forecasts | obs | game fc | snapshots | decisions | outcome | missing |
|---|---|---|---|---|---|---|---|---|
| CLE@PHI | 10-22T23:00 | 8 fam / 5 v | 171 | y | LIVE | 9716 | n | - |
| DEN@OKC | 10-23T01:30 | 8 fam / 4 v | 122 | y | LIVE | 6090 | n | - |


## 2. Projection performance

- minutes challenger: n=322 MAE +5.967 bias -0.585 [-2.027, +0.694]
- minutes incumbent: n=191 MAE +11.637 bias +11.533 [+10.439, +12.731]
- minutes naive_prior_mean: n=None MAE n/a bias n/a
- participation Brier: +0.125 [+0.087, +0.164] (n=485, games=14); mean P(play) +0.732 vs played rate +0.664
- assists (conditional on playing): n=322 games=14 MAE +1.339 bias -0.182 [-0.389, +0.024] CRPS +0.929 [+0.834, +1.024]
- fga (conditional on playing): n=322 games=14 MAE +3.017 bias -0.245 [-0.717, +0.224] CRPS +2.124 [+1.961, +2.281]
- points (conditional on playing): n=322 games=14 MAE +4.696 bias -0.475 [-1.172, +0.240] CRPS +3.279 [+2.981, +3.576]
- pra (conditional on playing): n=322 games=14 MAE +6.004 bias -0.743 [-1.759, +0.326] CRPS +4.299 [+3.878, +4.745]
- rebounds (conditional on playing): n=322 games=14 MAE +1.799 bias -0.194 [-0.535, +0.094] CRPS +1.255 [+1.125, +1.402]
- threes (conditional on playing): n=322 games=14 MAE +0.837 bias +0.064 [-0.061, +0.192] CRPS +0.537 [+0.493, +0.586]
- team points: MAE +9.558, margin MAE +16.309, total MAE +11.769

## 3. Market comparison

contracts (ladder rungs of a player-game are correlated); CIs resample games

| horizon | contracts | games | Brier model | Brier market mid | diff (model - market) |
|---|---|---|---|---|---|
| T-90 | 4217 | 14 | +0.167 | +0.155 | +0.012 [+0.003, +0.021] |
| T-60 | 4248 | 14 | +0.166 | +0.154 | +0.011 [+0.002, +0.020] |
| T-30 | 4256 | 14 | +0.166 | +0.154 | +0.011 [+0.001, +0.021] |
| T-10 | 4261 | 14 | +0.166 | +0.154 | +0.012 [+0.004, +0.020] |
| LAST_VALID | 4272 | 14 | +0.166 | +0.155 | +0.011 [+0.003, +0.020] |

## 4. Paper trading

Hypothetical net ROI after fees and slippage (paper only). `selected` = one contract per thesis per horizon; `all candidates` rows are not independent.

| strategy | view | decisions | contracts | theses | games | ROI | ROI CI | hit rate |
|---|---|---|---|---|---|---|---|---|
| PF_ALL_CANDIDATES_V1 | all candidates | 115134 | 4299 | 777 | 14 | -0.115 | [-0.120, -0.110] | +0.500 |
| PF_EDGE_STRICT_V1 | selected | 54 | 54 | 54 | 13 | -0.055 | [-0.456, +0.285] | +0.444 |
| PF_EDGE_STRICT_V1 | all candidates | 166 | 62 | 54 | 13 | -0.163 | [-0.500, +0.218] | +0.392 |
| PF_EDGE_V1 | selected | 201 | 201 | 201 | 14 | -0.096 | [-0.259, +0.058] | +0.430 |
| PF_EDGE_V1 | all candidates | 1208 | 287 | 201 | 14 | -0.097 | [-0.307, +0.138] | +0.401 |

Baselines: NO_BET_V1 = 0 by definition; MARKET_ONLY_V1 = quote mid (see section 3); control SHADOW_PURE_PREREG_V1 is read from the shadow branch (see Control).

**Expression ranking** (which market best expresses a basketball thesis; research only): 4144 theses scored, 12029 NO_TRADE, status OK

## 5. Market families

Hit rate of the side actually evaluated, by family (descriptive; sample sizes shown).

| family | contracts | games | hit rate |
|---|---|---|---|
| game_spread | None | 14 | +0.500 |
| game_total | None | 14 | +0.499 |
| game_winner | None | 14 | +0.499 |
| player_assists | None | 14 | +0.498 |
| player_points | None | 14 | +0.498 |
| player_pra | None | 14 | +0.497 |
| player_rebounds | None | 14 | +0.498 |
| player_threes | None | 14 | +0.500 |
| team_total | None | 14 | +0.499 |

## 6. Timing

share_h = sum(B_ref - B_h) / sum(B_ref - B_close), B = (mid - y_yes)^2 on contracts present at ref, h and close

| horizon | contracts | games | share of open->close improvement | mean abs move to close |
|---|---|---|---|---|
| T-90 | 1248 | 14 | +0.737 | +0.009 |
| T-60 | 1248 | 14 | +0.826 | +0.007 |
| T-30 | 1248 | 14 | +0.956 | +0.006 |
| T-10 | 1248 | 14 | +0.969 | +0.004 |
| LAST_VALID | 1248 | 14 | +1.000 | +0.000 |

## 7. Player matchup diagnostics

Segment tables (player, team, stat family, minutes bucket, starter proxy, injury status, opponent, home/away, price range, side, threshold, window, confidence/freshness) are in `report.json` under `sections.7_player_matchup_diagnostics`; cells below the minimum counts are suppressed.

## 8. Patterns

> INSUFFICIENT_SAMPLE: 16 games. Nothing here authorises a change to production parameters or betting; first-week results are never promotion evidence.

Leads are classified, never promoted. `p_holm` is Holm-adjusted over the declared family; exploratory screens use Benjamini-Hochberg (q=0.10).

| id | claim | class | effect | 95% CI | p (Holm) | games needed (observed effect) | note |
|---|---|---|---|---|---|---|---|
| H02 | the old simulator under-predicts minutes (negative bias) | PROJECTION_CALIBRATION_ISSUE | +11.533 | [+10.439, +12.731] | +0.000 | 1 | Holm-significant and larger than the equivalence margin |
| H03 | P(play) is mis-calibrated in the large | INCONCLUSIVE | +0.068 | [+0.002, +0.131] | +0.319 | 27 | not established either way |
| H06 | the model beats the market mid at T-60 (Brier, points-ladder and other props) | EVIDENCE_AGAINST | +0.011 | [+0.002, +0.020] | +0.151 | 20 | the effect has the opposite sign with a 95% CI excluding 0 |
| H04 | points projections are biased | INCONCLUSIVE | -0.475 | [-1.172, +0.240] | +1.000 | 65 | not established either way |
| H12 | more than 20% of candidate sides fail the quality / executability gate | EVIDENCE_AGAINST | -0.028 | [-0.041, -0.015] | +0.000 | 22 | within the materiality margin |
| H08 | PF_EDGE_V1 selected trades earn positive net P&L (1 per thesis) | INCONCLUSIVE | -0.043 | [-0.117, +0.025] | +1.000 | 92 | effect not distinguishable from 0 at this sample |
| H07 | the model beats the market mid at some pregame window overall | EVIDENCE_AGAINST | +0.007 | [-0.001, +0.015] | +0.689 | 38 | 95% CI lies inside +/-0.002 (practically no effect) |
| H01 | challenger minutes forecasts are biased | INCONCLUSIVE | -0.585 | [-2.027, +0.694] | +1.000 | 181 | not established either way |
| H11 | selected trades beat the closing line (positive CLV, valid closes only) | INCONCLUSIVE | -0.199 | [-0.927, +0.525] | +1.000 | 417 | effect not distinguishable from 0 at this sample |
| H05 | 80% central intervals for points do not cover 80% | INCONCLUSIVE | -0.017 | [-0.066, +0.029] | +1.000 | 203 | not established either way |
| H10 | T-90 market prices are less accurate than T-10/closing prices (late information not yet priced early) | EVIDENCE_AGAINST | -0.001 | [-0.002, +0.001] | +1.000 | 343 | 95% CI lies inside +/-0.002 (practically no effect) |
| H09 | NO-side (fade the ladder) candidates earn positive net P&L | INCONCLUSIVE | +0.000 | [-0.032, +0.032] | +1.000 | 162573 | effect not distinguishable from 0 at this sample |
| H13 | the DNP fair-price settlement costs more than a void policy assumes | INCONCLUSIVE | n/a | n/a | n/a | n/a | fewer than 2 games |

Exploratory screen: OK

## 9. Root cause

> INSUFFICIENT_SAMPLE: 16 games; every statistic below is descriptive, not a finding

Minutes under-prediction verdict: **INCUMBENT_BIAS_NOT_NEGATIVE**

| # | class | status | statistic | value | games | repeatability | reading |
|---|---|---|---|---|---|---|---|
| 1 | participation | MEASURED | mean(P(play) - played), challenger | +0.068 [+0.002, +0.131] | 14 | {'n_days': 2, 'share_same_sign': 1.0, 'note': ''} | P(play) is over-confident by 0.068 on average; Brier 0.1249. Participation errors enter unconditional stat error through (p - played) * mu; see decomposition. |
| 2 | starter_rotation_assumptions | MEASURED | minutes bias by role proxy (starter-like - bench) | n/a | 14 | {'n_days': 2, 'share_same_sign': 1.0, 'note': ''} | Role = predicted-minutes bucket (a proxy: starter flags are not archived with outcomes). A starter-minus-bench bias gap away from 0 means the rotation shape (not the overall level) is wrong; bias is conditional on playing. |
| 3 | minutes_allocation | MEASURED | minutes bias (pred - actual), challenger vs incumbent, paired | n/a | 14 | {'n_days': 2, 'share_same_sign': 1.0, 'note': ''} | verdict on the old simulator's systematic minutes under-prediction: INCUMBENT_BIAS_NOT_NEGATIVE. Challenger bias -0.59 [-2.03, +0.69] min. |
| 4 | usage_and_per_minute_rates | MEASURED | error = r_pred*(m_pred - m_act) + m_act*(r_pred - r_act): rate component, points | -0.027 [-0.438, +0.389] | n/a | {'n_days': 2, 'share_same_sign': 0.5, 'note': ''} | Per-minute rate (usage) accounts for ~71% of the squared-error budget (rate vs minutes components, points); a rate-component mean away from 0 is a usage / efficiency bias independent of minutes. |
| 5 | opponent_adjustment | NO_DATA | points bias: generous minus stingy opponents | n/a | n/a | n/a | NO_DATA: opponent-defence terciles need earlier final games in team_outcomes (unknown early in the season) and game_forecasts |
| 6 | pace | MEASURED | game total error (pred - actual) and correlation with mean player-points error | +4.744 [-1.887, +11.155] | 14 | n/a | Game-total bias +4.74 [-1.89, +11.16]; per-game correlation between total error and mean player-points error: 0.6542922265904381. A high correlation points at pace/environment (shared by all players) rather than player-specific rates. |
| 7 | distribution_shape_tails | MEASURED | PIT variance ratio / tail excess (observed share beyond the 10%/90% quantiles minus 10%) | +0.037 [-0.003, +0.079] | n/a | n/a | Largest departure of PIT variance from 1: minutes (1.22; >1 = too narrow). Upper-tail excess > 0 means actual outcomes exceed the forecast 90th percentile more often than 10%. |
| 8 | injury_information | MEASURED | participation Brier: official-report (REPORTED) minus unverified/projected information states | n/a | 14 | {'n_days': 2, 'share_same_sign': 1.0, 'note': ''} | A negative gap means official reports sharpen P(play) as intended; ~0 means the report adds nothing measurable yet (e.g. opening week). |
| 9 | market_timing | MEASURED | model-minus-market Brier at each pregame window (negative = model better), plus market price discovery | +0.007 [-0.001, +0.015] | 14 | n/a | Window with the smallest (best) model-minus-market gap: LAST_VALID. Prices converge toward the closing line; see price_discovery shares. A model edge that exists only at early windows and vanishes by T-10 is a timing signal, not yet value. |
| 10 | fees_settlement_execution | MEASURED | per-contract trading costs (fee + slippage) and the gross-to-net P&L gap; DNP settlement effect | +0.026 [+0.026, +0.026] | 14 | {'n_days': 2, 'share_same_sign': 1.0, 'note': ''} | Costs average 0.026 per contract; compare with the model's gross edge before reading any ROI. DNP legs and non-executable quotes are listed separately. |

## 10. Next week plan

1. **PROJECTION_CALIBRATION_ISSUE**: the old simulator under-predicts minutes (negative bias). Acceptance: effect keeps its sign over the next prospective sample and the Holm-adjusted p < 0.05 over the declared family

## Control and gates

```json
{
 "control": {
  "status": "OK",
  "strategy_id": "SHADOW_PURE_PREREG_V1",
  "evaluated_at": "2026-10-22T03:59:28.180261+00:00",
  "source_file": "scorecards/value/dt=2026-10-22/scorecards_value_20261022T035928Z_39719786082.jsonl.gz",
  "n_arms": 4,
  "arm": "sim_rotation",
  "capture_window": "pretip",
  "n_decisions": 178,
  "n_games": 7,
  "verdict": "INSUFFICIENT_SAMPLE",
  "verdict_reasons": [
   "n_decisions 178 < preregistered min_decisions 200",
   "n_games 7 < preregistered min_games 40"
  ],
  "preregistration_sha256": "af2240994739dbd04a89bd2f9d74f56970f8e7189d1dbe73d5deb069d9b2e05b",
  "thresholds": {
   "min_decisions": 200,
   "min_games": 40,
   "min_roi_ci_lower": 0.0
  },
  "roi": null,
  "note": "read-only view of the preregistered control; dry-run diagnostic; no wagering authority"
 },
 "gates": {
  "PF_ALL_CANDIDATES_V1": {
   "strategy_id": "PF_ALL_CANDIDATES_V1",
   "betting_authority": "NONE",
   "week1": true,
   "verdict": "INSUFFICIENT_SAMPLE",
   "verdict_reasons": [
    "n_decisions 0 < preregistered min_decisions 200",
    "n_games 0 < preregistered min_games 40"
   ],
   "required_prospective_sample": {
    "min_independent_decisions": 200,
    "min_games": 40,
    "roi_ci_lower_bound": "> 0.0 for every clustered CI (game, player)",
    "protocol": "chronological, prospective, preregistered before scoring, original model versions"
   },
   "remaining": {
    "decisions": 200,
    "games": 40
   },
   "statement": "Week 1 grants no betting authority; this is evidence collection only."
  },
  "PF_EDGE_STRICT_V1": {
   "strategy_id": "PF_EDGE_STRICT_V1",
   "betting_authority": "NONE",
   "week1": true,
   "verdict": "INSUFFICIENT_SAMPLE",
   "verdict_reasons": [
    "n_decisions 54 < preregistered min_decisions 200",
    "n_games 13 < preregistered min_games 40"
   ],
   "required_prospective_sample": {
    "min_independent_decisions": 200,
    "min_games": 40,
    "roi_ci_lower_bound": "> 0.0 for every clustered CI (game, player)",
    "protocol": "chronological, prospective, preregistered before scoring, original model versions"
   },
   "remaining": {
    "decisions": 146,
    "games": 27
   },
   "statement": "Week 1 grants no betting authority; this is evidence collection only."
  },
  "PF_EDGE_V1": {
   "strategy_id": "PF_EDGE_V1",
   "betting_authority": "NONE",
   "week1": true,
   "verdict": "INSUFFICIENT_SAMPLE",
   "verdict_reasons": [
    "n_games 14 < preregistered min_games 40"
   ],
   "required_prospective_sample": {
    "min_independent_decisions": 200,
    "min_games": 40,
    "roi_ci_lower_bound": "> 0.0 for every clustered CI (game, player)",
    "protocol": "chronological, prospective, preregistered before scoring, original model versions"
   },
   "remaining": {
    "decisions": 0,
    "games": 26
   },
   "statement": "Week 1 grants no betting authority; this is evidence collection only."
  }
 }
}
```

## Methods

```json
{
 "independent_unit": "game (cluster); player-game secondary; contracts, snapshots, YES/NO complements and ladder rungs are never treated as independent",
 "bootstrap": {
  "replicates": 2000,
  "seed": 20261020,
  "cluster": "game"
 },
 "paper_trading": "docs/research/PAPER_ENGINE_SPEC.md",
 "point_in_time": "forecasts/availability/boards as observed at the decision instant",
 "multiple_testing": "Holm on the declared confirmatory family, Benjamini-Hochberg q=0.10 for exploratory screens",
 "dnp": "player-prop DNP settles at the pre-game fair price (scalar), not NO and not a fee-free void"
}
```
