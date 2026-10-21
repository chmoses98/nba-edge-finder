"""Forward projections in `sift.projections.v1` (CONTRACT.md) for the next available NBA slate.

Inputs (all point-in-time; nothing after `data_asof_utc` is read):
  * history: ESPN box scores (sportsdataverse mirror, regular season) up to the newest available game;
  * slate: the newest `context/schedule` capture of the data-archive branch (ESPN scoreboard), first date
    >= --date with scheduled regular-season games;
  * rosters: newest `context/rosters` capture (ESPN team rosters, athlete ids);
  * availability: LIVE operation passes the resolved participation of every roster player (official NBA injury report,
    ESPN injuries, starters; `nba.live.participation`): OUT / DOUBTFUL players are treated as absent (drives the
    teammate-absence features exactly like the study's point-in-time report), P(play) is the report-recalibrated
    hurdle, minutes use the report-aware E_inj model where the official report covers the game, and the player/team
    reconciliation gate normalises minutes / points to the team projection (`nba.live.reconcile`). Without it (legacy
    `--archive` runs) the newest `context/injuries` capture is used as before (ESPN Out -> absent; others -> REVIEW).
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


def slate_rows(sl: dict, box: pd.DataFrame, availability: dict | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Slate player rows + team rows.

    `availability` (live operation) maps (event id 'espn:<game>', entity id 'espn:<athlete>') to the resolved participation
    (nba.live.participation): CONFIRMED_OUT / LIKELY_OUT players are absent exactly like OUT / DOUBTFUL on the study's
    point-in-time report (`injury.pit_absence`), everyone else is present. Without it the newest ESPN `context/injuries`
    capture is used (Out -> absent), as in the original forward projector."""
    ab2id, ab2tri = data.team_maps()
    tri2id = {v: ab2id[k] for k, v in ab2tri.items()}
    ros = sl["rosters"].copy()
    ros["tri"] = ros["team_abbreviation"].map(ab2tri)
    ros["pid"] = ros["espn_athlete_id"].astype(np.int64)
    inj = sl["injuries"].copy()
    st = {}
    if availability is None and len(inj):
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
                if availability is not None:
                    a = availability.get((f"espn:{gid}", f"espn:{int(r['pid'])}")) or {}
                    absent = a.get("status") in ("CONFIRMED_OUT", "LIKELY_OUT")
                    status = a.get("designation") or ("OUT" if absent else "ACTIVE")
                else:
                    status = st.get(f"{tri2id[team]}|{_norm(r['full_name'])}", "ACTIVE")
                    absent = status == "OUT"
                rows.append({"game_id": gid, "season": SLATE_SEASON, "date": pd.Timestamp(g["game_date_et"]),
                             "tip_utc": tip, "team": team, "team_id": tri2id[team], "opp": opp, "home": side == "home",
                             "pid": int(r["pid"]), "name": r["full_name"], "pos": data.pos_group(r.get("position")),
                             "started": False, "dnp": absent, "dnp_reason": "INJURY_REPORT_OUT" if absent else None,
                             "team_score": np.nan, "opp_score": np.nan, "in_box": not absent,
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


def _iso(ts) -> str:
    return pd.Timestamp(ts).strftime("%Y-%m-%dT%H:%M:%SZ")


def _legacy_participation(status: str | None) -> dict:
    """Participation block for runs without a live availability feed (ESPN context statuses only)."""
    s = (status or "UNKNOWN").upper()
    m = {"OUT": ("CONFIRMED_OUT", "OUT"), "DOUBTFUL": ("LIKELY_OUT", "DOUBTFUL"), "QUESTIONABLE": ("UNCERTAIN", "QUESTIONABLE"),
         "DAY-TO-DAY": ("UNCERTAIN", "DAY-TO-DAY"), "ACTIVE": ("UNVERIFIED", "UNKNOWN")}.get(s, ("UNVERIFIED", "UNKNOWN"))
    return {"status": m[0], "certainty": "UNKNOWN", "source": "espn_context_injuries", "captured_utc": None, "age_minutes": None,
            "reasons": ["legacy run: ESPN context injury status only, no point-in-time observation"], "designation": s,
            "implicit": False, "_class": None, "gate_injury_status": m[1]}


def project(archive: str | None, date: str | None, out: str, max_hist_seasons: int = 7) -> dict:
    """Legacy entry point (context archive, next regular-season date >= --date, or historical replay)."""
    sl = load_slate(archive, date) if archive else None
    return project_slate(sl, out, max_hist_seasons=max_hist_seasons)


def _game_forecast(gg: dict, g: pd.DataFrame, tdist, now_utc: str, asof: str) -> dict:
    """Team-points pmfs of one game (the model's own `tdist`) + context columns the team model already has. Nothing invented: a context
    field the model does not have for the game is simply absent."""
    from .live.forecasts import trim_pmf
    from .paper import config as PCFG
    gm = PCFG.load()["game_model"]
    teams, ctx = [], {}
    for _, r in g.iterrows():
        lo, probs = trim_pmf(int(tdist.lo), tdist.P[int(r["_tpos"])])
        teams.append({"team": r["team"], "mean": round(float(r["mean"]), 2), "lo": lo, "probs": probs})
        side = "home" if bool(r["home"]) else "away"
        for col in ("rest_days", "b2b", "three_in_four", "exp_pace", "exp_ortg", "exp_margin", "pace_off", "pace_def", "ortg_off", "drtg_def"):
            if col in r.index and pd.notna(r[col]):
                ctx[f"{side}_{col}"] = round(float(r[col]), 3)
    return {"game_id": gg["game_id"], "game_start_utc": gg["start_utc"], "home": gg["home"], "away": gg["away"], "generated_utc": now_utc,
            "data_asof_utc": asof, "model_id": f"{MODEL_ID}-team_points", "model_version": f"pf-{PF_VERSION}+{_git_sha()}", "teams": teams,
            "rho": gm["rho"], "rho_source": gm["rho_source"], "context": ctx, "inputs_asof": asof}


def project_slate(sl: dict | None, out: str | None, *, availability: dict | None = None, calib: dict | None = None, minutes_engine: str = "frozen",
                  now_utc: str | None = None, reconcile_cfg=None, max_hist_seasons: int = 7) -> dict:
    """Frozen-model forward projections for the games in `sl` (see load_slate; `sl["asof"]` = newest input captured).

    Live arguments: `availability` (resolved participation per (event, entity), nba.live.participation), `calib` (frozen
    report-aware P(play) coefficients) and `reconcile_cfg` (team reconciliation gate). Every player row carries
    `participation{status,certainty,source,captured_utc,reasons,p_play,...}` and `role: "shadow"`; the authority is always
    research_only."""
    from .live import participation as PART, reconcile as REC
    t0 = time.time()
    now_utc = now_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    frozen = json.loads(FROZEN.read_text())
    data.ensure_hoopr(range(data.FIRST_SEASON, SLATE_SEASON + 1), refresh_current=True)
    seasons = list(range(SLATE_SEASON - max_hist_seasons, SLATE_SEASON + 1))
    box = data.load_box(seasons)
    hist_last = box["date"].max()
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
        slate_c, tg_slate = slate_rows(sl, box, availability)
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
    f["min_inj"] = mp["E_inj"]
    f["p_hurdle"] = M.fit_hurdle(f, final_only=True)
    sl_idx = f.index[f["is_slate"]]
    F = f.loc[sl_idx].copy()
    # ---- participation per slate row
    keys = [(f"espn:{g}", f"espn:{p}") for g, p in zip(F["game_id"], F["pid"])]
    if availability is None:
        part = [_legacy_participation(s) for s in F["inj_status"]]
    else:
        part = [availability.get(k) or _legacy_participation(None) | {"reasons": ["no availability observation before the cut-off"]}
                for k in keys]
    classes = [p.get("_class") for p in part]
    if calib is not None:
        F["p_play"] = PART.calibrated_p_play(F["p_hurdle"].to_numpy(), classes, calib)
        basis = ["report-recalibrated hurdle" if c else "hurdle (no availability observation)" for c in classes]
        basis = ["confirmed starter" if c == "STARTER_CONFIRMED" else b for c, b in zip(classes, basis)]
    else:
        F["p_play"] = F["p_hurdle"]
        basis = ["hurdle"] * len(F)
    # optional joint rotation model (minutes_jrm): replaces the independent hurdle x marginal minutes by report-calibrated eligibility, a depth-aware
    # rotation model and an exact team-minutes budget. The default engine ("frozen") leaves everything below byte-for-byte as before.
    jrm_on = minutes_engine == "jrm" and mode == "next_slate"
    if minutes_engine not in ("frozen", "jrm"):
        raise ValueError(f"unknown minutes_engine {minutes_engine!r}")
    if jrm_on:
        from . import minutes_jrm as J
        fj = f.assign(E=mp["E"], D=mp["D"])
        jr = J.slate_minutes(fj, classes, SLATE_SEASON)
        F["p_play"] = jr["p_jrm"].to_numpy()
        F["min_best"] = jr["m_jrm"].to_numpy()
        F["min_inj"] = jr["m_jrm"].to_numpy()
        f.loc[sl_idx, "min_best"] = F["min_best"].to_numpy()
        from .live.availability import SRC_OFFICIAL as _SRC_OFF
        # the eligibility head is calibrated on the official designation exactly where the official report covers the player (the verifier's D1/D2 read these labels)
        basis = [("confirmed starter" if c == "STARTER_CONFIRMED" else
                  ("joint rotation model (report-calibrated eligibility)" if p.get("source") == _SRC_OFF else "joint rotation model (history-only eligibility)"))
                 for c, p in zip(classes, part)]
    # minutes: report-aware E_inj where the official report covers the game, else the frozen best (E)
    from .live.availability import SRC_OFFICIAL
    report_cov = np.array([bool(p.get("source") == SRC_OFFICIAL) for p in part])
    F["min_pub"] = np.where(report_cov, F["min_inj"], F["min_best"])
    caps = np.array([((p.get("restriction") or {}).get("minutes_cap") or np.nan) for p in part], float)
    F["min_cap"] = caps
    capped = np.isfinite(caps) & (F["min_best"].to_numpy() > caps)
    F["min_pub"] = np.where(capped, np.minimum(F["min_pub"], caps), F["min_pub"])
    F["min_best"] = np.where(capped, np.minimum(F["min_best"], caps), F["min_best"])
    mres = J.minutes_dist_params() if jrm_on else frozen["minutes_dist"]
    # team
    tt, _ = T.fit_team(tctx)
    tt = tt[tt["game_id"].isin(set(F["game_id"]))]
    tbest = frozen["team"]["best"]
    tdist = models.make_dist(frozen["team"]["dist"], tt[tbest].to_numpy())
    tt = tt.assign(mean=tdist.mean, p10=tdist.quantile(0.1), p90=tdist.quantile(0.9), _tpos=np.arange(len(tt)))
    team_mean = {(g, t_): float(m) for g, t_, m in zip(tt["game_id"], tt["team"], tt["mean"])}
    # ---- pass 1: family means (frozen best models), then the reconciliation gate
    fam_state = {}
    for fam, (col, gkey, rungs) in FAMILIES.items():
        fz = frozen["families"][fam]
        sp, _ = S.fit_family(f, col, "min_best", M.INJ, frozen=fz["params"], final_only=True)
        fam_state[fam] = {"sp": sp, "mu": sp.loc[sl_idx, fz["best"]].to_numpy().astype(float),
                          "rate": sp.loc[sl_idx, "rate"].to_numpy(), "fz": fz}
    rec_in = pd.DataFrame({"game_id": F["game_id"].to_numpy(), "team": F["team"].to_numpy(), "p_play": F["p_play"].to_numpy(),
                           "minutes": F["min_pub"].to_numpy(), "pts": fam_state["points"]["mu"]}, index=F.index)
    scales, recs = REC.reconcile(rec_in, team_mean, reconcile_cfg or REC.Config()) if mode == "next_slate" else \
        (pd.DataFrame({"min_scale": 1.0, "usage_scale": 1.0}, index=F.index), [])
    ms, us = scales["min_scale"].to_numpy(), scales["usage_scale"].to_numpy()
    F["min_best_f"] = np.minimum(F["min_best"].to_numpy() * ms, 46.0)
    F["min_pub_f"] = np.minimum(F["min_pub"].to_numpy() * ms, 46.0)
    pts_min = fam_state["points"]["mu"] * ms
    for fam in FAMILIES:
        mu = fam_state[fam]["mu"] * ms
        if fam in ("points", "fga", "threes"):
            mu = mu * us
        elif fam == "pra":
            mu = mu + pts_min * us - pts_min
        fam_state[fam]["mu_f"] = mu
    rec_by_team = {(r["game_id"], r["team"]): r for r in recs}
    mdist = models.make_dist(mres, F["min_pub_f"].to_numpy())
    hist_all = f[f["played"] & ~f["is_slate"]].sort_values(["date", "game_id"])
    hist = {pid: g.tail(10) for pid, g in hist_all[hist_all["pid"].isin(set(F["pid"]))].groupby("pid")}
    empty_h = hist_all.iloc[:0]
    fam_out = {}
    player_rows = []
    gate_now = now_utc

    def add_row(i, ix, fam, gkey, d, rungs, mean_pub, fz_readiness, opp_f, opp_n, minutes_pub, adj_extra=None):
        r = F.loc[ix]
        pa = part[i]
        h = hist.get(r["pid"], empty_h)
        col = FAMILIES[fam][0] if fam in FAMILIES else "minutes"
        th = {str(k): round(float(d.prob_ge(k)[i]), 4) for k in rungs}
        rec = rec_by_team.get((r["game_id"], r["team"]))
        gi = gate.GateInput(sport="NBA", family=gkey, entity_id=str(r["pid"]), entity_name=r["name"], team=r["team"],
                            game_id=f"espn:{r['game_id']}", game_start_utc=_iso(r["tip_utc"]),
                            mean=float(d.mean[i]), data_asof_utc=asof, injury_status=pa["gate_injury_status"],
                            expected_opportunity=float(F.loc[ix, "min_best_f"]),
                            opportunity_history=h["minutes_act"].tolist(),
                            stat_history=h[f"{col}_act"].tolist() if f"{col}_act" in h else h["minutes_act"].tolist(),
                            opponent_factor=opp_f, opponent_sample_games=opp_n,
                            support_lo=int(d.lo), probs=d.P[i], thresholds={k: v for k, v in th.items()},
                            sd=float(np.sqrt(max(d.var[i], 0))), model_n_obs=int(np.nan_to_num(r["minutes_p_n"])),
                            participation=pa["status"], participation_reasons=pa["reasons"])
        gres = gate.evaluate(gi, now_utc=gate_now)
        pp = {k: v for k, v in pa.items() if not k.startswith("_")}
        pp.pop("gate_injury_status", None)
        pp["p_play"] = round(float(r["p_play"]), 4)
        pp["p_play_basis"] = basis[i]
        adj = [f"Participation: P(play) {r['p_play']:.2f} ({basis[i]}; availability {pa['status']}"
               f"{', ' + pa['designation'].lower() if pa.get('designation') else ''}). Projections below are conditional on playing."]
        if fam in FAMILIES and abs(opp_f - 1) >= 0.03:
            adj.append(f"Opponent {r['opp']} allows {('more' if opp_f > 1 else 'less')} {fam} to {r['pos']}s than expected: "
                       f"x{opp_f:.3f} ({opp_n} games).")
        if r.get("out_min", 0) and r["out_min"] >= 20 and fam in FAMILIES:
            adj.append(f"Teammates listed out account for ~{r['out_min']:.0f} recent minutes (minutes/usage redistributed).")
        if r["team_changed"] == 1 or r["games_with_team"] < 5:
            adj.append("New team: role estimated from prior-team history and position priors.")
        if np.nan_to_num(r["minutes_p_n"]) < 3:
            adj.append("Fewer than 3 career games in the data: projection is prior-driven.")
        if np.isfinite(F.loc[ix, "min_cap"]):
            adj.append(f"Minutes restriction reported (cap ~{F.loc[ix, 'min_cap']:.0f} min): minutes capped.")
        if rec and rec["action"] != "none":
            adj.append(f"Team reconciliation: {'; '.join(rec['reasons'])}.")
        adj += adj_extra or []
        findings = [{k: x[k] for k in ("check", "severity", "what", "category", "action")} for x in gres["findings"]]
        status = gres["status"]
        if rec and (fam in ("points", "pra", "minutes") or rec["action"] != "none") and rec["status"] != "PASS":
            for fd in rec["findings"]:
                findings.append({k: fd[k] for k in ("check", "severity", "what", "category", "action")})
            if {"PASS": 0, "REVIEW": 1, "BLOCK": 2}[rec["status"]] > {"PASS": 0, "REVIEW": 1, "BLOCK": 2}[status]:
                status = rec["status"]
        if np.isfinite(F.loc[ix, "min_cap"]):
            findings.append({"check": "restriction", "severity": "REVIEW", "what": "Minutes restriction reported",
                             "category": "uncertainty", "action": "Treat as conditional on a limited role."})
            status = status if status == "BLOCK" else "REVIEW"
        row = {
            "player_id": f"espn:{r['pid']}", "name": r["name"], "team": r["team"], "opponent": r["opp"],
            "game_id": f"espn:{r['game_id']}", "family": fam, "mean": round(float(d.mean[i]), 2),
            "median": int(d.median[i]), "p10": int(d.quantile(0.1)[i]), "p90": int(d.quantile(0.9)[i]),
            "thresholds": th,
            "opportunity": {"family": "minutes", "mean": round(float(mdist.mean[i]), 1),
                            "p10": int(mdist.quantile(0.1)[i]), "p90": int(mdist.quantile(0.9)[i])},
            "opponent_adjustment": {"factor": round(opp_f, 4), "sample_games": int(opp_n)},
            "adjustments": adj, "readiness": fz_readiness,
            "gate": {"status": status, "findings": findings},
            "participation": pp, "role": "shadow", "data_asof_utc": asof,
            "_pmf": {"lo": int(d.lo), "probs": d.P[i]},
            "_tags": {"new_team": bool(r["team_changed"] == 1 or r["games_with_team"] < 5),
                      "reconciled": (rec or {}).get("action", "none"), "minutes_model": J.VERSION if jrm_on else ("E_inj" if report_cov[i] else best_min),
                      "n_own_games": int(np.nan_to_num(r["minutes_p_n"]))}}
        player_rows.append(row)

    # ---- pass 2: distributions, gate, rows
    for fam, (col, gkey, rungs) in FAMILIES.items():
        st_ = fam_state[fam]
        fz, sp, mu, rate = st_["fz"], st_["sp"], st_["mu_f"], st_["rate"]
        if fz["dist"] == "mixture":
            scen = D.minutes_scenarios(mres if jrm_on else fz["min_res"], F["min_best_f"].to_numpy())
            scale = mu / np.maximum(rate * scen.mean(axis=1), 1e-6)
            d = D.mixture(rate, scen, fz["alpha_given_minutes"], SUPPORT_K[col], scale)
        elif fz["dist"] == "single_minutes_nb":
            d = dists.negbin(np.maximum(mu, 0.05), fz["alpha_given_minutes"], SUPPORT_K[col])
        else:
            d = models.make_dist(fz["dist_params"], np.maximum(mu, 0.05))
        F[f"{col}_mean"] = d.mean
        fam_out[fam] = {"readiness": fz["readiness"], "model": fz["model_name"], "reason": fz["readiness_reason"]}
        for i, ix in enumerate(sl_idx):
            add_row(i, ix, fam, gkey, d, rungs, float(d.mean[i]), fz["readiness"], float(sp.loc[ix, "opp_factor"]),
                    int(sp.loc[ix, "opp_n"]), float(F.loc[ix, "min_pub_f"]),
                    [f"Expected pace adjustment x{sp.loc[ix, 'pace_adj']:.3f}."] if abs(sp.loc[ix, "pace_adj"] - 1) >= 0.01 else None)
    for i, ix in enumerate(sl_idx):                       # minutes: the study's priority family (report-aware where covered)
        add_row(i, ix, "minutes", "minutes", mdist, MINUTES_RUNGS, float(mdist.mean[i]),
                frozen["minutes_readiness"]["readiness"], 1.0, 0, float(F.loc[ix, "min_pub_f"]),
                ["Minutes model: " + (f"joint rotation model ({J.VERSION}, {'report-aware' if report_cov[i] else 'history-only'} eligibility): team minutes conserved, no normalisation" if jrm_on else
                                      ("E_inj (official report features)" if report_cov[i] else f"{best_min} (no official report for this game)")) + "."])
    # team block
    games = []
    game_forecast_errors: list[str] = []
    game_forecasts = []                      # sift.game_forecast.v1 (archived by nba.paper.run; additive, not part of the published projections)
    for gid, g in tt.groupby("game_id"):
        gg = {"game_id": f"espn:{gid}", "start_utc": _iso(g["tip_utc"].iloc[0]),
              "home": g.loc[g["home"], "team"].iloc[0], "away": g.loc[~g["home"], "team"].iloc[0], "teams": []}
        for _, r in g.iterrows():
            rec = rec_by_team.get((gid, r["team"]))
            sub = F[(F["game_id"] == gid) & (F["team"] == r["team"])]
            raw_sum = float((sub["p_play"] * fam_state["points"]["mu"][[F.index.get_loc(i) for i in sub.index]]).sum())
            t_ = {"team": r["team"], "family": "team_points", "mean": round(float(r["mean"]), 1), "p10": int(r["p10"]),
                  "p90": int(r["p90"]), "player_points_sum": round(rec["points_sum_final"] if rec else raw_sum, 1),
                  "player_points_sum_raw": round(raw_sum, 1),
                  "reconciliation": rec["status"] if rec else gate.team_reconciliation(raw_sum, float(r["mean"]), r["team"])["status"]}
            if rec:
                t_["reconciliation_detail"] = {k: rec[k] for k in ("minutes_sum_raw", "minutes_sum_final", "minutes_scale", "usage_scale",
                                                                   "points_sum_raw", "points_sum_final", "action", "reasons")}
            gg["teams"].append(t_)
        games.append(gg)
        try:
            game_forecasts.append(_game_forecast(gg, g, tdist, now_utc, asof))
        except Exception as e:  # noqa: BLE001  additive output: it must never take down the published player projections
            game_forecast_errors.append(f"{gid}: {type(e).__name__}: {e}"[:200])
    fam_out["team_points"] = {"readiness": frozen["team"]["readiness"], "model": frozen["team"]["model_name"],
                              "reason": frozen["team"]["readiness_reason"]}
    mr = frozen["minutes_readiness"]
    if jrm_on:
        mr = {**mr, **J.readiness()["minutes"], "model_name": f"joint rotation model ({J.VERSION})"}
    fam_out["minutes"] = {"readiness": mr["readiness"], "model": mr["model_name"], "reason": mr["readiness_reason"]}
    res = {"schema": "sift.projections.v1", "sport": "NBA",
           "generated_utc": now_utc, "data_asof_utc": asof,
           "model": {"id": MODEL_ID, "version": f"pf-{PF_VERSION}+{_git_sha()}", "authority": "research_only",
                     **({"minutes_engine": J.VERSION} if jrm_on else {})},          # the key exists only for the joint rotation model: the frozen document is unchanged
           "mode": mode, "slate_date": str(pd.Timestamp(F["date"].iloc[0]).date()) if len(F) else None,
           "history_through": str(pd.Timestamp(hist_last).date()),
           "inputs": files, "families": fam_out, "games": games, "players": player_rows,
           "reconciliation": recs, "runtime_s": round(time.time() - t0, 1), "game_forecasts": game_forecasts,
           "game_forecast_errors": game_forecast_errors}
    if out:
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        pub = dict(res, players=[{k: v for k, v in p.items() if not k.startswith("_")} for p in player_rows])
        pub.pop("game_forecasts", None)
        pub.pop("game_forecast_errors", None)                       # archived separately (nba.paper.run); the published view is unchanged
        with open(out, "w") as fh:
            json.dump(pub, fh, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
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
