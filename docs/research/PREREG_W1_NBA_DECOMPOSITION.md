# Preregistration — W1-C matched player-game decomposition (NBA)

Frozen **before** the holdout window is collected or scored. Committed on its own; the results
document cites this commit's hash. Nothing below may be changed after the holdout run; deviations
are reported as deviations.

## Question

On the **complete eligible** held-out population — not market-listed, not outcome-selected — does
the current champion's ~20% counting-stat low bias persist, and if a bias exists, is it carried by
participation, by minutes given play, or by production per played minute?

## Arms (identical rows, cutoffs and seeds)

| arm | definition |
|---|---|
| `ewm5` | simplest sports-only baseline: EWM half-life 5 over prior same-team regular-season games played; minutes = the feature layer's `min_mean` (the published EWM-5 minutes predictor); P(play) = EWM-5 of participation over the team's last 20 games, shrunk with one game at 0.5; counts ~ NB(mean, α) with α fitted by moments on rows **before 2024-11-15**; minutes ~ N(min_mean, min_sd) clipped [1, 48] |
| `sim_rotation` | **champion**: frozen `NBA_BASELINE_2026_PRESEASON_V1` (digest `5a4cbda0…193be78`) — `build_game_params(..., BuildConfig())` → `simulate`, rotation mixture active |
| `sim_waterfill` | diagnostic only: identical params with rotation profiles stripped (pre-Phase-3/4 path) |
| `sim_challenger` | `RATE_PRIOR_5`: the champion with ONE change, `BuildConfig.player_prior_minutes` 60 → **5** (see decision below); same roster, same seed, same draws otherwise |

**Participation semantics (fixed on DEV, applies to every arm).** The box score's `played` means the
player logged minutes. The simulator's `played` array is *availability*: an available player outside
the drawn rotation receives 0 minutes in most draws. Simulator arms are therefore scored on the
appearance event `available & minutes > 0`; conditional-on-playing distributions use those draws.
(The first DEV pass used availability and showed the champion ~11% low conditional on playing — an
artifact of mixing zero-minute draws into the conditional, not a forecast error.)

2,000 draws per game; per-game seed = sha256(game_id). No injury reports (none committed
historically): every arm sees the same participation-proxy inputs.

## Data and windows (chronological, regular season only, committed ESPN history)

- Inputs for a game: rows with `game_date_et` strictly before the game date (enforced in
  `forecast_game` and tested adversarially).
- **DEV** (diagnosis, any fitting): 2024-11-15..2025-04-13 and 2025-11-15..2026-01-31.
- **HOLDOUT** (scored once): **2026-02-01..2026-04-12**, every regular-season game (501 games).
- Eligible player-game: the champion's pre-tip roster rule — appeared in ≥1 of the team's last 10
  games before the cutoff, top 15 by `min_mean × p_play`. Outcome: box score; absent from the box ⇒
  did not play, all stats 0. Players who play but were not eligible are counted and reported.
- Known pre-existing contamination, not created here: `ROTATION_SIZE_PMF` (rotation.py:47) and the
  rotation validation used 2023-24..2025-26, i.e. include the holdout season; `rating_scale` 1.9 was
  confirmed once on 2025-26. These are properties of the frozen champion and are disclosed, not fixed.

## Metrics (one row per player-game-statistic; never one per ladder rung)

- Participation: Brier of P(play); Brier of P(minutes ≥ 10).
- Minutes: MAE, RMSE, bias, CRPS (exact sample CRPS), p10–p90 coverage — unconditional (all
  eligible) and conditional on actually playing.
- Per played minute (rows that played, weighted by actual minutes): predicted/actual for FGA, 3PA
  (simulator: three_share × FGA, the engine does not export 3PA), FTA, TOV, usage
  (FGA+0.44FTA+TOV), points, rebounds, assists, threes; points per shooting possession.
- Final points / rebounds / assists / threes: MAE, RMSE, bias, CRPS, p10–p90 coverage and **one**
  threshold Brier per player-game-stat at `t_ref` = the fixed-ladder rung nearest the EWM-5
  conditional mean (ties up). Unconditional and conditional.
- Decomposition (full eligible population, per arm and stat), exact identity
  `Σpred/Σactual = F_participation × F_minutes|play × F_rate`.
- Observation-choice table: the same ratio on pre-tip frames (all; predicted starters; predicted
  ≥28 min) and on selected frames (actually played; actually ≥28 min; player-games with a listed
  prop contract — listing keys only, never prices).
- Uncertainty: paired game-clustered bootstrap, 1,000 resamples, seed 20261010, 95% percentile CI.
- Strata (pre-tip only): predicted starter / bench; EWM-5 FGA-per-minute terciles with cut points
  frozen from DEV.

## Decision rules

1. **Bias persists** for a stat if the champion's full-population ratio has 95% CI upper bound
   < 0.90. "No material bias" if the CI lies inside [0.95, 1.05].
2. A channel **contributes** if its factor's CI excludes 1 and |factor − 1| ≥ 0.03.
3. A correction may be attempted **only** if DEV isolates a genuine per-minute-rate error that is not
   explained by participation/minutes and is consistent across both DEV seasons. *Refined after DEV
   inspection, before any holdout access:* the aggregate F_rate (0.984) does not meet rule 2 by itself;
   the error is isolated at the stratum level — by the arm's own pre-tip usage tercile, the top and
   bottom terciles miss with opposite signs by ≥ 0.03 in both DEV seasons (compression toward the
   league rate). That is the criterion used.
4. Any correction is ACCEPTED as a research challenger only if, on the holdout, its paired ΔCRPS and
   ΔMAE vs the champion are both < 0 with CI excluding 0 for the targeted stat and no other count
   stat worsens with CI excluding 0. Otherwise REJECTED. Promotion is never automatic.

## DEV result and correction decision (recorded before the holdout is collected)

DEV full pass (1,599 games, 46,713 eligible player-games, availability semantics; descriptive):
champion unconditional Σpred/Σactual — points 0.9999 [0.9956, 1.0043], rebounds 1.0326, assists
0.9764, threes 0.9987. **The ~20% low bias does not appear on the complete eligible population.**
On actually-≥28-minute player-games the same forecasts look ~20% low (outcome selection).

DEV subset (every 5th DEV game, 320 games, appearance semantics), champion decomposition for points:
F_participation 1.033, F_minutes|play 0.979, F_rate 0.984 (product 0.995). Per-played-minute
predicted/actual by the champion's own predicted-FGA-per-minute tercile:

| tercile | points | FGA | assists |
|---|---:|---:|---:|
| low | 1.034 | 1.015 | 0.996 |
| mid | 0.987 | 0.968 | 0.961 |
| high | 0.963 | 0.945 | 0.949 |

Full DEV, by season (top tercile points / FGA): 2024-25 0.966 / 0.950; 2025-26 0.967 / 0.946; bottom
tercile points 1.022 (2024-25), 1.070 (2025-26). The rate model is compressed toward the league mean.
The feature layer shrinks each player's per-minute rates toward league rates with
`player_prior_minutes` = 60 minutes of prior mass (features/build.py:242-245, :164-170).

**Decision: one correction, `RATE_PRIOR_5` (player_prior_minutes 60 → 5).** Candidates {20, 5} were
run on the DEV subset only (`collect --window dev --every 5 --player-prior-minutes {20,5}`). 5 gave the
lower MAE in all four count stats (paired ΔMAE points −0.0103 [−0.0153, −0.0055], assists −0.0059,
rebounds −0.0043, threes −0.0010, all CIs < 0) and the more balanced terciles (points 1.000 / 0.981 /
0.979). DEV ΔCRPS was small and its CI included 0 for points (−0.0025 [−0.0057, 0.0003]), so a holdout
pass under rule 4 is not expected to be easy. No other value, parameter or feature will be tried.

**Targeted stat for rule 4: points, unconditional (full eligible population).** All other stats and
the conditional frame are reported as secondary. Holdout command (run once, after this commit):

```
python scripts/nba_matched_decomposition.py collect --window holdout --player-prior-minutes 5 \
    --arms ewm5,sim_rotation,sim_waterfill --out $OUT
python scripts/nba_matched_decomposition.py report --window holdout --out $OUT \
    --usage-cuts 0.2920,0.3922 --listed $OUT/listed.parquet --json docs/research/w1_nba/scorecard_holdout.json
```

The usage-tercile cut points for the holdout strata are taken from the full DEV pass
(EWM-5 FGA/min **0.2920 / 0.3922**, from the full DEV report) and frozen here.
