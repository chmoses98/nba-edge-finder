"""Ages of the STATUS_*.json breadcrumbs each workflow drops, with no third-party imports.

This module exists to keep the conductor cheap. The conductor runs 144x/day purely to answer
"is anything worth doing right now?", and the answer depends only on a handful of timestamps on
disk. It used to reach this helper through ``nba_edge.archive.capture``, which imports the Kalshi
client, which imports httpx -- so the decision job had to ``pip install -e .`` (a ~690MB
environment, ~23s) before it could read a JSON file. Everything here is stdlib, so the decide job
can run against ``PYTHONPATH=src`` with no install at all.

Keep it that way: nothing in this module may import a third-party package, directly or
transitively. ``tests/test_conductor.py`` enforces this.
"""

from __future__ import annotations

import json
from pathlib import Path

from nba_edge.timeutil import parse_iso, utcnow


def status_age_minutes(path: Path, key: str) -> float | None:
    """Minutes since the timestamp at ``key`` in ``path``, or None if absent/unreadable.

    None means "we have no idea when this last ran", which every caller must treat as
    "possibly never" -- i.e. as a reason to run, not as a reason to skip.
    """
    if not path.exists():
        return None
    try:
        ts = parse_iso(json.loads(path.read_text())[key])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    return (utcnow() - ts).total_seconds() / 60
