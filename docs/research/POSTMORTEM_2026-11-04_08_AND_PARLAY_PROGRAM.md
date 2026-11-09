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
