# NBA research report: week 1 (2026-10-20 .. 2026-10-26 ET)

**Status: PRELIMINARY** (version 5, generated 2026-10-24T11:16:51Z). Research / paper only.

> PRELIMINARY: the week is not over or settlements/outcomes are incomplete; numbers will change.
> SAMPLE SIZE: 36 independent games in this report. Week-1 evidence cannot establish profitability: the preregistered control needs >= 200 independent decisions across >= 40 games with positive clustered lower confidence bounds before any VALIDATED_VALUE language is allowed.
> NO BETTING AUTHORITY: nothing in this report authorises a wager, a stake change or a model promotion. All trades are paper.

| independent games | player-games | theses | decisions | contracts |
|---|---|---|---|---|
| 36 | 1197 | 1576 | 644700 | 8577 |

## 1. Data integrity

### Data integrity (2026-10-20 .. 2026-10-26 ET)

- games scheduled: **36** (16 not yet covered by a projection slot (30 h window)), started: 12, fully complete evidence: **12**
- missing evidence counts: none
- pregame slots expected 12, executed/covered 12, missed: none

| game | tip (UTC) | forecasts | obs | game fc | snapshots | decisions | outcome | missing |
|---|---|---|---|---|---|---|---|---|
| CHI@MIL | 10-23T20:00 | 8 fam / 7 v | 206 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 21088 | y | - |
| NYK@BOS | 10-23T23:00 | 8 fam / 8 v | 249 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 28532 | y | - |
| ATL@CHA | 10-23T23:00 | 8 fam / 8 v | 293 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 22760 | y | - |
| DAL@IND | 10-23T23:00 | 8 fam / 8 v | 315 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 22238 | y | - |
| MIN@ORL | 10-23T23:00 | 8 fam / 8 v | 271 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 24410 | y | - |
| TOR@WAS | 10-23T23:00 | 8 fam / 8 v | 291 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 20936 | y | - |
| DET@MIA | 10-24T00:00 | 8 fam / 9 v | 303 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 26350 | y | - |
| HOU@SAS | 10-24T01:30 | 8 fam / 8 v | 318 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 27850 | y | - |
| NOP@UTA | 10-24T01:30 | 8 fam / 8 v | 290 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 23748 | y | - |
| MEM@GSW | 10-24T02:00 | 8 fam / 9 v | 349 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 23678 | y | - |
| LAC@LAL | 10-24T02:00 | 8 fam / 9 v | 361 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 22838 | y | - |
| POR@SAC | 10-24T02:00 | 8 fam / 9 v | 325 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 23996 | y | - |
| MIA@CHA | 10-24T22:00 | 8 fam / 6 v | 24 | y | LIVE | 180 | n | - |
| BKN@CLE | 10-24T23:30 | 8 fam / 5 v | 145 | y | LIVE | 150 | n | - |
| MIL@PHI | 10-24T23:30 | 8 fam / 5 v | 93 | y | LIVE | 150 | n | - |
| WAS@CHI | 10-25T00:00 | 8 fam / 5 v | 21 | y | LIVE | 150 | n | - |
| SAS@DAL | 10-25T00:00 | 8 fam / 5 v | 42 | y | LIVE | 150 | n | - |
| HOU@ATL | 10-25T00:30 | 8 fam / 4 v | 15 | y | LIVE | 120 | n | - |
| NOP@DEN | 10-25T01:00 | 8 fam / 4 v | 48 | y | LIVE | 120 | n | - |
| GSW@PHX | 10-25T02:00 | 8 fam / 4 v | 48 | y | LIVE | 120 | n | - |


## 2. Projection performance

- minutes challenger: n=642 MAE +5.505 bias +0.205 [-0.868, +1.119]
- minutes incumbent: n=453 MAE +9.184 bias +4.829 [+2.675, +7.158]
- minutes naive_prior_mean: n=266 MAE +4.643 bias +0.094 [-0.749, +0.943]
- participation Brier: +0.113 [+0.091, +0.136] (n=971, games=28); mean P(play) +0.722 vs played rate +0.661
- assists (conditional on playing): n=642 games=28 MAE +1.319 bias +0.000 [-0.171, +0.168] CRPS +0.901 [+0.847, +0.954]
- fga (conditional on playing): n=642 games=28 MAE +2.859 bias +0.034 [-0.273, +0.327] CRPS +2.011 [+1.891, +2.124]
- points (conditional on playing): n=642 games=28 MAE +4.681 bias +0.112 [-0.438, +0.659] CRPS +3.242 [+3.036, +3.448]
- pra (conditional on playing): n=642 games=28 MAE +6.087 bias +0.099 [-0.699, +0.898] CRPS +4.298 [+4.032, +4.578]
- rebounds (conditional on playing): n=642 games=28 MAE +1.837 bias -0.098 [-0.285, +0.080] CRPS +1.271 [+1.185, +1.356]
- threes (conditional on playing): n=642 games=28 MAE +0.793 bias +0.069 [-0.011, +0.151] CRPS +0.513 [+0.480, +0.546]
- team points: MAE +9.934, margin MAE +13.955, total MAE +14.451

## 3. Market comparison

contracts (ladder rungs of a player-game are correlated); CIs resample games

| horizon | contracts | games | Brier model | Brier market mid | diff (model - market) |
|---|---|---|---|---|---|
| T-90 | 8392 | 28 | +0.167 | +0.158 | +0.009 [+0.002, +0.016] |
| T-60 | 8431 | 28 | +0.166 | +0.158 | +0.009 [+0.002, +0.015] |
| T-30 | 8457 | 28 | +0.166 | +0.157 | +0.009 [+0.003, +0.016] |
| T-10 | 8473 | 28 | +0.166 | +0.157 | +0.009 [+0.004, +0.015] |
| LAST_VALID | 8468 | 28 | +0.167 | +0.158 | +0.009 [+0.003, +0.015] |

## 4. Paper trading

Hypothetical net ROI after fees and slippage (paper only). `selected` = one contract per thesis per horizon; `all candidates` rows are not independent.

| strategy | view | decisions | contracts | theses | games | ROI | ROI CI | hit rate |
|---|---|---|---|---|---|---|---|---|
| PF_ALL_CANDIDATES_V1 | all candidates | 214748 | 8561 | 1568 | 28 | -0.110 | [-0.114, -0.105] | +0.500 |
| PF_EDGE_STRICT_V1 | selected | 117 | 117 | 117 | 26 | -0.068 | [-0.326, +0.198] | +0.419 |
| PF_EDGE_STRICT_V1 | all candidates | 365 | 135 | 117 | 26 | -0.113 | [-0.360, +0.151] | +0.400 |
| PF_EDGE_V1 | selected | 377 | 377 | 377 | 28 | -0.093 | [-0.215, +0.032] | +0.428 |
| PF_EDGE_V1 | all candidates | 2162 | 533 | 377 | 28 | -0.100 | [-0.249, +0.070] | +0.402 |

Baselines: NO_BET_V1 = 0 by definition; MARKET_ONLY_V1 = quote mid (see section 3); control SHADOW_PURE_PREREG_V1 is read from the shadow branch (see Control).

**Expression ranking** (which market best expresses a basketball thesis; research only): 6870 theses scored, 21747 NO_TRADE, status OK

## 5. Market families

Hit rate of the side actually evaluated, by family (descriptive; sample sizes shown).

| family | contracts | games | hit rate |
|---|---|---|---|
| game_spread | None | 28 | +0.499 |
| game_total | None | 28 | +0.499 |
| game_winner | None | 28 | +0.500 |
| player_assists | None | 28 | +0.499 |
| player_points | None | 28 | +0.497 |
| player_pra | None | 28 | +0.498 |
| player_rebounds | None | 28 | +0.498 |
| player_threes | None | 28 | +0.500 |
| team_total | None | 28 | +0.499 |

## 6. Timing

share_h = sum(B_ref - B_h) / sum(B_ref - B_close), B = (mid - y_yes)^2 on contracts present at ref, h and close

| horizon | contracts | games | share of open->close improvement | mean abs move to close |
|---|---|---|---|---|
| T-90 | 1524 | 28 | +0.646 | +0.008 |
| T-60 | 1524 | 28 | +0.769 | +0.007 |
| T-30 | 1524 | 28 | +0.930 | +0.006 |
| T-10 | 1524 | 28 | +0.946 | +0.004 |
| LAST_VALID | 1524 | 28 | +1.000 | +0.000 |

## 7. Player matchup diagnostics

Segment tables (player, team, stat family, minutes bucket, starter proxy, injury status, opponent, home/away, price range, side, threshold, window, confidence/freshness) are in `report.json` under `sections.7_player_matchup_diagnostics`; cells below the minimum counts are suppressed.

## 8. Patterns

> INSUFFICIENT_SAMPLE: 36 games. Nothing here authorises a change to production parameters or betting; first-week results are never promotion evidence.

Leads are classified, never promoted. `p_holm` is Holm-adjusted over the declared family; exploratory screens use Benjamini-Hochberg (q=0.10).

| id | claim | class | effect | 95% CI | p (Holm) | games needed (observed effect) | note |
|---|---|---|---|---|---|---|---|
| H02 | the old simulator under-predicts minutes (negative bias) | PROJECTION_CALIBRATION_ISSUE | +4.829 | [+2.675, +7.158] | +0.000 | 14 | Holm-significant and larger than the equivalence margin |
| H03 | P(play) is mis-calibrated in the large | INCONCLUSIVE | +0.061 | [+0.016, +0.104] | +0.072 | 32 | not established either way |
| H12 | more than 20% of candidate sides fail the quality / executability gate | EVIDENCE_AGAINST | -0.049 | [-0.064, -0.035] | +0.000 | 17 | within the materiality margin |
| H11 | selected trades beat the closing line (positive CLV, valid closes only) | EVIDENCE_AGAINST | -0.531 | [-1.150, +0.052] | +0.550 | 74 | 95% CI lies inside +/-0.5 (practically no effect) |
| H06 | the model beats the market mid at T-60 (Brier, points-ladder and other props) | EVIDENCE_AGAINST | +0.009 | [+0.002, +0.015] | +0.072 | 34 | the effect has the opposite sign with a 95% CI excluding 0 |
| H08 | PF_EDGE_V1 selected trades earn positive net P&L (1 per thesis) | INCONCLUSIVE | -0.041 | [-0.096, +0.014] | +0.830 | 122 | effect not distinguishable from 0 at this sample |
| H07 | the model beats the market mid at some pregame window overall | EVIDENCE_AGAINST | +0.006 | [+0.000, +0.012] | +0.294 | 55 | the effect has the opposite sign with a 95% CI excluding 0 |
| H05 | 80% central intervals for points do not cover 80% | EVIDENCE_AGAINST | -0.010 | [-0.040, +0.018] | +1.000 | 535 | 95% CI inside +/-0.05: no calibration defect of material size detected |
| H01 | challenger minutes forecasts are biased | INCONCLUSIVE | +0.205 | [-0.868, +1.119] | +1.000 | 1351 | not established either way |
| H10 | T-90 market prices are less accurate than T-10/closing prices (late information not yet priced early) | EVIDENCE_AGAINST | -0.000 | [-0.001, +0.001] | +1.000 | 564 | 95% CI lies inside +/-0.002 (practically no effect) |
| H04 | points projections are biased | INCONCLUSIVE | +0.112 | [-0.438, +0.659] | +1.000 | 1453 | not established either way |
| H09 | NO-side (fade the ladder) candidates earn positive net P&L | INCONCLUSIVE | +0.000 | [-0.029, +0.029] | +1.000 | 6772632 | effect not distinguishable from 0 at this sample |
| H13 | the DNP fair-price settlement costs more than a void policy assumes | INCONCLUSIVE | n/a | n/a | n/a | n/a | fewer than 2 games |

Exploratory screen: OK

## 9. Root cause

> INSUFFICIENT_SAMPLE: 36 games; every statistic below is descriptive, not a finding

Minutes under-prediction verdict: **INCUMBENT_BIAS_NOT_NEGATIVE**

| # | class | status | statistic | value | games | repeatability | reading |
|---|---|---|---|---|---|---|---|
| 1 | participation | MEASURED | mean(P(play) - played), challenger | +0.061 [+0.016, +0.104] | 28 | {'n_days': 4, 'share_same_sign': 1.0, 'note': ''} | P(play) is over-confident by 0.061 on average; Brier 0.1133. Participation errors enter unconditional stat error through (p - played) * mu; see decomposition. |
| 2 | starter_rotation_assumptions | MEASURED | minutes bias by role proxy (starter-like - bench) | n/a | 28 | {'n_days': 4, 'share_same_sign': 0.5, 'note': ''} | Role = predicted-minutes bucket (a proxy: starter flags are not archived with outcomes). A starter-minus-bench bias gap away from 0 means the rotation shape (not the overall level) is wrong; bias is conditional on playing. |
| 3 | minutes_allocation | MEASURED | minutes bias (pred - actual), challenger vs incumbent, paired | n/a | 28 | {'n_days': 4, 'share_same_sign': 0.5, 'note': ''} | verdict on the old simulator's systematic minutes under-prediction: INCUMBENT_BIAS_NOT_NEGATIVE. Challenger bias +0.20 [-0.87, +1.12] min. |
| 4 | usage_and_per_minute_rates | MEASURED | error = r_pred*(m_pred - m_act) + m_act*(r_pred - r_act): rate component, points | +0.190 [-0.097, +0.481] | n/a | {'n_days': 4, 'share_same_sign': 0.75, 'note': ''} | Per-minute rate (usage) accounts for ~71% of the squared-error budget (rate vs minutes components, points); a rate-component mean away from 0 is a usage / efficiency bias independent of minutes. |
| 5 | opponent_adjustment | MEASURED | points bias (pred - actual): generous-defence opponents minus stingy ones | n/a | 28 | {'n_days': 4, 'share_same_sign': 0.5, 'note': ''} | If the opponent adjustment works this gap is ~0; a negative gap means the model under-projects against generous defences (adjustment too weak). |
| 6 | pace | MEASURED | game total error (pred - actual) and correlation with mean player-points error | +7.242 [+1.264, +13.678] | 28 | n/a | Game-total bias +7.24 [+1.26, +13.68]; per-game correlation between total error and mean player-points error: 0.7723421012771643. A high correlation points at pace/environment (shared by all players) rather than player-specific rates. |
| 7 | distribution_shape_tails | MEASURED | PIT variance ratio / tail excess (observed share beyond the 10%/90% quantiles minus 10%) | +0.018 [-0.009, +0.048] | n/a | n/a | Largest departure of PIT variance from 1: minutes (1.14; >1 = too narrow). Upper-tail excess > 0 means actual outcomes exceed the forecast 90th percentile more often than 10%. |
| 8 | injury_information | MEASURED | participation Brier: official-report (REPORTED) minus unverified/projected information states | n/a | 28 | {'n_days': 4, 'share_same_sign': 1.0, 'note': ''} | A negative gap means official reports sharpen P(play) as intended; ~0 means the report adds nothing measurable yet (e.g. opening week). |
| 9 | market_timing | MEASURED | model-minus-market Brier at each pregame window (negative = model better), plus market price discovery | +0.006 [+0.000, +0.012] | 28 | n/a | Window with the smallest (best) model-minus-market gap: T-60. Prices converge toward the closing line; see price_discovery shares. A model edge that exists only at early windows and vanishes by T-10 is a timing signal, not yet value. |
| 10 | fees_settlement_execution | MEASURED | per-contract trading costs (fee + slippage) and the gross-to-net P&L gap; DNP settlement effect | +0.026 [+0.026, +0.026] | 28 | {'n_days': 4, 'share_same_sign': 1.0, 'note': ''} | Costs average 0.026 per contract; compare with the model's gross edge before reading any ROI. DNP legs and non-executable quotes are listed separately. |

## 10. Next week plan

1. **PROJECTION_CALIBRATION_ISSUE**: the old simulator under-predicts minutes (negative bias). Acceptance: effect keeps its sign over the next prospective sample and the Holm-adjusted p < 0.05 over the declared family

## Control and gates

```json
{
 "control": {
  "status": "OK",
  "strategy_id": "SHADOW_PURE_PREREG_V1",
  "evaluated_at": "2026-10-24T03:56:47.503930+00:00",
  "source_file": "scorecards/value/dt=2026-10-24/scorecards_value_20261024T035647Z_40060316866.jsonl.gz",
  "n_arms": 4,
  "arm": "sim_rotation",
  "capture_window": "pretip",
  "n_decisions": 417,
  "n_games": 15,
  "verdict": "INSUFFICIENT_SAMPLE",
  "verdict_reasons": [
   "n_games 15 < preregistered min_games 40"
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
    "n_decisions 117 < preregistered min_decisions 200",
    "n_games 26 < preregistered min_games 40"
   ],
   "required_prospective_sample": {
    "min_independent_decisions": 200,
    "min_games": 40,
    "roi_ci_lower_bound": "> 0.0 for every clustered CI (game, player)",
    "protocol": "chronological, prospective, preregistered before scoring, original model versions"
   },
   "remaining": {
    "decisions": 83,
    "games": 14
   },
   "statement": "Week 1 grants no betting authority; this is evidence collection only."
  },
  "PF_EDGE_V1": {
   "strategy_id": "PF_EDGE_V1",
   "betting_authority": "NONE",
   "week1": true,
   "verdict": "INSUFFICIENT_SAMPLE",
   "verdict_reasons": [
    "n_games 28 < preregistered min_games 40"
   ],
   "required_prospective_sample": {
    "min_independent_decisions": 200,
    "min_games": 40,
    "roi_ci_lower_bound": "> 0.0 for every clustered CI (game, player)",
    "protocol": "chronological, prospective, preregistered before scoring, original model versions"
   },
   "remaining": {
    "decisions": 0,
    "games": 12
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
