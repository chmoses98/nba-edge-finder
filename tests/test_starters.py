import json
from datetime import UTC, datetime, timedelta

from nba_edge.archive.ledger import Ledger
from nba_edge.data.starters import STARTERS_KIND, capture_starters, parse_espn_starters, rows_for_game
from nba_edge.matchup.shadow import build_context
from nba_edge.matchup.schemas import LineupConfidence

NOW = datetime(2026, 11, 3, 23, 0, tzinfo=UTC)
TIP = NOW + timedelta(minutes=45)


def athlete(i, starter=None):
    a = {"athlete": {"id": str(i), "displayName": f"P{i}"}, "stats": []}
    if starter is not None:
        a["starter"] = starter
    return a


def body(home_starters=5, away_starters=5, extra=3):
    def team(tri, base, n):
        return {"team": {"abbreviation": tri}, "statistics": [{"keys": ["minutes"], "athletes": [athlete(base + k, True) for k in range(n)] + [athlete(base + 50 + k, False) for k in range(extra)]}]}
    return {"boxscore": {"players": [team("BOS", 100, home_starters), team("NYK", 200, away_starters)]}}


def game(**kw):
    g = {"game_id": "espn:401", "start_time_utc": TIP.isoformat(), "home_team_id": 1610612738, "away_team_id": 1610612752, "home_tricode": "BOS", "away_tricode": "NYK", "status": "scheduled"}
    return g | kw


def test_parse_reads_starter_flags_and_counts_athletes():
    p = parse_espn_starters(body())
    assert p["BOS"]["starter_ids"] == ["100", "101", "102", "103", "104"] and p["BOS"]["n_athletes_listed"] == 8
    assert parse_espn_starters({}) == {} and parse_espn_starters({"boxscore": {"players": [{"team": {}}]}}) == {}


def test_confirmed_only_with_exactly_five_flagged_and_observed_before_tip():
    rows = rows_for_game(game(), body(), NOW)
    assert [r["state"] for r in rows] == ["CONFIRMED", "CONFIRMED"] and rows[0]["minutes_to_tip"] == 45.0
    assert rows[0]["starter_espn_ids"] == ["100", "101", "102", "103", "104"]
    four = rows_for_game(game(), body(home_starters=4), NOW)
    assert four[0]["state"] == "NONE_PUBLISHED" and four[0]["starter_espn_ids"] == [] and four[0]["n_starters_flagged"] == 4 and four[0]["n_athletes_listed"] == 7   # coverage stays measurable
    late = rows_for_game(game(), body(), TIP + timedelta(minutes=1))                    # observed after tip can never be CONFIRMED
    assert {r["state"] for r in late} == {"NONE_PUBLISHED"}
    assert rows_for_game(game(), {}, NOW)[0]["state"] == "NONE_PUBLISHED"


def test_capture_gates_by_window_status_source_and_stamps_after_fetch(tmp_path):
    led = Ledger(tmp_path, run_id="r")
    calls = []
    clock_vals = iter([NOW + timedelta(seconds=3), NOW + timedelta(seconds=5)])
    def fetcher(url):
        calls.append(url); return body()
    games = [game(), game(game_id="espn:402", start_time_utc=(NOW + timedelta(hours=5)).isoformat()), game(game_id="espn:403", start_time_utc=(NOW - timedelta(minutes=5)).isoformat()),
             game(game_id="0022600123"), game(game_id="espn:404", status="final")]
    st = capture_starters(led, games, now=NOW, fetcher=fetcher, clock=lambda: next(clock_vals, NOW + timedelta(seconds=9)))
    assert calls == ["https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event=401"]       # only the in-window ESPN game
    assert (st["games_fetched"], st["rows"], st["confirmed_teams"]) == (1, 2, 2)
    rows = list(led.iter_rows(STARTERS_KIND))
    assert rows[0]["observed_at_utc"].startswith("2026-11-03T23:00:03")      # stamped by the clock read AFTER the fetch


def test_fetch_failure_is_recorded_not_fabricated(tmp_path):
    from nba_edge.data.http import FetchError
    led = Ledger(tmp_path, run_id="r")
    def boom(url): raise FetchError("403")
    st = capture_starters(led, [game()], now=NOW, fetcher=boom)
    assert st["rows"] == 0 and len(st["failures"]) == 1 and led.latest(STARTERS_KIND) is None


def ctx(starter_rows):
    return build_context(game(), [], NOW + timedelta(minutes=1), starter_rows=starter_rows)


def test_shadow_context_uses_only_confirmed_pretip_captures_on_both_sides():
    rows = rows_for_game(game(), body(), NOW)
    c = ctx(rows)
    assert c.lineup_confidence is LineupConfidence.CONFIRMED
    assert c.expected_home_starters == tuple(sorted(-i for i in (100, 101, 102, 103, 104))) and len(c.expected_away_starters) == 5
    assert "context/starters" in c.provenance["starters"]
    # one side unconfirmed -> neither filled, confidence UNKNOWN
    half = [rows[0], rows_for_game(game(), body(away_starters=2), NOW)[1]]
    c2 = ctx(half); assert c2.lineup_confidence is LineupConfidence.UNKNOWN and c2.expected_home_starters == () and c2.expected_away_starters == ()
    # a capture observed after the context's own 'now' is not yet knowable
    future = rows_for_game(game(), body(), NOW + timedelta(minutes=10))
    assert ctx(future).lineup_confidence is LineupConfidence.UNKNOWN
    assert ctx(None).lineup_confidence is LineupConfidence.UNKNOWN and ctx(None).expected_home_starters == ()
