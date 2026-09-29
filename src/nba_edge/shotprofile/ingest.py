"""Historical shot-event ingestion from ESPN summaries.

Reuses the existing ESPN history machinery -- same cache, same headers, same identity convention --
rather than opening a second path to the same host with different manners. The ``done`` set means a
re-run costs nothing for games already ingested, which matters because the full pull is ~1,230
summaries per season.

Writes Parquet next to the box-score datasets. The output is **descriptive**: shot locations and
outcomes. It carries no defender, because no reachable source supplies one.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from nba_edge.config import settings
from nba_edge.data.history import (
    fetch_json,
    iter_season_dates,
    scoreboard_events,
    scoreboard_ttl_s,
    scoreboard_url,
    summary_url,
    write_parquet,
)
from nba_edge.log import get_logger, kv
from nba_edge.shotprofile.court import classify
from nba_edge.shotprofile.events import parse_summary
from nba_edge.timeutil import iso, utcnow

log = get_logger(__name__)

SUMMARY_TTL_S = 90 * 24 * 3600.0  # a finished game's play-by-play never changes

COLUMNS = [
    "game_id", "event_id", "sequence", "event_time_utc", "period", "clock_display",
    "clock_seconds_remaining", "shooter_player_id", "shooter_name", "team_id",
    "opponent_team_id", "is_home", "x", "y", "coordinate_valid", "zone", "distance_ft",
    "shot_made", "points_value", "is_free_throw", "is_shooting_play", "event_type",
    "source", "source_observed_at_utc", "ingest_version", "schema_version",
]


def _paths(out_root: Path, season: str) -> dict[str, Path]:
    d = Path(out_root) / "espn"
    return {
        "dir": d,
        "events": d / f"shot_events_{season}.parquet",
        "done": d / f"shot_done_events_{season}.json",
        "manifest": d / "SHOT_EVENTS_MANIFEST.json",
    }


def _row(ev: Any, tip_utc: datetime | None) -> dict[str, Any]:
    from nba_edge.shotprofile.court import ShotZone, distance_ft

    zone = ShotZone.UNKNOWN
    dist = None
    if ev.usable_for_zone:
        zone = classify(ev.x, ev.y, points_value=ev.points_value)
        dist = round(distance_ft(ev.x, ev.y), 3)

    # The event time is the game's tip instant. ESPN's per-play wallclock is not consistently
    # present, and a shot's exact second does not matter for a point-in-time cutoff that operates
    # at game granularity -- but attributing a shot to the WRONG GAME would matter, so the tip is
    # used rather than a guess, and None is carried through when the tip is unknown.
    return {
        "game_id": ev.game_id,
        "event_id": ev.event_id,
        "sequence": ev.sequence,
        "event_time_utc": iso(tip_utc) if tip_utc else None,
        "period": ev.period,
        "clock_display": ev.clock_display,
        "clock_seconds_remaining": ev.clock_seconds_remaining,
        "shooter_player_id": ev.shooter_player_id,
        "shooter_name": ev.shooter_name,
        "team_id": ev.team_id,
        "opponent_team_id": ev.opponent_team_id,
        "is_home": ev.is_home,
        "x": ev.x,
        "y": ev.y,
        "coordinate_valid": ev.coordinate_valid,
        "zone": zone.value,
        "distance_ft": dist,
        "shot_made": ev.shot_made,
        "points_value": ev.points_value,
        "is_free_throw": ev.is_free_throw,
        "is_shooting_play": ev.is_shooting_play,
        "event_type": ev.event_type,
        "source": ev.source,
        "source_observed_at_utc": iso(ev.source_observed_at_utc) if ev.source_observed_at_utc else None,
        "ingest_version": ev.ingest_version,
        "schema_version": ev.schema_version,
    }


def run_shot_event_pull(
    out_root: Path, seasons: list[str], *, max_games: int | None = None
) -> int:
    """Pull shot events for each season into Parquet. Errors are recorded, never raised.

    A failure on one game must not end the pull: the dataset is built incrementally over many runs
    and one unavailable summary is not a reason to lose the rest.
    """
    out_root = Path(out_root)
    cache_root = settings().cache_root
    now = utcnow()
    # The manifest ACCUMULATES across runs. Rebuilding it from scratch each time meant a
    # single-season run silently erased every other season's record, so the manifest stopped
    # describing the files on disk the moment the backfill was done one season at a time -- which
    # is exactly how a long backfill has to be done.
    man_path = _paths(out_root, "x")["manifest"]
    summary: dict[str, Any] = {"pulled_at": iso(now), "seasons": {}}
    if man_path.exists():
        try:
            prior = json.loads(man_path.read_text())
            if isinstance(prior.get("seasons"), dict):
                summary["seasons"] = prior["seasons"]
        except (OSError, ValueError, TypeError):
            pass  # an unreadable manifest is regenerated, never allowed to abort the pull

    for season in [s.strip() for s in seasons if s.strip()]:
        p = _paths(out_root, season)
        p["dir"].mkdir(parents=True, exist_ok=True)
        done: set[str] = set()
        if p["done"].exists():
            try:
                done = set(json.loads(p["done"].read_text()).get("events", []))
            except (OSError, ValueError, TypeError):
                done = set()

        rows: list[dict[str, Any]] = []
        if p["events"].exists():
            import pandas as pd

            rows = pd.read_parquet(p["events"]).to_dict("records")

        n_new_games = n_new_rows = n_err = 0
        stop = False
        for d in iter_season_dates(season):
            if stop:
                break
            try:
                board, _ = fetch_json(scoreboard_url(d), scoreboard_ttl_s(d, now), cache_root)
            except Exception as e:  # noqa: BLE001
                n_err += 1
                log.warning(kv(event="shot_events_scoreboard_failed", date=str(d), err=str(e)[:120]))
                continue

            for game in scoreboard_events(board):
                gid = str(game.get("game_id") or "")
                if not gid or gid in done:
                    continue
                # scoreboard_events already returns only COMPLETED games and carries the event
                # id and tip time, so no status re-check and no id re-parsing is needed here.
                eid = str(game.get("event_id") or gid.split(":")[-1])
                try:
                    payload, _ = fetch_json(summary_url(eid), SUMMARY_TTL_S, cache_root)
                except Exception as e:  # noqa: BLE001
                    n_err += 1
                    log.warning(kv(event="shot_events_summary_failed", game=gid, err=str(e)[:120]))
                    continue

                tip = None
                try:
                    from nba_edge.timeutil import parse_iso

                    tip = parse_iso(game["start_time_utc"])
                except (KeyError, TypeError, ValueError):
                    tip = None

                evs = parse_summary(payload, game_id=gid, observed_at_utc=now)
                rows.extend(_row(e, tip) for e in evs)
                n_new_rows += len(evs)
                done.add(gid)
                n_new_games += 1
                if max_games is not None and n_new_games >= max_games:
                    stop = True
                    break

        n = write_parquet(rows, p["events"], COLUMNS)
        p["done"].write_text(json.dumps({"season": season, "events": sorted(done),
                                         "updated_at": iso(utcnow())}, indent=1))
        located = sum(1 for r in rows if r.get("coordinate_valid"))
        summary["seasons"][season] = {
            "games_ingested": len(done),
            "new_games_this_run": n_new_games,
            "shot_events": n,
            "new_events_this_run": n_new_rows,
            "located_events": located,
            "located_pct": round(100 * located / n, 2) if n else 0.0,
            "errors": n_err,
        }
        log.info(kv(event="shot_events_season_done", season=season, games=len(done), events=n))

    man_path.parent.mkdir(parents=True, exist_ok=True)
    man_path.write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))
    return 0


def load_shot_events(out_root: Path, seasons: list[str]):
    """Every ingested shot event across the given seasons, as a DataFrame."""
    import pandas as pd

    frames = []
    for s in seasons:
        p = _paths(Path(out_root), s)["events"]
        if p.exists():
            frames.append(pd.read_parquet(p))
    if not frames:
        return pd.DataFrame(columns=COLUMNS)
    return pd.concat(frames, ignore_index=True)
