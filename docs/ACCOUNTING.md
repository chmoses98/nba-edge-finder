# NBA wager accounting (routed from kalshi-bet-router)

**Accounting only.** This ledger records bets the owner already placed manually on Kalshi. It never decides,
sizes, recommends or places a bet. Every NBA model family remains **RESEARCH_ONLY** (`Authority.RESEARCH` on
every `ContractPrediction`; the slate's `authority_note` says the same), and nothing in the accounting path reads
or writes a prediction, a slate, a settlement record of the model's, or an authority ledger. A row here says
"the owner placed this NBA bet"; it never says "the NBA model recommended it".

## How a wager gets here
1. The owner places an NBA bet on Kalshi by hand.
2. kalshi-bet-router, which has READ-ONLY exchange access, sees the fills on its next scheduled run, classifies the
   market as NBA from Kalshi's own metadata, rebuilds the order from its fills and builds one import row
   (the snake_case router dialect: `source_bet_key`, `import_batch_id`, `entry_method`, `game_date`,
   `market_ticker`, `side`, `executed_at`, `contracts`, `execution_price`/`actual_price`, `stake`, `fees_paid`,
   `fees_are_estimated`, `venue`, and optionally `fee_state` / `execution_action`).
3. The router opens a delivery pull request into this repository's `accounting-data` branch, running this
   repository's importer (`scripts/accounting/import_routed_wagers.py --payload ... --base-dir ... --receipts-out ...`,
   code taken from `main`) and its validator (`scripts/accounting/validate_routed_ledger.py --base-dir ... --result-out ...`).
4. After Kalshi settles the market, the router's settlement job delivers the settlement the same way
   (`scripts/accounting/import_routed_settlements.py`, `router-settlement-economics.v2`).

**The router is the exchange-evidence authority.** Price, contracts, stake and fees come from the observed Kalshi
fills, and `fees_are_estimated` is always false. Nothing is reconstructed or estimated here.

## Where it lives
| what | where |
|---|---|
| ledger branch | `accounting-data`: an orphan branch holding only a README and the two files below; no model data, no market data |
| wagers | `data/accounting/wagers.jsonl` (`nba_accounted_wager.v1`), one line per order |
| settlements | `data/accounting/settlements.jsonl` (`nba_wager_settlement.v1`), one line per settled wager |
| code | `main`: `contract/edge_finder_contract/routed_ledger.py` (vendored, byte-identical across repos), `src/nba_edge/accounting/__init__.py` (the NBA `LedgerSpec`, declared once), `scripts/accounting/*.py` (thin CLI wrappers) |

There is no season partition: an NBA season spans two calendar years and filing must never guess one. The
`--season` flag is accepted and ignored for router compatibility.

The app export (`docs/APP_EXPORT.md`) reads this ledger read-only (`--accounting-dir <checkout of accounting-data>`)
and publishes it as `wagers.json` / `settlements.json`; it links a wager to a model price or recommendation only
temporally and never by hand.

## Identity
- `wager_id` = `nbaw-` + sha256(`source_bet_key`)[:24]
- `settlement_id` = `nbas-` + sha256(`source_bet_key`)[:24]
- No wall clock and no economics feed into either, so a re-delivery mints the same id and is recognised.

## Guarantees (tested in `tests/test_routed_accounting.py`)
- **Same row twice** gives `DUPLICATE_NOOP` and zero bytes change.
- **Same key with different economics** gives `CONFLICT` (field names reported, never values). Nothing is
  rewritten, and the importer exits 1 so the router's gate fails.
- **A settlement with no wager on the ledger** is refused as `ORPHAN`; a settlement whose ticker or side
  disagrees with its wager is refused.
- **A second, different settlement** for a settled wager is a `CONFLICT`.
- **Rows that are refused:** model or recommendation provenance fields (`recommendation_id`, `model_*`,
  `fair_*`, `prediction_id`, `authority`, `confidence`, `edge`, `gate` ...), unknown fields, estimated fees, a
  venue other than kalshi, non-positive contracts or stake, a price outside (0, 1), malformed timestamps,
  a stake that is not `contracts x price + fees`.
- **The validator** checks that every line decodes, both schemas, unique keys, that every settlement has its
  wager, and (with `--base-ref <git ref>`) that no existing line was removed or rewritten.
- **Exit codes:** 0 clean, 1 refused/conflict (gate fails), 2 unreadable payload or ledger.
- **Public Actions logs** carry counts and reasons only: never a ticker, stake, price, contract count, P&L or
  source key. Per-row receipts (key + minted id + verdict) go only to `--receipts-out`.
- **Isolation:** importing `nba_edge.accounting` loads no other `nba_edge` module.

## Status (2026-10-02)
- The importers exist on `main`; the `accounting-data` branch is created by the orchestrator and starts empty.
- No NBA wager has been placed through this path yet, so both ledger files are empty.
- The settlement path is TESTED, not OBSERVED.
