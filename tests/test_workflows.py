"""The workflows are production code, but nothing executed them until they ran for real.

A broken `run:` block or a malformed embedded Python heredoc in the conductor cannot fail CI --
it fails at 3am on a scheduled wake, on the one workflow that writes authoritative data. These
tests are cheap and cover the mistakes that are actually easy to make when editing YAML by hand.
"""

from __future__ import annotations

import ast
import re
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

WORKFLOWS = sorted((Path(__file__).resolve().parents[1] / ".github" / "workflows").glob("*.yml"))


def _despell(text: str) -> str:
    """Neutralise GitHub `${{ }}` expressions, which are substituted before the shell ever sees them."""
    return text.replace("${{", "$X{").replace("}}", "}")


def test_there_are_workflows_to_check():
    assert WORKFLOWS, "no workflow files found -- this test would silently pass forever"


@pytest.mark.parametrize("wf", WORKFLOWS, ids=lambda p: p.name)
def test_workflow_is_valid_yaml_with_timeouts(wf: Path):
    d = yaml.safe_load(wf.read_text())
    assert d.get("jobs"), f"{wf.name} defines no jobs"
    for name, job in d["jobs"].items():
        # An unbounded job on a schedule burns a runner for six hours before GitHub kills it.
        assert "timeout-minutes" in job, f"{wf.name}:{name} has no timeout-minutes"


@pytest.mark.parametrize("wf", WORKFLOWS, ids=lambda p: p.name)
def test_every_run_block_is_valid_bash(wf: Path):
    d = yaml.safe_load(wf.read_text())
    for name, job in d["jobs"].items():
        for i, step in enumerate(job.get("steps", []), 1):
            run = step.get("run")
            if not run:
                continue
            with tempfile.NamedTemporaryFile("w", suffix=".sh") as f:
                f.write(_despell(run))
                f.flush()
                r = subprocess.run(["bash", "-n", f.name], capture_output=True, text=True)
            assert r.returncode == 0, f"{wf.name}:{name} step {i} ({step.get('name')}) is not valid bash:\n{r.stderr}"


@pytest.mark.parametrize("wf", WORKFLOWS, ids=lambda p: p.name)
def test_every_embedded_python_heredoc_parses(wf: Path):
    d = yaml.safe_load(wf.read_text())
    for name, job in d["jobs"].items():
        for step in job.get("steps", []):
            for m in re.finditer(r"<<'PY'\n(.*?)\n\s*PY(\n|$)", step.get("run") or "", re.S):
                body = _despell(m.group(1))
                try:
                    ast.parse(body)
                except SyntaxError as e:  # pragma: no cover - only on a real breakage
                    pytest.fail(f"{wf.name}:{name} ({step.get('name')}) embedded python is invalid: {e}\n{body}")


def test_no_trigger_file_is_committed():
    """A trigger file is a push MECHANISM, never repository content.

    Two distinct incidents came from committing them. `.trigger/conductor` made every scheduled wake
    force a full capture, 144x/day. And because `.trigger/history`, `.trigger/kalshi_history` and
    `.trigger/probe` were committed on the feature branch, **merging PR #1 pushed them to main for
    the first time, matched their `paths:` filters, and fired all three expensive data pulls, each
    of which then committed straight to the default branch.** A merge is a push.

    Pushing a trigger file still starts a run -- that is the mechanism and it still works. What must
    not happen is the file living in the repo, where any future merge re-fires it.
    """
    root = Path(__file__).resolve().parents[1]
    tracked = subprocess.run(
        ["git", "ls-files", ".trigger/"], cwd=root, capture_output=True, text=True
    ).stdout.split()
    assert tracked == [], f"trigger files must not be committed, found: {tracked}"


def test_every_trigger_path_a_workflow_watches_is_gitignored():
    """Whatever path a workflow triggers on must be ignored, or it can be committed by accident."""
    root = Path(__file__).resolve().parents[1]
    ignored = (root / ".gitignore").read_text()
    watched = set()
    for wf in WORKFLOWS:
        on = yaml.safe_load(wf.read_text()).get(True) or yaml.safe_load(wf.read_text()).get("on") or {}
        push = (on or {}).get("push") or {}
        for p in (push.get("paths") or []):
            if p.startswith(".trigger/"):
                watched.add(p)
    assert watched, "expected at least one workflow to use the .trigger push mechanism"
    assert ".trigger/" in ignored, f"paths {sorted(watched)} are push triggers; .trigger/ must be gitignored"


def test_conductor_forcing_requires_a_push_event():
    """Pin the actual guard text: this is the exact line whose weakness caused the storm."""
    wf = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "conductor.yml"
    d = yaml.safe_load(wf.read_text())
    runs = " ".join(s.get("run") or "" for s in d["jobs"]["decide"]["steps"])
    assert ".trigger/conductor" in runs
    assert 'EVENT_NAME" == "push"' in runs, "the force-file guard must require the push event"


def test_scheduled_workflow_cannot_be_starved_by_a_ref_keyed_concurrency_group():
    """Two refs writing one constant branch must be in ONE concurrency group, or they race for it."""
    wf = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "conductor.yml"
    d = yaml.safe_load(wf.read_text())
    group = d["concurrency"]["group"]
    assert "github.ref" not in group, f"conductor concurrency group must not be ref-keyed, got {group!r}"


# -----------------------------------------------------------------------------------------------
# research streams must not be able to take down market capture
# -----------------------------------------------------------------------------------------------
def _conductor_text() -> str:
    from pathlib import Path

    return (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "conductor.yml").read_text()


def test_a_research_stream_failing_cannot_kill_market_capture():
    """Matchup shadow runs BEFORE market capture in the job, so without continue-on-error a bad
    research pull would take the night's market snapshots with it. Market capture is the one stream
    that cannot be re-collected later: a price at T-30m exists for thirty minutes and never again."""
    import yaml

    wf = yaml.safe_load(_conductor_text())
    steps = wf["jobs"]["run"]["steps"]
    names = [s.get("name", "") for s in steps]

    shadow = next(i for i, n in enumerate(names) if "Matchup shadow" in n)
    capture = next(i for i, n in enumerate(names) if "Market capture" in n)
    assert shadow < capture, "the ordering this test is about"
    assert steps[shadow].get("continue-on-error") is True, (
        "matchup shadow is RESEARCH; it must never be able to abort the job before market capture"
    )
    assert steps[capture].get("continue-on-error") is True


def test_every_collection_stream_is_isolated_but_the_alarm_step_is_not():
    """Two opposite requirements, and the difference is the point.

    A COLLECTION step must never abort the job: one stream's bad night is not a reason to lose the
    others. A REPORTING step must be able to, or a silent coverage failure ends as a green run --
    which is exactly how ~4.6% delivery went unnoticed for a wave. Reporting steps are the ones
    gated on always(); they run after the push and turn the run red when the DATA is wrong.
    """
    import yaml

    wf = yaml.safe_load(_conductor_text())
    collection, reporting = [], []
    for step in wf["jobs"]["run"]["steps"]:
        cond = str(step.get("if", ""))
        if "needs.decide.outputs" not in cond:
            continue
        (reporting if cond.strip().startswith("always()") else collection).append(step)

    assert collection and reporting, "both kinds must exist for this test to mean anything"
    for step in collection:
        assert step.get("continue-on-error") is True, f"{step.get('name')} can abort the job"
    for step in reporting:
        assert step.get("continue-on-error") is not True, (
            f"{step.get('name')} is an alarm; swallowing its exit code makes a bad run look green"
        )


def test_shot_profile_ingestion_is_not_in_the_conductor_at_all():
    """The strongest isolation available: the shot-event pull is its own workflow, so it cannot
    consume the conductor's runtime or fail its job under any circumstance."""
    assert "shot-events" not in _conductor_text()
    from pathlib import Path

    assert (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "shot_events.yml").exists()


def test_settlement_is_gated_separately_from_capture():
    import yaml

    wf = yaml.safe_load(_conductor_text())
    steps = {s.get("name", ""): s for s in wf["jobs"]["run"]["steps"]}
    settle = next(v for k, v in steps.items() if k.startswith("Settle"))
    capture = next(v for k, v in steps.items() if "Market capture" in k)
    assert "settle" in str(settle["if"]) and "capture" in str(capture["if"])
    assert str(settle["if"]) != str(capture["if"]), "settlement must not ride on the capture decision"


def test_the_preseason_to_regular_season_transition_stays_in_season():
    """The 2026-27 rollover. in_season must not blink off between the preseason finale and opening
    night -- a dormant day there is a day of market history that cannot be recovered."""
    from nba_edge.workflows.conductor import SEASON_CALENDAR, season_window

    cal = SEASON_CALENDAR["2026-27"]
    for day in (cal["preseason_start"], "2026-10-15", "2026-10-19", cal["regular_start"], "2026-12-25"):
        in_season, label, known = season_window(day)
        assert in_season and known and label == "2026-27", f"{day} should be live"

    # The day before preseason opens is correctly dormant, and correctly NOT on the fallback rule.
    in_season, label, known = season_window("2026-10-02")
    assert in_season is False and known is True and label is None
