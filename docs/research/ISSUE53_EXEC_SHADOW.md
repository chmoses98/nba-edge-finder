# Issue #53: opening-night attribution, executable T-60 shadow portfolio, matched JRM what-if

**RESEARCH ONLY.** Additive and read-only. No order, no wagering authority, no stake or router change, no deployment, no model activation (JRM / PR #47),
no workflow dispatched. `PF_EDGE_STRICT_V1`, `paper_config.json` (sha256 pinned), the forecasts, settlements, scorecards, `projection-data` and
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
| B. executable shadow portfolio | `exec_shadow.py` + `exec_shadow_config.json` | new strategy id `PF_EDGE_STRICT_T60_EXEC_V1`; frozen protocol; global ledger; independent archive clocks |
| C. matched JRM counterfactual | `jrm_matched.py` | new id `PF_EDGE_STRICT_T60_EXEC_JRM_V1`; consumes the PR #45 register, never re-implements or relaxes its rules |
| run + summary | `study53.py` | `python -m nba.paper.study53` |
| tests | `tests/test_issue53_*.py`, `tests/issue53_synth.py` | synthetic world driven by the REAL engine and settlement code |

### Protocol freeze (`exec_shadow_config.json`)
Study `ISSUE53_EXEC_SHADOW_V1`, declared 2026-10-21T21:35Z, **`prospective_start_utc` 2026-10-22T06:00Z**. The independent timestamp of the protocol is the
git push time of the commit that adds the file; a decision is prospective only if its checkpoint is at/after the start *and* that push precedes it.
Numeric thresholds are copied verbatim from `PF_EDGE_STRICT_V1` (EV >= 0.06, PASS only, p_play >= 0.85, spread <= 0.06, same caps); nothing was tuned on
October 20/21. The only new numbers are the executability parameters decided before anything was scored: checkpoint T-60, `max_quote_age_s` 900 (the
existing closing-line constant), displayed size >= 1 contract. Evidence minimums stay 200 decisions / 40 games with a positive lower bound under both game-
and player-game-clustered bootstraps; JRM's 20-game gate is tracked separately and decided by PR #45's script.

Rules of the executable portfolio: one checkpoint per game (a missing/stale/after-checkpoint/not-yet-archived board is `NO_TRADE` for the whole game; no other
horizon is substituted); board **and** forecast must be observed/generated **and archived** (self-reported clock, and the git commit time of the capture /
forecast file as an independent clock) at or before the checkpoint; side-specific ask (NO = 1 - YES bid, size = YES bid size), displayed size >= order,
sampled-order-book conflict blocks (`DEPTH_CONFLICT_ORDERBOOK`), 1 cent slippage, whole-order cent-rounded fee in the *entry* EV as well as in settlement;
one expression per thesis; one global chronological ledger (player-game, team-game, game, game notional, day notional, thesis) that is never reset;
settlement is the paper system's (Kalshi result, DNP at the scalar / last fair price, fee not refunded).

## Findings (retrospective, descriptive; archive state `projection-data` 8ce75b5, `minutes-shadow-archive` c38f874)

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
  the independent-clock rule the same frozen rules would trade 6 contracts in 2 games for $0.83. The rule is the issue's "generated AND archived before the
  decision" applied to the market side; it decides outcomes here only by 2 minutes of archive latency, which is itself a finding (3.4 min typical lag).
* **NYK@PHI (089) is `NO_TRADE`**: 512 sides blocked by the PASS-only gate, 85 by quote-quality, 21 by order-book depth conflict. The PASS-only gate fails for 1,554 of the 1,802 T-60 sides (86%). Other blockers: spread, extreme price, thin displayed size, sampled-book conflict; capped / not-best sides are listed.
* Contemporaneous cross-check at T-60: **NO_DATA** - the nearest contemporaneous run to the checkpoint was 41 / 85 / 92 minutes before tip, outside the 45-75
  minute comparison window; the replay vs live-fidelity question cannot be answered from opening night.
* Examples of `NO_TRADE` with large nominal edges and the reason each was blocked are in `exec_shadow.json` (`no_trade_examples`).

### C. Frozen vs JRM, matched (archive-scale approximation, retrospective)
* Eligible, same-feed, pre-tip JRM snapshots exist for **one** settled game (OKC@SAS, snapshot `20261021T000501Z`, feed 23:56:30Z, archived 00:05:01Z, commit
  00:05:21Z). `jrm_v1/` and `jrm_v2/` (variance-weighted) are rejected (`REGISTER_NOT_ELIGIBLE`); BOS@DET and NYK@PHI predate any JRM snapshot
  (`NO_SNAPSHOT_FOR_GAME`). **JRM gate: 1 / 20 eligible settled games -> `INSUFFICIENT_SAMPLE`; no promotion and no conclusion.**
* Same candidate rows, same ledger order: V1-only 2, JRM-only 2, both 1, neither 615 (607 blocked in both). On the 416 covered sides JRM minutes are on
  average 8.2% higher than the frozen published minutes; mean change in P(NO) -0.011. Settled P&L of the contracts only V1 took: +$0.11; only JRM took:
  +$0.18; both: +$0.35. One game: no inference.
* Of the original seven, 3 (the OKC@SAS rows) had an eligible matched snapshot at their T-90 decision. JRM raises minutes for all three (J. Williams
  26.5 -> 29.4, SGA 33.6 -> 35.0), EV net falls 0.133 -> 0.076 and 0.156 -> 0.112 for the two points rungs and stays ~0.166 for the threes rung; all three would
  still clear the 0.06 bar in this approximation. **"Artificial star unders" is a hypothesis with no support yet**: the only directional pattern (JRM minutes above
  frozen for the NO bets) is 3 of 3 rows from one game; the diagnostic prints the rule for what would count as evidence.
* Matched minutes accuracy (one game, 27 played): conditional MAE JRM 4.95 vs frozen 6.10; P(play) Brier JRM 0.067 vs frozen 0.049 (worse); rung Brier
  mixed by family. All intervals undefined at one game. The Gaussian CRPS is explicitly approximate.

## Outstanding risks and limits
1. **Sample.** 2-3 retrospective games, 0 prospective. Nothing here supports value or JRM promotion.
2. **JRM downstream is an approximation** (`p_ge(scale=r)` on the archived frozen pmf). Rates, usage redistribution and the participation gate are not re-estimated; the real test needs `PF_NBA_MINUTES_ENGINE=jrm` on the live feed (not run: no workflow was dispatched).
3. **Archive latency.** Boards are committed ~3.4 min after observation; whether a T-60 game is tradeable can hinge on that. The rule is frozen as written;
   changing it (e.g. a 6-minute margin on the checkpoint) is a new protocol version, not a patch.
4. **Replay vs live.** The primary checkpoint runs only exist as as-of replays (computed after the fact, within the information rules). Genuinely contemporaneous coverage near T-60 was absent on opening night.
5. `depth_at_entry` is optional evidence; 53 sides show size on the board but 0 at the ask in the sampled book (treated as a conflict, not a fill).
6. Fee model uses the series multiplier from the board row; DNP outcomes settle at `modeled_last_valid_mid` until an authoritative scalar is archived (none occurred).
7. Scope: the new modules are not scheduled anywhere; evidence accrues only when someone runs `study53` on new archive state (owner decision, see PR).
