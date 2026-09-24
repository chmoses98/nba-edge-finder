"""A tamper-evident freeze of every parameter that can change a prediction.

Why this exists
---------------
Two waves of work have now established that the market beats this model in all eight tested
families. That is the current result, and it is only worth anything if a future comparison is
honest. It stops being honest the moment a predictive parameter changes without anyone noticing --
a re-tuned constant, a different half-life, a quietly swapped default -- because then "the new model
is better" may just mean "the new model is different and nobody recorded the old one".

Recording version STRINGS does not prevent that. ``MODEL_VERSION = "nba-sim-0.1.0"`` stays exactly
the same when someone edits ``rating_scale`` from 1.9 to 2.1. So this module hashes the parameter
VALUES: change any of them and the digest changes, a test fails, and the change has to be deliberate.

What is frozen, and what is not
-------------------------------
Frozen: anything that can move a number the model outputs. League constants, the feature builder's
half-lives and shrinkage, ``rating_scale``, the rotation model's thresholds and size distribution,
minutes caps, hybrid weights, and the pricing/settlement engine versions.

Not frozen, and deliberately so: data collection, capture cadence, infrastructure, workflow safety,
reporting, and bug fixes whose purpose is to make the code do what it already claimed to do. Those
may improve freely -- that is the point of the current wave.

The contract
------------
Any change to a frozen value requires minting a NEW baseline id and keeping the old one in
``KNOWN_BASELINES``. A future model is then compared prospectively against the frozen one, rather
than against a moving target nobody can reconstruct.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from nba_edge import MODEL_VERSION
from nba_edge.features.build import FEATURE_VERSION, BuildConfig
from nba_edge.settlement.engine import ENGINE_VERSION
from nba_edge.sim.engine import SIM_VERSION
from nba_edge.sim.params import LEAGUE, PlayerParams
from nba_edge.sim.rotation import ROTATION_MIN, ROTATION_SIZE_PMF
from nba_edge.sim.season import SEASON_SIM_VERSION

BASELINE_ID = "NBA_BASELINE_2026_PRESEASON_V1"

# Digest of the frozen values below, minted 2026-09-24 against main 250a7b3. Recomputed by the test
# suite on every run; a mismatch means a predictive parameter moved.
BASELINE_DIGEST = "5a4cbda0b973d1e4d6289557b99372e4735ebe3146fa76e8f0b6ca833193be78"

KNOWN_BASELINES: dict[str, str] = {BASELINE_ID: BASELINE_DIGEST}  # every baseline ever minted, never removed


@dataclass(frozen=True)
class BaselineManifest:
    baseline_id: str
    digest: str
    model_version: str
    sim_version: str
    feature_version: str
    season_sim_version: str
    settlement_engine_version: str
    parameters: dict[str, Any]

    def to_json(self) -> dict[str, Any]:
        return {
            "baseline_id": self.baseline_id,
            "digest": self.digest,
            "versions": {
                "model": self.model_version,
                "simulation": self.sim_version,
                "features": self.feature_version,
                "season_simulation": self.season_sim_version,
                "settlement_engine": self.settlement_engine_version,
            },
            "parameters": self.parameters,
        }


def _hybrid_weights() -> dict[str, Any]:
    """The market/model blend weights, read from the slate job rather than restated here."""
    from nba_edge.workflows import simulate as sim_job

    return {
        "hybrid_market_weight": getattr(sim_job, "HYBRID_MARKET_WEIGHT", None),
        "hybrid_weight_by_scope": dict(getattr(sim_job, "HYBRID_WEIGHT_BY_SCOPE", {}) or {}),
        "stale_market_minutes": getattr(sim_job, "STALE_MARKET_MIN", None),
    }


def frozen_parameters() -> dict[str, Any]:
    """Every value that can move a prediction, in a stable, hashable form.

    Read from the live code rather than copied, so the manifest cannot silently disagree with what
    the simulator actually uses -- a hand-maintained copy would defeat the entire purpose.
    """
    cfg = BuildConfig()
    defaults = PlayerParams(nba_id=0, team_id=0, name="", p_play=1.0, p_start=0.0, min_mean=0.0, min_sd=0.0)
    return {
        "league_constants": {k: list(v) if isinstance(v, tuple) else v for k, v in sorted(LEAGUE.items())},
        "feature_builder": {
            "team_half_life": cfg.team_half_life,
            "team_prior_games": cfg.team_prior_games,
            "player_half_life": cfg.player_half_life,
            "player_prior_minutes": cfg.player_prior_minutes,
            "rate_half_life": cfg.rate_half_life,
            "role_window": cfg.role_window,
            "recent_team_games": cfg.recent_team_games,
            "rotation_window": cfg.rotation_window,
            "rotation_half_life": cfg.rotation_half_life,
            "rating_scale": cfg.rating_scale,
            "max_roster": cfg.max_roster,
            "min_player_games": cfg.min_player_games,
            "include_preseason": cfg.include_preseason,
        },
        "rotation_model": {
            "rotation_min_minutes": ROTATION_MIN,
            "rotation_size_pmf": {str(k): v for k, v in sorted(ROTATION_SIZE_PMF.items())},
        },
        "player_defaults": {
            "min_cap": defaults.min_cap,
            "minutes_dispersion": defaults.minutes_dispersion,
            "impact_ppp": defaults.impact_ppp,
            "usage_elasticity": defaults.usage_elasticity,
        },
        "pricing": _hybrid_weights(),
    }


def compute_digest(params: dict[str, Any] | None = None) -> str:
    """sha256 over the canonical JSON of the frozen parameters plus the version strings.

    Sorted keys and fixed separators so the digest depends on the values, not on dict ordering or
    formatting.
    """
    payload = {
        "parameters": params if params is not None else frozen_parameters(),
        "versions": {
            "model": MODEL_VERSION,
            "simulation": SIM_VERSION,
            "features": FEATURE_VERSION,
            "season_simulation": SEASON_SIM_VERSION,
            "settlement_engine": ENGINE_VERSION,
        },
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def current_manifest() -> BaselineManifest:
    params = frozen_parameters()
    return BaselineManifest(
        baseline_id=BASELINE_ID,
        digest=compute_digest(params),
        model_version=MODEL_VERSION,
        sim_version=SIM_VERSION,
        feature_version=FEATURE_VERSION,
        season_sim_version=SEASON_SIM_VERSION,
        settlement_engine_version=ENGINE_VERSION,
        parameters=params,
    )
