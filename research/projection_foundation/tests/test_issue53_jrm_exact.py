"""Issue #53, owner decision 3 on PR #54: the EXACT frozen-vs-JRM dry run runs both engines of nba.project.project_slate on one capture and prices both on one board.
The real engines need the live feed and PR #45's code, so the tests inject a stub `project_slate` / runner; everything else (records, pricing, selection, pairing) is real code
on the REAL opening-night Kalshi boards of tests/fixtures/paper/market_archive."""
import copy
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
PF = HERE.parent
sys.path.insert(0, str(PF))
sys.path.insert(0, str(HERE))
import test_paper_engine as T  # noqa: E402
from nba.paper import config as CFG, exec_shadow as X, jrm_exact as JX, markets as MK  # noqa: E402

NOW = datetime(2026, 10, 20, 18, 30, tzinfo=timezone.utc)


def stub_res(scale: float, minutes: float, p_play_shift: float = 0.0) -> dict:
    """A project_slate-shaped result built from the repo's synthetic pmf families on the real board's players."""
    dt, board = MK.ChainReader(str(T.FIXARCH), "markets").board_at(NOW)
    rows, _ = T.snaps_for(board, dt, T.GAME)
    recs = T.synth_forecasts(rows, T.GAME, gen="2026-10-20T15:00:00Z", scale=scale)
    players = []
    for r in recs:
        if r["family"] == "participation":
            continue
        pp = next(x["mean"] for x in recs if x["family"] == "participation" and x["entity_id"] == r["entity_id"]) + p_play_shift
        players.append({"game_id": r["game_id"], "player_id": r["entity_id"], "name": r["entity_name"], "team": r["team"], "family": r["family"], "mean": r["mean"],
                        "_pmf": {"lo": r["lo"], "probs": r["probs"]}, "readiness": "SHADOW VALIDATION", "data_asof_utc": r["data_asof_utc"], "_tags": {},
                        "gate": {"status": "PASS"}, "participation": {"status": "LIKELY_ACTIVE", "certainty": "REPORTED", "source": "stub", "captured_utc": "2026-10-20T14:59:00Z",
                                                                      "p_play": pp, "designation": "ACTIVE", "implicit": False}})
        if r["family"] == "points":
            players.append({**players[-1], "family": "minutes", "mean": minutes})
    gf = T.synth_game_forecast(T.GAME)
    return {"schema": "sift.projections.v1", "generated_utc": "2026-10-20T15:00:00Z", "model": {"version": "stub"}, "mode": "next_slate", "players": players, "reconciliation": [],
            "games": [{"game_id": T.GAME["game_id"], "start_utc": T.GAME["start_utc"], "home": T.GAME["home"], "away": T.GAME["away"], "teams": []}],
            "game_forecasts": [{k: v for k, v in gf.items() if k not in ("schema", "game_forecast_id", "archived_utc")}]}


@pytest.fixture(scope="module")
def pair():
    return {"frozen": stub_res(0.6, 26.0), "jrm": stub_res(0.4, 31.0, -0.02)}


def test_records_are_built_like_the_live_pipeline_and_nothing_is_archived(pair, tmp_path):
    recs, gfs = JX.records_from_res(pair["frozen"])
    assert recs and gfs and all(r["forecast_id"] and r["archived_utc"] == r["generated_utc"] and r["model_role"] == "challenger" for r in recs)
    assert {r["family"] for r in recs} >= {"participation", "points", "minutes"}
    assert not list(tmp_path.iterdir())                                                      # no archive was touched


def test_both_engines_are_priced_on_the_same_board_and_compared_contract_by_contract(pair):
    rep = JX.compare(copy.deepcopy(pair), str(T.FIXARCH), NOW, CFG.load(), X.load_study())
    assert rep["label"] == "exact_jrm_dry_run" and rep["authority"] == "research_only" and rep["market"]["status"] == "OK"
    assert rep["market"]["board_observed_utc"] == "2026-10-20T18:24:36Z"
    assert set(rep["engines"]) == {"frozen", "jrm"} and rep["engines"]["frozen"]["n_players"] == rep["engines"]["jrm"]["n_players"] > 0
    md = rep["minutes_difference"]
    assert md["share_jrm_higher"] == 1.0 and md["mean"] == pytest.approx(5.0)                  # every stub player gets 31 vs 26 minutes
    sel = rep["selections"]
    assert sel["status"] == "OK" and sel["downstream"] == "exact_jrm_dry_run" and "not an accuracy or P&L claim" in sel["note"]
    m = sel["paired"]["decision_matrix_candidate_sides"]
    assert sum(m.values()) == sel["jrm_exact"]["n_candidate_sides"] == sel["frozen"]["n_candidate_sides"]       # identical candidate rows
    assert m["v1_only"] + m["jrm_only"] + m["both_bet"] > 0 and m["v1_only"] + m["jrm_only"] > 0                  # the engines really disagree somewhere
    assert all(p["price"] is not None for p in sel["pairs"])


def test_identical_engines_give_an_identity_comparison(pair):
    same = {"frozen": stub_res(0.6, 26.0), "jrm": stub_res(0.6, 26.0)}
    rep = JX.compare(same, str(T.FIXARCH), NOW, CFG.load(), X.load_study())
    m = rep["selections"]["paired"]["decision_matrix_candidate_sides"]
    assert m["v1_only"] == 0 and m["jrm_only"] == 0 and m["both_bet"] > 0 and rep["minutes_difference"]["mean_abs"] == 0.0
    assert rep["selections"]["paired"]["common_contracts_covered"]["mean_abs_d_p_model"] == pytest.approx(0.0, abs=1e-12)


def test_no_board_is_reported_not_forced(pair, tmp_path):
    rep = JX.compare(copy.deepcopy(pair), str(tmp_path), NOW, CFG.load(), X.load_study())
    assert rep["market"]["status"] == "NO_BOARD" and rep["selections"]["status"] == "NO_DATA"


def test_project_pair_runs_both_engines_on_the_same_inputs_and_restores_the_environment(monkeypatch):
    import nba.project as P
    real = P.project_slate
    seen = []

    def fake_project_slate(sl, out, *, minutes_engine="frozen", **kw):
        seen.append((minutes_engine, sl["asof"], kw["now_utc"]))
        return {"engine": minutes_engine}

    def runner(a, now, work):
        assert os.environ["PF_NBA_MINUTES_ENGINE"] in ("frozen", "jrm")
        P.project_slate({"asof": "A"}, None, now_utc="N", minutes_engine=os.environ["PF_NBA_MINUTES_ENGINE"])
    monkeypatch.setattr(P, "project_slate", fake_project_slate)
    monkeypatch.delenv("PF_NBA_MINUTES_ENGINE", raising=False)
    out = JX.project_pair(SimpleNamespace(), NOW, "/tmp", runner=runner)
    assert out == {"frozen": {"engine": "frozen"}, "jrm": {"engine": "jrm"}} and seen == [("frozen", "A", "N"), ("jrm", "A", "N")]       # one capture, one clock
    assert "PF_NBA_MINUTES_ENGINE" not in os.environ and P.project_slate is fake_project_slate                      # environment and function restored
    assert real is not fake_project_slate


def test_a_checkout_without_pr45_reports_the_engine_as_unavailable(monkeypatch):
    import nba.project as P

    def main_project_slate(sl, out, **kw):                       # main's stage_project never passes minutes_engine: both calls are the frozen engine
        return {"engine": "frozen"}

    def runner(a, now, work):
        P.project_slate({"asof": "A"}, None, now_utc="N")
    monkeypatch.setattr(P, "project_slate", main_project_slate)
    with pytest.raises(JX.JrmUnavailable):
        JX.project_pair(SimpleNamespace(), NOW, "/tmp", runner=runner)
    assert P.project_slate is main_project_slate


def test_the_report_is_labelled_and_never_claims_accuracy(pair):
    rep = JX.compare(copy.deepcopy(pair), str(T.FIXARCH), NOW, CFG.load(), X.load_study())
    md = JX.markdown(rep)
    assert "Isolated throw-away run" in md and "No archive written" in md and "not an accuracy or P&L claim" in md
    assert json.dumps(rep, default=str)
