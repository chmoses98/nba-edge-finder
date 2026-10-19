"""Append-only guard for the archive paths added after pf_core 1.2.1 (pf_core itself is vendored byte-identically and is not edited).

Immutable (additions only): everything pf_core already protects, plus the run ledger, game-level forecasts, market snapshots and the
paper-trading decision / settlement records. Rewritable views (latest.json, scorecards, reports) stay outside the list.

    python -m nba.live.ops_guard <archive_dir> [<base_ref>]
"""
from __future__ import annotations

import re
import subprocess
import sys

from pf_core import archive_guard as AG

EXTRA_IMMUTABLE = ("ops/nba/slots/", "game_forecasts/", "market_snapshots/", "team_outcomes/", "paper/nba/decisions/",
                   "paper/nba/settlements/", "paper/nba/corrections/", "paper/nba/expressions/")


def _patched(fn, *a):
    saved = AG.IMMUTABLE
    AG.IMMUTABLE = tuple(saved) + EXTRA_IMMUTABLE
    try:
        return fn(*a)
    finally:
        AG.IMMUTABLE = saved


# immutable paths that need a pattern rather than a prefix: every published report version is write-once
_VERSION_RE = re.compile(r"^reports/nba/week\d+/versions/")


def _version_violations(archive_dir: str, base_ref: str | None) -> list[str]:
    bad = []
    st = subprocess.check_output(["git", "-C", archive_dir, "status", "--porcelain", "--untracked-files=all"], text=True)
    for line in st.splitlines():
        code, path = line[:2], line[3:].split(" -> ")[-1]
        if _VERSION_RE.match(path) and code.strip() not in ("??", "A"):
            bad.append(f"{code.strip()} {path}")
    if base_ref:
        out = subprocess.check_output(["git", "-C", archive_dir, "diff", "--name-status", "--no-renames", f"{base_ref}..HEAD"], text=True)
        for line in out.splitlines():
            code, _, path = line.partition("\t")
            if _VERSION_RE.match(path) and code.strip() != "A":
                bad.append(f"{code.strip()} {path} (since {base_ref})")
    return bad


def violations(archive_dir: str, base_ref: str | None = None) -> list[str]:
    bad = _patched(AG.violations, archive_dir)
    if base_ref:
        bad += _patched(AG.violations_since, archive_dir, base_ref)
    return bad + _version_violations(archive_dir, base_ref)


def main(argv=None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    bad = violations(args[0] if args else ".", args[1] if len(args) > 1 and args[1] else None)
    if bad:
        print("ops_guard: immutable archive files changed (only additions are allowed):")
        print("\n".join("  " + b for b in bad))
        return 1
    print("ops_guard: OK (additions only)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
