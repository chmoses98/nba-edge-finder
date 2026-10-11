# NBA PURE shadow collection, 2026-27 (Phase 2)

Prospective, append-only collection of market-independent player-stat forecasts, sports outcomes and,
in a separate file family, market listings. **Research only:** no promotion, no authority, no staking,
and nothing is published to production SIFT data. Nothing here is a result until games mature.

## Arms (frozen, exactly as measured in `MATCHED_DECOMPOSITION.md`)

| arm | model_version | model_frozen_hash | what it is |
|---|---|---|---|
| `sim_rotation` (champion) | `NBA_BASELINE_2026_PRESEASON_V1:sim-rotation-pure` | `sha256:5a4cbda0…193be78` (V1 digest, checked at runtime) | frozen simulator, rotation-mixture minutes, `impact_ppp = 0`, `build_game_params` with **no injury map and no roster** (participation proxy), 2,000 draws, seed sha256(game_id) |
| `ewm5` (simple baseline) | `EWM5_BASELINE_W1` | sha256 of its frozen parameters (half-life 5, NB dispersion fitted before 2024-11-15; re-fit and compared at every capture) | EWM half-life 5 over prior games played, team participation rate, NB / normal spread |

`RATE_PRIOR_5` was REJECTED in Wave 1 and is **not collected**. Players eligible for both teams (traded
between the opponents) are excluded and counted; the V1 collision fix (`PLAYER_TEAM_IDENTITY.md`, opt-in)
is not part of V1.

**Participation:** no point-in-time injury input is used. Every row's lineage includes
`participation_source = proxy_recent_team_games_no_injury_report`. If the data lane's PIT injury capture
reaches main, it can be read read-only as a new, separately labelled arm. It is not wired in here.

**Statistics:** minutes, points, rebounds, assists, threes. Each row carries mean, median, p10, p90, 7
quantiles (0.05…0.95), the fixed sports ladder inside the row (`LADDERS`; never one row per rung),
`participation_probability` = P(appear), and P(≥10 min) as both the minutes ladder rung and a lineage
feature. Unconditional and conditional-on-playing rows go to separate files.

**Lineage (sports-only, with observed_at):** participation proxy, P(start), P(rotation), rotation minutes,
expected minutes (unconditional and given play), FGA/min and usage per minute (given play), team and
opponent pace, expected game pace, team offensive and opponent defensive opponent-adjusted ratings, rest,
back-to-back, home, the simulator's expected team points, and prior games used.

## Captures

| slot | when | note |
|---|---|---|
| `morning` | game day (ET), ≥ 4 h before the scheduled tip | cron 14:13 and 15:43 UTC |
| `pretip` | 30–90 min before the tip (T-60m, after the injury report) | cron every 15 min, 21:00–03:45 UTC. With the participation proxy, a pretip capture differs from the morning one only if new box scores arrived; both are kept as captured |

One capture per game per slot. A slot that no run reached is missed; it is never back-filled. The
collector **refuses** to capture at or after the tip and **raises** if any input was observed at or
after `as_of`. That covers the schedule fetch, the committed history (obtained 2026-09-19T00:37:29Z),
and current-season box rows this collector fetched (`fetched_at < as_of`). It also re-checks the V1
digest and the EWM-5 dispersion, and validates every file with the vendored `pure_gate validate
--require-v1` before writing it.

Current-season history comes from the collector's own outcome store: ESPN box scores, first fetched
version stands. Early-season caveat, inherited unchanged from the champion: a player with no game for
the current team is not eligible until he plays for it, and the first game after a 30+-day gap caps
P(play) at 0.5. Non-eligible participants are counted in every evaluation.

## Record families (store = branch `nba-shadow-pure`, mounted at `data/shadow_pure/nba`)

| kind | content |
|---|---|
| `projections/<arm>/<unconditional\|conditional>/` | pure_forecast.v1 rows |
| `captures/` | per run: slot, mode, as_of, games, refusals, skipped games and why, input provenance, per-game projection digest, code commit |
| `outcomes/box/`, `outcomes/gate/` | ESPN summary box rows (player + team) with `fetched_at`; pure_gate outcome rows (`source=espn_summary`, `observed_at`) |
| `market/listings/`, `market/listings_status/` | **separate family.** Kalshi player-prop listings (points/rebounds/assists/threes) read **read-only** from the existing capture archive (`data-archive`) as reconstructed at `as_of`: ticker, threshold as `at_least`, open time, board observed time, quote cents, `listed_by_as_of`. Written after the projections, never read by them |
| `reconciliation/` | projection↔outcome joins; a listing's venue result vs the box-score outcome mismatch flag |
| `evaluations/` | evaluation reports (only when something new matured) |

The store is append-only and write-once (`ShadowStore` refuses to overwrite). It keeps a sha256
manifest and a hash chain (`chain.jsonl`: link = sha256(prev | path | sha256)). Before each push, the live
job runs `verify --base-ref origin/nba-shadow-pure --gate`. That fails on any modified or deleted file,
a rewritten log, a broken chain, an unlisted file, or a gate refusal.
`tests/test_shadow_pure_immutability.py` tests the check itself and guards `data/shadow_pure/` on main.

## Evaluation

`scripts/nba_shadow_pure.py evaluate` takes the earliest live capture per slot. It scores (a) the
**entire eligible population** and (b) the **pregame market-listed cohort**: listings captured at the
same as_of, on a board observed at or before as_of, and opened by then. The cohort is defined pregame,
never from settlement. Scoring uses the Wave 1 matched-decomposition functions: `stat_scorecard`,
`participation_scorecard`, and game-clustered paired bootstrap, champion vs EWM-5. It also runs the shared
`pure_gate compare`. An eligible player absent from a final box scores 0 / not played, as in Wave 1.
CRPS is the 7-level quantile approximation, because draws are not stored. The output is descriptive only.

## Workflow (`.github/workflows/nba_shadow_pure.yml`)

- `schedule` (default branch only, so after merge) and `workflow_dispatch mode=live`: outcomes, then
  capture `auto`, then evaluate, then verify, then commit and push to `nba-shadow-pure`. It has its own
  concurrency group and never touches `data-archive`, which it reads read-only. On failure the store is
  uploaded as an artifact.
- `workflow_dispatch mode=dry-run` and `pull_request` with the **`shadow-dry-run` label**: unit tests,
  then a live ESPN fetch and capture of today's not-yet-started and tomorrow's slate (any season type,
  slot window ignored, kickoff rule kept). Then a REPLAY capture of the most recent date with completed
  games (as_of 15:00 UTC that day, inputs cut to before it), that date's outcomes, the market snapshot,
  evaluation, verification and gate CLI validation. Everything goes into a throwaway store, uploaded as
  an artifact, with nothing committed. The PR trigger is label-gated so it never runs alongside `ci.yml`
  under the shared concurrent-job limit.
- Timeouts are 30 min. There are no matrix jobs.

## Size

About 63 KB of gzip projections per game per slot (30 eligible players × 5 stats × 2 conditionalities
× 2 arms). That is roughly 150 MB for a full regular season with both slots, held on the data branch,
not on main.

## Rollback

Disable or delete the workflow. The data branch is independent of main and of `data-archive`, and no
production flow reads it.
