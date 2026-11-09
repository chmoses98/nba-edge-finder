#!/usr/bin/env python3
"""Run the PR #87 pre-tip starter capture against LIVE ESPN for a bounded period and report measured coverage by lead time.

    python scripts/starters_live_check.py --archive out/archive --minutes 280 --interval-min 4

Real source, real clock: every row is stamped after its own fetch. Nothing is projected. The archive is a normal Ledger so the
shipped `nba starters-coverage` reads exactly what was captured."""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nba_edge.archive.ledger import Ledger  # noqa: E402
from nba_edge.data.schedule import fetch_espn_scoreboard  # noqa: E402
from nba_edge.data.starters import STARTERS_KIND, capture_starters, coverage_by_lead_time  # noqa: E402
from nba_edge.timeutil import iso, utcnow  # noqa: E402


def games_now(now):
    games, errs = [], []
    for d in range(-1, 2):          # ET-keyed scoreboard: yesterday's UTC date still holds the evening slate after 00:00 UTC
        try:
            gs, _ = fetch_espn_scoreboard(now + timedelta(days=d), ttl_s=0)
            games.extend(g.model_dump(mode="json") for g in gs)
        except Exception as e:  # noqa: BLE001
            errs.append(f"{type(e).__name__}: {str(e)[:100]}")
    return games, errs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    ap.add_argument("--minutes", type=float, default=280)
    ap.add_argument("--interval-min", type=float, default=4)
    a = ap.parse_args()
    ledger = Ledger(Path(a.archive))
    t_end = time.time() + a.minutes * 60
    loop = 0
    log = []
    while time.time() < t_end:
        loop += 1
        now = utcnow()
        games, errs = games_now(now)
        upcoming = sorted(g["start_time_utc"] for g in games if g.get("start_time_utc") and g["start_time_utc"] > iso(now))[:3]
        st = capture_starters(ledger, games, now=now)
        rec = {"loop": loop, "at": iso(now), "games_listed": len(games), "next_tips": upcoming, "scoreboard_errors": errs, **{k: st[k] for k in ("games_considered", "games_fetched", "rows", "confirmed_teams", "failures")}}
        log.append(rec)
        print(json.dumps(rec), flush=True)
        if loop % 8 == 0:
            rows = list(ledger.iter_rows(STARTERS_KIND))
            print("COVERAGE", json.dumps({"rows": len(rows), "coverage": coverage_by_lead_time(rows)}), flush=True)
        time.sleep(max(1.0, a.interval_min * 60 - (utcnow() - now).total_seconds()))
    rows = list(ledger.iter_rows(STARTERS_KIND))
    summary = {"loops": loop, "rows": len(rows), "coverage": coverage_by_lead_time(rows), "games": len({r["game_id"] for r in rows}),
               "states": {s: sum(r["state"] == s for r in rows) for s in ("CONFIRMED", "NONE_PUBLISHED", "FETCH_FAILED")},
               "confirmed_minutes_to_tip": sorted(round(r["minutes_to_tip"], 1) for r in rows if r["state"] == "CONFIRMED")}
    Path(a.archive, "STARTERS_LIVE_SUMMARY.json").write_text(json.dumps(summary, indent=1))
    print("FINAL", json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
