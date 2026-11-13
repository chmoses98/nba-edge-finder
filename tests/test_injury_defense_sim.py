"""Defensive injuries change the opponent's scoring, not the injured team's scoring."""
from copy import deepcopy

from nba_edge.sim.engine import simulate
from tests.conftest import make_synthetic_game


def test_defensive_absence_raises_opponent_team_points():
    control = make_synthetic_game()
    control.away.players[0].p_play = 0.0
    control.away.players[0].p_play_baseline = 1.0
    candidate = deepcopy(control)
    candidate.away.players[0].impact_def_ppp = 0.05
    base = simulate(control, 6000, seed=111)
    improved = simulate(candidate, 6000, seed=111)
    assert improved.home_pts.mean() > base.home_pts.mean() + 1.0
    assert improved.diagnostics["team_injury_response_modeled"] == 1.0
    # The shared fixture already gives away.players[0] an offensive effect.
    # Adding a defensive effect to that SAME player must not double-count
    # distinct players in the diagnostic (the metric counts players, not effects).
    assert base.diagnostics["team_injury_response_modeled"] == 1.0
    assert improved.diagnostics["players_with_impact_ppp"] == base.diagnostics["players_with_impact_ppp"]
