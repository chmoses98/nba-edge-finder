# Delta-encoded market archive: design and measured results

Reproduce with `python scripts/delta_benchmark.py --archive <checkout of data-archive>`; the raw
output is `docs/research/delta_benchmark.json`. Every size and change-rate figure below comes from
boards actually captured from Kalshi and stored on the `data-archive` branch — 11 of them, including
five taken ~5.5 minutes apart at production cadence specifically for this measurement.

---

## The seven requested metrics

### 1. Current bytes per full snapshot

| | |
|---|---|
| mean | **272,976 B** (11 real boards) |
| range | 236,589 – 287,072 B |
| markets per board | 2,818 → 3,494 (growing as the season approaches) |
| per market | **82.7 B** compressed |

### 2. Average changed-market percentage

| step | gap | changed | % of board |
|---|---|---|---|
| 09-27 21:23 → 21:29 | 5.9 m | 35 | **1.00%** |
| 09-27 21:29 → 21:35 | 5.5 m | 54 | **1.55%** |
| 09-27 21:35 → 21:41 | 5.6 m | 84 | **2.40%** |
| 09-27 21:41 → 21:46 | 5.5 m | 44 | **1.26%** |
| 09-18 07:36 → 07:40 | 4.1 m | 479 | 17.00% |
| 09-18 07:40 → 07:48 | 7.9 m | 2,818 | 100.00% ← **not market activity** |

**Steady state: 1.55% median, 4.64% mean** across the five genuine ticks.

Two notes that matter more than the average:

* The **100% step is a capture-code change**, not churn: `_quote_cents` appeared on every market
  between those two runs. The benchmark flags any step changing >95% of markets as suspected schema
  evolution and excludes it from the steady-state figures, because averaging it in would inflate
  every downstream number.
* An earlier wave reported **0.32%** changed over four minutes. That measurement was correct but
  narrower — it counted only 8 quote fields. Delta size is governed by *all* fields, and on that same
  pair the all-field rate is 17%, driven by Kalshi's own churning `previous_yes_bid/ask_dollars`.
  The figure that governs storage is the all-field one.

### 3. Delta bytes per tick

| | |
|---|---|
| median | **1,548 B** |
| mean | **2,040 B** |
| as a share of the snapshot it replaces | **0.77%** (≈130× smaller) |
| real 5-tick chain on 09-27 | checkpoint 286,993 B + 4 deltas totalling **6,278 B** |

### 4. Projected seasonal storage

98 ticks/day (the tiered cadence integrated over a ~16 h active day) × 180 days, markets board only:

| | |
|---|---|
| before — full board every tick | **4.485 GB** |
| after — checkpoint every 24 ticks + deltas | **0.219 GB** |
| reduction | **95.1%** (20.5× smaller) |

Comfortably under GitHub's ~1 GB guidance, with room for the order-book stream (delta-encoded by the
same machinery) and for the board continuing to grow.

### 5. Reconstruction speed

| chain | markets touched per delta | median |
|---|---|---|
| real 5-tick chain, genuine capture instants | — | **285 ms** |
| 24 deltas, typical tick | 35 | **475 ms** |
| 24 deltas, worst observed churn | 2,966 | 2,212 ms |

Cost is driven by how many markets each delta *touches*, since every touched market is re-digested.
Profiling an earlier version showed digest calls were 1.2 s of a 1.6 s reconstruction, which is why
the board hash is composed from per-market digests rather than from one serialisation of the whole
board: verification is now incremental.

### 6. Integrity / hash results

On the real 09-27 chain (1 checkpoint + 4 deltas), every tick was reconstructed and compared with
the full snapshot actually captured at that instant:

| check | result |
|---|---|
| canonical board hash | **5/5 match** |
| **field-for-field**, including `_observed_at_utc` and `_run_id` | **5/5 match** |

Field-for-field equality — not merely "equivalent" — is the contract, and it is why the delta header
carries the capture instant and run id: reconstruction restamps the *original* capturing run's id,
so a reconstructed board is usable anywhere a snapshot was.

*A trap worth recording.* The first benchmark run reported 3/3 hash but 1/3 field-for-field. That was
the benchmark's own fault: it replayed real boards through a fresh ledger with `run_id="bench"`, so
reconstruction faithfully restamped "bench". Matching hashes with mismatching fields is the signature
of exactly that class of error.

### 7. Failure and recovery behaviour

| case | behaviour |
|---|---|
| healthy chain | `delta-verify`: 1 chain OK, 0 broken |
| **corrupted delta** (field injected) | reconstruction **fails closed** — `DeltaChainError` |
| **deleted delta** | **fails closed** — "recorded in the manifest but missing from disk" |
| `delta-verify` after damage | reports `n_broken=1` **without raising**, so one bad chain does not abort the daily report |
| next capture after damage | writes a **full checkpoint**, reason "existing chain is unusable" |
| after that checkpoint | reconstruction works again (`source=snapshot`, 3,494 markets) |

Also fails closed, each with a test: a sequence gap, a chain not starting at 1, a delta applied to
the wrong checkpoint, a tampered `board_sha256`, a wrong market count, an unknown schema, capture
instants that do not strictly increase, and two *different* deltas claiming one `seq` (a forked
chain). An *identical* duplicate — a retried push — is collapsed rather than rejected, because that
is a real and harmless case.

---

## Design, and why each rule exists

**Existing full snapshots are the checkpoints.** Deltas are a new ledger kind; nothing already on the
archive is rewritten, re-encoded or deleted, and reconstruction resolves its base from the ordinary
`kalshi/markets` kind. So every board ever captured is already a valid base, a reader that knows only
about full snapshots keeps working, and there is no migration step to get wrong.

**Four change categories, not three.** `added` and `removed` carry ticker lifecycle (a newly
discovered market, a delisted one); `changed` carries new and updated field values; **`cleared`**
carries fields that vanished from a row. Without `cleared`, a field dropping out of a market's
payload would be invisible and reconstruction would keep a stale value forever.

**History never depends on current truth.** Reconstruction filters the manifest on `observed_at`
before reading anything, so nothing captured after the requested instant can influence the answer,
and a request before the first checkpoint is refused rather than served from a later checkpoint.

**Ledger stamps are excluded from the diff.** `_observed_at_utc` and `_run_id` change every tick, so
diffing them would mark all ~2,800 markets as changed and defeat the exercise. They are
snapshot-level facts, so they live in the delta header and are restamped on the way out.

**A capture that cannot verify its chain writes a checkpoint.** Stacking a delta on an unprovable
chain would make every later tick unreadable too. Degrading costs ~287 KB once and bounds the damage
to one chain.

### The part that could have quietly corrupted results

Three readers went straight to the `kalshi/markets` kind. Once most ticks are deltas,
`iter_rows("kalshi/markets")` yields only checkpoints — 1 tick in 24 — and `latest(...)` returns the
newest *checkpoint*, not the newest board:

* **evaluate** builds the market benchmark from those observations. The benchmark is *"the raw
  executable price at the final valid pre-tip snapshot"*, so losing 23 of 24 ticks moves that instant
  earlier and the **frozen benchmark methodology would change without anyone editing it.**
* **settle** scans for settlement `result` fields; one appearing first in a delta tick would be lost.
* **simulate** gates pricing on market age, and would have measured the age of a checkpoint up to
  four hours old — either refusing to price a slate or pricing it on stale quotes.

So `iter_market_rows` yields every tick's rows (byte-identical to `iter_rows` on an archive with no
deltas) and `latest_board` returns the newest tick whatever encoding it arrived in. Both walk each
chain once, applying deltas incrementally, and both verify the whole chain before yielding any of it
— a reader must never act on the good half of a chain whose tail is corrupt.

## Tools

| command | purpose |
|---|---|
| `nba reconstruct --at <iso>` | the board as of the latest tick at or before that instant |
| `nba reconstruct --at <iso> --compare <snapshot>` | verify field-for-field and hash-for-hash |
| `nba delta-verify` | walk every chain; exit 1 if any is broken |
| `nba capture --full-snapshots` | disable delta encoding entirely (previous behaviour, exactly) |
| `nba capture --checkpoint-every N` | tune the storage/reconstruction trade-off |

## What is deliberately unchanged

No model parameter, simulation rule, pricing rule or authority was touched. All families remain
RESEARCH. This is storage encoding and nothing else: the frozen baseline
`NBA_BASELINE_2026_PRESEASON_V1` is unaffected, and the market benchmark sees exactly the
observations it saw before.
