"""Starter capture from the ESPN CORE roster endpoint (probe run 41543056159: summary had 0 flags in 15 games; core
roster had 5 starters/team ~19 min pre-tip and 0 at ~49 min with 11-16 roster entries listed)."""
from datetime import UTC, datetime, timedelta

from nba_edge.archive.ledger import Ledger
from nba_edge.data.http import FetchError
from nba_edge.data.starters import (
    ESPN_CORE_ROSTER_URL,
    ESPN_TEAMS_URL,
    STARTERS_KIND,
    capture_starters,
    coverage_by_lead_time,
    parse_core_roster,
    team_row,
)
from nba_edge.matchup.schemas import LineupConfidence
from nba_edge.matchup.shadow import build_context

NOW = datetime(2026, 11, 3, 23, 0, tzinfo=UTC)
TIP = NOW + timedelta(minutes=19)


def entry(pid, starter=False):
    """Real core-roster entry shape (probe keys): active, athlete, didNotPlay, displayName, ejected, forPlayerId, jersey, period, playerId, position, projections, reason, starter, valid."""
    return {"active": True, "athlete": {"$ref": f"http://x/athletes/{pid}"}, "didNotPlay": False, "displayName": f"P{pid}", "ejected": False, "forPlayerId": pid,
            "jersey": "1", "period": 0, "playerId": pid, "position": {"abbreviation": "G"}, "projections": {}, "reason": "", "starter": starter, "valid": True}


def roster(base, n_starters=5, n=12):
    return {"entries": [entry(base + k, k < n_starters) for k in range(n)]}


TEAMS = {"sports": [{"leagues": [{"teams": [{"team": {"id": "2", "abbreviation": "BOS"}}, {"team": {"id": "18", "abbreviation": "NY"}}]}]}]}


def game(**kw):
    return {"game_id": "espn:401", "start_time_utc": TIP.isoformat(), "home_team_id": 1610612738, "away_team_id": 1610612752, "home_tricode": "BOS", "away_tricode": "NYK", "status": "scheduled"} | kw


def fetcher_for(home, away, calls=None):
    def f(url):
        if calls is not None:
            calls.append(url)
        if url == ESPN_TEAMS_URL:
            return TEAMS
        if url.endswith("/competitors/2/roster"):
            return home
        if url.endswith("/competitors/18/roster"):
            return away
        raise AssertionError(url)
    return f


def test_parse_counts_distinct_starter_flags_only():
    p = parse_core_roster(roster(100))
    assert p["starter_ids"] == ["100", "101", "102", "103", "104"] and len(p["entries"]) == 12
    dup = {"entries": [entry(1, True), entry(1, True), entry(2, "true"), entry(3, None)]}      # duplicates collapse; truthy-but-not-True is not a flag
    assert parse_core_roster(dup)["starter_ids"] == ["1"]
    assert parse_core_roster(None)["entries"] == [] and parse_core_roster({"entries": [{"displayName": "x"}]})["entries"] == []


def test_confirmed_needs_exactly_five_flags_and_pre_tip_observation():
    url = "u"
    ok = team_row(game(), "home", roster(100), NOW, url)
    assert ok["state"] == "CONFIRMED" and ok["minutes_to_tip"] == 19.0 and ok["n_roster_entries"] == 12 and ok["source"] == "espn_core_roster"
    assert ok["raw_entries"] == roster(100)["entries"] and ok["source_url"] == url                    # raw evidence preserved verbatim
    for n in (0, 4, 6):
        r = team_row(game(), "home", roster(100, n_starters=n), NOW, url)
        assert r["state"] == "NONE_PUBLISHED" and r["starter_espn_ids"] == [] and r["n_starters_flagged"] == n
    assert team_row(game(), "home", roster(100), TIP + timedelta(minutes=1), url)["state"] == "NONE_PUBLISHED"     # post-tip can never confirm


def test_full_roster_is_never_mistaken_for_starters():
    """The ~49-minute probe case: 12-16 roster entries, zero starter flags."""
    r = team_row(game(), "home", roster(100, n_starters=0, n=16), NOW - timedelta(minutes=30), "u")
    assert r["state"] == "NONE_PUBLISHED" and r["starter_espn_ids"] == [] and r["starter_names"] == [] and r["n_roster_entries"] == 16
    five_of_twelve_entries_no_flags = {"entries": [entry(i) for i in range(5)]}
    assert team_row(game(), "away", five_of_twelve_entries_no_flags, NOW, "u")["state"] == "NONE_PUBLISHED"       # exactly 5 entries != 5 starters


def test_capture_uses_core_roster_gates_window_and_stamps_after_fetch(tmp_path):
    led = Ledger(tmp_path, run_id="r")
    calls = []
    ticks = iter(NOW + timedelta(seconds=s) for s in (3, 5, 7))
    games = [game(), game(game_id="espn:402", start_time_utc=(NOW + timedelta(hours=5)).isoformat()), game(game_id="espn:403", start_time_utc=(NOW - timedelta(minutes=5)).isoformat()),
             game(game_id="0022600123"), game(game_id="espn:404", status="final")]
    st = capture_starters(led, games, now=NOW, fetcher=fetcher_for(roster(100), roster(200), calls), clock=lambda: next(ticks, NOW + timedelta(seconds=30)))
    assert calls[0] == ESPN_TEAMS_URL and calls[1:] == [ESPN_CORE_ROSTER_URL.format(event_id="401", team_id="2"), ESPN_CORE_ROSTER_URL.format(event_id="401", team_id="18")]
    assert not any("summary" in c for c in calls)                                    # the summary endpoint (no pregame starters) is never used
    assert (st["games_fetched"], st["rows"], st["confirmed_teams"]) == (1, 2, 2)
    rows = list(led.iter_rows(STARTERS_KIND))
    assert [r["observed_at_utc"][:19] for r in rows] == ["2026-11-03T23:00:03", "2026-11-03T23:00:05"]     # each stamped by a clock read AFTER its own fetch


def test_fetch_failures_are_recorded_as_failed_rows_not_fabricated(tmp_path):
    led = Ledger(tmp_path, run_id="r")
    def f(url):
        if url == ESPN_TEAMS_URL:
            return TEAMS
        raise FetchError("403")
    st = capture_starters(led, [game()], now=NOW, fetcher=f)
    rows = list(led.iter_rows(STARTERS_KIND))
    assert len(st["failures"]) == 2 and {r["state"] for r in rows} == {"FETCH_FAILED"} and all(r["starter_espn_ids"] == [] and r["error"] for r in rows)
    led2 = Ledger(tmp_path / "b", run_id="r")
    def teams_down(url):
        raise FetchError("down")
    st2 = capture_starters(led2, [game()], now=NOW, fetcher=teams_down)
    assert st2["rows"] == 0 and led2.latest(STARTERS_KIND) is None                   # no team ids -> nothing invented


def test_coverage_by_lead_time_separates_confirmed_from_full_roster():
    def obs(m, h, a):
        return [team_row(game(), "home", roster(100, h), TIP - timedelta(minutes=m), "u"), team_row(game(), "away", roster(200, a), TIP - timedelta(minutes=m), "u")]

    rows = obs(19, 5, 5) + obs(49, 0, 0) + obs(35, 5, 0)
    cov = {c["minutes_to_tip"]: c for c in coverage_by_lead_time(rows)}
    assert (cov["0-20"]["confirmed_teams"], cov["0-20"]["games_both_confirmed"], cov["0-20"]["share_teams_confirmed"]) == (2, 1, 1.0)
    assert (cov["45-60"]["confirmed_teams"], cov["45-60"]["full_roster_no_starters"], cov["45-60"]["share_teams_confirmed"]) == (0, 2, 0.0)
    assert (cov["30-45"]["confirmed_teams"], cov["30-45"]["games_both_confirmed"], cov["30-45"]["full_roster_no_starters"]) == (1, 0, 1)
    assert cov["60-90"]["team_observations"] == 0 and cov["60-90"]["share_teams_confirmed"] is None


def ctx(starter_rows):
    return build_context(game(), [], NOW + timedelta(minutes=1), starter_rows=starter_rows)


def test_shadow_context_uses_only_confirmed_pretip_captures_on_both_sides():
    rows = [team_row(game(), "home", roster(100), NOW, "u"), team_row(game(), "away", roster(200), NOW, "u")]
    c = ctx(rows)
    assert c.lineup_confidence is LineupConfidence.CONFIRMED
    assert c.expected_home_starters == tuple(sorted(-i for i in (100, 101, 102, 103, 104))) and len(c.expected_away_starters) == 5
    assert "core-roster" in c.provenance["starters"]
    half = [rows[0], team_row(game(), "away", roster(200, 0), NOW, "u")]
    c2 = ctx(half)
    assert c2.lineup_confidence is LineupConfidence.UNKNOWN and c2.expected_home_starters == () and c2.expected_away_starters == ()
    future = [team_row(game(), "home", roster(100), NOW + timedelta(minutes=10), "u"), team_row(game(), "away", roster(200), NOW + timedelta(minutes=10), "u")]
    assert ctx(future).lineup_confidence is LineupConfidence.UNKNOWN                  # not yet knowable at the context's own 'now'
    assert ctx(None).lineup_confidence is LineupConfidence.UNKNOWN and ctx(None).expected_home_starters == ()
    assert c.home_scheme is None and c.away_scheme is None                          # schemes / exposures are never invented


def test_coverage_counts_both_sides_confirmed_even_with_repeated_observations():
    from nba_edge.data.starters import coverage_by_lead_time
    rows = []
    for i in range(5):                                            # five polls per side inside 0-20 min
        for side in ("home", "away"):
            rows.append({"game_id": "espn:1", "side": side, "state": "CONFIRMED", "minutes_to_tip": 10.0 - i, "n_roster_entries": 15})
    rows.append({"game_id": "espn:2", "side": "home", "state": "CONFIRMED", "minutes_to_tip": 5.0, "n_roster_entries": 15})
    b = coverage_by_lead_time(rows)[0]
    assert b["games"] == 2 and b["games_both_confirmed"] == 1 and b["confirmed_teams"] == 11


def test_context_refresh_asks_for_yesterdays_utc_date_so_the_late_et_slate_is_not_lost(monkeypatch):
    import inspect

    from nba_edge.data import context
    assert "range(-1, days_ahead + 1)" in inspect.getsource(context.run_context_refresh)
