# Architecture

```
                 ┌──────────────── GitHub Actions (network-capable) ────────────────┐
  Kalshi API ───►│ discover ─► catalog/ontology (data/catalog)                        │
  Kalshi API ───►│ capture  ─► kalshi/markets, kalshi/orderbooks   (append-only)     │
  ESPN + NBA PDF►│ context  ─► context/schedule, injuries, rosters (append-only)     │──► data-archive branch
  history parquet│ simulate ─► predictions, contracts, slates/{slate,packet}.{json,md}│
  ESPN summary ─►│ settle   ─► boxscores, settlements                                │
                 │ evaluate ─► evaluations, eval/report.{json,md}, authority ledger  │
                 └──────────────────── conductor decides what runs ─────────────────┘
```

## Modules (src/nba_edge)

| package | responsibility |
|---|---|
| `kalshi/` | read client (live + historical hosts), NBA discovery, ticker parser, market ontology (YAML), contract semantics, fees, historical pull |
| `identity/` | team registry (NBA ids, tricodes, alt codes), player registry with strict alias resolution, name normalisation |
| `schemas/` | pydantic models: Game, InjuryEntry, MarketSnapshot, Contract, ContractPrediction (immutable prediction row), Fill/Position |
| `data/` | cached HTTP, schedule/box score/injury adapters (ESPN, NBA CDN, official PDF), context refresh, ESPN history puller |
| `archive/` | append-only content-hashed ledger (`manifest.jsonl` + gzip JSONL partitions), market capture job |
| `features/` | point-in-time construction of `GameParams` from history + injuries + rosters (shrinkage priors) |
| `sim/` | parameters, minutes model, coherent joint engine, convergence, `SimResult` |
| `pricing/` | contract → probability from draws; ladder coherence audit |
| `execution/` | fee-aware YES/NO economics, bet-up-to, Kelly, thesis grouping, portfolio filter |
| `settlement/` | `FinalBoxScore`, fail-closed idempotent settlement engine |
| `evaluation/` | Brier/log-loss/calibration/CLV, pregame filter, authority ledger (RESEARCH→SHADOW→LIMITED→TRUSTED) |
| `workflows/` | job entry points: conductor, simulate (RUN NBA), settle, evaluate |
| `fills/` | canonical fill/position adapter for the cross-sport importer |
| `research/` | calibration, walk-forward, minutes, distribution and market-calibration studies |
| `reporting` | lives in `workflows/simulate.py` (`slate.json`, `slate.md`, `packet.json`) |

## Point-in-time discipline
- Every archive row carries `_observed_at_utc`; nothing is overwritten (`Ledger.append_rows` refuses).
- Predictions carry `predicted_at_utc`, `data_cutoff_utc`, model/sim/feature versions, `n_sims`, the market
  observation time and prices, and the ids of the snapshots used.
- Pregame labelling is done at evaluation time against the authoritative tip (`FinalBoxScore.actual_tip_utc`,
  falling back to the schedule); any observation at or after tip is dropped from pregame metrics and CLV.
- Feature construction uses `game_date_et < cutoff` (strict); preseason rows are excluded from rate estimation.

## Three views
`p_data_only` (simulator), `p_market` (Kalshi mid), `p_hybrid` (logit blend with a *prior* weight of 0.70 on the
market, recorded on every row; to be replaced by a prospectively learned weight). `p_production` = hybrid but
authority is RESEARCH for every family, so nothing is a bet recommendation yet.

## Fail-closed gates
`UNSUPPORTED` (semantics not proven / family not priced), `CANNOT_TRUST_INPUTS` (stale/missing injury report,
stale market snapshot, thin history, unknown roster), `NO_EDGE`, `OK`. `NO_EDGE` and `CANNOT_TRUST_INPUTS` are
distinct outputs by design.

## Storage
- Code branch: catalog, identity tables, small fixtures, docs, research outputs, historical parquet (tens of MB).
- `data-archive` branch (orphan, created by the conductor): all prospective observations, predictions, settlements.
  gzip JSONL partitioned by day; `manifest.jsonl` has sha256 per file and `Ledger.verify()` runs before every push.
- Expected volume: ~5 MB/day compressed in season; migrate to Parquet/object storage when it exceeds ~1 GB.

## Scheduling
`conductor.yml` runs every 10 minutes on the default branch (GitHub ignores schedules elsewhere), decides in
seconds, and only then checks out the archive and runs jobs. Off-season: a single daily futures snapshot.
