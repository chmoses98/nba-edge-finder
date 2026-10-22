"""Seal windows, schedule snapshots and the idle gate of the Issue #53 sealed ledger (RESEARCH ONLY). Standard library only, on purpose.

Everything that decides "is a game owed a seal right now?" lives here, so that
  * `exec_seal` (the sealer) and the idle gate / liveness monitor use ONE implementation (no copy to drift), and
  * the gate runs on the bare runner interpreter, before any dependency is installed: an idle poll costs a ~1 s depth-1 blobless fetch and ~0.1 s of Python, not a 20 s
    install (repo note: the conductor's wake used to install ~690 MB, 144 times a day, to read five timestamps).

    python research/projection_foundation/nba/paper/seal_windows.py gate --context <data-archive> --seals <ledger> [--now ISO] [--horizon-h 14]

`gate` prints `active=true|false` (a game whose seal window is open now or opens within the horizon, or one whose window closed unsealed and still needs its MISSED marker),
`due`, `needs_watch` and the next window opening, as `key=value` lines for $GITHUB_OUTPUT.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import hashlib
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

UTC = timezone.utc
STUDY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exec_shadow_config_v2.json")


def parse_ts(x: str) -> datetime:
    d = datetime.fromisoformat(str(x).replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=UTC)


def iso(d: datetime) -> str:
    return d.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _iso(d: datetime | None) -> str | None:
    return None if d is None else iso(d)


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_study(path: str | None = None) -> dict:
    with open(path or STUDY_PATH) as f:
        return json.load(f)


def checkpoint_of(tip: datetime, study: dict) -> datetime:
    return tip - timedelta(minutes=int(study["checkpoint"]["minutes_before_tip"]))


def _stamp(path: str) -> datetime | None:
    m = re.search(r"context_schedule_(\d{8}T\d{6}Z)", os.path.basename(path))
    return datetime.strptime(m.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC) if m else None


def schedule_games(context_dir: str, now: datetime | None, season_types: tuple[str, ...] = ("regular",), lookback_h: float = 6.0, horizon_h: float = 48.0,
                   snapshot_span_h: float = 36.0, all_history: bool = False) -> list[dict]:
    """Games from the ESPN schedule snapshots of the capture branch observed at or before `now` within the last `snapshot_span_h` hours; the LATEST observation of a game
    wins (a postponed / moved tip is followed), and a game that has dropped out of the newest snapshot (finished, other ET day) is still known from an earlier one.
    Independent of our forecasts: a game without forecasts is still a game we owe a status."""
    files = [(st, p) for p in glob.glob(os.path.join(context_dir, "context", "schedule", "dt=*", "context_schedule_*.jsonl.gz"))
             if (st := _stamp(p)) is not None and (all_history or (now - timedelta(hours=snapshot_span_h) <= st <= now))]
    out: dict[str, dict] = {}
    for st, p in sorted(files, key=lambda x: (x[0], x[1])):
        raw = open(p, "rb").read()
        digest = sha256(raw)
        for line in gzip.decompress(raw).decode().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("season_type") not in season_types:
                continue
            if not r.get("start_time_utc"):
                out.pop(r["game_id"], None)                     # tip withdrawn (postponed / unscheduled): the stale earlier tip must not be sealed
                continue
            out[r["game_id"]] = {"game_id": r["game_id"], "start_utc": iso(parse_ts(r["start_time_utc"])), "home": r["home_tricode"], "away": r["away_tricode"],
                                 "game_date_et": r.get("game_date_et"), "schedule_file": os.path.basename(p), "schedule_sha256": digest,
                                 "schedule_observed_utc": r.get("_observed_at_utc"), "status": r.get("status")}
    keep = [g for g in out.values() if all_history or now - timedelta(hours=lookback_h) <= parse_ts(g["start_utc"]) <= now + timedelta(hours=horizon_h)]
    return sorted(keep, key=lambda g: (g["start_utc"], g["game_id"]))


def window(game: dict, study: dict) -> dict[str, datetime]:
    tip = parse_ts(game["start_utc"])
    cp = checkpoint_of(tip, study)
    sc = study["sealing"]
    return {"tip": tip, "checkpoint": cp, "opens": cp + timedelta(seconds=sc["earliest_after_checkpoint_s"]), "closes": tip - timedelta(seconds=sc["deadline_before_tip_s"])}


def enabled_utc(seal_dir: str) -> datetime | None:
    """When the ledger was first enabled (file `ENABLED_UTC`, written by the first live run). Games whose window opened earlier were never ours to seal."""
    try:
        return parse_ts(open(os.path.join(seal_dir, "ENABLED_UTC")).read().strip())
    except (OSError, ValueError):
        return None


def mark_enabled(seal_dir: str, now: datetime) -> None:
    p = os.path.join(seal_dir, "ENABLED_UTC")
    if not os.path.exists(p):
        with open(p, "x") as f:
            f.write(iso(now) + "\n")


def game_state(now: datetime, game: dict, study: dict, sealed: set[str], missed: set[str], enabled: datetime | None = None) -> str:
    w = window(game, study)
    if game["game_id"] not in sealed and ((enabled is not None and w["opens"] < enabled) or (enabled is None and now > w["closes"])):
        return "BEFORE_ENABLED"                              # the ledger was not enabled (yet) when this window ran: not ours, never MISSED
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
    return {"now": iso(now), "games": rows, "counts": dict(c), "due": bool(c.get("OPEN")), "needs_watch": bool(c.get("WINDOW_CLOSED_UNSEALED"))}


def gate(context_dir: str, seal_dir: str, now: datetime, study: dict, horizon_h: float = 14.0) -> dict[str, Any]:
    """Should the (expensive) sealer chain be alive now? Yes when a window is open, a closed window still needs its MISSED marker, or a window opens within `horizon_h`
    (the chain then idles cheaply; a delivered cron is the only thing that can start it, and a start attempt in the last hours before the first tip is the whole point)."""
    pl = plan(context_dir, seal_dir, now, study)
    nxt = sorted(r["opens_utc"] for r in pl["games"] if r["state"] == "NOT_DUE")
    soon = bool(nxt) and parse_ts(nxt[0]) <= now + timedelta(hours=horizon_h)
    active = pl["due"] or pl["needs_watch"] or soon
    return {"now": pl["now"], "active": active, "due": pl["due"], "needs_watch": pl["needs_watch"], "next_window_opens_utc": nxt[0] if nxt else None, "counts": pl["counts"],
            "horizon_h": horizon_h}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["gate", "plan"])
    ap.add_argument("--context", required=True)
    ap.add_argument("--seals", required=True)
    ap.add_argument("--now", default=None)
    ap.add_argument("--horizon-h", type=float, default=14.0)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    now = parse_ts(a.now) if a.now else datetime.now(UTC).replace(microsecond=0)
    study = load_study()
    res = gate(a.context, a.seals, now, study, a.horizon_h) if a.cmd == "gate" else plan(a.context, a.seals, now, study)
    if a.out:
        json.dump(res, open(a.out, "w"), indent=1, sort_keys=True)
    if a.cmd == "gate":
        for k in ("active", "due", "needs_watch"):
            print(f"{k}={'true' if res[k] else 'false'}")
        print(f"next_window_opens_utc={res['next_window_opens_utc'] or ''}")
        print(json.dumps({"now": res["now"], "counts": res["counts"]}), file=sys.stderr)
    else:
        print(json.dumps(res, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
