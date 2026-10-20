"""The NBA roster audit (nba/live/roster_audit.py): decision logic on the real 2026-10-20 projection with injected fetchers.

REAL: tests/fixtures/nba_live/d5_20261020T0210Z.json.gz (the published feed and the official-report observations the run archived).
SYNTHETIC: rosters, transactions and mutations built from those real rows; nothing here reaches the network.
"""
import copy
import gzip
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from nba.live import roster_audit as RA  # noqa: E402

FIX = HERE / "fixtures" / "nba_live" / "d5_20261020T0210Z.json.gz"


@pytest.fixture()
def fx():
    return copy.deepcopy(json.load(gzip.open(FIX, "rt")))


def espn_from(feed):
    teams = {}
    for p in feed["players"]:
        if p["family"] == "minutes":
            teams.setdefault(p["team"], []).append({"id": p["player_id"].replace("espn:", ""), "name": p["name"], "status": "Active", "injuries": []})
    return {"status": "ok", "teams": teams}


NONE = {"status": "unavailable", "teams": {}}
NO_TX = {"status": "ok", "rows": [], "name_hits": []}


def run(fx, espn=None, nba=NONE, tx=NO_TX):
    return RA.audit(fx["doc"], fx["official"], espn or espn_from(fx["doc"]), nba, tx)


def test_names_and_teams_normalise():
    assert RA.norm("Ronald Holland II") == RA.norm("Ronald Holland") == "ronaldholland"
    assert RA.norm("Kentavious Caldwell-Pope") == RA.norm("kentavious caldwell pope")
    assert RA.norm("Nikola Jokić") == "nikolajokic"
    assert RA.team("GS") == "GSW" and RA.team("NY") == "NYK" and RA.team("okc") == "OKC"


def test_a_feed_that_matches_the_rosters_and_the_official_report_has_no_error(fx):
    a = run(fx)
    assert a["genuine_roster_errors"] == 0 and a["errors"] == []
    assert a["availability"]["official_explicit_designations"] == {"OUT": 11, "QUESTIONABLE": 5}
    assert a["availability"]["n_misaligned"] == 0 and a["availability"]["ruled_out_rows_not_blocked"] == []


def test_the_minutes_structure_matches_the_reconciliation_the_gate_saw(fx):
    m = run(fx)["minutes"]
    assert {t: m[t]["minutes_sum_raw"] for t in m} == {"BOS": 288.9, "DET": 276.2, "NYK": 297.9, "PHI": 284.4, "OKC": 229.7, "SAS": 274.5}
    for t in m:                                                           # the sum recomputed from the rows reproduces the engine's
        assert abs(m[t]["minutes_sum_recomputed"] / m[t]["minutes_sum_raw"] - 1) < 0.015, t   # published p(play) and minutes are rounded
    assert m["OKC"]["status"] == "PASS" and all(m[t]["status"] == "REVIEW" for t in ("BOS", "DET", "NYK", "PHI", "SAS"))
    # the overshoot is not explained by carried-over roles alone on every team: NYK and SAS exceed the budget even without them
    assert m["NYK"]["overshoot_without_new_team_roles"] > 0 and m["SAS"]["overshoot_without_new_team_roles"] > 0
    assert m["PHI"]["n_new_team"] == 10


def test_a_player_missing_from_the_current_roster_is_a_roster_error(fx):
    espn = espn_from(fx["doc"])
    gone = espn["teams"]["BOS"].pop(0)
    a = run(fx, espn)
    assert a["genuine_roster_errors"] >= 1 and any(gone["name"] in e for e in a["errors"])


def test_a_player_on_another_team_is_reported_with_where_he_is(fx):
    espn = espn_from(fx["doc"])
    moved = espn["teams"]["BOS"].pop(0)
    espn["teams"]["DET"].append(moved)
    a = run(fx, espn)
    err = [e for e in a["errors"] if moved["name"] in e]
    assert err and "DET" in err[0]


def test_a_rostered_player_the_feed_omits_is_listed_not_an_error(fx):
    espn = espn_from(fx["doc"])
    espn["teams"]["OKC"].append({"id": "999", "name": "Some Rookie", "status": "Active", "injuries": []})
    a = run(fx, espn)
    assert any("Some Rookie" in x for x in a["identity"]["OKC"]["espn_roster_not_in_feed"]) and a["genuine_roster_errors"] == 0


def test_official_out_that_the_feed_does_not_block_is_an_availability_error(fx):
    p = next(q for q in fx["doc"]["players"] if q["participation"]["status"] == "CONFIRMED_OUT" and q["family"] == "points")
    p["gate"]["status"] = "PASS"
    a = run(fx)
    assert a["availability"]["ruled_out_rows_not_blocked"] and a["genuine_roster_errors"] >= 1


def test_official_questionable_published_as_a_clean_pass_is_an_error(fx):
    for p in fx["doc"]["players"]:
        if p["participation"]["designation"] == "QUESTIONABLE":
            p["participation"]["status"] = "LIKELY_ACTIVE"
            p["gate"]["status"] = "PASS"
    a = run(fx)
    assert a["availability"]["n_misaligned"] > 0


def test_an_incomplete_independent_roster_is_ignored_not_trusted(fx):
    espn = espn_from(fx["doc"])
    nba = {"status": "ok", "teams": {"BOS": [{"id": "", "name": "Only One"}], "DET": [{"id": "", "name": p["name"]} for p in fx["doc"]["players"] if p["team"] == "DET" and p["family"] == "minutes"]}}
    a = run(fx, espn, nba)
    assert a["identity"]["BOS"]["nba_roster"] is None and a["identity"]["DET"]["nba_roster"] == 18
    assert a["genuine_roster_errors"] == 0


def test_a_complete_independent_roster_that_disagrees_is_an_error(fx):
    espn = espn_from(fx["doc"])
    det = [{"id": "", "name": p["name"]} for p in fx["doc"]["players"] if p["team"] == "DET" and p["family"] == "minutes"]
    det[0] = {"id": "", "name": "Someone Else"}
    a = run(fx, espn, {"status": "ok", "teams": {"DET": det}})
    assert a["genuine_roster_errors"] == 1 and "not_on_league_roster_of_this_team" in a["errors"][0]


def test_parsing_a_basketball_reference_roster_reads_body_cells_only():
    html = ('<table id="roster"><thead><tr><th data-stat="player">Player</th></tr></thead><tbody>'
            '<tr><th data-stat="number">0</th><td class="left" data-stat="player"><a href="/p/x.html">Jayson Tatum</a></td></tr>'
            '<tr><td data-stat="player">Derrick White</td></tr></tbody></table>')
    assert [r["name"] for r in RA.parse_bbref_roster(html)] == ["Jayson Tatum", "Derrick White"]
    assert RA.parse_bbref_roster("<html>no table</html>") == [] and RA.parse_bbref_roster(None) == []


def test_fetchers_are_injected_and_failures_are_reported_not_fatal():
    calls = []

    def get(url, headers=None):
        calls.append(url)
        if url == RA.ESPN_TEAMS:
            return 200, {"sports": [{"leagues": [{"teams": [{"team": {"id": "2", "abbreviation": "BOS"}}, {"team": {"id": "3", "abbreviation": "DET"}}]}]}]}
        if url.endswith("/teams/2/roster"):
            return 200, {"athletes": [{"id": "1", "fullName": "A B", "status": {"type": "active"}, "injuries": [{"status": "Out"}]}]}
        return 500, None
    r = RA.espn_rosters(get)
    assert r["teams"] == {"BOS": [{"id": "1", "name": "A B", "status": "active", "injuries": ["Out"]}]}
    assert RA.espn_rosters(lambda u, h=None: (0, "timeout"))["status"].startswith("teams list HTTP 0")
    assert RA.nba_rosters(lambda u, h=None: (0, "x"), ["BOS"], "2026-27")["teams"] == {}


def test_transactions_naming_new_team_players_are_returned(fx):
    def get(url, headers=None):
        return 200, {"transactions": [{"date": "2026-07-06T07:00Z", "team": {"abbreviation": "PHI"}, "description": "Acquired G Jaylen Brown from the Boston Celtics."},
                                      {"date": "2026-07-06T07:00Z", "team": {"abbreviation": "SA"}, "description": "Signed F Tobias Harris to a contract."},
                                      {"date": "2026-07-01T07:00Z", "team": {"abbreviation": "X"}, "description": "unrelated"}]}
    tx = RA.espn_transactions(get, ["Jaylen Brown", "Tobias Harris", "LeBron James"])
    assert [h["team"] for h in tx["name_hits"]] == ["PHI", "SA"] and tx["n"] == 3
    assert RA.espn_transactions(lambda u, h=None: (404, None))["status"] == "unavailable"


def test_the_report_renders_and_names_the_errors(fx):
    espn = espn_from(fx["doc"])
    espn["teams"]["BOS"].pop(0)
    text = RA.render(run(fx, espn))
    assert "GENUINE ROSTER / AVAILABILITY ERRORS: " in text and "BOS" in text and "team  n  sumP" in text
