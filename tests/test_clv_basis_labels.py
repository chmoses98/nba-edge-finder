"""Quoted-execution CLV (close mid - entry ask) must not be mistaken for selection CLV (close mid - entry mid).

An unchanged market with a bid/ask spread scores about minus half the spread as quoted-execution CLV and exactly
zero as selection CLV. No fee is ever part of either figure.
"""
from __future__ import annotations

from datetime import timedelta

import pytest

from nba_edge.settlement.engine import SettlementOutcome, SettlementRecord
from nba_edge.workflows.evaluate import (
    View,
    build_evaluation_row,
    signed_clv,
    signed_selection_clv,
    view_metrics,
)
from tests.test_settle_job import GAME, NOW, TIP, WINNER, prediction_row


def _rec():
    return SettlementRecord(ticker=WINNER, game_id=GAME, outcome=SettlementOutcome.YES, value=1, reason="x",
                            settled_at_utc=NOW, box_source="t", box_stat_correction_version=0, engine_version="e",
                            idempotency_key="k")


def _pred(yes_bid, yes_ask, no_bid, no_ask, p_market=0.50):
    p = prediction_row("p", TIP - timedelta(hours=1))
    p.update(market_yes_bid=yes_bid, market_yes_ask=yes_ask, market_no_bid=no_bid, market_no_ask=no_ask,
             p_market=p_market, p_data_only=0.60)
    return p


def _obs(yes_bid, yes_ask, minutes_before=30, last=None):
    from nba_edge.timeutil import iso
    return {"ticker": WINNER, "yes_bid": yes_bid, "yes_ask": yes_ask, "no_bid": None, "no_ask": None,
            "last_price": last, "status": "active", "result": None, "_family": "x",
            "_observed_at_utc": iso(TIP - timedelta(minutes=minutes_before))}


def test_unchanged_spread_market_is_zero_selection_but_negative_quoted_execution():
    row = build_evaluation_row(_pred(48, 52, 48, 52), _rec(), TIP, [_obs(48, 52)])
    assert row["selection_clv_yes_prob"] == pytest.approx(0.0)
    assert row["selection_clv_no_prob"] == pytest.approx(0.0)
    assert row["quoted_execution_clv_yes_prob"] == pytest.approx(-0.02)    # mid 50 - ask 52
    assert row["quoted_execution_clv_no_prob"] == pytest.approx(-0.02)
    assert row["clv_yes_prob"] == row["quoted_execution_clv_yes_prob"]      # legacy name unchanged (gates read it)
    assert "fee" not in row["clv_basis"].replace("pre-fee", "")


def test_yes_no_symmetry_on_genuine_move():
    row = build_evaluation_row(_pred(48, 52, 48, 52), _rec(), TIP, [_obs(53, 57)])   # mid 50 -> 55
    assert row["selection_clv_yes_prob"] == pytest.approx(0.05)
    assert row["selection_clv_no_prob"] == pytest.approx(-0.05)
    assert signed_selection_clv(row, 0.60) == pytest.approx(0.05)    # model favours YES vs p_market 0.50
    assert signed_selection_clv(row, 0.40) == pytest.approx(-0.05)   # favours NO
    assert signed_clv(row, 0.60) == pytest.approx(0.03)              # legacy quoted: 55 - ask 52


def test_last_trade_fallback_is_not_a_midpoint_selection_close():
    row = build_evaluation_row(_pred(48, 52, 48, 52), _rec(), TIP, [_obs(None, None, last=55)])
    assert row["close_price_source"] == "last_trade"
    assert row["selection_clv_yes_prob"] is None and row["selection_clv_no_prob"] is None
    assert row["clv_yes_prob"] is not None                           # legacy behaviour preserved, now labelled


def test_one_sided_entry_book_has_no_selection_clv():
    row = build_evaluation_row(_pred(None, 52, None, 52), _rec(), TIP, [_obs(48, 52)])
    assert row["selection_clv_yes_prob"] is None


def test_view_metrics_report_both_with_basis_label():
    rows = [build_evaluation_row(_pred(48, 52, 48, 52), _rec(), TIP, [_obs(48, 52)])]
    m = view_metrics(rows, View.DATA_ONLY)
    assert m["selection_clv_mean"] == pytest.approx(0.0)
    assert m["clv_mean"] == pytest.approx(-0.02)
    assert "quoted_execution" in m["clv_mean_basis"]
