"""A malformed 200 response must fail one request, not the whole capture."""

from __future__ import annotations

import httpx
import pytest

from nba_edge.archive import capture as C
from nba_edge.config import Settings
from nba_edge.kalshi.client import KalshiClient, KalshiError, RateLimiter


def _client(handler, retries=2):
    cfg = Settings(kalshi_base_url="https://kalshi.test/trade-api/v2", http_max_retries=retries)
    return KalshiClient(cfg=cfg, rate=RateLimiter(rate_per_s=1e9), transport=httpx.MockTransport(handler))


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(KalshiClient, "_sleep", staticmethod(lambda attempt, retry_after=None: None))


def test_a_non_json_200_is_retried_and_then_recovers():
    calls = []

    def handler(req):
        calls.append(1)
        return httpx.Response(200, text="<html>maintenance</html>") if len(calls) < 3 else httpx.Response(200, json={"markets": [{"ticker": "T"}], "cursor": ""})

    assert [m["ticker"] for m in _client(handler).iter_markets(series_ticker="S")] == ["T"] and len(calls) == 3


def test_a_persistently_non_json_200_surfaces_as_kalshi_error_not_json_decode_error():
    with pytest.raises(KalshiError):
        list(_client(lambda req: httpx.Response(200, text="not json")).iter_markets(series_ticker="S"))


def test_one_bad_series_response_does_not_abort_the_capture():
    """The capture catches KalshiError per series. A JSONDecodeError escaped that handler and killed all 300 series."""
    def handler(req):
        if req.url.params.get("series_ticker") == "BAD":
            return httpx.Response(200, text="oops")
        return httpx.Response(200, json={"markets": [{"ticker": "KXNBAGAME-26OCT24AAABBB-AAA", "event_ticker": "e", "status": "active", "title": "t"}], "cursor": ""})

    rows = C.snapshot_markets(_client(handler, retries=1), ["GOOD", "BAD"], ["open"], C.Ontology.load())
    assert [r["ticker"] for r in rows if "ticker" in r] == ["KXNBAGAME-26OCT24AAABBB-AAA"]
    assert [r["series_ticker"] for r in rows if "_error" in r] == ["BAD"]
