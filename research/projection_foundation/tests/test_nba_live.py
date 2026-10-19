"""NBA live shadow operation: availability capture, participation, reconciliation, incumbent archive, results, settlement.

Every fixture is REAL recorded data (see tests/fixtures/nba_live/build_fixtures.py): the repo's own official injury-report PDFs
and ESPN game history, the data-archive context captures, the data-injury-pit ESPN injuries, the nba-shadow-pure incumbent
forecasts and final box scores of the 2026-10-16 preseason games, and a Kalshi board capture. Nothing is invented.
`-m slow` / PF_NBA_SLOW=1 additionally runs the frozen-model projector end to end (needs the hoopR cache, ~5 min)."""
import gzip
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

HERE = Path(__file__).resolve().parent
PF = HERE.parent
REPO = PF.parent.parent
sys.path.insert(0, str(PF))
from pf_core import archive_guard, availability as av, prospective as pr  # noqa: E402
from nba.live import availability as AV, forecasts as FC, incumbent as INC, kalshi_report as KR, participation as PART  # noqa: E402
from nba.live import reconcile as REC, results as RES, run as RUN  # noqa: E402
from nba.live.sources import RecordedSources, iso  # noqa: E402

FIX = HERE / "fixtures" / "nba_live"


def utc(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


@pytest.fixture(scope="module")
def pre():
    return json.load(gzip.open(FIX / "preseason_20261016.json.gz", "rt"))


# ------------------------------------------------------------------------------------------------ official report
@pytest.fixture(scope="module")
def official_jan15():
    """The real 2026-01-15 17:30 ET official report PDF (repo fixture) + the repo's ESPN game history for that day."""
    pytest.importorskip("pypdf")
    from nba_edge.availability.official_report import parse_report_pdf
    from nba_edge.timeutil import ET
    pdf = (REPO / "tests" / "fixtures" / "injury_reports" / "Injury-Report_2026-01-15_05_30PM.pdf").read_bytes()
    rows, meta = parse_report_pdf(pdf, datetime(2026, 1, 15, 17, 30, tzinfo=ET))
    tg = pd.read_parquet(REPO / "data/history/espn/team_games_2025-26.parquet")
    pg = pd.read_parquet(REPO / "data/history/espn/player_games_2025-26.parquet")
    from nba_edge.identity.teams import registry
    reg = registry()
    day = tg[(tg["game_date_et"] == "2026-01-15") & tg["home"]]
    games = []
    for r in day.itertuples():
        games.append({"game_id": r.game_id, "start_time_utc": r.start_time_utc, "game_date_et": r.game_date_et, "status": "scheduled",
                      "season_type": "regular", "home_tricode": reg.by_id(int(r.team_id)).tricode, "away_tricode": reg.by_id(int(r.opp_team_id)).tricode})
    teams = {g["home_tricode"] for g in games} | {g["away_tricode"] for g in games}
    tid = {reg.by_tricode(t).team_id: t for t in teams}
    prior = pg[(pg["game_date_et"] < "2026-01-15") & (pg["game_date_et"] >= "2025-12-31") & pg["team_id"].isin(tid) & pg["played"]]
    rosters = [{"team_abbreviation": tid[int(r.team_id)], "espn_athlete_id": str(-int(r.nba_id)), "full_name": r.player_name,
                "position": "G"} for r in prior.drop_duplicates(["team_id", "nba_id"]).itertuples()]
    return {"rows": rows, "meta": meta, "games": games, "rosters": rosters}


def test_official_report_to_observations_and_resolution(official_jan15, tmp_path):
    o = official_jan15
    now = utc("2026-01-15T22:46:00Z")            # the 17:30 ET report was uploaded ~22:30Z; the 14:00 ET MEM@ORL game is long gone
    rep = {"rows": o["rows"], "url": "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-01-15_05_30PM.pdf",
           "report_time_utc": "2026-01-15T22:30:00Z", "last_modified_utc": "2026-01-15T22:30:05Z",
           "fetched_at_utc": "2026-01-15T22:45:30Z", "pdf_sha256": "x"}
    src = RecordedSources(scoreboard=o["games"], rosters=o["rosters"], espn_injuries=[], official=rep)
    root = str(tmp_path)
    s = AV.capture(src, now, root, window_hours=12, workdir=str(tmp_path / "w"))
    off = s["sources"]["official"]
    assert s["games"] == 8 and off["status"] == "ok"                       # 9 games that day, one already started (never captured)
    assert off["official_explicit"] > 20 and off["official_implicit"] > 50
    assert off["status_OUT"] > 0 and off["games_covered"] >= 7
    rows = av.load_snapshots(root, "NBA")
    assert rows and all(not av.observation_from_dict(r).validate() for r in rows)
    started = {g["game_id"] for g in o["games"] if utc(g["start_time_utc"]) <= now}
    assert started and not ({r["event_id"] for r in rows} & started)       # nothing is captured for a game that has started
    explicit = [r for r in rows if r["source"] == AV.SRC_OFFICIAL and not r["detail"].get("implicit") and r["kind"] == "injury"]
    assert {r["certainty"] for r in explicit} == {"REPORTED"}
    assert {r["certainty"] for r in rows if r["detail"].get("implicit")} == {"PROJECTED"}
    assert all(r["source_updated_utc"] <= r["captured_utc"] for r in rows)
    # resolution: an OUT designation is CONFIRMED_OUT (REPORTED strength), unlisted players are LIKELY_ACTIVE (implicit)
    g = next(x for x in s["coverage"]["events"] if s["coverage"]["events"][x]["official_explicit_listed"] > 0)
    ev = next(gm for gm in AV.select_games(o["games"], now, 12) if gm["game_id"] == g)
    ents = [f"espn:{p['espn_athlete_id']}" for p in o["rosters"] if p["team_abbreviation"] in (ev["home"], ev["away"])]
    res = PART.resolve_event(rows, g, ev["start_utc"], ents, now)
    st = pd.Series({e: d["status"] for e, d in res.items()})
    assert (st == "CONFIRMED_OUT").any() and (st == "LIKELY_ACTIVE").any()
    out = next(e for e, d in res.items() if d["status"] == "CONFIRMED_OUT")
    assert res[out]["certainty"] == "REPORTED" and res[out]["designation"] == "OUT" and not res[out]["implicit"]
    imp = next(e for e, d in res.items() if d["implicit"])
    assert res[imp]["certainty"] == "PROJECTED" and res[imp]["status"] == "LIKELY_ACTIVE"
    # a player the roster does not contain is UNVERIFIED, never active
    assert PART.resolve_event(rows, g, ev["start_utc"], ["espn:999999999"], now)["espn:999999999"]["status"] == "UNVERIFIED"
    # as-of: a cut-off before the capture sees nothing
    assert all(d["status"] == "UNVERIFIED" for d in PART.resolve_event(rows, g, ev["start_utc"], ents, utc("2026-01-15T22:00:00Z")).values())
    # coverage + freshness are computed for every game
    assert s["coverage"]["mean_coverage"] > 0.9 and s["coverage"]["max_newest_age_minutes"] < 5


def test_calibrated_p_play_orders_by_designation():
    cal = PART.load_calibration()
    cls = ["OUT", "DOUBTFUL", "QUESTIONABLE", "AVAILABLE", "PROBABLE", None, "STARTER_CONFIRMED"]
    p = PART.calibrated_p_play(np.full(len(cls), 0.7), cls, cal)
    assert p[0] < 0.01 and p[1] < 0.1 and p[0] < p[1] < p[2] < p[3] < p[4]
    assert p[5] == 0.7 and p[6] == PART.CONFIRMED_STARTER_P                  # no observation: the raw hurdle is kept
    assert cal["study_split"]["brier_hurdle"] == 0.132 and cal["study_split"]["brier_hurdle_plus_report"] == 0.0868


def _obs(**kw):
    base = dict(sport="NBA", event_id="espn:1", event_start_utc="2026-10-20T23:00:00Z", entity_id="espn:7", entity_name="X", team="PHI",
                kind="injury", status="OUT", certainty="PROJECTED", source=AV.SRC_ESPN_INJ, captured_utc="2026-10-20T20:00:00Z",
                source_updated_utc="2026-10-19T12:00:00Z")
    base.update(kw)
    return av.Observation(**base).__dict__


def test_participation_precedence_and_conflicts():
    now = utc("2026-10-20T21:00:00Z")
    off = lambda st, **k: _obs(source=AV.SRC_OFFICIAL, certainty="REPORTED", status=st, source_updated_utc="2026-10-20T19:30:00Z", **k)  # noqa: E731
    imp = _obs(source=AV.SRC_OFFICIAL, certainty="PROJECTED", status="ACTIVE", source_updated_utc="2026-10-20T19:30:00Z", detail={"implicit": True})
    r = lambda rows: PART.resolve_event(rows, "espn:1", "2026-10-20T23:00:00Z", ["espn:7"], now)["espn:7"]  # noqa: E731
    assert r([off("OUT")])["status"] == "CONFIRMED_OUT" and r([off("OUT")])["certainty"] == "REPORTED"
    assert r([off("QUESTIONABLE")])["status"] == "UNCERTAIN"
    assert r([_obs()])["status"] == "LIKELY_OUT" and r([_obs()])["certainty"] == "PROJECTED"      # aggregator OUT is never CONFIRMED
    # ESPN OUT older than the official report that says AVAILABLE -> official wins
    assert r([off("ACTIVE"), _obs()])["status"] == "LIKELY_ACTIVE"
    # ESPN OUT newer than an official AVAILABLE -> the newer news wins
    assert r([off("ACTIVE"), _obs(source_updated_utc="2026-10-20T20:30:00Z")])["status"] == "LIKELY_OUT"
    # ESPN OUT that the covering official report does not list (implicit) -> uncertain, with the conflict spelled out
    c = r([imp, _obs()])
    assert c["status"] == "UNCERTAIN" and any("conflict" in x for x in c["reasons"])
    assert r([imp])["status"] == "LIKELY_ACTIVE" and r([imp])["implicit"]
    assert r([])["status"] == "UNVERIFIED"
    # a PROJECTED starter alone is LIKELY_ACTIVE, never CONFIRMED_ACTIVE
    st = _obs(kind="starter", status="STARTING", source=AV.SRC_STARTERS)
    assert r([st])["status"] == "LIKELY_ACTIVE"
    st["certainty"] = "CONFIRMED"
    assert r([st])["status"] == "CONFIRMED_ACTIVE" and r([st])["_class"] == "STARTER_CONFIRMED"
    # observations at/after the event start or the run time are not used
    assert r([_obs(captured_utc="2026-10-20T21:30:00Z")])["status"] == "UNVERIFIED"
    assert PART.resolve_event([_obs(captured_utc="2026-10-20T20:00:00Z")], "espn:1", "2026-10-20T19:00:00Z", ["espn:7"], now)["espn:7"]["status"] == "UNVERIFIED"


def test_restriction_and_starter_parsing():
    d = AV.restriction_detail("Embiid will be on a minutes restriction, limited to about 24 minutes, per the team.")
    assert d and d["minutes_cap"] == 24
    assert AV.restriction_detail("Injury/Illness - Left Knee; Soreness") is None
    payload = {"header": {"competitions": [{"status": {"type": {"state": "pre"}}}]},
               "boxscore": {"players": [{"team": {"abbreviation": "PHI"}, "statistics": [{"athletes": [
                   {"athlete": {"id": str(i)}, "starter": i < 5} for i in range(10)]}]},
                   {"team": {"abbreviation": "BOS"}, "statistics": [{"athletes": [{"athlete": {"id": str(i)}, "starter": i < 4} for i in range(10)]}]}]}}
    info = AV.parse_summary_starters(payload)
    assert info["state"] == "pre" and list(info["teams"]) == ["PHI"]       # BOS has 4 flags: not a lineup


# ------------------------------------------------------------------------------------------------ reconciliation
def test_reconciliation_normalises_incoherent_roster_and_leaves_coherent_ones(tmp_path):
    p = json.load(open(PF / "results" / "projections_latest.json"))       # the real 2026-10-20 forward projection
    import re
    rows = []
    for r in p["players"]:
        if r["family"] == "points":
            pp = float(re.search(r"P\(play\) ([0-9.]+)", r["adjustments"][0]).group(1))
            rows.append({"game_id": r["game_id"], "team": r["team"], "p_play": pp, "minutes": r["opportunity"]["mean"], "pts": r["mean"]})
    df = pd.DataFrame(rows)
    team = {(g["game_id"], t["team"]): t["mean"] for g in p["games"] for t in g["teams"]}
    sc, recs = REC.reconcile(df, team)
    phi = next(r for r in recs if r["team"] == "PHI")
    assert phi["points_sum_raw"] > 165 and phi["minutes_sum_raw"] > 340            # the documented 171 vs 112 incoherence
    assert abs(phi["ratio_final"] - 1) <= 0.15 and phi["status"] in ("PASS", "REVIEW") and phi["action"] != "none"
    assert phi["minutes_sum_final"] < 270
    assert (sc["min_scale"] <= 1.0001).all()
    # a coherent team is untouched
    ok = pd.DataFrame({"game_id": "espn:1", "team": "PHI", "p_play": 1.0,
                       "minutes": [34, 32, 30, 28, 26, 24, 22, 18, 14, 13.5]})
    ok["pts"] = ok["minutes"] * 0.5
    t = (ok["p_play"] * ok["pts"]).sum()
    sc2, rec2 = REC.reconcile(ok, {(ok["game_id"].iloc[0], "PHI"): t * 1.02})
    assert rec2[0]["action"] == "none" and rec2[0]["status"] == "PASS" and (sc2 == 1.0).all().all()
    # cannot be reconciled: minutes 4x the budget, beyond the scale limits -> BLOCK stays
    bad = pd.concat([ok, ok], ignore_index=True)
    bad["minutes"] = 40.0
    bad["p_play"] = 0.9
    bad["pts"] = 20.0
    _, rec3 = REC.reconcile(bad, {(bad["game_id"].iloc[0], "PHI"): 112.0})
    assert rec3[0]["status"] == "BLOCK"
    # no team projection -> never silently PASS
    _, rec4 = REC.reconcile(ok, {})
    assert rec4[0]["status"] == "REVIEW"


# ------------------------------------------------------------------------------------------------ incumbent / archive / settle
def _incumbent_records(pre):
    ab2id, _ = __import__("nba.data", fromlist=["x"]).team_maps()
    return INC.to_forecast_records(pre["incumbent"], {i: t for t, i in ab2id.items()})


def test_incumbent_archive_is_idempotent_unmodified_and_pregame_only(pre, tmp_path):
    shadow = tmp_path / "shadow"
    d = shadow / "projections" / "sim_rotation" / "conditional" / "dt=2026-10-16"
    d.mkdir(parents=True)
    with gzip.open(d / "projections_sim_rotation_conditional_x.jsonl.gz", "wt") as f:
        f.write("\n".join(json.dumps(r) for r in pre["incumbent"]))
    before = subprocess.check_output(["sha256sum", str(d / "projections_sim_rotation_conditional_x.jsonl.gz")]).split()[0]
    root = str(tmp_path / "arch")
    now = utc("2026-10-16T22:00:00Z")
    a = INC.archive(str(shadow), root, now, season_types=("preseason",))
    assert a["written"] == 595 + 119 and a["late_rejected"] == 0 and a["games"] == 4      # 5 stats x 119 players + 119 participation
    a2 = INC.archive(str(shadow), root, now + timedelta(minutes=5), season_types=("preseason",))
    assert a2["written"] == 0 and a2["duplicates"] == 714
    a3 = INC.archive(str(shadow), root, utc("2026-10-16T23:00:01Z"), season_types=("preseason",))
    assert a3.get("shadow_rows_read", 0) == 0 and a3["written"] == 0                        # tipped: nothing is read or archived
    assert subprocess.check_output(["sha256sum", str(d / "projections_sim_rotation_conditional_x.jsonl.gz")]).split()[0] == before
    f = pr.load_forecasts(root, "NBA")
    inc = f[f["family"] == "points"].iloc[0]
    assert inc["model_role"] == "incumbent" and list(inc["probs"]) == [] and inc["generated_utc"] == "2026-10-16T21:53:10Z"
    src = next(r for r in pre["incumbent"] if r["statistic"] == "points" and f"espn:{abs(int(r['player_id']))}" == inc["entity_id"]
               and r["game_id"] == inc["game_id"])
    assert abs(inc["mean"] - src["projection"]["mean"]) < 1e-9                              # values are exactly the incumbent's own


def _challenger_like(pre):
    """Challenger records produced by the REAL `FC.challenger_records` from a projection-shaped dict whose pmfs are Poisson
    around the incumbent's own mean (only the archive / settlement mechanics are under test here, not model quality)."""
    from pf_core import dists
    players, games = [], {}
    for r in pre["incumbent"]:
        if r["statistic"] not in ("points", "minutes"):
            continue
        mu = max(r["projection"]["mean"], 0.5) if r["statistic"] == "points" else r["projection"]["mean"] * 0.9
        d = dists.poisson(np.array([mu]), K=70)
        games[r["game_id"]] = {"game_id": r["game_id"], "start_utc": r["kickoff"]}
        out = r["participation_probability"] is not None and r["participation_probability"] < 0.02
        players.append({"player_id": f"espn:{abs(int(r['player_id']))}", "name": "x", "team": "T", "game_id": r["game_id"],
                        "family": r["statistic"], "mean": float(d.mean[0]), "readiness": "READY",
                        "gate": {"status": "BLOCK" if out else "PASS"}, "data_asof_utc": "2026-10-16T21:50:00Z",
                        "participation": {"status": "CONFIRMED_OUT" if out else "LIKELY_ACTIVE", "certainty": "REPORTED" if out else "PROJECTED",
                                          "source": "x", "captured_utc": "2026-10-16T21:00:00Z", "p_play": 0.01 if out else 0.8},
                        "_pmf": {"lo": 0, "probs": d.P[0]}, "_tags": {"new_team": False, "reconciled": "none", "minutes_model": "E"}})
    res = {"generated_utc": "2026-10-16T21:56:00Z", "games": list(games.values()), "players": players,
           "model": {"version": "t"}}
    return FC.challenger_records(res)


def test_full_loop_archive_results_settle_score_idempotent_with_correction(pre, tmp_path):
    root = str(tmp_path / "arch")
    subprocess.run(["git", "init", "-q", root], check=True)
    subprocess.run(["git", "-C", root, "-c", "user.email=a@b", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "i"], check=True)
    now = utc("2026-10-16T21:57:00Z")
    ch = _challenger_like(pre)
    a = pr.archive_forecasts(ch, root, iso(now))
    assert a["written"] == len(ch) and a["late_rejected"] == 0
    assert pr.archive_forecasts(ch, root, iso(now + timedelta(minutes=1)))["duplicates"] == len(ch)           # idempotent
    late = [dict(r, generated_utc="2026-10-16T23:00:00Z") for r in ch[:3]]
    assert pr.archive_forecasts(late, root, iso(now))["late_rejected"] == 3                                    # never at/after the start
    ab2id, ab2tri = __import__("nba.data", fromlist=["x"]).team_maps()
    INC.archive  # incumbent via records (the store reader is covered above)
    pr.archive_forecasts(_incumbent_records(pre), root, iso(now))
    boxes = {}
    for b in pre["boxes"]:
        boxes.setdefault(b["game_id"], []).append(b)
    src = RecordedSources(final_boxes=boxes)
    after = utc("2026-10-17T09:00:00Z")
    r1 = RES.run(src, root, after)
    assert r1["games_final"] == 4 and r1["outcomes_written"] > 0 and r1["fetch_errors"] == 0
    r2 = RES.run(src, root, after + timedelta(hours=1))
    assert r2["outcomes_written"] == 0 and r2["outcomes_unchanged"] > 0                                       # re-run is a no-op
    s1 = pr.settle(root, "NBA", iso(after))
    assert s1["settled"] > 0 and s1["void"] > 0                                                               # DNP / inactive -> void
    s2 = pr.settle(root, "NBA", iso(after + timedelta(hours=1)))
    assert s2["settled"] == 0 and s2["corrections"] == 0 and s2["already_settled"] > 0
    st = pr.load_settlements(root, "NBA")
    assert st["forecast_id"].is_unique
    # participation family: scored on every player, never void
    part = st[st["family"] == "participation"]
    assert len(part) > 0 and not part["void"].any() and set(part["actual"]) <= {0.0, 1.0}
    # DNP players: participated False in the outcome -> void stat forecasts
    box_dnp = {(b["game_id"], f"espn:{abs(b['nba_id'])}") for b in pre["boxes"] if not b["played"]}
    sd = st[(st["family"] == "points") & st.apply(lambda r: (r["game_id"], r["entity_id"]) in box_dnp, axis=1)]
    assert len(sd) and sd["void"].all()
    # a player forecast but absent from the box score (inactive) -> participated False as well
    assert (st[(st["family"] == "minutes") & st["void"]]).shape[0] >= len(sd)
    # a stat correction becomes ONE correction record; the original settlement is untouched
    gid = next(iter(boxes))
    fixed = [dict(b) for b in boxes[gid]]
    victim = next(b for b in fixed if b["played"])
    victim["pts"] = victim["pts"] + 3
    src2 = RecordedSources(final_boxes={**boxes, gid: fixed})
    r3 = RES.run(src2, root, after + timedelta(days=1))
    assert r3["outcomes_written"] >= 1
    c1 = pr.settle(root, "NBA", iso(after + timedelta(days=1)))
    assert c1["corrections"] >= 1
    c2 = pr.settle(root, "NBA", iso(after + timedelta(days=1, hours=1)))
    assert c2["corrections"] == 0
    st2 = pr.load_settlements(root, "NBA")
    orig = st[(st["entity_id"] == f"espn:{abs(victim['nba_id'])}") & (st["game_id"] == gid) & (st["family"] == "points")]
    now_ = st2[(st2["entity_id"] == f"espn:{abs(victim['nba_id'])}") & (st2["game_id"] == gid) & (st2["family"] == "points")]
    assert list(orig["actual"]) == list(now_["actual"])
    # scorecards + NBA segments render; the archive guard is clean (additions only)
    card = pr.scorecard("NBA", root, {"points": {"mae": 4.5, "crps": 3.0}}, iso(after + timedelta(days=2)))
    seg = FC.segments(root)
    assert {"participation_brier", "minutes_by_model"} <= set(seg)
    assert {r["model_role"] for r in seg["participation_brier"]["overall"]} == {"challenger", "incumbent"}
    assert "Participation Brier" in FC.segments_markdown(seg) and card["families"]
    assert archive_guard.violations(root) == []
    assert sum(1 for fam in card["families"] if fam.get("paired")) >= 1                                       # paired challenger vs incumbent


def test_in_progress_games_are_never_read_for_outcomes(pre, tmp_path):
    root = str(tmp_path / "arch")
    pr.archive_forecasts(_challenger_like(pre), root, "2026-10-16T21:57:00Z")
    r = RES.run(RecordedSources(final_boxes={}), root, utc("2026-10-17T03:00:00Z"))
    assert r["games_final"] == 0 and r["games_not_final"] == 4 and r["outcomes_written"] == 0
    assert pr.settle(root, "NBA", "2026-10-17T03:00:00Z")["settled"] == 0


def test_trim_pmf_keeps_mean_and_mass():
    from pf_core import dists
    d = dists.negbin(np.array([6.0]), 0.2, 80)
    lo, p = FC.trim_pmf(0, d.P[0])
    assert abs(sum(p) - 1) < 1e-5 and len(p) <= 45
    assert abs(sum((lo + i) * x for i, x in enumerate(p)) - d.mean[0]) < 1e-3


# ------------------------------------------------------------------------------------------------ kalshi (reporting only)
def test_kalshi_placeholders_are_never_executable():
    d = json.load(gzip.open(FIX / "kalshi_props_20261017T000200Z.json.gz", "rt"))
    rows = d["rows"]
    s = KR.summarize_board(rows, "2026-10-20")
    assert s["n_prop_markets"] == 369 and s["regular_season_total"]["markets"] == 369
    cls = s["regular_season_total"]["classes"]
    assert cls.get("PLACEHOLDER", 0) > 100 and cls.get("TWO_SIDED", 0) > 0
    for r in rows:
        c = KR.classify_quote(r)
        q = KR.executable_quote(r)
        if c in (KR.PLACEHOLDER, KR.NO_QUOTE, KR.ONE_SIDED, KR.INVALID):
            assert q is None
        if q:
            assert 0 < q["bid"] < q["ask"] < 1 and q["bid_size"] > 0 and q["ask_size"] > 0
    assert KR.executable_quote({"yes_bid_dollars": "0.0000", "yes_ask_dollars": "0.9800", "yes_bid_size_fp": "5", "yes_ask_size_fp": "5"}) is None
    assert KR.classify_quote({"yes_bid_dollars": "0.0200", "yes_ask_dollars": "0.9800"}) == KR.PLACEHOLDER
    assert KR.classify_quote({"yes_bid_dollars": "0.4000", "yes_ask_dollars": "0.4500"}) == KR.TWO_SIDED
    assert KR.event_date("KXNBAPTS-26OCT20PHINYK") == "2026-10-20"


# ------------------------------------------------------------------------------------------------ workflow + CLI
def test_workflow_shape():
    wf = yaml.safe_load((REPO / ".github" / "workflows" / "projection-foundation.yml").read_text())
    on = wf.get(True) or wf.get("on")
    assert "schedule" in on and "workflow_dispatch" in on and "pull_request" in on
    assert "dry_run" in on["workflow_dispatch"]["inputs"]
    paths = on["pull_request"]["paths"]
    assert any(p.startswith("research/projection_foundation") for p in paths) and ".github/workflows/projection-foundation.yml" in paths
    text = (REPO / ".github" / "workflows" / "projection-foundation.yml").read_text()
    assert "set -euo pipefail" in text and "ops_guard" in text and "--dry-run" in text
    for j in wf["jobs"].values():
        assert "timeout-minutes" in j
    jobs = wf["jobs"]
    assert all("group" in (j.get("concurrency") or {}) for n, j in jobs.items() if n not in ("plan", "outcome"))
    dry = jobs["dry-run"]
    dry_text = yaml.safe_dump(dry)
    assert dry["permissions"] == {"contents": "read"} and "commit_push" not in dry_text and "git push" not in dry_text
    assert "--dry-run" in dry_text and "--stage all" in dry_text
    assert jobs["live"]["permissions"] == {"contents": "write", "issues": "write"} and "commit_push" in yaml.safe_dump(jobs["live"])
    assert jobs["live"]["concurrency"]["group"] == "projection-foundation-nba" and not jobs["live"]["concurrency"]["cancel-in-progress"]
    plan_run = " ".join(st.get("run", "") for st in jobs["plan"]["steps"])
    assert "nba.live.schedule_plan" in plan_run and "date +%H" not in plan_run   # no wall-clock-hour decision (the delayed-run skip bug)


def test_dry_run_never_touches_the_archive(pre, tmp_path):
    arch = tmp_path / "arch"
    arch.mkdir()
    (arch / "keep.txt").write_text("x")
    src = RecordedSources(scoreboard=[dict(s, start_time_utc="2026-10-17T23:00:00Z") for s in pre["schedule"]], rosters=pre["rosters"],
                          espn_injuries=pre["espn_injuries"])
    before = sorted(p.name for p in arch.rglob("*"))
    rc = RUN.run(["--stage", "capture", "--archive", str(arch), "--dry-run", "--now", "2026-10-17T21:00:00Z", "--season-types", "preseason",
                  "--workdir", str(tmp_path / "w")], sources=src)
    assert rc == 0 and sorted(p.name for p in arch.rglob("*")) == before
