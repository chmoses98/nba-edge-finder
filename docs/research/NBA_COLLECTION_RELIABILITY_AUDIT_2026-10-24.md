# NBA collection reliability audit — 2026-10-24

Scope: data collection, Kalshi market coverage, order books and timing, the research-data pipeline, basketball inputs, projection error diagnostics, and the first
model-vs-Kalshi numbers. **No model, price, threshold, stake, exposure, execution, authority or frozen-control behaviour was changed** (section 9).
Everything below was measured from files on disk (archive checkouts) or from the GitHub API, with the exact command or file named; anything that could not be
measured is marked **UNVERIFIED** with the procedure that would verify it.

## 0. Baseline and limits of this audit

| item | value |
|---|---|
| repo `main` | `8927d69` (PR #57 merged). Open PRs: **#45** (JRM minutes, draft), **#47** (ESPN-OUT blocking, draft), **#48** (Kalshi wagers → `accounting-data`). Not touched. |
| `data-archive` snapshot audited | `9523c12` committed 2026-10-24T06:34:48Z (worker run 40069159793, last tick 06:31:22Z); read-only checkout, 6,859 ledger files |
| `projection-data` snapshot audited | `b1fad93` committed 2026-10-24T01:58:10Z |
| Frozen baseline | `NBA_BASELINE_2026_PRESEASON_V1` digest `5a4cbda0…be78` — intact (`tests/test_baseline_freeze.py` passes; no baseline file in any PR's diff) |
| Kalshi API | **not reachable from this sandbox**: the egress policy returns 403 to CONNECT for `api.elections.kalshi.com`. No workaround was attempted. The *independent read-only live API comparison* (Phase 2A) could therefore **not** be done; see section 7 for the exact procedure. Series/market universe numbers come from the collector's own archived discovery (15,387 series enumerated 2026-10-24T00:12Z) and boards. |
| GitHub Actions | read through the GitHub MCP tools only (run/job timestamps). No workflow was triggered, nothing was merged or deployed. |

## 1. Verification of the earlier observations

| earlier observation | verdict | measurement |
|---|---|---|
| a worker shift achieved 37/37 captures and 38/38 pushes | **consistent, not re-provable** | the commit log has `worker: 40017551302 retired after 37 cycles`; `STATUS_worker.json` keeps only the newest shift. The current shift (run 40049163034): 20/20 captures OK, 21/21 pushes OK. |
| boards held ~8,700–9,500 active markets across exactly 300 series | **partly misleading** | the 300 is the number of series the collector *queries*, not the number that have markets: **129** series had markets on the 06:31 board (9,497 markets). Board size over the last 8 days ranged 7,122 – 15,866 (checkpoint boards), i.e. it breathes with the slate. |
| why exactly 300? | **not a cap** | the queried-series count rose monotonically 256 → 264 → 270 → 280 → 290 → 299 → 300 as Kalshi listed new series (manifest `meta.series`, 2026-09-18 → 10-23). Discovery enumerates all 15,387 series (`n_series_total`), selects 300 NBA by rule, and `iter_series` has no limit. Reaching a round number is a coincidence. A live confirmation needs the API (UNVERIFIED, section 7). |
| 2,901 unresolved contracts in a recent snapshot | **true** | `STATUS_capture.json`: `by_support.UNRESOLVED = 2901`, 31 series (table in section 3). Now 0 (fixture-pinned). |
| full order-book collection capped at 300 | **true** | `--max-orderbooks 300` in both `worker/run.py` and `conductor.yml`; 9,369 live markets on the same board. |
| worker DEGRADED because of classification alarms despite successful capture | **true** | `STATUS_worker.json`: state `DEGRADED`, capture 20/20 OK, push 21/21 OK, `failures: []`, both `reasons` are ontology alarms. |
| ~4,160 games, 112,427 player-games, 137,059 Kalshi markets, 2,400 certified lineup games | **all four exact** | 4,160 includes 198 preseason; 1,383 (all of 2023-24) have no play-by-play; usable regular/play-in/playoff = 3,962; certified = 2,400 of 2,643 PBP games (90.8%), strict-certified 2,068 (78.2%). Detail: Appendix B. |
| paper scorecard: large numbers of excluded invalid identities and orphaned settlements | **counters were mislabelled, no corruption** | section 5. |
| hosted-runner queueing has caused missing pre-tip snapshots | **confirmed with the Actions API** | section 4.3 (62-minute runner wait on 2026-10-22). |

## 2. Findings register (severity, evidence, root cause, disposition)

P0 = data loss / corruption / research invalidity / silent missing pre-tip evidence. P1 = research completeness. P2 = improvement infrastructure.

| # | sev | finding | root cause | disposition |
|---|---|---|---|---|
| F1 | **P0** | `nba evaluate` has processed **0 rows** on every production run (18,231 settled tickers, 29,571 predicted) | worker and `conductor.yml` pass `--out data/archive/eval`; `--out` is the **ledger root**, so evaluate reads an empty directory and exits 0 | PR-B (fix + guard + 3.3× faster). Needs approval (workflow file). |
| F2 | **P0** | **0 of 444,322** archived predictions carry a market quote; `p_market`, `p_hybrid`, CLV and skill-vs-market can never be computed on the legacy path | `workflows/simulate.py:290,321,333` read bare `yes_bid`… which post-API-change boards carry only as `*_dollars`/`_quote_cents` ("§5.14", known since September, never fixed) | **Not changed.** Fixing it populates EV/gate/hybrid in slate output (live-facing). Proposed patch and consequences in PR-B doc; needs your decision. |
| F3 | **P0** | `capture-health` returned `NO_DATA` all season, and when forced to look at games it counted only checkpoint files (1 tick in ~24): "5.6% of intervals within 12 min, max gap 367 min" | graded only games in the *newest* schedule snapshot (which excludes finished games) and `snapshot_times` ignored `kalshi/markets_delta` | PR-A. Real numbers: 92.0% within 12 min, max gap 69 min (section 4). |
| F4 | P1 | a perfectly healthy shift reads DEGRADED | `classify_shift` folded ontology alarms into the collection verdict | PR-A (separate `classification` block + `::warning`). |
| F5 | P1 | **20 NBA-relevant Kalshi series are never captured** (e.g. `KXQUADRUPLEDOUBLE`, `KXSHAI20PTREC`, `KXKNUEPPEL3PTREC`, `KXWINSTREAKOKC`, `KXTATUMRETURN`, `KXLEBRONPLAY`) | the series rule needs `KXNBA` prefix, an `NBA` tag, or the word NBA in the title; these are Basketball-tagged player/team series with none | PR-A: reviewed `nba_series_overrides.yaml`, report lists the rest for review (17 name an NBA team/player). |
| F6 | P1 | 31 series / 2,901 markets UNRESOLVED | new Kalshi families after the 2026-09-18 ontology (protected props, season stat markets, awards, …) | PR-A: each classified from its own rules text; none MODELABLE (section 3). |
| F7 | P1 | a failed series fetch leaves no trace in the immutable record | `_error` rows have no ticker and are dropped by `canonical_board`; the delta chain records the series as *removed*, capture returns 0 | PR-A: `meta.complete=false`, `fetch_errors`, collection alarm; end-to-end tests. (No such partial tick exists in the archive: scanned 2,219 deltas, 0 error rows.) |
| F8 | P1 | order-book evidence is thin and concentrated | priority key = (support rank, quoted, earliest expiry) spends all 300 books on the first game to expire; the set churns completely every ~2 h | PR-A: stratified core + deterministic rotation (section 4.4). |
| F9 | P1 | a tick's stamp is the START of a 2–3 minute read | `observed_at = t0`; markets written median **134 s** later (p90 144, max 260), books **195 s** (max 320) | PR-A: window recorded in each new tick; skip-known-empty cuts the read (section 4.5). |
| F10 | P1 | 6 of 25 successor handovers took > 7 min (63, 24, 18, 15, 9, 8) | hosted-runner queue before the successor job starts (Actions API) | documented; remediation options need your approval (section 4.3). |
| F11 | P1 | paper counters: 64,695 "bad identity", 15,864 "invalid price", 100,749 daily "orphans" | counters conflated expected PASS records and window mismatches with corruption | PR-C (section 5). True orphans: **0**. |
| F12 | P1 | pace diagnostic had no data since day one; revised box scores ignored | `pace_expected` key never written (real keys `home_exp_pace`/`away_exp_pace`); `team_outcomes` kept the first observation | PR-D (section 6). |
| F13 | **P1** | shot-profile recency decay silently **off** (committed feature table has `tip_ts` in kiloseconds); the 2026-09-28 "no value beyond the market" study used it | `astype("int64") // 10**9` under pandas 3 (µs) | PR-E. Conclusion must be re-run on a rebuilt table. |
| F14 | P1 | lineup quarantine was a convention; dashboard said lineup data "absent" | flag column only, hard-coded `absent` | PR-A: `pbp/stints.py`, `OnOffIndex` refuses uncertified rows, dashboard reads disk. |
| F15 | P1 | archive working tree grows ~300 MB/day (`slates/` = 1.6 GB of 1.9 GB) | one 22 MB `packet.json` per simulate pass (20 passes/day), uncompressed | **not changed** (section 4.6); will exhaust a hosted runner's disk in roughly 4–6 weeks. |
| F16 | P1 | suspended markets are invisible: a paused market vanishes from the `open` listing | only `open,unopened` are listed; 7 single-tick disappearances in 2,219 ticks | documented; whether a `paused` listing filter exists is UNVERIFIED (section 7). |
| F18 | **P0** | a capture cycle that fails leaves a push labelled `capture:` but **no tick**; three consecutive cycles failed on 2026-10-22 (45-min hole) | one non-JSON 200 raised out of the client and aborted all series (fixed, 4.7); worker commit subject is written regardless of `capture_ok` | PR-A (client fix, tests); subject left unchanged because the Issue #53 commit index parses it; the hole itself is permanent and not backfilled |
| F17 | P2 | starter confirmation does not exist | ESPN pre-tip starter probe: 0 starters in 52 probes; the injury report has no starter field | research blocker (section 8). |

## 3. Market universe and classification (Phase 2)

Discovered (daily catalog, 2026-10-24T00:12Z): 15,387 Kalshi series; **300 NBA** (+20 reviewed inclusions pending); 14,526 live markets across all statuses at that instant.
Captured (06:31:22Z board): 9,497 markets, 129 series with markets, statuses `active` 9,369 / `initialized` 128. The board shrank from the catalog's 14,526 because
the earlier slate had finished (games' markets leave the open list) — it is not an omission: no catalog series with live markets was absent from the capture list.

Unresolved series on the board, with the settlement semantics read from each market's own `rules_primary`/`rules_secondary` (verified, not guessed):

| series | markets | what it settles on | new classification |
|---|---:|---|---|
| `KXNBA{PTS,REB,AST,3PT}PROT` | 141+150+118+145 | **protected** single-game player prop: same question as the unprotected ladder, but if the player enters in the first half and does **not** enter after halftime the contract resolves to the *fair price before the opening tip* unless the threshold was already reached. Injury not required. DNP-without-entering is *not stated*. Refund value is not on the contract. | 4 RESEARCH families (`player_*_protected`) — must not be priced with the unprotected distribution |
| `KXNBASTATLEADER` | 692 | season leader of a stat (double-doubles…) | `season_stat_leader` RESEARCH |
| `KXNBASTATAVG` | 188 | season per-game **average** ≥ threshold; rounded Source-Agency figure; zero games ⇒ average 0 | `season_player_average` RESEARCH |
| `KXNBAAWARDFIN`, `POTM`, `DPOTM`, `ROTM`, `COTM`, `HUSTLE`, `SJC`, `TEAMMATE`, `EXEC` | 303+120+120+60+30+75+75+74+56 | award finalists / monthly awards / executive (voting; ties pay $1/N) | `awards` UNMODELABLE |
| `KXNBAFINALSOUTCOME` | 250 | exact Finals matchup **and** winner | `finals_outcome` RESEARCH |
| `KXNBAFIRST50PTS`, `PLAYERHIGHSCORE`, `GAMEHIGHSCORE`, `ONE3PT` | 50, 32, 9, 10 | season-long on-court extremes | `season_specials` RESEARCH |
| `KXNBAH2HWINS` | 30 | team A more regular-season wins than B; tie ⇒ 50/50 (**not** a single-game market — the heuristic had guessed `game_unknown`) | `h2h_team_wins` RESEARCH |
| `KXNBALASTTOLOSE`, `POSTASREC`, `TEAMWINSTREAK`, `WINSTREAK` | 30,30,30,6 | season records/streaks | `season_record` RESEARCH |
| `KXNBASEEDOU` | 30 | seed ≤ N before the play-in | `playoff_seed` RESEARCH |
| `KXNBACITYEXPAND`, `FRANCHISECOST`, `FRANCHISEOWNER`, `EUROPEANNOUNCE`, `TOJOINCBA` | 7,7,3,5,25 | business / transactions | `franchise_business` / `transactions` UNMODELABLE |

Support-state discipline kept: *captured → classified → modelable → priced → book-sampled → validated* are counted separately in `COVERAGE_REPORT.json`.
On the 06:31 board: captured 9,497 · classified 9,497 (0 unresolved after the ontology update) · modelable 1,410 · priced (a prediction exists) 2,408 · books 300 (295 two-sided) ·
validated 0 families. `tests/test_market_coverage.py` pins one real market per series and fails if any series becomes UNRESOLVED, if any previously classified series changes
family/support, or if anything new becomes MODELABLE. Series-selection false-positive guard: `KXCOINBASE`, `KXZYNBAN`, WNBA, NCAA, European leagues stay excluded.

## 4. Snapshots, order books and timing (Phase 3)

### 4.1 Integrity of what exists (read-only)
* `Ledger.verify()`: 6,859 manifest entries, every sha256 matches, 0 missing, 0 duplicates, **0 files on disk that are not in the manifest**.
* `nba delta-verify`: **100 / 100 chains reconstruct**, 0 broken.
* No tick carries an error row; 7 markets disappeared for exactly one tick and returned (individual suspensions, re-listed within ≤ 8 min).

### 4.2 Pre-tip coverage, 28 regular-season games tipped 2026-10-17 → 10-24 (`nba capture-health --commit-log`)
1,400 expected intervals: **92.0% within 12 min**, median age 5.3 min, p90 10.1, p99 26.5, max 66; gaps median 10.0, p90 15.0, max 69 min. Verdict `FAIL` against the
Phase-5 criteria (≥ 95% and no gap > 30 min): four gaps > 30 min exist (33, 60, 69 and 31 min between ticks). Three are successor handovers (4.3). The 60-minute one (2026-10-22 07:05:50 → 08:05:50, overnight, no games) is **three consecutive failed capture cycles**: the archive has commits `capture: 39720178587 at …07:20:50Z / 07:35:50Z / 07:50:50Z` but no ledger tick, no manifest line and no file for any of them. The worker pushes a `capture:` commit after *every* cycle, successful or not (`worker/run.py:347`), so the commit subject is not evidence that a tick exists — only the manifest is. The failure itself is not recoverable and must not be backfilled; its cause is UNVERIFIED (needs that job's log). One plausible cause is fixed (4.7).

| horizon | covered ≤ 12 min | stale | missing | observed cover **not yet committed** at the checkpoint | committed cover ≤ 12 min old | commit lag median / p90 / max (s) |
|---|---:|---:|---:|---:|---:|---|
| T-90 | 27 | 1 | 0 | 14 | 26 | 219 / 450 / 502 |
| T-60 | 25 | 3 | 0 | **17** | 21 | 217 / 416 / 456 |
| T-30 | 24 | 4 | 0 | **19** | 22 | 222 / 378 / 544 |
| T-10 | 24 | 4 | 0 | 14 | 20 | 222 / 445 / 485 |

Three clocks, never merged: **observed** (tick stamp = capture start), **written** (manifest `written_at_utc`: +134 s markets, +195 s books), **committed** (git commit
on `data-archive`: ~217 s median after the stamp; a *lower bound* on availability, the push itself is not observed). For 17 of 28 games the tick that "covers" T-60 by the observation
clock was **not yet in the archive** at T-60. Any research decision at a checkpoint must use the committed clock (`published_cover_*` in the report); `nba.paper.latency_diag`
(Issue #53, untouched) already does so for the preregistered studies. The "stale" cells are marginal (12.07 and 12.78 min vs a 12.0 tolerance); the tick cadence inside the last hour is 10 min,
not the planned 5.

### 4.3 Worker continuity
25 handovers in 5 days (`worker: … retired` → `worker: … acquired lease`): median 0.9 min, but **6 exceeded 7 min: 63.1, 24.4, 18.3, 15.3, 8.6, 7.6**. The 63-minute one:
successor run 39833008690 — job created 2026-10-22T18:39:50Z (when the predecessor released the concurrency group), **started 19:41:58Z**: a 62-minute hosted-runner queue. No worker
bug; the earlier "handover ≈ 7 s" experiment measured an idle runner pool. The lease, fail-closed stand-down, retry-budget and final-push logic are covered by the existing
`test_worker_{lease,race,health}.py`; this audit added end-to-end `run_capture` tests for a failed series, a recovered series after a partial tick (delta chain stays verifiable),
pagination cut-off and a book outage. Options (none implemented — each changes the production workflow): retire the worker so a handover never lands in T-120…tip (the dormant
`t60a` lane already prototypes a "quiet-moment handover" — left untouched); a second standby workflow in a separate concurrency group guarded by the lease.

### 4.4 Order books (budget unchanged: 300 requests/tick)
Replay on the 17 finished regular-season games with the board as of T-60 (`scripts/replay_book_policy.py`):

| family (main line = rung nearest 50¢) | legacy: games with the main line booked | stratified-rotation-v1 |
|---|---:|---:|
| moneyline | 6/17 (35%) | **17/17** |
| game spread | 7/17 (41%) | **17/17** |
| game total | 5/17 (29%) | **17/17** |
| team total (per team) | 11/34 (32%) | **34/34** |
| player points / rebounds / assists / threes | 35% / 24% / 18% / 29% | headline players only: 3 per stat per game, one rung each (58 / 54 / 59 / 62 rungs over 17 games) |

The legacy set also turned over completely every ~2 h (Jaccard 0.0 between ticks 2 h apart). The trade-off is explicit: fewer *rungs per ladder* (e.g. spread rungs booked 45/561 vs 231/561) in exchange for
every game having its essentials; 25% of the budget is a deterministic hash rotation (`sha256(policy|tick|ticker)`) that samples the long tail across the day. Selection summary, per-book reason
(`_selected_by`) and policy id are written with each book board. If deep single-game ladders matter for a given study, `PLAYERS_PER_STAT_IN_L1` and `ROTATION_FRACTION` are the two knobs.
API cost: 300 book requests/tick as before; ~920 requests/tick total (582 list + 300 books + 37), ≈ 180–200 s at the client's 5 req/s.

### 4.5 Why a tick takes ~2 minutes, and a cut
171 of 300 queried series had no market, each costing 2 list requests per tick: **342 of 582 list requests (~59%)**. New: a series read OK and empty on the previous complete tick (≤ 45 min old) is
skipped, re-listed on a deterministic 6-tick rotation, never skipped if live in the daily catalog or new to the universe, and the skip is recorded (`meta.series_probe`, `STATUS_capture.series_probe`).
Expected effect ≈ −290 requests/tick and roughly half of the market-read time; **not yet measured** (needs one deployed shift). `--probe-all-series` restores the old behaviour.

### 4.7 One bad response aborted the whole capture (fixed)
`KalshiClient._get` returned `r.json()` on any HTTP 200. A 200 whose body is not JSON (maintenance page, truncated body) raised `JSONDecodeError`, which is not a `KalshiError`, so the
per-series handler in `snapshot_markets` did not catch it: one bad response killed all 300 series (`rc != 0`, no tick, worker moves on after a push). It is now retried like a 5xx and surfaces as `KalshiError`, so
at most one series fails and is recorded as such (F7). Whether this caused the 45-minute hole above is not established.

### 4.6 Storage growth (not changed)
`data-archive` working tree 1.9 GB: `slates/` **1.6 GB** (552 MB on 10-23 alone; 20 passes/day × a 22 MB `packet.json`, 1.34 MB gzipped), `kalshi/` 199 MB, `app/` 67 MB, manifest 16 MB (every tick repeats the full 300-name series list, ~2.3 KB/entry).
Each worker shift fetches and checks out the whole branch (the initial `--depth=1` fetch of this branch took ~10 minutes in this sandbox). At ~300 MB/day the tree passes ~10 GB in about 4–6 weeks, which is
the order of a hosted runner's free disk. Proposals needing approval: gzip `packet.json` (16.6×); sparse-checkout the worker without historical `slates/`; trim `meta.series` to a hash after the first tick of a day.

## 5. The research-data pipeline end to end (Phase 4)

Path: Kalshi market → board tick → forecast → paper decision → game outcome → settlement → scorecard. Joins checked on `projection-data` @ `b1fad93`:

| check | result |
|---|---|
| decisions: 715,089 raw rows, duplicate `decision_id` | 0 |
| settlements: 152,576 rows, duplicates; settlements whose decision exists in no day | 0; **0** |
| strategy mismatches decision↔settlement | 0 |
| forecasts generated after their decision's `as_of` / decisions at-or-after tip (prospective) | 0 / 0 |
| `64,695` "bad identity" | 100% are `PASS` with side `BOTH` for markets the engine could not price: `NO_PERIOD_MODEL` 63,116 + `NO_FORECAST` 1,579; every row has a game and ticker. Real bad identity: **0**. They also tell us that 63k period-market contracts (BUILDABLE) have no model. |
| `15,864` "invalid price" | 100% `PASS` with null price: `NO_EXECUTABLE_QUOTE` 11,562 + `OUTSIDE_PROTOCOL_HORIZON` 4,302. Impossible or crossed prices: **0**. |
| `100,749` "orphaned" on the 2026-10-22 daily card | settlements of *other days'* decisions (window mismatch). Season card: 0 orphans. |
| revised outcomes | 1 team-game (UTA possessions 99.379 → 98.419) and 1 player FGA were revised by ESPN after settlement; the evaluator scored the first value |
| scorecard denominators | the independent unit is the game (cluster bootstrap) and the thesis (one decision per thesis/horizon); a 25-rung ladder is 1 thesis, not 25 (`canonical_yes`, `collapse_units`, `n_theses 1,298` vs `n_decisions 443,208`). Reviewed, correct. |
| DNP semantics | unprotected props settle to a fair price when the player is inactive or never takes the court; the settlement engine fails closed (`UNSETTLEABLE`) unless Kalshi's own result is supplied; protected props differ (section 3) and are not settled at all today. |

Numeric-vs-prose check: minutes bias is `prediction − actual` everywhere; the root-cause class-3 text "under-prediction verdict INCUMBENT_BIAS_NOT_NEGATIVE" is consistent with the incumbent's +10.84 (it over-predicts).
The scorecard's footnote that "starter flags are not archived on the outcome" is **stale** (`outcomes` carries `started`); the postgame stage now uses it as a diagnostic grouping.

## 6. Projection diagnostics and Kalshi comparison (Phases 6–8)

See `docs/research/POSTGAME_DIAGNOSTICS_2026-10-24.md`. Headlines (19 finished games; **below the preregistered 40-game minimum, so direction only**): game totals over-projected +8.55 [+0.93, +16.55];
pace under-projected −3.74 [−5.46, −1.98]; the points error splits exactly into a pace term −4.22 and an efficiency term +8.50; starters' minutes −2.99 vs bench +2.21 (gap −5.19 [−7.27, −3.10]);
the model is worse than the Kalshi mid on player contracts at every horizon (Brier +0.0087 … +0.0094, 4 of 5 intervals exclude 0); PF_EDGE_V1 ROI −0.046 [−0.206, +0.131] on 228 selected theses.

## 7. What could not be verified here, and how to verify it

| item | why not | procedure |
|---|---|---|
| independent live comparison of the collector's universe with Kalshi | `api.elections.kalshi.com` blocked by the sandbox egress policy | from an allowed host: `GET /series` (all pages), filter with `kalshi.discovery.is_nba_series`, compare tickers with `COVERAGE_REPORT.json.capture`; then for 5 sampled series compare `GET /markets?series_ticker=…&status=open` totals with the board. |
| does a `paused`/`inactive` listing exist (suspended markets) | would need the API | `GET /markets?series_ticker=KXNBAPTS&status=paused` on one series; if accepted, add it to `--statuses` for that series only (a rejected filter would otherwise turn every series into an error row). |
| whether the PROT contract settles No/void for a player who never enters | rules text is silent | read 5 settled `KXNBA*PROT` markets after the first week (`result`, `settlement_value`, `expiration_value`). |
| per-push counts of the 37-cycle shift | `STATUS_worker.json` is overwritten each shift | none needed going forward: `capture-health --commit-log` reports every handover. |
| why 9 tipped games lack `outcomes` rows | collection lag suspected | rerun the results stage after the next day's settle; compare `team_outcomes` game ids. |

## 8. Basketball inputs (Phase 5) — summary; full table in Appendix B

Observed facts exist for box minutes/starters (post-game), 2025-26 point-in-time official injury reports (1,320 of 1,322 games `pit_ok`), 2 seasons of certified lineups, shot events (3 seasons), rest/back-to-back.
Modeled only: participation probability, opponent-adjusted ratings, pace, usage. **Missing**: any pregame starter source (**research blocker** — the injury report has no starter field, ESPN's pre-tip starter flags returned 0 in
52 probes, Rotowire is "projected, research-only" with no licence review in the repo), rebound/assist opportunity, defender/tracking data, travel/time-zone, point-in-time availability before 2025-26, and any 2026-27
lineup pipeline (`full_pbp.yml` is manual). Nothing was fabricated or inferred from proxies. Other defects found (all documented in Appendix B, none changed here): 2025-26 shot events disagree with box FGA
(36% exact vs 96–97% — 1,206 "Heave Jump Shot" events), preseason rows in the league prior (`features/build.py:298,417`) and in two research tables, ESPN-vs-NBA team-id split in the shot tables,
a CHI player missing from ESPN's 2025-26 box in 14 team-games, hand-set `STATUS_P_PLAY` constants that differ from measured rates (small n).

## 9. Constraint compliance

| constraint | status |
|---|---|
| PRs #45/#47/#48 | untouched; no overlap with their files |
| frozen baseline, shadow control, Issue #53 protocol, `SEAL_LANES`, control hash, dormant t60a lane | no file under `research/projection_foundation/nba/paper/{exec_*,seal_*,control,study53,compare_lanes}.py`, `exec_shadow_config*.json`, `docs/baseline/`, `exec-shadow-*.yml` appears in any diff; the baseline digest test passes |
| live prediction parameters, authority, thresholds, stakes, exposure, execution | not changed (the evaluate fix produces a research report no engine consumes; §5.14 deliberately **not** fixed) |
| no wagers, no Kalshi account | none; the Kalshi API was not reachable at all |
| no in-place edits of the archive | all archive reads were from detached read-only worktrees; no historical record rewritten; new fields appear only in new ticks |
| no paid services / new infrastructure | none |
| no merge / deploy | none; PRs are open for review |

## 10. Reproduction
```
git worktree add --detach /tmp/da origin/data-archive                       # read-only audit checkout
git log --format='%cI|%s' origin/data-archive > /tmp/commits.txt            # needs --filter=tree:0 --shallow-since to be cheap
nba capture-health --archive /tmp/da --days 7 --commit-log /tmp/commits.txt --out /tmp/ch.json
nba coverage-report --archive /tmp/da --out /tmp/cov
nba delta-verify --archive /tmp/da
python scripts/replay_book_policy.py --archive /tmp/da
(cd research/projection_foundation && python -c "from nba.paper import postgame as P; ...")      # see POSTGAME doc
```

## Appendix A — before / after scorecard

| metric | before | after |
|---|---|---|
| legacy evaluation rows processed per run | **0** | 228,190 (scratch archive copy; 159 s first run, 39 s steady; old full-archive pass 518 s) |
| `capture-health` games graded / verdict | 0 / `NO_DATA` | 28 / measured (92.0% within 12 min, gap max 69 min) |
| market-list requests per tick | ~582 | expected ~290 (not yet measured) |
| UNRESOLVED markets on the board | 2,901 (31 series) | 0, none promoted to MODELABLE |
| NBA-relevant series never captured | 20 | 0 (reviewed list) + 17 more flagged for review |
| shift verdict with 20/20 captures OK | DEGRADED | HEALTHY + separate ontology-debt block (tested) |
| moneyline / spread / total main line with a book at T-60 | 35% / 41% / 29% of games | 100% / 100% / 100% (replay) |
| failed series fetch visible in the archive | no | `meta.complete=false`, `fetch_errors`, alarm |
| paper "bad identity" / "invalid price" (full history) | 64,695 / 15,864 | 0 / 0 (reclassified: unpriced PASS 64,695, no-price PASS 15,864) |
| daily-card "orphaned" settlements (2026-10-22) | 100,749 | 0 (120,964 reported as out-of-window) |
| pace diagnostic | `NO_DATA` | −3.74 [−5.46, −1.98] |
| team outcome revisions scored | first value | newest value, count reported |
| lineup stints in dashboard | "absent" | 2,400 certified / 243 quarantined, historical only; consumers refuse uncertified rows |
| shot-profile 45-day half-life weight at 45 days | 0.9993 (1.9986 of 2.0) | 0.5 |
| model vs Kalshi | not computable on the legacy path; first paper-path numbers: section 6 | unchanged (research only) |

## Appendix B — Phase 5 input audit (full)

See `docs/research/NBA_INPUT_DATA_AUDIT_2026-10-24.md` (inventory, verification of the four headline counts, certification and quarantine analysis, point-in-time availability, observed-vs-modeled table, defect list with file:line). Two of its defects were re-verified by this author and fixed (shot-profile timestamps, lineup quarantine).
