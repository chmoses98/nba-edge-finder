"""Executable single-portfolio shadow study at ONE fixed pretip checkpoint (Issue #53, part B; RESEARCH ONLY, no orders, no authority).

    from nba.paper import exec_shadow as X
    study = X.load_study()                                   # exec_shadow_config.json (frozen protocol, pinned to paper_config.json)
    rows = X.select(candidates, study, base_cfg)             # pure function: candidate side rows -> TRADE / NO_TRADE rows

What it is. The original `PF_EDGE_STRICT_V1` is evaluated per (horizon, decision instant): `evaluate.paper_performance` keeps, per thesis, the
EARLIEST recorded TRADE across horizons, and `engine.apply_strategies` resets the exposure caps inside every horizon group. The seven opening-night
bets are therefore not a simultaneously executable portfolio. This module is a separate, additive study with its own strategy id
(`PF_EDGE_STRICT_T60_EXEC_V1`) and a frozen protocol (`exec_shadow_config.json`, same numeric thresholds as V1, none tuned):

  * ONE checkpoint per game (T-60, the already-designated primary horizon). A missing / stale / after-checkpoint board is a NO_TRADE game; it is
    never replaced by another horizon and nothing is backfilled;
  * a candidate must have been available at the checkpoint: board observed at or before it, forecast GENERATED and ARCHIVED at or before the
    information cut-off of the decision (both clocks);
  * side-specific ASK, displayed top-of-book size >= the order size (otherwise INSUFFICIENT_DEPTH -> NO_TRADE; nothing is filled beyond what was
    displayed), spread, quote age, 1 cent modelled slippage and the whole-order cent-rounded taker fee are applied to the ENTRY decision
    (`ev_net_exec`) as well as to settlement;
  * one expression per thesis, one GLOBAL chronological exposure ledger (per player-game, team-game, game, game notional, day notional, thesis): it
    is never reset between horizons, games or runs;
  * settlement is the paper system's own (Kalshi result first; DNP at the scalar / last fair price), joined from the archived settlements;
  * `decision_mode` (`asof_replay` vs `contemporaneous`) and the computation lag (decided_utc - as_of_utc) are recorded on every row.

Everything is derived from the immutable archives; nothing is written back to them. Rows before `prospective_start_utc` are RETROSPECTIVE and
descriptive: they are reported separately and never counted toward the evidence minimums.
"""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from . import config as CFG
from . import markets as MK
from . import settle as SE
from . import stats as ST

STUDY_PATH = Path(__file__).with_name("exec_shadow_config_v2.json")          # v1.1.0 (exec_shadow_config.json) is kept byte-identical for the record
STUDY_V1_PATH = Path(__file__).with_name("exec_shadow_config.json")
STRATEGY = "PF_EDGE_STRICT_T60_EXEC_V1"
BLOCK_CODES = ("NOT_CHECKPOINT_HORIZON", "MODE_NOT_ALLOWED", "BOARD_AFTER_CHECKPOINT", "FORECAST_AFTER_DECISION", "FORECAST_ARCHIVED_AFTER_DECISION",
               "FORECAST_ARCHIVE_UNVERIFIED", "FORECAST_COMMIT_UNVERIFIED", "FORECAST_COMMITTED_AFTER_CHECKPOINT", "BOARD_ARCHIVE_UNVERIFIED",
               "BOARD_ARCHIVED_AFTER_CHECKPOINT", "NO_EXECUTABLE_QUOTE", "QUALITY_GATE", "STALE_QUOTE_AT_CHECKPOINT", "INSUFFICIENT_DEPTH", "DEPTH_CONFLICT_ORDERBOOK",
               "GATE_STATUS", "LOW_P_PLAY", "SPREAD_WIDE_STRICT", "SPREAD_UNKNOWN", "EV_BELOW_THRESHOLD")
THESIS_CODES = ("NOT_BEST_IN_THESIS", "THESIS_ALREADY_HELD", "EXPOSURE_CAP")
EDGE_BINS = [0.06, 0.10, 0.15, 0.25, 10.0]
EDGE_LABELS = ["0.06-0.10", "0.10-0.15", "0.15-0.25", ">=0.25"]


# ================================================================================================ protocol
def load_study(path: str | Path | None = None) -> dict:
    return json.loads(Path(path or STUDY_PATH).read_text())


def study_sha(path: str | Path | None = None) -> str:
    import hashlib
    return hashlib.sha256(Path(path or STUDY_PATH).read_bytes()).hexdigest()


def base_protocol_ok(study: dict) -> tuple[bool, str]:
    """The pinned digest of the original protocol: the study must not run against a base file that has been edited."""
    got = CFG.config_sha()
    want = study["base_protocol"]["sha256"]
    return got == want, f"paper_config.json sha256 {got[:12]} {'==' if got == want else '!='} pinned {want[:12]}"


def _n(x: Any) -> Any:
    """NaN / NaT / pandas NA -> None."""
    if x is None:
        return None
    try:
        if pd.isna(x):
            return None
    except (TypeError, ValueError):
        pass
    return x


def _ts(x: Any) -> datetime | None:
    x = _n(x)
    if x is None:
        return None
    if isinstance(x, pd.Timestamp):
        return x.to_pydatetime()
    if isinstance(x, datetime):
        return x
    return MK.parse_ts(str(x))


def checkpoint_of(tip: datetime, study: dict) -> datetime:
    return tip - timedelta(minutes=int(study["checkpoint"]["minutes_before_tip"]))


# ================================================================================================ candidates
def prepare(row: dict, study: dict, base: dict) -> dict:
    """Normalise one archived PF_ALL_CANDIDATES_V1 side row (a dict, possibly with settlement columns) into the study's candidate record."""
    c = {k: _n(v) if not isinstance(v, (dict, list)) else v for k, v in row.items()}
    tip = _ts(c["game_start_utc"])
    as_of = _ts(c["as_of_utc"])
    board = _ts(c.get("board_observed_utc"))
    decided = _ts(c.get("decided_utc"))
    cp = checkpoint_of(tip, study)
    c["tip"], c["as_of"], c["board"], c["decided"], c["checkpoint"] = tip, as_of, board, decided, cp
    c["quote_age_at_checkpoint_s"] = None if board is None else (cp - board).total_seconds()
    c["computation_lag_s"] = None if (decided is None or as_of is None) else (decided - as_of).total_seconds()
    c["minutes_to_tip_decided"] = None if decided is None else (tip - decided).total_seconds() / 60.0
    # A row built here is a RECONSTRUCTION from archives, whenever it is computed: nothing can prove the choice existed before tip, so it is NEVER prospective
    # (owner review of PR #54). Prospective evidence exists only as a verified SEAL (nba.paper.exec_seal), which sets `prospective` itself after verification.
    c["computed_before_tip"] = bool(decided is not None and decided < tip)
    c["prospective"] = False
    c["origin"] = "reconstruction"
    price = _n(c.get("price"))
    contracts = int(study["execution"]["order_contracts"])
    if price is not None:
        eff = min(round(float(price) + float(study["execution"]["slippage"]), 4), 0.99)
        mult = float((c.get("fee_assumption") or {}).get("multiplier") or base["execution"]["fee_taker_multiplier"])
        fee = SE.fee_paid(eff, contracts, mult) / contracts
        c["effective_entry_exec"], c["fee_int"] = eff, fee
        pm = _n(c.get("p_model"))
        c["ev_net_exec"] = None if pm is None else float(pm) - eff - fee
    else:
        c["effective_entry_exec"] = c["fee_int"] = c["ev_net_exec"] = None
    return c


def block_reasons(c: dict, scfg: dict, study: dict, forecast_archive: dict[str, str] | None, clocks: dict | None = None) -> list[str]:
    """Every reason a candidate side is not tradeable at the checkpoint (empty list = eligible). First element = primary reason.

    `clocks` (optional) = {"board_commit": {tick_iso: commit_iso}, "forecast_commit": {forecast_id: commit_iso}}: the INDEPENDENT archive clocks (git commit time of the
    capture / forecast file on the data branches). When given, a board or forecast that was only committed after the checkpoint is not available to the decision."""
    ck, ex = study["checkpoint"], study["execution"]
    out: list[str] = []
    if c.get("horizon") != ck["horizon"]:
        out.append("NOT_CHECKPOINT_HORIZON")                  # no retroactive 'best horizon': any other snapshot of the game is not a candidate
    if c.get("decision_mode") not in ck["allowed_decision_modes"]:
        out.append("MODE_NOT_ALLOWED")
    # ---- time travel: the board and BOTH forecast clocks must precede the information cut-off, which must precede the checkpoint
    if c["board"] is None or c["as_of"] is None or c["board"] > c["checkpoint"] or c["as_of"] > c["checkpoint"]:
        out.append("BOARD_AFTER_CHECKPOINT")
    fg = _ts(c.get("forecast_generated_utc"))
    if fg is None or fg > c["as_of"]:
        out.append("FORECAST_AFTER_DECISION")
    ids = [i for i in (c.get("forecast_ids") or []) if i]
    if forecast_archive is not None:
        arch = [forecast_archive.get(i) for i in ids]
        if not ids or any(a is None for a in arch):
            out.append("FORECAST_ARCHIVE_UNVERIFIED")
        elif any(_ts(a) > c["as_of"] for a in arch):
            out.append("FORECAST_ARCHIVED_AFTER_DECISION")
    if clocks is not None:
        bc = clocks.get("board_commit")
        if bc is not None and c["board"] is not None:
            t = bc.get(MK.iso(c["board"]))
            c["board_commit_utc"] = t
            if t is None:
                out.append("BOARD_ARCHIVE_UNVERIFIED")
            elif _ts(t) > c["checkpoint"]:
                out.append("BOARD_ARCHIVED_AFTER_CHECKPOINT")
        fc = clocks.get("forecast_commit")
        if fc is not None and ids:
            ts_ = [fc.get(i) for i in ids]
            c["forecast_commit_utc"] = max((t for t in ts_ if t), default=None)
            if any(t is None for t in ts_):
                out.append("FORECAST_COMMIT_UNVERIFIED")
            elif any(_ts(t) > c["checkpoint"] for t in ts_):
                out.append("FORECAST_COMMITTED_AFTER_CHECKPOINT")
    if c.get("price") is None:
        out.append("NO_EXECUTABLE_QUOTE")
        return out
    for f in (c.get("quality") or {}).get("failures") or []:
        out.append(f"QUALITY_GATE:{f}")
    age = c.get("quote_age_at_checkpoint_s")
    if age is not None and age > float(ck["max_quote_age_s"]) + 1e-9:
        out.append("STALE_QUOTE_AT_CHECKPOINT")
    need = float(ex["min_displayed_size"]) * 1.0
    need = max(need, float(ex["order_contracts"]))
    size = _n(c.get("top_size"))
    depth = _n(c.get("depth_at_entry"))
    if size is None or float(size) < need:
        out.append("INSUFFICIENT_DEPTH")
    elif depth is not None and float(depth) < float(ex["order_contracts"]):
        out.append("DEPTH_CONFLICT_ORDERBOOK")                  # top of book shows size but the sampled order book at the same tick holds less at the ask: no liquidity is imagined
    gate = (c.get("gate") or {}).get("status")
    if scfg.get("gate_statuses") and gate not in scfg["gate_statuses"]:
        out.append("GATE_STATUS")
    if str(c.get("family", "")).startswith("player_") and scfg.get("min_p_play") is not None and (c.get("p_play") is None or c["p_play"] < scfg["min_p_play"]):
        out.append("LOW_P_PLAY")
    if scfg.get("max_spread") is not None and (c.get("spread") is None or c["spread"] > scfg["max_spread"] + 1e-9):
        out.append("SPREAD_WIDE_STRICT" if c.get("spread") is not None else "SPREAD_UNKNOWN")
    ev = c.get("ev_net_exec")
    if ev is None or not math.isfinite(ev) or ev < scfg["min_ev_net"] - 1e-12:
        out.append("EV_BELOW_THRESHOLD")
    return out


class Ledger:
    """The single global exposure ledger. `caps_hit` is a pure query; `admit` records a position. Never reset by horizon, game or run."""

    def __init__(self, caps: dict):
        self.caps = caps
        self.n_unit: dict[str, int] = defaultdict(int)
        self.n_team: dict[str, int] = defaultdict(int)
        self.n_game: dict[str, int] = defaultdict(int)
        self.notional_game: dict[str, float] = defaultdict(float)
        self.notional_day: dict[str, float] = defaultdict(float)
        self.theses: set[str] = set()

    @staticmethod
    def _team_key(c: dict) -> str:
        return f"{c['game_id']}|{c.get('team') or 'game'}"

    def caps_hit(self, c: dict, cost: float) -> str | None:
        k = self.caps
        if c["thesis_id"] in self.theses:
            return "THESIS_ALREADY_HELD"
        if str(c["family"]).startswith("player_") and self.n_unit[c["unit_id"]] >= k["max_trades_per_player_game"]:
            return "EXPOSURE_CAP:PLAYER_GAME"
        if c.get("team") and self.n_team[self._team_key(c)] >= k["max_trades_per_team_game"]:
            return "EXPOSURE_CAP:TEAM_GAME"
        if self.n_game[c["game_id"]] >= k["max_trades_per_game"]:
            return "EXPOSURE_CAP:GAME"
        if self.notional_game[c["game_id"]] + cost > k["max_notional_per_game"] + 1e-9:
            return "EXPOSURE_CAP:NOTIONAL_GAME"
        if self.notional_day[c["game_date_et"]] + cost > k["max_notional_per_day"] + 1e-9:
            return "EXPOSURE_CAP:NOTIONAL_DAY"
        return None

    def admit(self, c: dict, cost: float) -> dict:
        if str(c["family"]).startswith("player_"):
            self.n_unit[c["unit_id"]] += 1
        if c.get("team"):
            self.n_team[self._team_key(c)] += 1
        self.n_game[c["game_id"]] += 1
        self.notional_game[c["game_id"]] += cost
        self.notional_day[c["game_date_et"]] += cost
        self.theses.add(c["thesis_id"])
        return {"player_game": self.n_unit.get(c["unit_id"], 0), "team_game": self.n_team.get(self._team_key(c), 0), "game": self.n_game[c["game_id"]],
                "game_notional": round(self.notional_game[c["game_id"]], 4), "day_notional": round(self.notional_day[c["game_date_et"]], 4)}


def select(cands: list[dict], study: dict, base: dict, *, strategy_id: str = STRATEGY, ledger: Ledger | None = None,
           forecast_archive: dict[str, str] | None = None, ev_key: str = "ev_net_exec", prepared: bool = False, clocks: dict | None = None) -> list[dict]:
    """TRADE / NO_TRADE row for every candidate side. Pure and deterministic.

    Order of events (the exposure order): checkpoints chronologically; within one checkpoint instant (all games that share it) per thesis the eligible side
    with the highest `ev_key` (ties: lower price, ticker, side), then admission by descending `ev_key` through the ONE ledger."""
    scfg = study["strategies"][STRATEGY]                      # the JRM variant shares these rules by construction (differs_only_in)
    led = ledger or Ledger(study["exposure"])
    cs = cands if prepared else [prepare(r, study, base) for r in cands]
    verified = clocks is not None and clocks.get("board_commit") is not None and clocks.get("forecast_commit") is not None
    for c in cs:
        c["strategy_id"] = strategy_id
        c["blockers"] = block_reasons(c, scfg, study, forecast_archive, clocks)
        c["independent_clocks_checked"] = bool(verified)
        c["prospective"] = bool(c["prospective"] and verified)            # fail closed: no independent archive proof -> never counted as prospective
        c["decision"], c["reason"] = "NO_TRADE", (c["blockers"][0] if c["blockers"] else None)
        c["exposure_after"] = None
    elig = [c for c in cs if not c["blockers"]]
    by_cp: dict[Any, list[dict]] = defaultdict(list)
    for c in elig:
        by_cp[c["checkpoint"]].append(c)
    for key in sorted(by_cp):
        grp = by_cp[key]
        best: dict[str, dict] = {}
        for c in sorted(grp, key=lambda x: (-x[ev_key], x["price"], x["ticker"], x["side"])):
            best.setdefault(c["thesis_id"], c)
        for c in grp:
            if best[c["thesis_id"]] is not c:
                c["reason"] = "NOT_BEST_IN_THESIS"
        for c in sorted(best.values(), key=lambda x: (-x[ev_key], x["ticker"], x["side"])):
            cost = c["effective_entry_exec"] * int(study["execution"]["order_contracts"])
            cap = led.caps_hit(c, cost)
            if cap:
                c["reason"] = cap
                continue
            c["exposure_after"] = led.admit(c, cost)
            c["decision"], c["reason"] = "TRADE", "EV_ABOVE_THRESHOLD"
    return cs


# ================================================================================================ loading from the archives
def load_candidates(D, study: dict, base: dict, forecast_archive: dict[str, str] | None) -> list[dict]:
    """PF_ALL_CANDIDATES_V1 side rows of the checkpoint horizon (evaluate.Data.dec: cleaned, with archived settlements joined)."""
    d = D.dec
    if d is None or d.empty:
        return []
    h = study["checkpoint"]["horizon"]
    m = d[(d["strategy_id"] == "PF_ALL_CANDIDATES_V1") & (d["horizon"] == h) & d["side"].isin(["YES", "NO"])]
    if "compact" in m.columns:
        m = m[~m["compact"].fillna(False).astype(bool)]
    out = []
    for r in m.to_dict("records"):
        r["as_of_utc"] = r.get("as_of_utc") if isinstance(r.get("as_of_utc"), str) else MK.iso(_ts(r["as_of"]))
        out.append(prepare(r, study, base))
    return out


def forecast_archive_index(archive: str) -> dict[str, str]:
    """forecast_id -> archived_utc for player forecasts (pf_core archive) and game forecasts (paper store)."""
    from pf_core import prospective as pr
    from . import store
    idx: dict[str, str] = {}
    try:
        for r in pr._read(archive, "forecasts", "NBA", None):
            if r.get("forecast_id") and r.get("archived_utc"):
                idx[r["forecast_id"]] = r["archived_utc"]
    except Exception:  # noqa: BLE001
        pass
    for r in store.read(archive, "game_forecasts"):
        if r.get("game_forecast_id") and r.get("archived_utc"):
            idx[r["game_forecast_id"]] = r["archived_utc"]
    return idx


def forecast_archive_index_from(fc_records: list[dict], gf_records: list[dict]) -> dict[str, str]:
    """forecast_id / game_forecast_id -> self-reported archived_utc, from record lists already in memory."""
    idx = {r["forecast_id"]: r["archived_utc"] for r in fc_records if r.get("forecast_id") and r.get("archived_utc")}
    idx.update({r["game_forecast_id"]: r["archived_utc"] for r in gf_records if r.get("game_forecast_id") and r.get("archived_utc")})
    return idx


def board_commit_index(repo: str, ref: str = "origin/data-archive") -> dict[str, str]:
    """capture tick (UTC ISO, exactly as the chain reader derives it from the FILE NAME stamp) -> git commit time of the commit that ADDED that tick's checkpoint / delta file
    to the capture branch. Path-based, not commit-subject-based: subjects differ from the file stamps by 1-3 s on ~23% of ticks (measured), and a path is unique.
    History older than the fetched depth is simply absent (-> BOARD_ARCHIVE_UNVERIFIED)."""
    import re
    import subprocess
    out = subprocess.run(["git", "-C", repo, "log", ref, "--diff-filter=A", "--no-renames", "--name-only", "--format=@@%cI", "--", "kalshi/markets", "kalshi/markets_delta"],
                         capture_output=True, text=True, check=True).stdout
    idx: dict[str, str] = {}
    cur = None
    for line in out.splitlines():
        if line.startswith("@@"):
            cur = MK.iso(MK.parse_ts(line[2:]))
            continue
        m = re.search(r"kalshi_markets(?:_delta)?_(\d{8}T\d{6}Z)_", line)
        if m and cur:
            tick = MK.iso(datetime.strptime(m.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=MK.timezone.utc))
            if tick not in idx or cur < idx[tick]:
                idx[tick] = cur
    return idx


def forecast_commit_index(archive: str, repo: str, ref: str = "origin/projection-data") -> dict[str, str]:
    """forecast_id / game_forecast_id -> git commit time of the commit that added the file holding it to the data branch."""
    import glob
    import gzip
    import os
    import subprocess
    out = subprocess.run(["git", "-C", repo, "log", ref, "--diff-filter=A", "--name-only", "--format=@@%cI", "--", "forecasts/nba", "game_forecasts/nba"],
                         capture_output=True, text=True, check=True).stdout
    added: dict[str, str] = {}
    cur = None
    for line in out.splitlines():
        if line.startswith("@@"):
            cur = MK.iso(MK.parse_ts(line[2:]))
        elif line.strip():
            added[line.strip()] = cur
    idx: dict[str, str] = {}
    for sub, field in (("forecasts/nba", "forecast_id"), ("game_forecasts/nba", "game_forecast_id")):
        for p in sorted(glob.glob(os.path.join(archive, sub, "*", "*.jsonl.gz"))):
            t = added.get(os.path.relpath(p, archive))
            if t is None:
                continue
            with gzip.open(p, "rt") as f:
                for line in f:
                    if line.strip():
                        i = json.loads(line).get(field)
                        if i:
                            idx[i] = t
    return idx


# ================================================================================================ game-level status
def game_status(cs: list[dict], D, study: dict) -> list[dict]:
    """One row per game with any archived decision: TRADED / NO_TRADE (with the reason) / NOT_DUE. Non-traded games are never dropped."""
    d = D.dec
    if d is None or d.empty:
        return []
    horizon = study["checkpoint"]["horizon"]
    data_now = pd.to_datetime(d["as_of_utc"], utc=True, errors="coerce").max().to_pydatetime()
    miss: dict[str, str] = {}
    sn = D.snaps
    if sn is not None and len(sn) and "quote_class" in sn.columns:
        for r in sn[(sn["quote_class"] == "MISSING") & (sn["horizon"] == horizon)].to_dict("records"):
            miss[r["game_id"]] = str(r.get("missing_cause"))
    by_game: dict[str, list[dict]] = defaultdict(list)
    for c in cs:
        by_game[c["game_id"]].append(c)
    out = []
    games = d.drop_duplicates("game_id")[["game_id", "game_start_utc", "game_date_et"]].to_dict("records")
    for g in sorted(games, key=lambda x: (x["game_start_utc"], x["game_id"])):
        tip = _ts(g["game_start_utc"])
        cp = checkpoint_of(tip, study)
        rows = by_game.get(g["game_id"], [])
        trades = [c for c in rows if c["decision"] == "TRADE"]
        if trades:
            status, why = "TRADED", None
        elif not rows:
            status = "NOT_DUE" if cp > data_now else "NO_TRADE"
            why = None if status == "NOT_DUE" else (f"NO_CHECKPOINT_BOARD:{miss[g['game_id']]}" if g["game_id"] in miss else "NO_CHECKPOINT_DECISIONS_ARCHIVED")
        else:
            status = "NO_TRADE"
            cnt = Counter((c["reason"] or "ELIGIBLE_NOT_SELECTED").split(":")[0] for c in rows if c["reason"] != "NOT_BEST_IN_THESIS")
            why = "; ".join(f"{k}={v}" for k, v in cnt.most_common(4))
        out.append({"game_id": g["game_id"], "game_start_utc": g["game_start_utc"], "checkpoint_utc": MK.iso(cp), "after_prospective_start": bool(cp >= _ts(study["prospective_start_utc"])), "prospective": False,
                    "status": status, "reason": why, "n_candidate_sides": len(rows), "n_eligible": sum(1 for c in rows if not c["blockers"]),
                    "n_trades": len(trades)})
    return out


# ================================================================================================ metrics
def _frame(cs: list[dict]) -> pd.DataFrame:
    keep = ["decision_id", "candidate_id", "game_id", "game_date_et", "entity_id", "unit_id", "thesis_id", "player_name", "family", "side", "ticker", "team",
            "threshold", "k", "price", "effective_entry_exec", "fee_int", "spread", "top_size", "p_model", "p_cond", "p_play", "ev_net_exec", "ev_net",
            "quote_age_at_checkpoint_s", "computation_lag_s", "decision_mode", "prospective", "decision", "reason", "tip", "checkpoint", "as_of",
            "won", "net_pnl", "clv_cents", "closing_line", "dnp", "dnp_value_source", "fee_paid", "settled", "horizon", "forecast_generated_utc"]
    return pd.DataFrame([{k: c.get(k) for k in keep} for c in cs], columns=keep)


def _grp(g: pd.DataFrame) -> dict[str, Any]:
    n = len(g)
    s = g[g["settled"].fillna(False).astype(bool)] if n else g
    cost = (s["effective_entry_exec"] + s["fee_paid"].fillna(s["fee_int"])) if len(s) else pd.Series(dtype=float)
    return {"n_trades": int(n), "n_settled": int(len(s)), "n_games": int(g["game_id"].nunique()) if n else 0,
            "n_player_games": int(g["unit_id"].nunique()) if n else 0,
            "total_net_pnl": ST._f(s["net_pnl"].sum()) if len(s) else None, "cash_outlay": ST._f(cost.sum()) if len(s) else None,
            "roi_on_cash_outlay": ST._f(s["net_pnl"].sum() / cost.sum()) if len(s) and cost.sum() > 0 else None,
            "hit_rate": ST._f(s["won"].astype(float).mean()) if len(s) and s["won"].notna().any() else None,
            "n_dnp_settled_at_fair_price": int(s["dnp"].fillna(False).astype(bool).sum()) if len(s) else 0}


def max_drawdown(g: pd.DataFrame) -> dict[str, Any]:
    s = g[g["settled"].fillna(False).astype(bool)].sort_values(["tip", "decision_id"])
    if s.empty:
        return {"max_drawdown": None, "n": 0}
    eq = np.concatenate([[0.0], np.cumsum(s["net_pnl"].astype(float).to_numpy())])
    dd = np.maximum.accumulate(eq) - eq
    return {"max_drawdown": ST._f(dd.max()), "n": int(len(s)), "final_equity": ST._f(eq[-1]),
            "note": "dollars, 1 contract per position, ordered by tip time; a path statistic of a handful of games, not a risk estimate"}


def portfolio_metrics(cs: list[dict], study: dict, *, label: str, clocks_verified: bool | None = None) -> dict[str, Any]:
    """All metrics of the issue for one population of candidate rows (already run through `select`). Counts honestly; CIs only where defensible."""
    ev = study["evidence"]
    f = _frame(cs)
    out: dict[str, Any] = {"label": label, "strategy_id": cs[0]["strategy_id"] if cs else None, "n_candidate_sides": int(len(f))}
    if f.empty:
        return {**out, "status": "NO_DATA", "reason": "no candidate rows at the checkpoint in this population"}
    tr = f[f["decision"] == "TRADE"].copy()
    blk = Counter()
    for c in cs:
        for b in (c["blockers"] or []):
            blk[b] += 1
    out["eligible_vs_blocked"] = {"candidate_sides": int(len(f)), "eligible_sides": int(sum(1 for c in cs if not c["blockers"])),
                                  "blocked_sides": int(sum(1 for c in cs if c["blockers"])), "trades": int(len(tr)),
                                  "primary_block_reason": dict(Counter((c["blockers"][0] if c["blockers"] else "ELIGIBLE") for c in cs).most_common()),
                                  "any_block_reason": dict(blk.most_common()),
                                  "eligible_not_traded_reason": dict(Counter(c["reason"] for c in cs if not c["blockers"] and c["decision"] != "TRADE"))}
    if tr.empty:
        return {**out, "status": "NO_TRADES", "reason": "no candidate passed every rule: NO_TRADE for the whole population is a valid result",
                "n_games_with_candidates": int(f["game_id"].nunique())}
    tr["settled"] = tr["settled"].fillna(False).astype(bool)
    st = tr[tr["settled"]].copy()
    out["status"] = "OK"
    out["independent_units"] = {"n_decisions": int(len(tr)), "n_games": int(tr["game_id"].nunique()), "n_player_games": int(tr["unit_id"].nunique()),
                                "n_theses": int(tr["thesis_id"].nunique()), "n_settled_decisions": int(len(st)),
                                "note": "rungs, sides and snapshots are never independent bets; the unit is the game (cluster) and the player-game"}
    out["overall"] = _grp(tr)
    if len(st):
        cost = st["effective_entry_exec"] + st["fee_paid"].fillna(st["fee_int"])
        rg = ST.cluster_ratio(st["net_pnl"], cost, st["game_id"])
        rp = ST.cluster_ratio(st["net_pnl"], cost, st["unit_id"])
        rs = ST.cluster_ratio(st["net_pnl"], st["price"], st["game_id"])
        out["roi"] = {"on_cash_outlay_effective_entry_plus_fee": {"game_clustered": rg, "player_game_clustered": rp},
                      "on_quoted_price_scorecard_compatible": rs,
                      "mean_net_pnl_per_contract": ST.cluster_mean(st["net_pnl"], st["game_id"]),
                      "max_drawdown": max_drawdown(tr), "fees_per_contract_mean": ST._f(st["fee_paid"].fillna(st["fee_int"]).mean()),
                      "slippage_per_contract": float(study["execution"]["slippage"])}
        valid = st.apply(lambda r: isinstance(r["closing_line"], dict) and bool(r["closing_line"].get("valid")), axis=1) & st["clv_cents"].notna()
        sv = st[valid]
        out["clv_cents"] = {**ST.cluster_mean(sv["clv_cents"], sv["game_id"]), "share_positive": ST._f((sv["clv_cents"] > 0).mean()) if len(sv) else None,
                            "n_valid": int(len(sv)), "n_settled": int(len(st)), "note": "only trades with a VALID closing line (two-sided, <= 15 min before tip) count"}
        out["by_family"] = {k: _grp(g) for k, g in tr.groupby("family")}
        out["by_side"] = {k: _grp(g) for k, g in tr.groupby("side")}
        out["by_edge_bucket"] = {str(k): _grp(g) for k, g in tr.assign(b=pd.cut(tr["ev_net_exec"], EDGE_BINS, labels=EDGE_LABELS, right=False)).groupby("b", observed=True)}
        out["by_quote_age"] = {str(k): _grp(g) for k, g in tr.assign(b=pd.cut(tr["quote_age_at_checkpoint_s"], [-1, 120, 300, 900, 1e9], labels=["<=120s", "120-300s", "300-900s", ">900s"])).groupby("b", observed=True)}
        out["by_decision_mode"] = {k: _grp(g) for k, g in tr.groupby("decision_mode")}
        out["dnp"] = {"n_dnp": int(tr["dnp"].fillna(False).astype(bool).sum()), "sources": dict(Counter(tr["dnp_value_source"].dropna()))}
    out["exposure_concentration"] = concentration(tr)
    out["computation_lag_s"] = {"mean": ST._f(tr["computation_lag_s"].mean()), "max": ST._f(tr["computation_lag_s"].max()),
                                "note": "decided_utc - as_of_utc: how long after the information cut-off the decision row was actually computed (asof_replay)"}
    pro = st[st["prospective"].fillna(False).astype(bool)] if len(st) else st                  # only PROSPECTIVE, SETTLED decisions can count toward the minimums
    n_dec, n_games = len(pro), pro["game_id"].nunique() if len(pro) else 0
    lows = []
    if len(pro):
        cost_p = pro["effective_entry_exec"] + pro["fee_paid"].fillna(pro["fee_int"])
        lows = [ST.cluster_ratio(pro["net_pnl"], cost_p, pro["game_id"])["ci95"][0], ST.cluster_ratio(pro["net_pnl"], cost_p, pro["unit_id"])["ci95"][0]]
    meets = n_dec >= ev["min_decisions"] and n_games >= ev["min_games"]
    lo_ok = bool(lows) and all(x is not None and x > 0 for x in lows)
    out["evidence_status"] = {"counted": "prospective AND settled decisions only", "label": "INSUFFICIENT_SAMPLE" if not meets else ("POSITIVE_CI_PAPER_ONLY" if lo_ok else "NOT_ESTABLISHED"),
                              "have": {"decisions": int(n_dec), "games": int(n_games)}, "required": {"decisions": ev["min_decisions"], "games": ev["min_games"]},
                              "lower_cis_game_and_player_game": lows, "independent_clocks_verified": clocks_verified,
                              "authority": "none; never a value claim below the minimums"}
    if out["evidence_status"]["label"] == "POSITIVE_CI_PAPER_ONLY" and not clocks_verified:
        out["evidence_status"]["label"] = "NOT_ESTABLISHED_CLOCKS_UNVERIFIED"
    return out


def concentration(tr: pd.DataFrame) -> dict[str, Any]:
    if tr.empty:
        return {}
    cost = tr["effective_entry_exec"].astype(float)
    tot = cost.sum()

    def share(col: str) -> dict[str, float]:
        s = cost.groupby(tr[col].fillna("-")).sum() / tot
        return {str(k): ST._f(v) for k, v in s.sort_values(ascending=False).head(5).items()}
    return {"share_of_notional_by_game": share("game_id"), "share_of_notional_by_player": share("entity_id"), "share_of_notional_by_family": share("family"),
            "share_of_notional_by_side": share("side"), "share_NO": ST._f((tr["side"] == "NO").mean()),
            "max_trades_per_player_game": int(tr.groupby("unit_id").size().max()),
            "players_with_multiple_trades": int((tr.groupby("unit_id").size() > 1).sum()),
            "note": "trades on one player-game share one outcome (points/PRA/threes of the same player are strongly correlated)"}


def split_populations(cs: list[dict]) -> dict[str, list[dict]]:
    return {"prospective": [c for c in cs if c["prospective"]], "retrospective_descriptive": [c for c in cs if not c["prospective"]]}


def opening_hour_effect(tr: pd.DataFrame, snaps: pd.DataFrame | None) -> dict[str, Any]:
    """Hours between the contract's first archived two-sided board (horizon OPEN) and the checkpoint decision: do trades cluster in fresh listings?"""
    if tr.empty or snaps is None or snaps.empty or "horizon" not in snaps.columns:
        return {"status": "NO_DATA", "reason": "no OPEN snapshots or no trades"}
    op = snaps[(snaps["horizon"] == "OPEN") & snaps["board_observed_utc"].notna()].drop_duplicates("ticker").set_index("ticker")["board_observed_utc"]
    h = []
    for r in tr.to_dict("records"):
        o = op.get(r["ticker"])
        h.append(None if o is None else (r["as_of"] - _ts(o)).total_seconds() / 3600.0)
    tr = tr.assign(hours_since_open=pd.to_numeric(pd.Series(h, index=tr.index), errors="coerce"))
    b = pd.cut(tr["hours_since_open"], [-1e9, 1, 6, 1e9], labels=["<=1h", "1-6h", ">6h"])
    b = b.astype(object).where(tr["hours_since_open"].notna(), "unknown")
    return {"status": "OK", "definition": "as_of - first OPEN board of the ticker", "buckets": {str(k): _grp(g) for k, g in tr.groupby(b)}}


# ================================================================================================ replay fidelity: contemporaneous cross-check
def contemporaneous_runs(D, study: dict) -> pd.DataFrame:
    """Per game, the contemporaneous (LIVE) runs that exist with their minutes-to-tip, and the one nearest the T-60 checkpoint."""
    d = D.dec
    if d is None or d.empty:
        return pd.DataFrame()
    m = d[(d["strategy_id"] == "PF_ALL_CANDIDATES_V1") & (d["decision_mode"] == "contemporaneous") & d["side"].isin(["YES", "NO"])]
    if m.empty:
        return pd.DataFrame()
    g = m.groupby(["game_id", "as_of_utc"]).agg(minutes_to_tip=("minutes_to_tip", "first"), n=("ticker", "size")).reset_index()
    g["dist_to_checkpoint_min"] = (g["minutes_to_tip"] - float(study["checkpoint"]["minutes_before_tip"])).abs()
    return g


def crosscheck_contemporaneous(D, study: dict, base: dict, forecast_archive: dict[str, str] | None, replay_selected: list[dict],
                               window: tuple[float, float] = (45.0, 75.0)) -> dict[str, Any]:
    """How well does the as-of REPLAY at T-60 agree with a genuinely contemporaneous run near T-60? Only games with such a run are comparable;
    the rest are reported as NO_DATA (opening-night contemporaneous coverage of the checkpoint is a finding in itself)."""
    runs = contemporaneous_runs(D, study)
    if runs.empty:
        return {"status": "NO_DATA", "reason": "no contemporaneous runs archived"}
    near = runs.sort_values("dist_to_checkpoint_min").groupby("game_id").head(1)
    out: dict[str, Any] = {"window_minutes_to_tip": list(window), "games": {}}
    d = D.dec
    s2 = json.loads(json.dumps(study))
    s2["checkpoint"]["allowed_decision_modes"] = ["contemporaneous"]
    s2["checkpoint"]["horizon"] = "LIVE"
    led = Ledger(study["exposure"])
    for r in near.sort_values("as_of_utc").to_dict("records"):
        inwin = window[0] <= r["minutes_to_tip"] <= window[1]
        info = {"nearest_run_as_of": r["as_of_utc"], "minutes_to_tip": r["minutes_to_tip"], "within_window": bool(inwin)}
        if inwin:
            rows = d[(d["strategy_id"] == "PF_ALL_CANDIDATES_V1") & (d["game_id"] == r["game_id"]) & (d["as_of_utc"] == r["as_of_utc"]) & d["side"].isin(["YES", "NO"])]
            cs = []
            for x in rows.to_dict("records"):
                c = prepare(x, s2, base)
                c["checkpoint"] = c["as_of"]
                c["quote_age_at_checkpoint_s"] = (c["checkpoint"] - c["board"]).total_seconds() if c["board"] else None
                cs.append(c)
            cs = select(cs, s2, base, ledger=led, forecast_archive=forecast_archive, prepared=True)
            live = {(c["ticker"], c["side"]) for c in cs if c["decision"] == "TRADE"}
            rep_g = {(c["ticker"], c["side"]) for c in replay_selected if c["decision"] == "TRADE" and c["game_id"] == r["game_id"]}
            info.update({"live_trades": len(live), "replay_trades_same_game": len(rep_g), "same_contracts": len(live & rep_g),
                         "live_only": len(live - rep_g), "replay_only": len(rep_g - live)})
        else:
            info["status"] = "NO_DATA: nearest contemporaneous run is outside the comparison window"
        out["games"][r["game_id"]] = info
    out["status"] = "OK" if any(g["within_window"] for g in out["games"].values()) else "NO_DATA"
    return out
