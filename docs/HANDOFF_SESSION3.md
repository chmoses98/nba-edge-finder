# Handoff — production baseline, minutes rebuild, injury impact, and the post-repair re-study

Every figure measured. Nothing transcribed.

**Bottom line: fixing two known basketball defects improved the model's calibration substantially
and produced no incremental predictive information beyond Kalshi's price. One of the two repairs
was rejected outright. Authority remains RESEARCH everywhere.**

---

## A. Current main SHA

`d76f800b4007ac6b9cf6b7309b23a9ff4db55f5d` — "Measure scheduler delivery, and stop a configured cap
from failing the conductor daily (#3)".

Lineage this wave: `9b51dbd` → `3c7b318` (#2) → `d76f800` (#3). PR **#4** is open with Phases 3–8.

## B. Production-safety PR

**PR #2, merged at `3c7b318`.** Contents: the three committed `.trigger/*` files removed, `.trigger/`
gitignored, a default-branch push guard on all three data-pull workflows, artifact preservation when
that guard fires, and regression tests covering the whole failure mode. `.trigger/conductor` was
audited and confirmed already absent from main.

**Verified live rather than assumed.** Merging #2 is itself a push touching `.trigger/*`, so it
re-fired all three pulls on main. They refused:

```
warning: Refusing to push to the default branch
         Ran on main. The data is in this run's workspace/artifact.
artifact: history-dataset-35852817253  1,428,061 bytes
```

Main unchanged at the merge commit, runs green, data preserved. No workflow storm: post-merge runs
settled and nothing wrote to main.

A third instance of the same defect family was found and filed, not fixed here: the commit step is
`if: always()`, so a **cancelled** pull still commits partial state. One did, shrinking
`MANIFEST.json` by 36 lines; it was reverted rather than force-pushed away.

## C. Scheduler reliability

`*/10 * * * *` declared. Measured over 5 days on main:

| metric | value |
|---|---:|
| expected slots | 646 |
| delivered | 29 |
| **delivery rate** | **4.5%** |
| median delay | 4.2 min |
| max delay | 9.7 min |
| **effective interval** | **222.6 min** |
| longest gap | **357.2 min** |

**The failure is omission, not lateness.** Every delivered run arrived within 9.7 minutes of its
slot. GitHub is punctual when it fires and simply does not fire 19 times in 20. Delay tolerance,
retry-on-late and age-based triggers all address lateness and cannot help.

Requirement defined for preseason: ≥95% of capture intervals ≤12 min, no gap >30 min in an active
window. Current delivery fails by roughly 20×. Proposed fix, still GitHub-native: capture in a
bounded loop **inside one run**, near the 6-hour job limit, with overlapping runs — the worst
observed gap (357 min) exceeds a 5.5-hour loop, which is stated rather than glossed. External cron
and self-hosted runners named as alternatives, deliberately not taken.

Operational consequence, observed: the alarm fix merged at 11:08 and **no scheduled run had fired by
12:40**, so it is not yet confirmed in production. That is what a 3.7-hour effective interval costs.

## D. Rotation size, old vs new

Real NBA (7,386 team-games): mean 9.12 players at 10+ minutes, sd 0.97, 91% between 8 and 10.

| statistic | actual | old model | new model |
|---|---:|---:|---:|
| players ≥ 5 min | 9.93 | 11.83 (+1.90) | 9.33 (**−0.60**) |
| players ≥ 10 min | 9.12 | 10.37 (+1.25) | 8.96 (**−0.16**) |
| players ≥ 28 min | 3.98 | 2.13 (−1.85) | 3.70 (**−0.28**) |
| top-8 minute share | 0.90 | 0.81 (−0.09) | 0.92 (**+0.02**) |

## E. Minutes error, old vs new

| stratum | MAE EWM-5 | MAE old | MAE new |
|---|---:|---:|---:|
| all | **7.12** | 7.28 | 7.35 |
| starters | **6.58** | 7.56 | 7.85 |
| bench | 7.44 | 7.11 | **7.05** |
| did not play | 14.88 | 10.17 | **8.79** |

**EWM-5 wins on point accuracy and is not replaced.** The mixture's gain is distributional:

| 80% interval coverage | old | new |
|---|---:|---:|
| all | 0.613 | **0.782** |
| high-minute (≥28) | **0.391** | **0.712** |

And heavy-minute predictions now occur at the right rate: the old model predicted ≥28 minutes **270**
times against EWM-5's 751 and the new model's 691 (bias +1.19).

## F. Downstream prop effect

Small. Conditioned identically on both sides, the repair closes **6–8%** of the prop-over bias
(points 0.780 → 0.795 of actual). That frame is itself selection-biased and is quoted only to show
the repair is insufficient.

Points per minute conditioned on playing is **0.95** of actual, so Phase 7's earlier "minutes, not
efficiency" conclusion is **only partly supported** — there is a real ~5% efficiency shortfall the
earlier analysis called accurate. Both channels contribute.

## G. Injury-impact methodology

Minutes-share ridge APM. Each team-game row carries **both** teams — the scoring team's players as
offensive columns, the conceding team's as defensive — so opponent quality is controlled by
construction. Players under 15 games pool into a replacement bucket. Coefficients clipped at ±0.06
per possession with the clipping counted. True RAPM was **not** claimed: game-level box scores have
no lineups.

## H. Injury-impact out-of-sample results — **REJECTED**

| split | α | RMSE team | RMSE +impact | gain |
|---|---:|---:|---:|---:|
| tune | 25 | 0.10960 | 0.11041 | −0.00081 |
| tune | 1600 | 0.10960 | 0.11032 | −0.00072 |
| **holdout** | 1600 | **0.11506** | **0.11689** | **−0.00184** |

Negative at every α; the tuner's "best" is the most shrunk value tested. Fails on depleted rosters
too (MAE 0.0935 vs 0.0991). The test used **actual** minutes shares — oracle knowledge — and failed
anyway.

Mechanism: the impact term has sd **0.00017** across games, near-collinear with the team rating;
residual correlation after conditioning on that rating is **−0.046**. The holdout coefficient of
+93.9 is least squares rescaling a near-constant column.

**The problem is the data, not the fit.** `impact_ppp` stays 0.0. **R1 remains open and still blocks
promotion.**

## I–J. Team/moneyline performance and dispersion

| market price bin | market | OLD | NEW | actual | OLD err | NEW err |
|---|---:|---:|---:|---:|---:|---:|
| 0.024–0.285 | 0.186 | 0.250 | 0.219 | 0.190 | +0.061 | **+0.029** |
| 0.575–0.719 | 0.648 | 0.608 | 0.624 | 0.640 | −0.031 | **−0.016** |
| 0.719–0.975 | 0.820 | 0.752 | 0.784 | 0.818 | −0.066 | **−0.034** |

Error roughly halves in every bin. Probability spread 0.2083 → **0.2339** against the market's
0.2277: the model is no longer compressed toward 0.5.

**Attribution caveat:** this changes `rating_scale` (1.6 → 1.9) and the minutes model together and
cannot separate them. `rating_scale` was independently validated against exactly this failure, so it
probably carries most of it. A calibration slope was computed and deliberately **not** reported — the
market's own slope came out at 2.75, meaning the statistic measures a clipping artifact.

## K. Market-vs-model after repairs

| family | market raw | DATA_ONLY old | DATA_ONLY new | c old | c new |
|---|---:|---:|---:|---:|---:|
| game_winner | 0.5716 | 0.6074 | 0.6103 | −0.015 | −0.004 |
| game_spread | 0.5329 | 0.5709 | 0.5788 | −0.088 | −0.098 |
| game_total | 0.5957 | 0.6565 | 0.6676 | −0.116 | −0.122 |
| player_points | 0.4878 | 0.5585 | **0.5500** | +0.134 | +0.029 |
| player_rebounds | 0.5249 | 0.5739 | 0.5808 | +0.191 | +0.032 |
| player_assists | 0.4667 | 0.5313 | **0.5301** | +0.428 | +0.075 |
| player_threes | 0.4885 | 0.5101 | 0.5204 | +0.365 | +0.197 |
| team_total | 0.6149 | 0.6361 | 0.6496 | −0.455 | −0.391 |

The raw market price is still the best forecaster in **every** family.

## L. Does DATA_ONLY provide residual information beyond Kalshi? **No.**

De-laddered, one row per entity-game:

| family | c per fold, OLD | c per fold, NEW |
|---|---|---|
| player_points | 0.356, −0.029, −0.063, 0.002 | 0.099, −0.115, −0.097, −0.086 |
| **player_rebounds** | **0.238, 0.251, 0.224, 0.098** | **0.050, 0.084, 0.097, −0.113** |
| player_assists | 0.319, 0.026, 0.026, 0.068 | 0.124, −0.100, −0.005, −0.043 |
| player_threes | −0.340, −0.022, −0.484, −0.360 | −0.087, −0.053, −0.029, 0.058 |

Every family changes sign across folds. **`player_rebounds` — the one lead that survived the last
wave — does not survive the repair.** A signal that vanishes when an unrelated part of the model is
fixed was very probably noise.

Residual coefficients moved *toward* zero across the board. That is coherent: a better-calibrated
model of an already well-calibrated market agrees with it more closely. **Agreement is not edge.**

## M. Authority

**RESEARCH for all eight families. Unchanged. No promotion recommended, including to SHADOW.**
R1 (no empirical team-level injury response) is still open and still blocking.

## N. Unresolved blockers

1. **R1** — no team-level injury response. The box-score approach is now *disproven*, not untried.
   Needs play-by-play/lineup data.
2. **Scheduler delivery at 4.5%** — the 5–10 minute capture objective is unreachable as configured.
3. **`if: always()` on data-pull commit steps** — a cancelled run commits partial state.
4. **~20% prop-over bias remains**, with a ~5% efficiency component the earlier diagnosis missed.
5. **Alarm fix unconfirmed in production** — no scheduled run since it merged.

## O. Next five highest-value tasks

1. **Acquire play-by-play/lineup data.** It is the only path to R1, and R1 gates everything.
2. **Implement the in-run capture loop** and measure it against the §C requirement before the season.
3. **Find the residual ~5% efficiency shortfall** in prop projections — minutes are now largely
   right, so this is the remaining half of the prop bias.
4. **Fix `if: always()`** so partial pulls cannot commit, and re-pull ESPN history so committed data
   reproduces committed numbers.
5. **Stop adding model capacity until 1–3 are done.** Two rounds of repair have now improved
   calibration without producing edge; the next thing that changes that answer will be better data,
   not a better fit.
