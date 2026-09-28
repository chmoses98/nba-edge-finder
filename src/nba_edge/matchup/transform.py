"""Apply matchup adjustments to V1 simulation parameters, without forking the simulator.

The pipeline is deliberately boring:

    V1 GameParams -> apply_matchup(...) -> GameParams' -> the existing, unmodified engine

No V2 simulator exists. The engine, the RNG, the convergence rules and every predictive constant
stay exactly as V1 left them; the only thing V2 can do is hand that engine a different set of
per-player rates. That is what makes "V1 unchanged when the layer is disabled" a property of the
code rather than a promise: with no adjustments, ``apply_matchup`` returns **the very same object**.

Two honesty constraints are built in.

*Not every adjustment is applicable.* V1 has no shot-zone decomposition, so rim/midrange/pull-up/
catch-and-shoot rate deltas have nowhere to land. They are accepted, carried in provenance and
reported as inapplicable -- never silently dropped, and never approximated into a field that means
something else.

*Bad data fails closed.* A malformed or non-finite adjustment raises instead of being coerced, and
clamping only ever protects the physical bounds of a rate; it never invents a value.
"""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Any

from nba_edge.matchup.schemas import MatchupAdjustment
from nba_edge.matchup.version import EFFECTS_VERSION, MATCHUP_MODEL_VERSION
from nba_edge.sim.params import GameParams, PlayerParams

# Adjustment fields V1's PlayerParams can actually consume, and where each lands.
APPLICABLE_FIELDS: dict[str, str] = {
    "fga_multiplier": "fga_per_min",
    "usage_multiplier": "usage_elasticity",
    "minutes_multiplier": "min_mean",
    "three_rate_delta": "three_share",
    "ft_rate_delta": "fta_per_fga",
    "turnover_rate_delta": "tov_weight",
    "assist_rate_delta": "ast_weight",
    "rebound_weight_delta": "oreb_weight/dreb_weight",
    "fg2_eff_delta": "fg2_pct",
    "fg3_eff_delta": "fg3_pct",
}

# Fields with no V1 counterpart. Recorded so a future V2 that models shot zones can use them, and
# reported now so nobody believes a rim-rate effect is being applied when it cannot be.
UNAPPLICABLE_FIELDS: tuple[str, ...] = (
    "rim_rate_delta",
    "midrange_rate_delta",
    "pullup_rate_delta",
    "catch_shoot_rate_delta",
)


class MatchupTransformError(RuntimeError):
    """An adjustment could not be applied safely. Never downgraded to a warning."""


def _finite(name: str, value: float) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        raise MatchupTransformError(f"adjustment field {name} is not a finite number: {value!r}")
    return float(value)


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def validate(adj: MatchupAdjustment) -> None:
    """Fail closed on anything that cannot be applied as written."""
    for name in (*APPLICABLE_FIELDS, *UNAPPLICABLE_FIELDS):
        _finite(name, getattr(adj, name))
    for name in ("fga_multiplier", "usage_multiplier", "minutes_multiplier"):
        if getattr(adj, name) <= 0:
            raise MatchupTransformError(f"{name} must be positive, got {getattr(adj, name)!r}")
    if adj.effects_version != EFFECTS_VERSION and not adj.effects_version:
        raise MatchupTransformError("adjustment carries no effects_version")


def apply_to_player(p: PlayerParams, adj: MatchupAdjustment) -> PlayerParams:
    """Return a new PlayerParams with the applicable parts of ``adj`` applied.

    Clamps keep rates physically valid -- a share stays in [0, 1], a rate stays non-negative. Those
    bounds protect the simulator from impossible inputs; they are not a way to sneak a default in,
    because a neutral adjustment never reaches a bound.
    """
    validate(adj)
    return replace(
        p,
        fga_per_min=max(0.0, p.fga_per_min * adj.fga_multiplier),
        usage_elasticity=max(0.0, p.usage_elasticity * adj.usage_multiplier),
        min_mean=max(0.0, p.min_mean * adj.minutes_multiplier),
        three_share=_clamp(p.three_share + adj.three_rate_delta, 0.0, 1.0),
        fta_per_fga=max(0.0, p.fta_per_fga + adj.ft_rate_delta),
        tov_weight=max(0.0, p.tov_weight * (1.0 + adj.turnover_rate_delta)),
        ast_weight=max(0.0, p.ast_weight * (1.0 + adj.assist_rate_delta)),
        oreb_weight=max(0.0, p.oreb_weight * (1.0 + adj.rebound_weight_delta)),
        dreb_weight=max(0.0, p.dreb_weight * (1.0 + adj.rebound_weight_delta)),
        fg2_pct=_clamp(p.fg2_pct + adj.fg2_eff_delta, 0.0, 1.0),
        fg3_pct=_clamp(p.fg3_pct + adj.fg3_eff_delta, 0.0, 1.0),
    )


def apply_matchup(
    game: GameParams,
    adjustments: dict[int, MatchupAdjustment] | None = None,
    *,
    enabled: bool = True,
) -> tuple[GameParams, dict[str, Any]]:
    """Transform V1 params by per-player matchup adjustments. Returns ``(params, report)``.

    When the layer is disabled, or there is nothing to apply, the ORIGINAL object is returned
    unchanged -- identity, not a copy -- so "V1 is untouched" is verifiable with ``is``.
    """
    report: dict[str, Any] = {
        "matchup_model_version": MATCHUP_MODEL_VERSION,
        "effects_version": EFFECTS_VERSION,
        "enabled": bool(enabled),
        "n_players_adjusted": 0,
        "n_adjustments_supplied": len(adjustments or {}),
        "neutral": True,
        "applied_fields": [],
        "inapplicable_fields_present": [],
        "players": {},
    }
    if not enabled or not adjustments:
        report["reason"] = "matchup layer disabled" if not enabled else "no adjustments supplied"
        return game, report

    active = {pid: a for pid, a in adjustments.items() if not a.is_neutral}
    for a in adjustments.values():
        validate(a)
        for f in UNAPPLICABLE_FIELDS:
            if getattr(a, f) != 0.0 and f not in report["inapplicable_fields_present"]:
                report["inapplicable_fields_present"].append(f)

    if not active:
        # Every supplied adjustment is the identity. Returning the original object makes the
        # "neutral layer reproduces V1 exactly" guarantee structural rather than numerical.
        report["reason"] = "all supplied adjustments are neutral"
        return game, report

    touched: set[str] = set()
    new_sides = {}
    for side in ("home", "away"):
        team = getattr(game, side)
        players = []
        for p in team.players:
            adj = active.get(p.nba_id)
            if adj is None:
                players.append(p)
                continue
            players.append(apply_to_player(p, adj))
            report["n_players_adjusted"] += 1
            fields = [f for f in APPLICABLE_FIELDS if getattr(adj, f) not in (1.0, 0.0)]
            touched.update(fields)
            report["players"][str(p.nba_id)] = {
                "adjustment_version": adj.adjustment_version,
                "effects_version": adj.effects_version,
                "confidence": adj.confidence,
                "source": adj.source,
                "sample_size": adj.sample_size,
                "fields": fields,
            }
        new_sides[side] = replace(team, players=players)

    report["neutral"] = report["n_players_adjusted"] == 0
    report["applied_fields"] = sorted(touched)
    if report["neutral"]:
        report["reason"] = "no adjusted player matched a roster entry"
        return game, report
    return replace(game, home=new_sides["home"], away=new_sides["away"]), report
