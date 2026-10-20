# Minutes reconstruction: the joint rotation model (JRM)

Research only (authority: none). Production is unchanged: the publisher runs the frozen engine unless `PF_NBA_MINUTES_ENGINE=jrm`, which nothing sets.

| file | what it is |
|---|---|
| `PHASE1_ROOT_CAUSE.md` | why projected team minutes exceed 241.5 on the 2026-10-20 slate, with the additive decomposition and the historical evidence |
| `../nba/minutes_jrm.py` | the model (eligibility head, depth-aware rotation heads, scenario sampling, exact team budget) and the live entry point `slate_minutes()` |
| `../results/jrm/` | frozen assets: list-size distribution, report-aware eligibility calibration, minutes residual distribution, readiness |
| `artifacts/MINUTES_COMPARISON_v2.md` | complete minutes comparison (aggregate + 12 subgroups, validation and holdout, paired game-clustered CIs, incumbent) |
| `artifacts/DOWNSTREAM_COMPARISON_v2.md` | points, rebounds, assists, threes, PRA, FGA with frozen vs JRM minutes (same frozen hyper-parameters, no retuning) |
| `artifacts/READINESS_CHECK.md` | the study's original READY rules applied to the production distributions on JRM minutes |
| `artifacts/REPORT_AWARE_2025_26.txt` | the live recipe replayed on 2025-26 with the archived point-in-time official reports (second half, calibrations fitted on the first) |
| `artifacts/LIVE_SLATE_AUDIT_v2.md` | per-team / per-player shadow of the 2026-10-20/22 slate, largest differences investigated |
| `artifacts/*_v1*`, `MINUTES_COMPARISON.md`, `DOWNSTREAM_COMPARISON.md`, `LIVE_SLATE_AUDIT.md` | v1 (role level from the linear blend D, commit 6af0202), superseded by v2 but kept: v1's holdout was scored once |

## Reproduce (from `research/projection_foundation`, Python 3.13, the pins in `.github/workflows/projection-foundation.yml`)
```
python -c "from nba import data; data.ensure_hoopr()"                       # 2014-15 .. 2026-27 box scores (sportsdataverse mirror)
python -m nba.pipeline                                                       # frozen features + minutes ladder + hurdle + stat ladders (cached in .cache/)
python -m nba.incumbent 2023 2024 2025 2026                                  # the production simulator, reproduced walk-forward
cd minutes_rebuild
python run_jrm.py 2018,2019,2020,2021,2022,2023,2024 --S 64 --tag v2dev      # walk-forward JRM, development + validation
python run_jrm.py 2025,2026 --S 64 --tag v2hold                              # holdout seasons (design frozen first, see below)
python evaluate_minutes.py artifacts/MINUTES_COMPARISON_v2.md v2dev v2hold
python downstream_fit.py jrm,frozen_inj,jrm_set v2dev v2hold _v2 && python evaluate_downstream.py artifacts/DOWNSTREAM_COMPARISON_v2.md _v2
python readiness_check.py artifacts/READINESS_CHECK.md _v2
python eval_report_2026.py                                                   # report-aware 2025-26 analogue of the live system
python phase1_decomposition.py FEED.json ../.cache/hoopr                     # root-cause decomposition on a published feed
python jrm_live.py FEED.json OUT_PREFIX --S 400 && python archive_shadow.py FEED.json OUT_PREFIX.csv ARCHIVE_DIR v2     # live shadow + immutable archive
python evaluate_prospective.py ARCHIVE_CHECKOUT OUT.md --dir jrm_v2_uniform  # scores the pre-registered prospective test
```
`JRM_LEVEL=D` reproduces v1.

## Protocol and its honest limits
* Chronological, point-in-time: every feature uses strictly earlier games; LightGBM is refit per season on the previous five; calibrations (eligibility, minutes residual, list size) are fitted on development seasons or on 2025-26 PIT reports' first half only.
* v1 was frozen at `6af0202` before any 2024-25 / 2025-26 scoring. Its holdout subgroup table then exposed one weakness (the role level `D`, a linear blend, mis-ranks players returning from long absences). v2 swaps it for the stronger marginal `E`; that choice was made on development + validation numbers, but the holdout was **re-scored** for v2, so the holdout is no longer a pristine one-shot for the final model. The v1 numbers are in the `_v1`/unsuffixed files.
* The genuinely independent test is prospective: pre-tip forecasts of the validated configuration are archived on the `minutes-shadow-archive` branch (`jrm_v2_uniform/`; `ERRATA.md` explains two earlier snapshots produced with a different allocation rule that must not be used) and `evaluate_prospective.py` carries its pre-registration. No model change is allowed after seeing those results.
* Not tuned on any 2026-27 game. Nothing here changes betting authority, routing, thresholds or staking.
