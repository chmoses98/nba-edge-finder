"""Fill adapter: normalisation, netting, ledger dedupe, prediction matching and cross-sport routing."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from nba_edge.archive.ledger import Ledger
from nba_edge.fills import (
    import_fills_jsonl,
    is_nba_ticker,
    match_fills_to_predictions,
    normalize_kalshi_fill,
    position_key,
    positions_from_fills,
    route_fills,
)
from nba_edge.fills.adapter import implied_edge
from nba_edge.schemas.fills import Fill, FillAction
from tests.test_settle_job import TIP, WINNER, prediction_row

NFL = "KXNFLGAME-26OCT25KCBUF-KC"
T0 = datetime(2026, 10, 21, 20, 0, tzinfo=UTC)


def raw_fill(**over) -> dict:
    base = {
        "trade_id": "t1", "order_id": "o1", "ticker": WINNER, "created_time": "2026-10-21T20:00:00Z", "action": "buy", "side": "yes", "yes_price": 60,
        "no_price": 40, "count": 10, "is_taker": True,
    }
    base.update(over)
    return base


# ---- normalisation ------------------------------------------------------------------------------------


def test_normalize_yes_buy():
    f = normalize_kalshi_fill(raw_fill())
    assert f.fill_id == "t1" and f.order_id == "o1" and f.ticker == WINNER
    assert f.ts_utc == T0 and f.action == FillAction.BUY and f.side == "yes"
    assert f.price_cents == 60 and f.count == 10 and f.fee_cents == 0 and f.is_taker is True and f.source == "kalshi"


def test_normalize_no_side_uses_no_price_and_tolerates_missing_fields():
    f = normalize_kalshi_fill({"fill_id": "f9", "ticker": WINNER, "created_time": "2026-10-21T20:00:00+00:00", "action": "SELL", "side": "No", "no_price": "41", "count": "3"})
    assert f.fill_id == "f9" and f.order_id is None and f.action == FillAction.SELL and f.side == "no"
    assert f.price_cents == 41 and f.count == 3 and f.is_taker is None


def test_normalize_price_fallbacks_and_fees():
    f = normalize_kalshi_fill(raw_fill(yes_price=None, no_price=None, price=57, fee_cents=3))
    assert f.price_cents == 57 and f.fee_cents == 3
    f = normalize_kalshi_fill(raw_fill(yes_price=None, yes_price_dollars="0.6100", fee_cents=None, fee_dollars="0.02"))
    assert f.price_cents == 61 and f.fee_cents == 2
    f = normalize_kalshi_fill(raw_fill(trade_id=None, fill_id=None))
    assert f.fill_id.startswith("synthetic:")
    assert f.fill_id == normalize_kalshi_fill(raw_fill(trade_id=None, fill_id=None)).fill_id  # deterministic


@pytest.mark.parametrize("bad", [{"side": "maybe"}, {"action": "hold"}, {"ticker": None}, {"created_time": None}, {"yes_price": None, "no_price": None}, {"yes_price": 140}])
def test_normalize_rejects_bad_fields(bad):
    with pytest.raises(ValueError):
        normalize_kalshi_fill(raw_fill(**bad))


# ---- routing ----------------------------------------------------------------------------------------


def test_nba_ticker_detection_and_routing():
    assert is_nba_ticker(WINNER) and is_nba_ticker("KXNBA1HSPREAD-26OCT21NYKBOS-BOS3")
    assert not is_nba_ticker(NFL) and not is_nba_ticker("")
    nba, other = route_fills([normalize_kalshi_fill(raw_fill()), normalize_kalshi_fill(raw_fill(trade_id="t2", ticker=NFL))])
    assert [f.ticker for f in nba] == [WINNER] and [f.ticker for f in other] == [NFL]


# ---- positions ----------------------------------------------------------------------------------------


def _fill(fid: str, minutes: int, action: str, count: int, price: int, side: str = "yes", ticker: str = WINNER) -> Fill:
    return Fill(fill_id=fid, order_id=None, ticker=ticker, ts_utc=T0 + timedelta(minutes=minutes), action=FillAction(action), side=side, price_cents=price, count=count, fee_cents=1)


def test_positions_net_buys_and_sells_with_average_price():
    fills = [_fill("a", 0, "buy", 10, 40), _fill("b", 1, "buy", 10, 50), _fill("c", 2, "sell", 5, 70), _fill("n", 3, "buy", 4, 30, side="no")]
    pos = positions_from_fills(fills, as_of=T0 + timedelta(hours=1))
    assert set(pos) == {position_key(WINNER, "yes"), position_key(WINNER, "no")}
    yes = pos[position_key(WINNER, "yes")]
    assert yes.net_contracts == 15 and yes.avg_price_cents == pytest.approx(45.0) and yes.total_fees_cents == 3 and len(yes.fills) == 3
    no = pos[position_key(WINNER, "no")]
    assert no.net_contracts == 4 and no.avg_price_cents == 30.0
    # as_of excludes later fills
    early = positions_from_fills(fills, as_of=T0 + timedelta(seconds=30))
    assert early[position_key(WINNER, "yes")].net_contracts == 10 and position_key(WINNER, "no") not in early


def test_positions_oversell_is_warned_or_raised():
    fills = [_fill("a", 0, "buy", 5, 40), _fill("b", 1, "sell", 8, 60)]
    warnings: list[str] = []
    pos = positions_from_fills(fills, as_of=T0 + timedelta(hours=1), warnings=warnings)
    assert pos[position_key(WINNER, "yes")].net_contracts == 0 and pos[position_key(WINNER, "yes")].avg_price_cents == 0.0
    assert len(warnings) == 1 and "exceeds open" in warnings[0]
    with pytest.raises(ValueError):
        positions_from_fills(fills, as_of=T0 + timedelta(hours=1), strict=True)


# ---- ledger import ------------------------------------------------------------------------------------


def test_import_dedupes_and_routes(tmp_path):
    path = tmp_path / "fills.jsonl"
    rows = [raw_fill(), raw_fill(trade_id="t2", count=4), raw_fill(), raw_fill(trade_id="t3", ticker=NFL), {"ticker": WINNER, "action": "buy", "side": "yes", "yes_price": 50, "count": 1}]
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    led = Ledger(tmp_path / "archive", run_id="r1")
    routed: list[Fill] = []
    rejected: list[dict] = []
    assert import_fills_jsonl(path, led, routed_elsewhere=routed, rejected=rejected, now=T0) == 2
    assert [f.ticker for f in routed] == [NFL]
    assert len(rejected) == 1 and "timestamp" in rejected[0]["reason"]
    stored = list(led.iter_rows("fills"))
    assert sorted(r["fill_id"] for r in stored) == ["t1", "t2"] and stored[0]["price_cents"] == 60

    # second import of the same file (plus one new fill) adds only the new one; already-normalised rows are accepted too
    path2 = tmp_path / "fills2.jsonl"
    new = normalize_kalshi_fill(raw_fill(trade_id="t4", created_time="2026-10-21T21:00:00Z")).model_dump(mode="json")
    path2.write_text("\n".join(json.dumps(r) for r in [*rows[:2], new]) + "\n")
    assert import_fills_jsonl(path2, led, now=T0 + timedelta(hours=1)) == 1
    assert sorted(r["fill_id"] for r in led.iter_rows("fills")) == ["t1", "t2", "t4"]
    assert import_fills_jsonl(path2, led, now=T0 + timedelta(hours=2)) == 0
    assert led.verify() == []


# ---- matching ------------------------------------------------------------------------------------------


def test_match_fills_to_latest_live_prediction():
    preds = [prediction_row("p1", TIP - timedelta(hours=3), p_production=0.65), prediction_row("p2", TIP - timedelta(hours=1), p_production=0.55)]
    fills = [
        _fill("early", -300, "buy", 1, 60),  # 5h before tip: before any prediction
        _fill("mid", -120, "buy", 2, 60),  # 2h before tip: p1 is live
        _fill("late", -30, "buy", 3, 62, side="no"),  # 30 min before tip: p2 is live
        _fill("other", -30, "buy", 1, 50, ticker="KXNBAPTS-26OCT21NYKBOS-X"),
        _fill("nfl", -30, "buy", 1, 50, ticker=NFL),
    ]
    # fills are stamped relative to T0; TIP - T0 = 3h30 so shift them onto the TIP clock
    fills = [f.model_copy(update={"ts_utc": TIP + timedelta(minutes=int((f.ts_utc - T0).total_seconds() // 60))}) for f in fills]
    out = match_fills_to_predictions(fills, preds)
    matched = {m["fill_id"]: m for m in out["matched"]}
    assert set(matched) == {"mid", "late"}
    assert matched["mid"]["prediction_id"] == "p1" and matched["mid"]["p_production"] == 0.65
    assert matched["mid"]["implied_edge"] == pytest.approx(0.05)  # YES at 60c with p=0.65
    assert matched["late"]["prediction_id"] == "p2" and matched["late"]["implied_edge"] == pytest.approx(0.45 - 0.62)  # NO at 62c with p_no=0.45
    reasons = {u["fill_id"]: u["reason"] for u in out["unmatched"]}
    assert reasons == {"early": "no_prediction_before_fill", "other": "no_prediction_for_ticker"}
    assert [r["fill_id"] for r in out["routed_elsewhere"]] == ["nfl"]


def test_implied_edge_sign_for_sells():
    f = _fill("s", 0, "sell", 1, 70)
    assert implied_edge(f, 0.65) == pytest.approx(0.05)  # sold YES at 70c when worth 65c
    assert implied_edge(f, None) is None
