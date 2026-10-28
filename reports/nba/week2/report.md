# NBA research report: week 2 (2026-10-27 .. 2026-11-02 ET)

**Status: PRELIMINARY** (version 2, generated 2026-10-28T11:22:42Z). Research / paper only.

> PRELIMINARY: the week is not over or settlements/outcomes are incomplete; numbers will change.
> SAMPLE SIZE: 16 independent games in this report. Week-1 evidence cannot establish profitability: the preregistered control needs >= 200 independent decisions across >= 40 games with positive clustered lower confidence bounds before any VALIDATED_VALUE language is allowed.
> NO BETTING AUTHORITY: nothing in this report authorises a wager, a stake change or a model promotion. All trades are paper.

| independent games | player-games | theses | decisions | contracts |
|---|---|---|---|---|
| 16 | 161 | 276 | 86976 | 2401 |

## 1. Data integrity

### Data integrity (2026-10-27 .. 2026-11-02 ET)

- games scheduled: **55** (39 not yet covered by a projection slot (30 h window)), started: 4, fully complete evidence: **4**
- missing evidence counts: none
- pregame slots expected 11, executed/covered 11, missed: none

| game | tip (UTC) | forecasts | obs | game fc | snapshots | decisions | outcome | missing |
|---|---|---|---|---|---|---|---|---|
| BKN@BOS | 10-27T23:30 | 8 fam / 8 v | 182 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 16226 | y | - |
| DET@NYK | 10-28T00:00 | 8 fam / 8 v | 277 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 16808 | y | - |
| SAC@SAS | 10-28T00:00 | 8 fam / 8 v | 286 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 16568 | y | - |
| POR@LAL | 10-28T03:00 | 8 fam / 9 v | 290 | y | LAST_VALID,LIVE,OPEN,T-10,T-30,T-60,T-90 | 20420 | y | - |
| MIA@ATL | 10-28T23:00 | 8 fam / 5 v | 162 | y | LIVE | 2550 | n | - |
| WAS@CLE | 10-28T23:00 | 8 fam / 5 v | 160 | y | LIVE | 2550 | n | - |
| CHA@DET | 10-28T23:00 | 8 fam / 5 v | 104 | y | LIVE | 2550 | n | - |
| PHI@IND | 10-28T23:00 | 8 fam / 5 v | 195 | y | LIVE | 3150 | n | - |
| ORL@TOR | 10-28T23:30 | 8 fam / 5 v | 184 | y | LIVE | 1638 | n | - |
| NYK@CHI | 10-29T00:00 | 8 fam / 5 v | 87 | y | LIVE | 1950 | n | - |
| HOU@MIL | 10-29T00:00 | 8 fam / 5 v | 154 | y | LIVE | 2322 | n | - |
| GSW@MIN | 10-29T00:00 | 8 fam / 5 v | 164 | y | LIVE | 2550 | n | - |
| DEN@NOP | 10-29T00:00 | 8 fam / 5 v | 169 | y | LIVE | 2676 | n | - |
| SAS@UTA | 10-29T01:00 | 8 fam / 4 v | 104 | y | LIVE | 1920 | n | - |
| OKC@DAL | 10-29T01:30 | 8 fam / 4 v | 204 | y | LIVE | 1692 | n | - |
| LAL@LAC | 10-29T02:30 | 8 fam / 4 v | 85 | y | LIVE | 1920 | n | - |


## 2. Projection performance

- minutes challenger: n=93 MAE +4.048 bias +0.769 (CI withheld: TOO_FEW_CLUSTERS (<5 games))
- minutes incumbent: n=82 MAE +5.956 bias -0.434 (CI withheld: TOO_FEW_CLUSTERS (<5 games))
- minutes naive_prior_mean: n=None MAE n/a bias n/a
- participation Brier: +0.101 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) (n=139, games=4); mean P(play) +0.694 vs played rate +0.669
- assists (conditional on playing): n=93 games=4 MAE +1.279 bias +0.027 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) CRPS +0.849 (CI withheld: TOO_FEW_CLUSTERS (<5 games))
- fga (conditional on playing): n=93 games=4 MAE +2.848 bias +0.152 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) CRPS +1.942 (CI withheld: TOO_FEW_CLUSTERS (<5 games))
- points (conditional on playing): n=93 games=4 MAE +4.510 bias -0.218 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) CRPS +3.094 (CI withheld: TOO_FEW_CLUSTERS (<5 games))
- pra (conditional on playing): n=93 games=4 MAE +5.731 bias +0.147 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) CRPS +3.898 (CI withheld: TOO_FEW_CLUSTERS (<5 games))
- rebounds (conditional on playing): n=93 games=4 MAE +1.648 bias +0.380 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) CRPS +1.104 (CI withheld: TOO_FEW_CLUSTERS (<5 games))
- threes (conditional on playing): n=93 games=4 MAE +0.940 bias -0.048 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) CRPS +0.606 (CI withheld: TOO_FEW_CLUSTERS (<5 games))
- team points: MAE +11.618, margin MAE +12.535, total MAE +18.450

## 3. Market comparison

contracts (ladder rungs of a player-game are correlated); CIs resample games

| horizon | contracts | games | Brier model | Brier market mid | diff (model - market) |
|---|---|---|---|---|---|
| T-90 | 1163 | 4 | +0.176 | +0.162 | +0.013 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) |
| T-60 | 1190 | 4 | +0.176 | +0.163 | +0.013 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) |
| T-30 | 1211 | 4 | +0.176 | +0.163 | +0.013 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) |
| T-10 | 1211 | 4 | +0.176 | +0.163 | +0.013 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) |
| LAST_VALID | 1210 | 4 | +0.176 | +0.163 | +0.013 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) |

## 4. Paper trading

Hypothetical net ROI after fees and slippage (paper only). `selected` = one contract per thesis per horizon; `all candidates` rows are not independent.

| strategy | view | decisions | contracts | theses | games | ROI | ROI CI | hit rate |
|---|---|---|---|---|---|---|---|---|
| PF_ALL_CANDIDATES_V1 | all candidates | 20790 | 1212 | 219 | 4 | -0.095 | withheld (few games) | +0.500 |
| PF_EDGE_STRICT_V1 | selected | 21 | 21 | 21 | 4 | -0.577 | withheld (few games) | +0.190 |
| PF_EDGE_STRICT_V1 | all candidates | 66 | 25 | 21 | 4 | -0.644 | withheld (few games) | +0.167 |
| PF_EDGE_V1 | selected | 43 | 43 | 43 | 4 | -0.431 | withheld (few games) | +0.256 |
| PF_EDGE_V1 | all candidates | 199 | 58 | 43 | 4 | -0.629 | withheld (few games) | +0.171 |

Baselines: NO_BET_V1 = 0 by definition; MARKET_ONLY_V1 = quote mid (see section 3); control SHADOW_PURE_PREREG_V1 is read from the shadow branch (see Control).

**Expression ranking** (which market best expresses a basketball thesis; research only): 9554 theses scored, 34216 NO_TRADE, status OK

## 5. Market families

Hit rate of the side actually evaluated, by family (descriptive; sample sizes shown).

| family | contracts | games | hit rate |
|---|---|---|---|
| game_spread | None | 4 | +0.496 |
| game_total | None | 4 | +0.499 |
| game_winner | None | 4 | +0.480 |
| player_assists | None | 4 | +0.492 |
| player_points | None | 4 | +0.493 |
| player_pra | None | 4 | +0.492 |
| player_rebounds | None | 4 | +0.499 |
| player_threes | None | 4 | +0.498 |
| team_total | None | 4 | +0.497 |

## 6. Timing

share_h = sum(B_ref - B_h) / sum(B_ref - B_close), B = (mid - y_yes)^2 on contracts present at ref, h and close

| horizon | contracts | games | share of open->close improvement | mean abs move to close |
|---|---|---|---|---|
| T-90 | 8 | 4 | -3.769 | +0.008 |
| T-60 | 8 | 4 | -3.947 | +0.009 |
| T-30 | 8 | 4 | -1.585 | +0.006 |
| T-10 | 8 | 4 | -1.407 | +0.005 |
| LAST_VALID | 8 | 4 | +1.000 | +0.000 |

## 7. Player matchup diagnostics

Segment tables (player, team, stat family, minutes bucket, starter proxy, injury status, opponent, home/away, price range, side, threshold, window, confidence/freshness) are in `report.json` under `sections.7_player_matchup_diagnostics`; cells below the minimum counts are suppressed.

## 8. Patterns

> INSUFFICIENT_SAMPLE: 16 games. Nothing here authorises a change to production parameters or betting; first-week results are never promotion evidence.

Leads are classified, never promoted. `p_holm` is Holm-adjusted over the declared family; exploratory screens use Benjamini-Hochberg (q=0.10).

| id | claim | class | effect | 95% CI | p (Holm) | games needed (observed effect) | note |
|---|---|---|---|---|---|---|---|
| H12 | more than 20% of candidate sides fail the quality / executability gate | INCONCLUSIVE | +0.098 | [-0.015, +0.381] | +0.335 | 95 | not established |
| H01 | challenger minutes forecasts are biased | INCONCLUSIVE | +0.769 | n/a | n/a | 62 | only 4 games |
| H02 | the old simulator under-predicts minutes (negative bias) | INCONCLUSIVE | -0.434 | n/a | n/a | 179 | only 4 games |
| H03 | P(play) is mis-calibrated in the large | INCONCLUSIVE | +0.025 | n/a | n/a | 157 | only 4 games |
| H04 | points projections are biased | INCONCLUSIVE | -0.218 | n/a | n/a | 257 | only 4 games |
| H05 | 80% central intervals for points do not cover 80% | INCONCLUSIVE | -0.058 | n/a | n/a | 33 | only 4 games |
| H06 | the model beats the market mid at T-60 (Brier, points-ladder and other props) | INCONCLUSIVE | +0.013 | n/a | n/a | 6 | only 4 games |
| H07 | the model beats the market mid at some pregame window overall | INCONCLUSIVE | +0.013 | n/a | n/a | 7 | only 4 games |
| H08 | PF_EDGE_V1 selected trades earn positive net P&L (1 per thesis) | INCONCLUSIVE | -0.172 | n/a | n/a | 2 | only 4 games |
| H09 | NO-side (fade the ladder) candidates earn positive net P&L | INCONCLUSIVE | -0.082 | n/a | n/a | 3 | only 4 games |
| H10 | T-90 market prices are less accurate than T-10/closing prices (late information not yet priced early) | INCONCLUSIVE | +0.000 | n/a | n/a | 15886 | only 4 games |
| H11 | selected trades beat the closing line (positive CLV, valid closes only) | INCONCLUSIVE | -0.065 | n/a | n/a | 6807 | only 3 games |
| H13 | the DNP fair-price settlement costs more than a void policy assumes | INCONCLUSIVE | n/a | n/a | n/a | n/a | the archive holds no rows for this test yet |

Exploratory screen: NO_DATA no cell reaches n>=30 and games>=8

## 9. Root cause

> INSUFFICIENT_SAMPLE: 16 games; every statistic below is descriptive, not a finding

Minutes under-prediction verdict: **INCUMBENT_BIAS_NOT_NEGATIVE**

| # | class | status | statistic | value | games | repeatability | reading |
|---|---|---|---|---|---|---|---|
| 1 | participation | MEASURED | mean(P(play) - played), challenger | +0.025 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) | 4 | {'n_days': 1, 'share_same_sign': 1.0, 'note': 'fewer than 2 days: repeatability cannot be assessed'} | P(play) is over-confident by 0.025 on average; Brier 0.1012. Participation errors enter unconditional stat error through (p - played) * mu; see decomposition. |
| 2 | starter_rotation_assumptions | MEASURED | minutes bias by role proxy (starter-like - bench) | n/a | 4 | {'n_days': 1, 'share_same_sign': 1.0, 'note': 'fewer than 2 days: repeatability cannot be assessed'} | Role = predicted-minutes bucket (a proxy: starter flags are not archived with outcomes). A starter-minus-bench bias gap away from 0 means the rotation shape (not the overall level) is wrong; bias is conditional on playing. |
| 3 | minutes_allocation | MEASURED | minutes bias (pred - actual), challenger vs incumbent, paired | n/a | 4 | {'n_days': 1, 'share_same_sign': 1.0, 'note': 'fewer than 2 days: repeatability cannot be assessed'} | verdict on the old simulator's systematic minutes under-prediction: INCUMBENT_BIAS_NOT_NEGATIVE. Challenger bias +0.77 min. |
| 4 | usage_and_per_minute_rates | MEASURED | error = r_pred*(m_pred - m_act) + m_act*(r_pred - r_act): rate component, points | -0.404 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) | n/a | {'n_days': 1, 'share_same_sign': 1.0, 'note': 'fewer than 2 days: repeatability cannot be assessed'} | Per-minute rate (usage) accounts for ~79% of the squared-error budget (rate vs minutes components, points); a rate-component mean away from 0 is a usage / efficiency bias independent of minutes. |
| 5 | opponent_adjustment | NO_DATA | points bias: generous minus stingy opponents | n/a | n/a | n/a | NO_DATA: opponent-defence terciles need earlier final games in team_outcomes (unknown early in the season) and game_forecasts |
| 6 | pace | MEASURED | game total error (pred - actual) and correlation with mean player-points error | -11.420 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) | 4 | n/a | Game-total bias -11.42; per-game correlation between total error and mean player-points error: None. A high correlation points at pace/environment (shared by all players) rather than player-specific rates. |
| 7 | distribution_shape_tails | MEASURED | PIT variance ratio / tail excess (observed share beyond the 10%/90% quantiles minus 10%) | +0.018 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) | n/a | n/a | Largest departure of PIT variance from 1: minutes (0.76; >1 = too narrow). Upper-tail excess > 0 means actual outcomes exceed the forecast 90th percentile more often than 10%. |
| 8 | injury_information | MEASURED | participation Brier: official-report (REPORTED) minus unverified/projected information states | n/a | 4 | {'n_days': 1, 'share_same_sign': 1.0, 'note': 'fewer than 2 days: repeatability cannot be assessed'} | A negative gap means official reports sharpen P(play) as intended; ~0 means the report adds nothing measurable yet (e.g. opening week). |
| 9 | market_timing | MEASURED | model-minus-market Brier at each pregame window (negative = model better), plus market price discovery | +0.013 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) | 4 | n/a | Window with the smallest (best) model-minus-market gap: LAST_VALID. Prices converge toward the closing line; see price_discovery shares. A model edge that exists only at early windows and vanishes by T-10 is a timing signal, not yet value. |
| 10 | fees_settlement_execution | MEASURED | per-contract trading costs (fee + slippage) and the gross-to-net P&L gap; DNP settlement effect | +0.026 (CI withheld: TOO_FEW_CLUSTERS (<5 games)) | 4 | {'n_days': 1, 'share_same_sign': 1.0, 'note': 'fewer than 2 days: repeatability cannot be assessed'} | Costs average 0.026 per contract; compare with the model's gross edge before reading any ROI. DNP legs and non-executable quotes are listed separately. |

## 10. Next week plan

1. **INCONCLUSIVE**: keep collecting: no lead survives the sample-size floors. Acceptance: n_games >= 40 and >= 200 independent decisions per candidate strategy before any validated-value language

## Control and gates

```json
{
 "control": {
  "status": "OK",
  "strategy_id": "SHADOW_PURE_PREREG_V1",
  "evaluated_at": "2026-10-28T04:52:32.718601+00:00",
  "source_file": "scorecards/value/dt=2026-10-28/scorecards_value_20261028T045232Z_40634648639.jsonl.gz",
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
    "ROI after fees -0.1857001972386589 <= 0"
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
    "ROI after fees -0.13926300342409914 <= 0"
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
