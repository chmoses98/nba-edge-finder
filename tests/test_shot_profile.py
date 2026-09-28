"""Shot-profile ingestion, coordinate validation, zone classification and leakage-free features.

The constants under test came from measurement (``docs/research/ESPN_SHOT_COORDINATES.md``), so
these tests are as much a record of what ESPN does as a check on what this code does.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from nba_edge.shotprofile.court import (
    HOOP_X,
    HOOP_Y,
    ShotZone,
    classify,
    distance_ft,
    in_bounds,
    is_corner,
)
from nba_edge.shotprofile.events import (
    DEFENDER_ATTRIBUTION_AVAILABLE,
    SENTINEL_ABS,
    ShotEvent,
    clock_to_seconds,
    coordinate_is_usable,
    parse_play,
    parse_summary,
)
from nba_edge.shotprofile.features import (
    LeaguePrior,
    ShotProfileMatchupContext,
    build_profile,
    league_prior_before,
    opponent_allowed_profile,
    player_profile,
    zone_index,
)

T0 = datetime(2026, 1, 10, 0, 0, tzinfo=UTC)
# The measured sentinel, verbatim from the probe runs.
SENTINEL = {"x": -214748340, "y": -214748365}


def play(**kw):
    base = {
        "id": "401", "sequenceNumber": "5", "shootingPlay": True, "scoringPlay": False,
        "text": "Player misses 3-foot layup", "type": {"text": "Layup Shot"},
        "coordinate": {"x": 25, "y": 2}, "period": {"number": 1},
        "clock": {"displayValue": "9:47"}, "team": {"id": "1"}, "scoreValue": 2,
        "participants": [{"type": "scorer", "athlete": {"id": "3202", "displayName": "A Player"}}],
    }
    base.update(kw)
    return base


def ev(**kw) -> ShotEvent:
    base = dict(game_id="g1", event_id="e1", event_time_utc=T0, is_shooting_play=True,
                x=25.0, y=2.0, coordinate_valid=True, points_value=2, shot_made=True,
                shooter_player_id=-1, team_id=1, opponent_team_id=2)
    base.update(kw)
    return ShotEvent(**base)


# == 1. SENTINELS AND COORDINATE VALIDATION ====================================================


def test_the_measured_sentinel_is_not_a_location():
    """-214748365 is ESPN's int32 'not recorded' marker, seen 3,235 times in one probe run."""
    assert coordinate_is_usable(SENTINEL["x"], SENTINEL["y"]) is False
    assert coordinate_is_usable(25, 2) is True


def test_non_finite_and_out_of_scale_values_are_rejected():
    for x, y in [(float("nan"), 2), (float("inf"), 2), (25, float("-inf")),
                 (SENTINEL_ABS, 2), (25, -SENTINEL_ABS), (None, 2), ("25", 2), (True, 2)]:
        assert coordinate_is_usable(x, y) is False, f"{x},{y} must not count as a location"


def test_a_valid_flag_cannot_outrun_the_coordinate():
    """The single most damaging thing this schema could allow: a fabricated-looking position."""
    with pytest.raises(ValidationError, match="coordinate_valid=True but"):
        ev(x=float(SENTINEL["x"]), y=float(SENTINEL["y"]), coordinate_valid=True)
    with pytest.raises(ValidationError, match="coordinate_valid=True but"):
        ev(x=None, y=None, coordinate_valid=True)


def test_court_plausibility_bounds_reject_corruption():
    assert in_bounds(25, 2) and in_bounds(0, -4) and in_bounds(50, 60)
    assert not in_bounds(500, 2)
    assert not in_bounds(25, 900)
    assert not in_bounds(None, 2)
    assert not in_bounds(float("nan"), 2)


# == 2. FREE THROWS AND NON-SHOT EVENTS ========================================================


def test_a_free_throw_can_never_carry_a_field_goal_location():
    """Measured: 1,094 free throws, 0 with a coordinate. Admitting one skews foul-drawers' profiles."""
    with pytest.raises(ValidationError, match="free throw must not carry"):
        ev(is_free_throw=True, x=25.0, y=2.0, coordinate_valid=True)


def test_a_free_throw_parses_with_no_coordinate_even_if_one_is_present():
    e = parse_play(play(text="Player makes free throw 1 of 2", type={"text": "Free Throw - 1 of 2"},
                        coordinate={"x": 25, "y": 15}, shootingPlay=False, scoreValue=1),
                   game_id="g1", home_team_id=1, away_team_id=2)
    assert e is not None and e.is_free_throw
    assert e.coordinate_valid is False and e.x is None
    assert e.is_field_goal_attempt is False


def test_non_shot_events_that_carry_coordinates_are_not_attempts():
    """Rebounds outnumber shots in the coordinate-bearing stream; counting them inflates rim rates."""
    for t in ("Defensive Rebound", "Offensive Rebound", "Shooting Foul", "Bad Pass Turnover",
              "Substitution", "Full Timeout"):
        p = play(shootingPlay=False, scoringPlay=False, type={"text": t}, text=t,
                 coordinate={"x": 25, "y": 1}, scoreValue=0)
        assert parse_play(p, game_id="g1", home_team_id=1, away_team_id=2) is None, t


def test_a_shot_with_the_sentinel_is_kept_but_not_located():
    e = parse_play(play(coordinate=SENTINEL), game_id="g1", home_team_id=1, away_team_id=2)
    assert e is not None and e.is_shooting_play
    assert e.coordinate_valid is False and e.x is None and e.y is None
    assert e.usable_for_zone is False


# == 3. COURT GEOMETRY, AS MEASURED ============================================================


def test_the_hoop_origin_is_the_measured_one_not_the_intuitive_one():
    """y is measured from the BASKET. The baseline reading (y=5.25) scored 53.6% on the arc test."""
    assert (HOOP_X, HOOP_Y) == (25.0, 0.0)


def test_distance_and_corner_detection():
    assert distance_ft(25.0, 0.0) == 0.0
    assert distance_ft(25.0, 10.0) == pytest.approx(10.0)
    assert is_corner(2.0) and is_corner(48.0)
    assert not is_corner(25.0) and not is_corner(10.0)


def test_zone_classification_is_deterministic_and_covers_the_court():
    cases = [
        ((25.0, 1.0), 2, ShotZone.RIM),
        ((25.0, 8.0), 2, ShotZone.PAINT_NON_RIM),
        ((25.0, 18.0), 2, ShotZone.MIDRANGE),
        ((2.0, 1.0), 3, ShotZone.CORNER_THREE),
        ((25.0, 26.0), 3, ShotZone.ABOVE_BREAK_THREE),
    ]
    for (x, y), pv, want in cases:
        got = classify(x, y, points_value=pv)
        assert got is want, f"({x},{y}) value={pv} -> {got}, expected {want}"
        assert classify(x, y, points_value=pv) is got, "classification must be deterministic"


def test_a_recorded_three_is_never_reclassified_as_a_two_by_geometry():
    """Coordinates are integer-valued, so an attempt near the arc is ambiguous on distance alone.

    The scoreboard is not ambiguous. Letting geometry overrule it would move real attempts across
    the most consequential boundary in the whole profile.
    """
    # 21 ft out: inside the arc geometrically, but ESPN recorded it as a 3.
    assert classify(25.0, 21.0, points_value=3) is ShotZone.ABOVE_BREAK_THREE
    assert classify(25.0, 21.0, points_value=2) is ShotZone.MIDRANGE


def test_an_unlocatable_shot_is_UNKNOWN_rather_than_guessed():
    assert classify(None, None) is ShotZone.UNKNOWN
    assert classify(9999.0, 2.0, points_value=2) is ShotZone.UNKNOWN


# == 4. PARSING ================================================================================


def test_made_and_missed_are_read_from_the_flag_then_the_wording():
    made = parse_play(play(scoringPlay=True, text="Player makes 26-foot three point jumper"),
                      game_id="g", home_team_id=1, away_team_id=2)
    miss = parse_play(play(scoringPlay=False, text="Player misses 26-foot three point jumper"),
                      game_id="g", home_team_id=1, away_team_id=2)
    assert made.shot_made is True and miss.shot_made is False


def test_teams_and_sides_resolve_from_the_header():
    e = parse_play(play(team={"id": "2"}), game_id="g", home_team_id=1, away_team_id=2)
    assert e.team_id == 2 and e.opponent_team_id == 1 and e.is_home is False


def test_the_shooter_carries_the_projects_provisional_id_convention():
    e = parse_play(play(), game_id="g", home_team_id=1, away_team_id=2)
    assert e.shooter_player_id == -3202, "ESPN-sourced players are negative, as elsewhere"


def test_clock_parsing_returns_none_rather_than_guessing():
    assert clock_to_seconds("9:47") == pytest.approx(587.0)
    assert clock_to_seconds("12") == pytest.approx(12.0)
    assert clock_to_seconds("nonsense") is None
    assert clock_to_seconds(None) is None


def test_a_summary_without_plays_yields_no_events_rather_than_raising():
    assert parse_summary({}, game_id="g") == []
    assert parse_summary({"plays": None}, game_id="g") == []


def test_parse_summary_filters_to_attempts():
    payload = {
        "header": {"competitions": [{"competitors": [
            {"id": "1", "homeAway": "home"}, {"id": "2", "homeAway": "away"}]}]},
        "plays": [play(), play(id="402", shootingPlay=False, type={"text": "Defensive Rebound"},
                               text="Defensive Rebound"), play(id="403")],
    }
    out = parse_summary(payload, game_id="g1")
    assert [e.event_id for e in out] == ["401", "403"]
    assert all(e.is_shooting_play for e in out)


# == 5. THE DISTINCTION THIS ARM MUST NOT LOSE =================================================


def test_no_reachable_source_attributes_a_defender_and_the_code_says_so():
    """Shot-profile data available != defender matchup data available.

    A constant a test can assert against, rather than a sentence in a docstring somebody skims.
    """
    assert DEFENDER_ATTRIBUTION_AVAILABLE is False


def test_a_shot_event_carries_no_defender_field_at_all():
    assert not any("defender" in f for f in ShotEvent.model_fields), (
        "a defender field would invite something to populate it from shot locations")


# == 6. POINT-IN-TIME FEATURES =================================================================


def _stream(n_rim: int, n_three: int, *, player: int = -1, team: int = 1, opp: int = 2,
            start: datetime = T0) -> list[ShotEvent]:
    out = []
    for i in range(n_rim):
        out.append(ev(event_id=f"r{i}", x=25.0, y=1.0, points_value=2, shot_made=i % 2 == 0,
                      shooter_player_id=player, team_id=team, opponent_team_id=opp,
                      event_time_utc=start + timedelta(hours=i)))
    for i in range(n_three):
        out.append(ev(event_id=f"t{i}", x=25.0, y=26.0, points_value=3, shot_made=i % 3 == 0,
                      shooter_player_id=player, team_id=team, opponent_team_id=opp,
                      event_time_utc=start + timedelta(hours=i)))
    return out


def test_a_profile_cannot_see_its_own_game():
    """The purest leak available here: predicting a rim rate partly from the attempts predicted."""
    events = _stream(40, 10)
    cutoff = T0 + timedelta(hours=20)
    zi = zone_index(events)
    prof = build_profile(events, zi, before=cutoff, prior=LeaguePrior.from_events(events, zi))
    knowable = [e for e in events if e.event_time_utc < cutoff]
    assert prof.n_attempts == len(knowable)
    assert prof.n_attempts < len(events), "the cutoff must actually exclude something"


def test_an_event_exactly_at_the_cutoff_is_not_yet_knowable():
    events = _stream(3, 0)
    zi = zone_index(events)
    at = events[1].event_time_utc
    prof = build_profile(events, zi, before=at, prior=LeaguePrior.from_events(events, zi))
    assert prof.n_attempts == 1, "strictly before, not before-or-at"


def test_a_thin_sample_is_shrunk_toward_the_league_rather_than_believed():
    """Nine attempts do not make a 100% rim shooter."""
    league = LeaguePrior(zone_rate={"rim": 0.30, "paint_non_rim": 0.15, "midrange": 0.15,
                                    "corner_three": 0.15, "above_break_three": 0.25},
                         zone_efficiency={z: 0.45 for z in
                                          ("rim", "paint_non_rim", "midrange", "corner_three",
                                           "above_break_three")}, n_attempts=100000)
    thin = _stream(9, 0)
    zi = zone_index(thin)
    prof = build_profile(thin, zi, before=T0 + timedelta(days=5), prior=league)
    assert prof.zone_rate["rim"] < 0.45, f"9 rim attempts should not read as {prof.zone_rate['rim']:.2f}"
    assert prof.zone_rate["rim"] > league.zone_rate["rim"], "but it should move off the prior"


def test_a_large_sample_overcomes_the_prior():
    league = LeaguePrior(zone_rate={z: 0.2 for z in
                                    ("rim", "paint_non_rim", "midrange", "corner_three",
                                     "above_break_three")},
                         zone_efficiency={z: 0.45 for z in
                                          ("rim", "paint_non_rim", "midrange", "corner_three",
                                           "above_break_three")}, n_attempts=100000)
    # The cutoff sits just after the attempts on purpose. An earlier version put it 200 days out
    # and the profile stayed near the prior -- which was the recency weighting working, not the
    # shrinkage failing: 2,000 attempts all older than two half-lives carry an effective n far
    # below their raw count. Volume alone does not overcome the prior; RECENT volume does.
    heavy = _stream(2000, 0)
    zi = zone_index(heavy)
    cutoff = max(e.event_time_utc for e in heavy) + timedelta(hours=1)
    prof = build_profile(heavy, zi, before=cutoff, prior=league)
    assert prof.effective_n > 500, f"recent attempts should keep their weight (got {prof.effective_n:.0f})"
    assert prof.zone_rate["rim"] > 0.9, prof.zone_rate["rim"]


def test_zone_rates_form_a_distribution():
    events = _stream(30, 20)
    zi = zone_index(events)
    prof = build_profile(events, zi, before=T0 + timedelta(days=10),
                         prior=LeaguePrior.from_events(events, zi))
    assert sum(prof.zone_rate.values()) == pytest.approx(1.0, abs=1e-9)
    assert prof.three_rate == pytest.approx(
        prof.zone_rate["corner_three"] + prof.zone_rate["above_break_three"])


def test_recency_weighting_favours_recent_evidence():
    old = _stream(50, 0, start=T0)
    recent = [ShotEvent(**{**e.model_dump(), "event_id": f"n{i}"})
              for i, e in enumerate(_stream(50, 0, start=T0 + timedelta(days=200)))]
    events = old + recent
    zi = zone_index(events)
    cutoff = T0 + timedelta(days=400)
    prof = build_profile(events, zi, before=cutoff, prior=LeaguePrior.from_events(events, zi),
                         half_life_days=30.0)
    assert prof.effective_n < prof.n_attempts, "old evidence must weigh less than its raw count"


def test_no_evidence_produces_the_prior_and_an_empty_flag():
    league = LeaguePrior(zone_rate={"rim": 0.3, "paint_non_rim": 0.2, "midrange": 0.2,
                                    "corner_three": 0.1, "above_break_three": 0.2},
                         zone_efficiency={z: 0.5 for z in
                                          ("rim", "paint_non_rim", "midrange", "corner_three",
                                           "above_break_three")}, n_attempts=1000)
    prof = build_profile([], {}, before=T0, prior=league)
    assert prof.is_empty and prof.n_attempts == 0
    assert prof.zone_rate["rim"] == pytest.approx(0.3), "with no data, report the prior"


def test_player_and_opponent_profiles_select_different_sides():
    mine = _stream(20, 0, player=-1, team=1, opp=2)
    theirs = _stream(0, 20, player=-9, team=2, opp=1)
    events = mine + [ShotEvent(**{**e.model_dump(), "event_id": f"o{i}"}) for i, e in enumerate(theirs)]
    zi = zone_index(events)
    before = T0 + timedelta(days=30)
    prior = LeaguePrior.from_events(events, zi)

    p = player_profile(events, zi, -1, before=before, prior=prior)
    assert p.n_attempts == 20

    # Team 1 ALLOWED the attempts team 2 took against it.
    allowed = opponent_allowed_profile(events, zi, 1, before=before, prior=prior)
    assert allowed.n_attempts == 20
    assert allowed.zone_rate["above_break_three"] > allowed.zone_rate["rim"]


def test_the_league_prior_is_itself_leakage_free():
    events = _stream(30, 30)
    zi = zone_index(events)
    cut = T0 + timedelta(hours=10)
    prior = league_prior_before(events, zi, before=cut)
    assert prior.n_attempts == len([e for e in events if e.event_time_utc < cut])


# == 7. THE MATCHUP CONTEXT DESCRIBES, IT DOES NOT PREDICT =====================================


def _context() -> ShotProfileMatchupContext:
    mine = _stream(40, 10, player=-1, team=1, opp=2)
    zi = zone_index(mine)
    before = T0 + timedelta(days=30)
    prior = LeaguePrior.from_events(mine, zi)
    return ShotProfileMatchupContext(
        player_id=-1, game_id="g1", observed_at_utc=before, opponent_team_id=2,
        player=player_profile(mine, zi, -1, before=before, prior=prior),
        opponent_allowed=opponent_allowed_profile(mine, zi, 2, before=before, prior=prior),
        provenance={"source": "espn/summary", "geometry": "ESPN_SHOT_COORDINATES.md"},
    )


def test_the_context_declares_that_no_effect_has_been_learned():
    c = _context()
    assert c.effect_status == "NEUTRAL/UNLEARNED"
    assert c.as_dict()["effect_status"] == "NEUTRAL/UNLEARNED"


def test_deltas_are_differences_not_effects():
    c = _context()
    d = c.deltas
    assert set(d) == {"rim", "paint_non_rim", "midrange", "corner_three", "above_break_three"}
    for z, v in d.items():
        assert v == pytest.approx(
            c.player.zone_rate[z] - c.opponent_allowed.zone_rate[z], abs=1e-6), z


def test_confidence_is_driven_by_the_weaker_side_and_never_reaches_one():
    c = _context()
    assert 0.0 <= c.confidence < 1.0
    assert c.freshness_days() is not None


def test_the_context_carries_sample_sizes_and_provenance():
    d = _context().as_dict()
    assert d["sample_size"]["player_attempts"] > 0
    assert d["provenance"]["source"] == "espn/summary"
    assert "player_shot_profile" in d and "opponent_shot_profile_allowed" in d
    assert "matchup_profile_deltas" in d


def test_no_module_here_converts_a_profile_into_a_model_effect():
    """Phase 9: build the data, not the effect. Absence is the design, so absence is tested."""
    import nba_edge.shotprofile.features as F

    banned = [n for n in dir(F)
              if any(k in n.lower() for k in ("multiplier", "adjust", "boost", "edge", "effect_size"))]
    assert banned == [], f"shot-profile features must not expose effect machinery: {banned}"
