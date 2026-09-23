# Handoff — audit, merge, and the research that followed

Everything below is measured. `docs/PRE_MERGE_EVIDENCE.md` is generated from live state by
`scripts/evidence.py`; no figure here is transcribed by hand.

---

## A. What this session was asked to do, and what happened

Not a feature wave: audit PR #1 as if it would one day move real money, fix what was unsafe, merge
only if the gate genuinely passed, verify production from main, then do the market-vs-model research
the earlier work had not actually done.

**PR #1 is merged** (`6fa1e30`). Nine gates passed, ten blockers were found and fixed first, and the
research that followed produced a series of clear **negative** results.

**The single most important sentence in this handoff: no market family has a demonstrated edge, and
authority remains RESEARCH everywhere. Nothing here justifies a bet.**

## B. The audit: ten blockers, all fixed

Four parallel audits read the code rather than the documentation. Full evidence in
`docs/MERGE_GATE.md`; each fix carries a regression test.

| # | blocker | why it mattered |
|---|---|---|
| 1 | `.trigger/conductor` was committed and the guard tested only file existence | every scheduled wake forced a full capture: 144×/day, year-round, the conductor's real answer overwritten |
| 2 | concurrent archive push destroyed a run's snapshot **and reported success** | reproduced end to end: rebase always conflicts on an append-only manifest, `\|\| true` detached HEAD at the other run's tip, next push no-oped and returned 0 |
| 3 | push loop's last command was `sleep`, so 4 failures exited 0 | 100% silent data loss, green job, no artifact |
| 4 | run job fetched the unbounded archive with no `--depth` | slowest step in the job, compounding all season |
| 5 | `decide` ran `pip install -e .` 144×/day to read five timestamps | ~23 s and ~690 MB per wake; the conductor is now stdlib-only |
| 6 | `player_pra` was MODELABLE on **zero** observed markets | would have priced and settled an assumed shape at `confidence='high'` |
| 7 | an unknown tricode raised out of the slate loop | one real preseason market vs a non-NBA club would abort **every** game and family |
| 8 | `p_data or 0.5` | 0.0 is a legitimate deep-OTM probability and is falsy: a worthless contract became +$0.4467/contract and "bet up to 48¢" |
| 9 | crossed books were never rejected | bid 60/ask 40 gave +$0.1832 with no flag; a four-sided crossed book showed **both** sides profitable |
| 10 | `(played − p_play)·impact_ppp` is identically mean-zero | injury news could not move a team's price at any coefficient — verified, 0.0/0.03/0.06 gave byte-identical results |

Also fixed: ET cutoff using a hardcoded EDT offset, `pregame=True` frozen unconditionally into the
immutable ledger, Elo ordering by calendar date so a game could be rated from one that tipped later
the same evening, silent coverage omissions (now alarmed), and Kalshi's `scalar` result — which is
2.44% of all settled markets while `void`, the value the map *did* handle, never occurs once.

`PRICED` was renamed **`MODELABLE`**, with a legacy read path because the old name is already in the
append-only archive.

## C. Production state

- **main** `6fa1e30`; tree identical to the audited head. **309 tests**, ruff clean.
- Conductor: push-event gate, constant concurrency group, job-scoped `contents: write`,
  `--depth=1`, union-merge on the manifest, explicit `exit 1` on push failure, failure-artifact
  upload, coverage alarms that run **after** the archive push so an alarm never costs data.
- `.trigger/conductor` is **not** on main.
- **Open verification item:** the first *scheduled* conductor run from main had not fired when this
  was written. The workflow reads `state: active`; GitHub is often slow to start newly-landed
  schedules. **Confirm a scheduled run appears and that `capture=false` off-season.**

## D. The market data now available

16,091 markets at the final pre-tip horizon over 1,387 games, 68,235 rows across five horizons and
eight families. Zero rows observed at or after tip.

**Read sample sizes as games, never as markets.** Ladder lines for one entity in one game are
monotone functions of the same realised number.

| family | markets | independent entity-games | median spread |
|---|---:|---:|---:|
| game_winner | 2,772 | 2,772 | 1¢ |
| game_spread | 2,391 | 395 | 2¢ |
| game_total | 2,053 | 193 | 2¢ |
| player_points | 2,587 | 725 | 4¢ |
| player_rebounds | 2,332 | 557 | 4¢ |
| player_assists | 1,708 | 431 | 4¢ |
| player_threes | 1,493 | 383 | 4¢ |
| team_total | 755 | 132 | 8¢ |

## E. Result 1 — the market is the best forecaster in every family

`docs/research/ALL_FAMILIES_MODEL_VS_MARKET.md`. **In not one family does the fitted hybrid beat the
market out of sample.** DATA_ONLY trails by 3–7 points of log loss everywhere. Recalibrating the
Kalshi price makes it *worse* in 7 of 8 families, so the raw price is the benchmark — a harder one.

**Phase 6's answer: the learned weight for DATA_ONLY is zero, everywhere.**

## F. Result 2 — the prop signal that wasn't

All four prop families showed a residual coefficient positive in **every fold, 16 of 16** — exactly
what a real effect looks like. It was **ladder duplication**. De-laddered to one row per
entity-game, `player_threes` flips to **all-negative** and `player_points` loses consistency.

`player_rebounds` survives at ~+0.2 in all four folds and is the most promising lead in this work.
It is still not an edge: the hybrid loses, it rests on 557 entity-games, and rebounds is the family
with the highest rate of ESPN ±1 box-score errors.

## G. Result 3 — the moneyline model is under-dispersed

`docs/research/MONEYLINE_MODEL_VS_MARKET.md`. The residual coefficient changes sign across folds.
The failure is diagnosable: the model says 25.0% where the market says 18.6% and truth is 19.0%, and
75.2% where the market says 82.0% and truth is 81.8%. Probabilities are shrunk toward 0.5.

**Every "edge" it reports on a longshot is its own shrinkage.** A naive EV screen would buy underdogs
and lose on all of them, plus fees.

## H. Result 4 — prop overs are under-priced because minutes are diluted

`docs/research/PROP_BIAS_DIAGNOSIS.md`. Not a tail effect: the model is 13–25% low on **all four**
counting stats. Points per minute is accurate (+2%), so it is a minutes problem. Team minutes are
conserved at 240, but the simulator gives ≥5 minutes to **13.56 players per team against 10.07 in
reality** — every minute given to a 12th man is taken from a starter, and props are listed on the
players who lose. **Do not fix this with a multiplier.**

## I. Result 5 — `rating_scale` 1.6 → 1.9, and Elo is not beaten

`docs/research/RATING_SCALE.md`. Tuned on 2023-24/24-25, confirmed **once** on a 2025-26 holdout
sharing no games, paired per game: 1.6 is worse by 0.0079 nats, 95% CI **[+0.0015, +0.0140]**. The
only parameter change here with real out-of-sample support.

But on that holdout **Elo scores 0.5170 against the simulator's 0.5247**, and the paired intervals
contain zero. Sim and Elo are **statistically indistinguishable on moneylines, Elo's point estimate
ahead**. "The simulator beats Elo" is **not established**; ~0.047 nats of the original claim was
in-sample.

## J. What it costs to beat the market

| family | edge needed after fees |
|---|---:|
| game_winner | **2.5 pp** |
| game_spread / game_total | **3.4 pp** |
| player props | **~4.2 pp** |
| team_total | **5.8 pp** |

The fee, not the spread, dominates. The market's entire measurable miscalibration is about the same
size as the transaction cost, so only a substantially better model is profitable — not a marginally
better one.

## K. Three ways this analysis nearly fooled itself

Each was live before correction, and each is documented where it happened:

1. **Non-independence.** Complementary sides (the two moneyline tail bins were the same 64 games),
   fold boundaries splitting a game (outcome leakage, since sides are exact complements), and ladder
   lines (which produced the false 16/16 result).
2. **Standard errors from the observed rate instead of the null.** Turned a 1.85 SE result into an
   apparent 4.0 SE one.
3. **One-sided selection.** "Rotation players get 25.53 projected minutes against 33.77 actual"
   inverts to **+0.99** when you select on the model's projection instead. Most of it was regression
   to the mean.

## L. Authority — unchanged, deliberately

**Every family remains RESEARCH. Nothing is SHADOW, LIMITED or TRUSTED.**

I do **not** recommend promoting anything to SHADOW yet. The research argues against it: no family
beats the market, the moneyline model is under-dispersed, props are biased by roster dilution, and
the one surviving lead (rebounds) still loses to the market. Promotion should wait until at least
the minutes distribution is fixed and the model stops being wrong in a known direction.

## M. What to do next, in order

1. **Minutes allocation** (§H) — the largest, best-understood defect. Concentrate the rotation to
   ~9–10 players. Fixes all four prop families at once.
2. **Estimate `impact_ppp`** (`AUDIT_FOLLOWUPS.md` R1) — the simulator still has **no team-level
   injury response**, and this blocks any promotion above RESEARCH.
3. **Roster-quality renormalisation** — `factor = clip(ppp_mu / base_ppp, 0.75, 1.3)` actively
   renormalises roster quality away and is a prime suspect for the under-dispersion in §G.
4. **`player_rebounds` on more games** — the one lead worth a dedicated study.
5. **Storage compaction before the season is a month old** (`docs/MERGE_GATE.md` threshold table).
6. **Re-pull ESPN history** — the parser is fixed, but committed data still cannot reproduce
   committed numbers (48 errored games, not outcome-neutral).

## N. Registered and not fixed

`docs/AUDIT_FOLLOWUPS.md` lists 20 findings with why each was left; R2 and R4 are now resolved by §I
and §H. Judgement calls about gating semantics (should a thin book block a recommendation, or only
cap its size?) were deliberately left for an explicit decision rather than slipped in beside a merge.

## O. How to reproduce any number here

```bash
python scripts/evidence.py                                   # live repo/CI/dataset state
python -c "from nba_edge.research.market_table import *; ..."# rebuild the market table
python -m nba_edge.research.market_vs_model --horizon final  # all-family study (cached sims)
python scripts/rating_scale_walkforward.py                   # Phase 8, tune + holdout
pytest -q                                                    # 309 tests
```

Simulation results are cached in `data/research/market_table_scored.parquet`, so the study re-runs
its statistics in seconds. **If you change the simulator, delete that file** — otherwise you will
re-report the old model's probabilities against new code.
