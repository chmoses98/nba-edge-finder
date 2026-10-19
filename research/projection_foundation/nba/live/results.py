"""Final box scores -> archived outcomes (settlement input).

Reuses the repo's own history ingestion (`nba_edge.data.history.build_game_rows`: ESPN summary -> per-player rows with
minutes, points, rebounds, assists, threes, FGA, DNP reason, exactly what the study's history and the PURE shadow outcomes use).

Rules
  * only FINAL games (ESPN status.type.completed) are read; an in-progress game yields nothing;
  * every entity that has an archived forecast for the game gets an outcome row per family: a player who is in the box with
    minutes played has participated=True; a player who is not in the box, or is listed DNP / inactive, has participated=False
    (the forecast is then void: props settle on the conditional frame). The `participation` family is always
    participated=True with actual 1 (played) or 0 (did not), so the P(play) forecast is scored on every player;
  * games are re-read for `lookback_days` after they end, so a later stat correction produces a changed outcome that
    `prospective.settle` turns into a correction record (the original settlement is never touched);
  * nothing is written for an outcome identical to the latest archived one (re-running is a no-op).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from pf_core import prospective as pr

from .sources import Sources, iso, parse_ts

FAMILY_COL = {"minutes": "minutes", "points": "pts", "rebounds": "reb", "assists": "ast", "threes": "fg3m", "fga": "fga"}


def is_final(payload: dict) -> bool:
    comp = ((payload.get("header") or {}).get("competitions") or [{}])[0]
    t = (comp.get("status") or {}).get("type") or {}
    return bool(t.get("completed")) and t.get("state") == "post"


def box_rows(payload: dict, meta: dict) -> pd.DataFrame:
    """Player box rows; the team rows of the same summary (points, quarter scores, possessions) ride along in `.attrs["team_rows"]`."""
    from nba_edge.data.history import build_game_rows
    prow, trow = build_game_rows(payload, meta)
    df = pd.DataFrame(prow)
    df.attrs["team_rows"] = trow
    return df


def team_outcome_rows(game: dict, team_rows: list[dict], observed_utc: str, source: str) -> list[dict[str, Any]]:
    """Final team facts as `sift.team_outcome.v1` records (never invented: only what the ESPN summary carries)."""
    from nba_edge.identity.teams import TeamIdentityError, registry
    from ..paper import schema as S
    reg = registry()
    rows = []
    for t in team_rows:
        try:
            tri = reg.by_id(int(t["team_id"])).tricode
            opp = reg.by_id(int(t["opp_team_id"])).tricode
        except (TeamIdentityError, KeyError, TypeError, ValueError):
            tri = opp = None
        r = {"schema": S.TEAM_OUTCOME_SCHEMA, "game_id": game["game_id"], "game_start_utc": game["start_utc"],
             "game_date": game["start_utc"][:10], "game_date_et": game.get("game_date_et"), "team": tri, "opponent": opp,
             "team_id": int(t["team_id"]), "opp_team_id": int(t["opp_team_id"]), "home": bool(t["home"]), "final": True,
             "source": source, "observed_utc": observed_utc}
        for k in ("pts", "opp_pts", "q1", "q2", "q3", "q4", "ot_pts", "n_ot", "margin", "total", "fga", "fta", "oreb", "tov",
                  "possessions", "totals_source"):
            v = t.get(k)
            r[k] = v.item() if hasattr(v, "item") else v
        r["outcome_key"] = S.sha([r["game_id"], r["team_id"], r["pts"], r["opp_pts"], r["q1"], r["q2"], r["q3"], r["q4"], r["n_ot"],
                                  r["fga"], r["fta"], r["oreb"], r["tov"]])
        rows.append(r)
    return rows


def final_box(sources: Sources, game_id: str, meta: dict) -> tuple[bool, pd.DataFrame | None, str | None]:
    """(is_final, player box rows, source url). The live implementation reads the ESPN summary; tests replay recorded rows."""
    if hasattr(sources, "final_box_override"):
        return sources.final_box_override(game_id)
    s = sources.summary(game_id)
    if not is_final(s["payload"]):
        return False, None, s.get("url")
    return True, box_rows(s["payload"], meta), s.get("url")


def outcome_rows(game: dict, box: pd.DataFrame, entities: list[str], source: str) -> list[dict[str, Any]]:
    by = {f"espn:{abs(int(r['nba_id']))}": r for r in box.to_dict("records")}
    day = parse_ts(game["start_utc"]).strftime("%Y-%m-%d")
    rows = []
    for ent in entities:
        b = by.get(ent)
        played = bool(b and b["played"] and float(b["minutes"]) > 0)
        stats = {"minutes": float(b["minutes"]) if played else 0.0, "points": float(b["pts"]) if played else 0.0,
                 "rebounds": float(b["reb"]) if played else 0.0, "assists": float(b["ast"]) if played else 0.0,
                 "threes": float(b["fg3m"]) if played else 0.0, "fga": float(b["fga"]) if played else 0.0}
        stats["pra"] = stats["points"] + stats["rebounds"] + stats["assists"]
        base = {"game_id": game["game_id"], "entity_id": ent, "game_date": day, "game_date_et": game.get("game_date_et"),
                "final": True, "source": source, "in_box": b is not None, "dnp_reason": (b or {}).get("dnp_reason"),
                "started": bool(b and b.get("started"))}
        for fam, v in stats.items():
            rows.append({**base, "family": fam, "actual": v, "participated": played})
        # compact box facts beyond the forecast families (usage / per-minute / role diagnostics), only what the ESPN summary carries
        box = {k: (float(b[k]) if b is not None and played and b.get(k) is not None and b[k] == b[k] else None)
               for k in ("fgm", "fga", "fta", "ftm", "fg3a", "tov", "oreb", "dreb", "stl", "blk", "pf", "plus_minus")}
        rows.append({**base, "family": "participation", "actual": 1.0 if played else 0.0, "participated": True, "box": box})
    return rows


def run(sources: Sources, root: str, now: datetime, *, lookback_days: int = 3, min_age_hours: float = 2.0) -> dict[str, Any]:
    f = pr.load_forecasts(root, "NBA")
    st: dict[str, Any] = {"games_considered": 0, "games_final": 0, "games_not_final": 0, "fetch_errors": 0,
                          "outcomes_written": 0, "outcomes_unchanged": 0, "team_outcomes_written": 0, "team_outcomes_unchanged": 0,
                          "errors": []}
    team_new: dict[str, list[dict]] = {}
    if f.empty:
        return st
    f = f[(pd.to_datetime(f["game_start_utc"], utc=True) < pd.Timestamp(now) - pd.Timedelta(hours=min_age_hours)) &
          (pd.to_datetime(f["game_start_utc"], utc=True) > pd.Timestamp(now) - pd.Timedelta(days=lookback_days))]
    prev = pd.DataFrame(pr._read(root, "outcomes", "NBA"))
    last = {}
    if not prev.empty:
        p = prev.sort_values("observed_utc").groupby(["game_id", "entity_id", "family"], as_index=False).tail(1)
        last = {(a, b, c): (x, y) for a, b, c, x, y in zip(p["game_id"], p["entity_id"], p["family"], p["actual"], p["participated"])}
    new_rows: list[dict] = []
    for gid, g in f.groupby("game_id"):
        st["games_considered"] += 1
        game = {"game_id": gid, "start_utc": g["game_start_utc"].iloc[0], "game_date_et": None}
        try:
            fin, box, _url = final_box(sources, gid, {"game_id": gid, "start_time_utc": game["start_utc"]})
        except Exception as e:  # noqa: BLE001
            st["fetch_errors"] += 1
            st["errors"].append(f"{gid}: {type(e).__name__}: {e}"[:160])
            continue
        if not fin:
            st["games_not_final"] += 1
            continue
        st["games_final"] += 1
        tr = (getattr(box, "attrs", None) or {}).get("team_rows")
        if tr:
            for r in team_outcome_rows({**game, "game_date_et": None}, tr, iso(now), "espn_summary_final"):
                team_new.setdefault(r["game_date"], []).append(r)
        game["game_date_et"] = str(box["game_date_et"].iloc[0]) if len(box) and box["game_date_et"].notna().any() else None
        ents = sorted(set(g["entity_id"]))
        for r in outcome_rows(game, box, ents, "espn_summary_final"):
            k = (r["game_id"], r["entity_id"], r["family"])
            if k in last and abs(float(last[k][0]) - r["actual"]) < 1e-9 and bool(last[k][1]) == bool(r["participated"]):
                st["outcomes_unchanged"] += 1
            else:
                new_rows.append(r)
    from ..paper import store as PS
    for day, rows in team_new.items():
        w = PS.write_new(root, "team_outcomes", day, rows, "outcome_key", now)
        st["team_outcomes_written"] += w["written"]
        st["team_outcomes_unchanged"] += w["duplicates"]
    res = pr.archive_outcomes(new_rows, root, "NBA", iso(now))
    st["outcomes_written"] = res["written"]
    st["rejected_not_final"] = res["rejected_not_final"]
    return st
