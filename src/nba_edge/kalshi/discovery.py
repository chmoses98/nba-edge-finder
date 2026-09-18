"""Discover the Kalshi NBA universe programmatically.

Algorithm
1. Enumerate *all* series (no category filter; Kalshi categories drift). Decide NBA-ness per series with an
   auditable rule and keep the decision for every series so exclusions are visible (e.g. WNBA, NCAA).
2. For each NBA series, enumerate markets in every lifecycle status. Keep raw payloads.
3. Classify every market through the ontology; count support states; collect field-shape fingerprints
   (strike_type, market_type, title template) so new families are obvious.
4. Emit a machine-readable ``DiscoverySummary`` + per-series raw dumps for the archive.

Nothing is dropped: markets whose series/family is unknown are reported under UNRESOLVED with sample tickers.
"""

from __future__ import annotations

import gzip
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from nba_edge.kalshi.client import KalshiClient, KalshiError
from nba_edge.kalshi.ontology import Ontology, Support, classify_market
from nba_edge.kalshi.ticker import parse_ticker
from nba_edge.log import get_logger, kv
from nba_edge.timeutil import iso, utcnow

log = get_logger(__name__)

MARKET_STATUSES = ("unopened", "open", "closed", "settled")
NON_NBA_MARKERS = ("WNBA", "NCAA", "COLLEGE", "EUROLEAGUE", "FIBA", "OLYMPIC", "NBL", "G LEAGUE", "GLEAGUE", "BIG3", "SUMMER LEAGUE")


def is_nba_series(s: dict[str, Any]) -> tuple[bool, str]:
    """Return (is_nba, reason). Conservative on inclusion; explicit on exclusion."""
    ticker = (s.get("ticker") or "").upper()
    title = (s.get("title") or "").upper()
    tags = [str(t).upper() for t in (s.get("tags") or [])]
    blob = " ".join([ticker, title, *tags])
    for m in NON_NBA_MARKERS:
        if m in blob and "NBA" in blob and not ticker.startswith("KXNBA"):
            return False, f"non-NBA basketball marker '{m}'"
        if ticker.startswith("KXWNBA") or "WNBA" in title.split():
            return False, "WNBA"
    if ticker.startswith("KXNBA"):
        return True, "ticker prefix KXNBA"
    if "NBA" in tags:
        return True, "tag NBA"
    if re.search(r"\bNBA\b", title):
        return True, "title mentions NBA"
    return False, "no NBA marker"


def title_template(title: str) -> str:
    """Collapse names/numbers so families with many instances collapse to one template."""
    t = re.sub(r"\d+(\.\d+)?", "#", title or "")
    t = re.sub(r"\b[A-Z][a-z]+(?:[\s'\-][A-Z][a-z]+)+\b", "NAME", t)
    return t.strip()


@dataclass
class SeriesReport:
    ticker: str
    title: str
    category: str | None
    tags: list[str]
    frequency: str | None
    fee_type: str | None
    fee_multiplier: float | None
    family: str
    support: str
    counts_by_status: dict[str, int] = field(default_factory=dict)
    strike_types: dict[str, int] = field(default_factory=dict)
    market_types: dict[str, int] = field(default_factory=dict)
    title_templates: dict[str, int] = field(default_factory=dict)
    sample_tickers: list[str] = field(default_factory=list)
    sample_market: dict[str, Any] | None = None
    ticker_parse_confidence: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


@dataclass
class DiscoverySummary:
    discovered_at: str
    ontology_version: str
    exchange_status: dict[str, Any]
    n_series_total: int
    series_decisions: list[dict[str, Any]]
    nba_series: list[SeriesReport]
    support_counts: dict[str, int]
    family_counts: dict[str, int]
    unresolved_samples: list[dict[str, Any]]
    total_markets: int
    request_count: int

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=1, sort_keys=False, default=str)


def _market_fingerprint(m: dict[str, Any]) -> dict[str, Any]:
    keep = (
        "ticker", "event_ticker", "market_type", "title", "subtitle", "yes_sub_title", "no_sub_title",
        "strike_type", "floor_strike", "cap_strike", "custom_strike", "status", "open_time", "close_time",
        "expected_expiration_time", "result", "rules_primary", "yes_bid", "yes_ask", "no_bid", "no_ask",
        "last_price", "volume", "open_interest", "liquidity", "settlement_value", "response_price_units",
    )
    return {k: m.get(k) for k in keep if k in m}


def discover(
    client: KalshiClient,
    ontology: Ontology,
    raw_dir: Path | None = None,
    statuses: tuple[str, ...] = MARKET_STATUSES,
    max_pages_per_status: int | None = 60,
    include_series: list[str] | None = None,
) -> DiscoverySummary:
    now = utcnow()
    try:
        ex = client.exchange_status()
    except KalshiError as e:
        ex = {"error": str(e)}

    decisions: list[dict[str, Any]] = []
    nba_series_raw: list[dict[str, Any]] = []
    n_total = 0
    for s in client.iter_series():
        n_total += 1
        ok, reason = is_nba_series(s)
        blob = f"{s.get('ticker','')} {s.get('title','')} {' '.join(map(str, s.get('tags') or []))}".upper()
        if ok or "BASKETBALL" in blob or "NBA" in blob:
            decisions.append({"ticker": s.get("ticker"), "title": s.get("title"), "category": s.get("category"), "tags": s.get("tags"), "is_nba": ok, "reason": reason})
        if ok:
            nba_series_raw.append(s)
    if include_series:
        known = {s["ticker"] for s in nba_series_raw}
        for t in include_series:
            if t not in known:
                try:
                    nba_series_raw.append(client.get_series(t) | {"ticker": t})
                    decisions.append({"ticker": t, "is_nba": True, "reason": "explicitly included"})
                except KalshiError as e:
                    decisions.append({"ticker": t, "is_nba": False, "reason": f"explicit include failed: {e}"})
    log.info(kv(event="series_enumerated", total=n_total, nba=len(nba_series_raw)))

    reports: list[SeriesReport] = []
    support_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    unresolved_samples: list[dict[str, Any]] = []
    total_markets = 0
    if raw_dir:
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / "series.json").write_text(json.dumps(nba_series_raw, indent=1, default=str))
        (raw_dir / "series_decisions.json").write_text(json.dumps(decisions, indent=1, default=str))

    for s in sorted(nba_series_raw, key=lambda x: x.get("ticker", "")):
        st = s.get("ticker", "")
        fam_name = ontology.family_for_series(st) or "UNRESOLVED"
        fam = ontology.families.get(fam_name)
        rep = SeriesReport(
            ticker=st, title=s.get("title", ""), category=s.get("category"), tags=list(s.get("tags") or []),
            frequency=s.get("frequency"), fee_type=s.get("fee_type"), fee_multiplier=s.get("fee_multiplier"),
            family=fam_name, support=str(fam.support) if fam else str(Support.UNRESOLVED),
        )
        parse_conf: Counter[str] = Counter()
        seen: set[str] = set()
        for status in statuses:
            n = 0
            out = None
            if raw_dir:
                out = gzip.open(raw_dir / f"markets_{st}_{status}.jsonl.gz", "wt")
            try:
                for m in client.iter_markets(series_ticker=st, status=status, max_pages=max_pages_per_status):
                    tk = m.get("ticker", "")
                    if tk in seen:
                        continue  # duplicate across pages/status; counted once
                    seen.add(tk)
                    n += 1
                    total_markets += 1
                    m.setdefault("series_ticker", st)
                    if out:
                        out.write(json.dumps(m, default=str) + "\n")
                    cls = classify_market(m, ontology)
                    support_counts[str(cls.support)] += 1
                    family_counts[cls.family] += 1
                    rep.strike_types[str(m.get("strike_type"))] = rep.strike_types.get(str(m.get("strike_type")), 0) + 1
                    rep.market_types[str(m.get("market_type"))] = rep.market_types.get(str(m.get("market_type")), 0) + 1
                    tt = title_template(m.get("title", ""))
                    rep.title_templates[tt] = rep.title_templates.get(tt, 0) + 1
                    parse_conf[parse_ticker(tk).confidence] += 1
                    if len(rep.sample_tickers) < 12:
                        rep.sample_tickers.append(tk)
                    if rep.sample_market is None:
                        rep.sample_market = _market_fingerprint(m)
                    if cls.support == Support.UNRESOLVED and len(unresolved_samples) < 200:
                        unresolved_samples.append({"ticker": tk, "series": st, "title": m.get("title"), "reason": cls.reason, "guess": cls.family})
            except KalshiError as e:
                rep.errors.append(f"{status}: {e}")
                log.warning(kv(event="series_status_error", series=st, status=status, err=str(e)[:120]))
            finally:
                if out:
                    out.close()
            rep.counts_by_status[status] = n
        rep.ticker_parse_confidence = dict(parse_conf)
        reports.append(rep)
        log.info(kv(event="series_scanned", series=st, family=fam_name, **rep.counts_by_status))

    # Families present in the ontology but never observed are informative too (drift detection).
    for fam_name in ontology.families:
        family_counts.setdefault(fam_name, 0)

    return DiscoverySummary(
        discovered_at=iso(now),
        ontology_version=ontology.version,
        exchange_status=ex,
        n_series_total=n_total,
        series_decisions=decisions,
        nba_series=reports,
        support_counts=dict(support_counts),
        family_counts=dict(family_counts),
        unresolved_samples=unresolved_samples,
        total_markets=total_markets,
        request_count=client.request_count,
    )


def summary_markdown(s: DiscoverySummary) -> str:
    lines = [
        "# Kalshi NBA discovery summary",
        "",
        f"- discovered_at: `{s.discovered_at}`  ontology: `{s.ontology_version}`  requests: {s.request_count}",
        f"- series enumerated: {s.n_series_total}; NBA series: {len(s.nba_series)}; markets scanned: {s.total_markets}",
        "",
        "## Support states (coverage invariant)",
        "",
        "| support | markets |",
        "|---|---:|",
    ]
    for k in ("MODELABLE", "BUILDABLE", "RESEARCH", "UNMODELABLE", "UNRESOLVED"):
        lines.append(f"| {k} | {s.support_counts.get(k, 0)} |")
    lines += ["", "## NBA series", "", "| series | family | support | fee | unopened | open | closed | settled | strike_types | parse |", "|---|---|---|---|---:|---:|---:|---:|---|---|"]
    for r in s.nba_series:
        c = r.counts_by_status
        fee = f"{r.fee_type}/{r.fee_multiplier}" if r.fee_type or r.fee_multiplier else ""
        lines.append(
            f"| {r.ticker} | {r.family} | {r.support} | {fee} | {c.get('unopened',0)} | {c.get('open',0)} | {c.get('closed',0)} | {c.get('settled',0)} | {','.join(r.strike_types)} | {r.ticker_parse_confidence} |"
        )
    lines += ["", "## Title templates per series", ""]
    for r in s.nba_series:
        lines.append(f"### {r.ticker} — {r.title}")
        for tt, n in sorted(r.title_templates.items(), key=lambda kv: -kv[1])[:8]:
            lines.append(f"- ({n}) {tt}")
        if r.sample_tickers:
            lines.append(f"- samples: {', '.join(r.sample_tickers[:6])}")
        if r.sample_market:
            lines.append("- sample fields: `" + json.dumps(r.sample_market, default=str)[:600] + "`")
        if r.errors:
            lines.append(f"- errors: {r.errors}")
        lines.append("")
    if s.unresolved_samples:
        lines += ["## UNRESOLVED samples", ""]
        for u in s.unresolved_samples[:60]:
            lines.append(f"- `{u['ticker']}` — {u['title']} — {u['reason']}")
    lines += ["", "## Series decisions (basketball-related)", ""]
    for d in s.series_decisions:
        lines.append(f"- {'NBA ' if d.get('is_nba') else 'skip'} `{d.get('ticker')}` {d.get('title','')} — {d.get('reason')}")
    return "\n".join(lines) + "\n"
