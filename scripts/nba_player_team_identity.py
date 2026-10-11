"""Traded-player identity: quantify the opt-in fix on the Wave 1 holdout (research only).

    # 1. which holdout games change, and by how much (V1 frozen champion vs the opt-in fix)
    python scripts/nba_player_team_identity.py audit --out $OUT --json docs/research/w1_nba/player_team_identity.json
    # 2. bit-identity of every other output: a full holdout collect with the fix on
    #    (nba_matched_decomposition.py collect --resolve-cross-team-players) against a V1 collect
    python scripts/nba_player_team_identity.py compare --fixed $OUT/fix --reference $W1/hold --json ...

The frozen champion NBA_BASELINE_2026_PRESEASON_V1 is not modified. ``audit`` runs it exactly as the
matched-decomposition harness does (``BuildConfig()``), and runs the fix as
``BuildConfig(resolve_cross_team_players=True)`` on the same games, seeds and simulation counts.
Inputs are the committed ESPN box history only; no market file is opened.
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
sys.path.insert(0, str(ROOT / "scripts"))

import nba_matched_decomposition as runner  # noqa: E402

from nba_edge.features.build import BuildConfig, build_game_params, cross_team_resolution  # noqa: E402
from nba_edge.research import matched_decomposition as md  # noqa: E402
from nba_edge.sim.engine import simulate  # noqa: E402

FIX = BuildConfig(resolve_cross_team_players=True)
V1 = BuildConfig()
STAT_PAIRS = [("sim_rotation_v1", "sim_rotation_fix")]


def _arm(players: dict, three_share: dict) -> dict:
    """Same conversion as ``md._sim_arm`` (appearance = available AND minutes > 0), for any keying."""
    out = {}
    for key, ps in players.items():
        st = {k: np.asarray(ps.stats[k], dtype=float) for k in ("min", "pts", "reb", "ast", "fg3m", "fga", "fta", "tov")}
        st["fg3a"] = st["fga"] * float(three_share[(ps.team_id, ps.nba_id)])
        appeared = np.asarray(ps.played, dtype=bool) & (st["min"] > 0)
        out[key] = md.ArmForecast(played=appeared, stats=st, available=np.asarray(ps.played, dtype=bool))
    return out


def _three_share(gp) -> dict:
    return {(t.team_id, p.nba_id): p.three_share for t in (gp.home, gp.away) for p in t.players}


def audit(data_root: Path, n_sims: int, n_boot: int) -> dict:
    tg, pg = runner.load(data_root)
    alpha = md.fit_baseline_dispersion(pg, runner.DISPERSION_FIT_BEFORE)
    games = runner.window_games(tg, "holdout")
    identical, changed = 0, []
    wide_all, long_all, traded_rows = [], [], []
    for _, r in games.iterrows():
        date = str(r["game_date_et"])
        tgc, pgc = tg[tg["game_date_et"] < date], pg[pg["game_date_et"] < date]
        game = md.game_inputs(r, tgc)
        inj = {game["home_team_id"]: {}, game["away_team_id"]: {}}
        gp_v1, _ = build_game_params(game, tgc, pgc, date, inj, None, V1)
        gp_fx, _ = build_game_params(game, tgc, pgc, date, inj, None, FIX)
        if gp_v1 == gp_fx:
            identical += 1
            continue
        res = cross_team_resolution(game, tgc, pgc, date, inj, None, FIX)
        seed = md.game_seed(str(r["game_id"]))
        sim_v1 = simulate(gp_v1, n_sims, seed)
        sim_fx = simulate(gp_fx, n_sims, seed)
        # the fixed run through the harness itself (ewm5 + sim_rotation, identical to a collect with the flag)
        meta, fc, _ = md.forecast_game(r, tg, pg, alpha, n_sims, ("ewm5", "sim_rotation"), champion_cfg=FIX)
        fx_by_pid = fc["sim_rotation"]
        v1_by_pid = _arm(sim_v1.players, _three_share(gp_v1))  # what any id-keyed consumer of V1 receives
        v1_by_team = _arm(sim_v1.players_by_team, _three_share(gp_v1))
        assert set(sim_fx.players) == set(fx_by_pid)
        # V1 restricted to the fixed population, traded players read from their KEPT team's copy
        v1_keep = dict(v1_by_pid)
        for pid, rr in res.items():
            if (rr["keep_team_id"], pid) in v1_by_team:
                v1_keep[pid] = v1_by_team[(rr["keep_team_id"], pid)]
        box = pg[pg["game_id"] == r["game_id"]]
        fc_all = {"ewm5": fc["ewm5"], "sim_rotation_fix": fx_by_pid, "sim_rotation_v1": v1_by_pid, "sim_rotation_v1_keepcopy": v1_keep}
        w, lg = md.score_game(meta, fc_all, box)
        wide_all.extend(w)
        long_all.extend(lg)
        roster_v1 = {t: {p.nba_id for p in getattr(gp_v1, s).players} for s, t in (("home", gp_v1.home.team_id), ("away", gp_v1.away.team_id))}
        roster_fx = {t: {p.nba_id for p in getattr(gp_fx, s).players} for s, t in (("home", gp_fx.home.team_id), ("away", gp_fx.away.team_id))}
        added = {int(t): sorted(int(x) for x in roster_fx[t] - roster_v1[t]) for t in roster_fx}
        removed = {int(t): sorted(int(x) for x in roster_v1[t] - roster_fx[t]) for t in roster_fx}
        changed.append({"game_id": str(r["game_id"]), "date": date, "home_team_id": int(r["team_id"]), "away_team_id": int(r["opp_team_id"]),
                        "n_traded": len(res), "roster_added_by_fix": added, "roster_removed_by_fix": removed})
        for pid, rr in res.items():
            b = box[box["nba_id"] == pid]
            row = {"game_id": str(r["game_id"]), "date": date, "player_id": pid,
                   "name": str(pgc[pgc["nba_id"] == pid]["player_name"].iloc[-1]),
                   "keep_team_id": rr["keep_team_id"], "stale_team_id": rr["stale_team_id"], "last_dates": {str(k): v for k, v in rr["last_dates"].items()},
                   # False: admitted to the stale team only once another stale entry freed a roster slot
                   "dual_eligible_in_v1": (rr["stale_team_id"], pid) in v1_by_team and (rr["keep_team_id"], pid) in v1_by_team,
                   "v1_id_keyed_copy_team_id": int(sim_v1.players[pid].team_id) if pid in sim_v1.players else None,
                   "box_team_id": int(b["team_id"].iloc[0]) if len(b) else None, "box_played": bool(b["played"].iloc[0]) if len(b) else False,
                   "act_min": float(b["minutes"].iloc[0]) if len(b) else 0.0, "act_pts": float(b["pts"].iloc[0]) if len(b) else 0.0}
            for name, f in (("v1_reported", v1_by_pid.get(pid)), ("v1_stale_copy", v1_by_team.get((rr["stale_team_id"], pid))),
                            ("v1_keep_copy", v1_by_team.get((rr["keep_team_id"], pid))), ("fix", fx_by_pid[pid])):
                if f is None:
                    continue
                row[f"{name}_p_play"] = round(float(f.played.mean()), 4)
                row[f"{name}_min"] = round(float(f.stats["min"].mean()), 3)
                row[f"{name}_pts"] = round(float(f.stats["pts"].mean()), 3)
            traded_rows.append(row)

    wide, long = pd.DataFrame(wide_all), pd.DataFrame(long_all)
    arms = ("ewm5", "sim_rotation_v1", "sim_rotation_v1_keepcopy", "sim_rotation_fix")
    pairs = [("sim_rotation_v1", "sim_rotation_fix"), ("sim_rotation_v1_keepcopy", "sim_rotation_fix")]
    traded_ids = {(t["game_id"], t["player_id"]) for t in traded_rows}
    is_traded = pd.Series([(g, p) in traded_ids for g, p in zip(wide["game_id"], wide["player_id"])], index=wide.index)
    out = {
        "window": "holdout", "date_ranges": runner.WINDOWS["holdout"], "n_sims": n_sims, "n_boot": n_boot,
        "n_games": int(len(games)), "n_games_identical_params": identical, "n_games_changed": len(changed),
        "changed_games": changed, "traded_players": traded_rows,
        "population_after_fix": {"n_player_games_in_changed_games": int(len(wide)), "n_traded_rows": int(is_traded.sum()),
                                 "n_other_rows_in_changed_games": int((~is_traded).sum())},
        "affected_games_all_rows": {
            "participation": md.participation_scorecard(wide, arms, pairs, n_boot),
            "stats": {s: {c: md.stat_scorecard(long, s, c, arms, pairs, n_boot) for c in ("unc", "cond")} for s in md.STATS},
        },
    }
    # the traded rows alone (n is small; descriptive)
    tl = long[[(g, p) in traded_ids for g, p in zip(long["game_id"], long["player_id"])]]
    out["traded_rows_only"] = {s: {c: md.stat_scorecard(tl, s, c, arms, pairs, n_boot) for c in ("unc",)} for s in md.STATS}
    return out


def compare(fixed: Path, reference: Path, window: str, changed_games: set[str]) -> dict:
    """Every output row outside the changed games must be bit-identical between the two collects."""
    out: dict = {"fixed": str(fixed), "reference": str(reference), "changed_games_excluded": sorted(changed_games)}
    key_long = ["game_id", "player_id", "arm", "cond", "stat"]
    cols = ["mean", "median", "p10", "p90", "crps", "p_ref", "t_ref", "n_draws", "actual"]
    lf, lr = pd.read_parquet(fixed / f"long_{window}.parquet"), pd.read_parquet(reference / f"long_{window}.parquet")
    arms = sorted(set(lf["arm"]) & set(lr["arm"]))
    lf, lr = lf[lf["arm"].isin(arms)], lr[lr["arm"].isin(arms)]
    out["arms_compared"] = arms
    for name, df in (("fixed", lf), ("reference", lr)):
        out[f"n_long_rows_{name}"] = int(len(df))
        out[f"n_long_rows_{name}_in_changed_games"] = int(df["game_id"].isin(changed_games).sum())
    a, b = lf[~lf["game_id"].isin(changed_games)], lr[~lr["game_id"].isin(changed_games)]
    m = a.merge(b, on=key_long, how="outer", suffixes=("_f", "_r"), indicator=True)
    out["n_long_rows_compared"] = int((m["_merge"] == "both").sum())
    out["n_long_rows_only_in_one"] = int((m["_merge"] != "both").sum())
    both = m[m["_merge"] == "both"]
    diffs = {}
    for c in cols:
        x, y = both[f"{c}_f"], both[f"{c}_r"]
        diffs[c] = int((~((x == y) | (x.isna() & y.isna()))).sum())
    diffs["probs"] = int(sum(1 for x, y in zip(both["probs_f"], both["probs_r"], strict=True)
                             if not np.array_equal(np.asarray(x, dtype=float), np.asarray(y, dtype=float), equal_nan=True)))
    out["n_long_rows_differing_by_column"] = diffs
    wf, wr = pd.read_parquet(fixed / f"wide_{window}.parquet"), pd.read_parquet(reference / f"wide_{window}.parquet")
    wcols = sorted(c for c in set(wf.columns) & set(wr.columns) if not any(c.startswith(p) for p in ("sim_waterfill", "sim_challenger")))
    a, b = wf[~wf["game_id"].isin(changed_games)], wr[~wr["game_id"].isin(changed_games)]
    m = a[wcols].merge(b[wcols], on=["game_id", "player_id"], how="outer", suffixes=("_f", "_r"), indicator=True)
    out["n_wide_rows_compared"] = int((m["_merge"] == "both").sum())
    out["n_wide_rows_only_in_one"] = int((m["_merge"] != "both").sum())
    bm = m[m["_merge"] == "both"]
    nd = 0
    for c in wcols:
        if c in ("game_id", "player_id"):
            continue
        x, y = bm[f"{c}_f"], bm[f"{c}_r"]
        nd += int((~((x == y) | (x.isna() & y.isna()))).sum())
    out["n_wide_cells_differing"] = nd
    out["n_wide_columns_compared"] = len(wcols) - 2
    out["bit_identical_outside_changed_games"] = bool(nd == 0 and sum(diffs.values()) == 0 and out["n_long_rows_only_in_one"] == 0 and out["n_wide_rows_only_in_one"] == 0)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["audit", "compare"])
    ap.add_argument("--data", type=Path, default=ROOT / "data")
    ap.add_argument("--sims", type=int, default=runner.N_SIMS)
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--fixed", type=Path)
    ap.add_argument("--reference", type=Path)
    ap.add_argument("--audit-json", type=Path, help="compare: the audit output naming the changed games")
    ap.add_argument("--json", type=Path)
    a = ap.parse_args(argv)
    if a.cmd == "audit":
        rep = audit(a.data, a.sims, a.boot)
    else:
        changed = {g["game_id"] for g in json.loads(a.audit_json.read_text())["changed_games"]}
        rep = compare(a.fixed, a.reference, "holdout", changed)
    txt = json.dumps(rep, indent=1, default=str)
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(txt + "\n")
    print(txt[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
