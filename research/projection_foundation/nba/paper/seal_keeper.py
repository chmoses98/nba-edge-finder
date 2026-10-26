"""Seal-chain keeper: decide whether a live run of `exec-shadow-seal.yml` must be (re)started (RESEARCH ONLY; standard library only; no imports from this package).

Why: the sealing chain renews itself while a seal window is open or near, then exits when nothing is due for hours. Its only restart paths were the `*/5` cron bootstrap
(measured ~4% delivery in this repository) or a manual dispatch, so every slate needed a person. `nba-ticker` is already an always-on loop with `actions: write`; it asks this module,
once per quarter hour, whether to dispatch the workflow. The workflow's own idle gate exits in seconds when nothing is due, and its concurrency group (`exec-shadow-seal-live`)
remains the single-writer guarantee: this module only ever says "dispatch" when NO non-PR run of the workflow is queued, waiting, pending or in progress, so a live chain is never
duplicated, and a duplicate dispatch that still slipped through collapses into the group's single pending slot.

    gh run list --workflow exec-shadow-seal.yml --limit 20 --json status,event,createdAt | python nba/paper/seal_keeper.py --now 2026-10-26T16:30:00Z [--last-dispatch ISO]
prints `dispatch: <why>` or `skip: <why>` (exit 0 either way; malformed input -> `skip`, never a dispatch).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

LIVE = {"queued", "waiting", "pending", "requested", "in_progress"}
SEASON_MONTHS = {10, 11, 12, 1, 2, 3, 4, 5, 6}                  # the cron's month field
HOURS_UTC = set(range(12, 24)) | set(range(0, 4))               # the cron's hour field: weekend-afternoon tips through late west-coast games
MIN_GAP_S = 900.0                                               # at most one dispatch per quarter hour, even if the previous one has not shown up yet


def _t(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def decide(runs: list[dict], now: datetime, last_dispatch: datetime | None = None, min_gap_s: float = MIN_GAP_S) -> tuple[str, str]:
    if now.month not in SEASON_MONTHS:
        return "skip", f"out of season (month {now.month})"
    if now.hour not in HOURS_UTC:
        return "skip", f"outside the seal hours (UTC hour {now.hour})"
    live = [r for r in runs if str(r.get("event", "")) != "pull_request" and str(r.get("status", "")).lower() in LIVE]
    if live:
        return "skip", f"a chain run is already alive ({len(live)}: {sorted({str(r.get('status')) for r in live})})"
    if last_dispatch is not None and (now - last_dispatch).total_seconds() < min_gap_s:
        return "skip", f"dispatched {int((now - last_dispatch).total_seconds())} s ago"
    return "dispatch", "no live or queued run of the seal workflow"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--now", default=None, help="ISO UTC (default: the clock)")
    ap.add_argument("--last-dispatch", default=None, help="ISO UTC of this caller's previous dispatch")
    a = ap.parse_args(argv)
    now = _t(a.now) if a.now else datetime.now(timezone.utc)
    try:
        runs = json.load(sys.stdin)
        if not isinstance(runs, list):
            raise ValueError("not a list")
    except (ValueError, OSError) as e:
        print(f"skip: could not read the run list ({e})")
        return 0
    action, why = decide(runs, now, _t(a.last_dispatch) if a.last_dispatch else None)
    print(f"{action}: {why}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
