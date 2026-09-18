"""Tests for nba_edge.data.history against small hand-written ESPN-shaped fixtures (no network)."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from nba_edge.data import history as H

KEYS = [
    "minutes", "fieldGoalsMade-fieldGoalsAttempted", "threePointFieldGoalsMade-threePointFieldGoalsAttempted",
    "freeThrowsMade-freeThrowsAttempted", "offensiveRebounds", "defensiveRebounds", "rebounds", "assists", "steals",
    "blocks", "turnovers", "fouls", "plusMinus", "points",
]


def _athlete(aid: int, name: str, stats: list[str] | None, starter: bool = False, dnp: bool = False, reason: str | None = None):
    a = {"athlete": {"id": str(aid), "displayName": name}, "starter": starter, "didNotPlay": dnp, "stats": stats or []}
    if reason:
        a["reason"] = reason
    return a


def _competitor(abbr: str, home_away: str, score: int, linescores: list[int]):
    return {"homeAway": home_away, "team": {"abbreviation": abbr}, "score": str(score), "linescores": [{"value": float(v)} for v in linescores]}


def _team_totals(abbr: str, fg: str, ft: str, oreb: int, tov: int, total_tov: int | None = None):
    stats = [
        {"name": "fieldGoalsMade-fieldGoalsAttempted", "displayValue": fg},
        {"name": "freeThrowsMade-freeThrowsAttempted", "displayValue": ft},
        {"name": "offensiveRebounds", "displayValue": str(oreb)},
        {"name": "turnovers", "displayValue": str(tov)},
    ]
    if total_tov is not None:
        stats.append({"name": "totalTurnovers", "displayValue": str(total_tov)})
    return {"team": {"abbreviation": abbr}, "statistics": stats}


# Game 1: BOS (home) 110 - NYK (away) 100, regular season, no OT. NYK has NO team totals block -> player-sum fallback.
SUMMARY_1 = {
    "header": {
        "id": "401001",
        "competitions": [{
            "date": "2024-10-22T23:30Z",
            "status": {"type": {"completed": True, "state": "post"}},
            "competitors": [_competitor("BOS", "home", 110, [30, 25, 28, 27]), _competitor("NYK", "away", 100, [20, 30, 25, 25])],
        }],
    },
    "boxscore": {
        "teams": [_team_totals("BOS", "40-88", "20-25", 10, 12, total_tov=14)],
        "players": [
            {"team": {"abbreviation": "BOS"}, "statistics": [{"keys": KEYS, "athletes": [
                _athlete(1001, "Jayson Tatum", ["36", "10-22", "3-8", "7-8", "1", "9", "10", "5", "1", "0", "3", "2", "+12", "30"], starter=True),
                _athlete(1002, "Bench Guy", None, dnp=True, reason="COACH'S DECISION"),
            ]}]},
            {"team": {"abbreviation": "NYK"}, "statistics": [{"keys": KEYS, "athletes": [
                _athlete(2001, "Jalen Brunson", ["38", "9-20", "2-6", "6-6", "0", "3", "3", "8", "2", "0", "4", "3", "-10", "26"], starter=True),
                _athlete(2002, "Josh Hart", ["30", "4-10", "1-3", "2-4", "3", "7", "10", "4", "1", "1", "2", "1", "-8", "11"], starter=False),
            ]}]},
        ],
    },
}

# Game 2: LAL (home) 120 - GSW (away) 125, preseason, one OT.
SUMMARY_2 = {
    "header": {
        "id": "401002",
        "competitions": [{
            "date": "2024-10-24T02:30Z",  # 10:30pm ET on Oct 23
            "status": {"type": {"completed": True, "state": "post"}},
            "competitors": [_competitor("LAL", "home", 120, [28, 27, 30, 25, 10]), _competitor("GSW", "away", 125, [25, 30, 30, 25, 15])],
        }],
    },
    "boxscore": {
        "teams": [_team_totals("LAL", "45-95", "22-30", 12, 15), _team_totals("GSW", "48-100", "20-24", 8, 13)],
        "players": [
            {"team": {"abbreviation": "LAL"}, "statistics": [{"keys": KEYS, "athletes": [
                _athlete(3001, "LeBron James", ["40", "12-25", "2-7", "6-9", "2", "8", "10", "9", "1", "1", "5", "2", "-5", "32"], starter=True),
            ]}]},
            {"team": {"abbreviation": "GSW"}, "statistics": [{"keys": KEYS, "athletes": [
                _athlete(4001, "Stephen Curry", ["41", "11-24", "7-15", "5-5", "0", "4", "4", "7", "2", "0", "3", "1", "+5", "34"], starter=True),
            ]}]},
        ],
    },
}


def _scoreboard(*events):
    return {"events": list(events)}


def _event(eid: str, when: str, stype: int, home: str, away: str, completed: bool = True):
    return {
        "id": eid, "date": when, "season": {"year": 2025, "type": stype},
        "competitions": [{
            "status": {"type": {"completed": completed, "state": "post" if completed else "pre"}},
            "competitors": [{"homeAway": "home", "team": {"abbreviation": home}}, {"homeAway": "away", "team": {"abbreviation": away}}],
        }],
    }


SCOREBOARD_1022 = _scoreboard(_event("401001", "2024-10-22T23:30Z", 2, "BOS", "NYK"))
SCOREBOARD_1023 = _scoreboard(
    _event("401002", "2024-10-24T02:30Z", 1, "LAL", "GSW"),
    _event("401003", "2024-10-24T00:00Z", 2, "MIA", "ORL", completed=False),  # not completed -> ignored
    _event("401004", "2024-10-24T00:00Z", 2, "EAST", "WEST"),  # non-NBA tricodes -> ignored
)

META_1 = {"game_id": "espn:401001", "game_date_et": "2024-10-22", "season": "2024-25", "season_type": "regular"}
META_2 = {"game_id": "espn:401002", "game_date_et": "2024-10-23", "season": "2024-25", "season_type": "preseason"}


# ------------------------------------------------------------------------------------------------------------
def test_iter_season_dates():
    ds = list(H.iter_season_dates("2024-25"))
    assert ds[0] == date(2024, 10, 1) and ds[-1] == date(2025, 6, 30)
    assert len(ds) == 273
    assert H.season_years("2025-2026") == (2025, 2026)
    with pytest.raises(ValueError):
        H.season_years("2024-26")


def test_scoreboard_events_filters_and_maps_season_type():
    evs = H.scoreboard_events(SCOREBOARD_1023)
    assert [e["event_id"] for e in evs] == ["401002"]
    e = evs[0]
    assert e["season_type"] == "preseason" and e["espn_season_type"] == 1
    assert e["game_date_et"] == "2024-10-23"  # 02:30Z on the 24th is the 23rd in ET
    assert e["home_tricode"] == "LAL" and e["away_tricode"] == "GSW"
    assert H.scoreboard_events(SCOREBOARD_1022)[0]["season_type"] == "regular"


def test_parse_extended_and_player_rows_shape_and_dnp():
    box, extra = H.parse_espn_summary_extended(SUMMARY_1)
    assert len(extra) == len(box.players) == 4
    rows = H.parse_player_rows(box, META_1, extra)
    assert len(rows) == 4
    assert all(set(H.PLAYER_COLUMNS) <= set(r) for r in rows)
    by_name = {r["player_name"]: r for r in rows}
    t = by_name["Jayson Tatum"]
    assert t["nba_id"] == -1001 and t["team_id"] == 1610612738 and t["opp_team_id"] == 1610612752
    assert t["home"] is True and t["started"] is True and t["played"] is True
    assert (t["fgm"], t["fga"], t["fg3m"], t["fg3a"], t["ftm"], t["fta"]) == (10, 22, 3, 8, 7, 8)
    assert (t["oreb"], t["dreb"], t["reb"], t["ast"], t["stl"], t["blk"], t["tov"], t["pf"]) == (1, 9, 10, 5, 1, 0, 3, 2)
    assert t["pts"] == 30 and t["minutes"] == 36.0 and t["plus_minus"] == 12
    assert (t["team_pts"], t["opp_pts"], t["n_ot"]) == (110, 100, 0)
    assert (t["game_id"], t["game_date_et"], t["season"], t["season_type"]) == ("espn:401001", "2024-10-22", "2024-25", "regular")
    dnp = by_name["Bench Guy"]
    assert dnp["played"] is False and dnp["minutes"] == 0.0 and dnp["pts"] == 0 and dnp["fga"] == 0
    assert dnp["dnp_reason"] == "COACH'S DECISION"
    b = by_name["Jalen Brunson"]
    assert b["home"] is False and b["team_pts"] == 100 and b["opp_pts"] == 110 and b["opp_team_id"] == 1610612738
    assert b["plus_minus"] == -10


def test_team_rows_possessions_and_periods():
    box, extra = H.parse_espn_summary_extended(SUMMARY_1)
    prow = H.parse_player_rows(box, META_1, extra)
    trow = H.parse_team_rows(box, META_1, H.parse_espn_team_totals(SUMMARY_1), prow)
    assert len(trow) == 2 and all(set(H.TEAM_COLUMNS) <= set(r) for r in trow)
    bos, nyk = trow
    assert bos["home"] is True and nyk["home"] is False
    assert (bos["pts"], bos["opp_pts"], bos["won"], bos["margin"], bos["total"]) == (110, 100, True, 10, 210)
    assert (nyk["pts"], nyk["opp_pts"], nyk["won"], nyk["margin"]) == (100, 110, False, -10)
    assert (bos["q1"], bos["q2"], bos["q3"], bos["q4"], bos["ot_pts"], bos["n_ot"]) == (30, 25, 28, 27, 0, 0)
    # BOS from team totals (totalTurnovers preferred over turnovers): 0.96*(88 + 0.44*25 - 10 + 14)
    assert bos["totals_source"] == "team_totals"
    assert bos["possessions"] == pytest.approx(0.96 * (88 + 0.44 * 25 - 10 + 14), abs=1e-3)
    # NYK has no totals block -> sum of player rows: fga 30, fta 10, oreb 3, tov 6
    assert nyk["totals_source"] == "player_sum"
    assert (nyk["fga"], nyk["fta"], nyk["oreb"], nyk["tov"]) == (30, 10, 3, 6)
    assert nyk["possessions"] == pytest.approx(0.96 * (30 + 0.44 * 10 - 3 + 6), abs=1e-3)
    assert H.possessions(100, 20, 10, 15) == pytest.approx(0.96 * (100 + 8.8 - 10 + 15))


def test_overtime_and_preseason_game():
    prow, trow = H.build_game_rows(SUMMARY_2, META_2)
    lal, gsw = trow
    assert lal["n_ot"] == 1 and lal["ot_pts"] == 10 and gsw["ot_pts"] == 15
    assert (lal["q1"], lal["q2"], lal["q3"], lal["q4"]) == (28, 27, 30, 25)
    assert lal["won"] is False and gsw["won"] is True and lal["season_type"] == "preseason"
    assert lal["pts"] == 120 == sum([28, 27, 30, 25, 10])
    assert {r["n_ot"] for r in prow} == {1}
    assert gsw["possessions"] == pytest.approx(0.96 * (100 + 0.44 * 24 - 8 + 13), abs=1e-3)


def test_split_helpers():
    assert H.split_made_att("7-15") == (7, 15)
    assert H.split_made_att("--") == (0, 0) and H.split_made_att(None) == (0, 0)
    assert H.to_int("+12") == 12 and H.to_int("-3") == -3 and H.to_int("--") == 0


def test_should_skip_date():
    done = {"espn:1", "espn:2"}
    assert H.should_skip_date(True, ["espn:1", "espn:2"], done) is True
    assert H.should_skip_date(True, [], done) is True  # cached, no games that day
    assert H.should_skip_date(True, ["espn:1", "espn:3"], done) is False
    assert H.should_skip_date(False, ["espn:1"], done) is False  # never skip an uncached date


def test_scoreboard_ttl_trusts_only_post_settle_cache():
    d = date(2024, 10, 22)
    now = datetime(2024, 12, 1, tzinfo=UTC)
    assert H.scoreboard_ttl_s(d, now) == H.SCOREBOARD_TTL_PAST_S
    # a cache entry written *during* the games (before noon UTC next day) must be rejected
    settle = H.scoreboard_settle_instant(d)
    assert H.scoreboard_ttl_s(d, settle + timedelta(hours=1)) == pytest.approx(3600)
    assert H.scoreboard_ttl_s(d, settle - timedelta(hours=1)) == H.SCOREBOARD_TTL_RECENT_S
    assert H.scoreboard_ttl_s(date(2024, 10, 22), datetime(2024, 10, 22, 20, tzinfo=UTC)) == H.SCOREBOARD_TTL_RECENT_S


def test_parquet_round_trip(tmp_path: Path):
    prow, trow = H.build_game_rows(SUMMARY_1, META_1)
    p = tmp_path / "espn" / "player_games_2024-25.parquet"
    assert H.write_parquet(prow, p, H.PLAYER_COLUMNS) == 4
    df = H.read_parquet(p)
    assert len(df) == 4 and list(df.columns[: len(H.PLAYER_COLUMNS)]) == H.PLAYER_COLUMNS
    assert df.loc[df.player_name == "Jayson Tatum", "fga"].item() == 22
    assert bool(df.loc[df.player_name == "Bench Guy", "played"].item()) is False
    t = tmp_path / "espn" / "team_games_2024-25.parquet"
    H.write_parquet(trow, t, H.TEAM_COLUMNS)
    assert H.load_team_games(tmp_path, ["2024-25", "2023-24"]).shape[0] == 2
    assert H.load_player_games(tmp_path, ["2024-25"]).shape[0] == 4
    assert H.load_player_games(tmp_path, ["2019-20"]).empty


def test_run_history_pull_end_to_end_and_resumable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("NBA_EDGE_CACHE_ROOT", str(tmp_path / "cache"))
    calls = {"scoreboard": 0, "summary": 0}
    routes = {
        H.scoreboard_url(date(2024, 10, 22)): SCOREBOARD_1022, H.scoreboard_url(date(2024, 10, 23)): SCOREBOARD_1023,
        H.summary_url("401001"): SUMMARY_1, H.summary_url("401002"): SUMMARY_2,
    }

    def fake_fetch(url: str, ttl_s: float, cache_root=None):
        if "summary?" in url:
            calls["summary"] += 1
        else:
            calls["scoreboard"] += 1
        return routes.get(url, {"events": []}), True

    monkeypatch.setattr(H, "fetch_json", fake_fetch)
    out = tmp_path / "history"
    assert H.run_history_pull(out, ["2024-25"], ["espn"], sleep_s=0) == 0
    assert calls["summary"] == 2
    players = H.load_player_games(out, ["2024-25"])
    teams = H.load_team_games(out, ["2024-25"])
    assert len(players) == 6 and len(teams) == 4
    assert set(teams.season_type) == {"regular", "preseason"}
    man = json.loads((out / "espn" / "MANIFEST.json").read_text())
    assert man["seasons"]["2024-25"]["n_games"] == 2 and man["errors"] == []
    assert man["seasons"]["2024-25"]["date_min"] == "2024-10-22" and man["seasons"]["2024-25"]["date_max"] == "2024-10-23"
    done = json.loads((out / "espn" / "done_events_2024-25.json").read_text())
    assert sorted(done["events"]) == ["espn:401001", "espn:401002"]

    # second run: nothing new -> no summary fetches, same row counts
    calls["summary"] = 0
    assert H.run_history_pull(out, ["2024-25"], ["team_logs", "player_logs"], sleep_s=0) == 0
    assert calls["summary"] == 0
    assert len(H.load_player_games(out, ["2024-25"])) == 6 and len(H.load_team_games(out, ["2024-25"])) == 4


def test_run_history_pull_records_error_and_continues(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("NBA_EDGE_CACHE_ROOT", str(tmp_path / "cache"))
    routes = {
        H.scoreboard_url(date(2024, 10, 22)): SCOREBOARD_1022, H.scoreboard_url(date(2024, 10, 23)): SCOREBOARD_1023,
        H.summary_url("401002"): SUMMARY_2,
    }

    def fake_fetch(url: str, ttl_s: float, cache_root=None):
        if url == H.summary_url("401001"):
            raise RuntimeError("HTTP 500")
        return routes.get(url, {"events": []}), True

    monkeypatch.setattr(H, "fetch_json", fake_fetch)
    out = tmp_path / "history"
    assert H.run_history_pull(out, ["2024-25"], ["espn"], sleep_s=0) == 0
    man = json.loads((out / "espn" / "MANIFEST.json").read_text())
    assert len(man["errors"]) == 1 and man["errors"][0]["game_id"] == "espn:401001" and "HTTP 500" in man["errors"][0]["error"]
    assert man["seasons"]["2024-25"]["n_games"] == 1
    done = json.loads((out / "espn" / "done_events_2024-25.json").read_text())
    assert done["events"] == ["espn:401002"]  # failed game is retried next run


def test_run_history_pull_ignores_unknown_what(tmp_path: Path):
    assert H.run_history_pull(tmp_path, ["2024-25"], ["nothing"]) == 0
    assert not (tmp_path / "espn").exists()
