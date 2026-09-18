"""Fill ingestion boundary: Kalshi fill objects -> canonical ``Fill`` rows, positions, and prediction matching.

This is the seam the future cross-sport fill importer plugs into: it normalises, routes non-NBA tickers
elsewhere, dedupes into the ledger and joins fills to the prediction that was live when the fill happened.
"""

from nba_edge.fills.adapter import (
    import_fills_jsonl,
    is_nba_ticker,
    match_fills_to_predictions,
    normalize_kalshi_fill,
    position_key,
    positions_from_fills,
    route_fills,
)

__all__ = [
    "import_fills_jsonl",
    "is_nba_ticker",
    "match_fills_to_predictions",
    "normalize_kalshi_fill",
    "position_key",
    "positions_from_fills",
    "route_fills",
]
