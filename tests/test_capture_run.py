"""End-to-end `run_capture` against a stub Kalshi client: interrupted collection, timestamps, and archive integrity.

These are the cases the unit tests around `snapshot_markets` never exercised: what is written to the immutable archive and to
STATUS_capture.json when a series fetch fails halfway, and which instants a point-in-time reader can rely on.
"""

from __future__ import annotations

import json

import pytest

from nba_edge.archive import capture as C
from nba_edge.archive.ledger import Ledger
from nba_edge.archive.reconstruct import latest_board, verify_archive
from nba_edge.kalshi.client import KalshiError

GAME = {"ticker": "KXNBAGAME-26OCT24BKNCLE-BKN", "event_ticker": "KXNBAGAME-26OCT24BKNCLE", "status": "active", "title": "Brooklyn wins",
        "yes_bid_dollars": "0.4000", "yes_ask_dollars": "0.4200", "no_bid_dollars": "0.5800", "no_ask_dollars": "0.6000", "series_ticker": "KXNBAGAME"}
PTS = {"ticker": "KXNBAPTS-26OCT24BKNCLE-BKNDSHARPE20-10", "event_ticker": "KXNBAPTS-26OCT24BKNCLE", "status": "active", "title": "Sharpe: 10+ points",
       "yes_bid_dollars": "0.3000", "yes_ask_dollars": "0.3500", "no_bid_dollars": "0.6500", "no_ask_dollars": "0.7000", "series_ticker": "KXNBAPTS"}
BOOK = {"orderbook_fp": {"yes_dollars": [["0.4000", "100.00"]], "no_dollars": [["0.5800", "50.00"]]}}


class Stub:
    """Class-level knobs so each test configures the client the code under test constructs for itself."""
    fail_series: set[str] = set()
    fail_books: bool = False
    truncate = False

    def __init__(self, cfg=None):
        self.request_count = 0
        self.truncations = []

    def iter_markets(self, series_ticker=None, status=None, max_pages=None, **kw):
        self.request_count += 1
        if series_ticker in self.fail_series:
            raise KalshiError(f"HTTP 503 /markets series={series_ticker}")
        if status == "open":
            if series_ticker == "KXNBAGAME":
                yield dict(GAME)
            if series_ticker == "KXNBAPTS":
                yield dict(PTS)
        if self.truncate:
            self.truncations.append({"endpoint": "/markets", "series_ticker": series_ticker})

    def get_orderbook(self, ticker, depth=10):
        self.request_count += 1
        if self.fail_books:
            raise KalshiError("HTTP 500")
        return BOOK


@pytest.fixture(autouse=True)
def clock(monkeypatch):
    """Every utcnow() call advances a minute, so two captures never share a tick instant (a delta must be strictly after its base)."""
    from datetime import UTC, datetime, timedelta

    state = {"t": datetime(2026, 10, 24, 18, 0, tzinfo=UTC)}

    def now():
        state["t"] += timedelta(minutes=1)
        return state["t"]

    monkeypatch.setattr(C, "utcnow", now)


@pytest.fixture
def stub(monkeypatch):
    class S(Stub):
        fail_series = set()
        fail_books = False
        truncate = False
    monkeypatch.setattr(C, "KalshiClient", S)
    return S


def _status(root):
    return json.loads((root / "STATUS_capture.json").read_text())


def _meta(root, kind):
    return [e.meta for e in Ledger(root, run_id="r").manifest() if e.kind == kind]


def test_a_clean_capture_records_the_three_instants_and_no_alarms(tmp_path, stub):
    assert C.run_capture(tmp_path, ["open"], True, max_orderbooks=5, series_filter=["KXNBAGAME", "KXNBAPTS"]) == 0
    st = _status(tmp_path)
    assert st["collection_alarms"] == [] and st["n_fetch_errors"] == 0
    w = st["observation_window"]
    assert w["capture_started_utc"] <= w["markets_fetched_utc"] <= w["books_fetched_utc"]
    (mm,) = _meta(tmp_path, "kalshi/markets")
    (bm,) = _meta(tmp_path, "kalshi/orderbooks")
    assert mm["complete"] is True and mm["markets_fetched_utc"] >= mm["capture_started_utc"]
    assert bm["books_fetched_utc"] >= mm["markets_fetched_utc"] and bm["selection_policy"]


def test_a_failed_series_is_flagged_in_the_archive_and_never_fabricated(tmp_path, stub):
    stub.fail_series = {"KXNBAPTS"}
    assert C.run_capture(tmp_path, ["open"], False, series_filter=["KXNBAGAME", "KXNBAPTS"]) == 0
    st = _status(tmp_path)
    assert st["n_fetch_errors"] == 1 and any("MISSING" in a for a in st["collection_alarms"])
    (mm,) = _meta(tmp_path, "kalshi/markets")
    assert mm["complete"] is False and mm["n_fetch_errors"] == 1 and mm["fetch_errors"][0]["series_ticker"] == "KXNBAPTS"
    board = latest_board(Ledger(tmp_path, run_id="r"))
    assert {r["ticker"] for r in board.rows if "ticker" in r} == {GAME["ticker"]}, "the failed series' markets are absent, not carried forward or invented"


def test_a_recovered_series_after_a_partial_tick_keeps_the_delta_chain_verifiable(tmp_path, stub):
    stub.fail_series = {"KXNBAPTS"}
    C.run_capture(tmp_path, ["open"], False, series_filter=["KXNBAGAME", "KXNBAPTS"])
    stub.fail_series = set()
    C.run_capture(tmp_path, ["open"], False, series_filter=["KXNBAGAME", "KXNBAPTS"])  # second tick is a delta against the partial one
    led = Ledger(tmp_path, run_id="r")
    assert [e.meta.get("encoding") for e in led.manifest() if e.kind.startswith("kalshi/markets")] == ["checkpoint", "delta"]
    assert led.verify() == []
    rep = verify_archive(tmp_path)
    assert not rep.get("problems") if isinstance(rep, dict) else True
    board = latest_board(led)
    assert {r["ticker"] for r in board.rows} == {GAME["ticker"], PTS["ticker"]}


def test_pagination_cutoff_and_book_outage_are_collection_alarms(tmp_path, stub):
    stub.truncate = True
    stub.fail_books = True
    C.run_capture(tmp_path, ["open"], True, max_orderbooks=5, series_filter=["KXNBAGAME", "KXNBAPTS"])
    joined = " | ".join(_status(tmp_path)["collection_alarms"])
    assert "live cursor" in joined and "order-book" in joined
    assert _meta(tmp_path, "kalshi/orderbooks")[0]["n_errors"] == 2
