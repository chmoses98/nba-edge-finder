# Model freeze — `NBA_BASELINE_2026_PRESEASON_V1`

**Digest:** `5a4cbda0b973d1e4d6289557b99372e4735ebe3146fa76e8f0b6ca833193be78`
**Minted:** 2026-09-24 against main `250a7b3`
**Manifest:** [`docs/baseline/NBA_BASELINE_2026_PRESEASON_V1.json`](../baseline/NBA_BASELINE_2026_PRESEASON_V1.json)

## Why

Two waves of work have established a result: **the raw Kalshi price is a better forecaster than this
model in all eight tested families, and the repaired model carries no incremental information
conditional on that price.** That result is only worth something if a future comparison is honest.

It stops being honest the moment a predictive parameter moves without anyone recording it. "The new
model is better" then may only mean "the new model is different, and the old one can no longer be
reconstructed". Recording version *strings* does not prevent this: `MODEL_VERSION = "nba-sim-0.1.0"`
is unchanged by editing `rating_scale` from 1.9 to 2.1.

So the freeze hashes parameter **values**, read live from the code rather than copied, and
`tests/test_baseline_freeze.py` fails when the digest moves. Verified by deliberately tuning
`rating_scale` 1.9 → 2.1: the suite fails and names the parameter family.

## What is frozen

Everything that can move a number the model outputs, read from the source of truth at runtime:

| family | contents |
|---|---|
| league constants | 27 values — pace, ppp, home edge, b2b penalty, shooting/efficiency rates, rebounding, turnovers, quarter shares, OT rate, blowout thresholds |
| feature builder | `rating_scale` **1.9**, team/player/rate half-lives, priors, `role_window`, `rotation_window`, `rotation_half_life`, roster bounds |
| rotation model | `ROTATION_MIN` = 10.0, the empirical rotation-size PMF |
| player defaults | `min_cap`, `minutes_dispersion`, `impact_ppp` (**0.0** — R1 open), `usage_elasticity` |
| pricing | hybrid market weight 0.7, per-scope weights (game 0.9 / player 0.7 / season 0.95), stale-quote minutes |
| versions | model, simulation, features, season simulation, settlement engine |

The baseline also fixes the **market benchmark methodology**: the raw executable Kalshi price at the
final valid pre-tip observation, walk-forward with fold boundaries snapped to game boundaries, and
prop families de-laddered to one row per entity-game. Those choices are what the recorded numbers
mean, and changing them changes the comparison as surely as changing a constant would.

## What is NOT frozen

Deliberately free to improve, because this wave is about evidence rather than prediction:

- data collection, capture cadence, and archive structure
- workflow safety, scheduling, and infrastructure
- reporting, dashboards, and health artifacts
- bug fixes whose purpose is to make the code do what it already claimed to do

A bug fix that changes predictions is **not** a bug fix for these purposes — it is a model change
and needs a new baseline.

## The contract

1. A frozen value may change. It may not change **silently**.
2. Changing one requires minting a new `BASELINE_ID`, keeping the old entry in `KNOWN_BASELINES`,
   and recording the reason here.
3. Pasting a new digest over the old one is the one prohibited action: it erases the comparison
   point the next result depends on.
4. Future models are judged **prospectively against the frozen baseline**, not against a
   retrospectively re-fitted version of themselves.

## Research freeze in force

Until (A) a materially better data source is available, (B) lineup/stint data is validated, or
(C) meaningful 2026-27 prospective evidence accumulates, the following are **not** to be done:

- re-tune `rating_scale` or any league constant
- add predictive features speculatively
- optimise model weights against Kalshi prices
- create new HYBRID weights
- promote any family's authority
- claim an edge
- mine market segments for profitable-looking subsets

**The market beating us in all eight families is the current result. It is preserved, not
worked around.**
