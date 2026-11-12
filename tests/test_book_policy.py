"""Order-book selection: stratified core + deterministic rotation, at an unchanged request budget."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from nba_edge.archive.book_policy import FAMILY_RANK, POLICY_ID, ROTATION_FRACTION, select_books

NOW = datetime(2026, 10, 24, 22, 0, tzinfo=UTC)


def _m(ticker, family, tip_h, mid=50, oi=100.0, status="active"):
    tip = NOW + timedelta(hours=tip_h)
    return {"ticker": ticker, "event_ticker": ticker.rsplit("-", 1)[0], "_family": family, "status": status,
            "occurrence_datetime": tip.isoformat().replace("+00:00", "Z"), "open_interest_fp": str(oi),
            "_quote_cents": {"yes_bid": mid - 1, "yes_ask": mid + 1, "no_bid": None, "no_ask": None, "last_price": None}}


def slate(n_games=8, tip_h=1.0, rungs=12):
    """n simultaneous games, each with a deep spread/total ladder and four stats x ten players x three rungs."""
    out = []
    for g in range(n_games):
        key = f"26OCT24A{g:02d}B{g:02d}"
        for side in ("A", "B"):
            out.append(_m(f"KXNBAGAME-{key}-{side}{g:02d}", "game_winner", tip_h, 50))
        for r in range(rungs):
            out.append(_m(f"KXNBASPREAD-{key}-A{g:02d}{r}", "game_spread", tip_h, 20 + 5 * r))
            out.append(_m(f"KXNBATOTAL-{key}-{200 + 5 * r}", "game_total", tip_h, 20 + 5 * r))
            for t in ("A", "B"):
                out.append(_m(f"KXNBATEAMTOTAL-{key}-{t}{g:02d}{100 + 5 * r}", "team_total", tip_h, 20 + 5 * r))
        for fam, code in (("player_points", "KXNBAPTS"), ("player_rebounds", "KXNBAREB"), ("player_assists", "KXNBAAST"), ("player_threes", "KXNBA3PT")):
            for p in range(10):
                for r in range(3):
                    out.append(_m(f"{code}-{key}-P{g}{p:02d}-{r + 1}", fam, tip_h, 30 + 15 * r, oi=1000 - p))
    return out


def test_selection_is_deterministic_and_respects_the_budget():
    board = slate()
    a, b = select_books(board, now=NOW, max_books=300), select_books(list(reversed(board)), now=NOW, max_books=300)
    assert [m["ticker"] for m in a.markets] == [m["ticker"] for m in b.markets], "input order must not matter"
    assert len(a.markets) == 300 == len({m["ticker"] for m in a.markets})
    assert a.summary["policy"] == POLICY_ID and a.summary["n_core"] + a.summary["n_rotation"] == 300
    assert a.summary["selection_sha256"] == b.summary["selection_sha256"]


def test_every_game_gets_its_essentials_before_any_game_gets_a_second_ladder_rung():
    """The failure being fixed: the old ordering spent the cap on one game's ladders while later games on the slate had no book at all."""
    board = slate(n_games=10)
    sel = select_books(board, now=NOW, max_books=300)
    chosen = {m["ticker"] for m in sel.markets}
    for g in range(10):
        key = f"26OCT24A{g:02d}B{g:02d}"
        for fam, token in (("game_winner", "KXNBAGAME"), ("game_spread", "KXNBASPREAD"), ("game_total", "KXNBATOTAL")):
            assert any(t.startswith(f"{token}-{key}") for t in chosen), f"game {g} has no {fam} book"
        assert sum(1 for t in chosen if t.startswith(f"KXNBAGAME-{key}")) == 2, "both moneyline sides"


def test_the_main_line_is_the_rung_nearest_fifty_cents():
    sel = select_books(slate(n_games=1), now=NOW, max_books=40)
    spreads = [m for m in sel.markets if m["_family"] == "game_spread" and sel.reasons[m["ticker"]].startswith("core0")]
    assert len(spreads) == 1 and abs(spreads[0]["_quote_cents"]["yes_bid"] + 1 - 50) == min(abs(20 + 5 * r - 50) for r in range(12))


def test_nearer_games_win_the_scarce_slots():
    board = slate(n_games=2, tip_h=1.0) + [dict(m, ticker=m["ticker"].replace("26OCT24", "26OCT25"), occurrence_datetime=(NOW + timedelta(hours=20)).isoformat().replace("+00:00", "Z"))
                                          for m in slate(n_games=2, tip_h=20.0)]
    sel = select_books(board, now=NOW, max_books=8)  # 6 core slots, 2 rotation
    core = [m["ticker"] for m in sel.markets if sel.reasons[m["ticker"]].startswith("core")]
    assert len(core) == 6 and all("26OCT24" in t for t in core)


def test_rotation_is_reproducible_per_tick_and_varies_across_ticks():
    board = slate()
    t0 = select_books(board, now=NOW, max_books=300)
    again = select_books(board, now=NOW, max_books=300)
    t1 = select_books(board, now=NOW + timedelta(minutes=5), max_books=300)
    rot0 = {t for t, r in t0.reasons.items() if r == "rotation"}
    assert rot0 == {t for t, r in again.reasons.items() if r == "rotation"}
    rot1 = {t for t, r in t1.reasons.items() if r == "rotation"}
    assert rot0 != rot1 and len(rot0) == len(rot1) == int(300 * ROTATION_FRACTION)
    core0 = {t for t, r in t0.reasons.items() if r.startswith("core")}
    assert core0 == {t for t, r in t1.reasons.items() if r.startswith("core")}, "the core must not churn between ticks"


def test_rotation_eventually_samples_the_long_tail():
    """Over five hours of ticks nearly every non-core game-day market has been requested at least once."""
    board = slate()
    core = {t for t, r in select_books(board, now=NOW, max_books=300).reasons.items() if r.startswith("core")}
    pool = {m["ticker"] for m in board} - core
    seen: set[str] = set()
    for k in range(60):
        seen |= {t for t, r in select_books(board, now=NOW + timedelta(minutes=5 * k), max_books=300).reasons.items() if r == "rotation"}
    assert len(seen & pool) >= 0.95 * len(pool)


def test_season_long_and_far_future_markets_are_not_requested_and_are_counted():
    board = slate(n_games=1) + [dict(_m("KXNBAMVP-27-X", "awards", 1), occurrence_datetime=None), _m("KXNBAGAME-26NOV30A00B00-A", "game_winner", 24 * 30)]
    sel = select_books(board, now=NOW, max_books=300)
    assert "KXNBAMVP-27-X" not in sel.reasons and "KXNBAGAME-26NOV30A00B00-A" not in sel.reasons
    assert sel.summary["not_eligible"] == {"no_tip_season_long": 1, "outside_horizon": 1}


def test_non_live_markets_are_never_requested_and_missing_tips_yield_an_empty_selection_for_the_caller_to_fall_back_on():
    board = [_m("KXNBAGAME-26OCT24A00B00-A", "game_winner", 1, status="initialized")]
    assert select_books(board, now=NOW, max_books=10).markets == []
    notip = [dict(m, occurrence_datetime=None) for m in slate(n_games=1)]
    assert select_books(notip, now=NOW, max_books=10).markets == []


def test_policy_families_are_all_known_to_the_ontology_module():
    assert set(FAMILY_RANK) >= {"game_winner", "game_spread", "game_total", "team_total", "player_points"}
