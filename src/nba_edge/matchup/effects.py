"""Turning matchup context into adjustments -- neutrally, until an effect has been learned.

This is the seam a future fitted model plugs into, and it is deliberately empty of basketball
opinion. There is no table of "elite defender -> -8% scoring" anywhere in this package, and adding
one would defeat the point: the research question is whether matchup information improves forecasts
*beyond V1 and the market*, and you cannot answer that with effects you wrote down yourself.

While ``EFFECTS_VERSION`` is a ``neutral-*`` version, ``resolve_adjustments`` returns exactly
neutral adjustments and says why in each record's notes. A fitted estimator supplies its own
versioned effects later; its output is validated the same way, and anything malformed fails closed
rather than being partially applied.
"""

from __future__ import annotations

from typing import Protocol

from nba_edge.matchup.schemas import GameMatchupContext, MatchupAdjustment
from nba_edge.matchup.transform import validate
from nba_edge.matchup.version import EFFECTS_VERSION, effects_are_neutral


class EffectEstimator(Protocol):
    """A fitted matchup-effect model. Implemented by a future wave, not by this one."""

    version: str

    def estimate(self, context: GameMatchupContext) -> dict[int, MatchupAdjustment]:
        """Per offensive player id, the adjustment implied by this context."""
        ...


def neutral_adjustments(
    context: GameMatchupContext,
    *,
    effects_version: str = EFFECTS_VERSION,
    reason: str = "no matchup effect has been estimated from data",
) -> dict[int, MatchupAdjustment]:
    """A neutral adjustment for every player the context describes.

    Returned rather than an empty dict so provenance still records that the matchup layer ran, saw
    these players, and chose to change nothing -- which is different from the layer not running.
    """
    players: list[int] = []
    for e in context.exposures:
        if e.offensive_player_id not in players:
            players.append(e.offensive_player_id)
    for pid in (*context.expected_home_rotation, *context.expected_away_rotation):
        if pid not in players:
            players.append(pid)
    return {
        pid: MatchupAdjustment.neutral(
            context.game_id, pid, effects_version=effects_version, notes=(reason,)
        )
        for pid in players
    }


def resolve_adjustments(
    context: GameMatchupContext,
    *,
    estimator: EffectEstimator | None = None,
    effects_version: str = EFFECTS_VERSION,
) -> tuple[dict[int, MatchupAdjustment], dict[str, object]]:
    """``(adjustments, report)``. Neutral unless a fitted estimator supplies something else."""
    report: dict[str, object] = {
        "game_id": context.game_id,
        "effects_version": effects_version,
        "estimator": getattr(estimator, "version", None) if estimator else None,
        "context_observed_at_utc": context.observed_at_utc.isoformat(),
        "lineup_confidence": context.lineup_confidence.value,
        "n_exposures": len(context.exposures),
        "n_unknown_exposures": sum(1 for e in context.exposures if e.is_unknown),
    }

    if estimator is None or effects_are_neutral(effects_version):
        reason = (
            "no fitted estimator supplied"
            if estimator is None
            else f"effects_version {effects_version} is neutral: nothing has been learned yet"
        )
        adj = neutral_adjustments(context, effects_version=effects_version, reason=reason)
        report.update(neutral=True, reason=reason, n_adjustments=len(adj), n_active=0)
        return adj, report

    produced = estimator.estimate(context)
    for pid, a in produced.items():
        # Fail closed on anything an estimator got wrong, rather than applying the good half.
        validate(a)
        if a.offensive_player_id != pid:
            raise ValueError(f"estimator keyed {pid} to an adjustment for {a.offensive_player_id}")
        if a.game_id != context.game_id:
            raise ValueError(f"estimator returned an adjustment for game {a.game_id}")
        if a.effects_version != effects_version:
            raise ValueError(
                f"adjustment claims effects_version {a.effects_version!r} but the resolver is "
                f"running {effects_version!r}; a result must not misstate which effects produced it"
            )
    n_active = sum(1 for a in produced.values() if not a.is_neutral)
    report.update(neutral=n_active == 0, n_adjustments=len(produced), n_active=n_active)
    return produced, report
