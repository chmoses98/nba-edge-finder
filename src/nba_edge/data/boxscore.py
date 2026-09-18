"""Final box-score sources -> ``FinalBoxScore`` (settlement/boxscore.py).

Primary: NBA CDN liveData ``boxscore_{gameId}.json`` (official, includes period scores, starters, minutes 'PT34M12.00S').
Fallback: ESPN summary ``?event=<espn id>`` (period linescores + player stats; ESPN athlete ids need identity aliases).
Both parsers are pure functions over JSON so they are testable from fixtures.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from nba_edge.data.http import NBA_HEADERS, PLAIN_HEADERS_OK, fetch
from nba_edge.identity.teams import registry
from nba_edge.schemas.core import GameStatus
from nba_edge.settlement.boxscore import FinalBoxScore, PlayerLine
from nba_edge.timeutil import parse_iso

NBA_CDN_BOX_URL = "https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"
ESPN_SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={event_id}"

_ISO_MIN = re.compile(r"PT(?P<m>\d+)M(?P<s>[\d.]+)S")


def parse_nba_minutes(s: str | None) -> float:
    if not s:
        return 0.0
    m = _ISO_MIN.match(s)
    if m:
        return int(m["m"]) + float(m["s"]) / 60.0
    if ":" in s:
        mm, ss = s.split(":")[:2]
        return int(mm) + float(ss) / 60.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_espn_minutes(v: Any) -> float:
    """ESPN minutes come as '34', '34:12', '--' (did not play) or ''."""
    if v in (None, "", "--", "-"):
        return 0.0
    s = str(v)
    if ":" in s:
        mm, ss = s.split(":")[:2]
        try:
            return int(mm) + float(ss) / 60.0
        except ValueError:
            return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def _nba_status(game_status: int | None, text: str | None) -> GameStatus:
    t = (text or "").lower()
    if "ppd" in t or "postpone" in t:
        return GameStatus.POSTPONED
    if "cancel" in t:
        return GameStatus.CANCELLED
    if "suspend" in t:
        return GameStatus.SUSPENDED
    return {1: GameStatus.SCHEDULED, 2: GameStatus.IN_PROGRESS, 3: GameStatus.FINAL}.get(game_status or 0, GameStatus.UNKNOWN)


def parse_nba_cdn_boxscore(payload: dict[str, Any], fetched_at_utc: datetime | None = None) -> FinalBoxScore:
    g = payload["game"]
    home, away = g["homeTeam"], g["awayTeam"]
    status = _nba_status(g.get("gameStatus"), g.get("gameStatusText"))
    periods: dict[str, tuple[int, int]] = {}
    hp = {p["period"]: p["score"] for p in home.get("periods", [])}
    ap = {p["period"]: p["score"] for p in away.get("periods", [])}
    n_ot = 0
    for per in sorted(set(hp) | set(ap)):
        key = f"{per}Q" if per <= 4 else f"OT{per - 4}"
        if per > 4:
            n_ot += 1
        periods[key] = (int(hp.get(per, 0)), int(ap.get(per, 0)))
    players: list[PlayerLine] = []
    for team in (home, away):
        tid = int(team["teamId"])
        for p in team.get("players", []):
            st = p.get("statistics", {})
            mins = parse_nba_minutes(st.get("minutes"))
            played = p.get("played") == "1" or mins > 0
            players.append(
                PlayerLine(
                    nba_id=int(p["personId"]), team_id=tid, name=p.get("name") or f"{p.get('firstName','')} {p.get('familyName','')}".strip(),
                    played=played, started=p.get("starter") == "1", minutes=mins, pts=int(st.get("points", 0)), reb=int(st.get("reboundsTotal", 0)),
                    ast=int(st.get("assists", 0)), fg3m=int(st.get("threePointersMade", 0)), stl=int(st.get("steals", 0)), blk=int(st.get("blocks", 0)),
                    tov=int(st.get("turnovers", 0)), dnp_reason=(p.get("notPlayingReason") or p.get("notPlayingDescription")) if not played else None,
                )
            )
    tip = g.get("gameTimeUTC")
    return FinalBoxScore(
        game_id=g["gameId"], status=status, home_team_id=int(home["teamId"]), away_team_id=int(away["teamId"]), home_pts=int(home.get("score", 0)),
        away_pts=int(away.get("score", 0)), period_scores=periods, n_ot=n_ot, players=players, source="nba_cdn_boxscore",
        fetched_at_utc=fetched_at_utc or datetime.now(tz=UTC), actual_tip_utc=parse_iso(tip) if tip else None, is_final=status == GameStatus.FINAL,
    )


def fetch_nba_cdn_boxscore(game_id: str, ttl_s: float | None = None) -> FinalBoxScore:
    f = fetch(NBA_CDN_BOX_URL.format(game_id=game_id), headers=NBA_HEADERS, ttl_s=ttl_s)
    return parse_nba_cdn_boxscore(f.json(), parse_iso(f.fetched_at_utc))


def _linescore_value(x: Any) -> int:
    """ESPN summary linescores carry 'displayValue' ('30'); scoreboard linescores carry numeric 'value'."""
    for k in ("value", "displayValue"):
        v = x.get(k) if isinstance(x, dict) else None
        if v not in (None, ""):
            try:
                return int(float(v))
            except (TypeError, ValueError):
                continue
    return 0


def parse_espn_summary(payload: dict[str, Any], fetched_at_utc: datetime | None = None) -> FinalBoxScore:
    """ESPN summary -> FinalBoxScore. Player ids here are ESPN athlete ids (negative-encoded so they can never be
    confused with NBA ids); identity aliasing maps them to NBA ids before settlement."""
    reg = registry()
    header = payload.get("header", {})
    comp = (header.get("competitions") or [{}])[0]
    st = (comp.get("status") or {}).get("type", {})
    status = GameStatus.FINAL if st.get("completed") else GameStatus.IN_PROGRESS if st.get("state") == "in" else GameStatus.SCHEDULED
    if "postpone" in (st.get("description") or "").lower():
        status = GameStatus.POSTPONED
    comps = {c.get("homeAway"): c for c in comp.get("competitors", [])}
    home_c, away_c = comps["home"], comps["away"]
    home = reg.by_tricode(home_c["team"]["abbreviation"])
    away = reg.by_tricode(away_c["team"]["abbreviation"])
    hl = [_linescore_value(x) for x in home_c.get("linescores", [])]
    al = [_linescore_value(x) for x in away_c.get("linescores", [])]
    periods: dict[str, tuple[int, int]] = {}
    n_ot = 0
    for i in range(max(len(hl), len(al))):
        key = f"{i+1}Q" if i < 4 else f"OT{i-3}"
        if i >= 4:
            n_ot += 1
        periods[key] = (hl[i] if i < len(hl) else 0, al[i] if i < len(al) else 0)
    players: list[PlayerLine] = []
    box = payload.get("boxscore", {})
    for tp in box.get("players", []):
        tid = reg.by_tricode(tp["team"]["abbreviation"]).team_id
        for grp in tp.get("statistics", []):
            keys = grp.get("keys", [])
            for a in grp.get("athletes", []):
                vals = dict(zip(keys, a.get("stats", []), strict=False))
                dnp = a.get("didNotPlay", False)
                mins = parse_espn_minutes(vals.get("minutes")) if not dnp else 0.0
                _i = _int_stat_getter(vals)

                players.append(
                    PlayerLine(
                        nba_id=-int(a["athlete"]["id"]), team_id=tid, name=a["athlete"].get("displayName", ""), played=not dnp and mins > 0,
                        started=bool(a.get("starter")), minutes=mins, pts=_i("points"), reb=_i("rebounds"), ast=_i("assists"),
                        fg3m=_i("threePointFieldGoalsMade-threePointFieldGoalsAttempted"), stl=_i("steals"), blk=_i("blocks"), tov=_i("turnovers"),
                        dnp_reason=a.get("reason") if dnp else None,
                    )
                )
    tip = comp.get("date")
    return FinalBoxScore(
        game_id=f"espn:{header.get('id')}", status=status, home_team_id=home.team_id, away_team_id=away.team_id, home_pts=int(home_c.get("score", 0)),
        away_pts=int(away_c.get("score", 0)), period_scores=periods, n_ot=n_ot, players=players, source="espn_summary",
        fetched_at_utc=fetched_at_utc or datetime.now(tz=UTC), actual_tip_utc=parse_iso(tip) if tip else None, is_final=status == GameStatus.FINAL,
    )


def _int_stat_getter(vals: dict[str, Any]):
    def _i(k: str) -> int:
        v = vals.get(k)
        try:
            return int(str(v).split("-")[0]) if v not in (None, "", "--") else 0
        except ValueError:
            return 0

    return _i


def fetch_espn_summary(event_id: str, ttl_s: float | None = None) -> FinalBoxScore:
    f = fetch(ESPN_SUMMARY_URL.format(event_id=event_id), headers=PLAIN_HEADERS_OK, ttl_s=ttl_s)
    return parse_espn_summary(f.json(), parse_iso(f.fetched_at_utc))
