# Operations

## Day-one checklist (before 2026-10-03 preseason)
1. Merge PR #1 into `main` so `conductor.yml` runs on its 10-minute schedule (GitHub only schedules the default branch).
2. Confirm the `data-archive` branch keeps receiving commits (`git log origin/data-archive`), and that
   `STATUS_capture.json` / `STATUS_context.json` there are fresh.
3. On the first preseason day, open the latest `slates/latest/slate.md` on `data-archive`: every game should show
   `CANNOT_TRUST_INPUTS` with the reason "preseason" — that is correct behaviour (systems validation only).
4. After the first regular-season games: check `STATUS_settle.json` (n_new_settlements > 0, disagreements empty)
   and `eval/report.md` on `data-archive`.

## Triggering jobs from a non-default branch
Push a `.trigger/<job>` file (contents are ignored except for the conductor, where the file may list forced jobs,
e.g. `capture,context`): `probe`, `history`, `kalshi_history`, `conductor`. Each workflow also has
`workflow_dispatch` once it exists on the default branch.

## Local commands
```
nba discover  --out data/catalog                       # rebuild the market catalog from Kalshi
nba capture   --out data/archive --orderbook           # one immutable market snapshot
nba context   --out data/archive                       # schedule / injuries / rosters snapshot
nba simulate  --data data --out data/archive --date YYYY-MM-DD
nba settle    --data data --out data/archive
nba evaluate  --data data --out data/archive
nba history   --out data/history --seasons 2025-26     # ESPN box scores (resumable)
nba kalshi-history --out data/history --candles        # Kalshi settled markets + candles
python scripts/build_player_identity.py <rosters.jsonl.gz>   # refresh Kalshi uuid -> ESPN id aliases
python scripts/market_map.py                           # regenerate docs/KALSHI_MARKET_MAP.md
python -m nba_edge.research.calibrate_sim | walk_forward | prop_walk_forward | minutes_study | player_dist_study | market_calibration
```
`data/archive` is git-ignored on code branches; point `--out` at a checkout of `data-archive` to append to the real archive.

## Environment variables
None required. Optional (see `.env.example`): `KALSHI_BASE_URL`, `KALSHI_HISTORICAL_BASE_URL`, `ODDS_API_KEY`,
`NBA_EDGE_DATA_ROOT`, `NBA_EDGE_CACHE_ROOT`, `NBA_EDGE_LOG_LEVEL`.

## Onboarding a new Kalshi market family
Discovery reports it under UNRESOLVED in `data/catalog/discovery_summary.md`. Add a family (or a `series_patterns`
regex) to `data/catalog/market_ontology.yaml` with a conservative support state, extend `kalshi/contracts.py` if the
strike shape is new, add a fixture from the real market to `tests/test_contracts_real.py`, and only then consider
PRICED. `tests/test_ontology.py` fails if any discovered series is unmapped.

## Promoting authority
Never by hand from backtests. `evaluation/authority.py` computes per-family stages from prospective, pregame,
settled predictions (`eval/report.json` → `authority`). Thresholds there are placeholders to revisit once a few
hundred settled predictions exist per family.

## Archive hygiene
`Ledger.verify()` runs before every archive push. Files are never rewritten; a manifest line per file with sha256.
Expect ~5 MB/day compressed in season. When the branch passes ~1 GB, compact day partitions to Parquet in an
external bucket (not built yet).
