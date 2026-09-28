"""The shot-profile block a UI can render, while the effect is still unlearned.

The design problem this solves: a panel that shows nothing looks like missing data, and a panel that
shows a projected point swing claims knowledge nobody has. So the block states **facts with their
sample**, and says in a field that no effect has been learned.

    allowed:   "Takes 38% of attempts at the rim; opponent allows 31% at the rim (n=412 / 1,890)."
    forbidden: "+2.8 projected points from this matchup."

``effect_status`` is what a renderer must check before drawing anything that looks like a
projection. It is ``NEUTRAL/UNLEARNED`` until a leakage-free out-of-sample study says otherwise.
"""

from __future__ import annotations

from typing import Any

from nba_edge.shotprofile.court import ShotZone
from nba_edge.shotprofile.events import DEFENDER_ATTRIBUTION_AVAILABLE
from nba_edge.shotprofile.features import FEATURES_VERSION, ShotProfileMatchupContext

EFFECT_STATUS_UNLEARNED = "NEUTRAL/UNLEARNED"

# A zone difference smaller than this is not worth a sentence in a UI: zone rates carry a standard
# error of several points at realistic sample sizes, so a 1% gap is a rounding artefact presented as
# a basketball fact.
NOTABLE_DELTA = 0.05

ZONE_LABELS = {
    ShotZone.RIM.value: "at the rim",
    ShotZone.PAINT_NON_RIM.value: "in the paint (non-rim)",
    ShotZone.MIDRANGE.value: "from midrange",
    ShotZone.CORNER_THREE.value: "from the corners",
    ShotZone.ABOVE_BREAK_THREE.value: "from above the break",
}


def describe_deltas(ctx: ShotProfileMatchupContext, *, limit: int = 3) -> list[str]:
    """Factual sentences about the two profiles. Never a projection, never a recommendation.

    Each one is a statement about what has already happened, which is the only kind of claim this
    data supports.
    """
    out = []
    ranked = sorted(ctx.deltas.items(), key=lambda kv: abs(kv[1]), reverse=True)
    for zone, delta in ranked[:limit]:
        if abs(delta) < NOTABLE_DELTA:
            continue
        p = ctx.player.zone_rate.get(zone, 0.0)
        o = ctx.opponent_allowed.zone_rate.get(zone, 0.0)
        out.append(
            f"Takes {p:.0%} of attempts {ZONE_LABELS.get(zone, zone)}; "
            f"opponent allows {o:.0%} there."
        )
    return out


def shot_profile_block(
    ctx: ShotProfileMatchupContext | None, *, reason_if_absent: str | None = None
) -> dict[str, Any]:
    """The renderable block, or an explicit absence with a reason.

    A UI that receives ``available: False`` with a reason can say why it is empty. One that receives
    an empty dict shows a blank panel, which readers interpret as "no matchup edge" -- a conclusion
    the data has not licensed.
    """
    if ctx is None:
        return {
            "available": False,
            "reason": reason_if_absent or "no shot-profile context for this player-game",
            "effect_status": EFFECT_STATUS_UNLEARNED,
            "defender_attribution_available": DEFENDER_ATTRIBUTION_AVAILABLE,
            "features_version": FEATURES_VERSION,
        }

    d = ctx.as_dict()
    return {
        "available": True,
        "player_shot_profile": d["player_shot_profile"],
        "opponent_shot_profile_allowed": d["opponent_shot_profile_allowed"],
        "matchup_profile_deltas": d["matchup_profile_deltas"],
        "sample_size": d["sample_size"],
        "confidence": d["confidence"],
        "data_freshness_days": ctx.freshness_days(),
        "factual_notes": describe_deltas(ctx),
        # The two fields a renderer must respect.
        "effect_status": EFFECT_STATUS_UNLEARNED,
        "projected_effect": None,
        "projected_effect_reason": (
            "No effect has been learned. These are descriptions of past attempts, not a forecast; "
            "a shot-profile feature earns predictive influence only after leakage-free, "
            "out-of-sample evidence beats V1, the market and the hybrid."
        ),
        # Stated in the payload, not just in the docs, so a consumer cannot quietly treat an
        # opponent's allowed profile as evidence about an individual defender.
        "defender_attribution_available": DEFENDER_ATTRIBUTION_AVAILABLE,
        "opponent_profile_is": "team/scheme proxy from attempts allowed -- NOT defender attribution",
        "provenance": {
            **d["provenance"],
            "features_version": FEATURES_VERSION,
            "geometry": "docs/research/ESPN_SHOT_COORDINATES.md",
        },
    }
