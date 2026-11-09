# NBA all-market postmortem (Nov 4 + Nov 8, 2026), defect ranking and parlay research program

RESEARCH_ONLY · issue #95 · archive `data-archive` fetched 2026-11-09 · reproduce: `nba audit-markets --archive <archive> --date 2026-11-04 --date 2026-11-08 --out <dir>`
(outputs committed under `docs/audits/<date>/`: `report.md`, `report.json`, `universe.csv.gz`; the 60 MB per-horizon CSV is regenerated, not committed).

## 1. Coverage (no silent drops; universe = graded + ungraded, asserted in code)

| ET date | universe (unique tickers) | graded | ungraded: semantics not proven | player not in box | no settlement yet | unsupported stat (`stocks`) | tie semantics | DNP rules |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-11-04 | 12,179 | 8,307 | 3,527 | 126 | 92 | 87 | 10 | 30 |
| 2026-11-08 | 6,271 | 4,112 | 1,998 | 90 | 25 | 40 | 6 | 0 |

* "Graded" = settled YES/NO **and** has a valid pre-tip model probability. VOID/PUSH/UNSETTLEABLE/unsettled are never scored as losses.
* The 3.5k/2.0k "semantics not proven" tickets are the `*PROT` and `ESCALATOR`/`WINMARGIN` series (UNRESOLVED in the ontology): modelled by nobody, settled by nobody, so they cannot be evaluated. Blocker B3.
* Zero combo/RFQ/MVE markets (`KXMVE*`, `KXNBAPREPACK*`) exist in the archive for either date: **no combo price evidence exists**.
* The 29k (Nov 8) / 59k (Nov 4) forecast rows without `p_data_only` are predominantly `player_unknown`/`unknown` UNRESOLVED rows plus RESEARCH-only families (`game_points_leader`, `game_race_to`, `game_win_margin`); counted in `refused.no_model_probability`.
* Legacy simulator rows carry empty quote fields (§5.14). The audit does not depend on them: quotes are joined from the archived board at-or-before the forecast time (strictly pre-tip, post-tip boards refused). Live `p_market`/EV logic was **not** changed.

## 2. What the data say (descriptive, game-clustered 95% CI; 🟢 model>market, 🔴 market>model)

**Nov 4 (many games): the model is worse than the market on Brier in all 17 family groups**; market beats model with a game-clustered CI excluding 0 on `game_total`, `team_total`, `player_points`, `player_threes`, `player_double_double` (Brier gap), and the model's +EV picks lose after fees (ROI after exact fee, hypothetical taker, +EV-by-model picks: totals −39% [−59,−21], points −12% [−22,−2], threes −16% [−25,−8]). No family shows positive ROI with an interval excluding 0.
**Nov 8 (7 games):** mixed, every interval wide. Apparent greens (`period_winner`, `game_winner` ROI) are 7-game results across 17 families (no multiple-comparison control) and are **not** evidence of skill. `game_winner` n=14 tickers.
All forecasts remain RESEARCH; nothing here promotes any family. Selection CLV and quoted-execution CLV are small (|mean| ≤ 1.5¢ quoted-execution, ≤ 0.8¢ selection on Nov 4; same order on Nov 8) (the model's picks do not beat the close); actual-fill CLV n=0 (no fills exist).

### Nov 8 game level (frozen simulator vs final; home margin / total error = actual − predicted)
| game | margin err | total err |
|---|---:|---:|
| PHI@CHI | +2.8 | +19.5 |
| LAL@DET | −11.5 | +16.4 |
| UTA@MIN | −6.0 | −15.7 |
| BKN@DAL | +24.0 | +5.8 |
| BOS@MIL (CANNOT_TRUST input) | +2.6 | −14.4 |
| NOP@LAC | +8.7 | +29.8 |
| MIA@SAC | +8.8 | −23.7 |

Margin RMSE 11.4 (bias +4.2, SE ≈ 4.3), total RMSE 19.2 (bias +2.5). These are the size of ordinary NBA game noise (≈12 / ≈18–19). **Seven games cannot show a pace, total or blowout defect**; the Nov 8 misses should not be used to tune the simulator. The BKN@DAL 24-point margin miss (DAL blowout) is the one outlier consistent with the open L3/L4 rotation limits; the PR #61 diagnostics (merged into this branch) are the tool to attribute it and need ≥ 30 games before any change.

## 3. Ranked defects, repairs, blockers

| # | finding | evidence | status |
|---|---|---|---|
| 1 | `nba evaluate` evaluated 0 rows in production (`--out` was `archive/eval`, an empty ledger); exit 0 | PR #59 measurements; archive report `n_rows 0` vs 18k settled tickers | **Fixed**: PR #59 merged into this branch (+ closing quotes read via `_quote_cents`); the audit exits 3 / BLOCKED when eligible settled inputs exist but nothing is graded |
| 2 | Model is less accurate than the market on nearly every family; player_points/threes and game totals lose after fees with CI < 0 | Nov 4 audit | Open: **no promotion**; use market-anchored hybrids only after prospective validation |
| 3 | Production team-level injury impact is zero (SIMULATION.md L2) | PR #81 (draft) adds certified-lineup impact | Blocked: #81 does not merge cleanly with main (conflict in `projection_foundation/nba/project.py`); needs author rebase, then prospective holdout. Not promoted, not duplicated here |
| 4 | Legacy rows carry no quote fields (§5.14) | 444k rows, 0 with quotes | Audit works around it via board join; PR #65 (inert) awaits explicit approval because it changes live-facing EV |
| 5 | Unmodelled/unsettleable series (`*PROT`, escalators, win-margin, race, `stocks`) | 3.5k tickers on Nov 4 | Blocker: ontology + settlement semantics needed |
| 6 | Postgame attribution (pace/efficiency, observed role, layer coherence) | PR #61 | Merged into this branch (tests pass); needs ≥30 completed games |
| 7 | Cross-layer disagreement (e.g. PHI/CHI 228.5 sim total vs 243.3 player layer) | issue #95 | Logged by #61 layer-coherence; not reconciled |

Not evaluated (explicit): injury-status/participation splits per horizon (needs injury-snapshot join), multiple-comparison control, held-out test. Full-archive `nba evaluate` output was reproduced locally (see PR).

## 4. Parlay research program (paper only)

Code: `nba_edge/parlay/research.py` (dependence-aware joint probability, break-even incl. one fee, evidence calculator, append-only ticket freeze, settlement where void/unresolved legs are never losses) and `parlay/paper.py` (`nba parlay-paper freeze|eval`: one leg per game from distinct games, `selective` vs `simple_2leg` vs `random_same_pool` strategies, props excluded by default and admitted only at edge ≥ 10%).

Design rules: combined prices are **only** observed Kalshi Combo/RFQ quotes — none exist in the archive, so every ticket is `NO_RFQ` (calibration-only; leg-ask product stored as a labelled reference, never as P&L). Same-game legs use a Gaussian copula (default ρ=0.15, to be replaced by the residual correlations that the audit's per-horizon rows make estimable); cross-game legs are treated as independent. Verdict is never above `DESCRIPTIVE_ONLY`.

**Evidence needed** (`tickets_needed`): at ≈1-in-400 break-even, proving a true win rate 1.5× break-even (80% power, α=5%) needs several thousand independent tickets; one expects only ~63% chance of ≥ 1 hit in 400 tickets even if p = 1/400. Because the leg-level model is currently *worse than the market*, the product of model probabilities across ~8 legs is biased upward, and the central hypothesis is **unsupported today**. Gate to even start RFQ collection: ≥ 1 family with leg-level calibrated edge (CI > 0 out of sample, multiplicity-controlled).
Paper tickets are frozen before the first tip; no orders and no RFQ submissions are made.

## 5. Nightly automation
`.github/workflows/nightly_postmortem.yml` (06:40 ET): sparse archive fetch → `nba audit-markets` for the last two ET dates (fails the job on BLOCKED) → `nba parlay-paper eval` → artifact upload. Writes nothing to any branch.

## 6. Follow-up (2026-11-09 evening): root-cause evidence, ungraded accounting, runtime

**Multiple-comparison control.** The audit now reports Benjamini–Hochberg q across the family comparisons; green/red requires a game-clustered CI excluding 0 **and** q < 0.10. Nov 4: market beats model (q<0.10) on `game_total` (q=.009), `team_total` (.017), `player_points` (.043), `player_threes` (.043). Nov 8: nothing survives.

**Ungraded accounting (Nov 4).** Of 3,527 "semantics not proven" tickets, 2,900 (82%) are `*PROT` protected props (identical to the base prop except that a player who only plays the first half resolves to the fair price). They are gradeable as the base prop once per-period participation is known — the single largest coverage gain available. The rest: 199 points-leader, 134 scalar escalators (payout formula `floor(10000·(y/50)^3)/10000`, not binary: needs expected-payout scoring, not Brier), 112 win-margin buckets (settleable from the final score; the simulator emits no probability for them), 84 race-to, 98 other. Same split on Nov 8 (1,691 PROT of 1,998).

**Model-vs-market root-cause evidence** (`scripts/audit_diagnostics.py`; 21 games over both dates, per-game not per-rung):
* Totals are **anti-informative**: across games the sign of the model's disagreement with the market total is negatively correlated with the realised outcome vs market (game_total ρ=−0.62, team_total −0.59, period_total −0.66; p≤0.01). A model that merely added noise would show ρ≈0.
* The crude injury proxy does **not** explain it: ρ(model−market total gap, number of non-G-League OUT players) ≈ −0.02…−0.05. So the "missing team injury impact" hypothesis (L2) is not supported as the driver of the totals error, and PR #81's candidate failed its held-out test (below). Pace/efficiency attribution needs the #61 postgame diagnostics over ≥ 30 games on the `projection-data` branch.
* Frozen-weight blend: weights fitted on Nov 4 only are ≈0 for totals, player points and threes and ≤ 0.15 elsewhere; scored on untouched Nov 8 (4,060 tickets) pooled Brier is model 0.1612, market 0.1534, blend 0.1530. The market is the better forecast; a heavily market-weighted blend is at best marginally better. **No promotion**: 21 games, and the weights should be re-estimated prospectively.
* Caveat: `period_winner` shows ρ=+0.96 only because both teams' tickers appear per game and mirror each other; it is an artifact, not skill.

**#81 held-out result.** REJECT_FOR_PRODUCTION (RMSE gain −0.0005, CI [−0.0014, +0.0004], 2,444 team-games from untouched 2025-26). Details in `INJURY_RESPONSE_SHADOW.md`.

**Evaluator runtime.** `nba evaluate` is memory-bounded (the unbounded version was OOM-killed at 2M predictions) and capped at 150k new rows / 600 s per run, newest partitions first; the 1.4M-row backlog drains over ~10 runs (~85 s each locally; steady state 65 s), and market-only closes are cached. A run with eligible settled predictions but zero rows exits 3.

**CI.** The failing `dry-run` check (projection-foundation) died with "runner has received a shutdown signal" ~11 minutes into the research stage, exactly like the scheduled run on unmodified `main` (run 42679890601, same step, 11m08s) — infrastructure, not this change.
