"""Runtime configuration. Everything here is environment-driven and documented in .env.example."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _env(name: str, default: str = "") -> str:
    v = os.environ.get(name)
    return v if v not in (None, "") else default


@dataclass(frozen=True)
class Settings:
    kalshi_base_url: str = field(default_factory=lambda: _env("KALSHI_BASE_URL", "https://api.elections.kalshi.com/trade-api/v2"))
    kalshi_api_key_id: str = field(default_factory=lambda: _env("KALSHI_API_KEY_ID"))
    kalshi_private_key_path: str = field(default_factory=lambda: _env("KALSHI_PRIVATE_KEY_PEM_PATH"))
    odds_api_key: str = field(default_factory=lambda: _env("ODDS_API_KEY"))
    data_root: Path = field(default_factory=lambda: Path(_env("NBA_EDGE_DATA_ROOT", str(REPO_ROOT / "data"))))
    cache_root: Path = field(default_factory=lambda: Path(_env("NBA_EDGE_CACHE_ROOT", str(REPO_ROOT / ".cache"))))
    http_timeout_s: float = 30.0
    http_max_retries: int = 4
    user_agent: str = "nba-edge-finder/0.1 (+https://github.com/chmoses98/nba-edge-finder)"

    @property
    def catalog_dir(self) -> Path:
        return self.data_root / "catalog"

    @property
    def identity_dir(self) -> Path:
        return self.data_root / "identity"

    @property
    def archive_dir(self) -> Path:
        return self.data_root / "archive"


def settings() -> Settings:
    return Settings()
