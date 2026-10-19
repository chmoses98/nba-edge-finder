# NBA research automation: what runs, when, and how to read it

Authority: RESEARCH / PAPER ONLY. No orders, no staking, no account access, no secrets. Baseline `NBA_BASELINE_2026_PRESEASON_V1` and the preregistered control (`SHADOW_PURE_PREREG_V1`) are untouched.

## Workflows

| workflow | trigger | writes | purpose |
|---|---|---|---|
| `capture-worker` (existing, unchanged) | self-renewing long-lived job, cadence 15/10/7/5 min toward tip | `data-archive` | Kalshi boards + order books (delta chains), schedule, rosters, injuries |
| `projection-foundation` | pregame slots 11:20, 13:50, 17:20, 18:20, 19:50, 21:20 ET; settle slot 06:40 ET; every slot has a +25 min backup cron; hourly sweep heartbeat | `projection-data` | availability capture, frozen-model forecasts (player + game), paper decisions, results, settlement, scorecards, weekly report, run ledger |
| `nba-watchdog` | every 30 min | issue `nba-ops-alert` only | reads the archives; opens/updates/closes one alert issue |
| `nba-shadow-pure` (existing, unchanged) | existing schedule | `nba-shadow-pure` | the preregistered control |

### Scheduling rules (why a green run means something)
* Work is organised in ET **slots** (`nba/live/schedule_plan.py`). Any event runs the most recent due slot unless the write-once ledger (`ops/nba/slots/...`) holds it. A late delivery executes the slot; a duplicate/backup/DST-alternate firing is an explicit `already_done` skip; a failed run writes no ledger record, so the next backup firing retries.
* A pregame run whose window contains games but archived no forecast **fails**.
* The always-run `outcome` job lists every stage as EXECUTED / SKIPPED (valid reason) / FAILED and fails the workflow on anything else.

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
