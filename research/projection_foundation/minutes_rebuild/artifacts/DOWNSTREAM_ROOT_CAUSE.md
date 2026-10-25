# Why the JRM minutes did not improve the stat forecasts in the prospective sample: root cause

Research only. Nothing here changes a production projection, a gate, a threshold, a stake or a route. Evidence files: `DOWNSTREAM_DIAGNOSIS_HISTORICAL.md` (walk-forward, strictly earlier
seasons train), `DOWNSTREAM_PROSPECTIVE_DIAGNOSIS.md` (replays of the archived prospective feeds; diagnosis only), probes `probe_components.py`, `downstream_live_recipe.py`.

## Findings

1. **The live stat ladders are minutes-blind (true for the frozen engine too).** `nba/project.py` feeds the stat ladders (`nba/stats.py::fit_family`) the column `min_best`. It comes from
   `M.fit_ladder(final_only=True)`, which predicts only the slate season: **0.03% (feed of 2026-10-21) and 0.17% (feed of 2026-10-23) of the history rows have a finite minutes input**
   (probe `share of history rows with a finite minutes input`). The stat LightGBM (`E`, `E_inj`) is trained with `min_hat` and `C_hat` entirely missing, so it never splits on them and the
   served minutes are ignored; the opponent factor (computed from `C`) is empty for the same reason (`opp_n` = 0). The backtest recipe (`downstream_fit.py`) trains with a finite minutes
   forecast on every history row, so **the live recipe is not the recipe whose evidence promoted the families**.
2. **Therefore swapping the minutes engine cannot move the points, assists, PRA and FGA means.** Replaying the feeds with both engines: the *ungated* means are identical
   (points bias +0.725 in both engines on 554 player-games; assists +0.145; PRA +1.131; FGA +0.543). Historical emulation of the live recipe: JRM minutes + existing models vs the production
   frozen recipe, holdout 2024-25/2025-26, paired ΔMAE points +0.000 [-0.001, +0.002], assists +0.000, PRA +0.001, FGA +0.001 (rebounds/threes, which use the C/D rungs through the stack, move by -0.004/-0.001).
3. **The only minutes-to-stats link in production is the reconciliation gate**, and it is a bias-compensating accident. The frozen engine scales stat means by the minutes normalisation
   (mean ×0.944, ×0.72-0.88 on gated teams) and by a usage scale (×1.022). In the early-season sample the ungated stat means are biased **high** (points +7.4%, PRA +7.2%, FGA +7.1%;
   archived team-points forecasts +3.6 points = +3.2% high on 56 team-games, SE 1.6), and the frozen gate removes most of it by chance (final points bias +2.1%). The JRM conserves the budget, needs no
   gate (×1.000) and therefore exposes the underlying bias (+6.7%). In the historical backtest the same gate over-shrinks the teams it acts on (points bias -0.95 on gated teams), so this is not skill.
4. **The 'trained on the old minutes distribution' hypothesis is rejected.** P4 (history-consistent training with the OLD frozen minutes, served with JRM minutes) equals the challenger:
   points ΔMAE vs production -0.061 [-0.068, -0.054] vs -0.060 [-0.067, -0.053] for training on JRM minutes (P2). What matters is that the ladder is trained with a finite minutes input at all.
5. **The backtest/prospective discrepancy is reproduced and explained**: the backtest 'JRM' variant is the refitted recipe (P2/P3-type), the live candidate is the minutes-blind recipe (P1) without the
   gate, evaluated on an early season whose league-wide scoring ran about 3% below the frozen team model.

## What a corrected recipe is worth (historical, holdout, vs production frozen = P0; CIs game-clustered)

| family | P1 JRM + existing models | P3 frozen minutes + refitted models | P2 JRM + refitted models (R1) |
|---|---|---|---|
| points | +0.000 [-0.001, +0.002] | -0.048 [-0.055, -0.040] | **-0.060 [-0.067, -0.053]** |
| rebounds | -0.004 [-0.006, -0.003] | -0.002 [-0.003, -0.000] | -0.008 [-0.010, -0.006] |
| assists | +0.000 [-0.000, +0.001] | -0.015 [-0.018, -0.013] | **-0.018 [-0.020, -0.016]** |
| threes | -0.001 [-0.001, -0.001] | -0.002 [-0.002, -0.001] | -0.003 [-0.004, -0.002] |
| PRA | +0.001 [-0.002, +0.004] | -0.077 [-0.090, -0.066] | **-0.101 [-0.113, -0.089]** |
| FGA | +0.001 [-0.001, +0.003] | -0.037 [-0.043, -0.031] | **-0.049 [-0.055, -0.043]** |

About three quarters of the gain comes from fixing the stat recipe (P3, available to the FROZEN engine too) and about a quarter from the JRM minutes. The gains are modest (1-2% of MAE) and
every family improves; rung (betting) Brier improves in all six (points -0.0009 [-0.0010, -0.0007]).

## Prospective diagnosis (554 played player-games, two feeds; NOT validation)

R1 vs production frozen: points MAE 4.428 vs 4.636 (-0.208 [-0.330, -0.094]), PRA 5.749 vs 6.051 (-0.302), FGA 2.697 vs 2.823 (-0.126), assists 1.286 vs 1.317 (-0.032 [-0.064, +0.003]); rung Brier
better in points, assists, PRA, FGA (CIs exclude 0). **Bias remains**: R1 points +5.9%, PRA +4.7%, FGA +5.4% (production frozen +2.1%, +1.3%, +1.7% thanks to the gate), concentrated in non-starters
(points +1.06) while starters are now unbiased (-0.04 vs -1.17 for production). That early-season level shift is a property of the first weeks of 2026-27, not of the minutes engine;
whether it persists is what the forward validation measures (PREREG_STAT_REFIT.md criterion 2 would FAIL R1 if it does).

## Consequences

* The JRM minutes improvement is real (pre-registered minutes verdict PASS) and is preserved; the stat side needs the history-consistent recipe (candidate R1), validated forward on data it has never seen.
* Independently of the JRM, the production frozen engine's stat ladders are minutes-blind in live operation; the history-consistent recipe would improve them too (P3). Changing production is out of scope and
  needs the owner's approval; it is reported here so the decision can be taken with the evidence.
