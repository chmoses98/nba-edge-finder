"""Server-timestamped, additions-only publication of the sealed ledger (Issue #53; RESEARCH ONLY).

Why not `git commit && git push`: the committer date of a pushed commit is whatever the RUNNER's clock said, a retried push keeps the old date, and the push has no server-side
timestamp, so "sealed before tip" would rest on a self-reported clock (independent review of PR #54). Here the commit is created through the GitHub Git Data API with NO
client-supplied author / committer dates: GitHub stamps the commit with its own clock when it is created, and the branch ref is moved with `force: false` (fast-forward only), so
the seal exists on the remote, with a server timestamp, exactly when this call returns - or not at all.

    python -m nba.paper.ledger_remote publish --repo owner/name --branch exec-shadow-seals --seals <worktree> --out publish.json

Properties (tested against an in-memory fake of the API, tests/test_issue53_ledger_remote.py):
  * additions only: the tree is built from `base_tree` plus NEW blob entries; no deletion entry is ever sent; an existing path with different content aborts the whole publish;
  * no credentials in the workspace repo are needed (the branch is bootstrapped through the API when it does not exist);
  * a lost race (the ref moved) is retried on top of the new head; the result records the server commit time that `check-deadline` compares with the deadline.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
from typing import Any, Callable

ALLOWED = ("seals/", "missed/")
ALLOWED_FILES = ("ENABLED_UTC", "README.md")
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
README = ("# exec-shadow-seals\nAppend-only sealed pre-tip ledger of the Issue #53 executable T-60 shadow study (research only; no orders, no authority).\n"
          "Written only by .github/workflows/exec-shadow-seal.yml through the GitHub Git Data API: commit times are the server clock; seals/ and missed/ are write-once.\n")


class ApiError(RuntimeError):
    def __init__(self, status: int, msg: str = ""):
        super().__init__(f"HTTP {status}: {msg}")
        self.status = status


class Conflict(RuntimeError):
    pass


def gh_api(method: str, endpoint: str, body: dict | None = None) -> Any:
    """`gh api` wrapper (preinstalled on hosted runners; token from GH_TOKEN). Raises ApiError(status)."""
    cmd = ["gh", "api", "--method", method, endpoint]
    if body is not None:
        cmd += ["--input", "-"]
    r = subprocess.run(cmd, input=json.dumps(body) if body is not None else None, capture_output=True, text=True)
    if r.returncode != 0:
        m = re.search(r"HTTP (\d{3})", r.stderr + r.stdout)
        raise ApiError(int(m.group(1)) if m else 0, (r.stderr or r.stdout)[:300])
    return json.loads(r.stdout) if r.stdout.strip() else {}


def _head(api: Callable, repo: str, branch: str) -> str | None:
    try:
        return api("GET", f"repos/{repo}/git/ref/heads/{branch}")["object"]["sha"]
    except ApiError as e:
        if e.status == 404:
            return None
        raise


def publish(api: Callable, repo: str, branch: str, files: dict[str, bytes], message: str, *, attempts: int = 4, sleep: Callable[[float], None] = time.sleep) -> dict[str, Any]:
    """Create ONE commit adding `files` on top of the current head of `branch` (bootstrapping the branch if absent). Returns the server's commit record."""
    bad = [p for p in files if not (p.startswith(ALLOWED) or p in ALLOWED_FILES) or ".." in p.split("/")]
    if bad:
        raise Conflict(f"paths outside the ledger layout: {bad[:3]}")
    last: Exception | None = None
    for i in range(attempts):
        head = _head(api, repo, branch)
        todo = dict(files)
        parents: list[str] = []
        base_tree = None
        if head is None:
            todo.setdefault("README.md", README.encode())
        else:
            commit = api("GET", f"repos/{repo}/git/commits/{head}")
            base_tree, parents = commit["tree"]["sha"], [head]
            existing = {e["path"]: e["sha"] for e in api("GET", f"repos/{repo}/git/trees/{base_tree}?recursive=1").get("tree", []) if e.get("type") == "blob"}
            for path in list(todo):
                if path in existing:
                    blob = api("POST", f"repos/{repo}/git/blobs", {"content": base64.b64encode(todo[path]).decode(), "encoding": "base64"})
                    if blob["sha"] != existing[path]:
                        raise Conflict(f"{path} already exists with different content: seals are write-once")
                    del todo[path]                                  # identical re-submission is a no-op
        if not todo:
            return {"status": "NOTHING_TO_PUBLISH", "head": head}
        entries = []
        for path, data in sorted(todo.items()):
            blob = api("POST", f"repos/{repo}/git/blobs", {"content": base64.b64encode(data).decode(), "encoding": "base64"})
            entries.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        tree = api("POST", f"repos/{repo}/git/trees", {**({"base_tree": base_tree} if base_tree else {}), "tree": entries})
        commit = api("POST", f"repos/{repo}/git/commits", {"message": message, "tree": tree["sha"], "parents": parents})     # NO dates: the server stamps them
        try:
            if head is None:
                api("POST", f"repos/{repo}/git/refs", {"ref": f"refs/heads/{branch}", "sha": commit["sha"]})
            else:
                api("PATCH", f"repos/{repo}/git/refs/heads/{branch}", {"sha": commit["sha"], "force": False})
        except ApiError as e:
            if e.status in (409, 422):                              # the branch moved / appeared under us: rebuild on the new head
                last = e
                sleep(min(2 ** i, 8))
                continue
            raise
        return {"status": "PUBLISHED", "commit_sha": commit["sha"], "commit_utc": commit["committer"]["date"], "author_date": commit["author"]["date"], "branch": branch,
                "files": sorted(todo), "bootstrapped": head is None, "parent": head}
    raise ApiError(0, f"could not publish after {attempts} attempts: {last}")


def collect_additions(seal_dir: str) -> dict[str, bytes]:
    """New files in the ledger worktree (untracked) under the allowed layout. A modified or deleted TRACKED file aborts: existing seals are never touched."""
    st = subprocess.run(["git", "-C", seal_dir, "status", "--porcelain", "--untracked-files=all"], capture_output=True, text=True, check=True).stdout.splitlines()
    out: dict[str, bytes] = {}
    for line in st:
        code, path = line[:2], line[3:]
        if code == "??":
            if path.startswith(ALLOWED) or path in ALLOWED_FILES:
                out[path] = open(os.path.join(seal_dir, path), "rb").read()
        else:
            raise Conflict(f"tracked ledger file changed in the worktree ({code.strip()} {path}): refusing to publish")
    return out


def export(seal_dir: str, out_dir: str) -> dict[str, bytes]:
    """Copy the ledger additions of a worktree into `out_dir` (the hand-over between the read-only compute job and the write job)."""
    files = collect_additions(seal_dir)
    for path, data in files.items():
        dest = os.path.join(out_dir, path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as fh:
            fh.write(data)
    return files


def load_dir(root: str) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for dp, _dn, fn in os.walk(root):
        for f in fn:
            full = os.path.join(dp, f)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            if rel.startswith(ALLOWED) or rel in ALLOWED_FILES:
                out[rel] = open(full, "rb").read()
    return out


def verify_durable(api: Callable, repo: str, branch: str, sha: str) -> bool:
    """The commit exists on the server and is the head of, or an ancestor of, the branch (checked through the server, not the runner)."""
    api("GET", f"repos/{repo}/git/commits/{sha}")
    head = _head(api, repo, branch)
    if head == sha:
        return True
    if head is None:
        return False
    return api("GET", f"repos/{repo}/compare/{sha}...{head}").get("status") in ("ahead", "identical")


def late_games(report: dict, commit_utc: str) -> list[str]:
    """Seals of this run whose server commit time is after their pre-tip deadline (uncounted, loud)."""
    from datetime import datetime
    def p(t: str) -> datetime:
        return datetime.fromisoformat(t.replace("Z", "+00:00"))
    if report.get("dry_run"):
        return []
    return sorted(x["game_id"] for x in report.get("sealed", []) if p(commit_utc) > p(x["deadline_utc"]))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["export", "publish"])
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    ap.add_argument("--branch", default="exec-shadow-seals")
    ap.add_argument("--seals", help="export: ledger worktree")
    ap.add_argument("--dir", required=True, help="export: output dir; publish: directory of new files")
    ap.add_argument("--report", default=None, help="publish: seal_report.json of the compute job (deadlines)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    if a.cmd == "export":
        files = export(a.seals, a.dir)
        print(json.dumps({"new_files": sorted(files)}, indent=1))
        return 0
    files = load_dir(a.dir)
    if not files:
        res: dict[str, Any] = {"status": "NOTHING_TO_PUBLISH", "late": []}
        rc = 0
    else:
        res = publish(gh_api, a.repo, a.branch, files, f"exec-shadow seals (research only; run {os.environ.get('GITHUB_RUN_ID', 'local')})")
        rc = 0
        if res["status"] == "PUBLISHED":
            if not verify_durable(gh_api, a.repo, a.branch, res["commit_sha"]):
                res["status"] = "NOT_DURABLE"
                rc = 1
            report = json.load(open(a.report)) if a.report and os.path.exists(a.report) else {}
            res["late"] = late_games(report, res["commit_utc"])
            if res["late"]:
                rc = 5
    print(json.dumps(res, indent=1, sort_keys=True))
    if a.out:
        json.dump(res, open(a.out, "w"), indent=1, sort_keys=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
