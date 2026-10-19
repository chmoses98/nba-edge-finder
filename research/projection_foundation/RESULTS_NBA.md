# NBA Projection Foundation: results

**Research only. Betting authority is unchanged (RESEARCH for every family).** This is about how accurate and how well calibrated our own projections are. It does not show that we beat the market: earlier work in this repo found Kalshi's price beats the old model in 8 of 8 prop families, and that question is not re-tested here.

Every number below comes from `results/backtest_raw.json`, which `python -m nba.run_walkforward` produces. `python -m nba.summarize` turns it into `results/summary.json` (CONTRACT schema), `results/frozen_params.json`, `results/experiments/*.json` and `results/tables_nba.md` (all splits, including development).

## 1. Headline for a bettor

* **Minutes is the driver, and we now project it much better than the production model.** For a player who plays, the new LightGBM minutes forecast misses by **4.76 minutes on average** in the 2024-25 and 2025-26 holdout. The production simulator misses by **6.17 minutes**, and it under-projects minutes by **2.4 minutes per game** (it projects starters about 3 minutes short). The difference is −1.43 min MAE, 95% CI [−1.48, −1.38], with the CI taken over games.
* **The challenger beats the incumbent simulator and the season-average baseline on every prop family**, in both validation and holdout, and none of the CIs come close to zero. Holdout CRPS against the incumbent (lower is better): points −0.38, rebounds −0.16, assists −0.09, threes −0.04, PRA −0.70, FGA −0.38. Most of the incumbent's error is a systematic **under-projection**: holdout bias is −1.22 points, −0.39 rebounds, −0.33 assists and −1.94 PRA. That is the "~20% prop-over bias" documented in `docs/HANDOFF_SESSION3.md`.
* **The probabilities at Kalshi-style rungs are calibrated.** For points on validation, predicted and realised hit rates are 0.479 vs 0.475 at 10+, 0.293 vs 0.290 at 15+, 0.165 vs 0.167 at 20+, 0.086 vs 0.088 at 25+ and 0.042 vs 0.043 at 30+. The incumbent predicts 0.453 at 10+ against a realised 0.492, and 0.066 at 25+ against 0.082. On the same holdout rows the challenger has lower Brier than the incumbent at every rung of every family.
* **The single biggest improvement still available is the injury report.** On 2025-26, using the archived point-in-time official report (T-60):
  * it lowers minutes error for players who play by 0.20 min, CI [−0.22, −0.17];
  * it cuts participation Brier from 0.132 to 0.087;
  * it lowers unconditional minutes error by 1.57 min.

  Knowing the actual starters would add another 0.17 min, but nobody archived lineups.
* **Readiness** comes from the fixed rules in §9:
  * minutes, points, rebounds, assists, threes, PRA and FGA are **READY**, as research projections conditional on the player playing;
  * team points is **SHADOW VALIDATION**, because there is no incumbent to compare it with.

  READY means the projection is accurate and calibrated enough to display. It does not give betting authority.

## 2. Data inventory

| Dataset | Seasons | Rows | Point-in-time class | Notes |
|---|---|---:|---|---|
| Player box scores (min, pts, reb, ast, 3PM, FGA, FTA, TOV, PF) | 2014-15..2025-26 | 371,876 | reconstructable | ESPN box via the sportsdataverse (hoopR) mirror on GitHub releases (raw files in gitignored `.cache/`). Agrees with the repo's `data/history/espn` on 2024-25: 32,610/32,610 rows, minutes identical (test `test_hoopr_mirror_agrees_with_repo_history`). Regular season only. |
| Usage proxy (FGA + 0.44 FTA + TOV) | same | 305,994 played | reconstructable | True usage% needs on-court possessions; PBP stints exist only for 2024-25/2025-26. |
| Team box / pace | same | 28,878 team-games | reconstructable | Possessions = 0.96·(FGA+0.44FTA−OREB+TOV), averaged over both teams. |
| Pregame candidate pool | same | 431,316 | reconstructable | Box rows plus 59,440 synthetic "absent" rows for players who played for the team in its last 10 games but are not in the box (injured, inactive, G-League). |
| Starting lineups | same | 144,412 starts | **retrospective** | The box `starter` flag is post-game. No pregame lineup archive exists, so only prior start rates are used. Its value is measured as an oracle (§5). |
| Official NBA injury reports (PDF, timestamped) | **2025-26 only** | 167,101 rows | **archived** | 1,320/1,322 games have a certified pre-tip snapshot (T-60 and last pre-tip). Missing for 2014-15..2024-25; box DNP reasons are retrospective. |
| ESPN injuries / rosters / schedule captures | 2026-27 preseason onward | — | archived | Captured on the `data-archive` and `data-injury-pit` branches with timestamps. Feeds the forward projector. |
| Rest / back-to-back / 3-in-4 | all | — | reconstructable | Computed from the schedule. |
| Travel / time zones | — | — | **missing** | No arena-coordinates table. Reconstructable from a 30-row static table; not built. |
| PBP stints | 2024-25, 2025-26 | 83,177 | reconstructable | Not used (only two seasons). |
| Archived pregame forecasts (incumbent) | 2026-27 preseason; 3,676 rows of 2025-26 | 3,676 | archived | Historical incumbent forecasts were **reproduced** walk-forward from `src/nba_edge` (see §4). |
| Kalshi NBA markets and candles | 2025-26 | 137,059 markets | archived | No pregame spread or total history before 2025-26, so blowout risk uses a point-in-time rating-based expected margin instead. |
| Shot-profile point-in-time features | 2023-24..2025-26 | 80,404 | reconstructable | Not used. |

**What counts as pregame.** Whether a player plays, or starts, is **not** pregame information unless it comes from an archived injury report or lineup. Each frame is labelled with what it conditions on:

* **Conditional frame** (players who played). This is the frame Kalshi props settle in, because a player who does not play settles at a fair price rather than as zero. It is also the frame the incumbent reports. It uses post-game information, namely "did play".
* **Unconditional frame** (the full candidate pool, where absent or DNP counts as 0). This applies the participation hurdle.
* **The effect of conditioning on points** (holdout, best model):
  * conditional MAE is 4.52;
  * unconditional MAE is 4.17 when the forecast is P(play)·E[pts | play]. It is lower because 32% of candidate rows are zeros, and easy ones;
  * it rises to 5.25 if one assumes everybody plays.

  The archived injury report is what moves a projection from the unconditional frame toward the conditional one in production (§5).

## 3. Design

* **Splits.** Fixed before any evaluation:
  * development: 2015-16..2021-22, scored from 2016-17. 2014-15 is burn-in history only;
  * validation: 2022-23 and 2023-24, used to select models;
  * holdout: 2024-25 and 2025-26, scored once for the frozen winners.
* **Walk-forward.** Every feature uses strictly earlier dates. pf_core `lagged_features` shifts one game within each player, and team ratings are refit weekly on earlier blocks. LightGBM is refit each season on the previous five seasons. OLS coefficients, stack weights, shrinkage strengths, opponent elasticities and distribution parameters are fitted on development only and then frozen.
* **Metrics.** CRPS, log score, randomised-PIT coverage and PIT-variance ratio (1 = calibrated; above 1 = too narrow). All comparisons are paired on the same rows, with **game-clustered bootstrap** 95% CIs (`pf_core.metrics.cluster_bootstrap_diff`, 1,000 resamples). There are about 2,460 games in each of validation and holdout.
* **Ladders.** A = season-to-date average shrunk to a position prior. B = EWMA shrunk. C = minutes × per-minute rate, with the rate shrunk in minutes units. D = C × opponent factor × pace factor. E = LightGBM. F = non-negative stack. E_inj (LightGBM plus teammate-absence features) is reported separately because its inputs require the injury report.

## 4. Incumbent reproduction

The production model is the incumbent: `features.build.build_game_params` plus `sim.engine.simulate` from `src/nba_edge`, with frozen `BuildConfig()` defaults and no injury input, as in the production prop walk-forward. It was **reproduced walk-forward for every regular-season game from 2022-23 to 2025-26**: 4,923 games, 2,000 simulations each, with history converted to the production schema and production code untouched. That gives 104,923 played player-games, 96% coverage. The players it does not cover are ones its rotation builder excluded. The simulator's draws are scored per player:

* the conditional-on-playing distribution, for minutes and every stat;
* P(play) and unconditional minutes.

The comparison is apples to apples. The incumbent and the challenger see the same history and no injury report. The challenger's E_inj, which uses the injury proxy, is never the comparator for the incumbent.

## 5. Minutes and opportunity (the priority)

#### minutes — best `E_lightgbm` — **READY**

| Model | Split | n | MAE | RMSE | Bias | CRPS | 80% cover | PIT var | CRPS vs A (baseline) | CRPS vs incumbent | Verdict |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| A_season_avg_shrunk | vali | 52,127 | 5.606 | 7.220 | -0.094 | 3.951 | 0.784 | 1.038 | baseline | -0.517 [-0.555, -0.482] | baseline |
| B_ewma_shrunk | vali | 52,127 | 5.197 | 6.694 | +0.100 | 3.639 | 0.790 | 1.026 | -0.313 [-0.334, -0.293] | -0.837 [-0.864, -0.809] | competitive |
| C_role_blend | vali | 52,127 | 5.022 | 6.534 | -0.029 | 3.562 | 0.790 | 1.028 | -0.389 [-0.411, -0.369] | -0.897 [-0.926, -0.871] | competitive |
| D_role_plus_context | vali | 52,127 | 4.995 | 6.492 | +0.002 | 3.539 | 0.788 | 1.028 | -0.412 [-0.435, -0.391] | -0.914 [-0.944, -0.886] | competitive |
| E_lightgbm | vali | 52,127 | 4.843 | 6.281 | +0.091 | 3.430 | 0.790 | 1.022 | -0.522 [-0.546, -0.497] | -0.988 [-1.022, -0.954] | best |
| F_stack | vali | 52,127 | 4.845 | 6.281 | +0.083 | 3.428 | 0.791 | 1.022 | -0.523 [-0.548, -0.499] | -0.990 [-1.024, -0.957] | competitive |
| E_inj (teammate-absence proxy) | vali | 52,127 | 4.618 | 5.976 | +0.143 | 3.273 | 0.798 | 1.003 | -0.679 [-0.706, -0.649] | -1.141 [-1.177, -1.105] | needs injury feed |
| ORACLE (knows starters) | vali | 52,127 | 4.454 | 5.755 | +0.103 | 3.155 | 0.799 | 0.997 | -0.797 [-0.827, -0.766] | -1.255 [-1.293, -1.218] | oracle, not pregame |
| incumbent_sim_rotation | vali | 50,171 | 6.058 | 7.940 | -2.308 | 4.404 | 0.810 | 0.925 | +0.517 [+0.482, +0.555] | — | incumbent |
| A_season_avg_shrunk | hold | 52,796 | 5.510 | 7.132 | -0.317 | 3.897 | 0.799 | 0.999 | baseline | -0.686 [-0.724, -0.651] | baseline |
| **E_lightgbm** | hold | 52,796 | **4.764** | 6.218 | +0.086 | **3.392** | 0.800 | 0.990 | -0.505 [-0.529, -0.479] | **-1.145 [-1.181, -1.110]** | best |
| E_inj (proxy) | hold | 52,796 | 4.547 | 5.918 | +0.305 | 3.238 | 0.807 | 0.975 | -0.658 [-0.688, -0.628] | -1.293 [-1.332, -1.255] | needs injury feed |
| ORACLE (knows starters) | hold | 52,796 | 4.379 | 5.689 | +0.262 | 3.118 | 0.810 | 0.970 | -0.779 [-0.808, -0.747] | -1.412 [-1.454, -1.373] | oracle |
| incumbent_sim_rotation | hold | 50,615 | 6.168 | 8.130 | -2.419 | 4.523 | 0.819 | 0.906 | +0.686 [+0.651, +0.724] | — | incumbent |

Notes on this table:

* E was chosen by validation MAE, 4.843 against F's 4.845, because it feeds C's minutes term. The stack puts 0.90 weight on E.
* The conditional minutes distribution is an empirical residual distribution binned by the forecast. Its 80% coverage is 0.800 on holdout.

**Bias by role and minutes bucket (validation):**

| Segment | n | EWMA (B) bias | E bias | Incumbent bias |
|---|---:|---:|---:|---:|
| bench, projected <12 min | 7,018 | +2.31 | +0.34 | −3.27 |
| bench, 12–20 | 12,242 | +0.52 | +0.33 | −1.76 |
| starter role, 28–34 | 11,279 | −0.81 | −0.11 | −3.04 |
| starter role, 34+ | 5,545 | −0.93 | −0.07 | −3.27 |

The EWMA over-projects fringe players and under-projects heavy-minute starters, which is regression to the mean in the wrong direction. LightGBM removes both. The incumbent is short everywhere, worst on starters.

**DNPs and the hurdle (unconditional frame, candidate pool; the play rate is 68%):**

| | Validation | Holdout |
|---|---:|---:|
| P(play) Brier, LightGBM hurdle | **0.121** | **0.125** |
| P(play) Brier, EWMA participation rate | 0.160 | 0.167 |
| P(play) Brier, incumbent / ours on the incumbent's rows | 0.168 / 0.116 | 0.174 / 0.121 |
| Hurdle ECE | 0.004 | 0.008 |
| Unconditional minutes MAE, ours / EWMA | 5.80 / 7.28 | 5.97 / 7.51 |
| Unconditional MAE vs incumbent (same rows) | −0.76 [−0.80, −0.71] | −0.84 [−0.88, −0.79] |
| 80% coverage of the hurdle mixture | 0.802 | 0.805 |

**Injury information (the proxy, then the real point-in-time report):**

* *Proxy, validation.* Teammate-absence features computed from who is missing from the box: E_inj vs E is −0.225 min MAE, CI [−0.244, −0.205]. The absences that matter most are new ones, meaning teammates who played the previous game: −0.32 min on those rows.
* *Real point-in-time report, 2025-26.* The same LightGBM, trained 2020-21..2024-25, was scored with features built from the archived **T-60 official report**:
  * MAE 4.559 with the report, against 4.755 without injury information: −0.196, CI [−0.224, −0.171];
  * MAE 4.548 with the proxy. The report vs the proxy is +0.011, CI [−0.001, +0.024];
  * the report's "out minutes" correlate 0.90 with the proxy's.

  **The retrospective proxy is therefore not a leakage artefact: the real pregame report recovers essentially all of it.**
* *How the report statuses relate to who actually played* (2025-26 candidate rows):

  | Status | Rows | Played |
  |---|---:|---:|
  | OUT | 5,626 | 0.04% |
  | DOUBTFUL | 145 | 0% |
  | QUESTIONABLE | 1,041 | 57% |
  | PROBABLE | 426 | 92% |
  | Unlisted | — | 82% |

  OUT plus DOUBTFUL identify 74% of absences, with 82% precision.
* *The report in the hurdle.* A logistic recalibration of the hurdle with status dummies was fitted on games before 2026-01-15 and scored on later games:
  * Brier fell from 0.132 to **0.087**: −0.045, CI [−0.049, −0.042];
  * unconditional minutes MAE fell from 6.27 to **4.70**: −1.57, CI [−1.67, −1.47].
* *Starters (oracle).* Adding the actual starter flag cuts another 0.17 min, CI [−0.18, −0.15] (holdout). This is the ceiling for a confirmed-lineup feed, which does not exist historically.
* *Team minutes budget.* Forcing each team's expected minutes to total 240 (+OT) changes MAE by +0.009, CI [−0.003, +0.019], so it is **rejected**.

## 6. Stat families

All results are conditional on playing, and the minutes term uses the pregame LightGBM minutes forecast. Every rung gets a negative-binomial distribution whose dispersion is binned by the mean. The best rung, chosen by validation CRPS, then gets the distribution family that wins on validation log score (§7).

#### points — best `E_lightgbm + empirical` — **READY**

| Model | Split | n | MAE | RMSE | Bias | CRPS | 80% cover | PIT var | CRPS vs A | CRPS vs incumbent | Verdict |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| A season avg shrunk | vali | 52,127 | 4.750 | 6.155 | -0.083 | 3.325 | 0.755 | 1.107 | baseline | -0.187 [-0.204, -0.169] | baseline |
| B EWMA shrunk | vali | 52,127 | 4.692 | 6.074 | +0.095 | 3.272 | 0.754 | 1.107 | -0.052 [-0.059, -0.046] | -0.239 [-0.255, -0.223] | competitive |
| C minutes × rate | vali | 52,127 | 4.547 | 5.943 | +0.093 | 3.181 | 0.763 | 1.091 | -0.144 [-0.155, -0.133] | -0.309 [-0.326, -0.292] | competitive |
| D opponent-adjusted | vali | 52,127 | 4.537 | 5.931 | +0.071 | 3.175 | 0.763 | 1.093 | -0.149 [-0.160, -0.138] | -0.315 [-0.331, -0.298] | competitive |
| **E LightGBM + empirical** | vali | 52,127 | 4.519 | 5.911 | +0.066 | **3.159** | 0.799 | 1.002 | -0.166 [-0.177, -0.155] | -0.330 [-0.348, -0.314] | best |
| F stack | vali | 52,127 | 4.525 | 5.914 | +0.061 | 3.167 | 0.762 | 1.092 | -0.158 [-0.168, -0.148] | -0.323 [-0.340, -0.306] | competitive |
| E_inj (proxy) | vali | 52,127 | 4.443 | 5.818 | +0.073 | 3.110 | 0.763 | 1.092 | -0.215 [-0.227, -0.203] | -0.379 [-0.397, -0.361] | needs injury feed |
| incumbent sim | vali | 50,171 | 4.878 | — | **-1.243** | 3.527 | 0.790 | 0.985 | +0.187 | — | incumbent |
| A season avg shrunk | hold | 52,796 | 4.750 | — | -0.232 | 3.341 | 0.751 | 1.118 | baseline | -0.229 [-0.248, -0.210] | baseline |
| **E LightGBM + empirical** | hold | 52,796 | **4.518** | — | -0.033 | **3.166** | 0.792 | 1.015 | **-0.176 [-0.187, -0.165]** | **-0.383 [-0.401, -0.366]** | best |
| E_inj (proxy) | hold | 52,796 | 4.454 | — | +0.129 | 3.117 | 0.762 | 1.098 | -0.224 [-0.238, -0.210] | -0.431 [-0.451, -0.412] | needs injury feed |
| incumbent sim | hold | 50,615 | 4.933 | — | **-1.222** | 3.590 | 0.795 | 0.978 | +0.229 | — | incumbent |

For the other families, one line each. These are holdout figures for the frozen best model. Full validation and holdout tables are in `results/tables_nba.md`, and the CIs are in `summary.json`.

| Family | Best (distribution) | Holdout n | MAE | Bias | CRPS | 80% cover | PIT var | CRPS vs A | CRPS vs incumbent | Incumbent bias | Readiness |
|---|---|---:|---:|---:|---:|---:|---:|---|---|---:|---|
| rebounds | F stack (minutes mixture) | 52,796 | 1.870 | +0.005 | 1.295 | 0.789 | 1.025 | −0.058 [−0.063, −0.054] | −0.159 [−0.166, −0.152] | −0.390 | READY |
| assists | E LightGBM (mixture) | 52,796 | 1.323 | +0.000 | 0.900 | 0.797 | 1.008 | −0.037 [−0.040, −0.035] | −0.089 [−0.094, −0.085] | −0.329 | READY |
| threes | F stack (mixture) | 52,796 | 0.882 | −0.006 | 0.581 | 0.792 | 1.021 | −0.014 [−0.015, −0.012] | −0.036 [−0.038, −0.034] | −0.139 | READY |
| PRA | E LightGBM (NB) | 52,796 | 5.923 | −0.028 | 4.176 | 0.771 | 1.068 | −0.308 [−0.326, −0.289] | −0.700 [−0.728, −0.673] | −1.942 | READY (slightly narrow) |
| FGA (usage) | E LightGBM (mixture) | 52,796 | 2.723 | +0.000 | 1.914 | 0.800 | 0.996 | −0.161 [−0.170, −0.152] | −0.378 [−0.392, −0.366] | −1.137 | READY |

How the ladder behaves:

* The order is the same in every family: C (minutes × rate) is the big step, then D adds a little, then E adds a little more.
* A versus B, average versus recency, matters least for threes, where the difference is −0.002 CRPS.
* The gap between the incumbent and the challenger comes mostly from the minutes under-projection, not from rates. The incumbent's CRPS is worse than even the season-average baseline in every family.

**Team points and reconciliation.** These are scored on team-games.

| Model | Split | n | MAE | Bias | CRPS | 80% cover | CRPS vs A |
|---|---|---:|---:|---:|---:|---:|---|
| A season avg shrunk | vali | 4,922 | 9.666 | -0.805 | 6.844 | 0.807 | baseline |
| B EWMA | vali | 4,922 | 9.593 | -0.285 | 6.790 | 0.804 | -0.055 [-0.088, -0.021] |
| C pace × efficiency (ridge) | vali | 4,922 | 9.443 | -0.993 | 6.664 | 0.805 | -0.180 [-0.266, -0.094] |
| **D C + rest/back-to-back** | vali | 4,922 | 9.406 | +0.565 | 6.641 | 0.804 | -0.204 [-0.295, -0.116] |
| A | hold | 4,924 | 9.950 | -0.492 | 7.038 | 0.785 | baseline |
| **D** | hold | 4,924 | **9.460** | +0.702 | **6.698** | 0.794 | **-0.339 [-0.420, -0.251]** |

* The pace and efficiency ratings are schedule-adjusted ridge ratings (pf_core `rolling_ridge_ratings`).
* The development-fitted rest terms are −0.70 points for the team on a back-to-back and +1.10 points when the opponent is on one.
* No incumbent team-points projection was extracted, so this family is SHADOW VALIDATION.
* **Reconciliation.** The sum of P(play) × E[pts | play] over the candidate pool, divided by the team projection:
  * mean ratio 1.000 on validation (5–95%: 0.88–1.12) and 1.001 on holdout;
  * gate statuses on validation: PASS 4,730, REVIEW 191, BLOCK 1;
  * the bottom-up sum is less accurate than the team model (MAE 10.5 vs 9.4), so the team model owns team totals and the sum is a consistency check.

  In the forward slate the check fires for real: Philadelphia's listed roster sums to 171 player points against a team projection of 112, because each newly acquired player carries his previous team's role. Those players' points and PRA projections are BLOCKed until this season's data arrives (§10).

## 7. Distributions and calibration

These are validation results for each family's best mean, with all parameters fitted on development.

| Family | Poisson | NB (binned) | Normal | Empirical | Minutes mixture | Single-minutes NB | Chosen |
|---|---|---|---|---|---|---|---|
| points | logS 3.653, cover 0.50, PITvar 1.69 | 3.019 / 0.77 / 1.09 | 3.002 / 0.79 / 1.03 | **2.993 / 0.80 / 1.00** | 3.056 / 0.72 / 1.18 | 3.229 / 0.64 / 1.37 | empirical |
| rebounds | 2.197 / 0.72 / 1.19 | 2.149 / 0.80 / 1.00 | 2.195 / 0.81 / 0.98 | 2.170 / 0.80 / 0.99 | **2.141 / 0.79 / 1.02** | 2.185 / 0.73 / 1.16 | mixture |
| assists | 1.735 / 0.76 / 1.10 | 1.717 / 0.80 / 1.00 | 1.773 / 0.79 / 1.00 | 1.739 / 0.80 / 0.99 | **1.714 / 0.80 / 1.00** | 1.727 / 0.77 / 1.06 | mixture |
| threes | 1.265 / 0.78 / 1.04 | 1.256 / 0.80 / 1.00 | 1.313 / 0.78 / 1.02 | 1.276 / 0.80 / 0.99 | **1.254 / 0.79 / 1.01** | 1.262 / 0.79 / 1.03 | mixture |
| PRA | 4.101 / 0.49 / 1.72 | **3.355 / 0.77 / 1.07** | 3.367 / 0.80 / 1.01 | 3.391 / 0.79 / 1.02 | 3.373 / 0.74 / 1.13 | 3.687 / 0.60 / 1.46 | NB |
| FGA | 2.661 / 0.69 / 1.25 | 2.575 / 0.79 / 1.01 | 2.604 / 0.80 / 0.99 | 2.604 / 0.80 / 1.01 | **2.568 / 0.80 / 0.99** | 2.661 / 0.69 / 1.25 | mixture |

Each cell is log score / randomised 80% coverage / PIT-variance ratio, where 1 = calibrated and >1 = overconfident.

* **Poisson is badly overconfident for scoring.** For points, its 80% interval covers only 50%.
* **Propagating minutes uncertainty matters.** A single NB at the mean minutes, with the dispersion that holds when minutes are known, is overconfident everywhere: PIT variance 1.37 for points and 1.46 for PRA.
* **The mixture over minutes scenarios is the best family for rebounds, assists, threes and FGA.**
* **For points and PRA the mixture is still slightly narrow** (PIT variance 1.18 and 1.13), because shooting variance given minutes is not NB-shaped. The empirical quantile mapping (points) and binned NB (PRA) win there. PRA's chosen NB is slightly narrow on holdout (80% coverage 0.771). The discretised normal is better calibrated (0.80) but has a worse log score, which is recorded as a known trade-off.
* **Rungs.** Predicted against realised hit rates on validation:

  | Family | Rung | Predicted | Realised |
  |---|---|---:|---:|
  | rebounds | 8+ | 0.146 | 0.150 |
  | assists | 6+ | 0.122 | 0.126 |
  | threes | 3+ | 0.163 | 0.166 |
  | PRA | 30+ | 0.166 | 0.171 |
  | FGA | 15+ | 0.164 | 0.167 |

  On the same holdout rows the challenger's Brier beats the incumbent's at every rung. For example, points 10+ is 0.159 against 0.175 and threes 1+ is 0.165 against 0.186. The incumbent's probabilities sit below the realised rates at every rung.

## 8. Opponent adjustment and pace

For each player, D multiplies C by two factors:

* **Opponent factor**, specific to the player's position (G/F/C): the opponent's EWMA (half-life 20 games) of actual over expected production allowed to that position. The expectation is player-specific, which acts as a schedule adjustment. The factor is shrunk toward 1 with k = 5–10 games and raised to an elasticity β fitted on development.
* **Pace factor**: expected game pace, from ridge ratings, divided by the team's own EWMA pace.

| Family | k (games) | β opponent | β pace | Validation D−C CRPS | Holdout D−C CRPS | Factor sd |
|---|---:|---:|---:|---|---|---:|
| points | 10 | 0.66 | 0.26 | −0.0052 [−0.0072, −0.0030] | −0.0084 [−0.0105, −0.0064] | 0.031 |
| rebounds | 5 | 0.60 | 0.25 | −0.0019 [−0.0027, −0.0010] | −0.0033 [−0.0042, −0.0025] | 0.031 |
| assists | 5 | 0.63 | 0.14 | −0.0017 [−0.0024, −0.0010] | −0.0035 [−0.0042, −0.0027] | 0.045 |
| threes | 5 | 0.59 | 0.21 | −0.0010 [−0.0014, −0.0006] | −0.0010 [−0.0014, −0.0006] | 0.061 |
| PRA | 10 | 0.71 | 0.21 | −0.0093 [−0.0125, −0.0060] | −0.0180 [−0.0217, −0.0143] | 0.029 |
| FGA | 5 | 0.66 | 0.22 | −0.0042 [−0.0057, −0.0026] | −0.0042 [−0.0056, −0.0027] | 0.028 |

* **Verdict: the effect is real but small.** Every family improves with the CI below zero in both validation and holdout, but the gain is 0.1–0.4% of CRPS, against 4–5% for the minutes × rate step.
* A typical matchup moves a projection by about ±3–6%. Matchup stories should not outweigh minutes and role.
* At team level, schedule-adjusted pace × efficiency is where opponent quality pays (team D vs A: −0.34 CRPS on holdout).

## 9. Readiness

The rules were fixed in `nba/summarize.py` before the holdout was scored:

* **READY**: the best model beats both baseline A and the incumbent on holdout CRPS with the CI entirely below 0, holdout 80% coverage is in [0.76, 0.84], PIT variance is in [0.85, 1.15], and |bias| ≤ 5% of the mean.
* **SHADOW VALIDATION**: it beats both but fails a calibration band, or no incumbent exists.
* **NEEDS IMPROVEMENT**: it does not beat the baseline or the incumbent.
* **INSUFFICIENT DATA**: fewer than 2,000 holdout rows.

| Family | Readiness | Why |
|---|---|---|
| minutes | READY | Beats A by −0.51 CRPS and the incumbent by −1.15 CRPS. Coverage 0.80, PIT variance 0.99. Participation still needs the live report. |
| points | READY | Beats A by −0.18 and the incumbent by −0.38. Coverage 0.79, PIT variance 1.02. |
| rebounds | READY | Beats A by −0.06 and the incumbent by −0.16. Coverage 0.79. |
| assists | READY | Beats A by −0.04 and the incumbent by −0.09. Coverage 0.80. |
| threes | READY | Beats A by −0.014 and the incumbent by −0.036. Coverage 0.79. |
| PRA | READY | Beats A by −0.31 and the incumbent by −0.70. Coverage 0.77, at the edge of the band. |
| FGA / usage | READY | Beats A by −0.16 and the incumbent by −0.38. Coverage 0.80. |
| team points | SHADOW VALIDATION | Beats A by −0.34, but there is no incumbent comparison. Coverage 0.79. |

Caveats that apply to every READY:

* the projections are conditional on the player playing;
* they assume a live injury feed;
* they are not evidence of any edge over Kalshi prices;
* authority stays research_only.

## 10. Quality gate

`pf_core.gate.evaluate` was run on 15,000 sampled player-games per family and split, for the best model. Its inputs were:

* the pmf-derived thresholds;
* projected minutes as the opportunity;
* the previous 10 games of minutes as `opportunity_history`;
* the previous 10 games of the statistic as `stat_history`;
* the opponent factor and its sample size;
* the player's own game count;
* timestamps that mimic the daily pipeline: inputs as of 10:00 UTC on game day, evaluated 1 h before tip.

Injury status comes from the archived T-60 report for 2025-26. Before 2025-26 there is no point-in-time injury source, so every one of those rows gets the gate's "no injury status" REVIEW. That is correct for production, but it is structural to the backtest, so status counts are shown both with and without that single finding.

| Family | Split | Raw status (incl. no-injury-feed REVIEW) | Status excluding the no-feed finding | MAE PASS / REVIEW | Bias PASS / REVIEW |
|---|---|---|---|---|---|
| points | holdout | PASS 7,209 · REVIEW 7,790 · BLOCK 1 | PASS 14,729 (98.2%) · REVIEW 270 · BLOCK 1 | 4.51 / 3.01 | −0.01 / **+0.24** |
| rebounds | holdout | PASS 7,206 · REVIEW 7,793 · BLOCK 1 | PASS 14,727 · REVIEW 272 · BLOCK 1 | 1.87 / 1.42 | +0.02 / +0.20 |
| assists | holdout | PASS 7,209 · REVIEW 7,790 · BLOCK 1 | PASS 14,734 · REVIEW 265 · BLOCK 1 | 1.34 / 0.81 | +0.01 / +0.07 |
| threes | holdout | PASS 6,447 · REVIEW 8,552 · BLOCK 1 | PASS 13,085 · REVIEW 1,914 · BLOCK 1 | 0.99 / 0.14 | −0.00 / +0.01 |
| PRA | holdout | PASS 7,209 · REVIEW 7,790 · BLOCK 1 | PASS 14,729 · REVIEW 270 · BLOCK 1 | 5.91 / 4.24 | −0.02 / **+0.52** |
| FGA | holdout | PASS 7,207 · REVIEW 7,792 · BLOCK 1 | PASS 14,720 · REVIEW 279 · BLOCK 1 | 2.73 / 2.06 | +0.02 / +0.39 |
| points | validation | REVIEW 15,000 (no feed) | PASS 14,743 · REVIEW 257 | 4.54 / 3.30 | +0.02 / **+0.61** |

* **REVIEW findings** are role checks (projected minutes far outside the player's recent range, about 1.7%), confidence checks (fewer than 3 games of evidence, or a very wide distribution, which covers most low-volume three-point shooters) and a few plausibility checks.
* **REVIEW rows are not higher-error rows in absolute terms.** They are mostly low-volume players. They do carry a systematic **over-projection**: +0.6 points and +0.7 PRA on validation, against about 0 for PASS rows. The "far above recent role" flag is doing its job. A ±1-game role signal is not enough evidence, and SIFT should show these rows with a wider range or hold them back.
* **BLOCK**: one player per family on holdout was listed OUT on the T-60 report and still played. The gate withholds such projections by design.
* **Team reconciliation** is in §6: on validation, PASS 4,730, REVIEW 191 and BLOCK 1 team-games.
* **Forward slate** (2026-10-20, 774 player-family rows):
  * points: PASS 25, REVIEW 79, BLOCK 25;
  * all families: injury BLOCK on 18 rows (3 players listed OUT);
  * team-consistency BLOCK on Philadelphia's points and PRA (players sum to 171 against a team projection of 112);
  * REVIEW otherwise for players with fewer than 3 games or a new role.

  Opening night is the hardest case for the gate (new rosters, no current-season games), and it flags it accordingly.

## 11. Root cause of the largest minutes errors

A "big miss" is an error of 10 or more minutes: **10.5% of player-games, carrying 29% of all absolute error** (validation, best model). The rows below tag misses with causes identified after the game.

| Pattern | Share of games | Share of big misses (lift) | MAE when present vs absent | Bias when present | Share of total abs. error | Status / action |
|---|---:|---:|---|---:|---:|---|
| New teammate absence (≥25 recent minutes out) | 28.6% | 40.0% (1.40) | 5.44 vs 4.60 | −1.57 | 32.2% | **Verified and fixable with the injury report.** E_inj on these rows: −0.32 min [−0.38, −0.27]; confirmed with the point-in-time report. |
| Role change (started when he usually doesn't, or the reverse) | 11.5% | 22.8% (1.98) | 6.42 vs 4.64 | −2.32 | 15.2% | **Verified. Needs confirmed lineups**, which are not archived. The oracle shows −0.17 min overall. |
| Early exit, then missed the next game (in-game injury) | 4.6% | 13.1% (2.87) | 8.84 vs 4.65 | +8.84 | 8.3% | Not a model defect. Unforecastable; carried by the residual distribution. |
| Overtime | 5.2% | 11.5% (2.23) | 7.08 vs 4.72 | −3.33 | 7.5% | Not a model defect. |
| Blowout (final margin ≥20) | 19.9% | 20.3% (1.02) | 4.92 vs 4.83 | +1.30 | 20.1% | **Ruled out as a disproportionate cause.** Rating-based expected-margin terms do not help (D vs C on high expected-margin rows: −0.02 [−0.05, +0.005]). A real pregame spread is needed. |
| Back-to-back | 16.7% | 19.4% (1.17) | 5.15 vs 4.78 | −0.08 | 17.7% | Ruled out. Back-to-back features already in D and E. |
| Return from 3+ missed games | 5.2% | 6.0% (1.16) | 5.18 vs 4.82 | +0.28 | 5.5% | Ruled out (small). |
| New team (<5 games) | 3.5% | 5.5% (1.57) | 5.68 vs 4.81 | +0.21 | 4.1% | Hypothesis. Matters most in early season and after trades. |
| Foul trouble (5+ fouls) | 5.2% | 5.6% (1.08) | 4.97 vs 4.84 | −2.05 | 5.3% | Ruled out (unforecastable). |

Development shows the same ranking: new teammate absence has lift 1.43, role change 2.08, early exit 3.13 and overtime 2.27.

**Usage changes** behave the same way. Teammate-absence (usage freed) features improve every stat family, with validation CRPS for E_inj against the best model of:

| Family | Change in CRPS |
|---|---:|
| points | −0.054 |
| PRA | −0.096 |
| FGA | −0.059 |
| rebounds | −0.015 |
| assists | −0.011 |
| threes | −0.003 |

**Pace** effects are real but small (§8).

## 12. Experiments

Every experiment has a JSON record in `results/experiments/` (pf_core `registry`) and appears in `summary.json → experiments`. Each entry gives the question, hypothesis, method and data; the numbers it found; and the decision.

1. **NBA-MIN-01: minutes ladder.**
   * *Question:* which pregame minutes forecast (conditional on playing) is most accurate?
   * *Hypothesis:* role and rotation features plus boosting beat a shrunk EWMA, which is the incumbent's EWM-5 analogue.
   * *Method:* ladder A–F, walk-forward.
   * *Data:* 2016-17..2025-26 played rows.
   * *Result:* LightGBM vs EWMA is −0.355 min MAE [−0.382, −0.327] on validation and −0.332 [−0.357, −0.305] on holdout. Against the incumbent it is −1.43 [−1.48, −1.38] on holdout.
   * *Interpretation:* every rung adds accuracy. The incumbent's minutes shortfall propagates into every stat.
   * *Decision:* **adopt**.
2. **NBA-MIN-02: participation hurdle.**
   * *Result:* Brier 0.121 vs 0.160 for the EWMA rate and 0.168 for the incumbent. Unconditional minutes MAE vs the incumbent −0.76 [−0.80, −0.71].
   * *Decision:* **adopt**.
3. **NBA-MIN-03: teammate absences.**
   * *Result:* −0.22 min with the proxy. With the real point-in-time report on 2025-26, −0.196 [−0.224, −0.171], indistinguishable from the proxy.
   * *Decision:* **adopt**, once the live report is wired in (priority 1).
4. **NBA-MIN-04: starter oracle.**
   * *Result:* −0.17 min.
   * *Decision:* **investigate**. A lineup capture is needed.
5. **NBA-MIN-05: team minutes budget normalisation.**
   * *Result:* +0.009 [−0.003, +0.019].
   * *Decision:* **reject**.
6. **NBA-<FAMILY>-LADDER, six families.**
   * *Result:* the best model beats A and the incumbent in validation and holdout (tables above).
   * *Decision:* **adopt**.
7. **NBA-<FAMILY>-OPP: opponent and pace.**
   * *Result:* small but consistent gains (§8).
   * *Decision:* **adopt** (kept inside D, E and F).
8. **NBA-<FAMILY>-DIST: distribution family and minutes propagation.**
   * *Result:* §7.
   * *Decision:* **adopt** the chosen family per stat.
9. **NBA-<FAMILY>-INJ: usage freed by absences.**
   * *Result:* gains in every family.
   * *Decision:* **adopt** for the injury-informed track.
10. **NBA-TEAM-01: pace × efficiency ridge model.**
    * *Result:* −0.34 CRPS [−0.42, −0.25] on holdout.
    * *Decision:* **adopt**.
11. **NBA-TEAM-02: player-team reconciliation.**
    * *Result:* consistent on average, 96% PASS.
    * *Decision:* **investigate**. One BLOCK per season, and the season-start roster churn case above.
12. **NBA-INJ-01: point-in-time injury report in the hurdle.**
    * *Result:* Brier −0.045 [−0.049, −0.042], unconditional minutes −1.57 [−1.67, −1.47].
    * *Decision:* **adopt**.

## 13. Failed experiments and what they taught

* **Team minutes budget** (water-filling to 240). No gain. The incumbent's core mechanism adds nothing on top of a good per-player model.
* **Blowout risk from ratings.** Linear expected-margin terms do not help. Blowouts cost +1.3 min of over-projection when they happen, but they are not over-represented among big misses. A real spread history is needed before modelling garbage time.
* **Single-minutes NB.** Pricing a prop off a distribution conditioned on the mean minutes is overconfident: PIT variance 1.37 for points, and 80% intervals that cover 64%. This is how the old simulator's 39% coverage for heavy-minute players happened.
* **Minutes mixture for points and PRA.** It is still too narrow (PIT variance 1.18 and 1.13); the marginal empirical or NB fits are better.
* **Process.** Two silent numerical failures were caught before results were frozen:
  1. a pandas all-NaN group sum returns 0, which made opponent factors infinite at the 2016-17 opener;
  2. `pf_core.models.fit_opponent_beta` silently returns its first golden-section probe, **0.4549**, when any base mean is NaN, so every family's β came out identical.

  Both were fixed in this package, without changing pf_core.

## 14. pf_core issues (reported, not edited)

1. **Look-ahead in fallbacks.** `models.group_prior_pit`'s default fallback is the *whole-sample* mean, and `pit.rolling_opponent_allowed` fills a missing league mean the same way. Both are look-ahead for the earliest date. This package now passes an explicit fallback taken from the burn-in season to every `group_prior_pit` call (`features.position_priors`, `team.fit_team`) and does not use `rolling_opponent_allowed`. The cached feature tables were computed with the default fallback, but **only 77 player rows and 6 team-games, all on the 2014-10-28 burn-in opening night, use it; no development, validation or holdout row does** (checked with `features.prior_fallback_rows`).
2. **`models.fit_opponent_beta`** returns 0.4549 (the first golden-section probe on (−0.5, 2)) without warning when `base_mu` or `y` contains NaN. Suggested fix: mask non-finite rows or raise.
3. **`pit.lagged_features`** raises pandas `PerformanceWarning: DataFrame is highly fragmented` on wide frames. This affects performance only.
4. **`metrics.cluster_bootstrap_diff`** would fail on NaN cluster ids, because `pd.factorize` returns −1 and `bincount` rejects negatives. This is an edge case and not hit here.

## 15. Forward projections

`python -m nba.project --archive <data-archive checkout> --date YYYY-MM-DD` writes `sift.projections.v1`. The example in `results/projections_latest.json` is the **2026-27 opening night (2026-10-20: BOS@DET, PHI@NYK, OKC@SAS)**:

* history runs through 2026-04-12;
* rosters and ESPN injuries come from the 2026-10-17 00:25 UTC capture;
* there are 129 players across 6 families plus minutes;
* the families' frozen models are taken from `results/frozen_params.json`;
* every player row carries pmf-derived rungs, minutes (opportunity), opponent factor, plain-English adjustments (including P(play)) and its gate result.

Opening night is the hardest case: rosters have changed and there are no current-season games yet. The gate flags the new-roster teams accordingly.

The workflow `.github/workflows/projection-foundation.yml` runs daily in season and on `workflow_dispatch`. It publishes to the orphan branch `projection-data`, at `projections/nba/latest.json`, a timestamped copy alongside it, and `summary/nba/latest.json`. It commits only when the content changes, and it stays inert until merged.

## 16. Priorities (ranked)

1. **Wire the live official injury report (T-60 and final) into the projector.** It is the single largest measured gain: participation Brier −0.045 and minutes −0.20 for players who play. The parser and archive already exist; today the projector uses ESPN statuses.
2. **Capture confirmed starting lineups pregame.** The oracle is worth −0.17 min beyond injuries, and no history exists, so collection has to start now.
3. **Shadow-run the challenger daily against Kalshi quotes in 2026-27.** This is the only way to learn whether better projections become better prices; the earlier market-vs-model result stands until then.
4. **Replace the production minutes model**, on a research branch first, with the LightGBM minutes plus hurdle. Holdout minutes MAE vs the incumbent is −1.43, and its systematic −2.4 minute bias is the root of the documented prop-over bias.
5. **Get a pregame spread and total history.** Kalshi covers 2025-26 only, and a sportsbook archive would be needed for earlier seasons. Without it, blowout and garbage-time minutes cannot be modelled.

## Reproduce

Run from `research/projection_foundation`:

```
python -m nba.incumbent 2023 2024 2025 2026     # incumbent reproduction (~1 h on 2 cores)
python -m nba.run_walkforward                     # data + features + ladders + evaluation (~1 h)
python -m nba.summarize                           # summary.json, frozen_params.json, experiments, tables
python -m nba.project --archive <dir> --date YYYY-MM-DD
python -m pytest tests/test_nba_pf.py tests/test_pf_core.py
```

## 17. Live shadow operation (2026-27)

`python -m nba.live.run --stage all --archive <projection-data checkout>` (workflow `.github/workflows/projection-foundation.yml`). Research only, authority `research_only`; the frozen models are unchanged.

**Schedule (ET, DST-safe)**: pregame 11:20, 17:20, 21:20 (after the afternoon / evening official-report updates, before tip); settle 06:40; light incumbent sweep hourly 21:50-03:50 UTC. Pull requests and `dry_run` dispatches run the whole chain on a temporary copy of the archive with read-only permissions.

**Availability sources and certainty** (`nba/live/availability.py`, `participation.py`):

| Source | Observation | Certainty |
|---|---|---|
| Official NBA injury-report PDF (`ak-static.cms.nba.com`, parser of the 2025-26 archive) | Out / Doubtful / Questionable / Probable / Available -> OUT / DOUBTFUL / QUESTIONABLE / PROBABLE / ACTIVE, per game | REPORTED (an official designation, not a lineup) |
| Same report, player not listed for a game it covers (team not "NOT YET SUBMITTED") | implicit ACTIVE (the study: unlisted played 82%) | PROJECTED |
| ESPN `/injuries` (athlete ids) | Out -> OUT, Day-To-Day -> QUESTIONABLE | PROJECTED (an official OUT is CONFIRMED_OUT; an ESPN-only OUT is LIKELY_OUT) |
| ESPN game summary starter flags, only within 150 min of tip | STARTING | PROJECTED (ESPN does not label them confirmed; CONFIRMED is reserved for a source that does) |
| Stated minutes restriction in a reason / comment | `restriction` LIMITED (+ cap) | as its source |

A player with no observation is UNVERIFIED (gate REVIEW). Precedence: official designation > newer ESPN OUT/DOUBTFUL > ESPN > implicit; an ESPN OUT the covering official report does not list becomes UNCERTAIN with the conflict spelled out. `data-injury-pit` (hourly official + ESPN captures) is the fallback when a live fetch fails.

**P(play)** = the frozen LightGBM hurdle recalibrated with the designation exactly as in section 5 (`nba/live/fit_participation.py`, coefficients frozen in `participation_calibration.json`; the study split reproduces Brier 0.132 -> 0.0868). Published inside `participation` on every row with its basis. Minutes use the report-aware `E_inj` model where the official report covers the game (study: -0.20 min on players who play) and the frozen `E` elsewhere; stat families keep their frozen best models.

**Team reconciliation gate** (`nba/live/reconcile.py`): per team-game, minutes are scaled to 241.5 when |sum p x E[min] / 241.5 - 1| > 12%, then scoring volume (points, FGA, threes; PRA by its points part) to the team projection when |sum / team - 1| > 15%; the result is graded by `gate.team_reconciliation`; what cannot be reconciled inside the scale limits stays BLOCK. On the real 2026-10-20 forward projection PHI (171 vs 112 points, 360 expected minutes) reconciles. Historical check on the study's out-of-sample predictions (`python -m nba.live.reconcile_eval`, 9,846 team-games): the gate acts on 4.8%; on those rows points MAE 4.774 -> 4.703 (paired CI -0.122..-0.019) but bias moves 0.00 -> -0.34 and minutes MAE 5.333 -> 5.381, i.e. it is a repair for incoherent rosters, not an accuracy gain on ordinary ones.

**Incumbent**: the `sim_rotation` arm of the PURE shadow store (frozen NBA_BASELINE_2026_PRESEASON_V1 simulator), read-only, archived as `model_role: incumbent` with its own `as_of`; it publishes a mean, quantiles and a threshold ladder (no pmf), so it is scored on MAE; its P(appear) is the incumbent `participation` forecast. **Results**: ESPN final box scores through the repo's history ingestion; a forecast player missing from the box or DNP has `participated=False` (void); the `participation` family is scored on every player.

**Kalshi regular-season player props** (reporting only): `python -m nba.live.kalshi_report`. Placeholder quotes (0.00 / 0.98-0.99 boundary quotes) are never executable prices (`executable_quote`).


## 18. Activation verification (2026-10-19): what the live evidence shows, and what is still missing

SIFT keeps the seven approved NBA families (minutes, points, rebounds, assists, threes, PRA, FGA) on the established engine until the official injury
report has been verified on a real slate. `python -m nba.live.activation_check --archive <projection-data checkout>` turns that requirement into checks over
the archive (and runs inside the `score` stage of every run, as a read-only report in the job summary). Verdicts: READY, PENDING (waiting on data),
BLOCKED (evidence present and wrong). It never promotes anything.

**Result on the first live run (projection-data, 2026-10-19T18:52Z, slate 2026-10-20 BOS@DET, PHI@NYK, OKC@SAS): BLOCKED by a defect, and PENDING on the league.**

| Requirement | Evidence on the live archive | Result |
|---|---|---|
| Official report fetched live, with provenance | `https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-19_02_45PM.pdf`, last-modified 18:45:05Z, report time 18:45Z, sha256 recorded; captured by the run at 18:52Z | PASS |
| Fresh, and covering the three games | published 0.1 h before the capture; all 3 games appear on it | PASS |
| **Player-level designations for games that have not started** | **all 6 teams "NOT YET SUBMITTED" (6 such rows, 0 designations), on every capture so far (01:30, 07:15, 13:45 ET, and the run's own)** | **PENDING: the remaining requirement** |
| Statuses, identity, report-aware minutes, ruled-out withheld on live rows | nothing to evaluate until the league publishes player rows | PENDING |
| Projection archived before the start, after the availability it used | 3 games archived, none late | PASS |
| **Every archived availability observation reaches the projection** | **16 ESPN observations (5 OUT, 11 QUESTIONABLE) were archived at 18:52:42Z and every one of those players was published UNVERIFIED, including Devin Carter (OUT), with no gate BLOCK** | **FAIL (defect, fixed here)** |

**The defect.** Stage timestamps are whole seconds and `pf_core.availability.asof` takes only observations captured *strictly before* the cut-off. The
project stage read its clock truncated to the second (18:52:42) while the ESPN capture had just been stamped 18:52:42, so a run never saw its own
capture: ruled-out players were projected (P(play) 0.75 for a player out indefinitely) until a later run. `nba.live.run.wall_clock()` now rounds the
stage clock *up* to the next whole second (never more than one second ahead of real time), so every stage's clock is later than anything an earlier
stage stamped. `test_a_just_captured_espn_out_reaches_the_projection_of_the_same_run` reproduces the stamp with recorded rows. The next scheduled run
publishes the corrected rows; `activation_check` then moves from BLOCKED to PENDING.

**Unreadable statuses.** The report parser only produced rows for the five status words the league prints; a player line with any other word was
dropped, which left the player "unlisted" and therefore implicitly available. The parser now records those lines (`unrecognized_status_rows`) and the
capture reads each as an uncertain QUESTIONABLE REPORTED designation (never available), counted as `rows_unknown_status`.

**Identity.** Report names that do not match the ESPN roster are counted; those that share a surname with a rostered teammate are flagged
`possible_identity_misses` (never guessed), and a non-zero count fails check B1.

**What activation needs, exactly.** (1) At least one capture in which teams have submitted player-level rows for games that have not started, normally the
first report the league posts for the next day's games. (2) That capture parsed with no possible identity miss and with every status classified.
(3) The next run publishes rows whose OUT players are BLOCK, whose uncertain players are REVIEW and whose available players are not blocked, with minutes on the
report-aware model. (4) `activation_check` reads READY on the real archive and SIFT's `scripts/verify-nba-activation.ts` agrees on the published feed. Then a
person changes the seven rows of SIFT's `projectionApprovals.ts` from APPROVED_PENDING_LIVE_INPUTS to PROMOTED. No correction for the historical minutes
bias is applied or needed: the challenger's holdout bias is +0.09 minutes.
