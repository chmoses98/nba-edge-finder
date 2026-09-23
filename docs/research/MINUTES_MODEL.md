# Phase 3/4: rotation model — what it fixed, and what it did not

The old minutes model asked one question ("what does this player average?") and water-filled any
deficit across every available player. Measured against 7,386 real team-games it produced 11.83
players over 5 minutes where reality has 9.93, only 2.13 players at 28+ minutes where reality has
3.98, and sent 81% of minutes to its top eight where reality sends 90%.

The replacement models membership and conditional minutes as separate questions, draws rotation SIZE
from its empirical distribution, and treats depth as promotion under pressure. **It fixes the
distribution decisively and does not improve point accuracy. Both statements matter.**

## What it fixed: rotation shape

Error against reality, same 120 team-games, identical features:

| statistic | old error | new error |
|---|---:|---:|
| players ≥ 5 min | +1.90 | **−0.60** |
| players ≥ 10 min | +1.25 | **−0.16** |
| players ≥ 20 min | −0.69 | **+0.37** |
| players ≥ 28 min | **−1.85** | **−0.28** |
| top-8 minute share | −0.09 | **+0.02** |

## What it fixed: the simulator was badly overconfident

80% intervals, 3,676 held-out player-games:

| stratum | coverage old | coverage new |
|---|---:|---:|
| all | 0.613 | **0.782** |
| starters | 0.610 | **0.777** |
| **high-minute (≥28)** | **0.391** | **0.712** |
| did not play | 0.499 | **0.844** |

A nominal 80% interval covering 39% for exactly the players props are listed on is not a small
defect. This is the property a prop settles against.

## What it fixed: heavy-minute predictions now happen at the right rate

| predictor | times it predicted ≥ 28 min | predicted | actual | bias |
|---|---:|---:|---:|---:|
| EWM-5 | 751 | 30.66 | 29.79 | +0.86 |
| **old model** | **270** | 29.94 | 32.73 | −2.79 |
| **new model** | **691** | 30.81 | 29.62 | +1.19 |

The old model produced a heavy-minute prediction roughly a third as often as it should. That is the
starvation, quantified in a frame with no selection applied to the outcome.

## What it did NOT fix: point accuracy. EWM-5 keeps its job.

| stratum | MAE EWM-5 | MAE old | MAE new |
|---|---:|---:|---:|
| all | **7.12** | 7.28 | 7.35 |
| starters | **6.58** | 7.56 | 7.85 |
| bench | 7.44 | 7.11 | **7.05** |
| did not play | 14.88 | 10.17 | **8.79** |
| low-minute rotation | **4.35** | 5.03 | 6.39 |

**EWM-5 has the best mean-minutes accuracy and is not replaced.** The brief's rule is explicit and
the evidence does not clear it.

This is expected rather than disappointing: a blend minimises absolute error by construction, while
a mixture deliberately places mass at zero and at full rotation minutes. The two can share a mean
and score differently on MAE. The mixture is kept because coverage and heavy-minute frequency are
what price a contract, not the mean.

## Two wrong turns, both caught by measurement

**Leaving rotation size to chance.** The first version drew membership as independent Bernoullis and
produced 7.66 players at 10+ minutes against a real 9.12 — it swapped the old dilution for the
opposite error. Size is now drawn from the empirical distribution (mean 9.12, sd 0.97, 91% of
team-games between 8 and 10) via Gumbel-top-k, which keeps player-level uncertainty.

**Blaming selection noise for the starter regression.** The starter MAE regressed, and the apparent
cause was that the logit gap between a starter (0.850) and a bench player (0.482) is only 1.80
against Gumbel noise of sd ≈1.28. Lowering the temperature made marginal calibration **worse**
(0.089 → 0.157), because low noise collapses towards deterministic top-k.

The actual defect was that the membership estimates did not add up: they summed to 7.78 on a
representative roster while real rotations average 9.12, so selecting nine players had to inflate
the middle. A single additive log-odds offset, solved so the probabilities sum to the expected size,
fixed the inconsistency (marginal error 0.089 → 0.053). It did **not** move the validation metrics,
which is itself informative: the starter MAE gap is the mean-vs-mixture tradeoff above, not a
selection bug.

## The honest limit: this did not fix the prop-over bias

Conditioned identically on both sides, the model still projects roughly 20% low on counting stats,
and the rotation repair closes only **6–8%** of that gap (points 0.780 → 0.795 of actual).

That frame is itself selection-biased — conditioning on "actually played" selects games where a
player played more — so the 6–8% is not a clean number either, and it is quoted here only to say
that the repair is clearly not sufficient. In the unbiased symmetric frame the new model is well
calibrated (predicts ≥28 → actual 29.62 against predicted 30.81).

The decisive test is the market-anchored one in `ALL_FAMILIES_MODEL_VS_MARKET.md`, re-run with this
model, where every settled market is included and no conditioning choice is available.

**Phase 7's conclusion that the bias was "minutes, not efficiency" is therefore only partly
supported.** Minutes were genuinely mis-distributed and are now much better distributed, but fixing
that did not remove the bias. Points per minute conditioned on playing is 0.95 of actual — a real 5%
efficiency shortfall that the earlier analysis called accurate. Both channels contribute.
