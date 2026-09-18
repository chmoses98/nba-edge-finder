from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import Field

from nba_edge.schemas.core import Strict


class View(StrEnum):
    DATA_ONLY = "DATA_ONLY"
    MARKET_BASELINE = "MARKET_BASELINE"
    HYBRID = "HYBRID"
    PRODUCTION = "PRODUCTION"


class Authority(StrEnum):
    RESEARCH = "RESEARCH"
    SHADOW = "SHADOW"
    LIMITED = "LIMITED"
    TRUSTED = "TRUSTED"


class Gate(StrEnum):
    OK = "OK"
    NO_EDGE = "NO_EDGE"
    CANNOT_TRUST_INPUTS = "CANNOT_TRUST_INPUTS"
    UNSUPPORTED = "UNSUPPORTED"


class ContractPrediction(Strict):
    """Immutable prediction record. One row per (ticker, prediction_ts, model_version)."""
    prediction_id: str  # sha256 of key fields
    ticker: str
    game_id: str | None
    family: str
    predicted_at_utc: datetime
    data_cutoff_utc: datetime
    model_version: str
    sim_version: str
    feature_version: str
    n_sims: int
    p_data_only: float | None = None
    p_market: float | None = None
    p_hybrid: float | None = None
    p_production: float | None = None
    p_data_only_se: float | None = None  # Monte Carlo standard error
    market_observed_at_utc: datetime | None = None
    market_yes_bid: int | None = None
    market_yes_ask: int | None = None
    market_no_bid: int | None = None
    market_no_ask: int | None = None
    gate: Gate = Gate.UNSUPPORTED
    gate_reasons: list[str] = Field(default_factory=list)
    authority: Authority = Authority.RESEARCH
    support: str = "UNRESOLVED"
    pregame: bool = True  # False if predicted_at >= effective tip (never used for pregame evaluation)
    thesis_group: str | None = None
    input_snapshot_ids: dict[str, str] = Field(default_factory=dict)
