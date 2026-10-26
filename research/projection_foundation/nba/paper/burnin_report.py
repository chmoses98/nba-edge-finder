"""Side-by-side report of two sealed lanes over the same games (RESEARCH ONLY; read-only; descriptive). Burn-in seals (before a lane's prospective start) are labelled and NEVER counted.

Selections are read from the sealed ledgers and are never recomputed; settlement only joins outcomes to the sealed trades (`exec_seal.settle_sealed`). Per lane it reports valid / excluded / missed
games, the reasons for exclusion (archive-latency, no board, quality gate), trades, settled P&L, ROI on cash outlay, hit rate, CLV, board age, spread, depth, the ask drift to the next board, and
predicted EV against the realised result. Across lanes it splits trades into SHARED (same game, contract and side) and LANE-ONLY and reports the second group on its own, because the question
is whether the extra opportunities stay attractive after the execution costs already inside `ev_net_exec` (slippage, whole-order fee, displayed size).

Nothing here is evidence of profitability: with a handful of games every figure is an anecdote; an interval is printed only with at least `MIN_GAMES_FOR_INTERVAL` games.

    python -m nba.paper.burnin_report --archive <projection-data> --market <data-archive> --control <ledger dir> --other <ledger dir> --other-lane t60a --from 2026-10-25T12:00:00Z --out <dir>
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from datetime import timedelta
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


def load(ledger: str, study: dict, from_tip: str) -> tuple[list[dict], list[dict]]:
    bodies, rows = [], []
    for body, p in SL.iter_seals(ledger):
        if body["game"]["start_utc"] < from_tip:
            continue
        bodies.append(body)
        for r in SL.load_candidates(ledger, body, os.path.relpath(p, ledger)):
            rows.append(SL.hydrate(r, body, study, counted=False))
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


def build(archive: str, market: str, control_dir: str, other_dir: str, other_lane: str, from_tip: str, now=None, seed: int = 53) -> dict[str, Any]:
    base = CFG.load()
    now = now or MK.parse_ts(os.popen("date -u +%Y-%m-%dT%H:%M:%SZ").read().strip())
    studies = {"control": X.load_study(), other_lane: X.load_lane(SW.lane_study_path(other_lane))}
    dirs = {"control": control_dir, other_lane: other_dir}
    lanes: dict[str, Any] = {}
    allrows: dict[str, list[dict]] = {}
    for ln, d in dirs.items():
        bodies, rows = load(d, studies[ln], from_tip)
        trades = [r for r in rows if r.get("decision") == "TRADE"]
        st = SL.settle_sealed(trades, archive, market, now, base, strategy_id=X.strategy_id(studies[ln]), horizon=studies[ln]["checkpoint"]["horizon"])
        start = studies[ln]["prospective_start_utc"]
        counted_possible = [b for b in bodies if b["checkpoint_utc"] >= start and b["computed_utc"] >= start]
        lanes[ln] = {"prospective_start_utc": start, "evidence_status": f"{len(counted_possible)} of {len(bodies)} seals are at/after the prospective start (still subject to verification); the rest are BURN-IN and uncounted",
                     "settle_join": st, **summarize(bodies, trades, market)}
        allrows[ln] = trades
    shared_rows, only_ctrl, only_other = split_shared(allrows["control"], allrows[other_lane])
    shared = shared_rows
    games_c = {t["game_id"] for t in allrows["control"]}
    rep: dict[str, Any] = {"schema": "issue53.burnin_report.v1", "authority": "research_only", "from_tip": from_tip, "other_lane": other_lane, "lanes": lanes,
                           "shared_vs_lane_only": {"shared_trades": len(shared), "control_only_trades": len(only_ctrl), f"{other_lane}_only_trades": len(only_other),
                                                   f"{other_lane}_only_in_games_the_control_also_traded": sum(1 for t in only_other if t["game_id"] in games_c),
                                                   f"{other_lane}_only_games": len({t["game_id"] for t in only_other} - games_c),
                                                   f"{other_lane}_only": summarize([], only_other, market), "shared": summarize([], shared_rows, market)}}
    diffs = per_game_pnl(allrows[other_lane])
    for g, v in per_game_pnl(allrows["control"]).items():
        diffs[g] = diffs.get(g, 0.0) - v
    games = sorted(set(diffs))
    d = np.asarray([diffs[g] for g in games]) if games else np.asarray([])
    ci: dict[str, Any] = {"status": "INSUFFICIENT_GAMES", "min_games": MIN_GAMES_FOR_INTERVAL, "n_games": len(games)}
    if len(d) >= MIN_GAMES_FOR_INTERVAL:
        rng = np.random.default_rng(seed)
        bs = np.sort([float(rng.choice(d, size=len(d), replace=True).mean()) for _ in range(2000)])
        ci = {"status": "OK", "n_games": len(d), "mean_per_game": round(float(d.mean()), 4), "lo95": round(bs[49], 4), "hi95": round(bs[1949], 4), "method": "game-clustered bootstrap, seed 53"}
    rep["paired_net_pnl_difference_per_game"] = {f"{other_lane}_minus_control": ci}
    rep["caveat"] = ("descriptive only: archival quotes are displayed quotes, not proven live fills; costs (1 c slippage, whole-order fee, displayed size) are already inside ev_net_exec; "
                     "a handful of games supports no inference about profitability; burn-in seals are never counted")
    return rep


def markdown(rep: dict) -> str:
    o = rep["other_lane"]
    L = [f"# Control vs {o}: side-by-side (descriptive; burn-in is uncounted)", "", rep["caveat"], "", "| | control | " + o + " |", "|---|---|---|"]
    c, t = rep["lanes"]["control"], rep["lanes"][o]
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
    s = rep["shared_vs_lane_only"]
    L += ["", f"## Shared vs {o}-only trades", "", f"* shared {s['shared_trades']}; control-only {s['control_only_trades']}; {o}-only {s[o + '_only_trades']} "
          f"({s[o + '_only_games']} in games the control did not trade)",
          f"* shared: {json.dumps({k: s['shared'][k] for k in ('trades', 'settled', 'net_pnl', 'roi_on_outlay', 'hit_rate', 'mean_clv_cents')})}",
          f"* {o}-only: {json.dumps({k: s[o + '_only'][k] for k in ('trades', 'settled', 'net_pnl', 'roi_on_outlay', 'hit_rate', 'mean_clv_cents', 'predicted', 'board_age_s', 'spread_mean', 'depth_median')})}",
          "", f"## Paired per-game net P&L ({o} minus control)", "", "* " + json.dumps(rep["paired_net_pnl_difference_per_game"])]
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for a in ("archive", "market", "control", "other", "out"):
        ap.add_argument("--" + a, required=True)
    ap.add_argument("--other-lane", default="t60a")
    ap.add_argument("--from", dest="from_tip", default="2026-10-25T12:00:00Z")
    ap.add_argument("--now", default=None)
    a = ap.parse_args(argv)
    now = MK.parse_ts(a.now) if a.now else MK.parse_ts(os.popen("date -u +%Y-%m-%dT%H:%M:%SZ").read().strip()) + timedelta(0)
    rep = build(a.archive, a.market, a.control, a.other, a.other_lane, a.from_tip, now=now)
    os.makedirs(a.out, exist_ok=True)
    json.dump(rep, open(os.path.join(a.out, "burnin_report.json"), "w"), indent=1, sort_keys=True, default=str)
    open(os.path.join(a.out, "burnin_report.md"), "w").write(markdown(rep))
    print(markdown(rep))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
