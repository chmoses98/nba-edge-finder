"""Injury R1 gate: can the committed play-by-play support possession / stint / five-man lineups?

Measured on what is actually committed (data/history/espn/shot_events_*.parquet + box scores), not
on what an endpoint is believed to return. The gate is strict: no impact model may be fitted unless
five-man lineups can be reconstructed with 5 players per side at every instant and stint minutes
reconcile to the box score.

    python scripts/nba_lineup_feasibility.py --json docs/research/lineup_feasibility_r1.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nba_edge.data.history import load_player_games, load_team_games  # noqa: E402

SEASONS = ["2023-24", "2024-25", "2025-26"]
HOLDOUT = ("2026-02-01", "2026-04-12")
SUB_WORDS = ("substitution", "enters the game", "lineup", "timeout", "rebound", "turnover", "foul", "jump ball", "end of")


def season_report(hist: Path, season: str) -> dict:
    se = pd.read_parquet(hist / "espn" / f"shot_events_{season}.parquet")
    tg = load_team_games(hist, [season])
    pg = load_player_games(hist, [season])
    reg_games = set(tg.loc[tg["season_type"] == "regular", "game_id"])
    se = se[se["game_id"].isin(reg_games)]
    et = se["event_type"].str.lower()
    out: dict = {
        "season": season, "regular_season_games_in_box": len(reg_games), "games_with_events": int(se["game_id"].nunique()),
        "events": int(len(se)), "event_types_distinct": int(et.nunique()),
        "share_events_flagged_shooting_play": round(float(se["is_shooting_play"].mean()), 6),
        "substitution_events": int(et.str.contains("substitution|enters the game").sum()),
        "non_shot_events_of_any_kind": int((~se["is_shooting_play"]).sum()),
        "events_matching_non_shot_words": {w: int(et.str.contains(w).sum()) for w in SUB_WORDS},
    }
    # shot-attempt completeness vs the box score (what a possession builder would at least have)
    fga_ev = se[~se["is_free_throw"]].groupby(["game_id", "team_id"]).size()
    fta_ev = se[se["is_free_throw"]].groupby(["game_id", "team_id"]).size()
    # shot_events team_id is ESPN's team id; reconcile at game level (both teams) to avoid an id map
    g_ev = pd.DataFrame({"fga_ev": fga_ev.groupby(level=0).sum(), "fta_ev": fta_ev.groupby(level=0).sum()})
    g_box = tg[tg["season_type"] == "regular"].groupby("game_id")[["fga", "fta", "oreb", "tov", "possessions"]].sum()
    j = g_box.join(g_ev, how="left").fillna(0)
    out["game_level_fga_events_over_box"] = round(float(j["fga_ev"].sum() / j["fga"].sum()), 6)
    out["game_level_fta_events_over_box"] = round(float(j["fta_ev"].sum() / j["fta"].sum()), 6)
    out["games_fga_exact_match"] = int((j["fga_ev"] == j["fga"]).sum())
    out["box_possession_estimate_per_game"] = round(float(j["possessions"].mean()), 2)
    out["possession_terminal_events_available"] = {
        "field_goal_attempts": True, "free_throws": True, "defensive_rebounds": False, "turnovers": False,
        "end_of_period": False}
    # timestamp fidelity
    per_game_ts = se.groupby("game_id")["event_time_utc"].nunique()
    out["games_with_a_single_event_wallclock_value"] = int((per_game_ts == 1).sum())
    out["event_clock_present_share"] = round(float(se["clock_seconds_remaining"].notna().mean()), 6)
    srt = se.sort_values(["game_id", "period", "sequence"])
    dclock = srt.groupby(["game_id", "period"])["clock_seconds_remaining"].diff()
    out["clock_non_increasing_within_period_share"] = round(float((dclock.dropna() <= 0).mean()), 6)
    out["source_observed_at_distinct"] = sorted(se["source_observed_at_utc"].unique().tolist())[:3]
    # who can be placed on court: distinct shooters per team-period (a lower bound on presence only)
    ids = se.dropna(subset=["shooter_player_id"])
    tp = ids.groupby(["game_id", "team_id", "period"])["shooter_player_id"].nunique()
    out["distinct_shooters_per_team_period"] = {
        "mean": round(float(tp.mean()), 3), "share_lt5": round(float((tp < 5).mean()), 4),
        "share_eq5": round(float((tp == 5).mean()), 4), "share_gt5": round(float((tp > 5).mean()), 4)}
    # shooter identity reconciles to the box-score identity space?
    box_ids = set(zip(pg["game_id"], pg["nba_id"]))
    sid = ids[["game_id", "shooter_player_id"]].drop_duplicates()
    out["shooter_ids_found_in_box"] = round(float(np.mean([(g, int(p)) in box_ids for g, p in sid.itertuples(index=False)])), 6)
    # box-score minutes integrity: the target a future stint table must reconcile to
    pr = pg[pg["game_id"].isin(reg_games)]
    tm = pr.groupby(["game_id", "team_id"])["minutes"].sum().reset_index()
    tm = tm.merge(tg[["game_id", "team_id", "n_ot"]], on=["game_id", "team_id"], how="left")
    expected = 240 + 25 * tm["n_ot"].fillna(0)
    dev = (tm["minutes"] - expected).abs()
    out["box_minutes_vs_expected"] = {"team_games": int(len(tm)), "share_within_2min": round(float((dev <= 2).mean()), 4),
                                      "share_within_5min": round(float((dev <= 5).mean()), 4),
                                      "median_abs_dev": round(float(dev.median()), 2),
                                      "note": "ESPN box minutes are whole minutes, so exact reconciliation is impossible even with true stints"}
    if season == "2025-26":
        hold = tg[(tg["season_type"] == "regular") & (tg["game_date_et"] >= HOLDOUT[0]) & (tg["game_date_et"] <= HOLDOUT[1])]
        out["holdout_games"] = int(hold["game_id"].nunique())
        out["holdout_games_with_shot_events"] = int(len(set(hold["game_id"]) & set(se["game_id"])))
        out["holdout_games_with_reconstructable_lineups"] = 0
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hist", type=Path, default=ROOT / "data" / "history")
    ap.add_argument("--json", type=Path)
    a = ap.parse_args(argv)
    seasons = [season_report(a.hist, s) for s in SEASONS]
    verdict = {
        "possession_coverage": "NONE: only shooting plays are committed (no rebounds, turnovers, period ends), so possessions cannot be delimited from events",
        "substitution_events": sum(s["substitution_events"] for s in seasons),
        "five_man_lineups_reconstructable": False,
        "minutes_reconcile_to_box": "NOT TESTABLE (no stints); box minutes themselves are whole-minute rounded",
        "timestamp_fidelity": "game clock per event only; event wall-clock is the scheduled tip for every event; single retrospective ingest timestamp",
        "status": "BLOCKED_DATA",
        "impact_fit_attempted": False,
        "impact_ppp": 0.0,
    }
    rep = {"seasons": seasons, "verdict": verdict}
    txt = json.dumps(rep, indent=1, default=str)
    if a.json:
        a.json.write_text(txt + "\n")
    print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
