"""Record schemas, kinds, enumerations and id functions shared by every paper-system module (see docs/research/PAPER_ENGINE_SPEC.md)."""
from __future__ import annotations

import hashlib
import json
from typing import Any

SNAPSHOT_SCHEMA = "sift.market_snapshot.v1"
DECISION_SCHEMA = "sift.paper_decision.v1"
SETTLEMENT_SCHEMA = "sift.paper_settlement.v1"
CORRECTION_SCHEMA = "sift.paper_correction.v1"
GAME_FORECAST_SCHEMA = "sift.game_forecast.v1"
SCORECARD_SCHEMA = "sift.paper_scorecard.v1"
REPORT_SCHEMA = "sift.weekly_report.v1"

# kind -> directory under the projection-data root (immutable kinds; additions only)
KIND_DIR = {
    "game_forecasts": "game_forecasts/nba",
    "market_snapshots": "market_snapshots/nba",
    "decisions": "paper/nba/decisions",
    "settlements": "paper/nba/settlements",
    "corrections": "paper/nba/corrections",
}

HORIZONS = ("OPEN", "T-90", "T-60", "T-30", "T-10", "LAST_VALID", "LIVE")
HORIZON_MINUTES = {"T-90": 90, "T-60": 60, "T-30": 30, "T-10": 10}
MAX_SNAPSHOT_GAP_S = 30 * 60           # a snapshot further than this from its target is MISSED_STALE, never that horizon
CLOSING_MAX_AGE_S = 15 * 60            # LAST_VALID within this of tip is a closing line; otherwise closing_line_valid = false

QUOTE_CLASSES = ("TWO_SIDED", "ONE_SIDED", "PLACEHOLDER", "NO_QUOTE", "INVALID", "MISSING")
MISSING_CAUSES = ("NO_BOARD", "GAP_TOO_LARGE", "NOT_LISTED", "ONLY_PLACEHOLDER_QUOTES", "CHAIN_BROKEN")
DECISIONS = ("TRADE", "PASS")
SIDES = ("YES", "NO")
STRATEGIES = ("PF_ALL_CANDIDATES_V1", "PF_EDGE_V1", "PF_EDGE_STRICT_V1", "MARKET_ONLY_V1", "NO_BET_V1")
CONTROL_STRATEGY = "SHADOW_PURE_PREREG_V1"        # never produced here; read-only reference

PROSPECTIVE_START_UTC = "2026-10-20T00:00:00Z"   # regular-season opener; earlier / replay records never count toward week 1

FINDING_CLASSES = ("OPERATIONAL_DEFECT", "PROJECTION_CALIBRATION_ISSUE", "EXPLORATORY_MARKET_HYPOTHESIS", "INCONCLUSIVE",
                   "EVIDENCE_AGAINST", "ELIGIBLE_FOR_PROSPECTIVE_VALIDATION")


def sha(obj: Any, n: int = 24) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:n]


def snapshot_id(board_observed_utc: str, ticker: str, horizon: str) -> str:
    return sha(["snap", board_observed_utc, ticker, horizon])


def decision_id(strategy_id: str, snap_id: str, ticker: str, side: str) -> str:
    return sha(["dec", strategy_id, snap_id, ticker, side])


def thesis_id(game_id: str, scope: str, entity: str | None, stat: str) -> str:
    """Basketball thesis the contract expresses: player-game-stat for props; team/game-level quantity for game markets."""
    return f"{game_id}|{scope}|{entity or '-'}|{stat}"
