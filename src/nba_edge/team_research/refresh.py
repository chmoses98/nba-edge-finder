"""Scheduled current-season box-score refresh and the freshness/quality gate for the published team research."""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from nba_edge.data.history import current_season, run_history_pull
from nba_edge.timeutil import utcnow


def refresh(out_root: Path, *, seasons: list[str] | None = None, min_interval_s: float = 0.0, now: datetime | None = None, today: date | None = None) -> dict[str, Any]:
    """Pull any newly final games of the current season into ``out_root/espn`` (resumable, incremental). Skips when the last pull is younger than
    ``min_interval_s``. Returns a small status dict and writes ``out_root/espn/REFRESH.json``; never raises on a provider failure (the manifest
    records errors, and the explorer then simply keeps the data it has, labelled with its true age)."""
    now = now or utcnow()
    seasons = seasons or [current_season(today)]
    status_path = Path(out_root) / "espn" / "REFRESH.json"
    prev = json.loads(status_path.read_text()) if status_path.exists() else {}
    if min_interval_s and prev.get("pulled_at"):
        age = (now - datetime.fromisoformat(prev["pulled_at"].replace("Z", "+00:00"))).total_seconds()
        if age < min_interval_s and prev.get("seasons") == seasons:
            return {"skipped": True, "age_s": int(age), **prev}
    rc = run_history_pull(out_root=Path(out_root), seasons=seasons, what=["espn"], resume_window_days=3)
    man = json.loads((Path(out_root) / "espn" / "MANIFEST.json").read_text()) if (Path(out_root) / "espn" / "MANIFEST.json").exists() else {}
    per = {s: (man.get("seasons") or {}).get(s, {}) for s in seasons}
    status = {"pulled_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "seasons": seasons, "rc": rc,
              "games": {s: v.get("n_games") for s, v in per.items()}, "date_max": {s: v.get("date_max") for s, v in per.items()},
              "errors_this_run": {s: v.get("n_errors_this_run") for s, v in per.items()}}
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(json.dumps(status, indent=1))
    return status


def validate_explorer(explorer_dir: Path, *, season: str, now: datetime | None = None, max_age_days: float = 3.0, min_teams: int = 30) -> tuple[bool, dict[str, Any]]:
    """Is the PUBLISHED team research current? Checks, for every team profile under ``explorer_dir/teams``: the profile's season, that the blended and
    current-season metrics exist with a game count above zero, and that the newest observation is younger than ``max_age_days``. This is the same test
    SIFT applies before it opens NBA team research (scripts/probe-nba-freshness.mjs)."""
    now = now or utcnow()
    problems: list[str] = []
    teams = sorted(Path(explorer_dir, "teams").glob("*.json"))
    seen = 0
    newest = None
    for f in teams:
        d = json.loads(f.read_text())
        if d.get("entity_type") != "TEAM":
            continue
        seen += 1
        name = (d.get("entity") or {}).get("short_name") or f.stem
        if d.get("season") != season:
            problems.append(f"{name}: season {d.get('season')} != {season}")
            continue
        mids = {m.get("metric_id"): m for m in d.get("metrics", [])}
        blend = mids.get("met_nba.team_blend_net")
        cur = mids.get("met_nba.team_cur_adj_net")
        if not blend or not cur:
            problems.append(f"{name}: missing blended/current-season metrics")
            continue
        n = (blend.get("sample_size") or 0)
        if n <= 0:
            problems.append(f"{name}: blend built from 0 current-season games")
        asof = (d.get("quality") or {}).get("data_as_of")
        if asof:
            t = datetime.fromisoformat(asof.replace("Z", "+00:00"))
            newest = t if newest is None or t > newest else newest
            if (now - t).total_seconds() > max_age_days * 86400:
                problems.append(f"{name}: data_as_of {asof} older than {max_age_days} d")
    if seen < min_teams:
        problems.append(f"only {seen} team profiles (need {min_teams})")
    return (not problems), {"season": season, "teams": seen, "newest_data_as_of": newest.isoformat() if newest else None, "problems": problems}
