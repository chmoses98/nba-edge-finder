# Reproduction check of the eligible snapshot (written 2026-10-20T23:58Z, additive)

`jrm_v2_uniform/20261020T230949Z_jrm_v2.json.gz` (414 rows, 12 games) was regenerated from the exact input it recorded (production feed generated 2026-10-20T22:40:46Z) with the
repository's current model code (`nba/minutes_jrm.py`, defaults level E and uniform allocation, 400 scenarios, seed 7). All 414 rows match to the stored precision:
max |difference| = 0.0 for `p_play_jrm`, `minutes_given_play_jrm` and `expected_minutes_unconditional_jrm`.

The two earlier snapshots (`jrm_v1/`, `jrm_v2/`) were produced with variance-weighted allocation (see ERRATA.md) and are registered as NOT eligible. Ineligibility is recorded here;
the files themselves are untouched.
