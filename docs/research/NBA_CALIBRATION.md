# NBA participation and prop-ladder calibration (RESEARCH_ONLY, NO PROMOTION)

**Preregistration:** `docs/research/PREREG_NBA_CALIBRATION.md`, committed alone as `e576177` before any fit or
evaluation code existed. The methods, the hyperparameters (ridge-Platt, `lambda = 10`), the walk-forward scheme and
the decision rules are exactly as written there. No other method was tried.

**Reproduce:** `python scripts/nba_calibration_replay.py --shadow <nba-shadow-pure @ c8ef48f> --availability <projection-data @ a1cf3b5> --json docs/research/nba_calibration/replay.json --frozen docs/research/nba_calibration/frozen_calibrators.json`

## Verdicts

| calibrator | compared with | pooled Δ Brier [95% CI] | verdict |
|---|---|---|---|
| **P1 combined**: P(play) of confirmed-available players, on top of the #104 overlay | injury-only | **−0.0234 [−0.0296, −0.0172]** | **ADOPTED** (all rules pass) |
| P1 calibration-only: P(play) of every player, no injury information | baseline | +0.0072 [+0.0054, +0.0090] | REJECTED (rules 1, 2, 3) |
| P2: prop-ladder rungs P(stat ≥ rung \| plays) | baseline | +0.0005 [+0.0001, +0.0009] | REJECTED (rules 1, 2, 3) |

The participation calibrator is useful only together with the availability information. Without it, one map has
to serve injured, traded and healthy players at once: it lowers the probability for healthy players and raises it
for absent ones (the not-on-roster group got worse: +0.040 [+0.037, +0.043]). After the overlay has removed the
known absences, the remaining confirmed-available players are systematically under-forecast: they played **89%**
of the time, but the baseline gave them P ≈ 0.79. The fitted maps (sim_rotation `a ≈ 1.1`, `b ≈ 0.91–0.93`; ewm5
`a ≈ 1.6`, `b ≈ 0.68`) mostly shift the level up.

## Evaluation design (independence)
* **Walk-forward:** every evaluated game date uses maps fitted only on outcomes observed before that date's
  earliest `as_of`. A unit test poisons future labels and confirms earlier forecasts do not change.
* **Window A** (10-27..10-31: 36 games, 2,444 participation units, 43,524 prop rungs) was never looked at before.
  **Window B** (11-01..11-12: 86 games, 6,854 / 132,192) was #104's availability holdout. It was used for no
  calibration choice. Every result is shown for both.
* **Prospective:** the calibrators fitted on all data through 2026-11-13 06:13 UTC are frozen in
  `nba_calibration/frozen_calibrators.json`, sha256 `55dfdfbe…abefe3b`. Scoring them on games tipping after that
  time is **PENDING**: no such outcomes exist yet.

## Participation: baseline, injury-only, calibration-only, combined

Brier / log loss / ECE / calibration slope. Pooled walk-forward window: 122 games. Units are player-game
projections (sim_rotation and ewm5 have the same counts).

| slot, arm | n | baseline | injury-only (#104) | calibration-only | **combined** |
|---|---:|---|---|---|---|
| pretip, sim_rotation | 1,015 | 0.1216 / 0.397 / 0.059 / 0.95 | 0.0830 / 0.265 / 0.076 / 1.13 | 0.1233 / 0.399 / 0.047 / 1.00 | **0.0664 / 0.218 / 0.026 / 1.21** |
| pretip, ewm5 | 1,015 | 0.1519 / 0.473 / 0.102 / 1.38 | 0.1143 / 0.363 / 0.149 / 1.42 | 0.1793 / 0.543 / 0.140 / 3.29 | **0.0750 / 0.260 / 0.069 / 1.93** |
| morning, sim_rotation | 3,634 | 0.1187 / 0.392 / 0.072 / 1.01 | 0.0959 / 0.316 / 0.056 / 0.90 | 0.1175 / 0.391 / 0.063 / 0.93 | **0.0853 / 0.283 / 0.020 / 0.94** |
| morning, ewm5 | 3,634 | 0.1582 / 0.485 / 0.078 / 1.30 | 0.1310 / 0.410 / 0.131 / 1.11 | 0.1697 / 0.518 / 0.126 / 2.34 | **0.0973 / 0.324 / 0.029 / 1.15** |

Paired Δ Brier, game-clustered 95% CI:

| slot, arm | window | injury-only − base | calibration-only − base | combined − base | **combined − injury-only** |
|---|---|---|---|---|---|
| pretip, sim_rotation | A | −0.046 [−0.064, −0.033] | +0.001 [−0.004, +0.005] | −0.054 [−0.084, −0.021] | −0.009 [−0.028, +0.013] |
| pretip, sim_rotation | B | −0.037 [−0.051, −0.027] | +0.002 [−0.001, +0.004] | −0.055 [−0.071, −0.040] | **−0.018 [−0.028, −0.008]** |
| morning, sim_rotation | A | −0.034 [−0.040, −0.028] | −0.004 [−0.006, −0.003] | −0.045 [−0.055, −0.035] | **−0.011 [−0.018, −0.004]** |
| morning, sim_rotation | B | −0.018 [−0.022, −0.015] | +0.000 [−0.002, +0.002] | −0.029 [−0.036, −0.021] | **−0.010 [−0.017, −0.004]** |
| pretip, ewm5 | A | −0.041 [−0.072, −0.020] | +0.030 [+0.008, +0.061] | −0.098 [−0.153, −0.036] | **−0.057 [−0.096, −0.007]** |
| pretip, ewm5 | B | −0.037 [−0.047, −0.028] | +0.027 [+0.018, +0.037] | −0.073 [−0.089, −0.056] | **−0.036 [−0.050, −0.021]** |
| morning, ewm5 | A | −0.042 [−0.049, −0.034] | +0.017 [+0.009, +0.024] | −0.098 [−0.114, −0.081] | **−0.057 [−0.069, −0.044]** |
| morning, ewm5 | B | −0.021 [−0.025, −0.017] | +0.009 [+0.005, +0.013] | −0.045 [−0.056, −0.036] | **−0.024 [−0.034, −0.016]** |

The only combined − injury-only CI that includes 0 is pretip sim_rotation in window A (150 units, 5 game dates).

**By availability category** (sim_rotation; status at `as_of`). Only confirmed-available players are recalibrated;
every other category is identical to injury-only.

| slot, status | n | played | Brier: baseline → injury-only → **combined** | ECE: injury-only → combined (both arms) | slope: injury-only → combined (both arms) |
|---|---:|---:|---|---|---|
| pretip, unlisted (implicitly active) | 750 | 0.899 | 0.0944 → 0.0944 → **0.0732** (Δ −0.036 [−0.050, −0.021], both arms) | 0.162 → **0.042** | 1.03 → 1.18 |
| morning, unlisted | 2,247 | 0.891 | 0.0946 → 0.0946 → **0.0777** (Δ −0.035 [−0.045, −0.025], both arms) | 0.156 → **0.022** | 0.87 → 1.13 |
| pretip / morning, listed ACTIVE | 17 / 17 | 0.88 / 0.94 | 0.157 → **0.098** / 0.076 → **0.054** | small n | |
| out, doubtful, not on roster (suppressed) | 170 / 539 | 0.00 / 0.04 | 0.29 → **0.00** / 0.21 → **0.05** (injury overlay) | unchanged | |
| questionable | 27 / 138 | 0.44 / 0.45 | 0.385 → **0.260** / 0.318 → **0.255** (W2 cap) | unchanged | |
| unknown (no report yet), roster_unconfirmed | 566 / 133 | 0.74 / 0.00 | unchanged | unchanged | |

No subgroup gets worse, and none becomes falsely confident. Recalibrated confirmed-available players are slightly
**under**-confident (slope 1.13–1.18), which is the safe side.

## Prop ladders: P2 rejected

| slot, arm, family (pooled) | rungs | baseline Brier / ECE / slope | P2 Brier / ECE / slope | Δ Brier [95% CI] |
|---|---:|---|---|---|
| morning, sim_rotation, points | 20,344 | 0.0799 / 0.005 / 1.00 | 0.0807 / 0.016 / 1.13 | +0.0008 [+0.0003, +0.0014] |
| morning, sim_rotation, assists | 15,258 | 0.0732 / 0.009 / 0.93 | 0.0740 / 0.014 / 1.09 | +0.0009 [+0.0005, +0.0012] |
| morning, sim_rotation, threes | 15,258 | 0.1001 / 0.007 / 0.95 | 0.1010 / 0.018 / 1.08 | +0.0009 [+0.0004, +0.0015] |
| morning, sim_rotation, rebounds | 17,801 | 0.0926 / 0.011 / 0.98 | 0.0930 / 0.014 / 1.13 | +0.0004 [−0.0002, +0.0009] |
| pretip, sim_rotation, points | 5,688 | 0.0825 / 0.010 / 0.95 | 0.0828 / 0.012 / 1.08 | +0.0004 [−0.0006, +0.0014] |
| morning, ewm5, points | 20,344 | 0.0791 / 0.014 / 0.83 | 0.0794 / 0.014 / 1.05 | +0.0003 [−0.0004, +0.0010] |
| pretip, ewm5, points | 5,688 | 0.0807 / 0.021 / 0.83 | 0.0805 / 0.014 / 1.04 | −0.0002 [−0.0016, +0.0012] |

The rest of the 16 cells are in `replay.json`; none improves significantly. On the rungs of players who actually
played, the ladders are already close to calibrated (ECE 0.005–0.021). ewm5's slope of about 0.83–0.90 is
mildly over-confident. The walk-forward maps fix that slope, but the intercept shift costs more than the slope
gain. The postmortem's slope of 0.83 does not survive as a correctable error once ladders are scored only on
players who played. **The ladders stay unchanged.**

## Market comparison (Kalshi player-prop listings with bid and ask at the projection's `as_of`)

Pooled walk-forward window, sim_rotation. ewm5 is in `replay.json`; its direction is the same.

| slot | priced rungs (games) | market-mid Brier | model baseline Brier | Δ baseline − market | Δ P2 − market |
|---|---:|---:|---:|---|---|
| morning | 5,460 (50) | 0.1892 | 0.1759 | **−0.0132 [−0.0202, −0.0068]** | −0.0092 [−0.0154, −0.0034] |
| pretip | 6,109 (34) | 0.1556 | 0.1653 | +0.0096 [+0.0061, +0.0133] | +0.0122 [+0.0080, +0.0167] |

* **Morning:** the model's Brier is lower than the early listing's mid. Those quotes are thin and stale (market ECE
  0.069). This beats the quoted mid only; it is not tradeable edge (no spread, fees or fill evidence). Window A
  alone has 15 games.
* **Pretip:** **the market is better** than the model, and P2 widens the gap. No calibration variant here beats
  the pretip market.
* Participation calibration does not change prop rungs, which are conditional on playing and void on a DNP. Its
  value for props is choosing which players to quote (#104) and scoring unconditional markets.

## Coverage
Calibration adds and removes no forecast. Conditional quantiles are untouched. In the evaluation window, the #104
overlay withholds 270 of 175,716 prop rungs of players who then played (0.15%). Participation units:
9,298 scored, 1,282 suppressed by the overlay.

## Limits
* The data cover one month: 122 evaluated games, 86 of them in window B. The prospective check is pending.
* Rule 3's ECE tolerance (+0.01) is sample-size sensitive. A perfectly calibrated sharp forecaster on 4,000
  units can show ECE about 0.01–0.02 against a constant baseline (see the test). It did not decide any verdict
  here: P1 combined passed it, and P2 fails rules 1 and 2 independently.
* Calibration slopes of fully suppressed groups (every P = 0) are degenerate: they appear as huge numbers in
  `replay.json`. Those groups are identical with and without the calibrator, so they cannot trigger a rule. Their
  Brier is the meaningful number.
* Not wired into any collector, simulator or workflow. Minutes redistribution remains off.
