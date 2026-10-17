"""Archive the incumbent's own pregame forecasts, unchanged (model_role "incumbent").

The incumbent is the production simulator frozen as NBA_BASELINE_2026_PRESEASON_V1 with rotation-mixture minutes
("sim_rotation" arm of the PURE shadow collection, `.github/workflows/nba_shadow_pure.yml`, branch `nba-shadow-pure`). It is
the same model the study reproduced walk-forward as `incumbent_sim_rotation`. This module only READS that store (a checkout
of the branch) and re-keys its rows to the archive's forecast record:

  * conditional-on-playing rows (the frame the challenger forecasts in and Kalshi props settle in) for minutes, points,
    rebounds, assists, threes; plus `participation` = its P(appear) as a two-point pmf;
  * what it publishes is a mean, 7 quantiles and a threshold ladder, not a pmf, so `probs` is empty and scoring uses MAE
    (the pf_core.scorecard falls back to MAE when probabilities are missing);
  * its own `as_of` is the forecast's `generated_utc`, so re-reading the store is idempotent (same forecast_id) and a
    later capture of the same game is a new forecast version; nothing for a game that has started is archived
    (pf_core.prospective.archive_forecasts rejects it).
The shadow store is never written, and the incumbent code is not imported.
"""
from __future__ import annotations

import glob
import gzip
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from pf_core import prospective as pr

from .. import data
from .sources import iso, parse_ts

INC_ID = "nba_sim_rotation_v1"
STAT_FAMILY = {"minutes": "minutes", "points": "points", "rebounds": "rebounds", "assists": "assists", "threes": "threes"}


def _read(path: str) -> list[dict]:
    with gzip.open(path, "rt") as f:
        return [json.loads(x) for x in f if x.strip()]


def load_shadow_rows(shadow_dir: str, now: datetime, lookahead_hours: float = 48.0, lookback_hours: float = 6.0,
                     arm: str = "sim_rotation", season_types=("regular",)) -> list[dict]:
    """Conditional rows of games kicking off in (now - lookback, now + lookahead] from the newest capture files."""
    base = os.path.join(shadow_dir, "projections", arm, "conditional")
    days = {(now + timedelta(days=k)).strftime("%Y-%m-%d") for k in range(-2, 3)}
    out = []
    for p in sorted(glob.glob(os.path.join(base, "dt=*", "*.jsonl.gz"))):
        if os.path.basename(os.path.dirname(p))[3:] not in days:
            continue
        for r in _read(p):
            ko = parse_ts(r["kickoff"])
            if r.get("x_season_type") not in season_types or not r.get("conditional_on_playing", True):
                continue
            if r.get("x_capture_mode") != "LIVE":
                continue
            if ko <= now or ko > now + timedelta(hours=lookahead_hours):
                continue
            out.append(r)
    return out


def to_forecast_records(rows: list[dict], team_tri: dict[int, str]) -> list[dict[str, Any]]:
    """pure_forecast.v1 rows -> sift.forecast_archive.v1 records (role incumbent)."""
    recs = []
    for r in rows:
        stat = r["statistic"]
        fam = STAT_FAMILY.get(stat)
        if fam is None:
            continue
        pid = str(r["player_id"]).lstrip("-")
        base = {"sport": "NBA", "model_id": INC_ID, "model_role": "incumbent", "model_version": r.get("model_version"),
                "game_id": r["game_id"], "game_start_utc": r["kickoff"], "entity_id": f"espn:{pid}", "entity_name": None,
                "team": team_tri.get(int(r.get("x_team_id") or 0)), "generated_utc": r["as_of"],
                "data_asof_utc": r.get("source_max_observed_at"), "gate_status": None, "readiness": None,
                "source": {"store": "nba-shadow-pure", "slot": r.get("x_slot"), "capture_mode": r.get("x_capture_mode"),
                           "model_frozen_hash": r.get("model_frozen_hash")}}
        pj = r["projection"]
        recs.append({**base, "family": fam, "mean": float(pj["mean"]), "lo": 0, "probs": [],
                     "participation": None,
                     "quantiles": pj.get("quantiles"), "ladder": pj.get("thresholds"),
                     "p_appear": r.get("participation_probability")})
        if stat == "minutes" and r.get("participation_probability") is not None:      # one participation record per player-game
            p = float(min(max(r["participation_probability"], 0.0), 1.0))
            recs.append({**base, "family": "participation", "mean": p, "lo": 0, "probs": [1 - p, p], "participation": None,
                         "p_appear": p})
    return recs


def archive(shadow_dir: str | None, archive_root: str, now: datetime, *, lookahead_hours: float = 48.0,
            season_types=("regular",)) -> dict[str, Any]:
    if not shadow_dir or not os.path.isdir(shadow_dir):
        return {"status": "unavailable", "reason": "no nba-shadow-pure checkout", "written": 0}
    ab2id, ab2tri = data.team_maps()
    tri = {v: k for k, v in {a: ab2id[a] for a in ab2tri}.items()}
    team_tri = {}
    for a, i in ab2id.items():
        team_tri.setdefault(i, ab2tri[a])
    rows = load_shadow_rows(shadow_dir, now, lookahead_hours, season_types=season_types)
    recs = to_forecast_records(rows, team_tri)
    st = pr.archive_forecasts(recs, archive_root, iso(now))
    st.update({"status": "ok", "shadow_rows_read": len(rows), "records_built": len(recs),
               "games": len({r["game_id"] for r in recs})})
    return st
