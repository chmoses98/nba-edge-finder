"""Kalshi ticker parsing for NBA series.

Ticker anatomy (observed convention): ``{SERIES}-{EVENT}-{MARKET}``
    KXNBAGAME-26MAY22OKCSAS-OKC
    ^series   ^event suffix ^market suffix

Event suffixes for game-level series are ``{YYMMMDD}{AWAY}{HOME}``; e.g. ``26MAY22OKCSAS``.
This parser is deliberately *tolerant*: it never raises on an unfamiliar shape. It returns a
``ParsedTicker`` with ``confidence`` and a list of ``notes`` so downstream code can decide whether
the parse is trustworthy. Authoritative semantics always come from Kalshi market fields
(strike_type, floor_strike, cap_strike, custom_strike, yes_sub_title, rules_primary), never from
the ticker string alone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

MONTHS = {m: i for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}

# 26MAY22OKCSAS  -> yy=26 mon=MAY dd=22 away=OKC home=SAS ; tricodes are 2-4 uppercase letters
GAME_EVENT_RE = re.compile(r"^(?P<yy>\d{2})(?P<mon>[A-Z]{3})(?P<dd>\d{2})(?P<teams>[A-Z]{4,8})(?P<extra>[A-Z0-9]*)$")
DATE_ONLY_RE = re.compile(r"^(?P<yy>\d{2})(?P<mon>[A-Z]{3})(?P<dd>\d{2})$")
SEASON_RE = re.compile(r"^(?P<yy>\d{2})$|^(?P<y1>\d{2})(?P<y2>\d{2})$")


@dataclass
class ParsedTicker:
    ticker: str
    series_ticker: str
    event_ticker: str
    event_suffix: str
    market_suffix: str
    game_date: date | None = None
    away_tricode: str | None = None
    home_tricode: str | None = None
    extra: str = ""
    confidence: str = "low"  # low | medium | high
    notes: list[str] = field(default_factory=list)


def split_ticker(ticker: str) -> tuple[str, str, str]:
    parts = ticker.split("-")
    if len(parts) < 2:
        return ticker, "", ""
    series = parts[0]
    event_suffix = parts[1]
    market_suffix = "-".join(parts[2:]) if len(parts) > 2 else ""
    return series, event_suffix, market_suffix


def _split_teams(teams: str, known_tricodes: set[str] | None) -> tuple[str | None, str | None, list[str]]:
    """Split a concatenated AWAYHOME string. Tricodes are usually 3 letters but not always (e.g. two-letter codes
    do not exist in the NBA, but Kalshi could use 2-4). Prefer splits where both halves are known tricodes."""
    notes: list[str] = []
    candidates = []
    for cut in range(2, len(teams) - 1):
        a, h = teams[:cut], teams[cut:]
        score = 0
        if known_tricodes:
            score += (a in known_tricodes) + (h in known_tricodes)
        if len(a) == 3 and len(h) == 3:
            score += 1
        candidates.append((score, a, h))
    if not candidates:
        return None, None, ["teams string too short"]
    candidates.sort(key=lambda t: -t[0])
    score, a, h = candidates[0]
    if known_tricodes and score < 2:
        notes.append(f"team split not fully verified against known tricodes: {a}/{h}")
    return a, h, notes


def parse_ticker(ticker: str, known_tricodes: set[str] | None = None) -> ParsedTicker:
    series, ev, mk = split_ticker(ticker)
    p = ParsedTicker(ticker=ticker, series_ticker=series, event_ticker=f"{series}-{ev}" if ev else series, event_suffix=ev, market_suffix=mk)
    m = GAME_EVENT_RE.match(ev)
    if m:
        try:
            p.game_date = date(2000 + int(m["yy"]), MONTHS[m["mon"]], int(m["dd"]))
        except (KeyError, ValueError) as e:
            p.notes.append(f"bad date in event suffix: {e}")
            return p
        away, home, notes = _split_teams(m["teams"], known_tricodes)
        p.away_tricode, p.home_tricode = away, home
        p.extra = m["extra"]
        p.notes.extend(notes)
        p.confidence = "high" if not notes and away and home else "medium"
        return p
    m = DATE_ONLY_RE.match(ev)
    if m:
        try:
            p.game_date = date(2000 + int(m["yy"]), MONTHS[m["mon"]], int(m["dd"]))
            p.confidence = "medium"
            p.notes.append("date-only event suffix (no teams encoded)")
        except (KeyError, ValueError):
            p.notes.append("date-like suffix failed to parse")
        return p
    p.notes.append("event suffix shape not recognized as a game; treat as season/futures or unknown")
    return p
