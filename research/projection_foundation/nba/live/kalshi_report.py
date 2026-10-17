"""Reporting-only audit of Kalshi NBA player-prop listings (KXNBAPTS, KXNBAREB, KXNBAAST, KXNBA3PT, KXNBAPRA).

No market strategy and no price enters any projection. The one rule this module enforces for the rest of the code base:
a PLACEHOLDER quote (the 0.00 / 0.98-0.99 boundary quote a freshly listed market carries before anyone quotes it) is
never an executable price. `executable_quote` returns None for everything except a genuine two-sided quote with
displayed size on both sides; `classify_quote` says why a quote is not usable.

    python -m nba.live.kalshi_report --archive <data-archive checkout> [--regular-from 2026-10-20] [--out report.json]
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

SERIES = ("KXNBAPTS", "KXNBAREB", "KXNBAAST", "KXNBA3PT", "KXNBAPRA")
NO_QUOTE, PLACEHOLDER, ONE_SIDED, TWO_SIDED, INVALID = "NO_QUOTE", "PLACEHOLDER", "ONE_SIDED", "TWO_SIDED", "INVALID"
_EV = re.compile(r"-(\d{2})([A-Z]{3})(\d{2})")
_MON = {m: i + 1 for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"])}


def _f(x) -> float | None:
    try:
        return None if x in (None, "") else float(x)
    except (TypeError, ValueError):
        return None


def event_date(event_ticker: str) -> str | None:
    m = _EV.search(event_ticker or "")
    return f"20{m.group(1)}-{_MON[m.group(2)]:02d}-{m.group(3)}" if m and m.group(2) in _MON else None


def classify_quote(m: dict) -> str:
    """Quality of the displayed YES quote of one market (prices in dollars, 0..1)."""
    bid, ask = _f(m.get("yes_bid_dollars")), _f(m.get("yes_ask_dollars"))
    if bid is None and ask is None:
        return NO_QUOTE
    bid, ask = bid or 0.0, ask if ask is not None else 1.0
    if ask < bid or ask > 1.0 or bid < 0.0:
        return INVALID
    if bid <= 0.0 and (ask <= 0.0 or ask >= 1.0):
        return NO_QUOTE
    if bid <= 0.02 and ask >= 0.98:
        return PLACEHOLDER                      # boundary quote: no information, never a price
    if bid <= 0.0 or ask >= 1.0:
        return ONE_SIDED
    return TWO_SIDED


def executable_quote(m: dict) -> dict | None:
    """The only way a Kalshi price may be used anywhere: a genuine two-sided quote with displayed size on both sides.
    Placeholders, one-sided books and size-less quotes return None."""
    if classify_quote(m) != TWO_SIDED:
        return None
    bs, as_ = _f(m.get("yes_bid_size_fp")), _f(m.get("yes_ask_size_fp"))
    if not bs or not as_ or bs <= 0 or as_ <= 0:
        return None
    return {"bid": _f(m["yes_bid_dollars"]), "ask": _f(m["yes_ask_dollars"]), "bid_size": bs, "ask_size": as_}


def load_checkpoints(archive: str) -> list[tuple[str, list[dict]]]:
    """Every full-board checkpoint, reduced to its player-prop markets (streamed: a board has ~8,000 markets)."""
    out = []
    for p in sorted(glob.glob(os.path.join(archive, "kalshi", "markets", "dt=*", "kalshi_markets_*.jsonl.gz"))):
        m = re.search(r"kalshi_markets_(\d{8}T\d{6}Z)", p)
        rows = []
        with gzip.open(p, "rt") as f:
            for line in f:
                if line.strip() and ('"KXNBAPTS-' in line or '"KXNBAREB-' in line or '"KXNBAAST-' in line or '"KXNBA3PT-' in line
                                     or '"KXNBAPRA-' in line):
                    r = json.loads(line)
                    if r.get("event_ticker", "").split("-")[0] in SERIES:
                        rows.append({k: v for k, v in r.items() if k not in ("rules_primary", "rules_secondary", "early_close_condition", "price_ranges")})
        out.append((m.group(1) if m else p, rows))
    return out


def latest_board(archive: str) -> tuple[str, list[dict], int]:
    """Newest full checkpoint plus every later delta of that chain (the repo's own delta format), i.e. the board as the capture
    worker last saw it. Returns (board stamp, rows, deltas applied)."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))
    from nba_edge.archive.delta import Delta, apply_delta, canonical_board
    cps = sorted(glob.glob(os.path.join(archive, "kalshi", "markets", "dt=*", "kalshi_markets_*.jsonl.gz")))
    if not cps:
        return "", [], 0
    base = cps[-1]
    with gzip.open(base, "rt") as f:
        board = canonical_board([json.loads(x) for x in f if x.strip()])
    rel = os.path.relpath(base, archive)
    deltas = []
    for p in sorted(glob.glob(os.path.join(archive, "kalshi", "markets_delta", "dt=*", "*.json.gz"))):
        with open(p, "rb") as f:
            d = Delta.from_bytes(f.read())
        if d.base_path == rel:
            deltas.append(d)
    stamp = re.search(r"(\d{8}T\d{6}Z)", base).group(1)
    for d in sorted(deltas, key=lambda d: d.seq):
        board = apply_delta(board, d)
        stamp = d.captured_at_utc
    return stamp, list(board.values()), len(deltas)


def summarize_board(rows: list[dict], regular_from: str = "2026-10-20") -> dict[str, Any]:
    props = [r for r in rows if r.get("event_ticker", "").split("-")[0] in SERIES]
    out: dict[str, Any] = {"n_markets_on_board": len(rows), "n_prop_markets": len(props), "series": {}, "events": {}}
    by_ev = defaultdict(list)
    for r in props:
        by_ev[r["event_ticker"]].append(r)
    for s in SERIES:
        ms = [r for r in props if r["event_ticker"].startswith(s + "-")]
        reg = [r for r in ms if (event_date(r["event_ticker"]) or "") >= regular_from]
        out["series"][s] = {"markets": len(ms), "events": len({r["event_ticker"] for r in ms}),
                            "regular_season_markets": len(reg),
                            "regular_season_quote_classes": dict(Counter(classify_quote(r) for r in reg)),
                            "regular_season_executable": sum(1 for r in reg if executable_quote(r)),
                            "regular_season_executable_spread_le_10c": sum(
                                1 for r in reg if (q := executable_quote(r)) and q["ask"] - q["bid"] <= 0.10 + 1e-9),
                            "regular_season_with_volume": sum(1 for r in reg if (_f(r.get("volume_fp")) or 0) > 0),
                            "regular_season_with_open_interest": sum(1 for r in reg if (_f(r.get("open_interest_fp")) or 0) > 0),
                            "statuses": dict(Counter(r.get("status") for r in ms)),
                            "settled_results": dict(Counter(r.get("result") for r in ms if r.get("result")))}
    for ev, ms in sorted(by_ev.items()):
        cls = Counter(classify_quote(r) for r in ms)
        out["events"][ev] = {"date": event_date(ev), "markets": len(ms), "classes": dict(cls),
                             "executable": sum(1 for r in ms if executable_quote(r)),
                             "open_time_min": min(r["open_time"] for r in ms if r.get("open_time")),
                             "expected_expiration": ms[0].get("expected_expiration_time")}
    tot = Counter()
    for s in out["series"].values():
        tot.update(s["regular_season_quote_classes"])
    out["regular_season_total"] = {"markets": sum(s["regular_season_markets"] for s in out["series"].values()), "classes": dict(tot),
                                   "executable": sum(s["regular_season_executable"] for s in out["series"].values()),
                                   "executable_spread_le_10c": sum(s["regular_season_executable_spread_le_10c"] for s in out["series"].values()),
                                   "with_volume": sum(s["regular_season_with_volume"] for s in out["series"].values())}
    return out


def report(archive: str, regular_from: str = "2026-10-20") -> dict[str, Any]:
    cps = load_checkpoints(archive)
    if not cps:
        return {"status": "no kalshi checkpoints in the archive"}
    stamp, rows, n_delta = latest_board(archive)
    latest = summarize_board(rows, regular_from)
    timeline = []
    for st, rr in cps:
        reg = [r for r in rr if r.get("event_ticker", "").split("-")[0] in SERIES and (event_date(r["event_ticker"]) or "") >= regular_from]
        if reg:
            c = Counter(classify_quote(r) for r in reg)
            timeline.append({"board": st, "regular_season_prop_markets": len(reg), "classes": dict(c),
                             "executable": sum(1 for r in reg if executable_quote(r))})
    sample = next((r for r in rows if r.get("event_ticker", "").startswith("KXNBAPTS-") and r.get("rules_secondary")), {})
    return {"status": "ok", "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "latest_board": stamp, "deltas_applied": n_delta,
            "boards_scanned": len(cps), "regular_from": regular_from, "latest": latest,
            "first_board_with_regular_season_props": timeline[0]["board"] if timeline else None, "timeline": timeline,
            "settlement_rule": (sample.get("rules_secondary") or "").split("\n")[0], "settlement_timer_seconds": sample.get("settlement_timer_seconds"),
            "note": "reporting only: no price is used by the projections, and a PLACEHOLDER quote is never an executable price"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    ap.add_argument("--regular-from", default="2026-10-20")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    r = report(a.archive, a.regular_from)
    txt = json.dumps(r, indent=1, sort_keys=True)
    if a.out:
        with open(a.out, "w") as f:
            f.write(txt)
    print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
