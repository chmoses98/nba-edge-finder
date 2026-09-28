"""Point-in-time shot-profile features, for a player and for what an opponent allows.

Two rules hold everywhere in this module.

**Nothing may see its own game.** Every estimator takes a ``before`` instant and uses only events
observed strictly earlier. A same-game shot in a player's own profile is the purest form of leakage
available here: it would predict a player's rim rate partly from the rim attempts being predicted.

**Small samples shrink toward a prior, they do not shout.** A player with nine attempts does not
have a 44% rim rate; he has a number indistinguishable from the league's. Shrinkage is explicit and
the effective sample size travels with the estimate, so a consumer can see how much is data.

There is deliberately **no function here that turns a profile difference into a points, FGA or FG%
adjustment**. That absence is the design, not an omission: build the data and the research
pipeline, and let out-of-sample evidence decide whether any of it earns influence. The V2
adjustment layer stays neutral until then.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime

from nba_edge.shotprofile.court import THREE_ZONES, ShotZone
from nba_edge.shotprofile.events import ShotEvent

FEATURES_VERSION = "shotprofile-features/1"

# Shrinkage strength, in "pseudo-attempts of league-average evidence". A player needs roughly this
# many attempts before his own rates carry more weight than the prior. Set from the shape of the
# problem rather than tuned: zone rates over ~100 attempts have a standard error around 5%, which is
# the scale at which differences between players start to be real.
RATE_PRIOR_STRENGTH = 100.0
# Efficiency is noisier per attempt than rate is, so it shrinks harder.
EFF_PRIOR_STRENGTH = 150.0

# Half-life in days for exponential recency weighting. A shot profile is a stable trait that drifts
# with role, so this is deliberately long: short half-lives turn a cold week into a "changed
# player".
DEFAULT_HALF_LIFE_DAYS = 45.0

ZONES: tuple[ShotZone, ...] = (
    ShotZone.RIM,
    ShotZone.PAINT_NON_RIM,
    ShotZone.MIDRANGE,
    ShotZone.CORNER_THREE,
    ShotZone.ABOVE_BREAK_THREE,
)


def _decay(event_at: datetime, before: datetime, half_life_days: float) -> float:
    """Exponential recency weight. Events at the cutoff weigh 1.0; older ones decay."""
    if half_life_days <= 0:
        return 1.0
    age_days = max(0.0, (before - event_at).total_seconds() / 86400.0)
    return 0.5 ** (age_days / half_life_days)


@dataclass(frozen=True)
class ShotProfile:
    """Zone rates and efficiencies with the sample they rest on.

    ``zone_rate`` sums to 1.0 across zones by construction (they partition attempts). ``n_attempts``
    is the raw count and ``effective_n`` the recency-weighted one -- both are reported because a
    profile built from 200 attempts a season ago is not the same evidence as 200 last week.
    """

    zone_rate: dict[str, float]
    zone_efficiency: dict[str, float]
    zone_attempts: dict[str, float]
    n_attempts: int
    effective_n: float
    three_rate: float
    rim_rate: float
    observed_before_utc: datetime | None = None
    shrunk: bool = True
    features_version: str = FEATURES_VERSION

    @property
    def is_empty(self) -> bool:
        return self.n_attempts == 0

    def as_dict(self) -> dict[str, float | int | str | None]:
        out: dict[str, float | int | str | None] = {
            f"rate_{z}": round(self.zone_rate.get(z, 0.0), 6) for z in self.zone_rate
        }
        out.update({f"eff_{z}": round(v, 6) for z, v in self.zone_efficiency.items()})
        out["n_attempts"] = self.n_attempts
        out["effective_n"] = round(self.effective_n, 3)
        out["three_rate"] = round(self.three_rate, 6)
        out["rim_rate"] = round(self.rim_rate, 6)
        out["features_version"] = self.features_version
        return out


@dataclass
class LeaguePrior:
    """League-average zone rates and efficiencies, used as the shrinkage target.

    Computed from the same event stream rather than hardcoded, so it moves with the era. A league
    that shoots more threes every season should not be measured against a constant from 2019.
    """

    zone_rate: dict[str, float] = field(default_factory=dict)
    zone_efficiency: dict[str, float] = field(default_factory=dict)
    n_attempts: int = 0

    @classmethod
    def from_events(cls, events: Iterable[ShotEvent], zone_of: dict[str, ShotZone] | None = None) -> LeaguePrior:
        counts: dict[str, float] = defaultdict(float)
        makes: dict[str, float] = defaultdict(float)
        total = 0
        for ev in events:
            z = _zone_for(ev, zone_of)
            if z is None:
                continue
            counts[z.value] += 1.0
            if ev.shot_made:
                makes[z.value] += 1.0
            total += 1
        if total == 0:
            # A uniform prior is the honest default: with no evidence, no zone is favoured.
            return cls(zone_rate={z.value: 1.0 / len(ZONES) for z in ZONES},
                       zone_efficiency={z.value: 0.0 for z in ZONES}, n_attempts=0)
        return cls(
            zone_rate={z.value: counts[z.value] / total for z in ZONES},
            zone_efficiency={z.value: (makes[z.value] / counts[z.value]) if counts[z.value] else 0.0
                             for z in ZONES},
            n_attempts=total,
        )


def _zone_for(ev: ShotEvent, zone_of: dict[str, ShotZone] | None) -> ShotZone | None:
    """The zone of an attempt, or None if it is not a locatable field-goal attempt."""
    if zone_of is not None:
        z = zone_of.get(ev.event_id)
        return z if z is not None and z is not ShotZone.UNKNOWN else None
    return None


def build_profile(
    events: Sequence[ShotEvent],
    zone_of: dict[str, ShotZone],
    *,
    before: datetime,
    prior: LeaguePrior,
    half_life_days: float = DEFAULT_HALF_LIFE_DAYS,
    rate_prior_strength: float = RATE_PRIOR_STRENGTH,
    eff_prior_strength: float = EFF_PRIOR_STRENGTH,
) -> ShotProfile:
    """A shrunk, recency-weighted shot profile from events strictly before ``before``.

    The cutoff is applied here rather than left to the caller on purpose: a leakage rule that lives
    in the caller is a leakage rule that one caller will forget.
    """
    w_zone: dict[str, float] = defaultdict(float)
    w_make: dict[str, float] = defaultdict(float)
    n_raw = 0
    eff_n = 0.0

    for ev in events:
        if ev.event_time_utc is None or ev.event_time_utc >= before:
            continue  # strictly before: an event AT the cutoff is not yet knowable
        z = _zone_for(ev, zone_of)
        if z is None:
            continue
        w = _decay(ev.event_time_utc, before, half_life_days)
        w_zone[z.value] += w
        if ev.shot_made:
            w_make[z.value] += w
        n_raw += 1
        eff_n += w

    total_w = sum(w_zone.values())
    rates: dict[str, float] = {}
    effs: dict[str, float] = {}
    for z in ZONES:
        k = z.value
        p_rate = prior.zone_rate.get(k, 1.0 / len(ZONES))
        rates[k] = (w_zone[k] + rate_prior_strength * p_rate) / (total_w + rate_prior_strength)
        p_eff = prior.zone_efficiency.get(k, 0.0)
        denom = w_zone[k] + eff_prior_strength
        effs[k] = (w_make[k] + eff_prior_strength * p_eff) / denom if denom > 0 else p_eff

    return ShotProfile(
        zone_rate=rates,
        zone_efficiency=effs,
        zone_attempts={z.value: round(w_zone[z.value], 4) for z in ZONES},
        n_attempts=n_raw,
        effective_n=eff_n,
        three_rate=sum(rates[z.value] for z in THREE_ZONES),
        rim_rate=rates[ShotZone.RIM.value],
        observed_before_utc=before,
    )


def player_profile(
    events: Sequence[ShotEvent], zone_of: dict[str, ShotZone], player_id: int, *,
    before: datetime, prior: LeaguePrior, half_life_days: float = DEFAULT_HALF_LIFE_DAYS,
) -> ShotProfile:
    """What this player shoots, from his own attempts before the cutoff."""
    own = [e for e in events if e.shooter_player_id == player_id]
    return build_profile(own, zone_of, before=before, prior=prior, half_life_days=half_life_days)


def opponent_allowed_profile(
    events: Sequence[ShotEvent], zone_of: dict[str, ShotZone], team_id: int, *,
    before: datetime, prior: LeaguePrior, half_life_days: float = DEFAULT_HALF_LIFE_DAYS,
) -> ShotProfile:
    """What this team ALLOWS: the profile of attempts taken against it.

    Named "allowed" throughout, never "defensive matchup". This is what opponents did, which mixes
    the team's scheme with the schedule it faced and with those opponents' own tendencies. It is a
    team/scheme proxy and it is **raw**, not opponent-adjusted -- see the module docs and
    ``docs/research/ESPN_SHOT_COORDINATES.md``.
    """
    faced = [e for e in events if e.opponent_team_id == team_id]
    return build_profile(faced, zone_of, before=before, prior=prior, half_life_days=half_life_days)


@dataclass(frozen=True)
class ShotProfileMatchupContext:
    """A player's offensive shot profile beside what his opponent allows.

    **This object has no authority to change a prediction.** It is a description with two sides
    placed next to each other, which is the beginning of a research question, not the answer to one.
    ``effect_status`` says so in a field rather than in a comment.
    """

    player_id: int
    game_id: str
    observed_at_utc: datetime
    opponent_team_id: int | None
    player: ShotProfile
    opponent_allowed: ShotProfile
    league: LeaguePrior | None = None
    effect_status: str = "NEUTRAL/UNLEARNED"
    provenance: dict[str, str] = field(default_factory=dict)

    @property
    def deltas(self) -> dict[str, float]:
        """Player rate minus opponent-allowed rate, per zone.

        A difference, not an effect. It says these two descriptions differ; it does not say the
        game will move, and nothing in this codebase is permitted to read it as though it does.
        """
        return {
            z.value: round(self.player.zone_rate.get(z.value, 0.0)
                           - self.opponent_allowed.zone_rate.get(z.value, 0.0), 6)
            for z in ZONES
        }

    @property
    def confidence(self) -> float:
        """How much evidence stands behind the thinner of the two sides, in [0, 1).

        Deliberately bounded below 1 and driven by the weaker side: a profile is only as trustworthy
        as its scarcer half, and no amount of data makes a descriptive comparison certain.
        """
        n = min(self.player.effective_n, self.opponent_allowed.effective_n)
        return round(n / (n + 200.0), 4)

    def freshness_days(self, now: datetime | None = None) -> float | None:
        ref = now or self.observed_at_utc
        if self.player.observed_before_utc is None:
            return None
        return round(abs((ref - self.player.observed_before_utc).total_seconds()) / 86400.0, 3)

    def as_dict(self) -> dict[str, object]:
        return {
            "player_id": self.player_id,
            "game_id": self.game_id,
            "observed_at_utc": self.observed_at_utc.isoformat(),
            "opponent_team_id": self.opponent_team_id,
            "player_shot_profile": self.player.as_dict(),
            "opponent_shot_profile_allowed": self.opponent_allowed.as_dict(),
            "matchup_profile_deltas": self.deltas,
            "sample_size": {
                "player_attempts": self.player.n_attempts,
                "player_effective_n": round(self.player.effective_n, 3),
                "opponent_attempts_faced": self.opponent_allowed.n_attempts,
                "opponent_effective_n": round(self.opponent_allowed.effective_n, 3),
            },
            "confidence": self.confidence,
            "effect_status": self.effect_status,
            "provenance": dict(self.provenance),
        }


def zone_index(events: Iterable[ShotEvent]) -> dict[str, ShotZone]:
    """Map event id -> zone for every locatable field-goal attempt.

    Kept as a separate index rather than a field on ``ShotEvent`` so that a normalized event stays
    valid even if the court geometry is later revised: re-deriving zones then costs one pass and
    changes no stored event.
    """
    from nba_edge.shotprofile.court import classify

    out: dict[str, ShotZone] = {}
    for ev in events:
        if not ev.usable_for_zone:
            continue
        z = classify(ev.x, ev.y, points_value=ev.points_value)
        if z is not ShotZone.UNKNOWN:
            out[ev.event_id] = z
    return out


def league_prior_before(
    events: Sequence[ShotEvent], zone_of: dict[str, ShotZone], *, before: datetime
) -> LeaguePrior:
    """The league prior as it stood at ``before`` -- itself leakage-free."""
    return LeaguePrior.from_events(
        [e for e in events if e.event_time_utc is not None and e.event_time_utc < before], zone_of
    )
