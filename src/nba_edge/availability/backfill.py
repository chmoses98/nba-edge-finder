"""Bounded historical backfill of official NBA injury reports, with point-in-time verification.

For every game of the season (schedule = the committed ESPN team-games dataset, which carries the
scheduled tip), two reports are located on the official 15-minute slot grid:

* ``last_pre_tip``  -- the latest report whose nominal slot is strictly before the tip;
* ``t_minus_60``    -- the latest report whose nominal slot is at least 60 minutes before the tip
  (a decision-time snapshot that leaves room for a T-60m projection run).

A slot is found by HEAD-probing the archive (``ak-static.cms.nba.com``: 200 = published, 403 = no such
report) backwards from the tip. Each distinct report is downloaded once, parsed, stored with its
``fetched_at_utc``, its HTTP ``Last-Modified`` (the publication instant) and a sha256. A game's
snapshot is ``pit_ok`` only if BOTH the nominal slot and the Last-Modified instant precede the tip;
nothing published at or after the tip is ever attached to a game. No post-game source is consulted.

Outputs (``out_root/injury_reports/``): ``reports_<season>.parquet``, ``report_rows_<season>.parquet``,
``game_snapshots_<season>.parquet``, ``probe_cache_<season>.json`` (slot -> status, makes re-runs cheap),
``MANIFEST.json``.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import httpx
import pandas as pd

from nba_edge.availability.identity import PlayerIndex, game_lookup, tricode_to_team_id
from nba_edge.availability.official_report import PARSER_VERSION, parse_report_pdf, report_urls, slot_floor
from nba_edge.data.http import PLAIN_HEADERS_OK
from nba_edge.log import get_logger, kv
from nba_edge.timeutil import ET, iso, parse_iso, utcnow

log = get_logger(__name__)

SEASON_TYPES = ("regular", "playin", "playoffs")
MAX_LOOKBACK_SLOTS = 48  # 12 hours of 15-minute slots
T60 = timedelta(minutes=60)


def paths(out_root: Path, season: str) -> dict[str, Path]:
    d = Path(out_root) / "injury_reports"
    return {"dir": d, "reports": d / f"reports_{season}.parquet", "rows": d / f"report_rows_{season}.parquet",
            "games": d / f"game_snapshots_{season}.parquet", "probe": d / f"probe_cache_{season}.json",
            "manifest": d / "MANIFEST.json"}


def _http_dt(v: str | None) -> datetime | None:
    if not v:
        return None
    try:
        return parsedate_to_datetime(v)
    except (TypeError, ValueError):
        return None


class SlotProber:
    """HEAD-probe report slots with a persistent cache (published slots never disappear; a missing
    slot is cached too, but only for slots older than a day so a late upload is still found)."""

    def __init__(self, client: httpx.Client, cache_path: Path, sleep_s: float = 0.05) -> None:
        self.c = client
        self.path = cache_path
        self.sleep_s = sleep_s
        self.cache: dict[str, dict[str, Any]] = json.loads(cache_path.read_text()) if cache_path.exists() else {}
        self.n_head = 0

    def status(self, slot_et: datetime) -> dict[str, Any]:
        key = slot_et.strftime("%Y-%m-%dT%H:%M")
        if key in self.cache:
            return self.cache[key]
        st: dict[str, Any] = {"code": None}
        for url in report_urls(slot_et):
            try:
                r = self.c.head(url, headers=PLAIN_HEADERS_OK)
                self.n_head += 1
                st = {"code": r.status_code, "last_modified": r.headers.get("last-modified"), "url": url}
            except httpx.HTTPError as e:
                st = {"code": f"error:{type(e).__name__}", "url": url}
            if st["code"] == 200:
                break
        if isinstance(st["code"], int) and (st["code"] == 200 or slot_et < utcnow().astimezone(ET) - timedelta(days=1)):
            self.cache[key] = st
        if self.sleep_s:
            time.sleep(self.sleep_s)
        return st

    def latest_before(self, limit_et: datetime, strict: bool) -> datetime | None:
        s = slot_floor(limit_et)
        if strict and s >= limit_et:
            s -= timedelta(minutes=15)
        for _ in range(MAX_LOOKBACK_SLOTS):
            if self.status(s).get("code") == 200:
                return s
            s -= timedelta(minutes=15)
        return None

    def save(self) -> None:
        self.path.write_text(json.dumps(self.cache, indent=0, sort_keys=True))


def run_backfill(out_root: Path, hist_root: Path, season: str, *, date_from: str | None = None,
                 date_to: str | None = None, sleep_s: float = 0.05, max_minutes: float = 20.0) -> dict[str, Any]:
    """Locate, fetch and parse; resumable. Stops starting new work after ``max_minutes`` (Actions jobs
    are kept under 30 minutes) -- a re-run continues where this one stopped."""
    deadline = time.time() + 60 * max_minutes
    p = paths(out_root, season)
    p["dir"].mkdir(parents=True, exist_ok=True)
    tg = pd.read_parquet(Path(hist_root) / "espn" / f"team_games_{season}.parquet")
    pg = pd.read_parquet(Path(hist_root) / "espn" / f"player_games_{season}.parquet")
    tg = tg[tg["season_type"].isin(SEASON_TYPES)]
    if date_from:
        tg = tg[tg["game_date_et"] >= date_from]
    if date_to:
        tg = tg[tg["game_date_et"] <= date_to]
    games = tg[tg["home"].astype(bool)][["game_id", "game_date_et", "start_time_utc", "team_id", "opp_team_id", "season_type"]]
    index = PlayerIndex.from_player_games(pg)
    lookup = game_lookup(pd.read_parquet(Path(hist_root) / "espn" / f"team_games_{season}.parquet"))

    old_reports = pd.read_parquet(p["reports"]) if p["reports"].exists() else pd.DataFrame()
    old_rows = pd.read_parquet(p["rows"]) if p["rows"].exists() else pd.DataFrame()
    if len(old_reports) and "parser_version" in old_reports:
        stale = set(old_reports.loc[old_reports["parser_version"] != PARSER_VERSION, "slot_et"])
        old_reports = old_reports[~old_reports["slot_et"].isin(stale)]
        if len(old_rows):
            old_rows = old_rows[~old_rows["slot_et"].isin(stale)]
    have = set(old_reports["slot_et"]) if len(old_reports) else set()
    timed_out = False
    new_reports: list[dict[str, Any]] = []
    new_rows: list[dict[str, Any]] = []
    snaps: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    with httpx.Client(timeout=40.0, follow_redirects=True) as c:
        prober = SlotProber(c, p["probe"], sleep_s)
        wanted: dict[str, datetime] = {}
        for g in games.sort_values("start_time_utc").itertuples(index=False):
            if time.time() > deadline:
                timed_out = True
                break
            tip = parse_iso(str(g.start_time_utc))
            tip_et = tip.astimezone(ET)
            last = prober.latest_before(tip_et, strict=True)
            t60 = prober.latest_before(tip_et - T60, strict=False)
            snaps.append({"game_id": g.game_id, "game_date_et": g.game_date_et, "season_type": g.season_type,
                          "tip_utc": iso(tip), "home_team_id": int(g.team_id), "away_team_id": int(g.opp_team_id),
                          "last_pre_tip_slot_et": last.strftime("%Y-%m-%dT%H:%M") if last else None,
                          "t_minus_60_slot_et": t60.strftime("%Y-%m-%dT%H:%M") if t60 else None})
            for s in (last, t60):
                if s is not None:
                    wanted[s.strftime("%Y-%m-%dT%H:%M")] = s
        prober.save()
        log.info(kv(event="pit_slots_located", games=len(snaps), reports=len(wanted), head_requests=prober.n_head))

        for key, slot in sorted(wanted.items()):
            if key in have:
                continue
            if time.time() > deadline:
                timed_out = True
                break
            url = prober.status(slot).get("url")
            try:
                r = c.get(url, headers=PLAIN_HEADERS_OK)
                fetched = utcnow()
                if r.status_code != 200:
                    raise ValueError(f"HTTP {r.status_code}")
                rows, meta = parse_report_pdf(r.content, slot)
            except Exception as e:  # noqa: BLE001 - one report must not end the backfill
                errors.append({"slot_et": key, "url": url, "error": f"{type(e).__name__}: {e}"[:200]})
                continue
            lm = _http_dt(r.headers.get("last-modified"))
            new_reports.append({
                "slot_et": key, "report_time_utc": iso(slot.astimezone(ET)), "url": url, "fetched_at_utc": iso(fetched),
                "last_modified_utc": iso(lm) if lm else None, "sha256": hashlib.sha256(r.content).hexdigest(),
                "bytes": len(r.content), "parser_version": PARSER_VERSION,
                **{k: v for k, v in meta.items() if not isinstance(v, list)},
                "unresolved_team_text": "|".join(meta.get("unresolved_team_text") or [])})
            for row in rows:
                home = tricode_to_team_id(row.get("home_tricode") or "")
                gm = lookup.get((row.get("game_date") or "", home)) if home else None
                gid = gm["game_id"] if gm else None
                pid, method = (None, "team_level") if row.get("player_name_raw") is None else index.resolve(
                    row.get("team_id"), row["player_name_raw"], gid)
                new_rows.append({**row, "slot_et": key, "report_time_utc": iso(slot.astimezone(ET)),
                                 "game_id": gid, "nba_id": pid, "match_method": method})
            if sleep_s:
                time.sleep(sleep_s)

    reports = pd.concat([old_reports, pd.DataFrame(new_reports)], ignore_index=True) if new_reports else old_reports
    rows_df = pd.concat([old_rows, pd.DataFrame(new_rows)], ignore_index=True) if new_rows else old_rows
    if len(reports):
        reports = reports.drop_duplicates("slot_et", keep="last").sort_values("slot_et").reset_index(drop=True)
        reports.to_parquet(p["reports"], index=False, compression="zstd")
    if len(rows_df):
        rows_df = rows_df.sort_values(["slot_et"], kind="stable").reset_index(drop=True)
        rows_df.to_parquet(p["rows"], index=False, compression="zstd")
    snap_df = verify_snapshots(pd.DataFrame(snaps), reports, rows_df)
    if len(snap_df):
        snap_df.to_parquet(p["games"], index=False, compression="zstd")
    man = {"season": season, "built_at": iso(utcnow()), "games": int(len(snap_df)), "reports": int(len(reports)),
           "rows": int(len(rows_df)), "new_reports_this_run": len(new_reports), "complete": not timed_out,
           "games_located_this_run": len(snaps), "head_requests_this_run": prober.n_head, "errors": errors[:200],
           "n_errors": len(errors), "source": "ak-static.cms.nba.com/referee/injury (official NBA injury report PDFs)"}
    p["manifest"].write_text(json.dumps(man, indent=1))
    return man


def verify_snapshots(snaps: pd.DataFrame, reports: pd.DataFrame, rows: pd.DataFrame) -> pd.DataFrame:
    """Attach report times and point-in-time flags to each game snapshot."""
    if not len(snaps):
        return snaps
    rep = reports.set_index("slot_et") if len(reports) else pd.DataFrame()
    have_rows = rows.groupby(["slot_et", "game_id"]).size().to_dict() if len(rows) else {}
    teams_rows = (rows.dropna(subset=["game_id"]).groupby(["slot_et", "game_id"])["team_id"].nunique().to_dict()
                  if len(rows) else {})
    out = []
    for s in snaps.to_dict("records"):
        tip = parse_iso(s["tip_utc"])
        for tag in ("last_pre_tip", "t_minus_60"):
            key = s[f"{tag}_slot_et"]
            r = rep.loc[key] if key is not None and len(rep) and key in rep.index else None
            nominal = parse_iso(r["report_time_utc"]) if r is not None else None
            lm = parse_iso(r["last_modified_utc"]) if r is not None and r["last_modified_utc"] else None
            s[f"{tag}_report_time_utc"] = iso(nominal) if nominal else None
            s[f"{tag}_published_utc"] = iso(lm) if lm else None
            s[f"{tag}_lead_minutes"] = round((tip - nominal).total_seconds() / 60, 1) if nominal else None
            s[f"{tag}_nominal_before_tip"] = bool(nominal is not None and nominal < tip)
            s[f"{tag}_published_before_tip"] = bool(lm is not None and lm < tip)
            s[f"{tag}_rows_for_game"] = int(have_rows.get((key, s["game_id"]), 0)) if key else 0
            s[f"{tag}_teams_listed"] = int(teams_rows.get((key, s["game_id"]), 0)) if key else 0
            s[f"{tag}_pit_ok"] = bool(s[f"{tag}_nominal_before_tip"] and s[f"{tag}_published_before_tip"]
                                      and s[f"{tag}_rows_for_game"] > 0)
        out.append(s)
    return pd.DataFrame(out)
