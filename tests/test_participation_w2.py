"""W2 participation study: PIT arm mechanics and lineup on/off weights (pure functions, synthetic data)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from nba_edge.research import participation as pt


def _team_draws():
    # 3 players x 4 draws; player 0 is listed Out, player 2 does not appear in draw 3
    return np.array([[30.0, 20.0, 0.0, 10.0],
                     [20.0, 30.0, 40.0, 30.0],
                     [10.0, 10.0, 20.0, 0.0]])


def test_out_player_is_zeroed_and_minutes_are_conserved_per_draw():
    M = _team_draws()
    new, info = pt.apply_pit(M, [1, 2, 3], {1: "out"}, {"questionable": 0.5}, seed=7)
    assert (new[0] == 0).all()
    assert np.allclose(new.sum(axis=0), M.sum(axis=0))  # no clipping needed here
    # proportional: draw 0 hands 30 to players 2/3 in ratio 20:10
    assert np.allclose(new[1:, 0], [40.0, 20.0])
    # a non-appearing player never receives minutes (draw 3: player 3 absent)
    assert new[2, 3] == 0 and new[1, 3] == 40.0
    assert info["minutes_removed"] == np.mean([30, 20, 0, 10])


def test_lineup_weights_route_minutes_and_fall_back_when_missing():
    M = _team_draws()
    new, info = pt.apply_pit(M, [1, 2, 3], {1: "out"}, {}, seed=7, weight_fn=lambda a, rec: np.array([0.0, 1.0]))
    assert np.allclose(new[2, :3], M[2, :3] + M[0, :3]) and np.allclose(new[1, :3], M[1, :3])
    # draw 3: the weighted recipient did not appear -> proportional fallback to the one who did
    assert new[1, 3] == 40.0
    new2, info2 = pt.apply_pit(M, [1, 2, 3], {1: "out"}, {}, seed=7, weight_fn=lambda a, rec: None)
    assert info2["lineup_weight_fallback"] == 1
    assert np.allclose(new2, pt.apply_pit(M, [1, 2, 3], {1: "out"}, {}, seed=7)[0])


def test_thinning_only_lowers_appearance_to_the_dev_rate():
    rng = np.random.default_rng(0)
    M = np.vstack([np.where(rng.random(2000) < 0.9, 25.0, 0.0), np.full(2000, 30.0)])
    new, _ = pt.apply_pit(M, [1, 2], {1: "questionable"}, {"questionable": 0.6}, seed=1)
    assert abs((new[0] > 0).mean() - 0.6) < 0.04
    same, _ = pt.apply_pit(M, [1, 2], {1: "questionable"}, {"questionable": 0.95}, seed=1)
    assert np.array_equal(same, M)  # never raised above the champion's own rate


def test_onoff_uses_only_games_before_the_date():
    stints = pd.DataFrame([
        # game g1 (Jan 1): player 10 on for 600 s with 11..14, then off for 600 s, 15 replaces him
        {"game_id": "g1", "seconds": 600.0, **{f"home_p{i}": p for i, p in enumerate([10, 11, 12, 13, 14], 1)},
         **{f"away_p{i}": p for i, p in enumerate([20, 21, 22, 23, 24], 1)}},
        {"game_id": "g1", "seconds": 600.0, **{f"home_p{i}": p for i, p in enumerate([15, 11, 12, 13, 14], 1)},
         **{f"away_p{i}": p for i, p in enumerate([20, 21, 22, 23, 24], 1)}},
        # game g2 (Jan 5): only 16 plays with 10 sitting -> must be invisible to a Jan 5 forecast
        {"game_id": "g2", "seconds": 1200.0, **{f"home_p{i}": p for i, p in enumerate([16, 11, 12, 13, 14], 1)},
         **{f"away_p{i}": p for i, p in enumerate([20, 21, 22, 23, 24], 1)}},
    ])
    info = pd.DataFrame([{"game_id": "g1", "game_date_et": "2026-01-01", "home_team_id": 1, "away_team_id": 2},
                         {"game_id": "g2", "game_date_et": "2026-01-05", "home_team_id": 1, "away_team_id": 2}])
    idx = pt.OnOffIndex.from_stints(stints, info)
    w = idx.weights(1, "2026-01-05", 10, [11, 15, 16])
    assert np.allclose(w, [0.0, 1.0, 0.0])  # 15 replaces 10; 11 plays either way; 16 unseen before Jan 5
    w_later = idx.weights(1, "2026-01-06", 10, [11, 15, 16])
    assert w_later[2] > 0  # g2 counted once it is in the past
    assert idx.weights(1, "2026-01-01", 10, [11]) is None  # no prior certified games


def test_oracle_and_metrics():
    d = np.array([0.0, 0.0, 20.0, 30.0])
    assert pt.oracle_participation(d, 0.0).tolist() == [0.0]
    assert pt.oracle_participation(d, 25.0).tolist() == [20.0, 30.0]
    m = pt.row_metrics(np.zeros(1), 0.0)
    assert m["crps"] == 0 and m["p_appear"] == 0
