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
    max_report_age_minutes: float = 1440.0,
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
    # The official report may include implicit "not listed" rows. Those
    # establish coverage, but ONLY explicit, timely REPORTED designations can
    # create an injury shock. A stale PDF or PROJECTED status is not new news.
    def current_official(p: dict) -> bool:
        age = p.get("age_minutes")
        try:
            return (p.get("source") == SRC_OFFICIAL and age is not None
                    and np.isfinite(float(age)) and 0 <= float(age) <= max_report_age_minutes)
        except (TypeError, ValueError):
            return False

    x["_official"] = [current_official(p) for p in participation]
    x["_confirmed_out"] = [p.get("status") == "CONFIRMED_OUT" for p in participation]
    x["_injury_new"] = [
        current_official(p) and not p.get("implicit", False)
        and p.get("certainty") in ("REPORTED", "CONFIRMED")
        and (p.get("status") in ("CONFIRMED_OUT", "LIKELY_OUT")
             or str(p.get("designation") or "").upper() in ("OUT", "DOUBTFUL", "QUESTIONABLE"))
        for p in participation
    ]
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
        minute_audit: dict[str, dict] = {}
        has_official_shock = False
        for team, players in g.groupby("team"):
            # Five official rows are not proof that a 15-player roster is
            # covered. The capture emits explicit or implicit rows for every
            # roster member of a submitted team; require the entire current
            # slate roster to have a fresh official observation before using
            # its injury designations as a complete counterfactual.
            if not bool(players["_official"].all()):
                continue
            prior = history[(history["team"] == team) & (history["date"] < date)]
            recent_games = (prior[["game_id", "date"]].drop_duplicates()
                            .sort_values(["date", "game_id"]).tail(10)["game_id"])
            if len(recent_games) < min_prior_games:
                continue
            prior = prior[prior["game_id"].isin(recent_games)]
            baseline = prior.groupby("pid")["minutes"].sum() / len(recent_games)
            # A 48-minute regulation game has 240 player-minutes. A mirror
            # missing 20-60 minutes cannot support a replacement counterfactual;
            # allow reasonable overtime variation but reject incomplete boxes.
            if not 220.0 <= float(baseline.sum()) <= 280.0:
                continue
            # A substantial departed player's historical minutes cannot
            # remain in the current counterfactual as a ghost rotation slot.
            # This is a trade/roster-change problem, not an injury-only
            # adjustment; fail closed rather than assign the same minutes to
            # both a departed player and an active newcomer.
            current_roster = set(players["pid"].astype(int))
            departed = baseline[~baseline.index.isin(current_roster)]
            if float(departed.sum()) > 6.0:
                continue
            # Only a new, explicit official injury change may move the
            # lineup-injury research forecast. Comparing today's projected
            # rotation against historical box minutes without this gate
            # incorrectly labels ordinary role changes, trades and model
            # noise as injury effects, even when everybody is available.
            affected = players[players["_injury_new"]]
            # The historical team rating already includes the prior rotation.
            # A new official absence may remove some of those minutes, but
            # unrelated changes in today's published rotation must NOT become
            # injury effects. Construct a counterfactual from historical
            # minutes, moving ONLY the officially lost minutes.
            lost_by_pid: dict[int, float] = {}
            for pid, p_play, confirmed_out in zip(affected["pid"], affected["p_play"], affected["_confirmed_out"]):
                pid = int(pid)
                if not np.isfinite(float(p_play)):
                    # Missing participation probability is not an injury forecast.
                    effects.clear()
                    break
                # A definitive OUT has zero participation even if a caller
                # accidentally passed the raw logistic probability.
                prob = 0.0 if confirmed_out else float(np.clip(p_play, 0.0, 1.0))
                lost = float(baseline.get(pid, 0.0)) * (1.0 - prob)
                if lost > 0:
                    lost_by_pid[pid] = lost_by_pid.get(pid, 0.0) + lost
            if len(affected) and not np.isfinite(affected["p_play"].to_numpy(dtype=float)).all():
                effects.clear()
                break
            injury_shock_minutes = sum(lost_by_pid.values())
            if injury_shock_minutes < 2.0:
                # A healthy opponent still contributes its unchanged defensive
                # rating. Only one team needs a new official injury shock.
                effects[team] = (0.0, 0.0)
                minute_audit[team] = {"lost_minutes": 0.0, "replacement_minutes": {}}
                continue
            current = baseline.copy()
            for pid, lost in lost_by_pid.items():
                current.loc[pid] = max(0.0, float(current.loc[pid]) - lost)

            # Use pretip conditional-minute forecasts to select replacements.
            # Only players on TODAY'S slate may absorb vacated minutes: the
            # historical rotation can include traded/waived players. Conversely,
            # a new active teammate with no historical minutes must be eligible.
            # This is still a counterfactual to the historical team rating:
            # only officially lost minutes are moved, never unrelated role changes.
            today = players.drop_duplicates("pid").set_index("pid")
            published = pd.to_numeric(today["min_pub"], errors="coerce").fillna(0.0).clip(lower=0.0)
            active_prob = pd.to_numeric(today["p_play"], errors="coerce").fillna(0.0).clip(lower=0.0, upper=1.0)
            # min_pub is E[minutes | plays], NOT unconditional expected
            # minutes (see nba.live.reconcile). Replacement opportunity must
            # account for P(play) exactly once. Merely gating on p > 0 would
            # assign a DOUBTFUL teammate a full active-player replacement role.
            # A low-P(play) player can absorb only P(play) times the
            # remaining conditional-minute headroom above their *historical*
            # baseline; we do not reclassify their existing baseline minutes
            # as a new injury shock.
            replacement_weights = published * active_prob
            replacement_ids = replacement_weights.index[
                (replacement_weights > 0) & (~replacement_weights.index.isin(lost_by_pid))
            ]
            # Include eligible newcomers at zero historical minutes. Do not
            # invent their pregame availability or retroactively alter baseline.
            current = current.reindex(current.index.union(replacement_ids), fill_value=0.0)
            remaining = injury_shock_minutes
            # Keep the incremental cap fixed as minutes are allocated: if
            # recomputed each pass, a probabilistic cap can be exceeded.
            capacity = ((42.0 - current).clip(lower=0.0)
                        * active_prob.reindex(current.index).fillna(0.0))
            for _ in range(12):
                eligible = capacity[(capacity > 1e-6) & capacity.index.isin(replacement_ids)]
                if eligible.empty or remaining < 1e-6:
                    break
                weights = replacement_weights.reindex(eligible.index).fillna(0.0)
                if float(weights.sum()) <= 0:
                    break
                added = np.minimum(weights / float(weights.sum()) * remaining, eligible)
                current.loc[eligible.index] += added
                capacity.loc[eligible.index] -= added
                remaining -= float(added.sum())
            if remaining > 1.0:
                # An implausibly thin historical rotation cannot support a
                # defensible replacement forecast. Fail closed for this game.
                effects.clear()
                break
            has_official_shock = True
            replacement_added = (
                current.reindex(replacement_ids, fill_value=0.0)
                - baseline.reindex(replacement_ids, fill_value=0.0)
            ).clip(lower=0.0)
            minute_audit[team] = {
                "lost_minutes": round(float(injury_shock_minutes), 3),
                "replacement_minutes": {
                    int(pid): round(float(m), 3) for pid, m in replacement_added.items()
                    if m > 1e-6
                },
            }
            all_ids = baseline.index.union(current.index)
            delta = current.reindex(all_ids, fill_value=0.0) - baseline.reindex(all_ids, fill_value=0.0)
            offense = sum(float(v) * model.offensive_absence_ppp(-int(pid))
                          for pid, v in delta.items()) / 48.0
            defense = sum(float(v) * model.defensive_absence_ppp(-int(pid))
                          for pid, v in delta.items()) / 48.0
            effects[team] = (float(offense), float(defense))
        if len(effects) != 2 or not has_official_shock:
            # No report on one side, or no actual new injury on either side:
            # fail closed rather than manufacture a role-change adjustment.
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
                          "own_lost_minutes": minute_audit[team]["lost_minutes"],
                          "own_replacement_minutes": minute_audit[team]["replacement_minutes"],
                          "model_cutoff": model.training_cutoff,
                          "asof_rule": "official pretip availability and prior-date box minutes only"})
    return shifts, audit
