# NBA research report: week 1 (2026-10-20 .. 2026-10-26 ET)

**Status: PRELIMINARY** (version 7, generated 2026-10-26T11:23:39Z). Research / paper only.

> PRELIMINARY: the week is not over or settlements/outcomes are incomplete; numbers will change.
> SAMPLE SIZE: 52 independent games in this report. Week-1 evidence cannot establish profitability: the preregistered control needs >= 200 independent decisions across >= 40 games with positive clustered lower confidence bounds before any VALIDATED_VALUE language is allowed.
> NO BETTING AUTHORITY: nothing in this report authorises a wager, a stake change or a model promotion. All trades are paper.

| independent games | player-games | theses | decisions | contracts |
|---|---|---|---|---|
| 52 | 1789 | 2365 | 856140 | 13360 |

## 1. Data integrity

### Data integrity (2026-10-20 .. 2026-10-26 ET)

- games scheduled: **16** (0 not yet covered by a projection slot (30 h window)), started: 7, fully complete evidence: **7**
- missing evidence counts: none
- pregame slots expected 12, executed/covered 12, missed: none

| game | tip (UTC) | forecasts | obs | game fc | snapshots | decisions | outcome | missing |
|---|---|---|---|---|---|---|---|---|
| LAL@UTA | 10-25T21:00 | 8 fam / 8 v | 216 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 14190 | y | - |
| IND@BKN | 10-25T22:00 | 8 fam / 7 v | 156 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 13380 | y | - |
| ORL@NYK | 10-25T23:00 | 8 fam / 8 v | 301 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 17154 | y | - |
| TOR@MIN | 10-25T23:00 | 8 fam / 8 v | 241 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 17496 | y | - |
| LAC@OKC | 10-25T23:00 | 8 fam / 8 v | 298 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 15498 | y | - |
| DET@PHI | 10-25T23:30 | 8 fam / 8 v | 217 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 14346 | y | - |
| MEM@SAC | 10-26T01:00 | 8 fam / 7 v | 214 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60 | 13932 | y | - |
| WAS@CHA | 10-26T23:00 | 8 fam / 4 v | 133 | y | LIVE | 1320 | n | - |
| MIN@CLE | 10-26T23:00 | 8 fam / 4 v | 72 | y | LIVE | 120 | n | - |
| CHI@BOS | 10-26T23:30 | 8 fam / 4 v | 135 | y | LIVE | 1320 | n | - |
| DAL@MIA | 10-26T23:30 | 8 fam / 4 v | 129 | y | LIVE | 1320 | n | - |
| IND@MIL | 10-27T00:00 | 8 fam / 4 v | 69 | y | LIVE | 120 | n | - |
| PHX@OKC | 10-27T00:00 | 8 fam / 4 v | 76 | y | LIVE | 120 | n | - |
| ATL@HOU | 10-27T00:30 | 8 fam / 4 v | 122 | y | LIVE | 1320 | n | - |
| MEM@UTA | 10-27T01:00 | 8 fam / 4 v | 17 | y | LIVE | 120 | n | - |
| GSW@DEN | 10-27T02:00 | 8 fam / 3 v | 118 | y | LIVE | 1290 | n | - |


## 2. Projection performance

- minutes challenger: n=965 MAE +5.260 bias +0.197 [-0.526, +0.875]
- minutes incumbent: n=696 MAE +8.247 bias +2.346 [+0.643, +4.079]
- minutes naive_prior_mean: n=569 MAE +4.767 bias -0.694 [-1.383, -0.016]
- participation Brier: +0.115 [+0.098, +0.132] (n=1490, games=43); mean P(play) +0.711 vs played rate +0.648
- assists (conditional on playing): n=965 games=43 MAE +1.328 bias -0.026 [-0.154, +0.110] CRPS +0.906 [+0.864, +0.955]
- fga (conditional on playing): n=965 games=43 MAE +2.819 bias -0.001 [-0.250, +0.221] CRPS +1.976 [+1.882, +2.078]
- points (conditional on playing): n=965 games=43 MAE +4.638 bias +0.011 [-0.407, +0.421] CRPS +3.229 [+3.074, +3.385]
- pra (conditional on playing): n=965 games=43 MAE +6.152 bias -0.137 [-0.761, +0.480] CRPS +4.368 [+4.153, +4.605]
- rebounds (conditional on playing): n=965 games=43 MAE +1.851 bias -0.163 [-0.333, -0.005] CRPS +1.294 [+1.223, +1.374]
- threes (conditional on playing): n=965 games=43 MAE +0.839 bias +0.012 [-0.052, +0.080] CRPS +0.547 [+0.512, +0.584]
- team points: MAE +9.622, margin MAE +12.123, total MAE +15.013

## 3. Market comparison

contracts (ladder rungs of a player-game are correlated); CIs resample games

| horizon | contracts | games | Brier model | Brier market mid | diff (model - market) |
|---|---|---|---|---|---|
| T-90 | 12110 | 42 | +0.168 | +0.161 | +0.008 [+0.003, +0.013] |
| T-60 | 12462 | 43 | +0.167 | +0.159 | +0.007 [+0.003, +0.012] |
| T-30 | 12533 | 43 | +0.167 | +0.159 | +0.008 [+0.004, +0.013] |
| T-10 | 12588 | 43 | +0.167 | +0.159 | +0.008 [+0.004, +0.013] |
| LAST_VALID | 12573 | 43 | +0.167 | +0.160 | +0.008 [+0.003, +0.012] |

## 4. Paper trading

Hypothetical net ROI after fees and slippage (paper only). `selected` = one contract per thesis per horizon; `all candidates` rows are not independent.

| strategy | view | decisions | contracts | theses | games | ROI | ROI CI | hit rate |
|---|---|---|---|---|---|---|---|---|
| PF_ALL_CANDIDATES_V1 | all candidates | 282620 | 12785 | 2328 | 43 | -0.109 | [-0.113, -0.105] | +0.500 |
| PF_EDGE_STRICT_V1 | selected | 189 | 189 | 189 | 41 | -0.148 | [-0.346, +0.043] | +0.381 |
| PF_EDGE_STRICT_V1 | all candidates | 568 | 228 | 189 | 41 | -0.172 | [-0.371, +0.033] | +0.373 |
| PF_EDGE_V1 | selected | 549 | 549 | 549 | 43 | -0.115 | [-0.211, -0.021] | +0.423 |
| PF_EDGE_V1 | all candidates | 2925 | 767 | 549 | 43 | -0.114 | [-0.232, +0.013] | +0.400 |

Baselines: NO_BET_V1 = 0 by definition; MARKET_ONLY_V1 = quote mid (see section 3); control SHADOW_PURE_PREREG_V1 is read from the shadow branch (see Control).

**Expression ranking** (which market best expresses a basketball thesis; research only): 8131 theses scored, 27625 NO_TRADE, status OK

## 5. Market families

Hit rate of the side actually evaluated, by family (descriptive; sample sizes shown).

| family | contracts | games | hit rate |
|---|---|---|---|
| game_spread | None | 43 | +0.499 |
| game_total | None | 43 | +0.499 |
| game_winner | None | 43 | +0.493 |
| player_assists | None | 43 | +0.499 |
| player_points | None | 43 | +0.497 |
| player_pra | None | 43 | +0.499 |
| player_rebounds | None | 43 | +0.499 |
| player_threes | None | 43 | +0.500 |
| team_total | None | 43 | +0.499 |

## 6. Timing

share_h = sum(B_ref - B_h) / sum(B_ref - B_close), B = (mid - y_yes)^2 on contracts present at ref, h and close

| horizon | contracts | games | share of open->close improvement | mean abs move to close |
|---|---|---|---|---|
| T-90 | 1552 | 42 | +0.678 | +0.008 |
| T-60 | 1554 | 43 | +0.772 | +0.007 |
| T-30 | 1554 | 43 | +0.937 | +0.006 |
| T-10 | 1554 | 43 | +0.955 | +0.004 |
| LAST_VALID | 1554 | 43 | +1.000 | +0.000 |

## 7. Player matchup diagnostics

Segment tables (player, team, stat family, minutes bucket, starter proxy, injury status, opponent, home/away, price range, side, threshold, window, confidence/freshness) are in `report.json` under `sections.7_player_matchup_diagnostics`; cells below the minimum counts are suppressed.

## 8. Patterns

> Ranked leads are research priorities only; a change to production needs prospective validation on a fresh sample.

Leads are classified, never promoted. `p_holm` is Holm-adjusted over the declared family; exploratory screens use Benjamini-Hochberg (q=0.10).

| id | claim | class | effect | 95% CI | p (Holm) | games needed (observed effect) | note |
|---|---|---|---|---|---|---|---|
| H03 | P(play) is mis-calibrated in the large | PROJECTION_CALIBRATION_ISSUE | +0.063 | [+0.031, +0.097] | +0.002 | 24 | Holm-significant and larger than the equivalence margin |
| H11 | selected trades beat the closing line (positive CLV, valid closes only) | EVIDENCE_AGAINST | -0.607 | [-1.098, -0.144] | +0.097 | 48 | the effect has the opposite sign with a 95% CI excluding 0 |
| H12 | more than 20% of candidate sides fail the quality / executability gate | EVIDENCE_AGAINST | -0.052 | [-0.064, -0.040] | +0.000 | 15 | within the materiality margin |
| H02 | the old simulator under-predicts minutes (negative bias) | EVIDENCE_AGAINST | +2.346 | [+0.643, +4.079] | +0.084 | 65 | 95% CI inside +/-1: no calibration defect of material size detected |
| H08 | PF_EDGE_V1 selected trades earn positive net P&L (1 per thesis) | EVIDENCE_AGAINST | -0.051 | [-0.094, -0.009] | +0.103 | 64 | the effect has the opposite sign with a 95% CI excluding 0 |
| H06 | the model beats the market mid at T-60 (Brier, points-ladder and other props) | EVIDENCE_AGAINST | +0.007 | [+0.003, +0.012] | +0.020 | 38 | the effect has the opposite sign with a 95% CI excluding 0 |
| H07 | the model beats the market mid at some pregame window overall | EVIDENCE_AGAINST | +0.006 | [+0.001, +0.010] | +0.097 | 48 | the effect has the opposite sign with a 95% CI excluding 0 |
| H09 | NO-side (fade the ladder) candidates earn positive net P&L | EVIDENCE_AGAINST | -0.028 | [-0.055, -0.001] | +0.198 | 83 | the effect has the opposite sign with a 95% CI excluding 0 |
| H05 | 80% central intervals for points do not cover 80% | EVIDENCE_AGAINST | -0.015 | [-0.041, +0.012] | +1.000 | 293 | 95% CI inside +/-0.05: no calibration defect of material size detected |
| H01 | challenger minutes forecasts are biased | EVIDENCE_AGAINST | +0.197 | [-0.526, +0.875] | +1.000 | 1135 | 95% CI inside +/-1: no calibration defect of material size detected |
| H04 | points projections are biased | INCONCLUSIVE | +0.011 | [-0.407, +0.421] | +1.000 | 130341 | not established either way |
| H10 | T-90 market prices are less accurate than T-10/closing prices (late information not yet priced early) | EVIDENCE_AGAINST | -0.000 | [-0.001, +0.001] | +1.000 | 224996 | 95% CI lies inside +/-0.002 (practically no effect) |
| H13 | the DNP fair-price settlement costs more than a void policy assumes | INCONCLUSIVE | n/a | n/a | n/a | n/a | fewer than 2 games |

Exploratory screen: OK

## 9. Root cause

> None

Minutes under-prediction verdict: **INCUMBENT_BIAS_NOT_NEGATIVE**

| # | class | status | statistic | value | games | repeatability | reading |
|---|---|---|---|---|---|---|---|
| 1 | participation | MEASURED | mean(P(play) - played), challenger | +0.063 [+0.031, +0.097] | 43 | {'n_days': 6, 'share_same_sign': 1.0, 'note': ''} | P(play) is over-confident by 0.063 on average; Brier 0.1146. Participation errors enter unconditional stat error through (p - played) * mu; see decomposition. |
| 2 | starter_rotation_assumptions | MEASURED | minutes bias by role proxy (starter-like - bench) | n/a | 43 | {'n_days': 6, 'share_same_sign': 0.5, 'note': ''} | Role = predicted-minutes bucket (a proxy: starter flags are not archived with outcomes). A starter-minus-bench bias gap away from 0 means the rotation shape (not the overall level) is wrong; bias is conditional on playing. |
| 3 | minutes_allocation | MEASURED | minutes bias (pred - actual), challenger vs incumbent, paired | n/a | 43 | {'n_days': 6, 'share_same_sign': 0.5, 'note': ''} | verdict on the old simulator's systematic minutes under-prediction: INCUMBENT_BIAS_NOT_NEGATIVE. Challenger bias +0.20 [-0.53, +0.88] min. |
| 4 | usage_and_per_minute_rates | MEASURED | error = r_pred*(m_pred - m_act) + m_act*(r_pred - r_act): rate component, points | +0.092 [-0.169, +0.338] | n/a | {'n_days': 6, 'share_same_sign': 0.6666666666666666, 'note': ''} | Per-minute rate (usage) accounts for ~72% of the squared-error budget (rate vs minutes components, points); a rate-component mean away from 0 is a usage / efficiency bias independent of minutes. |
| 5 | opponent_adjustment | MEASURED | points bias (pred - actual): generous-defence opponents minus stingy ones | n/a | 43 | {'n_days': 6, 'share_same_sign': 0.5, 'note': ''} | If the opponent adjustment works this gap is ~0; a negative gap means the model under-projects against generous defences (adjustment too weak). |
| 6 | pace | MEASURED | game total error (pred - actual) and correlation with mean player-points error | +4.088 [-1.399, +9.296] | 43 | n/a | Game-total bias +4.09 [-1.40, +9.30]; per-game correlation between total error and mean player-points error: 0.7551890707435784. A high correlation points at pace/environment (shared by all players) rather than player-specific rates. |
| 7 | distribution_shape_tails | MEASURED | PIT variance ratio / tail excess (observed share beyond the 10%/90% quantiles minus 10%) | +0.012 [-0.009, +0.034] | n/a | n/a | Largest departure of PIT variance from 1: pra (1.13; >1 = too narrow). Upper-tail excess > 0 means actual outcomes exceed the forecast 90th percentile more often than 10%. |
| 8 | injury_information | MEASURED | participation Brier: official-report (REPORTED) minus unverified/projected information states | n/a | 43 | {'n_days': 6, 'share_same_sign': 1.0, 'note': ''} | A negative gap means official reports sharpen P(play) as intended; ~0 means the report adds nothing measurable yet (e.g. opening week). |
| 9 | market_timing | MEASURED | model-minus-market Brier at each pregame window (negative = model better), plus market price discovery | +0.006 [+0.001, +0.010] | 43 | n/a | Window with the smallest (best) model-minus-market gap: T-60. Prices converge toward the closing line; see price_discovery shares. A model edge that exists only at early windows and vanishes by T-10 is a timing signal, not yet value. |
| 10 | fees_settlement_execution | MEASURED | per-contract trading costs (fee + slippage) and the gross-to-net P&L gap; DNP settlement effect | +0.026 [+0.026, +0.026] | 43 | {'n_days': 6, 'share_same_sign': 1.0, 'note': ''} | Costs average 0.026 per contract; compare with the model's gross edge before reading any ROI. DNP legs and non-executable quotes are listed separately. |

## 10. Next week plan

1. **PROJECTION_CALIBRATION_ISSUE**: P(play) is mis-calibrated in the large. Acceptance: effect keeps its sign over the next prospective sample and the Holm-adjusted p < 0.05 over the declared family

## Control and gates

```json
{
 "control": {
  "status": "OK",
  "strategy_id": "SHADOW_PURE_PREREG_V1",
  "evaluated_at": "2026-10-26T04:05:37.932595+00:00",
  "source_file": "scorecards/value/dt=2026-10-26/scorecards_value_20261026T040537Z_40266802132.jsonl.gz",
  "n_arms": 4,
  "arm": "sim_rotation",
  "capture_window": "pretip",
  "n_decisions": 772,
  "n_games": 27,
  "verdict": "INSUFFICIENT_SAMPLE",
  "verdict_reasons": [
   "n_games 27 < preregistered min_games 40"
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
    "n_decisions 189 < preregistered min_decisions 200"
   ],
   "required_prospective_sample": {
    "min_independent_decisions": 200,
    "min_games": 40,
    "roi_ci_lower_bound": "> 0.0 for every clustered CI (game, player)",
    "protocol": "chronological, prospective, preregistered before scoring, original model versions"
   },
   "remaining": {
    "decisions": 11,
    "games": 0
   },
   "statement": "Week 1 grants no betting authority; this is evidence collection only."
  },
  "PF_EDGE_V1": {
   "strategy_id": "PF_EDGE_V1",
   "betting_authority": "NONE",
   "week1": true,
   "verdict": "NO_EVIDENCE_OF_VALUE",
   "verdict_reasons": [
    "ROI after fees -0.11504569859420466 <= 0"
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
