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


def test_the_seal_workflow_is_a_self_renewing_chain_gated_by_a_dependency_free_check_and_pull_requests_are_dry():
    wf = load(SEAL)
    assert wf["permissions"] == {"contents": "read"}
    crons = [s["cron"] for s in wf["on"]["schedule"]]
    assert crons == ["*/5 12-23,0-3 * 10-12,1-6 *"]                                           # bootstrap only: the repo measured ~4% cron delivery
    jobs = wf["jobs"]
    assert set(jobs) == {"tick"} and jobs["tick"]["timeout-minutes"] <= 355
    # the ONLY write permissions: contents (Git Data API publisher, ledger layout only) and actions (successor dispatch); no issues, no secrets
    assert jobs["tick"]["permissions"] == {"contents": "write", "actions": "write"}
    grp = wf["concurrency"]["group"]
    assert wf["concurrency"]["cancel-in-progress"] is False and "'live'" in grp and "pull_request" in grp and "dry-" in grp       # one live chain; rehearsals never queue behind it
    txt = SEAL.read_text()
    steps = jobs["tick"]["steps"]
    names = [x.get("name", x.get("uses", "")) for x in steps]
    gate_i = next(i for i, n in enumerate(names) if n.startswith("Idle gate"))
    py_i = next(i for i, x in enumerate(steps) if "setup-python" in str(x.get("uses", "")))
    pip_i = next(i for i, x in enumerate(steps) if "pip install" in str(x.get("run", "")))
    assert gate_i < py_i < pip_i                                                              # the gate runs before any interpreter setup or install
    assert "python3 $PF_DIR/nba/paper/seal_windows.py gate" in txt and "pip" not in steps[gate_i]["run"]
    for i in (py_i, pip_i) + tuple(i for i, n in enumerate(names) if n.startswith(("Seal chain", "History"))):
        assert "steps.gate.outputs.active == 'true'" in steps[i]["if"]                       # an idle poll stops after the gate
    assert '"$EVENT" = pull_request' in txt and "forcing dry run" in txt                          # pull requests and non-default branches are dry
    chain = steps[next(i for i, n in enumerate(names) if n.startswith("Seal chain"))]
    assert chain["env"]["PUBLISH_TOKEN"] == "${{ github.token }}" and "GH_TOKEN" not in chain["env"] and "GITHUB_TOKEN" not in chain["env"]
    assert "--dry-run" in chain["run"] and "seal_chain.py" in chain["run"]
    code = "\n".join(l for l in txt.splitlines() if not l.lstrip().startswith("#"))
    for forbidden in ("projection-foundation.yml", "nba-ticker", "capture-worker", "secrets.", "git push", "git commit", "--force", "force: true", "issues:"):
        assert forbidden not in code


def test_the_chain_code_never_pushes_and_the_token_is_scoped_to_two_commands():
    src = (ROOT / "research/projection_foundation/nba/paper/seal_chain.py").read_text()
    code = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#"))
    for forbidden in ("git push", "git commit", "--force", "force=True"):
        assert forbidden not in code
    assert code.count("token=True") == 1 and code.count("token_env()") == 3                  # def + publisher + successor dispatch
    lr = (ROOT / "research/projection_foundation/nba/paper/ledger_remote.py").read_text()
    assert '"force": False' in lr and "ALLOWED = " in lr


def test_the_watchdog_workflow_reads_the_seal_chain_without_widening_its_writes():
    wf = load(WF / "nba-watchdog.yml")
    assert wf["permissions"] == {"contents": "read", "issues": "write", "actions": "read"}
    txt = (WF / "nba-watchdog.yml").read_text()
    seal = next(x for x in wf["jobs"]["watch"]["steps"] if x.get("id") == "seal")
    assert seal["continue-on-error"] is True                                                  # the existing checks never depend on the new inputs
    assert "gh run list --workflow exec-shadow-seal.yml" in txt and "--seals" in txt and "git push" not in txt


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


def test_the_selftest_workflow_is_manual_and_can_only_reach_the_throwaway_branch():
    wf = load(WF / "exec-shadow-selftest.yml")
    assert set(wf["on"]) == {"workflow_dispatch"} and wf["permissions"] == {"contents": "write"}
    txt = (WF / "exec-shadow-selftest.yml").read_text()
    code = "\n".join(l for l in txt.splitlines() if not l.lstrip().startswith("#"))
    assert "ledger_remote.py selftest" in code and "git push" not in code and "refs/heads/main" not in code and "exec-shadow-seals " not in code
    lr = (ROOT / "research/projection_foundation/nba/paper/ledger_remote.py").read_text()
    assert 'SELFTEST_BRANCH = "exec-shadow-seals-selftest"' in lr and "selftest only ever writes the throw-away branch" in lr


def test_the_t45_lane_is_rehearsed_dry_but_not_enabled_live_without_approval():
    wf = load(SEAL)
    env = wf["env"]
    assert env["SEAL_LANES"] == "control"                                    # ACTIVATION of the T-45 study = adding t45 here, in an approved PR
    assert set(env["REHEARSAL_LANES"].split(",")) == {"control", "t45"}      # the dry PR rehearsal exercises both lanes on real archived data
    txt = SEAL.read_text()
    steps = wf["jobs"]["tick"]["steps"]
    chain = next(s for s in steps if str(s.get("name", "")).startswith("Seal chain"))
    assert '--lanes "$LANES"' in chain["run"] and "steps.gate.outputs.lanes" in chain["env"]["LANES"]
    gate = next(s for s in steps if str(s.get("name", "")).startswith("Idle gate"))
    assert 'LANES="$SEAL_LANES"' in gate["run"] and 'LANES="$REHEARSAL_LANES"' in gate["run"] and "pip" not in gate["run"]
    assert "exec-shadow-seals-t45" not in txt or "seal_windows.py branch" in txt          # the branch name comes from the one table (seal_windows.LANES), not from the YAML


def test_watchdog_reads_the_t45_ledger_best_effort():
    txt = (WF / "nba-watchdog.yml").read_text()
    assert "exec-shadow-seals-t45" in txt and "--seals-t45" in txt and "|| echo" in txt
