# Moneyline: does DATA_ONLY carry information the Kalshi price does not?

**No. The answer is a clear negative, and the reason is diagnosable.**

Method: one simulation per game at the game's own ET-date cutoff (strictly point-in-time), every
contract of that game priced from the same draws, then a chronological walk-forward fit of the
nested pair

```
market-only :  logit(y) ~ a + b·logit(p_market)
with-model  :  logit(y) ~ a + b·logit(p_market) + c·[logit(p_data) − logit(p_market)]
```

`c > 0` out of sample would mean the model's disagreement with the price points the right way.
Sample: **2,372 out-of-sample rows over 1,186 distinct games**, final valid pre-tip observation.
Nothing below is in-sample.

## The result

| model | OOS log loss | Brier | ECE |
|---|---:|---:|---:|
| market, raw price | **0.5715** | **0.1952** | 0.0237 |
| market, recalibrated | 0.5739 | 0.1959 | 0.0190 |
| DATA_ONLY | 0.6081 | 0.2093 | 0.0194 |
| HYBRID (fitted) | 0.5740 | 0.1960 | 0.0134 |

- **Residual coefficient per fold: `+0.096, +0.015, −0.015, −0.080`.** Mean `+0.004`. It changes
  sign across folds. This is noise, not signal.
- **The hybrid does not beat the recalibrated market** (log-loss gain **−0.00013**, i.e. worse).
- **Recalibrating the market makes it worse** (0.5739 vs 0.5715 raw). The Kalshi price is already so
  well calibrated that fitting a recalibration only adds estimation noise. The honest baseline is
  therefore the **raw price**, which is a higher bar than the calibrated one this test was designed
  to use.

## Why the model loses: it is under-dispersed, not unlucky

Grouping by market price shows the model's error is systematic and monotone, while the market's is
never worse than 0.8 points.

| market price bin | n | market | model | actual | market error | **model error** |
|---|---:|---:|---:|---:|---:|---:|
| 0.024–0.285 | 575 | 0.186 | 0.250 | 0.190 | −0.004 | **+0.061** |
| 0.285–0.425 | 552 | 0.361 | 0.398 | 0.364 | −0.003 | **+0.034** |
| 0.425–0.575 | 549 | 0.506 | 0.502 | 0.503 | +0.003 | −0.000 |
| 0.575–0.719 | 541 | 0.648 | 0.608 | 0.640 | +0.008 | **−0.031** |
| 0.719–0.975 | 555 | 0.820 | 0.752 | 0.818 | +0.002 | **−0.066** |

The simulator's win probabilities are **shrunk toward 0.5**. It is accurate on coin-flip games and
wrong by up to 6.6 points at the extremes, always in the direction of the middle. It does not
separate strong teams from weak ones enough.

**This is the practical consequence: every "edge" the model reports on a longshot is its own
shrinkage, not information.** A naive EV screen would systematically recommend buying underdogs —
the model says 25% where the market says 18.6% and the truth is 19.0% — and would lose on all of
them, plus fees. That is exactly the "treat every large disagreement as free money" failure, and
here it has a measured magnitude.

## What this does and does not establish

- It **does** establish that for `game_winner`, over 1,186 games, DATA_ONLY adds nothing to the
  Kalshi price, and that a HYBRID cannot be justified on this evidence.
- It **does not** generalise to spreads, totals, team totals or player props. `game_spread` had too
  few markets with candles to fit at all (101 markets over 10 games). Those families are tested
  separately and this result must not be quoted for them.
- Combined with `MARKET_BASELINE.md`: profit needs ~2.3 points of edge after fees, and the measured
  edge here is not merely under that threshold, it is **absent and of the wrong sign at the tails**.

## Follow-up this points at

Under-dispersion is a concrete, fixable defect, and it is consistent with two findings from the
pre-merge audit:

1. `engine.py` rescales every player's shooting by `factor = clip(ppp_mu / base_ppp, 0.75, 1.3)`, so
   realised efficiency tracks a roster-independent target — **roster quality is renormalised away**.
2. `impact_ppp` is unestimated, so team strength cannot respond to availability at all
   (`AUDIT_FOLLOWUPS.md` R1).

Both compress the spread of simulated team strength, which is exactly the shape of the error above.
`rating_scale` (R2, currently 1.6 and partly fitted in-sample) is the third candidate and the
cheapest to test: this table is the out-of-sample evidence against which any re-estimate should be
judged.

**Authority for `game_winner` remains RESEARCH, and this result is a reason against promotion, not
for it.**
