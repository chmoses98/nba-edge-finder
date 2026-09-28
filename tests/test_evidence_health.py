"""The daily dashboard must never let missing data look like zero data."""

from __future__ import annotations

import json
from datetime import UTC

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


def test_the_baseline_reports_even_when_evaluate_has_never_run(tmp_path):
    """The freeze holds or does not hold regardless of evaluation coverage.

    This was nested under the `evidence` section, whose fields are dropped when evaluate has not
    run -- so `frozen_parameters_intact` was invisible for the whole off-season, which is precisely
    when a silent parameter drift would go unnoticed longest.
    """
    report = EH.build_report(tmp_path)
    assert report["evidence"]["state"] == "absent", "evaluate genuinely has not run here"
    b = report["baseline"]
    assert b["state"] == "ok", b
    assert b["baseline_id"] == "NBA_BASELINE_2026_PRESEASON_V1"
    assert b["frozen_parameters_intact"] is True
    assert b["recorded_digest"] == b["live_digest"]


def test_a_drifted_parameter_would_report_as_not_intact(tmp_path, monkeypatch):
    """The signal has to be able to say NO, or reporting it proves nothing."""
    from nba_edge.baseline import manifest

    monkeypatch.setattr(manifest, "BASELINE_DIGEST", "0" * 64)
    assert EH.build_report(tmp_path)["baseline"]["frozen_parameters_intact"] is False


def test_every_section_carries_a_state_field(tmp_path):
    """The module promises `state` on every section; the worker section used to omit it."""
    import json as _json

    (tmp_path / "STATUS_worker.json").write_text(_json.dumps({"worker_id": "w1", "n_cycles": 3}))
    report = EH.build_report(tmp_path)
    for name, section in report.items():
        if name == "generated_at_utc" or not isinstance(section, dict):
            continue
        assert "state" in section, f"{name} has no state field"
    assert report["worker"]["state"] == "ok"
    assert report["worker"]["worker_id"] == "w1"


def test_delta_chain_integrity_is_on_the_daily_board(tmp_path):
    """Delta chains are now authoritative storage, so a broken one must surface daily."""
    from datetime import datetime, timedelta

    from nba_edge.archive.ledger import Ledger
    from nba_edge.archive.reconstruct import chain_tip, write_board

    t0 = datetime(2026, 10, 3, 18, 0, tzinfo=UTC)
    lg = Ledger(tmp_path, run_id="r1")
    rows = [{"ticker": f"T{i}", "yes_bid_dollars": "0.50"} for i in range(4)]
    write_board(lg, rows, observed_at=t0)
    changed = [dict(r) for r in rows]
    changed[0]["yes_bid_dollars"] = "0.60"
    write_board(lg, changed, observed_at=t0 + timedelta(minutes=10))

    assert EH.build_report(tmp_path)["delta_chains"]["state"] == "ok"

    _ck, deltas = chain_tip(lg)
    (tmp_path / deltas[0].path).unlink()
    broken = EH.build_report(tmp_path)["delta_chains"]
    assert broken["state"] == "broken"
    assert broken["n_broken"] == 1


def test_an_archive_with_no_deltas_reports_empty_not_broken(tmp_path):
    c = EH.build_report(tmp_path)["delta_chains"]
    assert c["state"] == "empty" and "reason" in c
