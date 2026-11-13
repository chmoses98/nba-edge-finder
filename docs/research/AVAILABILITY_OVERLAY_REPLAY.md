# PIT availability overlay: 2026-27 historical replay (RESEARCH_ONLY, NO PROMOTION)

**Question.** Alpha postmortem 001 (`sift-alpha/docs/alpha_eval/NBA_POSTMORTEM_001.md` §4) found **1,626**
projected player-games whose player never appeared in the box score, including **728** with no official
injury report in the archive window. Why does that happen, how much of it was knowable before tip, and
what does fixing it buy?

**Cause.** The frozen shadow arms (`sim_rotation`, `ewm5`) never read an injury report:
`PARTICIPATION_SOURCE = "proxy_recent_team_games_no_injury_report"`. Participation comes only from recent
team games. PR #101 fixed injury selection for the **live pricing path** (`workflows/simulate.py`) only.
The W2 study (`PARTICIPATION_MINUTES_W2.md`) validated PIT statuses on 2025-26 but was never wired in.

**Fix (this PR).** `nba_edge.availability.overlay` post-processes `pure_forecast.v1` rows, using only
`sift.availability.v1` records captured at or before each projection's own `as_of`. It never edits a
frozen arm; affected rows carry `model_version += "+pit-availability-overlay-v1"` and an `x_availability` block.

| status at `as_of` (latest official snapshot for the game and team) | P(play) |
|---|---|
| official OUT | 0, suppressed |
| **not on the report's roster** (team covered, player absent) | 0, suppressed |
| official DOUBTFUL | 0, suppressed (W2: 0 of 46 played) |
| official QUESTIONABLE / PROBABLE | capped at the W2 DEV rates 0.5881 / 0.9327, never raised |
| team has no official snapshot yet, ESPN says OUT or QUESTIONABLE | capped at 0.5881 (ESPN is unverified, as in #101) |
| listed ACTIVE, implicitly active, or no information | unchanged |

The not-on-roster rule is new. The availability archive emits one row for every rostered player in each
official snapshot (explicit status or implicit ACTIVE), so a projected player missing from a covered team's
snapshot is not with the team. Pretip: **0 of 306** such player-games played. Morning: 4 of 630.

## Replay

`python scripts/nba_availability_replay.py --shadow <nba-shadow-pure> --availability <projection-data> --json docs/research/availability_overlay/replay.json`

* Data: `nba-shadow-pure` @ `c8ef48f`, `projection-data` @ `a1cf3b5`. No network, no market file.
* Universe: every archived projection in a finished game with kickoff on or after the availability archive
  start (2026-10-19). That is **171 games**: 1,816 pretip and 5,087 morning player-games per arm, all four
  variants scored on identical rows.
* **Holdout:** games from 2026-11-01 onward (90 games). The only choice made on replay data (the redistribution
  ablation's `REGULAR_P`) used games before that date. The W2 caps were fitted on 2025-26.
* CIs: 95%, game-clustered bootstrap, paired (overlay − baseline).

### Overlay vs baseline

The table covers participation and the unconditional expected value, where a player who did not play has
an actual of 0.

| arm | window | slot | player-games | participation Brier | uncond. minutes MAE | uncond. points MAE | particip. calib. slope |
|---|---|---|---:|---|---|---|---|
| sim_rotation | all | pretip | 1,816 | 0.1490 → **0.0906** −0.058 [−0.069, −0.048] | 8.55 → **5.81** −2.74 [−3.31, −2.20] | 5.21 → **3.93** −1.28 [−1.56, −1.01] | 0.85 → 0.88 |
| sim_rotation | all | morning | 5,087 | 0.1345 → **0.0996** −0.035 [−0.039, −0.030] | 7.73 → **5.97** −1.76 [−2.05, −1.49] | 4.90 → **4.07** −0.83 [−0.97, −0.71] | 0.98 → 0.78 |
| sim_rotation | holdout | pretip | 955 | 0.1206 → **0.0806** −0.040 [−0.053, −0.030] | 6.94 → **5.46** −1.48 [−1.91, −1.14] | 4.66 → **3.98** −0.68 [−0.89, −0.52] | 0.94 → 0.96 |
| sim_rotation | holdout | morning | 2,682 | 0.1194 → **0.0991** −0.020 [−0.024, −0.017] | 6.44 → **5.59** −0.85 [−1.00, −0.70] | 4.44 → **4.03** −0.41 [−0.48, −0.35] | 0.93 → 0.78 |
| ewm5 | all | pretip | 1,816 | 0.2166 → **0.1352** −0.081 [−0.099, −0.065] | 9.79 → **6.83** −2.96 [−3.50, −2.45] | 5.45 → **4.01** −1.44 [−1.71, −1.18] | 0.55 → 0.74 |
| ewm5 | all | morning | 5,087 | 0.1940 → **0.1425** −0.051 [−0.060, −0.044] | 9.15 → **7.17** −1.99 [−2.24, −1.75] | 5.17 → **4.19** −0.98 [−1.10, −0.86] | 0.77 → 0.72 |
| ewm5 | holdout | pretip | 955 | 0.1480 → **0.1084** −0.040 [−0.050, −0.032] | 8.11 → **6.34** −1.77 [−2.17, −1.45] | 4.82 → **3.95** −0.87 [−1.09, −0.70] | 1.44 → 1.23 |
| ewm5 | holdout | morning | 2,682 | 0.1476 → **0.1241** −0.023 [−0.027, −0.020] | 7.80 → **6.68** −1.12 [−1.28, −0.97] | 4.64 → **4.08** −0.55 [−0.64, −0.48] | 1.39 → 1.06 |

Rebounds, assists and threes improve in the same direction (sim_rotation pretip MAE: 1.99 → 1.47,
1.35 → 1.05, 0.80 → 0.65). Every CI in the table excludes 0. Pretip gains about 1.5× more than morning,
because more of the report is published by then. The holdout is smaller than the full window because the
early-season roster carry-over (players gone since preseason) faded by November. The fix stays large there.

**Players who played (conditional rows).** By design the overlay leaves teammates' conditional
distributions unchanged. Conditional CRPS, coverage and prop-rung Brier are therefore identical to
baseline on every played row (Δ = 0). The overlay changes **who gets a forecast**, not how a played
player is forecast.

### Player props

These are prop ladder rungs (points, rebounds, assists, threes) issued for players who then did not play.
Kalshi voids those contracts, so each such rung is a wasted or misleading quote.

| sim_rotation | rungs issued | for non-players (baseline) | for non-players (overlay) | suppressed but player played |
|---|---:|---:|---:|---:|
| pretip, all | 49,032 | 17,010 | **4,590 (−73%)** | **0** |
| pretip, holdout | 25,785 | 7,533 | 2,376 (−68%) | 0 |
| morning, all | 137,349 | 44,901 | 20,007 (−55%) | 216 (8 player-games) |
| morning, holdout | 72,414 | 20,736 | 11,097 (−46%) | 108 |

### The 1,626, reconciled (absent from box, in-window, judged at each player-game's latest slot)

The postmortem's 1,626 = 1,238 in-window + 388 before the availability archive began. This replay, on newer
branch heads, finds **1,258** in-window absent player-games:

| what was knowable at `as_of` | player-games | treatment |
|---|---:|---|
| **not on the official roster** (the postmortem's "no report" bucket) | **672** | suppressed |
| official OUT | 321 | suppressed |
| official DOUBTFUL | 12 | suppressed |
| **predictable, removed** | **1,005 (80%)** | |
| official QUESTIONABLE / PROBABLE | 64 | thinned (P ≤ 0.59 / 0.93) |
| ESPN-only OUT / QUESTIONABLE (no official snapshot yet) | 45 | thinned (unverified) |
| **late scratch**: OUT or off-roster in a snapshot after `as_of` but before tip | 97 | not knowable at `as_of`; earlier slots only |
| no official snapshot for the team yet, no ESPN entry | 7 | unknowable |
| listed implicitly active, still absent (coach decision, unreported) | 40 | unexplained |

Of the postmortem's 728 "no report" absences, the large majority are the not-on-roster group: players the
proxy kept projecting after a trade, a waiver or a two-way move. The genuinely unpredictable residue is
**late scratches (97)** plus **47 unknowable or unexplained**, about 11% of absences. Pretip has only 2 late scratches.

### Minutes redistribution: implemented, measured, NOT recommended (off by default)

`apply_overlay(..., redistribute=True)` hands freed expected minutes to teammates in proportion to expected
minutes (W2 `pit_prop`), capped at 48, and rescales their stat distributions. On this season's data it does
not help:

| arm | window | slot | Δ cond. minutes CRPS (regulars only) | Δ prop Brier (regulars only) | Δ cond. min CRPS / Δ prop Brier (all freed minutes) | cond. minutes bias: base / regulars / all |
|---|---|---|---|---|---|---|
| sim_rotation | holdout | pretip | +0.026 [−0.087, +0.116] | +0.0005 [−0.0003, +0.0014] | +0.24 / +0.0024 | +0.11 / +0.99 / +2.55 |
| sim_rotation | holdout | morning | +0.065 [+0.029, +0.114] | +0.0002 [−0.0001, +0.0006] | +0.24 / +0.0013 | +0.33 / +0.74 / +2.06 |
| ewm5 | holdout | pretip | −0.003 [−0.041, +0.032] | +0.0002 [−0.0003, +0.0006] | +0.19 / +0.0049 | −0.50 / −0.19 / +2.82 |
| ewm5 | holdout | morning | −0.010 [−0.034, +0.017] | −0.0001 [−0.0004, +0.0003] | +0.17 / +0.0028 | −0.49 / −0.24 / +2.06 |

Why: unlike W2's 2025-26 holdout (played-row bias −3.25 min), the 2026-27 shadow projections are already
unbiased for players who play (+0.1 to +0.9). Most "freed" minutes belong to players already missing from
recent games, and teammates' recent-history projections already include those minutes. Redistributing every
freed minute double-counts (bias +2 to +6). Restricting it to newly ruled-out regulars (P ≥ 0.8; on the DEV
window teammates absorbed about 1.1 minute per freed regular minute) is roughly neutral. The real gap is in
**participation**: confirmed-available players play 89% of the time but get a mean baseline P of 0.76. That
is a calibration problem, not an allocation problem.

## Limits

* Distributions are re-derived from archived quantiles and rungs (draws are not stored). The default
  overlay only zeroes or thins participation, so no shape approximation enters its played-row scores.
* Statuses depend on the archive's identity join. 252 official rows were unmatched by name and are invisible
  to the overlay, as they are to the archive.
* Morning-slot calibration slope falls (0.98 → 0.78 for sim_rotation) even though Brier improves. That fall
  comes from 8 hard-zero suppressions of players who then played: 4 not-on-roster, 3 official OUT, 1 DOUBTFUL.
* Not exchange settlement. Outcomes are ESPN box rows, as in the postmortem.
* Not wired into the shadow collector or the live simulator. That is a separate, reviewed change (new arm,
  new frozen hash), so this PR does not alter any frozen arm or workflow.
