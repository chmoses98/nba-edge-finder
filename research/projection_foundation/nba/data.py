"""Data loading and normalisation.

Source of truth for history: ESPN box scores. The repo holds ESPN history for 2023-24..2025-26
(`data/history/espn`); the sportsdataverse mirror of the same ESPN feed (hoopR) extends it back to 2014-15
with identical ESPN game / athlete ids, so the two agree row-for-row where they overlap (checked in tests and
in the inventory). Raw files live in the gitignored cache `research/projection_foundation/.cache/hoopr`.

Two player tables are produced:

* ``box``  -- one row per player listed in an ESPN box score (active roster, incl. DNP-coach's-decision).
* ``cand`` -- the *pregame candidate pool*: box rows plus synthetic "absent" rows for players who played for
  the team in any of its previous ``CAND_WINDOW`` games, are not in this game's box and did not appear for
  another team that day. Absent players are injured/inactive/G-League/waived; without a roster or injury
  snapshot a pregame model cannot tell them apart, which is exactly the uncertainty the hurdle models.
"""
from __future__ import annotations

import os
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]          # repo root
PF_DIR = ROOT / "research" / "projection_foundation"
CACHE = PF_DIR / ".cache" / "hoopr"
RELEASE = "https://github.com/sportsdataverse/sportsdataverse-data/releases/download"
FIRST_SEASON, LAST_SEASON = 2015, 2026               # hoopR season = year the season ends
CAND_WINDOW = 10

STATS = ["minutes", "pts", "reb", "ast", "fg3m", "fga", "fta", "fgm", "fg3a", "ftm", "oreb", "dreb", "tov",
         "stl", "blk", "pf"]
_HOOPR_COLS = {"field_goals_made": "fgm", "field_goals_attempted": "fga", "three_point_field_goals_made": "fg3m",
               "three_point_field_goals_attempted": "fg3a", "free_throws_made": "ftm",
               "free_throws_attempted": "fta", "offensive_rebounds": "oreb", "defensive_rebounds": "dreb",
               "rebounds": "reb", "assists": "ast", "steals": "stl", "blocks": "blk", "turnovers": "tov",
               "points": "pts", "fouls": "pf"}


def season_label(y: int) -> str:
    return f"{y - 1}-{str(y)[2:]}"


def _download(url: str, dest: Path, tries: int = 4) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    for i in range(tries):
        try:
            tmp = dest.with_suffix(".part")
            with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
                f.write(r.read())
            os.replace(tmp, dest)
            return True
        except Exception as e:  # noqa: BLE001 - network: retry then report
            if "404" in str(e):
                return False
            time.sleep(2 ** (i + 1))
    return False


def ensure_hoopr(seasons=None, kinds=("player_box", "team_box"), refresh_current: bool = False) -> dict:
    """Download missing season files (idempotent). Returns {file: present?}."""
    seasons = seasons or range(FIRST_SEASON, LAST_SEASON + 1)
    repo = {"player_box": "espn_nba_player_boxscores", "team_box": "espn_nba_team_boxscores",
            "nba_schedule": "espn_nba_schedules"}
    out = {}
    for y in seasons:
        for k in kinds:
            f = CACHE / f"{k}_{y}.parquet"
            if not f.exists() or (refresh_current and y == max(seasons)):
                _download(f"{RELEASE}/{repo[k]}/{k}_{y}.parquet", f)
            out[f.name] = f.exists()
    return out


def team_maps() -> tuple[dict, dict]:
    """ESPN abbreviation -> (NBA team id, canonical tricode)."""
    t = pd.read_csv(ROOT / "data" / "identity" / "teams.csv")
    ab2id, ab2tri = {}, {}
    for _, r in t.iterrows():
        for a in [r["tricode"]] + (str(r["alt_tricodes"]).split("|") if isinstance(r["alt_tricodes"], str) else []):
            ab2id[a] = int(r["team_id"])
            ab2tri[a] = r["tricode"]
    for a, c in {"UTAH": "UTA", "WSH": "WAS", "NO": "NOP", "NY": "NYK", "SA": "SAS", "GS": "GSW", "PHX": "PHX"}.items():
        if c in ab2id:
            ab2id[a], ab2tri[a] = ab2id[c], c
    return ab2id, ab2tri


def pos_group(abbr) -> str:
    a = str(abbr or "").upper()
    if "C" in a:
        return "C"
    if a.startswith("G") or a in ("PG", "SG"):
        return "G"
    return "F"


def load_box(seasons=None, regular_only: bool = True) -> pd.DataFrame:
    """Normalised player box rows (ESPN, regular season)."""
    seasons = list(seasons or range(FIRST_SEASON, LAST_SEASON + 1))
    ab2id, ab2tri = team_maps()
    frames = []
    for y in seasons:
        f = CACHE / f"player_box_{y}.parquet"
        if not f.exists():
            continue
        d = pd.read_parquet(f)
        if regular_only:
            d = d[d["season_type"] == 2]
        d = d[~d["team_abbreviation"].isin(["EAST", "WEST"]) & d["athlete_id"].notna()]
        d = d.rename(columns=_HOOPR_COLS)
        out = pd.DataFrame({
            "game_id": d["game_id"].astype(np.int64),
            "season": d["season"].astype(int),
            "date": pd.to_datetime(d["game_date"]).dt.normalize(),
            "tip_utc": pd.to_datetime(d["game_date_time"]).dt.tz_convert("UTC"),
            "team": d["team_abbreviation"].map(ab2tri),
            "team_id": d["team_abbreviation"].map(ab2id),
            "opp": d["opponent_team_abbreviation"].map(ab2tri),
            "home": (d["home_away"] == "home"),
            "pid": d["athlete_id"].astype(np.int64),
            "name": d["athlete_display_name"],
            "pos": d["athlete_position_abbreviation"].map(pos_group),
            "started": d["starter"].fillna(False).astype(bool),
            "dnp": d["did_not_play"].fillna(False).astype(bool),
            "dnp_reason": d["reason"],
            "team_score": d["team_score"].astype(float),
            "opp_score": d["opponent_team_score"].astype(float),
        })
        for c in STATS:
            src = c if c in d.columns else None
            out[c] = d[src].astype(float) if src else np.nan
        frames.append(out)
    box = pd.concat(frames, ignore_index=True)
    box = box.dropna(subset=["team", "opp"])
    box["minutes"] = box["minutes"].where(~box["dnp"], 0.0).fillna(0.0)
    for c in STATS[1:]:
        box[c] = box[c].where(box["minutes"] > 0, 0.0).fillna(0.0)
    box["pra"] = box["pts"] + box["reb"] + box["ast"]
    box["played"] = box["minutes"] > 0
    box["in_box"] = True
    box = box.drop_duplicates(["game_id", "pid"]).sort_values(["date", "game_id", "team", "pid"]).reset_index(drop=True)
    return box


def team_games_from_box(box: pd.DataFrame) -> pd.DataFrame:
    """One row per team-game: points, possessions (0.96*(FGA+0.44FTA-OREB+TOV)), OT periods."""
    g = box.groupby(["game_id", "team"], sort=False)
    t = g.agg(season=("season", "first"), date=("date", "first"), tip_utc=("tip_utc", "first"),
              team_id=("team_id", "first"), opp=("opp", "first"), home=("home", "first"),
              pts=("team_score", "first"), opp_pts=("opp_score", "first"), fga=("fga", "sum"), fta=("fta", "sum"),
              oreb=("oreb", "sum"), tov=("tov", "sum"), fg3m=("fg3m", "sum"), reb=("reb", "sum"),
              ast=("ast", "sum"), team_min=("minutes", "sum"), box_pts=("pts", "sum")).reset_index()
    t["n_ot"] = np.clip(np.round((t["team_min"] / 5.0 - 48.0) / 5.0), 0, 6)
    t["poss_raw"] = 0.96 * (t["fga"] + 0.44 * t["fta"] - t["oreb"] + t["tov"])
    o = t[["game_id", "team", "poss_raw"]].rename(columns={"team": "opp", "poss_raw": "opp_poss_raw"})
    t = t.merge(o, on=["game_id", "opp"], how="left")
    t["poss"] = (t["poss_raw"] + t["opp_poss_raw"]) / 2.0          # game possessions (both teams' average)
    t["pace48"] = t["poss"] * 48.0 / (48.0 + 5.0 * t["n_ot"])
    t["ortg"] = 100.0 * t["pts"] / t["poss"]
    t["margin"] = t["pts"] - t["opp_pts"]
    return t.sort_values(["date", "game_id", "team"]).reset_index(drop=True)


def build_candidates(box: pd.DataFrame, window: int = CAND_WINDOW) -> pd.DataFrame:
    """Box rows + synthetic absent rows (see module docstring). Pregame-knowable definition: membership uses
    only the team's previous `window` games; the same-day other-team exclusion removes traded players whose
    new team already played (the only same-day information used, and it is roster information)."""
    tg = box[["game_id", "team", "date", "season"]].drop_duplicates(["game_id", "team"]).sort_values(["team", "date"])
    tg["tgi"] = tg.groupby("team").cumcount()
    b = box.merge(tg[["game_id", "team", "tgi"]], on=["game_id", "team"])
    played = b[b["played"]][["team", "tgi", "pid", "season"]]
    # for each team-game index t, players who played in [t-window, t-1] within the same season
    rows = []
    for k in range(1, window + 1):
        x = played.copy()
        x["tgi"] = x["tgi"] + k
        rows.append(x)
    c = pd.concat(rows).drop_duplicates(["team", "tgi", "pid"])
    c = c.merge(tg, on=["team", "tgi"], suffixes=("_prev", ""))
    c = c[c["season_prev"] == c["season"]].drop(columns=["season_prev"])
    present = b[["game_id", "pid"]].assign(_in=True)
    c = c.merge(present, on=["game_id", "pid"], how="left")
    c = c[c["_in"].isna()].drop(columns="_in")
    other = b[["date", "pid", "team"]].rename(columns={"team": "_t2"})
    c = c.merge(other, on=["date", "pid"], how="left")
    c = c[c["_t2"].isna()].drop(columns=["_t2", "tgi"])
    meta = box.drop_duplicates(["game_id", "team"])[["game_id", "team", "tip_utc", "team_id", "opp", "home",
                                                       "team_score", "opp_score"]]
    c = c.merge(meta, on=["game_id", "team"])
    last = box.sort_values("date").drop_duplicates("pid", keep="last")[["pid", "name", "pos"]]
    c = c.merge(last, on="pid", how="left")
    for col in STATS + ["pra"]:
        c[col] = 0.0
    c["started"] = False
    c["dnp"] = True
    c["dnp_reason"] = "ABSENT_FROM_BOX"
    c["played"] = False
    c["in_box"] = False
    out = pd.concat([box, c[box.columns]], ignore_index=True)
    return out.sort_values(["date", "game_id", "team", "pid"]).reset_index(drop=True)


# ---------------------------------------------------------------------------------------------------------
# production-schema conversion (to reproduce the incumbent on seasons the repo history does not hold)
# ---------------------------------------------------------------------------------------------------------
def to_repo_schema(box: pd.DataFrame, tg: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    ab_id = tg.drop_duplicates("team").set_index("team")["team_id"].to_dict()
    p = pd.DataFrame({
        "game_id": "espn:" + box["game_id"].astype(str), "game_date_et": box["date"].dt.strftime("%Y-%m-%d"),
        "season": box["season"].map(season_label), "season_type": "regular",
        "team_id": box["team_id"].astype(int), "opp_team_id": box["opp"].map(ab_id).astype(int),
        "home": box["home"].astype(bool), "nba_id": -box["pid"].astype(np.int64), "player_name": box["name"],
        "started": box["started"], "played": box["played"], "minutes": box["minutes"],
        "pts": box["pts"].astype(int), "reb": box["reb"].astype(int), "ast": box["ast"].astype(int),
        "fg3m": box["fg3m"].astype(int), "stl": box["stl"].astype(int), "blk": box["blk"].astype(int),
        "tov": box["tov"].astype(int), "fga": box["fga"].astype(int), "fta": box["fta"].astype(int),
        "fgm": box["fgm"].astype(int), "oreb": box["oreb"].astype(int), "dreb": box["dreb"].astype(int),
        "fg3a": box["fg3a"].astype(int), "ftm": box["ftm"].astype(int), "pf": 0, "plus_minus": 0.0,
        "dnp_reason": box["dnp_reason"].where(box["dnp"], None), "team_pts": box["team_score"].astype(int),
        "opp_pts": box["opp_score"].astype(int), "n_ot": 0,
        "start_time_utc": box["tip_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")})
    p = p[box["in_box"].to_numpy()]
    t = pd.DataFrame({
        "game_id": "espn:" + tg["game_id"].astype(str), "game_date_et": tg["date"].dt.strftime("%Y-%m-%d"),
        "start_time_utc": tg["tip_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "season": tg["season"].map(season_label),
        "season_type": "regular", "team_id": tg["team_id"].astype(int), "opp_team_id": tg["opp"].map(ab_id).astype(int),
        "home": tg["home"].astype(bool), "pts": tg["pts"].astype(int), "opp_pts": tg["opp_pts"].astype(int),
        "q1": np.nan, "q2": np.nan, "q3": np.nan, "q4": np.nan, "ot_pts": np.nan, "n_ot": tg["n_ot"].astype(int),
        "won": tg["margin"] > 0, "margin": tg["margin"].astype(int), "total": (tg["pts"] + tg["opp_pts"]).astype(int),
        "fga": tg["fga"].astype(int), "fta": tg["fta"].astype(int), "oreb": tg["oreb"].astype(int),
        "tov": tg["tov"].astype(int), "possessions": tg["poss_raw"].round(3), "totals_source": "hoopr_player_sum"})
    nmap = t.set_index(["game_id", "team_id"])["n_ot"]
    p["n_ot"] = pd.MultiIndex.from_arrays([p["game_id"], p["team_id"]]).map(nmap).fillna(0).astype(int)
    return p.reset_index(drop=True), t.reset_index(drop=True)
