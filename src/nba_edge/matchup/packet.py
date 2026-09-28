"""Matchup block for the research packet, so a future UI needs no simulator internals.

The shape is designed around one risk: a UI that renders "Likely defenders: Dort 51%" is extremely
persuasive, and it would be just as persuasive if the numbers were invented. So every field here is
either measured or explicitly absent, and the block always states whether the matchup layer actually
changed anything (``effects_active``). A UI showing a V2 projection identical to V1 with
``effects_active: false`` is telling the truth; one that hides that is not.
"""

from __future__ import annotations

from typing import Any

from nba_edge.matchup.schemas import (
    DefenderRef,
    GameMatchupContext,
    MatchupAdjustment,
    PlayerDefenderExposure,
    TeamDefensiveScheme,
)
from nba_edge.matchup.version import describe

# Below this share a defender is not worth calling "primary"; listing a 6% defender as a headline
# reads as knowledge we do not have.
PRIMARY_DEFENDER_MIN_SHARE = 0.20


def exposure_block(exposure: PlayerDefenderExposure | None) -> dict[str, Any]:
    if exposure is None:
        return {
            "available": False,
            "reason": "no defensive-assignment data for this player",
            "projected_primary_defenders": [],
            "defender_exposure_distribution": [],
            "matchup_confidence": None,
        }
    dist = [
        {
            "kind": s.ref.value,
            "player_id": s.defender_player_id,
            "label": s.label,
            "share": round(s.share, 4),
            "confidence": s.confidence,
            "evidence": s.evidence,
        }
        for s in exposure.shares
    ]
    primaries = [
        d for d in dist
        if d["kind"] == DefenderRef.PLAYER.value and d["share"] >= PRIMARY_DEFENDER_MIN_SHARE
    ]
    return {
        "available": not exposure.is_unknown,
        "reason": None if not exposure.is_unknown else "assignment evidence insufficient; reported UNKNOWN",
        "projected_primary_defenders": primaries,
        "defender_exposure_distribution": dist,
        "identified_share": round(exposure.identified_share, 4),
        "matchup_confidence": exposure.confidence,
        "observed_at_utc": exposure.observed_at_utc.isoformat(),
        "source": exposure.source,
    }


def scheme_block(scheme: TeamDefensiveScheme | None) -> dict[str, Any]:
    if scheme is None:
        return {"available": False, "reason": "no scheme-proxy source ingested", "features": {}}
    return {
        "available": bool(scheme.known_features),
        "reason": None if scheme.known_features else "scheme record exists but every feature is unavailable",
        "observed_at_utc": scheme.observed_at_utc.isoformat(),
        "source": scheme.source,
        "features": {
            str(name): {
                "value": m.value,
                "availability": m.availability.value,
                "sample_size": m.sample_size,
                "source": m.source,
            }
            for name, m in sorted(scheme.features.items(), key=lambda kv: str(kv[0]))
        },
    }


def adjustment_block(adj: MatchupAdjustment | None) -> dict[str, Any]:
    if adj is None:
        return {"available": False, "reason": "no adjustment produced for this player", "effects": {}}
    effects = {
        f: getattr(adj, f)
        for f in (
            "fga_multiplier", "usage_multiplier", "minutes_multiplier",
            "rim_rate_delta", "midrange_rate_delta", "three_rate_delta",
            "pullup_rate_delta", "catch_shoot_rate_delta", "ft_rate_delta",
            "turnover_rate_delta", "assist_rate_delta", "rebound_weight_delta",
            "fg2_eff_delta", "fg3_eff_delta",
        )
        if getattr(adj, f) not in (1.0, 0.0)
    }
    return {
        "available": True,
        "neutral": adj.is_neutral,
        "adjustment_version": adj.adjustment_version,
        "effects_version": adj.effects_version,
        "confidence": adj.confidence,
        "source": adj.source,
        "sample_size": adj.sample_size,
        "notes": list(adj.notes),
        "effects": effects,
    }


def matchup_packet(
    *,
    context: GameMatchupContext | None,
    offensive_player_id: int,
    adjustment: MatchupAdjustment | None = None,
    v1_projection: dict[str, float] | None = None,
    v2_projection: dict[str, float] | None = None,
    data_freshness_minutes: float | None = None,
) -> dict[str, Any]:
    """The per-player matchup block a UI can render directly.

    ``delta_v2_v1`` is computed, never supplied, so a caller cannot present a delta that does not
    follow from the two projections it also shows.
    """
    exposure = context.exposure_for(offensive_player_id) if context else None
    home_scheme = context.home_scheme if context else None
    away_scheme = context.away_scheme if context else None

    delta: dict[str, float] = {}
    if v1_projection and v2_projection:
        for k, v1 in v1_projection.items():
            if k in v2_projection:
                delta[k] = round(v2_projection[k] - v1, 6)

    effects_active = bool(adjustment and not adjustment.is_neutral)
    return {
        "offensive_player_id": offensive_player_id,
        "game_id": context.game_id if context else None,
        "matchup": exposure_block(exposure),
        "defensive_scheme_context": {
            "home": scheme_block(home_scheme),
            "away": scheme_block(away_scheme),
        },
        "matchup_adjustments": adjustment_block(adjustment),
        "v1_projection": v1_projection or {},
        "v2_projection": v2_projection or {},
        "delta_v2_v1": delta,
        "effects_active": effects_active,
        # Empty until effects are learned. A UI must not render a reason where none was measured.
        "explanatory_factors": (
            sorted(adjustment_block(adjustment)["effects"]) if effects_active else []
        ),
        "explanatory_factors_reason": (
            None if effects_active
            else "matchup layer ran and produced a neutral adjustment: no effect has been learned yet"
        ),
        "lineup_confidence": context.lineup_confidence.value if context else None,
        "data_freshness_minutes": data_freshness_minutes,
        "context_observed_at_utc": context.observed_at_utc.isoformat() if context else None,
        "provenance": describe(),
    }
