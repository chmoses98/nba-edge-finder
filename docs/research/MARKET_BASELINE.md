# The Kalshi moneyline baseline, and what it costs to beat it

Generated from `data/research/market_table.parquet` (canonical market-observation table, executable
prices from candle bid/ask, joined to authoritative ESPN tips and settled outcomes). Sample:
**2,772 markets over 1,386 games** at the final valid pre-tip observation, 2025-10 .. 2026-06.

This note deliberately contains **no model**. It establishes what the market alone does, because
every later claim about edge is a claim about beating *this*.

## 1. The market mid is well calibrated

| bin | n | mean price | observed | diff |
|---|---:|---:|---:|---:|
| 0.0–0.1 | 64 | 0.074 | 0.016 | −0.058 |
| 0.1–0.2 | 246 | 0.152 | 0.179 | +0.027 |
| 0.2–0.3 | 298 | 0.249 | 0.245 | −0.004 |
| 0.3–0.4 | 400 | 0.350 | 0.362 | +0.012 |
| 0.4–0.5 | 375 | 0.447 | 0.467 | +0.019 |
| 0.5–0.6 | 369 | 0.553 | 0.531 | −0.022 |
| 0.6–0.7 | 410 | 0.650 | 0.634 | −0.016 |
| 0.7–0.8 | 293 | 0.751 | 0.747 | −0.004 |
| 0.8–0.9 | 250 | 0.848 | 0.828 | −0.020 |
| 0.9–1.0 | 67 | 0.926 | 0.985 | +0.059 |

**Log loss 0.5810, Brier 0.1995** (a coin flip is 0.6931 / 0.2500).

## 2. Two traps in that table, both of which manufacture false edge

**The rows are not independent.** Each game contributes *both* sides, so 2,772 markets are 1,386
games seen twice. The 0.0–0.1 and 0.9–1.0 bins overlap on **64 of 64 games**: they are the same
games from opposite ends. Reading "both tails deviate in the same direction" as corroboration is
double-counting one observation.

**Computing the standard error from the observed rate inflates significance.** Collapsed to one row
per game, the favourites priced ≥0.9 won 98.5% against a priced 92.6%. Using the observed rate
(0.985) gives SE 0.015 and a **4.0 SE** result. Under the null — the market's own price, which is
what is being tested — SE is 0.032 and it is **1.85 SE, p = 0.062**, from five bins, so the
Bonferroni threshold is 0.010.

| bin (favourite side, one row per game) | n | priced | observed | diff | z under null | binomial p |
|---|---:|---:|---:|---:|---:|---:|
| 0.5–0.6 | 364 | 0.553 | 0.527 | −0.026 | −0.99 | 0.343 |
| 0.6–0.7 | 411 | 0.650 | 0.635 | −0.015 | −0.64 | 0.535 |
| 0.7–0.8 | 293 | 0.751 | 0.747 | −0.004 | −0.14 | 0.893 |
| 0.8–0.9 | 250 | 0.848 | 0.828 | −0.020 | −0.89 | 0.378 |
| 0.9–1.0 | 67 | 0.926 | 0.985 | +0.059 | +1.85 | 0.062 |

All 1,386 favourites: priced 0.6949, won **945** against **963.2** expected, binomial **p = 0.294**.

**There is no detectable favourite–longshot bias in this sample.** That is the finding.

## 3. What a model has to clear before a single trade is profitable

The quoted spread is tiny — **median 1¢**, and buying YES at the ask costs only **0.54¢** over the
mid. The fee is the real cost. It is quadratic in price and charged on the whole order, so it is
largest at 50¢ and shrinks per contract with size (a 1-contract order rounds up to a whole cent).

| ask | fee @1 | fee/contract @100 | half-spread | **edge needed @1** | **@100** |
|---:|---:|---:|---:|---:|---:|
| 10¢ | 1¢ | 0.63¢ | 0.54¢ | **1.54 pp** | **1.17 pp** |
| 25¢ | 2¢ | 1.32¢ | 0.54¢ | **2.54 pp** | **1.86 pp** |
| 50¢ | 2¢ | 1.75¢ | 0.54¢ | **2.54 pp** | **2.29 pp** |
| 75¢ | 2¢ | 1.32¢ | 0.54¢ | **2.54 pp** | **1.86 pp** |
| 90¢ | 1¢ | 0.63¢ | 0.54¢ | **1.54 pp** | **1.17 pp** |

## 4. The consequence

A model must be right by **more than ~2.3 percentage points** on a near-even game, against a price
whose own deciles sit within about **2 points** of the observed frequency, before one contract
clears costs.

So the transaction cost is roughly the same size as the market's entire measurable miscalibration.
A marginally better model is not a profitable one here; only a substantially better one is. Any
future claim of moneyline edge should be read against this table first, and any claim resting on a
few percentage points in one price bucket should be checked against both traps in §2 — they were
each live in this very analysis before correction.
