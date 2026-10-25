"""Issue #53: the idle gate, the self-renewing seal chain and the dead-man monitor (owner approval of 2026-10-22).

The chain is tested with an injected runner and clock: no network, no sleeping. What is checked is the CONTROL FLOW that the reliability argument rests on - the cheap gate, when
the expensive steps run, that dry runs publish nothing, that the publish token reaches only the publisher, one successor, retry after a failed publish, and the monitor's findings."""
import argparse
import gzip
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PF = HERE.parent
sys.path.insert(0, str(PF))
from nba.paper import seal_chain as SC, seal_monitor as SM, seal_windows as SW  # noqa: E402

UTC = timezone.utc
GAME = {"game_id": "espn:401909088", "season_type": "regular", "game_date_et": "2026-10-20", "start_time_utc": "2026-10-20T19:00:00Z", "home_tricode": "DET", "away_tricode": "BOS",
        "status": "scheduled", "_observed_at_utc": "2026-10-20T12:00:00Z"}


def t(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def make_ctx(root, rows=(GAME,), stamp="20261020T120000Z"):
    d = Path(root) / "context/schedule/dt=2026-10-20"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"context_schedule_{stamp}_x.jsonl.gz").write_bytes(gzip.compress("\n".join(json.dumps(r) for r in rows).encode()))
    return str(root)


def ledger(tmp_path, enabled="2026-10-20T00:00:00Z", sealed=(), missed=()):
    d = tmp_path / "ledger"
    d.mkdir()
    if enabled:
        (d / "ENABLED_UTC").write_text(enabled + "\n")
    for g in sealed:
        (d / "seals/2026-10-20").mkdir(parents=True, exist_ok=True)
        (d / f"seals/2026-10-20/{SW.gid_file(g)}__abc.json").write_text("{}")
    for g in missed:
        (d / "missed").mkdir(exist_ok=True)
        (d / f"missed/{SW.gid_file(g)}.json").write_text("{}")
    return str(d)


STUDY = SW.load_study()


# ------------------------------------------------------------------------------------------------------------------ gate
def test_the_gate_is_standard_library_only(tmp_path):
    """Run as a script with numpy / pandas made unimportable: an idle poll needs no install."""
    ctx = make_ctx(tmp_path / "ctx")
    led = ledger(tmp_path)
    code = ("import sys, runpy\nsys.modules['numpy']=None; sys.modules['pandas']=None; sys.modules['scipy']=None\nsys.argv=['x','gate','--context',%r,'--seals',%r,'--now','2026-10-20T18:20:00Z']\n"
            "runpy.run_path(%r, run_name='__main__')" % (ctx, led, str(PF / "nba/paper/seal_windows.py")))
    r = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True)
    assert r.returncode == 0 and "active=true" in r.stdout and "due=true" in r.stdout, r.stderr
    r = subprocess.run([sys.executable, "-I", str(PF / "nba/paper/seal_windows.py"), "gate", "--context", ctx, "--seals", led, "--now", "2026-10-20T05:00:00Z"], capture_output=True, text=True)
    assert "active=false" in r.stdout and "due=false" in r.stdout and "next_window_opens_utc=" in r.stdout


@pytest.mark.parametrize("hhmm,active,due,watch", [("11:59", False, False, False), ("12:10", True, False, False), ("18:09", True, False, False), ("18:10", True, True, False),
                                                   ("18:50", True, True, False), ("18:51", True, False, True), ("19:05", True, False, True)])
def test_gate_reflects_the_window_and_the_horizon(tmp_path, hhmm, active, due, watch):
    ctx = make_ctx(tmp_path / "c")
    led = ledger(tmp_path)
    g = SW.gate(ctx, led, t(f"2026-10-20T{hhmm}:00Z"), STUDY, horizon_h=6)
    assert (g["active"], g["due"], g["needs_watch"]) == (active, due, watch)


def test_a_sealed_or_missed_or_pre_enable_game_needs_no_chain(tmp_path):
    ctx = make_ctx(tmp_path / "c")
    for i, kw in enumerate(({"sealed": ["espn:401909088"]}, {"missed": ["espn:401909088"]}, {"enabled": "2026-10-20T18:30:00Z"})):
        sub = tmp_path / f"l{i}"
        sub.mkdir()
        led = ledger(sub, **kw)
        g = SW.gate(ctx, led, t("2026-10-20T19:30:00Z"), STUDY, horizon_h=6)
        assert g["active"] is False and not g["due"] and not g["needs_watch"], kw


def test_the_gate_and_the_sealer_share_one_implementation(tmp_path):
    from nba.paper import exec_seal as SL
    assert SL.plan is not SW.plan and SL.window is SW.window and SL.schedule_games is SW.schedule_games and SL.game_state is SW.game_state and SL.list_sealed is SW.list_sealed
    ctx = make_ctx(tmp_path / "c")
    led = ledger(tmp_path)
    for hhmm in ("17:00", "18:09", "18:10", "18:50", "18:51", "20:00"):
        now = t(f"2026-10-20T{hhmm}:00Z")
        assert SL.plan(ctx, led, now, STUDY) == SW.plan(ctx, led, now, STUDY)


# ------------------------------------------------------------------------------------------------------------------ monitor
def runs(*statuses, event="schedule", minutes_ago=None, now=None):
    out = []
    for i, s in enumerate(statuses):
        r = {"databaseId": i + 1, "status": s, "event": event}
        if minutes_ago is not None:
            r["updatedAt"] = (now - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")
        out.append(r)
    return out


def codes(f):
    return sorted(x["code"] for x in f)


def test_monitor_no_findings_when_the_chain_is_alive_or_nothing_is_due(tmp_path):
    ctx = make_ctx(tmp_path / "c")
    led = ledger(tmp_path)
    now = t("2026-10-20T18:20:00Z")
    assert SM.check(ctx, led, runs("in_progress"), now, STUDY) == []                                  # window open, chain alive
    assert SM.check(ctx, led, runs("queued"), now, STUDY) == []                                       # a queued successor counts
    assert SM.check(ctx, led, runs("completed", minutes_ago=5, now=now), now, STUDY) == []            # handover grace
    assert SM.check(ctx, led, [], t("2026-10-20T10:00:00Z"), STUDY) == []                             # nothing due or imminent: no chain needed


def test_monitor_flags_a_dead_chain_while_a_window_is_open_or_imminent(tmp_path):
    ctx = make_ctx(tmp_path / "c")
    led = ledger(tmp_path)
    now = t("2026-10-20T18:20:00Z")
    assert codes(SM.check(ctx, led, [], now, STUDY)) == ["SEAL_CHAIN_DEAD"]
    assert codes(SM.check(ctx, led, runs("completed", minutes_ago=90, now=now), now, STUDY)) == ["SEAL_CHAIN_DEAD"]
    assert codes(SM.check(ctx, led, runs("in_progress", event="pull_request"), now, STUDY)) == ["SEAL_CHAIN_DEAD"]     # a PR rehearsal is not the chain
    soon = t("2026-10-20T17:40:00Z")                                                                  # the window opens in 30 min
    assert codes(SM.check(ctx, led, [], soon, STUDY)) == ["SEAL_CHAIN_DEAD"]
    assert SM.check(ctx, led, [], t("2026-10-20T16:00:00Z"), STUDY) == []                              # opens in > 45 min: not yet
    f = SM.check(ctx, led, None, now, STUDY)
    assert codes(f) == ["SEAL_RUNS_UNKNOWN"] and f[0]["severity"] == "WARN"                            # an unreadable run list is not a verdict


def test_monitor_flags_a_closed_unmarked_window_and_missed_markers(tmp_path):
    ctx = make_ctx(tmp_path / "c")
    led = ledger(tmp_path)
    f = SM.check(ctx, led, runs("in_progress"), t("2026-10-20T19:05:00Z"), STUDY)                     # closed 15 min ago, no seal, no marker
    assert codes(f) == ["SEAL_UNMARKED_WINDOW"] and f[0]["severity"] == "CRITICAL"
    assert SM.check(ctx, led, [], t("2026-10-20T18:55:00Z"), STUDY) == []                              # < 10 min grace: the chain may still write the marker
    sub = tmp_path / "m"
    sub.mkdir()
    led2 = ledger(sub, missed=["espn:401909088"])
    f = SM.check(ctx, led2, runs("in_progress"), t("2026-10-20T22:00:00Z"), STUDY)
    assert codes(f) == ["SEAL_MISSED"] and f[0]["severity"] == "CRITICAL"
    assert SM.check(ctx, led2, runs("in_progress"), t("2026-10-22T22:00:00Z"), STUDY) == []            # > 36 h later the marker is history
    sub2 = tmp_path / "s"
    sub2.mkdir()
    assert SM.check(ctx, ledger(sub2, sealed=["espn:401909088"]), [], t("2026-10-20T19:30:00Z"), STUDY) == []
    sub3 = tmp_path / "b"
    sub3.mkdir()
    assert SM.check(ctx, ledger(sub3, enabled="2026-10-20T18:30:00Z"), [], t("2026-10-20T19:30:00Z"), STUDY) == []     # window opened before the ledger was enabled


def test_the_watchdog_merges_the_seal_findings_and_the_status(tmp_path, monkeypatch, capsys):
    from nba.live import watchdog as WD
    monkeypatch.setattr(WD, "check", lambda *a, **k: {"schema": "x", "generated_utc": "2026-10-20T18:20:00Z", "status": "OK", "findings": [], "counts": {}})
    ctx = make_ctx(tmp_path / "c")
    led = ledger(tmp_path)
    out = tmp_path / "h.json"
    rc = WD.main(["--archive", str(tmp_path), "--context", ctx, "--now", "2026-10-20T18:20:00Z", "--seals", led, "--seal-runs", str(tmp_path / "none.json"), "--out", str(out)])
    rep = json.load(open(out))
    assert rc == 0 and rep["status"] == "WARN" and [x["code"] for x in rep["findings"]] == ["SEAL_RUNS_UNKNOWN"]
    (tmp_path / "runs.json").write_text("[]")
    rc = WD.main(["--archive", str(tmp_path), "--context", ctx, "--now", "2026-10-20T18:20:00Z", "--seals", led, "--seal-runs", str(tmp_path / "runs.json"), "--out", str(out)])
    rep = json.load(open(out))
    assert rc == 1 and rep["status"] == "CRITICAL" and rep["findings"][0]["code"] == "SEAL_CHAIN_DEAD"          # the watchdog fails and opens nba-ops-alert
    rc = WD.main(["--archive", str(tmp_path), "--context", ctx, "--now", "2026-10-20T18:20:00Z", "--out", str(out)])
    assert rc == 0 and json.load(open(out))["findings"] == []                                              # without --seals the watchdog is unchanged


# ------------------------------------------------------------------------------------------------------------------ chain
class Fake:
    """Injected runner + clock. `script` maps a command kind to a returncode (or a callable)."""

    def __init__(self, tmp_path, ctx, rc=None):
        self.tmp, self.ctx, self.rc, self.calls, self.now = tmp_path, ctx, rc or {}, [], t("2026-10-20T18:00:00Z")
        self.mono = 0.0
        self.remote = {"exec-shadow-seals": dict(self.rc.get("ledger_files") or {}), "exec-shadow-seals-t45": dict(self.rc.get("ledger_files_t45") or {}), "exec-shadow-seals-t60a": dict(self.rc.get("ledger_files_t60a") or {})}
        self.dir_branch: dict[str, str] = {}
        self.mark_missed: dict[str, datetime] = {}

    def kind(self, cmd):
        s = " ".join(map(str, cmd))
        for k in ("mount_seals", "mount_context", "mount_inputs", "exec_seal seal", "exec_seal watch", "ledger_remote.py export", "ledger_remote.py publish", "workflow run", "git init"):
            if k in s:
                return k
        return s

    def run(self, cmd, env=None, cwd=None, capture=False):
        k = self.kind(cmd)
        self.calls.append((k, dict(env or {}), list(cmd)))
        if k == "mount_context":
            dest = Path(cmd[cmd.index("mount_context") + 1]) / "data-archive"
            shutil.rmtree(dest, ignore_errors=True)
            shutil.copytree(self.ctx, dest)
        if k == "mount_seals":
            i = cmd.index("mount_seals")
            d = Path(cmd[i + 1])
            br = cmd[i + 2] if len(cmd) > i + 2 else "exec-shadow-seals"
            self.dir_branch[str(d)] = br
            shutil.rmtree(d, ignore_errors=True)
            d.mkdir(parents=True)
            subprocess.run(["git", "init", "-q", str(d)], check=True)
            for name, text in self.remote[br].items():
                (d / name).parent.mkdir(parents=True, exist_ok=True)
                (d / name).write_text(text)
        if k == "exec_seal seal" and "--dry-run" not in cmd:                   # a seal file for the open game (what the real sealer writes)
            seals = Path(cmd[cmd.index("--seals") + 1])
            (seals / "seals/2026-10-20").mkdir(parents=True, exist_ok=True)
            (seals / "seals/2026-10-20/espn_401909088__fake.json").write_text("{}")
        if k == "exec_seal watch" and "--dry-run" not in cmd and self.mark_missed:                 # what the real watch does for a closed, unsealed window: a MISSED marker
            seals = Path(cmd[cmd.index("--seals") + 1])
            for gid, closes in self.mark_missed.items():
                if self.now > closes:
                    (seals / "missed").mkdir(exist_ok=True)
                    (seals / f"missed/{SW.gid_file(gid)}.json").write_text("{}")
        if k == "ledger_remote.py export":                                      # additions = every file of the (fresh) ledger worktree that the remote does not have
            src, dst = Path(cmd[cmd.index("--seals") + 1]), Path(cmd[cmd.index("--dir") + 1])
            have = set(self.remote[self.dir_branch.get(str(src), "exec-shadow-seals")])
            for p in src.rglob("*"):
                if p.is_file() and ".git" not in p.parts and str(p.relative_to(src)) not in have:
                    (dst / p.relative_to(src)).parent.mkdir(parents=True, exist_ok=True)
                    (dst / p.relative_to(src)).write_text(p.read_text())
        if k == "ledger_remote.py publish":
            out = cmd[cmd.index("--out") + 1]
            rc = self._rc(k)
            if rc == 0:
                Path(out).write_text(json.dumps({"status": "PUBLISHED", "commit_utc": "2026-10-20T18:21:00Z"}))
                files = self.remote[cmd[cmd.index("--branch") + 1]]             # the remote keeps what was published
                root = Path(cmd[cmd.index("--dir") + 1])
                for p in root.rglob("*"):
                    if p.is_file():
                        files[str(p.relative_to(root))] = p.read_text()
        rc = self._rc(k)
        return argparse.Namespace(returncode=rc, stdout="", stderr="")

    def _rc(self, k):
        v = self.rc.get(k, 0)
        if isinstance(v, list):
            return v[min(sum(1 for c in self.calls if c[0] == k) - 1, len(v) - 1)]
        return v

    def sleep(self, s):
        self.now += timedelta(seconds=s)
        self.mono += s

    def kinds(self):
        return [c[0] for c in self.calls]


def chain(tmp_path, fake, **kw):
    a = argparse.Namespace(work=str(tmp_path / "work"), repo_root=str(tmp_path), repo="o/n", dry_run=False, now=None, interval_s=90.0, max_minutes=335.0, successor_at_min=315.0, retire_after_min=240.0, quiet_lead_min=45.0,
                           horizon_h=6.0, default_branch="main", workflow_file="exec-shadow-seal.yml")
    for k, v in kw.items():
        setattr(a, k, v)
    os.makedirs(a.work, exist_ok=True)
    return SC.Chain(a, run=fake.run, clock=lambda: fake.now, sleep=fake.sleep, mono=lambda: fake.mono)


@pytest.fixture
def env_token(monkeypatch):
    monkeypatch.setenv("PUBLISH_TOKEN", "SECRET-TOKEN")
    monkeypatch.setenv("GH_TOKEN", "LEAK")


def test_an_idle_day_runs_one_cheap_iteration_and_ends(tmp_path, env_token):
    ctx = make_ctx(tmp_path / "c", rows=())
    f = Fake(tmp_path, ctx, rc={"ledger_files": {"ENABLED_UTC": "2026-10-20T00:00:00Z\n"}})
    rc = chain(tmp_path, f).run_chain()
    assert rc == 0 and f.kinds().count("mount_context") == 1 and not set(f.kinds()) & {"mount_inputs", "exec_seal seal", "ledger_remote.py publish", "workflow run"}


def test_a_chain_waits_for_the_window_then_seals_and_publishes_in_order(tmp_path, env_token):
    ctx = make_ctx(tmp_path / "c")
    f = Fake(tmp_path, ctx, rc={"ledger_files": {"ENABLED_UTC": "2026-10-20T00:00:00Z\n"}})
    # 18:00 now: window opens 18:10 (>= 6 min away) -> idle iterations until it opens, then seal + publish, then the game is "sealed" only once the ledger shows it
    c = chain(tmp_path, f, max_minutes=30)
    rc = c.run_chain()
    k = f.kinds()
    first_seal = k.index("exec_seal seal")
    assert k[first_seal - 1] == "mount_inputs" and k[first_seal + 1:first_seal + 3] == ["ledger_remote.py export", "ledger_remote.py publish"]
    assert f.now >= t("2026-10-20T18:10:00Z") and rc == 0
    assert "exec_seal watch" not in k[:first_seal]


def test_the_publish_token_reaches_only_the_publisher_and_the_dispatch(tmp_path, env_token):
    ctx = make_ctx(tmp_path / "c")
    f = Fake(tmp_path, ctx, rc={"ledger_files": {"ENABLED_UTC": "2026-10-20T00:00:00Z\n"}})
    f.now = t("2026-10-20T18:20:00Z")
    chain(tmp_path, f, max_minutes=5, successor_at_min=0).run_chain()
    for kind, env, cmd in f.calls:
        has = "GH_TOKEN" in env and env["GH_TOKEN"] == "SECRET-TOKEN"
        assert "PUBLISH_TOKEN" not in env and env.get("GH_TOKEN") != "LEAK", kind
        assert has == (kind in ("ledger_remote.py publish", "workflow run")), (kind, env.keys())
    assert "ledger_remote.py publish" in f.kinds() and "workflow run" in f.kinds()


def test_a_dry_run_is_exactly_one_iteration_on_an_empty_ledger_and_publishes_nothing(tmp_path, env_token):
    ctx = make_ctx(tmp_path / "c")
    f = Fake(tmp_path, ctx, rc={"ledger_files": {"ENABLED_UTC": "2099-01-01T00:00:00Z\n"}})            # the real ledger's enablement must not matter to a rehearsal
    c = chain(tmp_path, f, dry_run=True, now="2026-10-20T18:20:00Z", successor_at_min=0)
    assert c.run_chain() == 0
    k = f.kinds()
    assert "mount_seals" not in k and "exec_seal seal" in k and not set(k) & {"ledger_remote.py export", "ledger_remote.py publish", "workflow run"}
    seal_cmd = next(c[2] for c in f.calls if c[0] == "exec_seal seal")
    assert "--dry-run" in seal_cmd and "--now" in seal_cmd


def test_missed_windows_make_the_run_red_but_the_chain_keeps_going_and_publishes_the_marker(tmp_path, env_token):
    ctx = make_ctx(tmp_path / "c")
    f = Fake(tmp_path, ctx, rc={"ledger_files": {"ENABLED_UTC": "2026-10-20T00:00:00Z\n"}, "exec_seal watch": 3})
    f.now = t("2026-10-20T19:00:00Z")                                                                 # window closed unsealed
    c = chain(tmp_path, f, max_minutes=3)
    assert c.run_chain() == 1 and c.missed
    k = f.kinds()
    assert "exec_seal watch" in k and "ledger_remote.py publish" in k and "exec_seal seal" not in k


def test_a_failed_publish_is_reported_and_retried_on_the_next_iteration(tmp_path, env_token):
    ctx = make_ctx(tmp_path / "c")
    f = Fake(tmp_path, ctx, rc={"ledger_files": {"ENABLED_UTC": "2026-10-20T00:00:00Z\n"}, "ledger_remote.py publish": [1, 0]})
    f.now = t("2026-10-20T18:20:00Z")
    c = chain(tmp_path, f, max_minutes=10)
    rc = c.run_chain()
    k = f.kinds()
    assert rc == 1 and k.count("exec_seal seal") == 2 and k.count("ledger_remote.py publish") == 2                 # nothing remote -> the game is still due -> sealed again; then it is on the remote and the chain ends
    assert any("NOT DURABLE" in e for e in c.errors)


def test_the_first_live_iteration_enables_the_ledger_and_publishes_the_stamp(tmp_path, env_token):
    ctx = make_ctx(tmp_path / "c")
    f = Fake(tmp_path, ctx)                                                                           # no ENABLED_UTC on the remote
    f.now = t("2026-10-20T16:00:00Z")
    c = chain(tmp_path, f, max_minutes=1)
    c.run_chain()
    assert f.remote["exec-shadow-seals"]["ENABLED_UTC"].strip() == "2026-10-20T16:00:00Z"                              # published once; later iterations see it on the remote
    assert (Path(c.seals) / "ENABLED_UTC").read_text().strip() == "2026-10-20T16:00:00Z"
    assert "ledger_remote.py publish" in f.kinds()


def test_one_successor_after_the_threshold_only_while_still_needed_and_the_chain_ends_at_its_lifetime(tmp_path, env_token):
    ctx = make_ctx(tmp_path / "c")
    f = Fake(tmp_path, ctx, rc={"ledger_files": {"ENABLED_UTC": "2026-10-20T00:00:00Z\n"}})
    f.now = t("2026-10-20T12:30:00Z")                                                                 # window opens in ~5.7 h: active, idle
    c = chain(tmp_path, f, max_minutes=10, successor_at_min=5, interval_s=60)
    c.run_chain()
    assert f.kinds().count("workflow run") == 1 and f.kinds().count("exec_seal seal") == 0
    disp = next(c[2] for c in f.calls if c[0] == "workflow run")
    assert "--ref" in disp and "main" in disp and "dry_run=false" in disp
    # nothing needed any more (sealed game): no successor, the chain ends at once
    f2 = Fake(tmp_path, make_ctx(tmp_path / "c2"), rc={"ledger_files": {"ENABLED_UTC": "2026-10-20T00:00:00Z\n", "seals/2026-10-20/espn_401909088__x.json": "{}"}})
    f2.now = t("2026-10-20T19:30:00Z")
    c2 = chain(tmp_path, f2, successor_at_min=0)
    assert c2.run_chain() == 0 and "workflow run" not in f2.kinds() and f2.kinds().count("mount_context") == 1


def test_a_live_chain_refuses_a_clock_override(capsys):
    assert SC.main(["--work", "/tmp/x", "--now", "2026-10-20T18:20:00Z"]) == 2


def test_two_lanes_seal_and_publish_to_their_own_branches_and_never_share_state(tmp_path, env_token):
    ctx = make_ctx(tmp_path / "c")
    f = Fake(tmp_path, ctx, rc={"ledger_files": {"ENABLED_UTC": "2026-10-20T00:00:00Z\n"}, "ledger_files_t45": {"ENABLED_UTC": "2026-10-20T00:00:00Z\n"}})
    f.now = t("2026-10-20T18:26:00Z")                                                                  # inside both windows (control 18:10-18:50, t45 18:20-18:50)
    c = chain(tmp_path, f, max_minutes=1, lanes="control,t45")
    c.run_chain()
    seals = [x for x in f.calls if x[0] == "exec_seal seal"]
    assert [x[2][x[2].index("--lane") + 1] for x in seals[:2]] == ["control", "t45"]
    assert len({x[2][x[2].index("--seals") + 1] for x in seals[:2]}) == 2                              # separate worktrees
    pubs = [x for x in f.calls if x[0] == "ledger_remote.py publish"]
    assert {x[2][x[2].index("--branch") + 1] for x in pubs} == {"exec-shadow-seals", "exec-shadow-seals-t45"}
    assert any(x[2][x[2].index("--out") + 1].endswith("publish_t45.json") for x in pubs)
    mounts = [x for x in f.calls if x[0] == "mount_seals"]
    assert {x[2][x[2].index("mount_seals") + 2] for x in mounts} == {"exec-shadow-seals", "exec-shadow-seals-t45"}


def test_the_default_chain_runs_only_the_control_lane(tmp_path, env_token):
    ctx = make_ctx(tmp_path / "c")
    f = Fake(tmp_path, ctx, rc={"ledger_files": {"ENABLED_UTC": "2026-10-20T00:00:00Z\n"}})
    f.now = t("2026-10-20T18:26:00Z")
    chain(tmp_path, f, max_minutes=1).run_chain()
    assert all("--lane" not in x[2] or x[2][x[2].index("--lane") + 1] == "control" for x in f.calls) and not any("t45" in " ".join(map(str, x[2])) for x in f.calls)


def test_unknown_lanes_are_refused(tmp_path):
    with pytest.raises(SystemExit):
        chain(tmp_path, Fake(tmp_path, make_ctx(tmp_path / "c")), lanes="control,t90")


def test_a_dry_two_lane_rehearsal_publishes_nothing(tmp_path, env_token):
    f = Fake(tmp_path, make_ctx(tmp_path / "c"))
    chain(tmp_path, f, dry_run=True, now="2026-10-20T18:26:00Z", lanes="control,t45").run_chain()
    k = f.kinds()
    assert k.count("exec_seal seal") == 2 and not set(k) & {"mount_seals", "ledger_remote.py export", "ledger_remote.py publish", "workflow run"}


# ------------------------------------------------------------------------------------------------------------------ handover at a quiet moment (owner request 2026-10-23)
def games_ctx(root, specs):
    """specs: [(tip_iso, game_id)] -> schedule snapshot with those games."""
    rows = [{**GAME, "game_id": gid, "start_time_utc": tip} for tip, gid in specs]
    return make_ctx(root, rows=rows)


def run_handover(tmp_path, specs, start="2026-10-20T12:00:00Z", rc=None, marks=None, **kw):
    ctx = games_ctx(tmp_path / "c", specs)
    f = Fake(tmp_path, ctx, rc={"ledger_files": {"ENABLED_UTC": "2026-10-19T00:00:00Z\n"}, **(rc or {})})
    f.now = t(start)
    f.mark_missed = marks or {}
    c = chain(tmp_path, f, max_minutes=335, successor_at_min=315, retire_after_min=240, quiet_lead_min=45, interval_s=90, **kw)
    return c, f, c.run_chain()


def test_the_chain_retires_at_the_first_quiet_moment_after_the_threshold_not_before(tmp_path, env_token):
    c, f, rc = run_handover(tmp_path, [("2026-10-20T17:00:00Z", "espn:401909088"), ("2026-10-20T21:00:00Z", "espn:401909099")])
    disp = [x for x in f.calls if x[0] == "workflow run"]
    assert len(disp) == 1 and rc == 0
    # started 12:00: at 240 min (16:00) the window 16:10-16:50 opens in 10 min -> NOT quiet, the chain stays; the game is sealed and published at ~16:10-16:12, nothing is left to seal
    # and the next window is 4 h away -> the first quiet moment: the successor is dispatched and the chain ends. The runner-queue gap of the successor then falls in dead time.
    assert t("2026-10-20T16:10:00Z") <= f.now < t("2026-10-20T16:20:00Z")
    k = [x[0] for x in f.calls]
    first_seal = k.index("exec_seal seal")
    assert k.index("ledger_remote.py publish", first_seal) < k.index("workflow run")                     # sealed and durably published first, then handed over
    assert not [x for x in f.calls[:first_seal] if x[0] == "workflow run"]                              # and never dispatched before the window was dealt with


def test_the_chain_does_not_hand_over_while_a_window_is_open_or_imminent(tmp_path, env_token):
    # a game that cannot be sealed by the fake (not id 088) keeps its window OPEN: no quiet moment during 16:10-16:50, so no retirement before 16:51
    c, f, rc = run_handover(tmp_path, [("2026-10-20T17:00:00Z", "espn:401909055"), ("2026-10-20T21:00:00Z", "espn:401909099")], marks={"espn:401909055": t("2026-10-20T16:50:00Z")})
    disp = [x for x in f.calls if x[0] == "workflow run"]
    assert len(disp) == 1 and t("2026-10-20T16:50:00Z") < f.now < t("2026-10-20T17:00:00Z")           # the window closed unsealed (MISSED marker), then quiet


def test_a_quiet_chain_still_runs_the_minimum_before_retiring(tmp_path, env_token):
    c, f, rc = run_handover(tmp_path, [("2026-10-20T21:00:00Z", "espn:401909088")], start="2026-10-20T15:00:00Z")      # nothing before 20:10: quiet from the start
    assert len([x for x in f.calls if x[0] == "workflow run"]) == 1
    assert f.now >= t("2026-10-20T19:00:00Z")                                                           # not before retire_after_min (240 min after 15:00)
    assert f.now < t("2026-10-20T19:05:00Z")


def test_without_a_quiet_moment_the_successor_is_queued_by_315_and_the_chain_ends_at_the_hard_cap(tmp_path, env_token):
    specs = [((t("2026-10-20T16:30:00Z") + timedelta(minutes=40 * i)).strftime("%Y-%m-%dT%H:%M:%SZ"), f"espn:4019092{i:02d}") for i in range(12)]      # windows run back to back
    specs[0] = (specs[0][0], "espn:401909088")
    c, f, rc = run_handover(tmp_path, specs)
    disp_i = [i for i, x in enumerate(f.calls) if x[0] == "workflow run"]
    assert len(disp_i) == 1
    assert t("2026-10-20T17:14:00Z") <= f.now <= t("2026-10-20T17:38:00Z")                              # 12:00 + 335 min = 17:35
    # the dispatch happened at the 315-minute mark (17:15), i.e. ~20 minutes before the end, not at the end
    assert sum(1 for x in f.calls[:disp_i[0]] if x[0] == "mount_context") * 90 / 60 >= 300


def test_a_failed_dispatch_is_retried_and_the_chain_keeps_sealing_until_it_succeeds(tmp_path, env_token):
    c, f, rc = run_handover(tmp_path, [("2026-10-20T21:00:00Z", "espn:401909088")], start="2026-10-20T15:00:00Z", rc={"workflow run": [1, 1, 0]})
    assert [x[0] for x in f.calls].count("workflow run") == 3 and rc == 1 and any("successor" in e for e in c.errors)
    assert f.now > t("2026-10-20T19:00:00Z")


def test_nothing_to_hand_over_to_ends_quietly(tmp_path, env_token):
    c, f, rc = run_handover(tmp_path, [("2026-10-20T14:00:00Z", "espn:401909088")], rc={"ledger_files": {"ENABLED_UTC": "2026-10-19T00:00:00Z\n", "seals/2026-10-20/espn_401909088__x.json": "{}"}})
    assert "workflow run" not in f.kinds() and rc == 0                                                  # the only game is sealed: inactive, no successor, ends at once


# ------------------------------------------------------------------------------------------------------------------ stalled handover is visible to the dead-man check
def test_monitor_flags_a_window_open_while_the_only_chain_run_is_still_queued(tmp_path):
    ctx = make_ctx(tmp_path / "c")
    led = ledger(tmp_path)
    now = t("2026-10-20T18:30:00Z")                                                                     # window open
    queued = [{"databaseId": 7, "status": "queued", "event": "workflow_dispatch", "createdAt": "2026-10-20T18:05:00Z"}]
    f = SM.check(ctx, led, queued, now, STUDY)
    assert codes(f) == ["SEAL_CHAIN_STALLED"] and f[0]["severity"] == "CRITICAL"
    fresh = [{"databaseId": 7, "status": "queued", "event": "workflow_dispatch", "createdAt": "2026-10-20T18:25:00Z"}]
    assert SM.check(ctx, led, fresh, now, STUDY) == []                                                  # a 5-minute wait is normal
    assert SM.check(ctx, led, queued + [{"databaseId": 6, "status": "in_progress", "event": "schedule"}], now, STUDY) == []     # something is executing
    assert SM.check(ctx, led, queued, t("2026-10-20T17:50:00Z"), STUDY) == []                           # no window open yet: waiting in the queue costs nothing
