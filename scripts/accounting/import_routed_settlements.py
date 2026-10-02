#!/usr/bin/env python3
"""Import a kalshi-bet-router NBA settlement payload into data/accounting/settlements.jsonl. COUNTS ONLY.

    python scripts/accounting/import_routed_settlements.py --payload NBA-settlements.json \
        --base-dir <accounting-data checkout> --receipts-out receipts.json

The payload is ``{"settlements": [...]}`` (``router-settlement-economics.v2``). A settlement must name a wager
already on this ledger (same ``source_bet_key``, ticker and side) or it is refused as ORPHAN. A wager settles
once: an identical re-delivery is DUPLICATE_NOOP, a different one is CONFLICT (exit 1). Exit 2 means the payload
or the ledger could not be read.

Public logs carry counts and reasons only; per-row receipts go to --receipts-out. Accounting only: the NBA
model (RESEARCH only) is not involved.
"""

from __future__ import annotations

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "contract"))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

from edge_finder_contract.routed_ledger import run_import_cli  # noqa: E402

from nba_edge.accounting import SPEC  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    return run_import_cli(SPEC, "settlements", argv)


if __name__ == "__main__":
    raise SystemExit(main())
