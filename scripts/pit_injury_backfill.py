"""Backfill official NBA injury reports for a season and write the coverage report.

Runs where ak-static.cms.nba.com is reachable (GitHub Actions). Resumable and time-budgeted: each run
stops starting new work after --max-minutes and the next run continues (probe cache + parquet).

    python scripts/pit_injury_backfill.py --season 2025-26 --max-minutes 20
    python scripts/pit_injury_backfill.py --season 2025-26 --report-only   # coverage from committed data

Coverage output: docs/research/pit_availability/coverage_<season>.json. The post-game box score is read
ONLY to validate the parser/mapping (did players listed Out actually sit?), never as an input row.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nba_edge.availability.backfill import paths, run_backfill  # noqa: E402


def _q(s: pd.Series) -> dict:
    s = pd.to_numeric(s, errors="coerce").dropna()
    return {f"q{int(q * 100):02d}": round(float(s.quantile(q)), 2) for q in (0.01, 0.1, 0.5, 0.9, 0.99)} if len(s) else {}


def coverage(out_root: Path, hist: Path, season: str) -> dict:
    p = paths(out_root, season)
    if not p["games"].exists():
        return {"season": season, "error": "no snapshots"}
    g = pd.read_parquet(p["games"])
    rep = pd.read_parquet(p["reports"]) if p["reports"].exists() else pd.DataFrame()
    rows = pd.read_parquet(p["rows"]) if p["rows"].exists() else pd.DataFrame()
    out: dict = {"season": season, "games": int(len(g)),
                 "games_by_season_type": {k: int(v) for k, v in g["season_type"].value_counts().items()},
                 "reports_fetched": int(len(rep)), "rows": int(len(rows))}
    for tag in ("last_pre_tip", "t_minus_60"):
        d = {"located": int(g[f"{tag}_slot_et"].notna().sum()),
             "nominal_before_tip": int(g[f"{tag}_nominal_before_tip"].sum()),
             "published_before_tip": int(g[f"{tag}_published_before_tip"].sum()),
             "game_listed_in_report": int((g[f"{tag}_rows_for_game"] > 0).sum()),
             "both_teams_listed": int((g[f"{tag}_teams_listed"] >= 2).sum()),
             "pit_ok": int(g[f"{tag}_pit_ok"].sum()),
             "pit_ok_share": round(float(g[f"{tag}_pit_ok"].mean()), 4),
             "lead_minutes": _q(g[f"{tag}_lead_minutes"])}
        pub = pd.to_datetime(g[f"{tag}_published_utc"], utc=True, errors="coerce")
        nom = pd.to_datetime(g[f"{tag}_report_time_utc"], utc=True, errors="coerce")
        d["publish_lag_seconds"] = _q((pub - nom).dt.total_seconds())
        d["by_month_pit_ok_share"] = {str(k): round(float(v), 4) for k, v in
                                      g.groupby(g["game_date_et"].str[:7])[f"{tag}_pit_ok"].mean().items()}
        out[tag] = d
    if len(rep):
        out["reports"] = {
            "header_time_matches_slot_share": round(float(rep["header_time_matches_slot"].mean()), 4),
            "rows_missing_team": int(rep["rows_missing_team"].sum()),
            "rows_missing_game": int(rep["rows_missing_game"].sum()),
            "pages_without_header": int(rep["pages_without_header"].sum()),
            "url_patterns": {k: int(v) for k, v in rep["url"].str.extract(r"_(\d{2}(?:_\d{2})?[AP]M)\.pdf$")[0]
                             .str.contains("_").map({True: "HH_MM", False: "HH"}).value_counts().items()},
            "unresolved_team_text": sorted({t for x in rep.get("unresolved_team_text", pd.Series(dtype=str)).fillna("")
                                            for t in str(x).split("|") if t})[:30]}
    if len(rows):
        pl = rows[rows["player_name_raw"].notna()]
        out["player_rows"] = int(len(pl))
        out["status_counts"] = {k: int(v) for k, v in rows["status"].value_counts().items()}
        out["rows_with_game_id_share"] = round(float(rows["game_id"].notna().mean()), 4)
        mm = pl["match_method"].value_counts()
        out["player_match"] = {"matched_share": round(float(pl["nba_id"].notna().mean()), 4),
                               "by_method": {k: int(v) for k, v in mm.items()}}
        distinct = pl.drop_duplicates(["team_id", "player_name_raw"])
        out["player_match"]["distinct_names"] = int(len(distinct))
        out["player_match"]["distinct_names_matched_share"] = round(float(distinct["nba_id"].notna().mean()), 4)
        out["player_match"]["unmatched_examples"] = (distinct[distinct["nba_id"].isna()]["player_name_raw"]
                                                     .value_counts().head(25).index.tolist())
        # validation only: players listed OUT in the last pre-tip report vs whether they logged minutes
        pg = pd.read_parquet(hist / "espn" / f"player_games_{season}.parquet")
        played = {(str(a), int(b)) for a, b, c in pg[["game_id", "nba_id", "minutes"]].itertuples(index=False) if c > 0}
        last = g[g["last_pre_tip_pit_ok"]][["game_id", "last_pre_tip_slot_et"]]
        j = pl.merge(last, left_on=["game_id", "slot_et"], right_on=["game_id", "last_pre_tip_slot_et"])
        j = j[j["nba_id"].notna()]
        val = {}
        for st in ("out", "doubtful", "questionable", "probable", "available"):
            d = j[j["status"] == st]
            if len(d):
                val[st] = {"n": int(len(d)), "played_share": round(float(
                    sum((str(a), int(b)) in played for a, b in d[["game_id", "nba_id"]].itertuples(index=False)) / len(d)), 4)}
        out["validation_played_share_by_last_pre_tip_status"] = val
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", default="2025-26")
    ap.add_argument("--out", default=str(ROOT / "data" / "history"))
    ap.add_argument("--hist", default=str(ROOT / "data" / "history"))
    ap.add_argument("--max-minutes", type=float, default=20.0)
    ap.add_argument("--date-from")
    ap.add_argument("--date-to")
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--report-dir", default=str(ROOT / "docs" / "research" / "pit_availability"))
    a = ap.parse_args()
    if not a.report_only:
        man = run_backfill(Path(a.out), Path(a.hist), a.season, date_from=a.date_from, date_to=a.date_to,
                           max_minutes=a.max_minutes)
        print(json.dumps({k: v for k, v in man.items() if k != "errors"}, indent=1))
        for e in man.get("errors", [])[:10]:
            print("error:", e)
    cov = coverage(Path(a.out), Path(a.hist), a.season)
    d = Path(a.report_dir)
    d.mkdir(parents=True, exist_ok=True)
    (d / f"coverage_{a.season}.json").write_text(json.dumps(cov, indent=1, default=str))
    print(json.dumps(cov, indent=1, default=str)[:6000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
