"""Point-in-time starter capture from the ESPN CORE roster endpoint.

Why the core roster and not the summary: the SIFT Alpha ESPN probe (run 41543056159, 2026-11-02) found ZERO pregame
starter flags in 15 NBA ``summary`` payloads (``boxscore.players`` is absent before tip), while
``sports.core.api.espn.com/.../competitors/{team}/roster`` returned exactly 5 ``starter: true`` entries per team ~19 min
before tip and 0 at ~49 min (rosters of 11-16 entries were listed either way). So:

* Only games whose scheduled tip is still in the FUTURE (within ``WINDOW_MIN`` minutes) are fetched; ``observed_at_utc``
  is stamped AFTER each fetch returns, so a row can never be a post-tip reading mislabelled as pregame.
* A team is ``CONFIRMED`` only when exactly five DISTINCT players carry ``starter: true``. A full roster is NEVER read as
  a lineup: ``n_roster_entries`` is recorded so coverage can be measured, and the roster size is never used to decide.
* The raw roster entries are stored verbatim (``raw_entries``) with the source URL, so the mapping can be re-audited.
* States: CONFIRMED | NONE_PUBLISHED (roster fetched, starters not flagged yet) | FETCH_FAILED. Nothing is projected.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from nba_edge.archive.ledger import Ledger
from nba_edge.data.http import PLAIN_HEADERS_OK, FetchError, fetch
from nba_edge.identity.teams import TeamIdentityError, registry
from nba_edge.log import get_logger, kv
from nba_edge.timeutil import iso, parse_iso, utcnow

log = get_logger(__name__)
STARTERS_KIND = "context/starters"
WINDOW_MIN = 120.0
ESPN_TEAMS_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams"
ESPN_CORE_ROSTER_URL = (
    "https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/events/{event_id}/competitions/{event_id}/competitors/{team_id}/roster"
)
SOURCE = "espn_core_roster"
BUCKETS = ((0, 20), (20, 30), (30, 45), (45, 60), (60, 90), (90, 120))     # minutes before tip, [lo, hi)


def parse_core_roster(body: dict[str, Any] | None) -> dict[str, Any]:
    """{"entries": [{player_id, name, starter, active, ...}], "starter_ids": [distinct ids with starter is True], "starter_names": [...]}."""
    entries = []
    for e in (body or {}).get("entries") or []:
        pid = e.get("playerId")
        if pid in (None, ""):
            continue
        entries.append({"player_id": str(pid), "name": e.get("displayName") or "", "starter": e.get("starter") is True})
    ids: list[str] = []
    names: list[str] = []
    for e in entries:
        if e["starter"] and e["player_id"] not in ids:
            ids.append(e["player_id"])
            names.append(e["name"])
    return {"entries": entries, "starter_ids": ids, "starter_names": names}


def team_row(game: dict[str, Any], side: str, body: dict[str, Any] | None, observed_at: datetime, url: str, error: str | None = None) -> dict[str, Any]:
    tip = parse_iso(game["start_time_utc"])
    tri = game.get("home_tricode" if side == "home" else "away_tricode")
    p = parse_core_roster(body)
    confirmed = error is None and len(p["starter_ids"]) == 5 and observed_at < tip
    return {
        "game_id": game["game_id"], "espn_event_id": str(game["game_id"]).split(":", 1)[1], "side": side, "team_tricode": tri,
        "team_id": registry().by_tricode(tri).team_id if tri else None,
        "state": "FETCH_FAILED" if error else ("CONFIRMED" if confirmed else "NONE_PUBLISHED"),
        "starter_espn_ids": p["starter_ids"] if confirmed else [], "starter_names": p["starter_names"] if confirmed else [],
        "n_starters_flagged": len(p["starter_ids"]), "n_roster_entries": len(p["entries"]),
        "tip_utc": iso(tip), "observed_at_utc": iso(observed_at), "minutes_to_tip": round((tip - observed_at).total_seconds() / 60, 1),
        "source": SOURCE, "source_url": url, "raw_entries": (body or {}).get("entries") or [], "error": error,
    }


def espn_team_ids(fetcher) -> dict[str, str]:
    """registry tricode -> ESPN team id, resolved with the same alias rules the scoreboard parser uses."""
    out: dict[str, str] = {}
    for sport in fetcher(ESPN_TEAMS_URL).get("sports", []):
        for league in sport.get("leagues", []):
            for t in league.get("teams", []):
                t = t.get("team", {})
                try:
                    out[registry().by_tricode(t.get("abbreviation")).tricode] = str(t.get("id"))
                except TeamIdentityError:
                    continue
    return out


def capture_starters(ledger: Ledger, games: list[dict[str, Any]], *, now: datetime | None = None, fetcher=None, clock=None, window_min: float = WINDOW_MIN) -> dict[str, Any]:
    """``now`` selects the in-window games; ``clock()`` is read AFTER each fetch to stamp observed_at_utc."""
    fetcher = fetcher or (lambda url: fetch(url, headers=PLAIN_HEADERS_OK, ttl_s=0).json())     # ttl 0: never serve a cached (stale) roster
    clock = clock or utcnow
    now = now or clock()
    st: dict[str, Any] = {"games_considered": 0, "games_fetched": 0, "rows": 0, "confirmed_teams": 0, "failures": []}
    due = []
    for g in games:
        gid = str(g.get("game_id") or "")
        if not gid.startswith("espn:") or g.get("status") not in (None, "scheduled", "SCHEDULED"):
            continue
        try:
            tip = parse_iso(g["start_time_utc"])
        except (KeyError, TypeError, ValueError):
            continue
        st["games_considered"] += 1
        if now < tip <= now + timedelta(minutes=window_min):
            due.append(g)
    rows: list[dict[str, Any]] = []
    ids: dict[str, str] = {}
    if due:
        try:
            ids = espn_team_ids(fetcher)
        except (FetchError, ValueError) as e:
            st["failures"].append(f"teams: {str(e)[:100]}")
    for g in due:
        eid = str(g["game_id"]).split(":", 1)[1]
        for side in ("home", "away"):
            tid = ids.get(g.get("home_tricode" if side == "home" else "away_tricode") or "")
            if not tid:
                st["failures"].append(f"{g['game_id']}/{side}: no ESPN team id")
                continue
            url = ESPN_CORE_ROSTER_URL.format(event_id=eid, team_id=tid)
            try:
                body = fetcher(url)
                rows.append(team_row(g, side, body, clock(), url))
            except (FetchError, ValueError) as e:
                st["failures"].append(f"{g['game_id']}/{side}: {str(e)[:100]}")
                rows.append(team_row(g, side, None, clock(), url, error=str(e)[:200]))
        st["games_fetched"] += 1
    if rows:
        ledger.append_rows(STARTERS_KIND, rows, observed_at=clock(), meta={"n": len(rows), "source": SOURCE})
    st["rows"] = len(rows)
    st["confirmed_teams"] = sum(r["state"] == "CONFIRMED" for r in rows)
    log.info(kv(event="context_starters", **{k: v for k, v in st.items() if k != "failures"}))
    return st


def coverage_by_lead_time(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per minutes-before-tip bucket, over archived rows: how often starters were actually published. Uses only observed
    rows; ``full_roster_no_starters`` counts rosters that were listed without starter flags (never counted as confirmed)."""
    out = []
    for lo, hi in BUCKETS:
        b = [r for r in rows if lo <= (r.get("minutes_to_tip") if r.get("minutes_to_tip") is not None else -1) < hi]
        games = {r["game_id"] for r in b}
        both = {g for g in games if sum(r["state"] == "CONFIRMED" for r in b if r["game_id"] == g) == 2}
        out.append({
            "minutes_to_tip": f"{lo}-{hi}", "team_observations": len(b), "games": len(games),
            "confirmed_teams": sum(r["state"] == "CONFIRMED" for r in b), "games_both_confirmed": len(both),
            "full_roster_no_starters": sum(r["state"] == "NONE_PUBLISHED" and r.get("n_roster_entries", 0) > 0 for r in b),
            "fetch_failed": sum(r["state"] == "FETCH_FAILED" for r in b),
            "share_teams_confirmed": round(sum(r["state"] == "CONFIRMED" for r in b) / len(b), 3) if b else None,
        })
    return out
