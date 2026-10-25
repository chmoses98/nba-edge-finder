# Pre-registration: JRM minutes with refitted stat models (challenger R1)

Written before any forward outcome of the challenger exists. Research only; nothing here activates the joint rotation model, changes a production projection, a gate,
a betting threshold, a stake or a route.

## Why a challenger

The prospective evaluation of the JRM minutes (results/prospective_20261024T1235Z_PASS_26games.md on the `minutes-shadow-archive` branch) passed its pre-registered rules,
but the stat forecasts built on those minutes were not better than the frozen engine's (assists significantly worse, points/PRA/FGA biased high by +0.6 / +1.0 / +0.45).
Diagnosis (artifacts/DOWNSTREAM_ROOT_CAUSE.md): the live publisher trains the stat ladders with the minutes input missing for every history row and serves it only for the slate
season, so the stat models do not use minutes at all; the frozen engine's reconciliation gate (a minutes scale) was the only minutes-to-stats link and it hid the resulting
high bias; the JRM conserves the budget, needs no gate, and exposes the bias. The backtest (downstream_fit.py) trained the ladders with a finite minutes forecast on every history
row. The challenger makes the live recipe match the backtest recipe.

## Candidate R1 (frozen at the commit recorded in `challenger_rules.FREEZE`)

* minutes: JRM v2 (unchanged, uniform allocation, level E).
* stat ladders: `project_slate(..., minutes_engine="jrm", stat_models="refit")` (env `PF_NBA_STAT_MODELS=refit`): for history rows of seasons 2020-2026 the minutes input is the
  frozen walk-forward JRM minutes (`results/jrm/hist_minutes.parquet`, produced by heads trained on strictly earlier seasons); the frozen hyper-parameters and stack weights are unchanged;
  history rows of the current season keep their frozen forecast. Nothing is tuned.
* The default of every production path is unchanged (`stat_models="frozen"`); R1 exists only in research snapshots.

## Comparators (same feed, same players, archived pre-tip next to R1)

* P0 = the frozen production engine as published (after its live gate), `stats.frozen_published`.
* P1 = JRM minutes with the existing stat models, `stats.jrm_engine`.
* P2 = R1, `stats.jrm_refit`.

## Eligibility (forward only, never retroactive)

A snapshot counts for R1 only if (a) it is eligible under `archive_rules` (validated minutes configuration, pre-tip by the independent clock, clean tree), (b) it carries
`stats.jrm_refit` for the row, (c) its `code_commit` descends from `challenger_rules.FREEZE` and the challenger's files (nba/minutes_jrm.py, nba/stats.py, nba/project.py,
nba/live/reconcile.py, results/frozen_params.json, results/jrm/*) are byte-identical to the freeze. Snapshots archived before the freeze are never scored for R1. The archived
2026-10-20..24 prospective sample was used for DIAGNOSIS only and is not validation of R1.

## Decision rule (single look; intersection of all criteria)

Population: players who played in an eligible snapshot's game, conditional-on-playing frame. Minimum: **30 settled games and 500 played player-games**; the verdict is computed
once, on the first evaluation that meets the minimum (earlier runs are descriptive monitoring and cannot declare a pass or a failure).
For each family f in {points, rebounds, assists, threes, PRA, FGA}, with game-clustered paired bootstrap 95% intervals:

1. **Accuracy non-inferiority vs P0**: the upper bound of ΔMAE(P2 − P0) is below +2% of P0's MAE in that family.
2. **Bias**: |mean(P2 − y)| ≤ 5% of mean(y), and |bias(P2)| ≤ |bias(P0)| + 2% of mean(y).
3. **Betting probabilities**: the mean Brier score of the rung probabilities P(X ≥ k) at the family's rungs has a paired difference (P2 − P0) with an upper bound below +0.003.
4. **No regression of the minutes verdict**: the pre-registered minutes rules (primary, starter guard, coherence) still pass on the same games.

R1 PASSES only if criteria 1-3 hold for all six families and criterion 4 holds. Superiority (ΔMAE < 0), CRPS-like and cohort breakdowns (starters, bench, fringe rotation, new-to-team,
early season) are descriptive and cannot rescue a failed criterion. Failure of any criterion means R1 is not recommended and any change is a new version with a new freeze.

## Automation

`forward_cycle.py snapshot` (three times a day) archives the snapshots; `forward_cycle.py evaluate` (daily) runs this rule, commits the report under `results/` of the archive branch
and stays silent until the minimum is met; the only human action required is the activation decision.
