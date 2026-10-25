# NBA research report: week 1 (2026-10-20 .. 2026-10-26 ET)

**Status: PRELIMINARY** (version 6, generated 2026-10-25T11:19:23Z). Research / paper only.

> PRELIMINARY: the week is not over or settlements/outcomes are incomplete; numbers will change.
> SAMPLE SIZE: 43 independent games in this report. Week-1 evidence cannot establish profitability: the preregistered control needs >= 200 independent decisions across >= 40 games with positive clustered lower confidence bounds before any VALIDATED_VALUE language is allowed.
> NO BETTING AUTHORITY: nothing in this report authorises a wager, a stake change or a model promotion. All trades are paper.

| independent games | player-games | theses | decisions | contracts |
|---|---|---|---|---|
| 43 | 1519 | 2005 | 760920 | 11430 |

## 1. Data integrity

### Data integrity (2026-10-20 .. 2026-10-26 ET)

- games scheduled: **16** (9 not yet covered by a projection slot (30 h window)), started: 0, fully complete evidence: **0**
- missing evidence counts: none
- pregame slots expected 6, executed/covered 6, missed: none

| game | tip (UTC) | forecasts | obs | game fc | snapshots | decisions | outcome | missing |
|---|---|---|---|---|---|---|---|---|
| LAL@UTA | 10-25T21:00 | 8 fam / 6 v | 135 | y | LIVE | 780 | n | - |
| IND@BKN | 10-25T22:00 | 8 fam / 5 v | 92 | y | LIVE | 750 | n | - |
| ORL@NYK | 10-25T23:00 | 8 fam / 5 v | 182 | y | LIVE | 750 | n | - |
| TOR@MIN | 10-25T23:00 | 8 fam / 5 v | 138 | y | LIVE | 750 | n | - |
| LAC@OKC | 10-25T23:00 | 8 fam / 5 v | 166 | y | LIVE | 750 | n | - |
| DET@PHI | 10-25T23:30 | 8 fam / 5 v | 106 | y | LIVE | 150 | n | - |
| MEM@SAC | 10-26T01:00 | 8 fam / 4 v | 89 | y | LIVE | 720 | n | - |


## 2. Projection performance

- minutes challenger: n=810 MAE +5.399 bias +0.109 [-0.731, +0.912]
- minutes incumbent: n=599 MAE +8.620 bias +3.049 [+1.136, +5.054]
- minutes naive_prior_mean: n=424 MAE +4.809 bias -0.675 [-1.460, +0.154]
- participation Brier: +0.116 [+0.097, +0.135] (n=1247, games=36); mean P(play) +0.715 vs played rate +0.650
- assists (conditional on playing): n=810 games=36 MAE +1.315 bias -0.055 [-0.205, +0.095] CRPS +0.901 [+0.852, +0.952]
- fga (conditional on playing): n=810 games=36 MAE +2.833 bias +0.006 [-0.249, +0.259] CRPS +1.993 [+1.889, +2.094]
- points (conditional on playing): n=810 games=36 MAE +4.664 bias -0.035 [-0.515, +0.449] CRPS +3.247 [+3.078, +3.426]
- pra (conditional on playing): n=810 games=36 MAE +6.138 bias -0.196 [-0.922, +0.497] CRPS +4.341 [+4.102, +4.597]
- rebounds (conditional on playing): n=810 games=36 MAE +1.827 bias -0.153 [-0.326, +0.016] CRPS +1.273 [+1.194, +1.352]
- threes (conditional on playing): n=810 games=36 MAE +0.825 bias +0.026 [-0.053, +0.103] CRPS +0.538 [+0.504, +0.574]
- team points: MAE +9.603, margin MAE +12.068, total MAE +14.663

## 3. Market comparison

contracts (ladder rungs of a player-game are correlated); CIs resample games

| horizon | contracts | games | Brier model | Brier market mid | diff (model - market) |
|---|---|---|---|---|---|
| T-90 | 10518 | 36 | +0.166 | +0.158 | +0.008 [+0.003, +0.014] |
| T-60 | 10568 | 36 | +0.165 | +0.158 | +0.008 [+0.002, +0.013] |
| T-30 | 10619 | 36 | +0.166 | +0.157 | +0.008 [+0.003, +0.014] |
| T-10 | 10654 | 36 | +0.165 | +0.157 | +0.008 [+0.003, +0.014] |
| LAST_VALID | 10637 | 36 | +0.166 | +0.158 | +0.008 [+0.003, +0.013] |

## 4. Paper trading

Hypothetical net ROI after fees and slippage (paper only). `selected` = one contract per thesis per horizon; `all candidates` rows are not independent.

| strategy | view | decisions | contracts | theses | games | ROI | ROI CI | hit rate |
|---|---|---|---|---|---|---|---|---|
| PF_ALL_CANDIDATES_V1 | all candidates | 252220 | 10795 | 1975 | 36 | -0.109 | [-0.113, -0.105] | +0.500 |
| PF_EDGE_STRICT_V1 | selected | 155 | 155 | 155 | 34 | -0.104 | [-0.329, +0.110] | +0.400 |
| PF_EDGE_STRICT_V1 | all candidates | 483 | 185 | 155 | 34 | -0.116 | [-0.333, +0.102] | +0.395 |
| PF_EDGE_V1 | selected | 473 | 473 | 473 | 36 | -0.115 | [-0.222, -0.005] | +0.423 |
| PF_EDGE_V1 | all candidates | 2602 | 666 | 473 | 36 | -0.107 | [-0.244, +0.027] | +0.401 |

Baselines: NO_BET_V1 = 0 by definition; MARKET_ONLY_V1 = quote mid (see section 3); control SHADOW_PURE_PREREG_V1 is read from the shadow branch (see Control).

**Expression ranking** (which market best expresses a basketball thesis; research only): 7610 theses scored, 25085 NO_TRADE, status OK

## 5. Market families

Hit rate of the side actually evaluated, by family (descriptive; sample sizes shown).

| family | contracts | games | hit rate |
|---|---|---|---|
| game_spread | None | 36 | +0.499 |
| game_total | None | 36 | +0.499 |
| game_winner | None | 36 | +0.495 |
| player_assists | None | 36 | +0.499 |
| player_points | None | 36 | +0.497 |
| player_pra | None | 36 | +0.499 |
| player_rebounds | None | 36 | +0.499 |
| player_threes | None | 36 | +0.500 |
| team_total | None | 36 | +0.499 |

## 6. Timing

share_h = sum(B_ref - B_h) / sum(B_ref - B_close), B = (mid - y_yes)^2 on contracts present at ref, h and close

| horizon | contracts | games | share of open->close improvement | mean abs move to close |
|---|---|---|---|---|
| T-90 | 1540 | 36 | +0.677 | +0.008 |
| T-60 | 1540 | 36 | +0.791 | +0.007 |
| T-30 | 1540 | 36 | +0.936 | +0.006 |
| T-10 | 1540 | 36 | +0.948 | +0.004 |
| LAST_VALID | 1540 | 36 | +1.000 | +0.000 |

## 7. Player matchup diagnostics

Segment tables (player, team, stat family, minutes bucket, starter proxy, injury status, opponent, home/away, price range, side, threshold, window, confidence/freshness) are in `report.json` under `sections.7_player_matchup_diagnostics`; cells below the minimum counts are suppressed.

## 8. Patterns

> Ranked leads are research priorities only; a change to production needs prospective validation on a fresh sample.

Leads are classified, never promoted. `p_holm` is Holm-adjusted over the declared family; exploratory screens use Benjamini-Hochberg (q=0.10).

| id | claim | class | effect | 95% CI | p (Holm) | games needed (observed effect) | note |
|---|---|---|---|---|---|---|---|
| H03 | P(play) is mis-calibrated in the large | PROJECTION_CALIBRATION_ISSUE | +0.066 | [+0.029, +0.101] | +0.005 | 25 | Holm-significant and larger than the equivalence margin |
| H02 | the old simulator under-predicts minutes (negative bias) | PROJECTION_CALIBRATION_ISSUE | +3.049 | [+1.136, +5.054] | +0.026 | 39 | Holm-significant and larger than the equivalence margin |
| H11 | selected trades beat the closing line (positive CLV, valid closes only) | EVIDENCE_AGAINST | -0.609 | [-1.138, -0.093] | +0.171 | 55 | the effect has the opposite sign with a 95% CI excluding 0 |
| H12 | more than 20% of candidate sides fail the quality / executability gate | EVIDENCE_AGAINST | -0.053 | [-0.067, -0.040] | +0.000 | 23 | within the materiality margin |
| H08 | PF_EDGE_V1 selected trades earn positive net P&L (1 per thesis) | EVIDENCE_AGAINST | -0.051 | [-0.098, -0.002] | +0.214 | 69 | the effect has the opposite sign with a 95% CI excluding 0 |
| H06 | the model beats the market mid at T-60 (Brier, points-ladder and other props) | EVIDENCE_AGAINST | +0.008 | [+0.002, +0.013] | +0.048 | 39 | the effect has the opposite sign with a 95% CI excluding 0 |
| H07 | the model beats the market mid at some pregame window overall | EVIDENCE_AGAINST | +0.006 | [+0.001, +0.011] | +0.195 | 55 | the effect has the opposite sign with a 95% CI excluding 0 |
| H09 | NO-side (fade the ladder) candidates earn positive net P&L | EVIDENCE_AGAINST | -0.027 | [-0.057, +0.001] | +0.347 | 90 | 95% CI lies inside +/-0.01 (practically no effect) |
| H05 | 80% central intervals for points do not cover 80% | EVIDENCE_AGAINST | -0.010 | [-0.038, +0.017] | +1.000 | 641 | 95% CI inside +/-0.05: no calibration defect of material size detected |
| H10 | T-90 market prices are less accurate than T-10/closing prices (late information not yet priced early) | EVIDENCE_AGAINST | -0.000 | [-0.001, +0.001] | +1.000 | 1068 | 95% CI lies inside +/-0.002 (practically no effect) |
| H01 | challenger minutes forecasts are biased | EVIDENCE_AGAINST | +0.109 | [-0.731, +0.912] | +1.000 | 4092 | 95% CI inside +/-1: no calibration defect of material size detected |
| H04 | points projections are biased | INCONCLUSIVE | -0.035 | [-0.515, +0.449] | +1.000 | 13799 | not established either way |
| H13 | the DNP fair-price settlement costs more than a void policy assumes | INCONCLUSIVE | n/a | n/a | n/a | n/a | fewer than 2 games |

Exploratory screen: OK

## 9. Root cause

> None

Minutes under-prediction verdict: **INCUMBENT_BIAS_NOT_NEGATIVE**

| # | class | status | statistic | value | games | repeatability | reading |
|---|---|---|---|---|---|---|---|
| 1 | participation | MEASURED | mean(P(play) - played), challenger | +0.066 [+0.029, +0.101] | 36 | {'n_days': 5, 'share_same_sign': 1.0, 'note': ''} | P(play) is over-confident by 0.066 on average; Brier 0.1160. Participation errors enter unconditional stat error through (p - played) * mu; see decomposition. |
| 2 | starter_rotation_assumptions | MEASURED | minutes bias by role proxy (starter-like - bench) | n/a | 36 | {'n_days': 5, 'share_same_sign': 0.4, 'note': ''} | Role = predicted-minutes bucket (a proxy: starter flags are not archived with outcomes). A starter-minus-bench bias gap away from 0 means the rotation shape (not the overall level) is wrong; bias is conditional on playing. |
| 3 | minutes_allocation | MEASURED | minutes bias (pred - actual), challenger vs incumbent, paired | n/a | 36 | {'n_days': 5, 'share_same_sign': 0.4, 'note': ''} | verdict on the old simulator's systematic minutes under-prediction: INCUMBENT_BIAS_NOT_NEGATIVE. Challenger bias +0.11 [-0.73, +0.91] min. |
| 4 | usage_and_per_minute_rates | MEASURED | error = r_pred*(m_pred - m_act) + m_act*(r_pred - r_act): rate component, points | +0.103 [-0.176, +0.372] | n/a | {'n_days': 5, 'share_same_sign': 0.6, 'note': ''} | Per-minute rate (usage) accounts for ~71% of the squared-error budget (rate vs minutes components, points); a rate-component mean away from 0 is a usage / efficiency bias independent of minutes. |
| 5 | opponent_adjustment | MEASURED | points bias (pred - actual): generous-defence opponents minus stingy ones | n/a | 36 | {'n_days': 5, 'share_same_sign': 0.6, 'note': ''} | If the opponent adjustment works this gap is ~0; a negative gap means the model under-projects against generous defences (adjustment too weak). |
| 6 | pace | MEASURED | game total error (pred - actual) and correlation with mean player-points error | +3.338 [-2.460, +9.156] | 36 | n/a | Game-total bias +3.34 [-2.46, +9.16]; per-game correlation between total error and mean player-points error: 0.7838609385716443. A high correlation points at pace/environment (shared by all players) rather than player-specific rates. |
| 7 | distribution_shape_tails | MEASURED | PIT variance ratio / tail excess (observed share beyond the 10%/90% quantiles minus 10%) | +0.016 [-0.006, +0.039] | n/a | n/a | Largest departure of PIT variance from 1: pra (1.13; >1 = too narrow). Upper-tail excess > 0 means actual outcomes exceed the forecast 90th percentile more often than 10%. |
| 8 | injury_information | MEASURED | participation Brier: official-report (REPORTED) minus unverified/projected information states | n/a | 36 | {'n_days': 5, 'share_same_sign': 1.0, 'note': ''} | A negative gap means official reports sharpen P(play) as intended; ~0 means the report adds nothing measurable yet (e.g. opening week). |
| 9 | market_timing | MEASURED | model-minus-market Brier at each pregame window (negative = model better), plus market price discovery | +0.006 [+0.001, +0.011] | 36 | n/a | Window with the smallest (best) model-minus-market gap: T-60. Prices converge toward the closing line; see price_discovery shares. A model edge that exists only at early windows and vanishes by T-10 is a timing signal, not yet value. |
| 10 | fees_settlement_execution | MEASURED | per-contract trading costs (fee + slippage) and the gross-to-net P&L gap; DNP settlement effect | +0.026 [+0.026, +0.026] | 36 | {'n_days': 5, 'share_same_sign': 1.0, 'note': ''} | Costs average 0.026 per contract; compare with the model's gross edge before reading any ROI. DNP legs and non-executable quotes are listed separately. |

## 10. Next week plan

1. **PROJECTION_CALIBRATION_ISSUE**: P(play) is mis-calibrated in the large. Acceptance: effect keeps its sign over the next prospective sample and the Holm-adjusted p < 0.05 over the declared family
2. **PROJECTION_CALIBRATION_ISSUE**: the old simulator under-predicts minutes (negative bias). Acceptance: effect keeps its sign over the next prospective sample and the Holm-adjusted p < 0.05 over the declared family

## Control and gates

```json
{
 "control": {
  "status": "OK",
  "strategy_id": "SHADOW_PURE_PREREG_V1",
  "evaluated_at": "2026-10-25T03:56:48.832333+00:00",
  "source_file": "scorecards/value/dt=2026-10-25/scorecards_value_20261025T035648Z_40159998783.jsonl.gz",
  "n_arms": 4,
  "arm": "sim_rotation",
  "capture_window": "pretip",
  "n_decisions": 705,
  "n_games": 24,
  "verdict": "INSUFFICIENT_SAMPLE",
  "verdict_reasons": [
   "n_games 24 < preregistered min_games 40"
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
    "n_decisions 155 < preregistered min_decisions 200",
    "n_games 34 < preregistered min_games 40"
   ],
   "required_prospective_sample": {
    "min_independent_decisions": 200,
    "min_games": 40,
    "roi_ci_lower_bound": "> 0.0 for every clustered CI (game, player)",
    "protocol": "chronological, prospective, preregistered before scoring, original model versions"
   },
   "remaining": {
    "decisions": 45,
    "games": 6
   },
   "statement": "Week 1 grants no betting authority; this is evidence collection only."
  },
  "PF_EDGE_V1": {
   "strategy_id": "PF_EDGE_V1",
   "betting_authority": "NONE",
   "week1": true,
   "verdict": "INSUFFICIENT_SAMPLE",
   "verdict_reasons": [
    "n_games 36 < preregistered min_games 40"
   ],
   "required_prospective_sample": {
    "min_independent_decisions": 200,
    "min_games": 40,
    "roi_ci_lower_bound": "> 0.0 for every clustered CI (game, player)",
    "protocol": "chronological, prospective, preregistered before scoring, original model versions"
   },
   "remaining": {
    "decisions": 0,
    "games": 4
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
