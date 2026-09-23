# Phases 7/8: what the repairs changed, measured against the market

Re-run of the moneyline dispersion diagnostics and the full market-vs-model study after
`rating_scale` 1.9 and the rotation/minutes rebuild. The previous wave's results are kept unchanged
in `MONEYLINE_MODEL_VS_MARKET.md` and `ALL_FAMILIES_MODEL_VS_MARKET.md`; this is a versioned
comparison, not a revision.

**Headline: calibration improved substantially. Incremental information over Kalshi's price did
not appear — and the one lead that survived the last wave did not survive the repair.**

## Phase 7 — the under-dispersion is largely fixed

Moneyline, 2,772 markets over 1,386 games, grouped by the market's own price:

| market price bin | n | market | OLD | NEW | actual | OLD error | NEW error |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0.024–0.285 | 575 | 0.186 | 0.250 | 0.219 | 0.190 | +0.061 | **+0.029** |
| 0.285–0.425 | 552 | 0.361 | 0.398 | 0.383 | 0.364 | +0.034 | **+0.019** |
| 0.425–0.575 | 549 | 0.506 | 0.502 | 0.503 | 0.503 | −0.000 | +0.000 |
| 0.575–0.719 | 541 | 0.648 | 0.608 | 0.624 | 0.640 | −0.031 | **−0.016** |
| 0.719–0.975 | 555 | 0.820 | 0.752 | 0.784 | 0.818 | −0.066 | **−0.034** |

Error is roughly halved in every bin. Spread of model probabilities: **market 0.2277, old 0.2083,
new 0.2339** — the old model was visibly compressed relative to the market; the new one is not.

**Attribution caveat.** The old scores were produced with `rating_scale` 1.6 *and* the water-filled
minutes model. This comparison changes both at once and cannot separate them. `rating_scale` 1.9 was
independently validated against exactly this failure (`RATING_SCALE.md`), so it probably carries
most of the improvement.

A calibration slope was also computed and is **not** reported: the market's own slope came out at
2.75, which means the statistic is dominated by a clipping artifact on binary outcomes rather than
measuring dispersion. The bin table and the standard deviations above are the trustworthy measures.

## Phase 8 — still no information the market lacks

Full study, final pre-tip horizon, walk-forward, nothing in-sample:

| family | market raw | DATA_ONLY old | DATA_ONLY new | residual c old | residual c new | hybrid wins |
|---|---:|---:|---:|---:|---:|---|
| game_winner | 0.5716 | 0.6074 | 0.6103 | −0.015 | −0.004 | no |
| game_spread | 0.5329 | 0.5709 | 0.5788 | −0.088 | −0.098 | no |
| game_total | 0.5957 | 0.6565 | 0.6676 | −0.116 | −0.122 | no |
| team_total | 0.6149 | 0.6361 | 0.6496 | −0.455 | −0.391 | no |
| player_points | 0.4878 | 0.5585 | **0.5500** | +0.134 | +0.029 | no |
| player_rebounds | 0.5249 | 0.5739 | 0.5808 | +0.191 | +0.032 | (see below) |
| player_assists | 0.4667 | 0.5313 | **0.5301** | +0.428 | +0.075 | no |
| player_threes | 0.4885 | 0.5101 | 0.5204 | +0.365 | +0.197 | no |

The raw market price remains the best forecaster in every family. DATA_ONLY improved slightly on
points and assists and got *worse* on the other six.

`player_rebounds` shows `hybrid wins: YES` on the laddered rows, by **0.0001 nats**. That is noise,
on rows that are not independent, and the de-laddered test below is what it should be read against.

### De-laddered: the last surviving lead is gone

One row per entity-game — the frame that exposed the previous wave's 16-of-16 result as ladder
duplication:

| family | n | residual c per fold, OLD | residual c per fold, NEW |
|---|---:|---|---|
| player_points | 725 | 0.356, −0.029, −0.063, 0.002 | 0.099, −0.115, −0.097, −0.086 |
| **player_rebounds** | 557 | **0.238, 0.251, 0.224, 0.098** | **0.050, 0.084, 0.097, −0.113** |
| player_assists | 431 | 0.319, 0.026, 0.026, 0.068 | 0.124, −0.100, −0.005, −0.043 |
| player_threes | 383 | −0.340, −0.022, −0.484, −0.360 | −0.087, −0.053, −0.029, 0.058 |

Every family now changes sign across folds. The hybrid loses to the market in all four, both before
and after.

**`player_rebounds` was the one lead worth keeping from the last wave** — positive in all four folds
on independent rows at roughly +0.2. After the repair it collapses to ~+0.08 with the final fold
negative. A signal that disappears when an unrelated part of the model is fixed was very probably
noise to begin with, which is what the previous write-up suspected and declined to claim.

## What this answers

The question was whether repairing known basketball defects creates genuine incremental predictive
information. On this evidence:

- **It creates better calibration.** The simulator is no longer visibly compressed on moneylines,
  and its minutes distribution is no longer badly overconfident (80% intervals covering 39% of
  high-minute players, now 71%).
- **It does not create incremental information over Kalshi's price.** No family's hybrid beats the
  market out of sample. The residual coefficients moved *toward zero*, not away from it.

Those are consistent, not contradictory. A better-calibrated model of a market that is already
well calibrated produces a model that agrees with the market more closely — which is what the
shrinking residual coefficients are showing. Agreement is not edge.

**Authority remains RESEARCH for all eight families. Nothing here supports promotion, including to
SHADOW.**
