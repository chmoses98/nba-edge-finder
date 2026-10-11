"""W1-C runner: collect matched player-game forecasts for a window, then build the scorecard.

    python scripts/nba_matched_decomposition.py collect --window dev     --out $SCRATCH/nba
    python scripts/nba_matched_decomposition.py collect --window holdout --out $SCRATCH/nba
    python scripts/nba_matched_decomposition.py report  --window holdout --out $SCRATCH/nba \
        --json docs/research/matched_decomposition_holdout.json
    python scripts/nba_matched_decomposition.py sidecars --window holdout --out $SCRATCH/nba

Windows are frozen in docs/research/PREREG_W1_NBA_DECOMPOSITION.md. Inputs are the committed ESPN
history only (data/history/espn); nothing under data/history/kalshi is opened by this script.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nba_edge.data.history import load_player_games, load_team_games  # noqa: E402
from nba_edge.research import matched_decomposition as md  # noqa: E402

SEASONS = ["2023-24", "2024-25", "2025-26"]
# Frozen in the preregistration. DEV is used for diagnosis / fitting; HOLDOUT is scored once.
WINDOWS = {
    "dev": [("2024-11-15", "2025-04-13"), ("2025-11-15", "2026-01-31")],
    "holdout": [("2026-02-01", "2026-04-12")],
}
DISPERSION_FIT_BEFORE = "2024-11-15"  # baseline NB dispersion uses only rows before the first DEV game
N_SIMS = 2000
FREEZE_DIGEST = "sha256:5a4cbda0b973d1e4d6289557b99372e4735ebe3146fa76e8f0b6ca833193be78"  # NBA_BASELINE_2026_PRESEASON_V1


def load(data_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    hist = data_root / "history"
    tg = load_team_games(hist, SEASONS)
    pg = load_player_games(hist, SEASONS)
    tg = tg[tg["season_type"] == "regular"].copy()
    pg = pg[pg["season_type"] == "regular"].copy()
    pg["minutes"] = pd.to_numeric(pg["minutes"], errors="coerce").fillna(0.0)
    return tg, pg


def window_games(tg: pd.DataFrame, window: str) -> pd.DataFrame:
    home = tg[tg["home"] == True].sort_values(["game_date_et", "start_time_utc", "game_id"])  # noqa: E712
    mask = np.zeros(len(home), dtype=bool)
    for lo, hi in WINDOWS[window]:
        mask |= (home["game_date_et"] >= lo).to_numpy() & (home["game_date_et"] <= hi).to_numpy()
    return home[mask]


def collect(data_root: Path, window: str, out: Path, n_sims: int, limit: int | None, arms: tuple[str, ...] = md.ARMS,
            extra_arms=None, tag: str = "", challenger_cfg=None, every: int = 1, champion_cfg=None) -> dict:
    tg, pg = load(data_root)
    alpha = md.fit_baseline_dispersion(pg, DISPERSION_FIT_BEFORE)
    games = window_games(tg, window)
    if every > 1:
        games = games.iloc[::every]
    if limit:
        games = games.iloc[:limit]
    wide, long, gmeta = [], [], []
    t0 = time.time()
    for i, (_, r) in enumerate(games.iterrows()):
        meta, fc, gp = md.forecast_game(r, tg, pg, alpha, n_sims, arms, extra_arms, challenger_cfg, champion_cfg)
        box = pg[pg["game_id"] == r["game_id"]]
        w, lg = md.score_game(meta, fc, box)
        wide.extend(w)
        long.extend(lg)
        prior = tg[tg["game_date_et"] < str(r["game_date_et"])]
        gmeta.append({
            "game_id": str(r["game_id"]), "date": str(r["game_date_et"]), "kickoff": str(r["start_time_utc"]),
            "as_of": md.as_of_for(str(r["game_date_et"])), "source_max_observed_at": str(prior["start_time_utc"].max()),
            "home_team_id": int(r["team_id"]), "away_team_id": int(r["opp_team_id"]),
            "n_eligible": len(meta), "n_ambiguous_team_excluded": 2 * len(md.ambiguous_players(meta)), **{f"non_eligible_{k}": v for k, v in md.non_eligible_participants(box, {m["player_id"] for m in meta}).items()},
            "box_minutes_total": float(box["minutes"].sum()),
        })
        if (i + 1) % 50 == 0:
            print(f"{window}: {i + 1}/{len(games)} games, {len(wide)} player-games, {time.time() - t0:.0f}s", file=sys.stderr)
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(wide).to_parquet(out / f"wide_{window}{tag}.parquet", index=False)
    pd.DataFrame(long).to_parquet(out / f"long_{window}{tag}.parquet", index=False)
    pd.DataFrame(gmeta).to_parquet(out / f"games_{window}{tag}.parquet", index=False)
    info = {"challenger_cfg": repr(challenger_cfg) if challenger_cfg else None, "champion_cfg": repr(champion_cfg) if champion_cfg else None, "every": every, "window": window, "date_ranges": WINDOWS[window], "n_games": len(gmeta), "n_player_games": len(wide), "n_sims": n_sims,
            "baseline_nb_alpha": alpha, "dispersion_fit_before": DISPERSION_FIT_BEFORE, "seconds": round(time.time() - t0, 1)}
    (out / f"collect_{window}{tag}.json").write_text(json.dumps(info, indent=1))
    return info


def strata_masks(wide: pd.DataFrame, usage_cuts: tuple[float, float]) -> dict[str, pd.Series]:
    u = wide["ewm5_cm_fga"] / wide["ewm5_min_mean"].replace(0, np.nan)
    return {
        "pred_starter (p_start>=0.5)": wide["p_start"] >= 0.5,
        "pred_bench (p_start<0.5)": wide["p_start"] < 0.5,
        f"usage_low (ewm5 FGA/min<{usage_cuts[0]:.3f})": u < usage_cuts[0],
        "usage_mid": (u >= usage_cuts[0]) & (u < usage_cuts[1]),
        f"usage_high (ewm5 FGA/min>={usage_cuts[1]:.3f})": u >= usage_cuts[1],
    }


def report(out: Path, window: str, n_boot: int, usage_cuts: tuple[float, float] | None, listed_path: Path | None,
           arms: tuple[str, ...] | None = None, tag: str = "", pairs: list[tuple[str, str]] | None = None) -> dict:
    wide = pd.read_parquet(out / f"wide_{window}{tag}.parquet")
    if arms is None:
        arms = tuple(a for a in (*md.ARMS, "sim_challenger") if f"{a}_p_play" in wide.columns)
    long = pd.read_parquet(out / f"long_{window}{tag}.parquet")
    games = pd.read_parquet(out / f"games_{window}{tag}.parquet")
    # players eligible for both teams (see md.ambiguous_players); already dropped at collect time in
    # current code, dropped here too so older frames are scored identically
    dup = wide.duplicated(["game_id", "player_id"], keep=False)
    n_dup = int(dup.sum())
    wide = wide[~dup].reset_index(drop=True)
    long = long[~long.duplicated(["game_id", "player_id", "arm", "cond", "stat"], keep=False)].reset_index(drop=True)
    pairs = pairs or [p for p in (("ewm5", "sim_rotation"), ("sim_rotation", "sim_waterfill"), ("sim_rotation", "sim_challenger"))
                      if p[0] in arms and p[1] in arms]
    if usage_cuts is None:
        u = (wide["ewm5_cm_fga"] / wide["ewm5_min_mean"])[wide["ewm5_n_played"] >= 5]
        usage_cuts = (float(u.quantile(1 / 3)), float(u.quantile(2 / 3)))
    strata = strata_masks(wide, usage_cuts)
    rep: dict = {
        "window": window, "date_ranges": WINDOWS.get(window), "arms": list(arms),
        "population": {
            "n_games": int(len(games)), "n_eligible_player_games": int(len(wide)),
            "n_actually_played": int(wide["act_played"].sum()), "n_dnp_in_box": int((wide["act_in_box"] & ~wide["act_played"]).sum()),
            "n_not_in_box": int((~wide["act_in_box"]).sum()),
            "n_excluded_ambiguous_team_rows": n_dup + (int(games["n_ambiguous_team_excluded"].sum()) if "n_ambiguous_team_excluded" in games else 0),
            "non_eligible_participants": int(games["non_eligible_n"].sum()),
            "non_eligible_minutes_share": md._rnd(games["non_eligible_minutes"].sum() / games["box_minutes_total"].sum()),
            "non_eligible_points_share": md._rnd(games["non_eligible_pts"].sum() / max(wide["act_pts"].sum() + games["non_eligible_pts"].sum(), 1)),
            "eligibility_rule": "players of either team who appeared in >=1 of the team's last 10 regular-season games before the cutoff, top 15 by min_mean*p_play (features/build.py roster rule); fixed pre-tip",
            "by_season": wide.assign(season=np.where(wide["date"] < "2025-07-01", "2024-25", "2025-26")).groupby("season").size().to_dict(),
        },
        "usage_tercile_cuts_ewm5_fga_per_min": [round(c, 4) for c in usage_cuts],
        "participation": md.participation_scorecard(wide, arms, pairs, n_boot),
        "minutes": {c: md.stat_scorecard(long, "minutes", c, arms, pairs, n_boot) for c in ("unc", "cond")},
        "per_minute_conditional_on_playing": md.per_minute_scorecard(wide, arms, n_boot, strata),
        "final_stats": {s: {c: md.stat_scorecard(long, s, c, arms, pairs, n_boot) for c in ("unc", "cond")} for s in md.COUNT_STATS},
        "decomposition_full_eligible_population": {a: {s: md.decomposition(wide, a, md.STATS[s], n_boot) for s in md.COUNT_STATS} for a in arms},
        "decomposition_by_stratum": {name: {a: {s: md.decomposition(wide[msk], a, md.STATS[s], n_boot) for s in ("points", "rebounds", "assists")} for a in arms if a != "sim_waterfill"} for name, msk in strata.items()},
        "per_minute_by_own_usage_tercile": {a: md.own_usage_tercile_rates(wide, a, n_boot) for a in arms},
    }
    frames = {
        "A full eligible population (pre-tip)": pd.Series(True, index=wide.index),
        "B predicted starters (pre-tip)": wide["p_start"] >= 0.5,
        "C sim predicts >=28 min | play (pre-tip)": wide["sim_rotation_cond_min"] >= 28,
        "D actually played (outcome-selected)": wide["act_played"],
        "E actually >=28 min (outcome-selected)": wide["act_min"] >= 28,
    }
    if listed_path and listed_path.exists():
        listed = pd.read_parquet(listed_path)
        key = set(zip(listed["game_id"].astype(str), listed["player_id"].astype(int)))
        lm = pd.Series([(g, p) in key for g, p in zip(wide["game_id"].astype(str), wide["player_id"].astype(int))], index=wide.index)
        frames["F has a listed player-prop contract (selection by listing; diagnostic only)"] = lm
        frames["G listed AND actually played (selection by listing + outcome)"] = lm & wide["act_played"]
        rep["population"]["n_listed_player_games"] = int(lm.sum())
    rep["observation_choice"] = md.observation_choice_table(wide, arms, frames, n_boot)
    rep["by_month_points_ratio"] = {
        m: {a: md._rnd(g[f"{a}_unc_pts"].sum() / g["act_pts"].sum()) for a in arms}
        for m, g in wide.groupby(wide["date"].str[:7])
    }
    return rep


class _gz:
    """Deterministic gzip writer (mtime 0, no filename) so identical content gives identical bytes."""

    def __init__(self, path: Path):
        self.path, self.buf = path, io.StringIO()

    def __enter__(self):
        return self.buf

    def __exit__(self, *exc):
        if exc[0] is None:
            self.path.write_bytes(gzip.compress(self.buf.getvalue().encode("utf-8"), mtime=0))
        return False


def _module_hash() -> str:
    return "sha256:" + hashlib.sha256((ROOT / "src/nba_edge/research/matched_decomposition.py").read_bytes()).hexdigest()


def _v1(row: dict, arm: str, p_play: float) -> dict:
    """Upgrade a kit-format row to pure_forecast.v1 (sources + per-feature lineage + frozen hash)."""
    mf = row.pop("model_features")
    t = row["source_max_observed_at"]
    row["schema_version"] = "pure_forecast.v1"
    row["model_frozen_hash"] = FREEZE_DIGEST if arm.startswith("sim_") else _module_hash()
    row["participation_probability"] = round(float(p_play), 4)
    row["sources"] = [
        {"source_id": "espn_player_games", "class": "sports_only", "max_observed_at": t, "uri": "data/history/espn/player_games_*.parquet",
         "description": "regular-season player box rows dated strictly before the game date (retrospective backfill 2026-09-19)"},
        {"source_id": "espn_team_games", "class": "sports_only", "max_observed_at": t, "uri": "data/history/espn/team_games_*.parquet",
         "description": "regular-season team box rows dated strictly before the game date"},
    ]
    row["feature_lineage"] = [
        {"name": k, "value": mf[k], "source": "espn_player_games", "observed_at": t, "class": "sports_only"}
        for k in ("p_start", "p_play_feature", "n_prior_played_team", "ewm5_min_mean")
    ]
    row["x_draws"] = mf["draws"]
    row["x_feature_version"] = mf["feature_version"]
    row["x_sim_version"] = mf["sim_version"]
    return row


def write_sidecars(out: Path, window: str, dest: Path, arms: tuple[str, ...] = md.ARMS, tag: str = "", sample_games: int | None = None,
                   schema: str = "v0") -> dict:
    """PURE sidecars (one file per arm and conditionality) + outcomes. ``schema`` v0 = kit interim
    format; v1 = the shared pure_forecast.v1 contract."""
    long = pd.read_parquet(out / f"long_{window}{tag}.parquet")
    wide = pd.read_parquet(out / f"wide_{window}{tag}.parquet")
    games = pd.read_parquet(out / f"games_{window}{tag}.parquet").set_index("game_id")
    if sample_games:
        keep = sorted(games.index)[:sample_games]
        long = long[long["game_id"].isin(keep)]
        wide = wide[wide["game_id"].isin(keep)]
    feats = wide.set_index(["game_id", "player_id"])
    dest.mkdir(parents=True, exist_ok=True)
    paths = {}
    for cond in ("unc", "cond"):
        for arm in arms:
            sub = long[(long["arm"] == arm) & (long["cond"] == cond)]
            p = dest / f"pure_{arm}_{cond}{tag}{'' if schema == 'v0' else '.v1'}.jsonl.gz"
            n = 0
            with _gz(p) as fh:
                for r in sub.itertuples(index=False):
                    if not np.isfinite(r.mean):
                        continue  # conditional forecast undefined (no simulated participation); counted in report
                    g = games.loc[r.game_id]
                    f = feats.loc[(r.game_id, r.player_id)]
                    lad = md.LADDERS[r.stat]
                    probs = list(r.probs)
                    # enforce monotone non-increasing ladder (sample estimates already are; guard float noise)
                    for j in range(1, len(probs)):
                        probs[j] = min(probs[j], probs[j - 1])
                    row = {
                        "sport": "NBA", "game_id": r.game_id, "player_id": str(r.player_id), "statistic": r.stat,
                        "as_of": g["as_of"], "kickoff": g["kickoff"], "source_max_observed_at": g["source_max_observed_at"],
                        "model_version": md.MODEL_VERSIONS.get(arm, arm), "projection_mode": "PURE_INDEPENDENT",
                        "conditional_on_playing": cond == "cond",
                        "projection": {"mean": round(float(r.mean), 4), "median": round(float(r.median), 4), "p10": round(float(r.p10), 4),
                                       "p90": round(float(r.p90), 4),
                                       "thresholds": [{"at_least": t, "probability": round(float(q), 4)} for t, q in zip(lad, probs)]},
                        "model_features": {
                            "sources": ["data/history/espn player_games (regular season, game_date_et < cutoff)",
                                        "data/history/espn team_games (regular season, game_date_et < cutoff)"],
                            "history_snapshot_pulled_at": "2026-09-19T00:37:29Z (retrospective backfill; rows filtered by date)",
                            "injury_report": "none (participation proxy from prior team games)",
                            "feature_version": md.FEATURE_VERSION, "sim_version": md.SIM_VERSION,
                            "p_start": round(float(f["p_start"]), 4), "p_play_feature": round(float(f["p_play_feature"]), 4),
                            "n_prior_played_team": int(f["n_prior_played"]),
                            "ewm5_min_mean": round(float(f["ewm5_min_mean"]), 4),
                            "draws": int(r.n_draws),
                        },
                    }
                    if schema == "v1":
                        row = _v1(row, arm, f[f"{arm}_p_play"])
                    fh.write(json.dumps(row, sort_keys=True) + "\n")
                    n += 1
            paths[f"{arm}_{cond}"] = {"path": str(p), "rows": n}
    po = dest / f"outcomes{tag}.jsonl.gz"
    n = 0
    with _gz(po) as fh:
        for r in wide.itertuples(index=False):
            for stat, key in md.STATS.items():
                fh.write(json.dumps({"sport": "NBA", "game_id": r.game_id, "player_id": str(r.player_id), "statistic": stat,
                                     "actual": float(getattr(r, f"act_{key}")), "played": bool(r.act_played)}, sort_keys=True) + "\n")
                n += 1
    paths["outcomes"] = {"path": str(po), "rows": n}
    return paths


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["collect", "report", "sidecars"])
    ap.add_argument("--player-prior-minutes", type=float, help="challenger arm: BuildConfig.player_prior_minutes (preregistered)")
    ap.add_argument("--resolve-cross-team-players", action="store_true",
                    help="opt-in traded-player identity fix for the simulator arms (NOT the frozen V1 default)")
    ap.add_argument("--every", type=int, default=1, help="collect every k-th game (DEV-only sweeps)")
    ap.add_argument("--arms", default=",".join(md.ARMS))
    ap.add_argument("--tag", default="")
    ap.add_argument("--window", choices=list(WINDOWS), required=True)
    ap.add_argument("--out", type=Path, default=Path(os.environ.get("NBA_W1_OUT", "/tmp/nba_w1")))
    ap.add_argument("--data", type=Path, default=ROOT / "data")
    ap.add_argument("--sims", type=int, default=N_SIMS)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--json", type=Path)
    ap.add_argument("--usage-cuts", type=str, help="frozen 'lo,hi' EWM-5 FGA/min tercile cuts (from DEV)")
    ap.add_argument("--listed", type=Path, help="optional parquet of (game_id, player_id) with a listed prop contract (diagnostic)")
    ap.add_argument("--dest", type=Path)
    ap.add_argument("--sample-games", type=int)
    ap.add_argument("--schema", choices=["v0", "v1"], default="v0")
    a = ap.parse_args(argv)
    if a.cmd == "collect":
        from nba_edge.features.build import BuildConfig

        cfg = BuildConfig(player_prior_minutes=a.player_prior_minutes) if a.player_prior_minutes is not None else None
        print(json.dumps(collect(a.data, a.window, a.out, a.sims, a.limit, tuple(a.arms.split(",")), tag=a.tag,
                                 challenger_cfg=cfg, every=a.every,
                                 champion_cfg=BuildConfig(resolve_cross_team_players=True) if a.resolve_cross_team_players else None), indent=1))
    elif a.cmd == "report":
        cuts = tuple(float(x) for x in a.usage_cuts.split(",")) if a.usage_cuts else None
        rep = report(a.out, a.window, a.boot, cuts, a.listed, tag=a.tag)
        txt = json.dumps(rep, indent=1, default=str)
        if a.json:
            a.json.parent.mkdir(parents=True, exist_ok=True)
            a.json.write_text(txt + "\n")
        print(txt[:4000])
    else:
        print(json.dumps(write_sidecars(a.out, a.window, a.dest or a.out / "sidecars", arms=tuple(a.arms.split(",")), tag=a.tag,
                                        sample_games=a.sample_games, schema=a.schema), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
