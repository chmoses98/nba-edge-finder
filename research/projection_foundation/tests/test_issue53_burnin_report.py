"""Burn-in side-by-side: shared vs lane-only trades, settled metrics and the interval guard (synthetic trade rows; no ledgers, no network)."""
from nba.paper import burnin_report as B


def T(game, ticker, side="NO", pnl=None, entry=0.4, ev=0.1, p=0.6, won=None, clv=None, spread=0.02, depth=100.0):
    return {"game_id": game, "ticker": ticker, "side": side, "settled": pnl is not None, "net_pnl": pnl, "effective_entry_exec": entry, "ev_net_exec": ev, "p_model": p, "won": won,
            "clv_cents": clv, "spread": spread, "depth_at_entry": depth}


def test_shared_and_lane_only_trades_are_split_by_game_contract_and_side():
    c = [T("g1", "A"), T("g1", "B"), T("g2", "C", side="YES")]
    o = [T("g1", "A"), T("g2", "C", side="NO"), T("g3", "D")]
    shared, only_c, only_o = B.split_shared(c, o)
    assert [(t["game_id"], t["ticker"]) for t in shared] == [("g1", "A")]
    assert {(t["ticker"], t["side"]) for t in only_c} == {("B", "NO"), ("C", "YES")} and {(t["ticker"], t["side"]) for t in only_o} == {("C", "NO"), ("D", "NO")}


def test_summary_reports_settled_pnl_roi_hit_rate_and_predicted_against_realised_and_leaves_pending_out():
    trades = [T("g1", "A", pnl=0.55, won=True, entry=0.45, ev=0.12, p=0.6, clv=2.0), T("g1", "B", pnl=-0.41, won=False, entry=0.41, ev=0.10, p=0.5, clv=-1.0), T("g2", "C")]
    s = B.summarize([], trades, None)
    assert (s["trades"], s["settled"], s["pending"]) == (3, 2, 1)
    assert s["net_pnl"] == 0.14 and s["roi_on_outlay"] == round(0.14 / 0.86, 3) and s["hit_rate"] == 0.5
    assert s["predicted"]["mean_p_win"] == 0.55 and s["realised"]["mean_pnl_per_trade"] == 0.07 and s["mean_clv_cents"] == 0.5 and s["n_clv"] == 2
    assert s["games_traded"] == 2


def test_depth_falls_back_to_the_top_size_and_reasons_are_labelled():
    t = {**T("g1", "A"), "depth_at_entry": None, "top_size": 55.0}
    assert B.summarize([], [t], None)["depth_median"] == 55.0
    bodies = [{"status": "TRADED", "board": {"gap_s": 100.0}}, {"status": "NO_TRADE", "game_reason": "BOARD_COMMITTED_AFTER_CHECKPOINT; x", "board": {"gap_s": 12.0}},
              {"status": "NO_TRADE", "game_reason": "NO_BOARD_COMMITTED_BY_DECISION", "board": None}]
    s = B.summarize(bodies, [], None)
    assert s["reasons"] == {"TRADED": 1, "BOARD_COMMITTED_AFTER_CHECKPOINT": 1, "NO_BOARD_COMMITTED_BY_DECISION": 1} and s["board_age_s"]["n"] == 2


def test_per_game_pnl_ignores_unsettled_trades_and_the_interval_needs_enough_games():
    assert B.per_game_pnl([T("g1", "A", pnl=1.0), T("g1", "B", pnl=-0.25), T("g2", "C")]) == {"g1": 0.75}
    assert B.MIN_GAMES_FOR_INTERVAL >= 8
