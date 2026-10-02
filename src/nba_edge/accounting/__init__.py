"""NBA wager ACCOUNTING: what the owner actually placed on Kalshi, and what the exchange paid.

This package is deliberately walled off from everything else in ``nba_edge``. It imports no model,
simulator, feature, pricing or recommendation code (a test enforces that). A row here says "the
owner placed this NBA bet"; it never says "the NBA model recommended it". Every NBA model family
stays RESEARCH (``Authority.RESEARCH`` in ``nba_edge.schemas.prediction``), and nothing here reads
or writes a prediction, a slate, or an authority ledger.

Rows arrive only from kalshi-bet-router, which reads the owner's own Kalshi fills (read-only
exchange access). Nothing here places, sizes, recommends or cancels an order.

The ledger logic itself lives in the vendored, byte-identical contract module
``contract/edge_finder_contract/routed_ledger.py``; this package only pins the NBA ``LedgerSpec``
(the ONE place the sport, id prefixes and schema names are declared) and exposes it to the three
thin CLI scripts under ``scripts/accounting/``.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_DIR = REPO_ROOT / "contract"
if str(CONTRACT_DIR) not in sys.path:
    sys.path.insert(0, str(CONTRACT_DIR))

from edge_finder_contract.routed_ledger import LedgerSpec  # noqa: E402

#: The NBA accounting ledger. Wagers mint ``nbaw-<24hex>``, settlements ``nbas-<24hex>``, both from
#: ``source_bet_key`` alone; files live at ``data/accounting/{wagers,settlements}.jsonl`` under the
#: ``accounting-data`` branch checkout the router hands to the importers as ``--base-dir``.
SPEC = LedgerSpec(
    sport="NBA",
    id_prefix="nba",
    wager_schema="nba_accounted_wager.v1",
    settlement_schema="nba_wager_settlement.v1",
)

__all__ = ["SPEC", "LedgerSpec", "CONTRACT_DIR", "REPO_ROOT"]
