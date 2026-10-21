"""Issue #53 part A: the attribution table is derived from the archives, reconciles to the scorecard, and never fabricates a fill."""
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
PF = HERE.parent
sys.path.insert(0, str(PF))
sys.path.insert(0, str(HERE))
from issue53_synth import build_world  # noqa: E402
from nba.paper import attribution as A, evaluate as E  # noqa: E402

NOW = datetime(2026, 10, 24, tzinfo=timezone.utc)


@pytest.fixture(scope="module")
def arch(tmp_path_factory):
    d = tmp_path_factory.mktemp("a53")
    build_world(d / "pd")
    card = E.scorecard(str(d / "pd"), NOW, window=None, day_et="2026-10-20", prospective_only=True)
    E.write(str(d / "pd"), card)
    return str(d / "pd")


def test_table_is_the_scorecards_earliest_trade_per_thesis_not_a_per_horizon_pick(arch):
    t = A.attribute(arch, "2026-10-20", NOW)
    assert len(t) == 2 and set(t["horizon"]) == {"T-90"}                               # the same theses also traded at T-60 / T-30; the EARLIEST is kept
    assert all(h == ["T-90", "T-60", "T-30"] for h in t["also_traded_at_horizons"])
    assert (t["decision_mode"] == "asof_replay").all() and not t["contemporaneous_computation_evidence"].any()
    assert (t["computation_lag_s"] == 20 * 60).all()


def test_reconciles_to_the_archived_scorecard_exactly(arch):
    t = A.attribute(arch, "2026-10-20", NOW)
    rec = A.reconcile(arch, t, "2026-10-20")
    assert rec["matches_scorecard"] is True
    assert rec["recomputed"]["n_decisions"] == 2 and abs(rec["recomputed"]["entry_cost"] - t["price"].sum()) < 1e-12
    assert rec["matches_issue_text"] is False                                          # the synthetic world is not the opening night
    assert abs(rec["recomputed"]["roi"] - t["net_pnl"].sum() / t["price"].sum()) < 1e-12


def test_every_number_comes_from_the_archive_and_no_fill_is_invented(arch):
    t = A.attribute(arch, "2026-10-20", NOW)
    d = E.load(arch, NOW, day_et="2026-10-20").dec
    for r in t.to_dict("records"):
        src = d[d["decision_id"] == r["decision_id"]].iloc[0]
        assert r["price"] == src["price"] and r["p_model"] == src["p_model"] and r["net_pnl"] == src["net_pnl"] and r["as_of_utc"] == src["as_of_utc"]
        assert "no order" in r["fill_evidence"] and "no fill" in r["fill_evidence"]
        assert r["ticker"] and r["side"] in ("YES", "NO") and r["clv_valid"] in (True, False)
        assert r["archive"]["decision_file"] and r["archive"]["snapshot_file"] and r["archive"]["settlement_file"]
        assert r["forecast_archived_utc"] and r["forecast_generated_utc"]
    s = A.summarize(t)
    assert "no order exists" in s["evidence_gaps"]["fills"]
    assert s["evidence_gaps"]["contemporaneous_computation"].startswith("0 of 2")


def test_threshold_is_translated_into_plain_words():
    no = A.human_terms({"family": "player_points", "side": "NO", "k": 10, "threshold": 9.5, "player_name": "X"})
    yes = A.human_terms({"family": "player_pra", "side": "YES", "k": 30, "threshold": 29.5, "player_name": "Y"})
    assert "fewer than 10 points" in no and "at most 9" in no
    assert "30+" in yes and "at least 30" in yes
    assert "fewer than 2 made threes" in A.human_terms({"family": "player_threes", "side": "NO", "k": 2, "threshold": 1.5, "player_name": "Z"})


def test_summary_reports_side_and_player_structure(arch):
    t = A.attribute(arch, "2026-10-20", NOW)
    s = A.summarize(t)
    assert s["by_side"]["NO"]["n"] == 2 and s["overall"]["n"] == 2
    assert s["concentration"]["share_NO"] == 1.0 and s["concentration"]["n_games"] == 1
    md = A.to_markdown(t, A.reconcile(arch, t, "2026-10-20"), s, "2026-10-20")
    assert "## The seven selections" in md and "**asof_replay**" in md and "no fill" not in md.lower() or "recorded fill" in md


def test_board_archive_clock_is_attached_when_supplied(arch):
    t0 = A.attribute(arch, "2026-10-20", NOW)
    assert t0["board_committed_utc"].isna().all() and t0["board_commit_lag_s"].isna().all()               # not supplied -> not claimed
    obs = set(t0["board_observed_utc"])
    commits = {b: (pd.Timestamp(b) + pd.Timedelta(seconds=200)).strftime("%Y-%m-%dT%H:%M:%SZ") for b in obs}
    t = A.attribute(arch, "2026-10-20", NOW, board_commits=commits)
    assert (t["board_commit_lag_s"] == 200).all()
    assert "NOT_VERIFIED" in A.summarize(t0)["evidence_gaps"]["board_archive_clock"] and "200-200 s" in A.summarize(t)["evidence_gaps"]["board_archive_clock"]
