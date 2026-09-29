"""Lineup events, event windows, and the distributional metrics the study was missing.

Both were gaps in the V2 arm: section 12 asked for the residual test to run around lineup
confirmation and late scratches and nothing computed those windows, and ``_crps_normal`` sat as
dead code with no standard deviation on an Observation to feed it.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from nba_edge.matchup.events import (
    LATE_WINDOW,
    LineupEventKind,
    diff_contexts,
    events_for_game,
    stratify,
    window_labels,
)
from nba_edge.matchup.schemas import (
    DefenderRef,
    DefenderShare,
    GameMatchupContext,
    LineupConfidence,
    PlayerDefenderExposure,
)

TIP = datetime(2026, 10, 20, 23, 0, tzinfo=UTC)


def ctx(hours_before=6.0, **kw):
    base = dict(game_id="g1", observed_at_utc=TIP - timedelta(hours=hours_before),
                home_team_id=1, away_team_id=2, tip_utc=TIP)
    base.update(kw)
    return GameMatchupContext(**base)


def expo(off, defender, share=1.0):
    return PlayerDefenderExposure(
        game_id="g1", offensive_player_id=off, observed_at_utc=TIP - timedelta(hours=3),
        source="s", shares=(DefenderShare(ref=DefenderRef.PLAYER, defender_player_id=defender,
                                          share=share),))


# == EVENT DETECTION ===========================================================================


def test_a_lineup_confirmation_is_detected():
    before = ctx(6, lineup_confidence=LineupConfidence.PROJECTED)
    after = ctx(1, lineup_confidence=LineupConfidence.CONFIRMED)
    kinds = [e.kind for e in diff_contexts(before, after)]
    assert LineupEventKind.LINEUP_CONFIRMED in kinds


def test_first_reported_starters_are_a_confirmation_not_a_starter_change():
    """Empty -> a named five is the lineup being reported, not a starter being swapped.

    Counting it as a change would label almost every game a starter-change game, which would make
    the stratum meaningless.
    """
    before = ctx(6, expected_home_starters=())
    after = ctx(1, expected_home_starters=(1, 2, 3, 4, 5))
    assert LineupEventKind.STARTER_CHANGE not in [e.kind for e in diff_contexts(before, after)]


def test_a_real_starter_swap_is_detected_with_the_players_involved():
    before = ctx(6, expected_home_starters=(1, 2, 3, 4, 5))
    after = ctx(1, expected_home_starters=(1, 2, 3, 4, 9))
    ev = [e for e in diff_contexts(before, after) if e.kind is LineupEventKind.STARTER_CHANGE]
    assert len(ev) == 1
    assert set(ev[0].player_ids) == {5, 9}


def test_a_dropped_rotation_player_is_a_late_scratch_and_an_added_one_is_not():
    before = ctx(6, expected_home_rotation=(1, 2, 3))
    after = ctx(1, expected_home_rotation=(1, 2, 4))
    kinds = {e.kind: e for e in diff_contexts(before, after)}
    assert set(kinds[LineupEventKind.LATE_SCRATCH].player_ids) == {3}
    assert set(kinds[LineupEventKind.ROTATION_ADDITION].player_ids) == {4}


def test_a_changed_primary_defender_is_an_assignment_shift():
    before = ctx(6, exposures=(expo(7, 20),))
    after = ctx(1, exposures=(expo(7, 21),))
    ev = [e for e in diff_contexts(before, after) if e.kind is LineupEventKind.ASSIGNMENT_SHIFT]
    assert len(ev) == 1 and ev[0].player_ids == (7,)


def test_an_event_is_dated_when_it_became_knowable_not_when_it_happened():
    """The later capture's time is the first instant a forecaster could have acted on it."""
    before = ctx(6, lineup_confidence=LineupConfidence.PROJECTED)
    after = ctx(1, lineup_confidence=LineupConfidence.CONFIRMED)
    e = diff_contexts(before, after)[0]
    assert e.observed_at_utc == after.observed_at_utc
    assert e.minutes_before_tip == pytest.approx(60.0)


def test_lateness_needs_a_known_tip():
    late = ctx(1, lineup_confidence=LineupConfidence.CONFIRMED)
    early = ctx(9, lineup_confidence=LineupConfidence.CONFIRMED)
    base = ctx(12, lineup_confidence=LineupConfidence.PROJECTED)
    assert diff_contexts(base, late)[0].is_late is True
    assert diff_contexts(base, early)[0].is_late is False, f"9h > {LATE_WINDOW}"

    no_tip_b = ctx(12, tip_utc=None, lineup_confidence=LineupConfidence.PROJECTED)
    no_tip_a = ctx(1, tip_utc=None, lineup_confidence=LineupConfidence.CONFIRMED)
    assert diff_contexts(no_tip_b, no_tip_a)[0].is_late is False, "unknown tip is never 'late'"


def test_diffing_two_different_games_is_refused():
    with pytest.raises(ValueError, match="different games"):
        diff_contexts(ctx(6), ctx(1, game_id="other"))


def test_captures_must_be_ordered():
    with pytest.raises(ValueError, match="older than"):
        diff_contexts(ctx(1), ctx(6))


def test_events_for_game_walks_the_whole_capture_history():
    hist = [
        ctx(12, lineup_confidence=LineupConfidence.PROJECTED, expected_home_rotation=(1, 2, 3)),
        ctx(6, lineup_confidence=LineupConfidence.PROJECTED, expected_home_rotation=(1, 2, 3)),
        ctx(1, lineup_confidence=LineupConfidence.CONFIRMED, expected_home_rotation=(1, 2)),
    ]
    kinds = {e.kind for e in events_for_game(hist)}
    assert LineupEventKind.LINEUP_CONFIRMED in kinds
    assert LineupEventKind.LATE_SCRATCH in kinds


# == WINDOWS ARE STRICTLY CAUSAL ===============================================================


def test_an_event_cannot_label_a_forecast_that_preceded_it():
    """The whole point. A scratch reported at T-1h says nothing about a forecast made at T-6h."""
    ev = events_for_game([ctx(12, lineup_confidence=LineupConfidence.PROJECTED),
                          ctx(1, lineup_confidence=LineupConfidence.CONFIRMED)])
    early = window_labels(ev, decision_at=TIP - timedelta(hours=6), game_id="g1")
    later = window_labels(ev, decision_at=TIP - timedelta(minutes=30), game_id="g1")
    assert early["any_event"] is False and early["n_events_knowable"] == 0
    assert later["any_event"] is True and "lineup_confirmed" in later["kinds"]


def test_events_from_another_game_never_label_this_one():
    ev = events_for_game([ctx(12, lineup_confidence=LineupConfidence.PROJECTED),
                          ctx(1, lineup_confidence=LineupConfidence.CONFIRMED)])
    assert window_labels(ev, decision_at=TIP, game_id="different")["any_event"] is False


def test_stratify_splits_observations_and_keeps_a_control_group():
    from nba_edge.research.matchup_walkforward import Observation

    ev = events_for_game([ctx(12, lineup_confidence=LineupConfidence.PROJECTED),
                          ctx(1, lineup_confidence=LineupConfidence.CONFIRMED)])
    obs = [
        Observation(game_id="g1", player_id=1, family="points", tip_utc=TIP, actual=25.0),
        Observation(game_id="quiet", player_id=2, family="points", tip_utc=TIP, actual=20.0),
    ]
    s = stratify(obs, ev)
    assert len(s["any_event"]) == 1 and s["any_event"][0].game_id == "g1"
    assert len(s["no_event"]) == 1, "the control stratum must exist and be populated"
    assert len(s["all"]) == 2


def test_the_stratified_residual_test_reports_every_window_including_empty_ones():
    from nba_edge.research.matchup_walkforward import (
        Observation,
        residual_value_by_event_window,
    )

    ev = events_for_game([ctx(12, lineup_confidence=LineupConfidence.PROJECTED),
                          ctx(1, lineup_confidence=LineupConfidence.CONFIRMED)])
    obs = [Observation(game_id="g1", player_id=1, family="points", tip_utc=TIP, actual=25.0,
                       line=24.5, outcome_over=1, v1_p_over=0.5, v2_p_over=0.6, market_p_over=0.5)]
    r = residual_value_by_event_window(obs, ev)
    assert r["n_total"] == 1
    assert "no_event" in r["strata"], "the control window must always be reported"
    assert r["strata"]["lineup_confirmed"]["n"] == 1
    assert r["strata"]["late_scratch"]["n"] == 0
    assert "reason" in r["strata"]["late_scratch"], "an empty window says so rather than vanishing"


# == DISTRIBUTIONAL METRICS ====================================================================


def test_crps_and_coverage_are_actually_computed_now():
    """`_crps_normal` was dead code for a wave: defined, never called, nothing to feed it."""
    import random

    from nba_edge.research.matchup_walkforward import Observation, evaluate_family

    rng = random.Random(3)
    obs = [Observation(game_id=f"g{i}", player_id=1, family="points",
                       tip_utc=TIP + timedelta(days=i), actual=rng.gauss(25, 6),
                       v1_mean=25.0, v1_sd=6.0, v2_mean=25.0, v2_sd=6.0) for i in range(400)]
    r = evaluate_family(obs)
    assert r["crps_v1"] is not None and r["crps_v2"] is not None
    assert r["crps_delta_v2_minus_v1"] == pytest.approx(0.0, abs=1e-9)
    assert r["coverage_v1"]["n"] == 400


def test_coverage_catches_an_overconfident_model():
    """A nominal 80% interval covering far less is exactly the defect this repo has hit before."""
    import random

    from nba_edge.research.matchup_walkforward import Observation, evaluate_family

    rng = random.Random(5)
    obs = [Observation(game_id=f"g{i}", player_id=1, family="points",
                       tip_utc=TIP + timedelta(days=i), actual=rng.gauss(25, 6),
                       v1_mean=25.0, v1_sd=6.0,      # honest
                       v2_mean=25.0, v2_sd=1.5)      # overconfident
           for i in range(600)]
    r = evaluate_family(obs)
    assert r["coverage_v1"]["empirical"] > 0.75
    assert r["coverage_v2"]["empirical"] < 0.45, r["coverage_v2"]
    assert r["coverage_v2"]["miscoverage"] < -0.3
    # and CRPS should prefer the honest one
    assert r["crps_v1"] < r["crps_v2"]


def test_a_narrower_but_correct_model_wins_on_crps():
    import random

    from nba_edge.research.matchup_walkforward import Observation, evaluate_family

    rng = random.Random(9)
    obs = []
    for i in range(600):
        y = rng.gauss(25, 2)
        obs.append(Observation(game_id=f"g{i}", player_id=1, family="points",
                               tip_utc=TIP + timedelta(days=i), actual=y,
                               v1_mean=25.0, v1_sd=6.0, v2_mean=25.0, v2_sd=2.0))
    r = evaluate_family(obs)
    assert r["crps_delta_v2_minus_v1"] < 0, "a correctly sharp forecast must score better"


def test_missing_spread_reports_none_rather_than_inventing_one():
    from nba_edge.research.matchup_walkforward import Observation, evaluate_family

    obs = [Observation(game_id=f"g{i}", player_id=1, family="points",
                       tip_utc=TIP + timedelta(days=i), actual=25.0, v1_mean=25.0)
           for i in range(50)]
    r = evaluate_family(obs)
    assert r["crps_v1"] is None and r["coverage_v1"] is None
