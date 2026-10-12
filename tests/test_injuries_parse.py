import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest

from nba_edge.data import injuries
from nba_edge.data.http import Fetched
from nba_edge.data.injuries import (
    InjuryReportParseError,
    candidate_pdf_urls,
    extract_pdf_text,
    fetch_official_injury_report,
    latest_report_slots,
    parse_espn_injuries,
    parse_injury_report_pdf,
    parse_injury_report_text,
)
from nba_edge.schemas.core import InjuryStatus
from nba_edge.timeutil import ET

SAMPLE = """Injury Report: 12/26/25 06:00 PM Page 1 of 8
Game Date Game Time Matchup Team Player Name Current Status Reason
12/26/2025 07:00 (ET) BOS@NYK Boston Celtics Tatum, Jayson Out Injury/Illness - Right Achilles; Repair
Holiday, Jrue Questionable Injury/Illness - Left Knee; Soreness
Porzingis, Kristaps Probable Injury/Illness - Illness
New York Knicks Brunson, Jalen Available Injury/Illness - Right Ankle; Sprain
Robinson, Mitchell Out Injury/Illness - Left Ankle; Surgery
12/26/2025 10:00 (ET) LAL@LAC Los Angeles Lakers James, LeBron Doubtful Injury/Illness - Left Foot; Soreness
LA Clippers NOT YET SUBMITTED
"""


def test_parse_official_report_text():
    ts = datetime(2025, 12, 26, 23, 0, tzinfo=UTC)
    rows = parse_injury_report_text(SAMPLE, ts)
    by = {r.player_name_raw: r for r in rows}
    assert by["Jayson Tatum"].status == InjuryStatus.OUT and by["Jayson Tatum"].team_id == 1610612738
    assert by["Jrue Holiday"].status == InjuryStatus.QUESTIONABLE
    assert by["Kristaps Porzingis"].status == InjuryStatus.PROBABLE
    assert by["Jalen Brunson"].team_id == 1610612752 and by["Jalen Brunson"].status == InjuryStatus.AVAILABLE
    assert by["Mitchell Robinson"].status == InjuryStatus.OUT
    assert by["LeBron James"].team_id == 1610612747 and by["LeBron James"].status == InjuryStatus.DOUBTFUL
    assert all(r.game_date_et == "2025-12-26" for r in rows)
    assert all(r.source == "nba_official_pdf" for r in rows)
    assert "Achilles" in by["Jayson Tatum"].reason


def test_candidate_urls_new_and_old_formats():
    t = datetime(2025, 12, 26, 18, 0, tzinfo=ET)
    urls = candidate_pdf_urls(t)
    assert urls[0].endswith("Injury-Report_2025-12-26_06_00PM.pdf")
    assert urls[1].endswith("Injury-Report_2025-12-26_06PM.pdf")
    t2 = datetime(2025, 12, 26, 11, 45, tzinfo=ET)
    assert candidate_pdf_urls(t2) == ["https://ak-static.cms.nba.com/referee/injury/Injury-Report_2025-12-26_11_45AM.pdf"]


def test_latest_slots_are_15_minute_grid_descending():
    slots = latest_report_slots(datetime(2025, 12, 26, 23, 7, tzinfo=UTC), lookback_hours=1)
    assert len(slots) == 4 and slots[0].minute == 0 and slots[1].minute == 45
    assert all(s.tzinfo is not None for s in slots)


def test_parse_espn_injuries():
    payload = {"injuries": [{"displayName": "Boston Celtics", "injuries": [{"status": "Out", "athlete": {"displayName": "Jayson Tatum"}, "details": {"type": "Achilles"}}, {"status": "Day-To-Day", "athlete": {"displayName": "Jrue Holiday"}, "details": {"type": "Knee"}}]}, {"displayName": "Not A Team", "injuries": []}]}
    rows = parse_espn_injuries(payload, datetime(2025, 12, 26, 23, 0, tzinfo=UTC))
    assert len(rows) == 2 and rows[0].status == InjuryStatus.OUT and rows[1].status == InjuryStatus.QUESTIONABLE
    assert rows[0].team_id == 1610612738 and rows[0].reason == "Achilles"


# ---- real official report PDF (regression: the line-based parser returned 0 rows on every real report) ----
# tests/fixtures/injury_reports/Injury-Report_2026-04-25_06_00PM.pdf is the unmodified file published at
# https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-04-25_06_00PM.pdf
# (sha256 f3c81172a287fa21cf8c6e5627bd3f3204763fc1b2f5cf5e708c8cfef1ea6895): 2 pages, 6 games, 20 player rows,
# SAS@POR both teams NOT YET SUBMITTED.
FIXTURE_PDF = Path(__file__).parent / "fixtures" / "injury_reports" / "Injury-Report_2026-04-25_06_00PM.pdf"
SLOT_UTC = datetime(2026, 4, 25, 22, 0, tzinfo=UTC)  # 06:00 PM ET (EDT)
ORL, OKC, PHX, PHI, HOU, SAS, POR = 1610612753, 1610612760, 1610612756, 1610612755, 1610612745, 1610612759, 1610612757


def test_fixture_is_the_published_file():
    assert hashlib.sha256(FIXTURE_PDF.read_bytes()).hexdigest() == "f3c81172a287fa21cf8c6e5627bd3f3204763fc1b2f5cf5e708c8cfef1ea6895"


def test_parse_real_official_report_pdf():
    rows, meta = parse_injury_report_pdf(FIXTURE_PDF.read_bytes(), SLOT_UTC)
    assert len(rows) == 20 and meta["n_player_rows"] == 20 and meta["n_dropped_no_team"] == 0
    assert meta["pages"] == 2 and meta["header_time_et"] == "2026-04-25 06:00 PM"
    by = {r.player_name_raw: r for r in rows}
    assert by["Jonathan Isaac"].team_id == ORL and by["Jonathan Isaac"].status == InjuryStatus.OUT
    assert by["Jalen Williams"].team_id == OKC and by["Jalen Williams"].reason == "Injury/Illness - Left Hamstring; Strain"
    assert by["Grayson Allen"].team_id == PHX and by["Grayson Allen"].status == InjuryStatus.AVAILABLE
    assert by["Joel Embiid"].team_id == PHI and by["Joel Embiid"].status == InjuryStatus.DOUBTFUL
    assert by["Kevin Durant"].team_id == HOU and by["Kevin Durant"].status == InjuryStatus.QUESTIONABLE
    assert by["Kelly Oubre Jr."].team_id == PHI  # 'Oubre Jr., Kelly' -> display order, suffix kept
    # reasons that wrap onto a second printed line are re-attached to their row
    assert by["Mark Williams"].reason == "Injury/Illness - Left Foot Third Metatarsal; Stress Reaction"
    assert by["Tyrese Maxey"].reason == "Injury/Illness - Right Finger; Tendon Strain - Splint"
    # game date carries forward across rows and pages
    assert by["Jonathan Isaac"].game_date_et == "2026-04-25" and by["Fred VanVleet"].game_date_et == "2026-04-26"
    assert {r.status for r in rows} == {InjuryStatus.OUT, InjuryStatus.QUESTIONABLE, InjuryStatus.DOUBTFUL, InjuryStatus.AVAILABLE}
    assert sum(r.status == InjuryStatus.OUT for r in rows) == 12
    assert all(r.source == "nba_official_pdf" and r.report_time_utc == SLOT_UTC for r in rows)
    assert meta["not_yet_submitted"] == [f"SAS@POR:{POR}", f"SAS@POR:{SAS}"]
    assert not any(r.team_id in (SAS, POR) for r in rows)


def test_line_parser_on_real_extracted_text_fails_loudly():
    """Root cause: pypdf's plain extract_text emits one token per line for these PDFs, so the line-based parser
    finds nothing. It must raise, not return []."""
    text = extract_pdf_text(FIXTURE_PDF.read_bytes())
    assert text.splitlines()[:3] == ["Injury", "Report:", "04/25/26"]
    with pytest.raises(InjuryReportParseError, match="0 rows"):
        parse_injury_report_text(text, SLOT_UTC)


def test_line_parser_empty_or_status_free_text_is_not_an_error():
    assert parse_injury_report_text("", SLOT_UTC) == []
    assert parse_injury_report_text("Injury Report: 04/25/26 06:00 PM\nLA Clippers NOT YET SUBMITTED\n", SLOT_UTC) == []


def test_pdf_parser_raises_when_rows_present_but_none_survive(monkeypatch):
    """A non-empty report that yields zero entries (here: team names stop resolving) must raise."""
    monkeypatch.setattr(injuries, "_team_name_index", lambda: {})
    with pytest.raises(InjuryReportParseError, match="20 player rows but produced 0 entries"):
        parse_injury_report_pdf(FIXTURE_PDF.read_bytes(), SLOT_UTC)


def test_pdf_parser_raises_when_layout_header_is_lost(monkeypatch):
    words = [w for w in injuries._extract_words(FIXTURE_PDF.read_bytes()) if w.text not in ("Matchup", "Player")]
    monkeypatch.setattr(injuries, "_extract_words", lambda b: words)
    with pytest.raises(InjuryReportParseError, match="no column header"):
        parse_injury_report_pdf(FIXTURE_PDF.read_bytes(), SLOT_UTC)


def test_fetch_official_injury_report_parses_real_pdf(monkeypatch):
    pdf = FIXTURE_PDF.read_bytes()
    seen = []

    def fake_fetch(url, **kw):
        seen.append(url)
        return Fetched(url=url, status=200, content=pdf, fetched_at_utc="2026-04-25T22:01:00Z", from_cache=False, elapsed_ms=1)

    monkeypatch.setattr(injuries, "fetch", fake_fetch)
    entries, prov = fetch_official_injury_report(datetime(2026, 4, 25, 18, 0, tzinfo=ET))
    assert seen == ["https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-04-25_06_00PM.pdf"]
    assert len(entries) == 20 and prov["n"] == 20 and prov["n_player_rows"] == 20 and not prov.get("missing")
    assert prov["header_time_et"] == "2026-04-25 06:00 PM" and len(prov["not_yet_submitted"]) == 2


def test_fetch_stamps_rows_with_pdf_header_time_when_slot_differs(monkeypatch):
    """Older hourly files were filed under a slot that is not the report time; the PDF header wins."""
    pdf = FIXTURE_PDF.read_bytes()
    monkeypatch.setattr(injuries, "fetch", lambda url, **kw: Fetched(url, 200, pdf, "2026-04-25T22:01:00Z", False, 1))
    entries, _ = fetch_official_injury_report(datetime(2026, 4, 25, 17, 45, tzinfo=ET))
    assert {e.report_time_utc for e in entries} == {SLOT_UTC}


def test_fetch_propagates_parse_failure(monkeypatch):
    pdf = FIXTURE_PDF.read_bytes()
    monkeypatch.setattr(injuries, "fetch", lambda url, **kw: Fetched(url, 200, pdf, "2026-04-25T22:01:00Z", False, 1))
    monkeypatch.setattr(injuries, "_team_name_index", lambda: {})
    with pytest.raises(InjuryReportParseError):
        fetch_official_injury_report(datetime(2026, 4, 25, 18, 0, tzinfo=ET))
