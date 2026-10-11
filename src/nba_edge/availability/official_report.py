"""Official NBA injury report PDFs -> rows (player, team, game, status, reason, report_time).

Source: ``https://ak-static.cms.nba.com/referee/injury/Injury-Report_YYYY-MM-DD_HH_MMAM.pdf``. The slot in
the filename is the report's nominal publication time (US Eastern, 15-minute grid); the HTTP
``Last-Modified`` header is the actual upload instant. A slot with no report answers 403.

Why a positional parser: ``pypdf``'s plain ``extract_text`` emits one token per line for these files, so
row structure is lost (the line-based parser in :mod:`nba_edge.data.injuries` cannot recover it). Here
every text fragment keeps its (x, y) position; columns are located from the header row on each page,
fragments are grouped into visual lines, and a line is a player row when its Current Status cell holds
a status word. Game date/time, matchup and team are printed only on the first row of their group, so
they carry forward. A reason that wraps is printed vertically centred on its row, so wrapped reason
fragments are attached to the NEAREST player row on the page. A team whose report is not in yet is
printed as ``NOT YET SUBMITTED`` and becomes a team-level row with ``status = "not_yet_submitted"``.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from nba_edge.identity.teams import registry
from nba_edge.timeutil import ET

URL = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_{date}_{hh}_{mm}{ampm}.pdf"
# Older reports (hourly cadence) used ``_HHPM`` with no minutes; tried for on-the-hour slots only.
URL_HOURLY = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_{date}_{hh}{ampm}.pdf"
STATUSES = {"Out": "out", "Doubtful": "doubtful", "Questionable": "questionable", "Probable": "probable",
            "Available": "available"}
COLUMNS = ("game_date", "game_time", "matchup", "team", "player", "status", "reason")
_MATCHUP = re.compile(r"^([A-Z]{2,3})@([A-Z]{2,3})$")
_DATE = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")
_HEADER_TIME = re.compile(r"Injury Report:\s*(\d{2})/(\d{2})/(\d{2})\s+(\d{1,2}):(\d{2})\s*([AP]M)")
LINE_TOL = 2.0
PARSER_VERSION = "official-pdf-positional/2"


def report_url(slot_et: datetime) -> str:
    s = slot_et.astimezone(ET)
    return URL.format(date=s.strftime("%Y-%m-%d"), hh=s.strftime("%I"), mm=s.strftime("%M"), ampm=s.strftime("%p"))


def report_urls(slot_et: datetime, extended: bool = False) -> list[str]:
    """Filename variants a report filed under this slot may use, most common first.

    Measured on the 2025-26 archive: from 2025-12-22 files are ``_HH_MMPM`` on a 15-minute grid and the
    filename time is the report time. Before that, files were hourly ``_HHPM`` and the filename is NOT the
    report time -- the PDF header says HH:30 (to 2025-12-18) or HH:45 (2025-12-19..21), and Last-Modified
    agrees. The report time is therefore always taken from the PDF header, never from the filename.
    ``extended`` adds rarer spellings, used only for games no standard variant located.
    """
    s = slot_et.astimezone(ET)
    d, hh, mm, ap = s.strftime("%Y-%m-%d"), s.strftime("%I"), s.strftime("%M"), s.strftime("%p")
    urls = [report_url(s)]
    if s.minute == 0:
        urls.append(URL_HOURLY.format(date=d, hh=hh, ampm=ap))
    if extended:
        base = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_"
        h1 = str(int(hh))
        urls += [f"{base}{d}_{hh}_{mm}_{ap}.pdf", f"{base}{d}_{hh}{mm}{ap}.pdf", f"{base}{d}_{h1}_{mm}{ap}.pdf",
                 f"{base}{d}_{hh}_{mm}{ap.lower()}.pdf", f"{base}{d}_{hh}-{mm}{ap}.pdf"]
        if s.minute == 0:
            urls += [f"{base}{d}_{h1}{ap}.pdf", f"{base}{d}_{hh}{ap.lower()}.pdf"]
    return urls


def slot_floor(t_et: datetime) -> datetime:
    t = t_et.astimezone(ET).replace(second=0, microsecond=0)
    return t - timedelta(minutes=t.minute % 15)


@dataclass
class Word:
    page: int
    x: float
    top: float  # distance from the top of the page (larger = lower)
    text: str


def extract_words(pdf_bytes: bytes) -> tuple[list[Word], int]:
    """Every text fragment with its page position, via pypdf's text visitor (no extra dependency)."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(pdf_bytes))
    words: list[Word] = []
    for pi, page in enumerate(reader.pages):
        height = float(page.mediabox.height)

        def visit(text, cm, tm, font_dict, font_size, pi=pi, height=height):
            t = (text or "").strip()
            if not t:
                return
            x = tm[4] * cm[0] + tm[5] * cm[2] + cm[4]
            y = tm[4] * cm[1] + tm[5] * cm[3] + cm[5]
            words.append(Word(pi, round(float(x), 2), round(height - float(y), 2), t))

        start = len(words)
        page.extract_text(visitor_text=visit)
        _orient(words, start)
    return words, len(reader.pages)


def _orient(words: list[Word], start: int) -> None:
    """Make ``top`` grow downward on the page. Some of these PDFs use a flipped text matrix (pypdf's own
    layout mode prints them bottom-to-top); the page title 'Injury Report:' must be the topmost line."""
    page_words = words[start:]
    title = [w.top for w in page_words if w.text.startswith("Injury")]
    if not page_words or not title:
        return
    tops = sorted(w.top for w in page_words)
    median = tops[len(tops) // 2]
    if min(title) > median:  # the title sits below the body -> axis is inverted
        mx = tops[-1]
        for w in page_words:
            w.top = round(mx - w.top, 2)


def _lines(words: list[Word]) -> list[list[Word]]:
    out: list[list[Word]] = []
    for w in sorted(words, key=lambda w: (w.top, w.x)):
        if out and abs(out[-1][0].top - w.top) <= LINE_TOL:
            out[-1].append(w)
        else:
            out.append([w])
    return [sorted(line, key=lambda w: w.x) for line in out]


def _header_columns(lines: list[list[Word]]) -> tuple[dict[str, float], float] | None:
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
    for k in COLUMNS:
        if k in cols and x >= cols[k] - 3.0:
            if best is None or cols[k] >= cols[best]:
                best = k
    return best or "game_date"


def _join(ws: list[Word]) -> str:
    """Join fragments; a fragment ending in '-' (a hyphenated name split across fragments) is glued to
    the next one ('Hayes-' + 'Davis,' -> 'Hayes-Davis,')."""
    out = ""
    for w in ws:
        if out and not (out.endswith("-") and len(out) > 1 and out[-2] != " "):
            out += " "
        out += w.text
    return " ".join(out.split())


def _team_index() -> dict[str, int]:
    return {t.name.lower(): t.team_id for t in registry().teams}


def parse_words(words: list[Word], slot_et: datetime) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Row assembly over positioned words. Returns (rows, meta)."""
    teams = _team_index()
    rows: list[dict[str, Any]] = []
    meta: dict[str, Any] = {"pages_parsed": 0, "pages_without_header": 0, "header_time_et": None,
                            "unresolved_team_text": []}
    ctx: dict[str, Any] = {"game_date": None, "game_time": None, "away": None, "home": None, "team_id": None,
                           "team_text": None}
    cols_prev: dict[str, float] | None = None
    pages = sorted({w.page for w in words})
    for pg in pages:
        lines = _lines([w for w in words if w.page == pg])
        all_txt = " ".join(" ".join(w.text for w in ln) for ln in lines[:4])
        m = _HEADER_TIME.search(all_txt)
        if m and meta["header_time_et"] is None:
            mo, d, yy, hh, mi, ap = m.groups()
            meta["header_time_et"] = f"20{yy}-{mo}-{d} {int(hh):02d}:{mi} {ap}"
        hc = _header_columns(lines)
        if hc is None:
            meta["pages_without_header"] += 1
            if cols_prev is None:
                continue
            cols, header_top = cols_prev, -1.0
        else:
            cols, header_top = hc
            cols_prev = cols
        meta["pages_parsed"] += 1
        anchors: list[tuple[float, dict[str, Any]]] = []
        loose_reason: list[Word] = []
        for ln in lines:
            if ln[0].top <= header_top + LINE_TOL:
                continue
            first = ln[0].text
            if first.startswith("Injury") and any(w.text.startswith("Report") for w in ln[:3]):
                continue  # page title
            if first == "Page" and len(ln) <= 5:
                continue  # page footer/header 'Page N of M'

            cells: dict[str, list[Word]] = {k: [] for k in COLUMNS}
            for w in ln:
                cells[_column(w.x, cols)].append(w)
            text = {k: _join(v) for k, v in cells.items()}
            if text["game_date"] and _DATE.match(text["game_date"].split()[0]):
                mo, d, y = _DATE.match(text["game_date"].split()[0]).groups()
                ctx["game_date"] = f"{y}-{mo}-{d}"
            if text["game_time"]:
                ctx["game_time"] = text["game_time"].replace("(ET)", "").strip()
            mm = _MATCHUP.match(text["matchup"].replace(" ", "")) if text["matchup"] else None
            if mm:
                ctx["away"], ctx["home"] = mm.group(1), mm.group(2)
            if text["team"]:
                tid = teams.get(" ".join(text["team"].split()).lower())
                if tid is not None:
                    ctx["team_id"], ctx["team_text"] = tid, " ".join(text["team"].split())
                else:
                    meta["unresolved_team_text"].append(text["team"])
            status_tok = text["status"].split()[0] if text["status"] else ""
            nys = "NOT YET SUBMITTED" in " ".join(text[k] for k in ("player", "status", "reason")).upper()
            base = {"game_date": ctx["game_date"], "game_time_et": ctx["game_time"], "away_tricode": ctx["away"],
                    "home_tricode": ctx["home"], "team_id": ctx["team_id"], "team_text": ctx["team_text"]}
            if status_tok in STATUSES and text["player"]:
                row = {**base, "player_name_raw": " ".join(text["player"].split()), "status": STATUSES[status_tok],
                       "_reason": [w for w in cells["reason"]], "page": pg}
                anchors.append((ln[0].top, row))
            elif nys:
                row = {**base, "player_name_raw": None, "status": "not_yet_submitted", "_reason": [], "page": pg}
                anchors.append((ln[0].top, row))
            else:
                loose_reason.extend(cells["reason"])
        # wrapped reason fragments -> nearest player row on this page
        for w in loose_reason:
            if not anchors:
                break
            top, row = min(anchors, key=lambda a: abs(a[0] - w.top))
            row["_reason"].append(w)
        for top, row in anchors:
            frag = sorted(row.pop("_reason"), key=lambda w: (w.top, w.x))
            reason = _join(frag) or None
            rows.append({**row, "reason": reason, "_top": top})
    for r in rows:
        r.pop("_top", None)
    meta["n_rows"] = len(rows)
    meta["n_player_rows"] = sum(1 for r in rows if r["player_name_raw"])
    meta["n_not_yet_submitted"] = sum(1 for r in rows if r["status"] == "not_yet_submitted")
    meta["rows_missing_team"] = sum(1 for r in rows if r["team_id"] is None)
    meta["rows_missing_game"] = sum(1 for r in rows if not (r["home_tricode"] and r["game_date"]))
    expected = slot_et.astimezone(ET).strftime("%Y-%m-%d %I:%M %p")
    meta["header_time_matches_slot"] = meta["header_time_et"] == expected
    meta["report_time_et"] = None
    if meta["header_time_et"]:
        meta["report_time_et"] = datetime.strptime(meta["header_time_et"], "%Y-%m-%d %I:%M %p").replace(
            tzinfo=ET).isoformat()
    meta["unresolved_team_text"] = sorted(set(meta["unresolved_team_text"]))[:20]
    return rows, meta


def parse_report_pdf(pdf_bytes: bytes, slot_et: datetime) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    words, n_pages = extract_words(pdf_bytes)
    rows, meta = parse_words(words, slot_et)
    meta["n_pages"] = n_pages
    return rows, meta
