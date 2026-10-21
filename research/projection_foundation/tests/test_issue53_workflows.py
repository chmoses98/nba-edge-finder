"""Isolation / cost guards of the two Issue #53 workflows (owner conditions on PR #54): nothing here may write production branches, push from the JRM dry run, or run unbounded."""
import re
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
WF = ROOT / ".github" / "workflows"
SEAL = WF / "exec-shadow-seal.yml"
JRM = WF / "jrm-exact-dryrun.yml"
SCRIPT = ROOT / "research" / "projection_foundation" / "scripts" / "exec_seal_ci.sh"


def load(p):
    d = yaml.safe_load(p.read_text())
    d["on"] = d.pop(True, d.get("on"))                       # PyYAML reads the key `on` as boolean True
    return d


def test_the_seal_workflow_is_cheap_bounded_and_pull_requests_are_dry():
    wf = load(SEAL)
    assert wf["permissions"] == {"contents": "read"}
    crons = [s["cron"] for s in wf["on"]["schedule"]]
    assert crons == ["*/5 16-23,0-3 * 10-12,1-6 *"]                                       # every 5 minutes, game hours only, season months only
    job = wf["jobs"]["seal"]
    assert job["timeout-minutes"] <= 15 and wf["concurrency"] == {"group": "exec-shadow-seal", "cancel-in-progress": False}
    txt = SEAL.read_text()
    assert '"$EVENT" = pull_request' in txt and "forcing dry run" in txt                          # pull requests and non-default branches never push
    assert "git push" not in txt                                                           # the only push is in the reviewed helper script
    code = "\n".join(l for l in txt.splitlines() if not l.lstrip().startswith("#"))
    for forbidden in ("projection-foundation.yml", "nba-ticker", "capture-worker", "secrets.", "git push"):
        assert forbidden not in code


def test_the_seal_helper_writes_only_the_ledger_branch_and_only_additions():
    sh = SCRIPT.read_text()
    pushes = re.findall(r"git push [^\n]*", sh)
    assert pushes and all("exec-shadow-seals" in p or "$BRANCH" in p for p in pushes)
    assert "projection-data" not in " ".join(pushes) and "data-archive" not in " ".join(pushes)
    assert "grep -E '^(M|D|R)'" in sh                                                      # guard_diff: modifications / deletions / renames are refused
    assert subprocess.run(["bash", "-n", str(SCRIPT)]).returncode == 0


def test_the_jrm_dry_run_is_read_only_pinned_labelled_and_never_scheduled():
    wf = load(JRM)
    assert wf["permissions"] == {"contents": "read"} and wf["jobs"]["dryrun"]["permissions"] == {"contents": "read"}
    assert "schedule" not in wf["on"] and set(wf["on"]) == {"workflow_dispatch", "pull_request"}
    assert wf["jobs"]["dryrun"]["timeout-minutes"] <= 40 and wf["concurrency"]["cancel-in-progress"] is True
    txt = JRM.read_text()
    assert "git push" not in txt and "secrets." not in txt and "issues:" not in txt and "contents: write" not in txt
    assert "contains(github.event.pull_request.labels.*.name, 'jrm-exact-dryrun')" in txt     # pull requests run only with the label
    assert "e19f8dcff9a4e0b0b9f55f9703d08119ff25bc2f" in txt and "draft PR #45 moved since it was pinned" in txt
    assert "mount \"$RUNNER_TEMP/m\" dry" in txt                                             # the dry mount: the archive is copied, never written


def test_the_jrm_default_is_untouched_by_these_workflows():
    for p in (SEAL, JRM):
        assert "PF_NBA_MINUTES_ENGINE: jrm" not in p.read_text()                           # set per call inside jrm_exact.project_pair only
    live = (WF / "projection-foundation.yml").read_text()
    assert "PF_NBA_MINUTES_ENGINE" not in live or "dry run only" in live
