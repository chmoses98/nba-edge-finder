"""§5.14: simulate must read Kalshi's dollar-denominated quote fields (and the capture-time ``_quote_cents``), not bare ``yes_bid``."""

import json
from datetime import UTC, datetime

import pytest

from nba_edge.archive.ledger import Ledger
from nba_edge.execution.economics import compute_economics, market_implied_probability
from nba_edge.kalshi.fees import DEFAULT_SCHEDULE
from nba_edge.workflows.simulate import (
    QUOTE_FIX_ENV,
    legacy_market_snapshot,
    market_snapshot,
    quote_fix_enabled,
    run_simulate,
)
from tests.test_simulate_job import FIX, _archive, _history  # noqa: F401

DOLLARS = {"yes_bid_dollars": "0.6000", "yes_ask_dollars": "0.6200", "no_bid_dollars": "0.3800", "no_ask_dollars": "0.4000", "last_price_dollars": "0.6100",
           "volume_fp": "1200.00", "open_interest_fp": "800.00", "_observed_at_utc": "2026-10-20T17:57:00Z"}
Q = ("yes_bid", "yes_ask", "no_bid", "no_ask")


def test_fix_is_off_by_default_and_legacy_snapshot_is_unchanged(monkeypatch):
    monkeypatch.delenv(QUOTE_FIX_ENV, raising=False)
    assert not quote_fix_enabled()
    s = legacy_market_snapshot(dict(DOLLARS))
    assert all(s[k] is None for k in (*Q, "last_price"))  # the documented pre-fix behaviour on dollar-denominated boards
    for v, on in (("1", True), ("true", True), ("0", False), ("", False), ("off", False)):
        monkeypatch.setenv(QUOTE_FIX_ENV, v)
        assert quote_fix_enabled() is on


def test_dollar_only_row_yields_cents_quotes():
    s = market_snapshot(dict(DOLLARS))
    assert (s["yes_bid"], s["yes_ask"], s["no_bid"], s["no_ask"], s["last_price"]) == (60, 62, 38, 40, 61)
    assert s["volume"] == 1200.0 and s["open_interest"] == 800.0 and s["observed_at_utc"] == "2026-10-20T17:57:00Z"


def test_captured_quote_cents_take_precedence_and_degenerate_levels_stay_none():
    s = market_snapshot({"_quote_cents": {"yes_bid": None, "yes_ask": 62, "no_bid": 38, "no_ask": None, "last_price": 61}, "yes_bid_dollars": "0.0000", "yes_ask_dollars": "0.6200"})
    assert (s["yes_bid"], s["yes_ask"], s["no_bid"], s["no_ask"]) == (None, 62, 38, None)


def test_legacy_bare_cent_rows_unchanged():
    s = market_snapshot({"yes_bid": 45, "yes_ask": 48, "no_bid": 52, "no_ask": 55, "volume": 10})
    assert (s["yes_bid"], s["yes_ask"], s["no_bid"], s["no_ask"]) == (45, 48, 52, 55)


def test_row_with_no_quote_stays_without_quote_nothing_invented():
    s = market_snapshot({"ticker": "X"})
    assert all(s[k] is None for k in (*Q, "last_price"))
    assert market_implied_probability(s).p_mid is None


def test_market_probability_and_economics_flow_from_dollar_quotes():
    s = market_snapshot(dict(DOLLARS))
    s.pop("observed_at_utc")  # simulate passes observed_at/now to compute_economics explicitly as datetimes
    assert market_implied_probability(s).p_mid == pytest.approx(0.61)
    econ = compute_economics(s, 0.70, 0.01, schedule=DEFAULT_SCHEDULE)
    assert econ.best_side == "yes" and econ.yes.ev_per_contract > 0 and econ.spread_cents == 2


def _dollarize(row):
    out = {k: v for k, v in row.items() if k not in Q}
    for k in Q:
        if row.get(k) is not None:
            out[f"{k}_dollars"] = f"{row[k] / 100:.4f}"
    return out


@pytest.mark.slow
def test_end_to_end_dollar_boards_match_legacy_cent_boards(tmp_path, monkeypatch):
    """Same market state expressed as legacy cents vs as Kalshi dollars -> identical prices/probabilities/EV/gates (the pre-fix path priced the dollars as no quote)."""
    now = datetime(2026, 10, 20, 18, 0, tzinfo=UTC)
    monkeypatch.setenv(QUOTE_FIX_ENV, "1")
    res = {}
    for name, convert in (("cents", lambda r: r), ("dollars", _dollarize)):
        root = tmp_path / name
        root.mkdir()
        _history(root)
        led = _archive(root, now)
        rows = list(led.iter_rows("kalshi/markets"))
        if name == "dollars":
            led2 = Ledger(root / "archive2", run_id="t")
            for fn in ("context/schedule", "context/rosters", "context/injuries"):
                led2.append_rows(fn, list(led.iter_rows(fn)), observed_at=now - __import__("datetime").timedelta(minutes=5))
            led2.append_rows("kalshi/markets", [convert(r) for r in rows], observed_at=now - __import__("datetime").timedelta(minutes=3))
            arch = root / "archive2"
        else:
            arch = root / "archive"
        assert run_simulate(arch, root, date="2026-10-20", n_sims=4000, seed=3, now=now) == 0
        res[name] = {c["ticker"]: c for c in json.loads((arch / "slates" / "latest" / "slate.json").read_text())["contracts"]}
    for t, a in res["cents"].items():
        b = res["dollars"][t]
        for k in (*Q, "p_market", "p_hybrid", "ev_yes", "ev_no", "best_side", "gate", "bet_up_to_yes", "bet_up_to_no"):
            assert a[k] == pytest.approx(b[k]) if isinstance(a[k], float) else a[k] == b[k], (t, k, a[k], b[k])


@pytest.mark.slow
def test_end_to_end_default_run_is_unchanged_on_dollar_boards(tmp_path, monkeypatch):
    """With the flag unset a dollar-only board still prices with no quote (nothing changes on merge)."""
    monkeypatch.delenv(QUOTE_FIX_ENV, raising=False)
    now = datetime(2026, 10, 20, 18, 0, tzinfo=UTC)
    _history(tmp_path)
    led = _archive(tmp_path, now)
    led2 = Ledger(tmp_path / "archive2", run_id="t")
    d5, d3 = now - __import__("datetime").timedelta(minutes=5), now - __import__("datetime").timedelta(minutes=3)
    for fn in ("context/schedule", "context/rosters", "context/injuries"):
        led2.append_rows(fn, list(led.iter_rows(fn)), observed_at=d5)
    led2.append_rows("kalshi/markets", [_dollarize(r) for r in led.iter_rows("kalshi/markets")], observed_at=d3)
    assert run_simulate(tmp_path / "archive2", tmp_path, date="2026-10-20", n_sims=2000, seed=3, now=now) == 0
    c = json.loads((tmp_path / "archive2" / "slates" / "latest" / "slate.json").read_text())["contracts"]
    assert all(r["yes_bid"] is None and r["p_market"] is None and r["best_side"] is None for r in c)
