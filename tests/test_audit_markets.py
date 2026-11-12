"""Issue #95: all-market audit — fees once, strict point-in-time, no phantom success, CLV labels, universe reconciliation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from nba_edge.archive.ledger import Ledger
from nba_edge.audit.markets import (
    audit_date,
    breakeven_prob,
    cluster_bootstrap_ratio,
    fee_dollars_per_contract,
    hypothetical_pnl,
    midpoint,
    quote_cents,
    run_audit,
    side_ask,
    skill_flag,
)
from nba_edge.kalshi.fees import taker_fee_cents

TIP = datetime(2026, 11, 8, 0, 0, tzinfo=UTC)  # 19:00 ET on 2026-11-07 -> ET date must drive the slate, not the UTC partition
T = lambda m: TIP - timedelta(minutes=m)  # noqa: E731


def iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def build(tmp_path, *, settled=True, p=0.6, late_pred=False, cents=False, no_quotes=False, spread=False):
    led = Ledger(tmp_path, run_id="r1")
    led.append_rows("context/schedule", [{"game_id": "g1", "game_date_et": "2026-11-07", "start_time_utc": iso(TIP), "actual_tip_utc": None,
                                          "away_tricode": "AAA", "home_tricode": "HHH", "_observed_at_utc": iso(T(600))}], observed_at=T(600))
    led.append_rows("contracts", [{"ticker": "KXNBAGAME-26NOV07AAAHHH-AAA", "family": "game_winner", "game_id": "g1", "scope": "game", "stat": "winner",
                                   "support": "BUILDABLE", "threshold": 0.0, "_observed_at_utc": iso(T(600))}], observed_at=T(600))
    tk = "KXNBAGAME-26NOV07AAAHHH-AAA"
    spread_tk = "KXNBASPREAD-26NOV07AAAHHH-AAA-4"
    if spread:
        led.append_rows("contracts", [{"ticker": spread_tk, "family": "game_spread", "game_id": "g1",
                                      "scope": "game", "stat": "margin", "period": "game",
                                      "threshold": -4.5, "comparator": "gte", "support": "BUILDABLE"}], observed_at=T(600))
    q = (lambda a, b: {"_quote_cents": {"yes_bid": a, "yes_ask": b, "no_bid": 100 - b, "no_ask": 100 - a}}) if cents else \
        (lambda a, b: {"yes_bid_dollars": f"{a/100:.4f}", "yes_ask_dollars": f"{b/100:.4f}", "no_bid_dollars": f"{(100-b)/100:.4f}", "no_ask_dollars": f"{(100-a)/100:.4f}"})
    if no_quotes:
        def q(a, b):
            return {}  # board snapshots exist, but none carry executable bid/ask
    led.append_rows("kalshi/markets", [{"ticker": tk, **q(48, 52)}, {"ticker": "KXNBAUNKNOWN-26NOV07AAAHHH-X", **q(10, 12)}], observed_at=T(120))
    led.append_rows("kalshi/markets", [{"ticker": tk, **q(55, 59)}, {"ticker": "KXNBAUNKNOWN-26NOV07AAAHHH-X", **q(10, 12)}], observed_at=T(20))
    led.append_rows("kalshi/markets", [{"ticker": tk, **q(1, 2)}], observed_at=TIP + timedelta(minutes=5))  # post-tip board: must never be used
    preds = [{"prediction_id": "p1", "ticker": tk, "game_id": "g1", "predicted_at_utc": iso(T(90)), "p_data_only": p, "family": "game_winner"}]
    if spread:
        preds.append({"prediction_id": "spread1", "ticker": spread_tk, "game_id": "g1",
                      "predicted_at_utc": iso(T(90)), "p_data_only": 0.8, "family": "game_spread"})
    if late_pred:
        preds.append({"prediction_id": "p2", "ticker": tk, "game_id": "g1", "predicted_at_utc": iso(TIP + timedelta(minutes=1)), "p_data_only": 0.99})
    if p is not None:
        led.append_rows("predictions", preds, observed_at=T(90))
    if settled:
        led.append_rows("settlements", [{"ticker": tk, "game_id": "g1", "outcome": "YES", "settled_at_utc": iso(TIP + timedelta(hours=4)), "engine_version": "settle-1.0"},
                                        {"ticker": "KXNBAUNKNOWN-26NOV07AAAHHH-X", "game_id": "g1", "outcome": "UNSETTLEABLE", "reason": "semantics not proven (support=UNRESOLVED)",
                                         "settled_at_utc": iso(TIP + timedelta(hours=4)), "engine_version": "settle-1.0"}], observed_at=TIP + timedelta(hours=4))
        if spread:
            led.append_rows("settlements", [{"ticker": spread_tk, "game_id": "g1", "outcome": "YES",
                                             "settled_at_utc": iso(TIP + timedelta(hours=4)),
                                             "engine_version": "settle-1.0"}], observed_at=TIP + timedelta(hours=4))
    return led


def test_fee_is_charged_once_and_matches_kalshi_schedule():
    for c in (5, 30, 50, 77, 95):
        assert fee_dollars_per_contract(c) == pytest.approx(taker_fee_cents(c, 100) / 10000.0)
    # a winning YES at 50c: +0.50 gross minus ONE fee
    assert hypothetical_pnl("yes", 50, True) == pytest.approx(0.5 - fee_dollars_per_contract(50))
    assert hypothetical_pnl("no", 50, True) == pytest.approx(-0.5 - fee_dollars_per_contract(50))
    assert breakeven_prob(50) == pytest.approx(0.5 + fee_dollars_per_contract(50))


def test_quote_parsing_cents_dollars_legacy_and_invalid():
    assert quote_cents({"yes_ask_dollars": "0.4400", "yes_bid_dollars": "0.4000"})["yes_ask"] == pytest.approx(44.0)
    assert quote_cents({"_quote_cents": {"yes_ask": 44}, "yes_ask_dollars": "0.9"})["yes_ask"] == 44.0  # cents view wins
    assert quote_cents({"yes_ask": 61})["yes_ask"] == 61.0
    assert quote_cents({"yes_ask_dollars": "1.0000", "yes_bid_dollars": "0.0000"}) == {"yes_bid": None, "yes_ask": None, "no_bid": None, "no_ask": None}
    assert quote_cents(None)["yes_ask"] is None


def test_one_sided_quote_has_no_midpoint_and_derives_ask_only_from_complement():
    q = quote_cents({"yes_bid_dollars": "0.4000"})
    assert midpoint(q) is None and side_ask(q, "yes") is None
    assert side_ask(q, "no") == pytest.approx(60.0)  # no ask == 100 - yes bid


def test_empty_evaluation_is_blocked_not_success(tmp_path):
    build(tmp_path, p=None)  # eligible settled inputs exist but no model probability can be joined
    rep = audit_date(tmp_path, "2026-11-07", tmp_path / "out")
    assert rep["status"] == "BLOCKED" and rep["coverage"]["graded"] == 0
    assert run_audit(tmp_path, ["2026-11-07"], tmp_path / "out2") == 3


def test_slate_is_selected_by_et_date_and_universe_reconciles(tmp_path):
    build(tmp_path)
    assert audit_date(tmp_path, "2026-11-08", tmp_path / "o")["status"] == "BLOCKED"  # UTC date of tip: no ET games that day
    rep = audit_date(tmp_path, "2026-11-07", tmp_path / "o")
    c = rep["coverage"]
    assert rep["status"] == "OK" and c["graded"] == 1
    assert c["universe"] == c["graded"] + sum(c["ungraded_by_reason"].values()) == 2
    assert any(k.startswith("settlement_unsettleable") for k in c["ungraded_by_reason"])  # unsupported contract is counted, not dropped
    assert "unmapped:KXNBAUNKNOWN" in c["by_family_universe"]


@pytest.mark.parametrize("cents", [False, True])
def test_point_in_time_join_uses_board_at_prediction_and_never_post_tip(tmp_path, cents):
    build(tmp_path, late_pred=True, cents=cents)
    rep = audit_date(tmp_path, "2026-11-07", tmp_path / "o")
    assert rep["coverage"]["refused"]["prediction_at_or_after_tip"] == 1
    import csv
    rows = list(csv.DictReader(open(tmp_path / "o" / "2026-11-07" / "horizon_rows.csv")))
    assert len(rows) == 1
    r = rows[0]
    assert float(r["yes_ask"]) == 52.0, "T-90 prediction must see the T-120 board (52c), not the T-20 or post-tip board"
    assert float(r["p_model"]) == 0.6
    # model 0.6 vs ask 52c: YES is the pick; outcome YES -> positive P&L after one fee
    assert r["pick_side"] == "yes" and float(r["pick_pnl"]) == pytest.approx(0.48 - fee_dollars_per_contract(52))
    # CLV labels: quoted-execution = close ask (59, last pre-tip board) - entry ask (52); selection = mid(57)-mid(50); never actual-fill
    assert float(r["clv_quoted_exec"]) == pytest.approx(0.07)
    assert float(r["clv_selection"]) == pytest.approx(0.07)


def test_void_push_unsettled_are_never_losses(tmp_path):
    build(tmp_path, settled=False)
    rep = audit_date(tmp_path, "2026-11-07", tmp_path / "o")
    assert rep["coverage"]["graded"] == 0 and rep["coverage"]["ungraded_by_reason"]["no_settlement_record"] == 2


def test_audit_is_idempotent_and_does_not_touch_the_archive(tmp_path):
    build(tmp_path)
    before = sorted((p.name, p.stat().st_size) for p in tmp_path.rglob("*") if p.is_file())
    audit_date(tmp_path, "2026-11-07", tmp_path / "o1")
    audit_date(tmp_path, "2026-11-07", tmp_path / "o2")
    assert before == sorted((p.name, p.stat().st_size) for p in tmp_path.rglob("*") if p.is_file() and "o1" not in str(p) and "o2" not in str(p))
    a = (tmp_path / "o1/2026-11-07/horizon_rows.csv").read_text()
    assert a == (tmp_path / "o2/2026-11-07/horizon_rows.csv").read_text()


def test_clustered_ci_and_skill_flag_are_conservative():
    r = cluster_bootstrap_ratio([1.0, -1.0, 2.0], [1.0, 1.0, 1.0], ["a", "b", "c"])
    assert r["ci95"] is None, "fewer than 5 games: no interval, so no green flag"
    assert skill_flag(0.05, None, 3) == "🟡"
    assert skill_flag(0.05, [0.01, 0.09], 10) == "🟢" and skill_flag(-0.05, [-0.09, -0.01], 10) == "🔴" and skill_flag(0.0, [-0.1, 0.1], 10) == "🟡"


def test_bh_controls_multiplicity_and_skill_requires_q():
    from nba_edge.audit.markets import benjamini_hochberg, ungraded_group

    q = benjamini_hochberg([0.001, 0.02, 0.04, 0.5, None])
    assert q[4] is None and q[0] == pytest.approx(0.004) and all(a <= b for a, b in zip(q[:3], q[1:4], strict=False))
    assert skill_flag(0.05, [0.01, 0.09], 10, q_bh=0.5) == "🟡", "CI excludes 0 but the family-wise q does not: still inconclusive"
    assert skill_flag(0.05, [0.01, 0.09], 10, q_bh=0.01) == "🟢"
    assert ungraded_group("KXNBAPTSPROT-26NOV08BKNDAL-X") == "protected_prop_needs_period_participation"
    assert ungraded_group("KXNBAWINMARGIN-26NOV08BKNDAL-BKN11TO20").startswith("win_margin")
    assert ungraded_group("KXNBAPTS-26NOV08BKNDAL-X") == ""


def test_all_missing_executable_quotes_block_audit_even_when_settled_models_exist(tmp_path):
    build(tmp_path, no_quotes=True)
    rep = audit_date(tmp_path, "2026-11-07", tmp_path / "out")
    assert rep["coverage"]["graded"] == 1  # settlement and PIT probability are still valid
    assert rep["coverage"]["forecast_rows_with_an_executable_quote"] == 0
    assert rep["coverage"]["forecast_rows_without_any_executable_quote"] == 1
    assert rep["status"] == "BLOCKED"
    assert any("no executable quote" in reason for reason in rep["blockers"])
    assert run_audit(tmp_path, ["2026-11-07"], tmp_path / "out2") == 3


def test_direction_score_is_not_brier_and_every_spread_rung_is_kept(tmp_path):
    build(tmp_path, spread=True)
    rep = audit_date(tmp_path, "2026-11-07", tmp_path / "out")
    assert rep["status"] == "OK"
    assert len(rep["by_spread_rung"]) == 1
    rung = rep["by_spread_rung"][0]
    assert rung["spread_rung"] == "game_spread|game|gte|-4.5"
    assert rung["n"] == 1 and rung["n_games"] == 1
    assert rung["model_direction_hit_rate"] == 1.0  # 80% YES and actual YES
    assert rung["brier_model"] == pytest.approx(0.04)  # calibrated penalty, not 0/1 direction
    assert rung["market_direction_hit_rate"] is None  # no invented market quote for spread
    winner = next(x for x in rep["headline_latest_pretip_by_family"] if x["family"] == "game_winner")
    assert winner["model_direction_hit_rate"] == 1.0
    assert winner["n_market_direction_calls"] == 0  # market midpoint was exactly 0.50
    assert "multiple-comparison control" not in " ".join(rep["not_evaluated"])
