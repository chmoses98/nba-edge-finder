#!/usr/bin/env python3
"""Publish the Edge Finder app export (edge_finder.app.v1) from the NBA archive.

    python scripts/app_export.py --out <app_root> [--data-root data/archive] [--accounting-dir <accounting-data checkout>]
                                 [--now <iso>] [--commit-sha X] [--workflow-run-id Y]

Thin wrapper over ``nba_edge.app_export`` (also reachable as ``nba app-export``). Read-only over every input;
on any failure it writes health.json alone (export_failed=true), keeps the last-known-good payload and exits 1.
"""

from __future__ import annotations

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "contract"))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

from nba_edge.app_export import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
