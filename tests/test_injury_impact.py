"""Leakage, identification and sign tests for the research-only injury response."""
from dataclasses import replace

import pandas as pd
from nba_edge.features.injury_impact import estimate_team_injury_impacts
from nba_edge.sim.params import LEAGUE, PlayerParams


def _history(*, linked_absence=False):
    tg, pg = [], []
    for g, date in enumerate(pd.date_range("2026-01-01", periods=48)):
        gid = f"g{g}"
        absent = g % 5 == 0
        tg.append({
            "team_id": 1, "opp_team_id": 2, "game_id": gid,
            "game_date_et": date.strftime("%Y-%m-%d"), "home": g % 2 == 0,
            "season_type": "regular", "possessions": 100.0,
            "pts": 110 if absent else 120, "opp_pts": 112,
        })
        for j in range(10):
            out = absent and (j == 0 or (j == 1 and linked_absence))
            pg.append({
                "team_id": 1, "game_id": gid,
                "game_date_et": date.strftime("%Y-%m-%d"),
                "season_type": "regular",
                "nba_id": j, "minutes": 0.0 if out else (32.0 if j < 2 else 21.0),
            })
    players = [
        PlayerParams(nba_id=j, team_id=1, name=f"P{j}",
                     p_play=0.0 if j == 0 else 1.0,
                     p_start=1.0 if j < 5 else 0.0,
                     min_mean=32.0 if j < 2 else 21.0, min_sd=3.0)
        for j in range(10)
    ]
    return pd.DataFrame(tg), pd.DataFrame(pg), players


def _fit(tg, pg, players, cutoff="2026-02-18"):
    return estimate_team_injury_impacts(
        1, tg, pg, cutoff, players,
        ratings={2: (LEAGUE["ppp"], LEAGUE["ppp"], 30.0)},
    )


def test_repeated_absence_has_positive_estimated_effect_and_real_baseline():
    tg, pg, players = _history()
    fitted = _fit(tg, pg, players)
    assert set(fitted) == {0}
    assert 0.02 < fitted[0].impact_ppp <= 0.08
    assert 0.65 < fitted[0].baseline < 0.90
    assert fitted[0].off_games >= 4
    assert fitted[0].n_team_games == 48


def test_leakage_cutoff_excludes_future_games_even_for_absent_star():
    tg, pg, players = _history()
    old = _fit(tg, pg, players, "2026-02-01")
    extra = tg.copy()
    extra.loc[extra["game_date_et"] >= "2026-02-01", "pts"] = 9999
    assert _fit(extra, pg, players, "2026-02-01") == old


def test_unidentifiable_simultaneous_absences_are_not_assigned_impacts():
    tg, pg, players = _history(linked_absence=True)
    assert _fit(tg, pg, players) == {}


def test_no_off_games_does_not_impute_a_superstar_impact():
    tg, pg, players = _history()
    pg.loc[pg["nba_id"] == 0, "minutes"] = 32.0
    assert _fit(tg, pg, players) == {}


def test_incomplete_box_scores_are_not_interpreted_as_absences():
    tg, pg, players = _history()
    pg = pg.loc[~((pg["nba_id"] > 6) & (pg["game_id"].str[1:].astype(int) % 5 == 0))]
    # Those games now have only six players with minutes and are excluded.
    assert _fit(tg, pg, players) == {}


def test_never_estimates_from_todays_or_later_games():
    tg, pg, players = _history()
    assert _fit(tg, pg, players, "2026-01-01") == {}
    # Same cutoff date must have no effect from a later change in the injury report.
    players[0] = replace(players[0], p_play=1.0)
    assert _fit(tg, pg, players, "2026-01-01") == {}


def test_invalid_inputs_fail_closed():
    tg, pg, players = _history()
    assert _fit(tg.drop(columns=["possessions"]), pg, players) == {}
    assert _fit(tg, pg.drop(columns=["minutes"]), players) == {}
