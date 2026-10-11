"""One ESPN ``summary`` payload -> full play-by-play rows (every event type), box rows and one game row.

Pure functions over the JSON shape; no network. Unlike :func:`nba_edge.shotprofile.events.parse_summary`
(which keeps shooting plays only), every element of ``plays`` becomes a row: substitutions, timeouts,
period starts/ends, rebounds, turnovers, fouls, free throws, jump balls, violations, reviews.

Identity conventions match the rest of the project: players are ESPN athlete ids stored NEGATIVE
(``nba_id = -athlete_id``) and teams are the repo's NBA team ids (mapped by tricode through the team
registry). ESPN's own team ids are kept on the game row so the mapping is auditable.

Columns are deliberately few -- coordinates are already in the shot-event dataset and are not
duplicated -- so a season compresses to a few MB of zstd Parquet.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from nba_edge.data.boxscore import parse_espn_minutes
from nba_edge.data.history import parse_espn_team_totals, to_int
from nba_edge.identity.teams import TeamIdentityError, registry
from nba_edge.shotprofile.events import clock_to_seconds
from nba_edge.timeutil import iso

PBP_SCHEMA_VERSION = "pbpfull/1"
PBP_INGEST_VERSION = "espn-summary-full/1"
SOURCE = "espn/summary"

EVENT_COLUMNS = [
    "game_id", "event_id", "seq", "order", "period", "clock_s", "wallclock_utc", "type_id", "type_text",
    "text", "team_id", "p1", "p2", "p3", "scoring_play", "score_value", "shooting_play", "home_score",
    "away_score",
]
BOX_COLUMNS = [
    "game_id", "team_id", "nba_id", "player_name", "starter", "did_not_play", "minutes", "minutes_raw",
    "plus_minus", "pts", "ejected",
]
GAME_COLUMNS = [
    "game_id", "event_id", "season", "season_type", "espn_season_type", "start_time_utc", "home_team_id",
    "away_team_id", "home_espn_team_id", "away_espn_team_id", "home_pts", "away_pts", "n_periods",
    "status_completed", "n_plays", "n_substitutions", "wallclock_present_share", "home_fga", "home_fta",
    "home_oreb", "home_tov", "away_fga", "away_fta", "away_oreb", "away_tov", "source", "source_url",
    "fetched_at_utc", "from_cache", "payload_sha256", "ingest_version", "schema_version",
]


def _int_or_none(v: Any) -> int | None:
    if v is None or isinstance(v, bool):
        return None
    try:
        return int(str(v))
    except (TypeError, ValueError):
        return None


def competitors(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """{'home'|'away': {'espn_id', 'team_id', 'tricode', 'score'}} from the summary header."""
    reg = registry()
    out: dict[str, dict[str, Any]] = {}
    comps = ((payload.get("header") or {}).get("competitions") or [{}])[0]
    for c in comps.get("competitors") or []:
        side = c.get("homeAway")
        if side not in ("home", "away"):
            continue
        tri = ((c.get("team") or {}).get("abbreviation")) or ""
        try:
            tid = reg.by_tricode(tri).team_id
        except TeamIdentityError:
            tid = None
        out[side] = {"espn_id": _int_or_none(c.get("id") or (c.get("team") or {}).get("id")), "team_id": tid,
                     "tricode": tri, "score": _int_or_none(c.get("score"))}
    return out


def parse_events(payload: dict[str, Any], game_id: str) -> list[dict[str, Any]]:
    """Every element of ``plays`` as a flat row, in source order (``order`` is the array index)."""
    comp = competitors(payload)
    espn_to_team = {v["espn_id"]: v["team_id"] for v in comp.values() if v.get("espn_id") is not None}
    rows: list[dict[str, Any]] = []
    for i, p in enumerate(payload.get("plays") or []):
        if not isinstance(p, dict):
            continue
        typ = p.get("type") or {}
        per = p.get("period") or {}
        clk = p.get("clock") or {}
        team = p.get("team") or {}
        parts: list[int | None] = []
        for part in p.get("participants") or []:
            aid = _int_or_none(((part or {}).get("athlete") or {}).get("id")) if isinstance(part, dict) else None
            parts.append(-aid if aid is not None else None)
        parts += [None] * (3 - len(parts))
        sv = p.get("scoreValue")
        rows.append({
            "game_id": game_id,
            "event_id": _int_or_none(p.get("id")),
            "seq": _int_or_none(p.get("sequenceNumber")),
            "order": i,
            "period": _int_or_none(per.get("number")),
            "clock_s": clock_to_seconds(clk.get("displayValue")),
            "wallclock_utc": p.get("wallclock") or None,
            "type_id": _int_or_none(typ.get("id")),
            "type_text": typ.get("text") or None,
            "text": p.get("text") or None,
            "team_id": espn_to_team.get(_int_or_none(team.get("id"))) if isinstance(team, dict) else None,
            "p1": parts[0], "p2": parts[1], "p3": parts[2],
            "scoring_play": bool(p.get("scoringPlay")),
            "score_value": sv if isinstance(sv, int) and not isinstance(sv, bool) else None,
            "shooting_play": bool(p.get("shootingPlay")),
            "home_score": _int_or_none(p.get("homeScore")),
            "away_score": _int_or_none(p.get("awayScore")),
        })
    return rows


def parse_box(payload: dict[str, Any], game_id: str) -> list[dict[str, Any]]:
    """Per-player box lines from the SAME payload (starter flag, minutes, plus-minus), for reconciliation."""
    reg = registry()
    out: list[dict[str, Any]] = []
    for tp in (payload.get("boxscore") or {}).get("players") or []:
        try:
            tid = reg.by_tricode(tp["team"]["abbreviation"]).team_id
        except (KeyError, TypeError, TeamIdentityError):
            continue
        for grp in tp.get("statistics") or []:
            keys = grp.get("keys") or []
            for a in grp.get("athletes") or []:
                aid = _int_or_none((a.get("athlete") or {}).get("id"))
                if aid is None:
                    continue
                vals = dict(zip(keys, a.get("stats") or [], strict=False))
                dnp = bool(a.get("didNotPlay", False))
                pm_raw = vals.get("plusMinus")
                out.append({
                    "game_id": game_id, "team_id": tid, "nba_id": -aid,
                    "player_name": (a.get("athlete") or {}).get("displayName") or "",
                    "starter": bool(a.get("starter")), "did_not_play": dnp,
                    "minutes": 0.0 if dnp else parse_espn_minutes(vals.get("minutes")),
                    "minutes_raw": None if vals.get("minutes") is None else str(vals.get("minutes")),
                    "plus_minus": None if dnp or pm_raw in (None, "", "--") else to_int(pm_raw),
                    "pts": 0 if dnp else to_int(vals.get("points")),
                    "ejected": bool(a.get("ejected", False)),
                })
    return out


def parse_game(
    payload: dict[str, Any], game_meta: dict[str, Any], *, fetched_at_utc: datetime | str | None,
    source_url: str, from_cache: bool, payload_sha256: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """(event rows, box rows, game row) for one summary payload."""
    gid = str(game_meta.get("game_id") or f"espn:{(payload.get('header') or {}).get('id')}")
    events = parse_events(payload, gid)
    box = parse_box(payload, gid)
    comp = competitors(payload)
    hdr = ((payload.get("header") or {}).get("competitions") or [{}])[0]
    st = ((hdr.get("status") or {}).get("type") or {})
    totals = parse_espn_team_totals(payload)
    h, a = comp.get("home", {}), comp.get("away", {})
    ht, at = totals.get(h.get("team_id"), {}), totals.get(a.get("team_id"), {})
    periods = [e["period"] for e in events if e["period"] is not None]
    game = {
        "game_id": gid, "event_id": str(game_meta.get("event_id") or gid.split(":")[-1]),
        "season": game_meta.get("season"), "season_type": game_meta.get("season_type"),
        "espn_season_type": game_meta.get("espn_season_type"), "start_time_utc": game_meta.get("start_time_utc"),
        "home_team_id": h.get("team_id"), "away_team_id": a.get("team_id"),
        "home_espn_team_id": h.get("espn_id"), "away_espn_team_id": a.get("espn_id"),
        "home_pts": h.get("score"), "away_pts": a.get("score"), "n_periods": max(periods) if periods else None,
        "status_completed": bool(st.get("completed")), "n_plays": len(events),
        "n_substitutions": sum(1 for e in events if (e["type_text"] or "").lower() == "substitution"),
        "wallclock_present_share": round(sum(1 for e in events if e["wallclock_utc"]) / len(events), 4) if events else 0.0,
        "home_fga": ht.get("fga"), "home_fta": ht.get("fta"), "home_oreb": ht.get("oreb"), "home_tov": ht.get("tov"),
        "away_fga": at.get("fga"), "away_fta": at.get("fta"), "away_oreb": at.get("oreb"), "away_tov": at.get("tov"),
        "source": SOURCE, "source_url": source_url,
        "fetched_at_utc": iso(fetched_at_utc) if isinstance(fetched_at_utc, datetime) else fetched_at_utc,
        "from_cache": bool(from_cache), "payload_sha256": payload_sha256,
        "ingest_version": PBP_INGEST_VERSION, "schema_version": PBP_SCHEMA_VERSION,
    }
    return events, box, game
