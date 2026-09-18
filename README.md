# nba-edge-finder

NBA Kalshi market research and execution workstation.

Pipeline: data/context → game environment → player availability/minutes → opportunity/efficiency →
coherent Monte Carlo simulation → Kalshi contract probabilities → executable prices/fees → edge →
best expression → immutable archive → CLV → settlement → calibration/postmortem.

See `docs/` for architecture, data-source audit, market map, and the overnight handoff.

Quick start:

```
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest -q
nba discover --out data/catalog            # needs network (Kalshi public API)
nba capture  --out data/archive --orderbook
nba simulate --date 2026-10-21 --out out/slate
```

No credentials are required for anything in this repository today; see `.env.example`.
