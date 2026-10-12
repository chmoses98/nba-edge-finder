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
| `pretip` | 30–90 min before the tip (T-60m, after the injury report) | cron every 15 min, 15:00–03:45 UTC (covers weekend and holiday afternoon tips). With the participation proxy, a pretip capture differs from the morning one only if new box scores arrived; both are kept as captured |

One capture per game per slot. A slot that no run reached is missed; it is never back-filled. Once
collection has started (the first LIVE capture), every eligible game whose slot window closes without a
capture is written once to the `missed/<slot>` family (`reason = NO_CAPTURE_IN_WINDOW`, with the window's
close time and the game status at detection); postponed and cancelled games are not misses. Tips before
~18:13 UTC (noon/1 pm ET) cannot get a `morning` slot from the 14:13 UTC run and are recorded as missed
for that slot; their `pretip` slot is covered by the 15:00 UTC start of the sweeps. The
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
| `missed/<morning\|pretip>/` | one row per eligible game whose slot window closed with no capture after collection started (`NO_CAPTURE_IN_WINDOW`, window close time, game status at detection); written once, never back-filled |
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

## Dry run on Actions (run 38106857709, 2026-10-11 02:58–02:59 UTC, commit 7665b47)

The PR dry run was label-gated (`shadow-dry-run`) and wrote to a throwaway store; nothing was committed.
The artifact is `nba-shadow-pure-dry-run-38106857709`.

- **Live capture (as_of 2026-10-11T02:59:09Z), truly prospective:** 4 **preseason** games on 2026-10-11
  were projected before tip: espn:401898400 (tip 10:00Z), 401898401 (22:30Z), 401901821 (23:00Z) and
  401908941 (2026-10-12 01:00Z). That is 117 eligible players and 585 rows per arm × conditionality file.
  The 7 games of 2026-10-10 were skipped because they were already final (5) or in progress (2). There
  were 0 refusals and 0 traded-player exclusions. The schedule was fetched at 02:59:08Z, before as_of.
- **Replay capture (as_of 2026-10-09T15:00:00Z, labelled REPLAY_DRY_RUN):** espn:401908940 was projected
  (28 eligible, 140 rows per file). espn:401898395 (tip 12:00Z, before the 15:00Z as_of) was **refused,
  at_or_after_kickoff**, which is the refusal rule working on live data.
- **Outcomes:** 2 final ESPN box scores for 2026-10-09, fetched at 02:59:17Z, giving 465 outcome rows.
- **Market listings** (read-only archive board, reconstructed checkpoint + deltas): status OK for both
  captures. The boards were observed at 02:42:21Z (5,502 markets) and 2026-10-09T14:52:48Z (5,364
  markets). They held **0 player-prop listings** for these games, since there are no preseason
  KXNBAPTS/REB/AST/3PT markets, so the listed cohort is empty (n = 0).
- **Evaluation** (replay rows only, so this is not evidence): 1 matured game, 140 player-game-stat rows,
  and gate compare with 140 matched rows. Champion points, unconditional: mean 8.46, Σpred/Σactual 3.08.
  Non-eligible participants took 19 players and 58% of the minutes. That is a preseason game: rotations
  are not representative, and offseason roster moves are invisible to the champion's roster rule until a
  player appears for his new team. Preseason is excluded from live collection.
- **Verification:** 0 internal hash-chain or manifest problems, and the vendored gate CLI
  `validate --require-v1` passed on all 8 projection files.
- The dry run surfaced one bug, fixed afterwards: kind matching counted `market/listings_status` records
  as listings (`n_listing_rows` 2 instead of 0). Matching is now path-component exact, with a test.
