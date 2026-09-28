"""Canonical point-in-time schemas for matchup research.

Three rules shape every model here, and they are the reason the file looks more cautious than a
basketball-intuition version of it would:

1. **Unknown is a first-class answer.** A defender distribution that cannot be estimated returns a
   single UNKNOWN share of 1.0 rather than a confident guess. Every archetype and scheme feature is
   optional, and an absent value is recorded as unavailable rather than filled with a league mean.
2. **A matchup is a distribution, never a label.** Nothing here can express "player X is guarded by
   player Y". It can only express shares over defenders, positions, archetypes, switches and
   unknown, which is what actually happens on a possession.
3. **Neutral by default.** ``MatchupAdjustment`` defaults to the identity transform. There are no
   hand-written effects anywhere in this package; a non-neutral adjustment can only come from a
   fitted, versioned estimate.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import Field, field_validator, model_validator

from nba_edge.schemas.core import Strict

# Shares may miss 1.0 by this much before a distribution is rejected. Tight enough to catch a real
# construction bug, loose enough for float noise and for shares rounded at a data source.
SHARE_TOLERANCE = 1e-6


class Availability(StrEnum):
    """Why a value is what it is. `UNAVAILABLE` means no data -- never a filled-in default."""

    OBSERVED = "observed"      # measured directly from source data
    ESTIMATED = "estimated"    # derived/modelled from other observed data, with a sample behind it
    UNAVAILABLE = "unavailable"  # no trustworthy data; value MUST be None


class DefenderRef(StrEnum):
    """What a share is attributed to.

    Identified players are the ideal, but evidence is often only good enough to say "a wing" or
    "whoever switched". Those are legitimate answers and get their own kinds rather than being
    forced into a player id.
    """

    PLAYER = "player"
    POSITION = "position"
    ARCHETYPE = "archetype"
    SWITCH_OTHER = "switch_other"
    UNKNOWN = "unknown"


class LineupConfidence(StrEnum):
    """How firm the expected lineup is. Drives whether a matchup estimate is usable at all."""

    CONFIRMED = "confirmed"    # official confirmation (e.g. starters announced)
    REPORTED = "reported"      # beat reporting / probable
    PROJECTED = "projected"    # our own projection from rotation history
    UNKNOWN = "unknown"


class Measure(Strict):
    """A single numeric feature with its provenance and availability.

    Used instead of a bare float so that "we measured 0.42" and "we have no idea" are never the same
    value. ``value`` must be None exactly when availability is UNAVAILABLE.
    """

    value: float | None = None
    availability: Availability = Availability.UNAVAILABLE
    source: str | None = None
    observed_at_utc: datetime | None = None
    sample_size: int | None = None
    note: str | None = None

    @model_validator(mode="after")
    def _value_matches_availability(self) -> Measure:
        if self.availability is Availability.UNAVAILABLE and self.value is not None:
            raise ValueError("an UNAVAILABLE measure must not carry a value")
        if self.availability is not Availability.UNAVAILABLE and self.value is None:
            raise ValueError(f"availability {self.availability} requires a value")
        return self

    @property
    def known(self) -> bool:
        return self.availability is not Availability.UNAVAILABLE


class DefenderShare(Strict):
    """One slice of an offensive player's defensive exposure."""

    ref: DefenderRef
    share: float = Field(ge=0.0, le=1.0)
    defender_player_id: int | None = None
    label: str | None = None  # position or archetype when ref is not PLAYER
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence: str | None = None

    @model_validator(mode="after")
    def _ref_carries_its_identifier(self) -> DefenderShare:
        if self.ref is DefenderRef.PLAYER and self.defender_player_id is None:
            raise ValueError("a PLAYER share must carry defender_player_id")
        if self.ref is not DefenderRef.PLAYER and self.defender_player_id is not None:
            raise ValueError(f"a {self.ref} share must not carry defender_player_id")
        if self.ref in (DefenderRef.POSITION, DefenderRef.ARCHETYPE) and not self.label:
            raise ValueError(f"a {self.ref} share must carry a label")
        return self


class PlayerDefenderExposure(Strict):
    """Who is expected to guard one offensive player, as a distribution.

    The shares must sum to 1. That is not bookkeeping pedantry: a distribution that sums to 0.8
    silently means "20% of possessions are unmodelled", and downstream code would spread that
    missing mass however it happened to iterate. An explicit SWITCH_OTHER or UNKNOWN share makes the
    unmodelled part visible and attributable.
    """

    game_id: str
    offensive_player_id: int
    observed_at_utc: datetime
    shares: tuple[DefenderShare, ...]
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    source: str
    provenance: dict[str, str] = Field(default_factory=dict)

    @field_validator("shares")
    @classmethod
    def _shares_are_coherent(cls, shares: tuple[DefenderShare, ...]) -> tuple[DefenderShare, ...]:
        if not shares:
            raise ValueError(
                "an exposure must carry at least one share; use a single UNKNOWN share of 1.0 to "
                "say 'we do not know' rather than an empty distribution"
            )
        total = sum(s.share for s in shares)
        if abs(total - 1.0) > SHARE_TOLERANCE:
            raise ValueError(f"defender shares must sum to 1.0, got {total!r}")
        seen: set[tuple] = set()
        for s in shares:
            key = (s.ref, s.defender_player_id, s.label)
            if key in seen:
                raise ValueError(f"duplicate defender share for {key}")
            seen.add(key)
        return shares

    @property
    def is_unknown(self) -> bool:
        """True when essentially all mass sits in the unknown bucket."""
        unknown = sum(s.share for s in self.shares if s.ref is DefenderRef.UNKNOWN)
        return unknown >= 1.0 - SHARE_TOLERANCE

    @property
    def identified_share(self) -> float:
        """Mass attributed to a named player -- the part a player-level effect could ever use."""
        return sum(s.share for s in self.shares if s.ref is DefenderRef.PLAYER)

    def share_for_player(self, defender_player_id: int) -> float:
        return sum(
            s.share for s in self.shares
            if s.ref is DefenderRef.PLAYER and s.defender_player_id == defender_player_id
        )


class DefenderArchetype(Strict):
    """Research attributes of a defender. Every field optional: unknown is normal, not exceptional."""

    player_id: int
    observed_at_utc: datetime | None = None
    source: str | None = None
    position: str | None = None
    height_cm: Measure = Measure()
    wingspan_cm: Measure = Measure()
    weight_kg: Measure = Measure()
    point_of_attack: Measure = Measure()       # 0-1 role indicator, learned not asserted
    wing_stopper: Measure = Measure()
    rim_protector: Measure = Measure()
    switchability: Measure = Measure()
    screen_navigation: Measure = Measure()
    foul_rate: Measure = Measure()
    steal_rate: Measure = Measure()
    block_rate: Measure = Measure()
    opp_rim_suppression: Measure = Measure()
    opp_three_rate_effect: Measure = Measure()
    assignment_frequency: Measure = Measure()  # how often this player draws the top assignment

    @property
    def known_features(self) -> tuple[str, ...]:
        return tuple(
            n for n, v in self.__dict__.items() if isinstance(v, Measure) and v.known
        )


class OffensiveArchetype(Strict):
    """Research attributes of an offensive player. Same rule: optional, evidence-backed only."""

    player_id: int
    observed_at_utc: datetime | None = None
    source: str | None = None
    position: str | None = None
    primary_ballhandler: Measure = Measure()
    pnr_handler: Measure = Measure()
    isolation_scorer: Measure = Measure()
    post_scorer: Measure = Measure()
    rim_attacker: Measure = Measure()
    pullup_shooter: Measure = Measure()
    catch_and_shoot: Measure = Measure()
    movement_shooter: Measure = Measure()
    roll_man: Measure = Measure()
    stretch_big: Measure = Measure()

    @property
    def known_features(self) -> tuple[str, ...]:
        return tuple(
            n for n, v in self.__dict__.items() if isinstance(v, Measure) and v.known
        )


class SchemeFeature(StrEnum):
    """Named team-defensive scheme proxies. Names are fixed; values are always Measures."""

    DROP_COVERAGE = "drop_coverage"
    SWITCH_FREQUENCY = "switch_frequency"
    BLITZ_TRAP_RATE = "blitz_trap_rate"
    ZONE_USAGE = "zone_usage"
    HELP_INTENSITY = "help_intensity"
    RIM_PROTECTION = "rim_protection"
    PAINT_SUPPRESSION = "paint_suppression"
    THREE_RATE_ALLOWED = "three_rate_allowed"
    CORNER_THREE_TENDENCY = "corner_three_tendency"
    ABOVE_BREAK_THREE_TENDENCY = "above_break_three_tendency"
    TRANSITION_DEFENCE = "transition_defence"
    DEFENSIVE_REBOUNDING = "defensive_rebounding"
    OPP_TURNOVER_CREATION = "opp_turnover_creation"


class TeamDefensiveScheme(Strict):
    """Point-in-time scheme context for one team.

    Features absent from the mapping are simply unknown; ``feature`` returns an UNAVAILABLE Measure
    for them rather than a zero, so a caller cannot accidentally treat "no data" as "no tendency".
    """

    team_id: int
    observed_at_utc: datetime
    source: str
    features: dict[SchemeFeature, Measure] = Field(default_factory=dict)
    provenance: dict[str, str] = Field(default_factory=dict)

    def feature(self, name: SchemeFeature) -> Measure:
        return self.features.get(name, Measure())

    @property
    def known_features(self) -> tuple[SchemeFeature, ...]:
        return tuple(sorted((k for k, v in self.features.items() if v.known), key=str))


class GameMatchupContext(Strict):
    """Everything known about a game's matchup structure at one instant.

    ``observed_at_utc`` is the point-in-time cutoff and is load-bearing: a context may only inform a
    prediction made at or after it, and must be strictly before tip to count as pregame. The leakage
    checks live in ``matchup.leakage`` so they are enforced in one place rather than per caller.
    """

    game_id: str
    observed_at_utc: datetime
    home_team_id: int
    away_team_id: int
    tip_utc: datetime | None = None
    expected_home_starters: tuple[int, ...] = ()
    expected_away_starters: tuple[int, ...] = ()
    expected_home_rotation: tuple[int, ...] = ()
    expected_away_rotation: tuple[int, ...] = ()
    lineup_confidence: LineupConfidence = LineupConfidence.UNKNOWN
    lineup_confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    exposures: tuple[PlayerDefenderExposure, ...] = ()
    home_scheme: TeamDefensiveScheme | None = None
    away_scheme: TeamDefensiveScheme | None = None
    source: str = "unknown"
    provenance: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _starters_are_plausible(self) -> GameMatchupContext:
        for side, ids in (("home", self.expected_home_starters), ("away", self.expected_away_starters)):
            if ids and len(ids) != 5:
                raise ValueError(f"{side} starters must be empty (unknown) or exactly 5, got {len(ids)}")
            if len(set(ids)) != len(ids):
                raise ValueError(f"{side} starters contain duplicates")
        for e in self.exposures:
            if e.game_id != self.game_id:
                raise ValueError(f"exposure for game {e.game_id} attached to context for {self.game_id}")
        return self

    def exposure_for(self, offensive_player_id: int) -> PlayerDefenderExposure | None:
        for e in self.exposures:
            if e.offensive_player_id == offensive_player_id:
                return e
        return None


class MatchupAdjustment(Strict):
    """A per-player, per-game component-level adjustment. **Neutral by construction.**

    Multipliers default to 1.0 and deltas to 0.0, so a default-constructed adjustment is exactly the
    identity. That is the whole safety property of this arm: absent or unusable data produces an
    adjustment that provably changes nothing, rather than a plausible-looking guess.

    Component-level on purpose. A single "defender strength" multiplier can only ever say "all
    offence down", whereas real matchups move components in different directions -- a rim-protector
    can cut rim attempts while assists rise. Fields exist for components V1 cannot yet consume
    (see ``transform.APPLICABLE_FIELDS``); those are recorded and reported, never silently dropped.
    """

    game_id: str
    offensive_player_id: int
    adjustment_version: str
    effects_version: str

    fga_multiplier: float = Field(default=1.0, gt=0.0)
    usage_multiplier: float = Field(default=1.0, gt=0.0)
    minutes_multiplier: float = Field(default=1.0, gt=0.0)

    rim_rate_delta: float = 0.0
    midrange_rate_delta: float = 0.0
    three_rate_delta: float = 0.0
    pullup_rate_delta: float = 0.0
    catch_shoot_rate_delta: float = 0.0
    ft_rate_delta: float = 0.0

    turnover_rate_delta: float = 0.0
    assist_rate_delta: float = 0.0
    rebound_weight_delta: float = 0.0

    fg2_eff_delta: float = 0.0
    fg3_eff_delta: float = 0.0

    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    source: str | None = None
    sample_size: int | None = None
    notes: tuple[str, ...] = ()

    @property
    def is_neutral(self) -> bool:
        """True when this adjustment provably changes nothing."""
        return (
            self.fga_multiplier == 1.0
            and self.usage_multiplier == 1.0
            and self.minutes_multiplier == 1.0
            and self.rim_rate_delta == 0.0
            and self.midrange_rate_delta == 0.0
            and self.three_rate_delta == 0.0
            and self.pullup_rate_delta == 0.0
            and self.catch_shoot_rate_delta == 0.0
            and self.ft_rate_delta == 0.0
            and self.turnover_rate_delta == 0.0
            and self.assist_rate_delta == 0.0
            and self.rebound_weight_delta == 0.0
            and self.fg2_eff_delta == 0.0
            and self.fg3_eff_delta == 0.0
        )

    @staticmethod
    def neutral(game_id: str, offensive_player_id: int, *, effects_version: str,
                adjustment_version: str = "neutral", notes: tuple[str, ...] = ()) -> MatchupAdjustment:
        return MatchupAdjustment(
            game_id=game_id, offensive_player_id=offensive_player_id,
            adjustment_version=adjustment_version, effects_version=effects_version, notes=notes,
        )
