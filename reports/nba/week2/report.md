# NBA research report: week 2 (2026-10-27 .. 2026-11-02 ET)

**Status: PRELIMINARY** (version 3, generated 2026-10-29T11:26:41Z). Research / paper only.

> PRELIMINARY: the week is not over or settlements/outcomes are incomplete; numbers will change.
> SAMPLE SIZE: 19 independent games in this report. Week-1 evidence cannot establish profitability: the preregistered control needs >= 200 independent decisions across >= 40 games with positive clustered lower confidence bounds before any VALIDATED_VALUE language is allowed.
> NO BETTING AUTHORITY: nothing in this report authorises a wager, a stake change or a model promotion. All trades are paper.

| independent games | player-games | theses | decisions | contracts |
|---|---|---|---|---|
| 19 | 637 | 853 | 272124 | 4965 |

## 1. Data integrity

### Data integrity (2026-10-27 .. 2026-11-02 ET)

- games scheduled: **55** (36 not yet covered by a projection slot (30 h window)), started: 16, fully complete evidence: **16**
- missing evidence counts: none
- pregame slots expected 17, executed/covered 17, missed: none

| game | tip (UTC) | forecasts | obs | game fc | snapshots | decisions | outcome | missing |
|---|---|---|---|---|---|---|---|---|
| BKN@BOS | 10-27T23:30 | 8 fam / 8 v | 182 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 16226 | y | - |
| DET@NYK | 10-28T00:00 | 8 fam / 8 v | 277 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 16808 | y | - |
| SAC@SAS | 10-28T00:00 | 8 fam / 8 v | 286 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 16568 | y | - |
| POR@LAL | 10-28T03:00 | 8 fam / 9 v | 290 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 20420 | y | - |
| MIA@ATL | 10-28T23:00 | 8 fam / 8 v | 279 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 19100 | y | - |
| WAS@CLE | 10-28T23:00 | 8 fam / 8 v | 275 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 20198 | y | - |
| CHA@DET | 10-28T23:00 | 8 fam / 8 v | 214 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 16580 | y | - |
| PHI@IND | 10-28T23:00 | 8 fam / 8 v | 332 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 19340 | y | - |
| ORL@TOR | 10-28T23:30 | 8 fam / 9 v | 347 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 18326 | y | - |
| NYK@CHI | 10-29T00:00 | 8 fam / 9 v | 205 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 20258 | y | - |
| HOU@MIL | 10-29T00:00 | 8 fam / 9 v | 306 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 19952 | y | - |
| GSW@MIN | 10-29T00:00 | 8 fam / 9 v | 328 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 18908 | y | - |
| DEN@NOP | 10-29T00:00 | 8 fam / 9 v | 330 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 20144 | y | - |
| SAS@UTA | 10-29T01:00 | 8 fam / 9 v | 284 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 21062 | y | - |
| OKC@DAL | 10-29T01:30 | 8 fam / 9 v | 456 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 19225 | y | - |
| LAL@LAC | 10-29T02:30 | 8 fam / 10 v | 322 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 19886 | y | - |
| CLE@ATL | 10-30T00:00 | 8 fam / 5 v | 11 | y | LIVE | 60 | n | - |
| SAC@NOP | 10-30T00:00 | 8 fam / 5 v | 94 | y | LIVE | 1122 | n | - |
| MEM@POR | 10-30T02:00 | 8 fam / 4 v | 80 | y | LIVE | 2292 | n | - |


## 2. Projection performance

- minutes challenger: n=349 MAE +4.405 bias +0.287 [-0.521, +1.031]
- minutes incumbent: n=313 MAE +5.645 bias -1.167 [-2.029, -0.324]
- minutes naive_prior_mean: n=36 MAE +6.778 bias -2.389 (CI withheld: TOO_FEW_CLUSTERS (<5 games))
- participation Brier: +0.098 [+0.080, +0.115] (n=555, games=16); mean P(play) +0.678 vs played rate +0.629
- assists (conditional on playing): n=349 games=16 MAE +1.288 bias +0.001 [-0.170, +0.168] CRPS +0.866 [+0.784, +0.956]
- fga (conditional on playing): n=349 games=16 MAE +2.716 bias +0.214 [-0.135, +0.507] CRPS +1.881 [+1.731, +2.034]
- points (conditional on playing): n=349 games=16 MAE +4.569 bias +0.378 [-0.173, +0.869] CRPS +3.122 [+2.873, +3.403]
- pra (conditional on playing): n=349 games=16 MAE +5.531 bias +0.366 [-0.326, +0.997] CRPS +3.851 [+3.589, +4.150]
- rebounds (conditional on playing): n=349 games=16 MAE +1.815 bias -0.011 [-0.310, +0.254] CRPS +1.250 [+1.168, +1.340]
- threes (conditional on playing): n=349 games=16 MAE +0.912 bias +0.010 [-0.109, +0.124] CRPS +0.585 [+0.523, +0.647]
- team points: MAE +11.783, margin MAE +12.799, total MAE +16.712

## 3. Market comparison

contracts (ladder rungs of a player-game are correlated); CIs resample games

| horizon | contracts | games | Brier model | Brier market mid | diff (model - market) |
|---|---|---|---|---|---|
| T-90 | 4587 | 16 | +0.176 | +0.165 | +0.011 [+0.004, +0.016] |
| T-60 | 4638 | 16 | +0.176 | +0.165 | +0.011 [+0.005, +0.016] |
| T-30 | 4669 | 16 | +0.176 | +0.165 | +0.010 [+0.005, +0.016] |
| T-10 | 4681 | 16 | +0.176 | +0.165 | +0.011 [+0.006, +0.015] |
| LAST_VALID | 4680 | 16 | +0.176 | +0.165 | +0.010 [+0.005, +0.015] |

## 4. Paper trading

Hypothetical net ROI after fees and slippage (paper only). `selected` = one contract per thesis per horizon; `all candidates` rows are not independent.

| strategy | view | decisions | contracts | theses | games | ROI | ROI CI | hit rate |
|---|---|---|---|---|---|---|---|---|
| PF_ALL_CANDIDATES_V1 | all candidates | 89218 | 4687 | 827 | 16 | -0.109 | [-0.114, -0.105] | +0.500 |
| PF_EDGE_STRICT_V1 | selected | 82 | 82 | 82 | 16 | -0.193 | [-0.454, +0.104] | +0.366 |
| PF_EDGE_STRICT_V1 | all candidates | 265 | 101 | 82 | 16 | -0.224 | [-0.488, +0.053] | +0.347 |
| PF_EDGE_V1 | selected | 181 | 181 | 181 | 16 | -0.110 | [-0.254, +0.045] | +0.414 |
| PF_EDGE_V1 | all candidates | 893 | 274 | 181 | 16 | -0.249 | [-0.418, -0.072] | +0.342 |

Baselines: NO_BET_V1 = 0 by definition; MARKET_ONLY_V1 = quote mid (see section 3); control SHADOW_PURE_PREREG_V1 is read from the shadow branch (see Control).

**Expression ranking** (which market best expresses a basketball thesis; research only): 10772 theses scored, 39598 NO_TRADE, status OK

## 5. Market families

Hit rate of the side actually evaluated, by family (descriptive; sample sizes shown).

| family | contracts | games | hit rate |
|---|---|---|---|
| game_spread | None | 16 | +0.498 |
| game_total | None | 16 | +0.500 |
| game_winner | None | 16 | +0.481 |
| player_assists | None | 16 | +0.498 |
| player_points | None | 16 | +0.495 |
| player_pra | None | 16 | +0.497 |
| player_rebounds | None | 16 | +0.499 |
| player_threes | None | 16 | +0.499 |
| team_total | None | 16 | +0.498 |

## 6. Timing

share_h = sum(B_ref - B_h) / sum(B_ref - B_close), B = (mid - y_yes)^2 on contracts present at ref, h and close

| horizon | contracts | games | share of open->close improvement | mean abs move to close |
|---|---|---|---|---|
| T-90 | 32 | 16 | +0.988 | +0.007 |
| T-60 | 32 | 16 | +0.940 | +0.008 |
| T-30 | 32 | 16 | +0.911 | +0.005 |
| T-10 | 32 | 16 | +0.921 | +0.004 |
| LAST_VALID | 32 | 16 | +1.000 | +0.000 |

## 7. Player matchup diagnostics

Segment tables (player, team, stat family, minutes bucket, starter proxy, injury status, opponent, home/away, price range, side, threshold, window, confidence/freshness) are in `report.json` under `sections.7_player_matchup_diagnostics`; cells below the minimum counts are suppressed.

## 8. Patterns

> INSUFFICIENT_SAMPLE: 19 games. Nothing here authorises a change to production parameters or betting; first-week results are never promotion evidence.

Leads are classified, never promoted. `p_holm` is Holm-adjusted over the declared family; exploratory screens use Benjamini-Hochberg (q=0.10).

| id | claim | class | effect | 95% CI | p (Holm) | games needed (observed effect) | note |
|---|---|---|---|---|---|---|---|
| H06 | the model beats the market mid at T-60 (Brier, points-ladder and other props) | EVIDENCE_AGAINST | +0.011 | [+0.005, +0.016] | +0.002 | 10 | the effect has the opposite sign with a 95% CI excluding 0 |
| H07 | the model beats the market mid at some pregame window overall | EVIDENCE_AGAINST | +0.010 | [+0.004, +0.016] | +0.009 | 13 | the effect has the opposite sign with a 95% CI excluding 0 |
| H09 | NO-side (fade the ladder) candidates earn positive net P&L | EVIDENCE_AGAINST | -0.044 | [-0.078, -0.008] | +0.108 | 22 | the effect has the opposite sign with a 95% CI excluding 0 |
| H02 | the old simulator under-predicts minutes (negative bias) | INCONCLUSIVE | -1.167 | [-2.029, -0.324] | +0.071 | 20 | not established either way |
| H03 | P(play) is mis-calibrated in the large | INCONCLUSIVE | +0.049 | [+0.004, +0.093] | +0.224 | 31 | not established either way |
| H08 | PF_EDGE_V1 selected trades earn positive net P&L (1 per thesis) | INCONCLUSIVE | -0.047 | [-0.109, +0.019] | +0.929 | 65 | effect not distinguishable from 0 at this sample |
| H12 | more than 20% of candidate sides fail the quality / executability gate | EVIDENCE_AGAINST | -0.031 | [-0.053, -0.008] | +0.071 | 328 | within the materiality margin |
| H11 | selected trades beat the closing line (positive CLV, valid closes only) | INCONCLUSIVE | +0.457 | [-0.516, +1.337] | +1.000 | 120 | effect not distinguishable from 0 at this sample |
| H01 | challenger minutes forecasts are biased | INCONCLUSIVE | +0.287 | [-0.521, +1.031] | +1.000 | 278 | not established either way |
| H04 | points projections are biased | INCONCLUSIVE | +0.378 | [-0.173, +0.869] | +0.929 | 72 | not established either way |
| H05 | 80% central intervals for points do not cover 80% | INCONCLUSIVE | +0.011 | [-0.036, +0.053] | +1.000 | 604 | not established either way |
| H10 | T-90 market prices are less accurate than T-10/closing prices (late information not yet priced early) | EVIDENCE_AGAINST | +0.000 | [-0.001, +0.001] | +1.000 | 63833 | 95% CI lies inside +/-0.002 (practically no effect) |
| H13 | the DNP fair-price settlement costs more than a void policy assumes | INCONCLUSIVE | n/a | n/a | n/a | n/a | the archive holds no rows for this test yet |

Exploratory screen: OK

## 9. Root cause

> INSUFFICIENT_SAMPLE: 19 games; every statistic below is descriptive, not a finding

Minutes under-prediction verdict: **INCUMBENT_UNDERPREDICTS_CONFIRMED; CHALLENGER_UNDERPREDICTION_NOT_DETECTED**

| # | class | status | statistic | value | games | repeatability | reading |
|---|---|---|---|---|---|---|---|
| 1 | participation | MEASURED | mean(P(play) - played), challenger | +0.049 [+0.004, +0.093] | 16 | {'n_days': 2, 'share_same_sign': 1.0, 'note': ''} | P(play) is over-confident by 0.049 on average; Brier 0.0980. Participation errors enter unconditional stat error through (p - played) * mu; see decomposition. |
| 2 | starter_rotation_assumptions | MEASURED | minutes bias by role proxy (starter-like - bench) | n/a | 16 | {'n_days': 2, 'share_same_sign': 1.0, 'note': ''} | Role = predicted-minutes bucket (a proxy: starter flags are not archived with outcomes). A starter-minus-bench bias gap away from 0 means the rotation shape (not the overall level) is wrong; bias is conditional on playing. |
| 3 | minutes_allocation | MEASURED | minutes bias (pred - actual), challenger vs incumbent, paired | n/a | 16 | {'n_days': 2, 'share_same_sign': 1.0, 'note': ''} | verdict on the old simulator's systematic minutes under-prediction: INCUMBENT_UNDERPREDICTS_CONFIRMED; CHALLENGER_UNDERPREDICTION_NOT_DETECTED. Challenger bias +0.29 [-0.52, +1.03] min. |
| 4 | usage_and_per_minute_rates | MEASURED | error = r_pred*(m_pred - m_act) + m_act*(r_pred - r_act): rate component, points | +0.384 [-0.059, +0.830] | n/a | {'n_days': 2, 'share_same_sign': 0.5, 'note': ''} | Per-minute rate (usage) accounts for ~81% of the squared-error budget (rate vs minutes components, points); a rate-component mean away from 0 is a usage / efficiency bias independent of minutes. |
| 5 | opponent_adjustment | MEASURED | points bias (pred - actual): generous-defence opponents minus stingy ones | n/a | 16 | {'n_days': 2, 'share_same_sign': 0.5, 'note': ''} | If the opponent adjustment works this gap is ~0; a negative gap means the model under-projects against generous defences (adjustment too weak). |
| 6 | pace | MEASURED | game total error (pred - actual) and correlation with mean player-points error | +5.102 [-5.764, +15.180] | 16 | n/a | Game-total bias +5.10 [-5.76, +15.18]; per-game correlation between total error and mean player-points error: 0.9090019382232889. A high correlation points at pace/environment (shared by all players) rather than player-specific rates. |
| 7 | distribution_shape_tails | MEASURED | PIT variance ratio / tail excess (observed share beyond the 10%/90% quantiles minus 10%) | -0.014 [-0.042, +0.017] | n/a | n/a | Largest departure of PIT variance from 1: minutes (0.91; >1 = too narrow). Upper-tail excess > 0 means actual outcomes exceed the forecast 90th percentile more often than 10%. |
| 8 | injury_information | MEASURED | participation Brier: official-report (REPORTED) minus unverified/projected information states | n/a | 16 | {'n_days': 2, 'share_same_sign': 1.0, 'note': ''} | A negative gap means official reports sharpen P(play) as intended; ~0 means the report adds nothing measurable yet (e.g. opening week). |
| 9 | market_timing | MEASURED | model-minus-market Brier at each pregame window (negative = model better), plus market price discovery | +0.010 [+0.004, +0.016] | 16 | n/a | Window with the smallest (best) model-minus-market gap: LAST_VALID. Prices converge toward the closing line; see price_discovery shares. A model edge that exists only at early windows and vanishes by T-10 is a timing signal, not yet value. |
| 10 | fees_settlement_execution | MEASURED | per-contract trading costs (fee + slippage) and the gross-to-net P&L gap; DNP settlement effect | +0.026 [+0.026, +0.026] | 16 | {'n_days': 2, 'share_same_sign': 1.0, 'note': ''} | Costs average 0.026 per contract; compare with the model's gross edge before reading any ROI. DNP legs and non-executable quotes are listed separately. |

## 10. Next week plan

1. **INCONCLUSIVE**: keep collecting: no lead survives the sample-size floors. Acceptance: n_games >= 40 and >= 200 independent decisions per candidate strategy before any validated-value language

## Control and gates

```json
{
 "control": {
  "status": "OK",
  "strategy_id": "SHADOW_PURE_PREREG_V1",
  "evaluated_at": "2026-10-29T05:03:36.811934+00:00",
  "source_file": "scorecards/value/dt=2026-10-29/scorecards_value_20261029T050336Z_40820977572.jsonl.gz",
  "n_arms": 4,
  "arm": "sim_rotation",
  "capture_window": "pretip",
  "n_decisions": 824,
  "n_games": 29,
  "verdict": "INSUFFICIENT_SAMPLE",
  "verdict_reasons": [
   "n_games 29 < preregistered min_games 40"
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
   "week1": false,
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
   "statement": "Authority is never granted by this gate; VALIDATED_VALUE only makes the strategy eligible for human review."
  },
  "PF_EDGE_STRICT_V1": {
   "strategy_id": "PF_EDGE_STRICT_V1",
   "betting_authority": "NONE",
   "week1": false,
   "verdict": "NO_EVIDENCE_OF_VALUE",
   "verdict_reasons": [
    "ROI after fees -0.1631517052136417 <= 0"
   ],
   "required_prospective_sample": {
    "min_independent_decisions": 200,
    "min_games": 40,
    "roi_ci_lower_bound": "> 0.0 for every clustered CI (game, player)",
    "protocol": "chronological, prospective, preregistered before scoring, original model versions"
   },
   "remaining": {
    "decisions": 0,
    "games": 0
   },
   "statement": "Authority is never granted by this gate; VALIDATED_VALUE only makes the strategy eligible for human review."
  },
  "PF_EDGE_V1": {
   "strategy_id": "PF_EDGE_V1",
   "betting_authority": "NONE",
   "week1": false,
   "verdict": "NO_EVIDENCE_OF_VALUE",
   "verdict_reasons": [
    "ROI after fees -0.1193674706986104 <= 0"
   ],
   "required_prospective_sample": {
    "min_independent_decisions": 200,
    "min_games": 40,
    "roi_ci_lower_bound": "> 0.0 for every clustered CI (game, player)",
    "protocol": "chronological, prospective, preregistered before scoring, original model versions"
   },
   "remaining": {
    "decisions": 0,
    "games": 0
   },
   "statement": "Authority is never granted by this gate; VALIDATED_VALUE only makes the strategy eligible for human review."
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
