"""Seal-chain keeper: dispatch only when no run of the seal workflow is alive, inside the seal hours and season; the ticker wiring is bounded and cannot break the ticker."""
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from nba.paper import seal_keeper as K

UTC = timezone.utc
ROOT = Path(__file__).resolve().parents[3]
NOW = datetime(2026, 10, 26, 16, 30, tzinfo=UTC)


def run(status, event="schedule"):
    return {"status": status, "event": event, "createdAt": "2026-10-26T16:00:00Z"}


def test_dispatch_only_when_nothing_is_alive():
    assert K.decide([], NOW)[0] == "dispatch"
    assert K.decide([run("completed"), run("completed", "workflow_dispatch")], NOW)[0] == "dispatch"
    for st in ("queued", "in_progress", "waiting", "pending", "requested", "IN_PROGRESS"):
        assert K.decide([run("completed"), run(st)], NOW)[0] == "skip", st                          # any live or queued chain run: never a duplicate
    assert K.decide([run("in_progress", "pull_request")], NOW)[0] == "dispatch"                    # a PR rehearsal is not the chain


def test_the_hours_season_and_spacing_mirror_the_cron_and_never_burst():
    assert K.decide([], datetime(2026, 10, 26, 8, 0, tzinfo=UTC))[0] == "skip"                       # outside the 12-03Z seal hours
    assert K.decide([], datetime(2026, 10, 26, 3, 59, tzinfo=UTC))[0] == "dispatch"
    assert K.decide([], datetime(2026, 8, 26, 16, 0, tzinfo=UTC))[0] == "skip"                       # off-season
    assert K.decide([], NOW, last_dispatch=NOW - timedelta(minutes=5))[0] == "skip"                 # the previous dispatch may not be visible yet
    assert K.decide([], NOW, last_dispatch=NOW - timedelta(minutes=16))[0] == "dispatch"


def test_a_malformed_run_list_never_dispatches():
    for bad in ("", "not json", "{}", "null"):
        p = subprocess.run([sys.executable, str(ROOT / "research/projection_foundation/nba/paper/seal_keeper.py"), "--now", "2026-10-26T16:30:00Z"], input=bad, capture_output=True, text=True)
        assert p.returncode == 0 and p.stdout.startswith("skip"), (bad, p.stdout)


def test_the_cli_is_self_contained_and_decides_from_stdin():
    p = subprocess.run([sys.executable, str(ROOT / "research/projection_foundation/nba/paper/seal_keeper.py"), "--now", "2026-10-26T16:30:00Z"],
                       input=json.dumps([run("completed")]), capture_output=True, text=True, cwd="/")
    assert p.stdout.startswith("dispatch") and "import nba" not in (ROOT / "research/projection_foundation/nba/paper/seal_keeper.py").read_text()


def test_the_ticker_asks_the_keeper_every_quarter_hour_and_cannot_be_broken_by_it():
    wf = yaml.safe_load((ROOT / ".github/workflows/nba-ticker.yml").read_text())
    assert wf["permissions"] == {"contents": "read", "actions": "write"}                              # unchanged: no new permission
    run_txt = next(s for s in wf["jobs"]["tick"]["steps"] if str(s.get("name", "")).startswith("Tick every 5 minutes"))["run"]
    assert "exec-shadow-seal.yml" in run_txt and "nba/paper/seal_keeper.py" in run_txt and "dry_run=false" in run_txt and "--ref main" in run_txt
    assert "i % 3" in run_txt                                                                         # every third 5-minute tick = 15 min
    assert "gh run list --workflow exec-shadow-seal.yml" in run_txt
    # the keeper block is best effort: it must not abort the loop (no `set -e`; every command guarded)
    assert wf["defaults"]["run"]["shell"] == "bash -uo pipefail {0}" and "set -e" not in run_txt         # no errexit: a failing command in the keeper block cannot end the loop
    assert "|| true" in run_txt and "|| echo" in run_txt and run_txt.count("seal keeper:") == 3


def _keeper_block():
    wf = yaml.safe_load((ROOT / ".github/workflows/nba-ticker.yml").read_text())
    txt = next(s for s in wf["jobs"]["tick"]["steps"] if str(s.get("name", "")).startswith("Tick every 5 minutes"))["run"]
    a = txt.index("if [ $(( i % 3 )) = 1 ]; then")
    b = txt.index('if [ "$i" -ge 50 ]')
    return txt[a:b]


def _run_block(tmp_path, runs_json, i=1, gh_dispatch_rc=0):
    """Execute the real keeper block with a stub `gh` (records dispatches) and the real seal_keeper.py at a fixed clock."""
    stub = tmp_path / "gh"
    log = tmp_path / "gh.log"
    stub.write_text(f'#!/usr/bin/env bash\necho "$@" >> {log}\nif [ "$1" = run ]; then cat {tmp_path}/runs.json; exit 0; fi\nif [ "$1" = workflow ]; then exit {gh_dispatch_rc}; fi\n')
    stub.chmod(0o755)
    (tmp_path / "runs.json").write_text(runs_json)
    # a fixed `date` is not needed: the keeper clock is only used for the hour/season check, so pin it through a wrapper around date
    fake_date = tmp_path / "date"
    fake_date.write_text('#!/usr/bin/env bash\nexec /bin/date -d "2026-10-26T16:30:00Z" "$@"\n')
    fake_date.chmod(0o755)
    script = f'set -uo pipefail\nexport PATH={tmp_path}:$PATH\nPF_DIR={ROOT}/research/projection_foundation\ni={i}\nlast_seal_dispatch=""\n{_keeper_block()}\necho "last=$last_seal_dispatch"\n'
    p = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    return p, (log.read_text() if log.exists() else "")


def test_the_real_keeper_block_dispatches_once_when_idle_and_never_when_a_chain_is_alive(tmp_path):
    p, log = _run_block(tmp_path, json.dumps([{"status": "completed", "event": "schedule", "createdAt": "x"}]))
    assert p.returncode == 0 and "seal keeper: dispatch" in p.stdout and "workflow run exec-shadow-seal.yml --ref main -f dry_run=false" in log and "last=2026-10-26T16:30:00Z" in p.stdout
    q = tmp_path / "alive"
    q.mkdir()
    p2, log2 = _run_block(q, json.dumps([{"status": "queued", "event": "workflow_dispatch", "createdAt": "x"}]))
    assert p2.returncode == 0 and "seal keeper: skip" in p2.stdout and "workflow run" not in log2
    r = tmp_path / "offtick"
    r.mkdir()
    p3, log3 = _run_block(r, json.dumps([]), i=2)                                                      # only ticks 1, 4, 7, ... ask (every 15 minutes)
    assert "seal keeper" not in p3.stdout and log3 == ""
    f = tmp_path / "failing"
    f.mkdir()
    p4, _ = _run_block(f, json.dumps([]), gh_dispatch_rc=1)
    assert p4.returncode == 0 and "dispatch failed" in p4.stdout and "last=" in p4.stdout and "last=2026" not in p4.stdout   # a failed dispatch does not abort and is retried next time
