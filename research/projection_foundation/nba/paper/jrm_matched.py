"""Frozen-vs-JRM matched counterfactual on the executable T-60 portfolio (Issue #53, part C; read-only, RESEARCH ONLY).

Reuses, does not fork, PR #45: the registered, ELIGIBLE pre-tip snapshots of `minutes-shadow-archive` (eligibility/REGISTER.jsonl, produced by
minutes_rebuild/archive_rules.py F1-F5) are the only JRM inputs ever read. The register's verdict is the eligibility verdict; this module adds
only the per-decision checks that are about THIS study (sha256 of the bytes, both clocks before the decision instant and before tip - 5 min,
same feed as the frozen decision). Anything else is rejected with a reason and counted: jrm_v1/ and jrm_v2/ (variance-weighted variant), files
without a register row, late / post-tip files, edited files, unversioned snapshots, snapshots of another feed.

Matched means: same contract, side, price, size, entry time, costs, filters and exposure order as `PF_EDGE_STRICT_T60_EXEC_V1`; only the player's
participation probability and conditional stat probabilities change, from the JRM snapshot:

    r        = minutes_given_play_jrm / frozen_published.minutes_given_play_after_gate        (the frozen forecast of the SAME feed)
    p_yes'   = P(X >= k / r)   from the archived frozen pmf   (probability.p_ge(scale=r): the paper engine's own mean-scale convention)
    p_play'  = p_play_jrm
    p_model' = p_play' * p_side' + (1 - p_play') * m_side                                    (identical DNP-leg valuation)

This is an ARCHIVE-ONLY approximation of the downstream projection: per-minute rates, usage redistribution to teammates and the participation
gate are not re-estimated (that needs the live feature store and `PF_NBA_MINUTES_ENGINE=jrm` through project_slate). Every output carries the
label `downstream = archive_scale_approximation`. Game-level contracts are unchanged by construction. Historical use is RETROSPECTIVE.
"""
from __future__ import annotations

import glob
import gzip
import hashlib
import json
import math
import os
from collections import Counter
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

import numpy as np
import pandas as pd

from . import markets as MK
from . import probability as PR
from . import stats as ST

MARGIN = timedelta(minutes=5)                 # PR #45 archive_rules.MARGIN
V2_FREEZE = "f000f3c18b670ab94e3b71e403dda03bc0e5188a"
LABEL = "archive_scale_approximation"
REJECT_CODES = ("NO_REGISTER_ROW", "REGISTER_NOT_ELIGIBLE", "GAME_NOT_ELIGIBLE", "SHA_MISMATCH", "NOT_V2_UNIFORM", "ARCHIVED_AFTER_DECISION",
                "BRANCH_COMMIT_AFTER_DECISION", "TOO_CLOSE_TO_DECISION", "TOO_CLOSE_TO_TIP", "FEED_MISMATCH", "NO_SNAPSHOT_FOR_GAME", "PLAYER_NOT_IN_SNAPSHOT",
                "FROZEN_INPUT_MISMATCH", "ROW_INVALID", "ROW_NOT_PREGAME")


# ================================================================================================ register + snapshots
@dataclass
class Snapshot:
    file: str
    archived_utc: str
    branch_commit_utc: str | None
    feed_generated_utc: str
    sha_ok: bool
    register: dict
    doc: dict = field(repr=False, default_factory=dict)
    rows: dict = field(repr=False, default_factory=dict)       # (game_id, player_id) -> row


def read_register(msa_dir: str) -> dict[str, dict]:
    reg: dict[str, dict] = {}
    p = os.path.join(msa_dir, "eligibility", "REGISTER.jsonl")
    if os.path.exists(p):
        for line in open(p):
            if line.strip():
                r = json.loads(line)
                reg[r["file"]] = r          # a later audit of the same file supersedes an earlier row
    return reg


def load_snapshots(msa_dir: str) -> tuple[list[Snapshot], list[dict]]:
    """(usable snapshots, rejected files with reasons). 'usable' = register eligible AND the bytes match the registered sha256 AND v2 uniform."""
    reg = read_register(msa_dir)
    good: list[Snapshot] = []
    rejected: list[dict] = []
    files = sorted(glob.glob(os.path.join(msa_dir, "jrm_v*", "*.json.gz")))
    for p in files:
        rel = os.path.relpath(p, msa_dir)
        r = reg.get(rel)
        if r is None:
            rejected.append({"file": rel, "reason": "NO_REGISTER_ROW"})
            continue
        if not r.get("eligible_for_prospective_scoring"):
            rejected.append({"file": rel, "reason": "REGISTER_NOT_ELIGIBLE", "detail": r.get("reasons")})
            continue
        data = open(p, "rb").read()
        if hashlib.sha256(data).hexdigest() != r.get("sha256"):
            rejected.append({"file": rel, "reason": "SHA_MISMATCH"})
            continue
        doc = json.loads(gzip.decompress(data))
        if doc.get("version") != "v2" or not str(doc.get("allocation", "")).startswith("uniform") or doc.get("design_frozen_at") != V2_FREEZE:
            rejected.append({"file": rel, "reason": "NOT_V2_UNIFORM"})
            continue
        s = Snapshot(file=rel, archived_utc=doc["archived_utc"], branch_commit_utc=r.get("branch_commit_utc"), feed_generated_utc=doc["feed_generated_utc"],
                     sha_ok=True, register=r, doc=doc)
        elig_games = set(r.get("games_eligible") or [])
        for row in doc["rows"]:
            if row["game_id"] in elig_games:
                s.rows[(row["game_id"], row["player_id"])] = row
        good.append(s)
    return good, rejected


def row_valid(row: dict) -> bool:
    try:
        return (0 <= row["p_play_jrm"] <= 1 and 0 <= row["eligible_prob"] <= 1 and math.isfinite(row["minutes_given_play_jrm"]) and row["minutes_given_play_jrm"] >= 0
                and math.isfinite(row["expected_minutes_unconditional_jrm"]) and row["expected_minutes_unconditional_jrm"] >= 0)
    except (KeyError, TypeError):
        return False


def match_snapshot(snaps: list[Snapshot], game_id: str, tip, info_cutoff, frozen_feed_utc: str | None) -> tuple[Snapshot | None, str]:
    """The newest eligible snapshot of the game that existed (BOTH clocks) before the decision's information cut-off and tip - 5 min, from the
    SAME feed as the frozen decision. Returns (snapshot, "OK") or (None, reason)."""
    cands = [s for s in snaps if any(g == game_id for g, _ in s.rows)]
    if not cands:
        return None, "NO_SNAPSHOT_FOR_GAME"
    reasons: list[str] = []
    ok: list[Snapshot] = []
    for s in sorted(cands, key=lambda s: s.archived_utc):
        a = MK.parse_ts(s.archived_utc)
        b = MK.parse_ts(s.branch_commit_utc) if s.branch_commit_utc else None
        if a > info_cutoff:
            reasons.append("ARCHIVED_AFTER_DECISION")
        elif b is None or b > info_cutoff:
            reasons.append("BRANCH_COMMIT_AFTER_DECISION")
        elif a + MARGIN > info_cutoff or b + MARGIN > info_cutoff:
            reasons.append("TOO_CLOSE_TO_DECISION")            # config: both clocks at least 5 minutes before the decision instant
        elif a + MARGIN > tip or b + MARGIN > tip:
            reasons.append("TOO_CLOSE_TO_TIP")
        elif frozen_feed_utc is None or s.feed_generated_utc != frozen_feed_utc:
            reasons.append("FEED_MISMATCH")
        else:
            ok.append(s)
    if ok:
        return ok[-1], "OK"
    return None, Counter(reasons).most_common(1)[0][0]


# ================================================================================================ counterfactual probabilities
def forecast_pmfs(archive: str, ids: set[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in sorted(glob.glob(os.path.join(archive, "forecasts", "nba", "*", "*.jsonl.gz"))):
        with gzip.open(p, "rt") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    if r.get("forecast_id") in ids:
                        out[r["forecast_id"]] = {"lo": r["lo"], "probs": r["probs"], "mean": r["mean"], "family": r["family"], "entity_id": r["entity_id"]}
    return out


def jrm_probabilities(c: dict, row: dict, rec: dict) -> dict[str, Any] | None:
    """Counterfactual probabilities of ONE candidate side for a player covered by a JRM row. None when the inputs are not the same feed."""
    fp = row["frozen_published"]
    m_frozen = float(fp["minutes_given_play_after_gate"])
    if not row_valid(row) or m_frozen <= 0:
        return None
    if c.get("p_play") is not None and abs(float(fp["p_play"]) - float(c["p_play"])) > 5e-4:
        return None                                         # the snapshot's frozen leg is not the leg this decision used: different inputs, no match
    r = float(row["minutes_given_play_jrm"]) / m_frozen
    p_yes_f = PR.p_ge(rec, float(c["k"]))
    p_yes_j = PR.p_ge(rec, float(c["k"]), scale=r) if r > 0 else 0.0 if c["k"] > 0 else 1.0
    side_yes = c["side"] == "YES"
    p_c_f = p_yes_f if side_yes else 1 - p_yes_f
    p_c_j = p_yes_j if side_yes else 1 - p_yes_j
    if c.get("p_play") is None or c.get("p_model") is None:
        return None
    pp_f, pp_j = float(c["p_play"]), float(row["p_play_jrm"])
    m_side = c.get("p_market_mid")
    m_side = None if m_side is None or pd.isna(m_side) else float(m_side)
    if m_side is None and (pp_f < 1 or pp_j < 1):
        return None                                         # the DNP leg cannot be valued: never silently dropped
    mix = (lambda pp, pc: pp * pc + (1 - pp) * m_side) if m_side is not None else (lambda pp, pc: pc)
    if abs(mix(pp_f, p_c_f) - float(c["p_model"])) > 1e-6:
        return None                                         # the rebuilt frozen probability is not the archived one: any difference would be booked as a JRM effect
    return {"ratio_minutes": r, "p_cond_frozen": p_c_f, "p_cond_jrm": p_c_j, "p_play_frozen": pp_f, "p_play_jrm": pp_j, "p_model_frozen_rebuilt": mix(pp_f, p_c_f),
            "p_model_jrm": mix(pp_j, p_c_j), "m_side": m_side, "minutes_frozen": m_frozen, "minutes_jrm": float(row["minutes_given_play_jrm"]),
            "minutes_before_gate": float(fp.get("minutes_given_play_before_gate", np.nan))}


def build_variant(cands: list[dict], snaps: list[Snapshot], pmfs: dict[str, dict], study: dict, base: dict) -> tuple[list[dict], dict[str, Any]]:
    """Copy of the prepared candidates with JRM probabilities substituted where a matched eligible snapshot covers the player. Also returns the
    matching ledger (per game: snapshot, reason; per player-contract: covered or why not)."""
    out: list[dict] = []
    ledger: dict[str, Any] = {"games": {}, "rows": Counter()}
    cache: dict[str, tuple[Snapshot | None, str]] = {}
    for c in cands:
        v = dict(c)
        v["jrm"] = None
        gid = c["game_id"]
        player = str(c.get("family", "")).startswith("player_") and c.get("entity_id") is not None
        key = (gid, c.get("forecast_generated_utc"), c["as_of"])         # a game's player and game-level forecasts may come from different feed clocks
        if player and key not in cache:
            cache[key] = match_snapshot(snaps, gid, c["tip"], c["as_of"], c.get("forecast_generated_utc"))
            prev = ledger["games"].get(gid)
            if prev is None or (prev["snapshot"] is None and cache[key][0] is not None):
                ledger["games"][gid] = {"snapshot": cache[key][0].file if cache[key][0] else None, "reason": cache[key][1]}
        if not player:
            v["jrm_status"] = "GAME_LEVEL_UNCHANGED"
            ledger["rows"][v["jrm_status"]] += 1
            out.append(v)
            continue
        snap, why = cache[key]
        if snap is None:
            v["jrm_status"] = why
        else:
            row = snap.rows.get((gid, c["entity_id"]))
            rec = pmfs.get((c.get("forecast_ids") or [None])[0])
            if row is None or rec is None:
                v["jrm_status"] = "PLAYER_NOT_IN_SNAPSHOT" if row is None else "NO_PMF"
            elif not row.get("pregame", False):
                v["jrm_status"] = "ROW_NOT_PREGAME"
            else:
                pj = jrm_probabilities(c, row, rec)
                if pj is None:
                    v["jrm_status"] = "FROZEN_INPUT_MISMATCH" if row_valid(row) else "ROW_INVALID"
                else:
                    v["jrm_status"] = "COVERED"
                    v["jrm"] = {**pj, "snapshot": snap.file}
                    v["p_play"], v["p_cond"], v["p_model"] = pj["p_play_jrm"], pj["p_cond_jrm"], pj["p_model_jrm"]
                    v["ev_net_exec"] = None if v["effective_entry_exec"] is None else pj["p_model_jrm"] - v["effective_entry_exec"] - v["fee_int"]
        ledger["rows"][v["jrm_status"]] += 1
        out.append(v)
    ledger["rows"] = dict(ledger["rows"])
    return out, ledger


# ================================================================================================ paired decisions
def pair_decisions(v1: list[dict], jr: list[dict]) -> dict[str, Any]:
    """Paired classification of the two portfolios built on the SAME candidate rows. Keyed by (ticker, side)."""
    j = {(c["ticker"], c["side"]): c for c in jr}
    rows = []
    for a in v1:
        b = j[(a["ticker"], a["side"])]
        ta, tb = a["decision"] == "TRADE", b["decision"] == "TRADE"
        cls = "both_bet" if ta and tb else "v1_only" if ta else "jrm_only" if tb else "neither"
        rows.append({"ticker": a["ticker"], "side": a["side"], "game_id": a["game_id"], "player": a.get("player_name"), "family": a["family"], "k": a.get("k"),
                     "class": cls, "jrm_status": b["jrm_status"], "covered": b["jrm_status"] == "COVERED", "price": a.get("price"),
                     "p_model_v1": a["p_model"], "p_model_jrm": b["p_model"], "ev_v1": a["ev_net_exec"], "ev_jrm": b["ev_net_exec"],
                     "d_p_model": None if a["p_model"] is None else b["p_model"] - a["p_model"],
                     "d_ev": None if a["ev_net_exec"] is None else b["ev_net_exec"] - a["ev_net_exec"],
                     "reason_v1": a["reason"], "reason_jrm": b["reason"], "eligible_v1": not a["blockers"], "eligible_jrm": not b["blockers"],
                     "ratio_minutes": (b["jrm"] or {}).get("ratio_minutes"), "minutes_frozen": (b["jrm"] or {}).get("minutes_frozen"),
                     "minutes_jrm": (b["jrm"] or {}).get("minutes_jrm"), "p_play_v1": a.get("p_play"), "p_play_jrm": b.get("p_play"),
                     "won": a.get("won"), "dnp": bool(a.get("dnp")), "net_pnl": a.get("net_pnl"), "clv_cents": a.get("clv_cents"), "settled": bool(a.get("settled")),
                     "tip": a["tip"], "unit_id": a["unit_id"], "thesis_id": a["thesis_id"], "decision_mode": a["decision_mode"]})
    df = pd.DataFrame(rows)
    return {"frame": df}


def summarize_pairs(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {"status": "NO_DATA", "reason": "no matched candidate rows"}
    out: dict[str, Any] = {"status": "OK", "downstream": LABEL}
    traded = df[df["class"] != "neither"]
    cnt = Counter(df["class"])
    out["decision_matrix_candidate_sides"] = {k: int(cnt.get(k, 0)) for k in ("both_bet", "v1_only", "jrm_only", "neither")}
    ne = df[df["class"] == "neither"]
    out["neither_breakdown"] = {"eligible_in_either_not_selected": int((ne["eligible_v1"] | ne["eligible_jrm"]).sum()), "blocked_in_both": int((~(ne["eligible_v1"] | ne["eligible_jrm"])).sum())}
    th = traded.groupby("thesis_id")["class"].agg(lambda s: tuple(sorted(set(s))))
    out["thesis_level"] = {"theses_traded_by_either": int(len(th)), "same_contract_both": int(sum(1 for t in th if t == ("both_bet",))),
                           "different_contract_same_thesis": int(sum(1 for t in th if "jrm_only" in t and "v1_only" in t)),
                           "v1_only_thesis": int(sum(1 for t in th if t == ("v1_only",))), "jrm_only_thesis": int(sum(1 for t in th if t == ("jrm_only",)))}
    cov = df[df["covered"]]
    out["coverage"] = {"candidate_sides": int(len(df)), "covered_by_jrm_row": int(len(cov)), "covered_share": ST._f(len(cov) / len(df)),
                       "status_counts": {k: int(v) for k, v in Counter(df["jrm_status"]).most_common()}}
    if len(cov):
        out["common_contracts_covered"] = {"n_sides": int(len(cov)), "mean_d_p_model": ST._f(cov["d_p_model"].mean()), "mean_abs_d_p_model": ST._f(cov["d_p_model"].abs().mean()),
                                           "mean_d_ev": ST._f(cov["d_ev"].mean()), "mean_ratio_minutes": ST._f(cov["ratio_minutes"].mean()),
                                           "by_side": {s: {"n": int(len(g)), "mean_d_p_model": ST._f(g["d_p_model"].mean()), "mean_d_ev": ST._f(g["d_ev"].mean())} for s, g in cov.groupby("side")}}
    sd = traded[traded["settled"]]
    out["traded_outcomes"] = {}
    for k in ("both_bet", "v1_only", "jrm_only"):
        g = sd[sd["class"] == k]
        out["traded_outcomes"][k] = {"n": int(len(g)), "n_games": int(g["game_id"].nunique()), "net_pnl": ST._f(g["net_pnl"].sum()) if len(g) else None,
                                     "wins": int((g["won"] == True).sum()) if len(g) else 0,  # noqa: E712
                                     "mean_clv_cents": ST._f(g["clv_cents"].mean()) if g["clv_cents"].notna().any() else None,
                                     "contracts": [f"{r.player} {r.family} {r.side} {r.k}: {r.net_pnl:+.2f}" for r in g.itertuples()]}
    return out


def star_under_diagnostic(df: pd.DataFrame, min_star_minutes: float = 28.0) -> dict[str, Any]:
    """Evidence about the 'artificial star under' hypothesis. Never asserts the cause: reports what the matched numbers show."""
    cov = df[df["covered"]]
    if cov.empty:
        return {"status": "NO_DATA", "reason": "no covered player contracts"}
    stars = cov[cov["minutes_frozen"] >= min_star_minutes].drop_duplicates(["unit_id"])
    no_v1 = df[(df["class"].isin(["both_bet", "v1_only"])) & (df["side"] == "NO")]
    jrm_theses = set(df[df["class"].isin(["both_bet", "jrm_only"])]["thesis_id"])
    out: dict[str, Any] = {"status": "OK", "definition": f"star = frozen conditional minutes >= {min_star_minutes}", "n_covered_player_games": int(cov["unit_id"].nunique()),
                           "n_star_player_games": int(len(stars)),
                           "stars_mean_minutes_ratio_jrm_over_frozen": ST._f(stars["ratio_minutes"].mean()) if len(stars) else None,
                           "stars_share_jrm_minutes_higher": ST._f((stars["ratio_minutes"] > 1).mean()) if len(stars) else None,
                           "v1_NO_trades": []}
    for r in no_v1.to_dict("records"):
        out["v1_NO_trades"].append({"player": r["player"], "family": r["family"], "k": r["k"], "minutes_frozen": r["minutes_frozen"], "minutes_jrm": r["minutes_jrm"],
                                    "ratio": r["ratio_minutes"], "p_model_v1": r["p_model_v1"], "p_model_jrm": r["p_model_jrm"], "ev_v1": r["ev_v1"], "ev_jrm": r["ev_jrm"],
                                    "same_contract_still_bet_by_jrm": r["class"] == "both_bet", "same_thesis_still_traded_by_jrm": r["thesis_id"] in jrm_theses,
                                    "won": r["won"], "covered": r["covered"]})
    sub = [x for x in out["v1_NO_trades"] if x["covered"]]
    out["v1_NO_covered"] = {"n": len(sub), "jrm_minutes_higher": int(sum(1 for x in sub if x["ratio"] and x["ratio"] > 1)),
                            "same_contract_dropped_by_jrm": int(sum(1 for x in sub if not x["same_contract_still_bet_by_jrm"])),
                            "whole_thesis_dropped_by_jrm": int(sum(1 for x in sub if not x["same_thesis_still_traded_by_jrm"])),
                            "note": "a dropped contract is often replaced by another rung of the same player-stat thesis (one expression per thesis)"}
    out["interpretation_rule"] = ("Supportive evidence for 'incumbent normalization creates artificial star unders' would be: JRM minutes systematically ABOVE the frozen published minutes "
                                  "for stars AND the V1 NO bets disappearing under JRM AND (once outcomes exist at scale) JRM minutes being the closer forecast. With the sample here none of "
                                  "this can be concluded; the numbers above are descriptive.")
    return out


# ================================================================================================ forecast accuracy on matched, settled data
def _gauss_crps(mu: np.ndarray, sd: np.ndarray, y: np.ndarray) -> np.ndarray:
    from scipy import stats as sps
    sd = np.maximum(sd, 1e-6)
    z = (y - mu) / sd
    return sd * (z * (2 * sps.norm.cdf(z) - 1) + 2 * sps.norm.pdf(z) - 1 / math.sqrt(math.pi))


def minutes_accuracy(snaps_by_game: dict[str, Snapshot], actual: pd.DataFrame) -> dict[str, Any]:
    """actual: columns game_id, entity_id, played (bool), minutes (float or NaN). Matched = rows of the registered eligible snapshot used for the game."""
    rows = []
    for gid, s in snaps_by_game.items():
        for (g, pid), r in s.rows.items():
            if g != gid or not row_valid(r) or not r.get("pregame", False):
                continue
            rows.append({"game_id": gid, "entity_id": pid, "p_jrm": r["p_play_jrm"], "m_jrm": r["minutes_given_play_jrm"], "u_jrm": r["expected_minutes_unconditional_jrm"],
                         "p10": r.get("minutes_p10"), "p90": r.get("minutes_p90"), "p_fro": r["frozen_published"]["p_play"],
                         "m_fro": r["frozen_published"]["minutes_given_play_after_gate"], "m_fro_pre": r["frozen_published"].get("minutes_given_play_before_gate")})
    if not rows:
        return {"status": "NO_DATA", "reason": "no matched eligible snapshot rows"}
    f = pd.DataFrame(rows).merge(actual, on=["game_id", "entity_id"], how="inner")
    if f.empty:
        return {"status": "NO_DATA", "reason": "no settled outcomes for the matched snapshot players"}
    f["u_fro"] = f["p_fro"] * f["m_fro"]
    y_play = f["played"].astype(float)
    pl = f[f["played"] & f["minutes"].notna()]
    out: dict[str, Any] = {"status": "OK", "n_games": int(f["game_id"].nunique()), "n_player_games": int(len(f)), "n_played": int(len(pl)),
                           "frame": "players of the registered eligible snapshot with a settled outcome; frozen = its own frozen_published (same feed, after gate)"}
    if len(pl):
        ej, ef = (pl["m_jrm"] - pl["minutes"]).to_numpy(), (pl["m_fro"] - pl["minutes"]).to_numpy()
        out["conditional_minutes"] = {"mae_jrm": ST._f(np.abs(ej).mean()), "mae_frozen": ST._f(np.abs(ef).mean()), "bias_jrm": ST._f(ej.mean()), "bias_frozen": ST._f(ef.mean()),
                                      "mae_diff_jrm_minus_frozen": ST.cluster_diff(np.abs(ej), np.abs(ef), pl["game_id"]),
                                      "note": "negative diff = JRM better; bias = prediction - actual"}
        sj = ((pl["p90"].astype(float) - pl["p10"].astype(float)) / 2.5631).to_numpy()
        ok = np.isfinite(sj)
        if ok.any():                                         # rows without a JRM interval are left out, never given an invented width
            cr_j = _gauss_crps(pl["m_jrm"].to_numpy(float)[ok], sj[ok], pl["minutes"].to_numpy(float)[ok])
            # like-for-like: the frozen forecast gets the same Gaussian shape with the JRM interval width (the snapshot holds no frozen pmf width)
            cr_f = _gauss_crps(pl["m_fro"].to_numpy(float)[ok], sj[ok], pl["minutes"].to_numpy(float)[ok])
            out["conditional_minutes"]["crps_gauss_approx"] = {"n": int(ok.sum()), "jrm": ST._f(cr_j.mean()), "frozen_same_width": ST._f(cr_f.mean()),
                                                               "diff": ST.cluster_diff(cr_j, cr_f, pl["game_id"].to_numpy()[ok]),
                                                               "note": "APPROXIMATE: Gaussian with sd = (p90-p10)/2.563 of the JRM snapshot applied to both means; not a CRPS of either model's own distribution"}
        else:
            out["conditional_minutes"]["crps_gauss_approx"] = {"status": "NO_DATA", "reason": "no JRM p10/p90"}
    uj, uf = (f["u_jrm"] - f["minutes"].fillna(0)).to_numpy(), (f["u_fro"] - f["minutes"].fillna(0)).to_numpy()
    out["unconditional_minutes"] = {"mae_jrm": ST._f(np.abs(uj).mean()), "mae_frozen": ST._f(np.abs(uf).mean()), "bias_jrm": ST._f(uj.mean()), "bias_frozen": ST._f(uf.mean()),
                                    "mae_diff_jrm_minus_frozen": ST.cluster_diff(np.abs(uj), np.abs(uf), f["game_id"])}
    bj, bf = ST.brier(f["p_jrm"], y_play), ST.brier(f["p_fro"], y_play)
    out["p_play"] = {"brier_jrm": ST._f(bj.mean()), "brier_frozen": ST._f(bf.mean()), "diff_jrm_minus_frozen": ST.cluster_diff(bj, bf, f["game_id"]),
                     "mean_p_jrm": ST._f(f["p_jrm"].mean()), "mean_p_frozen": ST._f(f["p_fro"].mean()), "observed_play_rate": ST._f(y_play.mean())}
    return out


def stat_family_accuracy(pairs: pd.DataFrame) -> dict[str, Any]:
    """Rung-probability Brier of the covered, settled, played-or-not YES-complement per family: p_yes frozen vs JRM against the realised YES."""
    p = pairs[pairs["covered"] & pairs["settled"] & pairs["won"].notna() & ~pairs["dnp"].fillna(False).astype(bool)].copy()
    if p.empty:
        return {"status": "NO_DATA", "reason": "no covered settled player contracts"}
    p["y_side"] = p["won"].astype(float)
    # candidate p_model is side-specific expected payoff incl. the DNP leg: compare model payoff probabilities with the realised side payoff (won)
    out: dict[str, Any] = {"status": "OK", "note": "Brier of the side-specific participation-aware p_model against the realised side win, played contracts only; rungs of one player-game are not independent",
                           "by_family": {}}
    for fam, g in p.groupby("family"):
        bj, bf = ST.brier(g["p_model_jrm"], g["y_side"]), ST.brier(g["p_model_v1"], g["y_side"])
        out["by_family"][fam] = {"n_sides": int(len(g)), "n_games": int(g["game_id"].nunique()), "brier_jrm": ST._f(bj.mean()), "brier_frozen": ST._f(bf.mean()),
                                 "diff_jrm_minus_frozen": ST.cluster_diff(bj, bf, g["game_id"])}
    return out


# ================================================================================================ the prospective JRM gate (tracked, not decided here)
def gate_status(snaps: list[Snapshot], settled_games: set[str], study: dict) -> dict[str, Any]:
    need = int(study["jrm_matching"]["prospective_gate"]["min_settled_games"])
    elig: dict[str, Snapshot] = {}
    for s in snaps:
        for (g, _) in s.rows:
            if MK.parse_ts(s.archived_utc) is not None:
                elig.setdefault(g, s)
    games = sorted(g for g in elig if g in settled_games)
    return {"min_settled_games": need, "eligible_settled_games": len(games), "games": games, "status": "NO_DATA" if not games else "INSUFFICIENT_SAMPLE" if len(games) < need else "GATE_MINIMUM_REACHED",
            "starter_guard": study["jrm_matching"]["prospective_gate"]["starter_guard"],
            "verdict_owner": study["jrm_matching"]["prospective_gate"]["owner"],
            "note": "this study only counts games; the verdict (primary + starter guard) is PR #45's evaluate_prospective.py. No promotion is possible from here."}
