"""Replay archived NBA shadow projections with and without the PIT availability overlay (RESEARCH_ONLY).

Inputs are local copies of three archive branches of this repo (no network inside the run):

    git archive origin/nba-shadow-pure projections outcomes | tar -x -C $SHADOW
    git archive origin/projection-data availability        | tar -x -C $PDATA
    python scripts/nba_availability_replay.py --shadow $SHADOW --availability $PDATA \
        --json docs/research/availability_overlay/replay.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nba_edge.research.availability_replay import evaluate

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--shadow", required=True, help="local copy of the nba-shadow-pure branch")
    ap.add_argument("--availability", required=True, help="local copy of the projection-data branch")
    ap.add_argument("--teams", default=str(ROOT / "data/identity/teams.csv"))
    ap.add_argument("--arms", default="sim_rotation,ewm5")
    ap.add_argument("--json", required=True)
    a = ap.parse_args()
    rep = evaluate(a.shadow, a.availability, a.teams, arms=tuple(a.arms.split(",")))
    Path(a.json).parent.mkdir(parents=True, exist_ok=True)
    Path(a.json).write_text(json.dumps(rep, indent=1, sort_keys=True) + "\n")
    print(json.dumps({arm: {w: {s: {k: v for k, v in x["deltas"].items() if k.startswith("overlay")} for s, x in r[w]["by_slot"].items()}
                            for w in r} for arm, r in rep["arms"].items()}, indent=1)[:6000])


if __name__ == "__main__":
    main()
