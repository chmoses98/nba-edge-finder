"""Probe the play-by-play sources the full-PBP backfill depends on, from a GitHub-hosted runner.

Read-only. Prints what the payloads actually contain so the ingest is written against observed shape
rather than a remembered one:

* ESPN ``summary``: the ``plays`` array -- event-type mix, which fields are present (``wallclock``,
  ``participants`` ordering on substitutions), and the box-score minutes format.
* cdn.nba.com liveData ``playbyplay`` / ``boxscore``: reachable or not from Actions, with the
  project's own client and headers (the granular source audit measured 403 in 2026-09; re-checked).

    python scripts/probe_full_pbp.py --date 2025-11-12 --games 2
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from typing import Any

import httpx

from nba_edge.data.boxscore import ESPN_SUMMARY_URL
from nba_edge.data.http import NBA_HEADERS, PLAIN_HEADERS_OK
from nba_edge.data.schedule import ESPN_SCOREBOARD_URL

CDN_PBP = "https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_{gid}.json"
CDN_BOX = "https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{gid}.json"
CDN_SCHED = "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json"


def get(client: httpx.Client, url: str, headers: dict[str, str]) -> tuple[int | str, Any]:
    try:
        r = client.get(url, headers=headers)
        if r.status_code != 200:
            return r.status_code, r.text[:200]
        return 200, r.json()
    except Exception as e:  # noqa: BLE001 - a probe reports, it does not raise
        return f"{type(e).__name__}", str(e)[:200]


def espn_part(client: httpx.Client, date: str, n_games: int) -> None:
    st, board = get(client, ESPN_SCOREBOARD_URL.format(yyyymmdd=date.replace("-", "")), PLAIN_HEADERS_OK)
    print("ESPN scoreboard", st)
    if st != 200:
        return
    events = board.get("events", [])[:n_games]
    for ev in events:
        eid = str(ev["id"])
        st, s = get(client, ESPN_SUMMARY_URL.format(event_id=eid), PLAIN_HEADERS_OK)
        print(f"\n=== ESPN summary {eid} -> {st}")
        if st != 200:
            continue
        print("top-level keys:", sorted(s.keys()))
        plays = s.get("plays") or []
        print("n plays:", len(plays))
        keys = Counter(k for p in plays for k in p.keys())
        print("play keys:", dict(keys))
        types = Counter((str((p.get("type") or {}).get("id")), str((p.get("type") or {}).get("text"))) for p in plays)
        print("type mix:", json.dumps(sorted(((f"{a}|{b}", c) for (a, b), c in types.items()), key=lambda x: -x[1])))
        print("wallclock present share:", round(sum(1 for p in plays if p.get("wallclock")) / max(1, len(plays)), 4))
        print("first 3 plays:", json.dumps(plays[:3])[:3000])
        subs = [p for p in plays if "substitution" in str((p.get("type") or {}).get("text", "")).lower()]
        print("n substitutions:", len(subs))
        for p in subs[:4]:
            print("SUB:", json.dumps(p)[:1500])
        for want in ("End Period", "Timeout", "Defensive Rebound", "Offensive Rebound", "Jumpball", "Bad Pass Turnover",
                     "Personal Foul", "Free Throw - 1 of 2", "Technical Foul", "End Game"):
            ex = next((p for p in plays if str((p.get("type") or {}).get("text")) == want), None)
            if ex:
                print(f"EX {want}:", json.dumps(ex)[:1200])
        nparts = Counter(len(p.get("participants") or []) for p in plays)
        print("participants-length mix:", dict(nparts))
        bx = s.get("boxscore") or {}
        for tp in (bx.get("players") or [])[:1]:
            for grp in tp.get("statistics", [])[:1]:
                print("box keys:", grp.get("keys"), "labels:", grp.get("labels"))
                for a in grp.get("athletes", [])[:3]:
                    print("box athlete:", json.dumps(a)[:600])
        hdr = (s.get("header") or {}).get("competitions", [{}])[0]
        print("header comp keys:", sorted(hdr.keys()))
        print("status:", json.dumps(hdr.get("status"))[:400])
        print("gameInfo:", json.dumps(s.get("gameInfo"))[:400])


def cdn_part(client: httpx.Client) -> None:
    for label, h in (("NBA_HEADERS", NBA_HEADERS), ("PLAIN", PLAIN_HEADERS_OK)):
        st, sched = get(client, CDN_SCHED, h)
        print(f"\ncdn schedule [{label}] ->", st, "" if st == 200 else sched)
        gid = "0022500200"
        if st == 200:
            try:
                games = [g for d in sched["leagueSchedule"]["gameDates"] for g in d["games"]]
                print("cdn schedule games:", len(games), "season:", sched["leagueSchedule"].get("seasonYear"))
                gid = next(g["gameId"] for g in games if str(g["gameId"]).startswith("00225"))
                print("sample game:", json.dumps(games[300])[:800])
            except Exception as e:  # noqa: BLE001
                print("cdn schedule parse failed", e)
        st, pbp = get(client, CDN_PBP.format(gid=gid), h)
        print(f"cdn pbp {gid} [{label}] ->", st)
        if st == 200:
            acts = pbp.get("game", {}).get("actions", [])
            print("n actions:", len(acts), "keys:", sorted(acts[0].keys()) if acts else None)
            print("action types:", dict(Counter(a.get("actionType") for a in acts)))
            print("sub example:", json.dumps(next((a for a in acts if a.get("actionType") == "substitution"), {}))[:800])
        st, box = get(client, CDN_BOX.format(gid=gid), h)
        print(f"cdn box {gid} [{label}] ->", st)
        if st == 200:
            pl = box.get("game", {}).get("homeTeam", {}).get("players", [])[:1]
            print("box player:", json.dumps(pl)[:800])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="2025-11-12")
    ap.add_argument("--games", type=int, default=2)
    a = ap.parse_args()
    with httpx.Client(timeout=40.0, follow_redirects=True) as c:
        espn_part(c, a.date, a.games)
        cdn_part(c)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
