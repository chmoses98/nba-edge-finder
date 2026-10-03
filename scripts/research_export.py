#!/usr/bin/env python3
"""Publish the Edge Finder research explorer (contract 1.1.0) beside the v1 app export.

    python scripts/research_export.py --out <app_root> [--data-root data/archive] [--history-root data]
                                      [--now <iso>] [--commit-sha X]

Thin wrapper over ``nba_edge.research_export`` (also reachable as ``nba research-export``). Read-only over every
input; run it AFTER ``app_export`` (it takes the run id and clock from ``<app_root>/manifest.json``). On any failure
it exits 1 and the previous ``explorer/`` tree and every v1 file stay untouched.
"""

from __future__ import annotations

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "contract"))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

from nba_edge.research_export import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
