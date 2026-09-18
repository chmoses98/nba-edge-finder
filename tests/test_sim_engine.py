"""Tests for the joint Monte Carlo engine (nba_edge.sim.engine): determinism, bottom-up coherence, calibration
ranges, and directional responses to parameter changes. All sims use fixed seeds and 20-40k draws."""

from __future__ import annotations

import numpy as np
import pytest

from nba_edge.sim import engine
from nba_edge.sim.engine import MAX_OT, simulate, simulate_batch
from nba_edge.sim.params import LEAGUE, GameParams
from nba_edge.sim.result import STAT_KEYS
from tests.conftest import (
    AWAY_BASE_ID,
    HOME_BASE_ID,
    QUESTIONABLE_INDEX,
    STAR_INDEX,
    SYNTHETIC_N_SIMS,
    SYNTHETIC_SEED,
    away_ids,
    home_ids,
    make_synthetic_game,
    team_sum,
)

STAR_ID = HOME_BASE_ID + STAR_INDEX
Q_ID = HOME_BASE_ID + QUESTIONABLE_INDEX
COUNT_KEYS = tuple(k for k in STAT_KEYS if k != "min")

# ---------------------------------------------------------------------------------------------------------------
# determinism / shape
# ---------------------------------------------------------------------------------------------------------------


def test_same_seed_is_bitwise_identical(synthetic_game):
    a = simulate(synthetic_game, 20_000, 123)
    b = simulate(make_synthetic_game(), 20_000, 123)
    np.testing.assert_array_equal(a.home_pts, b.home_pts)
    np.testing.assert_array_equal(a.away_pts, b.away_pts)
    np.testing.assert_array_equal(a.period_pts, b.period_pts)
    np.testing.assert_array_equal(a.n_ot, b.n_ot)
    np.testing.assert_array_equal(a.possessions, b.possessions)
    for pid in a.players:
        np.testing.assert_array_equal(a.players[pid].played, b.players[pid].played)
        np.testing.assert_array_equal(a.players[pid].started, b.players[pid].started)
        for k in STAT_KEYS:
            np.testing.assert_array_equal(a.players[pid].stats[k], b.players[pid].stats[k])
    assert a.seed == b.seed == 123 and a.n_sims == b.n_sims == 20_000


def test_different_seed_differs(synthetic_game):
    a = simulate(synthetic_game, 20_000, 1)
    b = simulate(make_synthetic_game(), 20_000, 2)
    assert not np.array_equal(a.home_pts, b.home_pts)
    assert not np.array_equal(a.players[STAR_ID].stats["pts"], b.players[STAR_ID].stats["pts"])


def test_shapes_and_batching(synthetic_game):
    n = 25_000
    r = simulate(synthetic_game, n, 9, batch=10_000)  # exercises concat_results across 3 batches
    assert r.n_sims == n and r.seed == 9 and r.sim_version == engine.SIM_VERSION
    assert r.home_pts.shape == (n,) and r.away_pts.shape == (n,)
    assert r.period_pts.shape == (n, 2, 4 + MAX_OT)
    assert r.n_ot.shape == (n,) and r.possessions.shape == (n,)
    assert np.all(r.n_ot >= 0) and np.all(r.n_ot <= MAX_OT)
    assert set(r.players) == set(home_ids(synthetic_game)) | set(away_ids(synthetic_game))
    for ps in r.players.values():
        assert ps.played.shape == (n,) and ps.started.shape == (n,)
        assert set(ps.stats) == set(STAT_KEYS)
        assert all(v.shape == (n,) for v in ps.stats.values())
    assert {"ot_rate", "margin_sd", "total_sd", "poss_mean", "home_pts_mean", "home_pts_sd"} <= set(r.diagnostics)


# ---------------------------------------------------------------------------------------------------------------
# coherence invariants (every draw)
# ---------------------------------------------------------------------------------------------------------------


def test_team_points_equal_sum_of_player_points_every_draw(synthetic_sim, synthetic_sim_game):
    """THE coherence invariant: margin/total/team totals/player props all live in the same universe."""
    h = team_sum(synthetic_sim, home_ids(synthetic_sim_game), "pts")
    a = team_sum(synthetic_sim, away_ids(synthetic_sim_game), "pts")
    np.testing.assert_array_equal(h, synthetic_sim.home_pts)
    np.testing.assert_array_equal(a, synthetic_sim.away_pts)


def test_minutes_sum_to_240_plus_ot_every_draw(synthetic_sim, synthetic_sim_game):
    expected = LEAGUE["regulation_minutes"] + LEAGUE["ot_minutes"] * synthetic_sim.n_ot
    for ids in (home_ids(synthetic_sim_game), away_ids(synthetic_sim_game)):
        m = team_sum(synthetic_sim, ids, "min")
        np.testing.assert_allclose(m, expected, atol=1e-6)
    assert (synthetic_sim.n_ot > 0).any(), "OT rows must exist for this to test the +25/OT rule"


def test_period_points_structure(synthetic_sim):
    pp = synthetic_sim.period_pts
    reg = pp[:, :, :4].sum(axis=2)
    ot = pp[:, :, 4:].sum(axis=2)
    np.testing.assert_array_equal(reg[:, 0] + ot[:, 0], synthetic_sim.home_pts)
    np.testing.assert_array_equal(reg[:, 1] + ot[:, 1], synthetic_sim.away_pts)
    no_ot = synthetic_sim.n_ot == 0
    assert np.all(pp[no_ot][:, :, 4:] == 0), "OT columns are zero when n_ot == 0"
    np.testing.assert_array_equal(reg[no_ot, 0], synthetic_sim.home_pts[no_ot])
    # every OT period that was played has points for at least one side, unplayed OT periods are zero
    for k in range(MAX_OT):
        played_k = synthetic_sim.n_ot > k
        assert np.all(pp[~played_k][:, :, 4 + k] == 0)
        if played_k.any():
            assert np.all(pp[played_k][:, :, 4 + k].sum(axis=1) > 0)
    # regulation was tied in every OT draw
    assert np.all(reg[synthetic_sim.n_ot > 0, 0] == reg[synthetic_sim.n_ot > 0, 1])
    assert np.all(pp >= 0)
    # SimResult period helpers agree with the raw array
    np.testing.assert_array_equal(synthetic_sim.team_pts(1, "REG"), reg[:, 0])
    np.testing.assert_array_equal(synthetic_sim.team_pts(2, "1H"), pp[:, 1, 0] + pp[:, 1, 1])
    np.testing.assert_array_equal(synthetic_sim.period_total("2H"), pp[:, :, 2:4].sum(axis=(1, 2)))
    np.testing.assert_array_equal(synthetic_sim.team_margin(2), -synthetic_sim.margin)


def test_no_draw_ends_tied(synthetic_sim):
    assert not (synthetic_sim.home_pts == synthetic_sim.away_pts).any()


def test_ot_rate_in_range(synthetic_sim):
    rate = (synthetic_sim.n_ot > 0).mean()
    assert 0.03 <= rate <= 0.09, rate
    assert synthetic_sim.diagnostics["ot_rate"] == pytest.approx(rate)


def test_player_stats_are_nonnegative_integers(synthetic_sim):
    for ps in synthetic_sim.players.values():
        for k in COUNT_KEYS:
            v = ps.stats[k]
            assert np.issubdtype(v.dtype, np.integer), (ps.nba_id, k, v.dtype)
            assert np.all(v >= 0), (ps.nba_id, k)
        assert np.all(ps.stats["min"] >= 0.0)
        assert np.all(ps.stats["min"] <= 42.0 + 25.0 + 1e-9)  # cap + max OT minutes
        # shooting arithmetic per player: FG3M <= FGA, FTM <= FTA (implied by pts >= 0 is too weak, check directly)
        assert np.all(ps.stats["fg3m"] <= ps.stats["fga"])
        assert np.all(ps.stats["oreb"] + ps.stats["dreb"] == ps.stats["reb"])


def test_absent_players_have_zero_stats_and_minutes(synthetic_sim):
    for pid in (Q_ID, AWAY_BASE_ID + QUESTIONABLE_INDEX):
        ps = synthetic_sim.players[pid]
        out = ~ps.played
        assert out.any() and ps.played.any()
        for k in STAT_KEYS:
            assert np.all(ps.stats[k][out] == 0), (pid, k)
        assert np.all(ps.stats["min"][ps.played] > 0)
        assert not ps.started[out].any()


def test_questionable_player_played_rate(synthetic_sim):
    for pid in (Q_ID, AWAY_BASE_ID + QUESTIONABLE_INDEX):
        assert abs(synthetic_sim.players[pid].played.mean() - 0.5) <= 0.02


def test_exactly_five_starters_per_team_every_draw(synthetic_sim, synthetic_sim_game):
    for ids in (home_ids(synthetic_sim_game), away_ids(synthetic_sim_game)):
        started = np.stack([synthetic_sim.players[i].started for i in ids], axis=1)
        played = np.stack([synthetic_sim.players[i].played for i in ids], axis=1)
        assert np.all(started.sum(axis=1) == 5)
        assert not (started & ~played).any()


def test_star_pra_and_double_double_consistent(synthetic_sim):
    star = synthetic_sim.players[STAR_ID]
    s = star.stats
    np.testing.assert_array_equal(star.stat("pra"), s["pts"] + s["reb"] + s["ast"])
    np.testing.assert_array_equal(star.stat("pr"), s["pts"] + s["reb"])
    np.testing.assert_array_equal(star.stat("pa"), s["pts"] + s["ast"])
    np.testing.assert_array_equal(star.stat("ra"), s["reb"] + s["ast"])
    for ps in synthetic_sim.players.values():
        cats = sum((ps.stats[k] >= 10).astype(int) for k in ("pts", "reb", "ast", "stl", "blk"))
        np.testing.assert_array_equal(ps.stat("double_double"), (cats >= 2).astype(float))
        np.testing.assert_array_equal(ps.stat("triple_double"), (cats >= 3).astype(float))
    assert 0.0 < star.stat("double_double").mean() < 1.0, "star should have a non-degenerate DD rate"


# ---------------------------------------------------------------------------------------------------------------
# calibration ranges (league-average synthetic game should reproduce the LEAGUE priors)
# ---------------------------------------------------------------------------------------------------------------


def test_dispersion_calibration(synthetic_sim):
    assert 14.0 <= synthetic_sim.margin.std() <= 18.5  # empirical 2023-26 regular season: 16.0
    assert 17.0 <= synthetic_sim.total.std() <= 24.0
    assert 10.5 <= synthetic_sim.home_pts.std() <= 14.5
    assert 105.0 <= synthetic_sim.home_pts.mean() <= 122.0
    assert 215.0 <= synthetic_sim.total.mean() <= 240.0
    assert np.corrcoef(synthetic_sim.home_pts, synthetic_sim.away_pts)[0, 1] > 0.15, "game-environment shock"


def test_star_points_correlate_with_team_points(synthetic_sim):
    rho = np.corrcoef(synthetic_sim.players[STAR_ID].stats["pts"], synthetic_sim.home_pts)[0, 1]
    assert rho > 0.3, rho
    assert synthetic_sim.players[STAR_ID].stats["pts"].mean() > synthetic_sim.players[HOME_BASE_ID + 1].stats["pts"].mean()


def test_home_court_advantage_via_mirror(synthetic_game):
    n, seed = 30_000, 5
    straight = simulate(synthetic_game, n, seed)
    mirrored = simulate(GameParams(game_id="M", home=synthetic_game.away, away=synthetic_game.home), n, seed)
    p_team1_home = (straight.margin > 0).mean()
    p_team1_away = (mirrored.margin < 0).mean()  # team 1 is the away side in the mirror
    assert p_team1_home > p_team1_away + 0.03, (p_team1_home, p_team1_away)
    assert p_team1_home > 0.5 > p_team1_away
    assert straight.home_pts.mean() > mirrored.away_pts.mean()


def test_neutral_site_removes_home_edge(synthetic_game):
    synthetic_game.neutral_site = True
    r = simulate(synthetic_game, 40_000, 5)
    assert abs((r.margin > 0).mean() - 0.5) < 0.015


# ---------------------------------------------------------------------------------------------------------------
# directional responses
# ---------------------------------------------------------------------------------------------------------------


def test_player_out_redistributes_usage_to_teammates(synthetic_game):
    n, seed = 30_000, 7
    base = simulate(synthetic_game, n, seed)
    gp = make_synthetic_game()
    gp.home.players[STAR_INDEX].p_play = 0.0
    out = simulate(gp, n, seed)
    assert not out.players[STAR_ID].played.any()
    assert out.players[STAR_ID].stats["pts"].sum() == 0
    for pid in home_ids(gp):
        if pid == STAR_ID:
            continue
        assert out.players[pid].stats["fga"].mean() > base.players[pid].stats["fga"].mean() + 0.3, pid
        assert out.players[pid].stats["pts"].mean() > base.players[pid].stats["pts"].mean() + 0.3, pid
        assert out.players[pid].stats["min"].mean() > base.players[pid].stats["min"].mean(), pid
    drop = base.home_pts.mean() - out.home_pts.mean()
    assert -0.75 <= drop <= 5.0, f"team mean should fall only modestly, got {drop:+.2f}"
    # the away side is untouched in expectation
    assert abs(base.away_pts.mean() - out.away_pts.mean()) < 0.75


def test_impact_ppp_only_acts_as_availability_surprise(synthetic_game):
    """impact_ppp shifts efficiency by (played - p_play): a questionable star lifts the team in draws he plays."""
    synthetic_game.home.players[STAR_INDEX].p_play = 0.5
    r = simulate(synthetic_game, 40_000, 11)
    played = r.players[STAR_ID].played
    gap = r.home_pts[played].mean() - r.home_pts[~played].mean()
    # 0.03 ppp * ~99 poss ≈ 3 pts, split by (played - 0.5) = +/-0.5 each way -> ~3 pts expected difference
    assert 1.5 < gap < 5.0, gap


def test_back_to_back_lowers_scoring(synthetic_game):
    n, seed = 30_000, 7
    base = simulate(synthetic_game, n, seed)
    gp = make_synthetic_game()
    gp.home.b2b = True
    b2b = simulate(gp, n, seed)
    assert b2b.home_pts.mean() < base.home_pts.mean() - 1.0
    assert (b2b.margin > 0).mean() < (base.margin > 0).mean() - 0.02
    assert b2b.possessions.mean() < base.possessions.mean() - 0.5, "b2b slows the game"


def test_pace_raises_total(synthetic_game):
    n, seed = 30_000, 7
    base = simulate(synthetic_game, n, seed)
    gp = make_synthetic_game()
    gp.home.pace = gp.away.pace = LEAGUE["pace"] + 7.0
    fast = simulate(gp, n, seed)
    assert fast.total.mean() > base.total.mean() + 8.0
    assert fast.possessions.mean() > base.possessions.mean() + 5.0


def test_offensive_rating_moves_win_probability(synthetic_game):
    synthetic_game.home.off_ppp += 0.05  # +5 pts/100
    r = simulate(synthetic_game, 30_000, 13)
    assert (r.margin > 0).mean() > 0.62


# ---------------------------------------------------------------------------------------------------------------
# formerly-pinned defects (fixed 2026-09-18): blowout coupling, post-MAX_OT tie-break coherence, batch ot_rate
# ---------------------------------------------------------------------------------------------------------------


def test_starters_play_fewer_minutes_in_realised_blowouts(synthetic_sim, synthetic_sim_game):
    starters = home_ids(synthetic_sim_game)[:5]
    sm = team_sum(synthetic_sim, starters, "min")
    blow = np.abs(synthetic_sim.margin) >= LEAGUE["blowout_margin"]
    assert blow.mean() > 0.1
    assert sm[blow].mean() < sm[~blow].mean() - 5.0  # >= 1 minute per starter


def test_max_ot_tiebreak_keeps_coherence_when_player0_out(synthetic_game, monkeypatch):
    monkeypatch.setattr(engine, "MAX_OT", 0)  # every regulation tie goes straight to the tie-break path
    synthetic_game.home.players[0].p_play = 0.0
    r = simulate(synthetic_game, 20_000, 5)
    h = team_sum(r, home_ids(synthetic_game), "pts")
    np.testing.assert_array_equal(h, r.home_pts)


def test_simulate_batch_ot_rate_diagnostic(synthetic_game):
    r = simulate_batch(synthetic_game, 20_000, np.random.default_rng(0))
    assert r.diagnostics["ot_rate"] == pytest.approx((r.n_ot > 0).mean())


def test_synthetic_fixture_is_what_the_shared_sim_used(synthetic_sim, synthetic_sim_game):
    """Guards the shared session fixture: re-simulating the pristine game reproduces it exactly."""
    again = simulate(synthetic_sim_game, SYNTHETIC_N_SIMS, SYNTHETIC_SEED)
    np.testing.assert_array_equal(again.home_pts, synthetic_sim.home_pts)
