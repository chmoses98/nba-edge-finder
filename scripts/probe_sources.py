"""Probe NBA data sources from a network-capable runner (GitHub Actions). Records status, latency, size,
content type, and a small structural sample per source. Output: JSON + Markdown for docs/NBA_DATA_SOURCE_AUDIT.md.
Never raises; every failure is recorded as data."""

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

NBA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
}
PLAIN = {"User-Agent": "nba-edge-finder/0.1 (+https://github.com/chmoses98/nba-edge-finder)", "Accept": "*/*"}

SOURCES = [
    ("kalshi_exchange_status", "https://api.elections.kalshi.com/trade-api/v2/exchange/status", PLAIN),
    ("kalshi_series_nba", "https://api.elections.kalshi.com/trade-api/v2/series?category=Sports&limit=200", PLAIN),
    ("nba_cdn_schedule", "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json", NBA_HEADERS),
    ("nba_cdn_todays_scoreboard", "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json", NBA_HEADERS),
    ("nba_cdn_boxscore_sample", "https://cdn.nba.com/static/json/liveData/boxscore/boxscore_0022500001.json", NBA_HEADERS),
    ("nba_cdn_pbp_sample", "https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_0022500001.json", NBA_HEADERS),
    ("nba_stats_leaguegamelog_team", "https://stats.nba.com/stats/leaguegamelog?Counter=1000&DateFrom=&DateTo=&Direction=DESC&LeagueID=00&PlayerOrTeam=T&Season=2025-26&SeasonType=Regular+Season&Sorter=DATE", NBA_HEADERS),
    ("nba_stats_playergamelogs", "https://stats.nba.com/stats/playergamelogs?Season=2025-26&SeasonType=Regular+Season&LeagueID=00", NBA_HEADERS),
    ("nba_stats_commonallplayers", "https://stats.nba.com/stats/commonallplayers?IsOnlyCurrentSeason=0&LeagueID=00&Season=2025-26", NBA_HEADERS),
    ("nba_stats_scheduleleaguev2", "https://stats.nba.com/stats/scheduleleaguev2?Season=2026-27&LeagueID=00", NBA_HEADERS),
    ("nba_stats_boxscoretraditionalv3", "https://stats.nba.com/stats/boxscoretraditionalv3?GameID=0022500001&LeagueID=00&endPeriod=0&endRange=28800&rangeType=0&startPeriod=0&startRange=0", NBA_HEADERS),
    ("nba_stats_gamerotation", "https://stats.nba.com/stats/gamerotation?GameID=0022500001&LeagueID=00", NBA_HEADERS),
    ("nba_stats_leaguedashptstats", "https://stats.nba.com/stats/leaguedashptstats?College=&Conference=&Country=&DateFrom=&DateTo=&Division=&DraftPick=&DraftYear=&GameScope=&Height=&LastNGames=0&LeagueID=00&Location=&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PerMode=PerGame&PlayerExperience=&PlayerOrTeam=Player&PlayerPosition=&PtMeasureType=Possessions&Season=2025-26&SeasonSegment=&SeasonType=Regular+Season&StarterBench=&TeamID=0&VsConference=&VsDivision=&Weight=", NBA_HEADERS),
    ("nba_injury_report_pdf_index", "https://official.nba.com/nba-injury-report-2025-26-season/", PLAIN),
    ("nba_injury_report_pdf_sample", "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2025-12-26_06_00PM.pdf", PLAIN),
    ("nba_referee_assignments", "https://official.nba.com/referee-assignments/", PLAIN),
    ("espn_scoreboard", "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard", PLAIN),
    ("espn_injuries", "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries", PLAIN),
    ("espn_teams", "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams", PLAIN),
    ("bref_schedule", "https://www.basketball-reference.com/leagues/NBA_2026_games.html", PLAIN),
    ("pbpstats_totals", "https://api.pbpstats.com/get-totals/nba?Season=2025-26&SeasonType=Regular%20Season&Type=Team", PLAIN),
    ("rotowire_lineups", "https://www.rotowire.com/basketball/nba-lineups.php", PLAIN),
    ("odds_api_sports_noauth", "https://api.the-odds-api.com/v4/sports/?apiKey=", PLAIN),
    ("nbastuffer_placeholder", "https://www.nbastuffer.com/", PLAIN),
]


def probe(name: str, url: str, headers: dict[str, str]) -> dict:
    t0 = time.time()
    rec = {"name": name, "url": url, "ok": False}
    try:
        with httpx.Client(timeout=25, follow_redirects=True, headers=headers) as c:
            r = c.get(url)
        rec.update(status=r.status_code, ms=int((time.time() - t0) * 1000), bytes=len(r.content), content_type=r.headers.get("content-type", ""))
        rec["ok"] = r.status_code == 200
        ct = rec["content_type"]
        if "json" in ct or r.text[:1] in "{[":
            try:
                j = r.json()
                rec["json_keys"] = list(j.keys())[:25] if isinstance(j, dict) else f"list[{len(j)}]"
                if isinstance(j, dict):
                    for k in ("resultSets", "resultSet", "leagueSchedule", "scoreboard", "series", "events", "markets", "game"):
                        if k in j:
                            v = j[k]
                            if isinstance(v, list):
                                rec[f"sample_{k}"] = json.dumps(v[0], default=str)[:800] if v else "[]"
                            elif isinstance(v, dict):
                                rec[f"sample_{k}_keys"] = list(v.keys())[:25]
            except Exception as e:  # noqa: BLE001
                rec["json_error"] = str(e)[:200]
        else:
            rec["text_head"] = r.text[:300].replace("\n", " ")
    except Exception as e:  # noqa: BLE001
        rec.update(error=f"{type(e).__name__}: {e}"[:300], ms=int((time.time() - t0) * 1000))
    return rec


def main(out_dir: str) -> int:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    results = [probe(*s) for s in SOURCES]
    stamp = datetime.now(tz=UTC).isoformat(timespec="seconds")
    (out / "probe_results.json").write_text(json.dumps({"probed_at": stamp, "results": results}, indent=1))
    md = ["# Data source probe", "", f"probed_at: {stamp}", "", "| source | status | ms | bytes | ok | note |", "|---|---:|---:|---:|---|---|"]
    for r in results:
        note = r.get("error") or r.get("json_error") or (", ".join(r.get("json_keys", [])[:6]) if isinstance(r.get("json_keys"), list) else r.get("json_keys", "")) or r.get("text_head", "")[:80]
        md.append(f"| {r['name']} | {r.get('status','-')} | {r.get('ms','-')} | {r.get('bytes','-')} | {'yes' if r['ok'] else 'NO'} | {str(note)[:100].replace('|','/')} |")
    (out / "probe_results.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "out/probe"))
