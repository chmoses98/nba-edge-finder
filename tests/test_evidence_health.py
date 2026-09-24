"""The daily dashboard must never let missing data look like zero data."""

from __future__ import annotations

import json

from nba_edge.ops import evidence_health as EH


def test_every_section_is_present_even_on_a_bare_archive(tmp_path):
    report = EH.build_report(tmp_path)
    for section in ("markets", "context", "simulation", "settlement", "evidence", "stint_data", "worker"):
        assert section in report, f"{section} must always be reported"


def test_a_missing_subsystem_reports_absent_with_a_reason(tmp_path):
    report = EH.build_report(tmp_path)
    for section in ("simulation", "settlement", "stint_data", "worker"):
        assert report[section]["state"] == "absent"
        assert report[section].get("reason"), f"{section} must say WHY it is absent"


def test_absent_is_distinguishable_from_zero(tmp_path):
    """The whole point: a dashboard of zeros must not read like a dashboard of data."""
    report = EH.build_report(tmp_path)
    assert report["stint_data"]["state"] == "absent"
    assert report["stint_data"]["n_games_available"] == 0
    # Both are present, and the state is what a reader must act on -- not the count.
    assert "reason" in report["stint_data"]


def test_known_phase_10_gaps_are_named_rather_than_omitted(tmp_path):
    ctx = EH.build_report(tmp_path)["context"]
    assert ctx["confirmed_starters"]["state"] == "absent"
    assert ctx["lineups"]["state"] == "absent"


def test_capture_status_is_surfaced_including_its_alarms(tmp_path):
    (tmp_path / "STATUS_capture.json").write_text(
        json.dumps(
            {
                "last_capture_utc": "2026-10-03T22:00:00Z",
                "n_markets": 3463,
                "n_series": 256,
                "by_support": {"MODELABLE": 6, "RESEARCH": 1484},
                "alarms": ["series on the board with no ontology entry: ['KXNEW']"],
            }
        )
    )
    m = EH.build_report(tmp_path)["markets"]
    assert m["state"] == "ok"
    assert m["n_discovered"] == 3463
    assert m["n_unresolved_alarms"] == 1
    assert "KXNEW" in m["alarms"][0]


def test_settlement_disagreements_are_surfaced(tmp_path):
    (tmp_path / "STATUS_settle.json").write_text(
        json.dumps(
            {
                "settled_at_utc": "2026-10-04T06:00:00Z",
                "n_games_checked": 5,
                "n_settlements_total": 120,
                "n_unsettleable": 2,
                "disagreements": ["KXNBAGAME-X: model says YES, box says NO"],
            }
        )
    )
    s = EH.build_report(tmp_path)["settlement"]
    assert s["state"] == "ok"
    assert s["n_unsettleable"] == 2
    assert len(s["disagreements"]) == 1


def test_the_report_is_json_serialisable(tmp_path):
    json.dumps(EH.build_report(tmp_path), default=str)


def test_run_writes_the_artifact(tmp_path):
    out = tmp_path / "nested" / "EVIDENCE_HEALTH.json"
    EH.run_evidence_health(tmp_path, out)
    assert json.loads(out.read_text())["markets"]["state"] == "absent"
