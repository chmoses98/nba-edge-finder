"""Probe candidate sources for lineup/stint-level NBA data from wherever this runs.

The brief's criteria include "GitHub Actions accessibility", and that cannot be answered from a
developer machine: stats.nba.com in particular is well known to treat cloud egress differently
from residential egress. So this script is written to run ON a runner and report what it actually
got, rather than what a library's README claims.

It fetches one sample per source and reports status, size, latency and a shape probe. It does NOT
crawl: the brief is explicit that a source must not be scraped aggressively before its suitability
is established, and one request per endpoint is what establishing suitability costs.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
NBA_HEADERS = {
    "User-Agent": UA,
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
}
GAME = "0022500001"  # first regular-season game of 2025-26

SOURCES = [
    ("cdn.nba playbyplay", f"https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_{GAME}.json", {"User-Agent": UA}),
    ("cdn.nba boxscore", f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{GAME}.json", {"User-Agent": UA}),
    ("cdn.nba schedule", "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json", {"User-Agent": UA}),
    ("stats.nba gamerotation", f"https://stats.nba.com/stats/gamerotation?GameID={GAME}&LeagueID=00", NBA_HEADERS),
    ("stats.nba playbyplayv3", f"https://stats.nba.com/stats/playbyplayv3?GameID={GAME}&StartPeriod=1&EndPeriod=4", NBA_HEADERS),
    ("stats.nba boxscoreadvancedv3", f"https://stats.nba.com/stats/boxscoreadvancedv3?GameID={GAME}&StartPeriod=1&EndPeriod=4&StartRange=0&EndRange=0&RangeType=0", NBA_HEADERS),
    ("pbpstats get-games", "https://api.pbpstats.com/get-games/nba?Season=2025-26&SeasonType=Regular%20Season", {"User-Agent": UA}),
    ("pbpstats possessions", f"https://api.pbpstats.com/get-possessions/nba?GameId={GAME}", {"User-Agent": UA}),
    ("pbpstats game-lineups", f"https://api.pbpstats.com/get-game-stats?GameId={GAME}&Type=Lineup", {"User-Agent": UA}),
    ("espn pbp (control)", f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event=401705000", {"User-Agent": UA}),
    # hoopR publishes season-level NBA play-by-play as parquet in GitHub RELEASES. Being on GitHub
    # matters: it is reachable from a runner, unrate-limited, versioned and reproducible, which is
    # exactly what an archive of record needs and what a live JSON API is worst at.
    ("hoopR pbp release (HEAD)", "https://github.com/sportsdataverse/hoopR-data/releases/download/nba_pbp/play_by_play_2024.parquet", {"User-Agent": UA}),
]


def probe(name: str, url: str, headers: dict) -> dict:
    req = urllib.request.Request(url, headers=headers)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            body = r.read()
            dt = time.time() - t0
            shape = ""
            if body[:1] in (b"{", b"["):
                try:
                    d = json.loads(body)
                    if isinstance(d, dict):
                        shape = "keys=" + ",".join(list(d)[:6])
                        for k in ("resultSets", "resultSet", "game", "results", "multi_row_table_data"):
                            if k in d:
                                shape += f" | has:{k}"
                    else:
                        shape = f"list[{len(d)}]"
                except json.JSONDecodeError:
                    shape = "non-json body"
            else:
                shape = f"binary head={body[:4]!r}"
            return {"name": name, "status": r.status, "bytes": len(body), "seconds": round(dt, 2), "shape": shape}
    except urllib.error.HTTPError as e:
        return {"name": name, "status": e.code, "bytes": 0, "seconds": round(time.time() - t0, 2),
                "shape": f"HTTPError {e.reason}"}
    except Exception as e:  # noqa: BLE001 - a probe reports failure, it does not raise
        return {"name": name, "status": None, "bytes": 0, "seconds": round(time.time() - t0, 2),
                "shape": f"{type(e).__name__}: {e}"}


def main() -> int:
    out = []
    for name, url, headers in SOURCES:
        r = probe(name, url, headers)
        out.append(r)
        print(f"PROBE {r['status']!s:<6} {r['bytes']:>9}b {r['seconds']:>6}s  {name:<28} {r['shape'][:110]}")
        time.sleep(1.5)  # deliberate: one polite request per endpoint, never a crawl
    print("PROBE_JSON " + json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
