"""The only sanctioned way to read reconstructed lineup stints.

``scripts/lineup_certify.py`` writes certified AND uncertified stints into the same ``stints_<season>.parquet``, distinguished by a boolean
``certified`` column. 89.9% (2025-26) and 95.6% (2024-25) of the uncertified games contain only well-formed 5-man stints, so an uncertified game
is indistinguishable from a good one by inspection -- the flag is the only thing standing between a consumer and a game whose minutes, score or
substitutions failed the CORE checks. A convention in a docstring is not enforcement, so consumers go through here.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class UncertifiedStintsError(ValueError):
    pass


def certified_only(stints: pd.DataFrame) -> pd.DataFrame:
    """Rows of certified games. A frame with no ``certified`` column is refused: its provenance cannot be established."""
    if "certified" not in stints.columns:
        raise UncertifiedStintsError("stints frame has no `certified` column; refusing to treat it as certified")
    return stints[stints["certified"].astype(bool)].copy()


def require_certified(stints: pd.DataFrame) -> None:
    """Raise when a frame that carries the flag contains any uncertified row (frames without the flag are the caller's responsibility)."""
    if "certified" in stints.columns and not stints["certified"].astype(bool).all():
        n = int((~stints["certified"].astype(bool)).sum())
        raise UncertifiedStintsError(f"{n} stint row(s) from uncertified games were passed to a consumer that requires certified stints")


def load_certified(path: Path) -> pd.DataFrame:
    return certified_only(pd.read_parquet(path))
