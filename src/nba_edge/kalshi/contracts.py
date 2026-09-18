"""Turn a Kalshi market object into a ``Contract``: an explicit, testable statement of what YES means.

Authoritative fields (in priority order):
1. ``strike_type`` + ``floor_strike``/``cap_strike`` (numeric thresholds; Kalshi sends them as strings).
2. ``custom_strike`` (``{'basketball_team': <uuid>}`` / ``{'basketball_player': <uuid>}``) -> entity identity.
3. ``yes_sub_title`` / ``title`` / ``rules_primary`` -> entity names, period words, 'originally scheduled for' date.
4. Ticker (event suffix) -> game date + away/home tricodes, as a cross-check only.

Observed semantics (2026-09-18 discovery, see data/fixtures/kalshi_sample_markets.json):
- winner:   strike_type=structured, custom_strike.basketball_team, title 'San Antonio wins'
- spread:   strike_type=greater, floor_strike='15.5', title 'Denver wins by over 15.5 points?'  => YES iff margin(team) > 15.5
- total:    strike_type=greater, floor_strike='199.5', title 'Full Game: Over 199.5 points scored' => YES iff total > 199.5
- 1H spread/total/winner: same shapes with '1H' / 'First Half' words; rules say 'regulation time' for halves
- season wins: strike_type=greater_or_equal, floor_strike='60'
Anything else is returned with ``semantics_confidence='low'`` and support downgraded to UNRESOLVED.
"""

from __future__ import annotations

import ast
import re
from datetime import date
from typing import Any

from nba_edge.identity.teams import TeamIdentityError, TeamRegistry, registry
from nba_edge.kalshi.ontology import Ontology, Support, classify_market
from nba_edge.kalshi.ticker import parse_ticker
from nba_edge.schemas.market import Contract

_SCHED_RE = re.compile(r"originally scheduled for ([A-Z][a-z]{2}) (\d{1,2}), (\d{4})")
_MONTHS = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}
_H2H_RE = re.compile(r"\bmore\b.*\bthan\b", re.I)


def _num(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _custom_strike(m: dict[str, Any]) -> dict[str, Any]:
    cs = m.get("custom_strike")
    if isinstance(cs, dict):
        return cs
    if isinstance(cs, str):
        try:
            v = ast.literal_eval(cs)
            return v if isinstance(v, dict) else {}
        except (ValueError, SyntaxError):
            return {}
    return {}


def scheduled_date_from_rules(rules: str | None) -> date | None:
    m = _SCHED_RE.search(rules or "")
    if not m:
        return None
    try:
        return date(int(m[3]), _MONTHS[m[1]], int(m[2]))
    except (KeyError, ValueError):
        return None


def _team_from_text(text: str, reg: TeamRegistry, candidates: list[str]) -> int | None:
    """Find which of the two game teams (by tricode) the text names. Uses city/nickname/full-name matching and
    requires exactly one hit."""
    t = (text or "").lower()
    hits = []
    for code in candidates:
        try:
            team = reg.by_tricode(code)
        except TeamIdentityError:
            continue
        keys = {team.city.lower(), team.nickname.lower(), team.name.lower()}
        if team.tricode == "LAL":
            keys |= {"los angeles l", "la lakers"}
        if team.tricode == "LAC":
            keys |= {"los angeles c", "la clippers"}
        if any(k in t for k in keys):
            hits.append(team.team_id)
    hits = list(dict.fromkeys(hits))
    if len(hits) == 1:
        return hits[0]
    if len(hits) == 2 and ("los angeles" in t or t.startswith("la ")):
        # 'Los Angeles wins' is ambiguous between LAL/LAC unless the ticker suffix disambiguates
        return None
    return None


def build_contract(m: dict[str, Any], ontology: Ontology | None = None, reg: TeamRegistry | None = None) -> Contract:
    ontology = ontology or Ontology.load()
    reg = reg or registry()
    cls = classify_market(m, ontology)
    ticker = m.get("ticker", "")
    pt = parse_ticker(ticker, reg.tricodes)
    notes: list[str] = list(pt.notes)
    title = m.get("title") or ""
    ysub = m.get("yes_sub_title") or ""
    rules = m.get("rules_primary") or ""
    strike_type = m.get("strike_type")
    floor = _num(m.get("floor_strike"))
    cap = _num(m.get("cap_strike"))
    cs = _custom_strike(m)

    team_id: int | None = None
    nba_id: int | None = None
    threshold: float | None = None
    comparator: str | None = None
    upper: float | None = None
    conf = "low"
    support = cls.support

    game_candidates = [c for c in (pt.away_tricode, pt.home_tricode) if c]
    # market suffix often names the team (…-SAS, …-DEN16): use it to disambiguate LA teams
    suffix_team = None
    for code in game_candidates:
        if pt.market_suffix.upper().startswith(code):
            suffix_team = code
    if cls.scope.value == "game":
        if suffix_team:
            team_id = reg.by_tricode(suffix_team).team_id
        elif cls.stat in ("winner", "margin", "team_total"):
            team_id = _team_from_text(ysub or title, reg, game_candidates)
        if cls.stat == "winner" and strike_type == "structured" and cs.get("basketball_team") and team_id is not None:
            comparator, threshold, conf = "gt", 0.0, "high"
        elif cls.stat == "margin" and strike_type == "greater" and floor is not None and team_id is not None:
            comparator, threshold, conf = "gt", floor, "high"
        elif cls.stat == "total" and strike_type == "greater" and floor is not None:
            comparator, threshold, conf = "gt", floor, "high"
        elif cls.stat == "team_total" and strike_type == "greater" and floor is not None and team_id is not None:
            comparator, threshold, conf = "gt", floor, "high"
        elif strike_type == "between" and floor is not None and cap is not None:
            comparator, threshold, upper, conf = "in_range", floor, cap, "medium"
            notes.append("range market: verify inclusive/exclusive bounds in rules")
        elif strike_type == "greater_or_equal" and floor is not None:
            comparator, threshold, conf = "ge", floor, "medium"
        elif strike_type == "less" and floor is not None:
            comparator, threshold, conf = "lt", floor, "medium"
        else:
            notes.append(f"unrecognised game-market shape strike_type={strike_type} stat={cls.stat}")
        if _H2H_RE.search(title) and cls.stat not in ("winner",):
            conf = "low"
            notes.append("head-to-head phrasing; not a threshold contract")
    elif cls.scope.value == "player":
        # identity is resolved downstream (kalshi player uuid / display name -> nba_id); here we only extract threshold
        # observed 2025-26 shape: strike_type='structured', floor_strike='39.5', title 'Cade Cunningham records 40+ points'
        if strike_type in ("greater", "structured") and floor is not None:
            comparator, threshold, conf = "gt", floor, "high" if cs.get("basketball_player") else "medium"
        elif strike_type == "greater_or_equal" and floor is not None:
            comparator, threshold, conf = "ge", floor, "medium"
        elif strike_type == "structured" and cls.stat in ("double_double", "triple_double"):
            comparator, threshold, conf = "ge", 1.0, "medium"
        else:
            notes.append(f"unrecognised player-market shape strike_type={strike_type} stat={cls.stat}")
        if _H2H_RE.search(title):
            conf = "low"
            notes.append("head-to-head player market; needs two-player joint pricing")
    elif cls.scope.value == "season":
        if strike_type == "greater_or_equal" and floor is not None:
            comparator, threshold, conf = "ge", floor, "medium"
        elif strike_type == "structured" and cs.get("basketball_team"):
            comparator, threshold, conf = "gt", 0.0, "medium"

    sched = scheduled_date_from_rules(rules)
    if sched and pt.game_date and sched != pt.game_date:
        notes.append(f"rules date {sched} != ticker date {pt.game_date}")
        conf = "low"
    if cls.period in ("1Q", "2Q", "3Q", "4Q", "1H", "2H") and "regulation" not in rules.lower() and rules:
        notes.append("period market rules do not mention regulation; verify OT handling")
    if conf == "low" and support in (Support.PRICED, Support.BUILDABLE):
        support = Support.UNRESOLVED
        notes.append("support downgraded: semantics not proven")

    entity_name = player_name_from_title(title, ysub) if cls.scope.value == "player" else None
    if cls.scope.value == "player" and team_id is None:
        for code in game_candidates:
            if pt.market_suffix.upper().startswith(code):
                team_id = reg.by_tricode(code).team_id
    return Contract(
        ticker=ticker, family=cls.family, scope=cls.scope.value, stat=cls.stat, period=cls.period, game_id=None, team_id=team_id, nba_id=nba_id,
        threshold=threshold, comparator=comparator, upper=upper, support=str(support), semantics_confidence=conf, notes=notes,
        entity_name=entity_name, kalshi_entity_uuid=(cs.get("basketball_player") or cs.get("basketball_team")),
    )


_PLAYER_TITLE_RE = re.compile(r"^(?P<name>[A-Z][\w.'\-]+(?: [A-Z][\w.'\-]+){1,3}?) (?:records|scores|to record|to score)\b", re.U)
_PLAYER_SUB_RE = re.compile(r"^(?P<name>[A-Z][\w.'\-]+(?: [A-Z][\w.'\-]+){1,3}?): \d", re.U)


def player_name_from_title(title: str, yes_sub_title: str = "") -> str | None:
    m = _PLAYER_TITLE_RE.match(title or "")
    if m:
        return m["name"].strip()
    m = _PLAYER_SUB_RE.match(yes_sub_title or "")
    return m["name"].strip() if m else None


def kalshi_entity_uuid(m: dict[str, Any]) -> tuple[str, str] | None:
    cs = _custom_strike(m)
    for k in ("basketball_team", "basketball_player"):
        if cs.get(k):
            return k, str(cs[k])
    return None
