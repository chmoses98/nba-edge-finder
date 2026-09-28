# MATCHUP_AWARE_V2

**Status: RESEARCH. Effects version `neutral-0`. It changes no prediction, no price, and no bet.**

This is the machinery for learning player-vs-defender, lineup, scheme and shot-profile effects. It
has learned none. `NBA_BASELINE_2026_PRESEASON_V1` is untouched and remains the only thing that
prices anything.

The distinction the mission insists on, and this document keeps: **architecture existing is not the
same as an effect being known.** Everything below describes a pathway that is wired and tested and
currently carries a value of exactly 1.0.

---

## 1. The shape of it

```
                    (RESEARCH, neutral today)
  GameMatchupContext ──► resolve_adjustments ──► {player_id: MatchupAdjustment}
   (point-in-time)          (effects.py)                    │
                                                            ▼
        V1 GameParams ──────────────────────────► apply_matchup ──► GameParams
     (FROZEN BASELINE)                             (transform.py)        │
                                                                        ▼
                                                            simulate()  ── unchanged
                                                          (sim/engine.py)
```

Two properties do the load-bearing work.

**The simulator is not forked.** V2 is a transform on `GameParams`, so there is exactly one
simulation engine and no second copy to drift. A matchup effect is expressible if and only if it can
be written as a change to the parameters V1 already has.

**A neutral layer returns the original object.** `apply_matchup` returns `gp` *itself* — the same
Python object, not an equal copy — when every adjustment is neutral. That turns "V1 is unchanged"
from a claim into something the type system can be asked about, and it is why the regression test
can assert `v2_params is gp` before it ever runs a simulation.

The regression test then runs one anyway, and compares **full simulation arrays bitwise**, every
player and every stat, not means. A mutation check confirms it is not vacuous: shading one player's
`fga_per_min` by 0.1% makes it fail.

---

## 2. Defender exposure is a distribution

The single most important schema decision. `PlayerDefenderExposure.shares` is a set of
`DefenderShare` rows that **must sum to 1.0**, and the ref types are:

| ref | meaning |
|---|---|
| `PLAYER` | a named defender; the only ref that may carry `defender_player_id` |
| `POSITION` | a positional bucket — *"a SG guarded him"*, not *"this SG did"* |
| `ARCHETYPE` | a defender archetype bucket |
| `SWITCH_OTHER` | mass that switched, cross-matched, or was otherwise unattributable |
| `UNKNOWN` | mass the source could not attribute at all |

A switch-heavy environment is represented by a large `SWITCH_OTHER` share, and a game with no
defender data at all is `UNKNOWN: 1.0`. Neither is a missing value, and neither can be mistaken for
a confident assignment: `identified_share` reports precisely how much of the distribution names a
player.

**The forced one-to-one label is the failure mode this prevents.** "LeBron is guarded by the
opposing SF" is a sentence that survives contact with no NBA possession data. The tests assert that
a real distribution keeps its `SWITCH_OTHER` residual, that positional evidence can *never* produce
a `PLAYER` share, and that a thin sample reports `UNKNOWN` rather than a confident defender.

### Likely-defender assignment (`assignment.py`)

Three tiers, and a floor:

| evidence | output | confidence |
|---|---|---|
| observed shares, ≥ 200 possessions | `PLAYER` shares + `SWITCH_OTHER` residual | `min(0.85, n/(n+400))` |
| positional only | `POSITION` refs | 0.25 |
| none | `UNKNOWN: 1.0` | 0.0 |

`MIN_POSSESSIONS_FOR_NAMED_DEFENDERS = 200` is a fail-closed threshold, not a tuned one. Below it
the model declines to name anybody, which is the honest answer to "who guards him?" given thirty
possessions. Confidence never reaches 1.0 at any sample size.

---

## 3. Component effects, not one multiplier

`MatchupAdjustment` carries separate multipliers and deltas so a matchup can say **points down but
assists up** — which is what a good defensive matchup usually does, and what a single scalar cannot
express.

| applied to V1 | field |
|---|---|
| `fga_per_min` | `fga_multiplier` |
| `usage_elasticity` | `usage_multiplier` |
| `min_mean` | `minutes_multiplier` |
| `three_share`, `fta_per_fga` | `three_rate_delta`, `ft_rate_delta` |
| `ast_weight`, `tov_weight` | `assist_rate_delta`, `turnover_rate_delta` |
| `fg2_pct`, `fg3_pct` | `fg2_eff_delta`, `fg3_eff_delta` |
| `oreb_weight` / `dreb_weight` | `rebound_weight_delta` |
| **nothing — reported, not dropped** | `rim_rate_delta`, `midrange_rate_delta`, `pullup_rate_delta`, `catch_shoot_rate_delta` |

The last row matters. V1 has no shot-zone parameters, so a zone effect has nowhere to land today.
`transform.UNAPPLICABLE_FIELDS` makes that visible in the transform report instead of discarding it,
so a future V1 that gains a zone model finds the field already carrying data rather than discovering
it was silently thrown away for two seasons.

Everything defaults neutral: multipliers 1.0, deltas 0.0, `MatchupAdjustment.neutral()` is the
factory, and `is_neutral` is what `apply_matchup` checks before deciding to do nothing at all.

---

## 4. Point in time, and the leak it prevents

`leakage.py` enforces two rules, and refuses rather than assumes when it cannot.

- **Knowable-at.** A context is usable for a decision only if `observed_at_utc <= decision_at`.
  `latest_knowable` filters first and maximises second — the order is the whole point, because
  maximising first returns the newest context in the list, which is exactly how a confirmed lineup
  leaks backward into a decision made six hours before it existed.
- **Pregame is strictly before tip.** A context observed *at* tip is not pregame.
- **No tip, no verdict.** `assert_usable` raises when `tip_utc` is unknown rather than treating the
  context as pregame by default. The convenient assumption is the one that silently admits in-game
  information.

The walk-forward framework applies the same discipline at the study level: folds are snapped to game
boundaries, because a single game's props share an opponent, a lineup and a context, and splitting
one across train and eval leaks precisely the thing being tested.

---

## 5. The bar for earning influence

`residual_value_test` compares V2 against **three** baselines on paired rows: V1, the market, and
the hybrid. Beating V1 alone is not evidence — a matchup feature that merely recovers information
the market already prices is a more complicated way of agreeing with it, and this project has
measured that outcome before (`ALL_FAMILIES_MODEL_VS_MARKET.md`).

Every delta is reported next to its `n_paired`, and a study must state its sufficiency bar before
looking at the number.

Until that test passes prospectively: `MATCHUP_AUTHORITY = "RESEARCH"`, `EFFECTS_VERSION =
"neutral-0"`, and `effects_are_neutral()` returns True. The packet says so out loud rather than
rendering an empty explanation box — `explanatory_factors` is `[]` with a reason attached, because a
UI that shows nothing looks like missing data, and a UI that says "no effect has been learned" is
telling the truth.

---

## 6. What is collecting data now

`nba matchup-shadow`, wired as a worker `SLOW_JOB` and a `conductor.yml` step, writes one
`matchup/context` row per game inside a 36-hour horizon: schedule, both rosters, and explicit
provenance naming everything it does not have. No defensive-assignment source is reachable from this
project's egress — see `MATCHUP_SOURCE_AUDIT.md` — so exposures, starters and scheme are written
**empty with a stated reason**, never guessed.

That record is the asset. When a source does become reachable, the pre-tip state of each game will
already exist, recorded prospectively, instead of being reconstructed from hindsight.

---

## 7. What this arm is forbidden to do

Restated from the mission so the constraints live next to the code they constrain:

- not modify V1 predictive constants, or retune `rating_scale`
- not promote its own authority, or take any betting authority
- not invent matchup weights, or claim a defender effect without data
- not fit tiny matchup samples, or overfit individual defender-vs-player history
- not use same-game future information
- not create manually chosen superstar exceptions

Build the machinery now. Learn the weights later.
