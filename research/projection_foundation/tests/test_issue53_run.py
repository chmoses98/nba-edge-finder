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
    assert set(m1["outputs"]) >= {"SUMMARY.md", "exec_shadow.json", "jrm_matched.json", "attribution_2026-10-20.json", "attribution_2026-10-20.md", "manifest.json"} or \
        set(os.listdir(tmp_path / "o1")) >= {"SUMMARY.md", "exec_shadow.json", "jrm_matched.json", "attribution_2026-10-20.json"}


def test_three_separately_labelled_sets_and_honest_evidence_status(world, tmp_path):
    study53.run(str(world / "pd"), str(world / "msa"), str(tmp_path / "o"), "2026-10-20")
    man = json.load(open(tmp_path / "o" / "manifest.json"))
    tw = man["three_way"]
    assert set(tw) == {"1_original_frozen_strategy_selection", "2_new_fixed_checkpoint_executable_shadow", "3_eligible_matched_jrm_whatif"}
    assert "NOT simultaneously executable" in tw["1_original_frozen_strategy_selection"]["label"]
    assert "RETROSPECTIVE" in tw["2_new_fixed_checkpoint_executable_shadow"]["label"] and "RETROSPECTIVE" in tw["3_eligible_matched_jrm_whatif"]["label"]
    B = json.load(open(tmp_path / "o" / "exec_shadow.json"))
    assert B["independent_clocks"]["status"] == "NOT_VERIFIED"                                              # no git history supplied: reported, never assumed
    assert B["prospective"]["evidence_status"]["independent_clocks_verified"] is False
    assert B["retrospective_descriptive"]["status"] == "OK" and B["prospective"]["status"] == "OK"        # G2 is after prospective_start_utc
    assert B["prospective"]["evidence_status"]["label"] == "INSUFFICIENT_SAMPLE"
    assert B["progress_to_evidence_minimums"]["prospective_decisions"] == 2 and B["progress_to_evidence_minimums"]["prospective_games"] == 1
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
