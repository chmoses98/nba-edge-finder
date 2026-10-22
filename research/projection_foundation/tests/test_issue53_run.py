"""Issue #53 end to end: the research run is read-only, deterministic, labels retrospective vs prospective, and reports NO_DATA instead of forcing results."""
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PF = HERE.parent
sys.path.insert(0, str(PF))
sys.path.insert(0, str(HERE))
from issue53_synth import build_world  # noqa: E402
from nba.paper import study53  # noqa: E402


def tree_digest(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(root)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    d = tmp_path_factory.mktemp("run53")
    build_world(d / "pd", d / "msa", ratio=1.5)
    return d


def test_run_is_read_only_deterministic_and_never_places_orders(world, tmp_path):
    before = (tree_digest(world / "pd"), tree_digest(world / "msa"))
    m1 = study53.run(str(world / "pd"), str(world / "msa"), str(tmp_path / "o1"), "2026-10-20")
    m2 = study53.run(str(world / "pd"), str(world / "msa"), str(tmp_path / "o2"), "2026-10-20")
    assert (tree_digest(world / "pd"), tree_digest(world / "msa")) == before                    # neither data branch is touched
    assert tree_digest(tmp_path / "o1") == tree_digest(tmp_path / "o2") and m1["run_id"] == m2["run_id"]
    assert m1["read_only"] is True and m1["network"] is False and m1["orders_placed"] == 0 and m1["workflows_dispatched"] == 0
    assert set(os.listdir(tmp_path / "o1")) >= {"SUMMARY.md", "exec_shadow.json", "jrm_matched.json", "attribution_2026-10-20.json", "attribution_2026-10-20.md", "manifest.json"}


class Early(dict):
    def get(self, key, default=None):
        return "2000-01-01T00:00:00Z"


def test_three_separately_labelled_sets_and_honest_evidence_status(world, tmp_path, monkeypatch):
    monkeypatch.setattr(study53, "build_clocks", lambda *a, **k: ({"board_commit": Early(), "forecast_commit": Early()}, {"status": "VERIFIED", "synthetic": True}))
    study53.run(str(world / "pd"), str(world / "msa"), str(tmp_path / "o"), "2026-10-20")
    man = json.load(open(tmp_path / "o" / "manifest.json"))
    tw = man["three_way"]
    assert set(tw) == {"1_original_frozen_strategy_selection", "2_new_fixed_checkpoint_executable_shadow", "3_eligible_matched_jrm_whatif"}
    assert "NOT simultaneously executable" in tw["1_original_frozen_strategy_selection"]["label"]
    assert "RETROSPECTIVE" in tw["2_new_fixed_checkpoint_executable_shadow"]["label"] and "RETROSPECTIVE" in tw["3_eligible_matched_jrm_whatif"]["label"]
    B = json.load(open(tmp_path / "o" / "exec_shadow.json"))
    assert B["retrospective_descriptive"]["status"] == "OK" and B["prospective"]["status"] == "NO_DATA"      # no sealed ledger: reconstruction is never prospective
    assert B["progress_to_evidence_minimums"]["prospective_decisions"] == 0 and B["progress_to_evidence_minimums"]["prospective_games"] == 0
    assert B["progress_to_evidence_minimums"]["retrospective_rows_never_counted"] is True
    games = {g["game_id"]: g for g in B["games"]}
    assert games["espn:7003"]["status"] == "NO_TRADE" and "GAP_TOO_LARGE" in games["espn:7003"]["reason"]
    assert B["no_trade_examples"] and all(e["decision"] == "NO_TRADE" for e in B["no_trade_examples"])
    assert B["contemporaneous_crosscheck"]["status"] == "NO_DATA"                                           # the synthetic world has no contemporaneous run
    C = json.load(open(tmp_path / "o" / "jrm_matched.json"))
    assert C["status"] == "OK" and C["downstream"] == "archive_scale_approximation" and C["prospective_gate"]["status"] == "NO_DATA"
    assert set(C["matching"]["games"]) == {"espn:7001", "espn:7002"} and all(v["reason"] == "OK" for v in C["matching"]["games"].values())
    assert [r["reason"] for r in C["snapshots_rejected"]] == ["REGISTER_NOT_ELIGIBLE"]
    summary = (tmp_path / "o" / "SUMMARY.md").read_text()
    assert "Research only" in summary and "RETROSPECTIVE" in summary \
        and not re.search(r"\b(profitable|validated|proven)\b", summary.lower())


def test_without_a_jrm_archive_the_comparison_is_no_data_not_forced(world, tmp_path):
    study53.run(str(world / "pd"), None, str(tmp_path / "o"), "2026-10-20")
    C = json.load(open(tmp_path / "o" / "jrm_matched.json"))
    assert C["status"] == "NO_DATA" and "not provided" in C["reason"]


def test_a_changed_original_protocol_stops_the_run(world, tmp_path, monkeypatch):
    from nba.paper import exec_shadow as X
    monkeypatch.setattr(X, "base_protocol_ok", lambda study: (False, "paper_config.json edited"))
    with pytest.raises(SystemExit):
        study53.run(str(world / "pd"), None, str(tmp_path / "o"), "2026-10-20")


def test_without_independent_clocks_nothing_is_prospective_and_it_is_reported(world, tmp_path):
    study53.run(str(world / "pd"), str(world / "msa"), str(tmp_path / "o"), "2026-10-20")
    B = json.load(open(tmp_path / "o" / "exec_shadow.json"))
    assert B["independent_clocks"]["status"] == "NOT_VERIFIED"
    assert B["prospective"]["status"] == "NO_DATA" and B["progress_to_evidence_minimums"]["prospective_decisions"] == 0
    assert B["retrospective_descriptive"]["evidence_status"]["independent_clocks_verified"] is False


def test_regression_study53_run_the_day_after_a_final_game_cannot_create_a_prospective_selection(world, tmp_path, monkeypatch):
    """Owner review of PR #54: upstream paper decisions carry a pre-tip decided_utc (after the frozen start) but study53 first runs AFTER the game. The reconstructed
    new-strategy portfolio must NOT be prospective; with no sealed pre-tip artifact the prospective result is NO_DATA."""
    from nba.paper import exec_shadow as X2
    real = X2.load_study
    def early_start(path=None):
        s = real(path)
        s["prospective_start_utc"] = "2026-10-22T00:00:00Z"                                      # make game 7002 (tip 2026-10-23T00:00Z) 'after the start'
        return s
    monkeypatch.setattr(X2, "load_study", early_start)
    monkeypatch.setattr(study53, "build_clocks", lambda *a, **k: ({"board_commit": Early(), "forecast_commit": Early()}, {"status": "VERIFIED", "synthetic": True}))
    from datetime import datetime, timezone
    now = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)                                     # the day after the last final game
    study53.run(str(world / "pd"), str(world / "msa"), str(tmp_path / "o"), "2026-10-20", now=now)
    B = json.load(open(tmp_path / "o" / "exec_shadow.json"))
    g2 = [t for t in B["trades"] if t["game_id"] == "espn:7002"]
    assert g2 and all(t["prospective"] is False for t in B["trades"])                            # the reconstruction does contain game 7002's selections ...
    assert B["prospective"]["status"] == "NO_DATA" and B["progress_to_evidence_minimums"]["prospective_decisions"] == 0      # ... but none is prospective
    assert B["sealed_ledger"]["status"] == "NOT_SUPPLIED"


def test_empty_or_unsettled_states_report_no_data_instead_of_crashing(tmp_path):
    from nba.paper import store
    empty = tmp_path / "empty"
    empty.mkdir()
    man = study53.run(str(empty), None, str(tmp_path / "o_empty"), "2026-10-20")                 # nothing archived at all
    assert (tmp_path / "o_empty" / "SUMMARY.md").exists() and man["orders_placed"] == 0
    A_ = json.load(open(tmp_path / "o_empty" / "attribution_2026-10-20.json"))
    assert A_["reconciliation"]["status"] == "NO_DATA" and A_["summary"]["status"] == "NO_DATA"
    assert "NO_DATA" in (tmp_path / "o_empty" / "SUMMARY.md").read_text()
    # trades exist but nothing is settled yet (the normal state before the first final whistle)
    d = tmp_path / "w"
    d.mkdir()
    build_world(d / "pd", d / "msa")
    for p in (d / "pd" / "paper" / "nba" / "settlements").rglob("*.jsonl.gz"):
        p.unlink()
    study53.run(str(d / "pd"), str(d / "msa"), str(tmp_path / "o_unsettled"), "2026-10-20")
    B = json.load(open(tmp_path / "o_unsettled" / "exec_shadow.json"))
    o = B["retrospective_descriptive"]["overall"]
    assert o["n_trades"] > 0 and o["n_settled"] == 0 and o["total_net_pnl"] is None
    assert "n/a" in (tmp_path / "o_unsettled" / "SUMMARY.md").read_text()
    assert store  # imported for parity with the other tests
