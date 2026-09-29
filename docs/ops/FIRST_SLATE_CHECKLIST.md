# First-slate acceptance checklist — 2026-27

**Authority: RESEARCH.** This is an evidence-collection checklist, not a trading checklist. Nothing here
authorises a bet, promotes a model, or changes V1, pricing, hybrid weights or MATCHUP_AWARE_V2
(`effects_version = neutral-0`). Baseline `NBA_BASELINE_2026_PRESEASON_V1`, digest
`5a4cbda0b973d1e4d6289557b99372e4735ebe3146fa76e8f0b6ca833193be78`.

Run it once the **first real slate of 2026-27 has tipped** — the preseason opener on **2026-10-03**. Its only
job is to prove that a real slate produced complete, point-in-time evidence. It asks no question about whether
the model is any good; that needs a season of this evidence, not one night of it.

Every check below says what to run, what a pass looks like, and what a failure means. **Silence is never a
pass**: a check that returns nothing has failed.

## How to read the archive

The evidence lives on the `data-archive` branch, not on `main`.

```bash
git fetch origin data-archive
git worktree add /tmp/archive origin/data-archive      # read-only inspection copy
export A=/tmp/archive
```

## Timeline

| when (UTC) | what should happen |
|---|---|
| ~2026-10-02 11:00 | the first game enters the 36-hour matchup horizon; `matchup/context` should start writing |
| 2026-10-03, tip − 8h | the capture window opens; market cadence tightens toward tip |
| 2026-10-03, ~23:00 | first tip |
| next morning | run this checklist |

---

## 1. Market capture

```bash
nba capture-health --archive $A --days 2 --out /tmp/capture_health.json
nba delta-verify   --archive $A
jq '.worker, .markets.last_capture_utc' $A/EVIDENCE_HEALTH.json
jq '{worker_id, generation, heartbeat_at}' $A/LEASE_capture.json
```

- [ ] **Real rows.** `kalshi/markets` (or `kalshi/markets_delta`) partitions exist for the slate date.
- [ ] **Current.** `markets.last_capture_utc` falls inside the capture window of the first game, not days
      earlier.
- [ ] **One writer.** `LEASE_capture.json` names exactly one `worker_id`; its `heartbeat_at` is recent; the
      generation counter has advanced through handovers without two workers overlapping.
- [ ] **Delta chains valid.** `delta-verify` reports every chain OK, **zero broken**.

A broken chain means a past board can no longer be reconstructed. That is evidence loss, not a warning.

## 2. Horizon capture

```bash
jq '.summary.horizon_coverage, .summary.acceptance' /tmp/capture_health.json
```

Target horizons: **T-90m, T-60m, T-30m, T-10m, and the final valid pre-tip snapshot.**

- [ ] **Filling.** Each horizon reports `n_covered > 0` for games that have tipped.
- [ ] **Distance is reported.** Every covered horizon carries `age_minutes` — the real gap between the snapshot
      and the target instant. A horizon is a *target*, not a timestamp; the snapshot never lands exactly on it.
- [ ] **Missing horizons have reasons.** Every non-covered game appears in `missing_reasons`, and
      `n_covered + n_stale + n_missing == n_games` for every horizon.
- [ ] **No absent snapshot is marked covered.** A `COVERED` horizon always has a non-null `covered_by`.
- [ ] **The verdict is honest.** Before any game has tipped the acceptance verdict is `NO_DATA`. After the slate
      it must be `PASS` or `FAIL`. **`NO_DATA` after a real slate has tipped means capture is not seeing the
      games** — treat it as a failure.

## 3. Matchup context

```bash
git -C $A ls-tree -r HEAD --name-only | grep '^matchup/' | wc -l
```

- [ ] `matchup/context` moves from **zero rows** to real rows once a game is inside the 36-hour horizon.
- [ ] A game has **at least two** snapshots before tip. `stratify()` needs two per game before it can emit a
      single information event.
- [ ] `observed_at_utc` on every row is **before** that game's tip.

> **If eligible games exist and `matchup/context` is still zero rows, that is a SILENT FAILURE, not an
> offseason no-op.** Both conductor and worker run `matchup-shadow` with failures isolated, so a crashing job
> leaves the rest of the system green. Check the worker logs for `job matchup_shadow failed` first.

## 4. Injury and roster context

```bash
jq '.context' $A/EVIDENCE_HEALTH.json
jq '{refreshed_at_utc, schedule, injuries, rosters}' $A/STATUS_context.json
```

- [ ] `context/injuries` partitions exist with timestamps **before** tip — point-in-time, not back-filled.
- [ ] `context/rosters` is current: `refreshed_at_utc` is from the slate day.
- [ ] Freshness is recorded: `context.*.state == "ok"` with recent `last_day`.
- [ ] `injuries_official` may show `missing` — the NBA PDF is often unreachable from runners. The ESPN feed must
      then be present (`injuries_espn.n > 0`).

## 5. Model output

- [ ] **V1 generates normally.** `simulate` wrote output for the slate, with no fail-closed record.
- [ ] **V2 remains neutral.** Every packet carries `effects_version = neutral-0`, and no explanatory factor is
      attached to a neutral effect.
- [ ] **Timestamps line up.** For a given game and horizon, the model probability, market probability and hybrid
      probability each carry an observation time, and none is **after** tip.
- [ ] **Baseline intact.** `jq '.baseline' $A/EVIDENCE_HEALTH.json` shows `state: ok`,
      `frozen_parameters_intact: true`, and the digest above.

## 6. Archive integrity

- [ ] **Append-only intact.** No `ImmutabilityError` in any job log. The ledger refuses to overwrite an existing
      partition, so an error here means something *tried* to rewrite evidence.
- [ ] **Delta reconstruction works.** Pick one game and reconstruct its board at T-30m:
      `nba reconstruct --archive $A --at <tip minus 30 minutes, ISO-8601>`.
- [ ] **No history rewritten.** `manifest.jsonl` only grew. Compare its line count with yesterday's; it must not
      have shrunk.

## 7. Settlement

- [ ] After the slate's games are final, `settle` ran and resolved them against authoritative box scores.
- [ ] Settlement is independent: it is gated on its own decision and does not depend on capture having
      succeeded that cycle.
- [ ] Unsettled contracts are reported as unsettled, never guessed.

## 8. Authority

- [ ] `RESEARCH` everywhere: packets, ledger rows, evaluation output.
- [ ] **No bet is authorised by the NBA model.** Any output claiming otherwise is a defect.

---

## When to intervene

Intervene — investigate before the next slate — if **any** of these is true after the first slate has tipped:

1. `delta-verify` reports **any** broken chain.
2. Capture acceptance is still **`NO_DATA`** — capture is not seeing the games.
3. `matchup/context` is still **zero rows** although games were inside its 36-hour horizon.
4. Any `COVERED` horizon has a null `covered_by`, or horizon counts don't add up to `n_games`.
5. Two workers hold the lease at once, or no heartbeat for longer than one cadence interval inside a window.
6. Any model, market or hybrid timestamp is **after** tip for a pregame row.
7. The baseline digest changes, or anything reports an authority other than `RESEARCH`.

A `FAIL` on horizon *freshness*, on its own, is **not** an intervention trigger on night one. It needs a few
slates to separate a cadence problem from a slow first night.

## Do not

- Do not tune anything because of one slate. One night is evidence of plumbing, not of edge.
- Do not fill a missing horizon, starter, or context row by inference. Record the gap and its reason.

## Known limitations — preserved, not fixed

- **Defender attribution: unavailable.** No trustworthy reachable defender-assignment source exists.
  `DEFENDER_ATTRIBUTION_AVAILABLE = False`, named-defender effects stay unavailable, and V2 stays neutral.
- **Confirmed starters: unavailable.** No trustworthy pregame confirmed-starter source is ingested. Do not infer
  confirmed starters from projected lineups, and never use post-game starter flags — that is leakage.
  `LINEUP_CONFIRMED` and `STARTER_CHANGE` cannot fire until a real source exists. `LATE_SCRATCH` and
  `ROTATION_ADDITION` still work off the captured roster.
- **Market history is the bottleneck.** Every market-relative conclusion so far rests on one season of Kalshi
  prop history (2025-11-19 → 2026-06-14), giving 2–3 walk-forward folds per family. More shot-event history will
  not fix that and backtesting tricks will not either. Only prospective seasons of this evidence will.
