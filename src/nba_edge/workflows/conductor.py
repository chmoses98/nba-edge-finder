"""Cheap conductor: decide which expensive jobs are worth running right now.

Inputs: the season calendar (preseason from 2026-10-03, regular season from 2026-10-20 per NBA announcements),
the latest archived schedule snapshot (if any), and the age of the last capture. Output: key=value lines for
GitHub Actions ``$GITHUB_OUTPUT`` plus a JSON summary on stdout.

Rules (v0.1):
- capture:  every wake if a game tips within 36h; otherwise one daily futures snapshot (16:00 UTC)
- context:  every wake in the active window when a game is within 30h; otherwise every 6h
- simulate: if a not-started game tips within 26h and the last sim is older than 55 min
- settle:   if any game finished in the last 36h and settlement is older than 90 min
- evaluate: after settlement, or daily at 10:00 UTC in season
Outside NBA windows everything is 'false' and the workflow exits in seconds.
"""

from __future__ import annotations

import gzip
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from nba_edge.archive.capture import last_capture_age_minutes
from nba_edge.archive.ledger import Ledger
from nba_edge.timeutil import iso, parse_iso, utcnow

SEASON_2026_27 = {"preseason_start": "2026-10-03", "regular_start": "2026-10-20", "regular_end": "2027-04-11", "playoffs_end": "2027-06-30"}


def _latest_schedule(ledger: Ledger) -> list[dict[str, Any]]:
    entry = ledger.latest("context/schedule")
    if not entry:
        return []
    rows = []
    with gzip.open(ledger.root / entry.path, "rt") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def decide(now: datetime, schedule_rows: list[dict[str, Any]], capture_age_min: float | None, last_sim_age_min: float | None, last_settle_age_min: float | None, last_eval_age_min: float | None) -> dict[str, Any]:
    in_season = SEASON_2026_27["preseason_start"] <= now.date().isoformat() <= SEASON_2026_27["playoffs_end"]
    tips = []
    for g in schedule_rows:
        try:
            tips.append((parse_iso(g["start_time_utc"]), g.get("status"), g.get("game_id")))
        except (KeyError, ValueError):
            continue
    upcoming = [t for t, st, _ in tips if t > now and st in ("scheduled", None)]
    recent_final = [t for t, st, _ in tips if now - timedelta(hours=36) <= t <= now]
    next_tip_h = (min(upcoming) - now).total_seconds() / 3600 if upcoming else None
    hour = now.hour
    active_window = 13 <= hour or hour <= 4  # UTC: 9am ET .. midnight ET
    daily_slot = hour == 16 and (capture_age_min is None or capture_age_min > 20 * 60)

    capture = (in_season and next_tip_h is not None and next_tip_h <= 36) or daily_slot
    context = in_season and ((next_tip_h is not None and next_tip_h <= 30 and active_window) or capture_age_min is None or (hour % 6 == 0 and (capture_age_min or 0) > 55))
    if not schedule_rows:
        context = True  # bootstrap: we need a schedule snapshot before anything else can be decided
    simulate = in_season and next_tip_h is not None and next_tip_h <= 26 and (last_sim_age_min is None or last_sim_age_min > 55)
    settle = bool(recent_final) and (last_settle_age_min is None or last_settle_age_min > 90)
    evaluate = settle or (in_season and hour == 10 and (last_eval_age_min is None or last_eval_age_min > 23 * 60))
    discover = hour == 15 and now.minute < 10  # daily market-family discovery (new series never require code changes)
    return {
        "discover": bool(discover),
        "now_utc": iso(now), "in_season": in_season, "next_tip_hours": None if next_tip_h is None else round(next_tip_h, 2), "n_upcoming": len(upcoming),
        "n_recent_final": len(recent_final), "capture": bool(capture), "context": bool(context), "simulate": bool(simulate), "settle": bool(settle), "evaluate": bool(evaluate),
        "capture_age_min": capture_age_min,
    }


def _age(path: Path, key: str) -> float | None:
    if not path.exists():
        return None
    try:
        return (utcnow() - parse_iso(json.loads(path.read_text())[key])).total_seconds() / 60
    except (KeyError, ValueError, json.JSONDecodeError):
        return None


def run_conductor(data_root: Path, github_output: str | None = None) -> int:
    archive = data_root / "archive"
    ledger = Ledger(archive)
    rows = _latest_schedule(ledger) if archive.exists() else []
    d = decide(
        datetime.now(tz=UTC), rows, last_capture_age_minutes(archive), _age(archive / "STATUS_simulate.json", "simulated_at_utc"),
        _age(archive / "STATUS_settle.json", "settled_at_utc"), _age(archive / "STATUS_evaluate.json", "evaluated_at_utc"),
    )
    print(json.dumps(d, indent=1))
    if github_output:
        with open(github_output, "a") as f:
            for k in ("capture", "context", "simulate", "settle", "evaluate", "discover", "in_season"):
                f.write(f"{k}={'true' if d[k] else 'false'}\n")
    return 0
