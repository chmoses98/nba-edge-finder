"""Archived (settle-job) box scores carry no shooting stats and no season_type; rate models must not learn 'never shoots' from them (§ box integrity)."""

from datetime import UTC, datetime

import numpy as np
import pandas as pd
import pytest

from nba_edge.archive.ledger import Ledger
from nba_edge.features.build import BuildConfig, BuildReport, league_rates, player_params, team_params
from nba_edge.schemas.core import GameStatus
from nba_edge.settlement.boxscore import FinalBoxScore, PlayerLine
from nba_edge.workflows.simulate import BOX_INTEGRITY_ENV, box_integrity_enabled, load_history


def frames(n_complete=15, n_incomplete=4):
    t, p = [], []
    for g in range(n_complete + n_incomplete):
        d = f"2026-02-{g + 1:02d}"
        complete = g < n_complete
        fga = 17 if complete else 0
        t.append(dict(game_id=f"g{g}", game_date_et=d, season="2025-26", season_type="regular", team_id=1, opp_team_id=2, home=True, pts=110, opp_pts=105,
                      possessions=100.0 if complete else 0.0, n_ot=0, fga=88 if complete else 0, fgm=40 if complete else 0, oreb=10 if complete else 0, tov=13 if complete else 0, stats_complete=complete))
        p.append(dict(game_id=f"g{g}", game_date_et=d, season="2025-26", season_type="regular", team_id=1, nba_id=7, player_name="Star", started=True, played=True, minutes=34.0,
                      pts=28, reb=8, ast=5, fg3m=3, stl=1, blk=0, tov=2, fga=fga, fta=7 if complete else 0, fgm=9 if complete else 0, oreb=1, dreb=7, fg3a=8 if complete else 0, ftm=6 if complete else 0,
                      stats_complete=complete))
    return pd.DataFrame(t), pd.DataFrame(p)


def star(pg, cfg, cutoff="2026-03-01"):
    rep = BuildReport(cutoff_date=cutoff)
    return next(x for x in player_params(1, pg, cutoff, cfg, {}, None, rep) if x.nba_id == 7), rep


def test_default_behaviour_is_unchanged_by_the_new_column():
    _, pg = frames()
    with_col = star(pg, BuildConfig())[0]
    without = star(pg.drop(columns="stats_complete"), BuildConfig())[0]
    assert with_col == without
    assert with_col.fga_per_min < 0.40  # a 17-FGA-in-34-min player (0.50/min) is read as ~0.36 because four zero-FGA rows are the most recent (documents the defect)


def test_rate_models_skip_incomplete_rows_but_minutes_and_role_still_use_them():
    _, pg = frames()
    fixed, rep = star(pg, BuildConfig(require_complete_box=True))
    complete_only = star(pg[pg["stats_complete"]], BuildConfig())[0]
    default = star(pg, BuildConfig())[0]
    assert fixed.fga_per_min == pytest.approx(complete_only.fga_per_min)
    assert fixed.fga_per_min > default.fga_per_min * 1.10
    assert fixed.three_share == pytest.approx(complete_only.three_share) and fixed.ft_pct == pytest.approx(complete_only.ft_pct)
    assert fixed.min_mean == pytest.approx(default.min_mean)  # minutes/role learned from every game
    assert rep.player_games_used[7] == 19 and any("lack shooting stats" in w for w in rep.warnings)


def test_all_incomplete_means_league_priors_not_zero():
    _, pg = frames(n_complete=0, n_incomplete=6)
    fixed = star(pg, BuildConfig(require_complete_box=True))[0]
    default = star(pg, BuildConfig())[0]
    assert fixed.fga_per_min == pytest.approx(0.30)  # the documented prior, i.e. "unknown"
    assert default.fga_per_min < 0.15  # the defect: zeros read as a player who never shoots
    assert np.isfinite([fixed.three_share, fixed.fg3_pct, fixed.fg2_pct, fixed.ft_pct]).all()


def test_team_params_skip_rows_without_possessions_when_enabled():
    tg, _ = frames()
    rep, rep2 = BuildReport(cutoff_date="2026-03-01"), BuildReport(cutoff_date="2026-03-01")
    lg = league_rates(tg[tg["possessions"] > 0])
    legacy = team_params(1, "AAA", tg, "2026-03-01", lg, BuildConfig(), 2, False, rep)
    fixed = team_params(1, "AAA", tg, "2026-03-01", lg, BuildConfig(require_complete_box=True), 2, False, rep2)
    assert rep.team_games_used[1] == 19 and rep2.team_games_used[1] == 15
    assert fixed.pace == pytest.approx(team_params(1, "AAA", tg[tg["stats_complete"]], "2026-03-01", lg, BuildConfig(), 2, False, BuildReport(cutoff_date="x")).pace)
    assert legacy.def_ppp != pytest.approx(fixed.def_ppp)  # zero-possession rows entered as league-average pseudo-games


# ---- load_history --------------------------------------------------------------------------------

GAME, HOME, AWAY = "espn:401", 1610612748, 1610612760
NOW = datetime(2026, 10, 10, 3, 0, tzinfo=UTC)


def archive_with_box(root, season_type):
    led = Ledger(root / "archive", run_id="t")
    led.append_rows("context/schedule", [{"game_id": GAME, "season": "2026-27", "season_type": season_type, "game_date_et": "2026-10-09", "start_time_utc": "2026-10-09T23:00:00Z",
                                          "home_team_id": HOME, "away_team_id": AWAY, "home_tricode": "MIA", "away_tricode": "OKC", "status": "final", "source": "t"}], observed_at=NOW)
    box = FinalBoxScore(game_id=GAME, status=GameStatus.FINAL, home_team_id=HOME, away_team_id=AWAY, home_pts=100, away_pts=98, n_ot=0, source="t", fetched_at_utc=NOW, actual_tip_utc=NOW, is_final=True,
                        players=[PlayerLine(nba_id=-5, team_id=HOME, name="A Player", played=True, started=True, minutes=30.0, pts=20, reb=5, ast=4)])
    led.append_rows("boxscores", [box.model_dump(mode="json")], observed_at=NOW)
    return led


def test_load_history_tags_archive_rows_incomplete_and_defaults_are_legacy_when_disabled(tmp_path, monkeypatch):
    monkeypatch.delenv(BOX_INTEGRITY_ENV, raising=False)
    assert not box_integrity_enabled()
    tg, pg = load_history(tmp_path, archive_with_box(tmp_path, "preseason"))
    assert list(pg["stats_complete"]) == [False] and list(tg["stats_complete"]) == [False, False]
    assert set(pg["season_type"]) == {"regular"}  # legacy labelling, byte-for-byte, while the fix is not activated


def test_load_history_uses_the_archived_schedule_for_season_type_when_enabled(tmp_path, monkeypatch):
    monkeypatch.setenv(BOX_INTEGRITY_ENV, "1")
    tg, pg = load_history(tmp_path, archive_with_box(tmp_path, "preseason"))
    assert set(pg["season_type"]) == {"preseason"} and set(tg["season_type"]) == {"preseason"} and set(pg["season"]) == {"2026-27"}


def test_load_history_unknown_game_type_is_labelled_unknown_not_regular(tmp_path, monkeypatch):
    monkeypatch.setenv(BOX_INTEGRITY_ENV, "1")
    led = archive_with_box(tmp_path, "preseason")
    # a second box for a game with no schedule row
    box = FinalBoxScore(game_id="espn:999", status=GameStatus.FINAL, home_team_id=HOME, away_team_id=AWAY, home_pts=90, away_pts=80, source="t", fetched_at_utc=NOW, actual_tip_utc=NOW, is_final=True, players=[])
    led.append_rows("boxscores", [box.model_dump(mode="json")], observed_at=NOW.replace(minute=5))
    _, pg = load_history(tmp_path, led)
    tg, _ = load_history(tmp_path, led)
    assert "unknown" in set(tg["season_type"])
