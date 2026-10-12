# Preregistration — W2 NBA participation and minutes (research only, no promotion)

Frozen **before** any held-out evaluation in this study. Committed on its own; the results document
cites this commit. Nothing below may change after the holdout run; deviations are reported as
deviations. No model is promoted by this study whatever the outcome; the champion stays frozen
`NBA_BASELINE_2026_PRESEASON_V1` (digest `5a4cbda0…193be78`).

## Questions

1. How much of the frozen V1 simulator's minutes error on the complete eligible population comes from
   (a) player-games that did not happen (DNP / inactive), and (b) minutes misallocation among players
   who did play? How much of (a) was knowable before tip from the official injury report?
2. Do point-in-time injury statuses, with the freed minutes redistributed (i) proportionally or
   (ii) by five-man lineup on/off weights from certified stints, reduce that error out of sample?

## Wave 1 findings carried forward unchanged

From `MATCHED_DECOMPOSITION.md` / `PREREG_W1_NBA_DECOMPOSITION.md` (merged PR #21): no material
full-population bias (points Σpred/Σactual 1.007); participation over-forecast (F_participation
1.053), minutes given play slightly low (0.979), per-minute rates compressed; **`RATE_PRIOR_5`
REJECTED, not promoted; blanket multiplier NO PROMOTION; injury R1 was BLOCKED_DATA**. This study does
not revisit rates or the rejected challenger; it uses the champion as-is and only touches participation
and minutes.

## Data (all committed or in PRs #22 / #23; sports data only, no market file is opened)

- Champion forecasts: `scripts/nba_matched_decomposition.py` machinery, `forecast_game(...,
  arms=("sim_rotation",))`, 2,000 draws, per-game seed sha256(game_id) — the exact W1 champion draws.
  Inputs: ESPN box history rows dated strictly before the game date (cutoff 00:00 ET).
- Injury statuses: PR #23 `game_snapshots_2025-26` / `report_rows_2025-26`, the **`t_minus_60`**
  snapshot only (latest official report whose PDF header time AND upload instant precede tip − 60
  min), used only where `t_minus_60_pit_ok`. Rows with `nba_id` (identity map: see PR #23's
  disclosure — the id lookup is a retrospective join; the status is point-in-time).
  `not_yet_submitted` rows carry no player and are ignored.
- Lineups: PR #22 `stints_2025-26.parquet`, rows with `certified == True`, from games whose ET game
  date is **strictly before** the forecast game's date. Never the forecast game's own stints.
- Outcome: box score minutes (`player_games_2025-26`); absent from the box ⇒ did not play, 0 minutes.

## Population and windows (chronological, regular season 2025-26)

- Eligible player-game: the champion's pre-tip roster rule (identical to W1). Ambiguous two-team
  players excluded as in W1. Players who play but were not eligible are counted and reported.
- **DEV (fitting / inspection): 2025-11-15..2026-01-31** (the 2025-26 W1 DEV block; the only DEV
  block with point-in-time reports).
- **HOLDOUT (scored once): 2026-02-01..2026-04-12**, every regular-season game (501).
- Disclosure: this holdout window was already scored once by W1 for a *different* challenger
  (`RATE_PRIOR_5`). The arms below are new and have not been evaluated on it; the window is not
  pristine for the champion itself. The champion's own known contamination (rotation PMF fitted on
  2023-24..2025-26) is inherited and disclosed in W1.

## Part 1 — descriptive error decomposition (champion only; DEV and HOLDOUT)

Per eligible player-game with appearance probability p (sim: available & minutes > 0), conditional
mean c = E[min | appear], unconditional mean μ = p·c and actual y:

- Squared and absolute error of μ split into rows with y = 0 (did not play) and y > 0 (played);
  for played rows the identity μ − y = −(1 − p)·c + (c − y) splits participation under-forecast from
  conditional-minutes error (cross term reported).
- DNP rows split by the T-60 status: listed **Out**; listed doubtful/questionable/probable/available;
  not listed. Share of DNP error carried by each.
- Oracle bounds on the champion's draws (CRPS, exact sample CRPS; MAE of the draw median; RMSE of the
  draw mean), *not forecasts* — upper bounds on what information could buy:
  - `O_part`: appearance known (DNP → all-zero draws; played → the champion's conditional draws);
  - `O_part_total`: `O_part`, then each played player's conditional draws scaled so the team's
    conditional means sum to the team's actual box minutes (removes team-total error, leaves
    within-team allocation error). Target = Σ actual minutes of that team's *eligible* players who
    played (non-eligible minutes are excluded and reported). A played player with no appearing draw
    keeps the champion's draws in both oracles.
  The CRPS gap champion → `O_part` is attributed to (a); what remains under `O_part` to (b), with
  `O_part_total` splitting (b) into team-total vs within-team allocation.

## Part 2 — challenger arms (identical rows, draws and seeds)

All arms start from the champion's 2,000 draws for the game. Per-draw operations; minutes per draw
are clipped at 48 (clipped minutes are reported, not re-assigned).

| arm | definition |
|---|---|
| `champion` | frozen V1 draws, unchanged |
| `pit_prop` | T-60 status applied: **Out** → all draws 0. **Doubtful / Questionable / Probable** → target appearance rate π_s fitted on DEV (empirical appearance rate of eligible player-games with that T-60 status); if the champion's p > π_s, each appearing draw is kept with probability π_s / p (seeded sha256(game_id+"pit")), else unchanged. Available / unlisted unchanged. In each draw the removed minutes go to the team's remaining players who appear in that draw, **in proportion to their minutes in that draw** |
| `pit_lineup` | same participation changes; removed minutes of absent player A go to appearing teammates B in proportion to the lineup weight w_AB = max(0, s_B\|A off − s_B\|A on), where s_B\|A off (on) is the fraction of the team's certified on-court seconds with A off (on) court during which B was on, over certified 2025-26 games of that team dated before the forecast date. Fallback to the `pit_prop` rule for A when A has < 600 certified on-court or off-court team seconds, or Σ w over the draw's appearing teammates is 0 |

Fitted on DEV only: π_doubtful, π_questionable, π_probable (and, for the record, the Out appearance
rate, expected ≈ 0, which is not used — Out is set to 0). Values are frozen in an addendum commit
*before* the holdout is collected. No other parameter is tuned; the 600-second floor and the 48-minute
clip are fixed here.

## Metrics (minutes only; one row per eligible player-game)

- **Primary: unconditional minutes CRPS** (exact sample CRPS over 2,000 draws), all eligible
  holdout player-games, paired arm − champion.
- Secondary: MAE of the draw median; RMSE and bias of the draw mean; Brier of P(appear); Brier of
  P(minutes ≥ 10); p10–p90 coverage; the same restricted to (i) teams with ≥ 1 eligible player listed
  Out at T-60 and (ii) rows actually played (outcome-selected, diagnostic only).
- Uncertainty: paired game-clustered bootstrap, 1,000 resamples, seed 20261010, 95% percentile CI.

## Decision rules (evidence labels only; nothing is promoted)

1. `pit_prop` / `pit_lineup` **reduce minutes error** if holdout ΔCRPS < 0 AND ΔMAE < 0 with both
   CIs excluding 0, and Brier P(appear) is not worse with CI excluding 0. Otherwise "not shown".
2. Lineup weights **add over proportional** redistribution if `pit_lineup` − `pit_prop` ΔCRPS < 0 with
   CI excluding 0 and ΔMAE not worse with CI excluding 0. Otherwise "not shown".
3. Any positive result is a research finding to be re-tested prospectively (2026-27 capture), never a
   promotion; counting-stat effects are out of scope and not claimed.

## Run plan

1. This file, committed alone.
2. `scripts/nba_participation_study.py collect --window dev`, fit π_s, record them and the DEV
   numbers in an addendum commit (still before holdout).
3. `collect --window holdout`, `report`; results in `docs/research/PARTICIPATION_MINUTES_W2.md` and
   `docs/research/w2_nba_participation/*.json`, citing both commits.
