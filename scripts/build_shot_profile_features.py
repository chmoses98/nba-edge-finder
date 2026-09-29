"""Build the point-in-time shot-profile feature table.

Exists so the feature table is REPRODUCIBLE. The first version of this table was built by hand at a prompt,
which is how a 45,414-row preseason block ended up inside a study with nothing recording that it was there.
The population is now a named, printed argument.

    --population research   regular + play-in + playoffs (the default)
    --population all        every stored event, preseason included -- the pre-migration corpus, kept so the
                            contaminated result can be reproduced and compared rather than just described
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--history", default="data/history")
    ap.add_argument("--seasons", default="2023-24,2024-25,2025-26")
    ap.add_argument("--population", choices=["research", "all", "preseason_only"], default="research")
    ap.add_argument("--out", default="data/research/shot_profile_pit_features.parquet")
    a = ap.parse_args()

    from nba_edge.research.shot_profile_features_pit import build_pit_features
    from nba_edge.shotprofile.ingest import load_shot_events

    seasons = [s.strip() for s in a.seasons.split(",")]
    rep: dict = {}
    if a.population == "all":
        shots = load_shot_events(Path(a.history), seasons, all_season_types=True, report=rep)
    elif a.population == "preseason_only":
        shots = load_shot_events(Path(a.history), seasons, season_types=("preseason",), report=rep)
    else:
        shots = load_shot_events(Path(a.history), seasons, report=rep)

    ft = build_pit_features(shots)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    ft.to_parquet(out, engine="pyarrow", index=False)

    print(json.dumps({
        "population": a.population, "seasons": seasons, "shot_events_used": int(len(shots)),
        "population_report": rep, "feature_rows": int(len(ft)),
        "games": int(ft.game_id.nunique()) if len(ft) else 0,
        "players": int(ft.player_id.nunique()) if len(ft) else 0,
        "out": str(out),
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
