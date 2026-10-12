"""Certify (or not) five-man lineups reconstructed from the full ESPN play-by-play, per game.

Reads data/history/espn_pbp/pbp_{events,box,games}_<season>.parquet (written by scripts/pbp_backfill.py),
runs :func:`nba_edge.pbp.lineups.reconstruct_game` on every game and writes:

* docs/research/lineup_pbp/certification_<season>.csv   per-game pass flags, reasons and metrics
* data/history/espn_pbp/stints_<season>.parquet          stint table (both lineups, seconds, points,
                                                          possessions) with the game's certified flag
* docs/research/lineup_pbp/summary.json                  pass rates per check / season / season type,
                                                          minutes / possession / timestamp distributions

No model is fitted. Deterministic; no network.

    python scripts/lineup_certify.py --seasons 2025-26,2024-25
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nba_edge.pbp.ingest import paths, write_compact  # noqa: E402
from nba_edge.pbp.lineups import (  # noqa: E402
    MINUTES_TOL,
    POSS_TOL,
    period_length,
    reconstruct_game,
)

CHECKS = ["five_on_court", "starters_ok", "period_starts_ok", "minutes_ok", "score_ok", "no_offcourt",
          "subs_consistent", "plus_minus_ok", "possessions_ok", "clock_ok"]


def _q(s: pd.Series, qs=(0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99)) -> dict[str, float]:
    s = pd.to_numeric(s, errors="coerce").dropna()
    return {f"q{int(q * 100):02d}": round(float(s.quantile(q)), 4) for q in qs} if len(s) else {}


def timestamp_fidelity(ev: pd.DataFrame) -> dict:
    """Clock / wallclock fidelity over all events and over substitutions specifically."""
    ev = ev.sort_values(["game_id", "order"])
    out: dict = {"events": int(len(ev))}
    out["clock_present_share"] = round(float(ev["clock_s"].notna().mean()), 6)
    out["wallclock_present_share"] = round(float(ev["wallclock_utc"].notna().mean()), 6)
    wc = pd.to_datetime(ev["wallclock_utc"], utc=True, errors="coerce")
    d_wc = wc.groupby(ev["game_id"]).diff().dt.total_seconds()
    out["wallclock_non_decreasing_share"] = round(float((d_wc.dropna() >= 0).mean()), 6)
    d_clk = ev.groupby(["game_id", "period"])["clock_s"].diff()
    out["clock_non_increasing_within_period_share"] = round(float((d_clk.dropna() <= 1e-6).mean()), 6)
    is_sub = ev["type_text"].str.lower().eq("substitution")
    subs = ev[is_sub]
    out["substitutions"] = int(len(subs))
    out["sub_clock_present_share"] = round(float(subs["clock_s"].notna().mean()), 6) if len(subs) else None
    out["sub_wallclock_present_share"] = round(float(subs["wallclock_utc"].notna().mean()), 6) if len(subs) else None
    # a substitution happens at a dead ball, so its clock should equal the previous non-sub event's clock
    prev_clock = ev["clock_s"].where(~is_sub).groupby([ev["game_id"], ev["period"]]).ffill()
    prev_clock = prev_clock.groupby([ev["game_id"], ev["period"]]).shift(1)
    same = (subs["clock_s"] - prev_clock[is_sub]).abs() <= 1e-6
    period_start = subs["clock_s"] == subs["period"].map(lambda p: period_length(int(p)) if p == p else np.nan)
    out["sub_clock_equals_previous_event_share"] = round(float((same | period_start).mean()), 6) if len(subs) else None
    out["subs_with_both_participants_share"] = round(float((subs["p1"].notna() & subs["p2"].notna()).mean()), 6) if len(subs) else None
    # wallclock gap from the sub to the next non-sub event (s): how tightly ESPN timestamps it
    nxt = wc.where(~is_sub).groupby(ev["game_id"]).bfill()
    gap = (nxt[is_sub] - wc[is_sub]).dt.total_seconds()
    out["sub_wallclock_to_next_play_seconds"] = _q(gap)
    return out


def certify_season(hist: Path, season: str, out_dir: Path) -> dict:
    p = paths(hist, season)
    if not p["games"].exists():
        return {"season": season, "error": "no pbp data"}
    ev = pd.read_parquet(p["events"])
    bx = pd.read_parquet(p["box"])
    gm = pd.read_parquet(p["games"])
    ev_by = {g: d.sort_values("order").to_dict("records") for g, d in ev.groupby("game_id", sort=False)}
    bx_by = {g: d.to_dict("records") for g, d in bx.groupby("game_id", sort=False)}
    rows, stints, min_diffs = [], [], []
    offcourt_types: Counter = Counter()
    for g in gm.to_dict("records"):
        gid = g["game_id"]
        r = reconstruct_game(ev_by.get(gid, []), bx_by.get(gid, []), g)
        row = {"game_id": gid, "season": season, "season_type": g["season_type"], "start_time_utc": g["start_time_utc"],
               "fetched_at_utc": g["fetched_at_utc"], "source": g["source"], "certified": r["certified"],
               "certified_strict": r["certified_strict"], **r["checks"], "reasons": ";".join(r["reasons"]),
               **{k: v for k, v in r["metrics"].items() if not isinstance(v, dict)}}
        rows.append(row)
        for s in r["stints"]:
            stints.append({**s, "certified": r["certified"]})
        min_diffs.extend(r["player_minutes_diff"].values())
        offcourt_types.update(r["offcourt_event_types"])
    cert = pd.DataFrame(rows).sort_values(["start_time_utc", "game_id"])
    out_dir.mkdir(parents=True, exist_ok=True)
    cert.to_csv(out_dir / f"certification_{season}.csv", index=False)
    st = pd.DataFrame(stints)
    for c in [c for c in st.columns if c.endswith(tuple(f"_p{i}" for i in range(1, 6)))]:
        st[c] = st[c].astype("Int32")
    write_compact(st, p["dir"] / f"stints_{season}.parquet")

    def rates(df: pd.DataFrame) -> dict:
        return {"games": int(len(df)), "certified": int(df["certified"].sum()),
                "certified_share": round(float(df["certified"].mean()), 4) if len(df) else None,
                "certified_strict": int(df["certified_strict"].sum()),
                "certified_strict_share": round(float(df["certified_strict"].mean()), 4) if len(df) else None,
                "check_pass_share": {c: round(float(df[c].mean()), 4) for c in CHECKS}}

    md = pd.Series(min_diffs, dtype=float)
    reasons = Counter(r.split("=")[0].split("(")[0] for rs in cert["reasons"] for r in rs.split(";") if r)
    return {
        "season": season, "all": rates(cert),
        "by_season_type": {k: rates(d) for k, d in cert.groupby("season_type")},
        "failure_reasons": dict(reasons.most_common()),
        "player_minutes_diff_stint_minus_box": {
            "players": int(len(md)), "within_tol_share": round(float((md.abs() <= MINUTES_TOL + 1e-9).mean()), 6),
            "within_0.5_share": round(float((md.abs() <= 0.5).mean()), 6), "mean": round(float(md.mean()), 4),
            **_q(md)},
        "possession_ratio_pbp_over_box_estimate": {"mean": round(float(cert["possession_ratio"].mean()), 4),
                                                   **_q(cert["possession_ratio"])},
        "plus_minus_players_exact_share": round(float(cert["plus_minus_players_exact"].sum()
                                                       / max(1, cert["plus_minus_players"].sum())), 6),
        "plus_minus_players_exact_share_event_rule": round(float(cert["plus_minus_players_exact_event_rule"].sum()
                                                                  / max(1, cert["plus_minus_players"].sum())), 6),
        "offcourt_participation_event_types_top15": dict(offcourt_types.most_common(15)),
        "carryover_period_starts": int(cert["carryover_period_starts"].sum()),
        "q1_inferred_matches_box_starters_share": round(float(cert["q1_inferred_matches_box_starters"].mean()), 4),
        "stints": int(len(st)), "stints_in_certified_games": int(st["certified"].sum()) if len(st) else 0,
        "timestamp_fidelity": timestamp_fidelity(ev),
        "event_type_counts_top60": {str(k): int(v) for k, v in ev["type_text"].value_counts().head(60).items()},
        "fetched_at_range": [str(gm["fetched_at_utc"].min()), str(gm["fetched_at_utc"].max())],
        "subs_per_game_mean": round(float(ev["type_text"].str.lower().eq("substitution").sum() / max(1, len(gm))), 2),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hist", default=str(ROOT / "data" / "history"))
    ap.add_argument("--seasons", default="2025-26,2024-25")
    ap.add_argument("--out", default=str(ROOT / "docs" / "research" / "lineup_pbp"))
    a = ap.parse_args()
    out = Path(a.out)
    summary = {"tolerances": {"minutes_abs_per_player": MINUTES_TOL, "possessions_rel": POSS_TOL},
               "seasons": {}}
    for s in [x.strip() for x in a.seasons.split(",") if x.strip()]:
        summary["seasons"][s] = certify_season(Path(a.hist), s, out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=1, default=str))
    print(json.dumps({s: v.get("all", v) for s, v in summary["seasons"].items()}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
