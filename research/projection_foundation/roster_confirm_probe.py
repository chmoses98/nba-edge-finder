"""Probe (not product code): try to confirm, from sources other than ESPN, the players only ESPN's roster lists.
Runs inside research/projection_foundation with PYTHONPATH=. on a GitHub runner. Read-only."""
import json, re, sys, time, urllib.request, urllib.error
from nba.live import roster_audit as RA

TEAMS = {"BOS": (1610612738, "celtics", "boston-celtics", "bos"), "DET": (1610612765, "pistons", "detroit-pistons", "det"),
         "NYK": (1610612752, "knicks", "new-york-knicks", "ny"), "PHI": (1610612755, "sixers", "philadelphia-76ers", "phi"),
         "OKC": (1610612760, "thunder", "oklahoma-city-thunder", "okc"), "SAS": (1610612759, "spurs", "san-antonio-spurs", "sa")}
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

def get(url, headers=None, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/json,*/*", "Accept-Language": "en-US,en;q=0.9", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:  # noqa: BLE001
        return 0, str(e)[:80]

def sources(abbr):
    tid, nick, slug, short = TEAMS[abbr]
    return {
        "nba.com team page": f"https://www.nba.com/team/{tid}/{nick}",
        "nba.com stats roster": (f"https://stats.nba.com/stats/commonteamroster?LeagueID=00&Season=2026-27&TeamID={tid}", {"Referer": "https://www.nba.com/", "Origin": "https://www.nba.com", "x-nba-stats-origin": "stats", "x-nba-stats-token": "true"}),
        "team site (nba.com/{nick})": f"https://www.nba.com/{nick}/roster",
        "CBS Sports roster": f"https://www.cbssports.com/nba/teams/{abbr}/{slug}/roster/",
        "HoopsHype roster": f"https://hoopshype.com/team/{slug}/roster/",
        "Spotrac": f"https://www.spotrac.com/nba/{slug}/",
        "ESPN web roster (same provider)": f"https://www.espn.com/nba/team/roster/_/name/{short}",
        "Basketball-Reference": f"https://www.basketball-reference.com/teams/{abbr}/2027.html",
    }

def main():
    import glob, os
    archive = sys.argv[1]
    feed = RA.load_feed(archive); official = RA.load_official(archive, None)
    espn = RA.espn_rosters(RA.http_fetcher()); tx = RA.espn_transactions(RA.http_fetcher(), [p["name"] for p in feed["players"] if p["family"] == "minutes" and any(a.startswith("New team") for a in p.get("adjustments", []))])
    ind = RA.bbref_rosters(RA.http_fetcher(), sorted({p["team"] for p in feed["players"]}), 2027)
    ind = RA.usable(ind, espn)
    ident = RA.identity(feed, espn, ind, official, tx.get("rows", []))
    todo = [(t, u["name"]) for t, r in ident.items() for u in r.get("unconfirmed_by_independent_roster", []) if not u["corroborated_by"]]
    allun = [(t, u["name"], u["corroborated_by"]) for t, r in ident.items() for u in r.get("unconfirmed_by_independent_roster", [])]
    print("UNCONFIRMED by bbref:", len(allun), "| without corroboration:", len(todo))
    for t, n, c in allun: print("  ", t, n, c or "ESPN ONLY")
    cache = {}
    results = {}
    for t, name in todo:
        key = RA.norm(name)
        results[(t, name)] = {}
        for sname, spec in sources(t).items():
            url, hdr = (spec if isinstance(spec, tuple) else (spec, None))
            if url not in cache:
                cache[url] = get(url, hdr)
                time.sleep(0.5)
            st, body = cache[url]
            norm_body = RA.norm(re.sub(r"<[^>]+>", " ", body)) if st == 200 else ""
            hit = (st == 200) and key in norm_body
            results[(t, name)][sname] = ("HIT" if hit else f"no({st})")
    print("\nSOURCE STATUS (bytes):")
    for url, (st, body) in cache.items(): print(f"  {st:3d} {len(body):8d}  {url}")
    print("\nCONFIRMATION MATRIX (player-name found on the team's page of each source):")
    for (t, name), r in results.items(): print(f"  {t} {name:22} " + " | ".join(f"{k.split(' (')[0]}: {v}" for k, v in r.items()))
    json.dump({f"{t}|{n}": r for (t, n), r in results.items()}, open("/tmp/confirm.json", "w"), indent=1)

main()
