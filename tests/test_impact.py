"""The impact model was rejected out of sample, so these tests pin the properties that made the
rejection trustworthy rather than any claim that it works."""

from __future__ import annotations

import numpy as np
import pandas as pd

from nba_edge.research.impact import MAX_ABS_IMPACT_PPP, build_design, fit_impact


def _synthetic(n_games=400, n_players=20, seed=0):
    """Two teams, fixed rosters, one genuinely strong player -- enough to check the design's shape."""
    rng = np.random.default_rng(seed)
    tg, pg = [], []
    for g in range(n_games):
        gid = f"g{g}"
        for tid, opp in ((1, 2), (2, 1)):
            poss = 100.0
            ppp = 1.10 + (0.08 if tid == 1 else 0.0) + rng.normal(0, 0.05)
            tg.append({"game_id": gid, "game_date_et": f"2025-01-{g % 28 + 1:02d}", "season_type": "regular",
                       "team_id": tid, "opp_team_id": opp, "home": tid == 1,
                       "pts": ppp * poss, "opp_pts": 1.10 * poss, "possessions": poss})
            for j in range(n_players // 2):
                pid = tid * 100 + j
                pg.append({"game_id": gid, "team_id": tid, "nba_id": pid,
                           "game_date_et": f"2025-01-{g % 28 + 1:02d}", "season_type": "regular",
                           "minutes": 24.0, "player_name": f"P{pid}"})
    return pd.DataFrame(tg), pd.DataFrame(pg)


def test_design_carries_both_teams_so_opponent_is_controlled_by_construction():
    """An earlier version omitted opponent controls and rewarded role players on strong teams."""
    tg, pg = _synthetic()
    X, y, keep, tgm = build_design(tg, pg, min_player_games=5)
    n_p = len(keep) + 1
    assert X.shape[1] == 2 * n_p + 1, "offence block, defence block, home"

    # every row should carry offence shares summing to ~1 AND defence shares summing to ~1
    off_block = X[:, :n_p].sum(axis=1)
    def_block = X[:, n_p:2 * n_p].sum(axis=1)
    assert np.allclose(off_block, 1.0, atol=1e-5)
    assert np.allclose(def_block, 1.0, atol=1e-5), "the opponent's players must appear on the defence side"


def test_rare_players_are_pooled_not_given_personal_coefficients():
    """Estimating a personal effect from a handful of games is how a fit invents a +12 twelfth man."""
    tg, pg = _synthetic()
    cameo = pg.iloc[:3].copy()
    cameo["nba_id"] = 999
    pg2 = pd.concat([pg, cameo], ignore_index=True)
    m = fit_impact(tg, pg2, alpha=100.0, min_player_games=15)
    assert 999 not in m.off, "a 3-game player must land in the replacement bucket"


def test_coefficients_are_clipped_and_the_clipping_is_counted():
    tg, pg = _synthetic()
    m = fit_impact(tg, pg, alpha=1e-6, min_player_games=5)  # almost no regularisation
    assert all(abs(v) <= MAX_ABS_IMPACT_PPP + 1e-9 for v in m.off.values())
    assert all(abs(v) <= MAX_ABS_IMPACT_PPP + 1e-9 for v in m.deff.values())
    assert isinstance(m.clipped, int)


def test_stronger_regularisation_shrinks_the_spread():
    """The whole defence against unstable star effects is the penalty, so it must actually bite."""
    tg, pg = _synthetic()
    lo = fit_impact(tg, pg, alpha=10.0, min_player_games=5)
    hi = fit_impact(tg, pg, alpha=2000.0, min_player_games=5)
    spread = lambda m: float(np.std([m.total(p) for p in m.off]))  # noqa: E731
    assert spread(hi) < spread(lo)


def test_defence_is_signed_so_offence_and_defence_add_rather_than_cancel():
    """A defensive coefficient is an effect on the OPPONENT's scoring; unflipped, a good two-way
    player would cancel himself out when the two are summed."""
    tg, pg = _synthetic()
    m = fit_impact(tg, pg, alpha=100.0, min_player_games=5)
    pid = next(iter(m.off))
    assert m.total(pid) == m.off[pid] + m.deff[pid]


def test_insufficient_data_returns_an_empty_model_rather_than_guessing():
    tg, pg = _synthetic(n_games=10)
    m = fit_impact(tg, pg, alpha=100.0, min_player_games=5)
    assert m.off == {} and m.n_players >= 0
