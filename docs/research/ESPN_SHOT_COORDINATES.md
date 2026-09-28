# What ESPN play-by-play coordinates actually mean

**Verdict up front: the coordinates are half-court normalised, `y` is measured from the basket
rather than the baseline, free throws never carry a location, and roughly half of all
coordinate-bearing events are not shots at all.** Each of those was measured. One of them
contradicted the physically obvious guess.

Reproduce with `scripts/probe_shot_coordinates.py`, dispatched by the `shot-coordinate-probe`
workflow. Runs referenced here: **36462753403** (2024-25, 12 games), **36463091875** (2024-25, 20
games), **36443664372**→**36463400012** (2023-24, 25 games).

It has to run on a GitHub runner: `site.api.espn.com` is denied by the development container's
egress policy (403 on CONNECT, confirmed against the proxy status endpoint) and answers in ~0.2 s
from Actions. That is the mirror image of the `stats.nba.com` split in `MATCHUP_SOURCE_AUDIT.md`.

---

## 1. The grid

| property | measured |
|---|---|
| `x` range | **0 – 50**, median exactly 25 |
| `y` range | **−5 – 71** (season-dependent tail), median 7, p95 27 |
| sentinel | exactly one pair, **`x=-214748340, y=-214748365`** |
| coordinate-bearing events | 6,907 of 9,484 (72.8%) in the 20-game run |

`x` spans the court's 50-foot width with the centre line at 25. The single sentinel pair is the
int32-derived "not recorded" marker; nothing else appears, so a magnitude test cleanly separates
locations from absences.

## 2. Half-court normalised: no side, no half-flip

This is the property that would otherwise require a correction, and it turns out not to exist.

| | mean `x` |
|---|---|
| home, first half | 24.74 |
| away, first half | 24.85 |
| home, second half | 24.64 |
| away, second half | 24.64 |

Both teams sit on the same centre in both halves, with median exactly 25 throughout. **Both teams'
attempts are mapped onto one half-court**, so `x` carries no information about which basket and
needs no flip between periods. A pipeline that "corrected" for a side swap would be introducing an
error, not removing one.

## 3. Where the basket is — and the guess that was wrong

The three-point line is a physical constant, so it can be used as a ruler to *test* a candidate
origin rather than being assumed alongside one: a correct origin must put essentially every 3PT
attempt beyond the arc and every 2PT attempt inside it. A wrong origin cannot do both.

An NBA hoop sits 5.25 ft in from the baseline, so measuring `y` from the baseline is the natural
reading. **It scored 53.6%.**

| candidate origin | 3PT beyond arc | 2PT inside arc | joint |
|---|---|---|---|
| (25, **0**) | **638/638 (100.0%)** | **1431/1431 (100.0%)** | **1.0000** |
| (25, 4.75) | 395/638 (61.9%) | 1431/1431 (100.0%) | 0.6191 |
| (25, 5.25) | 342/638 (53.6%) | 1431/1431 (100.0%) | 0.5361 |
| (25, 6.00) | 299/638 (46.9%) | 1431/1431 (100.0%) | 0.4687 |
| (0, 25) *(transposed control)* | 385/638 (60.3%) | 78/1431 (5.5%) | 0.0329 |

**ESPN measures `y` from the basket, not the baseline.** That also explains `y` running to −5:
those are attempts from behind the backboard, which are impossible under a baseline origin.

The transposed control matters. It is the candidate that would win if `x` and `y` were swapped, and
it fails on the 2PT side (5.5%) rather than merely scoring lower — so the axes are the way round
this document says they are, not by convention but by measurement.

Under the fitted origin the two distributions separate with no overlap at all: **max 2PT distance
21.5 ft, min 3PT distance 22.0 ft.**

### The limitation this leaves

The arc test scores a perfect 1.0000 for every `y` in **[−1, +2]** and only degrades at −2. It
locates the origin to a band about three feet wide, not to a point.

That is ample for the 2PT/3PT split, which is what the arc actually measures. It is **not** ample
for a 4-foot rim radius, which the same uncertainty could shift by a third. So `rim` versus
`paint_non_rim` is the softest boundary in `shotprofile/court.py`, and a study that leans on it
should treat it as approximate. The three-point boundaries are measured; the rim boundary is
reasoned.

## 4. Free throws never carry a location

**1,094 free-throw events, 0 with a usable coordinate** — across every run, every season.

So the exclusion rule needs no cleverness, but it does need to exist: a free throw's notional
location is the line, and admitting one as a field-goal coordinate would pull every high-volume
foul-drawer's profile toward it. That reads as a real basketball finding rather than as a bug,
which is what makes it worth a schema validator rather than a comment.

## 5. Most coordinate-bearing events are not shots

| event type | count with a usable coordinate (25 games) |
|---|---|
| Defensive Rebound | 1,634 |
| Offensive Rebound | 673 |
| Shooting Foul | 490 |
| Personal Foul | 260 |
| Bad Pass Turnover | 214 |
| Lost Ball Turnover | 169 |

Rebounds alone outnumber the shot attempts. **Filtering on `shootingPlay` is not optional**: a
pipeline that treated every coordinate as an attempt would roughly double its sample and skew it
toward the rim, inflating rim rates for exactly the players who crash the glass — a bias that looks
like a plausible basketball result.

Conversely, some events legitimately carry the sentinel: substitutions (1,365), timeouts (254),
period ends (100), jump balls (36), and every free throw.

## 6. Made and missed are encoded alike

`made x: median 25.0, p5 3.0, p95 47.0` against `miss x: median 25.0, p5 2.0, p95 48.0`. No
positional bias between outcomes, so made and missed attempts can be pooled for rate estimation
without a correction.

`scoringPlay` is authoritative when true. False is **not** evidence of a miss on its own — it is
also false for every non-shot event — so the parser consults ESPN's own wording before returning a
verdict and returns `None` when neither says anything.

## 7. What this data is not

It is a description of **the shooter**: where the attempt came from, and whether it went in.

It says nothing about who was defending. Every endpoint that carries defender attribution is
unreachable from this project's egress (`MATCHUP_SOURCE_AUDIT.md`), and no amount of processing
turns a shot location into a defender. `shotprofile.events.DEFENDER_ATTRIBUTION_AVAILABLE` is
`False` so that this is a value a test can assert against rather than a sentence somebody skims.

**Shot-profile data available ≠ defender matchup data available.**
