"""Append-only prospective capture of the latest official NBA injury report (+ ESPN injuries snapshot).

    python scripts/pit_capture.py --root <store>/injury_pit            # real capture (data branch)
    python scripts/pit_capture.py --root /tmp/pit_dry --dry-run        # PR dry-run: build + validate only

See src/nba_edge/availability/capture.py for the write-once / hash-chain rules.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nba_edge.availability.capture import run_capture  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    status = run_capture(Path(a.root), dry_run=a.dry_run)
    if a.dry_run:  # the real store holds only write-once captured files + MANIFEST.jsonl
        (Path(a.root) / "DRY_RUN_STATUS.json").write_text(json.dumps(status, indent=1, default=str))
    print(json.dumps(status, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
