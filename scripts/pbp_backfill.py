"""Backfill the FULL ESPN play-by-play (all event types) into data/history/espn_pbp/ (research data).

Resumable and idempotent: games already listed in pbp_done_<season>.json / pbp_games_<season>.parquet
are skipped. Must run where site.api.espn.com is reachable (GitHub Actions; the dev container is
denied). See src/nba_edge/pbp/ingest.py for outputs and provenance fields.

    python scripts/pbp_backfill.py --seasons 2025-26,2024-25 [--max-games N]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nba_edge.pbp.ingest import run_full_pbp_pull  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "data" / "history"))
    ap.add_argument("--seasons", default="2025-26,2024-25")
    ap.add_argument("--max-games", type=int, default=0, help="cap on NEW games per season (0 = no cap)")
    ap.add_argument("--max-minutes", type=float, default=0, help="time budget; 0 = none")
    a = ap.parse_args()
    man = run_full_pbp_pull(Path(a.out), a.seasons.split(","), max_games=a.max_games or None,
                            max_minutes=a.max_minutes or None)
    print(json.dumps({k: v for k, v in man.items() if k != "errors"}, indent=1))
    print("errors:", len(man.get("errors", [])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
