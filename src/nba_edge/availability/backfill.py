"""Bounded historical backfill of official NBA injury reports, with point-in-time verification.

For every game of the season (schedule = the committed ESPN team-games dataset, which carries the
scheduled tip), two reports are located:

* ``last_pre_tip``  -- the latest report UPLOADED (HTTP Last-Modified) strictly before the tip;
* ``t_minus_60``    -- the latest report uploaded strictly before tip - 60 min (a decision-time
  snapshot that leaves room for a T-60m projection run).

Files are found by HEAD-probing the archive (``ak-static.cms.nba.com``: 200 = exists, 403 = no such
file) backwards over filename slots. The filename is only a locator: the report time is the one printed
in the PDF header (hourly-era files named ``_06PM`` are the 6:30 or 6:45 report). Each distinct report is
downloaded once, parsed, and stored with ``fetched_at_utc``, ``last_modified_utc`` and a sha256. A game's
snapshot is ``pit_ok`` only if the header report time AND the upload instant both precede the tip AND the
snapshot's own cutoff (tip, or tip - 60 min for ``t_minus_60``), and the report lists the game. Nothing uploaded at or after the tip is attached to a game; no post-game source is
an input (the box score is read only by the coverage script, to validate the parser).

Outputs (``out_root/injury_reports/``): ``reports_<season>.parquet``, ``report_rows_<season>.parquet``,
``game_snapshots_<season>.parquet``, ``probe_cache_<season>.json`` (HEAD results, makes re-runs cheap),
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
EXTENDED_LOOKBACK_SLOTS = 8  # the rare-spelling fallback only looks 2 hours back
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
    """HEAD-probe report slots with a persistent cache of FOUND files only.

    A 403 is not cached: the CDN answers 403 both for "no such file" and, transiently, for files that
    exist (the first 2025-26 run cached 403s for Dec 25-31 reports that a later run found), so a miss is
    re-checked on every run."""

    def __init__(self, client: httpx.Client, cache_path: Path, sleep_s: float = 0.05) -> None:
        self.c = client
        self.path = cache_path
        self.sleep_s = sleep_s
        raw = json.loads(cache_path.read_text()) if cache_path.exists() else {}
        self.cache: dict[str, dict[str, Any]] = {k: v for k, v in raw.items() if v.get("code") == 200}
        self.n_head = 0

    def status(self, slot_et: datetime, extended: bool = False) -> dict[str, Any]:
        key = slot_et.strftime("%Y-%m-%dT%H:%M") + ("+x" if extended else "")
        if key in self.cache:
            return self.cache[key]
        st: dict[str, Any] = {"code": None}
        urls = report_urls(slot_et, extended=extended)
        for url in (urls[2:] if extended else urls):  # extended pass: only the variants not tried before
            try:
                r = self.c.head(url, headers=PLAIN_HEADERS_OK)
                self.n_head += 1
                st = {"code": r.status_code, "last_modified": r.headers.get("last-modified"), "url": url}
            except httpx.HTTPError as e:
                st = {"code": f"error:{type(e).__name__}", "url": url}
            if st["code"] == 200:
                break
        if st["code"] == 200:
            self.cache[key] = st
        if self.sleep_s:
            time.sleep(self.sleep_s)
        return st

    def latest_published_before(self, limit_utc: datetime, extended: bool = False) -> tuple[datetime, dict] | None:
        """The latest report file whose upload instant (Last-Modified) is strictly before ``limit_utc``.

        Scans filename slots backwards from the limit. Upload time, not the filename, decides: hourly-era
        files are named an hour-slot but uploaded at HH:30/HH:45 (see report_urls)."""
        s = slot_floor(limit_utc.astimezone(ET))
        for _ in range(EXTENDED_LOOKBACK_SLOTS if extended else MAX_LOOKBACK_SLOTS):
            st = self.status(s, extended=extended)
            if st.get("code") == 200:
                lm = _http_dt(st.get("last_modified"))
                if lm is not None and lm < limit_utc:
                    return s, st
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
        wanted: dict[str, tuple[datetime, str]] = {}
        for g in games.sort_values("start_time_utc").itertuples(index=False):
            if time.time() > deadline:
                timed_out = True
                break
            tip = parse_iso(str(g.start_time_utc))
            found = {}
            for tag, limit in (("last_pre_tip", tip), ("t_minus_60", tip - T60)):
                hit = prober.latest_published_before(limit)
                if hit is None:
                    hit = prober.latest_published_before(limit, extended=True)
                found[tag] = hit
            snap = {"game_id": g.game_id, "game_date_et": g.game_date_et, "season_type": g.season_type,
                    "tip_utc": iso(tip), "home_team_id": int(g.team_id), "away_team_id": int(g.opp_team_id)}
            for tag, hit in found.items():
                snap[f"{tag}_slot_et"] = hit[0].strftime("%Y-%m-%dT%H:%M") if hit else None
                if hit:
                    wanted[hit[0].strftime("%Y-%m-%dT%H:%M")] = (hit[0], hit[1]["url"])
            snaps.append(snap)
        prober.save()
        log.info(kv(event="pit_slots_located", games=len(snaps), reports=len(wanted), head_requests=prober.n_head))

        for key, (slot, url) in sorted(wanted.items()):
            if key in have:
                continue
            if time.time() > deadline:
                timed_out = True
                break
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
            # the report time is the one printed in the PDF header; the filename slot is only a locator
            rt = datetime.fromisoformat(meta["report_time_et"]) if meta.get("report_time_et") else None
            report_time = iso(rt) if rt else None
            new_reports.append({
                "slot_et": key, "report_time_utc": report_time, "report_time_source": "pdf_header" if rt else "missing",
                "url": url, "fetched_at_utc": iso(fetched),
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
                new_rows.append({**row, "slot_et": key, "report_time_utc": report_time,
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
    snap_df = verify_snapshots(fallback_to_fetched(pd.DataFrame(snaps), reports), reports, rows_df)
    if len(snap_df):
        snap_df.to_parquet(p["games"], index=False, compression="zstd")
    man = {"season": season, "built_at": iso(utcnow()), "games": int(len(snap_df)), "reports": int(len(reports)),
           "rows": int(len(rows_df)), "new_reports_this_run": len(new_reports), "complete": not timed_out,
           "games_located_this_run": len(snaps), "head_requests_this_run": prober.n_head, "errors": errors[:200],
           "n_errors": len(errors), "source": "ak-static.cms.nba.com/referee/injury (official NBA injury report PDFs)"}
    p["manifest"].write_text(json.dumps(man, indent=1))
    return man


def fallback_to_fetched(snaps: pd.DataFrame, reports: pd.DataFrame) -> pd.DataFrame:
    """A located report that could not be downloaded (the CDN answers 403 transiently, and throttles
    long runs) must not cost the game its snapshot: fall back to the latest report that WAS fetched,
    is from the game's ET date and whose upload instant precedes the snapshot's cutoff. Marked in
    ``<tag>_fallback_fetched``; still verified by :func:`verify_snapshots` like any other snapshot."""
    if not len(snaps):
        return snaps
    have = set(reports["slot_et"]) if len(reports) else set()
    if len(reports):
        lm = pd.to_datetime(reports["last_modified_utc"], utc=True, errors="coerce")
        rep = reports.assign(_lm=lm, _date=reports["slot_et"].str[:10]).sort_values("slot_et")
    out = snaps.copy()
    for tag, off in (("last_pre_tip", timedelta(0)), ("t_minus_60", T60)):
        col = f"{tag}_slot_et"
        flags = []
        for i, s in out.iterrows():
            key = s[col]
            if key is None or (isinstance(key, float) and key != key) or key in have or not len(reports):
                flags.append(False)
                continue
            cutoff = pd.Timestamp(parse_iso(s["tip_utc"]) - off)
            c = rep[(rep["_date"] == str(s["game_date_et"])) & (rep["_lm"] < cutoff)]
            if len(c):
                out.at[i, col] = c["slot_et"].iloc[-1]
                flags.append(True)
            else:
                out.at[i, col] = None
                flags.append(False)
        out[f"{tag}_fallback_fetched"] = flags
    return out


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
        for tag, cutoff in (("last_pre_tip", tip), ("t_minus_60", tip - T60)):
            key = s[f"{tag}_slot_et"]
            r = rep.loc[key] if key is not None and len(rep) and key in rep.index else None
            nominal = parse_iso(r["report_time_utc"]) if r is not None and r["report_time_utc"] else None
            lm = parse_iso(r["last_modified_utc"]) if r is not None and r["last_modified_utc"] else None
            s[f"{tag}_report_time_utc"] = iso(nominal) if nominal else None
            s[f"{tag}_published_utc"] = iso(lm) if lm else None
            s[f"{tag}_lead_minutes"] = round((tip - nominal).total_seconds() / 60, 1) if nominal else None
            s[f"{tag}_nominal_before_tip"] = bool(nominal is not None and nominal < tip)
            s[f"{tag}_published_before_tip"] = bool(lm is not None and lm < tip)
            # the snapshot's own decision cutoff (tip for last_pre_tip, tip - 60 min for t_minus_60): the
            # locator already selects by upload < cutoff; this re-asserts it on the stored report times
            s[f"{tag}_cutoff_utc"] = iso(cutoff)
            s[f"{tag}_before_cutoff"] = bool(nominal is not None and lm is not None and nominal < cutoff
                                             and lm < cutoff)
            s[f"{tag}_rows_for_game"] = int(have_rows.get((key, s["game_id"]), 0)) if key else 0
            s[f"{tag}_teams_listed"] = int(teams_rows.get((key, s["game_id"]), 0)) if key else 0
            s[f"{tag}_pit_ok"] = bool(s[f"{tag}_nominal_before_tip"] and s[f"{tag}_published_before_tip"]
                                      and s[f"{tag}_before_cutoff"] and s[f"{tag}_rows_for_game"] > 0)
        out.append(s)
    return pd.DataFrame(out)
