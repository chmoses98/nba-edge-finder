# Frozen paper parlay tickets (RESEARCH_ONLY, no orders)

Append-only: one `tickets_<UTC>.jsonl` per freeze, created by `nba parlay-paper freeze --archive <archive> --date <ET date> --out docs/parlay_paper` strictly before the first tip and committed before tip (git timestamp is the second witness to `frozen_at_utc`). Never edit or delete a file; evaluate with `nba parlay-paper eval --archive <archive> --out docs/parlay_paper` (writes `parlay_eval.json`).

No Kalshi Combo/RFQ quote exists in the archive, so every ticket has `rfq_price_cents: null`: these are calibration-only tickets (hit frequency vs the predicted joint probability); the leg-ask product is a labelled reference, not a price, and no P&L or profitability claim can be made. Strategies: `selective` (raw model; the hypothesis under test), `selective_shrunk` (model shrunk 90% to the market; winner's-curse control), `simple_2leg`, `random_same_pool` (control).
