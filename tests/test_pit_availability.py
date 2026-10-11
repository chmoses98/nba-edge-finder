"""Point-in-time availability: identity mapping, append-only capture store, PIT verification, and the
official-report parser on real report PDFs committed as fixtures."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from nba_edge.availability import capture
from nba_edge.availability.backfill import verify_snapshots
from nba_edge.availability.identity import PlayerIndex, report_name_to_display
from nba_edge.availability.official_report import report_url, slot_floor
from nba_edge.timeutil import ET

FIX = Path(__file__).parent / "fixtures" / "injury_reports"


def test_report_url_and_slot_grid():
    t = datetime(2026, 1, 15, 17, 44, tzinfo=ET)
    assert slot_floor(t) == datetime(2026, 1, 15, 17, 30, tzinfo=ET)
    assert report_url(slot_floor(t)).endswith("Injury-Report_2026-01-15_05_30PM.pdf")


def test_name_resolution_tiers_and_no_guessing():
    pg = pd.DataFrame([
        {"game_id": "espn:1", "team_id": 1, "nba_id": -10, "player_name": "Scotty Pippen Jr."},
        {"game_id": "espn:2", "team_id": 1, "nba_id": -11, "player_name": "Jalen Green"},
        {"game_id": "espn:2", "team_id": 2, "nba_id": -12, "player_name": "Jalen Green"},
        {"game_id": "espn:3", "team_id": 3, "nba_id": -13, "player_name": "Nikola Jokić"},
    ])
    idx = PlayerIndex.from_player_games(pg)
    assert report_name_to_display("Pippen Jr.,Scotty") == "Scotty Pippen Jr."
    assert idx.resolve(1, "Pippen Jr.,Scotty", "espn:1") == (-10, "game_box")
    assert idx.resolve(1, "Green, Jalen") == (-11, "team_season")
    assert idx.resolve(9, "Green, Jalen") == (None, "ambiguous")  # two Jalen Greens, wrong team: no guess
    assert idx.resolve(9, "Jokic, Nikola") == (-13, "season_any_team")
    assert idx.resolve(1, "Nobody, Some") == (None, "unmatched")


def test_capture_store_is_write_once_and_hash_chained(tmp_path):
    sha = capture._write_once(tmp_path / "a/x.jsonl.gz", [{"a": 1}])
    capture._append_manifest(tmp_path, {"path": "a/x.jsonl.gz", "sha256": sha})
    sha2 = capture._write_once(tmp_path / "a/y.jsonl.gz", [{"b": 2}])
    capture._append_manifest(tmp_path, {"path": "a/y.jsonl.gz", "sha256": sha2})
    assert capture.verify_chain(tmp_path)["files"] == 2
    with pytest.raises(FileExistsError):
        capture._write_once(tmp_path / "a/x.jsonl.gz", [{"a": 2}])
    (tmp_path / "a/x.jsonl.gz").write_bytes(b"tampered")
    with pytest.raises(AssertionError, match="modified"):
        capture.verify_chain(tmp_path)
    (tmp_path / "a/x.jsonl.gz").unlink()
    with pytest.raises(AssertionError, match="deleted"):
        capture.verify_chain(tmp_path)


def test_snapshot_is_pit_ok_only_if_published_before_tip():
    snaps = pd.DataFrame([{"game_id": "g1", "tip_utc": "2026-01-16T00:00:00Z", "last_pre_tip_slot_et": "2026-01-15T18:30",
                           "t_minus_60_slot_et": "2026-01-15T18:00"}])
    reports = pd.DataFrame([
        {"slot_et": "2026-01-15T18:30", "report_time_utc": "2026-01-15T23:30:00Z", "last_modified_utc": "2026-01-16T00:01:00Z"},
        {"slot_et": "2026-01-15T18:00", "report_time_utc": "2026-01-15T23:00:00Z", "last_modified_utc": "2026-01-15T23:02:00Z"},
    ])
    rows = pd.DataFrame([{"slot_et": s, "game_id": "g1", "team_id": t} for s in ("2026-01-15T18:30", "2026-01-15T18:00")
                         for t in (1, 2)])
    out = verify_snapshots(snaps, reports, rows).iloc[0]
    assert out["last_pre_tip_nominal_before_tip"] and not out["last_pre_tip_published_before_tip"]
    assert not out["last_pre_tip_pit_ok"], "a report uploaded after the tip must never be attached to the game"
    assert out["t_minus_60_pit_ok"] and out["t_minus_60_lead_minutes"] == 60.0


def test_espn_rows_take_the_athlete_id_from_the_player_card_link():
    payload = {"injuries": [{"id": "1", "displayName": "Atlanta Hawks", "injuries": [
        {"status": "Out", "date": "2026-10-10T21:34Z", "athlete": {"displayName": "K G", "links": [
            {"href": "https://www.espn.com/nba/player/_/id/4585618/k-g"}]}}]}]}
    r = capture.espn_rows(payload, "2026-10-11T00:00:00Z")[0]
    assert r["nba_id"] == -4585618 and r["entry_date_utc"] == "2026-10-10T21:34Z"


def _parse_fixture(name: str, slot: datetime):
    from nba_edge.availability.official_report import parse_report_pdf

    return parse_report_pdf((FIX / name).read_bytes(), slot)


def test_real_report_parses_every_row_with_team_game_and_reason():
    rows, meta = _parse_fixture("Injury-Report_2026-01-15_05_30PM.pdf", datetime(2026, 1, 15, 17, 30, tzinfo=ET))
    assert meta["n_pages"] == 10 and meta["n_player_rows"] == 151 and meta["n_not_yet_submitted"] == 4
    assert meta["rows_missing_team"] == 0 and meta["rows_missing_game"] == 0 and not meta["unresolved_team_text"]
    assert meta["report_time_et"] == "2026-01-15T17:30:00-05:00"
    first = rows[0]
    assert (first["player_name_raw"], first["status"], first["away_tricode"], first["home_tricode"]) == (
        "Clarke, Brandon", "out", "MEM", "ORL")
    assert first["reason"] == "Injury/Illness - Right Calf; Strain"
    edey = next(r for r in rows if r["player_name_raw"] == "Edey, Zach")
    assert edey["reason"] == "Injury/Illness - Left Ankle; Stress Reaction"  # wrapped above + below the row
    assert any(r["player_name_raw"] == "Hayes-Davis, Nigel" for r in rows)  # hyphen split across fragments
    statuses = {r["status"] for r in rows}
    assert {"out", "questionable", "probable", "available", "not_yet_submitted"} <= statuses


def test_early_report_marks_teams_not_yet_submitted():
    rows, meta = _parse_fixture("Injury-Report_2026-01-15_12_00PM.pdf", datetime(2026, 1, 15, 12, 0, tzinfo=ET))
    nys = [r for r in rows if r["status"] == "not_yet_submitted"]
    assert len(nys) == meta["n_not_yet_submitted"] == 15
    assert all(r["player_name_raw"] is None and r["team_id"] is not None for r in nys)


def test_legacy_line_parser_finds_nothing_in_current_layout():
    """Documents why a positional parser was needed: the existing line-based parser returns 0 rows on
    a real 2025-26 report (151 player rows), because plain text extraction emits one token per line."""
    from datetime import UTC

    from nba_edge.data.injuries import extract_pdf_text, parse_injury_report_text

    text = extract_pdf_text((FIX / "Injury-Report_2026-01-15_05_30PM.pdf").read_bytes())
    assert parse_injury_report_text(text, datetime(2026, 1, 15, 22, 30, tzinfo=UTC)) == []
