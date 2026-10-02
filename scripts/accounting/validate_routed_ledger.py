#!/usr/bin/env python3
"""Validate the NBA accounting ledger (schema per row, unique keys, every settlement has its wager, and with
``--base-ref <git ref>`` that the files are append-only against that ref). COUNTS AND REASONS ONLY.

    python scripts/accounting/validate_routed_ledger.py --base-dir <accounting-data checkout> \
        [--base-ref origin/accounting-data] [--result-out result.json]

Exit 0 when the ledger is clean, 1 when it is not. Reasons name line numbers and field names, never values.
"""

from __future__ import annotations

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "contract"))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

from edge_finder_contract.routed_ledger import run_validate_cli  # noqa: E402

from nba_edge.accounting import SPEC  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    return run_validate_cli(SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
