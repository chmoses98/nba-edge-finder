"""Version identity for the matchup-aware research arm.

This arm is deliberately a SEPARATE identifier from the production baseline. The frozen baseline
``NBA_BASELINE_2026_PRESEASON_V1`` describes the predictive parameters production actually uses; it
is never edited, re-digested or "extended" by anything here. A V2 result instead carries BOTH ids,
so a reader can always tell which V1 it was computed against and which matchup layer was applied.

The distinction that matters most in this module is between *architecture existing* and *an effect
being known*. ``EFFECTS_VERSION`` is the learned-effect version, and it starts at ``neutral-0``,
meaning: the machinery is wired, and every adjustment it produces is exactly neutral because no
effect has been estimated from data yet. A future wave that fits effects mints a NEW effects
version; it must never silently re-point ``neutral-0`` at fitted numbers.
"""

from __future__ import annotations

from typing import Any

# The research arm's own identifier. Not a baseline, not a production model.
MATCHUP_MODEL_VERSION = "MATCHUP_AWARE_V2"

# The schema generation for matchup records on the archive.
MATCHUP_SCHEMA_VERSION = "matchup/1"

# The LEARNED-EFFECT version. `neutral-0` is the explicit statement that no matchup effect has been
# estimated: every adjustment is the identity. Fitting effects mints a new id (e.g. `fitted-2027a`)
# and the old one keeps meaning what it meant.
NEUTRAL_EFFECTS_VERSION = "neutral-0"
EFFECTS_VERSION = NEUTRAL_EFFECTS_VERSION

# Authority is fixed here, not configurable. Nothing in the matchup arm may carry betting authority
# until a leakage-free prospective study shows it beats both V1 and the market.
MATCHUP_AUTHORITY = "RESEARCH"


def effects_are_neutral(effects_version: str = EFFECTS_VERSION) -> bool:
    """True while no matchup effect has been estimated from data."""
    return effects_version.startswith("neutral-")


def describe(baseline_id: str | None = None, baseline_digest: str | None = None) -> dict[str, Any]:
    """The provenance stamp every V2 result must carry.

    Reads the frozen baseline live rather than restating it, so a V2 record can never claim to have
    been computed against a V1 that it was not.
    """
    if baseline_id is None or baseline_digest is None:
        try:
            from nba_edge.baseline.manifest import BASELINE_DIGEST, BASELINE_ID, compute_digest

            baseline_id = baseline_id or BASELINE_ID
            baseline_digest = baseline_digest or BASELINE_DIGEST
            intact = compute_digest() == BASELINE_DIGEST
        except Exception as e:  # noqa: BLE001 - research stamp must not depend on the manifest importing
            baseline_id = baseline_id or "unavailable"
            baseline_digest = baseline_digest or "unavailable"
            intact = None
            return {
                "matchup_model_version": MATCHUP_MODEL_VERSION,
                "matchup_schema_version": MATCHUP_SCHEMA_VERSION,
                "effects_version": EFFECTS_VERSION,
                "effects_neutral": effects_are_neutral(),
                "authority": MATCHUP_AUTHORITY,
                "v1_baseline_id": baseline_id,
                "v1_baseline_digest": baseline_digest,
                "v1_baseline_intact": intact,
                "baseline_error": str(e)[:200],
            }
    else:
        intact = None
    return {
        "matchup_model_version": MATCHUP_MODEL_VERSION,
        "matchup_schema_version": MATCHUP_SCHEMA_VERSION,
        "effects_version": EFFECTS_VERSION,
        "effects_neutral": effects_are_neutral(),
        "authority": MATCHUP_AUTHORITY,
        "v1_baseline_id": baseline_id,
        "v1_baseline_digest": baseline_digest,
        "v1_baseline_intact": intact,
    }
