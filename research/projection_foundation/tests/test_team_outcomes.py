"""Team outcomes (points, quarter scores, possessions) archived by the results stage from the same ESPN summary as the player outcomes."""
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PF = HERE.parent
REPO = PF.parent.parent
sys.path.insert(0, str(PF))
from nba.live import results as RES  # noqa: E402
from nba.paper import schema as S, store as PS  # noqa: E402


@pytest.fixture(scope="module")
def hist():
    spec = importlib.util.spec_from_file_location("repo_test_history", REPO / "tests" / "test_history.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_team_rows_ride_along_with_the_player_box(hist):
    box = RES.box_rows(hist.SUMMARY_1, hist.META_1)
    tr = box.attrs["team_rows"]
    assert len(tr) == 2 and {t["home"] for t in tr} == {True, False}
    game = {"game_id": "espn:1", "start_utc": "2026-10-20T23:00:00Z", "game_date_et": "2026-10-20"}
    rows = RES.team_outcome_rows(game, tr, "2026-10-21T10:40:00Z", "espn_summary_final")
    assert len(rows) == 2 and all(r["schema"] == S.TEAM_OUTCOME_SCHEMA and r["final"] for r in rows)
    a, b = rows
    assert a["pts"] == b["opp_pts"] and a["margin"] == -b["margin"] and a["total"] == b["total"] == a["pts"] + b["pts"]
    assert a["q1"] + a["q2"] + a["q3"] + a["q4"] + a["ot_pts"] == a["pts"]
    assert a["possessions"] and a["outcome_key"] != b["outcome_key"]


def test_team_outcomes_are_written_once_and_unchanged_reruns_add_nothing(hist, tmp_path):
    box = RES.box_rows(hist.SUMMARY_1, hist.META_1)
    game = {"game_id": "espn:1", "start_utc": "2026-10-20T23:00:00Z", "game_date_et": "2026-10-20"}
    rows = RES.team_outcome_rows(game, box.attrs["team_rows"], "2026-10-21T10:40:00Z", "x")
    now = datetime(2026, 10, 21, 10, 40, tzinfo=timezone.utc)
    w1 = PS.write_new(str(tmp_path), "team_outcomes", "2026-10-20", rows, "outcome_key", now)
    w2 = PS.write_new(str(tmp_path), "team_outcomes", "2026-10-20", [dict(r, observed_utc="2026-10-21T11:00:00Z") for r in rows],
                      "outcome_key", now.replace(hour=11))
    assert (w1["written"], w2["written"], w2["duplicates"]) == (2, 0, 2)
    assert len(PS.read(str(tmp_path), "team_outcomes")) == 2
