"""Dead-man monitor of the Issue #53 sealed-ledger chain (RESEARCH ONLY; standard library only; read-only).

The seal chain (`.github/workflows/exec-shadow-seal.yml`) is a long-lived, self-renewing job: a failed RUN is visible, but a chain that simply STOPS RUNNING (no cron delivered,
successor lost, workflow disabled) produces no failed run at all. This module is evaluated by the existing `nba-watchdog` (the repo's ops monitor, which opens / updates /
closes the single `nba-ops-alert` issue) from two independent facts it can read without trusting the chain:

  * the ledger itself (`exec-shadow-seals`): a game whose seal window has CLOSED with neither a seal nor a MISSED marker means nobody was alive to run even the `watch`
    step; a MISSED marker is the chain reporting a lost game;
  * the workflow runs (`gh run list`): while a seal window is open (or opens within `lead_min`) at least one run of the workflow must be queued or in progress, or must have
    finished within `grace_min`.

Findings use the watchdog's shape: {"severity": "CRITICAL"|"WARN", "code", "detail", ...}.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Any

try:                                   # imported as nba.paper.seal_monitor (watchdog) ...
    from . import seal_windows as SW
except ImportError:                    # ... or run as a script path
    import seal_windows as SW  # type: ignore

CRIT, WARN = "CRITICAL", "WARN"
ALIVE = {"queued", "in_progress", "waiting", "pending", "requested"}


def _run_time(r: dict) -> datetime | None:
    for k in ("updatedAt", "updated_at", "createdAt", "created_at", "startedAt", "run_started_at"):
        if r.get(k):
            return SW.parse_ts(r[k])
    return None


def chain_alive(runs: list[dict], now: datetime, grace_min: float = 20.0) -> tuple[bool, str]:
    """A run is queued / in progress, or one finished within `grace_min` (handover to the successor). Pull-request runs are dry rehearsals and never count."""
    runs = [r for r in runs if r.get("event") != "pull_request"]
    for r in runs:
        if str(r.get("status", "")).lower() in ALIVE:
            return True, f"run {r.get('databaseId') or r.get('id')} is {r.get('status')}"
    done = [t for r in runs if str(r.get("status", "")).lower() == "completed" and (t := _run_time(r)) is not None]
    if done and now - max(done) <= timedelta(minutes=grace_min):
        return True, f"last run finished {int((now - max(done)).total_seconds() // 60)} min ago"
    return False, "no run queued, in progress or recently finished"


def check(context_dir: str, seal_dir: str, runs: list[dict] | None, now: datetime, study: dict | None = None, *, lead_min: float = 45.0, grace_min: float = 20.0,
          missed_lookback_h: float = 36.0, lane: str = "control", liveness: bool = True) -> list[dict[str, Any]]:
    """Findings for ONE lane's ledger. `liveness=False` (second and later lanes) skips the chain-alive check, which the first lane already reports for the shared chain."""
    study = study or SW.load_study(SW.lane_study_path(lane))
    tag = "" if lane == "control" else f"[{lane}] "
    f: list[dict[str, Any]] = []
    games = SW.schedule_games(context_dir, now)
    sealed, missed = SW.list_sealed(seal_dir)
    en = SW.enabled_utc(seal_dir)
    open_or_soon = False
    for g in games:
        w = SW.window(g, study)
        st = SW.game_state(now, g, study, sealed, missed, en)
        label = f"{tag}{g.get('away')}@{g.get('home')} {g['start_utc']}"
        if st == "OPEN" or (st == "NOT_DUE" and w["opens"] - now <= timedelta(minutes=lead_min)):
            open_or_soon = True
        if st == "WINDOW_CLOSED_UNSEALED" and now - w["closes"] >= timedelta(minutes=10) and now - w["tip"] <= timedelta(hours=12):
            f.append({"severity": CRIT, "code": "SEAL_UNMARKED_WINDOW", "game_id": g["game_id"],
                      "detail": f"{label}: seal window closed {int((now - w['closes']).total_seconds() // 60)} min ago with neither a seal nor a MISSED marker: the seal chain is not running"})
        if st == "MISSED" and now - w["tip"] <= timedelta(hours=missed_lookback_h):
            f.append({"severity": CRIT, "code": "SEAL_MISSED", "game_id": g["game_id"],
                      "detail": f"{label}: seal window closed unsealed (MISSED marker); the game is uncounted and was never sealed late"})
    if not liveness:
        return f
    if runs is None:
        if open_or_soon:
            f.append({"severity": WARN, "code": "SEAL_RUNS_UNKNOWN", "detail": "workflow run list unavailable; chain liveness not verified"})
    elif open_or_soon:
        alive, why = chain_alive(runs, now, grace_min)
        if not alive:
            f.append({"severity": CRIT, "code": "SEAL_CHAIN_DEAD",
                      "detail": f"a seal window is open or opens within {int(lead_min)} min and the exec-shadow-seal chain has {why}"})
    return f


def load_runs(path: str | None) -> list[dict] | None:
    if not path or not os.path.exists(path):
        return None
    try:
        d = json.load(open(path))
    except (OSError, ValueError):
        return None
    return d if isinstance(d, list) else None
