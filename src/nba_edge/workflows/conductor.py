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

from nba_edge.archive.ledger import Ledger
from nba_edge.archive.status import status_age_minutes
from nba_edge.timeutil import iso, parse_iso

# Announced NBA calendars. Add each new season here as the league publishes it.
SEASON_CALENDAR = {
    "2026-27": {"preseason_start": "2026-10-03", "regular_start": "2026-10-20", "regular_end": "2027-04-11", "playoffs_end": "2027-06-30"},
}
SEASON_2026_27 = SEASON_CALENDAR["2026-27"]  # back-compat alias

# The NBA's season shape is stable: preseason opens in early October, the Finals end by late June.
# When the date falls past every calendar above we fall back to that shape rather than going
# dormant -- but we flag it (``calendar_known=False``) so the workflow can raise a visible alarm.
# A system that quietly decides the season is over, forever, is worse than one that is approximate.
FALLBACK_SEASON_START_MONTH = 10
FALLBACK_SEASON_END_MONTH = 6


def season_window(today: str) -> tuple[bool, str | None, bool]:
    """Return ``(in_season, season_label, calendar_known)`` for an ET date string.

    ``calendar_known`` is False once we are past the last announced calendar. The conductor keeps
    working on the fallback rule, but callers should surface it: somebody has to add real dates.
    """
    for label, cal in sorted(SEASON_CALENDAR.items()):
        if cal["preseason_start"] <= today <= cal["playoffs_end"]:
            return True, label, True
    last_known_end = max(cal["playoffs_end"] for cal in SEASON_CALENDAR.values())
    if today <= last_known_end:
        return False, None, True  # a real gap between announced seasons
    month = int(today[5:7])
    return (month >= FALLBACK_SEASON_START_MONTH or month <= FALLBACK_SEASON_END_MONTH), None, False


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


def decide(now: datetime, schedule_rows: list[dict[str, Any]], capture_age_min: float | None, last_sim_age_min: float | None, last_settle_age_min: float | None, last_eval_age_min: float | None, last_context_age_min: float | None = None, last_discover_age_min: float | None = None) -> dict[str, Any]:
    in_season, season_label, calendar_known = season_window(now.date().isoformat())
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

    # Context (schedule/roster refresh) is keyed to its OWN age, not to the capture age. Keying it
    # to capture_age_min was a latent bug: in season we capture every wake, so capture_age_min is
    # always < 55 and the "every 6h" branch could never fire; and off-season the whole clause was
    # gated on in_season, so a stale schedule was never refreshed at all. Both are fixed here --
    # context has a fast cadence near tip-off and a slow floor that always applies.
    context_stale_min = 6 * 60 if in_season else 24 * 60
    context = (
        (in_season and next_tip_h is not None and next_tip_h <= 30 and active_window and (last_context_age_min is None or last_context_age_min > 55))
        or last_context_age_min is None
        or last_context_age_min > context_stale_min
    )
    if not schedule_rows:
        context = True  # bootstrap: we need a schedule snapshot before anything else can be decided

    simulate = in_season and next_tip_h is not None and next_tip_h <= 26 and (last_sim_age_min is None or last_sim_age_min > 55)
    settle = bool(recent_final) and (last_settle_age_min is None or last_settle_age_min > 90)
    evaluate = settle or (in_season and hour == 10 and (last_eval_age_min is None or last_eval_age_min > 23 * 60))

    # Discovery is age-based, not "hour==15 and minute<10". GitHub routinely delays scheduled runs
    # past a ten-minute window, and every such delay silently skipped a day of discovery -- which is
    # exactly how a new Kalshi series would go unnoticed. An age check cannot be skipped, only late.
    discover = last_discover_age_min is None or last_discover_age_min > 23 * 60
    return {
        "discover": bool(discover),
        "now_utc": iso(now), "in_season": in_season, "season": season_label, "calendar_known": calendar_known,
        "next_tip_hours": None if next_tip_h is None else round(next_tip_h, 2), "n_upcoming": len(upcoming),
        "n_recent_final": len(recent_final), "capture": bool(capture), "context": bool(context), "simulate": bool(simulate), "settle": bool(settle), "evaluate": bool(evaluate),
        "capture_age_min": capture_age_min, "context_age_min": last_context_age_min, "discover_age_min": last_discover_age_min,
    }


_age = status_age_minutes  # back-compat alias for the pre-extraction name


def _discover_age(data_root: Path) -> float | None:
    """Age of the freshest discovery catalog, looking in both places one can live.

    Scheduled discovery writes into the archive worktree (unattended, immutable, append-only).
    ``data/catalog`` is the reviewed copy committed to the code branch by the manual probe
    workflow. Either counts as evidence that the market universe was recently enumerated, so we
    take whichever is fresher; None (neither exists) means discovery has never run and must.
    """
    ages = [
        status_age_minutes(root / "discovery_summary.json", "discovered_at")
        for root in (data_root / "archive" / "catalog", data_root / "catalog")
    ]
    known = [a for a in ages if a is not None]
    return min(known) if known else None


def decide_now(data_root: Path) -> dict[str, Any]:
    """The full decision, assembled from the STATUS breadcrumbs on the archive.

    Extracted from ``run_conductor`` so the long-lived capture worker can reuse exactly this logic
    instead of reimplementing it. That matters more than it looks: the worker holds the archive's
    concurrency group for hours, so every scheduled conductor run queues behind it and is
    cancelled. If the worker did not decide and run simulate/settle/evaluate/discover itself, those
    jobs would simply stop happening for as long as a worker was alive.
    """
    archive = data_root / "archive"
    ledger = Ledger(archive)
    rows = _latest_schedule(ledger) if archive.exists() else []
    return decide(
        datetime.now(tz=UTC), rows,
        status_age_minutes(archive / "STATUS_capture.json", "last_capture_utc"),
        status_age_minutes(archive / "STATUS_simulate.json", "simulated_at_utc"),
        status_age_minutes(archive / "STATUS_settle.json", "settled_at_utc"),
        status_age_minutes(archive / "STATUS_evaluate.json", "evaluated_at_utc"),
        status_age_minutes(archive / "STATUS_context.json", "refreshed_at_utc"),
        _discover_age(data_root),
    )


def run_conductor(data_root: Path, github_output: str | None = None) -> int:
    d = decide_now(data_root)
    print(json.dumps(d, indent=1))
    if github_output:
        with open(github_output, "a") as f:
            for k in ("capture", "context", "simulate", "settle", "evaluate", "discover", "in_season", "calendar_known"):
                f.write(f"{k}={'true' if d[k] else 'false'}\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Stdlib-only entry point: ``PYTHONPATH=src python -m nba_edge.workflows.conductor``.

    The scheduled decision job runs 144x/day purely to read a few timestamps. Going through the
    ``nba`` console script would force ``pip install -e .`` (a ~690MB environment, ~23s per wake,
    billed per job) before it could do so. This module and everything it imports are stdlib-only --
    see ``nba_edge.archive.status`` -- so the workflow can skip the install entirely.
    """
    import argparse

    ap = argparse.ArgumentParser(prog="nba-conductor", description=__doc__)
    ap.add_argument("--data", default="data", type=Path)
    ap.add_argument("--github-output", default=None)
    a = ap.parse_args(argv)
    return run_conductor(a.data, a.github_output)


if __name__ == "__main__":
    raise SystemExit(main())
