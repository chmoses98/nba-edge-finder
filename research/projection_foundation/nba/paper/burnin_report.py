"""Side-by-side report of two sealed lanes over the same games (RESEARCH ONLY; read-only; descriptive). Burn-in seals (before a lane's prospective start) are labelled and NEVER counted.

Selections are read from the sealed ledgers and are never recomputed; settlement only joins outcomes to the sealed trades (`exec_seal.settle_sealed`). Per lane it reports valid / excluded / missed
games, the reasons for exclusion (archive-latency, no board, quality gate), trades, settled P&L, ROI on cash outlay, hit rate, CLV, board age, spread, depth, the ask drift to the next board, and
predicted EV against the realised result. Across lanes it splits trades into SHARED (same game, contract and side) and LANE-ONLY and reports the second group on its own, because the question
is whether the extra opportunities stay attractive after the execution costs already inside `ev_net_exec` (slippage, whole-order fee, displayed size).

Nothing here is evidence of profitability: with a handful of games every figure is an anecdote; an interval is printed only with at least `MIN_GAMES_FOR_INTERVAL` games.

EVIDENCE CLASSES. Every seal is run through the same independent verification the evaluator uses (`exec_seal.evaluate` -> `verify_seal`: body / candidate hashes, additions-only history and the SERVER commit time against the
tip-10min deadline, protocol and code pins, default-branch reachability, duplicate detection, the board re-derived from the final archive, prospective start) and is put in exactly one class:
  COUNTED    verified and at/after the lane's prospective start        -> the only seals behind the headline statistics
  BURN_IN    verified except for BEFORE_PROSPECTIVE_START (nothing else) -> reported separately, labelled NOT EVIDENCE
  INVALID    any other failure (hash, late commit, modified history, dry run, unpinned code, unverifiable board, malformed ...) -> listed with reasons, in no statistic
  DUPLICATE  a later seal of an already sealed game                    -> listed, in no statistic
Without `--repo` (no way to prove code reachability or the final board commits) nothing can be COUNTED: the report fails closed.

    python -m nba.paper.burnin_report --archive <projection-data> --market <data-archive> --repo <code clone with origin/main and origin/data-archive> --control <ledger dir> --other <ledger dir> --other-lane t60a --from 2026-10-25T12:00:00Z --out <dir>
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Any

import numpy as np

from . import compare_lanes as CL
from . import config as CFG
from . import exec_seal as SL
from . import exec_shadow as X
from . import markets as MK
from . import seal_windows as SW

MIN_GAMES_FOR_INTERVAL = 8


def key(r: dict) -> tuple:
    return (r["game_id"], r["ticker"], r["side"])


COUNTED, BURN_IN, INVALID, DUPLICATE = "COUNTED", "BURN_IN", "INVALID", "DUPLICATE"
PRE_START = "BEFORE_PROSPECTIVE_START"


def load(ledger: str, from_tip: str) -> list[tuple[str, dict]]:
    """[(path relative to the ledger, seal body)] for every seal of a game at/after `from_tip`; unreadable files are kept (and become INVALID)."""
    out = []
    for body, p in SL.iter_seals(ledger):
        g = body.get("game") if isinstance(body.get("game"), dict) else None
        if g is not None and (g.get("start_utc") or "") < from_tip:
            continue
        out.append((os.path.relpath(p, ledger), body))
    return out


def classify(entries: list[tuple[str, dict]], ev: dict) -> dict[str, tuple[str, list[str]]]:
    """rel path -> (class, reasons), from the evaluator's own verdicts. Anything the evaluator did not vouch for is INVALID (never COUNTED by default)."""
    by_gid = {g["game_id"]: g for g in ev.get("games", []) if g.get("seal_id")}
    dup_paths = {d["path"] for d in ev.get("duplicates", [])}
    out: dict[str, tuple[str, list[str]]] = {}
    for rel, body in entries:
        gid = (body.get("game") or {}).get("game_id") if isinstance(body.get("game"), dict) else None
        if body.get("_unreadable") or not gid:
            out[rel] = (INVALID, ["UNREADABLE_OR_MALFORMED"])
        elif rel in dup_paths:
            out[rel] = (DUPLICATE, ["DUPLICATE_SEAL"])
        else:
            v = by_gid.get(gid)
            if v is None or v.get("seal_id") != body.get("seal_id"):
                out[rel] = (INVALID, ["NOT_VERIFIED_BY_EVALUATOR"])
            elif v.get("counted") is True and not v.get("uncounted_reasons"):
                out[rel] = (COUNTED, [])
            elif list(v.get("uncounted_reasons") or []) == [PRE_START]:
                out[rel] = (BURN_IN, [PRE_START])
            else:
                out[rel] = (INVALID, list(v.get("uncounted_reasons") or ["UNCOUNTED"]))
    return out


def lane_rows(ledger: str, entries: list[tuple[str, dict]], klass: dict, study: dict, wanted: str) -> tuple[list[dict], list[dict]]:
    """(bodies, hydrated candidate rows) of the seals in class `wanted` only; selections are read from the sealed candidate files, never recomputed."""
    bodies, rows = [], []
    for rel, body in entries:
        if klass[rel][0] != wanted:
            continue
        bodies.append(body)
        for r in SL.load_candidates(ledger, body, rel):
            rows.append(SL.hydrate(r, body, study, counted=(wanted == COUNTED)))
    return bodies, rows


def reason_of(b: dict) -> str:
    if b["status"] == "TRADED":
        return "TRADED"
    r = (b.get("game_reason") or "").split(";")[0].split("=")[0]
    return r or "NO_TRADE"


def summarize(bodies: list[dict], trades: list[dict], market: str | None) -> dict[str, Any]:
    settled = [t for t in trades if t.get("settled") and t.get("net_pnl") is not None]
    pnl = [float(t["net_pnl"]) for t in settled]
    outlay = sum(float(t["effective_entry_exec"]) for t in settled)
    won = [bool(t["won"]) for t in settled]
    clv = [float(t["clv_cents"]) for t in settled if t.get("clv_cents") is not None]
    ages = [float(b["board"]["gap_s"]) for b in bodies if b.get("board") and b["board"].get("gap_s") is not None]
    f = lambda a, nd=3: None if not len(a) else round(float(np.mean(a)), nd)      # noqa: E731
    depth = [float(t.get("depth_at_entry") if t.get("depth_at_entry") is not None else t["top_size"]) for t in trades if t.get("depth_at_entry") is not None or t.get("top_size") is not None]
    out = {
        "seals": len(bodies), "games_traded": len({t["game_id"] for t in trades}), "reasons": dict(Counter(reason_of(b) for b in bodies)),
        "trades": len(trades), "settled": len(settled), "pending": len(trades) - len(settled),
        "net_pnl": round(sum(pnl), 2), "roi_on_outlay": None if not outlay else round(sum(pnl) / outlay, 3), "hit_rate": f(won), "mean_clv_cents": f(clv, 2), "n_clv": len(clv),
        "predicted": {"mean_ev_per_trade": f([t["ev_net_exec"] for t in trades], 4), "mean_p_win": f([t["p_model"] for t in settled], 3), "sum_ev_settled": round(float(sum(t["ev_net_exec"] for t in settled)), 2)},
        "realised": {"net_pnl_settled": round(sum(pnl), 2), "mean_pnl_per_trade": f(pnl, 3), "hit_rate": f(won)},
        "board_age_s": {"median": None if not ages else round(float(np.median(ages)), 1), "p90": None if not ages else round(float(np.percentile(ages, 90)), 1), "n": len(ages)},
        "spread_mean": f([t["spread"] for t in trades if t.get("spread") is not None], 4), "depth_median": None if not depth else round(float(np.median(depth)), 1),
    }
    if market and trades:
        out["ask_drift_to_next_board"] = CL.price_drift(trades, market)
    return out


def split_shared(control: list[dict], other: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """(shared [control rows], control-only, other-only) by (game, contract, side)."""
    ck, ok = {key(t): t for t in control}, {key(t): t for t in other}
    return [ck[k] for k in sorted(set(ck) & set(ok))], [ck[k] for k in sorted(set(ck) - set(ok))], [ok[k] for k in sorted(set(ok) - set(ck))]


def per_game_pnl(trades: list[dict]) -> dict[str, float]:
    d: dict[str, float] = defaultdict(float)
    for t in trades:
        if t.get("settled") and t.get("net_pnl") is not None:
            d[t["game_id"]] += float(t["net_pnl"])
    return dict(d)


def compare(ctrl: list[dict], other: list[dict], other_lane: str, market: str | None, seed: int) -> dict[str, Any]:
    """Shared vs lane-only positions and the game-clustered paired P&L difference, over the given trade rows only."""
    shared_rows, only_ctrl, only_other = split_shared(ctrl, other)
    games_c = {t["game_id"] for t in ctrl}
    rep: dict[str, Any] = {"shared_trades": len(shared_rows), "control_only_trades": len(only_ctrl), f"{other_lane}_only_trades": len(only_other),
                           f"{other_lane}_only_in_games_the_control_also_traded": sum(1 for t in only_other if t["game_id"] in games_c),
                           f"{other_lane}_only_games": len({t["game_id"] for t in only_other} - games_c),
                           f"{other_lane}_only": summarize([], only_other, market), "shared": summarize([], shared_rows, market)}
    diffs = per_game_pnl(other)
    for g, v in per_game_pnl(ctrl).items():
        diffs[g] = diffs.get(g, 0.0) - v
    games = sorted(set(diffs))
    d = np.asarray([diffs[g] for g in games]) if games else np.asarray([])
    ci: dict[str, Any] = {"status": "INSUFFICIENT_GAMES", "min_games": MIN_GAMES_FOR_INTERVAL, "n_games": len(games)}
    if len(d) >= MIN_GAMES_FOR_INTERVAL:
        rng = np.random.default_rng(seed)
        bs = np.sort([float(rng.choice(d, size=len(d), replace=True).mean()) for _ in range(2000)])
        ci = {"status": "OK", "n_games": len(d), "mean_per_game": round(float(d.mean()), 4), "lo95": round(bs[49], 4), "hi95": round(bs[1949], 4), "method": "game-clustered bootstrap, seed 53"}
    rep["paired_net_pnl_difference_per_game"] = {f"{other_lane}_minus_control": ci}
    return rep


def lane_report(ledger: str, entries: list[tuple[str, dict]], ev: dict, study: dict, archive: str, market: str, now, base: dict) -> dict[str, Any]:
    """One lane: the class of every seal, then statistics for COUNTED seals (headline) and, apart, for clean BURN_IN seals (labelled not evidence)."""
    klass = classify(entries, ev)
    out: dict[str, Any] = {"prospective_start_utc": study["prospective_start_utc"], "seal_classes": dict(Counter(k for k, _ in klass.values())),
                           "game_categories": ev.get("game_counts", {}),
                           "excluded_seals": [{"path": rel, "class": k, "reasons": why} for rel, (k, why) in sorted(klass.items()) if k in (INVALID, DUPLICATE)]}
    trades_by: dict[str, list[dict]] = {}
    for name, wanted in (("counted", COUNTED), ("burn_in_not_evidence", BURN_IN)):
        bodies, rows = lane_rows(ledger, entries, klass, study, wanted)
        trades = [r for r in rows if r.get("decision") == "TRADE"]
        st = SL.settle_sealed(trades, archive, market, now, base, strategy_id=X.strategy_id(study), horizon=study["checkpoint"]["horizon"])
        out[name] = {"settle_join": st, **summarize(bodies, trades, market)}
        trades_by[name] = trades
    return out | {"_trades": trades_by}


def build(archive: str, market: str, control_dir: str, other_dir: str, other_lane: str, from_tip: str, now=None, seed: int = 53, *, code_repo: str | None = None,
          default_branch_ref: str = "origin/main", data_branch_ref: str = "origin/data-archive") -> dict[str, Any]:
    base = CFG.load()
    now = now or datetime.now(UTC)
    studies = {"control": X.load_study(), other_lane: X.load_lane(SW.lane_study_path(other_lane))}
    dirs = {"control": control_dir, other_lane: other_dir}
    schedule = [g for g in SW.schedule_games(market, None, all_history=True) if MK.parse_ts(g["start_utc"]) >= MK.parse_ts(from_tip)]
    lanes: dict[str, Any] = {}
    trades: dict[str, dict[str, list[dict]]] = {}
    for ln, d in dirs.items():
        study = studies[ln]
        # board commit index only for the availability rule (as the evaluator and the live sealer do); without a code repo nothing can be proven, so nothing counts
        bc = X.board_commit_index(code_repo, data_branch_ref) if code_repo and X.board_rule_id(study) == "latest_committed_by_decision" else None
        ev = SL.evaluate(d, archive, market, now, study, base, code_repo=code_repo, default_branch_ref=default_branch_ref, schedule=schedule, board_commits=bc)
        entries = load(d, from_tip)
        rep_l = lane_report(d, entries, ev, study, archive, market, now, base)
        trades[ln] = rep_l.pop("_trades")
        lanes[ln] = rep_l
    rep: dict[str, Any] = {"schema": "issue53.burnin_report.v2", "authority": "research_only", "from_tip": from_tip, "other_lane": other_lane, "lanes": lanes,
                           "code_repo_verified": bool(code_repo),
                           "counted": compare(trades["control"]["counted"], trades[other_lane]["counted"], other_lane, market, seed),
                           "burn_in_not_evidence": compare(trades["control"]["burn_in_not_evidence"], trades[other_lane]["burn_in_not_evidence"], other_lane, market, seed)}
    rep["caveat"] = ("descriptive only: archival quotes are displayed quotes, not proven live fills; costs (1 c slippage, whole-order fee, displayed size) are already inside ev_net_exec; "
                     "trades within a game are correlated; a handful of games supports no inference about profitability or calibration; "
                     "only COUNTED seals (independently verified, at/after the prospective start) are evidence; BURN_IN is shown apart and is never counted")
    return rep


def _table(rep: dict, section: str) -> list[str]:
    o = rep["other_lane"]
    L = ["| | control | " + o + " |", "|---|---|---|"]
    c, t = rep["lanes"]["control"][section], rep["lanes"][o][section]

    def row(name, f):
        L.append(f"| {name} | {f(c)} | {f(t)} |")
    row("seals", lambda x: x["seals"])
    row("reasons", lambda x: json.dumps(x["reasons"]))
    row("games traded / trades", lambda x: f"{x['games_traded']} / {x['trades']}")
    row("settled / pending", lambda x: f"{x['settled']} / {x['pending']}")
    row("net P&L (settled)", lambda x: x["net_pnl"])
    row("ROI on outlay", lambda x: x["roi_on_outlay"])
    row("hit rate (predicted p)", lambda x: f"{x['hit_rate']} ({x['predicted']['mean_p_win']})")
    row("mean EV predicted / realised per trade", lambda x: f"{x['predicted']['mean_ev_per_trade']} / {x['realised']['mean_pnl_per_trade']}")
    row("mean CLV (c, n)", lambda x: f"{x['mean_clv_cents']} ({x['n_clv']})")
    row("board age s (median / p90)", lambda x: f"{x['board_age_s']['median']} / {x['board_age_s']['p90']}")
    row("spread mean / depth median", lambda x: f"{x['spread_mean']} / {x['depth_median']}")
    row("ask drift to next board (mean c, adverse share)", lambda x: f"{((x.get('ask_drift_to_next_board') or {}).get('ask_drift_cents') or {}).get('mean')} / {(x.get('ask_drift_to_next_board') or {}).get('share_adverse')}")
    return L


def _shared(rep: dict, key_: str) -> list[str]:
    o, s = rep["other_lane"], rep[key_]
    return [f"* shared {s['shared_trades']}; control-only {s['control_only_trades']}; {o}-only {s[o + '_only_trades']} ({s[o + '_only_games']} in games the control did not trade)",
            f"* shared: {json.dumps({k: s['shared'][k] for k in ('trades', 'settled', 'net_pnl', 'roi_on_outlay', 'hit_rate', 'mean_clv_cents')})}",
            f"* {o}-only: {json.dumps({k: s[o + '_only'][k] for k in ('trades', 'settled', 'net_pnl', 'roi_on_outlay', 'hit_rate', 'mean_clv_cents', 'predicted', 'board_age_s', 'spread_mean', 'depth_median')})}",
            f"* paired per-game net P&L ({o} minus control): {json.dumps(s['paired_net_pnl_difference_per_game'])}"]


def markdown(rep: dict) -> str:
    o = rep["other_lane"]
    L = [f"# Control vs {o}: side-by-side (descriptive)", "", rep["caveat"], ""]
    if not rep.get("code_repo_verified"):
        L += ["**No code repo given: seals cannot be verified, so NOTHING is counted (fail closed).**", ""]
    L += ["## Seal classes (independent verification)", "", "| | control | " + o + " |", "|---|---|---|"]
    cl = {ln: rep["lanes"][ln]["seal_classes"] for ln in ("control", o)}
    for k in (COUNTED, BURN_IN, INVALID, DUPLICATE):
        L.append(f"| {k} | {cl['control'].get(k, 0)} | {cl[o].get(k, 0)} |")
    for ln in ("control", o):
        for e in rep["lanes"][ln]["excluded_seals"]:
            L.append(f"* {ln} {e['class']}: `{e['path']}` {e['reasons']}")
    L += ["", f"game categories: control {json.dumps(rep['lanes']['control']['game_categories'])}; {o} {json.dumps(rep['lanes'][o]['game_categories'])}", "",
          "## COUNTED seals only (the evidence)", ""] + _table(rep, "counted") + [""] + _shared(rep, "counted") + \
         ["", "## BURN-IN seals (verified but before the prospective start): NOT EVIDENCE, descriptive only", ""] + _table(rep, "burn_in_not_evidence") + [""] + _shared(rep, "burn_in_not_evidence")
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for a in ("archive", "market", "control", "other", "out"):
        ap.add_argument("--" + a, required=True)
    ap.add_argument("--repo", default=None, help="code clone holding origin/main and origin/data-archive; without it no seal can be COUNTED")
    ap.add_argument("--other-lane", default="t60a")
    ap.add_argument("--from", dest="from_tip", default="2026-10-25T12:00:00Z")
    ap.add_argument("--now", default=None)
    a = ap.parse_args(argv)
    now = MK.parse_ts(a.now) if a.now else datetime.now(UTC)
    rep = build(a.archive, a.market, a.control, a.other, a.other_lane, a.from_tip, now=now, code_repo=a.repo)
    os.makedirs(a.out, exist_ok=True)
    json.dump(rep, open(os.path.join(a.out, "burnin_report.json"), "w"), indent=1, sort_keys=True, default=str)
    open(os.path.join(a.out, "burnin_report.md"), "w").write(markdown(rep))
    print(markdown(rep))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
