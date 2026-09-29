# First walk-forward shot-profile study

**Verdict: no family shows value beyond the market. Nothing was activated.**
`effects_version = neutral-0`, authority `RESEARCH`, `NBA_BASELINE_2026_PRESEASON_V1` untouched.

The one positive signal — shot-profile context improving on **V1** for `player_points` — disappears
entirely against the market price. That is the pattern this repository has measured repeatedly, and
it means the same thing each time: the information was already in the price.

---

## 1. What made the study possible

The previous wave stopped at `INSUFFICIENT_DATA`: 98 distinct game dates against a 200-game fold
floor and **0 players with 200+ located attempts**. The backfill changed that.

| | before | after |
|---|---|---|
| seasons | 1 (partial) | **3 complete** |
| games | 150 | **4,160** |
| shot events | 33,943 | **927,349** |
| located attempts | 26,767 | **740,390** |
| distinct game times | 98 | **2,715** |
| players ≥ 200 located attempts | **0** | **523** |
| players ≥ 400 | 0 | **429** |

## 2. The binding constraint was not shot data

Kalshi player-prop history covers **2025-11-19 → 2026-06-14 only**. It does not reach 2023-24 or
2024-25. So the *evaluable* window is 1,115 games, and the backfill's real contribution is what sits
**behind** them: 3,045 prior games and 541,484 prior located attempts, giving the window's players a
median of **599 prior attempts** each.

That is the right shape for this question. A matchup feature needs history to describe a player
*before* the game being predicted, and that is exactly what two extra seasons buy.

| | |
|---|---|
| player-prop market rows | 8,120 |
| joined to a shot profile | **8,112 (99.9%)** |
| unjoined | 8 rows, 1 game — a player priced but with no located attempt that night |

The other 7,971 market rows are game-level (spread, total, winner, team total) and carry no player,
so they cannot have a player shot profile. The headline "50% join rate" is that split, not a defect.

## 3. Method

Identical in shape to `research/market_vs_model.py`, so the two are comparable — a nested pair of
logistic models fitted **walk-forward by date** and scored only on strictly later folds:

```
base     :  logit(y) ~ a + b·logit(p_base)
+profile :  logit(y) ~ a + b·logit(p_base) + c₁·d_rim + c₂·d_three_rate
```

for `p_base` ∈ {V1, market, hybrid}. The question is never "does the profile predict anything" but
whether it predicts anything **the baseline has not already priced**.

**The feature set is pre-specified and tiny: two features.**

- `d_rim` = player rim rate − opponent rim rate allowed
- `d_three_rate` = player three-point rate − opponent three-point rate allowed

Both are matchup *differences*, not player levels — a player's own rates are partly things V1
already models, so including them would quietly turn this into a test of whether V1 knows its own
inputs. **No search over feature sets was performed.** Searching until something scored is exactly
the failure the brief forbids.

The hybrid leg had to be reconstructed: `p_hybrid` is **null for all 16,091 rows** of the cached
scored table, because the fold loop that produced it never persisted per-row blends. It is refitted
here walk-forward as `logit(y) ~ market + V1` on each training slice.

## 4. Results

Negative Δ log loss favours the profile. Folds are date-separated.

| family | n | vs **V1** | vs **market** | vs **hybrid** |
|---|---|---|---|---|
| `player_points` | 2,585 | **−0.00433** (2/3 folds) | **+0.00001** (1/3) | −0.00014 (1/3) |
| `player_assists` | 1,707 | −0.00083 (1/2) | −0.00079 (1/2) | −0.00045 (1/2) |
| `player_rebounds` | 2,327 | +0.00211 (1/3) | +0.00157 (1/3) | +0.00108 (1/3) |
| `player_threes` | 1,493 | +0.00057 (1/2) | +0.00124 (0/2) | +0.00129 (0/2) |

**`player_points` is the whole story.** Against V1 the profile is worth −0.0043 log loss and wins
2 of 3 folds. Against the market the same features are worth **+0.00001** — not a small gain, but
no gain at all. The market already knows it.

`player_assists` is nominally negative everywhere, but at 1–2 folds better out of 2 and magnitudes
near 10⁻³ it is indistinguishable from noise. `player_rebounds` and `player_threes` are worse with
the profile than without, and `player_threes` fails in **every** fold against the market.

### Depth split

Restricting to players with more prior evidence does not rescue anything:

| min prior attempts | `player_points` vs market | `player_threes` vs market |
|---|---|---|
| 0 | +0.00001 | +0.00124 |
| 200 | +0.00001 | +0.00124 |
| 500 | +0.00024 | +0.00181 |

A real effect should strengthen where the profile rests on more evidence. This does the opposite or
nothing — the signature of noise rather than a weak-but-real signal.

## 5. Leakage audit

Four structural checks, verified by **independent recomputation** rather than by assertion:

| check | result |
|---|---|
| prior attempts match a strictly-before recomputation | PASS (max diff 2.7 × 10⁻¹²) |
| first game of the dataset has zero prior evidence | PASS |
| opponent-allowed profile excludes the predicted game | PASS (max diff 1.8 × 10⁻¹¹) |
| every feature row's timestamp equals its game's tip | PASS |

Leakage is structural here, not filtered: `build_pit_features` walks games in tip order and reads a
game's features **before** folding that game's shots into the accumulator, so same-game evidence
cannot be present.

### The control that matters

A null result is worthless if the pipeline simply ignores the features. So the study was re-run with
features deliberately shifted one game **forward**, injecting future information:

| family | honest | deliberately leaked |
|---|---|---|
| `player_assists` vs market | −0.00079 | −0.00184 |
| `player_points` vs V1 | −0.00433 | −0.00220 |

The numbers move, so the pipeline is demonstrably sensitive to feature content — the null is not an
artifact of inert plumbing. And the sharper point: **even with future information injected, no
family meaningfully beats the market.** These two features carry very little about prop outcomes
either way.

## 6. Interpretation

Per the brief's framing — not "did V2 beat V1 somewhere" but "did shot-profile context add stable
out-of-sample information beyond V1, the market, and the hybrid":

| family | conclusion |
|---|---|
| `player_points` | **value vs V1, none vs market.** The market prices it already. |
| `player_assists` | **insufficient evidence** — right sign, noise-scale magnitude, 2 folds. |
| `player_rebounds` | **no incremental value**; worse than every baseline. |
| `player_threes` | **no incremental value**; loses in every fold against the market. |

Nothing here justifies promotion, and nothing here was promoted.

## 7. Known limitations

- ~~**Preseason games are included.**~~ **Fixed.** `season_type` is now persisted (schema
  `shotevent/2`) and preseason is excluded from the research population by default. See
  `SEASON_TYPE.md` for the migration, and section 9 below for the controlled re-run. The estimate
  above was close: the real figure was 45,414 preseason shot events across the three seasons, 4.9%
  of the corpus.
- **One market season.** Every conclusion rests on 2025-11-19 → 2026-06-14. A second season of
  market history would roughly double the fold count, which is what the thin 2–3 folds per family
  most need.
- **Two features only.** A pre-specified pair was chosen over a search on purpose. A negative result
  for these two is not a negative result for shot-profile context in general — it is a negative
  result for the most obvious version of it, which is the right place to start.
- **Rim/paint boundary remains approximate** (`ESPN_SHOT_COORDINATES.md`), so `d_rim` carries that
  uncertainty.

## 8. Recommendation

Do **not** activate anything. Specifically:

1. ~~**Persist `season_type`**~~ — **done**, and the study re-run below. It removed the largest known
   contaminant and did not change any conclusion.
2. **Accumulate a second season of prop market history** prospectively. The constraint on this study
   was never shot data after the backfill — it was market coverage.
3. If a future study shows value beyond the market, the next step is **prospective shadow
   validation**, not activation: run the feature live, record what it would have said, and score it
   forward. Nothing should touch production probabilities, hybrid weights or authority before that.


---

## 9. Controlled re-run on the clean population

Run after the `season_type` migration (`SEASON_TYPE.md`). **Exactly one thing changed: the population.**
Feature definitions, zone geometry, half-life, prior strength, sample floors, fold construction, prediction
logic, thresholds and model parameters are all untouched, and the feature-build path was first shown to
reproduce the original feature table **value-for-value** (85,846 rows, every column identical) when run over
the unfiltered corpus, so the two runs differ in the population and nothing else.

Artifacts: `shot_profile_walkforward_clean.json`, `shot_profile_population_comparison.json`.

### The evaluated set did not change at all

| | before | after |
|---|---:|---:|
| shot events in corpus | 927,349 | 881,935 |
| feature rows | 85,846 | 80,404 |
| **rows the study scores** | **8,112** | **8,112** |

The Kalshi prop panel spans 2025-11-19 → 2026-06-14, which is entirely regular season and postseason. **No
preseason game was ever an evaluated row.** The contamination lived in the point-in-time accumulators that
feed the features, not in the rows being scored.

### What it did do

Every one of the 8,112 evaluated rows carries a different feature value now — none was unchanged:

| feature | mean abs change | max abs change | rows unchanged |
|---|---:|---:|---:|
| `d_rim` | 0.00183 | 0.01127 | 0 / 8,112 |
| `d_three_rate` | 0.00219 | 0.01173 | 0 / 8,112 |

Real and measurable, and far too small to move a result at this sample size.

### Out-of-sample log-loss delta (negative = profile helps)

| family | base | folds | before | after |
|---|---|---:|---:|---:|
| `player_assists` | vs V1 | 2 | −8.32e-04 | −1.05e-03 |
| `player_assists` | vs market | 2 | −7.90e-04 | −8.90e-04 |
| `player_assists` | vs hybrid | 2 | −4.54e-04 | −5.89e-04 |
| `player_points` | vs V1 | 3 | −4.33e-03 | −4.44e-03 |
| `player_points` | vs market | 3 | +5.45e-06 | −6.65e-05 |
| `player_points` | vs hybrid | 3 | −1.45e-04 | −2.19e-04 |
| `player_rebounds` | vs V1 | 3 | +2.11e-03 | +2.03e-03 |
| `player_rebounds` | vs market | 3 | +1.57e-03 | +1.54e-03 |
| `player_rebounds` | vs hybrid | 3 | +1.08e-03 | +1.03e-03 |
| `player_threes` | vs V1 | 2 | +5.74e-04 | +6.55e-04 |
| `player_threes` | vs market | 2 | +1.24e-03 | +1.28e-03 |
| `player_threes` | vs hybrid | 2 | +1.29e-03 | +1.34e-03 |

### Verdict: `NO_CHANGE_IN_CONCLUSION`

Judged by the study's **own pre-specified criterion** — the +profile model must beat the base model in *every*
out-of-sample fold — nothing moved. No family passed before; none passes after; against any of the three
baselines. No threshold was added, moved or relaxed to reach that statement.

One raw sign flip exists and is recorded: `player_points` vs market went from +5.45e-06 to −6.65e-05. That is
a change of 7e-05 nats across 1,919 out-of-sample rows, better in 1 of 3 folds. It is not distinguishable from
zero in either direction, and treating it as a result would be reading a conclusion out of the fifth decimal
place.

**The fix was still necessary.** The contamination was *invisible*, not harmless. On this panel it happened to
be small because the market history does not span preseason; on a panel that did, it would not have been, and
nothing in the schema would have revealed it.

## 10. Event-window stratification: `INSUFFICIENT_DATA`

The brief asks for residual value stratified by the lineup-event windows built in PR #16
(`matchup/events.py`: `LINEUP_CONFIRMED`, `STARTER_CHANGE`, `LATE_SCRATCH`, `ROTATION_ADDITION`,
`ASSIGNMENT_SHIFT`, plus `no_event`). Those windows are used **unchanged** — nothing was rebuilt, no window
was redefined, and no threshold was relaxed.

The stratification cannot run, and this is measured rather than assumed. The archive branch
(`origin/data-archive`) holds 140 manifest entries across these kinds:

| kind | rows |
|---|---:|
| `kalshi/markets` | 39,807 |
| `context/rosters` | 21,335 |
| `kalshi/orderbooks` | 3,300 |
| `context/injuries` | 2,834 |
| `context/schedule` | 64 |
| **`matchup/context`** | **0** |

`stratify()` needs at least two `matchup/context` snapshots per game to diff into events. There are zero
snapshots of any kind. Every stratum, including `no_event`, is therefore empty.

**`INSUFFICIENT_DATA`.** Not "no effect", not "no evidence of an effect" — no observations. `matchup-shadow`
is wired into `conductor.yml` and gated on the same condition as `context`, so the first snapshots will be
written when 2026-27 games enter the 36-hour horizon. Until a game's context has been captured at least twice,
there is nothing to diff and nothing to stratify.
