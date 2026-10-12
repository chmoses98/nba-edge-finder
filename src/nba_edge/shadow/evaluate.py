"""Score matured shadow projections: (a) the entire eligible population, (b) the pregame market-listed cohort.

Reuses the Wave 1 matched-decomposition scoring (``research/matched_decomposition``: game-clustered
paired bootstrap, one row per player-game-stat) and the shared pure_gate ``compare``. Outputs are
appended to the store (``evaluations/`` and ``reconciliation/``); nothing is overwritten.

Definitions
-----------
* One forecast per (slot, game, player, statistic, arm, conditionality): the EARLIEST live capture
  of that slot. Replay rows are scored only when ``include_replay`` is set (dry runs), and labelled.
* Matured = an outcome row exists (ESPN box score fetched by this collector).
* Pregame market-listed cohort = (game, player, statistic) with a ``market_listing`` row captured at
  the same as_of whose market was on a board observed at or before as_of and opened by then
  (``listed_by_as_of``). Defined pregame, never from settlement.
* CRPS here is the quantile approximation (2 x mean pinball loss over the 7 stored quantile levels);
  exact sample CRPS needs draws, which are not stored.
* Reconciliation flags a listing whose recorded venue result (from the read-only capture archive,
  when present) disagrees with the sports outcome (``actual >= at_least``).

Alongside these (``scorecards.py``): an ``accuracy_scorecard`` record (vendored accuracy_scorecard; V1 sim challenger
vs EWM5 baseline, both populations, unconditional and conditional rows) and a DRY-RUN ``value_scorecard`` record under
the committed preregistration, appended under ``scorecards/accuracy`` and ``scorecards/value`` whenever the
evaluation itself is written.

Descriptive only: no promotion, no authority, no staking.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from nba_edge.research import matched_decomposition as md
from nba_edge.shadow import projections as pj
from nba_edge.shadow import scorecards as SC
from nba_edge.shadow.collect import load_gate
from nba_edge.shadow.store import ShadowStore
from nba_edge.timeutil import iso

COND = {"unconditional": "unc", "conditional": "cond"}


def _clean(r: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in r.items() if not k.startswith("_")}


def crps_quantile(row: dict[str, Any], y: float) -> float:
    qs = row["projection"].get("quantiles") or []
    if len(qs) < 3:
        return float("nan")
    loss = [max(q["q"] * (y - q["value"]), (q["q"] - 1) * (y - q["value"])) for q in qs]
    return 2.0 * float(np.mean(loss))


def _p_at(row: dict[str, Any], t: float) -> float:
    for th in row["projection"]["thresholds"]:
        if abs(float(th["at_least"]) - float(t)) < 1e-9:
            return float(th["probability"])
    return float("nan")


def load_projections(store: ShadowStore, include_replay: bool) -> list[dict[str, Any]]:
    best: dict[tuple, dict[str, Any]] = {}
    for _e, r in store.iter_rows("projections/"):
        r = _clean(r)
        mode = r.get("x_capture_mode", "LIVE")
        if mode.startswith("REPLAY") and not include_replay:
            continue
        k = (r.get("x_slot"), r["game_id"], r["player_id"], r["statistic"], r["model_version"], r["conditional_on_playing"])
        if k not in best or r["as_of"] < best[k]["as_of"]:
            best[k] = r
    return list(best.values())


def load_outcomes(store: ShadowStore) -> tuple[dict[tuple, dict[str, Any]], pd.DataFrame]:
    gate: dict[tuple, dict[str, Any]] = {}
    for _e, r in store.iter_rows("outcomes/gate"):
        r = _clean(r)
        gate.setdefault((r["sport"], r["game_id"], r["player_id"], r["statistic"]), r)  # first fetched version stands
    box = pd.DataFrame([_clean(r) for _e, r in store.iter_rows("outcomes/box") if r.get("row_type") == "player"])
    if len(box):
        box = box.sort_values("fetched_at").drop_duplicates(["game_id", "team_id", "nba_id"], keep="first")
    return gate, box


def load_listed(store: ShadowStore) -> tuple[set[tuple], list[dict[str, Any]]]:
    keys, rows = set(), []
    for _e, r in store.iter_rows("market/listings"):
        r = _clean(r)
        rows.append(r)
        if r.get("player_id") and r.get("listed_by_as_of"):
            keys.add((r["pure_as_of"], r["game_id"], r["player_id"], r["statistic"]))
    return keys, rows


def _long_rows(proj: list[dict[str, Any]], gate: dict[tuple, dict[str, Any]], arm_of: dict[str, str]) -> pd.DataFrame:
    out = []
    for r in proj:
        o = gate.get((r["sport"], r["game_id"], r["player_id"], r["statistic"]))
        if o is None:
            continue
        cond = "conditional" if r["conditional_on_playing"] else "unconditional"
        y = float(o["actual"])
        t_ref = float(r.get("x_t_ref", float("nan")))
        p = r["projection"]
        out.append({"slot": r.get("x_slot"), "as_of": r["as_of"], "game_id": r["game_id"], "player_id": r["player_id"], "date": r["kickoff"][:10],
                    "team_id": r.get("x_team_id"), "arm": arm_of[r["model_version"]], "cond": COND[cond], "stat": r["statistic"],
                    "mean": float(p["mean"]), "median": float(p["median"]), "p10": float(p["p10"]), "p90": float(p["p90"]),
                    "crps": crps_quantile(r, y), "t_ref": t_ref, "p_ref": _p_at(r, t_ref), "actual": y, "played": bool(o["played"]),
                    "participation": r.get("participation_probability"), "phase": phase_of(r)})
    return pd.DataFrame(out)


def _wide(long: pd.DataFrame, arms: tuple[str, ...]) -> pd.DataFrame:
    """Participation frame from the unconditional minutes rows: P(play) and P(>=10 min) per arm."""
    m = long[(long["stat"] == "minutes") & (long["cond"] == "unc")]
    if m.empty:
        return pd.DataFrame()
    base = m[m["arm"] == arms[0]][["game_id", "player_id", "actual", "played"]].rename(columns={"actual": "act_min", "played": "act_played"})
    base = base.set_index(["game_id", "player_id"])
    for a in arms:
        s = m[m["arm"] == a].set_index(["game_id", "player_id"])
        base[f"{a}_p_play"] = s["participation"].astype(float)
        base[f"{a}_p10min"] = s["p10min"] if "p10min" in s else np.nan
    return base.dropna().reset_index()


def _scorecards(long: pd.DataFrame, wide: pd.DataFrame, n_boot: int) -> dict[str, Any]:
    arms = (pj.BASELINE, pj.CHAMPION)
    pairs = [(pj.BASELINE, pj.CHAMPION)]
    out: dict[str, Any] = {"n_games": int(long["game_id"].nunique()) if len(long) else 0}
    if long.empty:
        return out
    out["final_stats"] = {}
    for s in md.STATS:
        out["final_stats"][s] = {}
        for c in ("unc", "cond"):
            sub = long[(long["stat"] == s) & (long["cond"] == c)]
            if sub.empty or sub["arm"].nunique() < 2:
                continue
            out["final_stats"][s][c] = md.stat_scorecard(sub, s, c, arms, pairs, n_boot)
    if len(wide):
        out["participation"] = md.participation_scorecard(wide, arms, pairs, n_boot)
    return out


def phase_of(r: dict[str, Any]) -> str:
    """Preseason rows are research-only and never pooled with regular-season rows."""
    return "PRESEASON_RESEARCH" if r.get("x_season_type") == "preseason" else "REGULAR_SEASON"


def evaluate(store: ShadowStore, now: datetime, include_replay: bool = False, n_boot: int = 1000, archive_root: Path | None = None,
             write: bool = True) -> dict[str, Any]:
    gate_mod = load_gate()
    arm_of = {v: k for k, v in pj.MODEL_VERSION.items()}
    proj = load_projections(store, include_replay)
    gate, box = load_outcomes(store)
    listed, listing_rows = load_listed(store)
    # An eligible player absent from a final box score did not play for that team: scored as 0 /
    # not played, exactly as the Wave 1 harness did (``actual_outcomes``), and counted.
    n_absent = 0
    if len(box):
        fetched = box.groupby("game_id")["fetched_at"].min().to_dict()
        for r in proj:
            k = (r["sport"], r["game_id"], r["player_id"], r["statistic"])
            if k not in gate and r["game_id"] in fetched:
                gate[k] = {"sport": r["sport"], "game_id": r["game_id"], "player_id": r["player_id"], "statistic": r["statistic"],
                           "actual": 0.0, "played": False, "source": "espn_summary_absent_from_box", "observed_at": fetched[r["game_id"]]}
                n_absent += 1
    long = _long_rows(proj, gate, arm_of)
    rep: dict[str, Any] = {"record": "evaluation", "evaluated_at": iso(now), "include_replay": include_replay,
                           "n_projection_rows": len(proj), "n_outcome_rows": len(gate), "n_outcome_rows_absent_from_box": n_absent,
                           "n_listing_rows": len(listing_rows),
                           "crps_definition": "quantile approximation: 2 x mean pinball over 7 stored levels", "by_slot": {}}
    if not long.empty:
        # P(>=10 min) from the unconditional minutes ladder, for the participation scorecard
        p10 = {}
        for r in proj:
            if r["statistic"] == "minutes" and not r["conditional_on_playing"]:
                p10[(r.get("x_slot"), r["game_id"], r["player_id"], arm_of[r["model_version"]])] = _p_at(r, 10.0)
        long["p10min"] = [p10.get((s, g, p, a), np.nan) for s, g, p, a in zip(long["slot"], long["game_id"], long["player_id"], long["arm"], strict=True)]
        long["listed"] = [(a, g, p, s) in listed for a, g, p, s in zip(long["as_of"], long["game_id"], long["player_id"], long["stat"], strict=True)]
    groups = sorted({(ph, sl) for ph, sl in zip(long["phase"], long["slot"], strict=True)}) if len(long) else []
    for phase, slot in groups:
        L = long[(long["slot"] == slot) & (long["phase"] == phase)]
        key = slot if phase == "REGULAR_SEASON" else f"PRESEASON_RESEARCH/{slot}"
        res: dict[str, Any] = {"phase": phase, "matured_games": sorted(set(L["game_id"]))}
        for cohort, mask in (("all_eligible", pd.Series(True, index=L.index)), ("pregame_market_listed", L["listed"])):
            sub = L[mask]
            res[cohort] = _scorecards(sub, _wide(sub, (pj.BASELINE, pj.CHAMPION)), n_boot)
            res[cohort]["n_player_game_stat_rows"] = int(((sub["arm"] == pj.CHAMPION) & (sub["cond"] == "unc")).sum())
            # shared gate compare (champion vs the simple baseline), per conditionality
            gc = {}
            for cond in (False, True):
                ch = [r for r in proj if r.get("x_slot") == slot and phase_of(r) == phase and r["model_version"] == pj.MODEL_VERSION[pj.CHAMPION] and r["conditional_on_playing"] == cond]
                bl = [r for r in proj if r.get("x_slot") == slot and phase_of(r) == phase and r["model_version"] == pj.MODEL_VERSION[pj.BASELINE] and r["conditional_on_playing"] == cond]
                if cohort == "pregame_market_listed":
                    ch = [r for r in ch if (r["as_of"], r["game_id"], r["player_id"], r["statistic"]) in listed]
                    bl = [r for r in bl if (r["as_of"], r["game_id"], r["player_id"], r["statistic"]) in listed]
                keys = {(r["sport"], r["game_id"], r["player_id"], r["statistic"]) for r in ch}
                outs = [gate[k] for k in sorted(keys) if k in gate]
                if ch and bl and outs:
                    strip = lambda rows: [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]  # noqa: E731
                    gc["conditional" if cond else "unconditional"] = gate_mod.compare(strip(ch), strip(bl), outs, bootstrap=n_boot)
            res[cohort]["pure_gate_compare_champion_vs_ewm5"] = gc
        # eligibility gaps: box participants this slot never forecast
        if len(box):
            fc_keys = {(g, p) for g, p in zip(L["game_id"], L["player_id"], strict=True)}
            b = box[box["game_id"].isin(res["matured_games"]) & box["played"]]
            miss = b[[(g, str(p)) not in fc_keys for g, p in zip(b["game_id"], b["nba_id"], strict=True)]]
            res["non_eligible_participants"] = {"n": int(len(miss)), "minutes": float(miss["minutes"].sum()), "pts": float(miss["pts"].sum()),
                                                "minutes_share": float(miss["minutes"].sum() / max(b["minutes"].sum(), 1e-9))}
        rep["by_slot"][key] = res
    recon = reconcile(long, listing_rows, gate, archive_root)
    rep["reconciliation_summary"] = recon["summary"]
    prev = [r for _e, r in store.iter_rows("evaluations")]
    fingerprint = {"matured": {k: v["matured_games"] for k, v in rep["by_slot"].items()}, "n_listing_rows": len(listing_rows), "n_projection_rows": len(proj)}
    rep["fingerprint"] = fingerprint
    unchanged = bool(prev) and prev[-1].get("fingerprint") == fingerprint
    rep["written"] = bool(write and not unchanged and (len(long) or listing_rows))
    missed = [r for _e, r in store.iter_rows("missed")]
    acc, val = SC.build_safe([r for r in proj if phase_of(r) == "REGULAR_SEASON"], gate, listing_rows, missed, now=now, run_id=store.run_id, n_boot=n_boot)
    if rep["written"]:
        at = now
        store.append_rows("evaluations", [rep], observed_at=at, meta={"include_replay": include_replay})
        if recon["rows"]:
            store.append_rows("reconciliation", recon["rows"], observed_at=at, meta={})
        store.append_rows("scorecards/accuracy", [acc], observed_at=at, meta={"include_replay": include_replay})
        store.append_rows("scorecards/value", [val], observed_at=at, meta={"include_replay": include_replay, "mode": SC.VALUE_MODE})
    rep["scorecards"] = {"written": rep["written"], **SC.summary_safe(acc, val)}
    return rep


def reconcile(long: pd.DataFrame, listing_rows: list[dict[str, Any]], gate: dict[tuple, dict[str, Any]], archive_root: Path | None) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    if len(long):
        for r in long.itertuples(index=False):
            rows.append({"record": "projection_outcome", "slot": r.slot, "as_of": r.as_of, "game_id": r.game_id, "player_id": r.player_id,
                         "statistic": r.stat, "arm": r.arm, "cond": r.cond, "mean": r.mean, "actual": r.actual, "played": r.played,
                         "abs_err": abs(r.mean - r.actual), "listed": bool(getattr(r, "listed", False))})
    results = _venue_results(archive_root, {r["ticker"] for r in listing_rows if r.get("ticker")}) if listing_rows else {}
    n_mis = n_cmp = 0
    for lr in listing_rows:
        if not lr.get("player_id") or lr.get("at_least") is None:
            continue
        o = gate.get((pj.SPORT, lr["game_id"], lr["player_id"], lr["statistic"]))
        res = results.get(lr["ticker"])
        flag = None
        if o is not None and res in ("yes", "no"):
            sports_yes = float(o["actual"]) >= float(lr["at_least"])
            flag = sports_yes != (res == "yes")
            n_cmp += 1
            n_mis += int(flag)
        rows.append({"record": "listing_outcome", "ticker": lr["ticker"], "game_id": lr["game_id"], "player_id": lr["player_id"],
                     "statistic": lr["statistic"], "at_least": lr["at_least"], "pure_as_of": lr["pure_as_of"],
                     "actual": None if o is None else o["actual"], "played": None if o is None else o["played"],
                     "venue_result": res, "result_vs_sports_mismatch": flag})
    by = defaultdict(int)
    for r in rows:
        by[r["record"]] += 1
    return {"rows": rows, "summary": {"n_rows": dict(by), "listings_compared_to_venue_result": n_cmp, "venue_result_mismatches": n_mis,
                                      "archive_results_available": bool(results)}}


def _venue_results(archive_root: Path | None, tickers: set[str]) -> dict[str, str]:
    """Latest recorded ``result`` per ticker in the read-only capture archive (empty if unavailable)."""
    if archive_root is None or not tickers or not (Path(archive_root) / "manifest.jsonl").exists():
        return {}
    try:
        from nba_edge.archive.ledger import Ledger
        from nba_edge.archive.reconstruct import latest_board

        b = latest_board(Ledger(Path(archive_root)))
    except Exception:  # noqa: BLE001
        return {}
    out = {}
    for m in (b.rows if b else []):
        t = m.get("ticker")
        if t in tickers and m.get("result") in ("yes", "no"):
            out[t] = m["result"]
    return out

