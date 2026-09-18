"""Market ontology: how a Kalshi NBA market maps to a modelled quantity.

Two layers:
1. ``data/catalog/market_ontology.yaml`` — curated, versioned knowledge about series → family. Editing YAML,
   not code, is the normal way to onboard a new market family once discovery surfaces it.
2. Heuristic classification (``classify_market``) that works from Kalshi market *fields* (title, strike
   fields, sub-titles, rules) for series the YAML does not know. Anything it cannot place lands in
   ``UNRESOLVED`` with a reason — never silently dropped.

Support states (coverage invariant; every ticker gets exactly one):
    PRICED      : simulator + contract semantics produce a probability we stand behind (subject to gates)
    BUILDABLE   : semantics understood, sim output exists or is near, but pricing not wired/validated
    RESEARCH    : semantics understood, but we do not yet have a defensible model (e.g. first basket)
    UNMODELABLE : semantics understood; we will not model (e.g. awards voting, draft)
    UNRESOLVED  : we could not determine what the contract means; needs human/ontology update
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml

from nba_edge.config import REPO_ROOT

ONTOLOGY_PATH = REPO_ROOT / "data" / "catalog" / "market_ontology.yaml"


class Support(StrEnum):
    PRICED = "PRICED"
    BUILDABLE = "BUILDABLE"
    RESEARCH = "RESEARCH"
    UNMODELABLE = "UNMODELABLE"
    UNRESOLVED = "UNRESOLVED"


class Scope(StrEnum):
    GAME = "game"
    PLAYER = "player"
    SEASON = "season"
    OTHER = "other"


@dataclass
class FamilySpec:
    family: str
    scope: Scope
    stat: str | None  # e.g. margin, total, team_total, pts, reb, ast, fg3m, pra ...
    period: str = "FULL"  # FULL | 1Q | 2Q | 3Q | 4Q | 1H | 2H | SEASON
    support: Support = Support.UNRESOLVED
    description: str = ""
    settlement_notes: str = ""
    series_tickers: list[str] = field(default_factory=list)
    title_patterns: list[str] = field(default_factory=list)


@dataclass
class Ontology:
    version: str
    families: dict[str, FamilySpec]
    series_to_family: dict[str, str]

    @classmethod
    def load(cls, path: Path = ONTOLOGY_PATH) -> Ontology:
        raw = yaml.safe_load(path.read_text())
        fams: dict[str, FamilySpec] = {}
        s2f: dict[str, str] = {}
        for name, spec in raw["families"].items():
            fs = FamilySpec(
                family=name,
                scope=Scope(spec["scope"]),
                stat=spec.get("stat"),
                period=spec.get("period", "FULL"),
                support=Support(spec.get("support", "UNRESOLVED")),
                description=spec.get("description", ""),
                settlement_notes=spec.get("settlement_notes", ""),
                series_tickers=list(spec.get("series_tickers", [])),
                title_patterns=list(spec.get("title_patterns", [])),
            )
            fams[name] = fs
            for st in fs.series_tickers:
                s2f[st.upper()] = name
        return cls(version=str(raw.get("version", "0")), families=fams, series_to_family=s2f)


# ---- heuristic classification from market fields -----------------------------------------------

_STAT_WORDS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"points?\s*\+\s*rebounds?\s*\+\s*assists?|\bPRA\b", re.I), "pra"),
    (re.compile(r"points?\s*\+\s*rebounds?|\bP\+R\b", re.I), "pr"),
    (re.compile(r"points?\s*\+\s*assists?|\bP\+A\b", re.I), "pa"),
    (re.compile(r"rebounds?\s*\+\s*assists?|\bR\+A\b", re.I), "ra"),
    (re.compile(r"double[- ]double", re.I), "double_double"),
    (re.compile(r"triple[- ]double", re.I), "triple_double"),
    (re.compile(r"three[- ]?pointers?|\b3[- ]?pointers?|\bthrees\b|\b3PM\b", re.I), "fg3m"),
    (re.compile(r"\brebounds?\b", re.I), "reb"),
    (re.compile(r"\bassists?\b", re.I), "ast"),
    (re.compile(r"\bsteals?\b", re.I), "stl"),
    (re.compile(r"\bblocks?\b", re.I), "blk"),
    (re.compile(r"\bturnovers?\b", re.I), "tov"),
    (re.compile(r"\bpoints?\b", re.I), "pts"),
]
_PERIOD_WORDS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(first|1st)\s+quarter\b|\b1Q\b", re.I), "1Q"),
    (re.compile(r"\b(second|2nd)\s+quarter\b|\b2Q\b", re.I), "2Q"),
    (re.compile(r"\b(third|3rd)\s+quarter\b|\b3Q\b", re.I), "3Q"),
    (re.compile(r"\b(fourth|4th)\s+quarter\b|\b4Q\b", re.I), "4Q"),
    (re.compile(r"\b(first|1st)\s+half\b|\b1H\b", re.I), "1H"),
    (re.compile(r"\b(second|2nd)\s+half\b|\b2H\b", re.I), "2H"),
]


def _period_from_text(*texts: str) -> str:
    for t in texts:
        for rx, per in _PERIOD_WORDS:
            if t and rx.search(t):
                return per
    return "FULL"


def _stat_from_text(*texts: str) -> str | None:
    for t in texts:
        for rx, stat in _STAT_WORDS:
            if t and rx.search(t):
                return stat
    return None


@dataclass
class Classification:
    family: str
    scope: Scope
    stat: str | None
    period: str
    support: Support
    reason: str
    via: str  # "ontology" | "heuristic" | "none"


def classify_market(market: dict[str, Any], ontology: Ontology) -> Classification:
    series = (market.get("series_ticker") or market.get("ticker", "").split("-")[0]).upper()
    title = market.get("title") or ""
    subtitle = market.get("subtitle") or market.get("yes_sub_title") or ""
    rules = market.get("rules_primary") or ""
    fam = ontology.series_to_family.get(series)
    if fam:
        spec = ontology.families[fam]
        period = spec.period if spec.period != "FULL" else _period_from_text(title, subtitle)
        return Classification(fam, spec.scope, spec.stat, period, spec.support, f"series {series} in ontology", "ontology")

    # Heuristics for unknown series. These land in UNRESOLVED (needs ontology entry) but carry a best guess
    # so the coverage report is informative.
    period = _period_from_text(title, subtitle, rules)
    stat = _stat_from_text(title, subtitle)
    text = f"{title} {subtitle}".lower()
    if any(w in text for w in ("champion", "finals", "mvp", "rookie of the year", "award", "draft", "conference", "division", "playoffs", "make the playoffs", "win total", "regular season wins")):
        return Classification("season_unknown", Scope.SEASON, stat, "SEASON", Support.UNRESOLVED, f"series {series} not in ontology; season-scope words in title", "heuristic")
    if stat in {"pts", "reb", "ast", "fg3m", "stl", "blk", "tov", "pra", "pr", "pa", "ra", "double_double", "triple_double"} and ":" in title:
        return Classification("player_unknown", Scope.PLAYER, stat, period, Support.UNRESOLVED, f"series {series} not in ontology; player-stat words in title", "heuristic")
    if "spread" in text or "by over" in text or "wins by" in text or "margin" in text:
        return Classification("game_unknown", Scope.GAME, "margin", period, Support.UNRESOLVED, f"series {series} not in ontology; spread words in title", "heuristic")
    if "total" in text or "combined" in text:
        return Classification("game_unknown", Scope.GAME, "total", period, Support.UNRESOLVED, f"series {series} not in ontology; total words in title", "heuristic")
    if "win" in text or "winner" in text:
        return Classification("game_unknown", Scope.GAME, "winner", period, Support.UNRESOLVED, f"series {series} not in ontology; winner words in title", "heuristic")
    return Classification("unknown", Scope.OTHER, stat, period, Support.UNRESOLVED, f"series {series} not in ontology; no heuristic matched", "none")
