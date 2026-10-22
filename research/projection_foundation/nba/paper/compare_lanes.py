"""Side-by-side comparison of the Issue #53 sealing lanes (RESEARCH ONLY; read-only; descriptive). Results of different lanes are NEVER pooled.

Lanes: `control` = strict T-60 (observed tick must be committed by the checkpoint), `t45` = T-45 availability study (latest tick committed by the decision instant). Each lane has its
own protocol, strategy id, ledger branch, evidence counts and start date. This module reports, per lane and next to each other: coverage and exclusions, predicted EV, closing-line
value, settled performance, executability (board age, price drift), the overlap of selections, and - independently of any lane, trade or market - the projection accuracy on every
eligible game (TRADED, NO_TRADE and no-board games all stay in the denominator).

Two sources of lane rows, always labelled:
  * PROSPECTIVE: the verified, counted seals of a lane's ledger (`exec_seal.evaluate`) - the only evidence;
  * RETROSPECTIVE reconstruction: the lane's own sealer run over past games on the final archives with the lane's commit-time filters (`reconstruct`). It is uncounted and descriptive; it
    answers 'what coverage would the rule have had', never 'does it work'. It also runs two matched comparators (the other rule at the same offset) so a coverage change can be
    attributed to the board rule rather than to the offset.

    python -m nba.paper.compare_lanes --archive <projection-data checkout> --market <data-archive checkout> --repo <git repo with origin/data-archive> --out results/issue53_t45
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


def overlap(a: list[dict], b: list[dict]) -> dict[str, Any]:
    ka = {(c["game_id"], c["ticker"], c["side"]) for c in a}
    kb = {(c["game_id"], c["ticker"], c["side"]) for c in b}
    ga, gb = {k[0] for k in ka}, {k[0] for k in kb}
    return {"contracts_both": len(ka & kb), "control_only": len(ka - kb), "t45_only": len(kb - ka), "games_traded_both": len(ga & gb), "games_control_only": len(ga - gb), "games_t45_only": len(gb - ga),
            "reading": "descriptive; each lane keeps its own ledger and exposure caps, so a shared contract is two separate shadow positions"}


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
def markdown(rep: dict) -> str:
    L = ["# T-60 strict control vs T-45 availability study (research only; descriptive; lanes are never pooled)", "", rep["scope"], ""]
    cols = rep["lanes"]
    L += ["## Coverage", "", "| lane (source) | games | evaluated | traded | excluded by archive latency | excluded no data | share evaluated | decision instants usable |", "|---|---|---|---|---|---|---|---|"]
    for k, v in cols.items():
        c = v["coverage"]
        L.append(f"| {k} ({v['source']}) | {c['games']} | {c['games_with_a_decision_evaluated']} | {c['games_traded']} | {c['excluded_by_archive_latency']} | {c['classes'].get('EXCLUDED_NO_DATA', 0)} | {c['share_evaluated']} | "
                 f"{c.get('decision_instants_with_a_usable_board')} / {c.get('decision_instants')} |")
    L += ["", "## Predicted EV, closing-line value, settled performance (retrospective rows are descriptive; counted evidence only comes from the sealed ledgers)", "",
          "| lane | trades | mean predicted EV | settled | net P&L | ROI on outlay | hit rate | CLV mean (c, n valid) | board age median / p90 (s) | ask drift mean (c) |", "|---|---|---|---|---|---|---|---|---|---|"]
    for k, v in cols.items():
        pe, st, ex = v["predicted_ev"], v.get("settled") or {}, v.get("executability") or {}
        clv = (st.get("clv_cents") or {})
        age = (ex.get("board_age_at_decision_s") or {})
        L.append(f"| {k} | {pe['n_trades']} | {pe['mean_ev_net_exec']} | {st.get('n_settled')} | {st.get('net_pnl')} | {st.get('roi_on_cash_outlay')} | {st.get('hit_rate')} | "
                 f"{clv.get('mean')} ({clv.get('n_valid')}) | {age.get('median')} / {age.get('p90')} | {(ex.get('ask_drift_cents') or {}).get('mean')} |")
    L += ["", f"Selection overlap (control vs T-45, retrospective): {json.dumps(rep['overlap'])}", ""]
    a = rep["projection_accuracy_all_games"]
    L += ["## Projection accuracy on all eligible games (independent of trades, markets and lanes)", ""]
    if a.get("status") == "OK":
        L.append(f"* eligible games with settled forecasts: {a['n_eligible_games']}; challenger forecasts scored: {a['n_challenger_forecasts_scored']}")
        L.append(f"* eligible games by lane status: {json.dumps(a['eligible_games_by_lane_status'])}")
        L.append(f"* {a['rule']}")
    else:
        L.append(f"* {a.get('reason')}")
    L += ["", "## Caveats", ""] + [f"* {c}" for c in rep["caveats"]]
    return "\n".join(L) + "\n"


def run(archive: str, market: str, repo: str, context: str, out: str, since: str = "2026-10-20", ref: str = "origin/data-archive", forecast_ref: str = "origin/projection-data",
        now: datetime | None = None, prospective: dict[str, str] | None = None) -> dict[str, Any]:
    now = now or datetime.now(UTC).replace(microsecond=0)
    base = CFG.load()
    games_all = SW.schedule_games(context, None, all_history=True)
    games = [g for g in games_all if MK.parse_ts(g["start_utc"]) >= MK.parse_ts(since + "T00:00:00Z") and MK.parse_ts(g["start_utc"]) <= now - timedelta(hours=1)]
    clocks = {"board_commit": X.board_commit_index(repo, ref), "forecast_commit": X.forecast_commit_index(archive, repo, forecast_ref)}
    work = tempfile.mkdtemp(prefix="lanes_")
    ctrl, t45 = lane_study("control"), lane_study("t45")
    variants = {"control_T60_strict": ("control", ctrl, "RETROSPECTIVE_RECONSTRUCTION"), "t45_T45_available": ("t45", t45, "RETROSPECTIVE_RECONSTRUCTION"),
                "comparator_T60_available": ("cmp", _variant(t45, 60, "latest_committed_by_decision"), "RETROSPECTIVE_COMPARATOR"),
                "comparator_T45_strict": ("cmp", _variant(ctrl, 45, "observed_and_committed_by_checkpoint"), "RETROSPECTIVE_COMPARATOR")}
    lanes: dict[str, Any] = {}
    rows_by: dict[str, list[dict]] = {}
    for name, (_, st, src) in variants.items():
        rc = reconstruct(st, games, archive, market, clocks, base, work, name)
        trades = trade_rows(rc["rows"])
        settle = SL.settle_sealed(trades, archive, market, now, base, strategy_id=X.strategy_id(st), horizon=st["checkpoint"]["horizon"]) if trades else {}
        lanes[name] = summarize(name, src, st, rc["bodies"], rc["rows"], games, market, settle)
        lanes[name]["errors"] = rc["errors"]
        rows_by[name] = rc["rows"]
    if prospective:
        for ln, seal_dir in prospective.items():
            st = lane_study(ln)
            ev = SL.evaluate(seal_dir, archive, market, now, st, base, schedule=games, board_commits=clocks["board_commit"] if ln == "t45" else None)
            lanes[f"{ln}_PROSPECTIVE"] = {"source": "PROSPECTIVE_SEALED", "evaluation": {k: ev[k] for k in ("game_counts", "progress", "metrics", "settlement_join")}, "coverage": {
                "games": len(games), "games_with_a_decision_evaluated": None, "games_traded": ev["progress"]["counted_games_traded"], "excluded_by_archive_latency": None, "share_evaluated": None,
                "classes": ev["game_counts"]}, "predicted_ev": {"n_trades": ev["progress"]["counted_trades"], "mean_ev_net_exec": None}}
    cov = {k: v["coverage"] for k, v in lanes.items() if "per_game" in v["coverage"]}
    rep = {"schema": "issue53.lane_comparison.v1", "authority": "research_only", "generated_utc": MK.iso(now), "games_from": since, "n_games": len(games),
           "scope": "Retrospective reconstruction of both lanes' sealers over the games since " + since + " on the final archives (uncounted, descriptive) plus two matched comparators that change one thing at a time; "
                    "prospective, counted evidence is read only from each lane's own sealed ledger and is not available yet (control start 2026-10-24T06:00Z; T-45 start 2026-10-27T06:00Z, after approval).",
           "lanes": lanes, "overlap": overlap(trade_rows(rows_by["control_T60_strict"]), trade_rows(rows_by["t45_T45_available"])),
           "projection_accuracy_all_games": accuracy_all_games(archive, cov),
           "caveats": ["a handful of games: no interval, no inference; the coverage columns are mechanics, the P&L columns are anecdotes",
                       "the availability rule trades on a board that is on average ~8 minutes old at the decision instant (executability block); the control's board is younger but loses most games to commit latency",
                       "T-45 differs from the control in two things (offset AND board rule); the matched comparators (T-60 available, T-45 strict) separate them",
                       "settled P&L, CLV and drift use the final archives; none of it was available to the selection",
                       "retrospective reconstruction runs the sealer at the first minute of each window with commit-time filters, so it reproduces what a live sealer would have written; it is still uncounted"]}
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
    ap.add_argument("--seals-t45", default=None)
    a = ap.parse_args(argv)
    pro = {k: v for k, v in (("control", a.seals_control), ("t45", a.seals_t45)) if v}
    rep = run(a.archive, a.market, a.repo, a.context or a.market, a.out, a.since, now=MK.parse_ts(a.now) if a.now else None, prospective=pro or None)
    print(markdown(rep))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
