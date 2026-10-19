"""Operational watchdog: detects missing / stale pregame work from the archives themselves (never from a workflow's green tick).

    python -m nba.live.watchdog --archive <projection-data> --context <data-archive with context/schedule + STATUS_capture.json>
                                [--now ISO] [--out health.json] [--md health.md]

Findings (severity CRITICAL fails the job; WARN is reported):
  MISSING_PROJECTION   a game starts within 3 h (WARN within 12 h) and no challenger forecast for it is archived
  STALE_PROJECTION     a game starts within 2 h and its newest archived forecast is older than 8 h
  MISSED_SLOT          a pregame slot was due > 150 min ago, games start within 30 h after it, and the run ledger has no pregame
                       record at or after it (CRITICAL when one of those games starts within 4 h)
  MISSING_OUTCOME      a game that started > 10 h ago (CRITICAL > 30 h) has forecasts but no archived outcome
  MISSING_PAPER        (when the paper engine is enabled) a game with forecasts and a captured market board has no paper decisions
  STALE_MARKET_CAPTURE the market capture worker's last capture is > 45 min old (CRITICAL > 120 min) while games start within 12 h
  NO_SCHEDULE          the context archive holds no schedule
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any


from pf_core import prospective as pr

from . import ledger as LED
from . import schedule_plan as SP
from .sources import iso, parse_ts

CRIT, WARN, OK = "CRITICAL", "WARN", "OK"


def load_schedule(ctx: str, season_types=("regular",)) -> list[dict]:
    """Latest schedule snapshot of the data-archive context (every game once, newest observation wins)."""
    files = sorted(glob.glob(os.path.join(ctx, "context", "schedule", "dt=*", "*.jsonl.gz")))
    rows: dict[str, dict] = {}
    for p in files[-6:]:
        with gzip.open(p, "rt") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    rows[r["game_id"]] = r
    return [r for r in rows.values() if r.get("season_type", "regular") in season_types and r.get("start_time_utc")]


def forecast_index(archive: str, now: datetime) -> dict[str, dict]:
    """game_id -> {n, first_generated, last_generated} over archived challenger forecasts (only the dates near `now`)."""
    out: dict[str, dict] = {}
    base = os.path.join(archive, "forecasts", "nba")
    if not os.path.isdir(base):
        return out
    lo = (now - timedelta(days=4)).strftime("%Y-%m-%d")
    days = [d for d in sorted(os.listdir(base)) if d >= lo]
    for r in pr._read(archive, "forecasts", "NBA", days):
        if r.get("model_role") != "challenger":
            continue
        e = out.setdefault(r["game_id"], {"n": 0, "first_generated": r["generated_utc"], "last_generated": r["generated_utc"]})
        e["n"] += 1
        e["first_generated"] = min(e["first_generated"], r["generated_utc"])
        e["last_generated"] = max(e["last_generated"], r["generated_utc"])
    return out


def outcome_games(archive: str, now: datetime) -> set[str]:
    base = os.path.join(archive, "outcomes", "nba")
    if not os.path.isdir(base):
        return set()
    lo = (now - timedelta(days=5)).strftime("%Y-%m-%d")
    return {r["game_id"] for r in pr._read(archive, "outcomes", "NBA", [d for d in sorted(os.listdir(base)) if d >= lo])}


def paper_games(archive: str, now: datetime) -> set[str] | None:
    base = os.path.join(archive, "paper", "nba")
    if not os.path.isdir(base):
        return None
    out: set[str] = set()
    lo = (now - timedelta(days=4)).strftime("%Y-%m-%d")
    for day in sorted(os.listdir(base)):
        if day < lo:
            continue
        for fn in glob.glob(os.path.join(base, day, "decisions_*.jsonl.gz")):
            with gzip.open(fn, "rt") as f:
                for line in f:
                    if line.strip():
                        out.add(json.loads(line)["game_id"])
    return out


def market_capture_age_min(ctx: str, now: datetime) -> float | None:
    p = os.path.join(ctx, "STATUS_capture.json")
    if not os.path.exists(p):
        return None
    try:
        t = parse_ts(json.load(open(p))["last_capture_utc"])
    except (KeyError, ValueError, json.JSONDecodeError):
        return None
    return (now - t).total_seconds() / 60.0


def check(archive: str, ctx: str, now: datetime, season_types=("regular",), expect_paper: bool = False) -> dict[str, Any]:
    f: list[dict[str, Any]] = []

    def add(sev, code, detail, **kw):
        f.append({"severity": sev, "code": code, "detail": detail, **kw})

    sched = load_schedule(ctx, season_types)
    if not sched:
        add(WARN, "NO_SCHEDULE", "no schedule snapshot in the context archive")
    fidx = forecast_index(archive, now)
    out_games = outcome_games(archive, now)
    pgames = paper_games(archive, now) if expect_paper else None
    ledger = LED.load_all(archive, (now - timedelta(days=4)).strftime("%Y-%m-%d"))
    pre = [r for r in ledger if r.get("kind") == "pregame"]

    games = []
    for g in sched:
        tip = parse_ts(g["start_time_utc"])
        games.append((tip, g))
    games.sort(key=lambda x: x[0])

    for tip, g in games:
        gid = g["game_id"]
        dt_h = (tip - now).total_seconds() / 3600
        if 0 < dt_h <= 12:
            fi = fidx.get(gid)
            if fi is None:
                add(CRIT if dt_h <= 3 else WARN, "MISSING_PROJECTION",
                    f"{g.get('away_tricode')}@{g.get('home_tricode')} {g['start_time_utc']}: no challenger forecast archived, tip in {dt_h:.1f} h",
                    game_id=gid)
            elif dt_h <= 2 and (now - parse_ts(fi["last_generated"])).total_seconds() / 3600 > 8:
                add(WARN, "STALE_PROJECTION", f"{gid}: newest forecast {fi['last_generated']} is older than 8 h, tip in {dt_h:.1f} h", game_id=gid)
        if dt_h < -10 and gid in fidx and gid not in out_games:
            add(CRIT if dt_h < -30 else WARN, "MISSING_OUTCOME",
                f"{gid} started {-dt_h:.1f} h ago and has forecasts but no archived outcome (settle slot not run, or the game is not final)",
                game_id=gid)
        if pgames is not None and dt_h < -1 and gid in fidx and gid not in pgames:
            add(WARN, "MISSING_PAPER", f"{gid}: forecasts archived but no paper decisions", game_id=gid)

    # slots that should have run
    for inst, sid in SP.slot_instants("pregame", now, days_back=2):
        if not (now - timedelta(minutes=150) > inst > now - timedelta(hours=30)):
            continue
        soon = [(t, g) for t, g in games if inst < t <= inst + timedelta(hours=30)]
        if not soon:
            continue
        covered = any(r.get("slot_id") == sid or (r.get("finished_utc") and parse_ts(r["finished_utc"]) >= inst) for r in pre)
        if not covered:
            nearest = min((t for t, _ in soon if t > now), default=None)
            crit = nearest is not None and (nearest - now) <= timedelta(hours=4)
            add(CRIT if crit else WARN, "MISSED_SLOT",
                f"pregame slot {sid} ({iso(inst)}) has no ledger record and no later pregame run; {len(soon)} games start within 30 h",
                slot_id=sid)

    age = market_capture_age_min(ctx, now)
    upcoming = [t for t, _ in games if 0 < (t - now).total_seconds() / 3600 <= 12]
    if upcoming and age is not None:
        if age > 120:
            add(CRIT, "STALE_MARKET_CAPTURE", f"market capture is {age:.0f} min old; games start within 12 h")
        elif age > 45:
            add(WARN, "STALE_MARKET_CAPTURE", f"market capture is {age:.0f} min old; games start within 12 h")
    elif upcoming and age is None:
        add(WARN, "STALE_MARKET_CAPTURE", "no STATUS_capture.json in the context archive")

    status = CRIT if any(x["severity"] == CRIT for x in f) else WARN if f else OK
    return {"schema": "sift.nba_watchdog.v1", "generated_utc": iso(now), "status": status, "findings": f,
            "counts": {"games_in_schedule": len(games), "games_with_forecasts": len(fidx), "ledger_pregame_runs_4d": len(pre),
                       "market_capture_age_min": None if age is None else round(age, 1)}}


def markdown(rep: dict) -> str:
    lines = [f"## NBA ops watchdog: {rep['status']}", "", f"_{rep['generated_utc']}_ · {rep['counts']}", ""]
    if not rep["findings"]:
        lines.append("No findings.")
    for x in rep["findings"]:
        lines.append(f"- **{x['severity']} {x['code']}**: {x['detail']}")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    ap.add_argument("--context", required=True)
    ap.add_argument("--now", default=None)
    ap.add_argument("--season-types", default="regular")
    ap.add_argument("--expect-paper", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--md", default=None)
    a = ap.parse_args(argv)
    now = parse_ts(a.now) if a.now else datetime.now(timezone.utc).replace(microsecond=0)
    rep = check(a.archive, a.context, now, tuple(a.season_types.split(",")), a.expect_paper)
    txt = markdown(rep)
    print(txt)
    if a.out:
        with open(a.out, "w") as f:
            json.dump(rep, f, indent=1, sort_keys=True)
    if a.md:
        with open(a.md, "w") as f:
            f.write(txt)
    return 1 if rep["status"] == CRIT else 0


if __name__ == "__main__":
    raise SystemExit(main())
