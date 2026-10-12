"""Re-fetch a seeded sample of stored official injury reports and compare them with the stored records.

Provenance spot-check for the point-in-time availability dataset (research data). For each sampled
report the PDF is downloaded again from its stored ``url`` and compared with the stored record:
``sha256`` (byte identity), HTTP ``Last-Modified`` (the upload instant the PIT flags rely on), the
printed header time, and the parsed rows (same parser). A difference is reported (and annotated as a
workflow warning), never written back into the dataset. The sample always includes the reports used as
``t_minus_60`` snapshots of a few seeded games, so the instants that gate point-in-time use are checked
directly.

Runs where ak-static.cms.nba.com is reachable (GitHub Actions).

    python scripts/pit_refetch_spotcheck.py --season 2025-26 --n 6
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

import httpx
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nba_edge.availability.backfill import paths  # noqa: E402
from nba_edge.availability.official_report import parse_report_pdf  # noqa: E402
from nba_edge.data.http import PLAIN_HEADERS_OK  # noqa: E402
from nba_edge.timeutil import ET, iso, utcnow  # noqa: E402

ROW_KEYS = ["game_date", "away_tricode", "home_tricode", "team_id", "player_name_raw", "status", "reason"]


def _rows_key(rows: list[dict]) -> list[tuple]:
    return sorted((tuple("" if r.get(k) is None else str(r.get(k)) for k in ROW_KEYS) for r in rows), key=str)


def check_report(client: httpx.Client, rep: dict, stored_rows: pd.DataFrame) -> dict:
    out = {"slot_et": rep["slot_et"], "url": rep["url"], "stored_sha256": rep["sha256"],
           "stored_last_modified_utc": rep["last_modified_utc"], "stored_report_time_utc": rep["report_time_utc"],
           "stored_fetched_at_utc": rep["fetched_at_utc"]}
    r = client.get(rep["url"], headers=PLAIN_HEADERS_OK)
    out["refetched_at_utc"] = iso(utcnow())
    out["http_status"] = r.status_code
    if r.status_code != 200:
        out["ok"] = False
        return out
    lm = r.headers.get("last-modified")
    out["refetch_last_modified_utc"] = iso(parsedate_to_datetime(lm)) if lm else None
    out["refetch_sha256"] = hashlib.sha256(r.content).hexdigest()
    out["sha256_equal"] = out["refetch_sha256"] == rep["sha256"]
    out["last_modified_equal"] = out["refetch_last_modified_utc"] == rep["last_modified_utc"]
    slot = datetime.strptime(rep["slot_et"], "%Y-%m-%dT%H:%M").replace(tzinfo=ET)
    rows, meta = parse_report_pdf(r.content, slot)
    out["header_time_et"] = meta.get("header_time_et")
    out["rows_stored"], out["rows_refetched"] = int(len(stored_rows)), len(rows)
    out["rows_identical"] = _rows_key(stored_rows.to_dict("records")) == _rows_key(rows)
    out["ok"] = bool(out["sha256_equal"] and out["last_modified_equal"] and out["rows_identical"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hist", default=str(ROOT / "data" / "history"))
    ap.add_argument("--season", default="2025-26")
    ap.add_argument("--n", type=int, default=6, help="reports sampled at random (plus the T-60 reports of n/2 games)")
    ap.add_argument("--seed", type=int, default=20261012)
    ap.add_argument("--out", default=str(ROOT / "docs" / "research" / "pit_availability" / "refetch_spotcheck.json"))
    a = ap.parse_args()
    p = paths(Path(a.hist), a.season)
    reps = pd.read_parquet(p["reports"]).sort_values("slot_et")
    rows = pd.read_parquet(p["rows"])
    games = pd.read_parquet(p["games"]).sort_values("game_id")
    rng = random.Random(a.seed)
    slots = rng.sample(sorted(reps["slot_et"]), min(a.n, len(reps)))
    ok_games = games[games["t_minus_60_pit_ok"]]
    picked = ok_games.iloc[sorted(rng.sample(range(len(ok_games)), min(max(1, a.n // 2), len(ok_games))))]
    t60 = {str(s): g for s, g in zip(picked["t_minus_60_slot_et"], picked["game_id"], strict=True)}
    slots = sorted(set(slots) | set(t60))
    results = []
    with httpx.Client(timeout=40.0, follow_redirects=True) as client:
        for rep in reps[reps["slot_et"].isin(slots)].to_dict("records"):
            try:
                res = check_report(client, rep, rows[rows["slot_et"] == rep["slot_et"]])
            except Exception as e:  # noqa: BLE001 - report, never abort the job
                res = {"slot_et": rep["slot_et"], "ok": False, "error": f"{type(e).__name__}: {e}"[:200]}
            if rep["slot_et"] in t60:
                g = picked[picked["game_id"] == t60[rep["slot_et"]]].iloc[0]
                lm = res.get("refetch_last_modified_utc")
                res["t_minus_60_for_game"] = {"game_id": g["game_id"], "tip_utc": g["tip_utc"],
                                              "cutoff_utc": g.get("t_minus_60_cutoff_utc"),
                                              "refetch_last_modified_before_cutoff": bool(
                                                  lm and pd.Timestamp(lm) < pd.Timestamp(g["tip_utc"]) - pd.Timedelta(minutes=60))}
            results.append(res)
            if not res.get("ok"):
                print(f"::warning title=injury report refetch mismatch::{json.dumps(res)[:400]}")
    summary = {"checked_at_utc": iso(utcnow()), "seed": a.seed, "reports_checked": len(results),
               "reports_identical": sum(1 for r in results if r.get("ok")),
               "sha256_equal": sum(1 for r in results if r.get("sha256_equal")),
               "last_modified_equal": sum(1 for r in results if r.get("last_modified_equal")),
               "reports": results}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    print(json.dumps(summary, indent=1, default=str))  # full record, with timestamps, in the run log
    # the committed file keeps only fields that are stable across identical re-runs (no timestamps, no
    # volatile payload hash), so an unchanged result is not a new commit
    volatile = {"checked_at_utc", "refetched_at_utc", "refetch_payload_sha256"}
    stable = {k: v for k, v in summary.items() if k not in volatile}
    stable["reports"] = [{k: v for k, v in r.items() if k not in volatile} for r in summary["reports"]]
    Path(a.out).write_text(json.dumps(stable, indent=1, default=str) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
