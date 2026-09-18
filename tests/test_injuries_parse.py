from datetime import UTC, datetime

from nba_edge.data.injuries import (
    candidate_pdf_urls,
    latest_report_slots,
    parse_espn_injuries,
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
