"""Side-by-side comparison of the Issue #53 sealing lanes (RESEARCH ONLY; read-only; descriptive). Results of different lanes are NEVER pooled.

Lanes: `control` = strict T-60 (the latest observed tick must also be committed by the checkpoint), `t60a` = the T-60 availability study (the PRIMARY new experiment: the same T-60
checkpoint, the latest tick OBSERVED and COMMITTED by it - only the board-selection rule differs), `t45` = the T-45 availability study (EXPLORATORY, inactive; shown only with
`--include-t45`, in its own section, never in the primary comparison). Each lane has its own protocol, strategy id, ledger branch, evidence counts and start date. This module reports, per lane and next to each other: coverage and exclusions, predicted EV, closing-line
value, settled performance, executability (board age, price drift), the overlap of selections, and - independently of any lane, trade or market - the projection accuracy on every
eligible game (TRADED, NO_TRADE and no-board games all stay in the denominator).

Two sources of lane rows, always labelled:
  * PROSPECTIVE: the verified, counted seals of a lane's ledger (`exec_seal.evaluate`) - the only evidence;
  * RETROSPECTIVE reconstruction: the lane's own sealer run over past games on the final archives with the lane's commit-time filters (`reconstruct`). It is uncounted and descriptive; it
    answers 'what coverage would the rule have had', never 'does it work'. Because control and t60a share the checkpoint and every number, the board rule is the ONLY difference, so
    their paired differences are attributable to it; the exploratory T-45 lane also runs one matched comparator (T-45 with the strict rule).

    python -m nba.paper.compare_lanes --archive <projection-data checkout> --market <data-archive checkout> --repo <git repo with origin/data-archive> --out results/issue53_t60a [--include-t45]
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import tempfile
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np

from . import config as CFG
from . import exec_seal as SL
from . import exec_shadow as X
from . import markets as MK
from . import seal_windows as SW

UTC = timezone.utc
LATENCY_REASONS = ("BOARD_COMMITTED_AFTER_CHECKPOINT", "NO_BOARD_COMMITTED_BY_DECISION", "BOARD_ARCHIVE_UNVERIFIED")
DATA_REASONS = ("NO_BOARD_WITHIN_GAP", "CHAIN_BROKEN", "NO_FORECASTS_COMMITTED_BY_CHECKPOINT", "NO_EVALUABLE_CONTRACTS")


def _variant(study: dict, minutes: int | None = None, rule: str | None = None) -> dict:
    s = copy.deepcopy(study)
    if minutes is not None:
        s["checkpoint"]["minutes_before_tip"] = minutes
        s["checkpoint"]["horizon"] = f"T-{minutes}"
    if rule is not None:
        if rule == "latest_committed_by_decision":
            s["checkpoint"]["board_rule_id"] = rule
        else:
            s["checkpoint"].pop("board_rule_id", None)
    return s


def lane_study(lane: str) -> dict:
    return X.load_study() if lane == "control" else X.load_lane(SW.lane_study_path(lane))


def classify(status: str, reason: str | None, n_sides: int) -> str:
    if status == "TRADED":
        return "TRADED"
    r = (reason or "").split(";")[0].split("=")[0]
    if r in LATENCY_REASONS:
        return "EXCLUDED_ARCHIVE_LATENCY"
    if r in DATA_REASONS or n_sides == 0:
        return "EXCLUDED_NO_DATA"
    return "EVALUATED_NO_TRADE"


# ================================================================================================ retrospective reconstruction
def reconstruct(study: dict, games: list[dict], archive: str, market: str, clocks: dict, base: dict, work: str, label: str) -> dict[str, Any]:
    """Run the lane's sealer, game by game in checkpoint order, at the first minute of each window, into a SCRATCH ledger (never published, never counted)."""
    d = os.path.join(work, label)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    subprocess.run(["git", "init", "-q", d], check=True)
    open(os.path.join(d, "ENABLED_UTC"), "w").write("2000-01-01T00:00:00Z\n")
    code = {"sha": None, "dirty": False, "ref": "retrospective", "default_branch": None, "event": "retrospective_reconstruction", "workflow": None, "run_id": None,
            "protocol_effective_commit_utc": None}
    errors = []
    for g in sorted(games, key=lambda g: (SW.window(g, study)["checkpoint"], g["game_id"])):
        w = SW.window(g, study)
        now = w["opens"] + timedelta(seconds=60)
        if now > w["closes"]:
            continue
        rep = SL.seal_games([g], archive, market, d, now, study, base, clocks, code)
        errors += rep["errors"]
    bodies, rows = [], []
    for body, p in SL.iter_seals(d):
        bodies.append(body)
        for r in SL.load_candidates(d, body, os.path.relpath(p, d)):
            rows.append(SL.hydrate(r, body, study, counted=False))
    return {"dir": d, "bodies": bodies, "rows": rows, "errors": errors, "label": label}


# ================================================================================================ per-lane summary
def coverage(bodies: list[dict], games: list[dict]) -> dict[str, Any]:
    by = {b["game"]["game_id"]: b for b in bodies}
    per, cls = [], Counter()
    for g in games:
        b = by.get(g["game_id"])
        if b is None:
            per.append({"game_id": g["game_id"], "tip_utc": g["start_utc"], "class": "NO_SEAL", "reason": None})
            cls["NO_SEAL"] += 1
            continue
        c = classify(b["status"], b.get("game_reason"), b["candidates"]["n_sides"])
        cls[c] += 1
        per.append({"game_id": g["game_id"], "tip_utc": g["start_utc"], "class": c, "status": b["status"], "reason": (b.get("game_reason") or "")[:120], "n_trades": b["candidates"]["n_trades"],
                    "board_age_s": b["board"].get("gap_s") if b.get("board") else None})
    n = len(games)
    tips: dict[str, list[str]] = {}
    for pg in per:
        tips.setdefault(pg["tip_utc"], []).append(pg["class"])
    usable = sum(1 for v in tips.values() if any(c in ("TRADED", "EVALUATED_NO_TRADE") for c in v))
    return {"games": n, "decision_instants": len(tips), "decision_instants_with_a_usable_board": usable,
            "instants_note": "games that tip at the same time share one decision instant and therefore one board: their exclusion is perfectly correlated, so the number of independent coverage observations is the number of distinct instants",
            "classes": dict(cls), "games_with_a_decision_evaluated": cls["TRADED"] + cls["EVALUATED_NO_TRADE"], "games_traded": cls["TRADED"],
            "excluded_by_archive_latency": cls["EXCLUDED_ARCHIVE_LATENCY"], "share_evaluated": round((cls["TRADED"] + cls["EVALUATED_NO_TRADE"]) / n, 3) if n else None, "per_game": per}


def trade_rows(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r.get("decision") == "TRADE"]


def price_drift(trades: list[dict], market: str) -> dict[str, Any]:
    """Executability (descriptive): ask on the first board observed after the decision instant minus the sealed ask, in cents; and the sealed board's age at the decision."""
    reader = MK.ChainReader(market, "markets")
    drift, age = [], []
    for c in trades:
        cp = c["checkpoint"]
        age.append(float(c["quote_age_at_checkpoint_s"])) if c.get("quote_age_at_checkpoint_s") is not None else None
        ticks = reader.ticks(cp, cp + timedelta(minutes=30))
        if not ticks:
            continue
        board = None
        for dt, b in reader.walk(ticks[0], ticks[0]):
            if dt == ticks[0]:
                board = b
        if not board or c["ticker"] not in board:
            continue
        q = MK.quote(board[c["ticker"]])
        ask = q["yes_ask"] if c["side"] == "YES" else q["no_ask"]
        if ask is not None and c.get("price") is not None:
            drift.append(100.0 * (float(ask) - float(c["price"])))
    f = lambda a, p: None if not a else round(float(np.percentile(a, p)), 2)      # noqa: E731
    return {"n_with_a_later_board": len(drift), "ask_drift_cents": {"mean": None if not drift else round(float(np.mean(drift)), 2), "p10": f(drift, 10), "p90": f(drift, 90)},
            "share_adverse": None if not drift else round(float(np.mean([d > 0 for d in drift])), 3), "board_age_at_decision_s": {"median": f(age, 50), "p90": f(age, 90), "n": len(age)},
            "note": "drift is observed AFTER the decision and never used in a selection; adverse = the ask moved up before the next board"}


def summarize(label: str, source: str, study: dict, bodies: list[dict], rows: list[dict], games: list[dict], market: str | None, settle: dict | None) -> dict[str, Any]:
    tr = trade_rows(rows)
    m = X.portfolio_metrics(rows, study, label=label, clocks_verified=(source == "PROSPECTIVE_SEALED")) if rows else {"status": "NO_DATA", "reason": "no candidate rows"}
    ev = [float(c["ev_net_exec"]) for c in tr if c.get("ev_net_exec") is not None]
    out = {"label": label, "source": source, "strategy_id": X.strategy_id(study), "study_id": study["study_id"], "protocol_version": study["version"],
           "prospective_start_utc": study["prospective_start_utc"], "coverage": coverage(bodies, games),
           "predicted_ev": {"n_trades": len(tr), "mean_ev_net_exec": None if not ev else round(float(np.mean(ev)), 4), "sum_ev_net_exec": None if not ev else round(float(np.sum(ev)), 4),
                            "mean_p_model": None if not tr else round(float(np.mean([c["p_model"] for c in tr if c.get("p_model") is not None])), 4),
                            "note": "predicted by the model at the decision instant, before any outcome"},
           "settlement_join": settle or {}, "metrics": m}
    if m.get("status") == "OK":
        out["settled"] = {"n_settled": m["independent_units"]["n_settled_decisions"], "n_decisions": m["independent_units"]["n_decisions"], "n_games": m["independent_units"]["n_games"],
                          "net_pnl": m["overall"].get("total_net_pnl"), "roi_on_cash_outlay": m["overall"].get("roi_on_cash_outlay"), "hit_rate": m["overall"].get("hit_rate"),
                          "clv_cents": m.get("clv_cents"), "evidence_status": m["evidence_status"]}
    if market and tr:
        out["executability"] = price_drift(tr, market)
    return out


def overlap(a: list[dict], b: list[dict], other: str = "t60a") -> dict[str, Any]:
    ka = {(c["game_id"], c["ticker"], c["side"]) for c in a}
    kb = {(c["game_id"], c["ticker"], c["side"]) for c in b}
    ga, gb = {k[0] for k in ka}, {k[0] for k in kb}
    return {"contracts_both": len(ka & kb), "control_only": len(ka - kb), f"{other}_only": len(kb - ka), "games_traded_both": len(ga & gb), "games_control_only": len(ga - gb),
            f"games_{other}_only": len(gb - ga), "reading": "descriptive; each lane keeps its own ledger and exposure caps, so a shared contract is two separate shadow positions"}


def _per_game(rows: list[dict]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for c in trade_rows(rows):
        g = out.setdefault(c["game_id"], {"trades": 0, "settled": 0, "pnl": 0.0, "clv": [], "ev": 0.0})
        g["trades"] += 1
        g["ev"] += float(c.get("ev_net_exec") or 0.0)
        if c.get("settled") and c.get("net_pnl") is not None:
            g["settled"] += 1
            g["pnl"] += float(c["net_pnl"])
        if c.get("settled") and c.get("clv_cents") is not None:
            g["clv"].append(float(c["clv_cents"]))
    return out


def paired(control_cov: dict, other_cov: dict, control_rows: list[dict], other_rows: list[dict], other: str = "t60a", seed: int = 53, n_boot: int = 2000) -> dict[str, Any]:
    """Paired, per-game differences between the control and the primary lane on the SAME games (descriptive; never pooled with either lane's own evidence).

    The lanes share the checkpoint, the thresholds and the costs, so the lane rule that picks the board is the only difference. Whenever the control's latest observed tick is committed by D
    the availability rule picks the identical tick: the two must then agree contract for contract (`identical_selections_on_common_games`), and every difference comes from games the control
    loses to archive latency (`recovered`). A game that neither lane could evaluate is in `games` but in no difference."""
    cls_c = {pg["game_id"]: pg["class"] for pg in control_cov["per_game"]}
    cls_o = {pg["game_id"]: pg["class"] for pg in other_cov["per_game"]}
    ev = ("TRADED", "EVALUATED_NO_TRADE")
    both = sorted(g for g in cls_c if cls_c[g] in ev and cls_o.get(g) in ev)
    only_o = sorted(g for g in cls_o if cls_o[g] in ev and cls_c.get(g) not in ev)
    only_c = sorted(g for g in cls_c if cls_c[g] in ev and cls_o.get(g) not in ev)
    pc, po = _per_game(control_rows), _per_game(other_rows)
    keys = lambda rows: {(c["game_id"], c["ticker"], c["side"]) for c in trade_rows(rows)}      # noqa: E731
    kc, ko = keys(control_rows), keys(other_rows)
    same = all({k for k in kc if k[0] == g} == {k for k in ko if k[0] == g} for g in both)
    union = sorted(set(both) | set(only_o) | set(only_c))
    diffs = [(po.get(g, {}).get("pnl", 0.0) - pc.get(g, {}).get("pnl", 0.0)) for g in union]
    unsettled = sum(po.get(g, {}).get("trades", 0) - po.get(g, {}).get("settled", 0) for g in union) + sum(pc.get(g, {}).get("trades", 0) - pc.get(g, {}).get("settled", 0) for g in union)
    ci: dict[str, Any] = {"status": "INSUFFICIENT_GAMES", "min_games": 8}
    if len(diffs) >= 8:
        rng = np.random.default_rng(seed)
        d = np.asarray(diffs)
        bs = np.sort([float(rng.choice(d, size=len(d), replace=True).mean()) for _ in range(n_boot)])
        ci = {"status": "OK", "method": "game-clustered bootstrap of the per-game mean difference", "n_boot": n_boot, "seed": seed, "lo95": round(bs[int(0.025 * n_boot)], 4), "hi95": round(bs[int(0.975 * n_boot) - 1], 4)}

    def block(gs: list[str], per: dict) -> dict[str, Any]:
        clv = [x for g in gs for x in per.get(g, {}).get("clv", [])]
        return {"games": len(gs), "trades": sum(per.get(g, {}).get("trades", 0) for g in gs), "net_pnl": round(sum(per.get(g, {}).get("pnl", 0.0) for g in gs), 4),
                "mean_clv_cents": None if not clv else round(float(np.mean(clv)), 3), "n_clv": len(clv)}

    return {"pair": f"control vs {other}", "games_both_evaluated": len(both), f"games_only_{other}_evaluated": len(only_o), "games_only_control_evaluated": len(only_c),
            "identical_selections_on_common_games": bool(same),
            "check": "the availability rule is a superset of the strict rule: games_only_control_evaluated must be 0 and the common games must agree contract for contract",
            "common_games": {"control": block(both, pc), other: block(both, po)}, "recovered_games": {other: block(only_o, po)},
            "per_game_net_pnl_difference": {"n_games": len(diffs), "mean": None if not diffs else round(float(np.mean(diffs)), 4), "bootstrap": ci, "unsettled_trades_excluded": unsettled,
                                           "reading": f"{other} minus control, summed over a game's settled trades (0 for a game a lane did not evaluate); descriptive, not evidence of an edge until the sealed ledgers carry it"}}


# ================================================================================================ projection accuracy (lane-independent)
def accuracy_all_games(archive: str, lane_coverage: dict[str, dict]) -> dict[str, Any]:
    """Forecast accuracy on EVERY eligible game (settled, non-void challenger forecasts), regardless of any trade, market, seal or lane. Reuses the prospective scorecard (pf_core)."""
    from pf_core import prospective as pr
    s = pr.load_settlements(archive, "NBA")
    if s.empty:
        return {"status": "NO_DATA", "reason": "no settled forecasts yet"}
    s = s[~s["void"].astype(bool)]
    ch = s[s["model_role"] == "challenger"]
    games = sorted(ch["game_id"].unique())
    score = pr.score(s)
    fam = {r["family"]: next((m for m in r["models"] if m["model_role"] == "challenger"), None) for r in score}
    status = {ln: {pg["game_id"]: pg["class"] for pg in cov["per_game"]} for ln, cov in lane_coverage.items()}
    by_lane: dict[str, dict[str, int]] = {}
    for ln, st in status.items():
        c = Counter(st.get(g, "NO_LANE_RECORD") for g in games)
        by_lane[ln] = dict(c)
    return {"status": "OK", "n_eligible_games": len(games), "n_challenger_forecasts_scored": int(len(ch)), "games": games,
            "scoring_version": pr.SCORING_VERSION,
            "by_family_challenger": {f: ({k: (round(v, 4) if isinstance(v, float) else v) for k, v in m.items() if k in ("n", "n_games", "primary_metric", "crps", "brier", "mae", "bias")} if m else None) for f, m in fam.items()},
            "eligible_games_by_lane_status": by_lane,
            "rule": "the denominator is every game with settled forecasts. TRADED, EVALUATED_NO_TRADE, EXCLUDED_* and NO_SEAL games are all scored; a trade decision, a missing board or a lane exclusion never removes a game from the accuracy evaluation",
            "independent_of_lanes": True}


# ================================================================================================ report
def _f(x: Any, nd: int = 3) -> Any:
    return round(x, nd) if isinstance(x, float) else x


def _lane_tables(cols: dict[str, Any]) -> list[str]:
    L = ["| lane (source) | games | evaluated | traded | excluded by archive latency | excluded no data | share evaluated | decision instants usable |", "|---|---|---|---|---|---|---|---|"]
    for k, v in cols.items():
        c = v["coverage"]
        L.append(f"| {k} ({v['source']}) | {c['games']} | {c['games_with_a_decision_evaluated']} | {c['games_traded']} | {c['excluded_by_archive_latency']} | {c['classes'].get('EXCLUDED_NO_DATA', 0)} | {c['share_evaluated']} | "
                 f"{c.get('decision_instants_with_a_usable_board')} / {c.get('decision_instants')} |")
    L += ["", "| lane | trades | mean predicted EV | settled | net P&L | ROI on outlay | hit rate | CLV mean (c, n valid) | quote age at decision median / p90 (s) | ask drift mean (c) | adverse drift share |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, v in cols.items():
        pe, st, ex = v["predicted_ev"], v.get("settled") or {}, v.get("executability") or {}
        clv = (st.get("clv_cents") or {})
        age = (ex.get("board_age_at_decision_s") or {})
        L.append(f"| {k} | {pe['n_trades']} | {_f(pe['mean_ev_net_exec'])} | {st.get('n_settled')} | {_f(st.get('net_pnl'), 2)} | {_f(st.get('roi_on_cash_outlay'))} | {_f(st.get('hit_rate'))} | "
                 f"{_f(clv.get('mean'), 2)} ({clv.get('n_valid')}) | {age.get('median')} / {age.get('p90')} | {(ex.get('ask_drift_cents') or {}).get('mean')} | {ex.get('share_adverse')} |")
    return L


def markdown(rep: dict) -> str:
    L = ["# Strict T-60 control vs T-60 availability study (research only; descriptive; lanes are never pooled)", "", rep["scope"], "",
         "## Primary comparison: coverage, predicted EV, CLV, settled performance, quote freshness and price drift", ""]
    L += _lane_tables(rep["lanes"])
    pr = rep.get("paired")
    if pr:
        d = pr["per_game_net_pnl_difference"]
        L += ["", f"## Paired differences ({pr['pair']}, same games)", "",
              f"* games evaluated by both lanes: {pr['games_both_evaluated']}; only by the availability lane (recovered): {pr.get('games_only_t60a_evaluated')}; only by the control: {pr['games_only_control_evaluated']}",
              f"* identical selections on the common games: {pr['identical_selections_on_common_games']} ({pr['check']})",
              f"* common games: {json.dumps(pr['common_games'])}", f"* recovered games: {json.dumps(pr['recovered_games'])}",
              f"* per-game net P&L difference: n={d['n_games']}, mean={d['mean']}, bootstrap {json.dumps(d['bootstrap'])}; unsettled trades excluded: {d['unsettled_trades_excluded']}", f"* {d['reading']}"]
    L += ["", f"Selection overlap (control vs t60a, retrospective): {json.dumps(rep['overlap'])}", ""]
    a = rep["projection_accuracy_all_games"]
    L += ["## Projection accuracy on all eligible games (independent of trades, markets and lanes)", ""]
    if a.get("status") == "OK":
        L.append(f"* eligible games with settled forecasts: {a['n_eligible_games']}; challenger forecasts scored: {a['n_challenger_forecasts_scored']}")
        L.append(f"* eligible games by lane status: {json.dumps(a['eligible_games_by_lane_status'])}")
        L.append(f"* {a['rule']}")
    else:
        L.append(f"* {a.get('reason')}")
    ex = rep.get("exploratory")
    if ex:
        L += ["", "## EXPLORATORY ONLY: T-45 availability (inactive; not part of the primary comparison, never pooled, not an evidence line)", ""] + _lane_tables(ex["lanes"])
        L += ["", f"* {ex['note']}"]
    L += ["", "## Caveats", ""] + [f"* {c}" for c in rep["caveats"]]
    return "\n".join(L) + "\n"


PRIMARY = "t60a"


def run(archive: str, market: str, repo: str, context: str, out: str, since: str = "2026-10-20", ref: str = "origin/data-archive", forecast_ref: str = "origin/projection-data",
        now: datetime | None = None, prospective: dict[str, str] | None = None, include_t45: bool = False) -> dict[str, Any]:
    now = now or datetime.now(UTC).replace(microsecond=0)
    base = CFG.load()
    games_all = SW.schedule_games(context, None, all_history=True)
    games = [g for g in games_all if MK.parse_ts(g["start_utc"]) >= MK.parse_ts(since + "T00:00:00Z") and MK.parse_ts(g["start_utc"]) <= now - timedelta(hours=1)]
    clocks = {"board_commit": X.board_commit_index(repo, ref), "forecast_commit": X.forecast_commit_index(archive, repo, forecast_ref)}
    work = tempfile.mkdtemp(prefix="lanes_")
    ctrl, prim = lane_study("control"), lane_study(PRIMARY)
    primary = {"control_T60_strict": ("control", ctrl, "RETROSPECTIVE_RECONSTRUCTION"), "t60a_T60_available": (PRIMARY, prim, "RETROSPECTIVE_RECONSTRUCTION")}
    explore: dict[str, Any] = {}
    if include_t45:
        t45 = lane_study("t45")
        explore = {"t45_T45_available": ("t45", t45, "RETROSPECTIVE_RECONSTRUCTION"), "comparator_T45_strict": ("cmp", _variant(ctrl, 45, "observed_and_committed_by_checkpoint"), "RETROSPECTIVE_COMPARATOR")}
    lanes: dict[str, Any] = {}
    exp_lanes: dict[str, Any] = {}
    rows_by: dict[str, list[dict]] = {}
    for name, (_, st, src) in {**primary, **explore}.items():
        rc = reconstruct(st, games, archive, market, clocks, base, work, name)
        trades = trade_rows(rc["rows"])
        settle = SL.settle_sealed(trades, archive, market, now, base, strategy_id=X.strategy_id(st), horizon=st["checkpoint"]["horizon"]) if trades else {}
        (lanes if name in primary else exp_lanes)[name] = summarize(name, src, st, rc["bodies"], rc["rows"], games, market, settle)
        (lanes if name in primary else exp_lanes)[name]["errors"] = rc["errors"]
        rows_by[name] = rc["rows"]
    if prospective:
        for ln, seal_dir in prospective.items():
            if ln == "t45" and not include_t45:
                continue
            st = lane_study(ln)
            ev = SL.evaluate(seal_dir, archive, market, now, st, base, schedule=games, board_commits=clocks["board_commit"] if X.board_rule_id(st) == "latest_committed_by_decision" else None)
            (exp_lanes if ln == "t45" else lanes)[f"{ln}_PROSPECTIVE"] = {"source": "PROSPECTIVE_SEALED", "evaluation": {k: ev[k] for k in ("game_counts", "progress", "metrics", "settlement_join")}, "coverage": {
                "games": len(games), "games_with_a_decision_evaluated": None, "games_traded": ev["progress"]["counted_games_traded"], "excluded_by_archive_latency": None, "share_evaluated": None,
                "classes": ev["game_counts"]}, "predicted_ev": {"n_trades": ev["progress"]["counted_trades"], "mean_ev_net_exec": None}}
    cov = {k: v["coverage"] for k, v in lanes.items() if "per_game" in v["coverage"]}
    rep = {"schema": "issue53.lane_comparison.v2", "authority": "research_only", "generated_utc": MK.iso(now), "games_from": since, "n_games": len(games),
           "scope": "Retrospective reconstruction of the control and of the PRIMARY T-60 availability lane over the games since " + since + " on the final archives (uncounted, descriptive); the two share the T-60 "
                    "checkpoint, the thresholds, the costs and the caps, so the board-selection rule is the only difference. Prospective, counted evidence is read only from each lane's own sealed ledger "
                    "(control start 2026-10-24T06:00Z; t60a start " + prim["prospective_start_utc"] + "); archival quotes are displayed quotes, not proven live fills.",
           "lanes": lanes, "overlap": overlap(trade_rows(rows_by["control_T60_strict"]), trade_rows(rows_by["t60a_T60_available"])),
           "paired": paired(lanes["control_T60_strict"]["coverage"], lanes["t60a_T60_available"]["coverage"], rows_by["control_T60_strict"], rows_by["t60a_T60_available"]),
           "projection_accuracy_all_games": accuracy_all_games(archive, cov),
           "caveats": ["a handful of games: no inference; the coverage columns are mechanics, the P&L and CLV columns are anecdotes",
                       "the availability rule trades on a board that is older at the decision instant than the few boards the control can use (quote age block); the 900 s guard bounds it, the drift is reported",
                       "archival quotes are displayed quotes: nothing here shows that an order would have filled at the sealed price or size",
                       "settled P&L, CLV and drift use the final archives; none of it was available to the selection",
                       "retrospective reconstruction runs the sealer at the first minute of each window with commit-time filters, so it reproduces what a live sealer would have written; it is still uncounted"]}
    if exp_lanes:
        rep["exploratory"] = {"lanes": exp_lanes, "note": "T-45 changes two things relative to the control (the offset AND the board rule); it is inactive, kept only as a labelled exploratory option, and is excluded from the overlap, the paired differences and the accuracy table above."}
    os.makedirs(out, exist_ok=True)
    json.dump(rep, open(os.path.join(out, "lane_comparison.json"), "w"), indent=1, sort_keys=True, default=str)
    open(os.path.join(out, "lane_comparison.md"), "w").write(markdown(rep))
    shutil.rmtree(work, ignore_errors=True)
    return rep


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--archive", required=True)
    ap.add_argument("--market", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--context", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--since", default="2026-10-20")
    ap.add_argument("--now", default=None)
    ap.add_argument("--seals-control", default=None)
    ap.add_argument("--seals-t60a", default=None)
    ap.add_argument("--seals-t45", default=None, help="exploratory only; ignored without --include-t45")
    ap.add_argument("--include-t45", action="store_true", help="add the inactive T-45 study in a separate, labelled exploratory section")
    a = ap.parse_args(argv)
    pro = {k: v for k, v in (("control", a.seals_control), ("t60a", a.seals_t60a), ("t45", a.seals_t45)) if v}
    rep = run(a.archive, a.market, a.repo, a.context or a.market, a.out, a.since, now=MK.parse_ts(a.now) if a.now else None, prospective=pro or None, include_t45=a.include_t45)
    print(markdown(rep))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
