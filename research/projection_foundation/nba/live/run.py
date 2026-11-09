"""NBA live shadow pipeline: `python -m nba.live.run --stage all|capture|project|publish|results|settle|score|guard --archive DIR`
(run from research/projection_foundation).

  capture   availability snapshot (official injury report PDF, ESPN injuries, ESPN starters) -> availability/nba/<date>/
  project   frozen-model challenger projections for the games in the next window, participation resolved as of now,
            archived as model_role "challenger" (+ the incumbent's own pregame output as "incumbent")
  publish   projections/nba/latest.json (+ timestamped copy), summary/nba/latest.json, runs/nba/latest.json
  results   FINAL ESPN box scores of finished games -> outcomes/ (participated=False for DNP / inactive)
  settle    prospective.settle (settle-once, corrections appended)
  score     scorecards daily (7 d) / weekly (28 d) / season + NBA segment checks; markdown to $GITHUB_STEP_SUMMARY
  paper         contemporaneous paper-trading decisions on the newest Kalshi board (nba.paper.run; offline, research only)
  paper_replay  as-of rebuilds of the T-90/T-60/T-30/T-10/LAST_VALID horizons that have passed (labelled asof_replay)
  expressions   research-only thesis-level ranking of the betting expressions (which market expresses a basketball thesis best, or NO_TRADE)
  paper_settle  settle paper decisions (authoritative Kalshi result when archived, else box score; DNP scalar semantics)
  daily         daily scorecards (ET yesterday + day before, rolling 7 days) and root-cause diagnostics
  report        weekly report(s): PRELIMINARY until complete, FINAL after; versioned, never rewritten
  ledger    verify the run did what its slot promises (games in the window => forecasts archived) and write the write-once
            ops/nba/slots/<ET date>/<HHMM>_<kind>.json record; a failed verification fails the run (nothing is committed)
  guard     pf_core.archive_guard (additions only) -- must pass before any commit

`--archive` is a checkout of the `projection-data` branch. `--dry-run` runs everything on a temporary COPY of it and writes
nothing else (live fetches are real). `--now` fixes the clock (tests / replays). Every stage is idempotent.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

from pf_core import prospective as pr

from .. import data
from . import availability as AV, forecasts as FC, incumbent as INC, ledger as LED, ops_guard, participation as PART, results as RES
from .sources import Sources, iso, parse_ts

# critical stages (forecast archiving, results, settlement, ledger) come first and are committed on their own; the research stages (paper
# trading, scorecards, weekly report) follow and may fail without ever blocking or losing the critical evidence
CRITICAL_STAGES = ["capture", "project", "publish", "results", "settle", "score", "ledger", "guard"]
RESEARCH_STAGES = ["paper", "paper_replay", "expressions", "paper_settle", "daily", "report"]
STAGES = ["capture", "project", "publish", "paper", "results", "settle", "paper_replay", "expressions", "paper_settle", "score", "daily", "report",
          "ledger", "guard"]
EXTRA_STAGES = ["incumbent"]       # not part of `all` (project already archives the incumbent); the light pregame sweep uses it
SUMMARY_JSON = data.PF_DIR / "results" / "summary.json"


def wall_clock() -> datetime:
    """The wall clock rounded UP to a whole second. Stage timestamps are whole seconds and `pf_core.availability.asof` takes only
    observations captured STRICTLY before the cut-off: with the clock truncated, a capture that finished at 18:52:42.4 was stamped
    18:52:42 and the project stage that started at 18:52:42.9 (also 18:52:42) could not see it, so every run published its own
    just-captured OUT / QUESTIONABLE players as UNVERIFIED (2026-10-19T18:52Z). Rounding up makes every stage's clock later than
    anything an earlier stage of the same run stamped; it never exceeds the real time by a full second."""
    n = datetime.now(timezone.utc)
    return n.replace(microsecond=0) + (timedelta(seconds=1) if n.microsecond else timedelta(0))


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=True, default=lambda o: o.item() if hasattr(o, "item") else str(o))


def _core(d: dict) -> str:
    d = json.loads(json.dumps(d, default=str))
    for k in ("generated_utc", "runtime_s"):
        d.pop(k, None)
    return json.dumps(d, sort_keys=True)


def warn(msg: str) -> None:
    print(f"::warning::{msg}", flush=True)


def _state(work: str) -> dict:
    p = os.path.join(work, "run_summary.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def _save_state(work: str, st: dict) -> None:
    _write_json(os.path.join(work, "run_summary.json"), st)


# --------------------------------------------------------------------------------------------------------- stages
def stage_capture(a, sources: Sources, now: datetime, work: str) -> dict:
    s = AV.capture(sources, now, a.archive, window_hours=a.window_hours, season_types=tuple(a.season_types.split(",")),
                   pit_dir=a.pit, ctx_dir=a.context, workdir=work)
    off = s["sources"]["official"]
    print(f"capture: {s['n_observations']} observations for {s['games']} games; official report {off.get('status')} "
          f"({off.get('report_time_utc')}); coverage {s['coverage']['mean_coverage']}")
    for e in s["errors"]:
        warn(f"capture source problem: {e}")
    if s["games"] and off.get("status") != "ok":
        warn("no official injury report available: players without another observation stay UNVERIFIED")
    return s


def build_slate(ctx: dict) -> dict:
    games = ctx["games"]
    ros = pd.DataFrame(ctx["rosters"])
    sch = pd.DataFrame([{"game_id": g["game_id"], "start_time_utc": g["start_utc"], "home_tricode": g["home"],
                         "away_tricode": g["away"], "game_date_et": g["game_date_et"]} for g in games])
    return {"day": min(g["game_date_et"] for g in games), "schedule": sch, "rosters": ros,
            "injuries": pd.DataFrame(columns=["team_id", "player_name_raw", "status"]), "asof": ctx["captured_utc"],
            "files": {"schedule": ctx["schedule_source"], "rosters": ctx["roster_source"]}}


def stage_project(a, now: datetime, work: str) -> dict:
    from ..project import project_slate
    ctxp = os.path.join(work, "live_context.json")
    if not os.path.exists(ctxp):
        raise RuntimeError("no live_context.json: run the capture stage first")
    ctx = json.load(open(ctxp))
    games = [g for g in ctx["games"] if parse_ts(g["start_utc"]) > now]
    st: dict[str, Any] = {"games": len(games)}
    if not games:
        print("project: no games start in the window; nothing to project")
        st["status"] = "no_games"
        # the incumbent archive still runs: a later capture of an already-projected game is a new pregame version
        st["incumbent"] = INC.archive(a.shadow, a.archive, now, season_types=tuple(a.season_types.split(",")))
        return st
    ctx["games"] = games
    roster = AV.RosterIndex(ctx["rosters"])
    rows = AV.load_observations(a.archive, now)
    avail = {}
    for g in games:
        ents = [f"espn:{p['pid']}" for t in (g["home"], g["away"]) for p in roster.by_team.get(t, [])]
        for ent, d in PART.resolve_event(rows, g["game_id"], g["start_utc"], ents, now).items():
            avail[(g["game_id"], ent)] = d
    calib = PART.load_calibration()
    # any observation used must predate the run, and the projection input timestamp is the newest capture used
    used = [d["captured_utc"] for d in avail.values() if d["captured_utc"]]
    sl = build_slate(ctx)
    sl["asof"] = max([ctx["captured_utc"]] + used) if used else ctx["captured_utc"]
    sl["asof"] = min(sl["asof"], iso(now))
    out = os.path.join(work, "projections.json")
    res = project_slate(sl, out, availability=avail, calib=calib, now_utc=iso(now))
    recs = FC.challenger_records(res)
    ar = pr.archive_forecasts(recs, a.archive, iso(now))
    try:                                      # team-points pmfs (game markets need them); a failure here is a warning, never a lost projection
        from ..paper import run as PRUN
        st["game_forecasts"] = PRUN.stage_game_forecasts(res, a.archive, now)
        for e in res.get("game_forecast_errors") or []:
            warn(f"game forecast: {e}")
    except Exception as e:  # noqa: BLE001
        st["game_forecasts"] = {"status": "ERROR", "error": f"{type(e).__name__}: {e}"[:200]}
        warn(f"game forecast archive failed: {st['game_forecasts']['error']}")
    gate_counts = Counter(p["gate"]["status"] for p in res["players"])
    part_counts = Counter(p["participation"]["status"] for p in res["players"] if p["family"] == "points")
    st.update({"status": "ok", "mode": res["mode"], "slate_date": res["slate_date"], "players": len({p["player_id"] for p in res["players"]}),
               "rows": len(res["players"]), "gate": dict(gate_counts), "participation": dict(part_counts),
               "history_through": res["history_through"], "challenger_archive": {k: ar[k] for k in ("written", "late_rejected", "invalid", "duplicates")},
               "reconciliation": [{k: r[k] for k in ("game_id", "team", "minutes_sum_raw", "points_sum_raw", "points_sum_final",
                                                     "team_points", "action", "status")} for r in res["reconciliation"]],
               "runtime_s": res["runtime_s"]})
    st["incumbent"] = INC.archive(a.shadow, a.archive, now, season_types=tuple(a.season_types.split(",")))
    print(f"project: {st['players']} players, gate {st['gate']}, archived {ar['written']} challenger forecasts "
          f"(late rejected {ar['late_rejected']}), incumbent {st['incumbent'].get('written')}")
    return st


def stage_publish(a, now: datetime, work: str) -> dict:
    root = a.archive
    st: dict[str, Any] = {}
    pj = os.path.join(work, "projections.json")
    if os.path.exists(pj):
        new = json.load(open(pj))
        latest = os.path.join(root, "projections", "nba", "latest.json")
        old = json.load(open(latest)) if os.path.exists(latest) else None
        if old is not None and _core(old) == _core(new):
            st["projections"] = "unchanged"
        else:
            _write_json(latest, new)
            _write_json(os.path.join(root, "projections", "nba", f"{now.strftime('%Y-%m-%dT%H%MZ')}.json"), new)
            st["projections"] = "written"
    else:
        st["projections"] = "none_this_run"
    sm = json.load(open(SUMMARY_JSON))
    sp = os.path.join(root, "summary", "nba", "latest.json")
    if not os.path.exists(sp) or _core(json.load(open(sp))) != _core(sm):
        _write_json(sp, sm)
        st["summary"] = "written"
    else:
        st["summary"] = "unchanged"
    run = {**_state(work), "published_utc": iso(now), "schema": "sift.nba_live_run.v1", "authority": "research_only"}
    _write_json(os.path.join(root, "runs", "nba", "latest.json"), run)
    _write_json(os.path.join(root, "runs", "nba", f"{now.strftime('%Y-%m-%dT%H%M%SZ')}.json"), run)
    print(f"publish: {st}")
    return st


def stage_results(a, sources: Sources, now: datetime) -> dict:
    s = RES.run(sources, a.archive, now)
    print(f"results: {s}")
    for e in s["errors"]:
        warn(f"results: {e}")
    return s


def stage_settle(a, now: datetime) -> dict:
    s = pr.settle(a.archive, "NBA", iso(now))
    print(f"settle: {s}")
    return s


MAX_LIVE_SKEW_H = 1.0   # a run whose clock is further than this from the wall clock is a replay: it is never audited against live rosters


def _roster_audit(archive: str, now: datetime, work: str) -> dict | None:
    """The same-slate roster audit (nba/live/roster_audit.py) of the feed this run just published, so the activation check can judge D5 on one
    document and one run instead of a manually supplied file. The audit carries the feed's digest, so it cannot vouch for any other feed, and
    it is written beside the feed (`runs/nba/roster_audit.json`, a rewritable current view) for the verifiers. Skipped for a replay (live rosters
    say nothing about recorded data) and never fatal: with no audit, D5 simply stays PENDING."""
    if abs((datetime.now(timezone.utc) - now).total_seconds()) / 3600 > MAX_LIVE_SKEW_H or os.environ.get("PF_SKIP_ROSTER_AUDIT") == "1":
        print("roster audit: skipped (replayed clock or PF_SKIP_ROSTER_AUDIT=1)")
        return None
    if not os.path.exists(os.path.join(archive, "projections", "nba", "latest.json")):
        return None
    try:
        from . import roster_audit as RA
        res = RA.run_audit(archive)
    except Exception as e:  # noqa: BLE001
        warn(f"roster audit failed: {type(e).__name__}: {e}")
        return None
    _write_json(os.path.join(archive, "runs", "nba", "roster_audit.json"), res)
    _write_json(os.path.join(work, "roster_audit.json"), res)
    print(f"roster audit: feed {res['feed_generated_utc']} · {res['genuine_roster_errors']} error(s) · sources {res['sources']['espn_rosters']}")
    return res


def stage_score(a, now: datetime, work: str) -> dict:
    ref = pr.reference_from_summary(json.load(open(SUMMARY_JSON)))
    stt = _state(work)
    cap = stt.get("capture") or {}
    capture_stats = {"availability": {"coverage": (cap.get("coverage") or {}).get("mean_coverage"),
                                      "official_report_game_share": (cap.get("coverage") or {}).get("official_report_game_share"),
                                      "max_newest_age_minutes": (cap.get("coverage") or {}).get("max_newest_age_minutes"),
                                      "official": {k: v for k, v in (cap.get("sources", {}).get("official") or {}).items()
                                                   if k in ("status", "via", "report_time_utc", "last_modified_utc", "official_explicit",
                                                            "official_implicit", "rows_unmatched_player")},
                                      "errors": cap.get("errors")},
                     "incumbent": (stt.get("project") or {}).get("incumbent"),
                     "challenger_archive": (stt.get("project") or {}).get("challenger_archive")}
    out = {}
    md = []
    for tag, days in (("daily", 7), ("weekly", 28), ("season", None)):
        card = pr.scorecard("NBA", a.archive, ref, iso(now), window_days=days, capture_stats=capture_stats)
        since = card["window"].get("since_utc")
        seg = FC.segments(a.archive, since)
        card["nba_segments"] = seg
        path = pr.write_scorecard(card, a.archive, tag=tag)
        text = pr.render_markdown(card) + FC.segments_markdown(seg)
        with open(os.path.join(os.path.dirname(path), f"{tag}.md"), "w") as f:
            f.write(text)
        md.append(text)
        out[tag] = {"settled": card["settlement"]["settled"], "alerts": [(x["family"], x["status"]) for x in card["alerts"]]}
    # activation readiness of the NBA families, judged from the archive as it now stands (read-only report; it never fails a run and
    # never promotes anything: the promotion is a decision in SIFT, see nba/live/activation_check.py)
    try:
        from . import activation_check as AC
        audit = _roster_audit(a.archive, now, work)
        rep = AC.evaluate(a.archive, now, audit)
        _write_json(os.path.join(work, "activation_readiness.json"), rep)
        out["activation"] = {"verdict": rep["verdict"], "remaining": len(rep["remaining"])}
        md.append(AC.markdown(rep))
    except Exception as e:  # noqa: BLE001
        warn(f"activation readiness report failed: {type(e).__name__}: {e}")
    summ = os.environ.get("GITHUB_STEP_SUMMARY")
    if summ:
        with open(summ, "a") as f:
            f.write(run_markdown(stt) + "\n" + "\n".join(md))
    print(f"score: {out}")
    return out


def _market_dir(a) -> str:
    return a.market or a.context or ""


def stage_paper(a, now: datetime) -> dict:
    from ..paper import run as PRUN
    s = PRUN.stage_paper(a.archive, _market_dir(a), now, window_hours=a.window_hours)
    print(f"paper: {s.get('status')} games={s.get('games')} decisions={s.get('decisions')} snapshots={s.get('snapshots')}")
    if s.get("games") and s.get("status") in ("NO_BOARD", "CHAIN_BROKEN"):
        s["problem"] = f"paper: games with forecasts are in the window but the market board is unavailable ({s['status']})"
    return s


def stage_paper_replay(a, now: datetime) -> dict:
    from ..paper import run as PRUN
    s = PRUN.stage_paper_replay(a.archive, _market_dir(a), now)
    print(f"paper_replay: games_due={s.get('games_due')} horizons={s.get('horizons_archived')} missing={s.get('missing')} decisions={s.get('decisions')}")
    return s


def stage_expressions(a, now: datetime) -> dict:
    """Rank the expressions of every thesis from the all-candidates pool at the LIVE and T-60 decision instants of games that are not final
    yet or finished within 4 days. Idempotent (record ids), research only: nothing here selects a trade."""
    from datetime import timedelta
    from ..paper import expression as EX, store as PS
    lo = (now - timedelta(days=4)).strftime("%Y-%m-%d")
    days = [d for d in PS.days(a.archive, "decisions") if d >= lo]
    by: dict[tuple, list] = {}
    for r in PS.read(a.archive, "decisions", days):
        if r.get("strategy_id") == "PF_ALL_CANDIDATES_V1" and r.get("horizon") in ("LIVE", "T-60") and r.get("side") in ("YES", "NO"):
            by.setdefault((r["game_id"], r["horizon"], r["as_of_utc"]), []).append(r)
    out = {"groups": len(by), "theses": 0, "written": 0, "duplicates": 0, "no_trade": 0}
    for key, rows in sorted(by.items()):
        res = EX.rank_theses(rows)
        w = EX.write_expression_records(a.archive, res, now)
        out["theses"] += len(res["theses"])
        out["written"] += w["written"]
        out["duplicates"] += w["duplicates"]
        out["no_trade"] += sum(1 for t in res["theses"] if t["decision"] == "NO_TRADE")
    print(f"expressions: {out}")
    return out


def stage_paper_settle(a, now: datetime) -> dict:
    from ..paper import run as PRUN
    s = PRUN.stage_paper_settle(a.archive, _market_dir(a), now)
    print(f"paper_settle: {s}")
    return s


def stage_daily(a, now: datetime) -> dict:
    from datetime import timedelta
    from zoneinfo import ZoneInfo
    from ..paper import diagnostics as DG, evaluate as EV
    et = now.astimezone(ZoneInfo("America/New_York")).date()
    out: dict[str, Any] = {"days": []}
    for k in (1, 2):                                   # yesterday and the day before (late settlements / corrections refresh the card)
        day = (et - timedelta(days=k)).isoformat()
        card = EV.scorecard(a.archive, now, window=None, day_et=day)
        EV.write(a.archive, card)
        out["days"].append({"day_et": day, "n_games": (card.get("sample") or {}).get("forecast_settlements", {}).get("n_games"),
                            "flags": card.get("insufficient_sample")})
    roll = EV.scorecard(a.archive, now, window=7)
    EV.write(a.archive, roll, daily=False)
    out["rolling7"] = {"n_games": (roll.get("sample") or {}).get("forecast_settlements", {}).get("n_games"), "flags": roll.get("insufficient_sample")}
    base = os.path.join(a.archive, "paper", "nba", "scorecards")
    for name, fn in (("root_cause", DG.root_cause), ("hypotheses", DG.ranked_hypotheses)):
        d = fn(a.archive, now, window=None)
        _write_json(os.path.join(base, f"{name}_latest.json"), d)
    from ..paper import expression as EX
    _write_json(os.path.join(base, "expressions_latest.json"), EX.evaluate_expressions(a.archive))
    # Postgame diagnostics (research only; rewritable view under paper/nba/postgame/). Never allowed to fail the daily stage.
    try:
        from ..paper import postgame as PG
        pg = PG.build(a.archive, now, window=None)
        PG.write(a.archive, pg)
        out["postgame"] = {"n_games": pg["n_games"], "findings": [(f["id"], f["status"]) for f in pg["findings"]]}
    except Exception as e:  # noqa: BLE001
        print(f"daily: postgame diagnostics failed ({type(e).__name__}: {e})")
        out["postgame"] = {"error": f"{type(e).__name__}: {e}"[:200]}
    summ = os.environ.get("GITHUB_STEP_SUMMARY")
    if summ:
        with open(summ, "a") as f:
            f.write(EV.markdown(roll) + "\n")
    print(f"daily: {out}")
    return out


def stage_report(a, now: datetime) -> dict:
    from ..paper import report as REP
    res = REP.run_due(a.archive, a.context or "", now, a.shadow)
    probs = []
    for n in REP.weeks_started(now):
        p = os.path.join(a.archive, "reports", "nba", f"week{n}", "report.json")
        if os.path.exists(p):
            rep = json.load(open(p))
            bad = [k for k, v in rep["sections"].items() if isinstance(v, dict) and v.get("status") == "SECTION_ERROR"]
            if bad:
                probs.append(f"week {n} report sections failed: {bad}")
    print(f"report: {res}")
    out = {"published": res}
    if probs:
        out["problem"] = "; ".join(probs)
    return out


def stage_ledger(a, st: dict, now: datetime) -> dict:
    kind = a.slot_kind or ("settle" if "project" not in st and "capture" not in st else "pregame")
    sid = a.slot_id or ("manual-" + now.strftime("%Y%m%dT%H%M%SZ"))
    meta = {"slot_id": sid, "slot_utc": a.slot_utc, "lateness_min": a.lateness_min, "trigger": a.trigger, "cron": a.cron,
            "started_utc": iso(parse_ts(a.started_utc)) if a.started_utc else None, "github_run_id": os.environ.get("GITHUB_RUN_ID"),
            "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"), "code_sha": os.environ.get("GITHUB_SHA"),
            "stages": [s for s in STAGES if s in st], "dry_run": bool(a.dry_run)}
    rec = LED.build_record(kind, st, meta, now)        # raises RunVerificationError: the job fails, the slot stays open
    path = LED.write(a.archive, rec)
    print(f"ledger: {rec['outcome']} -> {os.path.relpath(path, a.archive)}" + (f" warnings={rec['warnings']}" if rec["warnings"] else ""))
    return {"outcome": rec["outcome"], "path": os.path.relpath(path, a.archive), "warnings": rec["warnings"]}


def stage_guard(a) -> dict:
    bad = ops_guard.violations(a.archive)              # pf_core's immutable set plus ledger / game forecasts / paper records
    if bad:
        raise SystemExit("archive_guard: immutable archive files changed: " + ", ".join(bad))
    print("archive_guard: OK (additions only)")
    return {"ok": True}


def run_markdown(st: dict) -> str:
    cap, pj = st.get("capture") or {}, st.get("project") or {}
    lines = ["## NBA projection foundation: live run", ""]
    if cap:
        off = cap.get("sources", {}).get("official", {})
        cov = cap.get("coverage", {})
        lines += [f"- availability: {cap['n_observations']} observations for {cap['games']} games, mean coverage {cov.get('mean_coverage')}, "
                  f"newest capture age (max) {cov.get('max_newest_age_minutes')} min",
                  f"- official injury report: {off.get('status')} via {off.get('via')}, report time {off.get('report_time_utc')}, "
                  f"explicit designations {off.get('official_explicit')}, implicit-available {off.get('official_implicit')}, "
                  f"unmatched names {off.get('rows_unmatched_player', 0)}",
                  f"- ESPN injuries: {cap['sources'].get('espn_injuries', {}).get('status')}; starters: {cap['sources'].get('starters', {})}"]
        if cap.get("errors"):
            lines.append(f"- source problems: {cap['errors']}")
    if pj:
        lines += [f"- projection: {pj.get('players')} players, gate {pj.get('gate')}, participation {pj.get('participation')}",
                  f"- forecasts archived: challenger {pj.get('challenger_archive')}, incumbent {pj.get('incumbent')}"]
        rec = [r for r in pj.get("reconciliation") or [] if r["action"] != "none"]
        if rec:
            lines.append("- team reconciliation applied: " + "; ".join(
                f"{r['team']} minutes {r['minutes_sum_raw']}, points {r['points_sum_raw']}->{r['points_sum_final']} vs {r['team_points']} ({r['status']})" for r in rec))
    for k in ("results", "settle"):
        if st.get(k):
            lines.append(f"- {k}: {st[k]}")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------------------------------------- driver
def prepare_archive(archive: str, dry_run: bool) -> tuple[str, str | None]:
    """Return (archive dir to use, temp dir to clean). Dry runs work on a copy; a missing archive becomes an empty git repo."""
    if dry_run:
        tmp = tempfile.mkdtemp(prefix="pf_nba_dry_")
        dst = os.path.join(tmp, "archive")
        if os.path.isdir(archive) and os.listdir(archive):
            shutil.copytree(archive, dst, symlinks=True)
            gf = os.path.join(dst, ".git")
            if os.path.isfile(gf):                 # the copy of a worktree must not stay linked to the real checkout: it becomes its own repo below
                os.remove(gf)
        else:
            os.makedirs(dst)
        archive, cleanup = dst, tmp
    else:
        os.makedirs(archive, exist_ok=True)
        cleanup = None
    if not os.path.exists(os.path.join(archive, ".git")):        # a worktree checkout has a .git FILE; only a bare directory needs an init
        subprocess.run(["git", "init", "-q", archive], check=True)
        subprocess.run(["git", "-C", archive, "-c", "user.email=pf@local", "-c", "user.name=pf", "commit", "-q", "--allow-empty",
                        "-m", "init"], check=True)
    return archive, cleanup


def run(argv=None, sources: Sources | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", default="all", help="all | " + " | ".join(STAGES + EXTRA_STAGES) + " (comma separated allowed)")
    ap.add_argument("--archive", required=True, help="checkout of the projection-data branch")
    ap.add_argument("--workdir", default=str(data.PF_DIR / ".cache" / "live_work"))
    ap.add_argument("--shadow", default=None, help="read-only checkout of the nba-shadow-pure branch (incumbent forecasts)")
    ap.add_argument("--pit", default=None, help="read-only checkout of data-injury-pit (fallback injury captures)")
    ap.add_argument("--context", default=None, help="read-only data-archive checkout (fallback schedule / rosters)")
    ap.add_argument("--now", default=None, help="ISO timestamp; default = the wall clock at each stage")
    ap.add_argument("--dry-run", action="store_true", help="work on a temporary copy of the archive; write nothing else")
    ap.add_argument("--window-hours", type=float, default=30.0)
    ap.add_argument("--season-types", default="regular", help="comma separated: regular,preseason,playoffs")
    ap.add_argument("--slot-id", default=None, help="schedule slot this run serves (nba.live.schedule_plan); ledger key")
    ap.add_argument("--slot-kind", default=None, choices=["pregame", "settle"])
    ap.add_argument("--slot-utc", default=None)
    ap.add_argument("--lateness-min", type=int, default=None)
    ap.add_argument("--trigger", default=None, help="github event name")
    ap.add_argument("--cron", default=None)
    ap.add_argument("--started-utc", default=None)
    ap.add_argument("--market", default=None, help="data-archive checkout with kalshi/markets*, kalshi/orderbooks* (default: --context)")
    a = ap.parse_args(argv)
    sources = sources or Sources()
    stages = STAGES if a.stage == "all" else a.stage.split(",")
    for s in stages:
        if s not in STAGES + EXTRA_STAGES:
            raise SystemExit(f"unknown stage {s}")
    a.archive, cleanup = prepare_archive(a.archive, a.dry_run)
    os.makedirs(a.workdir, exist_ok=True)
    st = _state(a.workdir) if a.stage != "all" else {}
    clock = (lambda: parse_ts(a.now)) if a.now else wall_clock
    try:
        for s in stages:
            now = clock()
            if s == "capture":
                st["capture"] = stage_capture(a, sources, now, a.workdir)
            elif s == "project":
                st["project"] = stage_project(a, now, a.workdir)
            elif s == "publish":
                _save_state(a.workdir, st)
                st["publish"] = stage_publish(a, now, a.workdir)
            elif s == "results":
                st["results"] = stage_results(a, sources, now)
            elif s == "settle":
                st["settle"] = stage_settle(a, now)
            elif s == "score":
                _save_state(a.workdir, st)
                st["score"] = stage_score(a, now, a.workdir)
            elif s == "incumbent":
                st["incumbent"] = INC.archive(a.shadow, a.archive, now, season_types=tuple(a.season_types.split(",")))
                print(f"incumbent: {st['incumbent']}")
            elif s == "paper":
                st["paper"] = stage_paper(a, now)
            elif s == "paper_replay":
                st["paper_replay"] = stage_paper_replay(a, now)
            elif s == "expressions":
                st["expressions"] = stage_expressions(a, now)
            elif s == "paper_settle":
                st["paper_settle"] = stage_paper_settle(a, now)
            elif s == "daily":
                st["daily"] = stage_daily(a, now)
            elif s == "report":
                st["report"] = stage_report(a, now)
            elif s == "ledger":
                st["ledger"] = stage_ledger(a, st, now)
            elif s == "guard":
                st["guard"] = stage_guard(a)
            _save_state(a.workdir, st)
        print(json.dumps({k: (v if k in ("guard", "publish", "settle", "ledger") else "ok") for k, v in st.items()}, default=str))
        problems = [v["problem"] for v in st.values() if isinstance(v, dict) and v.get("problem")]
        if problems:                           # research stages never raise for a bad status; they are made loud here, after everything ran
            for pm in problems:
                print(f"::error::{pm}", flush=True)
            _write_json(os.path.join(a.workdir, "research_problems.json"), problems)
            return 3
        if a.dry_run:
            print(f"dry-run archive copy (discarded): {a.archive}")
    finally:
        if cleanup and os.environ.get("PF_KEEP_DRY") != "1":
            shutil.rmtree(cleanup, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(run())
