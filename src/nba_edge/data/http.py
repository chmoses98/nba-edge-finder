"""Cached, retrying HTTP GET used by all data adapters.

- Disk cache keyed by sha256(url+headers subset) with TTL; cache hits record ``from_cache=True`` in provenance.
- Never caches non-200 responses.
- Retries on transport errors / 5xx / 429 with capped exponential backoff.
"""

from __future__ import annotations

import hashlib
import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from nba_edge.config import settings
from nba_edge.log import get_logger, kv
from nba_edge.timeutil import iso, utcnow

log = get_logger(__name__)

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}
PLAIN_HEADERS_OK = {"User-Agent": "nba-edge-finder/0.1 (+https://github.com/chmoses98/nba-edge-finder)", "Accept": "application/json, text/plain, */*"}
NBA_HEADERS = BROWSER_HEADERS | {"Referer": "https://www.nba.com/", "Origin": "https://www.nba.com", "x-nba-stats-origin": "stats", "x-nba-stats-token": "true"}


class FetchError(RuntimeError):
    pass


@dataclass
class Fetched:
    url: str
    status: int
    content: bytes
    fetched_at_utc: str
    from_cache: bool
    elapsed_ms: int

    def json(self) -> Any:
        return json.loads(self.content)

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")


def _cache_path(url: str, cache_root: Path) -> Path:
    h = hashlib.sha256(url.encode()).hexdigest()[:32]
    return cache_root / "http" / h[:2] / f"{h}.bin"


def fetch(url: str, headers: dict[str, str] | None = None, ttl_s: float | None = None, timeout_s: float = 30.0, max_retries: int = 3, cache_root: Path | None = None) -> Fetched:
    cfg = settings()
    cache_root = cache_root or cfg.cache_root
    cp = _cache_path(url, cache_root)
    meta = cp.with_suffix(".meta.json")
    if ttl_s is not None and cp.exists() and meta.exists():
        try:
            m = json.loads(meta.read_text())
            if time.time() - m["t"] <= ttl_s:
                return Fetched(url, 200, cp.read_bytes(), m["fetched_at_utc"], True, 0)
        except (json.JSONDecodeError, KeyError):
            pass
    last: Exception | None = None
    for attempt in range(max_retries + 1):
        t0 = time.time()
        try:
            with httpx.Client(timeout=timeout_s, follow_redirects=True, headers=headers or BROWSER_HEADERS) as c:
                r = c.get(url)
        except (httpx.TransportError, httpx.TimeoutException) as e:
            last = e
            log.warning(kv(event="fetch_retry", url=url[:120], attempt=attempt, err=type(e).__name__))
            time.sleep(min(2.0**attempt, 15.0) * (0.5 + random.random()))
            continue
        ms = int((time.time() - t0) * 1000)
        if r.status_code == 200:
            f = Fetched(url, 200, r.content, iso(utcnow()), False, ms)
            if ttl_s is not None:
                cp.parent.mkdir(parents=True, exist_ok=True)
                cp.write_bytes(r.content)
                meta.write_text(json.dumps({"t": time.time(), "fetched_at_utc": f.fetched_at_utc, "url": url}))
            return f
        if r.status_code in (429, 500, 502, 503, 504):
            last = FetchError(f"HTTP {r.status_code} {url}")
            time.sleep(min(2.0**attempt, 15.0) * (0.5 + random.random()))
            continue
        raise FetchError(f"HTTP {r.status_code} {url} {r.text[:200]}")
    raise FetchError(f"exhausted retries {url}: {last}")
