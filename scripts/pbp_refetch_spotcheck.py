"""Re-fetch a seeded sample of already-ingested games from ESPN and compare them to the stored rows.

Provenance spot-check for the full play-by-play dataset (research data): for each sampled game the
summary payload is downloaded again (fresh, no disk cache), parsed with the SAME parser, and compared to
``pbp_events_<season>`` / ``pbp_box_<season>`` / ``pbp_games_<season>``. ESPN's summary also carries
volatile sections (news, odds, standings), so the raw ``payload_sha256`` is expected to differ; the
check is on the parsed play-by-play and box content. A mismatch is reported (and annotated as a
workflow warning), never "repaired" into the stored data.

Runs where site.api.espn.com is reachable (GitHub Actions).

    python scripts/pbp_refetch_spotcheck.py --seasons 2025-26,2024-25 --per-season 4
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

import httpx
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nba_edge.data.http import PLAIN_HEADERS_OK  # noqa: E402
from nba_edge.pbp.espn_full import BOX_COLUMNS, EVENT_COLUMNS, parse_box, parse_events  # noqa: E402
from nba_edge.pbp.ingest import paths  # noqa: E402
from nba_edge.timeutil import iso, utcnow  # noqa: E402

EVENT_KEYS = [c for c in EVENT_COLUMNS if c != "game_id"]
BOX_KEYS = [c for c in BOX_COLUMNS if c not in ("game_id", "minutes_raw")]


def _norm(v):
    if v is None:
        return None
    try:
        if v != v:  # NaN / NA
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(v, float):
        return round(v, 3)
    if hasattr(v, "item"):
        return _norm(v.item())
    return v


def _tuples(rows: list[dict], keys: list[str]) -> list[tuple]:
    return [tuple(_norm(r.get(k)) for k in keys) for r in rows]


def check_game(client: httpx.Client, game: dict, ev: pd.DataFrame, bx: pd.DataFrame) -> dict:
    gid = game["game_id"]
    url = game["source_url"]
    out = {"game_id": gid, "source_url": url, "stored_fetched_at_utc": game["fetched_at_utc"],
           "stored_payload_sha256": game["payload_sha256"]}
    r = client.get(url, headers=PLAIN_HEADERS_OK)
    out["refetched_at_utc"] = iso(utcnow())
    out["http_status"] = r.status_code
    if r.status_code != 200:
        out["ok"] = False
        return out
    payload = r.json()
    out["refetch_payload_sha256"] = hashlib.sha256(r.content).hexdigest()
    out["payload_sha256_equal"] = out["refetch_payload_sha256"] == game["payload_sha256"]
    new_ev = parse_events(payload, gid)
    new_bx = parse_box(payload, gid)
    old_ev = ev[ev["game_id"] == gid].sort_values("order").to_dict("records")
    old_bx = bx[bx["game_id"] == gid].to_dict("records")
    a, b = _tuples(old_ev, EVENT_KEYS), _tuples(new_ev, EVENT_KEYS)
    out["events_stored"], out["events_refetched"] = len(a), len(b)
    out["events_identical"] = a == b
    if a != b:
        diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
        out["events_first_diffs"] = [{"order": i, "stored": list(a[i]), "refetched": list(b[i])} for i in diff[:3]]
        out["events_n_diff_positions"] = len(diff) + abs(len(a) - len(b))
    sa, sb = sorted(_tuples(old_bx, BOX_KEYS), key=str), sorted(_tuples(new_bx, BOX_KEYS), key=str)
    out["box_stored"], out["box_refetched"] = len(sa), len(sb)
    out["box_identical"] = sa == sb
    out["ok"] = bool(out["events_identical"] and out["box_identical"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hist", default=str(ROOT / "data" / "history"))
    ap.add_argument("--seasons", default="2025-26,2024-25")
    ap.add_argument("--per-season", type=int, default=4)
    ap.add_argument("--seed", type=int, default=20261012)
    ap.add_argument("--out", default=str(ROOT / "docs" / "research" / "lineup_pbp" / "refetch_spotcheck.json"))
    a = ap.parse_args()
    rng = random.Random(a.seed)
    results = []
    with httpx.Client(timeout=40.0, follow_redirects=True) as client:
        for season in [s.strip() for s in a.seasons.split(",") if s.strip()]:
            p = paths(Path(a.hist), season)
            if not p["games"].exists():
                continue
            gm = pd.read_parquet(p["games"]).sort_values("game_id")
            ev, bx = pd.read_parquet(p["events"]), pd.read_parquet(p["box"])
            ids = sorted(gm["game_id"].astype(str))
            sample = rng.sample(ids, min(a.per_season, len(ids)))
            for g in gm[gm["game_id"].isin(sample)].to_dict("records"):
                try:
                    res = check_game(client, g, ev, bx)
                except Exception as e:  # noqa: BLE001 - report, never abort the job
                    res = {"game_id": g["game_id"], "ok": False, "error": f"{type(e).__name__}: {e}"[:200]}
                res["season"] = season
                results.append(res)
                if not res.get("ok"):
                    print(f"::warning title=pbp refetch mismatch::{res['game_id']} {json.dumps(res)[:400]}")
    summary = {"checked_at_utc": iso(utcnow()), "seed": a.seed, "games_checked": len(results),
               "games_identical": sum(1 for r in results if r.get("ok")),
               "payload_sha256_equal": sum(1 for r in results if r.get("payload_sha256_equal")),
               "note": "raw payload sha is expected to differ (volatile non-pbp sections); parsed events and "
                       "box lines are compared", "games": results}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(summary, indent=1, default=str))
    print(json.dumps({k: v for k, v in summary.items() if k != "games"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
