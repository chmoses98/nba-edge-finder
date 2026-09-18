from datetime import UTC, datetime, timedelta

import pytest

from nba_edge.evaluation.clv import closing_snapshot, clv_cents, clv_prob, pregame_filter
from nba_edge.schemas.market import MarketSnapshot, Side

TIP = datetime(2026, 10, 22, 0, 10, tzinfo=UTC)


def snap(minutes_before_tip: float, yes_bid: int = 50) -> MarketSnapshot:
    return MarketSnapshot(
        ticker="T",
        event_ticker="E",
        series_ticker="S",
        observed_at_utc=TIP - timedelta(minutes=minutes_before_tip),
        status="open",
        title="t",
        yes_bid=yes_bid,
    )


def test_clv_cents_and_prob_sign_by_side():
    assert clv_cents(40, 55, Side.YES) == 15
    assert clv_cents(40, 55, "no") == -15
    assert clv_cents(60, 45, Side.NO) == 15
    assert clv_prob(40, 55, "yes") == pytest.approx(0.15)
    with pytest.raises(ValueError):
        clv_cents(101, 50, Side.YES)


def test_pregame_filter_drops_post_tip_and_equal_to_tip():
    obs = [snap(30), snap(5), snap(0), snap(-10)]
    kept, dropped = pregame_filter(obs, TIP)
    assert dropped == 2
    assert [o.observed_at_utc for o in kept] == [TIP - timedelta(minutes=30), TIP - timedelta(minutes=5)]


def test_pregame_filter_accepts_dicts_with_iso_strings():
    obs = [{"observed_at_utc": "2026-10-22T00:00:00Z"}, {"_observed_at_utc": "2026-10-22T00:10:00Z"}]
    kept, dropped = pregame_filter(obs, TIP)
    assert len(kept) == 1 and dropped == 1


def test_closing_snapshot_is_last_strictly_before_tip():
    obs = [snap(30, 40), snap(0, 99), snap(2, 52), snap(15, 45), snap(-5, 98)]
    close = closing_snapshot(obs, TIP)
    assert close is not None and close.yes_bid == 52
    assert closing_snapshot([snap(0), snap(-1)], TIP) is None
    assert closing_snapshot([], TIP) is None


def test_naive_tip_rejected():
    with pytest.raises(ValueError):
        pregame_filter([snap(1)], datetime(2026, 10, 22))
