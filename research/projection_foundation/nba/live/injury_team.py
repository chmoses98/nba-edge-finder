"""Research-only live NBA team-efficiency response to point-in-time injuries.

Uses certified-stint player effects (fitted separately), the actual pretip
participation probabilities, and historical box minutes STRICTLY before tip.
A team rating already includes the historical roster: only changes from that
baseline may be added, to avoid double-counting. No future box outcomes enter.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .availability import SRC_OFFICIAL


def lineup_team_deltas(
    slate: pd.DataFrame,
    history: pd.DataFrame,
    participation: list[dict],
    model,
    *,
    min_prior_games: int = 5,
    max_points: float = 12.0,
    pace_by_game: dict | None = None,
) -> tuple[dict[tuple[int, str], float], list[dict]]:
    """Return additive team-points shifts keyed (game_id, team), plus diagnostics.

    Slate is one row per pregame player with pid, game_id, team, opp, date,
    p_play and min_pub. Model IDs are negative ESPN athlete IDs; live IDs are
    positive ESPN athlete IDs. Official report coverage is required on both
    teams. Unverified status never silently becomes a confirmed absence.
    """
    if len(slate) != len(participation):
        raise ValueError("participation/slate length mismatch")
    if not model or not getattr(model, "n_players", 0):
        raise ValueError("fitted certified-lineup model required")
    x = slate.copy()
    x["_official"] = [p.get("source") == SRC_OFFICIAL for p in participation]
    if "date" not in x or "date" not in history:
        raise ValueError("point-in-time dates required")
    history = history.copy()
    history["date"] = pd.to_datetime(history["date"])
    shifts: dict[tuple[int, str], float] = {}
    audit: list[dict] = []
    for gid, g in x.groupby("game_id", sort=False):
        if len(g["team"].unique()) != 2:
            continue
        date = pd.Timestamp(g["date"].iloc[0])
        if model.training_cutoff >= str(date.date()):
            raise ValueError("lineup model fitted on or after projection date")
        effects: dict[str, tuple[float, float]] = {}
        for team, players in g.groupby("team"):
            if players["_official"].sum() < 5:
                continue
            prior = history[(history["team"] == team) & (history["date"] < date)]
            recent_games = (prior[["game_id", "date"]].drop_duplicates()
                            .sort_values(["date", "game_id"]).tail(10)["game_id"])
            if len(recent_games) < min_prior_games:
                continue
            prior = prior[prior["game_id"].isin(recent_games)]
            baseline = prior.groupby("pid")["minutes"].sum() / len(recent_games)
            if baseline.sum() < 180:
                continue
            current = (players.set_index("pid")["p_play"].astype(float)
                       * players.set_index("pid")["min_pub"].astype(float))
            if current.sum() <= 0:
                continue
            # Preserve expected 240 regulation minutes; a known confirmed OUT
            # already has exactly zero P(play) before this calculation.
            current *= 240.0 / current.sum()
            all_ids = baseline.index.union(current.index)
            delta = current.reindex(all_ids, fill_value=0.0) - baseline.reindex(all_ids, fill_value=0.0)
            offense = sum(float(v) * model.offensive_absence_ppp(-int(pid))
                          for pid, v in delta.items()) / 48.0
            defense = sum(float(v) * model.defensive_absence_ppp(-int(pid))
                          for pid, v in delta.items()) / 48.0
            effects[team] = (float(offense), float(defense))
        if len(effects) != 2:
            continue
        for team, players in g.groupby("team"):
            opp = str(players["opp"].iloc[0])
            if opp not in effects:
                continue
            pace = float((pace_by_game or {}).get((gid, team), 98.0))
            delta_ppp = effects[team][0] - effects[opp][1]
            pts = float(np.clip(delta_ppp * pace, -max_points, max_points))
            shifts[(gid, team)] = pts
            audit.append({"game_id": int(gid), "team": team, "opponent": opp,
                          "off_delta_ppp": effects[team][0],
                          "opp_def_delta_ppp": effects[opp][1],
                          "points_delta": pts, "pace": pace,
                          "model_cutoff": model.training_cutoff,
                          "asof_rule": "official pretip availability and prior-date box minutes only"})
    return shifts, audit
