"""Team box statistics beyond what ``team_games`` stores, built from the stored player box scores.

``team_games`` carries points, possessions, fga, fta, oreb and tov per team-game. Shooting makes, threes, rebounds, assists, steals,
blocks and fouls exist only in ``player_games``; this module sums them per (game, team) and joins the opponent's totals so a team row can
state shooting efficiency, rebounding rates and what it allowed, all raw (not opponent-adjusted)."""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any

PLAYER_SUMS = ("fgm", "fga", "fg3m", "fg3a", "ftm", "fta", "oreb", "dreb", "reb", "ast", "stl", "blk", "tov", "pf")


def player_totals(player_rows: Iterable[dict[str, Any]]) -> dict[tuple[str, int], dict[str, float]]:
    """(game_id, team_id) -> summed player counting stats (players who played; DNP rows carry zeros or nulls and add nothing)."""
    out: dict[tuple[str, int], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for r in player_rows:
        key = (r["game_id"], int(r["team_id"]))
        for c in PLAYER_SUMS:
            v = r.get(c)
            if v is not None and v == v:
                out[key][c] += float(v)
    return {k: dict(v) for k, v in out.items()}


def enrich_team_games(team_rows: Iterable[dict[str, Any]], player_rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Each team row plus fgm, fg3m, fg3a, ftm, reb, dreb, ast, stl, blk, pf and the opponent's ``opp_*`` equivalents.

    A row whose box score has no player lines (the player table is missing that game) gets ``box_complete = False`` and no player-derived
    fields: aggregates over such rows are skipped rather than treated as zeros."""
    totals = player_totals(player_rows)
    rows = [dict(r) for r in team_rows]
    for r in rows:
        mine = totals.get((r["game_id"], int(r["team_id"])))
        theirs = totals.get((r["game_id"], int(r["opp_team_id"])))
        ok = bool(mine and theirs and mine.get("fga", 0) > 0 and theirs.get("fga", 0) > 0)
        r["box_complete"] = ok
        if not ok:
            continue
        for c in ("fgm", "fg3m", "fg3a", "ftm", "reb", "dreb", "ast", "stl", "blk", "pf"):
            r[c] = mine.get(c, 0.0)
        for c in ("fgm", "fga", "fg3m", "fg3a", "ftm", "fta", "oreb", "dreb", "reb", "tov"):
            r[f"opp_{c}"] = theirs.get(c, 0.0)
    return rows


def _sum(rows: list[dict], key: str) -> float:
    return float(sum(r[key] for r in rows))


def box_rates(rows: list[dict[str, Any]]) -> dict[str, float | None]:
    """Season or window rates from enriched rows (raw). Uses only rows with a complete box. Returns None where the denominator is 0."""
    g = [r for r in rows if r.get("box_complete")]
    if not g:
        return {k: None for k in ("efg", "opp_efg", "fg3_rate", "fg3_pct", "tov_pct", "opp_tov_pct", "orb_pct", "drb_pct", "ft_rate", "opp_ft_rate",
                                  "ast_pct", "stl_per100", "blk_per100", "pf_per100")}
    fga, fgm, f3m, fta = _sum(g, "fga"), _sum(g, "fgm"), _sum(g, "fg3m"), _sum(g, "fta")
    ofga, ofgm, of3m, ofta = _sum(g, "opp_fga"), _sum(g, "opp_fgm"), _sum(g, "opp_fg3m"), _sum(g, "opp_fta")
    poss, oposs = _sum(g, "possessions"), _sum(g, "possessions")
    oreb, dreb, ooreb, odreb = _sum(g, "oreb"), _sum(g, "dreb"), _sum(g, "opp_oreb"), _sum(g, "opp_dreb")
    tov, otov = _sum(g, "tov"), _sum(g, "opp_tov")

    def ratio(n: float, d: float) -> float | None:
        return round(n / d, 5) if d > 0 else None

    return {
        "efg": ratio(fgm + 0.5 * f3m, fga), "opp_efg": ratio(ofgm + 0.5 * of3m, ofga),
        "fg3_rate": ratio(_sum(g, "fg3a"), fga), "fg3_pct": ratio(f3m, _sum(g, "fg3a")),
        "tov_pct": ratio(100 * tov, poss), "opp_tov_pct": ratio(100 * otov, oposs),
        "orb_pct": ratio(oreb, oreb + odreb), "drb_pct": ratio(dreb, dreb + ooreb),
        "ft_rate": ratio(fta, fga), "opp_ft_rate": ratio(ofta, ofga),
        "ast_pct": ratio(_sum(g, "ast"), fgm), "stl_per100": ratio(100 * _sum(g, "stl"), poss),
        "blk_per100": ratio(100 * _sum(g, "blk"), poss), "pf_per100": ratio(100 * _sum(g, "pf"), poss),
    }
