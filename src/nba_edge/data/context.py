"""Context refresh job: snapshot schedule, injuries and rosters into the ledger (append-only, timestamped).

Sources (as reachable from GitHub Actions per docs/probe/probe_results.md):
- schedule: ESPN scoreboard for today..+N days (NBA CDN is blocked from cloud IPs; adapter kept as fallback for local runs)
- injuries: official NBA injury-report PDF (ak-static.cms.nba.com) + ESPN injuries JSON
- rosters: ESPN team rosters (for identity registry growth)

Everything captured here is stamped with the observation time; the simulation later chooses the latest snapshot
strictly before its data cutoff.
"""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Any

from nba_edge.archive.ledger import Ledger
from nba_edge.data.http import PLAIN_HEADERS_OK, FetchError, fetch
from nba_edge.data.injuries import fetch_espn_injuries, fetch_latest_official_injury_report
from nba_edge.data.schedule import fetch_espn_scoreboard
from nba_edge.log import get_logger, kv
from nba_edge.timeutil import iso, utcnow

log = get_logger(__name__)
ESPN_TEAMS_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams"
ESPN_ROSTER_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/roster"


def fetch_espn_rosters() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    f = fetch(ESPN_TEAMS_URL, headers=PLAIN_HEADERS_OK, ttl_s=None)
    teams = []
    for sport in f.json().get("sports", []):
        for league in sport.get("leagues", []):
            for t in league.get("teams", []):
                teams.append(t.get("team", {}))
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for t in teams:
        tid = t.get("id")
        try:
            r = fetch(ESPN_ROSTER_URL.format(team_id=tid), headers=PLAIN_HEADERS_OK, ttl_s=None)
            for a in r.json().get("athletes", []):
                rows.append({
                    "espn_team_id": tid, "team_abbreviation": t.get("abbreviation"), "espn_athlete_id": a.get("id"), "full_name": a.get("fullName") or a.get("displayName"),
                    "position": (a.get("position") or {}).get("abbreviation"), "jersey": a.get("jersey"), "status": (a.get("status") or {}).get("type"),
                    "injuries": [{"status": i.get("status"), "type": (i.get("details") or {}).get("type")} for i in a.get("injuries", [])],
                })
        except FetchError as e:
            errors.append(f"{t.get('abbreviation')}: {e}"[:200])
    return rows, {"source": "espn_rosters", "n_teams": len(teams), "n_players": len(rows), "errors": errors}


def run_context_refresh(out_root: Path, season: str | None = None, days_ahead: int = 10) -> int:
    ledger = Ledger(out_root)
    now = utcnow()
    status: dict[str, Any] = {"refreshed_at_utc": iso(now)}

    # schedule window
    games: list[dict[str, Any]] = []
    sched_prov = []
    for d in range(days_ahead + 1):
        day = now + timedelta(days=d)
        try:
            gs, prov = fetch_espn_scoreboard(day, ttl_s=None)
            games.extend(g.model_dump(mode="json") | {"_query_date_utc": day.date().isoformat()} for g in gs)
            sched_prov.append(prov)
        except FetchError as e:
            sched_prov.append({"date": day.date().isoformat(), "error": str(e)[:200]})
    e1 = ledger.append_rows("context/schedule", games, observed_at=now, meta={"provenance": sched_prov})
    status["schedule"] = {"rows": e1.rows, "path": e1.path, "days_ahead": days_ahead}
    log.info(kv(event="context_schedule", rows=e1.rows))

    # injuries: official PDF first, ESPN second (both archived; the simulation prefers official when fresh)
    inj_rows: list[dict[str, Any]] = []
    try:
        off, prov = fetch_latest_official_injury_report(now)
        inj_rows.extend(i.model_dump(mode="json") for i in off)
        status["injuries_official"] = prov
    except Exception as e:  # noqa: BLE001 - one source failing must not stop the other
        status["injuries_official"] = {"error": f"{type(e).__name__}: {e}"[:200]}
    try:
        esp, prov = fetch_espn_injuries(now)
        inj_rows.extend(i.model_dump(mode="json") for i in esp)
        status["injuries_espn"] = prov
    except Exception as e:  # noqa: BLE001
        status["injuries_espn"] = {"error": f"{type(e).__name__}: {e}"[:200]}
    e2 = ledger.append_rows("context/injuries", inj_rows, observed_at=now, meta={"official": status.get("injuries_official"), "espn": status.get("injuries_espn")})
    status["injuries"] = {"rows": e2.rows, "path": e2.path}

    # rosters (daily is plenty; caller decides cadence)
    try:
        rows, prov = fetch_espn_rosters()
        e3 = ledger.append_rows("context/rosters", rows, observed_at=now, meta=prov)
        status["rosters"] = {"rows": e3.rows, "path": e3.path} | prov
    except Exception as e:  # noqa: BLE001
        status["rosters"] = {"error": f"{type(e).__name__}: {e}"[:200]}

    (out_root / "STATUS_context.json").write_text(json.dumps(status, indent=1, default=str))
    print(json.dumps(status, indent=1, default=str))
    return 0
