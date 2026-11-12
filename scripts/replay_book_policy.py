"""Replay the order-book selection policies on archived boards and report main-line coverage at T-60 for finished games.

Read-only over a data-archive checkout. Reproduces the table in docs/research/NBA_COLLECTION_RELIABILITY_AUDIT_2026-10-24.md:

    python scripts/replay_book_policy.py --archive /path/to/data-archive [--minutes 60] [--season-type regular]

For every final game with an actual tip it rebuilds the market board as of tip-minus-N (reconstruct_at, so nothing later can leak in), asks
both policies which 300 books they would have requested on that board, and reports, per family, how many games had a book on the family's
main line (the rung whose mid price is nearest 50 cents) and how many individual rungs were booked.
"""

from __future__ import annotations

import argparse
import collections
import gzip
import json
from datetime import datetime, timedelta
from pathlib import Path

from nba_edge.archive.book_policy import LIVE_STATUSES, legacy_priority_key, select_books
from nba_edge.archive.reconstruct import reconstruct_at
from nba_edge.timeutil import parse_iso

MAIN = ["game_winner", "game_spread", "game_total", "team_total", "player_points", "player_rebounds", "player_assists", "player_threes"]


def _mid(m):
    q = m.get("_quote_cents") or {}
    b, a = q.get("yes_bid"), q.get("yes_ask")
    return (b + a) / 2 if b is not None and a is not None else (q["last_price"] if q.get("last_price") is not None else 50)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--archive", required=True)
    ap.add_argument("--minutes", type=int, default=60)
    ap.add_argument("--season-type", default="regular")
    a = ap.parse_args(argv)
    root = Path(a.archive)
    rows = [json.loads(line) for line in (root / "manifest.jsonl").read_text().splitlines() if line.strip()]
    tips = {}
    for r in rows:
        if r["kind"] == "boxscores":
            for line in gzip.open(root / r["path"], "rt"):
                x = json.loads(line)
                if str(x.get("is_final")).lower() == "true" and x.get("actual_tip_utc"):
                    tips[x["game_id"]] = parse_iso(x["actual_tip_utc"])
    sched = {}
    for r in sorted((r for r in rows if r["kind"] == "context/schedule"), key=lambda r: r["observed_at_utc"]):
        for line in gzip.open(root / r["path"], "rt"):
            g = json.loads(line)
            sched[g["game_id"]] = g
    games = [(gid, t) for gid, t in tips.items() if gid in sched and sched[gid]["season_type"] == a.season_type]
    agg = {n: collections.defaultdict(lambda: [0, 0, 0, 0]) for n in ("legacy", "stratified")}
    cache = {}
    for gid, tip in games:
        g = sched[gid]
        key = f"{datetime.fromisoformat(g['game_date_et']).strftime('%y%b%d').upper()}{g['away_tricode']}{g['home_tricode']}"
        mk = reconstruct_at(root, tip - timedelta(minutes=a.minutes))
        if mk.observed_at_utc not in cache:
            board = [m for m in mk.rows if m.get("ticker")]
            legacy = sorted((m for m in board if m.get("status") in LIVE_STATUSES), key=legacy_priority_key)[:300]
            new = select_books(board, now=parse_iso(mk.observed_at_utc), max_books=300)
            cache[mk.observed_at_utc] = ({m["ticker"] for m in legacy}, {m["ticker"] for m in new.markets})
        sets = dict(zip(("legacy", "stratified"), cache[mk.observed_at_utc], strict=True))
        groups = collections.defaultdict(list)
        for m in mk.rows:
            if m.get("ticker") and key in m["ticker"] and m.get("status") == "active" and m.get("_family") in MAIN:
                parts = m["ticker"].split("-")
                sub = parts[2][:3] if m["_family"] == "team_total" else ""
                groups[(m["_family"], parts[0], sub)].append(m)
        for name, books in sets.items():
            for (fam, _, _), ms in groups.items():
                main_line = min(ms, key=lambda m: abs(_mid(m) - 50))
                v = agg[name][fam]
                v[0] += 1
                v[1] += main_line["ticker"] in books
                v[2] += len(ms)
                v[3] += sum(m["ticker"] in books for m in ms)
    print(f"{len(games)} finished {a.season_type} games, board as of T-{a.minutes}")
    for name in ("legacy", "stratified"):
        print(f"\n{name}")
        for fam in MAIN:
            v = agg[name].get(fam)
            if v and v[0]:
                print(f"  {fam:18} main line booked {v[1]:3}/{v[0]:3} = {v[1] / v[0]:4.0%}   all rungs {v[3]:4}/{v[2]:4} = {v[3] / v[2]:4.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
