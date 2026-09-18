"""Minimal, robust Kalshi Trade API v2 read client.

Only public (unauthenticated) endpoints are used: series, events, markets, orderbook, trades,
candlesticks, exchange status. Authenticated endpoints are deliberately not implemented yet;
see fills/ for the planned fill-ingestion boundary.

Design notes
- Every response is returned as parsed JSON *plus* we keep the raw payload available to callers,
  so the archive can store exactly what Kalshi said (no lossy re-modelling at capture time).
- Retries with exponential backoff on 429/5xx/network errors; never retries 4xx policy errors.
- A small token-bucket rate limiter keeps us well under Kalshi's basic-tier read limits.
"""

from __future__ import annotations

import random
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import httpx

from nba_edge.config import Settings, settings
from nba_edge.log import get_logger, kv

log = get_logger(__name__)

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class KalshiError(RuntimeError):
    pass


class KalshiPolicyError(KalshiError):
    """Non-retryable HTTP 4xx (other than 429)."""


@dataclass
class RateLimiter:
    rate_per_s: float = 5.0
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _next: float = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            if now < self._next:
                time.sleep(self._next - now)
                now = time.monotonic()
            self._next = now + 1.0 / self.rate_per_s


@dataclass
class KalshiClient:
    cfg: Settings = field(default_factory=settings)
    rate: RateLimiter = field(default_factory=RateLimiter)
    _client: httpx.Client | None = None
    request_count: int = 0

    def _http(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.cfg.kalshi_base_url,
                timeout=self.cfg.http_timeout_s,
                headers={"User-Agent": self.cfg.user_agent, "Accept": "application/json"},
            )
        return self._client

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        params = {k: v for k, v in (params or {}).items() if v is not None}
        last_exc: Exception | None = None
        for attempt in range(self.cfg.http_max_retries + 1):
            self.rate.wait()
            try:
                self.request_count += 1
                r = self._http().get(path, params=params)
            except (httpx.TransportError, httpx.TimeoutException) as e:
                last_exc = e
                self._sleep(attempt)
                continue
            if r.status_code == 200:
                return r.json()
            if r.status_code in RETRYABLE_STATUS:
                last_exc = KalshiError(f"HTTP {r.status_code} {path} {r.text[:200]}")
                log.warning(kv(event="kalshi_retry", status=r.status_code, path=path, attempt=attempt))
                self._sleep(attempt, retry_after=r.headers.get("Retry-After"))
                continue
            raise KalshiPolicyError(f"HTTP {r.status_code} {path} params={params} body={r.text[:300]}")
        raise KalshiError(f"exhausted retries for {path}: {last_exc}")

    @staticmethod
    def _sleep(attempt: int, retry_after: str | None = None) -> None:
        if retry_after:
            try:
                time.sleep(min(float(retry_after), 30.0))
                return
            except ValueError:
                pass
        time.sleep(min(2.0**attempt, 20.0) * (0.5 + random.random()))

    # ---- public endpoints -------------------------------------------------

    def exchange_status(self) -> dict[str, Any]:
        return self.get("/exchange/status")

    def iter_series(self, category: str | None = None, tags: str | None = None) -> Iterator[dict[str, Any]]:
        cursor = None
        while True:
            data = self.get(
                "/series",
                {"category": category, "tags": tags, "cursor": cursor, "limit": 200, "include_product_metadata": "true"},
            )
            yield from data.get("series", [])
            cursor = data.get("cursor")
            if not cursor:
                break

    def get_series(self, series_ticker: str) -> dict[str, Any]:
        return self.get(f"/series/{series_ticker}").get("series", {})

    def iter_events(
        self, series_ticker: str | None = None, status: str | None = None, with_nested_markets: bool = False
    ) -> Iterator[dict[str, Any]]:
        cursor = None
        while True:
            data = self.get(
                "/events",
                {
                    "series_ticker": series_ticker,
                    "status": status,
                    "with_nested_markets": "true" if with_nested_markets else None,
                    "limit": 200,
                    "cursor": cursor,
                },
            )
            yield from data.get("events", [])
            cursor = data.get("cursor")
            if not cursor:
                break

    def iter_markets(
        self,
        series_ticker: str | None = None,
        event_ticker: str | None = None,
        status: str | None = None,
        tickers: list[str] | None = None,
        min_close_ts: int | None = None,
        max_close_ts: int | None = None,
        max_pages: int | None = None,
    ) -> Iterator[dict[str, Any]]:
        cursor = None
        pages = 0
        while True:
            data = self.get(
                "/markets",
                {
                    "series_ticker": series_ticker,
                    "event_ticker": event_ticker,
                    "status": status,
                    "tickers": ",".join(tickers) if tickers else None,
                    "min_close_ts": min_close_ts,
                    "max_close_ts": max_close_ts,
                    "limit": 1000,
                    "cursor": cursor,
                },
            )
            yield from data.get("markets", [])
            pages += 1
            cursor = data.get("cursor")
            if not cursor or (max_pages is not None and pages >= max_pages):
                break

    def get_market(self, ticker: str) -> dict[str, Any]:
        return self.get(f"/markets/{ticker}").get("market", {})

    def get_orderbook(self, ticker: str, depth: int = 10) -> dict[str, Any]:
        return self.get(f"/markets/{ticker}/orderbook", {"depth": depth}).get("orderbook", {})

    def iter_trades(
        self, ticker: str, min_ts: int | None = None, max_ts: int | None = None, max_pages: int | None = None
    ) -> Iterator[dict[str, Any]]:
        cursor = None
        pages = 0
        while True:
            data = self.get(
                "/markets/trades",
                {"ticker": ticker, "min_ts": min_ts, "max_ts": max_ts, "limit": 1000, "cursor": cursor},
            )
            yield from data.get("trades", [])
            pages += 1
            cursor = data.get("cursor")
            if not cursor or (max_pages is not None and pages >= max_pages):
                break

    def candlesticks(
        self, series_ticker: str, ticker: str, start_ts: int, end_ts: int, period_interval: int = 60
    ) -> list[dict[str, Any]]:
        data = self.get(
            f"/series/{series_ticker}/markets/{ticker}/candlesticks",
            {"start_ts": start_ts, "end_ts": end_ts, "period_interval": period_interval},
        )
        return data.get("candlesticks", [])
