# Oct 26-27 weekly-rating-block boundary: production and forward-collection verification (2026-10-26)

Research only. Nothing here merges, deploys or activates the joint rotation model (JRM), promotes R1, changes a production projection, a gate, a threshold, a stake or a route, or changes the pre-registered criteria.

## Verdict

| item | result |
|---|---|
| Production pipeline across the Oct 26/27 ET boundary | **PASS**. No intervention required. |
| Forward snapshot of 21:47Z | **PASS**: eligible (12 of 12 games, 414 of 414 rows), pre-tip by 72.7 min, no duplicates, no post-tip information, challenger files identical to the R1 freeze. |
| Runtime shim against main's fix | **Equivalent**: bit-identical output on every input tested; one documented difference (a data-hole guard, below). |
| Missing games | none |

## What happened

2026-27 weekly rating blocks are counted in 7-day steps from the season's first game date (2026-10-20): Oct 20-26 is block 0, Oct 27-Nov 2 is block 1. From the 18:04Z production run on, the 30-hour
window holds games on both Oct 26 and Oct 27 ET. `pf_core.pit.rolling_ridge_ratings` fits every row of every earlier block; Oct 26 slate rows (no pace / efficiency yet) therefore reached sklearn as NaN
when block 1 was rated: `ValueError: Input y contains NaN`. Main fixed this on 2026-10-25 (PR #64, commit `67aa73e0233`, `ridge_ratings_observed` in `nba/features.py`: fit observed games only; a block with no observed
game is rated from earlier observed games plus its own rows). The research branch `claude/nba-minutes-jrm` predates the fix, so the research snapshot of 21:35Z crashed; production did not.

## 1. Production runs the fix (execution evidence, not source presence)

* `67aa73e0233` is an ancestor of main's head `77d3d6c785d` (`git merge-base --is-ancestor`); every `main` run of 2026-10-26 reports `head_sha` = `77d3d6c785d`.
* Run 40374271956 (`projection-foundation` #233, 2026-10-26 18:03Z, slot `2026-10-26@1350`): the `live` job's pipeline step passed (18:04:21-18:11:19Z). Its log shows `capture: 305 observations for 12 games` ->
  `project: 397 players ... archived 3123 challenger forecasts` -> `ledger: EXECUTED_PRODUCED`; no `NaN` or traceback in the 89,667-character log. The published feed is stamped `pf-1.3.0+77d3d6c`, 12 games, start times
  Oct 26 23:00Z through Oct 28 00:00Z (ET dates Oct 26 and Oct 27), archived under three date folders.
* Run 40398551557 (#236, slot `2026-10-26@1720`, started 22:07:30Z after a 43-minute runner queue): ledger `outcome EXECUTED_PRODUCED`, `code_sha 77d3d6c...`, `warnings []`, 13 games in the window, 3143 forecast rows, 3165 challenger forecasts archived, 0 late
  rejected; feed generated 22:07:37Z, 52 minutes before the first tip.
* Backup-cron run #235 (21:19Z) skipped as `already_done` for slot 1350 (a valid duplicate skip, `skip_valid=True`).

### Production-equivalent replay (A/B on the identical feed)

`prod_equiv.py` (scratchpad) calls the checkout's unmodified `nba.project.project_slate` on a slate rebuilt from the 18:04Z production feed (12 games, ET dates Oct 26 and Oct 27):

| code | result |
|---|---|
| main `77d3d6c785d` | OK, 2898 players, 12 games, 0 non-finite means. 2898 of 2898 player-family rows also in the production feed; 97.2% of means are bit-identical (the rest differ by at most 1.06: the replay rebuilds availability and roster inputs from the feed, not from the live captures). |
| `67aa73e0233^` (immediately before the fix) | `ValueError: Input y contains NaN`: the crash reproduces on exactly this input. |

Next scheduled run: run #237 (queued 21:55Z) is waiting for a runner on the same code (`77d3d6c`); the later pregame slots (18:20 ET, 19:50 ET, 21:20 ET) and the ticker backstop (`17 0,5,10,15,20 * * *`) follow. At the time of writing, run #236's research stages were still executing (its critical evidence was already committed). The risk to watch is runner queueing (this evening's slot 1720
started 47 minutes after its target), not the code. **Production: PASS. No intervention required.**

## 2. Recovered 21:47Z forward snapshot (`jrm_v2_uniform/20261026T214718Z_jrm_v2.json.gz`, `verify_snapshot.py`)

* **Pre-tip**: archive-branch commit 21:47:19Z (independent clock), self-reported 21:47:18Z, earliest tip 23:00:00Z: smallest margin 72.7 min against the 5-minute rule on both clocks; every row `pregame`.
* **No duplicates**: 414 unique (game, player) rows; register has 20 distinct files, no conflicting decisions. The evaluators keep the **latest eligible pre-tip snapshot per (game, player)** (`drop_duplicates(..., keep="last")`), so an earlier
  look at the same game can never be counted twice.
* **No post-tip information**: feed generated 18:04:28Z (as-of 18:04:26Z), newest availability capture 18:04:26Z; the history box ends 2026-10-25 (before the first slate day); no outcome-like field or settled value in any row.
* **Consistent with frozen R1**: the file's `code_commit` `2c9f5ca65a3` descends from the freeze `e11565292ef` and `challenger_rules.challenger_ok` passes; the challenger files (`nba/minutes_jrm.py`, `nba/stats.py`, `nba/project.py`,
  `nba/live/reconcile.py`, `results/frozen_params.json`, `results/jrm/*`) are byte-identical from the freeze to the snapshot code and to the current branch head. All 414 rows carry `stats.jrm_refit` (R1), `stats.jrm_engine` (P1) and
  `stats.frozen_published` (P0); R1 differs from P1 on 99.8% of rows (points mean 8.616 vs 9.034): the refit model really ran.
* **Coverage**: 12 feed games = 12 snapshot games, no game missing; per-game rows match the feed's player rows exactly; every team's sum of p x E[min] is 241.5.
* **Eligibility register**: 18 of 20 files eligible; the two ineligible entries are the 2026-10-20 pre-freeze files (v1 and variance-weighted v2), unchanged since they were registered.

**Provenance note (disclosed).** The snapshot ran the shim `minutes_rebuild/pit_patch.py` before it was committed, so the recorded `code_commit` (`2c9f5ca65a3`) does not contain it. The file was committed afterwards, byte-for-byte as it ran
(commit `1a5d47038c1`). The clean-tree guard and the challenger-file identity check cover `nba/`, `results/` and `pf_core/`, which the shim does not touch, and the shim leaves every fully observed computation unchanged (next section), so the forecasts are the ones the
frozen R1 code produces. Snapshots from 22:35Z on record a code commit that contains the shim.

## 3. The shim is equivalent to main's fix (`eq_ctx.py`, `tests/test_pit_patch.py`)

`features.team_context` on the same inputs in three checkouts: main (`ridge_ratings_observed`), the research branch with the shim, and the pre-fix commit. Inputs: V0 = the complete observed history 2019-2027 (19,128 team-games);
V1 = history plus the 12-game production slate (ET Oct 26 and Oct 27, two blocks); V2 = history plus a synthetic slate over three blocks including a block that holds nothing but unplayed games.

| comparison | result |
|---|---|
| shim vs main, V0 / V1 / V2 | bit-identical numeric columns (max abs difference 0), identical non-numeric columns, same shape (19,128 / 19,152 / 19,152 rows x 56) |
| shim vs pre-fix, V0 (fully observed) | bit-identical |
| main vs pre-fix, V0 | bit-identical (main's fix does not change fully observed computations either) |
| pre-fix, V1 and V2 | `ValueError: Input y contains NaN` |

Unit tests (5, passing): fully observed input is bit-identical to the unpatched function; the unpatched function fails on a slate row in an earlier block; a missing outcome never reaches a fit (blocks with observed games equal a fit on the
observed games alone); a block that holds only unplayed games is rated from the earlier observed games (equal to the specification); installation is idempotent.

**One intended difference.** Main also raises `ValueError` for a COMPLETED game with no pace or efficiency (a half-published box score); the shim does not (it excludes the row from the fit). The numerical results are identical whenever no such game
exists, and none does: 0 of 19,128 completed team-games lack pace or ortg. If the shim is still in use when such a hole appears, it would be dropped silently rather than refused; the re-freeze removes the shim.

## 4. Frozen R1 and the pre-registration

Unchanged. `nba/`, `results/`, `pf_core/` are clean and identical to the freeze for the challenger files; `PREREG_STAT_REFIT.md`, `challenger_rules.py` and the criteria are untouched; main has **not** been merged into the research branch. The planned re-freeze
(merge main, new freeze commit, re-validation) remains a separate step for the owner.

## 5. Forward collection

Unchanged and automated: snapshots at 15:35Z, 21:35Z, 22:35Z, 01:35Z and 00:05Z; the daily evaluation at 12:41Z (7 settled games / 155 played player-games so far against the single-look minimum of 30 / 500; the R1 verdict is not declared before then).
A pre-test of the 22:07Z production feed (13 games) through the research pipeline passed (JRM minutes, refit stat models, F1 minutes check PASS), so the 22:35Z snapshot is expected to run clean.
