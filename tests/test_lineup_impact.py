"""Fit real certified stints and verify point-in-time/non-production behaviour."""
import numpy as np
import pandas as pd
import pytest

from nba_edge.features.build import BuildConfig, build_game_params
from nba_edge.research.lineup_impact import LineupImpactModel, fit_lineup_impact


def _fixture():
    tg = []
    stints = []
    for k in range(120):
        gid = f"g{k}"
        dt = str((pd.Timestamp("2025-01-01") + pd.Timedelta(days=k)).date())
        tg.append({"game_id": gid, "game_date_et": dt, "team_id": 1,
                   "opp_team_id": 2, "home": True, "season_type": "regular"})
        h = list(range(10, 15)) if k % 3 else [10, 11, 12, 13, 15]
        a = list(range(20, 25))
        score = 13 if 14 in h else 9
        stints.append({"game_id": gid, "certified": True, "seconds": 360,
                       "home_pts": score, "away_pts": 11,
                       "home_poss": 10, "away_poss": 10,
                       **{f"home_p{i+1}": h[i] for i in range(5)},
                       **{f"away_p{i+1}": a[i] for i in range(5)}})
    return pd.DataFrame(stints), pd.DataFrame(tg)


def test_certified_stints_produce_fitted_player_effects():
    st, tg = _fixture()
    model = fit_lineup_impact(st, tg, "2025-06-01", min_player_seconds=1800)
    assert model.n_games == 120
    assert model.n_players >= 10
    assert model.offensive_absence_ppp(14) > model.offensive_absence_ppp(15)
    assert all(np.isfinite(v) and abs(v) <= 0.06 for v in model.offense.values())
    assert all(np.isfinite(v) and abs(v) <= 0.06 for v in model.defense.values())


def test_future_stints_and_uncertified_stints_never_change_fit():
    st, tg = _fixture()
    cutoff = "2025-03-20"
    good = fit_lineup_impact(st, tg, cutoff, min_player_seconds=1800, min_games=50)
    poisoned = st.copy()
    poisoned.loc[poisoned["game_id"].isin(tg[tg["game_date_et"] >= cutoff]["game_id"]), "home_pts"] = 9999
    assert fit_lineup_impact(poisoned, tg, cutoff, min_player_seconds=1800, min_games=50) == good
    bad = st.copy()
    bad["certified"] = False
    assert fit_lineup_impact(bad, tg, "2025-06-01", min_player_seconds=1800).n_players == 0


def test_lineup_shadow_requires_fitted_historical_model():
    with pytest.raises(ValueError, match="strictly historical"):
        build_game_params(
            {"game_id": "x", "home_team_id": 1, "away_team_id": 2},
            pd.DataFrame(), pd.DataFrame(), "2026-11-01", {},
            cfg=BuildConfig(injury_response_mode="lineup_shadow"),
        )
    bad = LineupImpactModel(offense={10: 0.01}, defense={}, n_players=1, training_cutoff="2026-11-02")
    with pytest.raises(ValueError, match="strictly historical"):
        build_game_params(
            {"game_id": "x", "home_team_id": 1, "away_team_id": 2},
            pd.DataFrame(), pd.DataFrame(), "2026-11-01", {},
            cfg=BuildConfig(injury_response_mode="lineup_shadow"), lineup_model=bad,
        )


def test_t60_pit_statuses_are_probabilistic_and_future_minutes_cannot_leak():
    from scripts.injury_lineup_holdout import _pit_minutes_delta

    games = [f"g{i}" for i in range(10)]
    prior = pd.DataFrame([
        {"game_id": gid, "nba_id": pid, "minutes": 36.0 if pid == 100 else 34.0}
        for gid in games for pid in range(100, 107)
    ])
    model = LineupImpactModel(offense={100: 0.05, 101: 0.02},
                              defense={100: 0.04, 101: 0.01})
    hard_out = _pit_minutes_delta(prior, games, {100: 0.0}, model)
    doubtful = _pit_minutes_delta(prior, games, {100: 0.08}, model)
    questionable = _pit_minutes_delta(prior, games, {100: 0.45}, model)
    assert hard_out[2] == pytest.approx(36.0)
    assert doubtful[2] == pytest.approx(33.12)
    assert questionable[2] == pytest.approx(19.8)
    assert hard_out[0] < doubtful[0] < questionable[0] < 0
    assert _pit_minutes_delta(prior, games, {}, model) == (0.0, 0.0, 0.0)
    # Even a corrupted postgame box must not enter the T-60 replacement.
    future = pd.concat([prior, pd.DataFrame([
        {"game_id": "future", "nba_id": 100, "minutes": 48000.0}
    ])], ignore_index=True)
    assert _pit_minutes_delta(future, games, {100: 0.08}, model) == doubtful
