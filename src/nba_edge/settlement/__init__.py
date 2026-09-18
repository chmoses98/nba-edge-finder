"""Settlement: turn a final box score plus a semantic ``Contract`` into a YES/NO/VOID/PUSH/UNSETTLEABLE record.

Design rule: FAIL CLOSED. Anything we cannot prove from the box score and the contract semantics is
``UNSETTLEABLE`` with a reason, never a guess. Kalshi's own result is the only authority for voids and DNPs.
"""

from nba_edge.settlement.boxscore import FinalBoxScore, PlayerLine, period_points
from nba_edge.settlement.engine import (
    ENGINE_VERSION,
    SettlementOutcome,
    SettlementRecord,
    settle_contract,
    settle_many,
)

__all__ = [
    "ENGINE_VERSION",
    "FinalBoxScore",
    "PlayerLine",
    "SettlementOutcome",
    "SettlementRecord",
    "period_points",
    "settle_contract",
    "settle_many",
]
