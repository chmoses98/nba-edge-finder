"""Forward projections in `sift.projections.v1` (CONTRACT.md) for the next available NBA slate.

Inputs (all point-in-time; nothing after `data_asof_utc` is read):
  * history: ESPN box scores (sportsdataverse mirror, regular season) up to the newest available game;
  * slate: the newest `context/schedule` capture of the data-archive branch (ESPN scoreboard), first date
    >= --date with scheduled regular-season games;
  * rosters: newest `context/rosters` capture (ESPN team rosters, athlete ids);
  * availability: newest `context/injuries` capture (ESPN injuries; Out -> treated as absent, which drives the
    teammate-absence features; Questionable/Doubtful/Day-To-Day -> gate REVIEW).
Models: the frozen parameters chosen in the walk-forward backtest (results/frozen_params.json); the LightGBM
components are refit on the five seasons before the slate (same recipe as the backtest's final block).
If no future slate exists the projector falls back to the most recent historical date using only prior data and
labels the output `"mode": "historical_replay"`.

Usage (from research/projection_foundation):
  python -m nba.project --archive <dir with context/...> [--date YYYY-MM-DD] [--out results/projections_latest.json]
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import re
import subprocess
import time
import unicodedata
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from pf_core import VERSION as PF_VERSION, dists, gate, models
from . import MODEL_ID, data, distributions as D, features, minutes as M, pipeline, stats as S, team as T
from .common import FAMILIES, MINUTES_RUNGS, SUPPORT_K

FROZEN = data.PF_DIR / "results" / "frozen_params.json"
SLATE_SEASON = 2027


def _latest(archive: str, kind: str) -> str | None:
    fs = sorted(glob.glob(os.path.join(archive, "context", kind, "dt=*", f"context_{kind}_*.jsonl.gz")))
    return fs[-1] if fs else None


def _read_jsonl_gz(p: str) -> pd.DataFrame:
    with gzip.open(p, "rt") as f:
        return pd.DataFrame([json.loads(x) for x in f if x.strip()])


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", s).strip()


def load_slate(archive: str, date: str | None):
    sp, rp, ip = _latest(archive, "schedule"), _latest(archive, "rosters"), _latest(archive, "injuries")
    if not sp or not rp:
        return None
    sch = _read_jsonl_gz(sp)
    sch = sch[(sch["season_type"] == "regular") & (sch["status"] == "scheduled")]
    if date:
        sch = sch[sch["game_date_et"] >= date]
    if sch.empty:
        return None
    day = sch["game_date_et"].min()
    sch = sch[sch["game_date_et"] == day].drop_duplicates("game_id")
    ros = _read_jsonl_gz(rp)
    inj = _read_jsonl_gz(ip) if ip else pd.DataFrame(columns=["team_id", "player_name_raw", "status"])
    obs = [x for x in [sch.get("_observed_at_utc"), ros.get("_observed_at_utc"), inj.get("_observed_at_utc")] if x is not None]
    asof = max(str(x.max()) for x in obs)
    return {"day": day, "schedule": sch, "rosters": ros, "injuries": inj, "asof": asof,
            "files": {"schedule": sp, "rosters": rp, "injuries": ip}}


def slate_rows(sl: dict, box: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    ab2id, ab2tri = data.team_maps()
    tri2id = {v: ab2id[k] for k, v in ab2tri.items()}
    ros = sl["rosters"].copy()
    ros["tri"] = ros["team_abbreviation"].map(ab2tri)
    ros["pid"] = ros["espn_athlete_id"].astype(np.int64)
    inj = sl["injuries"].copy()
    inj["key"] = inj["team_id"].astype(str) + "|" + inj["player_name_raw"].map(_norm)
    st = dict(zip(inj["key"], inj["status"].str.upper()))
    rows, tgr = [], []
    for _, g in sl["schedule"].iterrows():
        gid = int(str(g["game_id"]).split(":")[-1])
        tip = pd.Timestamp(g["start_time_utc"])
        for side, team, opp in (("home", g["home_tricode"], g["away_tricode"]), ("away", g["away_tricode"], g["home_tricode"])):
            tgr.append({"game_id": gid, "team": team, "season": SLATE_SEASON, "date": pd.Timestamp(g["game_date_et"]),
                        "tip_utc": tip, "team_id": tri2id[team], "opp": opp, "home": side == "home"})
            for _, r in ros[ros["tri"] == team].iterrows():
                status = st.get(f"{tri2id[team]}|{_norm(r['full_name'])}", "ACTIVE")
                rows.append({"game_id": gid, "season": SLATE_SEASON, "date": pd.Timestamp(g["game_date_et"]),
                             "tip_utc": tip, "team": team, "team_id": tri2id[team], "opp": opp, "home": side == "home",
                             "pid": int(r["pid"]), "name": r["full_name"], "pos": data.pos_group(r.get("position")),
                             "started": False, "dnp": status == "OUT", "dnp_reason": "INJURY_REPORT_OUT" if status == "OUT" else None,
                             "team_score": np.nan, "opp_score": np.nan, "in_box": status != "OUT",
                             "played": False, "inj_status": status})
    c = pd.DataFrame(rows)
    for col in data.STATS + ["pra"]:
        c[col] = np.nan
    return c, pd.DataFrame(tgr)


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(data.ROOT), "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def project(archive: str | None, date: str | None, out: str, max_hist_seasons: int = 7) -> dict:
    t0 = time.time()
    frozen = json.loads(FROZEN.read_text())
    data.ensure_hoopr(range(data.FIRST_SEASON, SLATE_SEASON + 1), refresh_current=True)
    seasons = list(range(SLATE_SEASON - max_hist_seasons, SLATE_SEASON + 1))
    box = data.load_box(seasons)
    hist_last = box["date"].max()
    sl = load_slate(archive, date) if archive else None
    mode = "next_slate"
    if sl is None:
        # historical replay: newest date in history, using only earlier games
        mode = "historical_replay"
        day = box["date"].max()
        hist = box[box["date"] < day]
        cur = box[box["date"] == day].copy()
        cur["inj_status"] = None
        for col in data.STATS + ["pra"]:
            cur[col] = np.nan
        cur["played"] = False
        cur["started"] = False
        box = hist
        slate_c = cur
        tg_slate = cur.drop_duplicates(["game_id", "team"])[["game_id", "team", "season", "date", "tip_utc", "team_id", "opp", "home"]]
        asof = (pd.Timestamp(day) - pd.Timedelta(hours=1)).tz_localize("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")
        files = {}
    else:
        slate_c, tg_slate = slate_rows(sl, box)
        asof = sl["asof"].replace("+00:00", "Z")
        files = sl["files"]
    tg = data.team_games_from_box(box)
    cand = data.build_candidates(box)
    slate_c["is_slate"] = True
    cand["is_slate"] = False
    allc = pd.concat([cand, slate_c[cand.columns.drop("is_slate").tolist() + ["is_slate", "inj_status"]]], ignore_index=True)
    tg_all = pd.concat([tg, tg_slate], ignore_index=True)
    f, tctx = features.build(allc, tg_all)
    f["is_slate"] = f["is_slate"].fillna(False).astype(bool)
    f["played"] = f["played"].fillna(False).astype(bool) & ~f["is_slate"]
    f = pipeline.with_targets(f)
    mp, _ = M.fit_ladder(f, frozen=frozen["minutes_params"], final_only=True, with_oracle=False)
    best_min = frozen["best_minutes_model"]
    f["min_best"] = mp[best_min]
    f["p_play"] = M.fit_hurdle(f, final_only=True)
    sl_idx = f.index[f["is_slate"]]
    F = f.loc[sl_idx].copy()
    mres = frozen["minutes_dist"]
    mdist = models.make_dist(mres, F["min_best"].to_numpy())
    # team
    tt, _ = T.fit_team(tctx)
    tt = tt[tt["game_id"].isin(set(F["game_id"]))]
    tbest = frozen["team"]["best"]
    tdist = models.make_dist(frozen["team"]["dist"], tt[tbest].to_numpy())
    tt = tt.assign(mean=tdist.mean, p10=tdist.quantile(0.1), p90=tdist.quantile(0.9))
    fam_out = {}
    player_rows = []
    for fam, (col, gkey, rungs) in FAMILIES.items():
        fz = frozen["families"][fam]
        sp, _ = S.fit_family(f, col, "min_best", M.INJ, frozen=fz["params"], final_only=True)
        mu = sp.loc[sl_idx, fz["best"]].to_numpy()
        rate = sp.loc[sl_idx, "rate"].to_numpy()
        if fz["dist"] == "mixture":
            scen = D.minutes_scenarios(fz["min_res"], F["min_best"].to_numpy())
            scale = mu / np.maximum(rate * scen.mean(axis=1), 1e-6)
            d = D.mixture(rate, scen, fz["alpha_given_minutes"], SUPPORT_K[col], scale)
        elif fz["dist"] == "single_minutes_nb":
            d = dists.negbin(np.maximum(mu, 0.05), fz["alpha_given_minutes"], SUPPORT_K[col])
        else:
            d = models.make_dist(fz["dist_params"], np.maximum(mu, 0.05))
        F[f"{col}_mean"] = d.mean
        fam_out[fam] = {"readiness": fz["readiness"], "model": fz["model_name"], "reason": fz["readiness_reason"]}
        for i, ix in enumerate(sl_idx):
            r = F.loc[ix]
            hist_min = f[(f["pid"] == r["pid"]) & f["played"] & ~f["is_slate"]].tail(10)
            th = {str(k): round(float(d.prob_ge(k)[i]), 4) for k in rungs}
            ist = r.get("inj_status") or "UNKNOWN"
            gi = gate.GateInput(sport="NBA", family=gkey, entity_id=str(r["pid"]), entity_name=r["name"], team=r["team"],
                                game_id=f"espn:{r['game_id']}", game_start_utc=pd.Timestamp(r["tip_utc"]).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                mean=float(d.mean[i]), data_asof_utc=asof,
                                injury_status={"ACTIVE": "ACTIVE", "DAY-TO-DAY": "DAY-TO-DAY"}.get(ist, ist),
                                expected_opportunity=float(r["min_best"]),
                                opportunity_history=hist_min["minutes_act"].tolist(),
                                stat_history=hist_min[f"{col}_act"].tolist(),
                                opponent_factor=float(sp.loc[ix, "opp_factor"]), opponent_sample_games=int(sp.loc[ix, "opp_n"]),
                                support_lo=0, probs=d.P[i], thresholds={k: v for k, v in th.items()},
                                sd=float(np.sqrt(max(d.var[i], 0))), model_n_obs=int(np.nan_to_num(r["minutes_p_n"])))
            gres = gate.evaluate(gi, now_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
            adj = [f"Participation: P(play) {r['p_play']:.2f} (projections below are conditional on playing; "
                   f"availability status {ist})."]
            if abs(sp.loc[ix, "opp_factor"] - 1) >= 0.03:
                adj.append(f"Opponent {r['opp']} allows {('more' if sp.loc[ix, 'opp_factor'] > 1 else 'less')} {fam} to "
                           f"{r['pos']}s than expected: x{sp.loc[ix, 'opp_factor']:.3f} ({int(sp.loc[ix, 'opp_n'])} games).")
            if abs(sp.loc[ix, "pace_adj"] - 1) >= 0.01:
                adj.append(f"Expected pace adjustment x{sp.loc[ix, 'pace_adj']:.3f}.")
            if r.get("out_min", 0) and r["out_min"] >= 20:
                adj.append(f"Teammates listed out account for ~{r['out_min']:.0f} recent minutes (minutes/usage redistributed).")
            if r["team_changed"] == 1 or r["games_with_team"] < 5:
                adj.append("New team: role estimated from prior-team history and position priors.")
            if np.nan_to_num(r["minutes_p_n"]) < 3:
                adj.append("Fewer than 3 career games in the data: projection is prior-driven.")
            player_rows.append({
                "player_id": f"espn:{r['pid']}", "name": r["name"], "team": r["team"], "opponent": r["opp"],
                "game_id": f"espn:{r['game_id']}", "family": fam, "mean": round(float(d.mean[i]), 2),
                "median": int(d.median[i]), "p10": int(d.quantile(0.1)[i]), "p90": int(d.quantile(0.9)[i]),
                "thresholds": th,
                "opportunity": {"family": "minutes", "mean": round(float(mdist.mean[i]), 1),
                                "p10": int(mdist.quantile(0.1)[i]), "p90": int(mdist.quantile(0.9)[i])},
                "opponent_adjustment": {"factor": round(float(sp.loc[ix, "opp_factor"]), 4), "sample_games": int(sp.loc[ix, "opp_n"])},
                "adjustments": adj, "readiness": fz["readiness"],
                "gate": {"status": gres["status"], "findings": [{k: x[k] for k in ("check", "severity", "what", "category", "action")}
                                                                for x in gres["findings"]]},
                "data_asof_utc": asof})
    # team reconciliation per team-game (points)
    pts_rows = [p for p in player_rows if p["family"] == "points"]
    pp = pd.DataFrame(pts_rows)
    games = []
    for gid, g in tt.groupby("game_id"):
        gg = {"game_id": f"espn:{gid}", "start_utc": pd.Timestamp(g["tip_utc"].iloc[0]).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "home": g.loc[g["home"], "team"].iloc[0], "away": g.loc[~g["home"], "team"].iloc[0], "teams": []}
        for _, r in g.iterrows():
            sub = F[(F["game_id"] == gid) & (F["team"] == r["team"])]
            psum = float((sub["p_play"] * sub["pts_mean"]).sum())
            rec = gate.team_reconciliation(psum, float(r["mean"]), f"{r['team']} player points vs team points")
            gg["teams"].append({"team": r["team"], "family": "team_points", "mean": round(float(r["mean"]), 1),
                                "p10": int(r["p10"]), "p90": int(r["p90"]),
                                "player_points_sum": round(psum, 1), "reconciliation": rec["status"]})
        games.append(gg)
    fam_out["team_points"] = {"readiness": frozen["team"]["readiness"], "model": frozen["team"]["model_name"],
                              "reason": frozen["team"]["readiness_reason"]}
    fam_out["minutes"] = {"readiness": frozen["minutes_readiness"]["readiness"], "model": frozen["minutes_readiness"]["model_name"],
                          "reason": frozen["minutes_readiness"]["readiness_reason"]}
    res = {"schema": "sift.projections.v1", "sport": "NBA",
           "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "data_asof_utc": asof,
           "model": {"id": MODEL_ID, "version": f"pf-{PF_VERSION}+{_git_sha()}", "authority": "research_only"},
           "mode": mode, "slate_date": str(pd.Timestamp(F["date"].iloc[0]).date()),
           "history_through": str(pd.Timestamp(hist_last).date()),
           "inputs": files, "families": fam_out, "games": games, "players": player_rows,
           "runtime_s": round(time.time() - t0, 1)}
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default=None, help="directory containing context/{schedule,rosters,injuries}/dt=*/...")
    ap.add_argument("--date", default=None, help="first slate date to consider (YYYY-MM-DD, ET)")
    ap.add_argument("--out", default=str(data.PF_DIR / "results" / "projections_latest.json"))
    a = ap.parse_args(argv)
    r = project(a.archive, a.date, a.out)
    print(json.dumps({"mode": r["mode"], "slate_date": r["slate_date"], "n_players": len(r["players"]),
                      "n_games": len(r["games"]), "runtime_s": r["runtime_s"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
