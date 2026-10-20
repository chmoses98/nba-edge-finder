"""The ticker workflow's shell loop, executed for real with stubbed `gh`, `git` and `python`: what it dispatches, when it holds back, how it
retries, and when it queues its successor. (The due-slot logic itself is covered in test_ops_schedule.py.)"""
import os
import stat
import subprocess
import textwrap
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[3]
WF = REPO / ".github" / "workflows" / "nba-ticker.yml"


def _script():
    wf = yaml.safe_load(WF.read_text())
    step = next(s for s in wf["jobs"]["tick"]["steps"] if s.get("name", "").startswith("Tick every"))
    return step["run"]


def _run(tmp_path, ticks, due, runs_json="[]", dispatch_rc=0, pending_ticker="0", first_tick=1):
    """Run the loop for `ticks` iterations starting at iteration number `first_tick`. `runs_json` is the `gh run list` payload that the
    --jq filter is applied to (the filter text is the one in the workflow, applied by real jq)."""
    (tmp_path / "research" / "projection_foundation").mkdir(parents=True, exist_ok=True)
    bin_ = tmp_path / "bin"
    bin_.mkdir(exist_ok=True)
    calls = tmp_path / "calls.log"
    calls.write_text("")
    stub = {
        "git": "exit 0",
        "python": f'printf "%s\\n" "$DUE"',
        "sleep": "exit 0",
        "gh": textwrap.dedent(f"""
            echo "gh $*" >> {calls}
            if [ "$1" = run ] && [ "$2" = list ]; then
              if [[ "$*" == *nba-ticker.yml* ]]; then echo {pending_ticker}; exit 0; fi
              jq_filter=$(printf '%s\\n' "$@" | sed -n '/^\\[/p')
              echo '{runs_json}' | jq "$jq_filter"
              exit 0
            fi
            if [ "$1" = workflow ] && [ "$2" = run ] && [[ "$*" == *projection-foundation* ]]; then exit {dispatch_rc}; fi
            exit 0
        """),
    }
    for name, body in stub.items():
        f = bin_ / name
        f.write_text("#!/usr/bin/env bash\n" + body + "\n")
        f.chmod(f.stat().st_mode | stat.S_IEXEC)
    script = _script().replace("$(seq 1 60)", f"$(seq {first_tick} {first_tick + ticks - 1})")
    env = {**os.environ, "PATH": f"{bin_}:{os.environ['PATH']}", "DUE": due, "GH_TOKEN": "x", "PF_DIR": "research/projection_foundation"}
    r = subprocess.run(["bash", "-uo", "pipefail", "-c", script], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60)
    return r.stdout, [c for c in calls.read_text().splitlines()]


needs_jq = pytest.mark.skipif(subprocess.run(["which", "jq"], capture_output=True).returncode != 0, reason="jq not installed")


@needs_jq
def test_dispatches_the_exact_named_slot_once(tmp_path):
    out, calls = _run(tmp_path, 3, "pregame 2026-10-20@1820 13")
    disp = [c for c in calls if c.startswith("gh workflow run projection-foundation.yml")]
    assert disp == ["gh workflow run projection-foundation.yml --ref main -f dry_run=false -f slot=2026-10-20@1820 -f slot_kind=pregame "
                    "-f season_types=regular -f window_hours=30"]
    assert out.count("dispatching pregame slot 2026-10-20@1820") == 1 and "dispatched <25 min ago: waiting" in out   # ticks 2 and 3 wait


@needs_jq
@pytest.mark.parametrize("status", ["queued", "in_progress"])
@pytest.mark.parametrize("event", ["schedule", "workflow_dispatch"])
def test_holds_back_while_a_live_run_is_queued_or_running(tmp_path, status, event):
    out, calls = _run(tmp_path, 2, "pregame 2026-10-20@1820 13", runs_json=f'[{{"status":"{status}","event":"{event}"}}]')
    assert not [c for c in calls if c.startswith("gh workflow run projection-foundation.yml")]
    assert out.count("already queued/running") == 2


@needs_jq
def test_a_pull_request_dry_run_or_finished_runs_do_not_block_a_make_up_dispatch(tmp_path):
    runs = '[{"status":"in_progress","event":"pull_request"},{"status":"queued","event":"pull_request"},{"status":"completed","event":"schedule"}]'
    _, calls = _run(tmp_path, 1, "pregame 2026-10-20@1820 13", runs_json=runs)
    assert len([c for c in calls if c.startswith("gh workflow run projection-foundation.yml")]) == 1


@needs_jq
def test_a_failed_dispatch_is_not_remembered_and_is_retried_on_the_next_tick(tmp_path):
    out, calls = _run(tmp_path, 3, "pregame 2026-10-20@1820 13", dispatch_rc=1)
    assert len([c for c in calls if c.startswith("gh workflow run projection-foundation.yml")]) == 3
    assert "waiting" not in out


@needs_jq
def test_nothing_due_dispatches_nothing_and_every_due_line_is_served(tmp_path):
    _, calls = _run(tmp_path, 3, "")
    assert not [c for c in calls if "workflow run" in c]
    _, calls = _run(tmp_path, 1, "pregame 2026-10-20@1820 13\nsettle 2026-10-20@0640 700")
    disp = [c for c in calls if c.startswith("gh workflow run projection-foundation.yml")]
    assert len(disp) == 1 and "slot=2026-10-20@1820" in disp[0]         # one live run at a time: the second line waits for the next tick


@needs_jq
def test_successor_is_queued_once_from_iteration_50_unless_one_is_already_pending(tmp_path):
    _, calls = _run(tmp_path, 4, "", first_tick=48)                       # iterations 48..51
    assert len([c for c in calls if c == "gh workflow run nba-ticker.yml --ref main"]) == 1
    _, calls = _run(tmp_path, 4, "", first_tick=48, pending_ticker="1")
    assert not [c for c in calls if c == "gh workflow run nba-ticker.yml --ref main"]
    _, calls = _run(tmp_path, 4, "", first_tick=1)                         # early iterations never queue a successor
    assert not [c for c in calls if c == "gh workflow run nba-ticker.yml --ref main"]
