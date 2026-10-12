"""Append-only prospective capture of the latest official injury report (+ an ESPN injuries snapshot).

Every run:

1. HEAD-probes the official slot grid backwards from now (up to ``LOOKBACK_SLOTS``) for the latest
   published report. If that slot (with the same sha256) was already captured, nothing is written.
2. Otherwise downloads it, parses it, and writes ONE write-once file
   ``official/dt=<ET date>/report_<slot>__captured_<UTC>.jsonl.gz`` whose every row carries
   ``report_time_utc`` (nominal slot), ``last_modified_utc`` (upload instant), ``fetched_at_utc`` and
   the PDF's sha256.
3. Snapshots ESPN ``/injuries`` (current statuses with ESPN athlete ids and each entry's own update
   ``date``) to ``espn/dt=<ET date>/espn_injuries__captured_<UTC>.jsonl.gz``.
4. Appends one line per written file to ``MANIFEST.jsonl`` with a sha256 hash chain
   (``chain = sha256(prev_chain + file_sha256)``); :func:`verify_chain` fails if any recorded file was
   modified or deleted.

Files are opened with mode ``"xb"``: an existing path is never overwritten. ``dry_run`` builds and
validates everything in a scratch directory and commits nothing (used on pull requests).
"""

from __future__ import annotations

import gzip
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from nba_edge.availability.official_report import parse_report_pdf, report_urls, slot_floor
from nba_edge.data.http import PLAIN_HEADERS_OK
from nba_edge.timeutil import ET, iso, utcnow

LOOKBACK_SLOTS = 24  # 6 hours
ESPN_INJURIES_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
SELF_TEST_SLOT = datetime(2026, 1, 15, 17, 30, tzinfo=ET)  # a known published report (parser self-test)


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _write_once(path: Path, rows: list[dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = gzip.compress("".join(json.dumps(r, sort_keys=True, default=str) + "\n" for r in rows).encode(), mtime=0)
    with open(path, "xb") as f:  # refuses to overwrite
        f.write(payload)
    return _sha(payload)


def _manifest(root: Path) -> list[dict[str, Any]]:
    p = root / "MANIFEST.jsonl"
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []


def _append_manifest(root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    prev = _manifest(root)
    prev_chain = prev[-1]["chain"] if prev else ""
    entry = {**entry, "prev_chain": prev_chain, "chain": _sha((prev_chain + entry["sha256"]).encode())}
    with open(root / "MANIFEST.jsonl", "a") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


def verify_chain(root: Path) -> dict[str, Any]:
    """Recompute every file hash and the chain. Raises AssertionError on any modification or deletion."""
    prev = ""
    n = 0
    for e in _manifest(root):
        f = root / e["path"]
        assert f.exists(), f"captured file deleted: {e['path']}"
        assert _sha(f.read_bytes()) == e["sha256"], f"captured file modified: {e['path']}"
        assert e["prev_chain"] == prev and e["chain"] == _sha((prev + e["sha256"]).encode()), f"chain broken at {e['path']}"
        prev = e["chain"]
        n += 1
    return {"files": n, "head": prev}


def espn_rows(payload: dict[str, Any], fetched_at: str) -> list[dict[str, Any]]:
    """ESPN /injuries -> rows with the ESPN athlete id (from the player-card link) and the entry's own date."""
    import re

    out = []
    for team in payload.get("injuries") or []:
        for inj in team.get("injuries") or []:
            ath = inj.get("athlete") or {}
            aid = None
            for ln in ath.get("links") or []:
                m = re.search(r"/id/(\d+)", str(ln.get("href") or ""))
                if m:
                    aid = int(m.group(1))
                    break
            out.append({"source": "espn/injuries", "espn_team_id": team.get("id"), "team_name": team.get("displayName"),
                        "nba_id": -aid if aid else None, "player_name": ath.get("displayName"),
                        "status": inj.get("status"), "entry_date_utc": inj.get("date"),
                        "short_comment": inj.get("shortComment"), "type": (inj.get("details") or {}).get("type"),
                        "fetched_at_utc": fetched_at})
    return out


def latest_slot(c: httpx.Client, now: datetime) -> tuple[datetime | None, dict[str, Any]]:
    s = slot_floor(now.astimezone(ET))
    tried = 0
    for _ in range(LOOKBACK_SLOTS):
        tried += 1
        for url in report_urls(s):
            r = c.head(url, headers=PLAIN_HEADERS_OK)
            if r.status_code == 200:
                return s, {"slots_tried": tried, "last_modified": r.headers.get("last-modified"), "url": url}
        s -= timedelta(minutes=15)
    return None, {"slots_tried": tried}


def fetch_report(c: httpx.Client, slot: datetime, url: str | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from email.utils import parsedate_to_datetime

    url = url or report_urls(slot)[0]
    r = c.get(url, headers=PLAIN_HEADERS_OK)
    fetched = iso(utcnow())
    r.raise_for_status()
    rows, meta = parse_report_pdf(r.content, slot)
    lm = r.headers.get("last-modified")
    lm_iso = iso(parsedate_to_datetime(lm)) if lm else None
    prov = {"source": "nba_official_injury_report_pdf", "url": url, "report_time_utc": iso(slot),
            "last_modified_utc": lm_iso, "fetched_at_utc": fetched, "pdf_sha256": _sha(r.content)}
    return [{**row, **prov} for row in rows], {**meta, **prov}


def run_capture(root: Path, *, dry_run: bool = False, now: datetime | None = None) -> dict[str, Any]:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    now = now or utcnow()
    cap = now.strftime("%Y%m%dT%H%M%SZ")
    status: dict[str, Any] = {"captured_at_utc": iso(now), "dry_run": dry_run, "written": []}
    if not dry_run:
        status["chain_before"] = verify_chain(root)
    with httpx.Client(timeout=40.0, follow_redirects=True) as c:
        # parser self-test against a known report: a capture that cannot parse must not look healthy
        st_rows, st_meta = fetch_report(c, SELF_TEST_SLOT)
        status["self_test"] = {"slot": iso(SELF_TEST_SLOT), "player_rows": st_meta["n_player_rows"],
                               "rows_missing_team": st_meta["rows_missing_team"]}
        assert st_meta["n_player_rows"] >= 50 and st_meta["rows_missing_team"] == 0, status["self_test"]

        slot, info = latest_slot(c, now)
        status["official"] = info | {"slot_et": slot.strftime("%Y-%m-%dT%H:%M") if slot else None}
        if slot is not None:
            rows, meta = fetch_report(c, slot, info.get("url"))
            seen = {(e.get("slot_et"), e.get("pdf_sha256")) for e in _manifest(root)}
            key = (slot.strftime("%Y-%m-%dT%H:%M"), meta["pdf_sha256"])
            status["official"].update({k: meta[k] for k in ("n_player_rows", "n_not_yet_submitted", "rows_missing_team",
                                                            "header_time_matches_slot", "last_modified_utc")})
            if key in seen:
                status["official"]["skipped"] = "already captured (same slot and sha256)"
            else:
                rel = f"official/dt={slot.strftime('%Y-%m-%d')}/report_{slot.strftime('%Y%m%dT%H%M')}ET__captured_{cap}.jsonl.gz"
                sha = _write_once(root / rel, rows)
                status["written"].append(_append_manifest(root, {
                    "path": rel, "sha256": sha, "kind": "official", "slot_et": key[0], "pdf_sha256": key[1],
                    "captured_at_utc": iso(now), "fetched_at_utc": meta["fetched_at_utc"], "rows": len(rows)}))
        try:
            r = c.get(ESPN_INJURIES_URL, headers=PLAIN_HEADERS_OK)
            r.raise_for_status()
            er = espn_rows(r.json(), iso(utcnow()))
            rel = f"espn/dt={now.astimezone(ET).strftime('%Y-%m-%d')}/espn_injuries__captured_{cap}.jsonl.gz"
            sha = _write_once(root / rel, er)
            status["written"].append(_append_manifest(root, {
                "path": rel, "sha256": sha, "kind": "espn", "captured_at_utc": iso(now), "rows": len(er),
                "fetched_at_utc": er[0]["fetched_at_utc"] if er else iso(utcnow())}))
            status["espn"] = {"rows": len(er), "with_athlete_id": sum(1 for x in er if x["nba_id"])}
        except Exception as e:  # noqa: BLE001 - one source failing must not stop the other
            status["espn"] = {"error": f"{type(e).__name__}: {e}"[:200]}
    status["chain_after"] = verify_chain(root)
    return status
