"""Schedule sources -> canonical ``Game`` rows.

Primary: NBA CDN static schedule (``scheduleLeagueV2_1.json``): full season incl. preseason, game ids, UTC tips.
Fallback: ESPN site API scoreboard per date (``?dates=YYYYMMDD``), which carries ESPN event ids we keep as aliases.
Season type comes from the NBA game id (3rd char) — preseason is *explicitly* tagged, never inferred from dates.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from nba_edge.data.http import NBA_HEADERS, PLAIN_HEADERS_OK, fetch
from nba_edge.identity.teams import TeamIdentityError, registry
from nba_edge.log import get_logger, kv
from nba_edge.schemas.core import Game, GameStatus, season_type_from_game_id
from nba_edge.timeutil import et_date, parse_iso

log = get_logger(__name__)

NBA_CDN_SCHEDULE_URL = "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json"
ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={yyyymmdd}&limit=100"


def _status_from_nba(game_status: int | None, text: str | None) -> GameStatus:
    t = (text or "").lower()
    if "ppd" in t or "postpone" in t:
        return GameStatus.POSTPONED
    if "cancel" in t:
        return GameStatus.CANCELLED
    if "suspend" in t:
        return GameStatus.SUSPENDED
    return {1: GameStatus.SCHEDULED, 2: GameStatus.IN_PROGRESS, 3: GameStatus.FINAL}.get(game_status or 0, GameStatus.UNKNOWN)


def parse_nba_cdn_schedule(payload: dict[str, Any]) -> list[Game]:
    ls = payload.get("leagueSchedule", {})
    season = ls.get("seasonYear") or ""
    games: list[Game] = []
    reg = registry()
    for gd in ls.get("gameDates", []):
        for g in gd.get("games", []):
            gid = g.get("gameId", "")
            try:
                home_tri = g["homeTeam"]["teamTricode"]
                away_tri = g["awayTeam"]["teamTricode"]
                home = reg.by_tricode(home_tri)
                away = reg.by_tricode(away_tri)
            except (KeyError, TeamIdentityError) as e:
                # non-NBA opponents (preseason vs international clubs) are kept out of the canonical game table
                log.info(kv(event="schedule_skip_game", game_id=gid, reason=str(e)[:80]))
                continue
            tip_raw = g.get("gameDateTimeUTC") or g.get("gameDateUTC")
            if not tip_raw:
                continue
            tip = parse_iso(tip_raw if tip_raw.endswith("Z") or "+" in tip_raw else tip_raw + "Z")
            games.append(
                Game(
                    game_id=gid, season=season, season_type=season_type_from_game_id(gid), game_date_et=et_date(tip),
                    start_time_utc=tip, home_team_id=home.team_id, away_team_id=away.team_id, home_tricode=home.tricode,
                    away_tricode=away.tricode, status=_status_from_nba(g.get("gameStatus"), g.get("gameStatusText")),
                    arena=g.get("arenaName"), neutral_site=bool(g.get("isNeutral")), source="nba_cdn_schedule",
                )
            )
    return games


def fetch_nba_cdn_schedule(ttl_s: float = 3600) -> tuple[list[Game], dict[str, Any]]:
    f = fetch(NBA_CDN_SCHEDULE_URL, headers=NBA_HEADERS, ttl_s=ttl_s)
    games = parse_nba_cdn_schedule(f.json())
    return games, {"source": "nba_cdn_schedule", "url": f.url, "fetched_at_utc": f.fetched_at_utc, "from_cache": f.from_cache, "n": len(games)}


def parse_espn_scoreboard(payload: dict[str, Any]) -> list[Game]:
    """ESPN events -> Game rows. NBA game ids are not present; we synthesise 'espn:<id>' and rely on identity
    aliasing later. season_type from ESPN 'season.type' (1 pre, 2 regular, 3 post)."""
    from nba_edge.schemas.core import SeasonType

    reg = registry()
    out = []
    for ev in payload.get("events", []):
        comp = (ev.get("competitions") or [{}])[0]
        teams = {c.get("homeAway"): c for c in comp.get("competitors", [])}
        try:
            home = reg.by_tricode(teams["home"]["team"]["abbreviation"])
            away = reg.by_tricode(teams["away"]["team"]["abbreviation"])
        except (KeyError, TeamIdentityError):
            continue
        tip = parse_iso(ev["date"])
        st = (comp.get("status") or {}).get("type", {})
        state = st.get("state")
        status = GameStatus.FINAL if st.get("completed") else {"pre": GameStatus.SCHEDULED, "in": GameStatus.IN_PROGRESS}.get(state, GameStatus.UNKNOWN)
        if "postpone" in (st.get("description") or "").lower():
            status = GameStatus.POSTPONED
        stype = {1: SeasonType.PRESEASON, 2: SeasonType.REGULAR, 3: SeasonType.PLAYOFFS}.get((ev.get("season") or {}).get("type"), SeasonType.OTHER)
        yr = (ev.get("season") or {}).get("year")
        out.append(
            Game(
                game_id=f"espn:{ev.get('id')}", season=f"{yr-1}-{str(yr)[2:]}" if yr else "", season_type=stype, game_date_et=et_date(tip),
                start_time_utc=tip, home_team_id=home.team_id, away_team_id=away.team_id, home_tricode=home.tricode, away_tricode=away.tricode,
                status=status, arena=((comp.get("venue") or {}).get("fullName")), neutral_site=bool(comp.get("neutralSite")), source="espn_scoreboard",
            )
        )
    return out


def fetch_espn_scoreboard(date_utc: datetime, ttl_s: float = 600) -> tuple[list[Game], dict[str, Any]]:
    url = ESPN_SCOREBOARD_URL.format(yyyymmdd=date_utc.astimezone(UTC).strftime("%Y%m%d"))
    f = fetch(url, headers=PLAIN_HEADERS_OK, ttl_s=ttl_s)
    games = parse_espn_scoreboard(f.json())
    return games, {"source": "espn_scoreboard", "url": url, "fetched_at_utc": f.fetched_at_utc, "from_cache": f.from_cache, "n": len(games)}
