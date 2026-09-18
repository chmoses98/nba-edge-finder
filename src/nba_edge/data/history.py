"""Historical NBA dataset puller (ESPN site API) -> flat per-player and per-team game rows in Parquet.

Design
------
- The network layer is deliberately thin (:func:`fetch_json`); everything else is a pure function over the
  ESPN JSON shape so it can be tested from small fixtures without network access.
- Scoreboard per date (``?dates=YYYYMMDD``) lists events; each completed event's summary (``?event=<id>``)
  supplies period linescores and per-player box lines. Player ids are ESPN athlete ids stored *negative*
  (``nba_id = -athlete_id``) exactly like :func:`nba_edge.data.boxscore.parse_espn_summary`.
- Resumable: per-season ``done_events_<season>.json`` + already-written Parquet decide which events are done,
  and :func:`should_skip_date` skips a date entirely when its scoreboard is cached and every event is done.
- Never raises on one bad game: the error is recorded in ``MANIFEST.json`` and the loop continues.

Outputs (``out_root/espn/``): ``player_games_<season>.parquet``, ``team_games_<season>.parquet``,
``done_events_<season>.json``, ``MANIFEST.json``.
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterable, Iterator
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from nba_edge.config import settings
from nba_edge.data.boxscore import ESPN_SUMMARY_URL, parse_espn_summary
from nba_edge.data.http import PLAIN_HEADERS_OK, _cache_path, fetch
from nba_edge.data.schedule import ESPN_SCOREBOARD_URL
from nba_edge.identity.teams import TeamIdentityError, registry
from nba_edge.log import get_logger, kv
from nba_edge.schemas.core import SeasonType
from nba_edge.settlement.boxscore import FinalBoxScore
from nba_edge.timeutil import ET, et_date, iso, parse_iso, utcnow

log = get_logger(__name__)

ESPN_SEASON_TYPES = {1: SeasonType.PRESEASON, 2: SeasonType.REGULAR, 3: SeasonType.PLAYOFFS}
ESPN_WHAT = {"espn", "team_logs", "player_logs", "team_games", "player_games"}

DAY_S = 86_400.0
SCOREBOARD_TTL_PAST_S = 30 * DAY_S
SCOREBOARD_TTL_RECENT_S = 600.0
SUMMARY_TTL_S = 10 * 365 * DAY_S
CHECKPOINT_EVERY = 100
PROGRESS_EVERY = 50

PLAYER_COLUMNS = [
    "game_id", "game_date_et", "season", "season_type", "team_id", "opp_team_id", "home", "nba_id", "player_name",
    "started", "played", "minutes", "pts", "reb", "ast", "fg3m", "stl", "blk", "tov", "fga", "fta", "fgm", "oreb",
    "dreb", "fg3a", "ftm", "pf", "plus_minus", "dnp_reason", "team_pts", "opp_pts", "n_ot",
]
TEAM_COLUMNS = [
    "game_id", "game_date_et", "season", "season_type", "team_id", "opp_team_id", "home", "pts", "opp_pts", "q1", "q2",
    "q3", "q4", "ot_pts", "n_ot", "won", "margin", "total", "fga", "fta", "oreb", "tov", "possessions", "totals_source",
]

# ESPN stat keys (player ``statistics[0].keys`` and team ``statistics[].name``)
K_FG = "fieldGoalsMade-fieldGoalsAttempted"
K_FG3 = "threePointFieldGoalsMade-threePointFieldGoalsAttempted"
K_FT = "freeThrowsMade-freeThrowsAttempted"


# --------------------------------------------------------------------------------------------------------------
# seasons / dates
# --------------------------------------------------------------------------------------------------------------
def season_years(season: str) -> tuple[int, int]:
    """'2024-25' -> (2024, 2025)."""
    s = season.strip()
    try:
        y0 = int(s[:4])
        tail = s.split("-", 1)[1]
        y1 = int(tail) if len(tail) == 4 else y0 // 100 * 100 + int(tail)
    except (ValueError, IndexError) as e:
        raise ValueError(f"bad season {season!r}; expected 'YYYY-YY'") from e
    if y1 != y0 + 1:
        raise ValueError(f"bad season {season!r}; second year must follow first")
    return y0, y1


def iter_season_dates(season: str) -> Iterator[date]:
    """Yield every calendar date from Oct 1 of the first year through Jun 30 of the second year, inclusive."""
    y0, y1 = season_years(season)
    d, end = date(y0, 10, 1), date(y1, 6, 30)
    while d <= end:
        yield d
        d += timedelta(days=1)


def scoreboard_url(d: date) -> str:
    return ESPN_SCOREBOARD_URL.format(yyyymmdd=d.strftime("%Y%m%d"))


def summary_url(event_id: str) -> str:
    return ESPN_SUMMARY_URL.format(event_id=event_id)


def scoreboard_settle_instant(d: date) -> datetime:
    """Instant after which a date's scoreboard is final: noon UTC the following day (late ET tips end ~3am ET)."""
    return datetime(d.year, d.month, d.day, 12, tzinfo=UTC) + timedelta(days=1)


def scoreboard_ttl_s(d: date, now: datetime | None = None) -> float:
    """Cache TTL for a date's scoreboard. A past date's cache is trusted for 30 days *but only if it was fetched
    after the games were over* (ttl = age allowed = now - settle instant); a recent date is re-polled every 10 min."""
    now = now or utcnow()
    allowed = (now - scoreboard_settle_instant(d)).total_seconds()
    if allowed <= 0:
        return SCOREBOARD_TTL_RECENT_S
    return min(SCOREBOARD_TTL_PAST_S, allowed)


# --------------------------------------------------------------------------------------------------------------
# network seam
# --------------------------------------------------------------------------------------------------------------
def fetch_json(url: str, ttl_s: float, cache_root: Path | None = None) -> tuple[dict[str, Any], bool]:
    """GET+cache via :func:`nba_edge.data.http.fetch`. Returns (payload, from_cache). Monkeypatched in tests."""
    f = fetch(url, headers=PLAIN_HEADERS_OK, ttl_s=ttl_s, cache_root=cache_root)
    return f.json(), f.from_cache


def cached_scoreboard(d: date, cache_root: Path, now: datetime | None = None) -> dict[str, Any] | None:
    """Return the cached scoreboard payload for ``d`` if a *valid* cache entry exists (see scoreboard_ttl_s), else None.
    Reads the disk cache only; never touches the network."""
    cp = _cache_path(scoreboard_url(d), cache_root)
    meta = cp.with_suffix(".meta.json")
    if not (cp.exists() and meta.exists()):
        return None
    try:
        m = json.loads(meta.read_text())
        now_s = (now or utcnow()).timestamp()
        if now_s - float(m["t"]) > scoreboard_ttl_s(d, now):
            return None
        return json.loads(cp.read_bytes())
    except (json.JSONDecodeError, KeyError, ValueError, OSError):
        return None


# --------------------------------------------------------------------------------------------------------------
# scoreboard parsing
# --------------------------------------------------------------------------------------------------------------
def scoreboard_events(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Completed NBA events from a scoreboard payload -> light meta dicts (id, date, season_type, teams).

    Events whose teams are not NBA teams (All-Star, preseason vs international clubs) are skipped, as are events
    whose ``season.type`` is not 1/2/3.
    """
    reg = registry()
    out: list[dict[str, Any]] = []
    for ev in payload.get("events", []) or []:
        comp = (ev.get("competitions") or [{}])[0]
        st = (comp.get("status") or ev.get("status") or {}).get("type", {}) or {}
        if not st.get("completed"):
            continue
        stype_raw = (ev.get("season") or {}).get("type")
        stype = ESPN_SEASON_TYPES.get(stype_raw)
        if stype is None:
            continue
        teams = {c.get("homeAway"): c for c in comp.get("competitors", [])}
        try:
            home = reg.by_tricode(teams["home"]["team"]["abbreviation"])
            away = reg.by_tricode(teams["away"]["team"]["abbreviation"])
        except (KeyError, TeamIdentityError):
            continue
        raw_date = ev.get("date") or comp.get("date")
        if not raw_date:
            continue
        tip = parse_iso(raw_date)
        out.append(
            {
                "event_id": str(ev.get("id")), "game_id": f"espn:{ev.get('id')}", "game_date_et": et_date(tip),
                "start_time_utc": iso(tip), "season_type": stype.value, "espn_season_type": stype_raw,
                "espn_season_year": (ev.get("season") or {}).get("year"), "home_team_id": home.team_id,
                "away_team_id": away.team_id, "home_tricode": home.tricode, "away_tricode": away.tricode,
            }
        )
    return out


def should_skip_date(cache_exists: bool, event_ids: Iterable[str], done: set[str]) -> bool:
    """Skip a date when its scoreboard is already cached *and* every (completed) event on it is done.
    A cached date with zero events is trivially skippable; an uncached date never is."""
    return bool(cache_exists) and all(e in done for e in event_ids)


# --------------------------------------------------------------------------------------------------------------
# summary parsing (extended: made-attempted splits, team totals)
# --------------------------------------------------------------------------------------------------------------
def split_made_att(v: Any) -> tuple[int, int]:
    """'7-15' -> (7, 15); '--'/None/'' -> (0, 0); '7' -> (7, 0)."""
    if v in (None, "", "--"):
        return 0, 0
    parts = str(v).split("-")
    try:
        made = int(float(parts[0])) if parts[0] not in ("", "--") else 0
        att = int(float(parts[1])) if len(parts) > 1 and parts[1] not in ("", "--") else 0
    except ValueError:
        return 0, 0
    return made, att


def to_int(v: Any) -> int:
    if v in (None, "", "--"):
        return 0
    try:
        return int(float(str(v).replace("+", "")))
    except ValueError:
        return 0


def parse_espn_summary_extended(payload: dict[str, Any], fetched_at_utc: datetime | None = None) -> tuple[FinalBoxScore, list[dict[str, Any]]]:
    """``parse_espn_summary`` plus a re-parse of the raw player groups for the made/attempted splits that
    ``PlayerLine`` does not carry. The extra list is aligned with ``box.players`` (same walk order) and each dict
    also carries ``nba_id``/``team_id`` so callers can join defensively."""
    box = parse_espn_summary(payload, fetched_at_utc)
    reg = registry()
    extra: list[dict[str, Any]] = []
    for tp in (payload.get("boxscore") or {}).get("players", []) or []:
        tid = reg.by_tricode(tp["team"]["abbreviation"]).team_id
        for grp in tp.get("statistics", []) or []:
            keys = grp.get("keys", []) or []
            for a in grp.get("athletes", []) or []:
                vals = dict(zip(keys, a.get("stats", []) or [], strict=False))
                dnp = bool(a.get("didNotPlay", False))
                fgm, fga = split_made_att(vals.get(K_FG)) if not dnp else (0, 0)
                fg3m, fg3a = split_made_att(vals.get(K_FG3)) if not dnp else (0, 0)
                ftm, fta = split_made_att(vals.get(K_FT)) if not dnp else (0, 0)
                extra.append(
                    {
                        "nba_id": -int(a["athlete"]["id"]), "team_id": tid, "fgm": fgm, "fga": fga, "fg3a": fg3a, "ftm": ftm,
                        "fta": fta, "fg3m": fg3m, "oreb": to_int(vals.get("offensiveRebounds")) if not dnp else 0,
                        "dreb": to_int(vals.get("defensiveRebounds")) if not dnp else 0, "pf": to_int(vals.get("fouls")) if not dnp else 0,
                        "plus_minus": to_int(vals.get("plusMinus")) if not dnp else 0,
                    }
                )
    return box, extra


def parse_espn_team_totals(payload: dict[str, Any]) -> dict[int, dict[str, int]]:
    """``boxscore.teams[].statistics`` (list of {name, displayValue}) -> {team_id: {fga, fgm, fta, ftm, oreb, dreb, tov, ...}}.
    Returns {} when the block is absent; a team is included only if it has FGA (else callers fall back to player sums)."""
    reg = registry()
    out: dict[int, dict[str, int]] = {}
    for t in (payload.get("boxscore") or {}).get("teams", []) or []:
        try:
            tid = reg.by_tricode(t["team"]["abbreviation"]).team_id
        except (KeyError, TeamIdentityError):
            continue
        stats = {s.get("name"): s.get("displayValue") for s in t.get("statistics", []) or [] if s.get("name")}
        if K_FG not in stats:
            continue
        fgm, fga = split_made_att(stats.get(K_FG))
        fg3m, fg3a = split_made_att(stats.get(K_FG3))
        ftm, fta = split_made_att(stats.get(K_FT))
        # ESPN reports both player 'turnovers' and 'totalTurnovers' (incl. team TOs); prefer the total when present.
        tov = to_int(stats.get("totalTurnovers")) if stats.get("totalTurnovers") not in (None, "", "--") else to_int(stats.get("turnovers"))
        out[tid] = {
            "fgm": fgm, "fga": fga, "fg3m": fg3m, "fg3a": fg3a, "ftm": ftm, "fta": fta, "oreb": to_int(stats.get("offensiveRebounds")),
            "dreb": to_int(stats.get("defensiveRebounds")), "reb": to_int(stats.get("totalRebounds") or stats.get("rebounds")),
            "ast": to_int(stats.get("assists")), "tov": tov, "stl": to_int(stats.get("steals")), "blk": to_int(stats.get("blocks")),
        }
    return out


# --------------------------------------------------------------------------------------------------------------
# row builders
# --------------------------------------------------------------------------------------------------------------
def possessions(fga: float, fta: float, oreb: float, tov: float) -> float:
    """Basketball-Reference-style estimate: 0.96 * (FGA + 0.44*FTA - OREB + TOV)."""
    return round(0.96 * (fga + 0.44 * fta - oreb + tov), 3)


def _meta_fields(game_meta: dict[str, Any], box: FinalBoxScore) -> dict[str, Any]:
    return {
        "game_id": game_meta.get("game_id") or box.game_id, "game_date_et": game_meta.get("game_date_et") or (et_date(box.actual_tip_utc) if box.actual_tip_utc else None),
        "season": game_meta.get("season"), "season_type": game_meta.get("season_type"),
    }


def parse_player_rows(box: FinalBoxScore, game_meta: dict[str, Any], extra: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Flat per-player rows for one game. ``extra`` (from parse_espn_summary_extended) supplies fga/fgm/fta/oreb/dreb;
    missing entries default to 0. DNP players get played=False, minutes=0, zero counting stats."""
    meta = _meta_fields(game_meta, box)
    ex_by_key = {(e["team_id"], e["nba_id"]): e for e in (extra or [])}
    rows: list[dict[str, Any]] = []
    for p in box.players:
        e = ex_by_key.get((p.team_id, p.nba_id), {})
        home = p.team_id == box.home_team_id
        team_pts = box.home_pts if home else box.away_pts
        opp_pts = box.away_pts if home else box.home_pts
        played = bool(p.played)
        rows.append(
            {
                **meta, "team_id": p.team_id, "opp_team_id": box.opponent_of(p.team_id), "home": home, "nba_id": p.nba_id,
                "player_name": p.name, "started": bool(p.started), "played": played, "minutes": float(p.minutes) if played else 0.0,
                "pts": p.pts, "reb": p.reb, "ast": p.ast, "fg3m": p.fg3m, "stl": p.stl, "blk": p.blk, "tov": p.tov,
                "fga": int(e.get("fga", 0)), "fta": int(e.get("fta", 0)), "fgm": int(e.get("fgm", 0)), "oreb": int(e.get("oreb", 0)),
                "dreb": int(e.get("dreb", 0)), "fg3a": int(e.get("fg3a", 0)), "ftm": int(e.get("ftm", 0)), "pf": int(e.get("pf", 0)),
                "plus_minus": int(e.get("plus_minus", 0)), "dnp_reason": p.dnp_reason, "team_pts": team_pts, "opp_pts": opp_pts,
                "n_ot": box.n_ot,
            }
        )
    return rows


def parse_team_rows(
    box: FinalBoxScore, game_meta: dict[str, Any], team_totals: dict[int, dict[str, int]] | None = None,
    player_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """One row per team per game with period scores and a possessions estimate.

    FGA/FTA/OREB/TOV come from ESPN team totals when present for that team, else from summing ``player_rows``
    (which must then be supplied, e.g. from parse_player_rows)."""
    meta = _meta_fields(game_meta, box)
    team_totals = team_totals or {}
    rows: list[dict[str, Any]] = []
    for idx, tid in enumerate((box.home_team_id, box.away_team_id)):
        home = idx == 0
        pts = box.home_pts if home else box.away_pts
        opp_pts = box.away_pts if home else box.home_pts
        q = [box.period_scores.get(f"{i}Q", (0, 0))[idx] for i in range(1, 5)]
        ot_pts = sum(v[idx] for k, v in box.period_scores.items() if k.startswith("OT"))
        tt = team_totals.get(tid)
        if tt:
            fga, fta, oreb, tov, src = tt["fga"], tt["fta"], tt["oreb"], tt["tov"], "team_totals"
        else:
            mine = [r for r in (player_rows or []) if r["team_id"] == tid]
            fga, fta = sum(r["fga"] for r in mine), sum(r["fta"] for r in mine)
            oreb, tov = sum(r["oreb"] for r in mine), sum(r["tov"] for r in mine)
            src = "player_sum" if mine else "none"
        rows.append(
            {
                **meta, "team_id": tid, "opp_team_id": box.opponent_of(tid), "home": home, "pts": pts, "opp_pts": opp_pts,
                "q1": q[0], "q2": q[1], "q3": q[2], "q4": q[3], "ot_pts": ot_pts, "n_ot": box.n_ot, "won": pts > opp_pts,
                "margin": pts - opp_pts, "total": pts + opp_pts, "fga": fga, "fta": fta, "oreb": oreb, "tov": tov,
                "possessions": possessions(fga, fta, oreb, tov), "totals_source": src,
            }
        )
    return rows


def build_game_rows(summary: dict[str, Any], game_meta: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Raw ESPN summary + scoreboard meta -> (player_rows, team_rows)."""
    box, extra = parse_espn_summary_extended(summary)
    prow = parse_player_rows(box, game_meta, extra)
    trow = parse_team_rows(box, game_meta, parse_espn_team_totals(summary), prow)
    return prow, trow


# --------------------------------------------------------------------------------------------------------------
# parquet i/o
# --------------------------------------------------------------------------------------------------------------
def write_parquet(rows: list[dict[str, Any]], path: Path, columns: list[str] | None = None) -> int:
    """Write rows to Parquet (pyarrow engine), creating parent dirs. Returns the row count. Empty rows -> empty frame."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    if columns:
        for c in columns:
            if c not in df.columns:
                df[c] = None
        df = df[columns + [c for c in df.columns if c not in columns]]
    df.to_parquet(path, engine="pyarrow", index=False)
    return len(df)


def read_parquet(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path, engine="pyarrow")


def _season_paths(out_root: Path, season: str) -> dict[str, Path]:
    d = Path(out_root) / "espn"
    return {
        "dir": d, "players": d / f"player_games_{season}.parquet", "teams": d / f"team_games_{season}.parquet",
        "done": d / f"done_events_{season}.json", "manifest": d / "MANIFEST.json",
    }


def _load_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    df = read_parquet(path)
    return df.to_dict("records") if len(df) else []


def _dedupe(rows: list[dict[str, Any]], key: tuple[str, ...]) -> list[dict[str, Any]]:
    seen: dict[tuple, dict[str, Any]] = {}
    for r in rows:
        seen[tuple(r.get(k) for k in key)] = r  # later rows (this run) win
    return sorted(seen.values(), key=lambda r: (str(r.get("game_date_et") or ""), str(r.get("game_id") or ""), str(r.get("team_id")), str(r.get("nba_id", ""))))


def load_player_games(out_root: Path, seasons: Iterable[str]) -> pd.DataFrame:
    frames = [read_parquet(_season_paths(out_root, s)["players"]) for s in seasons if _season_paths(out_root, s)["players"].exists()]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=PLAYER_COLUMNS)


def load_team_games(out_root: Path, seasons: Iterable[str]) -> pd.DataFrame:
    frames = [read_parquet(_season_paths(out_root, s)["teams"]) for s in seasons if _season_paths(out_root, s)["teams"].exists()]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=TEAM_COLUMNS)


# --------------------------------------------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------------------------------------------
class _SeasonState:
    def __init__(self, out_root: Path, season: str) -> None:
        self.season = season
        self.paths = _season_paths(out_root, season)
        self.players = _load_rows(self.paths["players"])
        self.teams = _load_rows(self.paths["teams"])
        self.done: set[str] = {str(r["game_id"]) for r in self.teams}
        if self.paths["done"].exists():
            try:
                self.done |= set(json.loads(self.paths["done"].read_text()).get("events", []))
            except (json.JSONDecodeError, AttributeError):
                log.warning(kv(event="history_done_events_unreadable", path=str(self.paths["done"])))
        self.n_new = 0
        self.errors: list[dict[str, Any]] = []

    def flush(self) -> None:
        self.players = _dedupe(self.players, ("game_id", "team_id", "nba_id"))
        self.teams = _dedupe(self.teams, ("game_id", "team_id"))
        write_parquet(self.players, self.paths["players"], PLAYER_COLUMNS)
        write_parquet(self.teams, self.paths["teams"], TEAM_COLUMNS)
        self.paths["done"].write_text(json.dumps({"season": self.season, "events": sorted(self.done), "updated_at": iso(utcnow())}, indent=0))

    def summary(self) -> dict[str, Any]:
        dates = sorted({str(r["game_date_et"]) for r in self.teams if r.get("game_date_et")})
        return {
            "n_games": len({r["game_id"] for r in self.teams}), "n_player_rows": len(self.players), "n_team_rows": len(self.teams),
            "n_new_games_this_run": self.n_new, "date_min": dates[0] if dates else None, "date_max": dates[-1] if dates else None,
            "n_errors_this_run": len(self.errors),
            "season_types": sorted({str(r.get("season_type")) for r in self.teams}),
        }


def _write_manifest(path: Path, seasons: dict[str, dict[str, Any]], errors: list[dict[str, Any]], what: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    m = {
        "pulled_at": iso(utcnow()), "source": "espn_site_api", "what": what, "seasons": seasons,
        "n_games": sum(s["n_games"] for s in seasons.values()), "n_player_rows": sum(s["n_player_rows"] for s in seasons.values()),
        "n_team_rows": sum(s["n_team_rows"] for s in seasons.values()), "n_errors": len(errors), "errors": errors[:500],
    }
    path.write_text(json.dumps(m, indent=2))


def run_history_pull(out_root: Path, seasons: list[str], what: list[str], sleep_s: float = 0.25, max_games: int | None = None) -> int:
    """Pull ESPN scoreboards+summaries for each season into Parquet under ``out_root/espn``. Returns 0 (errors are
    recorded in MANIFEST.json rather than raised). ``max_games`` caps *new* games per run (for smoke tests)."""
    what = [w.strip().lower() for w in what if w.strip()]
    if not any(w in ESPN_WHAT for w in what):
        log.warning(kv(event="history_nothing_to_do", what=",".join(what)))
        return 0
    for w in what:
        if w not in ESPN_WHAT:
            log.warning(kv(event="history_unknown_what", what=w))
    out_root = Path(out_root)
    cache_root = settings().cache_root
    seasons = [s.strip() for s in seasons if s.strip()]
    today_et = datetime.now(tz=ET).date()
    all_errors: list[dict[str, Any]] = []
    season_summaries: dict[str, dict[str, Any]] = {}
    manifest_path = _season_paths(out_root, "x")["manifest"]
    t_start = time.time()
    n_pulled_total = 0
    stop = False

    for season in seasons:
        try:
            season_years(season)
        except ValueError as e:
            all_errors.append({"season": season, "error": str(e)})
            log.error(kv(event="history_bad_season", season=season, err=str(e)))
            continue
        st = _SeasonState(out_root, season)
        log.info(kv(event="history_season_start", season=season, already_done=len(st.done)))
        n_dates = n_skipped = 0
        for d in iter_season_dates(season):
            if stop:
                break
            if d > today_et:
                break
            n_dates += 1
            now = utcnow()
            sb = cached_scoreboard(d, cache_root, now)
            if sb is not None:
                evs = scoreboard_events(sb)
                if should_skip_date(True, [e["game_id"] for e in evs], st.done):
                    n_skipped += 1
                    continue
            else:
                try:
                    sb, _ = fetch_json(scoreboard_url(d), scoreboard_ttl_s(d, now), cache_root)
                except Exception as e:  # noqa: BLE001 - one bad date must not kill the run
                    err = {"season": season, "date": d.isoformat(), "stage": "scoreboard", "error": f"{type(e).__name__}: {e}"[:300]}
                    st.errors.append(err)
                    log.warning(kv(event="history_scoreboard_error", **err))
                    continue
                evs = scoreboard_events(sb)
            for ev in evs:
                if ev["game_id"] in st.done:
                    continue
                meta = {**ev, "season": season}
                try:
                    payload, from_cache = fetch_json(summary_url(ev["event_id"]), SUMMARY_TTL_S, cache_root)
                    prow, trow = build_game_rows(payload, meta)
                    if not trow:
                        raise ValueError("no team rows parsed")
                    st.players.extend(prow)
                    st.teams.extend(trow)
                    st.done.add(ev["game_id"])
                    st.n_new += 1
                    n_pulled_total += 1
                except Exception as e:  # noqa: BLE001
                    from_cache = True
                    err = {"season": season, "date": ev["game_date_et"], "game_id": ev["game_id"], "stage": "summary", "error": f"{type(e).__name__}: {e}"[:300]}
                    st.errors.append(err)
                    log.warning(kv(event="history_game_error", **err))
                if n_pulled_total and n_pulled_total % PROGRESS_EVERY == 0:
                    log.info(kv(event="history_progress", season=season, date=d.isoformat(), games=n_pulled_total, errors=len(st.errors), elapsed_s=int(time.time() - t_start)))
                if st.n_new and st.n_new % CHECKPOINT_EVERY == 0:
                    st.flush()
                if not from_cache and sleep_s > 0:
                    time.sleep(sleep_s)
                if max_games is not None and n_pulled_total >= max_games:
                    stop = True
                    break
        st.flush()
        season_summaries[season] = st.summary()
        all_errors.extend(st.errors)
        log.info(kv(event="history_season_done", season=season, dates=n_dates, dates_skipped=n_skipped, **st.summary()))
        _write_manifest(manifest_path, season_summaries, all_errors, what)
        if stop:
            log.info(kv(event="history_max_games_reached", max_games=max_games))
            break
    _write_manifest(manifest_path, season_summaries, all_errors, what)
    log.info(kv(event="history_done", seasons=",".join(seasons), games_pulled=n_pulled_total, errors=len(all_errors), elapsed_s=int(time.time() - t_start)))
    return 0
