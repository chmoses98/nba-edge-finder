# Preregistration: betting-value evaluation of the NBA PURE shadow (dry-run diagnostic)

Committed 2026-10-12, before any prospective row matured. On that date the `nba-shadow-pure` store branch did not
exist yet. The machine-readable copy is [`SHADOW_PURE_NBA_VALUE_PREREG.json`](SHADOW_PURE_NBA_VALUE_PREREG.json).
The code loads it and writes its sha256 into every `value_scorecard` record, so if the two copies disagree, the JSON
is what ran. Changing any setting means a new preregistration id and a new evaluation window.

This is track C (market value). It is separate from accuracy promotion, which uses the `accuracy_scorecard` records.
It runs only as a **dry-run diagnostic** inside `nba_edge.shadow.evaluate.evaluate`. Nothing reads its output to
place, size or route an order, and nothing touches staking or a production surface.

## Hypothesis and arms

* **H1.** At the pretip capture (T−90m..T−30m), buying the side preferred by the frozen V1 simulator
  (`sim_rotation`, `NBA_BASELINE_2026_PRESEASON_V1:sim-rotation-pure`) makes money. "Preferred" uses the
  simulator's conditional-on-playing ladder. Entry is at the executable Kalshi price, and returns are net of taker
  fees and one tick of slippage.
* **Primary arm.** `sim_rotation` at `pretip`, with the conditional rows. This is the only arm eligible for an
  independent-value verdict.
* **Descriptive only.** `sim_rotation` at `morning`, and `ewm5` at `pretip`. They are reported but not
  verdict-bearing.
* **Market-informed arms.** The collector has none. Any probability source flagged market-informed is forced to
  `NOT_INDEPENDENT_EVIDENCE`.

## Inputs (as_of information only)

* **Probabilities.** The captured conditional ladder, exactly as published: `p_yes = P(actual ≥ at_least | the
  player appears)`.
* **Quotes.** The separate `market/listings` family, mapped by `nba_edge.shadow.scorecards.market_family`:
  * **Player.** The resolved NBA id. Unresolved rows are dropped and counted.
  * **Strike.** The listing's `at_least` is already the event X ≥ at_least. "25+" maps to 25, and "> 24.5" maps to
    25. It matches the integer PURE rung exactly, and a strike that isn't on the ladder is a missing quote.
  * **Prices.** Kept in **cents** (`yes_bid_cents` / `yes_ask_cents`).
  * **Dropped and counted.** A row observed (`row_observed_at`, else `board_observed_at`) after the capture's as_of,
    and any crossed or out-of-range price.
  * **Entry.** The latest quote observed at or before as_of, on a market open by then.
* **Outcomes.** The ESPN box-score outcomes the collector writes. An eligible player absent from a final box score
  counts as 0 / not played, as in the existing evaluation.

## Decision rule, costs, settlement

| setting | value |
|---|---|
| decision unit | one per (game, player, statistic), at the earliest as_of within the slot |
| rule | `max_edge_after_fees`, `min_edge = 0.02` |
| fees | Kalshi taker, coefficient 0.07, multiplier 1 (series `fee_multiplier` = 1 per `NBA_DATA_SOURCE_AUDIT.md`), 1 contract per order, cent round-up |
| slippage | $0.01 per contract |
| stale quote | a quote older than 21,600 s at as_of is discarded and counted |
| calibration window | none, because both arms are frozen before collection |
| DNP policy | **`void`** |
| DNP sensitivity | unconditional rows with `settle_by_actual`, reported as `dnp_sensitivity` and never verdict-bearing |

### DNP policy, checked against the series rules

The repository records the rule in `docs/NBA_DATA_SOURCE_AUDIT.md` and `docs/research/RESEARCH_NOTES.md`. A player
prop whose player never enters settles at the **pre-game fair price**. It is not NO and not void (4.3% of KXNBAPTS
markets settled `scalar`). Holding to that fair price gives back about the entry price, so `void` is the closest
policy the scorecard offers. Pairing `void` with the conditional probability prices only the played branch.

`void` leaves out two costs:

* the fee, which isn't refunded
* the difference between the entry price and the final fair price

Both are small next to the played branch, and both are disclosed here rather than modelled.

## Minimum sample and inference

* **Minimums.** `min_decisions = 200` and `min_games = 40`, the SCORECARDS.md defaults. Below them the verdict is
  `INSUFFICIENT_SAMPLE`.
* **Confidence intervals.** ROI after fees has percentile bootstrap CIs that resample **whole games**: 2,000
  replicates, seed 20261010. A second CI resamples whole players.
* **Verdicts.**
  * `VALIDATED_VALUE` needs ROI > 0 **and** every clustered 95% CI lower bound > 0.
  * ROI > 0 that misses the CI requirement is `POSITIVE_BUT_INCONCLUSIVE`.
  * ROI ≤ 0 is `NO_EVIDENCE_OF_VALUE`.
* **CLV.** Diagnostic only; it never enters the verdict.

## What a verdict means

A verdict describes a recorded, preregistered evaluation window. It does not grant wagering authority, and this
document authorizes no change to staking or routing.
