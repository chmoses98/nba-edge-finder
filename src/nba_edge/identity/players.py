"""Player identity registry.

The canonical player key is the NBA.com person id (``nba_id``). Every other identifier (Kalshi display
name, ESPN id, Basketball-Reference slug, etc.) is an *alias* stored in ``data/identity/players.jsonl``.

Production resolution rules
- Exact alias match (source, source_key) -> nba_id : OK.
- Normalized-name match that yields exactly one *active* candidate -> OK, but recorded as a
  ``provisional`` resolution so it can be reviewed and promoted to an explicit alias.
- Zero or multiple candidates -> ``PlayerIdentityError``. Never guess.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

from nba_edge.config import REPO_ROOT
from nba_edge.identity.normalize import normalize_name

PLAYERS_JSONL = REPO_ROOT / "data" / "identity" / "players.jsonl"


class PlayerIdentityError(KeyError):
    pass


@dataclass
class PlayerRecord:
    nba_id: int
    full_name: str
    aliases: dict[str, str] = field(default_factory=dict)  # source -> key (e.g. {"kalshi": "Jayson Tatum", "espn": "4065648"})
    team_id: int | None = None
    active: bool = True
    first_seen: str | None = None
    last_seen: str | None = None


@dataclass
class Resolution:
    nba_id: int
    full_name: str
    method: str  # alias | unique_normalized
    provisional: bool


class PlayerRegistry:
    def __init__(self, records: list[PlayerRecord]):
        self.records: dict[int, PlayerRecord] = {}
        self._alias: dict[tuple[str, str], int] = {}
        self._norm: dict[str, list[int]] = defaultdict(list)
        for r in records:
            self.add(r)

    def add(self, r: PlayerRecord) -> None:
        if r.nba_id in self.records:
            existing = self.records[r.nba_id]
            existing.aliases.update(r.aliases)
            existing.active = r.active
            existing.team_id = r.team_id if r.team_id is not None else existing.team_id
            r = existing
        else:
            self.records[r.nba_id] = r
            self._norm[normalize_name(r.full_name)].append(r.nba_id)
        for src, key in r.aliases.items():
            k = (src, key)
            if k in self._alias and self._alias[k] != r.nba_id:
                raise PlayerIdentityError(f"alias {k} maps to two players: {self._alias[k]} and {r.nba_id}")
            self._alias[k] = r.nba_id

    @classmethod
    def load(cls, path: Path = PLAYERS_JSONL) -> PlayerRegistry:
        recs = []
        if path.exists():
            with path.open() as f:
                for line in f:
                    if line.strip():
                        recs.append(PlayerRecord(**json.loads(line)))
        return cls(recs)

    def save(self, path: Path = PLAYERS_JSONL) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as f:
            for r in sorted(self.records.values(), key=lambda x: x.nba_id):
                f.write(json.dumps(asdict(r), sort_keys=True) + "\n")

    def resolve(self, source: str, key: str, team_id: int | None = None) -> Resolution:
        nba_id = self._alias.get((source, key))
        if nba_id is not None:
            r = self.records[nba_id]
            return Resolution(nba_id, r.full_name, "alias", False)
        cands = [self.records[i] for i in self._norm.get(normalize_name(key), [])]
        if team_id is not None and len(cands) > 1:
            cands = [c for c in cands if c.team_id == team_id]
        active = [c for c in cands if c.active]
        if len(active) == 1:
            return Resolution(active[0].nba_id, active[0].full_name, "unique_normalized", True)
        if len(cands) == 1:
            return Resolution(cands[0].nba_id, cands[0].full_name, "unique_normalized", True)
        if not cands:
            raise PlayerIdentityError(f"no player matches {source}:{key!r}")
        raise PlayerIdentityError(f"ambiguous player {source}:{key!r}: {[c.nba_id for c in cands]}")

    def promote(self, source: str, key: str, nba_id: int) -> None:
        """Turn a provisional resolution into a durable alias."""
        if nba_id not in self.records:
            raise PlayerIdentityError(f"unknown nba_id {nba_id}")
        self.records[nba_id].aliases[source] = key
        self._alias[(source, key)] = nba_id
