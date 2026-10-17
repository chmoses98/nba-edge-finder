"""Point-in-time availability capture for the NBA (Phase 2).

Sources -> `pf_core.availability.Observation`s (kind / status / certainty vocabularies are pf_core's):

  nba_official_injury_report   the league's injury-report PDF (reuse: src/nba_edge/availability, the parser behind the
                               2025-26 archive the study used). One OFFICIAL designation per listed player and game:
                               Out->OUT, Doubtful->DOUBTFUL, Questionable->QUESTIONABLE, Probable->PROBABLE,
                               Available->ACTIVE; kind "injury", certainty REPORTED (an official team designation, not a
                               confirmed lineup). Players of a game the report covers who are NOT listed are recorded as
                               implicit ACTIVE with certainty PROJECTED (the study treated unlisted players as available;
                               82% of them played) -- never REPORTED or CONFIRMED, and never for a team whose report is
                               "NOT YET SUBMITTED".
  espn_injuries                ESPN /injuries (reuse: the data-injury-pit capture code). Aggregated news, not the official
                               designation: certainty PROJECTED. Out->OUT, Day-To-Day->QUESTIONABLE.
  espn_summary_starters        ESPN game summary starter flags before tip. ESPN does not mark them "confirmed", so the
                               certainty is PROJECTED (CONFIRMED is reserved for a source that says so).
  restriction                  a stated minutes restriction in an injury reason / comment -> kind "restriction", LIMITED.

Every observation carries source, source_url, captured_utc (when WE fetched it), source_updated_utc when the source states
one, the event id and event start, and the ESPN athlete id (`espn:<id>`). Nothing is captured for a game that has already
started. A player with no observation stays UNVERIFIED downstream (gate REVIEW); nothing is ever assumed active.
"""
from __future__ import annotations

import gzip
import json
import os
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from pf_core import availability as av

from .. import data
from .sources import Sources, iso, parse_ts

SPORT = "NBA"
SRC_OFFICIAL = "nba_official_injury_report"
SRC_ESPN_INJ = "espn_injuries"
SRC_STARTERS = "espn_summary_starters"
OFFICIAL_STATUS = {"out": "OUT", "doubtful": "DOUBTFUL", "questionable": "QUESTIONABLE", "probable": "PROBABLE",
                   "available": "ACTIVE"}
ESPN_STATUS = {"out": "OUT", "day-to-day": "QUESTIONABLE", "questionable": "QUESTIONABLE", "doubtful": "DOUBTFUL",
               "probable": "PROBABLE", "suspension": "OUT", "suspended": "OUT"}
_RESTRICTION = re.compile(
    r"(minutes?[ -]?(restriction|limit)|(restriction|limit)\w* (on )?(his |her )?minutes|limited (to|in) (\w+ )?minutes?|"
    r"(\d+)[ -]minute (restriction|limit|cap)|limited to (about |around |roughly )?(\d+) minutes|play(ing)? limited minutes|"
    r"on a (strict )?(minutes|playing[- ]time) (restriction|limit))", re.I)
_CAP = re.compile(r"(?:limited to|cap(?:ped)? (?:at|of)|restriction of|limit of)\s*(?:about |around |roughly )?(\d{1,2})\s*min|"
                  r"(\d{1,2})[ -]minute (?:restriction|limit|cap)", re.I)


# --------------------------------------------------------------------------------------------------- identity
def _canon(code: str | None) -> str | None:
    if not code:
        return None
    from nba_edge.identity.teams import TeamIdentityError, registry
    try:
        return registry().by_tricode(code).tricode
    except (KeyError, TeamIdentityError):
        return None


class RosterIndex:
    """ESPN roster rows (point-in-time captured) -> player lookups. The report prints 'Last, First'; tiers never guess:
    team + full name, unique league-wide full name, team + first initial + last name, else unmatched."""

    def __init__(self, rosters: Iterable[dict]):
        from nba_edge.identity.normalize import normalize_name
        self._norm = normalize_name
        ab2id, ab2tri = data.team_maps()
        self.rows: list[dict] = []
        self.by_pid: dict[int, dict] = {}
        self.by_team: dict[str, list[dict]] = {}
        self._team_name: dict[tuple[str, str], set[int]] = {}
        self._name: dict[str, set[int]] = {}
        self._initial: dict[tuple[str, str], set[int]] = {}
        self.tri2id = {}
        for r in rosters:
            ab = r.get("team_abbreviation")
            tri = ab2tri.get(ab) or _canon(ab)
            if not tri or r.get("espn_athlete_id") in (None, ""):
                continue
            pid = int(r["espn_athlete_id"])
            row = {"pid": pid, "name": r.get("full_name") or "", "tri": tri, "team_id": ab2id.get(ab),
                   "pos": r.get("position"), "status": r.get("status")}
            self.tri2id[tri] = row["team_id"]
            self.rows.append(row)
            self.by_pid[pid] = row
            self.by_team.setdefault(tri, []).append(row)
            k = self._norm(row["name"])
            self._team_name.setdefault((tri, k), set()).add(pid)
            self._name.setdefault(k, set()).add(pid)
            parts = k.split()
            if len(parts) >= 2:
                self._initial.setdefault((tri, f"{parts[0][0]} {parts[-1]}"), set()).add(pid)

    def resolve_report_name(self, tri: str, raw: str) -> tuple[int | None, str]:
        from nba_edge.availability.identity import report_name_to_display
        k = self._norm(report_name_to_display(raw))
        if not k:
            return None, "empty_name"
        parts = k.split()
        for method, ids in (("team_name", self._team_name.get((tri, k))), ("league_name", self._name.get(k)),
                            ("team_initial_last", self._initial.get((tri, f"{parts[0][0]} {parts[-1]}")) if len(parts) >= 2 else None)):
            if ids and len(ids) == 1:
                return next(iter(ids)), method
        return None, "unmatched"


# --------------------------------------------------------------------------------------------------- games
def select_games(schedule: Iterable[dict], now: datetime, window_hours: float, season_types=("regular",)) -> list[dict]:
    """Scheduled games that start after `now` and within the window. Games that have started are never selected."""
    out = []
    for g in schedule:
        if g.get("status") != "scheduled" or str(g.get("season_type")) not in season_types:
            continue
        start = parse_ts(g["start_time_utc"])
        if start <= now or start > now + timedelta(hours=window_hours):
            continue
        out.append({"game_id": g["game_id"], "start_utc": iso(start), "home": _canon(g["home_tricode"]) or g["home_tricode"],
                    "away": _canon(g["away_tricode"]) or g["away_tricode"], "game_date_et": g.get("game_date_et"),
                    "season_type": str(g.get("season_type"))})
    return sorted(out, key=lambda x: (x["start_utc"], x["game_id"]))


# --------------------------------------------------------------------------------------------------- builders
def _obs(g: dict, side_team: str, pid: int, name: str, kind: str, status: str, certainty: str, source: str,
         captured: str, updated: str | None, url: str | None, detail: dict) -> av.Observation:
    cap_dt = parse_ts(captured)
    if updated and parse_ts(updated) > cap_dt:           # a source clock ahead of ours: do not claim a future update
        updated = captured
    return av.Observation(sport=SPORT, event_id=g["game_id"], event_start_utc=g["start_utc"], entity_id=f"espn:{pid}",
                          entity_name=name, team=side_team, kind=kind, status=status, certainty=certainty, source=source,
                          captured_utc=captured, source_updated_utc=updated, source_url=url, detail=detail)


def restriction_detail(text: str | None) -> dict | None:
    if not text or not _RESTRICTION.search(text):
        return None
    m = _CAP.search(text)
    cap = next((int(x) for x in m.groups() if x), None) if m else None
    return {"minutes_cap": cap, "text": text[:240]}


def official_observations(rep: dict, games: list[dict], roster: RosterIndex, captured: str) -> tuple[list[av.Observation], dict]:
    """Official injury-report rows -> explicit REPORTED designations + implicit PROJECTED availability."""
    obs: list[av.Observation] = []
    st: Counter = Counter()
    key = {(g["game_date_et"], g["home"], g["away"]): g for g in games}
    updated = rep.get("last_modified_utc") or rep.get("report_time_utc")
    url = rep.get("url")
    listed: dict[str, set[str]] = {}          # game -> team tricodes with at least one player row
    submitted_missing: dict[str, set[str]] = {}   # game -> teams whose report is NOT YET SUBMITTED
    covered: set[str] = set()
    for r in rep["rows"]:
        home, away = _canon(r.get("home_tricode")), _canon(r.get("away_tricode"))
        g = key.get((r.get("game_date"), home, away))
        if g is None:
            st["rows_other_games"] += 1
            continue
        covered.add(g["game_id"])
        team = None
        if r.get("team_id") is not None:
            team = next((t for t, i in roster.tri2id.items() if i == r["team_id"]), None)
        if r["status"] == "not_yet_submitted":
            if team:
                submitted_missing.setdefault(g["game_id"], set()).add(team)
            st["not_yet_submitted_rows"] += 1
            continue
        if team not in (g["home"], g["away"]):
            st["rows_team_not_in_game"] += 1
            continue
        pid, method = roster.resolve_report_name(team, r["player_name_raw"])
        status = OFFICIAL_STATUS.get(r["status"])
        if status is None:
            st["rows_unknown_status"] += 1
            continue
        detail = {"reason": r.get("reason"), "report_time_utc": rep.get("report_time_utc"), "match": method,
                  "player_name_raw": r["player_name_raw"], "game_time_et": r.get("game_time_et")}
        if pid is None:
            st["rows_unmatched_player"] += 1
            st["unmatched:" + team] += 1
            norm = re.sub(r"[^a-z]+", "_", r["player_name_raw"].lower()).strip("_")
            obs.append(_obs(g, team, 0, r["player_name_raw"], "injury", status, "REPORTED", SRC_OFFICIAL, captured, updated, url,
                            {**detail, "unmatched": True}))
            obs[-1].entity_id = f"unmatched:{team}:{norm}"
            continue
        listed.setdefault(g["game_id"], set()).add(team)
        st["official_explicit"] += 1
        st[f"status_{status}"] += 1
        obs.append(_obs(g, team, pid, roster.by_pid[pid]["name"], "injury", status, "REPORTED", SRC_OFFICIAL, captured, updated,
                        url, detail))
        rd = restriction_detail(r.get("reason"))
        if rd:
            obs.append(_obs(g, team, pid, roster.by_pid[pid]["name"], "restriction", "LIMITED", "REPORTED", SRC_OFFICIAL,
                            captured, updated, url, {**rd, "reason": r.get("reason")}))
            st["restrictions"] += 1
    # implicit availability: unlisted roster players of a game the report covers (study: unlisted == available)
    explicit = {(o.event_id, o.entity_id) for o in obs}
    for g in games:
        if g["game_id"] not in covered:
            continue
        for team in (g["home"], g["away"]):
            if team in submitted_missing.get(g["game_id"], set()):
                st["teams_not_yet_submitted"] += 1
                continue
            for p in roster.by_team.get(team, []):
                if (g["game_id"], f"espn:{p['pid']}") in explicit:
                    continue
                obs.append(_obs(g, team, p["pid"], p["name"], "injury", "ACTIVE", "PROJECTED", SRC_OFFICIAL, captured, updated,
                                url, {"implicit": True, "basis": "not listed on the official report that covers this game",
                                      "team_listed_in_report": team in listed.get(g["game_id"], set()),
                                      "report_time_utc": rep.get("report_time_utc")}))
                st["official_implicit"] += 1
    st["games_covered"] = len(covered)
    return obs, dict(st)


def espn_injury_observations(rows: list[dict], games: list[dict], roster: RosterIndex, captured: str) -> tuple[list[av.Observation], dict]:
    obs: list[av.Observation] = []
    st: Counter = Counter()
    by_team: dict[str, list[dict]] = {}
    for g in games:
        by_team.setdefault(g["home"], []).append(g)
        by_team.setdefault(g["away"], []).append(g)
    for r in rows:
        if not r.get("nba_id"):
            st["no_athlete_id"] += 1
            continue
        pid = abs(int(r["nba_id"]))
        p = roster.by_pid.get(pid)
        status = ESPN_STATUS.get(str(r.get("status") or "").lower())
        if p is None:
            st["not_on_roster"] += 1
            continue
        if status is None:
            st["unknown_status"] += 1
            continue
        for g in by_team.get(p["tri"], []):
            detail = {"espn_status": r.get("status"), "type": r.get("type"), "comment": (r.get("short_comment") or "")[:240],
                      "entry_date_utc": r.get("entry_date_utc")}
            obs.append(_obs(g, p["tri"], pid, p["name"], "injury", status, "PROJECTED", SRC_ESPN_INJ, captured,
                            r.get("entry_date_utc"), "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries", detail))
            st[f"status_{status}"] += 1
            rd = restriction_detail(r.get("short_comment"))
            if rd:
                obs.append(_obs(g, p["tri"], pid, p["name"], "restriction", "LIMITED", "PROJECTED", SRC_ESPN_INJ, captured,
                                r.get("entry_date_utc"), None, rd))
                st["restrictions"] += 1
    return obs, dict(st)


def parse_summary_starters(payload: dict) -> dict[str, Any]:
    """Starter flags in an ESPN game summary. Returns {state, teams: {abbr: [athlete ids]}}; teams only when a side has
    exactly five flagged starters (anything else is not a lineup)."""
    comp = ((payload.get("header") or {}).get("competitions") or [{}])[0]
    state = ((comp.get("status") or {}).get("type") or {}).get("state")
    teams: dict[str, list[int]] = {}
    for tp in (payload.get("boxscore") or {}).get("players", []) or []:
        ids = []
        for grp in tp.get("statistics", []) or []:
            for a in grp.get("athletes", []) or []:
                aid = (a.get("athlete") or {}).get("id")
                if a.get("starter") and aid not in (None, ""):
                    ids.append(int(aid))
        if len(ids) == 5:
            teams[(tp.get("team") or {}).get("abbreviation")] = ids
    return {"state": state, "teams": teams, "has_box_players": bool((payload.get("boxscore") or {}).get("players"))}


def starter_observations(sources: Sources, games: list[dict], roster: RosterIndex, now: datetime,
                         lead_minutes: float = 150.0) -> tuple[list[av.Observation], dict]:
    """Pregame starters from the ESPN summary, only for games that tip within `lead_minutes` (lineups are submitted
    ~30 min before tip). PROJECTED: ESPN does not label them confirmed."""
    obs, st = [], Counter()
    ab2id, ab2tri = data.team_maps()
    for g in games:
        if parse_ts(g["start_utc"]) - now > timedelta(minutes=lead_minutes):
            st["games_too_early"] += 1
            continue
        st["games_probed"] += 1
        try:
            s = sources.summary(g["game_id"])
        except Exception as e:  # noqa: BLE001 - lineups are optional; record and continue
            st["summary_errors"] += 1
            st["error_example"] = str(e)[:120]
            continue
        info = parse_summary_starters(s["payload"])
        st[f"state_{info['state']}"] += 1
        if info["has_box_players"]:
            st["games_with_box_players_pretip"] += 1
        if info["state"] != "pre":
            st["skipped_not_pregame"] += 1
            continue
        for ab, ids in info["teams"].items():
            tri = ab2tri.get(ab) or _canon(ab)
            for pid in ids:
                p = roster.by_pid.get(pid)
                obs.append(_obs(g, tri, pid, (p or {}).get("name", ""), "starter", "STARTING", "PROJECTED", SRC_STARTERS,
                                s["fetched_at_utc"], None, s.get("url"),
                                {"basis": "espn summary boxscore starter flag before tip", "state": info["state"]}))
                st["starters"] += 1
    return obs, dict(st)


# --------------------------------------------------------------------------------------------------- fallbacks
def read_pit(pit_dir: str | None, now: datetime) -> dict[str, Any]:
    """Latest `data-injury-pit` captures (hourly official + ESPN, hash-chained) as a fallback when a live fetch fails."""
    out: dict[str, Any] = {"espn": None, "official": None}
    if not pit_dir:
        return out
    base = os.path.join(pit_dir, "injury_pit")
    for kind in ("espn", "official"):
        files = []
        d = os.path.join(base, kind)
        if os.path.isdir(d):
            for day in sorted(os.listdir(d)):
                for fn in sorted(os.listdir(os.path.join(d, day))):
                    m = re.search(r"captured_(\d{8}T\d{6}Z)", fn)
                    if m and datetime.strptime(m.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc) < now:
                        files.append(os.path.join(d, day, fn))
        if files:
            with gzip.open(files[-1], "rt") as f:
                rows = [json.loads(x) for x in f if x.strip()]
            out[kind] = {"rows": rows, "path": files[-1]}
    return out


def context_fallback(ctx_dir: str | None, kind: str, now: datetime) -> list[dict] | None:
    """Newest data-archive `context/<kind>` capture strictly before now (schedule / rosters)."""
    if not ctx_dir:
        return None
    import glob
    best = None
    for p in sorted(glob.glob(os.path.join(ctx_dir, "context", kind, "dt=*", f"context_{kind}_*.jsonl.gz"))):
        m = re.search(r"_(\d{8}T\d{6}Z)_", p)
        if m and datetime.strptime(m.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc) < now:
            best = p
    if best is None:
        return None
    with gzip.open(best, "rt") as f:
        return [json.loads(x) for x in f if x.strip()]


# --------------------------------------------------------------------------------------------------- orchestration
def load_observations(root: str, now: datetime, lookback_days: int = 3) -> list[dict]:
    days = [(now - timedelta(days=k)).strftime("%Y-%m-%d") for k in range(lookback_days + 1)]
    base = os.path.join(root, "availability", SPORT.lower())
    return av.load_snapshots(root, SPORT, [d for d in days if os.path.isdir(os.path.join(base, d))])


def coverage_report(rows: list[dict], games: list[dict], roster: RosterIndex, now: datetime) -> dict[str, Any]:
    """pf_core coverage per event (share of the players we intend to project that have any observation before the
    cut-off) plus the official-report-specific shares and capture freshness."""
    expected = {g["game_id"]: [f"espn:{p['pid']}" for t in (g["home"], g["away"]) for p in roster.by_team.get(t, [])] for g in games}
    cuts = {g["game_id"]: iso(min(now, parse_ts(g["start_utc"]))) for g in games}
    cov = av.coverage(rows, expected, cuts, iso(now))
    explicit = Counter()
    for g in games:
        lat = av.asof([r for r in rows if r["source"] == SRC_OFFICIAL and not (r.get("detail") or {}).get("implicit")],
                      cuts[g["game_id"]], g["game_id"])
        explicit[g["game_id"]] = len({k[1] for k in lat} & set(expected[g["game_id"]]))
    for ev, v in cov["events"].items():
        v["official_explicit_listed"] = explicit[ev]
        v["official_report_covers_game"] = any(r["source"] == SRC_OFFICIAL and r["event_id"] == ev for r in rows)
    n = len(games)
    cov["official_report_game_share"] = round(sum(v["official_report_covers_game"] for v in cov["events"].values()) / n, 4) if n else None
    ages = [v["newest_age_minutes"] for v in cov["events"].values() if v["newest_age_minutes"] is not None]
    cov["max_newest_age_minutes"] = max(ages) if ages else None
    return cov


def capture(sources: Sources, now: datetime, root: str, *, window_hours: float = 30.0, season_types=("regular",),
            pit_dir: str | None = None, ctx_dir: str | None = None, workdir: str | None = None) -> dict[str, Any]:
    """One availability capture: fetch, build observations for every game in the window, write ONE write-once snapshot.

    Source failures never abort the stage: the failure is recorded, the PIT / context fallbacks are tried, and whatever
    could be observed is written. If the schedule or the rosters cannot be obtained at all, the stage raises."""
    errors: list[str] = []
    pit = read_pit(pit_dir, now)
    try:
        schedule = sources.scoreboard(now, days_ahead=int(window_hours // 24) + 2)
        sched_src = "espn_scoreboard_live"
    except Exception as e:  # noqa: BLE001
        errors.append(f"scoreboard: {type(e).__name__}: {e}"[:200])
        schedule, sched_src = context_fallback(ctx_dir, "schedule", now), "data_archive_context_schedule"
    if not schedule:
        raise RuntimeError(f"no schedule available ({errors})")
    try:
        rosters = sources.rosters()
        roster_src = "espn_rosters_live"
    except Exception as e:  # noqa: BLE001
        errors.append(f"rosters: {type(e).__name__}: {e}"[:200])
        rosters, roster_src = context_fallback(ctx_dir, "rosters", now), "data_archive_context_rosters"
    if not rosters:
        raise RuntimeError(f"no rosters available ({errors})")
    games = select_games(schedule, now, window_hours, season_types)
    roster = RosterIndex(rosters)
    captured = iso(now)
    stats: dict[str, Any] = {"schedule_source": sched_src, "roster_source": roster_src, "games": len(games), "sources": {}}
    obs: list[av.Observation] = []

    rep, rep_src = None, "nba_official_live"
    try:
        rep = sources.official_report(now)
    except Exception as e:  # noqa: BLE001
        errors.append(f"official: {type(e).__name__}: {e}"[:200])
    if rep is None and pit["official"] and pit["official"]["rows"]:
        rows = pit["official"]["rows"]
        rep = {"rows": rows, "url": rows[0].get("url"), "report_time_utc": rows[0].get("report_time_utc"),
               "last_modified_utc": rows[0].get("last_modified_utc"), "fetched_at_utc": rows[0].get("fetched_at_utc"),
               "pdf_sha256": rows[0].get("pdf_sha256")}
        rep_src = "data_injury_pit_fallback"
    if rep is not None:
        o, st = official_observations(rep, games, roster, min(rep.get("fetched_at_utc") or captured, captured_cap(now, rep)))
        obs += o
        stats["sources"]["official"] = {"status": "ok", "via": rep_src, "report_time_utc": rep["report_time_utc"],
                                        "last_modified_utc": rep.get("last_modified_utc"), "pdf_sha256": rep["pdf_sha256"],
                                        "url": rep["url"], "report_rows": len(rep["rows"]), **st}
    else:
        stats["sources"]["official"] = {"status": "unavailable"}
    espn_src = "espn_live"
    try:
        er = sources.espn_injuries(now)
    except Exception as e:  # noqa: BLE001
        errors.append(f"espn injuries: {type(e).__name__}: {e}"[:200])
        er, espn_src = (pit["espn"]["rows"] if pit["espn"] else None), "data_injury_pit_fallback"
    if er is not None:
        o, st = espn_injury_observations(er, games, roster, (er[0].get("fetched_at_utc") if er else None) or captured)
        obs += o
        stats["sources"]["espn_injuries"] = {"status": "ok", "via": espn_src, "rows": len(er), **st}
    else:
        stats["sources"]["espn_injuries"] = {"status": "unavailable"}
    o, st = starter_observations(sources, games, roster, now)
    obs += o
    stats["sources"]["starters"] = {"status": "ok" if st.get("games_probed") else "not_probed", **st}

    snap = av.write_snapshot(obs, root, SPORT, captured)
    cov = coverage_report(load_observations(root, now), games, roster, now)
    by = Counter((o.source, o.kind, o.status, o.certainty) for o in obs)
    summary = {"captured_utc": captured, "snapshot": {k: snap[k] for k in ("path", "written", "rejected", "duplicate")},
               "n_observations": len(obs), "by_source_kind_status_certainty": {"|".join(k): v for k, v in sorted(by.items())},
               "coverage": cov, "errors": errors + sources.errors, **stats}
    if workdir:
        os.makedirs(workdir, exist_ok=True)
        with open(os.path.join(workdir, "live_context.json"), "w") as f:
            json.dump({"captured_utc": captured, "games": games, "rosters": rosters, "schedule_source": sched_src,
                       "roster_source": roster_src}, f, default=str)
        with open(os.path.join(workdir, "capture_summary.json"), "w") as f:
            json.dump(summary, f, indent=1, default=str)
    return summary


def captured_cap(now: datetime, rep: dict) -> str:
    """A fetch time is never later than the run's own clock plus the fetch itself; used only to keep the fallback honest."""
    return iso(now + timedelta(minutes=10))
