# NBA research report: week 2 (2026-10-27 .. 2026-11-02 ET)

**Status: PRELIMINARY** (version 1, generated 2026-10-27T11:19:03Z). Research / paper only.

> PRELIMINARY: the week is not over or settlements/outcomes are incomplete; numbers will change.
> SAMPLE SIZE: 4 independent games in this report. Week-1 evidence cannot establish profitability: the preregistered control needs >= 200 independent decisions across >= 40 games with positive clustered lower confidence bounds before any VALIDATED_VALUE language is allowed.
> NO BETTING AUTHORITY: nothing in this report authorises a wager, a stake change or a model promotion. All trades are paper.

| independent games | player-games | theses | decisions | contracts |
|---|---|---|---|---|
| 4 | 4 | 14 | 2328 | 358 |

## 1. Data integrity

### Data integrity (2026-10-27 .. 2026-11-02 ET)

- games scheduled: **55** (51 not yet covered by a projection slot (30 h window)), started: 0, fully complete evidence: **0**
- missing evidence counts: none
- pregame slots expected 5, executed/covered 5, missed: none

| game | tip (UTC) | forecasts | obs | game fc | snapshots | decisions | outcome | missing |
|---|---|---|---|---|---|---|---|---|
| BKN@BOS | 10-27T23:30 | 8 fam / 5 v | 87 | y | LIVE | 750 | n | - |
| DET@NYK | 10-28T00:00 | 8 fam / 5 v | 160 | y | LIVE | 750 | n | - |
| SAC@SAS | 10-28T00:00 | 8 fam / 5 v | 166 | y | LIVE | 750 | n | - |
| POR@LAL | 10-28T03:00 | 8 fam / 4 v | 91 | y | LIVE | 492 | n | - |


## 2. Projection performance

- minutes: no data

## 3. Market comparison

NO_DATA: needs settled paper decisions with p_cond/p_model and bid/ask

## 4. Paper trading

NO_DATA: no settled paper decisions

**Expression ranking** (which market best expresses a basketball thesis; research only): 9221 theses scored, 32027 NO_TRADE, status OK

## 5. Market families

NO_DATA

## 6. Timing

NO_DATA

## 7. Player matchup diagnostics

Segment tables (player, team, stat family, minutes bucket, starter proxy, injury status, opponent, home/away, price range, side, threshold, window, confidence/freshness) are in `report.json` under `sections.7_player_matchup_diagnostics`; cells below the minimum counts are suppressed.

## 8. Patterns

> INSUFFICIENT_SAMPLE: 4 games. Nothing here authorises a change to production parameters or betting; first-week results are never promotion evidence.

Leads are classified, never promoted. `p_holm` is Holm-adjusted over the declared family; exploratory screens use Benjamini-Hochberg (q=0.10).

| id | claim | class | effect | 95% CI | p (Holm) | games needed (observed effect) | note |
|---|---|---|---|---|---|---|---|
| H12 | more than 20% of candidate sides fail the quality / executability gate | INCONCLUSIVE | +0.216 | n/a | n/a | 2 | only 4 games |
| H01 | challenger minutes forecasts are biased | INCONCLUSIVE | n/a | n/a | n/a | n/a | the archive holds no rows for this test yet |
| H02 | the old simulator under-predicts minutes (negative bias) | INCONCLUSIVE | n/a | n/a | n/a | n/a | the archive holds no rows for this test yet |
| H03 | P(play) is mis-calibrated in the large | INCONCLUSIVE | n/a | n/a | n/a | n/a | the archive holds no rows for this test yet |
| H04 | points projections are biased | INCONCLUSIVE | n/a | n/a | n/a | n/a | the archive holds no rows for this test yet |
| H05 | 80% central intervals for points do not cover 80% | INCONCLUSIVE | n/a | n/a | n/a | n/a | the archive holds no rows for this test yet |
| H06 | the model beats the market mid at T-60 (Brier, points-ladder and other props) | INCONCLUSIVE | n/a | n/a | n/a | n/a | the archive holds no rows for this test yet |
| H07 | the model beats the market mid at some pregame window overall | INCONCLUSIVE | n/a | n/a | n/a | n/a | the archive holds no rows for this test yet |
| H08 | PF_EDGE_V1 selected trades earn positive net P&L (1 per thesis) | INCONCLUSIVE | n/a | n/a | n/a | n/a | the archive holds no rows for this test yet |
| H09 | NO-side (fade the ladder) candidates earn positive net P&L | INCONCLUSIVE | n/a | n/a | n/a | n/a | the archive holds no rows for this test yet |
| H10 | T-90 market prices are less accurate than T-10/closing prices (late information not yet priced early) | INCONCLUSIVE | n/a | n/a | n/a | n/a | the archive holds no rows for this test yet |
| H11 | selected trades beat the closing line (positive CLV, valid closes only) | INCONCLUSIVE | n/a | n/a | n/a | n/a | the archive holds no rows for this test yet |
| H13 | the DNP fair-price settlement costs more than a void policy assumes | INCONCLUSIVE | n/a | n/a | n/a | n/a | the archive holds no rows for this test yet |

Exploratory screen: NO_DATA no settled canonical contracts

## 9. Root cause

> INSUFFICIENT_SAMPLE: 4 games; every statistic below is descriptive, not a finding

Minutes under-prediction verdict: **None**

| # | class | status | statistic | value | games | repeatability | reading |
|---|---|---|---|---|---|---|---|
| 1 | participation | NO_DATA |  | n/a | n/a | n/a | NO_DATA: no settled forecasts |
| 2 | starter_rotation_assumptions | NO_DATA |  | n/a | n/a | n/a | NO_DATA: no settled forecasts |
| 3 | minutes_allocation | NO_DATA |  | n/a | n/a | n/a | NO_DATA: no settled forecasts |
| 4 | usage_and_per_minute_rates | NO_DATA |  | n/a | n/a | n/a | NO_DATA: no settled forecasts |
| 5 | opponent_adjustment | NO_DATA |  | n/a | n/a | n/a | NO_DATA: no settled forecasts |
| 6 | pace | NO_DATA | game total error and pace error | n/a | n/a | n/a | NO_DATA: needs game_forecasts and team_outcomes (written by the pregame and results stages) |
| 7 | distribution_shape_tails | NO_DATA |  | n/a | n/a | n/a | NO_DATA: no settled forecasts |
| 8 | injury_information | NO_DATA |  | n/a | n/a | n/a | NO_DATA: no settled forecasts |
| 9 | market_timing | NO_DATA | model-minus-market Brier by pregame window | n/a | n/a | n/a | NO_DATA: needs settled paper decisions with p_cond/p_model and bid/ask |
| 10 | fees_settlement_execution | NO_DATA | gross vs net P&L, DNP settlement effect, execution quality | n/a | n/a | n/a | NO_DATA: no settled paper decisions |

## 10. Next week plan

1. **INCONCLUSIVE**: keep collecting: no lead survives the sample-size floors. Acceptance: n_games >= 40 and >= 200 independent decisions per candidate strategy before any validated-value language

## Control and gates

```json
{
 "control": {
  "status": "OK",
  "strategy_id": "SHADOW_PURE_PREREG_V1",
  "evaluated_at": "2026-10-27T04:57:08.490375+00:00",
  "source_file": "scorecards/value/dt=2026-10-27/scorecards_value_20261027T045708Z_40449215938.jsonl.gz",
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
    "ROI after fees -0.15230653965535704 <= 0"
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
    "ROI after fees -0.12195164075993091 <= 0"
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
