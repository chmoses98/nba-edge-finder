# Does DATA_ONLY beat the Kalshi price in any family? No.

Eight families, contemporaneous pre-tip prices, chronological walk-forward, nothing in-sample.
**In not one family does the fitted hybrid beat the market out of sample.** The honest answer to
Phase 6 — what family-specific HYBRID weight should DATA_ONLY get — is **zero, everywhere, on this
evidence**.

## Headline table (final pre-tip horizon, out-of-sample)

| family | n rows | games | market raw | market cal. | DATA_ONLY | hybrid | residual c | hybrid wins |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| game_winner | 2472 | 1236 | **0.5716** | 0.5772 | 0.6074 | 0.5777 | −0.015 | no |
| game_spread | 2089 | 172 | **0.5329** | 0.5366 | 0.5709 | 0.5379 | −0.088 | no |
| game_total | 1744 | 161 | **0.5957** | 0.6000 | 0.6565 | 0.6037 | −0.116 | no |
| team_total | 443 | 39 | **0.6149** | 0.6373 | 0.6361 | 0.6566 | −0.455 | no |
| player_points | 2276 | 116 | **0.4876** | 0.4901 | 0.5585 | 0.4908 | +0.134 | no |
| player_rebounds | 2031 | 106 | **0.5249** | 0.5389 | 0.5739 | 0.5392 | +0.191 | no |
| player_assists | 1408 | 96 | **0.4667** | 0.4646 | 0.5313 | 0.4674 | +0.428 | no |
| player_threes | 1191 | 83 | **0.4885** | 0.4935 | 0.5101 | 0.4980 | +0.365 | no |

The raw market price is the best forecaster in every single family. DATA_ONLY is worse than the
market everywhere, by 3–7 points of log loss.

## The finding that looked real, and was not

Run on the table as-is, all four player-prop families had a residual coefficient **positive in every
fold — 16 of 16.** That is exactly the pattern a genuine effect produces, and it is the sort of
result that gets promoted.

It was mostly **ladder duplication**. A player's points markets at 14.5, 19.5, 24.5 and 29.5 in one
game are four monotone functions of one realised number, so one lucky player-game enters the fit
four times. Re-running with **one row per entity-game** (the line nearest 50¢, so rows are
independent):

| family | rows | per-fold c, laddered | per-fold c, **de-laddered** | still all +? |
|---|---:|---|---|---|
| player_points | 724 | 0.206, 0.200, 0.114, 0.016 | 0.356, **−0.029**, **−0.063**, 0.002 | **no** |
| player_rebounds | 557 | 0.458, 0.101, 0.098, 0.105 | 0.238, 0.251, 0.224, 0.098 | yes |
| player_assists | 431 | 0.647, 0.625, 0.244, 0.195 | 0.319, 0.026, 0.026, 0.068 | yes (but ≈0) |
| player_threes | 383 | 0.041, 0.659, 0.346, 0.413 | **−0.340, −0.022, −0.484, −0.360** | **no — sign flipped entirely** |

`player_threes` inverts from all-positive to all-negative. Pooled across all four families on
independent rows: `0.112, 0.037, −0.032, 0.013` — not consistently positive, and the hybrid still
loses (−0.00058).

**The 16/16 headline was an artefact of counting one observation four times.**

## The one lead that survives

`player_rebounds` keeps a positive coefficient in all four folds on independent rows, around
**+0.2**, and is the only family for which that is true. It is the single most promising result in
this work. It is **not** an edge claim:

- the hybrid still loses to the market out of sample (−0.00101);
- it rests on **557 entity-games** across 138 games;
- and rebounds is the family where the settlement audit found ESPN box-score errors of ±1 at a rate
  of 0.072%, the highest of any prop, so some of the disagreement is reference-data noise.

It deserves a dedicated study on more games. It does not deserve a position.

## Even a real edge would have to be large

Prop spreads are four times the moneyline's, and the fee is charged regardless.

| family | median spread | half-spread | fee @50¢ | **edge needed** |
|---|---:|---:|---:|---:|
| game_winner | 1¢ | 0.54¢ | 2¢ | **2.54 pp** |
| game_spread / game_total | 2¢ | 1.44¢ | 2¢ | **3.44 pp** |
| player props | 4¢ | ~2.2¢ | 2¢ | **~4.2 pp** |
| team_total | 8¢ | 3.81¢ | 2¢ | **5.81 pp** |

A residual coefficient of +0.2 on a logit scale moves a 50¢ contract by roughly a point. The bar is
four.

## Conclusions

1. **No family may be promoted.** Authority stays RESEARCH for all eight. Phase 6's learned weight
   for DATA_ONLY is zero everywhere.
2. **Recalibrating the market hurts** in 7 of 8 families (assists is the lone exception, and by
   0.002). The Kalshi price is already well calibrated; fitting a recalibration adds noise. Use the
   raw price as the benchmark.
3. **The game families are not merely unhelpful, they are wrong-signed.** `team_total` at −0.455 and
   `game_total` at −0.116 mean the model's disagreement points the *wrong way*, consistent with the
   under-dispersion measured in `MONEYLINE_MODEL_VS_MARKET.md`.
4. **Sample sizes are small and must be quoted as games, not markets.** 39 games for team_total, 83
   for threes, 96 for assists. Nothing here could detect a small true effect, and nothing here
   licenses a claim of one.
