"""Data-availability matrix (counts computed from the files, not transcribed)."""
from __future__ import annotations

import gzip
import json

import pandas as pd

from . import data

R = data.ROOT


def _n_parquet(p) -> int:
    try:
        import pyarrow.parquet as pq
        return pq.ParquetFile(p).metadata.num_rows
    except Exception:  # noqa: BLE001
        return 0


def _jsonl_gz_rows(p) -> int:
    try:
        with gzip.open(p, "rt") as f:
            return sum(1 for _ in f)
    except Exception:  # noqa: BLE001
        return 0


def build(box: pd.DataFrame | None = None, cand: pd.DataFrame | None = None) -> list[dict]:
    rows = []
    if box is not None:
        seasons = f"{data.season_label(int(box['season'].min()))}..{data.season_label(int(box['season'].max()))}"
        played = int(box["played"].sum())
        rows.append({"dataset": "player box scores (minutes, pts, reb, ast, 3PM, FGA, FTA, TOV, PF)", "seasons": seasons,
                     "rows": int(len(box)), "pit_class": "reconstructable",
                     "notes": f"ESPN box via sportsdataverse mirror (hoopR) + repo data/history/espn (2023-24..2025-26; "
                              f"agree row-for-row on 2024-25: 32,610/32,610 rows, minutes identical). {played:,} played "
                              f"player-games, regular season only. Outcomes; used as features only after lagging."})
        rows.append({"dataset": "usage proxy (FGA + 0.44 FTA + TOV)", "seasons": seasons, "rows": played,
                     "pit_class": "reconstructable", "notes": "True usage% needs on-court team possessions; PBP stints exist "
                     "only for 2024-25/2025-26 (data/history/espn_pbp)."})
        tg = box.drop_duplicates(["game_id", "team"])
        rows.append({"dataset": "team box / pace (possessions = 0.96*(FGA+0.44FTA-OREB+TOV))", "seasons": seasons,
                     "rows": int(len(tg)), "pit_class": "reconstructable",
                     "notes": "Derived from player box sums; team points from the ESPN team score."})
        rows.append({"dataset": "starting lineups", "seasons": seasons, "rows": int(box["started"].sum()),
                     "pit_class": "retrospective",
                     "notes": "Box 'starter' flag is post-game. No archived pregame lineup for 2014-2026; only prior start "
                              "rates are used as features. Value of knowing starters quantified as an oracle."})
    if cand is not None:
        absent = int((~cand["in_box"]).sum())
        rows.append({"dataset": "pregame candidate pool (played for team in previous 10 games)", "seasons": "2014-15..2025-26",
                     "rows": int(len(cand)), "pit_class": "reconstructable",
                     "notes": f"{absent:,} synthetic rows for players absent from the box (inactive/injured/G-League). "
                              "Whether a player plays or starts is NOT pregame information without an archived report."})
    ir = R / "data/history/injury_reports"
    rows.append({"dataset": "official NBA injury reports (PDF, timestamped)", "seasons": "2025-26 only",
                 "rows": _n_parquet(ir / "report_rows_2025-26.parquet"), "pit_class": "archived",
                 "notes": "1,320/1,322 games have a certified pre-tip snapshot (T-60 and last pre-tip). 2014-15..2024-25: "
                          "missing (box DNP reasons are retrospective)."})
    rows.append({"dataset": "ESPN injuries / rosters / schedule captures", "seasons": "2026-27 preseason (from 2026-10-12)",
                 "rows": 0, "pit_class": "archived",
                 "notes": "data-injury-pit and data-archive branches (context/injuries, rosters, schedule; every capture "
                          "time-stamped). Used for the forward slate."})
    rows.append({"dataset": "rest / back-to-back / 3-in-4", "seasons": "2014-15..2025-26", "rows": 0,
                 "pit_class": "reconstructable", "notes": "From the schedule (dates of earlier games)."})
    rows.append({"dataset": "travel distance / time zones", "seasons": "-", "rows": 0, "pit_class": "missing",
                 "notes": "No arena coordinates table in the repo; reconstructable with a static 30-row table (not built)."})
    pbp = R / "data/history/espn_pbp"
    rows.append({"dataset": "play-by-play stints (on-court five-man units)", "seasons": "2024-25, 2025-26",
                 "rows": _n_parquet(pbp / "stints_2024-25.parquet") + _n_parquet(pbp / "stints_2025-26.parquet"),
                 "pit_class": "reconstructable", "notes": "Not used here (only two seasons; would feed lineup/on-off features)."})
    rows.append({"dataset": "archived pregame forecasts (incumbent)", "seasons": "2026-27 preseason; 2025-26 sample",
                 "rows": _n_parquet(R / "data/research/minutes_validation.parquet"), "pit_class": "archived",
                 "notes": "nba-shadow-pure branch holds frozen PURE forecasts from Oct 2026; minutes_validation.parquet holds "
                          "3,676 2025-26 player-games (old/new/EWM-5). Historical incumbent forecasts are REPRODUCED "
                          "walk-forward here from src/nba_edge (features.build + sim.engine), 2022-23..2025-26."})
    kal = R / "data/history/kalshi"
    n_k = 0
    for p in kal.glob("markets_*.jsonl.gz"):
        n_k += _jsonl_gz_rows(p)
    rows.append({"dataset": "Kalshi NBA markets + candles (props, spreads, totals)", "seasons": "2025-26",
                 "rows": n_k, "pit_class": "archived",
                 "notes": f"market_table.parquet has {_n_parquet(R / 'data/research/market_table.parquet'):,} pregame quote rows. "
                          "No pregame point spread/total exists for 2014-15..2024-25 (blowout risk uses PIT rating-based "
                          "expected margin instead)."})
    rows.append({"dataset": "shot-profile PIT features", "seasons": "2023-24..2025-26",
                 "rows": _n_parquet(R / "data/research/shot_profile_pit_features_clean.parquet"), "pit_class": "reconstructable",
                 "notes": "Not used (3 seasons; prior study found no robust gain)."})
    return rows
