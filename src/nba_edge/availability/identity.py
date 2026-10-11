"""Map official-report names and matchups onto the repo's ESPN identities.

Players: the report prints ``Last, First`` (suffixes attached to the last name, e.g. ``Pippen Jr.,Scotty``).
Candidates come from the ESPN box-score dataset already committed for the season
(``data/history/espn/player_games_<season>.parquet``: ``nba_id = -espn_athlete_id``). Resolution is
tiered and never guesses -- a name that matches zero or several candidates at every tier stays
unmatched, and the tier that matched is recorded on the row:

1. ``game_box``          normalized full name, among that team's players in that game's box score
2. ``team_season``       normalized full name, unique among the team's players this season
3. ``season_any_team``   normalized full name, unique across the league this season (trades, two-ways)
4. ``team_initial_last`` first initial + last name, unique among the team's players this season

Games: ``AWAY@HOME`` + the report's game date -> the ESPN ``game_id`` with that home team on that ET date.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import pandas as pd

from nba_edge.identity.normalize import normalize_name
from nba_edge.identity.teams import TeamIdentityError, registry


def report_name_to_display(raw: str) -> str:
    """``'Pippen Jr.,Scotty'`` -> ``'Scotty Pippen Jr.'``; a name without a comma is returned as is."""
    s = " ".join((raw or "").split())
    if "," not in s:
        return s
    last, first = s.split(",", 1)
    return f"{first.strip()} {last.strip()}".strip()


def _initial_last(norm: str) -> str | None:
    parts = norm.split()
    return f"{parts[0][0]} {parts[-1]}" if len(parts) >= 2 else None


@dataclass
class PlayerIndex:
    by_game_team_name: dict[tuple[str, int, str], set[int]]
    by_team_name: dict[tuple[int, str], set[int]]
    by_name: dict[str, set[int]]
    by_team_initial_last: dict[tuple[int, str], set[int]]

    @classmethod
    def from_player_games(cls, pg: pd.DataFrame) -> PlayerIndex:
        g, t, n, il = defaultdict(set), defaultdict(set), defaultdict(set), defaultdict(set)
        for gid, tid, pid, name in pg[["game_id", "team_id", "nba_id", "player_name"]].itertuples(index=False):
            k = normalize_name(str(name))
            if not k:
                continue
            g[(str(gid), int(tid), k)].add(int(pid))
            t[(int(tid), k)].add(int(pid))
            n[k].add(int(pid))
            i = _initial_last(k)
            if i:
                il[(int(tid), i)].add(int(pid))
        return cls(dict(g), dict(t), dict(n), dict(il))

    def resolve(self, team_id: int | None, raw_name: str, game_id: str | None = None) -> tuple[int | None, str]:
        k = normalize_name(report_name_to_display(raw_name))
        if not k:
            return None, "empty_name"
        tiers = []
        if game_id is not None and team_id is not None:
            tiers.append(("game_box", self.by_game_team_name.get((game_id, int(team_id), k))))
        if team_id is not None:
            tiers.append(("team_season", self.by_team_name.get((int(team_id), k))))
        tiers.append(("season_any_team", self.by_name.get(k)))
        if team_id is not None and _initial_last(k):
            tiers.append(("team_initial_last", self.by_team_initial_last.get((int(team_id), _initial_last(k)))))
        ambiguous = False
        for method, ids in tiers:
            if ids and len(ids) == 1:
                return next(iter(ids)), method
            if ids and len(ids) > 1:
                ambiguous = True
        return None, "ambiguous" if ambiguous else "unmatched"


def tricode_to_team_id(code: str) -> int | None:
    try:
        return registry().by_tricode(code).team_id
    except TeamIdentityError:
        return None


def game_lookup(team_games: pd.DataFrame) -> dict[tuple[str, int], dict]:
    """(game_date_et, home_team_id) -> {game_id, start_time_utc, away_team_id, season_type}."""
    out: dict[tuple[str, int], dict] = {}
    home = team_games[team_games["home"].astype(bool)]
    for r in home.itertuples(index=False):
        out[(str(r.game_date_et), int(r.team_id))] = {
            "game_id": str(r.game_id), "start_time_utc": str(r.start_time_utc), "away_team_id": int(r.opp_team_id),
            "season_type": str(r.season_type)}
    return out
