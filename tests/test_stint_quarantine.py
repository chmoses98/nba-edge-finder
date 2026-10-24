"""Uncertified lineup games are quarantined at the consumption boundary, and the dashboard reports what is actually on disk."""

from __future__ import annotations

import pandas as pd
import pytest

from nba_edge.ops import evidence_health as EH
from nba_edge.pbp.stints import UncertifiedStintsError, certified_only, load_certified, require_certified
from nba_edge.research.participation import OnOffIndex


def _stints(certified_games=("g1",), uncertified_games=("g2",)):
    rows = []
    for gid in (*certified_games, *uncertified_games):
        rows.append({"game_id": gid, "period": 1, "seconds": 720.0, "certified": gid in certified_games,
                     **{f"home_p{i}": i for i in range(1, 6)}, **{f"away_p{i}": 10 + i for i in range(1, 6)}})
    return pd.DataFrame(rows)


def test_certified_only_drops_uncertified_games_and_refuses_an_unflagged_frame():
    assert set(certified_only(_stints())["game_id"]) == {"g1"}
    with pytest.raises(UncertifiedStintsError):
        certified_only(_stints().drop(columns="certified"))


def test_on_off_index_refuses_uncertified_stints():
    """Regression: from_stints documented 'certified stint rows' but accepted the raw file, 89.9-95.6% of whose uncertified games look perfectly healthy."""
    info = pd.DataFrame({"game_id": ["g1", "g2"], "game_date_et": ["2026-01-01", "2026-01-02"], "home_team_id": [1, 1], "away_team_id": [2, 2]})
    with pytest.raises(UncertifiedStintsError):
        OnOffIndex.from_stints(_stints(), info)
    OnOffIndex.from_stints(certified_only(_stints()), info)  # the sanctioned path works


def test_require_certified_is_a_no_op_for_a_frame_that_is_all_certified():
    require_certified(_stints(uncertified_games=()))


def test_dashboard_reports_historical_stints_instead_of_a_hard_coded_absent(tmp_path):
    base = tmp_path / "data" / "history" / "espn_pbp"
    base.mkdir(parents=True)
    _stints(("a", "b", "c"), ("d",)).to_parquet(base / "stints_2025-26.parquet")
    sec = EH.stint_section(tmp_path / "data")
    assert sec["state"] == "historical_only" and sec["n_games_available"] == 3 and sec["n_quarantined_games"] == 1 and sec["n_games_with_stints"] == 4
    assert "no 2026-27 pipeline" in sec["reason"]
    assert load_certified(base / "stints_2025-26.parquet")["game_id"].nunique() == 3


def test_dashboard_still_says_absent_when_there_is_nothing_on_disk(tmp_path):
    assert EH.stint_section(tmp_path)["state"] == "absent"
    assert EH.build_report(tmp_path)["stint_data"]["state"] == "absent"
