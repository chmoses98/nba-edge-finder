# NBA research report: week 1 (2026-10-20 .. 2026-10-26 ET)

**Status: PRELIMINARY** (version 2, generated 2026-10-21T11:00:47Z). Research / paper only.

> PRELIMINARY: the week is not over or settlements/outcomes are incomplete; numbers will change.
> SAMPLE SIZE: 14 independent games in this report. Week-1 evidence cannot establish profitability: the preregistered control needs >= 200 independent decisions across >= 40 games with positive clustered lower confidence bounds before any VALIDATED_VALUE language is allowed.
> NO BETTING AUTHORITY: nothing in this report authorises a wager, a stake change or a model promotion. All trades are paper.

| independent games | player-games | theses | decisions | contracts |
|---|---|---|---|---|
| 14 | 143 | 603 | 155748 | 3587 |

## 1. Data integrity

### Data integrity (2026-10-20 .. 2026-10-26 ET)

- games scheduled: **52** (37 beyond the 36 h projection window, not yet due), started: 3, fully complete evidence: **3**
- missing evidence counts: {'forecast': 1, 'participation_forecast': 1, 'availability_obs': 1}
- pregame slots expected 12, executed/covered 12, missed: none

| game | tip (UTC) | forecasts | obs | game fc | snapshots | decisions | outcome | missing |
|---|---|---|---|---|---|---|---|---|
| BOS@DET | 10-20T19:00 | 8 fam / 9 v | 277 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 21986 | y | - |
| PHI@NYK | 10-20T23:00 | 8 fam / 12 v | 414 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 31104 | y | - |
| OKC@SAS | 10-21T01:30 | 8 fam / 14 v | 453 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 32947 | y | - |
| ATL@ORL | 10-21T23:00 | 8 fam / 6 v | 180 | y | LIVE | 10614 | n | - |
| MIL@WAS | 10-21T23:00 | 8 fam / 6 v | 166 | y | LIVE | 8502 | n | - |
| MIN@MIA | 10-21T23:30 | 8 fam / 6 v | 152 | y | LIVE | 10752 | n | - |
| CHA@BKN | 10-21T23:30 | 8 fam / 6 v | 174 | y | LIVE | 6816 | n | - |
| CHI@TOR | 10-21T23:30 | 8 fam / 6 v | 228 | y | LIVE | 8706 | n | - |
| UTA@MEM | 10-22T00:00 | 8 fam / 6 v | 144 | y | LIVE | 8094 | n | - |
| IND@NOP | 10-22T00:00 | 8 fam / 6 v | 161 | y | LIVE | 9564 | n | - |
| DAL@HOU | 10-22T00:30 | 8 fam / 5 v | 167 | y | LIVE | 8564 | n | - |
| GSW@LAL | 10-22T02:00 | 8 fam / 4 v | 96 | y | LIVE | 4224 | n | - |
| PHX@POR | 10-22T02:00 | 8 fam / 4 v | 80 | y | LIVE | 6126 | n | - |
| SAC@LAC | 10-22T02:30 | 8 fam / 4 v | 86 | y | LIVE | 4728 | n | - |
| CLE@PHI | 10-22T23:00 | 0 fam / 0 v | 0 | n | - | 0 | n | forecast, participation_forecast, availability_obs |


## 2. Projection performance

- minutes challenger: n=68 MAE +5.391 bias -0.876 (CI withheld: TOO_FEW_CLUSTERS (<5 games))
- minutes incumbent: n=51 MAE +10.107 bias +9.953 (CI withheld: TOO_FEW_CLUSTERS (<5 games))
- minutes naive_prior_mean: n=None MAE n/a bias n/a
- participation Brier: +0.115 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) (n=103, games=3); mean P(play) +0.749 vs played rate +0.660
- assists (conditional on playing): n=68 games=3 MAE +1.276 bias -0.061 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) CRPS +0.881 (CI withheld: TOO_FEW_CLUSTERS (<5 games))
- fga (conditional on playing): n=68 games=3 MAE +2.848 bias -0.905 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) CRPS +2.035 (CI withheld: TOO_FEW_CLUSTERS (<5 games))
- points (conditional on playing): n=68 games=3 MAE +4.349 bias -0.461 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) CRPS +3.051 (CI withheld: TOO_FEW_CLUSTERS (<5 games))
- pra (conditional on playing): n=68 games=3 MAE +5.502 bias -0.571 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) CRPS +3.905 (CI withheld: TOO_FEW_CLUSTERS (<5 games))
- rebounds (conditional on playing): n=68 games=3 MAE +1.882 bias -0.227 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) CRPS +1.273 (CI withheld: TOO_FEW_CLUSTERS (<5 games))
- threes (conditional on playing): n=68 games=3 MAE +0.907 bias -0.115 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) CRPS +0.609 (CI withheld: TOO_FEW_CLUSTERS (<5 games))
- team points: MAE +7.598, margin MAE +9.970, total MAE +15.150

## 3. Market comparison

contracts (ladder rungs of a player-game are correlated); CIs resample games

| horizon | contracts | games | Brier model | Brier market mid | diff (model - market) |
|---|---|---|---|---|---|
| T-90 | 872 | 3 | +0.159 | +0.163 | -0.004 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) |
| T-60 | 901 | 3 | +0.158 | +0.161 | -0.004 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) |
| T-30 | 908 | 3 | +0.156 | +0.160 | -0.004 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) |
| T-10 | 909 | 3 | +0.156 | +0.159 | -0.004 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) |
| LAST_VALID | 917 | 3 | +0.155 | +0.159 | -0.004 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) |

## 4. Paper trading

Hypothetical net ROI after fees and slippage (paper only). `selected` = one contract per thesis per horizon; `all candidates` rows are not independent.

| strategy | view | decisions | contracts | theses | games | ROI | ROI CI | hit rate |
|---|---|---|---|---|---|---|---|---|
| PF_ALL_CANDIDATES_V1 | all candidates | 25230 | 917 | 166 | 3 | -0.101 | withheld (few games) | +0.500 |
| PF_EDGE_STRICT_V1 | selected | 7 | 7 | 7 | 2 | +0.409 | withheld (few games) | +0.714 |
| PF_EDGE_STRICT_V1 | all candidates | 21 | 7 | 7 | 2 | +0.289 | withheld (few games) | +0.667 |
| PF_EDGE_V1 | selected | 42 | 42 | 42 | 3 | +0.010 | withheld (few games) | +0.476 |
| PF_EDGE_V1 | all candidates | 272 | 61 | 42 | 3 | +0.160 | withheld (few games) | +0.493 |

Baselines: NO_BET_V1 = 0 by definition; MARKET_ONLY_V1 = quote mid (see section 3); control SHADOW_PURE_PREREG_V1 is read from the shadow branch (see Control).

**Expression ranking** (which market best expresses a basketball thesis; research only): 904 theses scored, 6211 NO_TRADE, status OK

## 5. Market families

Hit rate of the side actually evaluated, by family (descriptive; sample sizes shown).

| family | contracts | games | hit rate |
|---|---|---|---|
| game_spread | None | 3 | +0.500 |
| game_total | None | 3 | +0.503 |
| game_winner | None | 3 | +0.500 |
| player_assists | None | 3 | +0.500 |
| player_points | None | 3 | +0.499 |
| player_pra | None | 3 | +0.504 |
| player_rebounds | None | 3 | +0.495 |
| player_threes | None | 3 | +0.502 |
| team_total | None | 3 | +0.500 |

## 6. Timing

share_h = sum(B_ref - B_h) / sum(B_ref - B_close), B = (mid - y_yes)^2 on contracts present at ref, h and close

| horizon | contracts | games | share of open->close improvement | mean abs move to close |
|---|---|---|---|---|
| T-90 | 544 | 3 | +0.504 | +0.015 |
| T-60 | 544 | 3 | +0.729 | +0.013 |
| T-30 | 544 | 3 | +0.864 | +0.011 |
| T-10 | 544 | 3 | +0.920 | +0.010 |
| LAST_VALID | 544 | 3 | +1.000 | +0.000 |

## 7. Player matchup diagnostics

Segment tables (player, team, stat family, minutes bucket, starter proxy, injury status, opponent, home/away, price range, side, threshold, window, confidence/freshness) are in `report.json` under `sections.7_player_matchup_diagnostics`; cells below the minimum counts are suppressed.

## 8. Patterns

> INSUFFICIENT_SAMPLE: 14 games. Nothing here authorises a change to production parameters or betting; first-week results are never promotion evidence.

Leads are classified, never promoted. `p_holm` is Holm-adjusted over the declared family; exploratory screens use Benjamini-Hochberg (q=0.10).

| id | claim | class | effect | 95% CI | p (Holm) | games needed (observed effect) | note |
|---|---|---|---|---|---|---|---|
| H12 | more than 20% of candidate sides fail the quality / executability gate | INCONCLUSIVE | +0.083 | [+0.012, +0.209] | +0.082 | 19 | not established |
| H01 | challenger minutes forecasts are biased | INCONCLUSIVE | -0.876 | n/a | n/a | 48 | only 3 games |
| H02 | the old simulator under-predicts minutes (negative bias) | INCONCLUSIVE | +9.953 | n/a | n/a | 1 | only 3 games |
| H03 | P(play) is mis-calibrated in the large | INCONCLUSIVE | +0.089 | n/a | n/a | 19 | only 3 games |
| H04 | points projections are biased | INCONCLUSIVE | -0.461 | n/a | n/a | 27 | only 3 games |
| H05 | 80% central intervals for points do not cover 80% | INCONCLUSIVE | -0.006 | n/a | n/a | 340 | only 3 games |
| H06 | the model beats the market mid at T-60 (Brier, points-ladder and other props) | INCONCLUSIVE | -0.004 | n/a | n/a | 47 | only 3 games |
| H07 | the model beats the market mid at some pregame window overall | INCONCLUSIVE | -0.004 | n/a | n/a | 61 | only 3 games |
| H08 | PF_EDGE_V1 selected trades earn positive net P&L (1 per thesis) | INCONCLUSIVE | +0.005 | n/a | n/a | 4315 | only 3 games |
| H09 | NO-side (fade the ladder) candidates earn positive net P&L | INCONCLUSIVE | +0.026 | n/a | n/a | 26 | only 3 games |
| H10 | T-90 market prices are less accurate than T-10/closing prices (late information not yet priced early) | INCONCLUSIVE | +0.002 | n/a | n/a | 34 | only 3 games |
| H11 | selected trades beat the closing line (positive CLV, valid closes only) | INCONCLUSIVE | +0.560 | n/a | n/a | 71 | only 3 games |
| H13 | the DNP fair-price settlement costs more than a void policy assumes | INCONCLUSIVE | n/a | n/a | n/a | n/a | the archive holds no rows for this test yet |

Exploratory screen: NO_DATA no cell reaches n>=30 and games>=8

## 9. Root cause

> INSUFFICIENT_SAMPLE: 14 games; every statistic below is descriptive, not a finding

Minutes under-prediction verdict: **INCUMBENT_BIAS_NOT_NEGATIVE**

| # | class | status | statistic | value | games | repeatability | reading |
|---|---|---|---|---|---|---|---|
| 1 | participation | MEASURED | mean(P(play) - played), challenger | +0.089 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) | 3 | {'n_days': 1, 'share_same_sign': 1.0, 'note': 'fewer than 2 days: repeatability cannot be assessed'} | P(play) is over-confident by 0.089 on average; Brier 0.1154. Participation errors enter unconditional stat error through (p - played) * mu; see decomposition. |
| 2 | starter_rotation_assumptions | MEASURED | minutes bias by role proxy (starter-like - bench) | n/a | 3 | {'n_days': 1, 'share_same_sign': 1.0, 'note': 'fewer than 2 days: repeatability cannot be assessed'} | Role = predicted-minutes bucket (a proxy: starter flags are not archived with outcomes). A starter-minus-bench bias gap away from 0 means the rotation shape (not the overall level) is wrong; bias is conditional on playing. |
| 3 | minutes_allocation | MEASURED | minutes bias (pred - actual), challenger vs incumbent, paired | n/a | 3 | {'n_days': 1, 'share_same_sign': 1.0, 'note': 'fewer than 2 days: repeatability cannot be assessed'} | verdict on the old simulator's systematic minutes under-prediction: INCUMBENT_BIAS_NOT_NEGATIVE. Challenger bias -0.88 min. |
| 4 | usage_and_per_minute_rates | MEASURED | error = r_pred*(m_pred - m_act) + m_act*(r_pred - r_act): rate component, points | +0.223 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) | n/a | {'n_days': 1, 'share_same_sign': 1.0, 'note': 'fewer than 2 days: repeatability cannot be assessed'} | Per-minute rate (usage) accounts for ~80% of the squared-error budget (rate vs minutes components, points); a rate-component mean away from 0 is a usage / efficiency bias independent of minutes. |
| 5 | opponent_adjustment | NO_DATA | points bias: generous minus stingy opponents | n/a | n/a | n/a | NO_DATA: opponent-defence terciles need earlier final games in team_outcomes (unknown early in the season) and game_forecasts |
| 6 | pace | MEASURED | game total error (pred - actual) and correlation with mean player-points error | +8.063 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) | 3 | n/a | Game-total bias +8.06; per-game correlation between total error and mean player-points error: None. A high correlation points at pace/environment (shared by all players) rather than player-specific rates. |
| 7 | distribution_shape_tails | MEASURED | PIT variance ratio / tail excess (observed share beyond the 10%/90% quantiles minus 10%) | +0.018 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) | n/a | n/a | Largest departure of PIT variance from 1: minutes (1.15; >1 = too narrow). Upper-tail excess > 0 means actual outcomes exceed the forecast 90th percentile more often than 10%. |
| 8 | injury_information | MEASURED | participation Brier: official-report (REPORTED) minus unverified/projected information states | n/a | 3 | {'n_days': 1, 'share_same_sign': 1.0, 'note': 'fewer than 2 days: repeatability cannot be assessed'} | A negative gap means official reports sharpen P(play) as intended; ~0 means the report adds nothing measurable yet (e.g. opening week). |
| 9 | market_timing | MEASURED | model-minus-market Brier at each pregame window (negative = model better), plus market price discovery | -0.004 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) | 3 | n/a | Window with the smallest (best) model-minus-market gap: LAST_VALID. Prices converge toward the closing line; see price_discovery shares. A model edge that exists only at early windows and vanishes by T-10 is a timing signal, not yet value. |
| 10 | fees_settlement_execution | MEASURED | per-contract trading costs (fee + slippage) and the gross-to-net P&L gap; DNP settlement effect | +0.026 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) | 3 | {'n_days': 1, 'share_same_sign': 1.0, 'note': 'fewer than 2 days: repeatability cannot be assessed'} | Costs average 0.026 per contract; compare with the model's gross edge before reading any ROI. DNP legs and non-executable quotes are listed separately. |

## 10. Next week plan

1. **OPERATIONAL_DEFECT**: close the evidence gaps found in the data-integrity table. Acceptance: next week: every started game has forecast, availability observations, game forecast, T-60 snapshot, decisions, outcome, team outcome and paper settlement (0 missing) and no missed pregame slot

## Control and gates

```json
{
 "control": {
  "status": "OK",
  "strategy_id": "SHADOW_PURE_PREREG_V1",
  "evaluated_at": "2026-10-21T03:58:38.755295+00:00",
  "source_file": "scorecards/value/dt=2026-10-21/scorecards_value_20261021T035838Z_39541445938.jsonl.gz",
  "n_arms": 4,
  "arm": "sim_rotation",
  "capture_window": "pretip",
  "n_decisions": 27,
  "n_games": 1,
  "verdict": "INSUFFICIENT_SAMPLE",
  "verdict_reasons": [
   "n_decisions 27 < preregistered min_decisions 200",
   "n_games 1 < preregistered min_games 40"
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
    "n_decisions 7 < preregistered min_decisions 200",
    "n_games 2 < preregistered min_games 40"
   ],
   "required_prospective_sample": {
    "min_independent_decisions": 200,
    "min_games": 40,
    "roi_ci_lower_bound": "> 0.0 for every clustered CI (game, player)",
    "protocol": "chronological, prospective, preregistered before scoring, original model versions"
   },
   "remaining": {
    "decisions": 193,
    "games": 38
   },
   "statement": "Week 1 grants no betting authority; this is evidence collection only."
  },
  "PF_EDGE_V1": {
   "strategy_id": "PF_EDGE_V1",
   "betting_authority": "NONE",
   "week1": true,
   "verdict": "INSUFFICIENT_SAMPLE",
   "verdict_reasons": [
    "n_decisions 42 < preregistered min_decisions 200",
    "n_games 3 < preregistered min_games 40"
   ],
   "required_prospective_sample": {
    "min_independent_decisions": 200,
    "min_games": 40,
    "roi_ci_lower_bound": "> 0.0 for every clustered CI (game, player)",
    "protocol": "chronological, prospective, preregistered before scoring, original model versions"
   },
   "remaining": {
    "decisions": 158,
    "games": 37
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
