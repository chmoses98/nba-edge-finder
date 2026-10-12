# W2: participation and minutes: where the frozen V1 simulator's minutes error comes from, and what point-in-time injury reports buy (research only, NO PROMOTION)

**Preregistration:** `docs/research/PREREG_W2_NBA_PARTICIPATION.md`, committed alone as `1045797`.
The DEV fit and DEV result were added as Addendum A in `af1129e`, before the holdout was collected.
The holdout was collected and scored once, with the command in the addendum.
**Champion:** frozen `NBA_BASELINE_2026_PRESEASON_V1`, unchanged. Its holdout draws reproduce W1
exactly: minutes CRPS 5.0591, MAE of the mean 7.3815, bias +0.428, RMSE 10.08.
**Inputs:** ESPN box history for the champion, with cutoff 00:00 ET on the game date. PR #23 T-60
official injury-report snapshots, using only rows where `t_minus_60_pit_ok`. PR #22 certified
stints from games dated strictly before the forecast game. No market file is read.
**Data versions used:** PR #22 head `cac640c` (stints unchanged since `7e8d34c`) and PR #23 head
`c2c1627`. The holdout games' T-60 snapshots are identical in every PR #23 version.

## Verdicts (holdout 2026-02-01..2026-04-12: 501 games, 14,763 eligible player-games, all 501 with a T-60 snapshot)

| question | answer |
|---|---|
| (a) How much error comes from player-games that did not happen? | **About half.** DNP / inactive rows are 30.3% of the eligible population (4,473). They carry **45.1% of the champion's squared error** and 36.5% of its absolute error (mean forecast). Knowing appearance (oracle) removes **45.6% of minutes CRPS** (5.059 → 2.750). |
| How much of (a) was knowable pre-tip? | **Most of it.** 61.1% of DNP absolute error sits on players the official report listed **Out at T-60**: 2,168 rows, **0 of which played**, yet the champion gave them a mean P(appear) of 0.505 and 11.2 expected minutes. Doubtful adds 2.9% (76 rows, 0 played) and Questionable 7.9%. 27.1% is from **unlisted** DNPs (coach's decisions, 1,971 rows), which the report cannot see. |
| (b) Misallocation among players who played | **The other half.** 54.4% of CRPS remains when appearance is known. Rescaling to the true team total removes only 2.5 points of that, so **51.8% of the champion's CRPS is within-team allocation** among players who played. On played rows the champion's mean forecast is 3.25 min low. |
| Do PIT statuses reduce the error? (rule 1) | **Yes, for both arms.** `pit_prop` ΔCRPS **−0.841 [−0.935, −0.760]** (−16.6%), ΔMAE −0.925 [−1.041, −0.812], ΔBrier P(appear) −0.054 [−0.059, −0.050]. `pit_lineup` ΔCRPS **−0.883 [−0.981, −0.798]** (−17.5%), ΔMAE −1.020 [−1.143, −0.904], same Brier gain. Every CI excludes 0. |
| Do lineup on/off weights add over proportional redistribution? (rule 2) | **Yes, but the effect is small.** `pit_lineup` − `pit_prop`: ΔCRPS **−0.042 [−0.063, −0.022]**, ΔMAE −0.095 [−0.132, −0.058], ΔBrier P(≥10 min) −0.0032 [−0.0038, −0.0027]. ΔMSE of the mean is +0.05 [−0.70, +0.73], i.e. no change. |
| Promotion? | **None.** These are research findings. The champion is unchanged. The next step is a prospective re-test on 2026-27 capture (see the end of this document). |

The PIT arms close **38%** of the gap between the champion and the known-appearance oracle
(0.883 of 2.310 CRPS). What remains is unlisted coach's-decision DNPs and the within-team allocation
of minutes. Neither can be fixed with an injury report.

## Part 1: decomposition of the champion's minutes error (holdout)

Per eligible player-game: μ = P(appear) · E[min | appear]. Shares are of the total over the 14,763
rows. Error is measured on the mean forecast unless the row says CRPS.

| | value |
|---|---:|
| rows / played / DNP (of which absent from the box) | 14,763 / 10,290 / 4,473 (2,588) |
| RMSE / MAE / bias of μ | 10.075 / 7.382 / +0.428 |
| share of squared error: DNP rows / played rows | **0.451** / 0.549 |
| share of absolute error: DNP rows / played rows | 0.365 / 0.635 |
| played rows: participation term −(1−p)c, squared, share of total | 0.132 |
| played rows: conditional term (c − y), squared, share of total | 0.353 |
| played rows: cross term | 0.064 |
| CRPS champion / oracle appearance / + oracle team total | 5.059 [4.905, 5.209] / 2.750 [2.690, 2.816] / 2.621 [2.563, 2.687] |
| MAE of the draw median, same three | 7.031 / 3.826 / 3.643 |

DNP rows by T-60 status:

| T-60 status | DNP rows | share of DNP abs. error | share of total sq. error | champion mean P(appear) | champion mean forecast (min) |
|---|---:|---:|---:|---:|---:|
| out | 2,168 | **0.611** | 0.298 | 0.505 | 11.2 |
| unlisted | 1,971 | 0.271 | 0.085 | 0.399 | 5.5 |
| questionable | 195 | 0.079 | 0.049 | 0.663 | 16.1 |
| doubtful | 76 | 0.029 | 0.015 | 0.663 | 15.0 |
| available | 55 | 0.006 | 0.002 | 0.333 | 4.4 |
| probable | 8 | 0.004 | 0.003 | 0.850 | 20.0 |

All eligible rows by status (holdout appearance rate vs the champion's mean P(appear)): out 2,168
rows, 0.000 vs 0.505; doubtful 76, 0.000 vs 0.663; questionable 436, 0.553 vs 0.672; probable 119,
0.933 vs 0.739; available 601, 0.909 vs 0.663; unlisted 11,363, 0.827 vs 0.746. The DEV-fitted rates
(questionable 0.588, probable 0.933) held on the holdout.

DEV (2025-11-15..2026-01-31: 544 games, 15,729 rows) shows the same pattern. DNP rows carry 41.6% of
squared error. Known appearance removes 41.0% of CRPS. Within-team allocation accounts for 56.6%
(`dev_report.json`).

## Part 2: preregistered arms (holdout, all 14,763 rows, game-clustered 95% CI over 501 games)

| arm | CRPS | MAE (median) | RMSE (mean) | bias (mean) | p10–p90 cov. | mean P(appear) |
|---|---:|---:|---:|---:|---:|---:|
| champion | 5.059 | 7.031 | 10.075 | +0.428 | 0.819 | 0.705 |
| `pit_prop` | 4.218 | 6.106 | 8.299 | +0.275 | 0.870 | 0.622 |
| `pit_lineup` | **4.176** | **6.011** | 8.302 | +0.271 | 0.861 | 0.622 |
| oracle appearance (bound) | 2.750 | 3.826 | 5.986 | −0.244 | 0.869 | 0.697 |
| + oracle team total (bound) | 2.621 | 3.643 | 5.673 | 0.000 | 0.887 | 0.697 |

| paired comparison | ΔCRPS | ΔMAE (median) | ΔMSE (mean) | ΔBrier appear | ΔBrier ≥10 min |
|---|---|---|---|---|---|
| `pit_prop` − champion | −0.841 [−0.935, −0.760] | −0.925 [−1.041, −0.812] | −32.6 [−36.0, −29.7] | −0.0544 [−0.0587, −0.0504] | −0.0459 [−0.0501, −0.0421] |
| `pit_lineup` − champion | −0.883 [−0.981, −0.798] | −1.020 [−1.143, −0.904] | −32.6 [−36.0, −29.4] | −0.0544 [−0.0587, −0.0504] | −0.0491 [−0.0536, −0.0449] |
| `pit_lineup` − `pit_prop` | −0.042 [−0.063, −0.022] | −0.095 [−0.132, −0.058] | +0.05 [−0.70, +0.73] | 0 | −0.0032 [−0.0038, −0.0027] |

Secondary frames:

* **Teams with an eligible player listed Out** (13,039 rows, 493 games). `pit_lineup` − champion
  ΔCRPS −0.994 [−1.092, −0.896]. `pit_lineup` − `pit_prop` ΔCRPS −0.047 [−0.070, −0.023].
* **Rows that actually played** (outcome-selected, diagnostic only; 10,290 rows). Both arms are
  *worse* here than the champion: ΔCRPS +0.322 (`pit_prop`) and +0.247 (`pit_lineup`). Their bias
  improves from −3.25 to −1.04 / −1.07 min. Questionable/doubtful thinning removes appearance mass
  from players who then played, and redistributed minutes widen the teammates' distributions. The
  lineup weights recover a third of that loss (−0.074 [−0.102, −0.046] vs `pit_prop`). This is the
  cost side of the trade, and it is why the full-population frame is the primary one.

Redistribution bookkeeping (holdout):
* 27,463 expected minutes were removed from listed players. Lineup weights were used for 2,478
  absent-player team-games, with 47 falling back to proportional weights.
* The 48-minute per-draw clip discarded 2,260 (`pit_prop`) and 2,318 (`pit_lineup`) expected minutes,
  about 2.3 per team-game (~1%). As a result, team totals of eligible players' mean forecasts are
  238.8 for both arms, against the champion's 241.1 and an actual 234.8 (actual excludes minutes
  played by non-eligible players).
* 1.1 minutes could not be assigned to anyone.

## Threats to validity (read before using the numbers)

* **Holdout reuse.** W1 already scored this window once, for the different, rejected `RATE_PRIOR_5`.
  The PIT arms are new to it, but the window is not pristine for the champion. The champion's
  inherited contamination (rotation PMF fitted on 2023-24..2025-26) is disclosed in W1.
* **Retrospective identity join.** PR #23 maps report names to ESPN ids using 2025-26 box scores,
  including later ones. For the rows used here this has no effect: **6,781 of 6,783** status rows on
  eligible players (DEV + holdout) resolve to the same id from *prior* same-team box rows alone. The
  other 2 could not be re-joined to their report row by team id in this check; none was ambiguous.
* **Reconstructed snapshots.** The T-60 snapshot was reconstructed from the report archive by upload
  instant (HTTP Last-Modified) and printed report time, both verified < tip − 60 min. It was not
  captured live. Prospective capture (PR #23 `capture` job) is what makes this deployable.
* **Scope.** Only minutes are scored here. Counting-stat effects of redistributed minutes are not
  measured and are not claimed. The W1 per-minute-rate findings and the rejected `RATE_PRIOR_5` are
  unchanged: this study does not touch rates.
* **Lineup coverage.** Lineup weights use certified games only: 448 of 501 holdout games, 90.2% of
  the 2025-26 season. Weights need ≥ 600 certified on and off seconds for the absent player, else the
  proportional fallback is used (47 cases).

## Wave 1 findings preserved

`MATCHED_DECOMPOSITION.md` stands as written:
* no material full-population bias;
* participation over-forecast (F 1.053), which this study locates: half of the DNP error is on
  players the league had already listed Out;
* `RATE_PRIOR_5` REJECTED under strict criteria, not promoted;
* blanket multiplier NO PROMOTION.

Injury R1 (impact on team ratings) is still not fitted. `impact_ppp` stays 0. The data gates for it
are now open: PR #22 lineups and PR #23 point-in-time availability.

## Next steps (not done here)

1. Prospective test on 2026-27. Wire the live T-60 capture (PR #23, `data-injury-pit`) into a
   *shadow* challenger. The arm is champion draws + `pit_lineup`, with π frozen from this study's DEV
   fit. Score it on the first N weeks against the champion under the same rules.
2. Measure how the redistributed minutes change counting stats before any props use.
3. The within-team allocation error (51.8% of CRPS) is the largest remaining channel. It is a
   rotation-model question, not an injury question.

## Reproduce

```
python scripts/nba_participation_study.py collect --window dev --out $OUT --pit <PR23>/data/history/injury_reports --pbp <PR22>/data/history/espn_pbp
python scripts/nba_participation_study.py fit --out $OUT
python scripts/nba_participation_study.py collect --window holdout --out $OUT --pi docs/research/w2_nba_participation/pi_dev_fit.json --pit ... --pbp ...
python scripts/nba_participation_study.py report --window holdout --out $OUT --json docs/research/w2_nba_participation/holdout_report.json
```
The run takes ~6 minutes per window on 4 CPUs at 2,000 draws per game. Once PRs #22/#23 are merged,
`--pit` / `--pbp` default to the repository paths.
