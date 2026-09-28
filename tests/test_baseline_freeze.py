"""The freeze is only real if something fails when it is broken.

Two waves of research concluded that the market beats this model in all eight tested families. That
conclusion is worth keeping only if a future comparison is honest, and it stops being honest the
moment a predictive parameter moves without anyone recording it -- "the new model is better" then
may only mean "the new model is different and the old one is unreconstructable".

So this file fails loudly when a frozen value changes. It is not asserting the values are *right*;
it is asserting that changing them is a deliberate act with a new baseline id attached.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nba_edge.baseline.manifest import (
    BASELINE_DIGEST,
    BASELINE_ID,
    KNOWN_BASELINES,
    compute_digest,
    current_manifest,
    frozen_parameters,
)

REPO = Path(__file__).resolve().parents[1]


def test_predictive_parameters_have_not_changed_without_a_new_baseline():
    """The whole point of the freeze.

    If this fails you changed something that moves predictions. That is allowed -- but it requires
    minting a NEW baseline id, adding the old one to KNOWN_BASELINES, and comparing the new model
    prospectively against the frozen one. It is not allowed to simply update the digest in place and
    carry on, because that erases the baseline the comparison depends on.
    """
    actual = compute_digest()
    assert actual == BASELINE_DIGEST, (
        f"\n\nA frozen predictive parameter changed.\n"
        f"  baseline : {BASELINE_ID}\n"
        f"  expected : {BASELINE_DIGEST}\n"
        f"  actual   : {actual}\n\n"
        f"If deliberate: mint a new BASELINE_ID, keep the old entry in KNOWN_BASELINES, and record\n"
        f"why in docs/research/MODEL_FREEZE.md. Do not just paste the new digest over the old one.\n"
    )


def test_the_frozen_values_are_the_ones_the_simulator_actually_uses():
    """The manifest reads live code rather than restating values.

    A hand-maintained copy would drift from the simulator and defeat the entire purpose, so this
    pins the link: change the source of truth and the manifest must follow.
    """
    from nba_edge.features.build import BuildConfig
    from nba_edge.sim.params import LEAGUE
    from nba_edge.sim.rotation import ROTATION_MIN

    p = frozen_parameters()
    assert p["feature_builder"]["rating_scale"] == BuildConfig().rating_scale
    assert p["league_constants"]["ppp"] == LEAGUE["ppp"]
    assert p["rotation_model"]["rotation_min_minutes"] == ROTATION_MIN


def test_the_manifest_covers_every_parameter_family_the_brief_named():
    """Coverage check: a freeze that quietly omits a knob is not a freeze."""
    p = frozen_parameters()
    assert {"league_constants", "feature_builder", "rotation_model", "player_defaults", "pricing"} <= set(p)
    fb = p["feature_builder"]
    for k in ("rating_scale", "player_half_life", "team_half_life", "rotation_window", "rotation_half_life"):
        assert k in fb, f"feature builder parameter {k} is not frozen"
    for k in ("pace", "ppp", "home_ppp_edge", "tov_per_poss", "oreb_pct", "fg2_pct", "fg3_pct"):
        assert k in p["league_constants"], f"league constant {k} is not frozen"
    assert p["rotation_model"]["rotation_size_pmf"], "the rotation size distribution is a predictive parameter"
    assert p["pricing"]["hybrid_weight_by_scope"], "hybrid weights are predictive parameters"


def test_the_digest_responds_to_a_change_in_any_frozen_value():
    """A digest that does not move when a parameter moves is worse than no digest."""
    base = frozen_parameters()
    original = compute_digest(base)

    for path in (
        ("feature_builder", "rating_scale"),
        ("league_constants", "ppp"),
        ("rotation_model", "rotation_min_minutes"),
        ("player_defaults", "impact_ppp"),
    ):
        mutated = json.loads(json.dumps(base))
        cur = mutated
        for k in path[:-1]:
            cur = cur[k]
        cur[path[-1]] = (cur[path[-1]] or 0) + 0.5
        assert compute_digest(mutated) != original, f"changing {'.'.join(path)} did not move the digest"


def test_known_baselines_never_loses_an_entry():
    """Old baselines are the comparison points; dropping one destroys the ability to compare."""
    assert BASELINE_ID in KNOWN_BASELINES
    assert KNOWN_BASELINES[BASELINE_ID] == BASELINE_DIGEST


def test_the_committed_manifest_artifact_matches_the_code():
    """The published JSON is what a future reader will diff against, so it must not go stale."""
    path = REPO / "docs" / "baseline" / f"{BASELINE_ID}.json"
    if not path.exists():
        pytest.skip("manifest artifact not generated yet")
    published = json.loads(path.read_text())
    live = current_manifest().to_json()
    assert published["digest"] == live["digest"], "the committed manifest no longer matches the code"
    assert published["parameters"] == live["parameters"]
