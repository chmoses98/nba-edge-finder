"""MATCHUP_AWARE_V2: schemas, leakage guards, neutral-by-default effects, and the V1 regression.

The most important test in this file is ``test_the_neutral_matchup_layer_reproduces_v1_bitwise``.
Everything else guards a way of breaking it, or a way of claiming knowledge the data does not
support.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np
import pytest
from pydantic import ValidationError

from nba_edge.matchup import effects as EFF
from nba_edge.matchup import leakage as LK
from nba_edge.matchup import transform as TR
from nba_edge.matchup.assignment import (
    MIN_POSSESSIONS_FOR_NAMED_DEFENDERS,
    AssignmentEvidence,
    estimate_exposure,
)
from nba_edge.matchup.packet import matchup_packet
from nba_edge.matchup.schemas import (
    Availability,
    DefenderRef,
    DefenderShare,
    GameMatchupContext,
    LineupConfidence,
    MatchupAdjustment,
    Measure,
    PlayerDefenderExposure,
    SchemeFeature,
    TeamDefensiveScheme,
)
from nba_edge.matchup.version import (
    EFFECTS_VERSION,
    MATCHUP_AUTHORITY,
    MATCHUP_MODEL_VERSION,
    describe,
    effects_are_neutral,
)
from nba_edge.sim.engine import simulate
from tests.conftest import make_synthetic_game

T0 = datetime(2026, 10, 20, 18, 0, tzinfo=UTC)
TIP = datetime(2026, 10, 20, 23, 0, tzinfo=UTC)


def ctx(**kw):
    base = dict(
        game_id="0022600001", observed_at_utc=T0, home_team_id=1, away_team_id=2, tip_utc=TIP,
    )
    base.update(kw)
    return GameMatchupContext(**base)


# == 1. V1 REGRESSION: the layer must be invisible when it has learned nothing ==================


def test_the_neutral_matchup_layer_reproduces_v1_bitwise():
    """V1 must be byte-identical through the V2 pipeline while effects are neutral.

    Not "close" -- identical arrays. The pipeline is `V1 params -> transform -> existing engine`, so
    if the transform is a true identity the engine cannot tell it ran.
    """
    gp = make_synthetic_game()
    context = ctx()
    adjustments, report = EFF.resolve_adjustments(context)
    assert report["neutral"] is True

    v2_params, tr = TR.apply_matchup(gp, adjustments)
    assert v2_params is gp, "a neutral layer must return the ORIGINAL params object"
    assert tr["neutral"] is True

    v1 = simulate(gp, 4000, seed=11)
    v2 = simulate(v2_params, 4000, seed=11)
    assert np.array_equal(v1.home_pts, v2.home_pts)
    assert np.array_equal(v1.away_pts, v2.away_pts)
    assert np.array_equal(v1.period_pts, v2.period_pts)
    assert np.array_equal(v1.possessions, v2.possessions)
    assert v1.sim_version == v2.sim_version and v1.seed == v2.seed
    for pid, ps in v1.players.items():
        other = v2.players[pid]
        assert np.array_equal(ps.played, other.played)
        assert np.array_equal(ps.started, other.started)
        for key, arr in ps.stats.items():
            assert np.array_equal(arr, other.stats[key]), f"player {pid} stat {key} diverged"


def test_v1_params_are_not_mutated_by_an_active_adjustment():
    """V2 must never reach back into the object V1 is holding."""
    gp = make_synthetic_game()
    pid = gp.home.players[0].nba_id
    before = gp.home.players[0].fga_per_min
    adj = {pid: MatchupAdjustment(game_id="g", offensive_player_id=pid, adjustment_version="t",
                                  effects_version="fitted-x", fga_multiplier=0.8)}
    out, _ = TR.apply_matchup(gp, adj)
    assert gp.home.players[0].fga_per_min == before
    assert out.home.players[0].fga_per_min == pytest.approx(before * 0.8)


def test_simulation_is_deterministic_for_the_same_inputs_and_seed():
    gp = make_synthetic_game()
    a = simulate(gp, 3000, seed=7)
    b = simulate(gp, 3000, seed=7)
    assert np.array_equal(a.home_pts, b.home_pts) and np.array_equal(a.away_pts, b.away_pts)


def test_the_arm_carries_its_own_version_and_never_claims_authority():
    d = describe()
    assert d["matchup_model_version"] == MATCHUP_MODEL_VERSION == "MATCHUP_AWARE_V2"
    assert d["authority"] == MATCHUP_AUTHORITY == "RESEARCH"
    assert d["v1_baseline_id"] == "NBA_BASELINE_2026_PRESEASON_V1"
    assert d["v1_baseline_intact"] is True
    assert d["effects_neutral"] is True and effects_are_neutral()


# == 2. DEFENDER DISTRIBUTIONS: probabilities, never labels =====================================


def test_defender_shares_must_sum_to_one():
    with pytest.raises(ValidationError, match="sum to 1.0"):
        PlayerDefenderExposure(
            game_id="g", offensive_player_id=1, observed_at_utc=T0, source="s",
            shares=(DefenderShare(ref=DefenderRef.PLAYER, defender_player_id=9, share=0.5),),
        )


def test_an_exposure_cannot_be_empty():
    with pytest.raises(ValidationError, match="at least one share"):
        PlayerDefenderExposure(game_id="g", offensive_player_id=1, observed_at_utc=T0,
                               source="s", shares=())


def test_unknown_is_expressible_as_a_full_distribution():
    e = PlayerDefenderExposure(
        game_id="g", offensive_player_id=1, observed_at_utc=T0, source="s",
        shares=(DefenderShare(ref=DefenderRef.UNKNOWN, share=1.0),),
    )
    assert e.is_unknown and e.identified_share == 0.0


def test_a_player_share_must_name_a_player_and_others_must_not():
    with pytest.raises(ValidationError, match="must carry defender_player_id"):
        DefenderShare(ref=DefenderRef.PLAYER, share=1.0)
    with pytest.raises(ValidationError, match="must not carry defender_player_id"):
        DefenderShare(ref=DefenderRef.SWITCH_OTHER, share=1.0, defender_player_id=3)
    with pytest.raises(ValidationError, match="must carry a label"):
        DefenderShare(ref=DefenderRef.POSITION, share=1.0)


def test_duplicate_defenders_in_one_distribution_are_rejected():
    with pytest.raises(ValidationError, match="duplicate"):
        PlayerDefenderExposure(
            game_id="g", offensive_player_id=1, observed_at_utc=T0, source="s",
            shares=(DefenderShare(ref=DefenderRef.PLAYER, defender_player_id=9, share=0.5),
                    DefenderShare(ref=DefenderRef.PLAYER, defender_player_id=9, share=0.5)),
        )


def test_a_distribution_is_never_collapsed_to_a_single_defender():
    """The brief's example: a real assignment is spread, with switches explicitly carried."""
    e = estimate_exposure("g", 1, T0, AssignmentEvidence(
        observed_shares={9: 0.51, 8: 0.19, 7: 0.17}, observed_possessions=640, source="pbp"))
    kinds = [s.ref for s in e.shares]
    assert kinds.count(DefenderRef.PLAYER) == 3
    assert DefenderRef.SWITCH_OTHER in kinds, "unmodelled mass must stay visible"
    assert e.share_for_player(9) == pytest.approx(0.51)
    assert 0 < e.confidence < 1.0, "assignment is never certain"


def test_a_thin_sample_reports_unknown_rather_than_a_confident_defender():
    e = estimate_exposure("g", 1, T0, AssignmentEvidence(
        observed_shares={9: 0.95}, observed_possessions=MIN_POSSESSIONS_FOR_NAMED_DEFENDERS - 1,
        source="pbp"))
    assert e.is_unknown and e.confidence == 0.0


def test_positional_evidence_alone_can_never_name_a_defender():
    """Position equality is weak evidence about assignments and must not produce a named player."""
    e = estimate_exposure("g", 1, T0, AssignmentEvidence(
        positional_shares={"SG": 0.6, "SF": 0.25}, source="depth_chart"))
    assert e.identified_share == 0.0
    assert all(s.ref is not DefenderRef.PLAYER for s in e.shares)
    assert e.confidence is not None and e.confidence <= 0.3


def test_no_evidence_at_all_reports_unknown():
    e = estimate_exposure("g", 1, T0, AssignmentEvidence(source="none"))
    assert e.is_unknown


def test_observed_shares_over_one_fail_closed():
    with pytest.raises(ValueError, match="exceeds 1.0"):
        estimate_exposure("g", 1, T0, AssignmentEvidence(
            observed_shares={9: 0.8, 8: 0.5}, observed_possessions=900, source="pbp"))


# == 3. UNKNOWN / UNAVAILABLE DATA =============================================================


def test_an_unavailable_measure_cannot_carry_a_value():
    with pytest.raises(ValidationError, match="must not carry a value"):
        Measure(value=0.4, availability=Availability.UNAVAILABLE)
    with pytest.raises(ValidationError, match="requires a value"):
        Measure(availability=Availability.OBSERVED)


def test_absent_scheme_features_read_as_unavailable_not_zero():
    s = TeamDefensiveScheme(team_id=1, observed_at_utc=T0, source="x", features={})
    m = s.feature(SchemeFeature.SWITCH_FREQUENCY)
    assert m.value is None and m.availability is Availability.UNAVAILABLE
    assert s.known_features == ()


def test_starters_are_five_or_explicitly_unknown():
    ctx(expected_home_starters=())  # unknown is fine
    with pytest.raises(ValidationError, match="exactly 5"):
        ctx(expected_home_starters=(1, 2, 3))


# == 4. NEUTRALITY AND FAIL-CLOSED BEHAVIOUR ====================================================


def test_a_default_adjustment_is_exactly_neutral():
    assert MatchupAdjustment.neutral("g", 1, effects_version=EFFECTS_VERSION).is_neutral


def test_missing_matchup_data_produces_neutral_adjustments_not_guesses():
    adj, rep = EFF.resolve_adjustments(ctx(expected_home_rotation=(1, 2, 3)))
    assert rep["neutral"] is True and rep["n_active"] == 0
    assert all(a.is_neutral for a in adj.values())
    assert all("neutral" in " ".join(a.notes) or "no fitted" in " ".join(a.notes) for a in adj.values())


def test_a_malformed_adjustment_fails_closed():
    bad = MatchupAdjustment(game_id="g", offensive_player_id=1, adjustment_version="t",
                            effects_version="x", assist_rate_delta=float("nan"))
    with pytest.raises(TR.MatchupTransformError, match="not a finite number"):
        TR.validate(bad)
    gp = make_synthetic_game()
    with pytest.raises(TR.MatchupTransformError):
        TR.apply_matchup(gp, {gp.home.players[0].nba_id: bad})


def test_a_non_positive_multiplier_is_rejected_at_the_schema():
    with pytest.raises(ValidationError):
        MatchupAdjustment(game_id="g", offensive_player_id=1, adjustment_version="t",
                          effects_version="x", fga_multiplier=0.0)


def test_an_estimator_that_misstates_its_effects_version_fails_closed():
    class Liar:
        version = "fitted-1"

        def estimate(self, context):
            return {1: MatchupAdjustment(game_id=context.game_id, offensive_player_id=1,
                                         adjustment_version="a", effects_version="something-else",
                                         fga_multiplier=0.9)}

    with pytest.raises(ValueError, match="misstate"):
        EFF.resolve_adjustments(ctx(), estimator=Liar(), effects_version="fitted-1")


def test_an_estimator_returning_another_games_adjustment_fails_closed():
    class WrongGame:
        version = "fitted-1"

        def estimate(self, context):
            return {1: MatchupAdjustment(game_id="other", offensive_player_id=1,
                                         adjustment_version="a", effects_version="fitted-1")}

    with pytest.raises(ValueError, match="adjustment for game"):
        EFF.resolve_adjustments(ctx(), estimator=WrongGame(), effects_version="fitted-1")


def test_adjustments_v1_cannot_consume_are_reported_not_silently_dropped():
    gp = make_synthetic_game()
    pid = gp.home.players[0].nba_id
    adj = {pid: MatchupAdjustment(game_id="g", offensive_player_id=pid, adjustment_version="t",
                                  effects_version="fitted-x", rim_rate_delta=-0.08)}
    _out, rep = TR.apply_matchup(gp, adj)
    assert "rim_rate_delta" in rep["inapplicable_fields_present"]


def test_component_effects_can_move_in_opposite_directions():
    """A matchup must be able to say 'points down, assists up' -- not one global multiplier."""
    gp = make_synthetic_game()
    p = gp.home.players[0]
    adj = {p.nba_id: MatchupAdjustment(game_id="g", offensive_player_id=p.nba_id,
                                       adjustment_version="t", effects_version="fitted-x",
                                       fga_multiplier=0.9, assist_rate_delta=0.06)}
    out, _ = TR.apply_matchup(gp, adj)
    q = out.home.players[0]
    assert q.fga_per_min < p.fga_per_min and q.ast_weight > p.ast_weight


# == 5. POINT-IN-TIME / LEAKAGE ================================================================


def test_a_context_observed_after_the_decision_is_refused():
    late = ctx(observed_at_utc=TIP - timedelta(minutes=5))
    with pytest.raises(LK.MatchupLeakageError, match="leak the future"):
        LK.assert_usable(late, decision_at=T0)


def test_a_context_observed_at_or_after_tip_is_not_pregame():
    at_tip = ctx(observed_at_utc=TIP)
    assert LK.is_pregame(at_tip) is False
    with pytest.raises(LK.MatchupLeakageError, match="not pregame"):
        LK.assert_usable(at_tip, decision_at=TIP + timedelta(hours=1))


def test_a_context_without_a_tip_cannot_be_called_pregame():
    no_tip = ctx(tip_utc=None)
    with pytest.raises(LK.MatchupLeakageError, match="carries no tip"):
        LK.assert_usable(no_tip, decision_at=T0 + timedelta(minutes=1))


def test_future_lineup_information_cannot_leak_backward():
    """The newest context overall must not be returned for an earlier decision instant."""
    early = ctx(observed_at_utc=TIP - timedelta(hours=6), lineup_confidence=LineupConfidence.PROJECTED)
    confirmed = ctx(observed_at_utc=TIP - timedelta(minutes=20),
                    lineup_confidence=LineupConfidence.CONFIRMED)
    got = LK.latest_knowable([early, confirmed], decision_at=TIP - timedelta(hours=3))
    assert got is early, "the confirmed lineup did not exist yet at the decision instant"
    got2 = LK.latest_knowable([early, confirmed], decision_at=TIP - timedelta(minutes=5))
    assert got2 is confirmed


def test_latest_knowable_returns_none_when_nothing_was_observable_yet():
    assert LK.latest_knowable([ctx(observed_at_utc=TIP)], decision_at=T0) is None


def test_an_exposure_for_another_game_cannot_be_attached_to_a_context():
    e = PlayerDefenderExposure(game_id="other", offensive_player_id=1, observed_at_utc=T0,
                               source="s", shares=(DefenderShare(ref=DefenderRef.UNKNOWN, share=1.0),))
    with pytest.raises(ValidationError, match="attached to context"):
        ctx(exposures=(e,))


# == 6. PACKET / UI ============================================================================


def test_the_packet_never_invents_explanatory_factors_when_effects_are_neutral():
    adj = MatchupAdjustment.neutral("0022600001", 1, effects_version=EFFECTS_VERSION)
    blk = matchup_packet(context=ctx(), offensive_player_id=1, adjustment=adj,
                         v1_projection={"points": 27.8}, v2_projection={"points": 27.8})
    assert blk["effects_active"] is False
    assert blk["explanatory_factors"] == []
    assert "no effect has been learned" in blk["explanatory_factors_reason"]
    assert blk["delta_v2_v1"] == {"points": 0.0}


def test_the_packet_computes_its_own_delta_rather_than_trusting_a_caller():
    blk = matchup_packet(context=ctx(), offensive_player_id=1,
                         v1_projection={"points": 27.8}, v2_projection={"points": 25.9})
    assert blk["delta_v2_v1"]["points"] == pytest.approx(-1.9)


def test_the_packet_reports_missing_matchup_data_as_unavailable():
    blk = matchup_packet(context=ctx(), offensive_player_id=99)
    assert blk["matchup"]["available"] is False
    assert blk["defensive_scheme_context"]["home"]["available"] is False
    assert blk["matchup_adjustments"]["available"] is False


def test_the_packet_carries_full_provenance():
    blk = matchup_packet(context=ctx(), offensive_player_id=1)
    p = blk["provenance"]
    assert p["matchup_model_version"] == "MATCHUP_AWARE_V2"
    assert p["v1_baseline_id"] == "NBA_BASELINE_2026_PRESEASON_V1"
    assert p["effects_version"] == EFFECTS_VERSION
    assert p["authority"] == "RESEARCH"


def test_only_meaningful_shares_are_called_primary_defenders():
    e = PlayerDefenderExposure(
        game_id="0022600001", offensive_player_id=1, observed_at_utc=T0, source="s",
        shares=(DefenderShare(ref=DefenderRef.PLAYER, defender_player_id=9, share=0.55),
                DefenderShare(ref=DefenderRef.PLAYER, defender_player_id=8, share=0.06),
                DefenderShare(ref=DefenderRef.SWITCH_OTHER, share=0.39)),
    )
    blk = matchup_packet(context=ctx(exposures=(e,)), offensive_player_id=1)
    ids = [d["player_id"] for d in blk["matchup"]["projected_primary_defenders"]]
    assert ids == [9], "a 6% defender is not a headline"


# == 7. SHADOW CAPTURE =========================================================================


def test_shadow_contexts_resolve_real_captured_roster_rows():
    """The join must match the shape context actually captures, not a shape we wish it captured.

    Captured roster rows carry ESPN keys; the schedule carries NBA team ids. Matching on a
    ``team_id``/``nba_id`` field that the rows do not have produced an empty rotation for every
    game -- 17 records that looked written and held nothing.
    """
    from nba_edge.matchup.shadow import build_context

    game = {"game_id": "espn:401902644", "start_time_utc": "2026-10-03T23:00:00Z",
            "home_team_id": 1610612761, "away_team_id": 1610612748,
            "home_tricode": "TOR", "away_tricode": "MIA"}
    rosters = [
        {"espn_team_id": "28", "team_abbreviation": "TOR", "espn_athlete_id": "4396993"},
        {"espn_team_id": "28", "team_abbreviation": "TOR", "espn_athlete_id": "3136776"},
        {"espn_team_id": "14", "team_abbreviation": "MIA", "espn_athlete_id": "4066648"},
        {"espn_team_id": "1", "team_abbreviation": "ATL", "espn_athlete_id": "4278039"},
    ]
    c = build_context(game, rosters, T0)
    assert c is not None
    assert c.expected_home_rotation == (-4396993, -3136776)[::-1] or set(c.expected_home_rotation) == {
        -4396993, -3136776}
    assert set(c.expected_away_rotation) == {-4066648}, "the ATL row must not leak into this game"
    assert all(pid < 0 for pid in c.expected_home_rotation), "ESPN ids are provisional (negative)"


def test_a_shadow_context_never_fabricates_matchup_data():
    from nba_edge.matchup.shadow import build_context

    c = build_context({"game_id": "g", "start_time_utc": "2026-10-03T23:00:00Z",
                       "home_team_id": 1610612761, "away_team_id": 1610612748}, [], T0)
    assert c.exposures == () and c.expected_home_starters == ()
    assert c.home_scheme is None and c.lineup_confidence is LineupConfidence.UNKNOWN
    assert "no defensive-assignment source" in c.provenance["exposures"]


def test_a_game_that_cannot_be_identified_is_skipped_not_guessed():
    from nba_edge.matchup.shadow import build_context

    assert build_context({"start_time_utc": "2026-10-03T23:00:00Z"}, [], T0) is None
    assert build_context({"game_id": "g", "home_team_id": 1, "away_team_id": 2}, [], T0) is None


# == 8. WALK-FORWARD RESEARCH FRAMEWORK ========================================================


def test_a_fold_cannot_train_past_its_evaluation_window():
    from nba_edge.research.matchup_walkforward import Fold

    Fold(index=0, train_start=T0, train_end=T0, eval_start=T0, eval_end=T0 + timedelta(days=7))
    with pytest.raises(ValueError, match="leakage"):
        Fold(index=1, train_start=T0, train_end=T0 + timedelta(days=1), eval_start=T0,
             eval_end=T0 + timedelta(days=7))


def test_walk_forward_folds_are_ordered_disjoint_and_snapped_to_game_boundaries():
    from nba_edge.research.matchup_walkforward import walk_forward_folds

    times = [T0 + timedelta(hours=6 * i) for i in range(600)]
    folds = walk_forward_folds(times, n_folds=4, min_train_games=200)
    assert len(folds) == 4
    for f in folds:
        assert f.train_end <= f.eval_start, "no fold may train on its own evaluation window"
        assert f.train_start <= f.train_end < f.eval_end
        assert f.train_end in times and f.eval_start in times, "boundaries must sit on a game"
    for a, b in zip(folds, folds[1:], strict=False):
        assert a.eval_end <= b.eval_start, "evaluation windows must not overlap"
        assert a.train_end <= b.train_end, "the training window must only expand"


def test_too_little_history_yields_no_folds_rather_than_a_thin_one():
    from nba_edge.research.matchup_walkforward import walk_forward_folds

    assert walk_forward_folds([T0 + timedelta(days=i) for i in range(50)], min_train_games=200) == []


def test_the_residual_value_test_compares_v2_against_v1_market_and_hybrid():
    """V2 earns influence only by beating V1 AND the market AND the hybrid -- not just V1."""
    import random

    from nba_edge.research.matchup_walkforward import Observation, residual_value_test

    rng = random.Random(0)
    obs = []
    for i in range(400):
        p = rng.uniform(0.15, 0.85)
        y = int(rng.random() < p)
        obs.append(Observation(
            game_id=f"g{i}", player_id=1, family="points", tip_utc=T0 + timedelta(days=i),
            actual=25.0, line=24.5, outcome_over=y,
            v1_p_over=p, market_p_over=p, hybrid_p_over=p, v2_p_over=p))
    out = residual_value_test(obs)
    assert set(out) >= {"v2_vs_v1", "v2_vs_market", "v2_vs_hybrid"}
    for key in ("v2_vs_v1", "v2_vs_market", "v2_vs_hybrid"):
        assert out[key]["n_paired"] == 400, key
        assert out[key]["logloss_delta"] == pytest.approx(0.0, abs=1e-9), (
            f"{key}: an identical forecast must score identically")


def test_a_noisier_v2_is_reported_as_worse_not_better():
    """The control: V2 = V1 plus noise must not come out ahead."""
    import random

    from nba_edge.research.matchup_walkforward import Observation, residual_value_test

    rng = random.Random(7)
    obs = []
    for i in range(1500):
        p = rng.uniform(0.2, 0.8)
        y = int(rng.random() < p)
        noisy = min(0.99, max(0.01, p + rng.gauss(0, 0.15)))
        obs.append(Observation(
            game_id=f"g{i}", player_id=1, family="points", tip_utc=T0 + timedelta(days=i),
            actual=25.0, line=24.5, outcome_over=y,
            v1_p_over=p, market_p_over=p, hybrid_p_over=p, v2_p_over=noisy))
    out = residual_value_test(obs)
    assert out["v2_vs_v1"]["logloss_delta"] > 0, "adding noise must not improve log loss"


def test_the_residual_test_reports_absence_rather_than_a_number_it_cannot_compute():
    from nba_edge.research.matchup_walkforward import Observation, residual_value_test

    out = residual_value_test([Observation(game_id="g", player_id=1, family="points",
                                           tip_utc=T0, actual=25.0)])
    assert out["v2_vs_market"]["n_paired"] == 0 and "reason" in out["v2_vs_market"]


# == 9. INGESTION =============================================================================


def test_the_capability_report_states_what_is_missing_rather_than_assuming_it_exists():
    from nba_edge.matchup.ingest import CAPABILITIES, capability_report

    class PbpOnly:
        name = "pbp"

        def available(self):
            return {"possessions": True, "substitutions": True}

    rep = capability_report(PbpOnly())
    assert rep["source"] == "pbp"
    assert set(rep["capabilities"]) == set(CAPABILITIES), "every capability must be stated"
    assert rep["capabilities"]["possessions"] is True
    assert rep["capabilities"]["defenders"] is False
    assert "defenders" in rep["missing"], "an unsupplied capability must be named, not absent"


def test_incomplete_lineup_stints_are_quarantined_with_a_reason():
    from nba_edge.matchup.ingest import LineupStintRecord, quarantine_stints

    good = LineupStintRecord(game_id="g", period=1, stint_index=0,
                             home_lineup=(1, 2, 3, 4, 5), away_lineup=(6, 7, 8, 9, 10))
    short = LineupStintRecord(game_id="g", period=1, stint_index=1,
                              home_lineup=(1, 2, 3, 4), away_lineup=(6, 7, 8, 9, 10))
    dupe = LineupStintRecord(game_id="g", period=1, stint_index=2,
                             home_lineup=(1, 1, 3, 4, 5), away_lineup=(6, 7, 8, 9, 10))
    assert good.lineups_are_complete and not short.lineups_are_complete
    kept, dropped = quarantine_stints([good, short, dupe])
    assert kept == [good]
    assert len(dropped) == 2
    assert all(d["reasons"] for d in dropped), "every rejection must carry a reason"


def test_an_unidentified_shot_defender_stays_unidentified():
    from nba_edge.matchup.ingest import ShotAttemptRecord, ShotType, ShotZone

    s = ShotAttemptRecord(game_id="g", period=1, clock_seconds=500.0, shooter_player_id=1,
                          defender_player_id=None, made=True, source="pbp")
    assert s.defender_player_id is None, "None means the source did not identify one, not 'nobody'"
    assert s.zone is ShotZone.UNKNOWN and s.shot_type is ShotType.UNKNOWN, (
        "an unreported zone must default to UNKNOWN, never to a guessed bucket")
