"""EXACT frozen-vs-JRM comparison through the full downstream projection engine (Issue #53, owner decision 3 on PR #54). ISOLATED DRY RUN, RESEARCH ONLY.

Unlike `jrm_matched.py` (an archive-scale APPROXIMATION from saved pmfs, always labelled as such), this runs PR #45's opt-in engine for real:

    nba.project.project_slate(sl, ..., minutes_engine="frozen")   and   (..., minutes_engine="jrm")

in ONE process, from ONE capture (same slate, same availability observations, same calibration, same clock) by calling the production `nba.live.run.stage_project`
twice with `PF_NBA_MINUTES_ENGINE` set per call. Usage, participation, reconciliation and publisher gates are therefore the engine's own. The two result sets are turned
into forecast records exactly as the live pipeline does (`nba.live.forecasts.challenger_records`), and BOTH are priced against the SAME market board with the SAME strict
rules (`engine.candidates_for` + `exec_shadow.select`), so the matched market selections can be compared contract by contract.

Isolation: everything runs on a throw-away copy of the archive (`run.prepare_archive(dry_run=True)`); nothing is written to projection-data, data-archive or
minutes-shadow-archive; no forecast archive is added or replaced; no production default is switched; no staking or trading route exists. The JRM code comes from a
PINNED SHA of draft PR #45 merged only inside the runner's throw-away checkout (see .github/workflows/jrm-exact-dryrun.yml). With no outcomes yet (future games) this is a
decision / probability / minutes comparison, not an accuracy claim; the per-player table is written so it can be scored once the games are final.

    python -m nba.paper.jrm_exact --archive <projection-data> --context <data-archive> --market <data-archive> --pit <data-injury-pit> --shadow <nba-shadow-pure> --out DIR
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import sys
from argparse import Namespace
from collections import Counter
from datetime import datetime
from typing import Any

import numpy as np

from . import config as CFG
from . import engine as EN
from . import exec_shadow as X
from . import jrm_matched as J
from . import markets as MK
from . import probability as PR
from . import run as RUN
from . import schema as S

MODE = "exact_jrm_dry_run"
LABEL = "exact_jrm_dry_run"


class JrmUnavailable(RuntimeError):
    pass


# ================================================================================================ projection pair
def project_pair(a: Namespace, now: datetime, work: str, *, runner=None) -> dict[str, dict]:
    """Run the production project stage twice (frozen, jrm) on the same capture and return both raw `project_slate` results.

    `runner(a, now, work)` defaults to `nba.live.run.stage_project`; tests inject a stub. The `project_slate` return value is captured by wrapping the function the stage
    imports at call time."""
    import nba.project as P
    out: dict[str, dict] = {}
    orig = P.project_slate

    def wrapped(*args, **kw):
        res = orig(*args, **kw)
        out[kw.get("minutes_engine", "frozen")] = res
        return res
    if runner is None:
        from nba.live import run as LR
        runner = LR.stage_project
    old = os.environ.get("PF_NBA_MINUTES_ENGINE")
    P.project_slate = wrapped
    try:
        for eng in ("frozen", "jrm"):
            os.environ["PF_NBA_MINUTES_ENGINE"] = eng
            try:
                runner(a, now, work)
            except TypeError as e:                       # project_slate without minutes_engine: PR #45 is not in this checkout
                if eng == "jrm":
                    raise JrmUnavailable(f"the jrm engine is not available in this checkout: {e}") from e
                raise
    finally:
        P.project_slate = orig
        if old is None:
            os.environ.pop("PF_NBA_MINUTES_ENGINE", None)
        else:
            os.environ["PF_NBA_MINUTES_ENGINE"] = old
    if "jrm" not in out or "frozen" not in out:
        raise JrmUnavailable(f"project_slate did not run for both engines (got {sorted(out)}); probably no game in the window")
    return out


def records_from_res(res: dict) -> tuple[list[dict], list[dict]]:
    """(player records, game-forecast records) exactly as the live pipeline archives them (nba.live.forecasts.challenger_records /
    paper.run.challenger_game_records), with forecast ids and self-archive times filled so `probability.Forecasts` accepts them. Nothing is archived."""
    from nba.live import forecasts as FC
    from pf_core import prospective as pr
    recs = FC.challenger_records(res)
    for r in recs:
        r["archived_utc"] = r["generated_utc"]
        r["forecast_id"] = pr.forecast_id(r)
    gfs = RUN.challenger_game_records(res)
    for g in gfs:
        g["archived_utc"] = g["generated_utc"]
    return recs, gfs


# ================================================================================================ pricing both engines on one board
def price_engine(recs: list[dict], gfs: list[dict], rows: list[dict], board_dt: datetime, now: datetime, base: dict, study: dict, tag: str) -> list[dict]:
    """Candidates of one engine on a COPY of the shared snapshot rows, then the strict selection as if `now` were its own checkpoint (fresh ledger, no clocks)."""
    rws = copy.deepcopy(rows)
    players = MK.PlayerIndex(recs)
    RUN._fill_player_ids(rws, players)
    fc, gfc = PR.Forecasts(recs, now), PR.GameForecasts(gfs, now)
    cands = EN.candidates_for(rws, fc, gfc, players, as_of=now, decided=now, mode=MODE, cfg=base)
    s2 = copy.deepcopy(study)
    s2["checkpoint"]["horizon"] = "LIVE"
    s2["checkpoint"]["allowed_decision_modes"] = [MODE]
    out = []
    for c in cands:
        if c["side"] not in S.SIDES:
            continue
        p = X.prepare({**c, "settled": False}, s2, base)
        p["checkpoint"] = p["as_of"]                                       # a dry run evaluates 'now'; the 60-minute checkpoint geometry does not apply
        p["quote_age_at_checkpoint_s"] = (p["as_of"] - p["board"]).total_seconds()
        out.append(p)
    return X.select(out, s2, base, strategy_id=f"PF_EDGE_STRICT_T60_EXEC_{tag}", prepared=True, forecast_archive=None, clocks=None)


def minutes_table(res: dict) -> dict[tuple[str, str], dict]:
    t: dict[tuple[str, str], dict] = {}
    for p in res["players"]:
        k = (p["game_id"], p["player_id"])
        e = t.setdefault(k, {"game_id": p["game_id"], "player_id": p["player_id"], "name": p["name"], "team": p["team"], "p_play": float(p["participation"]["p_play"]),
                             "participation_status": p["participation"]["status"], "gate": {}})
        if p["family"] == "minutes":
            e["minutes_mean"] = float(p["mean"])
        e["gate"][p["family"]] = p["gate"]["status"]
    return t


def engine_diagnostics(res: dict) -> dict[str, Any]:
    gates = Counter(p["gate"]["status"] for p in res["players"])
    part = Counter(p["participation"]["status"] for p in res["players"] if p["family"] == "points")
    rec = [{k: r.get(k) for k in ("game_id", "team", "minutes_sum_raw", "points_sum_raw", "points_sum_final", "team_points", "action", "status")} for r in res.get("reconciliation") or []]
    t = minutes_table(res)
    by_team: dict[tuple, float] = {}
    for e in t.values():
        if "minutes_mean" in e:
            by_team[(e["game_id"], e["team"])] = by_team.get((e["game_id"], e["team"]), 0.0) + e["p_play"] * e["minutes_mean"]
    return {"model": res.get("model"), "mode": res.get("mode"), "n_players": len(t), "n_rows": len(res["players"]), "gate_counts": dict(gates), "participation_counts": dict(part),
            "reconciliation": rec, "teams_normalised": sum(1 for r in rec if r.get("action") not in (None, "none")),
            "team_sum_p_times_minutes": {f"{g}|{tm}": round(v, 2) for (g, tm), v in sorted(by_team.items())},
            "runtime_s": res.get("runtime_s")}


def compare(res: dict[str, dict], market: str, now: datetime, base: dict, study: dict) -> dict[str, Any]:
    """The full comparison. `res` = {"frozen": project_slate result, "jrm": project_slate result}."""
    rf, rj = records_from_res(res["frozen"]), records_from_res(res["jrm"])
    games = [MK.Game.from_dict({"game_id": g["game_id"], "start_utc": g["start_utc"], "home": g["home"], "away": g["away"], "game_date_et": g.get("game_date_et")})
             for g in res["frozen"]["games"] if MK.parse_ts(g["start_utc"]) > now]
    out: dict[str, Any] = {"schema": "issue53.jrm_exact.v1", "label": LABEL, "authority": "research_only", "now": MK.iso(now), "n_games": len(games),
                           "engines": {k: engine_diagnostics(v) for k, v in res.items()}}
    mt_f, mt_j = minutes_table(res["frozen"]), minutes_table(res["jrm"])
    players = []
    for k, ef in sorted(mt_f.items()):
        ej = mt_j.get(k)
        if ej is None or "minutes_mean" not in ef or "minutes_mean" not in ej:
            continue
        players.append({**{x: ef[x] for x in ("game_id", "player_id", "name", "team")}, "p_play_frozen": ef["p_play"], "p_play_jrm": ej["p_play"],
                        "minutes_frozen": ef["minutes_mean"], "minutes_jrm": ej["minutes_mean"], "ratio": ej["minutes_mean"] / ef["minutes_mean"] if ef["minutes_mean"] else None,
                        "gate_frozen": ef["gate"].get("points"), "gate_jrm": ej["gate"].get("points")})
    out["players"] = players
    # the engine switch must have changed something: a JRM table identical to the frozen one means PF_NBA_MINUTES_ENGINE did not take effect (not a finding about JRM)
    identical = bool(players) and all(abs(p["minutes_jrm"] - p["minutes_frozen"]) < 1e-9 and p["p_play_jrm"] == p["p_play_frozen"] for p in players)
    out["engine_check"] = {"status": "ENGINE_NOT_SWITCHED" if identical else "OK", "minutes_tables_identical": identical, "n_players": len(players)}
    if players:
        d = np.array([p["minutes_jrm"] - p["minutes_frozen"] for p in players])
        out["minutes_difference"] = {"n": len(players), "mean": float(d.mean()), "mean_abs": float(np.abs(d).mean()), "share_jrm_higher": float((d > 0).mean()),
                                     "stars_ge_28_frozen": {"n": int(sum(1 for p in players if p["minutes_frozen"] >= 28)),
                                                            "mean_ratio": float(np.mean([p["ratio"] for p in players if p["minutes_frozen"] >= 28])) if any(p["minutes_frozen"] >= 28 for p in players) else None}}
    reader = MK.ChainReader(market, "markets")
    got = reader.board_at(now)
    if got is None or got[1] is None:
        out["market"] = {"status": "NO_BOARD" if got is None else "CHAIN_BROKEN", "reason": "no reconstructable board at or before now"}
        out["selections"] = {"status": "NO_DATA"}
        return out
    dt, board = got
    out["market"] = {"status": "OK", "board_observed_utc": MK.iso(dt), "board_age_s": (now - dt).total_seconds()}
    gi = MK.GameIndex(games)
    ob = MK.ChainReader(market, "orderbooks")
    rows = []
    for g in games:
        r, _ = MK.snapshot_rows(board, gi, g, "LIVE", now, dt, book=RUN._book_at(ob, {}, dt))
        rows += r
    sel_f = price_engine(rf[0], rf[1], rows, dt, now, base, study, "FROZEN")
    sel_j = price_engine(rj[0], rj[1], rows, dt, now, base, study, "JRM_EXACT")
    mj = {(p["game_id"], p["player_id"]): p for p in players}
    for c in sel_j:                                                      # attach the exact minutes to the JRM rows so the pair summaries can use them
        p = mj.get((c["game_id"], c.get("entity_id")))
        c["jrm_status"] = "COVERED" if p else "GAME_LEVEL_UNCHANGED"
        c["jrm"] = None if not p else {"ratio_minutes": p["ratio"], "minutes_frozen": p["minutes_frozen"], "minutes_jrm": p["minutes_jrm"]}
    pairs = J.pair_decisions(sel_f, sel_j)["frame"]
    out["selections"] = {"status": "OK", "downstream": LABEL, "frozen": X.portfolio_metrics(sel_f, study, label="frozen_exact_dry_run"),
                         "jrm_exact": X.portfolio_metrics(sel_j, study, label="jrm_exact_dry_run"), "paired": J.summarize_pairs(pairs), "star_unders": J.star_under_diagnostic(pairs),
                         "pairs": json.loads(pairs[pairs["class"] != "neither"].to_json(orient="records", default_handler=str)),
                         "note": "no outcomes exist for future games: this is a decision / probability / minutes comparison, not an accuracy or P&L claim"}
    return out


def markdown(rep: dict) -> str:
    L = [f"# Exact JRM dry run ({LABEL}), {rep['now']}", "", "**Research only. Isolated throw-away run. No archive written, no production switch, no promotion.**", ""]
    for k, e in rep["engines"].items():
        L.append(f"- {k}: model {json.dumps(e['model'])}; players {e['n_players']}; gates {json.dumps(e['gate_counts'])}; teams normalised by the reconciliation gate: {e['teams_normalised']}")
    md = rep.get("minutes_difference")
    if md:
        L.append(f"- minutes (conditional mean) JRM - frozen: mean {md['mean']:+.2f}, mean |diff| {md['mean_abs']:.2f}, JRM higher for {100 * md['share_jrm_higher']:.0f}% of {md['n']} players; "
                 f"frozen stars >= 28 min: n={md['stars_ge_28_frozen']['n']}, mean JRM/frozen {md['stars_ge_28_frozen']['mean_ratio']}")
    ec = rep.get("engine_check") or {}
    if ec.get("status") == "ENGINE_NOT_SWITCHED":
        L.append("- **ENGINE_NOT_SWITCHED: the JRM minutes are identical to the frozen minutes; the comparison below is an identity and says nothing about JRM**")
    s = rep.get("selections", {})
    if s.get("status") == "OK":
        L.append(f"- same board ({rep['market']['board_observed_utc']}), same strict rules: decision matrix {json.dumps(s['paired']['decision_matrix_candidate_sides'])}; "
                 f"theses {json.dumps(s['paired']['thesis_level'])}")
        L.append(f"- {s['note']}")
    else:
        L.append(f"- selections: {s.get('status')} ({rep.get('market', {}).get('reason')})")
    return "\n".join(L) + "\n"


# ================================================================================================ CLI
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--archive", required=True, help="projection-data checkout (READ-ONLY: a throw-away copy is used)")
    ap.add_argument("--context", default=None)
    ap.add_argument("--market", default=None)
    ap.add_argument("--pit", default=None)
    ap.add_argument("--shadow", default=None)
    ap.add_argument("--workdir", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--now", default=None)
    ap.add_argument("--window-hours", type=float, default=30.0)         # the workflow default is the same
    ap.add_argument("--season-types", default="regular")
    a = ap.parse_args(argv)
    from nba.live import run as LR
    from nba.live.sources import Sources
    os.makedirs(a.out, exist_ok=True)
    work = a.workdir or os.path.join(a.out, "work")
    os.makedirs(work, exist_ok=True)
    arch, cleanup = LR.prepare_archive(a.archive, True)               # a COPY: the mounted branch is never written
    ns = Namespace(archive=arch, shadow=a.shadow, pit=a.pit, context=a.context, market=a.market or a.context, window_hours=a.window_hours, season_types=a.season_types, now=a.now)
    now = MK.parse_ts(a.now) if a.now else LR.wall_clock()
    try:
        LR.stage_capture(ns, Sources(), now, work)
        res = project_pair(ns, now, work)
        base, study = CFG.load(), X.load_study()
        rep = compare(res, ns.market, now, base, study)
        rep["code"] = {"workspace_sha": os.environ.get("GITHUB_SHA"), "jrm_pr45_sha": os.environ.get("JRM_PR45_SHA"), "run_id": os.environ.get("GITHUB_RUN_ID")}
        json.dump(rep, open(os.path.join(a.out, "jrm_exact_dryrun.json"), "w"), indent=1, sort_keys=True, default=str)
        open(os.path.join(a.out, "jrm_exact_dryrun.md"), "w").write(markdown(rep))
        print(markdown(rep))
        summ = os.environ.get("GITHUB_STEP_SUMMARY")
        if summ:
            open(summ, "a").write(markdown(rep))
        if (rep.get("engine_check") or {}).get("status") == "ENGINE_NOT_SWITCHED":
            print("::error::ENGINE_NOT_SWITCHED: PF_NBA_MINUTES_ENGINE=jrm produced the frozen minutes")
            return 6
    except JrmUnavailable as e:
        print(f"::error::{e}")
        json.dump({"schema": "issue53.jrm_exact.v1", "status": "JRM_ENGINE_UNAVAILABLE", "reason": str(e)}, open(os.path.join(a.out, "jrm_exact_dryrun.json"), "w"))
        return 4
    finally:
        shutil.rmtree(cleanup, ignore_errors=True) if cleanup else None
    return 0


if __name__ == "__main__":
    sys.exit(main())
