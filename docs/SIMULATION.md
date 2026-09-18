# SIMULATION.md — what the Monte Carlo engine does today

Scope: `src/nba_edge/sim/` (`params.py`, `minutes.py`, `engine.py`, `result.py`, `convergence.py`) at
`SIM_VERSION = "nba-sim-0.1.0"`. This is a description of the code as it is, not of what it should become.
Tests that enforce the invariants below live in `tests/test_sim_minutes.py`, `tests/test_sim_engine.py` and
`tests/test_pricing.py`; the shared synthetic game is in `tests/conftest.py`.

## 1. Inputs

The engine sees only `GameParams` (two `TeamParams`, each with a list of `PlayerParams`). Everything the feature
layer knows must be encoded there:

- `PlayerParams`: `p_play` (availability), `p_start` (start | play), `min_mean`/`min_sd`/`min_cap`
  (minutes | play, before redistribution), `fga_per_min`, shooting rates (`three_share`, `fg2_pct`, `fg3_pct`,
  `ft_pct`, `fta_per_fga`), share weights for secondary stats (`ast_weight`, `oreb_weight`, `dreb_weight`,
  `stl_weight`, `blk_weight`, `tov_weight`), `impact_ppp`, `minutes_dispersion`. `usage_elasticity` is declared
  but **not read** by the engine.
- `TeamParams`: `pace`, `off_ppp`, `def_ppp`, `oreb_pct`, `ast_per_fgm`, `tov_per_poss`, `blk_per_opp_2pa`,
  `b2b`, `rating_sd`. `rest_days` is declared but **not read**.
- `GameParams`: `neutral_site`, `pace_sd`, `ot_rate_target`, `quarter_shares`, `quarter_conc`.

`simulate(gp, n_sims, seed, batch=20000)` is deterministic given `(params, n_sims, seed, batch)`; changing `batch`
changes the draws. Draws are generated in batches by `simulate_batch` and concatenated by `concat_results`.

## 2. Draw structure (in execution order, all vectorised over draws)

1. **Possessions.** One value per draw, shared by both teams:
   `poss ~ max(N(mean_pace, pace_sd), 70)` with `mean_pace = (home.pace + away.pace)/2 - 1 per b2b team`.
2. **Game-environment shooting shock.** `env_shock ~ N(0, game_env_shock_sd)` on the logit scale, shared by both
   teams. This is what creates the positive home/away score correlation (~0.40 on the synthetic game).
3. **Per team** (home first, then away):
   1. Availability: `played_j ~ Bernoulli(p_play_j)`, independent across players.
   2. Starters: `Bernoulli(p_start_j)` among those who play; if the count is not exactly five, the five available
      players with the highest `p_start` (tiny random tie-break) are used instead. With fewer than five available,
      everyone available starts.
   3. Minutes: `N(min_mean, min_sd * minutes_dispersion)` clipped to `[0, min_cap]`, floor 0.5 for anyone who
      plays (applied *before* renormalisation, so a surplus row can scale it below 0.5; the guarantee that
      survives is minutes > 0 for everyone who plays), then **water-filled** to exactly 240: a deficit is distributed in proportion to each available
      player's headroom `(cap - m)`; a surplus is scaled down proportionally; nobody exceeds `min_cap`;
      unavailable players stay at 0. Six iterations, but a feasible row converges in one.
   4. Target efficiency: `ppp_mu = off_ppp + (opp.def_ppp - LEAGUE.ppp) ± home_ppp_edge/2 (unless neutral)
      - b2b_ppp_penalty (if b2b) + Σ_j (played_j - p_play_j) * impact_ppp_j + N(0, rating_sd)`.
      Note that `impact_ppp` enters only as the **surprise** relative to `p_play`: a star with `p_play = 0` moves
      nothing, because expected availability is assumed to be already priced into `off_ppp`.
   5. Team shooting shock: `N(0, team_shooting_shock_sd) + env_shock` (logit scale).
4. **Blowout pre-draw.** `pre_margin = poss*(mu_h - mu_a) + 0.55*poss*(shock_h - shock_a) + N(0, 8)`. Where
   `|pre_margin| >= blowout_margin` (18), each starter gives `blowout_starter_cut` (12 %) of their minutes to the
   bench, split in proportion to bench minutes; the team total stays 240. See limitation L3.
5. **Shooting** (per team; `_shoot`):
   - Team FGA: `rint(N(E[FGA], team_fga_resid_sd * sqrt(poss/pace)))` clipped to `[5, 140]`, with
     `E[FGA] = poss * (1 - tov_per_poss) / (1 + 0.44*mean(fta_per_fga) - 0.14)` (≈ 88.5 at 99 possessions).
   - Player FGA: multinomial split of team FGA with weights `minutes_j * fga_per_min_j`. This is where usage
     redistributes: absent players have zero minutes, so their share flows to teammates in proportion to
     `minutes * rate`. (`usage_elasticity` is not used.)
   - `FG3A ~ Binomial(FGA, three_share)`, `FG2A = FGA - FG3A`, `FTA ~ Poisson(FGA * fta_per_fga)`.
   - Efficiency: the baseline expected points from the rates are compared with the target `ppp_mu` and a
     multiplicative `factor = clip(ppp_mu / base_ppp, 0.75, 1.3)` is applied to `fg2_pct` and `fg3_pct` before
     the logit shocks (team shock + per-player `N(0, player_shooting_shock_sd)`); FT% gets half the shock.
     Make probabilities are clipped to `[0.05, 0.95]` (2PT), `[0.03, 0.85]` (3PT), `[0.30, 0.98]` (FT).
   - `FG2M`, `FG3M`, `FTM ~ Binomial`; `pts = 2*FG2M + 3*FG3M + FTM`.
6. **Endgame compression.** `move = rint(|margin| * endgame_compression / 2)` points are taken from the leader
   (multinomially, weights = each player's points, capped at their points) and given to the trailer (multinomially,
   weights = `max(pts, 1)` over players with minutes). Team points remain the sum of player points and the game
   total is unchanged (up to the cap-clipping of `take`); only the margin shrinks. See limitation L5.
7. **Regulation result and OT inflation.** `reg_h`, `reg_a` are the team sums. Natural ties go to overtime. If
   the natural tie rate in the batch is below `ot_rate_target`, near-ties (`|margin| ∈ {1, 2}`) are converted to
   ties with probability `q = (target - natural) / P(near)`, by subtracting the difference from the leader's top
   scorer (coherence preserved as long as that player had at least `|margin|` points).
8. **Quarters.** Each team's regulation points are split into four quarters with a Dirichlet-multinomial:
   `p ~ Dirichlet(quarter_shares * quarter_conc)`, `q ~ Multinomial(reg_pts, p)`. Quarters therefore always sum to
   regulation points, and `1H`, `2H`, `REG` slices exclude OT.
9. **Overtime** (up to `MAX_OT = 4` periods). Per OT: possessions `= poss * 5/48` (floor 3); minutes: 5 each to
   the five highest-minute players who have minutes > 0 (`_closing_minutes`); a fresh `_shoot` with the same
   `ppp_mu` and shock; period points recorded in `period_pts[:, :, 4+k]`; team minutes += 25. Still tied after four
   OTs: the home side gets +1 point, booked to home player index 0 and the last OT column (see bug B1).
10. **Secondary stats** on the full-game minutes (regulation + OT) and possessions `poss * (1 + n_ot*5/48)`:
    - OREB: `Binomial(own misses, oreb_pct)`; DREB: opponent misses not rebounded by the opponent's OREB%
      (`Binomial(opp misses, opp.oreb_pct)` complement). Split multinomially by `minutes * weight`.
    - AST: `Binomial(team FGM, ast_per_fgm)`; TOV: `Poisson(poss * tov_per_poss)`;
      STL: `Binomial(opp TOV, stl_share_of_opp_tov)`; BLK: `Binomial(opp FG2A, blk_per_opp_2pa)`; each split
      multinomially by `minutes * weight`.
11. **Player arrays.** For each player, every stat is masked to 0 where `played` is False (`min` to 0.0).

`SimResult` exposes `home_pts`, `away_pts`, `period_pts (n, 2, 8)`, `n_ot`, `possessions`, per-player
`PlayerSim(played, started, stats)` and derived `margin`, `total`, `team_pts/team_margin/period_total(period)`
and `PlayerSim.stat("pra"|"pr"|"pa"|"ra"|"double_double"|"triple_double")`.

## 3. Invariants the tests enforce (hold in every draw unless stated)

| # | Invariant | Test |
|---|-----------|------|
| I1 | `home_pts == Σ player pts (home)` and same for away | `test_team_points_equal_sum_of_player_points_every_draw` |
| I2 | Σ team minutes `== 240 + 25 * n_ot` (atol 1e-6), for both teams | `test_minutes_sum_to_240_plus_ot_every_draw` |
| I3 | `Σ quarters + Σ OT columns == team pts`; OT columns are 0 where `n_ot == 0`; regulation tied in every OT draw; unplayed OT columns are 0 | `test_period_points_structure` |
| I4 | `home_pts != away_pts` (no ties) | `test_no_draw_ends_tied`, `test_winner_probabilities_sum_to_one_exactly` |
| I5 | Exactly five starters per team; starters ⊆ played | `test_exactly_five_starters_per_team_every_draw`, `test_draw_starters_*` |
| I6 | Counting stats are non-negative integers; `reb == oreb + dreb`; `fg3m <= fga`; `0 <= min <= cap + 25` | `test_player_stats_are_nonnegative_integers` |
| I7 | `played == False` ⇒ all stats 0, minutes 0, not started; `played` ⇒ minutes > 0 | `test_absent_players_have_zero_stats_and_minutes` |
| I8 | `pra == pts + reb + ast`; `double_double`/`triple_double` computed from ≥10 in pts/reb/ast/stl/blk | `test_star_pra_and_double_double_consistent` |
| I9 | Same seed ⇒ bit-identical result; different seed ⇒ different | `test_same_seed_is_bitwise_identical`, `test_different_seed_differs` |
| I10 | Water-fill: sums to total, caps respected, zeros stay zero, deficit split by headroom, surplus scaled (property-tested with Hypothesis over feasible rows) | `test_water_fill_*` |
| I11 | Blowout adjustment keeps the team total, only touches rows with `\|margin\| >= 18`, moves minutes starters → bench only | `test_apply_blowout_*` |
| I12 | Pricing: `P(home) + P(away) == 1` exactly; spread/total/player ladders are monotone; `audit_ladders` is clean on simulator prices and flags corrupted ladders; `P(team_pts > X)` equals the direct numpy computation; `se == sqrt(p(1-p)/n)` | `test_pricing.py` |
| I13 | 1H points ≤ full-game points for each team and for the total | `test_first_half_pricing` |
| I14 | Player prop indicator is False where the player did not play; `p` is conditional on playing with `n = #played` | `test_player_prop_indicator_false_when_player_did_not_play` |

Distributional checks on the league-average synthetic game (40k draws, seed 1): OT rate in [3 %, 9 %]; margin sd in
[12, 16]; total sd in [17, 24]; team sd in [10.5, 14.5]; corr(star pts, team pts) > 0.3; corr(home, away) > 0.15;
questionable player plays 50 % ± 2 %. Directional checks: star out ⇒ every teammate's mean FGA, pts and minutes
rise and the team mean falls only modestly (in fact by ~0, see L2); b2b ⇒ fewer points, fewer possessions, lower
win probability; higher pace ⇒ higher total; mirrored matchup ⇒ home side wins more; neutral site ⇒ 50/50;
+0.05 `off_ppp` ⇒ P(win) > 0.62; questionable star with `impact_ppp = 0.03` ⇒ team scores ~3 more when he plays.

## 4. Known crude parts / limitations

- **L1 Independent availability.** `played_j` are independent Bernoullis. Correlated rest (several starters sat
  together), lineup-dependent minutes and "if A is out, B starts" logic are not modelled beyond the headroom
  water-fill.
- **L2 There is NO team-level injury response. This is the single most important limitation on this page.**
  A player being ruled out redistributes his minutes and shots to teammates (that part is real and measured),
  but it does **not** lower the team's expected efficiency, so team points, spread, total and moneyline barely
  move. Measured on the engine: ruling out a **29.7-ppg** star costs the team **0.68 points** and 2.3 points of
  win probability. The true figure for a star of that size is several points of spread.

  Two separate causes, one fixed and one open:
  1. *(fixed)* The availability term read `(played - p_play) * impact_ppp`, using **today's** `p_play` as the
     baseline. That is identically mean-zero — `(0-0)` for a player ruled out, `(1-1)` for a certain one — so the
     term could never shift the mean at any value of `impact_ppp`. Verified: `impact_ppp` of 0.0, 0.03 and 0.06
     gave byte-identical team means. The baseline is now `p_play_baseline`, the availability the trailing
     `off_ppp` rating was actually earned with, which is what that rating already prices in. With the fix,
     `impact_ppp = 0.06` moves a star's absence to −5.65 points and −14.3 points of win probability.
  2. *(open)* **`impact_ppp` is never estimated.** Nothing in `features/build.py` populates it, so it is `0.0`
     for every real player and the channel above carries nothing in production. Estimating it needs on/off or
     lineup data that is not yet ingested. Compounding it, `engine.py` rescales every player's shooting by
     `factor = clip(ppp_mu / base_ppp, 0.75, 1.3)` so realised efficiency tracks a roster-independent target —
     which actively renormalises roster quality away.

  Every `SimResult` therefore carries `diagnostics["team_injury_response_modeled"]`, which is `0.0` today. Do not
  read a slate as though injuries are priced into team efficiency. **No market family may be promoted above
  RESEARCH authority until `impact_ppp` is estimated and validated walk-forward.**
- **L3 Blowout rotations are almost decoupled from the realised score.** The pre-draw margin has sd ≈ 8.6 (rating
  and shock components contribute ≈ 3 of that), so `|pre_margin| >= 18` happens in ≈ 4 % of draws while the
  realised `|margin| >= 18` happens in ≈ 20 %; the two are correlated at roughly ρ ≈ 0.1. Starters lose < 0.5
  minutes each in realised blowouts (pinned as a strict xfail: `test_starters_play_fewer_minutes_in_realised_blowouts`).
- **L4 Quarter split ignores rotations and garbage time.** Points are split Dirichlet-multinomially with fixed
  shares; there is no minute-by-minute model, so quarter/half markets inherit only the game-level randomness plus
  Dirichlet noise (`quarter_dirichlet_conc = 60`), and 1H/2H are conditionally independent of who is on the floor.
- **L5 Endgame compression is a calibration hack.** A fixed 18 % of the raw margin is transferred leader → trailer
  so that margin sd lands near 13.5 while total sd stays near 19-21. It is not a possession-level endgame model
  and it slightly distorts individual scoring lines in lopsided draws (points are moved between players by
  multinomial draws weighted by points).
- **L6 Multinomial shares are under-dispersed.** Player FGA, OREB, DREB, AST, TOV, STL, BLK are multinomial splits
  of a team count, so a player's share has no game-to-game variance beyond binomial noise. Real shares vary more
  (matchups, foul trouble, hot hand, role changes).
- **L7 OT lineup heuristic.** OT minutes go 5 each to the five highest-minute players, regardless of who started
  or fouled out; OT possessions are `5/48` of regulation with no clutch adjustment. OT also reuses the same
  `ppp_mu` and shocks.
- **L8 Tie inflation is a book-keeping trick.** To hit `ot_rate_target`, some 1-2 point regulation results are
  turned into ties by removing points from the leader's top scorer. Regulation-only markets (`REG`, quarters)
  therefore have slightly fewer 1-2 point margins than the shot model alone would give.
- **L9 League constants are priors, not fitted.** All `LEAGUE` values are 2023-24..2025-26 era round numbers chosen
  so that the synthetic league-average game reproduces target dispersions; nothing here is estimated from
  `data/history` inside the engine.
- **L10 Fewer than six available players** breaks I2: the 42-minute caps make 240 infeasible and `water_fill`
  silently leaves the shortfall (e.g. four available ⇒ 168 minutes). OT minutes also come up short when fewer than
  five players have minutes.
- **L11 Convergence monitors are threshold-keyed.** The monitored total and player-points thresholds are derived
  from the running median/mean, so their keys can change between batches and silently drop out of the delta
  comparison (`p_home` and the fixed spread ladder always remain).
- Unused parameters: `PlayerParams.usage_elasticity`, `TeamParams.rest_days`.

## 5. Calibration constants (`LEAGUE` in `params.py`)

| Constant | Value | Role / what it is calibrated against |
|----------|-------|--------------------------------------|
| `pace` | 99.0 | possessions per team per 48 min (era prior) |
| `pace_sd` | 3.0 | game-level sd of realised possessions around expectation |
| `ppp` | 1.145 | league points per possession (ORtg ≈ 114.5); also the reference for `def_ppp` offsets |
| `home_ppp_edge` | 0.015 | ≈ 1.5 pts/100 total home edge, applied as ±0.0075 to each side |
| `b2b_ppp_penalty` | 0.020 | ≈ 2 pts/100 on the second night of a back-to-back (plus −1 possession) |
| `team_shooting_shock_sd` | 0.03 | logit-scale team shooting shock; with `team_fga_resid_sd` targets team pts sd ≈ 12.5 |
| `game_env_shock_sd` | 0.08 | logit shock shared by both teams; drives home/away correlation, hence total sd ≈ 19-21 vs margin sd ≈ 13.5 |
| `team_fga_resid_sd` | 2.0 | residual sd of team FGA given possessions |
| `endgame_compression` | 0.18 | fraction of raw margin transferred leader → trailer; calibrates margin sd ≈ 13.5 with total sd ≈ 19 |
| `player_shooting_shock_sd` | 0.06 | per-player logit shooting shock |
| `three_share`, `fg2_pct`, `fg3_pct`, `ft_pct`, `fta_per_fga` | 0.42, 0.545, 0.360, 0.785, 0.245 | default player shooting profile |
| `oreb_pct`, `ast_per_fgm`, `tov_per_poss` | 0.265, 0.62, 0.135 | team secondary-stat rates |
| `stl_share_of_opp_tov`, `blk_per_opp_2pa` | 0.55, 0.080 | steals and blocks as shares of opponent events |
| `ot_rate_target` | 0.055 | empirical OT rate ≈ 5.5 %; near-ties are inflated to reach it |
| `quarter_shares`, `quarter_dirichlet_conc` | (0.253, 0.247, 0.255, 0.245), 60.0 | quarter split mean and concentration |
| `blowout_margin`, `blowout_starter_cut` | 18, 0.12 | blowout threshold and starter minutes given up |
| `regulation_minutes`, `ot_minutes` | 240.0, 25.0 | team minutes per regulation / per OT |

Observed on the synthetic league-average game (40k draws, seed 1): team pts sd 12.4, margin sd 13.6, total sd 20.8,
OT rate 5.6 %, mean total 228.3, home/away correlation 0.40, P(home) 0.536.

## 6. How convergence picks `n_sims` (`convergence.py`)

`simulate_until_converged(gp, seed, target_se=0.004, target_delta=0.006, min_sims=20000, max_sims=200000,
batch=20000)`:

1. Simulate one batch, append, concatenate everything so far.
2. Compute the monitored probabilities on the cumulative result: `P(home)`, `P(margin > k)` for
   `k ∈ {±2.5, ±5.5, ±10.5}`, `P(total > median ± {5, 10})`, and for the four highest-scoring players
   `P(pts > round(mean) ± {0, 5} + 0.5)`.
3. `max_se = max sqrt(p(1-p)/n)` over the monitored set; `max_delta = max |p_now - p_prev|` over keys present in
   both the current and previous batch (∞ on the first batch, so at least two batches always run).
4. Stop when `n >= min_sims`, `max_se <= target_se` and `max_delta <= target_delta`, or when `n >= max_sims`
   (then `converged = False`).

With the defaults, `target_se = 0.004` requires `n >= 15,625` for a 50 % proposition, so `min_sims` already
satisfies the SE criterion and the second batch (40k) is usually where `max_delta` (sd ≈ 0.0025 per monitored key,
max over ~26 keys) clears 0.006; occasionally a third batch is needed. The `ConvergenceReport` records
`n_sims`, `converged`, `max_se`, `max_delta`, the final monitored dict and the per-batch history.

## 7. Bugs found while writing the tests (not fixed in `src/`)

- **B1** `engine.simulate_batch`: the post-`MAX_OT` tie-break does `h.pts[idx, 0] += 1` without checking
  `h.played[idx, 0]`; if home player index 0 is out, the player-level stat is masked to 0 while `home_pts` keeps
  the point, breaking I1. Reachable only after four tied OTs (very rare); reproduced by monkeypatching `MAX_OT = 0`
  (`test_max_ot_tiebreak_keeps_coherence_when_player0_out`, strict xfail).
- **B2** `engine.simulate_batch` sets `diagnostics["ot_rate"] = float(n_ot.mean() > 0)`, i.e. 1.0 whenever any
  OT occurred. `simulate()` and `simulate_until_converged()` overwrite it with the correct rate, so only direct
  callers of `simulate_batch` see it (`test_simulate_batch_ot_rate_diagnostic`, strict xfail).
- **B3** `minutes.water_fill` does not clip to caps when the row already sums to `total` (early `break` before
  the `np.minimum(m, caps)` line), so `raw = [50, 10, 10, 10]`, `caps = 42`, `total = 80` returns 50 for the first
  player. Unreachable from `draw_minutes` (raw is pre-clipped), but the docstring's cap guarantee is not
  unconditional.
- **B4** (design, see L3) the blowout pre-draw is nearly independent of the realised margin, so the blowout
  rotation logic has almost no effect on the joint distribution of starter minutes and margin.
