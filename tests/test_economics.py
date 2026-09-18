from datetime import UTC, datetime, timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nba_edge.execution.economics import (
    DEFAULT_SCHEDULE,
    EconomicsConfig,
    bet_up_to_cents,
    compute_economics,
    ev_per_contract,
    kelly_fraction,
    market_implied_probability,
    normalize_quotes,
)
from nba_edge.kalshi.fees import fee_per_contract_dollars

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def snap(**kw):
    base = {"yes_bid": 48, "yes_ask": 50, "no_bid": 50, "no_ask": 52, "observed_at_utc": NOW}
    base.update(kw)
    return base


# ---- quotes ------------------------------------------------------------------------------------------


def test_normalize_quotes_derives_missing_sides():
    q = normalize_quotes({"yes_bid": 40, "yes_ask": 45})
    assert (q.no_bid, q.no_ask) == (55, 60)
    q = normalize_quotes({"no_bid": 55, "no_ask": 60})
    assert (q.yes_bid, q.yes_ask) == (40, 45)
    assert q.spread_cents == 5


def test_normalize_quotes_treats_empty_book_as_missing():
    q = normalize_quotes({"yes_bid": 0, "yes_ask": 100})
    assert q == normalize_quotes({})
    assert q.yes_ask is None and q.no_ask is None


def test_market_implied_probability_mid_then_last_then_none():
    m = market_implied_probability({"yes_bid": 40, "yes_ask": 44})
    assert m.p_mid == pytest.approx(0.42)
    assert (m.p_market_bid, m.p_market_ask, m.source) == (0.40, 0.44, "mid")
    m = market_implied_probability({"yes_bid": 40, "last_price": 41})
    assert (m.p_mid, m.source) == (0.41, "last")
    assert m.p_market_bid == 0.40 and m.p_market_ask is None
    m = market_implied_probability({})
    assert (m.p_mid, m.source) == (None, "none")


# ---- EV math -----------------------------------------------------------------------------------------


def test_ev_at_p60_price50():
    e = compute_economics(snap(yes_ask=50), p_fair=0.6, now=NOW)
    fee = fee_per_contract_dollars(50)
    assert e.yes.gross_edge == pytest.approx(0.10)
    assert e.yes.ev_per_contract == pytest.approx(0.10 - fee)
    assert e.yes.fee_per_contract == pytest.approx(0.0175)
    assert e.yes.roi == pytest.approx((0.10 - fee) / 0.5)
    assert e.yes.implied_prob == 0.5
    assert e.best_side == "yes"
    assert e.no.ev_per_contract < 0


def test_bet_up_to_below_fair_and_decreasing_in_min_edge():
    up0 = bet_up_to_cents(0.6)
    assert up0 is not None and up0 < 60
    up1 = bet_up_to_cents(0.6, min_edge=0.01)
    up2 = bet_up_to_cents(0.6, min_edge=0.03)
    assert up0 > up1 > up2
    assert bet_up_to_cents(0.5) < 50
    assert bet_up_to_cents(0.6, min_edge=0.99) is None


def test_bet_up_to_is_consistent_with_ev():
    for p in (0.1, 0.35, 0.5, 0.72, 0.95):
        c = bet_up_to_cents(p)
        assert c is not None
        assert ev_per_contract(p, c, DEFAULT_SCHEDULE) >= 0
        if c < 99:
            assert ev_per_contract(p, c + 1, DEFAULT_SCHEDULE) < 0


def test_kelly_zero_when_no_edge_and_positive_with_edge():
    assert kelly_fraction(0.5, 50, DEFAULT_SCHEDULE) == 0.0
    k = kelly_fraction(0.6, 50, DEFAULT_SCHEDULE)
    assert 0 < k < 0.2
    e = compute_economics(snap(yes_ask=50), p_fair=0.6, now=NOW)
    assert e.yes.kelly_full == pytest.approx(k)
    assert e.yes.kelly_fraction == pytest.approx(0.25 * k)
    e2 = compute_economics(snap(yes_ask=50), 0.6, config=EconomicsConfig(kelly_multiplier=0.5), now=NOW)
    assert e2.yes.kelly_fraction == pytest.approx(0.5 * k)


def test_yes_no_symmetry():
    a = compute_economics({"yes_bid": 30, "yes_ask": 34, "no_bid": 66, "no_ask": 70}, p_fair=0.25, now=NOW)
    b = compute_economics({"yes_bid": 66, "yes_ask": 70, "no_bid": 30, "no_ask": 34}, p_fair=0.75, now=NOW)
    assert a.no.price_cents == 70 == b.yes.price_cents
    assert a.no.ev_per_contract == pytest.approx(b.yes.ev_per_contract)
    assert a.no.kelly_full == pytest.approx(b.yes.kelly_full)
    assert a.no.bet_up_to_cents == b.yes.bet_up_to_cents
    assert a.best_side == "no" and b.best_side == "yes"


def test_min_edge_blocks_marginal_recommendation():
    e = compute_economics(snap(yes_ask=50), 0.6, config=EconomicsConfig(min_edge=0.5), now=NOW)
    assert e.best_side is None
    assert any(r.startswith("no_edge") for r in e.reasons)


# ---- flags -------------------------------------------------------------------------------------------


def test_missing_quotes_flag_and_no_best_side():
    e = compute_economics({"observed_at_utc": NOW}, p_fair=0.9, now=NOW)
    assert e.no_quote is True
    assert e.best_side is None
    assert e.yes.price_cents is None and e.yes.ev_per_contract is None
    assert e.yes.bet_up_to_cents is not None  # still useful for resting an order
    assert any(r.startswith("no_quote") for r in e.reasons)


def test_one_sided_book_flags_no_quote_but_prices_other_side():
    # Only a YES bid: we can buy NO at 100 - yes_bid but cannot buy YES.
    e = compute_economics({"yes_bid": 40, "observed_at_utc": NOW}, p_fair=0.3, now=NOW)
    assert e.no_quote is True
    assert e.no.price_cents == 60
    assert e.yes.price_cents is None


def test_wide_spread_flag():
    e = compute_economics(snap(yes_bid=40, yes_ask=50, no_bid=50, no_ask=60), 0.55, now=NOW)
    assert e.spread_cents == 10 and e.wide_spread is True
    e = compute_economics(snap(yes_bid=44, yes_ask=50, no_bid=50, no_ask=56), 0.55, now=NOW)
    assert e.spread_cents == 6 and e.wide_spread is False


def test_stale_flag_suppresses_recommendation():
    old = NOW - timedelta(minutes=30)
    e = compute_economics(snap(observed_at_utc=old), 0.7, now=NOW)
    assert e.stale is True and e.best_side is None
    fresh = compute_economics(snap(), 0.7, observed_at=NOW - timedelta(minutes=1), now=NOW)
    assert fresh.stale is False and fresh.best_side == "yes"


def test_thin_flag():
    e = compute_economics(snap(liquidity=500, volume=2), 0.7, now=NOW)
    assert e.thin is True
    assert sum(r.startswith("thin") for r in e.reasons) == 2
    e = compute_economics(snap(liquidity=50_000, volume=100), 0.7, now=NOW)
    assert e.thin is False


def test_accepts_pydantic_snapshot():
    from nba_edge.schemas.market import MarketSnapshot

    ms = MarketSnapshot(
        ticker="T", event_ticker="E", series_ticker="S", observed_at_utc=NOW, status="open", title="t",
        yes_bid=48, yes_ask=50, no_bid=50, no_ask=52,
    )
    e = compute_economics(ms, 0.6, now=NOW)
    assert e.best_side == "yes"
    assert e.market.p_mid == pytest.approx(0.49)


def test_invalid_p_fair():
    with pytest.raises(ValueError):
        compute_economics(snap(), 1.2, now=NOW)


# ---- property: gross parts cancel across YES@q and NO@(100-q) ------------------------------------------


@given(
    st.floats(min_value=0.01, max_value=0.99),
    st.integers(min_value=1, max_value=99),
)
def test_ev_yes_plus_ev_no_equals_minus_fees(p, q):
    ev_yes = ev_per_contract(p, q, DEFAULT_SCHEDULE)
    ev_no = ev_per_contract(1.0 - p, 100 - q, DEFAULT_SCHEDULE)
    fees = fee_per_contract_dollars(q) + fee_per_contract_dollars(100 - q)
    assert ev_yes + ev_no == pytest.approx(-fees, abs=1e-12)


@given(st.floats(min_value=0.01, max_value=0.99), st.integers(min_value=1, max_value=99))
def test_compute_economics_never_recommends_negative_ev(p, q):
    e = compute_economics({"yes_bid": q, "yes_ask": q, "no_bid": 100 - q, "no_ask": 100 - q}, p, now=NOW)
    if e.best_side is not None:
        assert e.best.ev_per_contract > 0
        other = e.side("no" if e.best_side == "yes" else "yes")
        assert e.best.ev_per_contract >= other.ev_per_contract


# --- pre-merge audit regressions -------------------------------------------------


def test_zero_is_a_real_probability_not_a_missing_one():
    """0.0 must price as 0.0. It used to become 0.5 and recommend a buy.

    The slate computed ``p_data or 0.5``. A deep-OTM ladder leg is legitimately priced at exactly
    0.0 by the simulator, and 0.0 is falsy, so the fair value silently became a coin flip. On a
    one-sided book (an ask, no bid, never traded) the market midpoint is None, so the hybrid is None
    too and that fabricated 0.5 went straight into the economics -- turning a contract the model
    calls worthless into positive EV and a recommendation to buy.
    """
    from nba_edge.execution.economics import EconomicsConfig, compute_economics

    snap = {"yes_bid": None, "yes_ask": 5, "no_bid": None, "no_ask": None, "last_price": None,
            "volume": 5000, "open_interest": 5000, "liquidity": 500_000, "observed_at_utc": None}

    honest = compute_economics(snap, 0.0, 0.0, config=EconomicsConfig())
    assert honest.p_fair == 0.0
    assert honest.best_side is None, "a contract the model prices at zero must never be recommended"
    assert honest.yes.ev_per_contract < 0
    assert honest.yes.bet_up_to_cents is None

    fabricated = compute_economics(snap, 0.5, 0.0, config=EconomicsConfig())
    assert fabricated.best_side == "yes" and fabricated.yes.ev_per_contract > 0.4, (
        "this is what the bug produced; it is here so the two are never confused again"
    )


def test_crossed_books_are_refused_not_traded():
    """An impossible book is a corrupt observation, not free money."""
    from nba_edge.execution.economics import EconomicsConfig, compute_economics

    base = {"last_price": None, "volume": 5000, "open_interest": 5000, "liquidity": 500_000, "observed_at_utc": None}

    # ask below bid: spread is -20c, which the wide_spread test (spread > 6) could never catch
    crossed = compute_economics({**base, "yes_bid": 60, "yes_ask": 40, "no_bid": None, "no_ask": None}, 0.60, 0.0, config=EconomicsConfig())
    assert crossed.crossed and crossed.best_side is None
    assert crossed.yes.ev_per_contract > 0, "the phantom edge is still computed; it just must not be actionable"
    assert any("crossed" in r for r in crossed.reasons)

    # both asks under a dollar: buying both sides would pay you to hold a certainty
    both = compute_economics({**base, "yes_bid": 60, "yes_ask": 40, "no_bid": 55, "no_ask": 35}, 0.50, 0.0, config=EconomicsConfig())
    assert both.crossed and both.best_side is None
    assert both.yes.ev_per_contract > 0 and both.no.ev_per_contract > 0, (
        "the giveaway: a coherent book can never make both sides profitable at once"
    )

    # a normal book is untouched
    sane = compute_economics({**base, "yes_bid": 40, "yes_ask": 42, "no_bid": 56, "no_ask": 58}, 0.60, 0.0, config=EconomicsConfig())
    assert not sane.crossed and sane.best_side == "yes"
