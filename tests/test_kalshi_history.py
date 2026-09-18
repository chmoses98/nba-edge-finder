import gzip
import json
from pathlib import Path

import httpx

from nba_edge.config import Settings
from nba_edge.kalshi.client import KalshiClient, KalshiError, RateLimiter
from nba_edge.kalshi.history import build_team_uuid_map, merge_markets, run_kalshi_history

BOS = "11111111-1111-1111-1111-111111111111"
NYK = "22222222-2222-2222-2222-222222222222"


def _mkt(ticker, series, team_uuid, sub, title, result="yes", **extra):
    return {
        "ticker": ticker,
        "event_ticker": ticker.rsplit("-", 1)[0],
        "series_ticker": series,
        "title": title,
        "yes_sub_title": sub,
        "custom_strike": {"basketball_team": team_uuid},
        "status": "settled",
        "result": result,
        "open_time": "2025-11-01T00:00:00Z",
        "close_time": "2025-11-02T03:00:00Z",
        **extra,
    }


class FakeClient:
    """Same method names as KalshiClient; records calls."""

    def __init__(self, hist, live, candle_fail=(), hist_fail=()):
        self.hist, self.live = hist, live
        self.candle_fail, self.hist_fail = set(candle_fail), set(hist_fail)
        self.calls = []
        self.request_count = 0

    def iter_historical_markets(self, series_ticker=None, min_close_ts=None, max_close_ts=None, **kw):
        self.calls.append(("hist", series_ticker, min_close_ts, max_close_ts))
        self.request_count += 1
        if series_ticker in self.hist_fail:
            raise KalshiError("HTTP 404 /markets")
        yield from self.hist.get(series_ticker, [])

    def iter_markets(self, series_ticker=None, status=None, min_close_ts=None, max_close_ts=None, **kw):
        self.calls.append(("live", series_ticker, status))
        self.request_count += 1
        yield from self.live.get(series_ticker, [])

    def historical_candlesticks(self, ticker, start_ts, end_ts, period_interval=60):
        self.calls.append(("hcandle", ticker, start_ts, end_ts, period_interval))
        self.request_count += 1
        if ticker in self.candle_fail:
            raise KalshiError("HTTP 404 candles")
        return [{"end_period_ts": start_ts + 3600, "price": {"close": 55}}, {"end_period_ts": end_ts, "price": {"close": 99}}]

    def candlesticks(self, series_ticker, ticker, start_ts, end_ts, period_interval=60):
        self.calls.append(("lcandle", ticker))
        self.request_count += 1
        return [{"end_period_ts": end_ts, "price": {"close": 1}}]


def _read_gz(p: Path):
    with gzip.open(p, "rt") as f:
        return [json.loads(line) for line in f]


def test_run_kalshi_history_writes_files_and_merges_without_duplicates(tmp_path):
    hist = {
        "KXNBAGAME": [
            _mkt("KXNBAGAME-25NOV01BOSNYK-BOS", "KXNBAGAME", BOS, "Boston", "Boston wins", settlement_value=100),
            _mkt("KXNBAGAME-25NOV01BOSNYK-NYK", "KXNBAGAME", NYK, "New York", "New York wins", result="no"),
        ],
        "KXNBAWINS": [
            _mkt("KXNBAWINS-26BOS-50", "KXNBAWINS", BOS, "50+ wins",
                 "Will the Boston Pro Basketball team win at least 50 games in the 2025-26 regular season?"),
        ],
    }
    live = {
        "KXNBAGAME": [
            # same ticker as historical -> must merge, not duplicate; historical keys win
            _mkt("KXNBAGAME-25NOV01BOSNYK-BOS", "KXNBAGAME", BOS, "Boston", "Boston wins", result="", volume=123),
            _mkt("KXNBAGAME-25NOV03NYKBOS-NYK", "KXNBAGAME", NYK, "New York", "New York wins"),
        ],
    }
    fc = FakeClient(hist, live)
    rc = run_kalshi_history(
        out_root=tmp_path, series=["KXNBAGAME", "KXNBAWINS"], min_close="2025-10-01", max_close="2026-07-01",
        with_candles=True, candle_interval=60, max_markets_for_candles=2, client=fc,
    )
    assert rc == 0
    out = tmp_path / "kalshi"
    game = _read_gz(out / "markets_KXNBAGAME.jsonl.gz")
    tickers = [m["ticker"] for m in game]
    assert len(tickers) == len(set(tickers)) == 3
    bos = next(m for m in game if m["ticker"].endswith("BOSNYK-BOS"))
    assert bos["_source"] == "both" and bos["result"] == "yes" and bos["volume"] == 123 and bos["settlement_value"] == 100
    assert next(m for m in game if m["ticker"].endswith("NYKBOS-NYK"))["_source"] == "live"
    assert next(m for m in game if m["ticker"].endswith("BOSNYK-NYK"))["_source"] == "historical"
    wins = _read_gz(out / "markets_KXNBAWINS.jsonl.gz")
    assert len(wins) == 1 and wins[0]["series_ticker"] == "KXNBAWINS"

    # window passed through as unix ts
    hist_calls = [c for c in fc.calls if c[0] == "hist"]
    assert hist_calls[0][2] == 1759276800 and hist_calls[0][3] == 1782864000
    assert ("live", "KXNBAGAME", "settled") in fc.calls

    # candles: budget of 2, KXNBAGAME prioritised over KXNBAWINS
    hc = [c for c in fc.calls if c[0] == "hcandle"]
    assert len(hc) == 2 and all(c[1].startswith("KXNBAGAME") for c in hc)
    candles = _read_gz(out / "candles_KXNBAGAME.jsonl.gz")
    assert len(candles) == 4 and {c["ticker"] for c in candles} <= set(tickers)
    assert all(c["series_ticker"] == "KXNBAGAME" and c["period_interval"] == 60 for c in candles)
    assert not (out / "candles_KXNBAWINS.jsonl.gz").exists()

    man = json.loads((out / "MANIFEST.json").read_text())
    assert man["series"]["KXNBAGAME"] == {
        "historical": 2, "live": 2, "merged": 3, "errors": [], "markets_file": "markets_KXNBAGAME.jsonl.gz",
        "candles_markets": 2, "candles_errors": 0, "candles_rows": 4, "candles_file": "candles_KXNBAGAME.jsonl.gz",
    }
    assert man["total_markets"] == 4 and man["pulled_at"].endswith("Z") and man["request_count"] == fc.request_count

    uu = json.loads((out / "kalshi_team_uuids.json").read_text())
    assert set(uu) == {BOS, NYK}
    assert uu[BOS]["name"] == "Boston" and uu[BOS]["n_markets"] == 2 and uu[BOS]["tricode"] == "BOS"
    assert uu[NYK]["name"] == "New York" and uu[NYK]["tricode"] == "NYK"


def test_run_kalshi_history_falls_back_to_live_and_records_errors(tmp_path):
    live = {"KXNBASPREAD": [_mkt("KXNBASPREAD-25NOV01BOSNYK-BOS", "KXNBASPREAD", BOS, "Boston", "Boston wins by over 3.5 points?")]}
    fc = FakeClient({}, live, hist_fail={"KXNBASPREAD"}, candle_fail={"KXNBASPREAD-25NOV01BOSNYK-BOS"})
    rc = run_kalshi_history(tmp_path, ["KXNBASPREAD"], "2025-10-01", "2026-07-01", True, client=fc)
    assert rc == 0
    man = json.loads((tmp_path / "kalshi" / "MANIFEST.json").read_text())
    rep = man["series"]["KXNBASPREAD"]
    assert rep["historical"] == 0 and rep["live"] == 1 and rep["merged"] == 1
    assert rep["errors"] and rep["errors"][0].startswith("historical:")
    # historical candles failed -> live candlestick fallback used
    assert ("lcandle", "KXNBASPREAD-25NOV01BOSNYK-BOS") in fc.calls
    assert rep["candles_markets"] == 1 and rep["candles_rows"] == 1


def test_run_returns_1_when_nothing_pulled_and_errors(tmp_path):
    fc = FakeClient({}, {}, hist_fail={"KXNBAGAME"})
    assert run_kalshi_history(tmp_path, ["KXNBAGAME"], "2025-10-01", "2026-07-01", False, client=fc) == 1
    assert (tmp_path / "kalshi" / "MANIFEST.json").exists()


def test_merge_markets_prefers_historical_values_and_sorts():
    h = [{"ticker": "B", "result": "yes"}, {"ticker": "A", "result": "no", "volume": None}]
    live = [{"ticker": "A", "result": "", "volume": 7}, {"ticker": "C", "result": ""}]
    out = merge_markets(h, live, "KXNBAGAME")
    assert [m["ticker"] for m in out] == ["A", "B", "C"]
    a = out[0]
    assert a["result"] == "no" and a["volume"] == 7 and a["_source"] == "both" and a["series_ticker"] == "KXNBAGAME"


def test_build_team_uuid_map_marks_ambiguous_text():
    ms = [
        {"custom_strike": {"basketball_team": "u1"}, "yes_sub_title": "Los Angeles", "title": "Los Angeles wins"},
        {"custom_strike": {"basketball_team": "u2"}, "yes_sub_title": "Utah", "title": "Utah wins"},
        {"custom_strike": {"basketball_player": "p1"}, "yes_sub_title": "25+"},
        {"title": "no strike"},
    ]
    uu = build_team_uuid_map(ms)
    assert set(uu) == {"u1", "u2"}
    assert uu["u1"]["name"] == "Los Angeles" and "tricode" not in uu["u1"]
    assert uu["u2"]["tricode"] == "UTA"


# ---- client pagination against the historical host -------------------------------------------------


def _client(handler) -> KalshiClient:
    cfg = Settings(
        kalshi_base_url="https://live.test/trade-api/v2",
        kalshi_historical_base_url="https://hist.test/trade-api/v2/historical",
        http_max_retries=0,
    )
    return KalshiClient(cfg=cfg, rate=RateLimiter(rate_per_s=1e9), transport=httpx.MockTransport(handler))


def test_iter_historical_markets_paginates_until_cursor_empty():
    seen = []

    def handler(req: httpx.Request) -> httpx.Response:
        seen.append(req)
        cur = req.url.params.get("cursor")
        if cur is None:
            return httpx.Response(200, json={"markets": [{"ticker": "T1"}, {"ticker": "T2"}], "cursor": "c2"})
        if cur == "c2":
            return httpx.Response(200, json={"markets": [{"ticker": "T3"}], "cursor": ""})
        raise AssertionError(f"unexpected cursor {cur!r}")

    c = _client(handler)
    rows = list(c.iter_historical_markets(series_ticker="KXNBAGAME", min_close_ts=1, max_close_ts=2, status="settled"))
    assert [r["ticker"] for r in rows] == ["T1", "T2", "T3"]
    assert len(seen) == 2 and c.request_count == 2
    u = seen[0].url
    assert u.host == "hist.test" and u.path == "/trade-api/v2/historical/markets"
    assert u.params["series_ticker"] == "KXNBAGAME" and u.params["min_close_ts"] == "1" and u.params["status"] == "settled"
    assert "cursor" not in seen[0].url.params and seen[1].url.params["cursor"] == "c2"


def test_historical_candlesticks_and_trades_use_hist_host_and_tolerant_keys():
    def handler(req: httpx.Request) -> httpx.Response:
        assert req.url.host == "hist.test"
        if req.url.path.endswith("/candlesticks"):
            assert req.url.path == "/trade-api/v2/historical/markets/KXNBAGAME-X-BOS/candlesticks"
            assert req.url.params["period_interval"] == "60"
            return httpx.Response(200, json={"candles": [{"end_period_ts": 5}]})
        if req.url.path.endswith("/trades"):
            if req.url.params.get("cursor"):
                return httpx.Response(200, json={"trades": [{"trade_id": "b"}]})  # no cursor key -> stop
            return httpx.Response(200, json={"trades": [{"trade_id": "a"}], "cursor": "n"})
        return httpx.Response(200, json={"market": {"ticker": "KXNBAGAME-X-BOS"}})

    c = _client(handler)
    assert c.historical_candlesticks("KXNBAGAME-X-BOS", 1, 2, 60) == [{"end_period_ts": 5}]
    assert [t["trade_id"] for t in c.iter_historical_trades("KXNBAGAME-X-BOS", min_ts=1)] == ["a", "b"]
    assert c.get_historical_market("KXNBAGAME-X-BOS")["ticker"] == "KXNBAGAME-X-BOS"


def test_live_and_historical_hosts_are_independent():
    hosts = []

    def handler(req: httpx.Request) -> httpx.Response:
        hosts.append(req.url.host)
        return httpx.Response(200, json={"markets": [], "cursor": ""})

    c = _client(handler)
    list(c.iter_markets(series_ticker="KXNBAGAME"))
    list(c.iter_historical_markets(series_ticker="KXNBAGAME"))
    assert hosts == ["live.test", "hist.test"]
    c.close()
    assert c._client is None and c._hist_client is None
