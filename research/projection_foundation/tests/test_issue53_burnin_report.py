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


# -- evidence classes: only independently verified, at/after-start seals are evidence --------------------------------------------------------------------------------------------------


def seal(gid, sid="s", **kw):
    return {"game": {"game_id": gid, "start_utc": "2026-10-28T00:00:00Z"}, "seal_id": sid + gid, "status": "TRADED", "board": {"gap_s": 100.0}, **kw}


def verdict(gid, counted, why=(), sid="s"):
    return {"game_id": gid, "seal_id": sid + gid, "counted": counted, "uncounted_reasons": list(why)}


def test_every_seal_gets_exactly_one_class_and_only_a_clean_verified_seal_is_counted():
    entries = [("seals/d/a.json", seal("a")), ("seals/d/b.json", seal("b")), ("seals/d/c.json", seal("c")), ("seals/d/c2.json", seal("c", sid="late")),
               ("seals/d/d.json", seal("d")), ("seals/d/e.json", {"_unreadable": True}), ("seals/d/f.json", seal("f")), ("seals/d/g.json", seal("g")),
               ("seals/d/h.json", seal("h"))]
    ev = {"games": [verdict("a", True), verdict("b", False, ["BEFORE_PROSPECTIVE_START"]), verdict("c", False, ["BODY_HASH_MISMATCH"]), verdict("d", False, ["COMMITTED_AFTER_DEADLINE"]),
                    verdict("g", True, ["SOMETHING"]), verdict("h", False, ["BEFORE_PROSPECTIVE_START", "CODE_UNPINNED_OR_DIRTY"])],
          "duplicates": [{"game_id": "c", "path": "seals/d/c2.json"}]}
    k = B.classify(entries, ev)
    assert k["seals/d/a.json"] == (B.COUNTED, [])
    assert k["seals/d/b.json"] == (B.BURN_IN, ["BEFORE_PROSPECTIVE_START"])
    assert k["seals/d/c.json"][0] == B.INVALID and k["seals/d/d.json"] == (B.INVALID, ["COMMITTED_AFTER_DEADLINE"])
    assert k["seals/d/c2.json"][0] == B.DUPLICATE
    assert k["seals/d/e.json"][0] == B.INVALID                       # unreadable
    assert k["seals/d/f.json"] == (B.INVALID, ["NOT_VERIFIED_BY_EVALUATOR"])      # the evaluator never vouched for it
    assert k["seals/d/g.json"][0] == B.INVALID                       # a True flag with reasons attached is not trusted
    assert k["seals/d/h.json"][0] == B.INVALID                       # pre-start AND another failure is not clean burn-in
    assert {v[0] for v in k.values()} <= {B.COUNTED, B.BURN_IN, B.INVALID, B.DUPLICATE}


def test_a_seal_the_evaluator_did_not_vouch_for_is_never_counted_by_default():
    entries = [("seals/d/a.json", seal("a"))]
    assert B.classify(entries, {"games": [], "duplicates": []})["seals/d/a.json"][0] == B.INVALID
    assert B.classify(entries, {})["seals/d/a.json"][0] == B.INVALID                    # fails closed on an empty verdict


def test_headline_statistics_use_counted_seals_only(monkeypatch):
    entries = [("seals/d/a.json", seal("a")), ("seals/d/b.json", seal("b")), ("seals/d/c.json", seal("c")), ("seals/d/d.json", seal("d"))]
    ev = {"games": [verdict("a", True), verdict("b", False, ["BEFORE_PROSPECTIVE_START"]), verdict("c", False, ["BODY_HASH_MISMATCH"])], "duplicates": [{"game_id": "d", "path": "seals/d/d.json"}],
          "game_counts": {"SEALED_COUNTED": 1}}
    rows = {"a": [{**T("a", "A", pnl=1.0, won=True), "decision": "TRADE", "prospective": True}], "b": [{**T("b", "B", pnl=-5.0, won=False), "decision": "TRADE"}],
            "c": [{**T("c", "C", pnl=-7.0, won=False), "decision": "TRADE"}], "d": [{**T("d", "D", pnl=-9.0, won=False), "decision": "TRADE"}]}
    monkeypatch.setattr(B.SL, "load_candidates", lambda ledger, body, rel: rows[body["game"]["game_id"]])
    monkeypatch.setattr(B.SL, "hydrate", lambda r, body, study, counted: {**r, "counted_flag": counted})
    monkeypatch.setattr(B.SL, "settle_sealed", lambda trades, *a, **k: {"n": len(trades)})
    monkeypatch.setattr(B.X, "strategy_id", lambda study: "x")
    study = {"prospective_start_utc": "2026-10-27T06:00:00Z", "checkpoint": {"horizon": "T-60"}}
    out = B.lane_report("led", entries, ev, study, "arch", None, None, {})
    assert out["seal_classes"] == {B.COUNTED: 1, B.BURN_IN: 1, B.INVALID: 1, B.DUPLICATE: 1}
    assert out["counted"]["trades"] == 1 and out["counted"]["net_pnl"] == 1.0                # the -5 / -7 / -9 trades are in no headline statistic
    assert out["burn_in_not_evidence"]["trades"] == 1 and out["burn_in_not_evidence"]["net_pnl"] == -5.0
    assert {e["class"] for e in out["excluded_seals"]} == {B.INVALID, B.DUPLICATE}
    assert out["_trades"]["counted"][0]["counted_flag"] is True and out["_trades"]["burn_in_not_evidence"][0]["counted_flag"] is False


def test_without_a_code_repo_the_markdown_says_nothing_is_counted():
    cls = {"seal_classes": {B.BURN_IN: 2}, "game_categories": {}, "excluded_seals": [], "counted": B.summarize([], [], None), "burn_in_not_evidence": B.summarize([], [], None)}
    cmp_ = {"shared_trades": 0, "control_only_trades": 0, "t60a_only_trades": 0, "t60a_only_games": 0, "shared": B.summarize([], [], None), "t60a_only": B.summarize([], [], None),
            "paired_net_pnl_difference_per_game": {"t60a_minus_control": {"status": "INSUFFICIENT_GAMES"}}}
    rep = {"other_lane": "t60a", "caveat": "c", "code_repo_verified": False, "coverage": {"games_counted_in_both": 0, "games_t60a_burn_in_with_a_control_seal": 0}, "lanes": {"control": cls, "t60a": cls}, "counted": cmp_, "burn_in_not_evidence": cmp_}
    md = B.markdown(rep)
    assert "NOTHING is counted" in md and "NOT EVIDENCE" in md


def test_paired_scope_only_covers_games_both_lanes_have_evidence_for():
    ctrl = {B.COUNTED: {"g1", "g2", "g3", "g9"}, B.BURN_IN: {"g4"}}
    other = {B.COUNTED: {"g3", "g9"}, B.BURN_IN: {"g1", "g2", "g4", "g5"}}
    joint, burn = B.paired_scope(ctrl, other)
    assert joint == {"g3", "g9"}                       # a game one lane has not counted is NOT a zero difference
    assert burn == {"g1", "g2", "g4"}                  # g5: the control has no seal, so there is nothing to compare with
    assert B.paired_scope({}, {}) == (set(), set())
