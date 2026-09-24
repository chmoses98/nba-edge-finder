# The prospective evidence base: cadence cost, context archive, and what comes next

Companion to `CAPTURE_ARCHITECTURE.md`, which covers how the capture worker runs. This covers what
it should capture, what that costs, and what is deliberately **not** being built yet.

---

## 1. Cadence cost, measured (Phase 11)

The brief is explicit: *"Do not implement 5-minute cadence merely because it sounds better. Measure
API cost, runtime and archive growth."* So:

**Per-tick storage, measured on the archive:** markets snapshot **276 KB** compressed
(2,818 markets, off-season board), order books up to **17 KB**. Call it **293 KB per tick**.

**Runtime, measured over 39 `conductor/run` jobs:** `nba capture` p90 **181s**, max **186s**.

Projected archive growth over a 180-day season, assuming a ~16h active day:

| cadence | ticks/day | MB/day | GB/season |
|---|---|---|---|
| flat 5 min | 192 | 55.0 | **9.66** |
| flat 10 min | 96 | 27.5 | 4.83 |
| flat 15 min | 64 | 18.3 | 3.22 |
| **tiered (implemented: 15 → 10 → 7 → 5)** | 98 | 27.9 | **4.91** |

GitHub recommends repositories stay under ~1 GB. **Every figure above is a floor**, because the
off-season board carries far fewer markets than a night with a full slate of game and prop markets.
Left alone, the archive breaks the repository partway through the season.

### The measurement that changes the answer

Between two consecutive snapshots four minutes apart:

| quantity | value |
|---|---|
| markets in each snapshot | 2,818 |
| markets whose quote changed | **9** |
| share of the board that changed | **0.32%** |

Almost the entire per-tick cost is **re-writing prices that did not move** — championship futures,
expansion markets, season win totals. A delta snapshot (changed rows only, against a periodic full
board) would carry ~0.3–1% of the bytes.

**Conclusion.** Cadence is *not* storage-bound or API-bound once deltas exist; it is bound by the
186s capture runtime, which comfortably fits a 5-minute tick. The tiered cadence is implemented as
specified, and **delta encoding is the top-priority next task** — it is what makes the season's
archive affordable at all, and it is infrastructure, not a model change, so the freeze permits it.

The in-season change rate will be higher than 0.32% and must be re-measured during preseason before
the delta format is fixed. Do not design the format against an off-season number.

## 2. Live context archive (Phase 10)

The goal is to be able to answer, months later: *"Exactly what did we know at T-90 before Celtics
vs Knicks?"* That requires the state as it was, never reconciled against later truth.

Per meaningful pregame snapshot, preserve point-in-time:

| element | status today |
|---|---|
| Kalshi market board (all NBA families) | **captured** — `kalshi/markets/` |
| executable quotes / order-book depth | **captured** — `kalshi/orderbooks/`, capped at 300 books |
| ESPN injuries | **captured** — `context/injuries/` |
| rosters | **captured** — `context/rosters/` |
| schedule / rest context | **captured** — `context/schedule/` |
| official NBA injury report (PDF) | **not captured** — probed, not ingested |
| likely vs **confirmed** starters | **not distinguished** — the single most valuable gap |
| model version + model output at that instant | partially — simulation output is archived, but not stamped with the frozen baseline id |
| authority state | **captured** — evaluation ledger |

**The governing rule, which the capture layer already honours: never overwrite earlier context with
later truth.** Every snapshot is append-only and content-addressed; a correction is a new row, never
an edit. The two gaps worth closing before the regular season are *confirmed starters* (a distinct
event from projected starters, and the thing late markets actually react to) and *stamping each
simulation output with `NBA_BASELINE_2026_PRESEASON_V1`* so a prediction can always be attributed to
the exact parameter set that produced it.

## 3. What is deliberately NOT being built (Phase 13)

This wave is data infrastructure. The model freeze and the research-freeze list live in
`MODEL_FREEZE.md`. Restated here only so the boundary is unambiguous:

- No tuning of `rating_scale`, or of any frozen parameter.
- No new predictive features.
- No new HYBRID weights, no promotion of any authority.
- No impact model v2 — Phase 9 is explicit that this wave produces **coverage counts**, not models.
- **The current result stands: the market beats the model in all eight families.** That is the
  finding, and it is preserved rather than engineered around.

## 4. Future research queue — recorded, not executed (Phase 14)

Ordered by what the new data would actually unlock, not by appeal:

1. Lineup/stint player impact from real possessions (replacing the rejected box-score APM).
2. Injury/absence redistribution measured over actual lineup possessions.
3. Residual prop efficiency bias, re-tested once prospective data exists.
4. Late-news market response: how fast Kalshi repricess a confirmed scratch.
5. Starter-confirmation effects specifically.
6. Role-change and trade priors.
7. Pace and usage redistribution after lineup changes.
8. Whether `DATA_ONLY` disagreement becomes informative in the minutes immediately after news.

None of these may begin until one of the Phase 13 release conditions is met: a materially better
data source, sufficient validated lineup/stint data, or meaningful 2026-27 prospective evidence.

## 5. Next tasks, in priority order

1. **Delta-encode the market archive.** Measured 0.32% change rate; without this the season's
   archive exceeds GitHub's practical repository size. Re-measure in-season first.
2. **Merge `capture_worker.yml` to `main`** — until then the chain cannot renew itself at all (E0).
3. **Run the preseason acceptance test** from 2026-10-03; `nba capture-health --gate` reports the
   verdict without prose.
4. **Distinguish confirmed from projected starters** in the context snapshot.
5. **Stamp simulation output with the frozen baseline id.**
