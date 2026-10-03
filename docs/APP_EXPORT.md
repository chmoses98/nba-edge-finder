# Edge Finder app export (`edge_finder.app.v1`)

The app-facing re-expression of this repository's production data, built by `src/nba_edge/app_export.py`
(CLI: `python scripts/app_export.py ...` or `nba app-export ...`) against the vendored, byte-identical contract
package `contract/edge_finder_contract/` (never edited here; `tests/test_app_contract_v1.py::test_vendored_contract_is_intact`
proves it stays so).

**This is an infrastructure pass.** It changes no model weight, simulation assumption, projection, calibration,
fair value, gate, threshold, staking rule or authority. Every NBA family remains **RESEARCH** (`Authority.RESEARCH`
on each `ContractPrediction`), which the export reports as `bet_authority = RESEARCH_ONLY`, recommendation
`status = RESEARCH_CANDIDATE`, `authority = RESEARCH_ONLY`, `research_only = true`.

## Where the app reads it
| | |
|---|---|
| repository | `chmoses98/nba-edge-finder` |
| branch | `data-archive` (the immutable archive branch; registry entry `NBA` in `contract/edge_finder_contract/registry.json`) |
| path | `app/latest/` at the archive root (`data/archive/app/latest` in a worktree) |
| raw base URL | `https://raw.githubusercontent.com/chmoses98/nba-edge-finder/data-archive/app/latest` |

Files: `manifest.json`, `events.json`, `markets.json`, `model_prices.json`, `recommendations.json`, `theses.json`,
`wagers.json`, `settlements.json`, `runs.json`, `board.json`, `performance.json`, `health.json`,
`event_detail/<event_id>.json` (one per event on the board). Compact JSON, sorted keys, atomic publication
(`publish.publish`: validated, cross-referenced, manifest written last; `PublishError` leaves the tree untouched).

## Who runs it
- **Capture worker** (`src/nba_edge/worker/run.py`): `app_export` is the last `SLOW_JOBS` entry
  (`nba app-export --data-root <archive> --out <archive>/app/latest`) and is in `ALWAYS_DUE`, so it runs every
  cycle after capture/context/simulate/settle/evaluate, then `scripts/archive_push.sh` commits `app/latest` with
  the rest of the archive. A failing export is logged like any other failed job and never ends the worker.
- **conductor.yml** (manual / recovery path): step `App export` after `Evaluate`, `continue-on-error: true`, before
  `Verify archive immutability and push`; a later step turns a failed export into a red run AFTER the push so a
  captured snapshot is never lost.
- `app/latest` is not a ledger kind: it is not in `manifest.jsonl`, so `Ledger.verify()` ignores it
  (`test_app_latest_does_not_break_archive_immutability`). `publish` stages beside `latest` (inside `app/`) and
  cleans up after itself.
- On any exception the exporter writes **`health.json` only** (`export_failed = true`, `payload_run_id` = the
  last-known-good manifest's run), keeps the previous payload byte for byte, and exits 1.

## What is exported, from where
| document | source (read-only) | notes |
|---|---|---|
| events | latest `context/schedule` row per game (`workflows.settle.latest_schedule`) | games tipping within the last 48 h or later, plus any game a market references; participants from `identity.teams.registry()` |
| markets | newest captured board, `archive.reconstruct.latest_board` (checkpoint + deltas) | every market on the NBA board (~4,000 in preseason, most of them futures/awards/transactions); semantics from `kalshi.contracts.build_contract` + `kalshi.ticker.parse_ticker`; joined to games with the same (ET date, home, away) rule as `workflows.simulate.markets_for_game` (`test_market_to_game_join_matches_the_simulate_jobs_rule`) |
| model_prices | `slates/latest/slate.json` `contracts[]` joined to the newest `predictions` ledger partition by `prediction_id` | `fair_probability = p_production` (primary), `uncertainty = mc_se` (Monte Carlo SE of DATA_ONLY), `market_probability = p_market`, `inputs_as_of = data_cutoff_utc`, `generated_at = model_ts`; `p_hybrid`, `p_data_only`, gate and reasons in `extensions`; gate -> `data_quality_status` (OK/NO_EDGE -> OK, CANNOT_TRUST_INPUTS, UNSUPPORTED) |
| recommendations | slate contracts with `gate == OK` and a `best_side` | selection = best side; fair/current price converted to the selection (`p_no = 1 - p_yes`, ask of that side); `edge` = the slate's after-fee EV per contract (dollars); `bet_up_to_price` from `bet_up_to_{yes,no}` cents; `native_id = <prediction_id>:<SIDE>` |
| theses | `slate["theses"]` structured groups, one thesis per event | `summary = null` (the repo produces no prose); supporting factors = the group labels + best contract, opposing = group warnings, dependencies = alternative tickers |
| wagers / settlements | `--accounting-dir` = a checkout of `accounting-data`: `data/accounting/{wagers,settlements}.jsonl` via the contract's `routed_ledger.read_jsonl` | `source = KALSHI_ROUTER`, identity from `source_bet_key`; links to model prices / recommendations applied by `linkage.apply_links` (temporal, never by hand); a wager whose market left the board gets a price-less `market_stub` |
| runs | one run per export | `native_run_id = simulate:<slate_dir>` when a slate exists, else `capture:<STATUS_capture.run_id>:<last_capture_utc>` |
| health | `STATUS_capture.json`, `STATUS_simulate.json`, `LEASE_capture.json` (`expected_next_capture_at` -> `next_scheduled_run`), the board's observation time | see thresholds below |
| board / performance / event_detail | the contract's own builders over the documents above | CLV is never computed here (`performance.clv.available = false`) |

The worker does not pass `--accounting-dir` today (the archive worktree holds no `accounting-data` checkout), so
`wagers.json` / `settlements.json` are empty and `router_status` / `settlement_status` are `NOT_APPLICABLE`.

## Identity
- `event_id`: `espn_event_id` with the numeric part of `game_id` (`espn:401902644` -> `401902644`); a bare 10-digit
  NBA id uses `nba_game_id`. The raw `game_id` and team ids/tricodes travel in `source_ids`.
- teams: `nba_team_id` (NBA.com id, `data/identity/teams.csv`), `short_name` = tricode.
- players: `nba_player_id` = the registry's `nba_id` (negative ids are ESPN-derived, as the registry itself uses);
  `source_ids` also carry `espn_athlete_id` and `kalshi_player_uuid`. Resolved via `identity.players.PlayerRegistry`
  (Kalshi uuid alias first, then display name); an unresolved player leaves `player_id = null` and keeps the
  display name in `extensions.entity_name`. Player participants are referenced from markets only.
- markets: `mkt_kalshi_<TICKER>`; recommendations from the prediction id; wagers from `source_bet_key`;
  run ids from (sport, repo, native run id, completed_at) -- deterministic: two runs on the same inputs with the
  same `--now` are byte-identical (`test_two_runs_with_the_same_now_are_byte_identical`).

## Freshness thresholds and status
| component | fresh | stale | why |
|---|---|---|---|
| market_data | 20 min | 3 h | the worker captures every 15 min (down to 5 min inside T-30m) while a game is within its active window, and once a day otherwise (`worker/plan.py`, `workflows/conductor.py`). Off-window the board really is a day old and the export says so. |
| model | 60 min | 6 h | simulate runs when a not-started game tips within 26 h and the last slate is older than 55 min |

`overall_status` follows the contract rule. Until the first `simulate` of the season there is no slate, so
`model_status = UNAVAILABLE`, `model_prices` / `recommendations` are empty, a warning says so, and `overall_status`
is `UNAVAILABLE` -- that is honest, not a bug: `model_required = true` because this repository does have a
production pricing path. Once a slate exists the status becomes `RESEARCH_ONLY` while fresh, `STALE` when either
component ages out. `freshness_status` is `STALE` while the model component is UNKNOWN (contract rule).

## Timestamps
Every emitted timestamp is UTC `...Z`. A naive timestamp anywhere in the inputs makes the build fail (health-only
written, exit 1): `test_a_naive_timestamp_in_the_input_is_refused`. Schedule rows come from ESPN's scoreboard, so
`start_time_confidence = SCHEDULED`; `actual_tip_utc` (when known) is `effective_start_time_utc`.

## Tests
`tests/test_app_contract_v1.py`: contract intact; end-to-end on a synthetic root written with the repo's own
`Ledger`; join rule equals `markets_for_game`; no-slate honesty; determinism; failure safety (payload byte-identical,
health DEGRADED/UNAVAILABLE with errors); first-build failure; far-future `--now` -> STALE; naive input refused; no
naive output; real-data smoke (skips unless `data/archive` or `NBA_APP_EXPORT_DATA_ROOT` holds a manifest); no
secret-shaped strings; wagers/settlements cross reference and P&L equal to the ledger's own sums; CLI + worker
command; archive immutability.

## Real-data proof (2026-10-02, `data-archive` checkout)
40 schedule rows (preseason 2026-10-03 .. 2026-10-12) -> 40 events; 4,093 markets on the newest board (29 joined to
games: the 32 `KXNBAGAME`/`KXNBA1H` contracts of games the 10-day schedule window knows; the 6 for Oct 20 openers
stay unjoined until the schedule covers them); 314 player-linked markets; 0 model prices, 0 recommendations, 0 theses
(no slate yet); health `UNAVAILABLE` (model), `market_data OK`; `verify_published == []`;
`python -m edge_finder_contract validate <out>` -> OK; two runs byte-identical.

## Known gaps
- No slate exists until the first `simulate` of 2026-27 (preseason starts 2026-10-03), so model prices and
  recommendations are empty and `overall_status` is `UNAVAILABLE`. Nothing to fix in the exporter.
- `markets.json` carries the whole NBA board (~4.3 MB in preseason, dominated by futures / awards / transaction
  markets the model never prices). A family filter would shrink it, but the app registry treats the board as market
  inventory, so everything stays. Extensions omit null keys to keep it as small as it honestly can be.
- Player identity resolves through the registry's Kalshi uuid / name aliases (175 records today); players outside
  the registry are exported by display name only.
- `wagers.json` stays empty until the worker is given an `accounting-data` checkout (`--accounting-dir`); the
  importers (`docs/ACCOUNTING.md`) are in place.
- CLV, bankroll history and fees-at-settlement are not produced by this repository and are therefore null.
- The slate's `thesis` groups carry no prose; `theses.summary` is null by design.

## Contract feedback
- `health.build_health` reports `freshness_status = STALE` when the model component is UNKNOWN but market data is
  fresh; for a pre-season repository "UNKNOWN" would read more honestly. Worked around by the warning text.
- `build.event` defaults `last_updated_at` to the wall clock; the adapter passes the schedule row's observation
  time explicitly so output is deterministic.

## Research explorer (`app/latest/explorer/`, contract 1.1.0 research graph)

Built by `src/nba_edge/research_export.py` (CLI `nba research-export --data-root data/archive --out data/archive/app/latest
--history-root data`, or `python scripts/research_export.py ...`) **after** the v1 export, as its own command: the
conductor step `research_export` (continue-on-error, surfaced by a later "fail the job" step after the push) and the
worker job `research_export` (straight after `app_export`, always due). It takes `run_id` and `generated_at` from the v1
`manifest.json`, so both describe the same publication, and writes only `explorer/` through
`research.publish_explorer` (staged, validated, graph- and capability-checked, swapped in index-last; on any failure the
previous tree and every v1 file are untouched and the command exits 1). No network, no model fitting; the one model
function called is the repo's own `features.build.opponent_adjusted_ratings` with the frozen `BuildConfig`, exactly as
`build_game_params` applies it (its values equal the 2026-10-03 slate packet's `off_ppp`/`def_ppp` for TOR and MIA).
Authority on what may be shown: `scratchpad/phase2/audit_nba.md` (audit 2026-10-03).

### What it publishes
| documents | source | content |
|---|---|---|
| `teams/<prt_>.json` (30) | `data/history/espn/team_games_*.parquet` | 12 box metrics (pts, opp_pts, margin, total, possessions, off/def/net rating per 100 stored possessions, win %, 1H points, TOV/100, FT rate) for SEASON (2025-26 regular season) and L10/L5/L3 (last non-preseason games), home/away splits, SOS, rankings context on every ranked number; `extensions.game_log` = every stored game of the last 3 seasons (season_type, q1-q4, OT, possessions, margin, total); `extensions.market_log` = moneyline mid at T-24h/T-6h/T-90m/T-30m/final + settled outcome; ESPN injuries |
| (same profiles, RESEARCH) | `opponent_adjusted_ratings`; `shot_events_2025-26` | adj off/def/net per 100 (one cutoff, the day after the last stored game); shot-zone shares (ESPN team ids mapped through each game's home flag) |
| (same profiles) | `data/research/market_table.parquet` | T-30m moneyline implied win prob, wins minus implied, spread/total/team-total YES minus implied, de-laddered to the line nearest 50c (the repo's own rule) |
| `players/<prt_>.json` (175) | `player_games_*.parquet`, `data/identity/players.jsonl`, latest `context/rosters` | identity-registry players who played 2025-26 or appear in current markets (the same `nba_player_id` participants the v1 markets use): per-game box, shooting %, start rate, usage (min/FGA/FTA), windows and home/away splits, prop residuals per family, `extensions.game_log` (last 82 rows incl. DNP reason, plus_minus), `extensions.prop_log` |
| `events/<evt_>.json` (one per v1 event) | v1 events/markets/model prices, slate packet, ESPN injuries | matchup rows (home vs away on the same metric), registry players of both rosters, every v1 market, v1 model prices as research-only projections, packet quantiles (game margin/total/team points/1H/1Q, player min/pts/reb/ast/3PM; RESEARCH, gated) and `extensions.raw_projection`, venue (arena, neutral site), notes: model-vs-market verdict, gate reasons, the §5.14 quote defect, no lineups, ESPN-only injuries |
| `rankings/` (70) | as above | full universes: 30 teams per metric/window; players with >= 20 regular-season games (all players, profiled or not) for 8 per-game metrics |
| `series/` (428) | as above | per-game team series (pts, opp_pts, margin, total, possessions, T-30m moneyline prob) and player points, last 82 games, rolling 10; per-run model probability (`p_data_only`, RESEARCH, x_axis RUN) for every contract with a prediction |
| `market_history/` (170) | archive board ticks (`iter_board_ticks`: checkpoints + deltas); `candles_KXNBAGAME.jsonl.gz` | one per v1 event (first, every change and latest observation per ticker); hourly moneyline candles for each team's last 5 games of 2025-26 |
| `capabilities.json`, `metrics.json` (46 metrics), `search_index.json`, `index.json` | | |

### Capabilities (audit 2026-10-03)
PARTIAL: team_profiles, player_profiles, event_research, team_metrics, player_metrics, team_game_logs, player_game_logs,
historical_results, opponents, schedule_strength, recent_form_windows, usage, injuries, market_prices, market_price_history,
advanced_stats, situational_splits, player_props, team_props, game_markets, play_by_play (shots only), rankings, time_series,
comparisons, search -- real committed/captured data with the audit's limitations quoted (history pulled manually, last
2026-09-19; registry covers 175 players; preseason-only archive; ESPN-only injuries).
RESEARCH: opponent_adjustment, projection_distributions, raw_projections (gated `CANNOT_TRUST_INPUTS`; §5.14 quote defect,
so the v1 export has 0 model prices), matchup_metrics (neutral by construction), calibration and historical_accuracy
(`docs/research/market_vs_model.json`: the raw Kalshi price has lower log loss than DATA_ONLY in 8 of 8 families -- market
beats model in all 8 families).
UNAVAILABLE: lineups/confirmed starters, weather, venue effects (arena name only), CLV, wager history.
A capability whose data is absent from a given archive (no injury snapshot, no slate packet, ...) is published UNAVAILABLE
with the reason rather than claimed.

### Sizes (real data: data-archive @ 2026-10-03T06:07Z, `research.tree_bytes`)
teams 4.18 MB (max 147 KB), players 8.48 MB (max 56 KB), events 1.49 MB (max 134 KB), rankings 1.28 MB, series 8.91 MB
(max 26 KB), market_history 4.42 MB (max 107 KB), index 251 KB, search 125 KB, metrics 96 KB, capabilities 21 KB:
**29.3 MB per publication**, ~17 s. Every file carries the run id, so every cycle rewrites the whole tree.

### Deliberately not published
Lineups/stints/on-off, confirmed starters, the official injury report (never captured), CLV, wagers, settlements and
evaluations (never run), weather, venue effects, play-by-play beyond shooting plays, PRA markets (0 rows), positive NBA
person ids, raw shot events, the full 653,308-row candle history (only each team's last 5 moneyline games), player series
other than points, the season simulator (not wired to any ledger), and the §5.14 fix (out of scope).
