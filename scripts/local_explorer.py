#!/usr/bin/env python
"""Build the research explorer locally from a published v1 app export and a history root, for inspection and for SIFT fixtures.

    python scripts/local_explorer.py --app-root <dir with manifest.json, events.json, markets.json> --history-root <dir holding history/espn and research/> \
        --out <dir>

Copies the v1 files into --out and writes --out/explorer/ with the production exporter (nba_edge.research_export), so what SIFT reads is exactly what the
worker would publish for that history. --data-root defaults to an empty archive (no rosters, injuries or price paths: the exporter records the warning)."""
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from nba_edge.research_export import export_explorer


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app-root", required=True)
    ap.add_argument("--history-root", required=True)
    ap.add_argument("--data-root", default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for f in Path(a.app_root).glob("*.json"):
        shutil.copy(f, out / f.name)
    data_root = Path(a.data_root) if a.data_root else Path(tempfile.mkdtemp(prefix="nba-empty-archive-"))
    index = export_explorer(out, data_root, history_root=Path(a.history_root))
    print(f"explorer: {index['counts']} as_of={index.get('as_of')} -> {out / 'explorer'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
