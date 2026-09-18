"""Injury sources -> ``InjuryEntry`` rows.

Primary: the official NBA injury report PDF, published at fixed times (URL pattern
``https://ak-static.cms.nba.com/referee/injury/Injury-Report_YYYY-MM-DD_HH_MMAM.pdf``; older files use
``_HHAM``). Text is extracted with pypdf and parsed with a tolerant state machine. The report lists, per game,
each team's players with Current Status in {Out, Doubtful, Questionable, Probable, Available} and a reason.

Fallback: ESPN injuries JSON (``/injuries``), which is team-level and less precise about game-specific status.
"""

from __future__ import annotations

import io
import re
from datetime import UTC, datetime, timedelta
from typing import Any

from nba_edge.data.http import PLAIN_HEADERS_OK, FetchError, fetch
from nba_edge.identity.teams import TeamIdentityError, registry
from nba_edge.log import get_logger, kv
from nba_edge.schemas.core import InjuryEntry, InjuryStatus
from nba_edge.timeutil import ET

log = get_logger(__name__)

PDF_URL_NEW = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_{date}_{hh}_{mm}{ampm}.pdf"
PDF_URL_OLD = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_{date}_{hh}{ampm}.pdf"
ESPN_INJURIES_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"

STATUS_MAP = {"out": InjuryStatus.OUT, "doubtful": InjuryStatus.DOUBTFUL, "questionable": InjuryStatus.QUESTIONABLE, "probable": InjuryStatus.PROBABLE, "available": InjuryStatus.AVAILABLE}
_STATUS_RE = re.compile(r"\b(Out|Doubtful|Questionable|Probable|Available)\b")
_MATCHUP_RE = re.compile(r"\b([A-Z]{3})@([A-Z]{3})\b")
_DATE_RE = re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\b")
_TIME_RE = re.compile(r"\b(\d{1,2}:\d{2})\s*\(ET\)")
_TEAM_NAMES: dict[str, int] = {}


def _team_name_index() -> dict[str, int]:
    if not _TEAM_NAMES:
        for t in registry().teams:
            _TEAM_NAMES[t.name.lower()] = t.team_id
    return _TEAM_NAMES


def candidate_pdf_urls(report_time_et: datetime) -> list[str]:
    d = report_time_et.strftime("%Y-%m-%d")
    hh = report_time_et.strftime("%I")
    mm = report_time_et.strftime("%M")
    ampm = report_time_et.strftime("%p")
    urls = [PDF_URL_NEW.format(date=d, hh=hh, mm=mm, ampm=ampm)]
    if mm == "00":
        urls.append(PDF_URL_OLD.format(date=d, hh=hh, ampm=ampm))
    return urls


def parse_injury_report_text(text: str, report_time_utc: datetime, source: str = "nba_official_pdf") -> list[InjuryEntry]:
    """Tolerant parser for the extracted PDF text. Lines may be wrapped/merged; we scan tokens sequentially,
    tracking (game date, matchup, team) context and emitting an entry whenever we see 'Surname, First  Status  Reason'."""
    entries: list[InjuryEntry] = []
    names = _team_name_index()
    reg = registry()
    game_date: str | None = None
    home: str | None = None
    team_id: int | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("Injury Report:", "Page ", "Game Date", "NOT YET SUBMITTED")):
            if "NOT YET SUBMITTED" in line and team_id is not None:
                pass
            continue
        m = _DATE_RE.search(line)
        if m:
            game_date = f"{m[3]}-{m[1]}-{m[2]}"
        mm = _MATCHUP_RE.search(line)
        if mm:
            home = mm[2]
        low = line.lower()
        for nm, tid in names.items():
            if nm in low:
                team_id = tid
                break
        sm = _STATUS_RE.search(line)
        if sm and team_id is not None and "," in line[: sm.start()]:
            name_part = line[: sm.start()].strip()
            # strip leading context tokens (dates, times, matchup, team name) from the player name
            name_part = _DATE_RE.sub("", name_part)
            name_part = _TIME_RE.sub("", name_part)
            name_part = _MATCHUP_RE.sub("", name_part)
            for nm in names:
                name_part = re.sub(re.escape(nm), "", name_part, flags=re.I)
            name_part = re.sub(r"\s+", " ", name_part).strip(" -")
            if "," not in name_part:
                continue
            last, first = [x.strip() for x in name_part.split(",", 1)]
            player = f"{first} {last}".strip()
            reason = line[sm.end():].strip() or None
            gid = None
            entries.append(
                InjuryEntry(
                    game_id=gid, game_date_et=game_date or report_time_utc.astimezone(ET).date().isoformat(), team_id=team_id, nba_id=None,
                    player_name_raw=player, status=STATUS_MAP[sm[1].lower()], reason=reason, report_time_utc=report_time_utc, source=source,
                )
            )
    try:
        reg.by_tricode(home or "BOS")
    except TeamIdentityError:
        pass
    return entries


def extract_pdf_text(pdf_bytes: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def fetch_official_injury_report(report_time_et: datetime) -> tuple[list[InjuryEntry], dict[str, Any]]:
    """Fetch the report published at ``report_time_et`` (an ET-aware datetime on a 15-minute grid). Returns
    (entries, provenance). Missing report (404) -> empty list with provenance['missing']=True."""
    last_err: str | None = None
    for url in candidate_pdf_urls(report_time_et):
        try:
            f = fetch(url, headers=PLAIN_HEADERS_OK, ttl_s=None)
        except FetchError as e:
            last_err = str(e)[:200]
            continue
        text = extract_pdf_text(f.content)
        entries = parse_injury_report_text(text, report_time_et.astimezone(UTC))
        return entries, {"source": "nba_official_pdf", "url": url, "fetched_at_utc": f.fetched_at_utc, "n": len(entries), "bytes": len(f.content)}
    return [], {"source": "nba_official_pdf", "missing": True, "error": last_err, "report_time_et": report_time_et.isoformat()}


def latest_report_slots(now_utc: datetime, lookback_hours: int = 6) -> list[datetime]:
    """Official reports are published on the hour/half/quarter; try the most recent 15-minute slots first."""
    now_et = now_utc.astimezone(ET).replace(second=0, microsecond=0)
    now_et = now_et - timedelta(minutes=now_et.minute % 15)
    slots = []
    for k in range(lookback_hours * 4):
        slots.append(now_et - timedelta(minutes=15 * k))
    return slots


def fetch_latest_official_injury_report(now_utc: datetime) -> tuple[list[InjuryEntry], dict[str, Any]]:
    tried = 0
    for slot in latest_report_slots(now_utc):
        entries, prov = fetch_official_injury_report(slot)
        tried += 1
        if not prov.get("missing"):
            prov["slots_tried"] = tried
            return entries, prov
        if tried >= 8:
            break
    return [], {"source": "nba_official_pdf", "missing": True, "slots_tried": tried}


def parse_espn_injuries(payload: dict[str, Any], report_time_utc: datetime) -> list[InjuryEntry]:
    reg = registry()
    out = []
    for team in payload.get("injuries", []):
        try:
            tid = reg.by_name(team.get("displayName", "")).team_id
        except TeamIdentityError:
            continue
        for inj in team.get("injuries", []):
            st = (inj.get("status") or "").lower()
            status = STATUS_MAP.get(st, InjuryStatus.UNKNOWN)
            if st in ("day-to-day",):
                status = InjuryStatus.QUESTIONABLE
            details = inj.get("details") or {}
            out.append(
                InjuryEntry(
                    game_id=None, game_date_et=report_time_utc.astimezone(ET).date().isoformat(), team_id=tid, nba_id=None,
                    player_name_raw=(inj.get("athlete") or {}).get("displayName", ""), status=status,
                    reason=(details.get("type") or inj.get("shortComment") or None), report_time_utc=report_time_utc, source="espn_injuries",
                )
            )
    return out


def fetch_espn_injuries(now_utc: datetime) -> tuple[list[InjuryEntry], dict[str, Any]]:
    f = fetch(ESPN_INJURIES_URL, headers=PLAIN_HEADERS_OK, ttl_s=None)
    entries = parse_espn_injuries(f.json(), now_utc)
    log.info(kv(event="espn_injuries", n=len(entries)))
    return entries, {"source": "espn_injuries", "url": ESPN_INJURIES_URL, "fetched_at_utc": f.fetched_at_utc, "n": len(entries)}
