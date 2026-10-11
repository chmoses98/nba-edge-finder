"""Five-man lineup, stint and possession reconstruction from the full ESPN play-by-play, with per-game
certification. Pure functions over the rows written by :mod:`nba_edge.pbp.ingest`; no network.

Certification only. Nothing here fits an impact / RAPM model, and a game that fails a check is
QUARANTINED (``certified=False`` with the failing reasons), never repaired.

Period-start lineup inference (the step reconstruction from substitutions alone gets wrong)
------------------------------------------------------------------------------------------
ESPN, like the league feed, logs no substitutions between periods, so who starts periods 2+ must be
inferred. The rules, applied per team, in order:

R1  Period 1: the box score's five ``starter`` players. The game fails if the box does not name
    exactly five per team.
R2  Periods 2+: walk the period's events in source order. A player whose FIRST appearance in the
    period is (a) as the EXITING player of a substitution, or (b) as a participant in any
    non-substitution evidence event, was on court at the period start. A player whose first
    appearance is as the ENTERING player of a substitution was not. Technical fouls, ejections and
    delay-of-game events are NOT evidence (bench players and coaches can be charged with them).
R3  If R2 names fewer than five, the missing players are taken from the previous period's ENDING
    lineup, restricted to players with no appearance at all in this period -- but only when that
    candidate set has exactly as many players as are missing (rule ``carryover``). Any other count
    means the period start is ambiguous and the game fails; no candidate is ever chosen by
    minutes or any other validation target, so the minutes check below stays independent.
R4  If R2 names more than five, the game fails (``period_start_overfull``).

Checks (all computed; ``certified`` requires every CORE check)
--------------------------------------------------------------
CORE  five_on_court      every event has exactly 5 players per side after inference and substitutions.
CORE  starters_ok        the box names 5 starters per team (R1).
CORE  period_starts_ok   every period start resolved by R2/R3.
CORE  minutes_ok         every player's stint minutes within ``MINUTES_TOL`` (1.0) of the box minutes.
                         ESPN box minutes are whole minutes, so 1.0 is the rounding band; a DNP player
                         or a player absent from the box who is placed on court fails it.
CORE  score_ok           the final event's score equals the box final score.
CORE  no_offcourt        no player participates in an evidence event while reconstructed off court.
CORE  subs_consistent    no substitution removes a player who is not on court or adds one who is.
STRICT plus_minus_ok     every player's on-court point differential equals the box plus-minus exactly.
                         Free-throw points are credited to the lineup on court at the FOUL (revision 2,
                         made after the first backfill showed at-event crediting matched only ~36-42% of
                         players; the at-event count is still reported as ``..._event_rule``). This check
                         is STRICT-only, so the revision cannot change ``certified``.
STRICT possessions_ok    play-by-play possessions within ``POSS_TOL`` (5%) of the box estimate
                         0.96*(FGA + 0.44*FTA - OREB + TOV), both teams combined.
STRICT clock_ok          game clock present on every event and non-increasing within each period.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

MINUTES_TOL = 1.0
POSS_TOL = 0.05
REG_PERIOD_S = 720.0
OT_PERIOD_S = 300.0

_NON_EVIDENCE_WORDS = ("technical", "ejection", "delay", "coach's challenge", "timeout", "end period",
                       "end game", "start period")
# ESPN logs most turnovers with "turnover" in the type text; a few violations are typed without it.
# Deliberately NOT here: "Kicked Ball" (a DEFENSIVE violation; the offensive one is "Kicked Ball Turnover")
# and "Lane Violation" (either side), which would hand the ball to the wrong team.
_TURNOVER_EXACT = {"traveling", "double dribble", "discontinued dribble", "palming", "offensive goaltending",
                   "step out of bounds", "illegal assist", "inbound"}


def period_length(period: int) -> float:
    return REG_PERIOD_S if period <= 4 else OT_PERIOD_S


def _tt(e: dict[str, Any]) -> str:
    return str(e.get("type_text") or "").lower()


def is_substitution(e: dict[str, Any]) -> bool:
    return _tt(e) == "substitution"


def is_evidence(e: dict[str, Any]) -> bool:
    t = _tt(e)
    return not is_substitution(e) and not any(w in t for w in _NON_EVIDENCE_WORDS)


def is_turnover(e: dict[str, Any]) -> bool:
    t = _tt(e)
    return "turnover" in t or t in _TURNOVER_EXACT


def _pid(v: Any) -> int | None:
    if v is None:
        return None
    try:
        if v != v:  # NaN / NA
            return None
    except TypeError:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def participants(e: dict[str, Any]) -> list[int]:
    return [p for p in (_pid(e.get("p1")), _pid(e.get("p2")), _pid(e.get("p3"))) if p is not None]


def possession_team(e: dict[str, Any]) -> int | None:
    """The team that has the ball as a consequence of this event, or None if the event says nothing."""
    t = _tt(e)
    team = _pid(e.get("team_id"))
    if team is None or "technical" in t:
        return None
    if e.get("shooting_play") or t.startswith("free throw"):
        return team
    if "rebound" in t:
        return team
    if is_turnover(e):
        return team  # the turnover ends this team's possession; the opponent's next event starts one
    return None


def infer_period_start(
    events: list[dict[str, Any]], team_of: dict[int, int], team_ids: tuple[int, int],
    prev_end: dict[int, set[int]] | None,
) -> tuple[dict[int, set[int]], dict[int, str]]:
    """R2-R4 for one period. Returns ({team: starters}, {team: rule or failure reason})."""
    starters: dict[int, set[int]] = {t: set() for t in team_ids}
    entered: dict[int, set[int]] = {t: set() for t in team_ids}
    seen: dict[int, set[int]] = {t: set() for t in team_ids}
    for e in events:
        if is_substitution(e):
            inn, out = _pid(e.get("p1")), _pid(e.get("p2"))
            for pid, role in ((out, "out"), (inn, "in")):
                tm = team_of.get(pid) if pid is not None else None
                if tm is None or tm not in starters:
                    continue
                if pid not in seen[tm]:
                    (starters if role == "out" else entered)[tm].add(pid)
                    seen[tm].add(pid)
        elif is_evidence(e):
            for pid in participants(e):
                tm = team_of.get(pid)
                if tm is None or tm not in starters:
                    continue
                if pid not in seen[tm]:
                    starters[tm].add(pid)
                    seen[tm].add(pid)
    rule: dict[int, str] = {}
    for tm in team_ids:
        n = len(starters[tm])
        if n == 5:
            rule[tm] = "events"
        elif n > 5:
            rule[tm] = "fail:period_start_overfull"
        else:
            need = 5 - n
            cands = (prev_end or {}).get(tm, set()) - seen[tm]
            if len(cands) == need:
                starters[tm] |= cands
                rule[tm] = "carryover"
            else:
                rule[tm] = f"fail:period_start_ambiguous(need={need},candidates={len(cands)})"
    return starters, rule


def reconstruct_game(events: list[dict[str, Any]], box: list[dict[str, Any]], game: dict[str, Any]) -> dict[str, Any]:
    """Reconstruct lineups/stints/possessions for one game and certify it.

    ``events`` must be in source order. Returns {"checks": {...}, "certified": bool, "reasons": [...],
    "stints": [...], "player_seconds": {nba_id: s}, "metrics": {...}}.
    """
    home, away = int(game["home_team_id"]), int(game["away_team_id"])
    teams = (home, away)
    team_of = {int(b["nba_id"]): int(b["team_id"]) for b in box}
    box_min = {int(b["nba_id"]): float(b["minutes"] or 0.0) for b in box}
    box_pm = {int(b["nba_id"]): b.get("plus_minus") for b in box}
    dnp = {int(b["nba_id"]) for b in box if b.get("did_not_play")}
    reasons: list[str] = []
    m: dict[str, Any] = defaultdict(int)

    box_starters = {t: {int(b["nba_id"]) for b in box if b.get("starter") and int(b["team_id"]) == t} for t in teams}
    starters_ok = all(len(box_starters[t]) == 5 for t in teams)
    if not starters_ok:
        reasons.append("box_starters_not_5")

    by_period: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for e in events:
        p = _pid(e.get("period"))
        if p is not None:
            by_period[p].append(e)
    periods = sorted(by_period)

    secs: dict[int, float] = defaultdict(float)
    pm: dict[int, int] = defaultdict(int)
    pm_event: dict[int, int] = defaultdict(int)
    offcourt_types: list[str] = []
    stints: list[dict[str, Any]] = []
    poss = {home: 0, away: 0}
    period_rules: dict[str, str] = {}
    period_starts_ok = True
    five_ok = True
    clock_ok = True
    prev_h = prev_a = 0
    prev_end: dict[int, set[int]] | None = None
    q1_inferred_agrees = None

    for per in periods:
        evs = by_period[per]
        inferred, rule = infer_period_start(evs, team_of, teams, prev_end)
        if per == 1:
            q1_inferred_agrees = all(inferred[t] == box_starters[t] for t in teams)
            lineup = {t: set(box_starters[t]) for t in teams}
            rule = {t: "box_starters" for t in teams}
        else:
            lineup = {t: set(inferred[t]) for t in teams}
        for t in teams:
            period_rules[f"{per}:{'H' if t == home else 'A'}"] = rule[t]
            if rule[t].startswith("fail"):
                period_starts_ok = False
                reasons.append(f"P{per}{'H' if t == home else 'A'}:{rule[t][5:]}")
        plen = period_length(per)
        stint_start_clock = plen
        stint_pts = {home: 0, away: 0}
        stint_poss = {home: 0, away: 0}
        stint_first_order = _pid(evs[0].get("order")) if evs else None
        offense: int | None = None
        last_clock = plen
        foul_lineup: dict[int, set[int]] | None = None
        foul_stint: Any = None

        def close(end_clock: float, end_order: int | None, lineup=lineup, per=per) -> None:
            nonlocal stint_start_clock, stint_pts, stint_poss, stint_first_order, foul_stint
            dur = max(0.0, stint_start_clock - end_clock)
            hl, al = sorted(lineup[home]), sorted(lineup[away])
            if dur > 0 or any(stint_pts.values()) or any(stint_poss.values()):
                stints.append({
                    "game_id": game["game_id"], "period": per, "start_clock_s": stint_start_clock,
                    "end_clock_s": end_clock, "seconds": dur, "start_order": stint_first_order, "end_order": end_order,
                    **{f"home_p{i+1}": (hl[i] if i < len(hl) else None) for i in range(5)},
                    **{f"away_p{i+1}": (al[i] if i < len(al) else None) for i in range(5)},
                    "home_n": len(hl), "away_n": len(al),
                    "home_pts": stint_pts[home], "away_pts": stint_pts[away],
                    "home_poss": stint_poss[home], "away_poss": stint_poss[away],
                })
                if foul_stint == "current":
                    foul_stint = stints[-1]
            if len(hl) == 5 and len(al) == 5:
                for p in hl + al:
                    secs[p] += dur
            stint_start_clock = end_clock
            stint_pts = {home: 0, away: 0}
            stint_poss = {home: 0, away: 0}
            stint_first_order = end_order

        for e in evs:
            clk = e.get("clock_s")
            clk = None if clk is None or clk != clk else float(clk)
            if clk is None:
                clock_ok = False
                clk = last_clock
            elif clk > last_clock + 1e-6:
                clock_ok = False
                m["clock_increases"] += 1
            if is_substitution(e):
                inn, out = _pid(e.get("p1")), _pid(e.get("p2"))
                tm = team_of.get(out) if out is not None else team_of.get(inn) if inn is not None else None
                if tm is None or tm not in lineup or inn is None or out is None:
                    m["sub_unresolved"] += 1
                    reasons.append("sub_unresolved")
                else:
                    if out not in lineup[tm]:
                        m["sub_out_not_on_court"] += 1
                    if inn in lineup[tm]:
                        m["sub_in_already_on_court"] += 1
                    if team_of.get(inn) != tm:
                        m["sub_cross_team"] += 1
                    if (clk < stint_start_clock - 1e-6 or any(stint_pts.values()) or any(stint_poss.values())):
                        close(clk, _pid(e.get("order")))
                    lineup[tm].discard(out)
                    lineup[tm].add(inn)
            elif is_evidence(e):
                for pid in participants(e):
                    tm = team_of.get(pid)
                    if tm is None:
                        m["unknown_participant"] += 1
                    elif pid not in lineup[tm]:
                        m["offcourt_participation"] += 1
                        offcourt_types.append(str(e.get("type_text")))
            if not (len(lineup[home]) == 5 and len(lineup[away]) == 5):
                five_ok = False
                m["events_not_five_per_side"] += 1
            tt = _tt(e)
            if "foul" in tt and "technical" not in tt:
                foul_lineup = {t: set(lineup[t]) for t in teams}
                foul_stint = "current"
            # points: a free throw's points belong to the lineup on court when the FOUL happened (the
            # convention behind the league's plus-minus; substitutions are made between the foul and the
            # shots); every other score change belongs to the lineup on court at the event.
            h, a = _pid(e.get("home_score")), _pid(e.get("away_score"))
            if h is not None and a is not None:
                dh, da = h - prev_h, a - prev_a
                if dh or da:
                    is_ft = tt.startswith("free throw") and "technical" not in tt
                    on = foul_lineup if (is_ft and foul_lineup is not None) else lineup
                    if is_ft and isinstance(foul_stint, dict):
                        foul_stint["home_pts"] += dh
                        foul_stint["away_pts"] += da
                    else:
                        stint_pts[home] += dh
                        stint_pts[away] += da
                    for p in on[home]:
                        pm[p] += dh - da
                    for p in on[away]:
                        pm[p] += da - dh
                    for p in lineup[home]:  # at-event attribution, kept as a diagnostic
                        pm_event[p] += dh - da
                    for p in lineup[away]:
                        pm_event[p] += da - dh
                prev_h, prev_a = h, a
            # possessions: count each change of the team in control
            pt = possession_team(e)
            if pt in poss and pt != offense:
                poss[pt] += 1
                stint_poss[pt] += 1
                offense = pt
            last_clock = clk
        if abs(last_clock) > 1e-6:
            m["periods_not_ending_at_zero"] += 1
        close(0.0, _pid(evs[-1].get("order")) if evs else None)
        prev_end = {t: set(lineup[t]) for t in teams}

    # ---- reconciliation
    played = {p for p, s in secs.items() if s > 0}
    min_diffs: dict[int, float] = {}
    for p in set(box_min) | played:
        min_diffs[p] = secs.get(p, 0.0) / 60.0 - box_min.get(p, 0.0)
    worst_min = max((abs(v) for v in min_diffs.values()), default=0.0)
    minutes_ok = worst_min <= MINUTES_TOL + 1e-9 and not (played & dnp) and played <= set(box_min)
    if not minutes_ok:
        reasons.append(f"minutes_max_abs_diff={worst_min:.2f}")
    pm_diffs = [pm.get(p, 0) - int(v) for p, v in box_pm.items() if v is not None and v == v]
    pm_event_diffs = [pm_event.get(p, 0) - int(v) for p, v in box_pm.items() if v is not None and v == v]
    plus_minus_ok = bool(pm_diffs) and all(d == 0 for d in pm_diffs)
    last = events[-1] if events else {}
    score_ok = (_pid(last.get("home_score")) == _pid(game.get("home_pts"))
                and _pid(last.get("away_score")) == _pid(game.get("away_pts")))
    if not score_ok:
        reasons.append("final_score_mismatch")
    est = 0.0
    est_ok = True
    for side in ("home", "away"):
        vals = [game.get(f"{side}_{k}") for k in ("fga", "fta", "oreb", "tov")]
        if any(v is None or v != v for v in vals):
            est_ok = False
            continue
        fga, fta, oreb, tov = (float(v) for v in vals)
        est += 0.96 * (fga + 0.44 * fta - oreb + tov)
    pbp_poss = poss[home] + poss[away]
    poss_ratio = (pbp_poss / est) if est_ok and est > 0 else None
    possessions_ok = poss_ratio is not None and abs(poss_ratio - 1.0) <= POSS_TOL
    no_offcourt = m["offcourt_participation"] == 0
    subs_consistent = (m["sub_out_not_on_court"] + m["sub_in_already_on_court"] + m["sub_unresolved"]
                       + m["sub_cross_team"]) == 0
    if not five_ok:
        reasons.append("not_five_per_side")
    if not no_offcourt:
        reasons.append(f"offcourt_participation={m['offcourt_participation']}")
    if not subs_consistent:
        reasons.append("sub_inconsistent")
    checks = {
        "five_on_court": five_ok, "starters_ok": starters_ok, "period_starts_ok": period_starts_ok,
        "minutes_ok": minutes_ok, "score_ok": score_ok, "no_offcourt": no_offcourt,
        "subs_consistent": subs_consistent, "plus_minus_ok": plus_minus_ok, "possessions_ok": possessions_ok,
        "clock_ok": clock_ok,
    }
    core = all(checks[k] for k in ("five_on_court", "starters_ok", "period_starts_ok", "minutes_ok", "score_ok",
                                   "no_offcourt", "subs_consistent"))
    strict = core and all(checks[k] for k in ("plus_minus_ok", "possessions_ok", "clock_ok"))
    metrics = dict(m)
    metrics.update({
        "n_events": len(events), "n_periods": len(periods), "n_stints": len(stints),
        "minutes_max_abs_diff": round(worst_min, 4),
        "minutes_mean_signed_diff": round(sum(min_diffs.values()) / len(min_diffs), 4) if min_diffs else None,
        "players_minutes_within_tol": sum(1 for v in min_diffs.values() if abs(v) <= MINUTES_TOL + 1e-9),
        "players_compared": len(min_diffs),
        "plus_minus_players_exact": sum(1 for d in pm_diffs if d == 0), "plus_minus_players": len(pm_diffs),
        "plus_minus_max_abs_diff": max((abs(d) for d in pm_diffs), default=None),
        "plus_minus_players_exact_event_rule": sum(1 for d in pm_event_diffs if d == 0),
        "pbp_possessions_home": poss[home], "pbp_possessions_away": poss[away],
        "box_possession_estimate": round(est, 2) if est_ok else None,
        "possession_ratio": round(poss_ratio, 4) if poss_ratio is not None else None,
        "q1_inferred_matches_box_starters": q1_inferred_agrees,
        "carryover_period_starts": sum(1 for v in period_rules.values() if v == "carryover"),
        "team_stint_seconds": round(sum(s["seconds"] for s in stints), 1),
        "regulation_plus_ot_seconds": sum(period_length(p) for p in periods),
    })
    return {"game_id": game["game_id"], "checks": checks, "certified": core, "certified_strict": strict,
            "reasons": reasons, "period_rules": period_rules, "stints": stints,
            "player_seconds": dict(secs), "offcourt_event_types": offcourt_types, "player_minutes_diff": min_diffs, "metrics": metrics}
