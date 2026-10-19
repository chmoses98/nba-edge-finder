"""Load the versioned paper-trading protocol (paper_config.json) and its sha256 (stamped into every record as `config_sha`)."""
from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

PATH = Path(__file__).with_name("paper_config.json")


@lru_cache(maxsize=4)
def _load(path: str) -> tuple[dict, str]:
    raw = Path(path).read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def load(path: str | Path | None = None) -> dict:
    """A private copy of the protocol (callers cannot mutate the cached one)."""
    return json.loads(json.dumps(_load(str(path or PATH))[0]))


def config_sha(path: str | Path | None = None) -> str:
    return _load(str(path or PATH))[1]
