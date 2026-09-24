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

import httpx

# Use the project's OWN header sets, not invented ones.
#
# The first version of this probe sent a spoofed Chrome User-Agent via urllib and reported 403 for
# every host -- including ESPN, which `nba context` fetches successfully from this exact workflow
# environment several times a day. The control failing was the tell: a spoofed browser UA arriving
# from a datacenter IP is *more* suspicious to bot detection than an honest one, so the probe was
# manufacturing the blocks it then reported. Probing with anything other than the client we
# actually ingest with measures the probe, not the source.
from nba_edge.data.http import NBA_HEADERS, PLAIN_HEADERS_OK

UA = PLAIN_HEADERS_OK["User-Agent"]
GAME = "0022500001"  # first regular-season game of 2025-26

# Endpoints that timed out at 40s get a much longer budget on the retry. The distinction matters:
# a source that is SLOW is usable from a batch job, a source that is BLOCKED is not, and a 40s
# timeout cannot tell them apart. pbpstats returned 200 in 2.6s for one endpoint while three others
# timed out, which is the signature of slow generation rather than an IP block.
SLOW_BUDGET_S = 180.0
SLOW = ("pbpstats get-games", "pbpstats possessions", "stats.nba gamerotation")

SOURCES = [
    (
        "cdn.nba playbyplay",
        f"https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_{GAME}.json",
        PLAIN_HEADERS_OK,
    ),
    (
        "cdn.nba boxscore",
        f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{GAME}.json",
        PLAIN_HEADERS_OK,
    ),
    (
        "cdn.nba schedule",
        "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json",
        PLAIN_HEADERS_OK,
    ),
    (
        "stats.nba gamerotation",
        f"https://stats.nba.com/stats/gamerotation?GameID={GAME}&LeagueID=00",
        NBA_HEADERS,
    ),
    (
        "stats.nba playbyplayv3",
        f"https://stats.nba.com/stats/playbyplayv3?GameID={GAME}&StartPeriod=1&EndPeriod=4",
        NBA_HEADERS,
    ),
    (
        "stats.nba boxscoreadvancedv3",
        f"https://stats.nba.com/stats/boxscoreadvancedv3?GameID={GAME}&StartPeriod=1&EndPeriod=4&StartRange=0&EndRange=0&RangeType=0",
        NBA_HEADERS,
    ),
    (
        "pbpstats get-games",
        "https://api.pbpstats.com/get-games/nba?Season=2025-26&SeasonType=Regular%20Season",
        PLAIN_HEADERS_OK,
    ),
    ("pbpstats possessions", f"https://api.pbpstats.com/get-possessions/nba?GameId={GAME}", PLAIN_HEADERS_OK),
    (
        "pbpstats game-lineups",
        f"https://api.pbpstats.com/get-game-stats?GameId={GAME}&Type=Lineup",
        PLAIN_HEADERS_OK,
    ),
    # CONTROL. This is the exact endpoint `nba context` fetches several times a day from this
    # same workflow environment, so it is known-good. If the control fails, the probe is broken --
    # not the internet. That is how the first run of this script was caught reporting false blocks.
    (
        "espn injuries (CONTROL)",
        "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries",
        PLAIN_HEADERS_OK,
    ),
    # hoopR publishes season-level NBA play-by-play as parquet in GitHub RELEASES. Being on GitHub
    # matters: reachable from a runner, effectively unrate-limited, versioned and reproducible --
    # exactly what an archive of record needs and what a live JSON API is worst at. Ask the API
    # for the real asset names rather than guessing a URL (a guess returned 404 first time).
    (
        "hoopR releases (index)",
        "https://api.github.com/repos/sportsdataverse/hoopR-data/releases?per_page=100",
        PLAIN_HEADERS_OK,
    ),
]


def probe(name: str, url: str, headers: dict) -> dict:
    t0 = time.time()
    try:
        budget = SLOW_BUDGET_S if name in SLOW else 40.0
        with httpx.Client(timeout=budget, follow_redirects=True, headers=headers) as c:
            r = c.get(url)
            body = r.content
            dt = time.time() - t0
            if r.status_code >= 400:
                return {
                    "name": name,
                    "status": r.status_code,
                    "bytes": len(body),
                    "seconds": round(dt, 2),
                    "shape": f"HTTP {r.status_code}",
                }
            shape = ""
            if name.startswith("hoopR releases"):
                try:
                    rel = json.loads(body)
                    tags = [r["tag_name"] for r in rel]
                    nba = [t for t in tags if "nba" in t.lower()]
                    sample = next(
                        (
                            a["name"]
                            for r in rel
                            if "nba" in r["tag_name"].lower()
                            for a in r.get("assets", [])
                        ),
                        None,
                    )
                    n_assets = sum(len(r.get("assets", [])) for r in rel if "nba" in r["tag_name"].lower())
                    return {
                        "name": name,
                        "status": r.status_code,
                        "bytes": len(body),
                        "seconds": round(dt, 2),
                        "shape": f"nba tags={nba[:6]} nba_assets={n_assets} sample={sample}",
                    }
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    return {
                        "name": name,
                        "status": r.status_code,
                        "bytes": len(body),
                        "seconds": round(dt, 2),
                        "shape": f"unparsed: {e}",
                    }
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
            return {
                "name": name,
                "status": r.status_code,
                "bytes": len(body),
                "seconds": round(dt, 2),
                "shape": shape,
            }
    except Exception as e:  # noqa: BLE001 - a probe reports failure, it does not raise
        return {
            "name": name,
            "status": None,
            "bytes": 0,
            "seconds": round(time.time() - t0, 2),
            "shape": f"{type(e).__name__}: {e}",
        }


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
