# Shot-profile research arm

**Status: RESEARCH. No effect learned, none activated.** `EFFECTS_VERSION = neutral-0`,
`MATCHUP_AUTHORITY = RESEARCH`, `NBA_BASELINE_2026_PRESEASON_V1` untouched (digest
`5a4cbda0b973…`, verified live). V1 and neutral V2 still simulate bit-identically.

This is the first MATCHUP_AWARE_V2 data arm backed by a source the project can actually reach. It
describes **shooters**, not defenders.

---

## 1. The distinction this arm exists to preserve

> **Shot-profile data available ≠ defender matchup data available.**

ESPN supplies where an attempt was taken and whether it went in. It supplies nothing about who was
guarding. Every endpoint that carries defender attribution times out from this project's egress at a
180-second budget with a passing control (`MATCHUP_SOURCE_AUDIT.md`), and no amount of processing
converts a shot location into a defender.

Three things enforce that rather than asserting it:

- `shotprofile.events.DEFENDER_ATTRIBUTION_AVAILABLE = False` — a constant a test asserts against.
- `ShotEvent` has **no defender field at all**, tested, so nothing can populate one from locations.
- The opponent-side feature is named `opponent_allowed_profile` everywhere and the packet says
  `"team/scheme proxy from attempts allowed -- NOT defender attribution"` in the payload itself.

An opponent's allowed profile mixes its scheme with its schedule and with its opponents' own
tendencies. It is **raw, not opponent-adjusted**. Calling it a defensive matchup effect would be
three unearned inferences stacked on one real measurement.

## 2. Geometry (measured — see `ESPN_SHOT_COORDINATES.md`)

| finding | value |
|---|---|
| coordinates | **half-court normalised** — mean `x` ≈ 24.7 for both teams in both halves |
| origin | **(25, 0)** — `y` from the **basket**, not the baseline |
| arc test | 3PT 638/638 beyond, 2PT 1431/1431 inside; clean separation (21.5 ft vs 22.0 ft) |
| free throws | **1,094 events, 0 coordinates** |
| non-shot events with coordinates | rebounds alone outnumber attempts |

The origin contradicted the obvious guess: measuring `y` from the baseline, where an NBA hoop
actually sits 5.25 ft in, scored **53.6%**. The three-point line was used as a ruler to *test*
candidate origins rather than assumed alongside one.

**Limitation carried forward:** the arc test is perfect for any `y` in `[-1, +2]`, so the origin is
located to a three-foot band. Ample for the 2PT/3PT split; **not** ample for a 4-foot rim radius. So
`rim` vs `paint_non_rim` is the softest boundary in the module and a study leaning on it should say
so. The three-point boundaries are measured; the rim boundary is reasoned.

## 3. What is built

| piece | what it does |
|---|---|
| `shotprofile/events.py` | normalized `ShotEvent`; raw coordinates + validity flag, no zone, no defender |
| `shotprofile/court.py` | measured geometry and deterministic zone classification |
| `shotprofile/ingest.py` | historical pull via `nba shot-events`, resumable, reusing the ESPN history cache |
| `shotprofile/features.py` | point-in-time player and opponent-allowed profiles, shrunk to a league prior |
| `shotprofile/packet.py` | renderable block that states facts and refuses to state a projection |
| `research/shot_profile_study.py` | walk-forward comparison against V1, market and hybrid |

Two rules hold throughout the feature layer. **The cutoff lives in the estimator, not the caller** —
a leakage rule that lives in the caller is one that a caller eventually forgets. And **small samples
shrink toward a league prior computed from the same stream**, with effective sample size travelling
alongside so a consumer can see how much of an estimate is data.

There is deliberately **no function converting a profile difference into a points, FGA or FG%
adjustment**. That absence is tested (`test_no_module_here_converts_a_profile_into_a_model_effect`).

## 4. Tests

47 tests, and the ones that matter were mutation-checked rather than assumed to work:

| mutation | caught by |
|---|---|
| hoop origin reverted to the intuitive `y = 5.25` | zone classification and downstream features |
| point-in-time cutoff made inclusive (`<=`) | `test_a_profile_cannot_see_its_own_game` |
| free throws allowed a field-goal coordinate | schema validator, at parse time |

One test failure was my own setup rather than the code: 2,000 attempts more than two half-lives
before the cutoff stayed near the prior, which is the recency weighting working correctly. Volume
alone does not overcome a prior; *recent* volume does. The test now says so.

## 4b. Validated against 150 real games

`nba shot-events --seasons 2024-25 --max-games 150` (run 36467977361): **33,943 events, 26,767
located field-goal attempts, 0 errors.**

**What the data confirms.** 178.4 FGA per game against a real NBA rate near 176. A 3PA share of
**43.0% against a league rate near 42%**. And FG% by zone lands where basketball says it should:

| zone | measured FG% |
|---|---|
| rim | 66.2% |
| paint (non-rim) | 42.5% |
| midrange | 39.3% |
| corner three | 36.6% |
| above the break | 33.9% |

Monotone from the rim outwards, with the corner three above the break-three, which is the ordering
every public shot chart shows. The 2PT/3PT boundary — the one the arc test actually measured — is
sound.

**What the data corrected.** The first zone definitions were checked against public league rates and
two were visibly wrong. Both fixes are geometric, not curve-fitting:

| zone | first | corrected | league |
|---|---|---|---|
| rim | 27.9% | 27.9% | ~32% |
| paint (non-rim) | 21.6% | **19.5%** | ~12% |
| midrange | 7.4% | **9.5%** | ~13% |
| corner three | 12.8% | **10.5%** | ~8% |
| above the break | 30.2% | **32.6%** | ~34% |
| **total absolute deviation** | **0.278** | **0.190** | |

- **The corner needs a ceiling, not just a width.** Testing only `|x−25| ≥ 22` counted wing threes
  taken near the sideline. The arc meets the sideline at `sqrt(23.75² − 22²) = 8.94 ft` from the
  basket; above that the line curves and the shot is above-the-break at the same x.
- **The paint is a rectangle, not a radius.** A 14-ft radius sweeps in baseline and elbow jumpers
  that sit outside the lane but close to the basket — which is why non-rim paint was inflated while
  midrange starved. The lane is 16 ft wide and 19 ft deep from the baseline, so 8 ft either side of
  centre and 13.75 ft from the basket.

**Where it is still off, and why I stopped.** Rim remains ~4 points low and non-rim paint ~7 high.
That is the residual the documented origin band predicts: a 4-foot rim radius is the boundary most
sensitive to a ±1.5 ft uncertainty in `y`.

I did not tune further. The league rates above are quoted from memory, not measured, and different
sources define "rim" and "paint" differently — NBA.com's restricted area is not the same cut as
"within 4 feet". Adjusting constants until they match an unverified target would be fitting, and it
would destroy the property that makes the 2PT/3PT split trustworthy: that it was checked against a
physical constant rather than against an aggregate.

**So: the three-point boundaries are measured; the rim/paint split is approximate and documented as
such.** A study that leans on rim-vs-paint should say so.

## 5. Stop condition (mission Phase 14)

> Do not continue into a learned matchup model unless there is already enough historical shot-event
> coverage to perform a proper walk-forward study.

**There is not, yet — and this is the absence of a test, not a negative result.** Measured on the
150 games ingested so far: **98 distinct game dates against a 200-game fold floor**, and **0 players
with 200+ located attempts** (80 clear 100, 219 clear 50; median 36, max 196). The distinction is
enforced in code: `run_study` returns `verdict: INSUFFICIENT_DATA` with the reason *"This is not
evidence against shot-profile features; it is the absence of a test"* rather than a null finding
that a later reader could mistake for one.

### Sample requirements, stated so the bar is checkable

| requirement | value | why |
|---|---|---|
| distinct game dates for folds | **≥ 200** training games before the first fold | fold boundaries snap to game boundaries; one game's props share an opponent and a context |
| paired rows per comparison | **≥ 1,000** (`MIN_PAIRED_ROWS`) | below this a prop-level log-loss difference is indistinguishable from noise |
| player profile depth | **≥ 200 effective attempts** for the deepest bucket | `by_evidence_depth` splits results so an edge that fails to strengthen with evidence is visible |
| seasons | ~1,230 games each | `nba shot-events --seasons 2023-24,2024-25,2025-26` |

A full season yields roughly 220,000 play events, of which ~2,000 per game are coordinate-bearing
and about a quarter are field-goal attempts. One season clears the fold floor; the per-player depth
requirement is what actually binds, since a bench player accumulates attempts slowly.

### Why the data is not here yet

`site.api.espn.com` is denied by this development container's egress policy (403 on CONNECT), so
ingestion has to run in Actions. The path is built, tested and wired (`shot-events-pull` workflow,
resumable, refusing to push to the default branch); it needs to be on `main` before it can be
dispatched at all, which is experiment **E0** from the capture-worker wave — a branch-only workflow
returns 404.

**So the honest state is: pipeline ready, dataset not yet collected, study not yet run.** Running it
is a dispatch, not a rewrite.

## 6. What remains unlearned

Everything. No shot-profile feature has been shown to improve any forecast, and none has been given
the opportunity to try. The UI may state *"takes 38% of attempts at the rim; opponent allows 31%"*.
It may not state *"+2.8 projected points"*, and `effect_status: NEUTRAL/UNLEARNED` plus
`projected_effect: None` are what a renderer checks to keep that true.

A feature earns influence only after leakage-free, out-of-sample evidence shows it improves
predictions beyond **both V1 and the market** — the bar this repository has already watched several
promising-looking signals fail.
