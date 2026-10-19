# NBA paper-trading, evaluation and weekly-report system: design contract

**Authority: RESEARCH / PAPER ONLY.** Nothing here places an order, sizes a stake, touches an account, or promotes a model. Every record
carries `authority: "research_only"` and `paper: true`. The preregistered `SHADOW_PURE_NBA_VALUE_PREREG` strategy (the old V1 simulator
champion, evaluated by `nba-shadow-pure`) is **not** modified, re-implemented or re-labelled; it is the control and is only *read* by
the weekly report. Every strategy below is a separately versioned candidate with its own evaluation protocol, fixed **before** any
prospective record is scored.

Code lives in `research/projection_foundation/nba/paper/`; data lives on the append-only `projection-data` branch.

## 1. Archive layout (immutable = additions only, enforced by `nba.live.ops_guard`)

| Path (under `projection-data`) | Schema | Immutable | Written by |
|---|---|---|---|
| `game_forecasts/nba/<game date UTC>/<HHMMSS>Z_<hash>.jsonl.gz` | `sift.game_forecast.v1` | yes | pregame run (`project` stage) |
| `market_snapshots/nba/<game date UTC>/<HHMMSS>Z_<hash>.jsonl.gz` | `sift.market_snapshot.v1` | yes | `paper` stage / replay |
| `paper/nba/decisions/<game date UTC>/<HHMMSS>Z_<hash>.jsonl.gz` | `sift.paper_decision.v1` | yes | `paper` stage / replay |
| `paper/nba/settlements/<game date UTC>/<HHMMSS>Z_<hash>.jsonl.gz` | `sift.paper_settlement.v1` | yes | `paper_settle` stage (one per decision_id, ever) |
| `paper/nba/corrections/<game date UTC>/...` | `sift.paper_correction.v1` | yes | `paper_settle` (changed authoritative value) |
| `paper/nba/scorecards/daily/<ET date>.{json,md}`, `paper/nba/scorecards/latest.{json,md}` | `sift.paper_scorecard.v1` | no (views) | `daily` stage |
| `reports/nba/<week id>/report.{json,md}`, `tables/*.csv`, `reports/nba/latest.json` | `sift.weekly_report.v1` | no (views, versioned by `report_version`) | `report` stage |
| `ops/nba/slots/...` | `sift.nba_run_ledger.v1` | yes | `ledger` stage |

`<game date UTC>` is the UTC date of the game's tip. Files are named by content hash; writing identical content twice is a no-op.
Pre-existing kinds (`forecasts`, `availability`, `outcomes`, `settlements`, `corrections`) are produced by `pf_core` and untouched.

## 2. Point-in-time discipline (non-negotiable)

* A decision made "as of" instant `t` may use only: forecasts with `generated_utc <= t` **and** `archived_utc <= t`; availability
  observations captured `<= t`; the Kalshi board reconstructed from artifacts observed `<= t` (use `nba_edge.archive.reconstruct`, which
  filters the manifest on `observed_at_utc` before reading anything); nothing from after tip.
* `decision_mode` is `contemporaneous` (the job ran at `t` with a live board) or `asof_replay` (a later job rebuilt the board and the
  forecast set as of `t` from the immutable archives). Replays are legitimate evidence **only because** the inputs are immutable and
  time-filtered, and they are always labelled. Reports show both; `contemporaneous` is the headline where both exist for a horizon.
* Every decision stores `forecast_id`s (or the forecast `generated_utc` + `model_version`) and the board stamp it consumed, so any
  decision can be re-derived.
* Models are never refit on the observations being evaluated. Model versions are preserved verbatim in each record.
* Replay/historical-fixture data is flagged `replay: true` (never counted toward opening-week results). Only records whose `game_start_utc`
  is on/after `2026-10-20T00:00:00Z` **and** `replay=false` are prospective regular-season evidence.

## 3. Horizons

`OPEN` (first valid two-sided board for the game), `T-90`, `T-60`, `T-30`, `T-10` (targets: tip minus N minutes; the snapshot used is the
latest board observed at or before the target), `LAST_VALID` (latest valid pre-tip board; `quote_age_s` is mandatory). `LIVE` is a
contemporaneous decision at an arbitrary run time. Fields `horizon`, `horizon_target_utc`, `board_observed_utc`, `snapshot_gap_s`
(= target − observed) are stored. If the gap exceeds 30 min the horizon is **MISSED_STALE** (recorded with a cause, never labelled as
that horizon, never called a closing line). Missing snapshots are written as `sift.market_snapshot.v1` rows with `status:"MISSING"` and
a `missing_cause` (`NO_BOARD`, `GAP_TOO_LARGE`, `NOT_LISTED`, `ONLY_PLACEHOLDER_QUOTES`, `CHAIN_BROKEN`).
"Closing line" = the `LAST_VALID` snapshot when its gap to tip is <= 15 min; otherwise the `closing_line_valid=false` flag is stored.

## 4. Contract semantics and probabilities

Quote model (from the Kalshi market row, dollars 0..1): `yes_bid`, `yes_ask`, `no_bid = 1 - yes_ask`, `no_ask = 1 - yes_bid`; sizes from
`*_size_fp` and, where an orderbook was captured, depth. A quote is executable only if `kalshi_report.executable_quote`-style rules pass
(two-sided, not a 0.00/0.98-0.99 placeholder, displayed size > 0). Buying YES costs `yes_ask` (+ slippage), buying NO costs `no_ask`.

Fees: `nba_edge.kalshi.fees` (taker, quadratic `0.07 * P * (1-P)`, per-order ceiling to the cent, series multiplier where the market row
carries one). EV uses the continuous per-contract fee; settled P&L uses the whole-order cent-rounded fee for the simulated order size (1
contract unless the strategy says otherwise). Slippage: configurable, default one tick ($0.01) against the trader.

Player-stat markets (`KXNBAPTS/REB/AST/3PT/PRA`, other modelable player markets where a family exists): `X >= k` where `k = floor_strike + 0.5`
for `greater` strikes, `k = floor_strike` for `greater_or_equal`. `p_cond = P(X >= k | plays)` from the archived challenger pmf (`forecasts`,
the pregame version available at `t`). `p_play` from the archived `participation` forecast. **DNP**: Kalshi settles a player prop whose
player never enters at the pre-game fair price (scalar), not as NO and not as a fee-free void. Paper settlement therefore uses the
authoritative market result/settlement value when the archive has it; until then (and for the model's expected value) the DNP leg is
valued, **in the decision-time EV**, at the contract's mid at the decision instant (`m`, no look-ahead). At **settlement** the DNP value is the authoritative
Kalshi value when archived (`dnp_value_source: "authoritative"`), else the `LAST_VALID` mid **only if that snapshot is a valid closing line** (two-sided and
within 15 min of tip; `"modeled_last_valid_mid"`), otherwise the settlement stays pending (no fair-price estimate is invented). Later authoritative values
supersede through append-only correction rows, which evaluation applies. Entry fee is **not** refunded. Participation-aware EV for buying side S at price `a`:
`EV = p_play * (p_S_cond - a) + (1 - p_play) * (m_S - a) - fee - slippage`, where `m_S` is `m` (YES) or `1 - m` (NO). Conditional-only EV
(`ev_conditional`) is also stored (it is what the preregistered control reports as `void`).

Game markets: `KXNBAGAME` winner, `KXNBASPREAD` (`team wins by over X`), `KXNBATOTAL`, `KXNBATEAMTOTAL`, from `sift.game_forecast.v1`
(home/away team-points pmfs + a documented within-game correlation `rho` from `paper_config`), via a Gaussian copula and a fixed-seed
discretisation (deterministic). Period markets (`1H`, `2H`, quarters) have **no validated period model**: their quotes are snapshotted
and their price discovery is analysed, but every candidate is `pass: NO_PERIOD_MODEL`. Unsupported/novelty/futures/off-court series are
not candidates (counted in coverage as `UNSUPPORTED_SERIES`).

## 5. Records

### 5.1 `sift.market_snapshot.v1` (one row per market per board observation used)
`snapshot_id, schema, board_observed_utc, horizon, horizon_target_utc, snapshot_gap_s, game_id, game_start_utc, ticker, event_ticker,
series, family, scope, stat, period, player_id, player_name, team, opponent, threshold (k, X>=k), comparator, status, yes_bid, yes_ask,
no_bid, no_ask, yes_bid_size, yes_ask_size, depth_yes_ask, depth_no_ask, volume, open_interest, last_price, quote_class
(TWO_SIDED|ONE_SIDED|PLACEHOLDER|NO_QUOTE|INVALID|MISSING), missing_cause, replay, source_run_id, captured_utc`.

### 5.2 `sift.paper_decision.v1` (one row per candidate contract-side per decision instant, trade AND pass)
`decision_id` (sha of strategy_id|snapshot_id:forecast_generated_utc|ticker|side: a newer forecast on an unchanged board is a new decision), `schema, strategy_id, strategy_version, config_sha, decision_mode,
decided_utc, as_of_utc, horizon, replay, game_id, game_start_utc, game_date_et, thesis_id, unit_id, cluster_id (= game_id),
entity_id (player), team, opponent, ticker, event_ticker, family, stat, period, threshold, side (YES|NO), price (executable entry),
price_basis (ask), bid, ask, spread, depth_at_entry, quote_age_s, slippage, fee_assumption {multiplier, source, taker}, fee_per_contract,
model_id, model_version, forecast_ids[], forecast_generated_utc, p_model (P(side wins) used for the decision, participation-aware),
p_cond, p_play, p_model_sd (uncertainty: pmf-based sd of the prob + participation + minutes scenarios; method named in
`uncertainty_method`), p_market (side-implied probability: ask-based and mid-based both stored), edge_raw (p_model - price),
ev_gross, ev_net (after fee + slippage, participation-aware), ev_conditional, gate {status, findings}, quality {passed (bool),
failures[]}, decision (TRADE|PASS), reason (enumerated: `EV_ABOVE_THRESHOLD`, `EV_BELOW_THRESHOLD`, `QUALITY_GATE:<code>`,
`NOT_BEST_IN_THESIS`, `EXPOSURE_CAP:<code>`, `NO_PERIOD_MODEL`, `NO_MODEL_FOR_FAMILY`, `NO_FORECAST`, `NO_EXECUTABLE_QUOTE`, `STALE_QUOTE`,
`LATE`), simulated_contracts (0 for PASS), exposure {player, team, game, day notional after this decision}, replay, authority`.

### 5.3 `sift.paper_settlement.v1` (one per decision_id, ever)
`decision_id, strategy_id, settled_utc, outcome_source (kalshi_result|box_score_derived), kalshi_result (yes|no|scalar|void|null), actual
(stat value), participated, dnp, dnp_value (value the contract settled/was valued at), dnp_value_source, won (bool|null), gross_payoff,
fee_paid, net_pnl (per contract, after fee + slippage), net_pnl_if_conditional_void (for the control-comparable view), closing_line:
{ticker, board_observed_utc, yes_bid, yes_ask, mid_yes, valid (bool), age_s}, clv_cents (closing mid of the side minus entry price),
settlement_note`.

### 5.4 `sift.game_forecast.v1`
`game_id, game_start_utc, home, away, generated_utc, data_asof_utc, model_id, model_version, teams: [{team, mean, lo, probs}], rho,
rho_source, context {home, rest_days, b2b, pace_expected, off_rating, def_rating, opp_adjusted... where the model has them, else absent},
inputs_asof`. Only the model's own numbers; never invented.

## 6. Independence units and uncertainty

* Primary independent unit: the **game**. Secondary: the **player-game** (`unit_id`). Never contracts, snapshots, YES/NO complements or ladder
  rungs.
* Cluster bootstrap by `cluster_id` (game), 2,000 replicates, seed 20261020 for paper ROI/P&L/CLV differences (`pf_core.metrics.cluster_bootstrap_diff`
  where applicable). Selected-trade statistics collapse to one decision per `thesis_id` per horizon before inference (the strategy itself
  already keeps at most one contract per thesis; "all candidates" tables are descriptive and say so).
* Daily scorecards and the weekly report always print `n_games`, `n_player_games`, `n_theses`, `n_decisions`, `n_contracts`.

## 7. Strategies (versioned; protocol fixed in `paper_config.json`, sha stamped into each record)

| id | role | rule |
|---|---|---|
| `SHADOW_PURE_PREREG_V1` | control (not run here) | read from `nba-shadow-pure` value scorecards; 200 decisions / 40 games / positive clustered lower bounds for `VALIDATED_VALUE` |
| `PF_ALL_CANDIDATES_V1` | descriptive | every eligible contract, **both sides**, with hypothetical P&L; no selection |
| `PF_EDGE_V1` | candidate | TRADE when quality gates pass and `ev_net >= 0.03`; at most one contract per `thesis_id` per horizon (highest `ev_net`, ties by lower price); exposure caps |
| `PF_EDGE_STRICT_V1` | candidate | `ev_net >= 0.06`, gate PASS only, `p_play >= 0.85` for props, horizons T-90..T-30, spread <= $0.06 |
| `MARKET_ONLY_V1` | benchmark | probability = quote mid; never trades |
| `NO_BET_V1` | baseline | zero P&L by definition |

Exposure constraints (configurable): one paper contract per decision; max 1 trade per `thesis_id`; max 2 trades per player-game across stats;
max 3 per team-game; max 8 per game; max $100 notional per game and $300 per day. Caps apply inside each (strategy, horizon, decision instant): LIVE by run time, replay by board time. Candidates dropped by a cap are stored as PASS with
`EXPOSURE_CAP:*`. Trades on the same game share one cluster, which inference respects.

## 8. Promotion discipline (week 1 and beyond)

Week 1 never grants betting authority. Findings are classified: `OPERATIONAL_DEFECT`, `PROJECTION_CALIBRATION_ISSUE`,
`EXPLORATORY_MARKET_HYPOTHESIS`, `INCONCLUSIVE`, `EVIDENCE_AGAINST`, `ELIGIBLE_FOR_PROSPECTIVE_VALIDATION`. A hypothesis is eligible only if it
was declared in `paper_config.json` hypotheses before the data, has a stated sample requirement, and survives the multiple-testing rule
(Holm over the declared family; Benjamini-Hochberg q=0.10 for exploratory screens labelled as such). The control's thresholds (200
independent decisions, 40 games, positive clustered CI lower bounds) are the minimum bar for any `VALIDATED_VALUE` language.
