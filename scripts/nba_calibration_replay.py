"""Preregistered NBA calibration replay (docs/research/PREREG_NBA_CALIBRATION.md). RESEARCH_ONLY.

    python scripts/nba_calibration_replay.py --shadow $SHADOW --availability $PDATA \
        --json docs/research/nba_calibration/replay.json --frozen docs/research/nba_calibration/frozen_calibrators.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from nba_edge.research import calibration as cal

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--shadow", required=True)
    ap.add_argument("--availability", required=True)
    ap.add_argument("--teams", default=str(ROOT / "data/identity/teams.csv"))
    ap.add_argument("--json", required=True)
    ap.add_argument("--frozen", required=True)
    a = ap.parse_args()
    part, props = cal.build_units(a.shadow, a.availability, a.teams)
    rep = cal.evaluate(part, props)
    allp = pd.Series(True, index=props.index)
    conf = part["status"].isin(cal.CONFIRMED_AVAILABLE)
    horizon = max(part.outcome_observed_at.max(), props.outcome_observed_at.max())
    frozen = {"schema": "nba_calibration_frozen.v1", "fitted_through_outcomes_observed_at": horizon,
              "valid_for_games_tipping_after": horizon,
              "P1_combined": cal.freeze(part, "p_overlay", ["arm", "slot"], conf, cal.EPS_PART),
              "P1_calibration_only": cal.freeze(part, "p_base", ["arm", "slot"], pd.Series(True, index=part.index), cal.EPS_PART),
              "P2_props": cal.freeze(props, "p_base", ["arm", "family"], allp, cal.EPS_PROP)}
    blob = json.dumps(frozen, indent=1, sort_keys=True) + "\n"
    Path(a.frozen).parent.mkdir(parents=True, exist_ok=True)
    Path(a.frozen).write_text(blob)
    rep["frozen_calibrators"] = {"path": a.frozen, "sha256": hashlib.sha256(blob.encode()).hexdigest(),
                                 "valid_for_games_tipping_after": horizon, "prospective_result": "PENDING"}
    Path(a.json).write_text(json.dumps(rep, indent=1, sort_keys=True, default=str) + "\n")
    print(json.dumps({k: {"verdict": v["verdict"], "overall": v["overall"], "reasons": v["reasons"][:6]}
                      for k, v in rep["decisions"].items()}, indent=1))


if __name__ == "__main__":
    main()
