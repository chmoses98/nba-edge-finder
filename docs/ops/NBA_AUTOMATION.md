# NBA research automation: what runs, when, and how to read it

Authority: RESEARCH / PAPER ONLY. No orders, no staking, no account access, no secrets. Baseline `NBA_BASELINE_2026_PRESEASON_V1` and the preregistered control (`SHADOW_PURE_PREREG_V1`) are untouched.

## Workflows

| workflow | trigger | writes | purpose |
|---|---|---|---|
| `capture-worker` (existing, unchanged) | self-renewing long-lived job, cadence 15/10/7/5 min toward tip | `data-archive` | Kalshi boards + order books (delta chains), schedule, rosters, injuries |
| `projection-foundation` | pregame slots 11:20, 13:50, 17:20, 18:20, 19:50, 21:20 ET; settle slot 06:40 ET; every slot has a +25 min backup cron; hourly sweep heartbeat | `projection-data` | availability capture, frozen-model forecasts (player + game), paper decisions, results, settlement, scorecards, weekly report, run ledger |
| `nba-ticker` | self-renewing long-lived job (5-min loop, ~5 h), cron backstop starts every 5 h, concurrency group `nba-ticker` | nothing (dispatches only) | asks `nba.live.ticker` which slot is due (past a 12 min grace) but not in the run ledger and dispatches `projection-foundation` for exactly that slot |
| `nba-watchdog` | every 30 min | issue `nba-ops-alert` only | reads the archives; opens/updates/closes one alert issue |
| `nba-shadow-pure` (existing, unchanged) | existing schedule | `nba-shadow-pure` | the preregistered control |

### Scheduling rules (why a green run means something)
* Work is organised in ET **slots** (`nba/live/schedule_plan.py`). Any event runs the most recent due slot unless the write-once ledger (`ops/nba/slots/...`) holds it. A late delivery executes the slot; a duplicate/backup/DST-alternate firing is an explicit `already_done` skip; a failed run writes no ledger record, so the next backup firing retries.
* A pregame run whose window contains games but archived no forecast **fails**.
* The always-run `outcome` job lists every stage as EXECUTED / SKIPPED (valid reason) / FAILED and fails the workflow on anything else.

### Ticker (why GitHub's cron is no longer the clock)
GitHub `schedule` delivery is late or absent (opening day 2026-10-20: the 11:20 and 13:50 ET slots, their backups and the sweep produced no run for 3+ hours). `nba-ticker` is a long-lived job like the capture worker: every 5 minutes it reads the run ledger on `projection-data`, and for a due pregame/settle slot that is missing it runs `gh workflow run projection-foundation.yml -f slot=<ET date>@<HHMM> -f slot_kind=<kind>`. That dispatch serves exactly that slot (named-slot plan), is a valid `already_done` skip if the ledger has it, and writes the same ledger record a scheduled run would.
* It dispatches nothing while a live (`schedule`/`workflow_dispatch`) run is queued or running (PR dry-run CI does not count), never twice for one slot within 25 min, and treats a later manual pregame run as covering an earlier slot. A dispatch that fails, or a run that fails verification, leaves no ledger record, so the slot is requested again on a later tick.
* A slot older than 8 h (pregame) / 30 h (settle) is not resurrected. A slot whose games already started cannot be served: forecasts are archived pre-tip only (late records are rejected, never backdated).
* Self-renewal: at iteration 50 (~4 h 10 min) it queues a successor (`nba-ticker.yml`, waits in the concurrency group until the current job ends) unless one is already queued; the 5-hourly cron is the backstop. `workflow_dispatch` of `nba-ticker.yml` starts one by hand.
* Ledger lookups use `git ls-tree --full-tree`: paths otherwise resolve relative to the current directory and a lookup from `research/projection_foundation` silently reports every slot as missing (found on the first live activation; pinned by a test).
* Operational note: a manual `projection-foundation` dispatch is still valid (unnamed, always runs, recorded as `manual_<HHMMSS>`); the ticker treats it as covering earlier pregame slots.

### Known limits (observed on opening night 2026-10-20)
* **Hosted-runner queueing is the dominant latency.** Jobs waited 4-6 min for a runner (plan/outcome jobs) and the capture worker's successor waited **23.7 min** (created 22:17:18Z, started 22:40:58Z). That left no new Kalshi board between 22:08:59Z and 22:41:44Z; boards cannot be backfilled. Effect on evidence: the T-30 horizon of PHI@NYK used a board 21 min old and the LIVE horizon 33 min old (> `max_board_age_s` 1800), which the engine records as `STALE_QUOTE` passes. The staleness is stamped on every record (`snapshot_gap_s`, `board_observed_utc`), never hidden. The capture worker is left unchanged: a successor dispatched earlier waits in the concurrency group without requesting a runner, so it cannot hide platform queueing.
* **Ticker grace vs. a tip close to a slot.** A slot is requested only after a 12 min grace, then a run needs a runner (4-24 min observed) and ~2 min to run. A game tipping within ~15 min of a slot instant cannot be served by the ticker for that slot (tonight's 21:30 ET OKC@SAS vs the 21:20 ET slot). The previous slot's forecast is the last pre-tip evidence; a named-slot manual dispatch at the slot instant is the documented fallback (`gh workflow run projection-foundation.yml --ref main -f dry_run=false -f slot=<date>@<HHMM> -f slot_kind=pregame`). Forecasts are never backdated: a run after tip rejects that game's records as late.
* **Late schedule events are still useful.** A scheduled event delivered hours late resolves the currently due slot (never the stale one it was meant for) and runs it, or is a valid `already_done` skip. Observed 2026-10-20: the 13:50 ET backup cron delivered at 21:41Z skipped `2026-10-20@1720` as already done; the 17:20 ET primary cron delivered at 23:55Z executed `2026-10-20@1950`.
* **Self-renewal** is observable only after ~4 h 10 min of ticker life (iteration 50); until then it is covered by the shell-loop test, the shared `actions: write` dispatch path (observed working for projection-foundation) and the 5-hourly cron backstop.

## Archive map (`projection-data` branch; additions only unless marked view)

| path | content |
|---|---|
| `availability/nba/<date>/` | availability observations with capture time, source and certainty |
| `forecasts/nba/<game date>/` | per-player pmfs (minutes, points, rebounds, assists, threes, FGA, PRA, participation), challenger and incumbent |
| `game_forecasts/nba/<game date>/` | team-points pmfs per game |
| `market_snapshots/nba/<game date>/` | Kalshi quotes by horizon (OPEN, T-90, T-60, T-30, T-10, LAST_VALID) incl. explicit MISSING rows with causes |
| `paper/nba/decisions/<game date>/` | every candidate (both sides), trade or pass with reason |
| `paper/nba/expressions/<game date>/` | thesis-level expression ranking (research only) |
| `paper/nba/settlements/`, `corrections/` | paper settlement (authoritative Kalshi result when available, else box score) and later corrections |
| `outcomes/`, `team_outcomes/`, `settlements/` | final player and team facts, forecast settlement |
| `ops/nba/slots/` | run ledger |
| `paper/nba/scorecards/daily/<ET date>.{json,md}`, `latest.*` (view) | daily scorecards |
| `reports/nba/week<N>/report.{json,md}`, `tables/*.csv` (view), `versions/v<NNN>.*` (immutable), `reports/nba/latest.json` (index) | weekly reports |

Read without running anything: `git fetch origin projection-data && git show origin/projection-data:reports/nba/week1/report.md`, the job summary of the settle run, and the pinned `NBA week 1 report` issue (updated by the report stage).

## Automatic timeline
* **2026-10-20 (opening day):** 11:20 ET first pregame slot; 13:50 ET slot gives BOS@DET (15:00 ET) a fresh forecast at ~T-70; 17:20 ET picks up the afternoon official injury report; 18:20 / 19:50 / 21:20 ET cover PHI@NYK (19:00 ET) and OKC@SAS (21:30 ET). Each pregame run archives forecasts, game forecasts and paper decisions for the board it sees; the market worker keeps capturing boards every 5-15 min.
* **Every following morning 06:40 ET:** final box scores -> outcomes and team outcomes -> forecast settlement -> as-of replays of T-90/T-60/T-30/T-10/LAST_VALID decisions for games whose horizons have passed (labelled `asof_replay`) -> paper settlement -> daily scorecard -> weekly report refresh.
* **2026-10-27 06:40 ET:** the week-1 report is built for 2026-10-20..26. It is `FINAL` only when every started game has outcomes and settled paper decisions; otherwise `PRELIMINARY` and re-issued (new version) on the following mornings until complete.
