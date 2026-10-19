"""Append-only guard for the archive paths added after pf_core 1.2.1 (pf_core itself is vendored byte-identically and is not edited).

Immutable (additions only): everything pf_core already protects, plus the run ledger, game-level forecasts, market snapshots and the
paper-trading decision / settlement records. Rewritable views (latest.json, scorecards, reports) stay outside the list.

    python -m nba.live.ops_guard <archive_dir> [<base_ref>]
"""
from __future__ import annotations

import sys

from pf_core import archive_guard as AG

EXTRA_IMMUTABLE = ("ops/nba/slots/", "game_forecasts/", "market_snapshots/", "paper/nba/decisions/", "paper/nba/settlements/",
                   "paper/nba/corrections/")


def _patched(fn, *a):
    saved = AG.IMMUTABLE
    AG.IMMUTABLE = tuple(saved) + EXTRA_IMMUTABLE
    try:
        return fn(*a)
    finally:
        AG.IMMUTABLE = saved


def violations(archive_dir: str, base_ref: str | None = None) -> list[str]:
    bad = _patched(AG.violations, archive_dir)
    if base_ref:
        bad += _patched(AG.violations_since, archive_dir, base_ref)
    return bad


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
