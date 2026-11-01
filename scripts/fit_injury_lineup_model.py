"""Fit certified 2024-25 NBA lineup model; write a shadow-only JSON artifact.

Do not use 2025-26 holdout stints for fitting. The generated model is not
eligible for production until the paired PIT holdout and live replay pass.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from nba_edge.config import REPO_ROOT
from nba_edge.research.lineup_impact import fit_lineup_impact


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--history", type=Path, default=REPO_ROOT / "data" / "history")
    ap.add_argument("--out", type=Path, default=Path("/tmp/nba_lineup_injury_model_2024-25.json"))
    a = ap.parse_args()
    tg = pd.read_parquet(a.history / "espn" / "team_games_2024-25.parquet")
    st = pd.read_parquet(a.history / "espn_pbp" / "stints_2024-25.parquet")
    model = fit_lineup_impact(st, tg, "2025-07-01")
    if model.n_players < 100 or model.n_games < 1000:
        raise RuntimeError(f"insufficient certified historical lineup coverage: {model}")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(asdict(model), indent=2))
    print(json.dumps({"n_games": model.n_games, "n_stints": model.n_stints,
                      "n_players": model.n_players, "training_cutoff": model.training_cutoff,
                      "artifact": str(a.out), "production_authority": "NONE"}))


if __name__ == "__main__":
    main()
