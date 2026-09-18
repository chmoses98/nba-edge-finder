"""Team identity registry backed by data/identity/teams.csv (30 NBA teams, NBA.com team IDs)."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from nba_edge.config import REPO_ROOT

TEAMS_CSV = REPO_ROOT / "data" / "identity" / "teams.csv"


class TeamIdentityError(KeyError):
    pass


@dataclass(frozen=True)
class Team:
    team_id: int
    tricode: str
    name: str
    city: str
    nickname: str
    conference: str
    division: str
    alt_tricodes: tuple[str, ...]


@dataclass(frozen=True)
class TeamRegistry:
    teams: tuple[Team, ...]

    @classmethod
    def load(cls, path: Path = TEAMS_CSV) -> TeamRegistry:
        rows = []
        with path.open() as f:
            for r in csv.DictReader(f):
                rows.append(
                    Team(
                        team_id=int(r["team_id"]), tricode=r["tricode"], name=r["name"], city=r["city"], nickname=r["nickname"],
                        conference=r["conference"], division=r["division"],
                        alt_tricodes=tuple(x for x in (r.get("alt_tricodes") or "").split("|") if x),
                    )
                )
        return cls(tuple(rows))

    @property
    def tricodes(self) -> set[str]:
        return {t.tricode for t in self.teams}

    def by_tricode(self, code: str) -> Team:
        c = (code or "").upper().strip()
        for t in self.teams:
            if t.tricode == c or c in t.alt_tricodes:
                return t
        raise TeamIdentityError(f"unknown team tricode: {code!r}")

    def by_id(self, team_id: int) -> Team:
        for t in self.teams:
            if t.team_id == int(team_id):
                return t
        raise TeamIdentityError(f"unknown team id: {team_id}")

    def by_name(self, text: str) -> Team:
        """Match a full name, city, or nickname (case-insensitive). Exactly one match required."""
        s = (text or "").strip().lower()
        hits = [t for t in self.teams if s in {t.name.lower(), t.city.lower(), t.nickname.lower()}]
        if s in {"la", "los angeles"}:
            raise TeamIdentityError(f"ambiguous team text: {text!r} (LAL vs LAC)")
        if len(hits) != 1:
            raise TeamIdentityError(f"team text {text!r} matched {len(hits)} teams")
        return hits[0]


@lru_cache(maxsize=1)
def registry() -> TeamRegistry:
    return TeamRegistry.load()
