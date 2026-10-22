# Issue #53: opening-night attribution, executable T-60 shadow portfolio, matched JRM what-if

**RESEARCH ONLY.** Additive and read-only. No order, no wagering authority, no stake or router change, no deployment, no model activation (JRM / PR #47),
no production workflow dispatched or changed. `PF_EDGE_STRICT_V1`, `paper_config.json` (sha256 pinned), the forecasts, settlements, scorecards, `projection-data` and
`minutes-shadow-archive` are untouched. Everything below dated before `prospective_start_utc` is **retrospective and descriptive**; two or three
opening games are not evidence of an edge and no profitable edge is claimed.

Artifacts of the run described here (all under `research/projection_foundation/results/issue53/`, run id in `manifest.json`):
`SUMMARY.md` (the short daily/weekly page), `attribution_2026-10-20.{md,json}`, `exec_shadow.json`, `jrm_matched.json`, `manifest.json`.
Regenerate with:

```
git fetch origin projection-data minutes-shadow-archive && git fetch --filter=blob:none --shallow-since=2026-10-20T16:00:00Z origin data-archive
git archive origin/projection-data | tar -x -C /tmp/pd ; git archive origin/minutes-shadow-archive | tar -x -C /tmp/msa
cd research/projection_foundation && PYTHONPATH=../../src python -m nba.paper.study53 --archive /tmp/pd --msa /tmp/msa \
    --git-repo ../.. --out results/issue53        # offline, deterministic: same inputs -> byte-identical files
```

## What is new (one module per deliverable, all in `nba/paper/`)

| deliverable | module | notes |
|---|---|---|
| A. seven-bet attribution | `attribution.py` | reuses `evaluate.load` and the scorecard's own earliest-trade-per-thesis rule; reconciles to the archived scorecard JSON; archive paths + git commit times; no hand-entered picks |
| B. executable shadow portfolio | `exec_shadow.py` + `exec_shadow_config_v2.json` (v1.1.0 preserved) | new strategy id `PF_EDGE_STRICT_T60_EXEC_V1`; frozen protocol; global ledger; independent archive clocks; reconstruction only |
| B'. sealed pre-tip ledger | `exec_seal.py`, `scripts/exec_seal_ci.sh`, `.github/workflows/exec-shadow-seal.yml` | the only source of prospective evidence; write-once seals on branch `exec-shadow-seals`; MISSED markers; offline verification and settlement join |
| C'. exact JRM dry run | `jrm_exact.py`, `.github/workflows/jrm-exact-dryrun.yml` | full downstream engine, frozen and jrm from one capture, one board; isolated, label-gated |
| C. matched JRM counterfactual | `jrm_matched.py` | new id `PF_EDGE_STRICT_T60_EXEC_JRM_V1`; consumes the PR #45 register, never re-implements or relaxes its rules |
| run + summary | `study53.py` | `python -m nba.paper.study53` |
| tests | `tests/test_issue53_*.py`, `tests/issue53_synth.py` | synthetic world driven by the REAL engine and settlement code |

### Protocol v2.0.1 (`exec_shadow_config_v2.json`), owner decisions of 2026-10-21 on PR #54
* **Strict T-60 cut-off kept** (decision 1): a board and a forecast must be observed/generated **and committed** to their archive branches at/before the checkpoint.
  No grace window, no later horizon, no fallback to an earlier archived tick. BOS@DET stays `NO_TRADE`.
* **Sealed pre-tip ledger replaces reconstruction as the only source of prospective evidence** (decision 2, the review's finding): v1.1.0 keyed `prospective` off the
  upstream paper engine's `decided_utc`; a study run after the game could therefore label a reconstructed new-strategy portfolio prospective. v1.1.0 is kept
  byte-identical (`exec_shadow_config.json`, sha256 `4b6d8fe6...`), nothing was ever collected under it, and **nothing computed under v1.x counts**. In v2 a row built by
  `exec_shadow.prepare` is a reconstruction and `prospective` is always False (regression test: `study53.run` the day after a final game on an upstream pre-tip
  `decided_utc` creates no prospective selection). New later start: **`prospective_start_utc` = 2026-10-24T06:00Z** (v1.1.0's 2026-10-22T06:00Z lapsed without a sealing path).
  Selection rules, strategy ids and thresholds are unchanged (copied from `PF_EDGE_STRICT_V1`, never tuned). If the PR is merged and the schedule first runs after
  the start, the start must be amended again (a seal is counted only if the protocol file's commit on the default branch precedes it).
* **Exact JRM through the full engine as an isolated dry run** (decision 3), see below; the archive-scale approximation stays separately labelled.
* **v2.0.1 (second review, still before any collection and before the start): the amendments are in the protocol's `amendments` log.** Window opens checkpoint + **600 s** (was
  360 s: the measured capture lag over 150 real ticks is median 213 s, p90 357 s, **max 502 s**, so 360 s sealed some games before their own board had reached the branch);
  seal commits are created through the **GitHub Git Data API** so the commit time is GitHub's clock, not the runner's (see below); board commit times are read **by file path**
  (commit subjects differ from the file stamps by 1-3 s on ~23% of ticks); the board must be the **latest tick observed at/before the checkpoint in the final archive**
  (`NOT_LATEST_TICK_AT_CHECKPOINT`), the tip unchanged since the seal, no seal modified/deleted/duplicated after being added. No rule, threshold or strategy id changed; the
  start stays 2026-10-24T06:00Z.

Rules of the executable portfolio (unchanged from v1): one checkpoint per game (a missing / stale / after-checkpoint / not-yet-archived board is `NO_TRADE` for the whole
game); side-specific ask (NO = 1 - YES bid, size = YES bid size), displayed size >= order, sampled-order-book conflict blocks (`DEPTH_CONFLICT_ORDERBOOK`), 1 cent
slippage, whole-order cent-rounded fee in the *entry* EV as well as in settlement; one expression per thesis; one global chronological ledger that is never reset;
settlement is the paper system's (Kalshi result, DNP at the scalar / last fair price, fee not refunded). Evidence minimums stay 200 decisions / 40 games with a
positive lower bound under both game- and player-game-clustered bootstraps; JRM's 20-game gate is tracked separately and decided by PR #45's script.

## Sealed pre-tip ledger (`nba/paper/exec_seal.py`, `.github/workflows/exec-shadow-seal.yml`)
**What a seal is.** A read-only job runs after a game's T-60 archive cut-off + 10 minutes (measured capture lag: median 213 s, p90 357 s, max 502 s) and
at least 10 minutes before tip, evaluates the game with the frozen rules **from the raw archives, not from upstream paper-decision rows**, and appends an immutable seal to
its own branch `exec-shadow-seals` (the only branch it writes; additions only: the publisher sends only new blobs on top of the current head and aborts if an existing path would change). A seal records: strategy id, protocol sha256, code sha and
dirtiness, ref/event/run id, data refs, the market tick (observed time, commit time, gap) and the forecast ids with commit times, the decision and reasons of **every**
candidate side (hashed file), the selected decisions with prices and sizes, the exposure ledger before/after, the computation time and source hashes. Games with no board,
no forecasts, a late board commit or no tradeable contract are sealed `NO_TRADE` with the reason; a game whose window closes unsealed gets a `MISSED` marker, a red run and
an alert issue (`nba-exec-shadow-alert`) and is **never sealed late as if on time**. Games whose window opened before the ledger was first enabled are `BEFORE_ENABLED`.

**Who writes the ledger, and with whose clock.** One workflow job (`.github/workflows/exec-shadow-seal.yml`, driver `nba/paper/seal_chain.py`) holds `contents: write` and
`actions: write` (successor dispatch); the publish token is handed **only** to `nba/paper/ledger_remote.py publish` and to the successor dispatch, never to the sealing subprocesses
(tests pin this). The publisher creates the commit through the Git Data API with **no client-supplied dates** and moves the ref **fast-forward only** (`force: false`), retrying on
top of the new head if it lost a race, sends only new blobs under `seals/`, `missed/`, `ENABLED_UTC`, aborts if an existing path would change, then re-checks through the server
that the commit is on the branch (durable) and that its **server commit time precedes each seal's deadline** (otherwise exit 5: late, uncounted, red run). No step runs
`git push` or `git commit`. (An earlier draft split compute / publish into separate jobs; a long-lived chain must publish inside the loop, so the separation is by process and
token scope instead of by job.)

**What counts** (`verify_seal`, offline, post-game): body and candidate-file hashes match; protocol sha256/version match; computed inside
[start, tip - 10 min] and not before the window opened; the seal's **adding commit** (exactly one; never modified or deleted afterwards; working-tree bytes equal to that commit) has a
server commit time not before the computation and not after the deadline; the sealed board is the latest tick observed at/before the checkpoint in the final archive and the tip is unchanged; code sha reachable from the default branch (a pull-request or branch run can never be counted); protocol file committed on the default branch before the start;
independent clocks recorded; not a dry run. Anything else is listed with its reason and is uncounted. **Postgame, `exec_seal.evaluate` joins the paper settlement
(Kalshi result first, box score second, DNP at the fair price) to the counted sealed trades and never recomputes a selection**; every scheduled game appears as
SEALED_COUNTED / SEALED_UNCOUNTED / MISSED / NO_SEAL_RECORD / NOT_DUE.

**Dress rehearsal on real data (not evidence).** Running the sealer in `--dry-run` at simulated pre-tip times against the real archives reproduces the reconstruction without
reading any upstream decision row: BOS@DET `NO_TRADE` (board committed 18:02:15Z > 18:00Z), NYK@PHI `NO_TRADE` (gate/quality/depth), OKC@SAS **the same 3 contracts at the same prices**
(`results/issue53/dress_rehearsal/`). That agreement is a consistency check of the sealer, not a result.

**Cadence, cost and reliability.** The repository MEASURED its own scheduled-workflow delivery (`capture_worker.yml`: 34 runs of 864 expected, 3.9%, gaps of 2-3 h), so a 5-minute
cron cannot seal a 40-minute window reliably. The sealer is therefore a **self-renewing chain** like `capture-worker` / `nba-ticker`: one run (~280 min) polls every 90 s (about 25
attempts per window), dispatches its successor at ~250 min, and ends when nothing is open, closing or opening within 6 h; cron (`*/5`, UTC 12:00-03:55, season months) is only the
bootstrap, and a cron delivered while the chain is running queues as its natural successor (one live concurrency group; rehearsals have their own). **Idle cost:** a delivered
cron runs a stdlib-only gate (depth-1 blobless fetch of the capture branch ~1 s + 0.1 s of Python, no `setup-python`, no `pip install`; the old design installed ~690 MB 144 times a day);
dependencies are installed once per chain and only when a window is open or within 6 h. A game day costs roughly one chain of runner time from ~6 h before the first window to the last
window, comparable to the existing long-lived workers; an off day costs nothing but delivered crons' ~15 s. Fail-closed: a missed window gets a MISSED marker and a red run, is
uncounted and never sealed late. **Dead-man:** the existing `nba-watchdog` (opens the `nba-ops-alert` issue) now also evaluates `nba/paper/seal_monitor.py`: CRITICAL when a window is
open or opens within 45 min and no run of the workflow is queued / running / finished within 20 min (`SEAL_CHAIN_DEAD`), when a window closed 10+ min ago with neither a seal nor a MISSED
marker (`SEAL_UNMARKED_WINDOW`), and on any MISSED marker in the last 36 h (`SEAL_MISSED`). Residual risk, stated plainly: the watchdog is itself a cron workflow (`12,42 * * * *`), so
a platform-wide scheduler outage would silence both; there is no second platform. Expected loss of games to archive lag: the last tick before T-60 is committed in time only when it was observed more than its lag (median 213 s) before the checkpoint, so a large share of games is `NO_TRADE` by construction: in the retrospective application **6 of the 8 games already due** (088, 091, 834-837) fail only because their T-60 board was committed 203-220 s after the checkpoint. That slows the 200-decision / 40-game
target and is the price of the strict rule; every seal records the tick gap and commit margin so this can be quantified without any change to the rule.

**Safe proposed cadence.** (1) Merge (approved); the first live chain stamps `ENABLED_UTC` and publishes it. (2) 2026-10-22..23: burn-in (seals are produced and verified but, by the
start rule, uncounted). (3) Run `python -m nba.paper.study53 --seals <ledger checkout> --context ... --market ... --code-repo ...` any morning for the daily page; weekly for the report.
(4) Before 2026-10-24T06:00Z confirm in the burn-in that games show SEALED_UNCOUNTED with only BEFORE_PROSPECTIVE_START as the reason, then the start stands; otherwise amend it.

## Exact JRM dry run (`nba/paper/jrm_exact.py`, `.github/workflows/jrm-exact-dryrun.yml`)
PR #45's opt-in engine (`project_slate(minutes_engine="jrm")`) is run **in one process on one capture** (the production `stage_project` is called twice with
`PF_NBA_MINUTES_ENGINE` set per call; same slate, availability, calibration, clock), so usage, participation, reconciliation and publisher gates are the engine's own.
Both result sets are converted to forecast records exactly as the live pipeline does and priced on the **same Kalshi board** with the **same strict rules**; the report
compares engine diagnostics (gate counts, teams normalised, team sum of p x minutes), the per-player minutes / P(play) table (written so it can be scored when the games
finish), and the matched market selections contract by contract. Isolation: `contents: read` only, no secrets or push step, every data branch mounted read-only and a
throw-away copy used, PR #45 merged only inside the runner at a pinned SHA (fails if the branch moved), runs only on manual dispatch or a PR carrying the label
`jrm-exact-dryrun`, 40-minute timeout, never scheduled. Tests inject stub engines; guards on the workflow files are tests too.

## Findings (retrospective, descriptive)
Section A and the OKC@SAS numbers were fixed on the opening-night archive state and do not change. The regenerated `results/issue53/` (run `f4f7ab85a666eebb`, archive state fetched
2026-10-22) now also covers the games that were played since (091, 834-837 are due; 838+ are `NOT_DUE`); the figures quoted below say which state they come from.

### A. The seven opening-night bets
* Reproduced exactly: **7 decisions, 2 games, net P&L $1.39, entry cost $3.40 (sum of quoted asks), ROI 40.882%**; matches the archived scorecard and the
  issue text. (On cash outlay incl. slippage and fees: $3.47 entry, ROI 38.5%.)
* **6 of 7 are as-of replays, only 1 is contemporaneous.** The six (all T-90) were *computed* 51-90 minutes after the price they use (`decided_utc` vs
  `as_of_utc`; the OKC@SAS rows at 01:22:50Z, seven minutes before tip, for a 23:53Z board). The only contemporaneous trade is the Duren PRA YES (LIVE,
  board 382 s old) and it supplies **37% of the headline P&L** ($0.52 of $1.39); the six replay rows make $0.87 (ROI 29.5%).
* **No fill evidence for any row.** Actionability check against the latest contemporaneous board that existed when each replay row was computed: five
  asks moved by 0-1 cent, but **Cunningham PRA NO: $0.52 at T-90 vs $0.91 at 18:12Z (EV -0.16)**, i.e. the selected price had gone.
* Each thesis was traded at the earliest of 3-4 horizons; the horizons are alternative runs with separately reset caps, so the seven are not a portfolio.
* Structure: NO 6 (+$0.87) / YES 1 (+$0.52); points 4, PRA 2, threes 1 (all points-based); 5 player-games in 2 games, Cunningham (points+PRA) and
  J. Williams (points+threes) each carry two contracts on one outcome; without the largest winner net P&L is $0.87. Capture-branch commit lag of the boards:
  192-211 s (none was committed after its row was decided).

### B. Executable fixed-checkpoint (T-60) portfolio, rules applied retrospectively
* **3 trades in 1 game** (OKC@SAS): $0.46 net P&L, ROI on cash outlay 29.9%, 2 of 3 wins, CLV +0.33c mean (3 valid). **No interval is defined (< 5 games);
  status `INSUFFICIENT_SAMPLE`; prospective: `NO_DATA` (0/200 decisions, 0/40 games).**
* **BOS@DET (088) is `NO_TRADE`**: its T-60 board (observed 17:58:51Z) reached the capture branch at 18:02:15Z, after the 18:00:00Z checkpoint. Without
  the independent-clock rule the same frozen rules would trade 6 contracts in 2 games for $0.83 on that evening, and **21 contracts in 5 games (net $0.83) over all 8 games due so far**: 6 of those 8
  games (088, 091, 834-837) are `NO_TRADE` only because their T-60 board reached the capture branch 203-220 s after the checkpoint. The rule is the issue's "generated AND archived before the
  decision" applied to the market side; it decides outcomes here only by 2 minutes of archive latency, which is itself a finding (3.4 min typical lag).
* **NYK@PHI (089) is `NO_TRADE`**: 512 sides blocked by the PASS-only gate, 85 by quote-quality, 21 by order-book depth conflict. The PASS-only gate fails for 1,554 of the 1,802 T-60 sides (86%). Other blockers: spread, extreme price, thin displayed size, sampled-book conflict; capped / not-best sides are listed.
* Contemporaneous cross-check at T-60: **NO_DATA** - the nearest contemporaneous run to the checkpoint was 41 / 85 / 92 minutes before tip, outside the 45-75
  minute comparison window; the replay vs live-fidelity question cannot be answered from opening night.
* Examples of `NO_TRADE` with large nominal edges and the reason each was blocked are in `exec_shadow.json` (`no_trade_examples`).

### C. Frozen vs JRM, matched (archive-scale approximation, retrospective)
* (Regenerated state: three further games matched a snapshot, but the gate still counts 1 settled eligible game.) Eligible, same-feed, pre-tip JRM snapshots exist for **one** settled game (OKC@SAS, snapshot `20261021T000501Z`, feed 23:56:30Z, archived 00:05:01Z, commit
  00:05:21Z). `jrm_v1/` and `jrm_v2/` (variance-weighted) are rejected (`REGISTER_NOT_ELIGIBLE`); BOS@DET and NYK@PHI predate any JRM snapshot
  (`NO_SNAPSHOT_FOR_GAME`). **JRM gate: 1 / 20 eligible settled games -> `INSUFFICIENT_SAMPLE`; no promotion and no conclusion.**
* Same candidate rows, same ledger order (regenerated state, 4 matched games, 1 settled): V1-only 2, JRM-only 2, both 1, neither 2,427. On the 1,616 covered sides JRM minutes are on
  average 7.6% higher than the frozen published minutes; mean change in P(NO) +0.0007 (opening-night state: 416 sides, +8.2%, -0.011). Settled P&L of the contracts only V1 took: +$0.11; only JRM took:
  +$0.18; both: +$0.35. One game: no inference.
* Of the original seven, 3 (the OKC@SAS rows) had an eligible matched snapshot at their T-90 decision. JRM raises minutes for all three (J. Williams
  26.5 -> 29.4, SGA 33.6 -> 35.0), EV net falls 0.133 -> 0.076 and 0.156 -> 0.112 for the two points rungs and stays ~0.166 for the threes rung; all three would
  still clear the 0.06 bar in this approximation. **"Artificial star unders" is a hypothesis with no support yet**: the only directional pattern (JRM minutes above
  frozen for the NO bets) is 3 of 3 rows from one game; the diagnostic prints the rule for what would count as evidence.
* Matched minutes accuracy (one game, 27 played): conditional MAE JRM 4.95 vs frozen 6.10; P(play) Brier JRM 0.067 vs frozen 0.049 (worse); rung Brier
  mixed by family. All intervals undefined at one game. The Gaussian CRPS is explicitly approximate.

## Outstanding risks and limits
1. **Sample.** 2-3 retrospective games, 0 prospective. Nothing here supports value or JRM promotion.
2. **JRM downstream is an approximation** (`p_ge(scale=r)` on the archived frozen pmf). Rates, usage redistribution and the participation gate are not re-estimated; the real test needs `PF_NBA_MINUTES_ENGINE=jrm` on the live feed (the isolated workflow exists; not yet run).
3. **Archive latency.** Boards are committed ~3.4 min after observation; whether a T-60 game is tradeable can hinge on that. The rule is frozen as written;
   changing it (e.g. a 6-minute margin on the checkpoint) is a new protocol version, not a patch.
4. **Replay vs live.** The primary checkpoint runs only exist as as-of replays (computed after the fact, within the information rules). Genuinely contemporaneous coverage near T-60 was absent on opening night.
5. `depth_at_entry` is optional evidence; 53 sides show size on the board but 0 at the ask in the sampled book (treated as a conflict, not a fill).
6. Fee model uses the series multiplier from the board row; DNP outcomes settle at `modeled_last_valid_mid` until an authoritative scalar is archived (none occurred).
7. `board_commit_index` is path-based (the commit that added the tick's file) and only covers the fetched history depth; ticks outside it are `BOARD_ARCHIVE_UNVERIFIED`.
8. JRM eligibility is the PR #45 register; this study additionally requires both snapshot clocks >= 5 minutes before the decision instant, the same feed as the frozen decision, and an identical rebuilt frozen probability (otherwise the player is `FROZEN_INPUT_MISMATCH`, not a JRM effect).
9. Scope: the seal workflow is schedulable only from the default branch, i.e. after your merge; nothing runs before. The exact-JRM dry run needs network and the PR #45 code, so it runs only in Actions (label `jrm-exact-dryrun` or manual dispatch); the harness is tested here with stub engines only.
10. The Git Data API publication path, the 5-minute cron's real delivery rate and the real capture lag at seal time can only be observed after merge (burn-in).
