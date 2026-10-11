"""Full play-by-play parsing and lineup certification, on a small hand-built game.

The game is synthetic and exists only to pin the rules; it is never reported as a result.
"""

from __future__ import annotations

import copy

import pytest

from nba_edge.pbp.espn_full import parse_game
from nba_edge.pbp.lineups import infer_period_start, is_turnover, possession_team, reconstruct_game

H, A = 1610612738, 1610612752  # BOS (home), NYK (away)


def ev(order, period, clock, typ, team=None, p=(), hs=0, as_=0, shooting=False):
    p = list(p) + [None] * (3 - len(p))
    return {"game_id": "espn:1", "order": order, "period": period, "clock_s": clock, "type_text": typ,
            "team_id": team, "p1": p[0], "p2": p[1], "p3": p[2], "home_score": hs, "away_score": as_,
            "shooting_play": shooting, "wallclock_utc": None}


def game_events():
    e = [
        ev(0, 1, 720.0, "Jumpball", H, (-5, -15, -1)),
        ev(1, 1, 690.0, "Jump Shot", H, (-1,), 2, 0, True),
        ev(2, 1, 360.0, "Substitution", H, (-6, -2), 2, 0),
        ev(3, 1, 300.0, "Jump Shot", A, (-11,), 2, 3, True),
        ev(4, 1, 0.0, "End Period", None, (), 2, 3),
        ev(5, 2, 600.0, "Jump Shot", H, (-6,), 4, 3, True),
        ev(6, 2, 360.0, "Substitution", H, (-7, -3), 4, 3),
        ev(7, 2, 0.0, "End Period", None, (), 4, 3),
        ev(8, 3, 0.0, "End Period", None, (), 4, 3),
        ev(9, 4, 0.0, "End Game", None, (), 4, 3),
    ]
    return e


def box_rows():
    mins = {-1: 48, -2: 6, -3: 18, -4: 48, -5: 48, -6: 42, -7: 30}
    pm = {-1: 1, -2: 2, -3: 1, -4: 1, -5: 1, -6: -1, -7: 0}
    rows = [{"game_id": "espn:1", "team_id": H, "nba_id": k, "starter": k in (-1, -2, -3, -4, -5),
             "did_not_play": False, "minutes": float(v), "plus_minus": pm[k]} for k, v in mins.items()]
    rows += [{"game_id": "espn:1", "team_id": A, "nba_id": k, "starter": True, "did_not_play": False,
              "minutes": 48.0, "plus_minus": -1} for k in (-11, -12, -13, -14, -15)]
    rows.append({"game_id": "espn:1", "team_id": A, "nba_id": -16, "starter": False, "did_not_play": True,
                 "minutes": 0.0, "plus_minus": None})
    return rows


GAME = {"game_id": "espn:1", "home_team_id": H, "away_team_id": A, "home_pts": 4, "away_pts": 3,
        "home_fga": 2, "home_fta": 0, "home_oreb": 0, "home_tov": 0,
        "away_fga": 1, "away_fta": 0, "away_oreb": 0, "away_tov": 0}


def test_clean_game_is_certified_strict():
    r = reconstruct_game(game_events(), box_rows(), GAME)
    assert r["checks"] == {k: True for k in r["checks"]}, r["reasons"]
    assert r["certified"] and r["certified_strict"]
    assert r["period_rules"]["2:H"] == "carryover" and r["period_rules"]["2:A"] == "carryover"
    assert r["player_seconds"][-7] == pytest.approx(30 * 60)
    assert r["player_seconds"][-2] == pytest.approx(6 * 60)
    assert r["metrics"]["team_stint_seconds"] == pytest.approx(48 * 60)
    assert r["metrics"]["pbp_possessions_home"] == 2 and r["metrics"]["pbp_possessions_away"] == 1


def test_period_start_inference_uses_first_appearance():
    team_of = {k: H for k in range(-7, 0)} | {k: A for k in range(-16, -10)}
    q2 = [e for e in game_events() if e["period"] == 2]
    prev = {H: {-1, -3, -4, -5, -6}, A: {-11, -12, -13, -14, -15}}
    st, rule = infer_period_start(q2, team_of, (H, A), prev)
    assert st[H] == {-1, -3, -4, -5, -6} and rule[H] == "carryover"
    # -6 is evidence (shot), -3 exits first (so started), -7 enters first (so did not start)
    st2, _ = infer_period_start(q2, team_of, (H, A), None)
    assert -7 not in st2[H] and {-6, -3} <= st2[H]


def test_ambiguous_period_start_fails_rather_than_guessing():
    evs = game_events()
    evs = [e for e in evs if e["order"] != 6]  # drop the Q2 substitution ...
    evs.insert(6, ev(6, 2, 180.0, "Jump Shot", H, (-7,), 4, 3, True))  # ... but -7 still appears
    r = reconstruct_game(evs, box_rows(), GAME)
    assert not r["certified"] and not r["checks"]["period_starts_ok"]
    assert any("ambiguous" in x for x in r["reasons"])


def test_missing_substitution_is_caught_by_offcourt_and_minutes():
    evs = game_events()
    evs[2] = ev(2, 1, 360.0, "Jump Shot", H, (-6,), 2, 0, True)  # -6 appears without having entered
    evs[2]["home_score"] = 2
    r = reconstruct_game(evs, box_rows(), GAME)
    assert not r["certified"]
    assert not r["checks"]["no_offcourt"] and not r["checks"]["minutes_ok"]


def test_score_and_plus_minus_mismatch_are_reported():
    g = dict(GAME, home_pts=5)
    b = box_rows()
    b[0]["plus_minus"] = 9
    r = reconstruct_game(game_events(), b, g)
    assert not r["checks"]["score_ok"] and not r["checks"]["plus_minus_ok"]


def test_technical_foul_is_not_evidence_of_presence():
    evs = game_events()
    evs.insert(6, ev(5.5, 2, 500.0, "Technical Foul", A, (-16,), 4, 3))  # bench player
    r = reconstruct_game(evs, box_rows(), GAME)
    assert r["checks"]["no_offcourt"] and r["certified"]


def test_turnover_and_possession_rules():
    assert is_turnover({"type_text": "Bad Pass\nTurnover"})
    assert is_turnover({"type_text": "Traveling"})
    assert not is_turnover({"type_text": "Kicked Ball"})  # defensive violation
    assert possession_team({"type_text": "Defensive Rebound", "team_id": A}) == A
    assert possession_team({"type_text": "Technical Free Throw", "team_id": A, "shooting_play": True}) is None
    assert possession_team({"type_text": "Personal Foul", "team_id": A}) is None


def _payload():
    play = {"id": "4011", "sequenceNumber": "4", "type": {"id": "584", "text": "Substitution"},
            "text": "B enters the game for C", "awayScore": 0, "homeScore": 0,
            "period": {"number": 1}, "clock": {"displayValue": "5:56"}, "scoringPlay": False, "scoreValue": 0,
            "team": {"id": "2"}, "participants": [{"athlete": {"id": "7"}}, {"athlete": {"id": "8"}}],
            "wallclock": "2025-11-13T00:21:50Z", "shootingPlay": False}
    athlete = {"athlete": {"id": "7", "displayName": "B"}, "starter": False, "didNotPlay": False,
               "stats": ["12", "4", "2-5", "0-1", "0-0", "3", "1", "0", "0", "0", "1", "2", "1", "-4"]}
    keys = ["minutes", "points", "fieldGoalsMade-fieldGoalsAttempted",
            "threePointFieldGoalsMade-threePointFieldGoalsAttempted", "freeThrowsMade-freeThrowsAttempted",
            "rebounds", "assists", "turnovers", "steals", "blocks", "offensiveRebounds", "defensiveRebounds",
            "fouls", "plusMinus"]
    return {
        "header": {"id": "1", "competitions": [{"status": {"type": {"completed": True}}, "competitors": [
            {"id": "2", "homeAway": "home", "score": "4", "team": {"id": "2", "abbreviation": "BOS"}},
            {"id": "18", "homeAway": "away", "score": "3", "team": {"id": "18", "abbreviation": "NY"}}]}]},
        "plays": [play, copy.deepcopy(play) | {"type": {"id": "16", "text": "Full Timeout"}, "participants": []}],
        "boxscore": {"players": [{"team": {"abbreviation": "BOS"}, "statistics": [{"keys": keys, "athletes": [athlete]}]}]},
    }


def test_parse_game_keeps_every_event_type_with_provenance():
    ev_rows, box, g = parse_game(_payload(), {"game_id": "espn:1", "event_id": "1", "season": "2025-26",
                                              "season_type": "regular"},
                                 fetched_at_utc="2026-10-11T00:00:00Z", source_url="u", from_cache=False,
                                 payload_sha256="x")
    assert [e["type_text"] for e in ev_rows] == ["Substitution", "Full Timeout"]
    assert ev_rows[0]["p1"] == -7 and ev_rows[0]["p2"] == -8 and ev_rows[0]["team_id"] == H
    assert ev_rows[0]["clock_s"] == pytest.approx(356.0)
    assert box[0]["minutes"] == 12.0 and box[0]["plus_minus"] == -4 and box[0]["nba_id"] == -7
    assert g["fetched_at_utc"] == "2026-10-11T00:00:00Z" and g["source"] == "espn/summary"
    assert g["home_team_id"] == H and g["away_team_id"] == A and g["n_substitutions"] == 1


def test_ingest_writes_compact_files_and_is_idempotent(tmp_path, monkeypatch):
    import json as _json
    from datetime import date

    import pandas as pd

    from nba_edge.data.http import Fetched
    from nba_edge.pbp import ingest

    board_game = {"event_id": "1", "game_id": "espn:1", "start_time_utc": "2025-11-13T00:00:00Z",
                  "season_type": "regular", "espn_season_type": 2}
    monkeypatch.setattr(ingest, "iter_season_dates", lambda s: iter([date(2025, 11, 12)]))
    monkeypatch.setattr(ingest, "fetch_json", lambda *a, **k: ({}, False))
    monkeypatch.setattr(ingest, "scoreboard_events", lambda b: [board_game])
    calls = []

    def fake_fetch(url, **k):
        calls.append(url)
        return Fetched(url, 200, _json.dumps(_payload()).encode(), "2026-10-11T00:00:00Z", False, 1)

    monkeypatch.setattr(ingest, "fetch", fake_fetch)
    man = ingest.run_full_pbp_pull(tmp_path, ["2025-26"], sleep_s=0)
    assert man["seasons"]["2025-26"]["games"] == 1 and man["seasons"]["2025-26"]["events"] == 2
    p = ingest.paths(tmp_path, "2025-26")
    g = pd.read_parquet(p["games"])
    assert g.loc[0, "fetched_at_utc"] == "2026-10-11T00:00:00Z" and len(g.loc[0, "payload_sha256"]) == 64
    ingest.run_full_pbp_pull(tmp_path, ["2025-26"], sleep_s=0)
    assert len(calls) == 1, "a re-run must not refetch an ingested game"
    assert len(pd.read_parquet(p["events"])) == 2


def test_free_throw_points_belong_to_the_lineup_at_the_foul():
    evs = game_events()
    # foul at 6:00, substitution (-6 for -2), then the free throw: the point belongs to the unit with -2
    evs.insert(2, ev(1.5, 1, 360.0, "Shooting Foul", A, (-11,), 2, 0))
    evs.insert(4, ev(2.5, 1, 360.0, "Free Throw - 1 of 1", H, (-1,), 3, 0, True))
    for e in evs[5:]:
        e["home_score"] += 1
    g = dict(GAME, home_pts=5)
    r = reconstruct_game(evs, box_rows(), g)
    first = r["stints"][0]
    assert -2 in [first[f"home_p{i}"] for i in range(1, 6)] and first["home_pts"] == 3
    assert sum(s["home_pts"] for s in r["stints"]) == 5
    assert r["checks"]["score_ok"]
