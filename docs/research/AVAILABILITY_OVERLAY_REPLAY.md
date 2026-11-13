# PIT availability overlay: 2026-27 historical replay (RESEARCH_ONLY, NO PROMOTION)

**Question.** Alpha postmortem 001 (`sift-alpha/docs/alpha_eval/NBA_POSTMORTEM_001.md` §4) found **1,626**
projected player-games whose player never appeared in the box score, including **728** with no official
injury report in the archive window. Why does that happen, how much of it was knowable before tip, and
what does fixing it buy?

**Cause.** The frozen shadow arms (`sim_rotation`, `ewm5`) never read an injury report:
`PARTICIPATION_SOURCE = "proxy_recent_team_games_no_injury_report"`. Participation comes only from recent
team games. PR #101 fixed injury selection for the **live pricing path** (`workflows/simulate.py`) only.
The W2 study (`PARTICIPATION_MINUTES_W2.md`) validated PIT statuses on 2025-26 but was never wired in.

**Fix.** `nba_edge.availability.overlay` post-processes `pure_forecast.v1` rows, using only
`sift.availability.v1` records whose **effective time** is at or before the projection's own `as_of`. Effective
time is the later of the record's `captured_utc` and its snapshot's write time. The overlay never edits a frozen
arm (no existing file is modified). Affected rows carry `model_version += "+pit-availability-overlay-v1"` and an
`x_availability` block.

| status at `as_of` (latest official snapshot for the game and team) | P(play) |
|---|---|
| official OUT | 0, suppressed |
| official DOUBTFUL | 0, suppressed (W2: 0 of 46 played) |
| **missing from the team's roster with positive evidence** (on another team's roster, or dropped from this one) | 0, suppressed |
| missing, but on the **opponent's** roster for the same game (stale projection team) | unchanged, flagged `team_mismatch` |
| missing, never seen on any roster snapshot (no positive evidence) | unchanged, flagged `roster_unconfirmed` |
| official QUESTIONABLE / PROBABLE | capped at the W2 DEV rates 0.5881 / 0.9327, never raised |
| team has no official snapshot yet, ESPN says OUT or QUESTIONABLE | capped at 0.5881 (ESPN is unverified, as in #101) |
| listed ACTIVE, implicitly active, or no information | unchanged |

## Review of the roster evidence (what "not on roster" rests on)

The availability producer (`research/projection_foundation/nba/live/availability.py`) builds the implicit rows
from **ESPN team rosters fetched at capture time** (`sources.rosters()`, else the newest data-archive roster
captured before the run), not from the injury report. Two defects were found and fixed in this PR:

1. **Time safety.** Implicit rows are stamped with the official report's fetch time. When the producer reused
   an older report (PIT fallback), rosters fetched later carried an earlier stamp. This happened in 2 of 144
   snapshots (both 2026-10-30): roster evidence was visible 2.3 h and 4.6 h before it existed. Both snapshots
   also shared a stamp, so their rosters merged. Fix: a record is usable only from its effective time; the
   loader reads snapshot write times from the archive path.
2. **Absence is not evidence.** The first version suppressed any player missing from his projected team's
   snapshot. Three of the 8 morning false removals were players the projector still assigned to their
   **previous** team, which was that night's opponent: Andre Drummond (PHI → NYK, 24 min), Kyle Anderson
   (MIN → TOR, 11 min) and Kris Murray (POR → MEM, 3 min). The rule now requires positive roster evidence; the
   table shows how each evidence type played out.

| roster evidence at `as_of` (sim_rotation) | pretip: n / played | morning: n / played | treatment |
|---|---:|---:|---|
| moved (latest roster appearance is another team) | 181 / 0 | 401 / 0 | suppressed |
| dropped (earlier on this team's roster, now gone) | 4 / 0 | 13 / 1 | suppressed |
| on opponent's roster, same game | 1 / 0 | 5 / 3 | kept |
| never on any roster snapshot | 120 / 0 | 211 / 0 | kept: no positive evidence |

The `roster_unconfirmed` group (331 player-games, none played) is kept on purpose. It was identified during
this review, so suppressing it now would be a rule chosen after seeing the outcomes. It is a candidate rule to
validate prospectively ("not on any of 30 rosters for ≥ 24 h").

## The morning-slot false removals (8 before the review → 5 after)

| player | game | status at morning `as_of` | what happened | now |
|---|---|---|---|---|
| Andre Drummond, Kyle Anderson, Kris Murray | 10-20, 10-25, 10-29 | missing from projected team | on the opponent's roster: stale projection team | **kept** (`team_mismatch`) |
| Isaiah Evans (MIN) | 11-12 | dropped from MIN's roster on 11-08 | recalled, played 8 min | suppressed (1 miss) |
| Christian Anderson, Hannes Steinbach (CHA) | 11-06 | official OUT, "G League - On Assignment" (05:00 UTC report) | recalled; ACTIVE on the 16:57 report; 25 and 27 min | suppressed (2 misses) |
| Jonathan Mogbo (SAC) | 11-08 | official OUT, "G League - Two-Way" | ACTIVE on the final pre-tip report; 2 min | suppressed (1 miss) |
| Gui Santos (GSW) | 10-30 | official DOUBTFUL | upgraded to QUESTIONABLE in the afternoon; 16 min | suppressed (1 miss) |

G-League designations are reversible the same day. At morning, 3 of 24 G-League OUTs played (12.5%), against
0 of 266 injury OUTs. At pretip it is 0 of 9. Pretip has **no** false removals at all.

## Replay

`python scripts/nba_availability_replay.py --shadow <nba-shadow-pure> --availability <projection-data> --json docs/research/availability_overlay/replay.json`

* Data: `nba-shadow-pure` @ `c8ef48f`, `projection-data` @ `a1cf3b5`. No network, no market file.
* Universe: every archived projection in a finished game with kickoff on or after the availability archive
  start (2026-10-19). That is **171 games**: 1,816 pretip and 5,087 morning player-games per arm, all variants
  scored on identical rows.
* **Holdout:** games from 2026-11-01 onward (90 games). The only replay-data choice (the redistribution
  ablation's `REGULAR_P`) used earlier games. The W2 caps were fitted on 2025-26. The roster-evidence rule is a
  priori, and was **not** extended to the outcome-favourable `roster_unconfirmed` group.
* CIs: 95%, game-clustered bootstrap, paired (overlay − baseline).

### Pretip slot

| arm | window | player-games | participation Brier | uncond. minutes MAE | uncond. points MAE | particip. calib. slope |
|---|---|---:|---|---|---|---|
| sim_rotation | all | 1,816 | 0.1490 → **0.1019** −0.047 [−0.056, −0.038] | 8.55 → **6.51** −2.04 [−2.44, −1.64] | 5.21 → **4.22** −0.99 [−1.20, −0.79] | 0.85 → 1.12 |
| sim_rotation | holdout | 955 | 0.1206 → **0.0832** −0.037 [−0.051, −0.027] | 6.94 → **5.62** −1.32 [−1.75, −1.00] | 4.66 → **4.04** −0.63 [−0.83, −0.46] | 0.94 → 1.12 |
| ewm5 | all | 1,816 | 0.2166 → **0.1525** −0.064 [−0.079, −0.051] | 9.79 → **7.49** −2.30 [−2.74, −1.89] | 5.45 → **4.26** −1.19 [−1.42, −0.98] | 0.55 → 0.72 |
| ewm5 | holdout | 955 | 0.1480 → **0.1116** −0.036 [−0.047, −0.028] | 8.11 → **6.55** −1.56 [−1.97, −1.25] | 4.82 → **4.03** −0.79 [−1.02, −0.62] | 1.44 → 1.51 |

### Morning slot

| arm | window | player-games | participation Brier | uncond. minutes MAE | uncond. points MAE | particip. calib. slope |
|---|---|---:|---|---|---|---|
| sim_rotation | all | 5,087 | 0.1345 → **0.1061** −0.028 [−0.032, −0.025] | 7.73 → **6.40** −1.33 [−1.49, −1.15] | 4.90 → **4.25** −0.65 [−0.74, −0.57] | 0.98 → 0.92 |
| sim_rotation | holdout | 2,682 | 0.1194 → **0.1006** −0.019 [−0.023, −0.015] | 6.44 → **5.69** −0.76 [−0.89, −0.62] | 4.44 → **4.06** −0.38 [−0.44, −0.32] | 0.93 → 0.85 |
| ewm5 | all | 5,087 | 0.1940 → **0.1530** −0.041 [−0.047, −0.035] | 9.15 → **7.57** −1.59 [−1.78, −1.40] | 5.17 → **4.35** −0.82 [−0.92, −0.72] | 0.77 → 0.76 |
| ewm5 | holdout | 2,682 | 0.1476 → **0.1261** −0.021 [−0.025, −0.018] | 7.80 → **6.82** −0.98 [−1.13, −0.84] | 4.64 → **4.14** −0.50 [−0.58, −0.43] | 1.39 → 1.18 |

Every CI above excludes 0. Rebounds, assists and threes improve in the same direction (sim_rotation pretip MAE:
1.99 → 1.59, 1.35 → 1.13, 0.80 → 0.69). Morning gains are about two-thirds of pretip's, because fewer reports are
out by then.

Participation calibration (logistic slope on P(play); 1 is ideal) is mixed. Pretip moves from 0.85 to 1.12:
slightly under-confident, because the kept groups (unlisted 89% played, baseline P 0.76) are now the bulk.
Morning sim_rotation falls from 0.93 to 0.85 on the holdout, driven by the 5 hard-zero misses above. Neither is
fixed here; participation calibration is the follow-up PR.

**Players who played (conditional rows).** By design the overlay leaves teammates' conditional distributions
unchanged. Conditional CRPS, coverage and prop-rung Brier are therefore identical to baseline on every played
row (Δ = 0). The overlay changes **who gets a forecast**, not how a played player is forecast.

### Player props

These are prop ladder rungs (points, rebounds, assists, threes) issued for players who then did not play.
Kalshi voids those contracts, so each such rung is a wasted or misleading quote.

| sim_rotation | rungs issued | for non-players (baseline) | for non-players (overlay) | suppressed but player played |
|---|---:|---:|---:|---:|
| pretip, all | 49,032 | 17,010 | **7,857 (−54%)** | **0** |
| pretip, holdout | 25,785 | 7,533 | 3,267 (−57%) | 0 |
| morning, all | 137,349 | 44,901 | 25,758 (−43%) | 135 (5 player-games) |
| morning, holdout | 72,414 | 20,736 | 12,663 (−39%) | 108 (4 player-games) |

### The 1,626, reconciled

Population: absent from the box, in-window, each player-game judged at its latest slot. The postmortem's
1,626 = 1,238 in-window + 388 before the availability archive began. This replay, on newer branch heads,
finds **1,258** in-window absent player-games:

| what was knowable at `as_of` | player-games | treatment |
|---|---:|---|
| moved to another team's roster | 432 | suppressed |
| dropped from this team's roster | 10 | suppressed |
| official OUT | 321 | suppressed |
| official DOUBTFUL | 12 | suppressed |
| **predictable with positive evidence, removed** | **775 (62%)** | |
| official QUESTIONABLE / PROBABLE, ESPN-only OUT / QUESTIONABLE | 109 | thinned |
| never on any roster snapshot (`roster_unconfirmed`) | 228 | kept (no positive evidence; prospective candidate) |
| on the opponent's roster (stale projection team) | 2 | kept, flagged |
| **late scratch**: OUT / moved / dropped after `as_of` but before tip | 86 | not knowable at `as_of` |
| no official snapshot for the team yet, no ESPN entry | 18 | unknowable |
| implicitly active, still absent (coach decision, unreported) | 40 | unexplained |

### Minutes redistribution: implemented, measured, NOT recommended (off by default)

`apply_overlay(..., redistribute=True)` hands freed expected minutes to teammates in proportion to expected
minutes (W2 `pit_prop`), capped at 48, and rescales their stat distributions. Holdout results:

| arm | slot | Δ cond. minutes CRPS (regulars only) | Δ prop Brier (regulars only) | Δ cond. min CRPS / Δ prop Brier (all freed) | cond. minutes bias: base / regulars / all |
|---|---|---|---|---|---|
| sim_rotation | pretip | +0.025 [−0.087, +0.115] | +0.0005 [−0.0003, +0.0013] | +0.18 / +0.0019 | +0.11 / +0.98 / +2.27 |
| sim_rotation | morning | +0.063 [+0.027, +0.112] | +0.0002 [−0.0002, +0.0006] | +0.18 / +0.0008 | +0.33 / +0.73 / +1.65 |
| ewm5 | pretip | −0.004 [−0.041, +0.031] | +0.0002 [−0.0003, +0.0006] | +0.07 / +0.0034 | −0.50 / −0.19 / +2.33 |
| ewm5 | morning | −0.006 [−0.030, +0.020] | −0.0001 [−0.0004, +0.0002] | +0.10 / +0.0016 | −0.49 / −0.27 / +1.40 |

Unlike W2's 2025-26 holdout (played-row bias −3.25 min), the 2026-27 shadow projections are already unbiased
for players who play. Most "freed" minutes belong to players already missing from recent games, so
redistributing them double-counts. It stays off unless independent evidence supports it.

## Frozen baseline

No existing file is modified (`git diff --name-status main` shows only additions). The shadow-pure
immutability, baseline-freeze and shadow-pure tests pass. The overlay is not wired into the collector, the
live simulator or any workflow.

## Limits

* Distributions are re-derived from archived quantiles and rungs (draws are not stored). The default overlay
  only zeroes or thins participation, so no shape approximation enters its played-row scores.
* Statuses depend on the archive's identity join. 252 official rows were unmatched by name and are invisible
  to the overlay, as they are to the archive.
* Roster evidence is ESPN's roster feed. Its lag can produce a "dropped" signal for a recalled player (1 case).
* Not exchange settlement. Outcomes are ESPN box rows, as in the postmortem.
