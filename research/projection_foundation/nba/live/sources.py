"""Network layer for the live NBA pipeline.

Everything that touches the network goes through a `Sources` object so tests (and the offline smoke run) can
inject REAL recorded payloads instead. The default implementation reuses the repo's own, already-validated
adapters (src/nba_edge): ESPN scoreboard / rosters / injuries and the official NBA injury-report PDF parser.
The dev sandbox cannot reach any of these hosts; GitHub Actions runners can (docs/NBA_DATA_SOURCE_AUDIT.md).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from .. import data

ROOT = data.ROOT
if str(ROOT / "src") not in sys.path:          # the research package imports the production adapters read-only
    sys.path.insert(0, str(ROOT / "src"))

ESPN_SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={event_id}"
ESPN_INJURIES_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"


def iso(d: datetime) -> str:
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_ts(x: str) -> datetime:
    d = datetime.fromisoformat(str(x).replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


@dataclass
class Sources:
    """Live sources. Each method returns plain python (no pydantic) and records its own provenance."""
    errors: list[str] = field(default_factory=list)

    # -- schedule ---------------------------------------------------------------------------------------------
    def scoreboard(self, now: datetime, days_ahead: int = 2) -> list[dict[str, Any]]:
        """ESPN scoreboard rows for the ET dates today..today+days_ahead (yesterday too: late games span midnight UTC)."""
        from zoneinfo import ZoneInfo
        from nba_edge.data.http import FetchError
        from nba_edge.data.schedule import fetch_espn_scoreboard
        et0 = now.astimezone(ZoneInfo("America/New_York")).date()
        rows: dict[str, dict] = {}
        for k in range(-1, days_ahead + 1):
            day = datetime(et0.year, et0.month, et0.day, 12, tzinfo=ZoneInfo("America/New_York")) + timedelta(days=k)
            try:
                games, prov = fetch_espn_scoreboard(day, ttl_s=None)
            except FetchError as e:
                self.errors.append(f"scoreboard {day.date()}: {e}"[:200])
                continue
            for g in games:
                d = g.model_dump(mode="json")
                d["_fetched_at_utc"] = prov["fetched_at_utc"]
                rows[d["game_id"]] = d
        return list(rows.values())

    def rosters(self) -> list[dict[str, Any]]:
        from nba_edge.data.context import fetch_espn_rosters
        rows, prov = fetch_espn_rosters()
        if prov.get("errors"):
            self.errors += [f"roster {e}" for e in prov["errors"]]
        fetched = iso(datetime.now(timezone.utc))
        for r in rows:
            r["_fetched_at_utc"] = fetched
        return rows

    # -- availability -----------------------------------------------------------------------------------------
    def espn_injuries(self, now: datetime) -> list[dict[str, Any]]:
        """ESPN /injuries rows with the athlete id (research capture parser)."""
        import httpx
        from nba_edge.availability.capture import espn_rows
        from nba_edge.data.http import PLAIN_HEADERS_OK
        with httpx.Client(timeout=40.0, follow_redirects=True) as c:
            r = c.get(ESPN_INJURIES_URL, headers=PLAIN_HEADERS_OK)
            r.raise_for_status()
            fetched = iso(datetime.now(timezone.utc))
            rows = espn_rows(r.json(), fetched)
        return rows

    def official_report(self, now: datetime) -> dict[str, Any] | None:
        """Latest published official injury report (PDF) within the last 6 h, parsed positionally.

        Returns {rows, meta, url, report_time_utc, last_modified_utc, fetched_at_utc, pdf_sha256} or None."""
        import httpx
        from nba_edge.availability.capture import fetch_report, latest_slot
        with httpx.Client(timeout=40.0, follow_redirects=True) as c:
            slot, info = latest_slot(c, now)
            if slot is None:
                self.errors.append(f"official report: no slot found ({info})")
                return None
            rows, meta = fetch_report(c, slot, info.get("url"))
        meta = dict(meta)
        meta["slots_tried"] = info.get("slots_tried")
        return {"rows": rows, "meta": meta, "url": meta["url"], "report_time_utc": meta["report_time_utc"],
                "last_modified_utc": meta.get("last_modified_utc"), "fetched_at_utc": meta["fetched_at_utc"],
                "pdf_sha256": meta["pdf_sha256"]}

    def summary(self, event_id: str) -> dict[str, Any]:
        """Raw ESPN game summary (starters pre-tip, final box score post-game)."""
        import httpx
        from nba_edge.data.http import PLAIN_HEADERS_OK
        eid = str(event_id).split(":")[-1]
        with httpx.Client(timeout=40.0, follow_redirects=True) as c:
            r = c.get(ESPN_SUMMARY_URL.format(event_id=eid), headers=PLAIN_HEADERS_OK)
            r.raise_for_status()
            return {"payload": r.json(), "fetched_at_utc": iso(datetime.now(timezone.utc)),
                    "url": ESPN_SUMMARY_URL.format(event_id=eid)}


class RecordedSources(Sources):
    """Replays recorded payloads. Every argument is optional; a missing source behaves like a failed fetch."""

    def __init__(self, scoreboard: list[dict] | None = None, rosters: list[dict] | None = None,
                 espn_injuries: list[dict] | None = None, official: dict | None = None,
                 summaries: dict[str, dict] | None = None, fail: set[str] | None = None,
                 final_boxes: dict[str, list[dict]] | None = None):
        super().__init__()
        if final_boxes is not None:
            self._boxes = final_boxes
        self._sb, self._ro, self._ei, self._off = scoreboard, rosters, espn_injuries, official
        self._sum, self._fail = summaries or {}, fail or set()

    def scoreboard(self, now, days_ahead=2):
        if "scoreboard" in self._fail or self._sb is None:
            raise RuntimeError("scoreboard unavailable")
        return list(self._sb)

    def rosters(self):
        if "rosters" in self._fail or self._ro is None:
            raise RuntimeError("rosters unavailable")
        return list(self._ro)

    def espn_injuries(self, now):
        if "espn_injuries" in self._fail or self._ei is None:
            raise RuntimeError("espn injuries unavailable")
        return list(self._ei)

    def official_report(self, now):
        if "official" in self._fail:
            raise RuntimeError("official report unavailable")
        return self._off

    def summary(self, event_id):
        if str(event_id) not in self._sum:
            raise RuntimeError(f"no recorded summary for {event_id}")
        return self._sum[str(event_id)]

    def final_box_override(self, game_id):
        """Recorded FINAL player box rows (shadow-store `outcomes/box`, ESPN summary rows) for results-stage replays."""
        import pandas as pd
        rows = self._boxes.get(str(game_id)) if hasattr(self, "_boxes") else None
        if rows is None:
            return False, None, None
        return True, pd.DataFrame(rows), "recorded"
