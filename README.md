# nba-edge-finder

NBA Kalshi market research and execution workstation. Philosophy (mirrors the NFL system):

```
data/context → game environment → availability → minutes → opportunity → efficiency
  → coherent Monte Carlo simulation → Kalshi contract probabilities → executable prices + fees → edge
  → best expression → immutable archive → CLV → settlement → calibration / authority
```

Status (2026-09-18, overnight foundation build): infrastructure complete and running; every model family is in
**RESEARCH** authority — nothing here is a bet recommendation. On the same games the Kalshi pregame moneyline
currently beats the DATA_ONLY model (log loss 0.465 vs 0.522). See `docs/HANDOFF.md` and `docs/research/RESEARCH_NOTES.md`.

## What runs automatically (GitHub Actions)
| workflow | trigger | what |
|---|---|---|
| `conductor.yml` | every 10 min on the default branch (also `.trigger/conductor` on any branch) | decides cheaply, then: context refresh (ESPN schedule/rosters, official injury PDF), Kalshi market + order-book capture, simulate/price, settle, evaluate, daily discovery; pushes to the `data-archive` branch |
| `probe.yml` | `.trigger/probe` / manual | data-source reachability probe + full Kalshi NBA discovery → `data/catalog` |
| `history.yml` | `.trigger/history` / manual | ESPN historical box scores → `data/history/espn/*.parquet` |
| `kalshi_history.yml` | `.trigger/kalshi_history` / manual | Kalshi historical (settled) NBA markets + candles → `data/history/kalshi` |
| `ci.yml` | push / PR | ruff + pytest |

Schedules only fire on the default branch; until this branch is merged, jobs are started by pushing a `.trigger/*` file.

## Local use
```
python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
pytest -q                                   # ~250 tests incl. hypothesis property tests, ~60 s
nba discover --out data/catalog             # Kalshi NBA universe (network)
nba capture  --out data/archive --orderbook # append-only market snapshot
nba context  --out data/archive             # schedule / injuries / rosters snapshot
nba simulate --data data --out data/archive --date 2026-10-21   # RUN NBA: slate.json / slate.md / packet.json
nba settle   --data data --out data/archive
nba evaluate --data data --out data/archive
python -m nba_edge.research.walk_forward    # research scripts write to docs/research/
```
No credentials are needed for anything in this repository; see `.env.example`.

## Docs
- `docs/HANDOFF.md` — overnight handoff: what exists, evidence, risks, next tasks
- `docs/ARCHITECTURE.md` — modules, point-in-time discipline, storage, scheduling
- `docs/KALSHI_MARKET_MAP.md` — every discovered NBA series and its support state
- `docs/NBA_DATA_SOURCE_AUDIT.md` — what is reachable from cloud runners and what production depends on
- `docs/SIMULATION.md` — exactly what the simulator does and what is crude
- `docs/research/RESEARCH_NOTES.md` — findings so far, including negative results
