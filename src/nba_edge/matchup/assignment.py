"""Estimating who is likely to guard whom -- as a distribution, with UNKNOWN as a real answer.

The brief's constraint is the important one: **do not rely on position equality alone.** "Both are
listed SG" is close to worthless as evidence about assignments; teams cross-match, hide weak
defenders, put their point-of-attack stopper on the opposing primary regardless of listed position,
and switch. A model that infers a named defender from position alone will be confidently wrong in
exactly the games anyone cares about.

So this module enforces a hierarchy of evidence strength:

* **Observed assignment shares** (from real matchup data) can produce named-PLAYER shares.
* **Positional or archetype compatibility alone** can only ever produce POSITION/ARCHETYPE shares --
  it is not allowed to name a defender, because it does not know one.
* **No usable evidence** produces a single UNKNOWN share of 1.0.

Nothing here invents a number. There is no fallback prior that quietly becomes the answer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from nba_edge.matchup.schemas import (
    SHARE_TOLERANCE,
    DefenderRef,
    DefenderShare,
    PlayerDefenderExposure,
)

# An observed-share estimate needs at least this many prior possessions behind it before it is
# allowed to name defenders. Below it the sample is noise and the honest answer is positional or
# unknown. Deliberately conservative: overfitting a handful of possessions of individual
# defender-vs-player history is one of the failure modes the brief names explicitly.
MIN_POSSESSIONS_FOR_NAMED_DEFENDERS = 200

# Mass left unassigned after named shares is attributed to switches/other rather than being
# renormalised away, so "we modelled 84% of this player's possessions" stays visible.
MIN_RESIDUAL_TO_RECORD = 1e-9


@dataclass
class AssignmentEvidence:
    """What we actually know. Every field optional; absent means absent, not zero."""

    # {defender_player_id: share} observed historically for this offensive player vs this opponent.
    observed_shares: dict[int, float] | None = None
    observed_possessions: int | None = None
    # {position_or_archetype_label: share} -- weaker evidence, cannot name a player.
    positional_shares: dict[str, float] | None = None
    # Team switch frequency in [0, 1]; when high, more mass belongs in switch/other.
    switch_frequency: float | None = None
    source: str = "unknown"
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def has_named_evidence(self) -> bool:
        return bool(
            self.observed_shares
            and self.observed_possessions is not None
            and self.observed_possessions >= MIN_POSSESSIONS_FOR_NAMED_DEFENDERS
        )

    @property
    def has_positional_evidence(self) -> bool:
        return bool(self.positional_shares)


def unknown_exposure(game_id: str, offensive_player_id: int, observed_at_utc: datetime,
                     source: str, reason: str) -> PlayerDefenderExposure:
    """The honest answer when evidence is insufficient."""
    return PlayerDefenderExposure(
        game_id=game_id,
        offensive_player_id=offensive_player_id,
        observed_at_utc=observed_at_utc,
        shares=(DefenderShare(ref=DefenderRef.UNKNOWN, share=1.0, evidence=reason),),
        confidence=0.0,
        source=source,
        provenance={"reason": reason},
    )


def estimate_exposure(
    game_id: str,
    offensive_player_id: int,
    observed_at_utc: datetime,
    evidence: AssignmentEvidence,
) -> PlayerDefenderExposure:
    """Probabilistic defensive exposure for one offensive player.

    Returns UNKNOWN unless the evidence clears the bar for its kind. Confidence is reported and is
    never 1.0: assignment is a distribution over a noisy process even when well measured.
    """
    if evidence.has_named_evidence:
        raw = {pid: s for pid, s in (evidence.observed_shares or {}).items() if s > 0}
        if not raw:
            return unknown_exposure(game_id, offensive_player_id, observed_at_utc,
                                    evidence.source, "observed shares were all zero")
        total = sum(raw.values())
        if total > 1.0 + SHARE_TOLERANCE:
            # Fail closed: shares that exceed 1 mean the upstream estimate is wrong, and silently
            # renormalising would hide that.
            raise ValueError(f"observed defender shares sum to {total!r}, which exceeds 1.0")
        shares = [
            DefenderShare(ref=DefenderRef.PLAYER, defender_player_id=pid, share=s,
                          evidence=f"observed over {evidence.observed_possessions} possessions")
            for pid, s in sorted(raw.items(), key=lambda kv: (-kv[1], kv[0]))
        ]
        residual = 1.0 - total
        if residual > MIN_RESIDUAL_TO_RECORD:
            shares.append(DefenderShare(
                ref=DefenderRef.SWITCH_OTHER, share=residual,
                evidence="unmodelled possessions: switches, help and unattributed",
            ))
        # More possessions -> more confidence, saturating well below certainty.
        n = evidence.observed_possessions or 0
        confidence = min(0.85, n / (n + 400.0))
        return PlayerDefenderExposure(
            game_id=game_id, offensive_player_id=offensive_player_id,
            observed_at_utc=observed_at_utc, shares=tuple(shares), confidence=confidence,
            source=evidence.source,
            provenance={"basis": "observed_shares", "possessions": str(n)},
        )

    if evidence.has_positional_evidence:
        raw = {lbl: s for lbl, s in (evidence.positional_shares or {}).items() if s > 0}
        total = sum(raw.values())
        if total <= 0:
            return unknown_exposure(game_id, offensive_player_id, observed_at_utc,
                                    evidence.source, "positional shares were all zero")
        if total > 1.0 + SHARE_TOLERANCE:
            raise ValueError(f"positional shares sum to {total!r}, which exceeds 1.0")
        shares = [
            DefenderShare(ref=DefenderRef.POSITION, label=lbl, share=s,
                          evidence="positional compatibility only; cannot name a defender")
            for lbl, s in sorted(raw.items(), key=lambda kv: (-kv[1], kv[0]))
        ]
        residual = 1.0 - total
        if residual > MIN_RESIDUAL_TO_RECORD:
            shares.append(DefenderShare(ref=DefenderRef.SWITCH_OTHER, share=residual,
                                        evidence="switches and unattributed"))
        return PlayerDefenderExposure(
            game_id=game_id, offensive_player_id=offensive_player_id,
            observed_at_utc=observed_at_utc, shares=tuple(shares),
            # Capped low on purpose: positional compatibility is weak evidence about assignments.
            confidence=0.25,
            source=evidence.source,
            provenance={"basis": "positional_only",
                        "warning": "positional compatibility cannot identify a defender"},
        )

    return unknown_exposure(
        game_id, offensive_player_id, observed_at_utc, evidence.source,
        "no assignment evidence met the threshold "
        f"(named requires >= {MIN_POSSESSIONS_FOR_NAMED_DEFENDERS} possessions)",
    )
