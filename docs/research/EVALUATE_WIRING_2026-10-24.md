# `nba evaluate` has evaluated nothing since it was wired in — evidence and fix

Date: 2026-10-24 · scope: research reporting only (the evaluation ledger/report; nothing here feeds a bet, a price or an authority gate).

## What was wrong

`nba evaluate --out X` treats **X as the ledger root**: it reads `X/predictions`, `X/settlements`, `X/context/schedule`, `X/kalshi/markets*`,
and writes `X/eval/report.json`, `X/STATUS_evaluate.json`. Both the capture worker (`worker/run.py::SLOW_JOBS`) and `conductor.yml` called it with
`--out data/archive/eval`, i.e. an **empty directory one level below the ledger**.

Archive `data-archive` @ `9523c12` (2026-10-24T06:34:48Z), measured read-only:

| | production (as wired) |
|---|---|
| `eval/eval/report.json` (`evaluated_at` 2026-10-23T23:28:06Z) | `n_rows 0`, `n_pregame 0`, `skipped {0,0,0}`, `authority {}` |
| settled tickers on the archive (`settlements`) | 18,231 (YES 5,765 / NO 8,492 / UNSETTLEABLE 3,974 rows) |
| prediction tickers on the archive | 29,571 (18,231 of them settled) |
| `STATUS_evaluate.json` location | `eval/STATUS_evaluate.json` — `evidence_health` reads `<archive>/STATUS_evaluate.json`, so the dashboard also said "evaluate has not run" |

It looked healthy because 0 rows is indistinguishable from "nothing settled yet" and the job exits 0.

## Before / after (same archive, scratch copy, `nba evaluate --out <ledger root>`)

| | before | after |
|---|---:|---:|
| evaluation rows | 0 | 228,190 (216,132 predictions skipped: not yet settled) |
| first-run wall time | n/a (no work) / 518 s with the old full-archive market pass | **159 s** |
| steady-state rerun (0 new rows) | — | **39 s** |
| row-for-row result vs the old pass over every tick | — | identical counts and DATA_ONLY Brier 0.2113 / log loss 0.6454 |

Also fixed in the same change (evaluate only):
* the closing price read the bare `yes_bid`/`yes_ask` keys; boards since the API moved to dollar strings carry them only under `_quote_cents`, so every closing
  quote was `None`. `_slim` now falls back to `_quote_cents` (Kalshi's own closing calibration in `eval/market_only.json` becomes computable).
* the market pass visited every tick of the archive (2,336 ticks x ~7,000 rows = 16.4 M row visits, 211 s just to walk it, linear in archive size) to find ONE
  observation per ticker. It now reconstructs the closing board once per distinct tip and only for newly evaluated rows; a ticker absent from the last pre-tip board
  (a briefly paused market) is searched back up to 12 ticks and keeps its own observation timestamp.
* `run_evaluate` refuses `--out <archive>/eval` (exit 2) so the mistake cannot silently recur.

## What the numbers do NOT show

Plumbing proof only. The 228k rows are repeated simulate passes over the same ~18k tickers (about 12 passes per ticker), so they are neither independent nor a
sample of games; the authority stage `SHADOW` on every family is what the existing ledger arithmetic yields from these rows and **nothing consumes it**
(`predictions` rows are still written with `"authority": "RESEARCH"`).

DATA_ONLY, pregame rows, pooled over passes (Brier / log loss / ECE):

| family | rows | brier | log loss | ECE | mean p | mean y |
|---|---:|---:|---:|---:|---:|---:|
| game_spread | 41,400 | 0.2561 | 0.7585 | 0.1601 | 0.368 | 0.310 |
| game_total | 35,192 | 0.2013 | 0.5902 | 0.0380 | 0.482 | 0.506 |
| game_winner | 3,124 | 0.3079 | 0.9120 | 0.1739 | 0.500 | 0.500 |
| period_spread | 29,655 | 0.1953 | 0.5744 | 0.0152 | 0.302 | 0.299 |
| period_total | 29,539 | 0.1755 | 0.5283 | 0.0412 | 0.449 | 0.455 |
| period_winner | 6,334 | 0.2382 | 0.6711 | 0.0533 | 0.486 | 0.500 |
| team_total | 12,350 | 0.1797 | 0.5312 | 0.0486 | 0.436 | 0.426 |
| player_points | 11,950 | 0.2389 | 0.8617 | 0.1234 | 0.340 | 0.405 |
| player_rebounds | 13,264 | 0.2136 | 0.6878 | 0.1018 | 0.411 | 0.486 |
| player_assists | 10,614 | 0.1723 | 0.5249 | 0.0788 | 0.299 | 0.338 |
| player_threes | 14,546 | 0.1717 | 0.5336 | 0.0635 | 0.305 | 0.292 |
| player_pra | 5,539 | 0.3150 | 1.2494 | 0.2089 | 0.361 | 0.485 |

A Brier of 0.3079 on `game_winner` with mean p 0.500 means the DATA_ONLY moneyline probabilities are far from 0.5 on individual games and are not calibrated
(consistent with `docs/research/MONEYLINE_MODEL_VS_MARKET.md`). `p_market` is empty on every row — see below.

## Known, unfixed here: §5.14 (needs approval, changes slate output)

`workflows/simulate.py:290,321,333` read `m.get("yes_bid")` etc. from board rows that only carry `*_dollars`/`_quote_cents`. Result on the archive:

| date | prediction rows | with any market quote | `p_market` / `p_hybrid` |
|---|---:|---:|---:|
| 2026-10-03 … 2026-10-24 (20 days) | 444,322 | **0** | **0** |

So the legacy path can never compute skill-vs-market, CLV, or the HYBRID view; the paper/projection-foundation path (own market parse) is unaffected. The fix is two
lines but it **populates `p_market`, `p_hybrid`, `p_production` and the gate** in `slate.md`/`app` output, which is a change to live-facing numbers. It is therefore
deliberately NOT in this PR. It was first recorded as an out-of-scope defect in `docs/APP_EXPORT.md` / `research_export.py` (`A_DEFECT`).

## Activation / risk

* Touches `.github/workflows/conductor.yml` and `worker/run.py` → **needs your approval to merge** (the capture worker picks it up at its next handover).
* First run after merge appends ~228k rows (one-off, ~20 MB gz) to the `evaluations` ledger kind and takes ~3 minutes against a 900 s job budget; later runs ~40 s.
  `evaluate` is an OPTIONAL stream in the shift verdict: a failure is DEGRADED, never FAILED.
* Rollback: revert the PR; the extra `evaluations/` files are append-only evidence and can stay.
