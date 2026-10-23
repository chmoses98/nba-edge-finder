# NBA research report: week 1 (2026-10-20 .. 2026-10-26 ET)

**Status: PRELIMINARY** (version 4, generated 2026-10-23T11:09:42Z). Research / paper only.

> PRELIMINARY: the week is not over or settlements/outcomes are incomplete; numbers will change.
> SAMPLE SIZE: 28 independent games in this report. Week-1 evidence cannot establish profitability: the preregistered control needs >= 200 independent decisions across >= 40 games with positive clustered lower confidence bounds before any VALIDATED_VALUE language is allowed.
> NO BETTING AUTHORITY: nothing in this report authorises a wager, a stake change or a model promotion. All trades are paper.

| independent games | player-games | theses | decisions | contracts |
|---|---|---|---|---|
| 28 | 717 | 1298 | 443208 | 7451 |

## 1. Data integrity

### Data integrity (2026-10-20 .. 2026-10-26 ET)

- games scheduled: **38** (24 not yet covered by a projection slot (30 h window)), started: 2, fully complete evidence: **2**
- missing evidence counts: none
- pregame slots expected 11, executed/covered 11, missed: none

| game | tip (UTC) | forecasts | obs | game fc | snapshots | decisions | outcome | missing |
|---|---|---|---|---|---|---|---|---|
| CLE@PHI | 10-22T23:00 | 8 fam / 8 v | 293 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 27954 | y | - |
| DEN@OKC | 10-23T01:30 | 8 fam / 8 v | 278 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 25042 | y | - |
| CHI@MIL | 10-23T20:00 | 8 fam / 5 v | 129 | y | LIVE | 7130 | n | - |
| NYK@BOS | 10-23T23:00 | 8 fam / 4 v | 106 | y | LIVE | 8338 | n | - |
| ATL@CHA | 10-23T23:00 | 8 fam / 4 v | 129 | y | LIVE | 5406 | n | - |
| DAL@IND | 10-23T23:00 | 8 fam / 4 v | 140 | y | LIVE | 3192 | n | - |
| MIN@ORL | 10-23T23:00 | 8 fam / 4 v | 119 | y | LIVE | 6858 | n | - |
| TOR@WAS | 10-23T23:00 | 8 fam / 4 v | 137 | y | LIVE | 2520 | n | - |
| DET@MIA | 10-24T00:00 | 8 fam / 4 v | 127 | y | LIVE | 6980 | n | - |
| HOU@SAS | 10-24T01:30 | 8 fam / 3 v | 120 | y | LIVE | 5880 | n | - |
| NOP@UTA | 10-24T01:30 | 8 fam / 3 v | 99 | y | LIVE | 4042 | n | - |
| MEM@GSW | 10-24T02:00 | 8 fam / 3 v | 92 | y | LIVE | 1890 | n | - |
| LAC@LAL | 10-24T02:00 | 8 fam / 3 v | 97 | y | LIVE | 2388 | n | - |
| POR@SAC | 10-24T02:00 | 8 fam / 3 v | 87 | y | LIVE | 1890 | n | - |


## 2. Projection performance

- minutes challenger: n=367 MAE +5.725 bias -0.345 [-1.791, +0.878]
- minutes incumbent: n=208 MAE +11.134 bias +10.839 [+9.059, +12.357]
- minutes naive_prior_mean: n=22 MAE +2.545 bias +0.000 (CI withheld: TOO_FEW_CLUSTERS (<5 games))
- participation Brier: +0.121 [+0.087, +0.157] (n=553, games=16); mean P(play) +0.727 vs played rate +0.664
- assists (conditional on playing): n=367 games=16 MAE +1.348 bias -0.054 [-0.299, +0.201] CRPS +0.924 [+0.841, +1.014]
- fga (conditional on playing): n=367 games=16 MAE +2.943 bias -0.184 [-0.597, +0.230] CRPS +2.076 [+1.911, +2.238]
- points (conditional on playing): n=367 games=16 MAE +4.623 bias -0.176 [-0.938, +0.576] CRPS +3.214 [+2.952, +3.479]
- pra (conditional on playing): n=367 games=16 MAE +5.955 bias -0.301 [-1.401, +0.772] CRPS +4.220 [+3.853, +4.595]
- rebounds (conditional on playing): n=367 games=16 MAE +1.820 bias -0.175 [-0.465, +0.088] CRPS +1.268 [+1.132, +1.396]
- threes (conditional on playing): n=367 games=16 MAE +0.818 bias +0.097 [-0.023, +0.213] CRPS +0.521 [+0.478, +0.568]
- team points: MAE +10.493, margin MAE +15.260, total MAE +14.558

## 3. Market comparison

contracts (ladder rungs of a player-game are correlated); CIs resample games

| horizon | contracts | games | Brier model | Brier market mid | diff (model - market) |
|---|---|---|---|---|---|
| T-90 | 4846 | 16 | +0.167 | +0.158 | +0.009 [+0.000, +0.018] |
| T-60 | 4877 | 16 | +0.166 | +0.158 | +0.009 [-0.000, +0.018] |
| T-30 | 4888 | 16 | +0.167 | +0.157 | +0.009 [+0.000, +0.018] |
| T-10 | 4897 | 16 | +0.167 | +0.158 | +0.009 [+0.002, +0.017] |
| LAST_VALID | 4913 | 16 | +0.167 | +0.158 | +0.009 [+0.001, +0.017] |

## 4. Paper trading

Hypothetical net ROI after fees and slippage (paper only). `selected` = one contract per thesis per horizon; `all candidates` rows are not independent.

| strategy | view | decisions | contracts | theses | games | ROI | ROI CI | hit rate |
|---|---|---|---|---|---|---|---|---|
| PF_ALL_CANDIDATES_V1 | all candidates | 130818 | 4968 | 902 | 16 | -0.115 | [-0.119, -0.110] | +0.500 |
| PF_EDGE_STRICT_V1 | selected | 65 | 65 | 65 | 15 | -0.116 | [-0.473, +0.208] | +0.415 |
| PF_EDGE_STRICT_V1 | all candidates | 194 | 74 | 65 | 15 | -0.199 | [-0.544, +0.154] | +0.376 |
| PF_EDGE_V1 | selected | 228 | 228 | 228 | 16 | -0.035 | [-0.206, +0.131] | +0.458 |
| PF_EDGE_V1 | all candidates | 1349 | 326 | 228 | 16 | -0.046 | [-0.252, +0.168] | +0.423 |

Baselines: NO_BET_V1 = 0 by definition; MARKET_ONLY_V1 = quote mid (see section 3); control SHADOW_PURE_PREREG_V1 is read from the shadow branch (see Control).

**Expression ranking** (which market best expresses a basketball thesis; research only): 4497 theses scored, 15538 NO_TRADE, status OK

## 5. Market families

Hit rate of the side actually evaluated, by family (descriptive; sample sizes shown).

| family | contracts | games | hit rate |
|---|---|---|---|
| game_spread | None | 16 | +0.499 |
| game_total | None | 16 | +0.499 |
| game_winner | None | 16 | +0.499 |
| player_assists | None | 16 | +0.499 |
| player_points | None | 16 | +0.498 |
| player_pra | None | 16 | +0.498 |
| player_rebounds | None | 16 | +0.498 |
| player_threes | None | 16 | +0.500 |
| team_total | None | 16 | +0.500 |

## 6. Timing

share_h = sum(B_ref - B_h) / sum(B_ref - B_close), B = (mid - y_yes)^2 on contracts present at ref, h and close

| horizon | contracts | games | share of open->close improvement | mean abs move to close |
|---|---|---|---|---|
| T-90 | 1376 | 16 | +0.519 | +0.008 |
| T-60 | 1376 | 16 | +0.691 | +0.007 |
| T-30 | 1376 | 16 | +0.903 | +0.006 |
| T-10 | 1376 | 16 | +0.945 | +0.004 |
| LAST_VALID | 1376 | 16 | +1.000 | +0.000 |

## 7. Player matchup diagnostics

Segment tables (player, team, stat family, minutes bucket, starter proxy, injury status, opponent, home/away, price range, side, threshold, window, confidence/freshness) are in `report.json` under `sections.7_player_matchup_diagnostics`; cells below the minimum counts are suppressed.

## 8. Patterns

> INSUFFICIENT_SAMPLE: 28 games. Nothing here authorises a change to production parameters or betting; first-week results are never promotion evidence.

Leads are classified, never promoted. `p_holm` is Holm-adjusted over the declared family; exploratory screens use Benjamini-Hochberg (q=0.10).

| id | claim | class | effect | 95% CI | p (Holm) | games needed (observed effect) | note |
|---|---|---|---|---|---|---|---|
| H02 | the old simulator under-predicts minutes (negative bias) | PROJECTION_CALIBRATION_ISSUE | +10.839 | [+9.059, +12.357] | +0.000 | 1 | Holm-significant and larger than the equivalence margin |
| H03 | P(play) is mis-calibrated in the large | INCONCLUSIVE | +0.064 | [+0.006, +0.122] | +0.340 | 29 | not established either way |
| H06 | the model beats the market mid at T-60 (Brier, points-ladder and other props) | EVIDENCE_AGAINST | +0.009 | [-0.000, +0.018] | +0.577 | 37 | 95% CI lies inside +/-0.002 (practically no effect) |
| H09 | NO-side (fade the ladder) candidates earn positive net P&L | INCONCLUSIVE | +0.017 | [-0.019, +0.055] | +1.000 | 161 | effect not distinguishable from 0 at this sample |
| H07 | the model beats the market mid at some pregame window overall | INCONCLUSIVE | +0.005 | [-0.003, +0.013] | +1.000 | 82 | effect not distinguishable from 0 at this sample |
| H01 | challenger minutes forecasts are biased | INCONCLUSIVE | -0.345 | [-1.791, +0.878] | +1.000 | 491 | not established either way |
| H04 | points projections are biased | INCONCLUSIVE | -0.176 | [-0.938, +0.576] | +1.000 | 604 | not established either way |
| H08 | PF_EDGE_V1 selected trades earn positive net P&L (1 per thesis) | INCONCLUSIVE | -0.016 | [-0.093, +0.058] | +1.000 | 780 | effect not distinguishable from 0 at this sample |
| H10 | T-90 market prices are less accurate than T-10/closing prices (late information not yet priced early) | EVIDENCE_AGAINST | -0.000 | [-0.002, +0.001] | +1.000 | 323 | 95% CI lies inside +/-0.002 (practically no effect) |
| H12 | more than 20% of candidate sides fail the quality / executability gate | EVIDENCE_AGAINST | -0.007 | [-0.024, +0.017] | +1.000 | 1894 | within the materiality margin |
| H11 | selected trades beat the closing line (positive CLV, valid closes only) | INCONCLUSIVE | -0.037 | [-0.714, +0.632] | +1.000 | 11629 | effect not distinguishable from 0 at this sample |
| H05 | 80% central intervals for points do not cover 80% | EVIDENCE_AGAINST | -0.002 | [-0.041, +0.037] | +1.000 | 21836 | 95% CI inside +/-0.05: no calibration defect of material size detected |
| H13 | the DNP fair-price settlement costs more than a void policy assumes | INCONCLUSIVE | n/a | n/a | n/a | n/a | fewer than 2 games |

Exploratory screen: OK

## 9. Root cause

> INSUFFICIENT_SAMPLE: 28 games; every statistic below is descriptive, not a finding

Minutes under-prediction verdict: **INCUMBENT_BIAS_NOT_NEGATIVE**

| # | class | status | statistic | value | games | repeatability | reading |
|---|---|---|---|---|---|---|---|
| 1 | participation | MEASURED | mean(P(play) - played), challenger | +0.064 [+0.006, +0.122] | 16 | {'n_days': 3, 'share_same_sign': 1.0, 'note': ''} | P(play) is over-confident by 0.064 on average; Brier 0.1206. Participation errors enter unconditional stat error through (p - played) * mu; see decomposition. |
| 2 | starter_rotation_assumptions | MEASURED | minutes bias by role proxy (starter-like - bench) | n/a | 16 | {'n_days': 3, 'share_same_sign': 0.6666666666666666, 'note': ''} | Role = predicted-minutes bucket (a proxy: starter flags are not archived with outcomes). A starter-minus-bench bias gap away from 0 means the rotation shape (not the overall level) is wrong; bias is conditional on playing. |
| 3 | minutes_allocation | MEASURED | minutes bias (pred - actual), challenger vs incumbent, paired | n/a | 16 | {'n_days': 3, 'share_same_sign': 0.6666666666666666, 'note': ''} | verdict on the old simulator's systematic minutes under-prediction: INCUMBENT_BIAS_NOT_NEGATIVE. Challenger bias -0.35 [-1.79, +0.88] min. |
| 4 | usage_and_per_minute_rates | MEASURED | error = r_pred*(m_pred - m_act) + m_act*(r_pred - r_act): rate component, points | +0.171 [-0.282, +0.647] | n/a | {'n_days': 3, 'share_same_sign': 0.6666666666666666, 'note': ''} | Per-minute rate (usage) accounts for ~72% of the squared-error budget (rate vs minutes components, points); a rate-component mean away from 0 is a usage / efficiency bias independent of minutes. |
| 5 | opponent_adjustment | MEASURED | points bias (pred - actual): generous-defence opponents minus stingy ones | n/a | 16 | {'n_days': 3, 'share_same_sign': 0.6666666666666666, 'note': ''} | If the opponent adjustment works this gap is ~0; a negative gap means the model under-projects against generous defences (adjustment too weak). |
| 6 | pace | MEASURED | game total error (pred - actual) and correlation with mean player-points error | +8.411 [+0.615, +17.013] | 16 | n/a | Game-total bias +8.41 [+0.61, +17.01]; per-game correlation between total error and mean player-points error: 0.776614117398203. A high correlation points at pace/environment (shared by all players) rather than player-specific rates. |
| 7 | distribution_shape_tails | MEASURED | PIT variance ratio / tail excess (observed share beyond the 10%/90% quantiles minus 10%) | +0.028 [-0.013, +0.074] | n/a | n/a | Largest departure of PIT variance from 1: minutes (1.17; >1 = too narrow). Upper-tail excess > 0 means actual outcomes exceed the forecast 90th percentile more often than 10%. |
| 8 | injury_information | MEASURED | participation Brier: official-report (REPORTED) minus unverified/projected information states | n/a | 16 | {'n_days': 3, 'share_same_sign': 1.0, 'note': ''} | A negative gap means official reports sharpen P(play) as intended; ~0 means the report adds nothing measurable yet (e.g. opening week). |
| 9 | market_timing | MEASURED | model-minus-market Brier at each pregame window (negative = model better), plus market price discovery | +0.005 [-0.003, +0.013] | 16 | n/a | Window with the smallest (best) model-minus-market gap: LAST_VALID. Prices converge toward the closing line; see price_discovery shares. A model edge that exists only at early windows and vanishes by T-10 is a timing signal, not yet value. |
| 10 | fees_settlement_execution | MEASURED | per-contract trading costs (fee + slippage) and the gross-to-net P&L gap; DNP settlement effect | +0.026 [+0.026, +0.026] | 16 | {'n_days': 3, 'share_same_sign': 1.0, 'note': ''} | Costs average 0.026 per contract; compare with the model's gross edge before reading any ROI. DNP legs and non-executable quotes are listed separately. |

## 10. Next week plan

1. **PROJECTION_CALIBRATION_ISSUE**: the old simulator under-predicts minutes (negative bias). Acceptance: effect keeps its sign over the next prospective sample and the Holm-adjusted p < 0.05 over the declared family

## Control and gates

```json
{
 "control": {
  "status": "OK",
  "strategy_id": "SHADOW_PURE_PREREG_V1",
  "evaluated_at": "2026-10-23T04:52:37.270611+00:00",
  "source_file": "scorecards/value/dt=2026-10-23/scorecards_value_20261023T045237Z_39898125396.jsonl.gz",
  "n_arms": 4,
  "arm": "sim_rotation",
  "capture_window": "pretip",
  "n_decisions": 231,
  "n_games": 9,
  "verdict": "INSUFFICIENT_SAMPLE",
  "verdict_reasons": [
   "n_games 9 < preregistered min_games 40"
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
    "n_decisions 65 < preregistered min_decisions 200",
    "n_games 15 < preregistered min_games 40"
   ],
   "required_prospective_sample": {
    "min_independent_decisions": 200,
    "min_games": 40,
    "roi_ci_lower_bound": "> 0.0 for every clustered CI (game, player)",
    "protocol": "chronological, prospective, preregistered before scoring, original model versions"
   },
   "remaining": {
    "decisions": 135,
    "games": 25
   },
   "statement": "Week 1 grants no betting authority; this is evidence collection only."
  },
  "PF_EDGE_V1": {
   "strategy_id": "PF_EDGE_V1",
   "betting_authority": "NONE",
   "week1": true,
   "verdict": "INSUFFICIENT_SAMPLE",
   "verdict_reasons": [
    "n_games 16 < preregistered min_games 40"
   ],
   "required_prospective_sample": {
    "min_independent_decisions": 200,
    "min_games": 40,
    "roi_ci_lower_bound": "> 0.0 for every clustered CI (game, player)",
    "protocol": "chronological, prospective, preregistered before scoring, original model versions"
   },
   "remaining": {
    "decisions": 0,
    "games": 24
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
