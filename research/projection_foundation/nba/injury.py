"""Archived point-in-time official injury reports (2025-26 only; data/history/injury_reports).

`snapshot_status(tag)` returns, per (game_id, pid), the status printed in the report selected for that game
by the certified snapshot (`t_minus_60`: latest report uploaded before tip-60min; `last_pre_tip`: latest
before tip). Players not listed are implicitly AVAILABLE. Only `pit_ok` snapshots are used.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import data

DIR = data.ROOT / "data" / "history" / "injury_reports"


def snapshot_status(tag: str = "t_minus_60") -> pd.DataFrame:
    rows = pd.read_parquet(DIR / "report_rows_2025-26.parquet")
    snap = pd.read_parquet(DIR / "game_snapshots_2025-26.parquet")
    snap = snap[snap[f"{tag}_pit_ok"] & (snap["season_type"] == "regular")]
    m = rows.merge(snap[["game_id", f"{tag}_report_time_utc"]], on="game_id")
    m = m[(m["report_time_utc"] == m[f"{tag}_report_time_utc"]) & m["nba_id"].notna()]
    m = m[m["status"].isin(["out", "doubtful", "questionable", "probable", "available"])]
    out = pd.DataFrame({"game_id": m["game_id"].str[5:].astype(np.int64), "pid": (-m["nba_id"]).astype(np.int64),
                        "inj_status": m["status"].str.upper(), "inj_report_utc": m["report_time_utc"]})
    games = pd.DataFrame({"game_id": snap["game_id"].str[5:].astype(np.int64)})
    return out.drop_duplicates(["game_id", "pid"]), games


def pit_absence(c: pd.DataFrame, status: pd.DataFrame, games: pd.DataFrame,
                out_states=("OUT", "DOUBTFUL")) -> pd.DataFrame:
    """PIT version of features.teammate_absence for games with a certified snapshot."""
    c = c.merge(status[["game_id", "pid", "inj_status"]], on=["game_id", "pid"], how="left")
    c["inj_status"] = c["inj_status"].fillna("AVAILABLE")
    c["has_snapshot"] = c["game_id"].isin(set(games["game_id"]))
    out = c["inj_status"].isin(out_states)
    lvl = c["minutes_p_ewm8"].fillna(0.0)
    use = c["usage_p_ewm8"].fillna(0.0)
    new = out & (c["missed_streak"] == 0) & c["last_min"].notna()
    c = c.assign(_om=np.where(out, lvl, 0.0), _ou=np.where(out, use, 0.0), _nm=np.where(new, lvl, 0.0))
    agg = c.groupby(["game_id", "team"])[["_om", "_ou", "_nm"]].transform("sum")
    pos = c.groupby(["game_id", "team", "pos"])["_om"].transform("sum")
    c["out_min_pit"] = agg["_om"] - c["_om"]
    c["out_usage_pit"] = agg["_ou"] - c["_ou"]
    c["out_new_min_pit"] = agg["_nm"] - c["_nm"]
    c["out_pos_min_pit"] = pos - c["_om"]
    return c.drop(columns=["_om", "_ou", "_nm"])
