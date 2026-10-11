"""Resumable backfill of the FULL ESPN play-by-play into compact Parquet (research data).

Outputs (``out_root/espn_pbp/``), one family per season, none of which overlaps an existing dataset:

* ``pbp_events_<season>.parquet`` -- every play, all event types (zstd, narrow columns).
* ``pbp_box_<season>.parquet``    -- per-player box lines from the SAME payload (starter, minutes, +/-).
* ``pbp_games_<season>.parquet``  -- one row per game with provenance: ``source``, ``source_url``,
  ``fetched_at_utc``, ``payload_sha256``, ingest/schema versions.
* ``pbp_done_<season>.json``      -- game ids already ingested (re-runs skip them).
* ``PBP_MANIFEST.json``           -- accumulating per-season counts and errors.

Only COMPLETED games of the research season types (regular, play-in, playoffs) are fetched; preseason
and unlabelled games are skipped and counted. A game whose summary cannot be fetched or parsed is
recorded as an error and left out -- it is never filled from another source.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from nba_edge.data.history import (
    fetch_json,
    iter_season_dates,
    scoreboard_events,
    scoreboard_ttl_s,
    scoreboard_url,
    summary_url,
)
from nba_edge.data.http import PLAIN_HEADERS_OK, fetch
from nba_edge.log import get_logger, kv
from nba_edge.pbp.espn_full import BOX_COLUMNS, EVENT_COLUMNS, GAME_COLUMNS, parse_game
from nba_edge.timeutil import ET, iso, utcnow

log = get_logger(__name__)

RESEARCH_SEASON_TYPES = ("regular", "playin", "playoffs")
CHECKPOINT_EVERY = 150

EVENT_DTYPES = {
    "event_id": "Int64", "seq": "Int32", "order": "Int16", "period": "Int8", "clock_s": "float32",
    "type_id": "Int16", "team_id": "Int32", "p1": "Int32", "p2": "Int32", "p3": "Int32",
    "score_value": "Int8", "home_score": "Int16", "away_score": "Int16",
}
BOX_DTYPES = {"team_id": "Int32", "nba_id": "Int32", "minutes": "float32", "plus_minus": "Int16", "pts": "Int16"}


def paths(out_root: Path, season: str) -> dict[str, Path]:
    d = Path(out_root) / "espn_pbp"
    return {
        "dir": d, "events": d / f"pbp_events_{season}.parquet", "box": d / f"pbp_box_{season}.parquet",
        "games": d / f"pbp_games_{season}.parquet", "done": d / f"pbp_done_{season}.json",
        "manifest": d / "PBP_MANIFEST.json",
    }


def _frame(rows: list[dict[str, Any]], columns: list[str], dtypes: dict[str, str]) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=columns)
    for c, t in dtypes.items():
        if c in df.columns:
            df[c] = df[c].astype(t)
    return df


def write_compact(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, engine="pyarrow", index=False, compression="zstd", compression_level=15)


def _read(path: Path) -> pd.DataFrame | None:
    return pd.read_parquet(path) if path.exists() else None


class _Season:
    def __init__(self, out_root: Path, season: str) -> None:
        self.season = season
        self.p = paths(out_root, season)
        self.p["dir"].mkdir(parents=True, exist_ok=True)
        self.done: set[str] = set()
        if self.p["done"].exists():
            try:
                self.done = set(json.loads(self.p["done"].read_text()).get("games", []))
            except (OSError, ValueError, TypeError):
                self.done = set()
        self.frames = {k: _read(self.p[k]) for k in ("events", "box", "games")}
        if self.frames["games"] is not None:
            # the games file is the record of truth for what was ingested; done-file is only a fast path
            self.done |= set(self.frames["games"]["game_id"].astype(str))
        self.new: dict[str, list[dict[str, Any]]] = {"events": [], "box": [], "games": []}
        self.n_new = 0
        self.errors: list[dict[str, Any]] = []
        self.skipped_types: dict[str, int] = {}

    def add(self, ev: list[dict[str, Any]], bx: list[dict[str, Any]], gm: dict[str, Any]) -> None:
        self.new["events"].extend(ev)
        self.new["box"].extend(bx)
        self.new["games"].append(gm)
        self.done.add(gm["game_id"])
        self.n_new += 1

    def flush(self) -> None:
        spec = {"events": (EVENT_COLUMNS, EVENT_DTYPES), "box": (BOX_COLUMNS, BOX_DTYPES), "games": (GAME_COLUMNS, {})}
        for k, (cols, dt) in spec.items():
            if not self.new[k] and self.frames[k] is not None:
                continue
            add = _frame(self.new[k], cols, dt)
            old = self.frames[k]
            df = add if old is None else pd.concat([old, add], ignore_index=True)
            if k == "events":
                df = df.sort_values(["game_id", "order"], kind="stable").reset_index(drop=True)
            elif k == "box":
                df = df.drop_duplicates(["game_id", "team_id", "nba_id"], keep="last").reset_index(drop=True)
            else:
                df = df.drop_duplicates(["game_id"], keep="last").sort_values("game_id").reset_index(drop=True)
            write_compact(df, self.p[k])
            self.frames[k] = df
            self.new[k] = []
        self.p["done"].write_text(json.dumps({"season": self.season, "games": sorted(self.done),
                                              "updated_at": iso(utcnow())}, indent=0))

    def summary(self) -> dict[str, Any]:
        g = self.frames["games"]
        e = self.frames["events"]
        return {
            "games": 0 if g is None else int(len(g)),
            "events": 0 if e is None else int(len(e)),
            "new_games_this_run": self.n_new,
            "by_season_type": {} if g is None else {str(k): int(v) for k, v in g["season_type"].value_counts().items()},
            "fetched_at_min": None if g is None else str(g["fetched_at_utc"].min()),
            "fetched_at_max": None if g is None else str(g["fetched_at_utc"].max()),
            "skipped_non_research_season_type": self.skipped_types,
            "errors_this_run": len(self.errors),
        }


def run_full_pbp_pull(out_root: Path, seasons: list[str], *, max_games: int | None = None,
                      sleep_s: float = 0.1, season_types: tuple[str, ...] = RESEARCH_SEASON_TYPES) -> dict[str, Any]:
    out_root = Path(out_root)
    man_path = paths(out_root, "x")["manifest"]
    manifest: dict[str, Any] = {"seasons": {}, "errors": []}
    if man_path.exists():
        try:
            prior = json.loads(man_path.read_text())
            manifest["seasons"] = prior.get("seasons") or {}
            manifest["errors"] = prior.get("errors") or []
        except (OSError, ValueError):
            pass
    today_et = datetime.now(tz=ET).date()
    for season in [s.strip() for s in seasons if s.strip()]:
        st = _Season(out_root, season)
        log.info(kv(event="pbp_season_start", season=season, already=len(st.done)))
        stop = False
        for d in iter_season_dates(season):
            if stop or d >= today_et:
                break
            now = utcnow()
            try:
                board, _ = fetch_json(scoreboard_url(d), scoreboard_ttl_s(d, now), None)
            except Exception as e:  # noqa: BLE001 - one bad date must not end the pull
                st.errors.append({"season": season, "date": d.isoformat(), "stage": "scoreboard", "error": str(e)[:200]})
                continue
            for g in scoreboard_events(board):
                gid = str(g["game_id"])
                if gid in st.done:
                    continue
                if g.get("season_type") not in season_types:
                    k = str(g.get("season_type"))
                    st.skipped_types[k] = st.skipped_types.get(k, 0) + 1
                    continue
                url = summary_url(g["event_id"])
                try:
                    f = fetch(url, headers=PLAIN_HEADERS_OK, ttl_s=None)
                    payload = f.json()
                    ev, bx, gm = parse_game(
                        payload, {**g, "season": season}, fetched_at_utc=f.fetched_at_utc, source_url=url,
                        from_cache=f.from_cache, payload_sha256=hashlib.sha256(f.content).hexdigest())
                    if not ev:
                        raise ValueError("summary has no plays")
                    if not gm["status_completed"]:
                        raise ValueError("summary status is not completed")
                    st.add(ev, bx, gm)
                except Exception as e:  # noqa: BLE001
                    st.errors.append({"season": season, "game_id": gid, "stage": "summary", "error": f"{type(e).__name__}: {e}"[:200]})
                    log.warning(kv(event="pbp_game_error", game=gid, err=str(e)[:120]))
                if st.n_new and st.n_new % CHECKPOINT_EVERY == 0:
                    st.flush()
                    log.info(kv(event="pbp_progress", season=season, date=d.isoformat(), new=st.n_new))
                if sleep_s:
                    time.sleep(sleep_s)
                if max_games and st.n_new >= max_games:
                    stop = True
                    break
        st.flush()
        manifest["seasons"][season] = st.summary()
        manifest["errors"] = [e for e in manifest["errors"] if e.get("season") != season] + st.errors
        manifest["pulled_at"] = iso(utcnow())
        man_path.write_text(json.dumps(manifest, indent=1))
        log.info(kv(event="pbp_season_done", season=season, **{k: v for k, v in st.summary().items() if isinstance(v, int)}))
    manifest["source"] = "espn_site_api summary (plays + boxscore)"
    man_path.write_text(json.dumps(manifest, indent=1))
    return manifest
