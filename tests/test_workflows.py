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


def test_the_conductor_force_file_is_not_committed():
    """A committed .trigger/conductor made every scheduled wake force a full capture.

    The guard is now gated on the push event, so the file's presence is no longer sufficient to
    force a run -- but committing it again would still mean every push to it re-forces, and it was
    the root of a 144x/day storm. Keep it out of the repo; pushing a new one still triggers the
    workflow through its `paths:` filter.
    """
    root = Path(__file__).resolve().parents[1]
    tracked = subprocess.run(
        ["git", "ls-files", ".trigger/conductor"], cwd=root, capture_output=True, text=True
    ).stdout.strip()
    assert tracked == "", ".trigger/conductor must not be committed"


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
