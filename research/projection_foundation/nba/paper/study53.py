"""Issue #53 research run: attribution (A) + executable T-60 shadow portfolio (B) + matched JRM counterfactual (C) + the three-way table.

    python -m nba.paper.study53 --archive <projection-data checkout> --msa <minutes-shadow-archive checkout> --out <dir> \
        [--attribution-day 2026-10-20] [--projection-ref <sha>] [--msa-ref <sha>] [--git-repo <repo with projection-data fetched>]

READ-ONLY and OFFLINE. Writes only under --out (default research/projection_foundation/results/issue53/): attribution_<day>.{json,md},
exec_shadow.json, jrm_matched.json, SUMMARY.md, manifest.json. It never writes to either data branch, never calls a network, never starts a
workflow, places no order and changes no authority. The output is a pure function of the archives (no wall-clock fields), so re-running on
the same inputs reproduces the files byte for byte (`run_id` = digest of the inputs).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from . import attribution as A
from . import config as CFG
from . import evaluate as E
from . import exec_shadow as X
from . import jrm_matched as J
from . import markets as MK

AUTHORITY = "research_only"
OUT_DEFAULT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "results", "issue53"))


def inputs_digest(archive: str, msa: str | None, study: dict) -> str:
    h = hashlib.sha256()
    for sub in ("paper/nba/decisions", "paper/nba/settlements", "paper/nba/corrections", "market_snapshots/nba", "forecasts/nba", "game_forecasts/nba", "outcomes/nba", "settlements/nba"):
        base = os.path.join(archive, sub)
        for root, _, files in sorted(os.walk(base)):
            for fn in sorted(files):
                p = os.path.join(root, fn)
                h.update(os.path.relpath(p, archive).encode())
                with open(p, "rb") as f:
                    h.update(hashlib.sha256(f.read()).digest())
    if msa:
        reg = os.path.join(msa, "eligibility", "REGISTER.jsonl")
        if os.path.exists(reg):
            h.update(open(reg, "rb").read())
    h.update(X.study_sha().encode())
    h.update(CFG.config_sha().encode())
    return h.hexdigest()[:16]


def _num(x):
    return A._clean(x)


def three_way(attr_summary: dict, exec_all: dict, jrm_block: dict) -> dict[str, Any]:
    """The three separately labelled sets of the acceptance criteria. All RETROSPECTIVE/DESCRIPTIVE unless a prospective count is shown."""
    def exec_row(m: dict) -> dict:
        if not m or m.get("status") not in ("OK",):
            return {"status": (m or {}).get("status", "NO_DATA")}
        o = m["overall"]
        return {"n_decisions": o["n_trades"], "n_games": o["n_games"], "net_pnl": o["total_net_pnl"], "roi_on_cash_outlay": o["roi_on_cash_outlay"], "hit_rate": o["hit_rate"]}
    if attr_summary.get("status") == "NO_DATA":
        first = {"label": "PF_EDGE_STRICT_V1 earliest TRADE per thesis across horizons", "status": "NO_DATA", "reason": attr_summary.get("reason")}
    else:
        nr = attr_summary["by_decision_mode"].get("asof_replay", {}).get("n", 0)
        first = {"label": f"PF_EDGE_STRICT_V1 earliest TRADE per thesis across horizons (NOT simultaneously executable; {nr} of {attr_summary['overall']['n']} are as-of replays)",
                 **{k: attr_summary["overall"][k] for k in ("n", "net_pnl", "entry_cost", "roi")}, "roi_basis": "net P&L / sum of quoted asks (scorecard definition)"}
    return {
        "1_original_frozen_strategy_selection": first,
        "2_new_fixed_checkpoint_executable_shadow": {"label": "PF_EDGE_STRICT_T60_EXEC_V1, T-60 only, global ledger, displayed size, integer fee (RETROSPECTIVE application of the frozen rules; not prospective evidence)",
                                                      **exec_row(exec_all)},
        "3_eligible_matched_jrm_whatif": jrm_block.get("headline", {"status": "NO_DATA"})}


def build_clocks(archive: str, git_repo: str | None, board_ref: str, forecast_ref: str) -> tuple[dict | None, dict]:
    """Independent archive clocks (git commit times of the capture and forecast files). None when the repo / refs are not available: nothing is then verified."""
    if not git_repo:
        return None, {"status": "NOT_VERIFIED", "reason": "no --git-repo given"}
    try:
        bc = X.board_commit_index(git_repo, board_ref)
        fc = X.forecast_commit_index(archive, git_repo, forecast_ref)
    except Exception as e:  # noqa: BLE001
        return None, {"status": "NOT_VERIFIED", "reason": f"{type(e).__name__}: {str(e)[:160]}"}
    return {"board_commit": bc, "forecast_commit": fc}, {"status": "VERIFIED", "board_ref": board_ref, "forecast_ref": forecast_ref, "board_ticks_indexed": len(bc),
                                                         "board_ticks_earliest": min(bc) if bc else None, "forecast_ids_indexed": len(fc)}


def run(archive: str, msa: str | None, out: str, attribution_day: str = "2026-10-20", *, git_repo: str | None = None, projection_ref: str | None = None,
        msa_ref: str | None = None, now: datetime | None = None, board_ref: str = "origin/data-archive", forecast_ref: str = "origin/projection-data") -> dict[str, Any]:
    os.makedirs(out, exist_ok=True)
    study, base = X.load_study(), CFG.load()
    ok, why = X.base_protocol_ok(study)
    if not ok:
        raise SystemExit(f"base protocol changed: {why}")
    now = now or datetime(2099, 1, 1, tzinfo=timezone.utc)
    run_id = inputs_digest(archive, msa, study)
    D = E.load(archive, now, window=None, prospective_only=True)
    fa = X.forecast_archive_index(archive)

    clocks, clock_info = build_clocks(archive, git_repo, board_ref, forecast_ref)
    # ---------------------------------------------------------------- A
    t = A.attribute(archive, attribution_day, now, git_repo=git_repo, board_commits=(clocks or {}).get("board_commit"))
    rec = A.reconcile(archive, t, attribution_day)
    summ = A.summarize(t)
    with open(os.path.join(out, f"attribution_{attribution_day}.json"), "w") as f:
        json.dump(_num({"schema": "issue53.attribution.v1", "authority": AUTHORITY, "run_id": run_id, "day_et": attribution_day, "strategy": A.STRATEGY,
                        "reconciliation": rec, "summary": summ, "table": A.table_records(t)}), f, indent=1, sort_keys=True)
    with open(os.path.join(out, f"attribution_{attribution_day}.md"), "w") as f:
        f.write(A.to_markdown(t, rec, summ, attribution_day))

    # ---------------------------------------------------------------- B
    prepared = X.load_candidates(D, study, base, fa)
    v1 = X.select([dict(c) for c in prepared], study, base, forecast_archive=fa, prepared=True, clocks=clocks)
    v1_unverified = X.select([dict(c) for c in prepared], study, base, forecast_archive=fa, prepared=True, clocks=None) if clocks else None
    pops = X.split_populations(v1)
    B: dict[str, Any] = {"schema": "issue53.exec_shadow.v1", "authority": AUTHORITY, "run_id": run_id, "study_id": study["study_id"], "strategy_id": X.STRATEGY,
                         "study_config_sha256": X.study_sha(), "base_protocol": {"sha256": study["base_protocol"]["sha256"], "ok": ok, "detail": why},
                         "prospective_start_utc": study["prospective_start_utc"], "declared_utc": study["declared_utc"], "data_integrity": _num(D.quality),
                         "independent_clocks": clock_info}
    cv = clocks is not None
    B["prospective"] = X.portfolio_metrics(pops["prospective"], study, label="prospective", clocks_verified=cv) if pops["prospective"] else {"status": "NO_DATA", "reason": f"no decision instants at or after {study['prospective_start_utc']} in the archive yet", "label": "prospective"}
    B["retrospective_descriptive"] = X.portfolio_metrics(pops["retrospective_descriptive"], study, label="retrospective_descriptive", clocks_verified=cv)
    if v1_unverified is not None:
        B["comparator_retrospective_without_independent_clocks"] = X.portfolio_metrics(X.split_populations(v1_unverified)["retrospective_descriptive"], study,
                                                                                         label="retrospective_descriptive_no_clock_check", clocks_verified=False)
        B["comparator_retrospective_without_independent_clocks"]["note"] = ("same rules WITHOUT requiring the board / forecast to have been committed to the data branches before "
                                                                           "the checkpoint: shows what the independent-clock rule removes")
    tr = X._frame(pops["retrospective_descriptive"])
    tr = tr[tr["decision"] == "TRADE"] if len(tr) else tr
    B["retrospective_descriptive"]["opening_hour_effect"] = X.opening_hour_effect(tr, D.snaps)
    B["games"] = X.game_status(v1, D, study)
    B["contemporaneous_crosscheck"] = X.crosscheck_contemporaneous(D, study, base, fa, v1)
    B["board_archive_lag_s"] = _num(board_lag(v1))
    B["contemporaneous_runs_by_game"] = _num(X.contemporaneous_runs(D, study).to_dict("records"))
    B["trades"] = _num([{k: c.get(k) for k in ("game_id", "player_name", "family", "k", "side", "ticker", "price", "effective_entry_exec", "fee_int", "top_size", "spread", "p_model", "p_play",
                                                "ev_net_exec", "quote_age_at_checkpoint_s", "computation_lag_s", "decision_mode", "prospective", "won", "net_pnl", "clv_cents", "exposure_after",
                                                "board_commit_utc", "forecast_commit_utc")}
                        for c in v1 if c["decision"] == "TRADE"])
    B["no_trade_examples"] = _num(no_trade_examples(v1))
    B["progress_to_evidence_minimums"] = {"prospective_decisions": int(sum(1 for c in pops["prospective"] if c["decision"] == "TRADE")),
                                          "prospective_games": int(len({c["game_id"] for c in pops["prospective"] if c["decision"] == "TRADE"})),
                                          "required_decisions": study["evidence"]["min_decisions"], "required_games": study["evidence"]["min_games"],
                                          "retrospective_rows_never_counted": True}
    with open(os.path.join(out, "exec_shadow.json"), "w") as f:
        json.dump(_num(B), f, indent=1, sort_keys=True)

    # ---------------------------------------------------------------- C
    C: dict[str, Any] = {"schema": "issue53.jrm_matched.v1", "authority": AUTHORITY, "run_id": run_id, "downstream": J.LABEL, "label": "RETROSPECTIVE unless prospective gate reached"}
    if not msa:
        C.update({"status": "NO_DATA", "reason": "minutes-shadow-archive checkout not provided"})
        jrm_headline = {"status": "NO_DATA"}
    else:
        snaps, rejected = J.load_snapshots(msa)
        C["snapshots_usable"] = [{"file": s.file, "archived_utc": s.archived_utc, "branch_commit_utc": s.branch_commit_utc, "feed_generated_utc": s.feed_generated_utc,
                                   "games": sorted({g for g, _ in s.rows}), "sha256_verified": s.sha_ok} for s in snaps]
        C["snapshots_rejected"] = rejected
        # the matched population: T-60 candidate rows of the games with a matched eligible snapshot
        vj, mledger = J.build_variant([dict(c) for c in prepared], snaps, J.forecast_pmfs(archive, {(c.get("forecast_ids") or [None])[0] for c in prepared if c.get("forecast_ids")} - {None}), study, base)
        matched_games = {g for g, v in mledger["games"].items() if v["snapshot"]}
        C["matching"] = {"games": mledger["games"], "row_status": mledger["rows"], "matched_games": sorted(matched_games)}
        sub_v1 = [dict(c) for c in prepared if c["game_id"] in matched_games]
        sub_j = [c for c in vj if c["game_id"] in matched_games]
        if not sub_v1:
            C.update({"status": "NO_DATA", "reason": "no game has an eligible, same-feed JRM snapshot archived before its T-60 decision"})
            jrm_headline = {"status": "NO_DATA", "reason": C["reason"]}
        else:
            s1 = X.select(sub_v1, study, base, forecast_archive=fa, prepared=True, clocks=clocks)
            s2 = X.select(sub_j, study, base, strategy_id="PF_EDGE_STRICT_T60_EXEC_JRM_V1", forecast_archive=fa, prepared=True, clocks=clocks)
            pr = J.pair_decisions(s1, s2)["frame"]
            C["status"] = "OK"
            C["population"] = {"matched_games": sorted(matched_games), "n_games": len(matched_games), "candidate_sides": int(len(pr)),
                               "note": "both portfolios rebuilt on the SAME candidate rows with fresh single ledgers; V1 on the full archive is in exec_shadow.json"}
            C["v1_on_matched_games"] = X.portfolio_metrics(s1, study, label="v1_matched_games", clocks_verified=cv)
            C["jrm_on_matched_games"] = X.portfolio_metrics(s2, study, label="jrm_matched_games", clocks_verified=cv)
            C["paired"] = J.summarize_pairs(pr)
            C["star_unders"] = J.star_under_diagnostic(pr)
            C["stat_family_accuracy"] = J.stat_family_accuracy(pr)
            # forecast accuracy on the registered snapshot used per game, against settled outcomes
            by_game = {g: next(s for s in snaps if s.file == v["snapshot"]) for g, v in mledger["games"].items() if v["snapshot"]}
            C["minutes_accuracy"] = J.minutes_accuracy(by_game, _actuals(D))
            C["pairs"] = _num(pr[pr["class"] != "neither"].to_dict("records"))
            jrm_headline = {"label": "PF_EDGE_STRICT_T60_EXEC_JRM_V1 vs V1 on the same candidate rows (archive_scale_approximation; RETROSPECTIVE)",
                            "matched_games": len(matched_games), "decision_matrix": C["paired"]["decision_matrix_candidate_sides"],
                            "v1_net_pnl": (C["v1_on_matched_games"].get("overall") or {}).get("total_net_pnl"),
                            "jrm_net_pnl": (C["jrm_on_matched_games"].get("overall") or {}).get("total_net_pnl"),
                            "status": "OK"}
        C["original_seven_coverage"] = _num(original_seven_jrm(t, snaps, archive, base, study))
        settled_games = set(D.settle["game_id"].unique()) if len(D.settle) else set()
        C["prospective_gate"] = J.gate_status(snaps, settled_games, study)
    with open(os.path.join(out, "jrm_matched.json"), "w") as f:
        json.dump(_num(C), f, indent=1, sort_keys=True)

    # ---------------------------------------------------------------- summary + manifest
    tw = three_way(summ, B["retrospective_descriptive"], {"headline": jrm_headline})
    md = summary_markdown(study, rec, summ, B, C, tw, attribution_day, run_id, t)
    with open(os.path.join(out, "SUMMARY.md"), "w") as f:
        f.write(md)
    man = {"schema": "issue53.manifest.v1", "authority": AUTHORITY, "run_id": run_id, "study_config_sha256": X.study_sha(), "paper_config_sha256": CFG.config_sha(),
           "inputs": {"projection_data_ref": projection_ref, "minutes_shadow_archive_ref": msa_ref}, "outputs": sorted(os.listdir(out)),
           "read_only": True, "network": False, "orders_placed": 0, "workflows_dispatched": 0, "three_way": _num(tw)}
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(man, f, indent=1, sort_keys=True)
    return man


def _actuals(D) -> pd.DataFrame:
    s = D.settle
    if s is None or s.empty:
        return pd.DataFrame(columns=["game_id", "entity_id", "played", "minutes"])
    m = s[(s["model_role"] == "challenger") & (s["family"] == "minutes")]
    return pd.DataFrame({"game_id": m["game_id"], "entity_id": m["entity_id"], "played": ~m["void"].astype(bool), "minutes": m["actual"].where(~m["void"].astype(bool))}).drop_duplicates(["game_id", "entity_id"])


def board_lag(cs: list[dict]) -> dict[str, Any]:
    """Seconds between a board's observation and its commit to the capture branch, for the boards the checkpoint decisions used (per game)."""
    out: dict[str, Any] = {}
    for c in cs:
        if c.get("board_commit_utc") and c["game_id"] not in out and c.get("board"):
            out[c["game_id"]] = {"board_observed_utc": MK.iso(c["board"]), "board_committed_utc": c["board_commit_utc"], "checkpoint_utc": MK.iso(c["checkpoint"]),
                                 "lag_s": (MK.parse_ts(c["board_commit_utc"]) - c["board"]).total_seconds(),
                                 "committed_after_checkpoint": MK.parse_ts(c["board_commit_utc"]) > c["checkpoint"]}
    return out


def no_trade_examples(cs: list[dict], per_reason: int = 2, cap: int = 14) -> list[dict]:
    """Examples of NO_TRADE: the largest nominal edges (V1 ev_net >= 0.06) that did not trade, up to `per_reason` for each distinct primary reason."""
    blocked = [c for c in cs if c["decision"] != "TRADE" and c.get("ev_net") is not None and c["ev_net"] >= 0.06 and c["reason"] != "NOT_BEST_IN_THESIS"]
    blocked.sort(key=lambda c: -c["ev_net"])
    seen: Counter = Counter()
    out = []
    for c in blocked:
        why = (c["reason"] or "ELIGIBLE_NOT_SELECTED").split(":")[0] + (":" + c["reason"].split(":")[1] if (c["reason"] or "").startswith("EXPOSURE") else "")
        if seen[why] >= per_reason or len(out) >= cap:
            continue
        seen[why] += 1
        out.append({"game_id": c["game_id"], "player": c.get("player_name"), "family": c["family"], "k": c.get("k"), "side": c["side"], "price": c.get("price"),
                    "ev_net_v1_basis": c.get("ev_net"), "ev_net_exec": c.get("ev_net_exec"), "top_size": c.get("top_size"), "spread": c.get("spread"),
                    "decision": "NO_TRADE", "primary_reason": c["reason"], "all_blockers": c["blockers"]})
    return out


def original_seven_jrm(t: pd.DataFrame, snaps: list[J.Snapshot], archive: str, base: dict, study: dict) -> list[dict]:
    """For each of the seven original selections: was an eligible same-feed JRM snapshot available at ITS decision instant, and would JRM still pass the strict rules?"""
    if t.empty:
        return []
    out = []
    ids = {i for fids in t["forecast_ids"] for i in (fids or [])[:1] if i}
    pm = J.forecast_pmfs(archive, ids)
    for r in t.to_dict("records"):
        tip, asof = MK.parse_ts(r["tip_utc"]), MK.parse_ts(r["as_of_utc"])
        snap, why = J.match_snapshot(snaps, r["game_id"], tip, asof, r["forecast_generated_utc"])
        row = {"n": r["n"], "game_id": r["game_id"], "player": r["player"], "contract": r["terms"], "horizon": r["horizon"], "snapshot": snap.file if snap else None, "match": why}
        if snap:
            pr_ = snap.rows.get((r["game_id"], r["entity_id"]))
            rec = pm.get((r["forecast_ids"] or [None])[0])
            cdict = {"p_play": r["p_play"], "k": r["k"], "side": r["side"], "p_market_mid": r.get("p_market_mid"), "p_model": r["p_model"]}
            pj = J.jrm_probabilities(cdict, pr_, rec) if pr_ and rec else None
            if pj:
                eff, fee = r["effective_entry"], r["fee_paid_settlement"]
                ev_j = pj["p_model_jrm"] - eff - fee
                row.update({"minutes_frozen": pj["minutes_frozen"], "minutes_jrm": pj["minutes_jrm"], "p_play_frozen": pj["p_play_frozen"], "p_play_jrm": pj["p_play_jrm"],
                            "p_model_frozen": r["p_model"], "p_model_jrm": pj["p_model_jrm"], "ev_net_exec_frozen": r["p_model"] - eff - fee, "ev_net_exec_jrm": ev_j,
                            "jrm_would_pass_ev_0.06": bool(ev_j >= study["strategies"][X.STRATEGY]["min_ev_net"]),
                            "rebuild_check_p_model": pj["p_model_frozen_rebuilt"], "note": "retrospective what-if on the original T-90 / LIVE selection, archive_scale_approximation"})
            else:
                row["note"] = "matched snapshot lacks the player, the DNP-leg mid is unavailable, or the rebuilt frozen probability differs from the archived one: no what-if"
        out.append(row)
    return out


def summary_markdown(study: dict, rec: dict, summ: dict, B: dict, C: dict, tw: dict, day: str, run_id: str, t: pd.DataFrame) -> str:
    L = [f"# Issue #53 research summary (run `{run_id}`)", "",
         "**Research only. No orders, no wagering authority, no deployment, no model activation.** Everything below that precedes "
         f"`prospective_start_utc` = {study['prospective_start_utc']} is RETROSPECTIVE and DESCRIPTIVE; a handful of games is not evidence of an edge.", "",
         "## 1. The original strict-strategy selections, reconciled"]
    if summ.get("status") == "NO_DATA":
        L.append(f"- **NO_DATA**: {summ.get('reason')}")
        return "\n".join(L + _summary_tail(study, B, C, tw))
    L.append(f"- recomputed {rec['recomputed']['n_decisions']} decisions in {rec['recomputed']['n_games']} games: net P&L ${rec['recomputed']['net_pnl']:.2f} on ${rec['recomputed']['entry_cost']:.2f} of quoted asks = "
             f"{100 * rec['recomputed']['roi']:.3f}% (matches the archived scorecard: {rec.get('matches_scorecard')}; matches the issue text: {rec['matches_issue_text']}).")
    n_all = summ["overall"]["n"]
    modes = summ["by_decision_mode"]
    L.append("- decision mode: " + ", ".join(f"{v['n']} of {n_all} {k} (P&L ${v['net_pnl']:.2f})" for k, v in modes.items()) + "; none has a recorded fill.")
    lag = summ["evidence_gaps"]["computation_lag_s_replay"]
    if lag["min"] is not None:
        L.append(f"- the as-of replays were computed {lag['min'] / 60:.0f}-{lag['max'] / 60:.0f} minutes after the price they use (the price may no longer have been available).")
    L.append(f"- NO {summ['by_side'].get('NO', {}).get('n', 0)} (P&L ${summ['by_side'].get('NO', {}).get('net_pnl', 0):.2f}) vs YES {summ['by_side'].get('YES', {}).get('n', 0)} "
             f"(P&L ${summ['by_side'].get('YES', {}).get('net_pnl', 0):.2f}); families {', '.join(sorted(summ['by_family']))}; "
             f"{summ['concentration']['n_player_games']} player-games in {summ['concentration']['n_games']} games"
             + (f"; players with two contracts (one outcome, two bets): {', '.join(summ['same_player_pairs'])}" if summ["same_player_pairs"] else "")
             + f"; without the largest winner net P&L is ${summ['leave_one_out']['without_largest_winner']['net_pnl']:.2f}.")
    act = [r for r in A.table_records(t) if r.get("actionability_check")]
    if act:
        L.append("- actionability check (latest contemporaneous board before each replay row was computed): " + "; ".join(
            f"#{r['n']} {r['player'].split()[-1]} ask {r['actionability_check']['ask_then']} vs selected {r['price']}" for r in act if r["decision_mode"] == "asof_replay") + ".")
    L.append("")
    return "\n".join(L + _summary_tail(study, B, C, tw))


def _summary_tail(study: dict, B: dict, C: dict, tw: dict) -> list[str]:
    L: list[str] = []
    L += ["## 2. Executable fixed-checkpoint portfolio (T-60, global ledger)"]
    pro = B["prospective"]
    rt = B["retrospective_descriptive"]
    L.append(f"- prospective: **{pro.get('status')}**" + (f" - {pro['reason']}" if pro.get("reason") else "") if pro.get("status") != "OK" else f"- prospective: {json.dumps(pro.get('overall'))}")
    rt = B["retrospective_descriptive"]
    if rt.get("status") == "OK":
        o = rt["overall"]
        pct = lambda x: "n/a" if x is None else f"{100 * x:.1f}%"  # noqa: E731
        usd = "n/a (no settled trade)" if o["total_net_pnl"] is None else f"${o['total_net_pnl']:.2f}"
        L.append(f"- retrospective application of the frozen rules: {o['n_trades']} trades in {o['n_games']} games ({o['n_settled']} settled), net P&L {usd}, "
                 f"ROI on cash outlay {pct(o['roi_on_cash_outlay'])}, hit rate {pct(o['hit_rate'])}"
                 + ("; no interval is defined (< 5 games)." if o["n_games"] < 5 else "."))
    elif rt.get("status") in ("NO_DATA", "NO_TRADES"):
        L.append(f"- retrospective: **{rt['status']}** - {rt.get('reason')}")
    if rt.get("eligible_vs_blocked"):
        ev = rt["eligible_vs_blocked"]
        L.append(f"- candidate sides {ev['candidate_sides']}: eligible {ev['eligible_sides']}, blocked {ev['blocked_sides']}; primary reasons {json.dumps(ev['primary_block_reason'])}")
    cmp_ = B.get("comparator_retrospective_without_independent_clocks")
    if cmp_ and cmp_.get("status") == "OK":
        o2 = cmp_["overall"]
        pnl2 = "n/a" if o2["total_net_pnl"] is None else f"${o2['total_net_pnl']:.2f}"
        L.append(f"- the same rules WITHOUT the independent-clock requirement would trade {o2['n_trades']} in {o2['n_games']} games (net P&L {pnl2}); the difference is boards "
                 "committed to the capture branch only after the checkpoint (lag per game: "
                 + ", ".join(f"{g[-3:]} {v['lag_s']:.0f}s{' AFTER' if v['committed_after_checkpoint'] else ''}" for g, v in B.get("board_archive_lag_s", {}).items()) + ").")
    L.append(f"- independent clocks: {json.dumps(B['independent_clocks'])}")
    L.append("- games: " + ", ".join(f"{g['game_id'][-3:]}={g['status']}" for g in B["games"]))
    pg = B["progress_to_evidence_minimums"]
    L.append(f"- progress to the evidence minimum: {pg['prospective_decisions']}/{pg['required_decisions']} prospective decisions, {pg['prospective_games']}/{pg['required_games']} games (retrospective rows never count).")
    L += ["", "## 3. Matched JRM what-if"]
    if C.get("status") != "OK":
        L.append(f"- **{C.get('status')}**: {C.get('reason')}")
    else:
        pm = C["paired"]
        L.append(f"- matched games: {C['population']['n_games']}; decision matrix over candidate sides: {json.dumps(pm['decision_matrix_candidate_sides'])}; downstream = {J.LABEL}.")
    gt = C.get("prospective_gate")
    if gt:
        L.append(f"- JRM prospective gate (tracked separately, verdict owned by PR #45): {gt['eligible_settled_games']}/{gt['min_settled_games']} eligible settled games -> **{gt['status']}**.")
    L += ["", "## 4. Three-way table (separately labelled)", "", "```json", json.dumps(_num(tw), indent=1, sort_keys=True), "```", "",
          "Full detail: `attribution_*.md`, `exec_shadow.json`, `jrm_matched.json`. Outstanding risks are listed in `docs/research/ISSUE53_EXEC_SHADOW.md`.", ""]
    return L


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--archive", required=True, help="projection-data checkout (read-only)")
    ap.add_argument("--msa", default=None, help="minutes-shadow-archive checkout (read-only)")
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--attribution-day", default="2026-10-20")
    ap.add_argument("--git-repo", default=None, help="repo with the projection-data branch fetched (for git-added timestamps)")
    ap.add_argument("--board-ref", default="origin/data-archive", help="git ref of the capture branch inside --git-repo (independent board archive clock)")
    ap.add_argument("--forecast-ref", default="origin/projection-data", help="git ref of the projection-data branch inside --git-repo (independent forecast archive clock)")
    ap.add_argument("--projection-ref", default=None)
    ap.add_argument("--msa-ref", default=None)
    a = ap.parse_args(argv)
    man = run(a.archive, a.msa, a.out, a.attribution_day, git_repo=a.git_repo, projection_ref=a.projection_ref, msa_ref=a.msa_ref,
              board_ref=a.board_ref, forecast_ref=a.forecast_ref)
    print(json.dumps({"run_id": man["run_id"], "outputs": man["outputs"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
