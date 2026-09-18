import math

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nba_edge.kalshi.fees import (
    BASE_MAKER_MULTIPLIER,
    BASE_TAKER_MULTIPLIER,
    FeeSchedule,
    fee_per_contract_dollars,
    maker_fee_cents,
    taker_fee_cents,
)


def test_taker_fee_single_contract_at_50c():
    assert taker_fee_cents(50, 1) == 2  # ceil(0.07 * 1 * 0.25 * 100) = ceil(1.75)


def test_taker_fee_rounds_up_on_whole_order_not_per_contract():
    assert taker_fee_cents(50, 10) == 18  # ceil(17.5), not 10 * 2


def test_fees_tiny_at_extremes():
    assert taker_fee_cents(1, 1) == 1  # ceil(0.0693)
    assert taker_fee_cents(99, 1) == 1
    assert taker_fee_cents(1, 100) == 7  # 0.07 * 100 * 0.0099 * 100 = 6.93
    assert taker_fee_cents(0, 5) == 0
    assert taker_fee_cents(100, 5) == 0


def test_zero_contracts_is_free():
    assert taker_fee_cents(50, 0) == 0
    assert maker_fee_cents(50, 0) == 0


def test_maker_cheaper_than_taker():
    for price in (10, 35, 50, 77):
        assert maker_fee_cents(price, 100) < taker_fee_cents(price, 100)
    assert maker_fee_cents(50, 1) == 1  # ceil(0.4375)
    assert maker_fee_cents(50, 100) == 44  # ceil(43.75)


@pytest.mark.parametrize("price", [1, 10, 25, 40, 49])
def test_fee_symmetric_in_price(price):
    for n in (1, 7, 100):
        assert taker_fee_cents(price, n) == taker_fee_cents(100 - price, n)
        assert maker_fee_cents(price, n) == maker_fee_cents(100 - price, n)


def test_no_float_noise_at_exact_half_cents():
    # 0.07 * 10 * 0.5 * 0.5 * 100 == 17.5 exactly in the decimal world; float noise must not give 19.
    assert taker_fee_cents(50, 10) == 18
    assert taker_fee_cents(50, 20) == 35  # exactly 35.0 -> must not become 36


def test_invalid_inputs():
    with pytest.raises(ValueError):
        taker_fee_cents(101, 1)
    with pytest.raises(ValueError):
        taker_fee_cents(50, -1)


def test_fee_per_contract_continuous():
    assert fee_per_contract_dollars(50) == pytest.approx(0.0175)
    assert fee_per_contract_dollars(50, taker=False) == pytest.approx(0.004375)
    assert fee_per_contract_dollars(0) == 0.0
    assert fee_per_contract_dollars(30) == pytest.approx(fee_per_contract_dollars(70))


@given(st.integers(min_value=0, max_value=100), st.integers(min_value=1, max_value=500))
def test_order_fee_is_ceiling_of_continuous_fee(price, n):
    cont = fee_per_contract_dollars(price) * n * 100
    got = taker_fee_cents(price, n)
    assert got >= cont - 1e-6
    assert got < cont + 1.0 + 1e-6
    assert got == math.ceil(round(cont, 9))


# ---- FeeSchedule.from_series -----------------------------------------------------------------------


def test_schedule_default_when_no_series():
    s = FeeSchedule.from_series(None)
    assert (s.taker_multiplier, s.maker_multiplier, s.source) == (0.07, 0.0175, "default")
    s = FeeSchedule.from_series({"ticker": "KXNBAGAME", "fee_type": "quadratic"})
    assert s.source == "default"
    assert s.series_ticker == "KXNBAGAME"


def test_schedule_multiple_of_base():
    s = FeeSchedule.from_series({"ticker": "X", "fee_multiplier": 1.0})
    assert s.source == "series:multiple_of_base"
    assert s.taker_multiplier == pytest.approx(BASE_TAKER_MULTIPLIER)
    assert s.maker_multiplier == pytest.approx(BASE_MAKER_MULTIPLIER)
    half = FeeSchedule.from_series({"ticker": "X", "fee_multiplier": 0.5})
    assert half.taker_multiplier == pytest.approx(0.035)
    assert taker_fee_cents(50, 100, half) == 88  # ceil(87.5)


def test_schedule_absolute_rate():
    s = FeeSchedule.from_series({"ticker": "X", "fee_multiplier": 0.07})
    assert s.source == "series:absolute_rate"
    assert s.taker_multiplier == pytest.approx(0.07)
    assert s.maker_multiplier == pytest.approx(0.0175)
    s2 = FeeSchedule.from_series({"ticker": "X", "fee_multiplier": 0.035})
    assert s2.taker_multiplier == pytest.approx(0.035)


def test_schedule_out_of_range_falls_back_and_flags():
    s = FeeSchedule.from_series({"ticker": "X", "fee_multiplier": 7.0})
    assert s.source == "default:ignored_out_of_range"
    assert s.taker_multiplier == 0.07


def test_schedule_garbage_multiplier_is_default():
    assert FeeSchedule.from_series({"fee_multiplier": "abc"}).source == "default"
    assert FeeSchedule.from_series({"fee_multiplier": 0}).source == "default"
    assert FeeSchedule.from_series({"fee_multiplier": -1}).source == "default"
