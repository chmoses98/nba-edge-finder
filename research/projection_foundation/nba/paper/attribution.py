"""Exact attribution of the original `PF_EDGE_STRICT_V1` selected trades (Issue #53, part A; read-only, RESEARCH ONLY).

    from nba.paper import attribution as A
    t = A.attribute(archive, day_et="2026-10-20")      # DataFrame: one row per selected thesis, every field read from the archives
    rec = A.reconcile(archive, t, "2026-10-20")         # reconciliation against paper/nba/scorecards/daily/<day>.json

The selection is the scorecard's own (evaluate.paper_performance): all TRADE decisions of the strategy, then per thesis the EARLIEST by
(as_of, decision_id) across horizons. That rule is the reason the seven bets are not a simultaneously executable portfolio: each horizon is an
alternative run with its own exposure caps, and the earliest horizon that traded a thesis wins. Nothing is typed in by hand; no price, size or
fill is backfilled; a field the archive does not hold is None.
"""
from __future__ import annotations

import glob
import gzip
import json
import os
import subprocess
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from . import evaluate as E
from . import markets as MK
from . import schema as S
from . import stats as ST

STRATEGY = "PF_EDGE_STRICT_V1"
ISSUE_STATED = {"n_decisions": 7, "n_games": 2, "net_pnl": 1.39, "entry_cost": 3.40, "roi": 0.40882}


# ================================================================================================ human readable terms
def human_terms(r: dict) -> str:
    """Kalshi strike -> plain words. Player ladders are 'X or more' (k = floor(strike) + 1, strike = k - 0.5); NO = strictly fewer than k."""
    fam, side, k = r.get("family"), r.get("side"), r.get("k")
    thr = r.get("threshold")
    unit = {"player_points": "points", "player_rebounds": "rebounds", "player_assists": "assists", "player_threes": "made threes",
            "player_pra": "points+rebounds+assists"}.get(fam)
    if unit and k is not None and not pd.isna(k):
        k = int(k)
        who = r.get("player_name") or r.get("entity_id")
        if side == "YES":
            return f"{who}: YES = {k}+ {unit} (at least {k})"
        return f"{who}: NO = fewer than {k} {unit} (at most {k - 1}); contract strike {thr}"
    if fam == "game_total":
        return f"Game total {'over' if side == 'YES' else 'under'} {thr}"
    if fam == "team_total":
        return f"{r.get('team')} team total {'over' if side == 'YES' else 'under'} {thr}"
    if fam in ("game_spread", "game_winner"):
        return f"{r.get('team')} {fam.replace('game_', '')} {thr if thr is not None else ''} ({side})".strip()
    return f"{fam} {thr} ({side})"


# ================================================================================================ archive provenance
def _git_added(repo: str | None, ref: str, rel: str) -> str | None:
    if not repo:
        return None
    out = subprocess.run(["git", "-C", repo, "log", ref, "--diff-filter=A", "--format=%cI", "--", rel], capture_output=True, text=True).stdout.split()
    return pd.Timestamp(out[-1]).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ") if out else None


def locate(archive: str, subdir: str, id_field: str, ids: set[str], day_glob: str = "*") -> dict[str, str]:
    """id -> archive-relative path of the (first) file holding it. Reads each file once."""
    found: dict[str, str] = {}
    for p in sorted(glob.glob(os.path.join(archive, subdir, day_glob, "*.jsonl.gz"))):
        with gzip.open(p, "rt") as f:
            for line in f:
                if not line.strip():
                    continue
                for i in ids:
                    if i not in found and i in line:           # cheap pre-filter, exact check below
                        r = json.loads(line)
                        if r.get(id_field) == i:
                            found[i] = os.path.relpath(p, archive)
                if len(found) == len(ids):
                    return found
    return found


def _forecast_records(archive: str, ids: set[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in sorted(glob.glob(os.path.join(archive, "forecasts", "nba", "*", "*.jsonl.gz"))):
        with gzip.open(p, "rt") as f:
            for line in f:
                if not line.strip():
                    continue
                if any(i in line for i in ids):
                    r = json.loads(line)
                    if r.get("forecast_id") in ids:
                        out[r["forecast_id"]] = {"archived_utc": r.get("archived_utc"), "generated_utc": r.get("generated_utc"), "model_id": r.get("model_id"),
                                                 "model_version": r.get("model_version"), "family": r.get("family"), "path": os.path.relpath(p, archive)}
    return out


# ================================================================================================ selection
def first_trade_per_thesis(sel: pd.DataFrame) -> pd.DataFrame:
    """The scorecard's `overall_one_per_thesis`: earliest TRADE of each thesis across horizons (evaluate.paper_performance)."""
    return sel.sort_values(["as_of", "decision_id"]).drop_duplicates("thesis_id", keep="first")


def attribute(archive: str, day_et: str, now: datetime | None = None, *, git_repo: str | None = None, git_ref: str = "origin/projection-data",
              strategy: str = STRATEGY, board_commits: dict[str, str] | None = None) -> pd.DataFrame:
    now = now or datetime(2099, 1, 1, tzinfo=__import__("datetime").timezone.utc)
    D = E.load(archive, now, day_et=day_et, prospective_only=True)
    d = D.dec
    if d.empty:
        return pd.DataFrame()
    sel = d[(d["strategy_id"] == strategy) & (d["decision"] == "TRADE") & d["settled"]]
    first = first_trade_per_thesis(sel).sort_values(["as_of", "decision_id"]).reset_index(drop=True)
    if first.empty:
        return pd.DataFrame()
    # ---- horizon path of every selected thesis (all horizons, TRADE and PASS, same strategy)
    allv = d[(d["strategy_id"] == strategy) & d["thesis_id"].isin(first["thesis_id"])]
    live = d[(d["strategy_id"] == "PF_ALL_CANDIDATES_V1") & (d["decision_mode"] == "contemporaneous") & d["side"].isin(["YES", "NO"])]
    fids = {i for ids in first["forecast_ids"] for i in (ids or []) if i}
    fr = _forecast_records(archive, fids)
    dec_files = locate(archive, "paper/nba/decisions", "decision_id", set(first["decision_id"]))
    set_files = locate(archive, "paper/nba/settlements", "decision_id", set(first["decision_id"]))
    snap_files = locate(archive, "market_snapshots/nba", "snapshot_id", set(first["snapshot_id"]))
    rows = []
    for r in first.to_dict("records"):
        path = allv[allv["thesis_id"] == r["thesis_id"]].sort_values(["as_of", "decision_id"])
        # other candidates of the same thesis at the same instant: why they lost (read from the compact PASS rows of the same horizon run)
        same = d[(d["strategy_id"] == strategy) & (d["thesis_id"] == r["thesis_id"]) & (d["horizon"] == r["horizon"]) & (d["as_of_utc"] == r["as_of_utc"])]
        cl = r.get("closing_line") if isinstance(r.get("closing_line"), dict) else {}
        fcs = [fr.get(i) for i in (r.get("forecast_ids") or []) if i]
        ev = {"decision_file": dec_files.get(r["decision_id"]), "settlement_file": set_files.get(r["decision_id"]), "snapshot_file": snap_files.get(r["snapshot_id"])}
        for k_, f_ in list(ev.items()):
            ev[k_ + "_git_added_utc"] = _git_added(git_repo, git_ref, f_) if f_ else None
        later_horizons = [str(x) for x in path[path["decision"] == "TRADE"]["horizon"]]
        # what the same contract looked like on the latest CONTEMPORANEOUS board that existed when the row was actually computed (descriptive drift check)
        lv = live[(live["ticker"] == r["ticker"]) & (live["side"] == r["side"]) & (live["as_of"] <= pd.Timestamp(r["decided_utc"]))].sort_values("as_of")
        lv = lv.iloc[-1] if len(lv) else None
        rows.append({
            "n": len(rows) + 1, "game_id": r["game_id"], "matchup": f"{r.get('team')} vs {r.get('opponent')}", "tip_utc": r["game_start_utc"],
            "player": r.get("player_name"), "entity_id": r.get("entity_id"), "team": r.get("team"), "family": r["family"], "stat": r["stat"],
            "k": r.get("k"), "strike": r.get("threshold"), "side": r["side"], "terms": human_terms(r), "ticker": r["ticker"], "horizon": r["horizon"],
            "decision_mode": r["decision_mode"], "decision_id": r["decision_id"], "thesis_id": r["thesis_id"],
            "forecast_ids": r.get("forecast_ids"), "model_id": r.get("model_id"), "model_version": r.get("model_version"),
            "forecast_generated_utc": r.get("forecast_generated_utc"), "forecast_archived_utc": [f.get("archived_utc") for f in fcs if f],
            "forecast_file": [f.get("path") for f in fcs if f],
            "board_observed_utc": r["board_observed_utc"], "board_committed_utc": (board_commits or {}).get(r["board_observed_utc"]),
            "board_commit_lag_s": None if not (board_commits or {}).get(r["board_observed_utc"]) else
            (MK.parse_ts(board_commits[r["board_observed_utc"]]) - MK.parse_ts(r["board_observed_utc"])).total_seconds(),
            "as_of_utc": r["as_of_utc"], "decided_utc": r["decided_utc"],
            "computation_lag_s": (MK.parse_ts(r["decided_utc"]) - MK.parse_ts(r["as_of_utc"])).total_seconds(),
            "minutes_to_tip_asof": r["minutes_to_tip"], "minutes_to_tip_decided": round((MK.parse_ts(r["game_start_utc"]) - MK.parse_ts(r["decided_utc"])).total_seconds() / 60, 1),
            "snapshot_gap_s": r.get("snapshot_gap_s"), "quote_age_s": r.get("quote_age_s"),
            "p_model": r["p_model"], "p_cond": r.get("p_cond"), "p_play": r.get("p_play"), "p_market_mid": r.get("p_market_mid") if "p_market_mid" in r else None,
            "price": r["price"], "bid": r.get("bid"), "top_size": r.get("top_size"), "depth_at_entry": r.get("depth_at_entry"), "spread": r.get("spread"),
            "slippage": r.get("slippage"), "effective_entry": r.get("effective_entry"), "fee_per_contract_decision": r.get("fee_per_contract"),
            "fee_paid_settlement": r.get("fee_paid"), "ev_net": r["ev_net"],
            "result_actual": r.get("stat_actual"), "participated": r.get("stat_participated"), "kalshi_result": r.get("kalshi_result"), "dnp": bool(r.get("dnp")),
            "won": r.get("won"), "gross_payoff": r.get("gross_payoff"), "net_pnl": r["net_pnl"],
            "clv_cents": r.get("clv_cents"), "clv_valid": bool(cl.get("valid")), "clv_cause": cl.get("cause"), "clv_close_board_utc": cl.get("board_observed_utc"),
            "clv_close_mid_yes": cl.get("mid_yes"), "clv_source": "archived LAST_VALID snapshot (<= 15 min before tip)" if cl.get("valid") else "none",
            "also_traded_at_horizons": later_horizons,
            "actionability_check": None if lv is None else {
                "latest_contemporaneous_board_before_decided_utc": lv["board_observed_utc"], "ask_then": None if pd.isna(lv["price"]) else float(lv["price"]),
                "top_size_then": None if pd.isna(lv["top_size"]) else float(lv["top_size"]), "ev_net_then": None if pd.isna(lv["ev_net"]) else float(lv["ev_net"]),
                "ask_change_vs_selected": None if pd.isna(lv["price"]) else round(float(lv["price"]) - float(r["price"]), 4)},
            "horizon_path": [{"horizon": p["horizon"], "mode": p["decision_mode"], "as_of": p["as_of_utc"], "decision": p["decision"], "reason": p["reason"],
                              "price": None if pd.isna(p["price"]) else float(p["price"]), "ev_net": None if pd.isna(p["ev_net"]) else float(p["ev_net"])}
                             for p in path.to_dict("records")],
            "selection_reason": f"earliest TRADE of the thesis by (as_of, decision_id) across {len(later_horizons)} traded horizon run(s); best net EV of its thesis at that run; "
                                f"{'; '.join(f'{x} competing row(s) {y}' for y, x in same[same['decision'] == 'PASS']['reason'].value_counts().items()) or 'no competing row at that run'}",
            "fill_evidence": "none: paper decision, no order and no fill; the price is the archived displayed ask plus modelled slippage",
            "contemporaneous_computation_evidence": r["decision_mode"] == "contemporaneous",
            "exposure_after": r.get("exposure"), "archive": ev,
        })
    return pd.DataFrame(rows)


# ================================================================================================ reconciliation + summaries
def reconcile(archive: str, t: pd.DataFrame, day_et: str) -> dict[str, Any]:
    """Recompute net P&L / entry cost / ROI from the table and compare with the archived daily scorecard and with the figures quoted in the issue."""
    p = os.path.join(archive, "paper", "nba", "scorecards", "daily", f"{day_et}.json")
    card = json.load(open(p)) if os.path.exists(p) else None
    ov = None
    if card:
        ov = (((card.get("market") or {}).get("paper") or {}).get("strategies") or {}).get(STRATEGY, {}).get("selected", {}).get("overall_one_per_thesis")
    mine = {"n_decisions": int(len(t)), "n_games": int(t["game_id"].nunique()), "net_pnl": round(float(t["net_pnl"].sum()), 6),
            "entry_cost": round(float(t["price"].sum()), 6), "roi": float(t["net_pnl"].sum() / t["price"].sum())}
    out: dict[str, Any] = {"recomputed": mine, "scorecard_file": os.path.relpath(p, archive) if card else None,
                           "roi_definition": "sum(net_pnl) / sum(quoted ask price); slippage and fees are inside net_pnl, not in the denominator",
                           "entry_cost_incl_slippage": round(float(t["effective_entry"].sum()), 6),
                           "roi_on_cash_outlay": float(t["net_pnl"].sum() / (t["effective_entry"] + t["fee_paid_settlement"].fillna(0)).sum())}
    if ov:
        sc = {"n_decisions": ov["n_decisions"], "n_games": ov["n_games"], "net_pnl": ov["total_net_pnl"], "roi": ov["roi"]}
        out["scorecard"] = sc
        out["matches_scorecard"] = bool(sc["n_decisions"] == mine["n_decisions"] and sc["n_games"] == mine["n_games"]
                                        and abs(sc["net_pnl"] - mine["net_pnl"]) < 1e-9 and abs(sc["roi"] - mine["roi"]) < 1e-9)
    else:
        out["matches_scorecard"] = None
    out["issue_stated"] = ISSUE_STATED
    out["matches_issue_text"] = bool(mine["n_decisions"] == 7 and mine["n_games"] == 2 and abs(mine["net_pnl"] - 1.39) < 1e-6 and abs(mine["entry_cost"] - 3.40) < 1e-6
                                     and abs(mine["roi"] - 0.40882) < 5e-6)
    return out


def summarize(t: pd.DataFrame) -> dict[str, Any]:
    """NO vs YES, family concentration, per-player / per-game structure and what drives the headline."""
    if t.empty:
        return {"status": "NO_DATA"}

    def blk(g: pd.DataFrame) -> dict[str, Any]:
        return {"n": int(len(g)), "wins": int((g["won"] == True).sum()), "net_pnl": round(float(g["net_pnl"].sum()), 4),  # noqa: E712
                "entry_cost": round(float(g["price"].sum()), 4), "roi": round(float(g["net_pnl"].sum() / g["price"].sum()), 5) if g["price"].sum() else None}
    out: dict[str, Any] = {"overall": blk(t), "by_side": {k: blk(g) for k, g in t.groupby("side")}, "by_family": {k: blk(g) for k, g in t.groupby("family")},
                           "by_decision_mode": {k: blk(g) for k, g in t.groupby("decision_mode")}, "by_horizon": {k: blk(g) for k, g in t.groupby("horizon")},
                           "by_game": {k: blk(g) for k, g in t.groupby("game_id")}}
    pg = t.groupby("entity_id")
    out["by_player"] = {str(k): {**blk(g), "player": g["player"].iloc[0], "families": sorted(g["family"])} for k, g in pg}
    out["same_player_pairs"] = {g["player"].iloc[0]: sorted(g["family"]) for _, g in pg if len(g) > 1}
    out["concentration"] = {"share_NO": round(float((t["side"] == "NO").mean()), 4), "share_points_family": round(float(t["family"].isin(["player_points", "player_pra", "player_threes"]).mean()), 4),
                            "n_player_games": int(t["entity_id"].nunique()), "n_games": int(t["game_id"].nunique()),
                            "effective_independent_units_note": "7 theses sit on 5 player-games in 2 games; points, PRA and threes of one player move together, so the number of independent outcomes is closer to 5 player-games, and the game is the cluster"}
    best = t.sort_values("net_pnl", ascending=False).iloc[0]
    out["leave_one_out"] = {"without_largest_winner": {"dropped": f"{best['player']} {best['family']} {best['side']}", "net_pnl": round(float(t['net_pnl'].sum() - best['net_pnl']), 4)},
                            "replay_only_rows": blk(t[t["decision_mode"] == "asof_replay"]) if (t["decision_mode"] == "asof_replay").any() else None,
                            "contemporaneous_only_rows": blk(t[t["decision_mode"] == "contemporaneous"]) if (t["decision_mode"] == "contemporaneous").any() else None}
    out["evidence_gaps"] = {
        "contemporaneous_computation": f"{int((t['decision_mode'] == 'contemporaneous').sum())} of {len(t)} selected rows were computed at the time (decision_mode contemporaneous); "
                                       f"{int((t['decision_mode'] == 'asof_replay').sum())} are as-of replays rebuilt from the capture archive after the fact",
        "computation_lag_s_replay": {"min": float(t[t['decision_mode'] == 'asof_replay']['computation_lag_s'].min()) if (t["decision_mode"] == "asof_replay").any() else None,
                                     "max": float(t[t['decision_mode'] == 'asof_replay']['computation_lag_s'].max()) if (t["decision_mode"] == "asof_replay").any() else None,
                                     "meaning": "seconds between the information cut-off (as_of) and the moment the replay row was actually computed; the price may no longer have been available then"},
        "board_archive_clock": ("capture-branch commit time of the board each row used (independent clock): " + (
            f"{int(t['board_commit_lag_s'].min())}-{int(t['board_commit_lag_s'].max())} s after observation; "
            f"{int((pd.to_datetime(t['board_committed_utc']) > pd.to_datetime(t['decided_utc'])).sum())} of {len(t)} boards were committed AFTER the row was decided"
            if t["board_commit_lag_s"].notna().any() else "NOT_VERIFIED (capture branch history not supplied)")),
        "fills": "no order exists for any of the rows; none of the prices is a recorded fill",
        "multi_horizon_selection": "each thesis is taken at the EARLIEST horizon that traded it; the alternative horizons are alternative runs with separately reset exposure caps"}
    return out


def to_markdown(t: pd.DataFrame, rec: dict, summ: dict, day_et: str) -> str:
    L = [f"# Issue #53 A: exact attribution of the {STRATEGY} selected trades, {day_et}", "",
         "Read-only reconstruction from the immutable `projection-data` archive. Descriptive; **not** evidence of an executable edge (2 games).", "",
         "## Reconciliation", "",
         f"- recomputed: {rec['recomputed']['n_decisions']} decisions, {rec['recomputed']['n_games']} games, net P&L **${rec['recomputed']['net_pnl']:.2f}**, "
         f"entry cost (sum of quoted asks) **${rec['recomputed']['entry_cost']:.2f}**, ROI **{100 * rec['recomputed']['roi']:.3f}%**",
         f"- archived scorecard `{rec.get('scorecard_file')}`: match = **{rec.get('matches_scorecard')}**; issue text (7 / 2 games / $1.39 / $3.40 / 40.882%): match = **{rec['matches_issue_text']}**",
         f"- ROI definition: {rec['roi_definition']}. With slippage in the denominator the entry cost is ${rec['entry_cost_incl_slippage']:.2f}; on cash outlay (entry + fee) ROI is "
         f"{100 * rec['roi_on_cash_outlay']:.2f}%.", "",
         "## The seven selections", "",
         "| # | game | player | contract (plain words) | horizon / mode | as_of -> decided (lag) | p_model | p_play | ask | size | spread | fee/slip | EV net | result | net P&L | CLV |",
         "|--:|---|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|---|--:|---|"]
    for r in t.to_dict("records"):
        res = f"{'WIN' if r['won'] else 'LOSS'} (actual {r['result_actual']})" if r["won"] is not None and not pd.isna(r["won"]) else "?"
        clv = f"{r['clv_cents']:+.1f}c ({'valid' if r['clv_valid'] else r['clv_cause']})" if r["clv_cents"] is not None and not pd.isna(r["clv_cents"]) else "n/a"
        L.append(f"| {r['n']} | {r['game_id'][-3:]} {r['matchup']} | {r['player']} | {r['terms']} | {r['horizon']} / **{r['decision_mode']}** | "
                 f"{r['as_of_utc'][11:19]} -> {r['decided_utc'][11:19]} ({r['computation_lag_s'] / 60:.0f} min) | {r['p_model']:.3f} | {r['p_play']:.3f} | {r['price']:.2f} | "
                 f"{r['top_size']:.0f} | {r['spread']:.2f} | {r['fee_paid_settlement']:.2f}/{r['slippage']:.2f} | {r['ev_net']:.3f} | {res} | {r['net_pnl']:+.2f} | {clv} |")
    L += ["", "Archive evidence per row (paths relative to `projection-data`): decision, settlement, market snapshot, forecast file; `*_git_added_utc` = commit time on the data branch.", ""]
    for r in t.to_dict("records"):
        a = r["archive"]
        L.append(f"- #{r['n']} `{r['ticker']}` {r['side']}: decision `{a.get('decision_file')}` ({a.get('decision_file_git_added_utc')}), snapshot `{a.get('snapshot_file')}` "
                 f"({a.get('snapshot_file_git_added_utc')}; board observed {r['board_observed_utc']}, committed to the capture branch {r.get('board_committed_utc')}), forecast generated {r['forecast_generated_utc']} archived {r['forecast_archived_utc']} "
                 f"in `{r['forecast_file']}` ({r['model_id']} {r['model_version']}), settlement `{a.get('settlement_file')}`; also traded at {r['also_traded_at_horizons']}")
    s = summ
    L += ["", "## Structure", "",
          f"- side: {json.dumps(s['by_side'])}", f"- family: {json.dumps(s['by_family'])}", f"- decision mode: {json.dumps(s['by_decision_mode'])}",
          f"- by game: {json.dumps(s['by_game'])}", f"- same-player pairs (one outcome, two contracts): {json.dumps(s['same_player_pairs'])}",
          f"- leave-one-out: {json.dumps(s['leave_one_out'])}", "", "## What is missing", ""]
    for k, v in s["evidence_gaps"].items():
        L.append(f"- **{k}**: {v if isinstance(v, str) else json.dumps(v)}")
    L += ["", f"Concentration: {s['concentration']['effective_independent_units_note']}.", ""]
    return "\n".join(L)


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, pd.Timestamp):
        return o.isoformat()
    return o


def table_records(t: pd.DataFrame) -> list[dict]:
    return _clean(t.to_dict("records"))


__all__ = ["attribute", "reconcile", "summarize", "to_markdown", "human_terms", "first_trade_per_thesis", "table_records", "ISSUE_STATED", "S", "ST"]
