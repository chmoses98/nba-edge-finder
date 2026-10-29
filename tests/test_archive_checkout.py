"""Sparse archive checkout: old slates are not materialised, nothing is lost from the branch, and a new pass pushes through archive_push.sh."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHECKOUT, PUSH = ROOT / "scripts" / "archive_checkout.sh", ROOT / "scripts" / "archive_push.sh"
pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git required")


def git(cwd, *a, check=True):
    r = subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    if check and r.returncode:
        raise AssertionError(f"git {a}: {r.stderr}")
    return r


@pytest.fixture()
def remote(tmp_path):
    bare = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", str(bare))
    git(bare, "config", "uploadpack.allowFilter", "true")
    git(bare, "config", "uploadpack.allowAnySHA1InWant", "true")
    seed = tmp_path / "seed"
    git(tmp_path, "clone", "-q", str(bare), str(seed))
    git(seed, "config", "user.name", "t")
    git(seed, "config", "user.email", "t@t")
    for rel, txt in {"kalshi/markets/x.jsonl": "m", "predictions/p.jsonl": "p", "slates/dt=2026-10-01/a/packet.json": "OLD" * 100, "slates/latest/slate.json": "l", "manifest.jsonl": "x\n"}.items():
        f = seed / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(txt)
    git(seed, "add", "-A")
    git(seed, "commit", "-qm", "init")
    git(seed, "push", "-q", "origin", "HEAD:data-archive")
    return bare


def worker_repo(tmp_path, remote):
    w = tmp_path / "work"
    git(tmp_path, "init", "-q", str(w))
    git(w, "remote", "add", "origin", f"file://{remote}")
    return w


def test_sparse_checkout_skips_old_slates_keeps_everything_else_and_pushes_a_new_pass(tmp_path, remote):
    w = worker_repo(tmp_path, remote)
    r = subprocess.run(["bash", str(CHECKOUT), "data-archive", str(w / "data" / "archive")], cwd=w, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    a = w / "data" / "archive"
    assert (a / "kalshi/markets/x.jsonl").exists() and (a / "predictions/p.jsonl").exists() and (a / "slates/latest/slate.json").exists() and (a / "manifest.jsonl").exists()
    assert not (a / "slates/dt=2026-10-01").exists(), "historical pass must not be materialised"

    git(a, "config", "user.name", "t")
    git(a, "config", "user.email", "t@t")
    (a / "slates/dt=2026-10-25/b").mkdir(parents=True)
    (a / "slates/dt=2026-10-25/b/packet.json.gz").write_bytes(b"new")
    (a / "manifest.jsonl").write_text("x\ny\n")
    p = subprocess.run(["bash", str(PUSH), str(a), "data-archive", "pass"], capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr

    verify = tmp_path / "verify"
    git(tmp_path, "clone", "-q", "--branch", "data-archive", str(remote), str(verify))
    assert (verify / "slates/dt=2026-10-01/a/packet.json").read_text() == "OLD" * 100  # history preserved, not deleted by the sparse worktree
    assert (verify / "slates/dt=2026-10-25/b/packet.json.gz").read_bytes() == b"new"
    assert (verify / "manifest.jsonl").read_text() == "x\ny\n"


def test_missing_branch_exits_3_so_the_caller_creates_the_orphan(tmp_path, remote):
    w = worker_repo(tmp_path, remote)
    r = subprocess.run(["bash", str(CHECKOUT), "no-such-branch", str(w / "data" / "archive")], cwd=w, capture_output=True, text=True)
    assert r.returncode == 3
