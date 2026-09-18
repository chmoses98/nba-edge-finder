# Pre-merge production gate — PR #1

Every row was decided by running code against real data, not by reading documentation. Figures come
from `docs/PRE_MERGE_EVIDENCE.md` (generated from live state) and from the four audits recorded in
this PR's commits. A gate is PASS only if it passed **after** the fixes listed beside it.

**Verdict: all nine material gates PASS. 10 blockers were found and fixed before this table was
written; none was waived.** Betting authority stays RESEARCH — this gate is about whether the system
is safe to run and honest about what it knows, not about whether it has edge.

| # | Gate | Result | Evidence |
|---|------|--------|----------|
| A | Schedule / conductor safety | **PASS** (after 5 blocker fixes) | `.trigger/conductor` was committed and the force-guard tested only for the file's existence, so **every scheduled wake forced a full capture** — 144×/day, year-round, and the conductor's real answer was overwritten by a later `$GITHUB_OUTPUT` line. Replayed against the real file: schedule → `FORCE=capture`. Now gated on the push event; file removed. Concurrent archive pushes **silently destroyed one run's entire snapshot**: both runs append to `manifest.jsonl`, so `git rebase` conflicts every time, `\|\| true` left HEAD detached at the other run's tip, and the next push was a no-op returning 0. Reproduced end-to-end in a scratch repo (run B vanished, job green); fixed with `merge=union`, `rebase --abort` per retry, explicit `exit 1`, and a failure-artifact upload — re-verified in the same harness with both runs surviving. Also: 4 failed pushes ended on `sleep` so the step exited 0; the run job fetched the unbounded archive branch with no `--depth`; and `decide` ran `pip install -e .` (~23 s, ~690 MB) 144×/day to read five timestamps — the conductor is now stdlib-only (verified: zero non-stdlib imports). |
| B | Point-in-time integrity | **PASS** | Poisoning every future row (`pts=999`, up to 24,447 rows) changed nothing downstream; `opponent_adjusted_ratings` filters on its own first line. `close_time` is 100% post-buzzer (median tip+2.76 h) and is never used as a tip anywhere in `src/`. `start_time_utc` non-null in 8,188/8,188 team-game rows. Capture never labels a snapshot pregame; `pregame` is recomputed at evaluation from the box-score tip, and post-tip rows are excluded **and counted**. Three real defects fixed: the ET cutoff used a hardcoded `-04:00` (EDT) offset, silently wrong for most of the season; `ContractPrediction` froze `pregame=True` unconditionally into the immutable ledger; and the Elo baseline ordered games by calendar date, letting a game be rated from another that tipped later the same evening. |
| C | Market semantics, every MODELABLE family | **PASS** (after 2 blocker fixes) | Every settled market replayed through the **real** `build_contract` + `settle_contract` with Kalshi's own result **withheld**: game_spread, game_total, team_total, player_points, player_threes **100.000%**; game_winner 99.856%, player_assists 99.994%, player_rebounds 99.928% (127,264/127,285 decided overall). All 21 disagreements resolved individually — 16 are ESPN box-score errors of exactly ±1, provable from Kalshi's *own* ladder, and 4 are two preseason games inverted whole. Regular season + playoffs: 2,694/2,694. Comparator proven at the line (6,859 at-the-line observations, zero exceptions); overtime inclusion proven in both directions (full game 100% incl-OT, halves 100% excl-OT); 0 impossible ladder pairs in 97,026 adjacent pairs. **`player_pra` was MODELABLE on zero evidence** (0 markets in the entire pull) and would have priced at `semantics_confidence='high'` on an assumed shape — demoted to BUILDABLE. **An unknown tricode crashed the whole slate** (`…GUAMIN-GUA`, a real settled preseason market vs a non-NBA club) — now fails closed per-market; swept all 137,059 markets, 0 exceptions. |
| D | Coverage: DISCOVERED = ACCOUNTED FOR | **PASS** (after alarm added) | All 256 discovered series map to exactly one family: 0 unmapped, 0 ambiguous, 0 duplicates. Arithmetic reconciles exactly: Σ per-series = `total_markets` = Σ `support_counts` = **5,552**, with **UNRESOLVED = 0**. A real captured snapshot (2,818 rows) has 0 missing family/support, 0 error rows, sha256 matching the manifest, and zero drift when reclassified under the current ontology. The invariant *held*, but a breach would have been **silent** — a brand-new Kalshi series would classify UNRESOLVED and nothing failed, warned or alerted. Now alarmed: unresolved markets, unclassified markets, series with no ontology entry, pagination that stopped with a live cursor, and truncated order books, surfaced by the workflow as an error annotation. The committed catalog was also two ontology versions stale, claiming 5,011 UNRESOLVED where the truth is 0 — regenerated. |
| E | Simulation invariants / adversarial | **PASS** (after 1 blocker fix) | `team_pts == Σ player_pts` exactly (max deviation **0** over 40k draws, both teams); minutes sum to `240 + 25·n_ot` to 1.7e-13; `Σ period_pts == home_pts` exactly; PRA elementwise exact from the same draws; **0** ladder violations. Convergence honest: 12 seeds, cross-seed spread / claimed SE in 0.82–1.20, 0/23 keys above 1.6×. **Blocker:** the availability term read `(played − p_play)·impact_ppp`, which is identically mean-zero, so injury news could not move a team's expected points at *any* coefficient — verified: impact 0.0/0.03/0.06 gave byte-identical results, and ruling out a 29.7-ppg star cost 0.68 points. Algebra fixed (baseline is now the availability the rating was earned with; at impact 0.06 the same absence is −5.65 pts). **The model gap remains and is declared, not papered over:** `impact_ppp` is unestimated, so there is **no team-level injury response** in production. Every result carries `diagnostics["team_injury_response_modeled"]` (0.0 today), `docs/SIMULATION.md` L2 states it as the headline limitation, and promotion above RESEARCH is explicitly gated on estimating it. |
| F | Execution economics | **PASS** (after 2 blocker fixes) | `taker_fee_cents` matches an independent exact-`Decimal` reference on **707/707** and **909/909** cases; Kalshi's published examples reproduce (10 @ 50¢ = 18¢, 100 @ 50¢ = 175¢); `bet_up_to_cents` monotone with the exact break-even. EV uses the **executable ask, never the mid**: at 40/60 with `p_fair=0.55`, ev_yes = −0.0668, where the mid would have returned +0.0325 and a recommendation. **Blocker:** `p_data or 0.5` — 0.0 is a legitimate deep-OTM probability and is falsy, so a worthless contract became a coin flip worth **+$0.4467/contract, `Gate.OK`, "bet up to 48¢"**. **Blocker:** nothing rejected a crossed book; bid 60 / ask 40 yielded +$0.1832 with no flag (`wide_spread` only fires on spread > 6, so −20 was never "wide"), and a four-sided crossed book reported **both** sides simultaneously profitable. Both now refuse to trade, with regression tests. |
| G | Settlement replay, diverse sample | **PASS** | 130,905 real settled markets replayed against real ESPN box scores: **99.984%** agreement, 3,618 fail closed. Fail-closed verified for postponed / cancelled / suspended / scheduled / in-progress / `is_final=False` / unknown comparator / missing threshold / unknown stat / missing period data / game-id mismatch / low confidence / DNP-without-result / `result="scalar"` (all 3,618 real cases). Idempotent: a second `settle_many` returns the identical object with the same `settled_at_utc` and appends nothing; a `stat_correction_version` bump appends a new record and leaves the old intact. Engine keeps its own answer and flags `DISAGREES_WITH_KALSHI:` rather than deferring. |
| H | Immutability | **PASS** | 15 manifest entries on `data-archive`, every one sha256-hashed and verified; `Ledger.verify()` clean; partitions are content-hashed and never rewritten; a same-second re-run raises `ImmutabilityError` rather than overwriting. (Two known weaknesses recorded as follow-ups, neither a merge blocker: `verify()` does not detect an un-manifested partition that `iter_rows` would read, and the manifest itself has no hash chain.) |
| I | Resource / GitHub hygiene | **PASS** (threshold documented below) | All workflows have timeouts (5/40/20/45/120/180 min). Concurrency group made constant so two refs cannot race for the one archive branch; `contents: write` scoped to the job that needs it; `ci.yml` no longer matches `data-archive`. Kalshi is not abused: a 5 req/s token bucket with `Retry-After` backoff. Cost: with the B1 storm fixed, the off-season conductor does ~1 capture/day instead of 144. |

## Storage migration threshold (gate I)

Measured from the real archive: **250,618 bytes for a 2,818-market snapshot ≈ 89 B/market**, gzip, so
git stores no delta between snapshots and nothing is ever deleted. In season, capture fires on every
10-minute wake while a game is within 36 h — 144 snapshots/day.

| live board | per snapshot | per day | per month | per season | 5 GB reached in |
|---|---:|---:|---:|---:|---:|
| 3,000 markets | 261 KB | 36.6 MB | 1.07 GB | 6.4 GB | 140 days |
| 4,000 markets | 347 KB | 48.9 MB | 1.43 GB | 8.6 GB | 105 days |
| 6,000 markets | 521 KB | 73.3 MB | 2.15 GB | 12.9 GB | 70 days |

**Thresholds and the action each one triggers** (`data-archive` size, checked by the conductor's
archive step):

- **1 GB** — compact closed days to Parquet (`ledger.py` already promises this) and scope
  `Ledger.verify()` to the current run, with a nightly full sweep. A full sha256 of the whole
  archive on all 144 wakes is already the dominant cost of the run job.
- **3 GB** — stop committing full-board snapshots on every wake; keep per-wake capture only for
  markets of games tipping within 6 h, and take one full-board snapshot per hour.
- **5 GB** — GitHub's recommended repository ceiling. Move the archive off git to object storage
  (the ledger's content-hashed layout ports unchanged) and keep only the manifest in the repo.

At a 4,000-market board this is reached about **15 weeks** into a season, so the 1 GB compaction work
must land before the regular season is a month old. It is **not** a merge blocker: the archive is
0.76 MB today and the off-season cadence is one capture per day.

## Findings deliberately not fixed before merge

`docs/AUDIT_FOLLOWUPS.md` lists all 20, each with why it was left. None is a blocker; several are
research tasks and several are judgement calls about gating semantics that should be decided
explicitly rather than slipped in beside a merge. **R1 (no team-level injury response) blocks any
promotion above RESEARCH.**

## What this gate does NOT claim

- **No edge is claimed.** Nothing here measures profitability. The moneyline market-vs-model study
  found the market better than DATA_ONLY, and the prop study compared no contemporaneous prices at
  all, so it establishes nothing about betting.
- **Injuries are not priced into team efficiency.** See gate E. This alone is sufficient reason for
  every family to remain at RESEARCH authority.
- **`rating_scale = 1.6` remains provisional** and was fitted on the same 300 games it is reported
  on; roughly 0.047 nats of the reported 0.569 → 0.522 gain is in-sample.
