"""Regression: an official injury PDF spans multiple game dates and not-yet-submitted clubs."""
from nba_edge.schemas.core import InjuryStatus
from nba_edge.workflows.simulate import injuries_by_team


class _Names:
    def __init__(self, entries):
        self.entries = entries

    def resolve_name(self, name, tid):
        return self.entries.get((tid, name))


def _row(tid, name, status, source, date="2026-11-11"):
    return {
        "team_id": tid,
        "player_name_raw": name,
        "status": status,
        "source": source,
        "game_date_et": date,
    }


def test_official_current_game_wins_espn_and_next_day():
    names = _Names({(1, "Starter"): 101, (2, "Forward"): 202})
    rows = [
        _row(1, "Starter", "out", "nba_official_pdf"),
        _row(1, "Starter", "available", "nba_official_pdf", "2026-11-12"),
        _row(1, "Starter", "available", "espn_injuries"),
        _row(2, "Forward", "out", "espn_injuries"),
    ]
    result, provenance = injuries_by_team(
        rows, names, target_date="2026-11-11", espn_fallback_team_ids={2},
    )
    assert result[1][101] == InjuryStatus.OUT
    assert result[2][202] == InjuryStatus.OUT
    assert provenance["source"] == "official"
    assert provenance["espn_fallback_teams"] == [2]


def test_espn_not_used_for_a_team_with_official_submission():
    names = _Names({(1, "Starter"): 101, (2, "Forward"): 202})
    rows = [
        _row(1, "Starter", "available", "nba_official_pdf"),
        _row(1, "Starter", "out", "espn_injuries"),
        _row(2, "Forward", "out", "espn_injuries"),
    ]
    result, provenance = injuries_by_team(
        rows, names, target_date="2026-11-11", espn_fallback_team_ids={1},
    )
    assert result[1][101] == InjuryStatus.AVAILABLE
    assert 2 not in result
    assert provenance["espn_fallback_teams"] == []


def test_future_official_report_not_used_for_tonights_game():
    names = _Names({(1, "Starter"): 101})
    rows = [
        _row(1, "Starter", "out", "nba_official_pdf", "2026-11-12"),
        _row(1, "Starter", "questionable", "espn_injuries"),
    ]
    result, provenance = injuries_by_team(rows, names, target_date="2026-11-11")
    assert result[1][101] == InjuryStatus.QUESTIONABLE
    assert provenance["source"] == "espn"


def test_unresolved_official_out_is_still_reported():
    names = _Names({})
    result, provenance = injuries_by_team(
        [_row(1, "Missing Star", "out", "nba_official_pdf")],
        names, target_date="2026-11-11",
    )
    assert result == {}
    assert provenance["unresolved_official_out_by_team"] == {1: ["Missing Star"]}
