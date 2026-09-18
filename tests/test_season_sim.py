import numpy as np

from nba_edge.sim.season import TeamStrength, simulate_season


def _league():
    teams = []
    for i in range(30):
        teams.append(TeamStrength(team_id=i, conference="East" if i < 15 else "West", rating=(i % 15 - 7) * 1.2, rating_sd=2.0))
    remaining = []
    for i in range(30):
        for j in range(30):
            if i != j and (i + j) % 3 == 0:
                remaining.append((i, j))
    return teams, remaining


def test_win_totals_sum_to_games_played():
    teams, rem = _league()
    r = simulate_season(teams, rem, 2000, seed=1)
    assert r.wins.shape == (2000, 30)
    assert np.all(r.wins.sum(axis=1) == len(rem))


def test_better_teams_win_more_and_rank_higher():
    teams, rem = _league()
    r = simulate_season(teams, rem, 4000, seed=2)
    mean_w = r.wins.mean(axis=0)
    assert mean_w[7] > mean_w[0] and mean_w[14] > mean_w[7]  # ratings -8.4 .. +8.4 within the East
    assert r.p_playoffs_direct(14) > 0.9 and r.p_playoffs_direct(0) < 0.05
    assert 0 <= r.p_playin(7) <= 1


def test_win_total_ladder_monotone_and_reproducible():
    teams, rem = _league()
    r = simulate_season(teams, rem, 3000, seed=3)
    ks = [5, 10, 15, 20]
    ps = [r.p_wins_ge(14, k) for k in ks]
    assert all(a >= b for a, b in zip(ps, ps[1:], strict=False))
    r2 = simulate_season(teams, rem, 3000, seed=3)
    assert np.array_equal(r.wins, r2.wins)


def test_rating_uncertainty_widens_win_distribution():
    teams, rem = _league()
    narrow = simulate_season([TeamStrength(t.team_id, t.conference, t.rating, 0.1) for t in teams], rem, 3000, seed=4)
    wide = simulate_season([TeamStrength(t.team_id, t.conference, t.rating, 4.0) for t in teams], rem, 3000, seed=4)
    assert wide.wins[:, 14].std() > narrow.wins[:, 14].std() * 1.3
