"""Pull settled Kalshi NBA markets (and optionally their candlesticks) for research / backtesting.

Kalshi archives settled markets on a separate *historical* host. Its endpoint shapes are not verified, so
this job is deliberately belt-and-braces:

1. For each series, page the historical ``/markets`` endpoint for markets closing in ``[min_close, max_close]``.
2. Also page the LIVE ``/markets`` endpoint with ``status=settled`` over the same window and merge by ticker
   (historical record wins on conflicting keys; live fills the gaps). Nothing is dropped and nothing is
   duplicated.
3. Write one gzip JSONL per series: ``<out>/kalshi/markets_<series>.jsonl.gz``.
4. Optionally fetch candlesticks (default hourly) from ``open_time`` to ``close_time`` for up to
   ``max_markets_for_candles`` markets, prioritising the core game families, then player props. One row per
   candlestick, each tagged with ``ticker`` / ``series_ticker``: ``<out>/kalshi/candles_<series>.jsonl.gz``.
5. Write ``MANIFEST.json`` (counts, errors, pulled_at) and ``kalshi_team_uuids.json`` (Kalshi's
   ``custom_strike.basketball_team`` uuid -> team-name text seen on those markets, plus a tricode when the
   identity registry resolves it uniquely).

Any client object exposing ``iter_historical_markets``, ``iter_markets``, ``historical_candlesticks`` and
``candlesticks`` works (tests pass a stub); errors per series/market are recorded in the manifest, never fatal.
"""

from __future__ import annotations

import gzip
import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from nba_edge.kalshi.client import KalshiClient, KalshiError
from nba_edge.log import get_logger, kv
from nba_edge.timeutil import iso, parse_iso, utcnow

log = get_logger(__name__)

CANDLE_PRIORITY: dict[str, int] = {
    "KXNBAGAME": 0,
    "KXNBASPREAD": 1,
    "KXNBATOTAL": 2,
    "KXNBATEAMTOTAL": 3,
    "KXNBAPTS": 4,
    "KXNBAREB": 4,
    "KXNBAAST": 4,
    "KXNBA3PT": 4,
    "KXNBAPRA": 4,
}
_DEFAULT_PRIORITY = 9

_TITLE_TEAM_RES = [
    re.compile(r"^Will the (.+?) Pro Basketball team\b", re.I),
    re.compile(r"^Will (.+?) win\b", re.I),
    re.compile(r"^(.+?) wins?\b", re.I),
]


def _ts(value: str) -> int:
    """'YYYY-MM-DD' (UTC midnight) or ISO-8601 with offset -> unix seconds."""
    v = value.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        return int(datetime.fromisoformat(v).replace(tzinfo=UTC).timestamp())
    return int(parse_iso(v).timestamp())


def _ts_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, int | float):
        return int(value)
    try:
        return int(parse_iso(str(value)).timestamp())
    except (ValueError, TypeError):
        return None


def _write_jsonl_gz(path: Path, rows: list[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt") as f:
        for r in rows:
            f.write(json.dumps(r, default=str, sort_keys=True) + "\n")
    return len(rows)


def merge_markets(historical: list[dict[str, Any]], live: list[dict[str, Any]], series: str) -> list[dict[str, Any]]:
    """Merge by ticker. Historical keys win; live fills missing keys. ``_source`` records provenance."""
    merged: dict[str, dict[str, Any]] = {}
    for m in live:
        tk = m.get("ticker")
        if not tk:
            continue
        row = dict(m)
        row["_source"] = "live"
        merged[tk] = row
    for m in historical:
        tk = m.get("ticker")
        if not tk:
            continue
        if tk in merged:
            row = merged[tk]
            row.update({k: v for k, v in m.items() if v not in (None, "")})
            row["_source"] = "both"
        else:
            row = dict(m)
            row["_source"] = "historical"
            merged[tk] = row
    for row in merged.values():
        row.setdefault("series_ticker", series)
    return [merged[k] for k in sorted(merged)]


def _team_text_candidates(m: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for k in ("yes_sub_title", "subtitle", "no_sub_title"):
        v = m.get(k)
        if v and isinstance(v, str):
            out.append(v.strip())
    title = m.get("title") or ""
    for rx in _TITLE_TEAM_RES:
        mm = rx.match(title)
        if mm:
            out.append(mm.group(1).strip())
    return out


def build_team_uuid_map(markets: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """custom_strike.basketball_team uuid -> {name, tricode?, n_markets, names}.

    Name text is what Kalshi printed in yes_sub_title/title; tricode is added only when the identity registry
    resolves a candidate text to exactly one team. Tricode resolution proper is left to identity code.
    """
    names: dict[str, Counter[str]] = defaultdict(Counter)
    tricodes: dict[str, Counter[str]] = defaultdict(Counter)
    n: Counter[str] = Counter()
    try:
        from nba_edge.identity.teams import registry

        reg = registry()
    except Exception:  # noqa: BLE001 - identity data optional here
        reg = None
    for m in markets:
        cs = m.get("custom_strike") or {}
        uuid = cs.get("basketball_team") if isinstance(cs, dict) else None
        if not uuid:
            continue
        n[uuid] += 1
        cands = _team_text_candidates(m)
        if cands:
            names[uuid][cands[0]] += 1
        if reg is not None:
            for c in cands:
                try:
                    tricodes[uuid][reg.by_name(c).tricode] += 1
                    break
                except Exception:  # noqa: BLE001 - ambiguous/unknown text: leave to identity code
                    continue
    out: dict[str, dict[str, Any]] = {}
    for uuid in sorted(n):
        entry: dict[str, Any] = {
            "name": names[uuid].most_common(1)[0][0] if names[uuid] else None,
            "n_markets": n[uuid],
            "names": dict(names[uuid].most_common(5)),
        }
        if tricodes[uuid]:
            tc, _ = tricodes[uuid].most_common(1)[0]
            if len(tricodes[uuid]) == 1:
                entry["tricode"] = tc
            else:
                entry["tricode_candidates"] = dict(tricodes[uuid])
        out[uuid] = entry
    return out


def _candle_candidates(by_series: dict[str, list[dict[str, Any]]], budget: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for series, ms in by_series.items():
        pri = CANDLE_PRIORITY.get(series, _DEFAULT_PRIORITY)
        for m in ms:
            if m.get("ticker") and _ts_or_none(m.get("open_time")) and _ts_or_none(m.get("close_time")):
                rows.append({"_pri": pri, **m})
    rows.sort(key=lambda m: (m["_pri"], str(m.get("close_time") or ""), m["ticker"]))
    return rows[:budget]


def run_kalshi_history(
    out_root: Path,
    series: list[str],
    min_close: str,
    max_close: str,
    with_candles: bool,
    candle_interval: int = 60,
    max_markets_for_candles: int = 3000,
    client: Any | None = None,
) -> int:
    client = client or KalshiClient()
    out = Path(out_root) / "kalshi"
    out.mkdir(parents=True, exist_ok=True)
    min_ts, max_ts = _ts(min_close), _ts(max_close)
    pulled_at = iso(utcnow())
    manifest: dict[str, Any] = {
        "pulled_at": pulled_at,
        "min_close": min_close,
        "max_close": max_close,
        "min_close_ts": min_ts,
        "max_close_ts": max_ts,
        "candle_interval": candle_interval if with_candles else None,
        "series": {},
        "errors": [],
    }
    by_series: dict[str, list[dict[str, Any]]] = {}
    all_markets: list[dict[str, Any]] = []

    for st in series:
        st = st.strip().upper()
        if not st:
            continue
        rep: dict[str, Any] = {"historical": 0, "live": 0, "merged": 0, "errors": []}
        hist: list[dict[str, Any]] = []
        live: list[dict[str, Any]] = []
        try:
            hist = list(client.iter_historical_markets(series_ticker=st, min_close_ts=min_ts, max_close_ts=max_ts))
        except KalshiError as e:
            rep["errors"].append(f"historical: {str(e)[:300]}")
            log.warning(kv(event="kalshi_history_error", series=st, source="historical", err=str(e)[:160]))
        try:
            live = list(
                client.iter_markets(series_ticker=st, status="settled", min_close_ts=min_ts, max_close_ts=max_ts)
            )
        except KalshiError as e:
            rep["errors"].append(f"live: {str(e)[:300]}")
            log.warning(kv(event="kalshi_history_error", series=st, source="live", err=str(e)[:160]))
        merged = merge_markets(hist, live, st)
        rep["historical"], rep["live"], rep["merged"] = len(hist), len(live), len(merged)
        rep["markets_file"] = f"markets_{st}.jsonl.gz"
        _write_jsonl_gz(out / rep["markets_file"], merged)
        by_series[st] = merged
        all_markets.extend(merged)
        manifest["series"][st] = rep
        log.info(kv(event="kalshi_history_series", series=st, **{k: rep[k] for k in ("historical", "live", "merged")}))

    if with_candles:
        cands = _candle_candidates(by_series, max_markets_for_candles)
        manifest["candle_markets_selected"] = len(cands)
        rows_by_series: dict[str, list[dict[str, Any]]] = defaultdict(list)
        n_ok: Counter[str] = Counter()
        n_err: Counter[str] = Counter()
        for m in cands:
            st, tk = m["series_ticker"], m["ticker"]
            start, end = _ts_or_none(m.get("open_time")), _ts_or_none(m.get("close_time"))
            rows: list[dict[str, Any]] = []
            try:
                rows = client.historical_candlesticks(tk, start, end, candle_interval)
            except KalshiError as e:
                try:
                    rows = client.candlesticks(st, tk, start, end, candle_interval)
                except KalshiError as e2:
                    n_err[st] += 1
                    if len(manifest["errors"]) < 200:
                        manifest["errors"].append({"ticker": tk, "historical": str(e)[:200], "live": str(e2)[:200]})
                    continue
            n_ok[st] += 1
            for c in rows:
                rows_by_series[st].append({"ticker": tk, "series_ticker": st, "period_interval": candle_interval, **c})
        for st in by_series:
            rep = manifest["series"][st]
            rep["candles_markets"] = n_ok[st]
            rep["candles_errors"] = n_err[st]
            rep["candles_rows"] = len(rows_by_series.get(st, []))
            if rows_by_series.get(st):
                rep["candles_file"] = f"candles_{st}.jsonl.gz"
                _write_jsonl_gz(out / rep["candles_file"], rows_by_series[st])

    uuid_map = build_team_uuid_map(all_markets)
    (out / "kalshi_team_uuids.json").write_text(json.dumps(uuid_map, indent=1, sort_keys=True))
    manifest["total_markets"] = len(all_markets)
    manifest["team_uuids"] = len(uuid_map)
    manifest["request_count"] = getattr(client, "request_count", None)
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=1, default=str))
    log.info(kv(event="kalshi_history_done", markets=len(all_markets), team_uuids=len(uuid_map)))
    if not all_markets and any(rep["errors"] for rep in manifest["series"].values()):
        return 1
    return 0
