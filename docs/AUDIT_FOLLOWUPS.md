# Audit follow-ups not fixed before the merge

The ten blockers found by the pre-merge audit are fixed (see `docs/MERGE_GATE.md`). Everything below
is a real finding that was deliberately **not** fixed in the same pass, because each one is either a
judgement call about gating semantics, or a research task, and making sweeping unvalidated changes
immediately before a merge adds risk rather than removing it.

Nothing here is a reason to trade. Authority is RESEARCH and no family may be promoted while **R1**
is open.

## Research (blocks any promotion above RESEARCH)

| id | finding | why it matters |
|---|---|---|
| **R1** | **`impact_ppp` is unestimated**, so the simulator has no team-level injury response. The algebra is now correct but the coefficient is 0.0 for every real player. | Ruling out a 29.7-ppg star moves the team by 0.68 points. Estimating it needs on/off or lineup data not yet ingested. **This alone blocks SHADOW.** |
| ~~R2~~ **RESOLVED** | `rating_scale` re-estimated out of sample and raised 1.6 → **1.9** (`docs/research/RATING_SCALE.md`): tuned on 2023-24/24-25, confirmed once on a 2025-26 holdout sharing no games, paired per game, 95% CI [+0.0015, +0.0140] excludes zero. | The **second half of R2 stands and is now measured**: on the holdout, Elo scores 0.5170 against the simulator's 0.5247. The paired intervals contain zero, so sim and Elo are **statistically indistinguishable on moneylines, with Elo's point estimate ahead**. "The simulator beats Elo" remains **not established**. |
| **R3** | `LEAGUE` constants were calibrated on the full sample. | Same in-sample concern, smaller magnitude. |
| ~~R4~~ **RESOLVED (and re-framed)** | Not a tail problem: the model under-predicts `P(over)` at every line level in every prop family, 13–25% low on all four counting stats (`docs/research/PROP_BIAS_DIAGNOSIS.md`). | Cause is **minutes, not efficiency** — points per minute is accurate. The simulator gives ≥5 minutes to **13.56 players per team against 10.07 in reality**, so starters are starved by roster dilution. Fix belongs in minutes allocation; a multiplier would be wrong for the bench players already over-served. |
| **R5** | `usage_elasticity` is declared, documented and never read. Bench players get exactly zero OT minutes. `_endgame_compression` moves points without moving makes (24 draws with `pts < 3·fg3m`). | Each distorts prop tails specifically. |

## Execution safety (fix before any real order is sized)

| id | finding | current behaviour |
|---|---|---|
| **E1** | Only `stale` and `crossed` block a recommendation. `thin` (liquidity 0, volume 0) and `wide_spread` are flagged but still yield `Gate.OK`. | A zero-liquidity market can be recommended. Deliberately left alone: `best_side` means "best expression", and whether thinness blocks or merely sizes is a decision to make explicitly, not to slip in. |
| **E2** | A quote with **no** timestamp is treated as fresh, and a **future** timestamp gives a negative age so it is never stale. | Unknown age is not freshness. Narrow fix (future timestamps) is safe; the `None` case changes behaviour broadly and needs its own pass. |
| **E3** | Player props are priced conditional on the player playing, and `p_play` is recorded only as free text. | A `scalar` settlement pays roughly the pre-game mark, so the loss is mostly the unrecovered taker fee, not the stake — the two audits disagreed on the magnitude and the smaller reading is the one the settlement evidence supports. Quantify before adjusting. |
| **E4** | `FeeSchedule.from_series` has no production caller; `simulate.py` hardcodes `DEFAULT_SCHEDULE` while discovery already captures per-series multipliers. | Fees are exact for the default schedule; a series with a different multiplier would be mispriced. |
| **E5** | `roi = ev/q` excludes the fee from the denominator, and it is the ranking key in `expression.py`. | Ranking distortion, not a pricing error. |

## Data integrity / operations

| id | finding |
|---|---|
| **O1** | `Ledger.verify()` does not detect an un-manifested partition that `iter_rows` would happily read, and the manifest itself has no hash chain — an edit to the manifest is undetectable. |
| **O2** | `_pred_id` has second resolution and no run id, so same-second reruns collide (`evaluate.py` silently drops one) and different-second reruns double-count the same view. |
| **O3** | A same-second rerun raises `ImmutabilityError` out of `run_simulate` *after* all simulation work and *before* `slate.json` is written, losing the whole capture. The two ledger appends are also non-transactional. |
| **O4** | Postponed/rescheduled games break the ticker→game join: `KXNBAPTS-26JAN24GSWMIN` settled off the 2026-01-25 game, and both `markets_for_game` and `resolve_game_id` match on the ticker date. |
| **O5** | The committed ESPN history cannot reproduce the committed research numbers: 48 games errored, and the dropped games are not outcome-neutral (y-mean 0.800 vs 0.610). The parser is fixed; the dataset needs re-pulling so the numbers are reproducible. |
| **O6** | Storage: see the migration threshold in `docs/MERGE_GATE.md`. Compaction work must land before the regular season is a month old. |

## Semantics

| id | finding |
|---|---|
| **S1** | `build_contract` maps `strike_type="greater"` to a strict `gt`. Every observed line in every MODELABLE family is a half-point, so `gt` vs `ge` is literally unobservable — but the mapping is load-bearing the day Kalshi lists an integer line. Add an explicit alarm when `greater` arrives with an integral floor. |
| **S2** | `KXNBA1HWINNER` is a **three**-way market (`-ATL`, `-ORL`, `-TIE`); ties are 3.44% of first halves. Fail-closed today, but `complementary_pairs_ok` assumes two-way and returns False on a coherent three-way price. |
| **S3** | `ladder_key` keys on `game_id`, which `build_contract` leaves `None`. Safe in `simulate.py`, which fills it first; unsafe if called on raw output. |
| **S4** | Settlement is stricter than pricing on 1H ties: 44 real contracts are UNSETTLEABLE where Kalshi settles NO. |
