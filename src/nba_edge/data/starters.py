"""Point-in-time starter capture from the ESPN game summary, replacing the "no source" placeholder.

What is recorded and what is not:
* Only games whose scheduled tip is still in the FUTURE (within ``WINDOW_MIN`` minutes) are fetched, so a row can
  never be a post-tip reading mislabelled as pregame. ``observed_at_utc`` is the time AFTER the fetch returned.
* A team's starters are ``CONFIRMED`` only when exactly five athletes carry ``starter: true`` in
  ``boxscore.players[].statistics[].athletes[]`` (the structure ``data.boxscore`` already parses post-game). Anything
  else is ``NONE_PUBLISHED`` -- with ``n_athletes_listed`` so the lead-time/coverage of ESPN's pregame data can be
  measured from the archive instead of assumed. Whether ESPN publishes starters before tip is NOT assumed here.
* Nothing is projected or guessed.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from nba_edge.archive.ledger import Ledger
from nba_edge.data.boxscore import ESPN_SUMMARY_URL
from nba_edge.data.http import PLAIN_HEADERS_OK, FetchError, fetch
from nba_edge.identity.teams import registry
from nba_edge.log import get_logger, kv
from nba_edge.timeutil import iso, parse_iso, utcnow

log = get_logger(__name__)
STARTERS_KIND = "context/starters"
WINDOW_MIN = 120.0


def parse_espn_starters(body: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """{team_tricode: {"starter_ids": [espn ids with starter=true], "starter_names": [...], "n_athletes_listed": int}}."""
    out: dict[str, dict[str, Any]] = {}
    for tp in (body.get("boxscore") or {}).get("players") or []:
        tri = (tp.get("team") or {}).get("abbreviation")
        if not tri:
            continue
        e = out.setdefault(tri, {"starter_ids": [], "starter_names": [], "n_athletes_listed": 0})
        for grp in tp.get("statistics") or []:
            for a in grp.get("athletes") or []:
                ath = a.get("athlete") or {}
                if ath.get("id") in (None, ""):
                    continue
                e["n_athletes_listed"] += 1
                if a.get("starter") is True:
                    e["starter_ids"].append(str(ath["id"])); e["starter_names"].append(ath.get("displayName") or "")
    return out


def rows_for_game(game: dict[str, Any], body: dict[str, Any], observed_at: datetime) -> list[dict[str, Any]]:
    tip = parse_iso(game["start_time_utc"])
    reg = registry()
    parsed = parse_espn_starters(body)
    rows = []
    for side, tri_key in (("home", "home_tricode"), ("away", "away_tricode")):
        tri = game.get(tri_key)
        p = parsed.get(tri) or {"starter_ids": [], "starter_names": [], "n_athletes_listed": 0}
        ids = list(dict.fromkeys(p["starter_ids"]))
        confirmed = len(ids) == 5 and observed_at < tip
        rows.append({
            "game_id": game["game_id"], "espn_event_id": str(game["game_id"]).split(":", 1)[1], "side": side, "team_tricode": tri,
            "team_id": reg.by_tricode(tri).team_id if tri else None, "state": "CONFIRMED" if confirmed else "NONE_PUBLISHED",
            "starter_espn_ids": ids if confirmed else [], "starter_names": p["starter_names"] if confirmed else [], "n_starters_flagged": len(ids),
            "n_athletes_listed": p["n_athletes_listed"], "tip_utc": iso(tip), "observed_at_utc": iso(observed_at),
            "minutes_to_tip": round((tip - observed_at).total_seconds() / 60, 1), "source": "espn_summary_boxscore",
        })
    return rows


def capture_starters(ledger: Ledger, games: list[dict[str, Any]], *, now: datetime | None = None, fetcher=None, clock=None, window_min: float = WINDOW_MIN) -> dict[str, Any]:
    """``now`` decides which games are in the pre-tip window; ``clock()`` is read AFTER each fetch to stamp observed_at_utc."""
    fetcher = fetcher or (lambda url: fetch(url, headers=PLAIN_HEADERS_OK, ttl_s=None).json())
    clock = clock or utcnow
    now = now or clock()
    st: dict[str, Any] = {"games_considered": 0, "games_fetched": 0, "rows": 0, "confirmed_teams": 0, "failures": []}
    rows: list[dict[str, Any]] = []
    for g in games:
        gid = str(g.get("game_id") or "")
        if not gid.startswith("espn:") or g.get("status") not in (None, "scheduled", "SCHEDULED"):
            continue
        try:
            tip = parse_iso(g["start_time_utc"])
        except (KeyError, TypeError, ValueError):
            continue
        st["games_considered"] += 1
        if not (now < tip <= now + timedelta(minutes=window_min)):
            continue
        try:
            body = fetcher(ESPN_SUMMARY_URL.format(event_id=gid.split(":", 1)[1]))
        except (FetchError, ValueError) as e:
            st["failures"].append(f"{gid}: {str(e)[:100]}")
            continue
        rows += rows_for_game(g, body, clock())
        st["games_fetched"] += 1
    if rows:
        ledger.append_rows(STARTERS_KIND, rows, observed_at=clock(), meta={"n": len(rows)})
    st["rows"] = len(rows)
    st["confirmed_teams"] = sum(r["state"] == "CONFIRMED" for r in rows)
    log.info(kv(event="context_starters", **{k: v for k, v in st.items() if k != "failures"}))
    return st
