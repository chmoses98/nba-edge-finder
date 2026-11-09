from datetime import UTC, datetime, timedelta

import pytest

from nba_edge.parlay.research import (
    Leg,
    breakeven_from_price,
    build_ticket,
    corr_matrix,
    evaluate_tickets,
    fee_per_contract,
    frechet_bounds,
    freeze,
    joint_probability,
    p_at_least_one_hit,
    settle_ticket,
    stake_for_payout,
    tickets_needed,
)

TIP = datetime(2026, 11, 9, 23, 0, tzinfo=UTC)
FROZEN = TIP - timedelta(hours=2)


def leg(t, g, p=0.6, ask=55.0, side="yes", fam="f"):
    return Leg(t, g, side, ask, p, p_market=ask / 100.0, family=fam)


def test_independent_across_games_is_exact_product():
    legs = [leg("a", "g1"), leg("b", "g2"), leg("c", "g3")]
    assert joint_probability([0.6] * 3, corr_matrix(legs)) == pytest.approx(0.216)


def test_same_game_positive_dependence_raises_joint_vs_naive_product():
    legs = [leg("a", "g1"), leg("b", "g1")]
    j = joint_probability([0.6, 0.6], corr_matrix(legs, 0.5))
    assert j > 0.36 + 0.02 and j <= 0.6
    lo, hi = frechet_bounds([0.6, 0.6])
    assert lo <= j <= hi


def test_ticket_marks_same_game_and_never_invents_a_combo_price():
    t = build_ticket([leg("a", "g1"), leg("b", "g1"), leg("c", "g2")], "2026-11-09", FROZEN, TIP, 10.0)
    assert t.joint_method == "gaussian_copula" and t.rfq_price_cents is None and t.payout_if_hit_usd is None and t.breakeven_prob is None
    assert any("NO_RFQ" in n for n in t.notes)
    assert t.reference_leg_product_cents == pytest.approx(55 ** 3 / 1e4)


def test_freeze_must_precede_tip_and_file_is_append_only(tmp_path):
    with pytest.raises(ValueError):
        build_ticket([leg("a", "g1")], "d", TIP, TIP, 10.0)
    t = build_ticket([leg("a", "g1"), leg("b", "g2")], "d", FROZEN, TIP, 10.0, rfq_price_cents=0.25, rfq_observed_at=FROZEN)
    p = freeze(tmp_path / "t.jsonl", [t])
    with pytest.raises(FileExistsError):
        freeze(p, [t])


def test_payout_and_breakeven_include_fee_once():
    assert stake_for_payout(0.25, 8000) == pytest.approx(20.0)  # 400x
    assert breakeven_from_price(0.25) == pytest.approx(0.0025 + fee_per_contract(0.25))
    assert breakeven_from_price(50) > 0.5


def test_unsettled_void_leg_is_unresolved_not_a_loss():
    t = build_ticket([leg("a", "g1"), leg("b", "g2")], "d", FROZEN, TIP, 10.0, rfq_price_cents=25.0, rfq_observed_at=FROZEN)
    assert settle_ticket(t, {"a": "YES", "b": "VOID"})["status"] == "UNRESOLVED"
    assert settle_ticket(t, {"a": "YES"})["status"] == "UNRESOLVED"
    assert settle_ticket(t, {"a": "YES", "b": "NO"})["status"] == "MISS"
    hit = settle_ticket(t, {"a": "YES", "b": "YES"})
    assert hit["status"] == "HIT" and hit["net_pnl_usd"] > 0


def test_no_rfq_ticket_has_no_pnl_and_evaluation_never_claims_profit():
    ts = [build_ticket([leg("a", "g1"), leg("b", "g2")], "d", FROZEN, TIP, 10.0)]
    r = evaluate_tickets(ts, {"a": "YES", "b": "NO"})["selective"]
    assert r["priced_by_rfq"] == 0 and r["net_pnl_usd"] == 0.0 and r["verdict"] == "INSUFFICIENT_EVIDENCE" and r["hit_rate"] == 0.0


def test_evidence_requirements_for_longshots_are_large():
    be = breakeven_from_price(0.25)  # ~1-in-400 ticket
    n = tickets_needed(be * 1.5, be)  # a 50% true edge over break-even
    assert n > 5000, "proving a longshot edge needs thousands of tickets; do not infer it from a handful"
    assert tickets_needed(be * 0.9, be) == float("inf")
    assert p_at_least_one_hit(1 / 400, 400) == pytest.approx(0.63, abs=0.01)


def test_paper_freeze_and_eval_end_to_end(tmp_path):
    from nba_edge.archive.ledger import Ledger
    from nba_edge.parlay.paper import run_eval, run_freeze

    led = Ledger(tmp_path / "a", run_id="r")
    tip = datetime(2026, 11, 10, 0, 0, tzinfo=UTC)
    now = tip - timedelta(hours=2)
    sched, contracts, preds, board, sett = [], [], [], [], []
    for i in range(3):
        g, tk = f"g{i}", f"KXNBAGAME-26NOV09A{i}H{i}-A{i}"
        sched.append({"game_id": g, "game_date_et": "2026-11-09", "start_time_utc": tip.strftime("%Y-%m-%dT%H:%M:%SZ"), "away_tricode": f"A{i}", "home_tricode": f"H{i}", "_observed_at_utc": "2026-11-09T10:00:00Z"})
        contracts.append({"ticker": tk, "game_id": g, "family": "game_winner", "support": "BUILDABLE", "_observed_at_utc": "2026-11-09T10:00:00Z"})
        preds.append({"ticker": tk, "game_id": g, "predicted_at_utc": (now - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ"), "p_data_only": 0.7})
        board.append({"ticker": tk, "yes_bid_dollars": "0.5000", "yes_ask_dollars": "0.5200", "no_bid_dollars": "0.4800", "no_ask_dollars": "0.5000"})
        sett.append({"ticker": tk, "game_id": g, "outcome": "YES"})
    led.append_rows("context/schedule", sched, observed_at=now - timedelta(hours=9))
    led.append_rows("contracts", contracts, observed_at=now - timedelta(hours=9))
    led.append_rows("predictions", preds, observed_at=now - timedelta(minutes=5))
    led.append_rows("kalshi/markets", board, observed_at=now - timedelta(minutes=3))
    led.append_rows("settlements", sett, observed_at=tip + timedelta(hours=4))
    assert run_freeze(tmp_path / "a", "2026-11-09", tmp_path / "p", now=now) == 0
    assert list((tmp_path / "p").glob("dt=*/tickets_*.jsonl"))
    assert run_eval(tmp_path / "a", tmp_path / "p") == 0
    import json
    rep = json.loads((tmp_path / "p" / "parlay_eval.json").read_text())
    assert "selective_shrunk" in rep and rep["selective"]["resolved"] == 1 and rep["selective"]["hits"] == 1 and rep["selective"]["priced_by_rfq"] == 0
    assert rep["selective"]["verdict"] == "INSUFFICIENT_EVIDENCE"
