"""Evaluation job on the synthetic archive from test_settle_job (after settlement has run)."""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

from nba_edge.archive.ledger import Ledger
from nba_edge.timeutil import iso
from nba_edge.workflows.evaluate import build_evaluation_row, run_evaluate, signed_clv
from nba_edge.workflows.settle import run_settle
from tests.test_settle_job import (
    GAME,
    NOW,
    TIP,
    TOTAL,
    WINNER,
    FakeFetch,
    build_archive,
    final_box,
    prediction_row,
)

EVAL_AT = NOW + timedelta(minutes=10)


def _rows(root, kind):
    return list(Ledger(root, run_id="reader").iter_rows(kind))


@pytest.fixture
def settled(tmp_path):
    build_archive(tmp_path)
    run_settle(tmp_path, tmp_path / "data", fetch_box=FakeFetch(final_box()), now=NOW)
    return tmp_path


def test_evaluate_rows_pregame_labels_closing_and_clv(settled):
    assert run_evaluate(settled, settled / "data", now=EVAL_AT) == 0
    rows = {r["prediction_id"]: r for r in _rows(settled, "evaluations")}
    assert set(rows) == {"p1", "p2"}
    p1, p2 = rows["p1"], rows["p2"]
    assert p1["pregame"] is True and p2["pregame"] is False
    assert p1["y"] == 1 and p1["ticker"] == WINNER and p1["game_id"] == GAME and p1["tip_utc"] == iso(TIP)
    # closing snapshot: the 30-min-before-tip observation (63/67), NOT the one stamped exactly at tip (70/74)
    assert p1["close_prob"] == pytest.approx(0.65)
    assert p1["close_observed_at_utc"] == iso(TIP - timedelta(minutes=30))
    # YES bought at ask 60 -> line moved to 65: +5c; NO bought at 42 (YES-equiv 58) -> -7c
    assert p1["clv_yes_prob"] == pytest.approx(0.05)
    assert p1["clv_no_prob"] == pytest.approx(-0.07)
    assert p1["hours_before_tip"] == pytest.approx(2.5)
    assert p2["hours_before_tip"] < 0
    # model favoured YES (0.70 > market 0.59) so the signed CLV is the YES leg
    assert signed_clv(p1, p1["p_data_only"]) == pytest.approx(0.05)


def test_report_files_written_and_post_tip_rows_excluded_from_metrics(settled):
    run_evaluate(settled, settled / "data", now=EVAL_AT)
    report = json.loads((settled / "eval" / "report.json").read_text())
    assert report["n_rows"] == 2 and report["n_pregame"] == 1 and report["n_new_rows"] == 2
    fam = report["families"]["game_winner"]
    assert fam["n"] == 2 and fam["n_pregame"] == 1 and fam["n_post_tip_excluded"] == 1
    views = fam["views"]
    assert set(views) == {"DATA_ONLY", "MARKET_BASELINE", "HYBRID"}
    assert views["DATA_ONLY"]["n"] == 1 and views["MARKET_BASELINE"]["n"] == 1
    assert views["DATA_ONLY"]["brier"] == pytest.approx((0.70 - 1) ** 2)
    assert views["MARKET_BASELINE"]["brier"] == pytest.approx((0.59 - 1) ** 2)
    assert views["DATA_ONLY"]["brier_skill_vs_market"] > 0
    assert views["DATA_ONLY"]["clv_mean"] == pytest.approx(0.05)
    assert views["MARKET_BASELINE"]["clv_mean"] is None
    assert len(views["DATA_ONLY"]["calibration_table"]) == 10 and len(views["HYBRID"]["by_prob_bucket"]) == 10
    assert views["DATA_ONLY"]["by_hours_bucket"]["1-6h"]["n"] == 1 and views["DATA_ONLY"]["by_hours_bucket"]["<1h"]["n"] == 0
    assert fam["authority"]["stage"] == "RESEARCH" and fam["authority"]["n_settled_predictions"] == 1
    assert "game_winner" in (settled / "eval" / "report.md").read_text()

    status = json.loads((settled / "STATUS_evaluate.json").read_text())
    assert status["evaluated_at_utc"] == iso(EVAL_AT) and status["n_rows"] == 2 and status["n_pregame"] == 1
    assert status["families"] == ["game_winner"]


def test_market_only_calibration_uses_kalshi_close(settled):
    run_evaluate(settled, settled / "data", now=EVAL_AT)
    mo = json.loads((settled / "eval" / "market_only.json").read_text())
    fam = mo["families"]["game_total"]
    assert fam["n"] == 1 and fam["mean_p"] == pytest.approx(0.42)  # 40/44 close 30 min before tip, result yes
    assert fam["mean_y"] == 1.0 and mo["families"]["ALL"]["n"] == 1
    assert TOTAL not in {r["ticker"] for r in _rows(settled, "evaluations")}  # no prediction -> no evaluation row


def test_evaluate_is_idempotent_and_reports_are_overwritten(settled):
    run_evaluate(settled, settled / "data", now=EVAL_AT)
    n = len(_rows(settled, "evaluations"))
    manifest_len = len(Ledger(settled).manifest())
    run_evaluate(settled, settled / "data", now=EVAL_AT + timedelta(hours=1))
    assert len(_rows(settled, "evaluations")) == n
    assert len(Ledger(settled).manifest()) == manifest_len
    report = json.loads((settled / "eval" / "report.json").read_text())
    assert report["n_new_rows"] == 0 and report["n_rows"] == 2


def test_new_prediction_after_first_evaluation_is_appended(settled):
    run_evaluate(settled, settled / "data", now=EVAL_AT)
    Ledger(settled, run_id="late").append_rows("predictions", [prediction_row("p3", TIP - timedelta(minutes=45), p_data_only=0.4)], observed_at=EVAL_AT + timedelta(minutes=1))
    run_evaluate(settled, settled / "data", now=EVAL_AT + timedelta(hours=1))
    rows = {r["prediction_id"] for r in _rows(settled, "evaluations")}
    assert rows == {"p1", "p2", "p3"}
    report = json.loads((settled / "eval" / "report.json").read_text())
    assert report["n_new_rows"] == 1 and report["families"]["game_winner"]["views"]["DATA_ONLY"]["n"] == 2
    assert report["families"]["game_winner"]["views"]["DATA_ONLY"]["by_hours_bucket"]["<1h"]["n"] == 1


def test_box_actual_tip_overrides_schedule(tmp_path):
    build_archive(tmp_path)
    late_tip = TIP + timedelta(minutes=6)
    run_settle(tmp_path, tmp_path / "data", fetch_box=FakeFetch(final_box(actual_tip=late_tip)), now=NOW)
    run_evaluate(tmp_path, tmp_path / "data", now=EVAL_AT)
    p1 = {r["prediction_id"]: r for r in _rows(tmp_path, "evaluations")}["p1"]
    assert p1["tip_utc"] == iso(late_tip)
    assert p1["close_observed_at_utc"] == iso(TIP)  # the at-scheduled-tip snapshot is now strictly before actual tip
    assert p1["close_prob"] == pytest.approx(0.72)
    assert p1["clv_yes_prob"] == pytest.approx(0.12)


def test_unsettled_predictions_are_skipped_and_empty_archive_is_fine(tmp_path):
    build_archive(tmp_path)  # predictions but no settlements yet
    assert run_evaluate(tmp_path, tmp_path / "data", now=EVAL_AT) == 0
    assert not (tmp_path / "evaluations").exists()
    status = json.loads((tmp_path / "STATUS_evaluate.json").read_text())
    assert status["n_rows"] == 0 and status["skipped"]["unsettled"] == 2
    empty = tmp_path / "empty"
    assert run_evaluate(empty, empty / "data", now=EVAL_AT) == 0
    assert json.loads((empty / "eval" / "report.json").read_text())["families"] == {}


def test_build_row_requires_yes_no_outcome():
    from nba_edge.settlement.engine import SettlementOutcome, SettlementRecord

    rec = SettlementRecord(
        ticker=WINNER, game_id=GAME, outcome=SettlementOutcome.VOID, value=None, reason="x", settled_at_utc=NOW, box_source="t", box_stat_correction_version=0,
        engine_version="e", idempotency_key="k",
    )
    assert build_evaluation_row(prediction_row("p", TIP - timedelta(hours=1)), rec, TIP, []) is None
