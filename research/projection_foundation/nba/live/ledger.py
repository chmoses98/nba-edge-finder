"""Run ledger: one write-once record per executed slot, plus the checks that stop a green run from implying work that did not happen.

    ops/nba/slots/<ET date>/<HHMM>_<kind>.json        scheduled slot (pregame | settle)
    ops/nba/slots/<UTC date>/manual_<HHMMSS>.json     manual dispatch

A record exists only if the run's stages all completed AND `verify_run` accepted their results. A run that fails verification raises
`RunVerificationError` (the job turns red, nothing is committed, the slot stays open and the backup cron retries it).
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

SCHEMA = "sift.nba_run_ledger.v1"

OUTCOMES = {
    "EXECUTED_PRODUCED": "games were in the window and forecasts are archived (written now or already present)",
    "EXECUTED_NO_GAMES": "no game starts inside the projection window; nothing to project (explicit, not a success of projection)",
    "EXECUTED_SETTLED": "settle slot: results/settle/score stages ran",
}


class RunVerificationError(RuntimeError):
    pass


def slot_file(root: str, rec: dict) -> str:
    sid, kind = rec["slot_id"], rec["kind"]
    if sid.startswith("manual-"):
        day = f"{sid[7:11]}-{sid[11:13]}-{sid[13:15]}"
        name = f"manual_{sid[16:22]}.json"
    else:
        day, hm = sid.split("@")
        name = f"{hm}_{kind}.json"
    return os.path.join(root, "ops", "nba", "slots", day, name)


def has_slot(root: str, slot_id: str, kind: str) -> bool:
    return os.path.exists(slot_file(root, {"slot_id": slot_id, "kind": kind}))


def verify_run(kind: str, st: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    """(outcome, warnings, problems). `problems` non-empty means the run must fail."""
    warn: list[str] = []
    bad: list[str] = []
    if kind == "settle":
        for k in ("results", "settle", "score"):
            if k not in st:
                bad.append(f"settle slot: stage `{k}` did not run")
        res = st.get("results") or {}
        if res.get("fetch_errors") and not res.get("games_final"):
            warn.append(f"results: {res['fetch_errors']} fetch errors and no final game read: {res.get('errors')}")
        return "EXECUTED_SETTLED", warn, bad
    cap, pj = st.get("capture"), st.get("project")
    if cap is None or pj is None:
        bad.append("pregame slot: the capture and project stages must both run")
        return "FAILED", warn, bad
    n_games = int(pj.get("games") or 0)
    if cap.get("errors"):
        warn.append(f"capture source problems: {cap['errors']}")
    if n_games == 0:
        return "EXECUTED_NO_GAMES", warn, bad
    arch = pj.get("challenger_archive") or {}
    present = int(arch.get("written", 0)) + int(arch.get("duplicates", 0))
    if pj.get("status") != "ok":
        bad.append(f"{n_games} games in the window but project status is {pj.get('status')!r}")
    if present < 1:
        bad.append(f"{n_games} games in the window but no challenger forecast was archived or already present "
                   f"(late_rejected={arch.get('late_rejected')}, invalid={arch.get('invalid')})")
    if arch.get("invalid"):
        warn.append(f"{arch['invalid']} forecast records were invalid and not archived")
    off = ((cap.get("sources") or {}).get("official") or {})
    if off.get("status") != "ok":
        warn.append(f"official injury report status {off.get('status')!r}: players without another observation stay UNVERIFIED")
    return "EXECUTED_PRODUCED", warn, bad


def build_record(kind: str, st: dict[str, Any], meta: dict[str, Any], now: datetime) -> dict[str, Any]:
    outcome, warn, bad = verify_run(kind, st)
    if bad:
        raise RunVerificationError("; ".join(bad))
    cap, pj = st.get("capture") or {}, st.get("project") or {}
    produced: dict[str, Any] = {}
    if kind == "pregame":
        produced = {"games_in_window": pj.get("games"), "players": pj.get("players"), "forecast_rows": pj.get("rows"),
                    "challenger_archive": pj.get("challenger_archive"), "incumbent": pj.get("incumbent"),
                    "availability_observations": cap.get("n_observations"), "gate": pj.get("gate"),
                    "official_report": ((cap.get("sources") or {}).get("official") or {}).get("status"),
                    "slate_date": pj.get("slate_date")}
    else:
        produced = {k: st.get(k) for k in ("results", "settle")}
    return {"schema": SCHEMA, "authority": "research_only", "kind": kind, "outcome": outcome, "warnings": warn,
            "finished_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "produced": produced, **meta}


def write(root: str, rec: dict[str, Any]) -> str:
    """Write once. An existing record for the slot is kept (a duplicate run never rewrites history)."""
    path = slot_file(root, rec)
    if os.path.exists(path):
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "x") as f:
        json.dump(rec, f, indent=1, sort_keys=True, default=str)
    return path


def load_all(root: str, since_day: str | None = None) -> list[dict[str, Any]]:
    base = os.path.join(root, "ops", "nba", "slots")
    out: list[dict[str, Any]] = []
    if not os.path.isdir(base):
        return out
    for day in sorted(os.listdir(base)):
        if since_day and day < since_day:
            continue
        d = os.path.join(base, day)
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".json"):
                with open(os.path.join(d, fn)) as f:
                    out.append(json.load(f))
    return out
