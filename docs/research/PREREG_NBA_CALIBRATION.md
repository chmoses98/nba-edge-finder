# Preregistration: NBA participation and prop-ladder calibration (RESEARCH_ONLY, NO PROMOTION)

Committed alone, **before** any calibration fit or evaluation is run. Nothing below may change after the first
evaluation run; any deviation is reported as such.

## Questions
1. Does recalibrating P(play) for **confirmed-available** players (official report: implicitly active, or listed
   ACTIVE), using only information available before tip, improve participation forecasts?
2. Does an independent recalibration of player-prop ladder probabilities P(stat >= rung | plays) improve them?
3. Do the two help on top of the PIT availability overlay (PR #104)? Do they beat the market where a Kalshi
   quote exists?

## Data
* `nba-shadow-pure` @ `c8ef48f` (projections, outcomes/gate, market/listings). The availability archive is
  `projection-data` @ `a1cf3b5`, read through `nba_edge.availability.overlay` (effective-time PIT rules of #104).
* Population: REGULAR_SEASON projections in finished games with kickoff >= 2026-10-19 (availability archive
  start), both arms (`sim_rotation`, `ewm5`), both slots (`morning`, `pretip`). Preseason rows are excluded.

## Independence of evaluation
* **Walk-forward (primary).** For each ET game date `d`, a calibrator is fitted only on rows whose outcome was
  observed (`outcomes/gate.observed_at`) before the earliest `as_of` of date `d`, then applied to date `d`.
  Burn-in: the first evaluated date is 2026-10-27 (at least 7 game dates of fitting data).
* Results are reported for window **A** (2026-10-27..10-31) and window **B** (2026-11-01..), and pooled. Window B
  was PR #104's availability holdout. It was viewed for availability metrics only; no calibration choice in this
  document used it.
* **Prospective.** A calibrator fitted on every eligible row through the data horizon is frozen
  (`docs/research/nba_calibration/frozen_calibrators.json`, sha256 recorded in the report). It is scored, unchanged,
  only on games tipping after the freeze. This result is reported as PENDING until such games exist.

## Methods (fixed; no other method or hyperparameter is tried)
* **Ridge-Platt.** `logit p' = a + b * logit(clip(p, eps, 1 - eps))`, fitted by penalised maximum likelihood with
  penalty `lambda * (a^2 + (b - 1)^2)` toward the identity map, `lambda = 10`. If the fitted `b <= 0.05`, the map
  is the identity (a monotone ladder must stay monotone).
* **P1, participation** (`eps = 0.01`): one map per (arm, slot).
  * *calibration-only:* fitted and applied on every projected player's baseline P(play).
  * *combined:* the #104 overlay first. Then a map fitted and applied only on players whose status at `as_of` is
    `unlisted` or `available`. All other statuses keep the overlay's rules (suppressed, capped or unchanged).
* **P2, prop ladders** (`eps = 0.005`): one map per (arm, family), family in {points, rebounds, assists, threes},
  pooled over slots. Fitted on the conditional rung probabilities of players who played, with y = 1{stat >= rung}.
  Applied to every rung of every issued ladder, in both the calibration-only and combined variants.
* Variants: `baseline`, `injury_only` (#104 overlay), `calibration_only` (P1 on baseline + P2), `combined`
  (overlay + P1 on confirmed-available + P2).

## Metrics
* **Participation.** Unit: player-game projection. Brier; log loss (every variant clipped to [0.005, 0.995], so a
  suppressed player is scored at 0.005); ECE (10 equal-width bins); logistic calibration intercept/slope.
* **Props.** Unit: rung of a player who played. Brier, log loss (same clip), ECE, calibration slope.
* **Market.** Kalshi listings with both yes bid and yes ask at the projection's `as_of`; market probability is
  the mid. Reported: paired Δ Brier (model − market).
* **Coverage.** Player-games and rungs issued per variant. Calibration never adds or removes a forecast; the
  conditional quantiles are untouched.
* **Subgroups:** slot × arm. Participation is also split by availability category (status at `as_of`); props by
  family. CIs are 95%, game-clustered bootstrap (2,000 resamples).

## Decision rules (a calibrator is ADOPTED only if all hold on the pooled walk-forward window)
1. **Improvement:** the target's paired Δ Brier vs the variant without it has a CI upper bound < 0.
2. **No subgroup harm:** no subgroup with >= 300 scored units has a Δ Brier CI lower bound > 0.
3. **No false confidence:** no subgroup with >= 300 units ends with calibration slope < 0.80 when its uncalibrated
   slope was >= 0.80, and no such subgroup's ECE worsens by more than 0.01.
4. **Market:** a "beats the market" statement requires a Δ Brier (model − market) CI upper bound < 0. Otherwise
   the result is reported as "not better than market".

Rejected methods are reported with their numbers; they are not replaced by a variant found afterwards.
