# Archive-latency diagnosis (Issue #53; research only, descriptive)

Four clocks decide whether a market snapshot can be used for a decision at instant D (= tip - offset):
  1. OBSERVED  - the capture tick stamp (file name `kalshi_markets*_<stamp>_*`): when the capture worker finished its Kalshi fetch (the quotes are at most this old);
  2. COMMITTED - the git commit time of the commit that ADDED the tick's file to the capture branch (`data-archive`): the independent archive clock;
  3. VISIBLE   - when a sealer can read it: commit time + push/fetch propagation + (for a polling sealer) up to one poll interval; this is not recorded anywhere, so it is
                 bounded here by the commit time (lower bound) and the poll interval (90 s) of the chain;
  4. DECISION  - the checkpoint D at which an order could really be placed.
The strict control (PF_EDGE_STRICT_T60_EXEC_V1) uses the latest tick OBSERVED <= D and requires it to be COMMITTED <= D. Because ticks reach the branch ~3.5 minutes after they are
observed, that rule fails whenever the latest tick is younger than its own lag, whatever the checkpoint minute is. The alternative studied here uses the latest tick COMMITTED <= D
(what a trader running at D could actually have read) and bounds its staleness.

* live capture ticks analysed: 378 (2026-10-18T16:14:20Z .. 2026-10-22T13:48:47Z); 0 rewritten / backfilled commits excluded
* observed -> committed lag (s): min 188, p10 199, median 211, p90 331, max 502
* tick spacing in game hours (s): p10 300, median 600, p90 900

## Coverage of a usable board by rule (all game-hour instants, descriptive)

| rule | instants | share ok | median board age (s) | p90 age (s) |
|---|---|---|---|---|
| strict_observed_and_committed | 528 | 0.456 | 500.0 | 800.0 |
| available_latest_committed | 528 | 0.633 | 500.0 | 800.0 |

## Coverage by real game and checkpoint offset (regular-season games with live ticks)

| offset | games | strict (control rule) ok | available-board rule ok | fcst committed by D | median age of available board (s) |
|---|---|---|---|---|---|
| T-30 | 14 | 5 | 13 | 14 | 617.0 |
| T-35 | 14 | 5 | 13 | 14 | 424.0 |
| T-40 | 14 | 3 | 11 | 14 | 414.0 |
| T-45 | 14 | 5 | 14 | 14 | 497.0 |
| T-50 | 14 | 5 | 13 | 14 | 424.0 |
| T-55 | 14 | 3 | 11 | 14 | 437.0 |
| T-60 | 14 | 5 | 14 | 14 | 557.0 |

Under the strict rule the usable share is set by tick spacing and lag, not by the checkpoint minute (the T-60 and T-45 rows are alike); reading the latest tick COMMITTED by the decision instant removes the commit-latency exclusion at the price of an older quote (the age column), which the executable-price check and the 900 s age guard bound.
