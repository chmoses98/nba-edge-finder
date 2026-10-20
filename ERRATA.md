# Errata (written 2026-10-20 ~23:10Z, before any of these games had been scored)

The two earlier snapshots, `jrm_v1/20261020T223327Z_jrm_v1.json.gz` and `jrm_v2/20261020T230246Z_jrm_v2.json.gz`, were produced by a live-shadow runner that
passed `alloc="var"` (variance-weighted conservation) to the model. The configuration that was selected and validated on development / validation seasons is
`alloc="uniform"` (equal minutes per eligible player). Participation probabilities (`p_play_jrm`, `eligible_prob`) and the raw scenario sums are identical under
both rules; the conservation correction, and therefore `minutes_given_play_jrm` and `expected_minutes_unconditional_jrm`, differ by up to ~6 minutes for individual
players. Those two files are retained unaltered as a record of the variance-weighted variant (not the validated one) and must NOT be used to evaluate the validated model.

Valid pre-tip records of the validated configuration are in `jrm_v2_uniform/` (every file there records `"allocation": "uniform (validated configuration)"` and
the code commit). PHI @ NYK (23:00Z) started before the first corrected snapshot existed, so it has no pre-tip record of the validated configuration.
