"""Scheduling, run ledger and watchdog: the opening-night readiness fixes.

The defect these tests pin: the plan job compared the WALL-CLOCK ET hour at the moment a (late) scheduled event ran with the intended
hour, so late events concluded "nothing to do" and the workflow finished green with every job skipped. Real evidence: the scheduled
runs of 2026-10-19 (06:15Z and 17:08Z) both ended `success` with `live` and `sweep` skipped."""
import gzip
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import yaml

HERE = Path(__file__).resolve().parent
PF = HERE.parent
REPO = PF.parent.parent
sys.path.insert(0, str(PF))
from nba.live import ledger as LED, schedule_plan as SP, watchdog as WD  # noqa: E402
from pf_core import prospective as pr  # noqa: E402

WF = REPO / ".github" / "workflows" / "projection-foundation.yml"


def utc(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def plan(event, cron, now, has=lambda s, k: False, **kw):
    return SP.make_plan(event, cron, utc(now), ledger_has=has, **kw)


# ------------------------------------------------------------------------------------------------ cron table == workflow file
def test_cron_table_matches_the_workflow_exactly():
    on = yaml.safe_load(WF.read_text()).get(True)
    crons = [c["cron"] for c in on["schedule"]]
    assert sorted(crons) == sorted(SP.cron_table()), "schedule_plan.cron_table() and the workflow's cron list diverged"
    assert len(crons) == len(set(crons))


def test_every_slot_has_edt_and_est_hours_and_a_backup():
    t = SP.cron_table()
    assert "20 15,16 * 1-6,10-12 *" in t and t["20 15,16 * 1-6,10-12 *"] == "pregame"          # 11:20 ET
    assert "50 17,18 * 1-6,10-12 *" in t                                                       # 13:50 ET (the 15:00 ET opener)
    assert "20 21,22 * 1-6,10-12 *" in t and "20 1,2 * 1-6,10-12 *" in t
    assert "40 10,11 * 1-6,10-12 *" in t and t["40 10,11 * 1-6,10-12 *"] == "settle"
    assert sum(1 for k in t.values() if k == "pregame") == 12 and sum(1 for k in t.values() if k == "settle") == 2
    assert "50 0,23 * 1-6,10-12 *" in t and "20 22,23 * 1-6,10-12 *" in t                       # 19:50 and 18:20 ET slots


# ------------------------------------------------------------------------------------------------ late delivery is never a skip
@pytest.mark.parametrize("now,cron,slot", [
    ("2026-10-19T17:08:58Z", "20 15,16 * 1-6,10-12 *", "2026-10-19@1120"),    # the real 17:08Z run (13:08 EDT): old plan skipped it
    ("2026-10-19T06:15:09Z", "20 1,2 * 1-6,10-12 *", "2026-10-18@2120"),      # the real 06:15Z run: a 21:20 ET slot delivered ~5 h late
    ("2026-10-20T15:20:03Z", "20 15,16 * 1-6,10-12 *", "2026-10-20@1120"),    # on time
    ("2026-10-20T16:20:03Z", "20 15,16 * 1-6,10-12 *", "2026-10-20@1120"),    # the EDT alternate: same slot, ledger makes it a no-op
])
def test_late_events_run_the_due_slot(now, cron, slot):
    p = plan("schedule", cron, now)
    assert p.mode == "pregame" and p.slot_id == slot and p.kind == "pregame"
    assert p.stage.split(",")[0] == "capture" and "ledger" in p.stage and p.stage.endswith("guard")


def test_late_event_is_labelled_late_but_executed():
    p = plan("schedule", "20 1,2 * 1-6,10-12 *", "2026-10-19T06:15:09Z")
    assert p.mode == "pregame" and p.lateness_min > 45 and "late delivery" in p.reason


def test_settle_slot_late_delivery_still_settles():
    p = plan("schedule", "40 10,11 * 1-6,10-12 *", "2026-10-21T14:30:00Z")        # 10:30 ET, 3h50 late
    assert p.mode == "settle" and p.slot_id == "2026-10-21@0640" and p.stage == "results,settle,score,ledger,guard"


def test_duplicate_firing_is_an_explicit_valid_skip():
    done = {("2026-10-20@1120", "pregame")}
    p = plan("schedule", "20 15,16 * 1-6,10-12 *", "2026-10-20T16:20:03Z", has=lambda s, k: (s, k) in done)
    assert p.mode == "skip" and p.skip_valid and p.reason.startswith("already_done") and SP.skip_is_valid(p.reason)


def test_a_failed_slot_is_retried_by_the_backup_cron():
    # no ledger record -> the 11:45 ET backup run the same slot again
    p = plan("schedule", "45 15,16 * 1-6,10-12 *", "2026-10-20T15:46:00Z")
    assert p.mode == "pregame" and p.slot_id == "2026-10-20@1120"


def test_unknown_cron_or_event_is_never_a_silent_success():
    p = plan("schedule", "13 3 * * *", "2026-10-20T15:46:00Z")
    assert p.mode == "skip" and not p.skip_valid and not SP.skip_is_valid(p.reason)
    p = plan("issues", None, "2026-10-20T15:46:00Z")
    assert p.mode == "skip" and not p.skip_valid


def test_sweep_is_a_heartbeat_for_a_pregame_slot_that_is_due_and_not_in_the_ledger():
    # 14:05 ET on the opening day: the 13:50 slot is due; if the ledger has it the sweep stays a sweep, otherwise it runs the slot
    p = plan("schedule", SP.SWEEP_CRON, "2026-10-20T18:05:00Z")
    assert p.mode == "pregame" and p.slot_id == "2026-10-20@1350" and "heartbeat" in p.reason
    done = {("2026-10-20@1350", "pregame")}
    p = plan("schedule", SP.SWEEP_CRON, "2026-10-20T18:05:00Z", has=lambda s, k: (s, k) in done)
    assert p.mode == "sweep" and p.stage == "incumbent,guard"
    # a slot that is more than 6 h old is not resurrected by a sweep (its own crons and later slots own it)
    p = plan("schedule", SP.SWEEP_CRON, "2026-10-20T08:50:00Z")
    assert p.mode == "sweep"


def test_sweep_dispatch_and_pr_modes():
    d = plan("workflow_dispatch", None, "2026-10-20T18:05:00Z", stage_in="all")
    assert d.mode == "pregame" and d.slot_id.startswith("manual-")
    assert plan("workflow_dispatch", None, "2026-10-20T18:05:00Z", dry_run=True).mode == "dry"
    assert plan("pull_request", None, "2026-10-20T18:05:00Z").mode == "dry"


# ------------------------------------------------------------------------------------------------ DST
def test_slots_keep_their_et_clock_time_across_dst():
    # US DST ends Sunday 2026-11-01 02:00 ET and starts 2027-03-14
    assert SP.due_slot("pregame", utc("2026-10-31T15:30:00Z"))[0] == utc("2026-10-31T15:20:00Z")    # EDT: 11:20 ET = 15:20Z
    assert SP.due_slot("pregame", utc("2026-11-01T16:30:00Z"))[0] == utc("2026-11-01T16:20:00Z")    # EST: 11:20 ET = 16:20Z
    assert SP.due_slot("settle", utc("2026-11-02T12:00:00Z"))[0] == utc("2026-11-02T11:40:00Z")     # 06:40 EST
    assert SP.due_slot("settle", utc("2027-03-15T12:00:00Z"))[0] == utc("2027-03-15T10:40:00Z")     # 06:40 EDT after spring forward
    # the same cron string serves both: whichever of the two UTC hours is the intended one runs the slot, the other is a no-op
    cron = "20 15,16 * 1-6,10-12 *"
    for now, slot in (("2026-11-01T15:20:00Z", "2026-10-31@2120"), ("2026-11-01T16:20:00Z", "2026-11-01@1120")):
        p = plan("schedule", cron, now)
        assert p.mode == "pregame"
        assert p.slot_id == slot or p.slot_id == "2026-11-01@1120" or p.slot_id == "2026-10-31@2120"
    assert plan("schedule", cron, "2026-11-01T16:20:00Z").slot_id == "2026-11-01@1120"
    # 10:20 EST (15:20Z) is before the 11:20 slot, so it serves the previous evening's slot (explicit make-up, ledger decides)
    assert plan("schedule", cron, "2026-11-01T15:20:00Z").slot_id == "2026-10-31@2120"


def test_never_selects_a_future_slot():
    for h in range(0, 24):
        now = utc("2026-10-20T00:00:00Z") + timedelta(hours=h, minutes=7)
        inst, _ = SP.due_slot("pregame", now)
        assert inst <= now and (now - inst) < timedelta(hours=14)


# ------------------------------------------------------------------------------------------------ run ledger
def _st(games=3, written=300, dup=0, late=0, official="ok", errors=None):
    return {"capture": {"n_observations": 500, "errors": errors or [], "sources": {"official": {"status": official}}},
            "project": {"games": games, "status": "ok" if games else "no_games", "players": 90, "rows": 800,
                        "challenger_archive": {"written": written, "duplicates": dup, "late_rejected": late, "invalid": 0},
                        "incumbent": {"written": 10}, "gate": {"PASS": 5}}}


def test_games_in_window_but_no_forecast_fails_the_run():
    with pytest.raises(LED.RunVerificationError):
        LED.build_record("pregame", _st(games=3, written=0, dup=0), {"slot_id": "2026-10-20@1120"}, utc("2026-10-20T15:30:00Z"))


def test_project_stage_not_run_fails_the_run():
    with pytest.raises(LED.RunVerificationError):
        LED.build_record("pregame", {"capture": {}}, {"slot_id": "2026-10-20@1120"}, utc("2026-10-20T15:30:00Z"))


def test_no_games_is_recorded_as_no_games_not_as_produced():
    r = LED.build_record("pregame", _st(games=0, written=0), {"slot_id": "2026-10-20@1120"}, utc("2026-10-20T15:30:00Z"))
    assert r["outcome"] == "EXECUTED_NO_GAMES"


def test_duplicate_forecasts_count_as_present_and_missing_official_report_is_a_warning():
    r = LED.build_record("pregame", _st(written=0, dup=250, official="unavailable"), {"slot_id": "x@1"}, utc("2026-10-20T15:30:00Z"))
    assert r["outcome"] == "EXECUTED_PRODUCED" and any("official injury report" in w for w in r["warnings"])


def test_ledger_is_write_once_and_keyed_by_slot(tmp_path):
    rec = LED.build_record("pregame", _st(), {"slot_id": "2026-10-20@1120", "kind": "pregame"}, utc("2026-10-20T15:30:00Z"))
    rec["kind"] = "pregame"
    p = LED.write(str(tmp_path), rec)
    assert p.endswith("ops/nba/slots/2026-10-20/1120_pregame.json") and LED.has_slot(str(tmp_path), "2026-10-20@1120", "pregame")
    first = Path(p).read_text()
    rec2 = dict(rec, outcome="EXECUTED_NO_GAMES", finished_utc="2026-10-20T16:00:00Z")
    assert LED.write(str(tmp_path), rec2) == p and Path(p).read_text() == first            # a second writer never rewrites history
    m = dict(rec, slot_id="manual-20261020T153000Z")
    assert LED.write(str(tmp_path), m).endswith("2026-10-20/manual_153000.json")


def test_plan_cli_reads_the_ledger_from_a_git_ref(tmp_path):
    import subprocess
    r = tmp_path / "r"
    r.mkdir()
    sh = lambda *a: subprocess.run(["git", "-C", str(r), "-c", "user.email=a@b", "-c", "user.name=n", *a], check=True, capture_output=True)  # noqa: E731
    sh("init", "-q")
    (r / "ops/nba/slots/2026-10-20").mkdir(parents=True)
    (r / "ops/nba/slots/2026-10-20/1120_pregame.json").write_text("{}")
    sh("add", "-A")
    sh("commit", "-q", "-m", "x")
    has = SP._ledger_lookup("HEAD")
    import os
    cwd = os.getcwd()
    os.chdir(r)
    try:
        assert has("2026-10-20@1120", "pregame") and not has("2026-10-20@1350", "pregame") and not has("2026-10-20@1120", "settle")
    finally:
        os.chdir(cwd)


# ------------------------------------------------------------------------------------------------ watchdog
def _ctx(tmp, tips, capture_age_min=10, now=None):
    d = tmp / "ctx"
    (d / "context/schedule/dt=2026-10-19").mkdir(parents=True)
    rows = [{"game_id": f"espn:{i}", "season_type": "regular", "start_time_utc": t, "home_tricode": "AAA", "away_tricode": "BBB"}
            for i, t in enumerate(tips)]
    with gzip.open(d / "context/schedule/dt=2026-10-19/s.jsonl.gz", "wt") as f:
        f.write("\n".join(json.dumps(r) for r in rows))
    (d / "STATUS_capture.json").write_text(json.dumps({"last_capture_utc": (now - timedelta(minutes=capture_age_min)).strftime("%Y-%m-%dT%H:%M:%SZ")}))
    return str(d)


def _forecast(arch, gid, tip, gen):
    rec = {"sport": "NBA", "family": "points", "model_id": "pf-nba-points", "model_role": "challenger", "model_version": "v", "game_id": gid,
           "game_start_utc": tip, "entity_id": "espn:1", "entity_name": "A", "team": "AAA", "generated_utc": gen, "data_asof_utc": gen,
           "mean": 10.0, "lo": 0, "probs": [0.5, 0.5], "gate_status": "PASS", "readiness": "SHADOW", "participation": {}}
    pr.archive_forecasts([rec], str(arch), gen)


def test_watchdog_flags_a_game_with_no_projection_and_passes_when_present(tmp_path):
    now = utc("2026-10-20T17:00:00Z")
    arch = tmp_path / "arch"
    arch.mkdir()
    ctx = _ctx(tmp_path, ["2026-10-20T19:00:00Z"], now=now)
    rep = WD.check(str(arch), ctx, now)
    assert rep["status"] == "CRITICAL" and {f["code"] for f in rep["findings"]} >= {"MISSING_PROJECTION", "MISSED_SLOT"}
    _forecast(arch, "espn:0", "2026-10-20T19:00:00Z", "2026-10-20T15:30:00Z")
    rec = LED.build_record("pregame", _st(), {"slot_id": "2026-10-20@1120", "kind": "pregame"}, utc("2026-10-20T15:40:00Z"))
    rec["kind"] = "pregame"
    LED.write(str(arch), rec)
    rep = WD.check(str(arch), ctx, now)
    assert rep["status"] == "OK", rep["findings"]


def test_watchdog_stale_capture_and_missing_outcome(tmp_path):
    now = utc("2026-10-20T17:00:00Z")
    arch = tmp_path / "arch"
    arch.mkdir()
    ctx = _ctx(tmp_path, ["2026-10-20T19:00:00Z", "2026-10-19T19:00:00Z"], capture_age_min=200, now=now)
    _forecast(arch, "espn:0", "2026-10-20T19:00:00Z", "2026-10-20T15:30:00Z")
    _forecast(arch, "espn:1", "2026-10-19T19:00:00Z", "2026-10-19T15:30:00Z")
    rep = WD.check(str(arch), ctx, now)
    codes = {f["code"]: f["severity"] for f in rep["findings"]}
    assert codes["STALE_MARKET_CAPTURE"] == "CRITICAL" and codes["MISSING_OUTCOME"] == "WARN"        # 22 h after tip: warn, not yet critical


def test_watchdog_cli_exit_code(tmp_path):
    now = utc("2026-10-20T17:00:00Z")
    arch = tmp_path / "arch"
    arch.mkdir()
    ctx = _ctx(tmp_path, ["2026-10-20T19:00:00Z"], now=now)
    assert WD.main(["--archive", str(arch), "--context", ctx, "--now", "2026-10-20T17:00:00Z", "--out", str(tmp_path / "o.json")]) == 1
    assert json.load(open(tmp_path / "o.json"))["status"] == "CRITICAL"


# ------------------------------------------------------------------------------------------------ extended archive guard
def test_ops_guard_protects_ledger_and_new_immutable_dirs(tmp_path):
    import subprocess
    from nba.live import ops_guard
    sh = lambda *a: subprocess.run(["git", "-C", str(tmp_path), "-c", "user.email=a@b", "-c", "user.name=n", *a], check=True, capture_output=True)  # noqa: E731
    sh("init", "-q")
    for rel in ("ops/nba/slots/2026-10-20/1120_pregame.json", "paper/nba/decisions/2026-10-20/a.jsonl.gz", "reports/nba/week1/report.md"):
        f = tmp_path / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("v1")
    sh("add", "-A")
    sh("commit", "-q", "-m", "base")
    assert ops_guard.violations(str(tmp_path)) == []
    (tmp_path / "reports/nba/week1/report.md").write_text("v2")                      # rewritable view: allowed
    assert ops_guard.violations(str(tmp_path)) == []
    (tmp_path / "ops/nba/slots/2026-10-20/1120_pregame.json").write_text("v2")      # ledger rewrite: forbidden
    (tmp_path / "paper/nba/decisions/2026-10-20/a.jsonl.gz").write_text("v2")
    assert len(ops_guard.violations(str(tmp_path))) == 2
    sh("checkout", "--", ".")
    v = tmp_path / "reports/nba/week1/versions/v001.json"
    v.parent.mkdir(parents=True)
    v.write_text("v1")
    sh("add", "-A")
    sh("commit", "-q", "-m", "versions")
    assert ops_guard.violations(str(tmp_path)) == []
    v.write_text("v2")                                                                       # a published report version is write-once
    assert len(ops_guard.violations(str(tmp_path))) == 1
