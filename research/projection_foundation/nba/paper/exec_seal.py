"""Sealed pre-tip ledger for the executable T-60 shadow study (Issue #53, owner review of PR #54; RESEARCH ONLY, read-only on every data branch).

Why. A study run AFTER a game can rebuild the T-60 portfolio from archives, but nothing then proves the choices existed before tip. The upstream paper engine's
`decided_utc` is not evidence about THIS study. So prospective evidence is a SEAL: a read-only job runs after the T-60 archive cut-off and before tip, evaluates
each due game with the frozen rules (`exec_shadow.select`), and persists an immutable, independently timestamped artifact on its own branch (`exec-shadow-seals`).
Post-game research JOINS settlements to the sealed ledger; it never recomputes or changes a selection from later archive state.

    python -m nba.paper.exec_seal plan     --context <data-archive> --seals <seal worktree> [--now ISO]            # which games have a window open
    python -m nba.paper.exec_seal seal     --archive <projection-data> --market <data-archive> --context <data-archive> --seals <dir> [--dry-run] [...]
    python -m nba.paper.exec_seal watch    --context ... --seals ...                                               # MISSED markers + exit code for alerts
    python -m nba.paper.exec_seal evaluate --seals ... --archive ... --market ...                                  # verify + join settlements (study53 calls it)

Rules (protocol v2.0.0, `exec_shadow_config_v2.json`, section `sealing`)
  * window per game: opens `earliest_after_checkpoint_s` after the T-60 checkpoint (capture ticks reach the capture branch ~3.4 min after observation), closes
    `deadline_before_tip_s` before tip. A game still unsealed after its window is MISSED (marker, alert), never sealed late as if on time;
  * the board is the latest capture tick OBSERVED at/before the checkpoint and must be COMMITTED to the capture branch at/before it; otherwise the game is NO_TRADE
    (no fallback to an earlier tick, no grace window); forecasts must be generated, self-archived AND committed at/before the checkpoint;
  * one global ledger: exposure state is replayed from the earlier seals, so the caps are never reset between games, days or runs;
  * a seal is write-once (a second attempt for the same game is a no-op) and records strategy id, protocol sha256, code sha and dirtiness, data refs, the market tick,
    forecast ids and commit times, the decision of EVERY candidate side with reasons (hashed file), selected decisions with prices and sizes, ledger before/after,
    computation time and source hashes;
  * counted only if `verify_seal` passes: body hash, protocol match, computation inside [prospective start, tip - deadline], independent commit time on the ledger
    branch within the window and not before the computation, code reachable from the default branch. Anything else is NO_DATA / uncounted, never prospective.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

from . import config as CFG
from . import engine as EN
from . import exec_shadow as X
from . import markets as MK
from . import probability as PR
from . import run as RUN
from . import schema as S
from . import settle as SE
from . import stats as ST

SCHEMA = "issue53.exec_seal.v1"
MODE = "sealed_pretip_asof"
UTC = timezone.utc
CAND_KEEP = ("candidate_id", "game_id", "game_date_et", "entity_id", "unit_id", "thesis_id", "player_name", "family", "stat", "side", "ticker", "team", "opponent", "threshold",
             "k", "price", "effective_entry_exec", "fee_int", "spread", "top_size", "depth_at_entry", "p_model", "p_cond", "p_play", "p_market_mid", "ev_net", "ev_net_exec",
             "quote_age_at_checkpoint_s", "computation_lag_s", "decision_mode", "decision", "reason", "blockers", "horizon", "forecast_generated_utc", "forecast_ids",
             "model_id", "model_version", "board_commit_utc", "forecast_commit_utc", "exposure_after", "quality", "gate", "fee_assumption", "bid", "ask", "slippage",
             "effective_entry", "snapshot_id", "board_observed_utc", "as_of_utc", "game_start_utc", "decided_utc", "event_ticker", "period", "comparator", "participation")


# ================================================================================================ small helpers
def canon(o: Any) -> bytes:
    return json.dumps(o, sort_keys=True, separators=(",", ":"), default=str).encode()


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def body_sha(body: dict) -> str:
    return sha256(canon({k: v for k, v in body.items() if k != "body_sha256"}))


def _iso(d: datetime | None) -> str | None:
    return None if d is None else MK.iso(d)


def _jsonable(c: dict) -> dict:
    out = {}
    for k in CAND_KEEP:
        v = c.get(k)
        if isinstance(v, datetime):
            v = MK.iso(v)
        out[k] = None if (isinstance(v, float) and v != v) else v
    for k in ("tip", "checkpoint", "as_of", "board", "decided"):
        if isinstance(c.get(k), datetime):
            out[k + "_utc"] = MK.iso(c[k])
    return out


def git(repo: str, *a: str) -> str:
    r = subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def code_info(repo: str, study_path: str | None = None) -> dict[str, Any]:
    """Code identity of the sealer: HEAD sha, dirtiness, the ref it runs from, and when the protocol file's CURRENT version landed on this checkout."""
    path = study_path or str(X.STUDY_PATH)
    rel = os.path.relpath(path, git(repo, "rev-parse", "--show-toplevel") or repo)
    return {"sha": git(repo, "rev-parse", "HEAD") or None, "dirty": bool(git(repo, "status", "--porcelain", "--untracked-files=no")),
            "ref": os.environ.get("GITHUB_REF"), "event": os.environ.get("GITHUB_EVENT_NAME"), "workflow": os.environ.get("GITHUB_WORKFLOW"),
            "run_id": os.environ.get("GITHUB_RUN_ID"), "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
            "protocol_path": rel, "protocol_effective_commit_utc": (lambda t: MK.iso(MK.parse_ts(t)) if t else None)(git(repo, "log", "-1", "--format=%cI", "--", rel))}


# ================================================================================================ schedule + windows
def _stamp(path: str) -> datetime | None:
    import re
    m = re.search(r"context_schedule_(\d{8}T\d{6}Z)", os.path.basename(path))
    return datetime.strptime(m.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC) if m else None


def schedule_games(context_dir: str, now: datetime, season_types: tuple[str, ...] = ("regular",), lookback_h: float = 6.0, horizon_h: float = 48.0,
                   snapshot_span_h: float = 36.0) -> list[dict]:
    """Games from the ESPN schedule snapshots of the capture branch observed at or before `now` within the last `snapshot_span_h` hours; the LATEST observation of a game
    wins (a postponed / moved tip is followed), and a game that has dropped out of the newest snapshot (finished, other ET day) is still known from an earlier one.
    Independent of our forecasts: a game without forecasts is still a game we owe a status."""
    files = [(st, p) for p in glob.glob(os.path.join(context_dir, "context", "schedule", "dt=*", "context_schedule_*.jsonl.gz"))
             if (st := _stamp(p)) is not None and now - timedelta(hours=snapshot_span_h) <= st <= now]
    out: dict[str, dict] = {}
    for st, p in sorted(files, key=lambda x: (x[0], x[1])):
        raw = open(p, "rb").read()
        digest = sha256(raw)
        for line in gzip.decompress(raw).decode().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("season_type") not in season_types or not r.get("start_time_utc"):
                continue
            out[r["game_id"]] = {"game_id": r["game_id"], "start_utc": MK.iso(MK.parse_ts(r["start_time_utc"])), "home": r["home_tricode"], "away": r["away_tricode"],
                                 "game_date_et": r.get("game_date_et"), "schedule_file": os.path.basename(p), "schedule_sha256": digest,
                                 "schedule_observed_utc": r.get("_observed_at_utc"), "status": r.get("status")}
    keep = [g for g in out.values() if now - timedelta(hours=lookback_h) <= MK.parse_ts(g["start_utc"]) <= now + timedelta(hours=horizon_h)]
    return sorted(keep, key=lambda g: (g["start_utc"], g["game_id"]))


def window(game: dict, study: dict) -> dict[str, datetime]:
    tip = MK.parse_ts(game["start_utc"])
    cp = X.checkpoint_of(tip, study)
    sc = study["sealing"]
    return {"tip": tip, "checkpoint": cp, "opens": cp + timedelta(seconds=sc["earliest_after_checkpoint_s"]), "closes": tip - timedelta(seconds=sc["deadline_before_tip_s"])}


def enabled_utc(seal_dir: str) -> datetime | None:
    """When the ledger was first enabled (file `ENABLED_UTC`, written by the first live run). Games whose window opened earlier were never ours to seal."""
    p = os.path.join(seal_dir, "ENABLED_UTC")
    try:
        return MK.parse_ts(open(p).read().strip())
    except (OSError, ValueError):
        return None


def mark_enabled(seal_dir: str, now: datetime) -> None:
    p = os.path.join(seal_dir, "ENABLED_UTC")
    if not os.path.exists(p):
        with open(p, "x") as f:
            f.write(MK.iso(now) + "\n")


def game_state(now: datetime, game: dict, study: dict, sealed: set[str], missed: set[str], enabled: datetime | None = None) -> str:
    w = window(game, study)
    if enabled is not None and w["opens"] < enabled and game["game_id"] not in sealed:
        return "BEFORE_ENABLED"
    if game["game_id"] in sealed:
        return "SEALED"
    if game["game_id"] in missed:
        return "MISSED"
    if now < w["opens"]:
        return "NOT_DUE"
    if now <= w["closes"]:
        return "OPEN"
    return "WINDOW_CLOSED_UNSEALED"


def list_sealed(seal_dir: str) -> tuple[set[str], set[str]]:
    sealed, missed = set(), set()
    for p in glob.glob(os.path.join(seal_dir, "seals", "*", "*.json")):
        sealed.add(os.path.basename(p).split("__")[0].replace("_", ":", 1))
    for p in glob.glob(os.path.join(seal_dir, "missed", "*.json")):
        missed.add(os.path.basename(p)[:-5].replace("_", ":", 1))
    return sealed, missed


def gid_file(gid: str) -> str:
    return gid.replace(":", "_", 1)


def plan(context_dir: str, seal_dir: str, now: datetime, study: dict) -> dict[str, Any]:
    games = schedule_games(context_dir, now)
    sealed, missed = list_sealed(seal_dir)
    en = enabled_utc(seal_dir)
    rows = []
    for g in games:
        w = window(g, study)
        rows.append({"game_id": g["game_id"], "tip_utc": g["start_utc"], "checkpoint_utc": _iso(w["checkpoint"]), "opens_utc": _iso(w["opens"]), "closes_utc": _iso(w["closes"]),
                     "state": game_state(now, g, study, sealed, missed, en)})
    c = Counter(r["state"] for r in rows)
    return {"now": _iso(now), "games": rows, "counts": dict(c), "due": bool(c.get("OPEN")), "needs_watch": bool(c.get("WINDOW_CLOSED_UNSEALED"))}


# ================================================================================================ sealing
def ledger_from_seals(seal_dir: str, study: dict) -> X.Ledger:
    """Exposure state replayed from the earlier non-dry-run seals in checkpoint order: the caps are global and never reset."""
    led = X.Ledger(study["exposure"])
    rows = []
    for body, _ in iter_seals(seal_dir):
        if body.get("dry_run") or body.get("status") != "TRADED":
            continue
        for pos in body.get("selected") or []:
            rows.append((body["checkpoint_utc"], body["game"]["game_id"], pos))
    for _, _, pos in sorted(rows, key=lambda x: (x[0], x[1], x[2]["ticker"])):
        led.admit(pos, float(pos["effective_entry_exec"]))
    return led


def iter_seals(seal_dir: str):
    for p in sorted(glob.glob(os.path.join(seal_dir, "seals", "*", "*.json"))):
        try:
            yield json.load(open(p)), p
        except (OSError, ValueError):
            yield {"_unreadable": True}, p


def _book_rows(market: str, cp: datetime, gap_max_s: int) -> tuple[Any, ...]:
    """(tick, board, why): the latest capture tick OBSERVED at/before the checkpoint within the allowed gap, reconstructed as-of that tick."""
    reader = MK.ChainReader(market, "markets")
    ticks = reader.ticks(cp - timedelta(seconds=gap_max_s), cp)
    if not ticks:
        return None, None, "NO_BOARD_WITHIN_GAP"
    want = ticks[-1]
    board = None
    for dt, b in reader.walk(want, want):
        if dt == want:
            board = b
    if board is None:
        return want, None, "CHAIN_BROKEN"
    return want, board, None


def seal_games(games: list[dict], archive: str, market: str, seal_dir: str, now: datetime, study: dict, base: dict, clocks: dict, code: dict, *,
               dry_run: bool = False, extra_inputs: dict | None = None) -> dict[str, Any]:
    """Evaluate and seal every given game whose window is open. Returns a report; writes seals unless dry_run (then to nothing)."""
    sealed, missed = list_sealed(seal_dir)
    en = enabled_utc(seal_dir)
    due = [g for g in games if game_state(now, g, study, sealed, missed, en) == "OPEN"]
    rep: dict[str, Any] = {"now": _iso(now), "dry_run": dry_run, "due": [g["game_id"] for g in due], "sealed": [], "errors": []}
    if not due:
        return rep
    if not dry_run:
        mark_enabled(seal_dir, now)                       # first live run: games whose window opened earlier are not ours (never MISSED)
    fc_rec, gf_rec = RUN.load_inputs(archive, now, back_days=2, fwd_days=2)
    fcm, gcm = clocks.get("forecast_commit") or {}, clocks.get("forecast_commit") or {}
    ledger = ledger_from_seals(seal_dir, study)
    ledger_before = _ledger_state(ledger)
    prepared_all: list[dict] = []
    meta: dict[str, dict] = {}
    for g in due:
        w = window(g, study)
        cp = w["checkpoint"]
        m: dict[str, Any] = {"game": g, "w": w, "reason": None, "board": None}
        meta[g["game_id"]] = m
        gm = MK.Game.from_dict({"game_id": g["game_id"], "start_utc": g["start_utc"], "home": g["home"], "away": g["away"], "game_date_et": g.get("game_date_et")})
        tick, board, why = _book_rows(market, cp, 1800)
        m["board"] = {"tick_observed_utc": _iso(tick), "gap_s": None if tick is None else (cp - tick).total_seconds()}
        if why:
            m["reason"] = why
            continue
        bc = (clocks.get("board_commit") or {}).get(MK.iso(tick))
        m["board"]["commit_utc"] = bc
        if bc is None:
            m["reason"] = "BOARD_ARCHIVE_UNVERIFIED"
            continue
        if MK.parse_ts(bc) > cp:
            m["reason"] = "BOARD_COMMITTED_AFTER_CHECKPOINT"
            continue
        # forecasts: only records committed to projection-data at/before the checkpoint can exist for this decision
        fc_ok = [r for r in fc_rec if r.get("game_id") == g["game_id"] and fcm.get(r.get("forecast_id")) and MK.parse_ts(fcm[r["forecast_id"]]) <= cp]
        gf_ok = [r for r in gf_rec if r.get("game_id") == g["game_id"] and gcm.get(r.get("game_forecast_id")) and MK.parse_ts(gcm[r["game_forecast_id"]]) <= cp]
        m["forecasts"] = {"n_player_records_used": len(fc_ok), "n_game_records_used": len(gf_ok),
                          "n_player_records_late_or_unverified": sum(1 for r in fc_rec if r.get("game_id") == g["game_id"]) - len(fc_ok)}
        if not fc_ok:
            m["reason"] = "NO_FORECASTS_COMMITTED_BY_CHECKPOINT"
            continue
        gi = MK.GameIndex([gm])
        ob = MK.ChainReader(market, "orderbooks")
        rows, cov = MK.snapshot_rows(board, gi, gm, "T-60", cp, tick, book=RUN._book_at(ob, {}, tick))
        players = MK.PlayerIndex(fc_ok)
        RUN._fill_player_ids(rows, players)
        fc, gfc = PR.Forecasts(fc_ok, tick), PR.GameForecasts(gf_ok, tick)
        cands = EN.candidates_for(rows, fc, gfc, players, as_of=tick, decided=now, mode=MODE, cfg=base)
        sides = [c for c in cands if c["side"] in S.SIDES]
        m["coverage"] = dict(cov)
        m["n_rows"] = len(rows)
        if not sides:
            m["reason"] = "NO_EVALUABLE_CONTRACTS"
            continue
        for c in sides:
            p = X.prepare({**c, "settled": False}, study, base)
            p["game_ref"] = g["game_id"]
            prepared_all.append(p)
        m["fc_ids"] = sorted({i for r in fc_ok for i in [r.get("forecast_id")] if i} | {r.get("game_forecast_id") for r in gf_ok if r.get("game_forecast_id")})
    fa = X.forecast_archive_index_from(fc_rec, gf_rec)
    selected_all = X.select(prepared_all, study, base, forecast_archive=fa, prepared=True, clocks=clocks, ledger=ledger) if prepared_all else []
    by_game: dict[str, list[dict]] = defaultdict(list)
    for c in selected_all:
        by_game[c["game_id"]].append(c)
    after = _ledger_state(ledger)
    seal_paths: list[str] = []
    for g in due:
        gid = g["game_id"]
        m = meta[gid]
        cs = by_game.get(gid, [])
        trades = [c for c in cs if c["decision"] == "TRADE"]
        status = "TRADED" if trades else "NO_TRADE"
        reason = m["reason"] if (m["reason"] and not cs) else (None if trades else _dominant_reason(cs))
        rows_json = [_jsonable(c) for c in cs]
        cand_bytes = gzip.compress("\n".join(json.dumps(r, sort_keys=True, default=str) for r in rows_json).encode(), mtime=0)
        w = m["w"]
        body = {
            "schema": SCHEMA, "study_id": study["study_id"], "study_version": study["version"], "strategy_id": X.STRATEGY, "protocol_sha256": X.study_sha(),
            "paper_config_sha256": CFG.config_sha(), "decision_mode": MODE, "dry_run": bool(dry_run),
            "game": {k: g.get(k) for k in ("game_id", "start_utc", "home", "away", "game_date_et", "schedule_file", "schedule_sha256", "schedule_observed_utc")},
            "checkpoint_utc": _iso(w["checkpoint"]), "window": {"opens_utc": _iso(w["opens"]), "closes_utc": _iso(w["closes"])}, "computed_utc": _iso(now),
            "status": status, "game_reason": reason, "board": m["board"], "forecasts": m.get("forecasts"), "forecast_ids_sha256": sha256(canon(m.get("fc_ids") or [])),
            "candidates": {"n_sides": len(cs), "n_eligible": sum(1 for c in cs if not c["blockers"]), "n_trades": len(trades),
                           "file": f"{gid_file(gid)}__candidates.jsonl.gz", "sha256": sha256(cand_bytes),
                           "primary_reason_histogram": dict(Counter((c["blockers"][0] if c["blockers"] else (c["reason"] or "ELIGIBLE")) for c in cs).most_common())},
            "selected": [{k: (MK.iso(v) if isinstance(v, datetime) else v) for k, v in _jsonable(c).items()} for c in trades],
            "ledger_before": ledger_before, "ledger_after": after if trades else ledger_before,
            "code": code, "inputs": {**(extra_inputs or {}), "coverage": m.get("coverage"), "n_snapshot_rows": m.get("n_rows")},
            "clocks": {"board_commit_index_ticks": len(clocks.get("board_commit") or {}), "forecast_commit_index_ids": len(clocks.get("forecast_commit") or {})},
        }
        body["seal_id"] = sha256(canon([gid, body["protocol_sha256"], body["board"].get("tick_observed_utc"), body["computed_utc"]]))[:20]
        body["body_sha256"] = body_sha(body)
        rep["sealed"].append({"game_id": gid, "status": status, "reason": reason, "trades": len(trades), "seal_id": body["seal_id"], "candidates": len(cs),
                              "deadline_utc": _iso(w["closes"]), "tip_utc": g["start_utc"], "board": m["board"],
                              "selected": [{"ticker": x["ticker"], "side": x["side"], "price": x["price"], "ev_net_exec": round(x["ev_net_exec"], 4)} for x in body["selected"]]})
        if dry_run:
            continue
        day = MK.parse_ts(g["start_utc"]).strftime("%Y-%m-%d")
        d = os.path.join(seal_dir, "seals", day)
        os.makedirs(d, exist_ok=True)
        jp = os.path.join(d, f"{gid_file(gid)}__{body['seal_id']}.json")
        cp_ = os.path.join(d, body["candidates"]["file"])
        if glob.glob(os.path.join(d, f"{gid_file(gid)}__*.json")):
            rep["errors"].append({"game_id": gid, "error": "ALREADY_SEALED_NOOP"})
            continue
        with open(cp_, "xb") as f:
            f.write(cand_bytes)
        with open(jp, "x") as f:
            json.dump(body, f, indent=1, sort_keys=True, default=str)
            f.write("\n")
        seal_paths += [jp, cp_]
    rep["paths"] = [os.path.relpath(p, seal_dir) for p in seal_paths]
    return rep


def _ledger_state(led: X.Ledger) -> dict:
    return {"n_unit": dict(led.n_unit), "n_team": dict(led.n_team), "n_game": dict(led.n_game), "notional_game": {k: round(v, 4) for k, v in led.notional_game.items()},
            "notional_day": {k: round(v, 4) for k, v in led.notional_day.items()}, "theses": sorted(led.theses)}


def _dominant_reason(cs: list[dict]) -> str:
    h = Counter((c["blockers"][0] if c["blockers"] else (c["reason"] or "ELIGIBLE")) for c in cs)
    return "; ".join(f"{k}={v}" for k, v in h.most_common(4)) if h else "NO_CANDIDATES"


def mark_missed(games: list[dict], seal_dir: str, now: datetime, study: dict, *, dry_run: bool = False) -> list[dict]:
    """Record a MISSED marker for every game whose window closed without a seal. Never creates a seal; never counted."""
    sealed, missed = list_sealed(seal_dir)
    en = enabled_utc(seal_dir)
    out = []
    for g in games:
        if game_state(now, g, study, sealed, missed, en) != "WINDOW_CLOSED_UNSEALED":
            continue
        w = window(g, study)
        rec = {"schema": SCHEMA + ".missed", "game_id": g["game_id"], "tip_utc": g["start_utc"], "checkpoint_utc": _iso(w["checkpoint"]), "window_closed_utc": _iso(w["closes"]),
               "detected_utc": _iso(now), "status": "MISSED", "counted": False,
               "reason": "no seal was committed inside the window (scheduler delay / runner outage / archive lag); uncounted, never sealed late", "protocol_sha256": X.study_sha()}
        out.append(rec)
        if not dry_run:
            os.makedirs(os.path.join(seal_dir, "missed"), exist_ok=True)
            with open(os.path.join(seal_dir, "missed", f"{gid_file(g['game_id'])}.json"), "x") as f:
                json.dump(rec, f, indent=1, sort_keys=True)
                f.write("\n")
    return out


# ================================================================================================ verification (post-game, offline)
def seal_commit_times(seal_dir: str) -> dict[str, str]:
    """relative path -> independent git commit time of the commit that ADDED it to the ledger branch."""
    if not os.path.isdir(os.path.join(seal_dir, ".git")) and not git(seal_dir, "rev-parse", "--git-dir"):
        return {}
    out = subprocess.run(["git", "-C", seal_dir, "log", "--diff-filter=A", "--name-only", "--format=@@%cI", "--", "seals", "missed"], capture_output=True, text=True).stdout
    cur, res = None, {}
    for line in out.splitlines():
        if line.startswith("@@"):
            cur = MK.iso(MK.parse_ts(line[2:]))
        elif line.strip():
            res[line.strip()] = cur
    return res


def verify_seal(body: dict, path_rel: str, commit_times: dict[str, str], study: dict, *, protocol_sha: str, seal_dir: str, code_reachable: bool | None) -> tuple[bool, list[str]]:
    """(counted, reasons). Every failure is listed; counted only with an empty list."""
    why: list[str] = []
    sc = study["sealing"]
    if body.get("_unreadable"):
        return False, ["UNREADABLE"]
    if body.get("schema") != SCHEMA:
        why.append("SCHEMA")
    if body.get("body_sha256") != body_sha(body):
        why.append("BODY_HASH_MISMATCH")
    cf = os.path.join(os.path.dirname(os.path.join(seal_dir, path_rel)), body.get("candidates", {}).get("file", ""))
    try:
        if sha256(open(cf, "rb").read()) != body["candidates"]["sha256"]:
            why.append("CANDIDATES_HASH_MISMATCH")
    except (OSError, KeyError):
        why.append("CANDIDATES_FILE_MISSING")
    if body.get("dry_run"):
        why.append("DRY_RUN_SEAL")
    if body.get("protocol_sha256") != protocol_sha or body.get("study_version") != study["version"]:
        why.append("PROTOCOL_MISMATCH")
    start = MK.parse_ts(study["prospective_start_utc"])
    tip = MK.parse_ts(body["game"]["start_utc"])
    comp = MK.parse_ts(body["computed_utc"]) if body.get("computed_utc") else None
    cp = MK.parse_ts(body["checkpoint_utc"])
    deadline = tip - timedelta(seconds=sc["deadline_before_tip_s"])
    opens = cp + timedelta(seconds=sc["earliest_after_checkpoint_s"])
    if comp is None or comp < start or cp < start:
        why.append("BEFORE_PROSPECTIVE_START")
    if comp is not None and (comp < opens or comp > deadline):
        why.append("COMPUTED_OUTSIDE_WINDOW")
    ct = commit_times.get(path_rel)
    if ct is None:
        why.append("NO_INDEPENDENT_COMMIT_TIME")
    else:
        ctt = MK.parse_ts(ct)
        if comp is not None and ctt < comp - timedelta(seconds=120):
            why.append("COMMIT_BEFORE_COMPUTATION")          # a seal cannot be committed before it was computed
        if ctt > deadline:
            why.append("COMMITTED_AFTER_DEADLINE")
    code = body.get("code") or {}
    if not code.get("sha") or code.get("dirty"):
        why.append("CODE_UNPINNED_OR_DIRTY")
    ref = code.get("ref") or ""
    if not ref.startswith("refs/heads/") or code.get("event") not in ("schedule", "workflow_dispatch"):
        why.append("NOT_A_DEFAULT_BRANCH_RUN")
    if code_reachable is not True:
        why.append("CODE_NOT_REACHABLE_FROM_DEFAULT_BRANCH" if code_reachable is False else "CODE_REACHABILITY_UNVERIFIED")
    pc = code.get("protocol_effective_commit_utc")
    if not pc or MK.parse_ts(pc) >= start:
        why.append("PROTOCOL_COMMIT_NOT_BEFORE_START")
    if not (body.get("clocks") or {}).get("board_commit_index_ticks") or not (body.get("clocks") or {}).get("forecast_commit_index_ids"):
        why.append("INDEPENDENT_CLOCKS_NOT_RECORDED")
    if body.get("status") == "TRADED" and not (body.get("board") or {}).get("commit_utc"):
        why.append("BOARD_COMMIT_NOT_RECORDED")
    return not why, why


def load_candidates(seal_dir: str, body: dict, path_rel: str) -> list[dict]:
    cf = os.path.join(os.path.dirname(os.path.join(seal_dir, path_rel)), body["candidates"]["file"])
    rows = []
    with gzip.open(cf, "rt") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def hydrate(row: dict, body: dict, study: dict, counted: bool) -> dict:
    c = dict(row)
    for k in ("tip", "checkpoint", "as_of", "board", "decided"):
        v = c.get(k + "_utc")
        c[k] = MK.parse_ts(v) if v else None
    c["tip"] = c["tip"] or MK.parse_ts(body["game"]["start_utc"])
    c["checkpoint"] = c["checkpoint"] or MK.parse_ts(body["checkpoint_utc"])
    c["as_of"] = c["as_of"] or MK.parse_ts(c["as_of_utc"])
    c["strategy_id"] = X.STRATEGY
    c["blockers"] = c.get("blockers") or []
    c["prospective"] = bool(counted)
    c["origin"] = "sealed_pretip"
    c["seal_id"] = body["seal_id"]
    c["settled"] = False
    for k in ("won", "net_pnl", "clv_cents", "closing_line", "dnp", "dnp_value_source", "fee_paid"):
        c.setdefault(k, None)
    return c


# ================================================================================================ settlement join (post-game; never changes a selection)
def settle_sealed(trades: list[dict], archive: str | None, market: str | None, now: datetime, base: dict) -> dict[str, Any]:
    """Attach the paper system's settlement to SEALED trades (Kalshi result first, box-derived second, DNP at the fair price). Selections are not touched."""
    st: Counter = Counter()
    if not trades:
        return dict(st)
    outs = SE._latest_outcomes(archive) if archive else {}
    teams: dict[tuple, dict] = {}
    if archive:
        from . import store
        for r in sorted(store.read(archive, "team_outcomes"), key=lambda x: x.get("observed_utc") or ""):
            teams[(r["game_id"], r["team"])] = r
            teams[(r["game_id"], None)] = r
    reader = MK.ChainReader(market, "markets") if market else None
    cutoff = now - timedelta(hours=2)
    todo = [c for c in trades if c["tip"] <= cutoff]
    auth = SE.authoritative_results(reader, {c["ticker"]: c["tip"] for c in todo}, now) if (reader and todo) else {}
    for c in trades:
        if c["tip"] > cutoff:
            st["PENDING_GAME_NOT_OVER"] += 1
            continue
        d = {**c, "decision_id": S.decision_id(X.STRATEGY, c["candidate_id"], c["ticker"], c["side"]), "cluster_id": c["game_id"], "replay": False, "simulated_contracts": 1,
             "effective_entry": c["effective_entry_exec"], "game_start_utc": MK.iso(c["tip"]), "horizon": "T-60", "decision": "TRADE",
             "fee_assumption": c.get("fee_assumption") or {"multiplier": base["execution"]["fee_taker_multiplier"]}}
        o = None
        if d["family"] in SE.PROP_FAMILY and d.get("entity_id"):
            r = outs.get((d["game_id"], d["entity_id"], SE.PROP_FAMILY[d["family"]]))
            if r is not None:
                o = {"actual": 0.0, "participated": False} if not r.get("participated", True) else {"actual": r["actual"], "participated": True}
        closing = _closing(reader, c["ticker"], c["tip"]) if reader else SE.closing_for(None, c["tip"])
        row, why = SE.build_settlement(d, auth=auth.get(c["ticker"]), outcome=o, closing=closing, now=now,
                                       team=teams.get((d["game_id"], d.get("team"))) if d["family"] in SE.GAME_FAMILY else None)
        if row is None:
            st["PENDING_" + str(why)] += 1
            continue
        c.update({"settled": True, "won": row["won"], "net_pnl": row["net_pnl"], "clv_cents": row["clv_cents"], "closing_line": row["closing_line"], "dnp": row["dnp"],
                  "dnp_value_source": row["dnp_value_source"], "fee_paid": row["fee_paid"], "kalshi_result": row["kalshi_result"], "outcome_source": row["outcome_source"],
                  "gross_payoff": row["gross_payoff"]})
        st["SETTLED_" + row["outcome_source"]] += 1
    return dict(st)


def _closing(reader: MK.ChainReader, ticker: str, tip: datetime) -> dict:
    """LAST_VALID-style closing line straight from the capture chain: the last tick strictly before tip (valid only if two-sided and <= 15 min before tip)."""
    got = reader.board_at(tip - timedelta(seconds=1), lookback=timedelta(minutes=30))
    if got is None or got[1] is None or ticker not in got[1]:
        return SE.closing_for(None, tip)
    dt, board = got
    q = MK.quote(board[ticker])
    return SE.closing_for({"ticker": ticker, "board_observed_utc": MK.iso(dt), "quote_class": q["quote_class"], "yes_bid": q["yes_bid"], "yes_ask": q["yes_ask"]}, tip)


# ================================================================================================ evaluation
def evaluate(seal_dir: str, archive: str | None, market: str | None, now: datetime, study: dict, base: dict, *, code_repo: str | None = None,
             default_branch_ref: str = "origin/main", schedule: list[dict] | None = None) -> dict[str, Any]:
    """Verify every seal, join settlements to the COUNTED trades, and report every scheduled game (sealed / missed / not sealed). Selections are read, never recomputed."""
    protocol_sha = X.study_sha()
    cts = seal_commit_times(seal_dir)
    games: dict[str, dict] = {}
    all_cs: list[dict] = []
    counted_trades: list[dict] = []
    for body, p in iter_seals(seal_dir):
        rel = os.path.relpath(p, seal_dir)
        reach = None
        if code_repo and not body.get("_unreadable"):
            sha = (body.get("code") or {}).get("sha")
            if sha:
                r = subprocess.run(["git", "-C", code_repo, "merge-base", "--is-ancestor", sha, default_branch_ref], capture_output=True)
                reach = (r.returncode == 0) if r.returncode in (0, 1) else None
        ok, why = verify_seal(body, rel, cts, study, protocol_sha=protocol_sha, seal_dir=seal_dir, code_reachable=reach)
        if body.get("_unreadable"):
            games[rel] = {"status": "UNREADABLE_SEAL", "counted": False, "reasons": why}
            continue
        gid = body["game"]["game_id"]
        games[gid] = {"game_id": gid, "status": body["status"], "game_reason": body.get("game_reason"), "counted": ok, "uncounted_reasons": why, "seal_id": body["seal_id"],
                      "seal_commit_utc": cts.get(rel), "computed_utc": body.get("computed_utc"), "tip_utc": body["game"]["start_utc"], "board": body.get("board"),
                      "n_trades": body["candidates"]["n_trades"], "category": "SEALED_COUNTED" if ok else "SEALED_UNCOUNTED"}
        try:
            rows = [hydrate(r, body, study, ok) for r in load_candidates(seal_dir, body, rel)]
        except OSError:
            rows = []
        all_cs += rows
        if ok:
            counted_trades += [c for c in rows if c["decision"] == "TRADE"]
    for p in glob.glob(os.path.join(seal_dir, "missed", "*.json")):
        m = json.load(open(p))
        games.setdefault(m["game_id"], {"game_id": m["game_id"], "status": "MISSED", "counted": False, "tip_utc": m["tip_utc"], "category": "MISSED", "reason": m["reason"]})
    for g in schedule or []:
        if g["game_id"] not in games:
            w = window(g, study)
            games[g["game_id"]] = {"game_id": g["game_id"], "tip_utc": g["start_utc"], "counted": False,
                                   "category": "NOT_DUE" if now < w["opens"] else "NO_SEAL_RECORD", "status": "NO_DATA"}
    settle = settle_sealed(counted_trades, archive, market, now, base)
    counted_all = [c for c in all_cs if c["prospective"]]
    metrics = X.portfolio_metrics(counted_all, study, label="sealed_prospective", clocks_verified=True) if counted_all else \
        {"status": "NO_DATA", "reason": "no COUNTED sealed decisions yet", "label": "sealed_prospective"}
    cats = Counter(g.get("category") for g in games.values())
    return {"schema": "issue53.sealed_evaluation.v1", "protocol_sha256": protocol_sha, "study_version": study["version"], "prospective_start_utc": study["prospective_start_utc"],
            "n_seals_read": sum(1 for _ in iter_seals(seal_dir)), "games": sorted(games.values(), key=lambda g: (g.get("tip_utc") or "", g.get("game_id") or "")),
            "game_counts": dict(cats), "settlement_join": settle, "metrics": metrics,
            "counted_trades": [{k: c.get(k) for k in ("game_id", "player_name", "family", "k", "side", "ticker", "price", "effective_entry_exec", "ev_net_exec", "won", "net_pnl", "settled", "seal_id")}
                               for c in counted_trades],
            "progress": {"counted_trades": len(counted_trades), "counted_trades_settled": sum(1 for c in counted_trades if c["settled"]),
                         "counted_games_traded": len({c["game_id"] for c in counted_trades}), "required_decisions": study["evidence"]["min_decisions"],
                         "required_games": study["evidence"]["min_games"]},
            "rule": "selections are those sealed before tip; a missing / late / unverifiable seal is uncounted; nothing is recomputed from later archive state"}


# ================================================================================================ CLI
def _now(a) -> datetime:
    return MK.parse_ts(a.now) if getattr(a, "now", None) else datetime.now(UTC).replace(microsecond=0)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("plan", "seal", "watch", "evaluate", "check-deadline"):
        sp = sub.add_parser(name)
        sp.add_argument("--now", default=None)
        sp.add_argument("--seals", required=True)
        sp.add_argument("--context", default=None, help="data-archive checkout holding context/schedule")
        sp.add_argument("--archive", default=None, help="projection-data checkout")
        sp.add_argument("--market", default=None, help="data-archive checkout holding kalshi/markets*")
        sp.add_argument("--code-repo", default=".")
        sp.add_argument("--board-repo", default=None, help="git repo+ref of the capture branch for the independent board clock: <dir>")
        sp.add_argument("--board-ref", default="origin/data-archive")
        sp.add_argument("--forecast-ref", default="origin/projection-data")
        sp.add_argument("--dry-run", action="store_true")
        sp.add_argument("--out", default=None)
        sp.add_argument("--default-branch-ref", default="origin/main")
    a = ap.parse_args(argv)
    now = _now(a)
    study, base = X.load_study(), CFG.load()
    if a.cmd == "plan":
        pl = plan(a.context, a.seals, now, study)
        if a.out:
            json.dump(pl, open(a.out, "w"), indent=1, sort_keys=True)
        print(f"due={'true' if pl['due'] else 'false'}")
        print(f"needs_watch={'true' if pl['needs_watch'] else 'false'}")
        print(json.dumps(pl["counts"]), file=sys.stderr)
        return 0
    if a.cmd == "watch":
        games = schedule_games(a.context, now)
        miss = mark_missed(games, a.seals, now, study, dry_run=a.dry_run)
        print(json.dumps({"missed_now": [m["game_id"] for m in miss]}, indent=1))
        return 3 if miss else 0
    if a.cmd == "check-deadline":
        # after the push: every sealed game of the report must have been durably pushed before its deadline (otherwise the seal is LATE: uncounted, loud)
        rep = json.load(open(a.out))
        late = [x["game_id"] for x in rep.get("sealed", []) if not rep.get("dry_run") and now > MK.parse_ts(x["deadline_utc"])]
        print(json.dumps({"checked_at": _iso(now), "late": late}))
        return 5 if late else 0
    if a.cmd == "seal":
        ok, why = X.base_protocol_ok(study)
        if not ok:
            print(f"::error::base protocol changed: {why}", file=sys.stderr)
            return 2
        games = schedule_games(a.context, now)
        clocks = {"board_commit": X.board_commit_index(a.board_repo or a.market, a.board_ref), "forecast_commit": X.forecast_commit_index(a.archive, a.archive, a.forecast_ref)}
        rep = seal_games(games, a.archive, a.market, a.seals, now, study, base, clocks, code_info(a.code_repo), dry_run=a.dry_run,
                         extra_inputs={"projection_data_head": git(a.archive, "rev-parse", "HEAD"), "data_archive_head": git(a.board_repo or a.market, "rev-parse", "HEAD")})
        if a.out:
            json.dump(rep, open(a.out, "w"), indent=1, sort_keys=True)
        print(json.dumps(rep, indent=1, sort_keys=True, default=str))
        return 1 if rep["errors"] and not all(e["error"] == "ALREADY_SEALED_NOOP" for e in rep["errors"]) else 0
    if a.cmd == "evaluate":
        games = schedule_games(a.context, now, lookback_h=24 * 14) if a.context else None
        rep = evaluate(a.seals, a.archive, a.market, now, study, base, code_repo=a.code_repo, default_branch_ref=a.default_branch_ref, schedule=games)
        txt = json.dumps(rep, indent=1, sort_keys=True, default=str)
        if a.out:
            open(a.out, "w").write(txt)
        print(txt)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
