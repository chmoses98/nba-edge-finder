"""The shadow store is append-only: any existing file modified or deleted vs a base ref fails.

Two layers:
* ``check_immutable`` itself, exercised on a scratch git repository (append passes; modify, delete or
  rewrite of an append-only log fails) -- this is the check the live workflow runs against
  ``origin/nba-shadow-pure`` before every push;
* this repository: nothing under ``data/shadow_pure/`` that exists on ``origin/main`` (override with
  SHADOW_IMMUTABILITY_REF) may be modified or deleted.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from nba_edge.shadow.store import ShadowStore, check_immutable
from nba_edge.timeutil import parse_iso

REPO = Path(__file__).resolve().parents[1]


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True).stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "store"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@t")
    _git(root, "config", "user.name", "t")
    s = ShadowStore(root, run_id="r1")
    s.append_rows("projections/a/unconditional", [{"k": 1}], observed_at=parse_iso("2026-10-27T15:00:00Z"))
    s.append_rows("captures", [{"slot": "morning", "games": []}], observed_at=parse_iso("2026-10-27T15:00:00Z"))
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "base")
    _git(root, "tag", "base")
    return root


def test_appending_new_files_passes(repo: Path):
    s = ShadowStore(repo, run_id="r2")
    s.append_rows("projections/a/unconditional", [{"k": 2}], observed_at=parse_iso("2026-10-27T23:00:00Z"))
    rep = check_immutable(repo, "base")
    assert rep.ok and rep.checked_files >= 3
    assert s.verify() == []


def test_modifying_an_existing_file_fails(repo: Path):
    f = next(repo.rglob("*.jsonl.gz"))
    f.write_bytes(f.read_bytes() + b"\0")
    rep = check_immutable(repo, "base")
    assert not rep.ok and any(p.startswith("modified:") for p in rep.problems)
    assert ShadowStore(repo).verify()  # the sha256 manifest catches it too


def test_deleting_an_existing_file_fails(repo: Path):
    next(repo.rglob("*.jsonl.gz")).unlink()
    rep = check_immutable(repo, "base")
    assert not rep.ok and any(p.startswith("deleted:") for p in rep.problems)


def test_rewriting_an_append_only_log_fails(repo: Path):
    m = repo / "manifest.jsonl"
    lines = m.read_text().splitlines()
    m.write_text("\n".join(reversed(lines)) + "\n")
    rep = check_immutable(repo, "base")
    assert any("append-only log rewritten: manifest.jsonl" in p for p in rep.problems)


def test_missing_base_ref_is_a_failure_not_a_pass(repo: Path):
    rep = check_immutable(repo, "no-such-ref")
    assert not rep.ok


def test_repository_shadow_dir_is_unchanged_vs_base_ref():
    ref = os.environ.get("SHADOW_IMMUTABILITY_REF", "origin/main")
    have = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], capture_output=True, check=False)
    if have.returncode != 0 and ref == "origin/main":
        subprocess.run(["git", "-C", str(REPO), "fetch", "-q", "--depth=1", "origin", "main:refs/remotes/origin/main"],
                       capture_output=True, check=False, timeout=120)
        have = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], capture_output=True, check=False)
    if have.returncode != 0:
        pytest.skip(f"base ref {ref} not available in this checkout")
    rep = check_immutable(REPO, ref, "data/shadow_pure")
    assert rep.ok, rep.problems
