"""Isolation / cost guards of the two Issue #53 workflows (owner conditions on PR #54): nothing here may write production branches, push from the JRM dry run, or run unbounded."""
import subprocess
from pathlib import Path

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


def test_the_seal_workflow_is_cheap_bounded_least_privilege_and_pull_requests_are_dry():
    wf = load(SEAL)
    assert wf["permissions"] == {"contents": "read"}
    crons = [s["cron"] for s in wf["on"]["schedule"]]
    assert crons == ["*/5 16-23,0-3 * 10-12,1-6 *"]                                       # every 5 minutes, game hours only, season months only
    assert wf["concurrency"] == {"group": "exec-shadow-seal", "cancel-in-progress": False}
    jobs = wf["jobs"]
    assert set(jobs) == {"compute", "publish", "alert"} and all(j["timeout-minutes"] <= 15 for j in jobs.values())
    # least privilege: the job that runs the research code can write NOTHING; write access exists only in the stdlib-only publisher and issues only in the alert job
    assert jobs["compute"]["permissions"] == {"contents": "read"}
    assert jobs["publish"]["permissions"] == {"contents": "write"} and jobs["alert"]["permissions"] == {"issues": "write"}
    cond = jobs["publish"]["if"]
    assert "github.event.repository.default_branch" in cond and "'schedule'" in cond and "'workflow_dispatch'" in cond and "pull_request" not in cond
    assert "dry == 'false'" in cond                                                         # dry runs never reach the publisher
    assert "pull_request" in jobs["alert"]["if"]                                            # ... and never open issues
    txt = SEAL.read_text()
    assert '"$EVENT" = pull_request' in txt and "forcing dry run" in txt                          # pull requests and non-default branches are dry
    code = "\n".join(l for l in txt.splitlines() if not l.lstrip().startswith("#"))
    for forbidden in ("projection-foundation.yml", "nba-ticker", "capture-worker", "secrets.", "git push", "git commit", "--force", "force: true"):
        assert forbidden not in code
    # the clock override is honoured only for dry runs (a live run uses the wall clock)
    assert code.count("steps.mode.outputs.dry == 'true' && github.event.inputs.now || ''") == 3
    # a watch failure other than 'missed' (rc 3) is an error; sealing errors fail the run; the publisher runs even when compute failed late
    assert 'if [ "$rc" != 0 ] && [ "$rc" != 3 ]' in txt and "steps.seal.outcome == 'failure'" in txt
    assert "needs.compute.outputs.has_new == 'true'" in cond and "always()" in cond


def test_the_seal_helper_never_pushes_and_distinguishes_a_missing_ledger_from_an_error():
    sh = SCRIPT.read_text()
    code = "\n".join(l for l in sh.splitlines() if not l.lstrip().startswith("#"))
    for forbidden in ("git push", "git commit", "git config user", "commit_push", "--force"):
        assert forbidden not in code
    assert "ls-remote --exit-code" in sh and '"$rc" = 2' in sh and "refusing to treat an error as a missing ledger" in sh
    assert subprocess.run(["bash", "-n", str(SCRIPT)]).returncode == 0


def test_mount_seals_fails_closed_on_a_remote_error_and_bootstraps_only_when_the_branch_is_missing(tmp_path):
    """Functional: ls-remote rc 2 (no ref) -> an empty orphan ledger; any other failure (unreachable remote) -> exit 1, never an empty ledger."""
    import os
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}

    def run(*a, cwd):
        return subprocess.run(a, cwd=cwd, env=env, capture_output=True, text=True)
    remote = tmp_path / "remote.git"
    run("git", "init", "-q", "--bare", str(remote), cwd=tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    run("git", "init", "-q", "-b", "main", cwd=work)
    run("git", "remote", "add", "origin", str(remote), cwd=work)
    r = run("bash", str(SCRIPT), "mount_seals", str(tmp_path / "seals"), cwd=work)
    assert r.returncode == 0 and (tmp_path / "seals" / ".git").exists() and "does not exist yet" in r.stdout
    run("git", "remote", "set-url", "origin", str(tmp_path / "no-such-remote"), cwd=work)
    r = run("bash", str(SCRIPT), "mount_seals", str(tmp_path / "seals2"), cwd=work)
    assert r.returncode == 1 and "refusing to treat an error as a missing ledger" in (r.stdout + r.stderr)


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
