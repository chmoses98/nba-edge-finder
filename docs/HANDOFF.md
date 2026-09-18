# NBA Edge Finder — overnight foundation build handoff (2026-09-18)

Branch: `claude/nba-edge-finder-foundation-h2csoj` (PR opened against `main`). Archive branch: `data-archive`.
Nothing here is a bet recommendation: **every market family is in RESEARCH authority.**

## A. Executive summary

What now exists is a working, tested, automated pipeline from Kalshi discovery to calibration, with real data in it:

- The whole Kalshi NBA universe is discovered programmatically (256 NBA series, 5,552 live markets scanned; 14,154
  series enumerated on the exchange) and every series maps to a family with an explicit support state — zero
  UNRESOLVED. Coverage is an audited invariant (`docs/KALSHI_MARKET_MAP.md`).
- Prospective, append-only, hash-verified capture is live on the `data-archive` branch: three Kalshi snapshots of
  2,818 active NBA markets with normalised quotes and order books, plus ESPN schedule/rosters and injury snapshots.
- A historical research base exists on the code branch: 137,059 settled 2025-26 Kalshi NBA markets (game, spread,
  total, team total, first-half, player points/rebounds/assists/threes, win totals) and 3,931 ESPN box scores
  (2023-24..2025-26, 105,891 player-game rows).
- A coherent joint Monte Carlo game simulator (availability → minutes → possessions → opportunity → efficiency →
  bottom-up team scores → OT → quarters → rebounds/assists/steals/blocks/turnovers) prices every PRICED contract
  from the same draws, with convergence-driven draw counts and 14 enforced invariants.
- Fee-aware YES/NO economics, bet-up-to, thesis grouping with simulated correlations, fail-closed gates that
  distinguish NO_EDGE from CANNOT_TRUST_INPUTS, immutable prediction rows carrying model/sim/feature versions,
  idempotent fail-closed settlement, pregame-filtered evaluation with CLV and a granular authority ledger.
- Research on real data already corrected several priors (margin sd is 16, not 13.5; EWM half-life 5 minutes
  beat season averages; negative binomial beats Poisson and still under-predicts the points upper tail) and
  produced an honest negative result: the v1 DATA_ONLY win probabilities lose to a plain Elo.

## B. Repository state

- 18 commits on the feature branch; CI (ruff + pytest) green on every push.
- Tests: 252 collected (unit, integration, hypothesis property tests), ~60 s.
- Workflows: `ci.yml`, `probe.yml` (discovery), `history.yml` (ESPN dataset), `kalshi_history.yml` (Kalshi
  archive + candles), `conductor.yml` (10-minute scheduler: context, capture, simulate, settle, evaluate, daily
  discovery, archive push). Schedules only fire on the default branch; on this branch jobs are triggered by pushing
  `.trigger/<name>` files (that is how everything ran tonight).
- Key packages: `kalshi/` (client incl. historical host, discovery, ontology YAML, ticker parser, contract
  semantics, dollar→cents normaliser, fees, history), `identity/`, `schemas/`, `data/` (ESPN, NBA CDN, official
  injury PDF, context refresh, history puller), `archive/` (ledger, capture), `features/` (point-in-time builder
  with opponent-adjusted ratings), `sim/` (engine, minutes, convergence, season sim interface), `pricing/`,
  `execution/`, `settlement/`, `evaluation/`, `workflows/` (conductor, simulate, settle, evaluate), `fills/`,
  `research/`.

## C. Kalshi market map

Discovery (live API, off-season): 256 NBA-related series. Under the ontology (v2026.09.18.2): PRICED 9 series,
BUILDABLE 53, RESEARCH 82, UNMODELABLE 112, UNRESOLVED 0. Live markets on 2026-09-18: 2,818 active (6 opening-night
game winners, 312 win totals, futures/awards/all-NBA/transactions dominate the rest).

Historical (2025-26 season, settled): KXNBAPTS 23,562 · KXNBAREB 22,656 · KXNBAAST 17,745 · KXNBASPREAD 16,937 ·
KXNBA3PT 16,619 · KXNBATOTAL 14,787 · KXNBATEAMTOTAL 9,486 · KXNBA1HSPREAD 5,823 · KXNBA1HTOTAL 4,707 · KXNBAGAME
2,898 · KXNBA1HWINNER 1,569 · KXNBAWINS 270 · KXNBAPRA 0 (series exists but had no markets).

Families and states: game_winner/spread/total/team_total and player pts/reb/ast/3pt/PRA are PRICED (semantics
proven against real markets with high confidence; tests in `tests/test_contracts_real.py`); quarters/halves, win
margin, OT, steals/blocks/turnovers, PR/PA/RA, double/triple-double, head-to-head, parlays are BUILDABLE; futures,
series props, first basket, race-to-X, starting lineups, season specials are RESEARCH; awards, draft, all-NBA
teams, transactions, franchise/business, all-star events are UNMODELABLE.

Verified semantics: spreads/totals/team totals use `strike_type=greater` with half-point `floor_strike`; player
props use `strike_type=structured` with `floor_strike` and stable player/team UUIDs; halves/quarters exclude OT;
player props settle `scalar` (pre-game fair value) when a player never enters (4.3% of PTS markets); prices are
dollar strings (`yes_bid_dollars`) on both live and historical hosts; `close_time` is not tip time.

## D. Data sources

Probed from GitHub Actions (`docs/probe/probe_results.md`, `docs/NBA_DATA_SOURCE_AUDIT.md`):
- Working and used in production: Kalshi live + historical APIs; ESPN site API (scoreboard by date, summary box
  scores, injuries, teams, rosters); official NBA injury-report PDF (`ak-static.cms.nba.com`).
- Reachable but not depended on: Basketball-Reference (terms/rate limits), pbpstats API (undocumented), Rotowire
  lineups (HTML).
- Blocked from cloud runners: `cdn.nba.com` (403), `stats.nba.com` (timeout, known cloud-IP block). Adapters exist
  for local runs; a self-hosted runner or proxy would unlock them.
- The build sandbox itself had no access to any sports host; everything network-related was executed in Actions.

## E. Simulation

See `docs/SIMULATION.md`. Linked together in one draw: possessions (shared by both teams), team efficiency
targets with rating uncertainty, availability (questionable = 0.5), starters, water-filled minutes (240 + 25/OT)
that redistribute when players are out, team FGA from possessions split by minutes-weighted rates (usage
redistributes), 3PA/2PA/FTA per player, makes with shared game-environment and team shocks, team points = sum of
player points, near-tie inflation to the empirical OT rate and OT periods with a closing lineup, Dirichlet
quarter split, blowout production transfer starters→bench tied to the realised margin, small endgame
compression, rebounds from misses, assists from makes, turnovers/steals/blocks. Convergence stops when the max
Monte Carlo SE over Kalshi-relevant probabilities ≤ 0.004 (min 20k draws).

Calibrated to 2023-26 data: margin sd 16.4 (emp. 16.0), total sd 20.3 (20.0), team sd 13.1 (12.2–12.8),
home/away corr 0.21 (0.22), OT 4.9% (4.8%), blowouts 29% (26%).

Crude: independent availability across players; quarter split ignores rotation timing; multinomial shares are
under-dispersed for rebounds/assists; OT lineup = five highest-minute players; endgame compression is a hack;
rest/b2b effect is a literature prior (−2 pts/100), not yet estimated from our data; `usage_elasticity` unused.

## F. Historical research (docs/research/RESEARCH_NOTES.md)

Dataset: 3 seasons ESPN (3,931 games) + 137k settled Kalshi markets. Completed walk-forward tests (strict
point-in-time, 300 late-2025-26 games):
- DATA_ONLY v1: log loss 0.569 / Brier 0.190 / ECE 0.187 vs Elo 0.500 / 0.162 / 0.078 vs constant 0.675.
  **Negative result.** Diagnosis: the sim's expected margins were far too compressed (spread across games 5.1
  pts vs 8.5 implied by Elo; realised margin regresses on sim margin with slope 2.1) — over-shrunk ratings.
  Margin MAE still beat naive (12.6 vs 14.3), total MAE 15.3 vs 16.0.
- Retuned dispersion + opponent-adjusted ratings (v2): calibration of intervals fixed (80% band covers 81%), win
  probabilities still under-confident; a shrinkage sweep (half-life 25/40/60, prior 4/2/1 games) is recorded in
  `docs/research/wf_hl*_p*.json` — see the appended results at the bottom of this file.
- Minutes: EWM half-life 5 is the best next-game minutes estimator (MAE 4.96; season mean 5.39; residual sd 6.4).
- Distributions: negative binomial ≫ Poisson for points (log score −3.22 vs −3.78); points upper tail P(>mu+5) is
  17.5% empirically vs 13.6% NB — fat tails matter for ladders.
- Market calibration: first attempt invalid (post-tip quotes); candle-based pregame calibration wired, pending the
  candle commit + tip-time join.

## G. Automation

Conductor (every 10 min once on the default branch): context refresh when a game is within 30 h or every 6 h,
capture when a game is within 36 h (plus a daily futures snapshot off-season), simulate when a game tips within
26 h and the last sim is > 55 min old, settle when games finished in the last 36 h, evaluate after settlement or
daily, discovery daily. Off-window wakes exit in ~30 s. Manual today: merging to `main` (to enable schedules),
seeding `.trigger/*` files on a branch, promoting authority stages.

## H. Prospective capture — proof

`data-archive` branch, `manifest.jsonl` (15 entries, sha256 each, `Ledger.verify()` passes before every push):
`kalshi/markets/dt=2026-09-18/kalshi_markets_20260918T073603Z_35320111760.jsonl.gz` (2,818 rows),
`..._20260918T074007Z_...`, `..._20260918T074802Z_...` (with `_quote_cents`, e.g. KXNBAGAME-26OCT20OKCSAS-SAS
yes 53/56), `kalshi/orderbooks/...` (raw `orderbook_fp` bodies; level parsing fixed in the last commit),
`context/injuries` (75 ESPN rows; official PDF absent off-season), `context/rosters` (560), `context/schedule` (0
rows: no games in the next 10 days).

## I. Settlement

Automatic: game winner/spread/total/team total (incl. OT), halves/quarters (OT excluded), player pts/reb/ast/3pm/
stl/blk/tov, PRA/PR/PA/RA, double/triple-double — from ESPN summary box scores, idempotent by
(ticker, game, engine version, stat-correction version), with Kalshi's own result recorded and disagreements
flagged. Not automatic (fail closed): DNP/`scalar` settlements without a Kalshi result, postponed/cancelled
games, ties in period markets, any contract whose semantics are not proven, and player contracts until the
Kalshi-name → ESPN-id resolution is confirmed for that player.

## J. Model authority

RESEARCH for every family. Nothing has SHADOW/LIMITED/TRUSTED. Promotion requires prospective, pregame,
settled evidence per family (thresholds in `evaluation/authority.py` are placeholders).

## K. Risks / blockers

1. Player identity across Kalshi ↔ ESPN is name-based (unique normalised match within the game's two rosters);
   Kalshi UUIDs are captured but not yet mapped to ESPN ids. Ambiguities fail closed.
2. NBA.com endpoints are blocked from cloud runners; production depends on undocumented ESPN endpoints.
3. The HYBRID weight (0.70 market) is a prior, not learned.
4. Order-book capture prioritises by expiration; in season it must prioritise game markets (trivial change).
5. Historical quarter line scores were zero in the first pull (parser fixed; re-pull in progress at handoff).
6. Archive growth (~5 MB/day in season) will eventually need Parquet compaction / object storage.
7. Off-season: no game contexts have been exercised end-to-end against live data; the first preseason games
   (2026-10-03) are the systems test.

## L. Next 10 highest-value tasks

1. Fix rating shrinkage from the sweep, then full-season walk-forward (2024-25, 2025-26) vs Elo and vs Kalshi
   pregame candles; learn the HYBRID weight prospectively.
2. Candle-based pregame market calibration + CLV baseline per family; make `kalshi_history` pull candles for all
   game/spread/total markets (budget permitting) and player props at primary lines.
3. Kalshi player UUID ↔ ESPN athlete id registry from the 100k+ historical prop titles; promote to durable aliases.
4. Player-prop walk-forward: simulate historical games, price the settled ladders, evaluate by threshold distance.
5. Merge to `main` so the conductor schedule runs; watch the first preseason slate end to end.
6. Estimate rest/b2b, home-court and pace effects from the dataset (replace literature priors).
7. Period (1Q/1H) dispersion calibration → promote period families to PRICED if calibrated.
8. Correlated availability and starter-lineup confirmation from the official injury report near tip.
9. Season simulator wiring (remaining schedule from ESPN, ratings) → win totals / playoff qualification BUILDABLE→PRICED.
10. Portfolio sizing that respects the thin player-prop books (median volume ~400–1,100 contracts).
