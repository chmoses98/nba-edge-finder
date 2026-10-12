"""Injury sources -> ``InjuryEntry`` rows.

Primary: the official NBA injury report PDF, published at fixed times (URL pattern
``https://ak-static.cms.nba.com/referee/injury/Injury-Report_YYYY-MM-DD_HH_MMAM.pdf``; older files use
``_HHAM``). The report lists, per game, each team's players with Current Status in {Out, Doubtful,
Questionable, Probable, Available} and a reason.

The PDF is parsed POSITIONALLY (:func:`parse_injury_report_pdf`). ``pypdf``'s plain ``extract_text`` emits one
token per line for these files ('Injury', 'Report:', ..., 'Memphis', 'Grizzlies', 'Morant,', 'Ja', 'Out', ...),
so a line-based parser sees no row structure at all and returns zero rows on every real report. Instead every
text fragment keeps its (x, y) page position, columns are located from the header row, fragments are grouped
into visual lines, and a line is a player row when its Current Status cell holds a status word. Game date,
matchup and team are printed only on the first row of their group, so they carry forward. A reason that wraps
is printed vertically centred on its row, so wrapped reason fragments attach to the nearest player row.

A report that visibly contains player rows but parses to none raises :class:`InjuryReportParseError` rather
than returning an empty list: an empty official report is indistinguishable from "nobody is injured" downstream.

Fallback: ESPN injuries JSON (``/injuries``), which is team-level and less precise about game-specific status.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
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


class InjuryReportParseError(ValueError):
    """A non-empty official injury report parsed to zero player rows (or lost its column layout). Raised instead
    of returning ``[]`` so a format change or extraction regression cannot masquerade as an empty report."""


def _team_name_index() -> dict[str, int]:
    if not _TEAM_NAMES:
        for t in registry().teams:
            _TEAM_NAMES[t.name.lower()] = t.team_id
    return _TEAM_NAMES


# Publication cadence, measured on the 2025-26 archive (2,430 located files) and the 2026-27 preseason capture:
# through 2025-12-21 reports were hourly and named ``_HHPM`` (the file named 06PM is the 6:30/6:45 PM report);
# from 2025-12-22 a report can appear in any 15-minute slot, named ``_HH_MMPM`` and uploaded ~5 s after the
# slot. No ``_HH_MM`` file exists before that date and no ``_HH`` file after it, so the hourly spelling is only
# tried for older dates.
HOURLY_NAMING_UNTIL = "2025-12-21"
SEARCH_MAX_HOURS = 24  # never look further back than this
SEARCH_MIN_SLOTS = 8  # ...but always at least the previous 2 hours, even just after midnight ET
SEARCH_MAX_REQUESTS = 100  # hard bound on HTTP requests per search (a full ET day is at most 96 slots)


def candidate_pdf_urls(report_time_et: datetime) -> list[str]:
    d = report_time_et.strftime("%Y-%m-%d")
    hh = report_time_et.strftime("%I")
    mm = report_time_et.strftime("%M")
    ampm = report_time_et.strftime("%p")
    urls = [PDF_URL_NEW.format(date=d, hh=hh, mm=mm, ampm=ampm)]
    if mm == "00" and d <= HOURLY_NAMING_UNTIL:
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
    if not entries:
        n_status = len(_STATUS_RE.findall(text))
        if n_status:
            raise InjuryReportParseError(
                f"injury report text holds {n_status} status tokens but parsed to 0 rows "
                "(if this is extracted PDF text, use parse_injury_report_pdf: pypdf emits one token per line)")
    return entries


def extract_pdf_text(pdf_bytes: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


# ---- positional parser for the official PDF -------------------------------------------------------------
_COLUMNS = ("game_date", "game_time", "matchup", "team", "player", "status", "reason")
_PDF_STATUS = {"Out": InjuryStatus.OUT, "Doubtful": InjuryStatus.DOUBTFUL, "Questionable": InjuryStatus.QUESTIONABLE,
               "Probable": InjuryStatus.PROBABLE, "Available": InjuryStatus.AVAILABLE}
_CELL_MATCHUP_RE = re.compile(r"^([A-Z]{2,3})@([A-Z]{2,3})$")
_CELL_DATE_RE = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")
_HEADER_TIME_RE = re.compile(r"Injury Report:\s*(\d{2})/(\d{2})/(\d{2})\s+(\d{1,2}):(\d{2})\s*([AP]M)")
_LINE_TOL = 2.0


@dataclass
class _Word:
    page: int
    x: float
    top: float  # distance from the top of the page (larger = lower)
    text: str


def _extract_words(pdf_bytes: bytes) -> list[_Word]:
    """Every text fragment with its page position, via pypdf's text visitor."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(pdf_bytes))
    words: list[_Word] = []
    for pi, page in enumerate(reader.pages):
        height = float(page.mediabox.height)

        def visit(text, cm, tm, font_dict, font_size, pi=pi, height=height):
            t = (text or "").strip()
            if not t:
                return
            x = tm[4] * cm[0] + tm[5] * cm[2] + cm[4]
            y = tm[4] * cm[1] + tm[5] * cm[3] + cm[5]
            words.append(_Word(pi, round(float(x), 2), round(height - float(y), 2), t))

        start = len(words)
        page.extract_text(visitor_text=visit)
        _orient(words, start)
    return words


def _orient(words: list[_Word], start: int) -> None:
    """Make ``top`` grow downward. Some of these PDFs use a flipped text matrix; the page title 'Injury Report:'
    must be the topmost line."""
    page_words = words[start:]
    title = [w.top for w in page_words if w.text.startswith("Injury")]
    if not page_words or not title:
        return
    tops = sorted(w.top for w in page_words)
    if min(title) > tops[len(tops) // 2]:
        mx = tops[-1]
        for w in page_words:
            w.top = round(mx - w.top, 2)


def _lines(words: list[_Word]) -> list[list[_Word]]:
    out: list[list[_Word]] = []
    for w in sorted(words, key=lambda w: (w.top, w.x)):
        if out and abs(out[-1][0].top - w.top) <= _LINE_TOL:
            out[-1].append(w)
        else:
            out.append([w])
    return [sorted(line, key=lambda w: w.x) for line in out]


def _header_columns(lines: list[list[_Word]]) -> tuple[dict[str, float], float] | None:
    """Column left edges from the header row ('Game Date  Game Time  Matchup  Team  Player Name ...')."""
    for line in lines:
        txt = " ".join(w.text for w in line)
        if "Matchup" in txt and "Player" in txt and ("Status" in txt or "Current" in txt):
            xs: dict[str, float] = {}
            games = [w for w in line if w.text.startswith("Game")]
            if games:
                xs["game_date"] = games[0].x
            if len(games) > 1:
                xs["game_time"] = games[1].x
            for w in line:
                for key, label in (("matchup", "Matchup"), ("team", "Team"), ("player", "Player"),
                                   ("status", "Current"), ("reason", "Reason")):
                    if w.text.startswith(label) and key not in xs:
                        xs[key] = w.x
            if {"matchup", "team", "player", "status", "reason"} <= set(xs):
                return xs, line[0].top
    return None


def _column(x: float, cols: dict[str, float]) -> str:
    best = None
    for k in _COLUMNS:
        if k in cols and x >= cols[k] - 3.0 and (best is None or cols[k] >= cols[best]):
            best = k
    return best or "game_date"


def _join(ws: list[_Word]) -> str:
    """Join fragments; a fragment ending in '-' (a hyphenated name split across fragments) is glued to the next."""
    out = ""
    for w in ws:
        if out and not (out.endswith("-") and len(out) > 1 and out[-2] != " "):
            out += " "
        out += w.text
    return " ".join(out.split())


def _display_name(raw: str) -> str:
    """'Morant, Ja' / 'Pippen Jr.,Scotty' -> 'Ja Morant' / 'Scotty Pippen Jr.'."""
    if "," not in raw:
        return raw.strip()
    last, first = (x.strip() for x in raw.split(",", 1))
    return f"{first} {last}".strip()


def _parse_words(words: list[_Word]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    teams = _team_name_index()
    rows: list[dict[str, Any]] = []
    meta: dict[str, Any] = {"pages": len({w.page for w in words}), "pages_with_header": 0, "header_time_et": None,
                            "unresolved_team_text": set(), "status_tokens": sum(1 for w in words if w.text in _PDF_STATUS)}
    ctx: dict[str, Any] = {"game_date": None, "game_time": None, "away": None, "home": None, "team_id": None}
    cols_prev: dict[str, float] | None = None
    for pg in sorted({w.page for w in words}):
        lines = _lines([w for w in words if w.page == pg])
        m = _HEADER_TIME_RE.search(" ".join(" ".join(w.text for w in ln) for ln in lines[:4]))
        if m and meta["header_time_et"] is None:
            mo, d, yy, hh, mi, ap = m.groups()
            meta["header_time_et"] = f"20{yy}-{mo}-{d} {int(hh):02d}:{mi} {ap}"
        hc = _header_columns(lines)
        if hc is None:
            if cols_prev is None:
                continue
            cols, header_top = cols_prev, -1.0
        else:
            cols, header_top = hc
            cols_prev = cols
            meta["pages_with_header"] += 1
        anchors: list[tuple[float, dict[str, Any]]] = []
        loose_reason: list[_Word] = []
        for ln in lines:
            if ln[0].top <= header_top + _LINE_TOL:
                continue
            first = ln[0].text
            if first.startswith("Injury") and any(w.text.startswith("Report") for w in ln[:3]):
                continue  # page title
            if first == "Page" and len(ln) <= 5:
                continue  # 'Page N of M'
            cells: dict[str, list[_Word]] = {k: [] for k in _COLUMNS}
            for w in ln:
                cells[_column(w.x, cols)].append(w)
            text = {k: _join(v) for k, v in cells.items()}
            dm = _CELL_DATE_RE.match(text["game_date"].split()[0]) if text["game_date"] else None
            if dm:
                ctx["game_date"] = f"{dm[3]}-{dm[1]}-{dm[2]}"
            if text["game_time"]:
                ctx["game_time"] = text["game_time"].replace("(ET)", "").strip()
            mm = _CELL_MATCHUP_RE.match(text["matchup"].replace(" ", "")) if text["matchup"] else None
            if mm:
                ctx["away"], ctx["home"] = mm[1], mm[2]
            if text["team"]:
                tid = teams.get(text["team"].lower())
                if tid is not None:
                    ctx["team_id"] = tid
                else:
                    meta["unresolved_team_text"].add(text["team"])
            status_tok = text["status"].split()[0] if text["status"] else ""
            nys = "NOT YET SUBMITTED" in " ".join(text[k] for k in ("player", "status", "reason")).upper()
            base = {"game_date": ctx["game_date"], "game_time_et": ctx["game_time"], "away_tricode": ctx["away"],
                    "home_tricode": ctx["home"], "team_id": ctx["team_id"]}
            if status_tok in _PDF_STATUS and text["player"]:
                anchors.append((ln[0].top, {**base, "player": text["player"], "status": _PDF_STATUS[status_tok],
                                            "_reason": list(cells["reason"])}))
            elif nys:
                anchors.append((ln[0].top, {**base, "player": None, "status": None, "_reason": []}))
            else:
                loose_reason.extend(cells["reason"])
        for w in loose_reason:  # wrapped reason fragments -> nearest row on this page
            if not anchors:
                break
            min(anchors, key=lambda a: abs(a[0] - w.top))[1]["_reason"].append(w)
        for _, row in anchors:
            frag = sorted(row.pop("_reason"), key=lambda w: (w.top, w.x))
            rows.append({**row, "reason": _join(frag) or None})
    meta["unresolved_team_text"] = sorted(meta["unresolved_team_text"])[:20]
    return rows, meta


def parse_injury_report_pdf(pdf_bytes: bytes, report_time_utc: datetime, source: str = "nba_official_pdf") -> tuple[list[InjuryEntry], dict[str, Any]]:
    """Official report PDF -> (entries, meta). ``meta`` reports pages, row counts, the report time printed in the
    PDF header, teams whose report was NOT YET SUBMITTED and rows dropped for an unresolvable team.

    Raises :class:`InjuryReportParseError` when the PDF holds text but no column header, or holds status words
    but yields no player rows -- never silently returns ``[]`` for a non-empty report."""
    words = _extract_words(pdf_bytes)
    rows, meta = _parse_words(words)
    if words and meta["pages_with_header"] == 0:
        raise InjuryReportParseError(f"injury report PDF has {len(words)} text fragments but no column header row")
    player_rows = [r for r in rows if r["player"]]
    entries: list[InjuryEntry] = []
    dropped = 0
    fallback_date = report_time_utc.astimezone(ET).date().isoformat()
    for r in player_rows:
        if r["team_id"] is None:
            dropped += 1
            continue
        entries.append(InjuryEntry(
            game_id=None, game_date_et=r["game_date"] or fallback_date, team_id=r["team_id"], nba_id=None,
            player_name_raw=_display_name(r["player"]), status=r["status"], reason=r["reason"],
            report_time_utc=report_time_utc, source=source,
        ))
    meta["n_player_rows"] = len(player_rows)
    meta["n_dropped_no_team"] = dropped
    meta["not_yet_submitted"] = sorted({f"{r['away_tricode']}@{r['home_tricode']}:{r['team_id']}" for r in rows if not r["player"]})
    meta["n"] = len(entries)
    if not entries and (meta["status_tokens"] or player_rows):
        raise InjuryReportParseError(
            f"injury report PDF holds {meta['status_tokens']} status words and {len(player_rows)} player rows "
            f"but produced 0 entries (unresolved team text: {meta['unresolved_team_text']})")
    if dropped:
        log.warning(kv(event="injury_report_rows_dropped", dropped=dropped, unresolved=meta["unresolved_team_text"]))
    return entries, meta


def _header_time_utc(header_time_et: str | None) -> datetime | None:
    if not header_time_et:
        return None
    return datetime.strptime(header_time_et, "%Y-%m-%d %I:%M %p").replace(tzinfo=ET).astimezone(UTC)


def fetch_official_injury_report(report_time_et: datetime, max_retries: int = 3) -> tuple[list[InjuryEntry], dict[str, Any]]:
    """Fetch the report published at ``report_time_et`` (an ET-aware datetime on a 15-minute grid). Returns
    (entries, provenance). Missing report (404/403) -> empty list with provenance['missing']=True. A report that
    is present but unparseable raises :class:`InjuryReportParseError` (the caller records it as an error).

    Rows are stamped with the report time printed in the PDF header (``report_time_source = "pdf_header"``),
    never with anything later. Without a usable header the slot time is used; it is never later than the
    header (hourly-era files are named for the hour and printed HH:30/HH:45; 15-minute files match)."""
    last_err: str | None = None
    urls = candidate_pdf_urls(report_time_et)
    for i, url in enumerate(urls):
        try:
            f = fetch(url, headers=PLAIN_HEADERS_OK, ttl_s=None, max_retries=max_retries)
        except FetchError as e:
            last_err = str(e)[:200]
            continue
        slot_utc = report_time_et.astimezone(UTC)
        try:
            entries, meta = parse_injury_report_pdf(f.content, slot_utc)
        except InjuryReportParseError as e:
            log.error(kv(event="injury_report_parse_failed", url=url, error=str(e)[:200]))
            raise
        header_utc = _header_time_utc(meta.get("header_time_et"))
        fetched_utc = datetime.fromisoformat(f.fetched_at_utc.replace("Z", "+00:00"))
        source = "slot"
        if header_utc is not None and header_utc <= fetched_utc:
            source = "pdf_header"
            if header_utc != slot_utc:
                entries = [e.model_copy(update={"report_time_utc": header_utc}) for e in entries]
        elif header_utc is not None:  # a header time after we downloaded it cannot be right; keep the slot
            log.warning(kv(event="injury_report_header_after_fetch", url=url, header=meta.get("header_time_et")))
        report_time = header_utc if source == "pdf_header" else slot_utc
        log.info(kv(event="official_injury_report", url=url, n=len(entries), pages=meta["pages"]))
        return entries, {"source": "nba_official_pdf", "url": url, "fetched_at_utc": f.fetched_at_utc, "n": len(entries), "bytes": len(f.content),
                         "slot_et": report_time_et.astimezone(ET).strftime("%Y-%m-%dT%H:%M"),
                         "report_time_utc": report_time.strftime("%Y-%m-%dT%H:%M:%SZ"), "report_time_source": source,
                         "requests": i + 1, "pages": meta["pages"], "n_player_rows": meta["n_player_rows"], "n_dropped_no_team": meta["n_dropped_no_team"],
                         "header_time_et": meta["header_time_et"], "not_yet_submitted": meta["not_yet_submitted"],
                         "unresolved_team_text": meta["unresolved_team_text"]}
    return [], {"source": "nba_official_pdf", "missing": True, "error": last_err, "report_time_et": report_time_et.isoformat(), "requests": len(urls)}


def latest_report_slots(now_utc: datetime, lookback_hours: int = 6) -> list[datetime]:
    """Official reports are published on the hour/half/quarter; try the most recent 15-minute slots first."""
    now_et = now_utc.astimezone(ET).replace(second=0, microsecond=0)
    now_et = now_et - timedelta(minutes=now_et.minute % 15)
    slots = []
    for k in range(lookback_hours * 4):
        slots.append(now_et - timedelta(minutes=15 * k))
    return slots


def report_search_slots(now_utc: datetime, max_hours: int = SEARCH_MAX_HOURS, min_slots: int = SEARCH_MIN_SLOTS) -> list[datetime]:
    """The 15-minute slots to probe for the latest published report, newest first: back to the start of the
    current ET game day (00:00 ET), at least ``min_slots`` and at most ``max_hours`` back.

    A report from an earlier ET day lists that day's games, which have been played, so it is not the
    "latest report" for anything still to tip; the 2-hour floor keeps the old behaviour just after midnight."""
    now_et = now_utc.astimezone(ET).replace(second=0, microsecond=0)
    newest = now_et - timedelta(minutes=now_et.minute % 15)
    day_start = newest.replace(hour=0, minute=0)
    n = int((newest - day_start).total_seconds() // 900) + 1
    n = max(min_slots, min(n, max_hours * 4))
    return [newest - timedelta(minutes=15 * k) for k in range(n)]


def fetch_latest_official_injury_report(now_utc: datetime, max_requests: int = SEARCH_MAX_REQUESTS) -> tuple[list[InjuryEntry], dict[str, Any]]:
    """Probe :func:`report_search_slots` newest first and return the first report found (the latest one
    published), with provenance naming the slot found, slots probed and HTTP requests made. Each probe is a
    single attempt plus one retry on transport errors; the search stops at ``max_requests``."""
    slots = report_search_slots(now_utc)
    window = {"search_newest_slot_et": slots[0].strftime("%Y-%m-%dT%H:%M"), "search_oldest_slot_et": slots[-1].strftime("%Y-%m-%dT%H:%M"),
              "search_window_slots": len(slots), "max_requests": max_requests}
    tried = requests = 0
    for slot in slots:
        if requests + len(candidate_pdf_urls(slot)) > max_requests:
            break
        entries, prov = fetch_official_injury_report(slot, max_retries=1)
        tried += 1
        requests += prov.get("requests", 1)
        if not prov.get("missing"):
            prov.update(window, slots_tried=tried, requests=requests)
            age = (now_utc - datetime.fromisoformat(prov["report_time_utc"].replace("Z", "+00:00"))).total_seconds() / 60
            prov["report_age_min"] = round(age, 1)
            return entries, prov
    log.info(kv(event="official_injury_report_missing", slots_tried=tried, requests=requests, oldest=window["search_oldest_slot_et"]))
    return [], {"source": "nba_official_pdf", "missing": True, "slots_tried": tried, "requests": requests,
                "budget_exhausted": tried < len(slots), **window}


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
