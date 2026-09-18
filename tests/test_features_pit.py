"""Point-in-time guarantees of the feature builder."""

import numpy as np
import pandas as pd

from nba_edge.features.build import (
    BuildConfig,
    BuildReport,
    build_game_params,
    league_rates,
    player_params,
    rest_days_for,
    team_params,
)
from nba_edge.schemas.core import InjuryStatus


def _frames():
    t, p = [], []
    for g in range(20):
        d = f"2026-01-{g+1:02d}"
        stype = "preseason" if g < 3 else "regular"
        t.append(dict(game_id=f"g{g}", game_date_et=d, season="2025-26", season_type=stype, team_id=1, opp_team_id=2, home=True, pts=100 + g, opp_pts=100, possessions=100.0, n_ot=0, fga=88, fgm=40, oreb=10, tov=13))
        for j in range(10):
            p.append(dict(game_id=f"g{g}", game_date_et=d, season="2025-26", season_type=stype, team_id=1, nba_id=j, player_name=f"P{j}", started=j < 5, played=True, minutes=30.0 if g < 15 else 10.0, pts=10, reb=5, ast=3, fg3m=1, stl=1, blk=0, tov=1, fga=8, fta=2, fgm=4, oreb=1, dreb=4, fg3a=3, ftm=2))
    return pd.DataFrame(t), pd.DataFrame(p)


def test_cutoff_is_strict_and_excludes_preseason():
    tg, pg = _frames()
    rep = BuildReport(cutoff_date="2026-01-10")
    tp = team_params(1, "AAA", tg, "2026-01-10", league_rates(tg), BuildConfig(), 2, False, rep)
    # games 2026-01-01..01-09 exist (9), minus 3 preseason = 6 usable
    assert rep.team_games_used[1] == 6
    # the game ON the cutoff date must not be used
    rep2 = BuildReport(cutoff_date="2026-01-11")
    team_params(1, "AAA", tg, "2026-01-11", league_rates(tg), BuildConfig(), 2, False, rep2)
    assert rep2.team_games_used[1] == 7
    # offensive rating reflects only prior games (pts 103..108 -> ppp ~1.055 shrunk toward league)
    assert 1.0 < tp.off_ppp < league_rates(tg)["ppp"] + 0.05


def test_future_minutes_do_not_leak_into_role_estimate():
    tg, pg = _frames()
    rep = BuildReport(cutoff_date="2026-01-12")
    pls = player_params(1, pg, "2026-01-12", BuildConfig(), {}, None, rep)
    p0 = next(p for p in pls if p.nba_id == 0)
    assert 28 < p0.min_mean < 31  # minutes dropped to 10 only from game 16 onward; unseen at this cutoff
    rep = BuildReport(cutoff_date="2026-01-21")
    pls = player_params(1, pg, "2026-01-21", BuildConfig(), {}, None, rep)
    p0 = next(p for p in pls if p.nba_id == 0)
    assert p0.min_mean < 22  # recent role change now visible and weighted


def test_injury_status_maps_to_availability_and_unknown_players_get_priors():
    tg, pg = _frames()
    rep = BuildReport(cutoff_date="2026-01-21")
    inj = {0: InjuryStatus.OUT, 1: InjuryStatus.QUESTIONABLE, 2: InjuryStatus.PROBABLE}
    pls = player_params(1, pg, "2026-01-21", BuildConfig(), inj, [0, 1, 2, 3, 99], rep)
    by = {p.nba_id: p for p in pls}
    assert by[0].p_play == 0.0 and by[1].p_play == 0.5 and by[2].p_play == 0.85 and by[3].p_play == 1.0
    assert by[99].min_mean <= 6.0 and by[99].p_play <= 0.9  # never seen: deep-bench prior, flagged
    assert any("99" in w for w in rep.warnings)


def test_rest_days_and_thin_roster_warning():
    tg, pg = _frames()
    assert rest_days_for(1, "2026-01-21", tg) == 1
    assert rest_days_for(1, "2026-01-01", tg) is None
    game = dict(game_id="X", home_team_id=1, away_team_id=2, home_tricode="AAA", away_tricode="BBB")
    gp, rep = build_game_params(game, tg, pg, "2026-01-21", {1: {}, 2: {}})
    assert gp.home.b2b is True
    assert any("fewer than 8 available players" in w and "BBB" in w for w in rep.warnings)  # team 2 has no player rows
    assert gp.away.rating_sd > gp.home.rating_sd  # no data -> wider uncertainty


def test_no_nan_in_params():
    tg, pg = _frames()
    game = dict(game_id="X", home_team_id=1, away_team_id=2, home_tricode="AAA", away_tricode="BBB")
    gp, _ = build_game_params(game, tg, pg, "2026-01-21", {1: {}, 2: {}})
    for p in gp.home.players:
        vals = [p.min_mean, p.min_sd, p.fga_per_min, p.three_share, p.fg2_pct, p.fg3_pct, p.ft_pct, p.fta_per_fga, p.ast_weight, p.oreb_weight, p.dreb_weight]
        assert all(np.isfinite(vals)), p
