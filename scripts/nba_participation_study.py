"""W2 runner: participation / minutes decomposition of the frozen V1 simulator + preregistered PIT arms.

    python scripts/nba_participation_study.py collect --window dev     --out $SCRATCH/w2 \
        --pit data/history/injury_reports --pbp data/history/espn_pbp
    python scripts/nba_participation_study.py fit     --out $SCRATCH/w2          # pi_s from DEV
    python scripts/nba_participation_study.py collect --window holdout --out $SCRATCH/w2 --pi $SCRATCH/w2/pi.json ...
    python scripts/nba_participation_study.py report  --window holdout --out $SCRATCH/w2 --json docs/...

Preregistration: docs/research/PREREG_W2_NBA_PARTICIPATION.md. Inputs: committed ESPN box history
(champion), PR #23 T-60 injury snapshots, PR #22 certified stints. No market file is opened.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import nba_matched_decomposition as nmd  # noqa: E402

from nba_edge.research import matched_decomposition as md  # noqa: E402
from nba_edge.research import participation as pt  # noqa: E402

SEASON = "2025-26"
WINDOWS = {"dev": [("2025-11-15", "2026-01-31")], "holdout": nmd.WINDOWS["holdout"]}
N_SIMS = 2000
ARMS = ("champion", "pit_prop", "pit_lineup", "o_part", "o_part_total")
STATUSES = ("out", "doubtful", "questionable", "probable", "available")


def window_games(tg: pd.DataFrame, window: str) -> pd.DataFrame:
    home = tg[tg["home"] == True].sort_values(["game_date_et", "start_time_utc", "game_id"])  # noqa: E712
    m = np.zeros(len(home), dtype=bool)
    for lo, hi in WINDOWS[window]:
        m |= (home["game_date_et"] >= lo).to_numpy() & (home["game_date_et"] <= hi).to_numpy()
    return home[m]


def load_pit(pit_dir: Path) -> tuple[dict[str, dict[int, str]], dict[str, dict]]:
    """game_id -> {nba_id: T-60 status} (only pit_ok snapshots), and per-game snapshot provenance."""
    g = pd.read_parquet(pit_dir / f"game_snapshots_{SEASON}.parquet")
    rows = pd.read_parquet(pit_dir / f"report_rows_{SEASON}.parquet")
    g = g[g["t_minus_60_pit_ok"]]
    sev = {s: i for i, s in enumerate(STATUSES)}
    rows = rows[rows["nba_id"].notna() & rows["status"].isin(STATUSES)]
    key = rows.merge(g[["game_id", "t_minus_60_slot_et"]], left_on=["game_id", "slot_et"],
                     right_on=["game_id", "t_minus_60_slot_et"])
    out: dict[str, dict[int, str]] = {gid: {} for gid in g["game_id"]}
    for gid, pid, st in key[["game_id", "nba_id", "status"]].itertuples(index=False):
        cur = out[gid].get(int(pid))
        if cur is None or sev[st] < sev[cur]:  # duplicate listing: keep the more severe
            out[gid][int(pid)] = st
    prov = {r["game_id"]: {"slot_et": r["t_minus_60_slot_et"], "report_time_utc": r["t_minus_60_report_time_utc"],
                           "published_utc": r["t_minus_60_published_utc"], "tip_utc": r["tip_utc"]}
            for r in g.to_dict("records")}
    return out, prov


def load_onoff(pbp_dir: Path, tg: pd.DataFrame) -> pt.OnOffIndex:
    st = pd.read_parquet(pbp_dir / f"stints_{SEASON}.parquet")
    st = st[st["certified"]]
    info = tg[tg["home"] == True][["game_id", "game_date_et", "team_id", "opp_team_id"]].rename(  # noqa: E712
        columns={"team_id": "home_team_id", "opp_team_id": "away_team_id"})
    gm = pd.read_parquet(pbp_dir / f"pbp_games_{SEASON}.parquet")[["game_id", "home_team_id", "away_team_id"]]
    chk = info.merge(gm, on="game_id", suffixes=("", "_pbp"))
    bad = int(((chk["home_team_id"] != chk["home_team_id_pbp"]) | (chk["away_team_id"] != chk["away_team_id_pbp"])).sum())
    if bad:
        raise ValueError(f"{bad} games disagree on home/away team between box history and pbp")
    return pt.OnOffIndex.from_stints(st, info)


def collect(a) -> dict:
    tg, pg = nmd.load(Path(a.data))
    alpha = md.fit_baseline_dispersion(pg, nmd.DISPERSION_FIT_BEFORE)
    statuses, prov = load_pit(Path(a.pit))
    onoff = load_onoff(Path(a.pbp), tg)
    pi = json.loads(Path(a.pi).read_text())["pi"] if a.pi else {}
    games = window_games(tg, a.window)
    if a.limit:
        games = games.iloc[: a.limit]
    rows, ginfo = [], []
    t0 = time.time()
    for k, (_, r) in enumerate(games.iterrows()):
        gid, date = str(r["game_id"]), str(r["game_date_et"])
        meta, fc, _ = md.forecast_game(r, tg, pg, alpha, N_SIMS, ("sim_rotation",))
        amb = md.ambiguous_players(meta)
        box = pg[pg["game_id"] == gid]
        st = statuses.get(gid)
        gi = {"game_id": gid, "date": date, "pit_ok": st is not None, **(prov.get(gid) or {})}
        for team_id in (int(r["team_id"]), int(r["opp_team_id"])):
            mt = [m for m in meta if m["team_id"] == team_id and m["player_id"] not in amb]
            ids = [m["player_id"] for m in mt]
            M = np.stack([fc["sim_rotation"][p].stats["min"] * fc["sim_rotation"][p].played for p in ids])
            act = {p: md.actual_outcomes(box, p, team_id) for p in ids}
            y = np.array([act[p]["min"] for p in ids])
            team_st = {p: s for p, s in (st or {}).items() if p in set(ids)}
            seed = pt.pit_seed(gid) + team_id
            arms = {"champion": M}
            if st is not None and pi:
                arms["pit_prop"], ip = pt.apply_pit(M, ids, team_st, pi, seed)
                wf = lambda a_, rec, team_id=team_id, date=date: onoff.weights(team_id, date, a_, rec)  # noqa: E731
                arms["pit_lineup"], il = pt.apply_pit(M, ids, team_st, pi, seed, weight_fn=wf)
                gi[f"t{team_id}_removed"] = ip["minutes_removed"]
                gi[f"t{team_id}_unassigned_prop"] = ip["minutes_unassigned"]
                gi[f"t{team_id}_unassigned_lineup"] = il["minutes_unassigned"]
                gi[f"t{team_id}_clipped_lineup"] = il["minutes_clipped"]
                gi[f"t{team_id}_lineup_used"] = il["lineup_weight_used"]
                gi[f"t{team_id}_lineup_fallback"] = il["lineup_weight_fallback"]
            else:
                arms["pit_prop"] = arms["pit_lineup"] = M
            # oracles (upper bounds, not forecasts)
            op = [pt.oracle_participation(M[i], y[i]) for i in range(len(ids))]
            cm = np.array([o.mean() if y[i] > 0 and (M[i] > 0).any() else np.nan for i, o in enumerate(op)])
            target = float(sum(y[i] for i in range(len(ids)) if y[i] > 0))
            denom = float(np.nansum(cm))
            scale = target / denom if denom > 0 else 1.0
            opt = [o * scale if np.isfinite(cm[i]) else o for i, o in enumerate(op)]
            for i, p in enumerate(ids):
                row = {"game_id": gid, "date": date, "team_id": team_id, "player_id": p, "actual_min": float(y[i]),
                       "played": bool(y[i] > 0), "in_box": bool(act[p]["in_box"]), "status_t60": team_st.get(p, "unlisted" if st is not None else "no_pit"),
                       "p_start": float(mt[i]["p_start"])}
                draws = {"champion": M[i], "pit_prop": arms["pit_prop"][i], "pit_lineup": arms["pit_lineup"][i],
                         "o_part": op[i], "o_part_total": opt[i]}
                for arm, x in draws.items():
                    for k2, v in pt.row_metrics(x, float(y[i])).items():
                        row[f"{arm}_{k2}"] = v
                c = M[i][M[i] > 0]
                row["champion_cond_mean"] = float(c.mean()) if c.size else float("nan")
                rows.append(row)
        ginfo.append(gi)
        if (k + 1) % 50 == 0:
            print(f"{a.window}: {k + 1}/{len(games)} games, {len(rows)} rows, {time.time() - t0:.0f}s", file=sys.stderr)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(out / f"rows_{a.window}.parquet", index=False)
    pd.DataFrame(ginfo).to_parquet(out / f"games_{a.window}.parquet", index=False)
    info = {"window": a.window, "dates": WINDOWS[a.window], "n_games": len(ginfo), "n_rows": len(rows),
            "n_sims": N_SIMS, "pi": pi, "seconds": round(time.time() - t0, 1),
            "non_eligible_played": "see report"}
    (out / f"collect_{a.window}.json").write_text(json.dumps(info, indent=1))
    return info


def fit(a) -> dict:
    w = pd.read_parquet(Path(a.out) / "rows_dev.parquet")
    w = w[w["status_t60"] != "no_pit"]
    res = {"n_dev_rows": int(len(w)), "by_status": {}}
    for s in (*STATUSES, "unlisted"):
        d = w[w["status_t60"] == s]
        res["by_status"][s] = {"n": int(len(d)), "appear_rate": round(float(d["played"].mean()), 4) if len(d) else None,
                               "champion_mean_p_appear": round(float(d["champion_p_appear"].mean()), 4) if len(d) else None}
    res["pi"] = {s: res["by_status"][s]["appear_rate"] for s in pt.THINNED_STATUSES if res["by_status"][s]["n"]}
    (Path(a.out) / "pi.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    return res


def _boot_mean(df: pd.DataFrame, col: str, n_boot: int) -> dict:
    d = df[["game_id", col]].assign(one=1.0).dropna()
    pgs = md.per_game_sums(d, [col, "one"])
    p, ci = md.cluster_bootstrap(pgs, lambda s: np.array([s[0] / s[1]]), n_boot)
    return {"value": md._rnd(p[0]), "ci95": md._rnd(ci[0])}


def _paired(df: pd.DataFrame, metric: str, a: str, b: str, n_boot: int, y: str | None = None) -> dict:
    if y is None:
        la, lb = df[f"{a}_{metric}"], df[f"{b}_{metric}"]
    else:  # Brier of a probability column against an outcome column
        la, lb = (df[f"{a}_{metric}"] - df[y]) ** 2, (df[f"{b}_{metric}"] - df[y]) ** 2
    d = pd.DataFrame({"game_id": df["game_id"], "la": la, "lb": lb, "one": 1.0}).dropna()
    if d.empty:
        return {"n": 0}
    pgs = md.per_game_sums(d, ["la", "lb", "one"])
    p, ci = md.cluster_bootstrap(pgs, lambda s: np.array([s[0] / s[2], s[1] / s[2], (s[1] - s[0]) / s[2]]), n_boot)
    return {"n": int(len(d)), "n_games": int(pgs.shape[0]), a: md._rnd(p[0]), b: md._rnd(p[1]),
            "delta": md._rnd(p[2]), "ci95": md._rnd(ci[2])}


def decomposition(w: pd.DataFrame, n_boot: int) -> dict:
    """Part 1: champion error of the mean forecast split by participation outcome and T-60 status."""
    mu = w["champion_mean"]
    y = w["actual_min"]
    p = w["champion_p_appear"]
    c = w["champion_cond_mean"].fillna(0.0)
    e = mu - y
    dnp = ~w["played"]
    out = {"rows": int(len(w)), "games": int(w["game_id"].nunique()), "played_rows": int((~dnp).sum()),
           "dnp_rows": int(dnp.sum()), "dnp_not_in_box_rows": int((dnp & ~w["in_box"]).sum())}
    sse, sae = float((e**2).sum()), float(e.abs().sum())
    out["mean_forecast"] = {"rmse": round(float(np.sqrt((e**2).mean())), 4), "mae": round(float(e.abs().mean()), 4),
                            "bias": round(float(e.mean()), 4)}
    out["share_of_squared_error"] = {"dnp_rows": round(float((e[dnp] ** 2).sum()) / sse, 4),
                                     "played_rows": round(float((e[~dnp] ** 2).sum()) / sse, 4)}
    out["share_of_absolute_error"] = {"dnp_rows": round(float(e[dnp].abs().sum()) / sae, 4),
                                      "played_rows": round(float(e[~dnp].abs().sum()) / sae, 4)}
    part = -(1 - p[~dnp]) * c[~dnp]
    cond = c[~dnp] - y[~dnp]
    out["played_rows_split"] = {
        "sum_sq_participation_term": round(float((part**2).sum()) / sse, 4),
        "sum_sq_conditional_term": round(float((cond**2).sum()) / sse, 4),
        "cross_term": round(float((2 * part * cond).sum()) / sse, 4),
        "note": "shares of the TOTAL squared error; participation term = -(1-p)c, conditional term = c - y"}
    by = {}
    for s, d in w[dnp].groupby("status_t60"):
        ed = e[d.index]
        by[s] = {"dnp_rows": int(len(d)), "share_of_dnp_abs_error": round(float(ed.abs().sum()) / float(e[dnp].abs().sum()), 4),
                 "share_of_total_sq_error": round(float((ed**2).sum()) / sse, 4),
                 "mean_champion_p_appear": round(float(d["champion_p_appear"].mean()), 4),
                 "mean_champion_forecast_min": round(float(mu[d.index].mean()), 3)}
    out["dnp_by_t60_status"] = by
    out["rows_by_t60_status"] = {s: {"n": int(len(d)), "appear_rate": round(float(d["played"].mean()), 4),
                                     "champion_mean_p_appear": round(float(d["champion_p_appear"].mean()), 4)}
                                 for s, d in w.groupby("status_t60")}
    out["crps_oracle_attribution"] = {
        arm: _boot_mean(w, f"{arm}_crps", n_boot) for arm in ("champion", "o_part", "o_part_total")}
    ch, op, opt = (out["crps_oracle_attribution"][k]["value"] for k in ("champion", "o_part", "o_part_total"))
    out["crps_oracle_attribution"]["share_removed_by_known_participation_(a)"] = round((ch - op) / ch, 4)
    out["crps_oracle_attribution"]["share_remaining_minutes_given_play_(b)"] = round(op / ch, 4)
    out["crps_oracle_attribution"]["of_(b)_team_total_part"] = round((op - opt) / ch, 4)
    out["crps_oracle_attribution"]["of_(b)_within_team_allocation"] = round(opt / ch, 4)
    out["mae_oracle"] = {arm: _boot_mean(w, f"{arm}_ae_median", n_boot) for arm in ("champion", "o_part", "o_part_total")}
    return out


def report(a) -> dict:
    out = Path(a.out)
    w = pd.read_parquet(out / f"rows_{a.window}.parquet")
    g = pd.read_parquet(out / f"games_{a.window}.parquet")
    nb = a.n_boot
    res: dict = {"window": a.window, "dates": WINDOWS[a.window], "n_games": int(len(g)), "n_rows": int(len(w)),
                 "games_with_pit_t60": int(g["pit_ok"].sum()),
                 "collect": json.loads((out / f"collect_{a.window}.json").read_text())}
    res["part1_decomposition"] = decomposition(w, nb)
    w["y10"] = (w["actual_min"] >= 10).astype(float)
    w["yplay"] = w["played"].astype(float)
    team_has_out = w.groupby(["game_id", "team_id"])["status_t60"].transform(lambda s: (s == "out").any())
    frames = {"all": w, "teams_with_eligible_out": w[team_has_out], "played_rows_diagnostic": w[w["played"]]}
    part2 = {}
    for fname, f in frames.items():
        fr = {}
        for a_, b_ in (("champion", "pit_prop"), ("champion", "pit_lineup"), ("pit_prop", "pit_lineup")):
            fr[f"{b_}_minus_{a_}"] = {
                "crps": _paired(f, "crps", a_, b_, nb), "mae_median": _paired(f, "ae_median", a_, b_, nb),
                "mse_mean": _paired(f, "se_mean", a_, b_, nb),
                "brier_appear": _paired(f, "p_appear", a_, b_, nb, y="yplay"),
                "brier_10min": _paired(f, "p10min", a_, b_, nb, y="y10")}
        fr["levels"] = {arm: {"crps": md._rnd(f[f"{arm}_crps"].mean()), "mae_median": md._rnd(f[f"{arm}_ae_median"].mean()),
                              "rmse_mean": md._rnd(np.sqrt(f[f"{arm}_se_mean"].mean())),
                              "bias_mean": md._rnd((f[f"{arm}_mean"] - f["actual_min"]).mean()),
                              "coverage_p10_p90": md._rnd(f[f"{arm}_cov_p10_p90"].mean()),
                              "mean_p_appear": md._rnd(f[f"{arm}_p_appear"].mean())} for arm in ARMS}
        fr["n_rows"], fr["n_games"] = int(len(f)), int(f["game_id"].nunique())
        part2[fname] = fr
    res["part2_arms"] = part2
    tcols = [c for c in g.columns if c.startswith("t") and c[1:].split("_")[0].isdigit()]
    agg = {}
    for suffix in ("removed", "unassigned_prop", "unassigned_lineup", "clipped_lineup", "lineup_used", "lineup_fallback"):
        cols = [c for c in tcols if c.endswith("_" + suffix)]
        agg[suffix] = round(float(g[cols].sum().sum()), 2) if cols else 0.0
    res["redistribution_totals"] = agg
    res["observed_actual_play_rate"] = round(float(w["played"].mean()), 4)
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(res, indent=1, default=str)[:20000])
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["collect", "fit", "report"])
    ap.add_argument("--window", choices=list(WINDOWS), default="dev")
    ap.add_argument("--out", required=True)
    ap.add_argument("--data", default=str(ROOT / "data"))
    ap.add_argument("--pit", default=str(ROOT / "data" / "history" / "injury_reports"))
    ap.add_argument("--pbp", default=str(ROOT / "data" / "history" / "espn_pbp"))
    ap.add_argument("--pi", default=None, help="pi.json from `fit` (DEV); without it the PIT arms equal the champion")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    {"collect": collect, "fit": fit, "report": report}[a.cmd](a)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
