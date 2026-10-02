#!/usr/bin/env python3
"""Import a kalshi-bet-router NBA wager payload into data/accounting/wagers.jsonl. COUNTS ONLY.

    python scripts/accounting/import_routed_wagers.py --payload NBA.json --base-dir <accounting-data checkout> \
        --receipts-out receipts.json

The payload is the router's envelope ``{"importBatchId": ..., "rows": [...]}``. Identity (``wager_id``) is
minted from ``source_bet_key``; an identical re-delivery is DUPLICATE_NOOP and changes zero bytes; a re-delivery
with different economics is CONFLICT and exits 1 so the router's merge gate fails. Exit 2 means the payload or
the ledger could not be read at all.

This repository's Actions logs are public: stdout carries counts and refusal REASONS by row position, never a
ticker, price, stake, contract count or key. Per-row receipts (source key + minted id + verdict) go only to the
--receipts-out file the router's gate reads.

Recording is not endorsing: a row says the owner placed an NBA bet. The NBA model (RESEARCH only) is not involved.
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
    return run_import_cli(SPEC, "wagers", argv)


if __name__ == "__main__":
    raise SystemExit(main())
