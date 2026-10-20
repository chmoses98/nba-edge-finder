"""Roster / identity / availability audit of a published NBA projection feed (read-only).

    python -m nba.live.roster_audit --archive <projection-data checkout> [--json OUT] [--offline FIXTURE.json]

Why this exists: the Projection Foundation publishes every player row with a team-level `team_consistency` REVIEW when a team's
expected minutes (sum of p(play) x E[minutes | play]) had to be normalised to the 241.5 minutes a game offers by more than 10 %
("Roles carried over from previous teams overlapped; early-season roster uncertainty."). Before that finding is treated as the
documented early-season effect and nothing else, this audit checks the things that could ALSO inflate the sum, against sources
outside the projection pipeline's own cache:

  1. team identity         every projected player is on the team the feed says, per a freshly fetched ESPN roster and (where
                           the host answers) the league's own roster; nobody is on two teams; the feed omits nobody who is on
                           the roster and in a rotation role (listed, not blocked)
  2. trades / transactions every player the feed marks "New team" is on the new team now; recent transactions that touch a
                           projected team are listed
  3. availability          every OUT / DOUBTFUL / QUESTIONABLE designation in the official injury report (archived by the run
                           with its provenance) is reflected in the row's participation, and every ruled-out row is BLOCK
  4. minutes assumptions   Sum p(play) x E[minutes | play] by team, how much of it comes from "New team" roles, and how much from
                           players the model gives a middling p(play) (the deep bench), so an overshoot that exists WITHOUT any
                           carried-over role is visible as such

Network access is injected (`Fetcher`) so the decision logic is tested on recorded data; the live fetch runs on a GitHub-hosted
runner (the build sandbox cannot reach ESPN or nba.com). Nothing here changes a projection, a gate or an approval.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable

ESPN_TEAMS = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams"
ESPN_ROSTER = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{id}/roster"
ESPN_TRANSACTIONS = ["https://site.web.api.espn.com/apis/site/v2/sports/basketball/nba/transactions?limit=1000",
                     "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/transactions?limit=1000"]
NBA_ROSTER = "https://stats.nba.com/stats/commonteamroster?LeagueID=00&Season={season}&TeamID={id}"
NBA_TEAM_IDS = {"ATL": 1610612737, "BOS": 1610612738, "BKN": 1610612751, "CHA": 1610612766, "CHI": 1610612741, "CLE": 1610612739,
                "DAL": 1610612742, "DEN": 1610612743, "DET": 1610612765, "GS": 1610612744, "GSW": 1610612744, "HOU": 1610612745,
                "IND": 1610612754, "LAC": 1610612746, "LAL": 1610612747, "MEM": 1610612763, "MIA": 1610612748, "MIL": 1610612749,
                "MIN": 1610612750, "NO": 1610612740, "NOP": 1610612740, "NY": 1610612752, "NYK": 1610612752, "OKC": 1610612760,
                "ORL": 1610612753, "PHI": 1610612755, "PHX": 1610612756, "POR": 1610612757, "SAC": 1610612758, "SA": 1610612759,
                "SAS": 1610612759, "TOR": 1610612761, "UTA": 1610612762, "UTAH": 1610612762, "WAS": 1610612764}
ALIASES = {"GS": "GSW", "NO": "NOP", "NY": "NYK", "SA": "SAS", "UTAH": "UTA", "WSH": "WAS", "PHO": "PHX"}
BUDGET = 241.5
BIG_SCALE = 0.10          # reconcile.Config.big_scale: a normalisation larger than this is the REVIEW the gate raises
DEEP_BENCH_P = (0.0, 0.85)  # players the model gives a middling chance of playing at all

Fetcher = Callable[[str, dict | None], tuple[int, Any]]   # (url, headers) -> (http status, parsed JSON or text)


def norm(name: str) -> str:
    s = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b\.?", "", s)
    return re.sub(r"[^a-z0-9]", "", s)


def team(abbr: str) -> str:
    a = (abbr or "").upper()
    return ALIASES.get(a, a)


def http_fetcher(timeout: float = 12.0) -> Fetcher:
    def get(url: str, headers: dict | None = None) -> tuple[int, Any]:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research audit)", "Accept": "application/json, text/html", **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8", "replace")
                try:
                    return r.status, json.loads(body)
                except ValueError:
                    return r.status, body
        except urllib.error.HTTPError as e:
            return e.code, None
        except Exception as e:  # noqa: BLE001 - a source that does not answer is reported, not fatal
            return 0, str(e)[:160]
    return get


# ----------------------------------------------------------------------------------------------------------------- sources

def espn_rosters(get: Fetcher) -> dict[str, Any]:
    """{"status": ..., "teams": {abbr: [{"id","name","status"}]}} from a fresh ESPN fetch."""
    st, doc = get(ESPN_TEAMS, None)
    if st != 200 or not isinstance(doc, dict):
        return {"status": f"teams list HTTP {st}", "teams": {}}
    teams = [t.get("team", {}) for s in doc.get("sports", []) for lg in s.get("leagues", []) for t in lg.get("teams", [])]
    out: dict[str, list[dict]] = {}
    for t in teams:
        st, r = get(ESPN_ROSTER.format(id=t.get("id")), None)
        if st != 200 or not isinstance(r, dict):
            continue
        out[team(t.get("abbreviation"))] = [{"id": str(a.get("id")), "name": a.get("fullName") or a.get("displayName"),
                                              "status": (a.get("status") or {}).get("type"),
                                              "injuries": [i.get("status") for i in a.get("injuries", [])]} for a in r.get("athletes", [])]
    return {"status": "ok" if out else "no roster answered", "teams": out, "n_teams": len(out)}


def nba_rosters(get: Fetcher, abbrs: list[str], season: str) -> dict[str, Any]:
    """The league's own roster (stats.nba.com commonteamroster), best effort: cloud egress is often refused."""
    hdr = {"Referer": "https://www.nba.com/", "Origin": "https://www.nba.com", "x-nba-stats-origin": "stats", "x-nba-stats-token": "true"}
    out: dict[str, list[dict]] = {}
    statuses: dict[str, Any] = {}
    for a in abbrs:
        tid = NBA_TEAM_IDS.get(a)
        if not tid:
            continue
        st, doc = get(NBA_ROSTER.format(season=season, id=tid), hdr)
        statuses[a] = st
        try:
            rs = next(x for x in doc["resultSets"] if x["name"] == "CommonTeamRoster")
            cols = rs["headers"]
            out[a] = [{"id": str(r[cols.index("PLAYER_ID")]), "name": r[cols.index("PLAYER")]} for r in rs["rowSet"]]
        except Exception:  # noqa: BLE001
            continue
    return {"status": "ok" if out else f"unavailable {statuses}", "teams": out, "http": statuses}


BBREF_ROSTER = "https://www.basketball-reference.com/teams/{abbr}/{year}.html"
BBREF_CODE = {"BKN": "BRK", "CHA": "CHO", "PHX": "PHO"}


def parse_bbref_roster(html: str) -> list[dict]:
    """Player names from the `roster` table of a Basketball-Reference team page (an independent, non-ESPN source)."""
    m = re.search(r'<table[^>]*id="roster"[^>]*>(.*?)</table>', html or "", re.S)
    if not m:
        return []
    cells = re.findall(r'<td[^>]*data-stat="player"[^>]*>(.*?)</td>', m.group(1), re.S)      # body cells only: the header cell is a <th>
    return [{"id": "", "name": re.sub(r"<[^>]+>", "", x).strip()} for x in cells if re.sub(r"<[^>]+>", "", x).strip()]


def bbref_rosters(get: Fetcher, abbrs: list[str], year: int) -> dict[str, Any]:
    out: dict[str, list[dict]] = {}
    statuses: dict[str, Any] = {}
    for a in abbrs:
        st, html = get(BBREF_ROSTER.format(abbr=BBREF_CODE.get(a, a), year=year), None)
        statuses[a] = st
        rows = parse_bbref_roster(html) if isinstance(html, str) else []
        if rows:
            out[a] = rows
    return {"status": "ok" if out else f"unavailable {statuses}", "teams": out, "http": statuses}


def espn_transactions(get: Fetcher, names: list[str] | None = None) -> dict[str, Any]:
    """Recent league transactions (ESPN). With `names`, every transaction text that mentions one of them is returned too."""
    for url in ESPN_TRANSACTIONS:
        st, doc = get(url, None)
        if st == 200 and isinstance(doc, dict):
            tx = doc.get("transactions") or doc.get("items") or []
            rows = [{"date": t.get("date"), "team": (t.get("team") or {}).get("abbreviation"), "text": (t.get("description") or t.get("text") or "")[:240]} for t in tx]
            wanted = {norm(n) for n in (names or [])}
            hits = [r for r in rows if any(w and w in norm(r["text"]) for w in wanted)]
            return {"status": "ok", "url": url, "n": len(rows), "oldest": min((r["date"] for r in rows if r["date"]), default=None), "rows": rows[:200], "name_hits": hits}
    return {"status": "unavailable", "rows": [], "name_hits": []}


# ----------------------------------------------------------------------------------------------------------------- analysis

def load_feed(archive: str) -> dict:
    with open(os.path.join(archive, "projections", "nba", "latest.json")) as f:
        return json.load(f)


def load_official(archive: str, slate: str | None) -> list[dict]:
    """Official-report observations the run archived (with provenance), newest capture per (entity, event)."""
    import glob
    import gzip
    best: dict[tuple, dict] = {}
    for p in sorted(glob.glob(os.path.join(archive, "availability", "nba", "*", "*.jsonl.gz"))):
        with gzip.open(p, "rt") as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                if r.get("source") != "nba_official_injury_report":
                    continue
                k = (r.get("entity_id"), r.get("event_id"))
                if k not in best or r["captured_utc"] >= best[k]["captured_utc"]:
                    best[k] = r
    return list(best.values())


def minutes_structure(feed: dict) -> dict[str, dict]:
    """Per team-game: the sum the reconciliation saw, where it comes from, and what it would be without carried-over roles."""
    recs = {(str(r["game_id"]).replace("espn:", ""), r["team"]): r for r in feed.get("reconciliation", [])}
    out: dict[str, dict] = {}
    by: dict[tuple, list[dict]] = defaultdict(list)
    for p in feed["players"]:
        if p["family"] == "minutes":
            by[(str(p["game_id"]).replace("espn:", ""), p["team"])].append(p)
    for (gid, t), ps in by.items():
        rec = recs.get((gid, t), {})
        sc = rec.get("minutes_scale") or 1.0
        rows = []
        for p in ps:
            part = p["participation"]
            pp = float(part.get("p_play") or 0.0)
            cond = float(p["mean"]) / sc          # the published mean is after the team normalisation
            new_team = any(a.startswith("New team") for a in p.get("adjustments", []))
            rows.append({"name": p["name"], "id": p["player_id"], "p": pp, "cond_min": cond, "new_team": new_team,
                         "status": part.get("status"), "designation": part.get("designation"), "implicit": bool(part.get("implicit"))})
        tot = sum(r["p"] * r["cond_min"] for r in rows)
        new = sum(r["p"] * r["cond_min"] for r in rows if r["new_team"])
        deep = sum(r["p"] * r["cond_min"] for r in rows if DEEP_BENCH_P[0] < r["p"] < DEEP_BENCH_P[1])
        out[f"{t}"] = {"game_id": gid, "n_players": len(rows), "sum_p": round(sum(r["p"] for r in rows), 2), "minutes_sum_raw": rec.get("minutes_sum_raw"),
                       "minutes_sum_recomputed": round(tot, 1), "minutes_scale": rec.get("minutes_scale"), "status": rec.get("status"),
                       "from_new_team_roles": round(new, 1), "n_new_team": sum(r["new_team"] for r in rows),
                       "sum_without_new_team_roles": round(tot - new, 1), "overshoot_without_new_team_roles": round((tot - new) / BUDGET - 1, 3),
                       "from_middling_p_play": round(deep, 1), "n_middling_p_play": sum(1 for r in rows if DEEP_BENCH_P[0] < r["p"] < DEEP_BENCH_P[1]),
                       "players": rows}
    return out


def usable(indep: dict, espn: dict, floor: float = 0.6) -> dict:
    """Keep only teams whose independent roster is plausibly complete (at least `floor` of the ESPN roster): a page that parsed to a
    handful of names is a source problem, and comparing against it would invent roster errors."""
    keep = {t: r for t, r in (indep.get("teams") or {}).items() if len(r) >= floor * max(1, len(espn.get("teams", {}).get(t, [])))}
    dropped = sorted(set(indep.get("teams") or {}) - set(keep))
    return {**indep, "teams": keep, "dropped_incomplete": dropped}


def identity(feed: dict, espn: dict, nba: dict) -> dict[str, dict]:
    """Per team: feed players missing from each roster source, roster players the feed omits, players on two teams."""
    feed_by: dict[str, dict[str, dict]] = defaultdict(dict)
    for p in feed["players"]:
        if p["family"] == "minutes":
            feed_by[p["team"]][p["player_id"].replace("espn:", "")] = p
    espn_team_of: dict[str, set] = defaultdict(set)
    for t, ps in espn["teams"].items():
        for a in ps:
            espn_team_of[a["id"]].add(t)
    res: dict[str, dict] = {}
    for t, fp in feed_by.items():
        e = {a["id"]: a for a in espn["teams"].get(t, [])}
        n = {(a["id"] or norm(a["name"])): a for a in nba["teams"].get(t, [])}      # sources without ids are keyed by name
        row: dict[str, Any] = {"feed": len(fp), "espn_roster": len(e) or None, "nba_roster": len(n) or None}
        row["not_on_espn_roster_of_this_team"] = [f"{p['name']} ({p['player_id']})" + (f" -> now on {sorted(espn_team_of.get(i, []))}" if espn_team_of.get(i) else " -> on no NBA roster")
                                                   for i, p in fp.items() if e and i not in e]
        if n:
            nn = {norm(a["name"]) for a in n.values()}
            row["not_on_league_roster_of_this_team"] = [p["name"] for p in fp.values() if norm(p["name"]) not in nn]
            ff = {norm(p["name"]) for p in fp.values()}
            row["league_roster_not_in_feed"] = [a["name"] for a in n.values() if norm(a["name"]) not in ff]
        row["espn_roster_not_in_feed"] = [f"{a['name']} ({a['status'] or ''}{'; ' + ','.join(a['injuries']) if a['injuries'] else ''})" for i, a in e.items() if i not in fp] if e else None
        row["on_two_rosters"] = [p["name"] for i, p in fp.items() if len(espn_team_of.get(i, [])) > 1]
        res[t] = row
    return res


def availability_alignment(feed: dict, official: list[dict]) -> dict[str, Any]:
    """Official-report designations vs the published participation, and ruled-out rows vs the gate."""
    pl: dict[tuple, dict] = {}
    for p in feed["players"]:
        pl[(p["player_id"], p["game_id"], p["family"])] = p
    problems: list[str] = []
    counts: dict[str, int] = defaultdict(int)
    explicit = [r for r in official if (r.get("detail") or {}).get("implicit") is not True]
    for r in explicit:
        counts[r["status"]] += 1
        for fam in {k[2] for k in pl if k[0] == r["entity_id"] and k[1] == r["event_id"]}:
            p = pl[(r["entity_id"], r["event_id"], fam)]
            st = p["participation"]["status"]
            gate = p["gate"]["status"]
            if r["status"] == "OUT" and not (st in ("CONFIRMED_OUT", "LIKELY_OUT") and gate == "BLOCK"):
                problems.append(f"{r['entity_name']} {fam}: official OUT, feed {st}/{gate}")
            if r["status"] in ("QUESTIONABLE", "DOUBTFUL") and (st in ("CONFIRMED_ACTIVE", "LIKELY_ACTIVE") and gate == "PASS"):
                problems.append(f"{r['entity_name']} {fam}: official {r['status']}, feed {st}/{gate}")
    blocked_not_out = sorted({f"{p['name']} ({p['participation']['status']})" for p in feed["players"]
                              if p["gate"]["status"] == "BLOCK" and p["participation"]["status"] not in ("CONFIRMED_OUT", "LIKELY_OUT")})
    ruled_out_not_blocked = sorted({p["name"] for p in feed["players"]
                                    if p["participation"]["status"] in ("CONFIRMED_OUT", "LIKELY_OUT") and p["gate"]["status"] != "BLOCK"})
    return {"official_explicit_designations": dict(counts), "misaligned": problems[:30], "n_misaligned": len(problems),
            "ruled_out_rows_not_blocked": ruled_out_not_blocked, "blocked_but_not_ruled_out": blocked_not_out}


def audit(feed: dict, official: list[dict], espn: dict, nba: dict, tx: dict) -> dict[str, Any]:
    ms = minutes_structure(feed)
    nba = usable(nba, espn)
    ident = identity(feed, espn, nba)
    avail = availability_alignment(feed, official)
    errors: list[str] = []
    for t, r in ident.items():
        for k in ("not_on_espn_roster_of_this_team", "not_on_league_roster_of_this_team", "on_two_rosters"):
            for x in r.get(k) or []:
                errors.append(f"{t}: {k}: {x}")
    errors += [f"availability: {x}" for x in avail["misaligned"]]
    errors += [f"ruled-out row not blocked: {x}" for x in avail["ruled_out_rows_not_blocked"]]
    return {"schema": "sift.nba_roster_audit.v1", "feed_generated_utc": feed.get("generated_utc"), "slate": feed.get("slate_date"),
            "checked_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sources": {"espn_rosters": espn.get("status"), "independent_rosters": f"{nba.get('status')}; usable teams {sorted(nba.get('teams', {}))}; dropped as incomplete {nba.get('dropped_incomplete')}", "transactions": tx.get("status")},
            "minutes": {t: {k: v for k, v in m.items() if k != "players"} for t, m in ms.items()},
            "identity": ident, "availability": avail, "errors": errors, "genuine_roster_errors": len(errors),
            "transactions": [x for x in tx.get("rows", []) if x.get("team") in ms][:40],
            "transactions_about_new_team_players": tx.get("name_hits", []), "transactions_window": {"n": tx.get("n"), "oldest": tx.get("oldest")}}


def render(a: dict) -> str:
    L = [f"# NBA roster audit  feed {a['feed_generated_utc']}  slate {a['slate']}", f"sources: {a['sources']}", ""]
    L.append("team  n  sumP  raw   scale  status  fromNewTeam  sumWithoutNew(overshoot)  middlingP(n)")
    for t, m in a["minutes"].items():
        L.append(f"{t:4} {m['n_players']:3} {m['sum_p']:5} {m['minutes_sum_raw']!s:6} {m['minutes_scale']!s:6} {m['status']:6} {m['from_new_team_roles']:6}({m['n_new_team']}) "
                 f"{m['sum_without_new_team_roles']:6}({m['overshoot_without_new_team_roles']:+.0%}) {m['from_middling_p_play']:6}({m['n_middling_p_play']})")
    L.append("")
    for t, r in a["identity"].items():
        L.append(f"{t}: feed {r['feed']} · espn roster {r['espn_roster']} · league roster {r['nba_roster']}")
        for k in ("not_on_espn_roster_of_this_team", "not_on_league_roster_of_this_team", "on_two_rosters"):
            if r.get(k): L.append(f"   {k}: {r[k]}")
        for k in ("league_roster_not_in_feed", "espn_roster_not_in_feed"):
            if r.get(k): L.append(f"   {k}: {r[k]}")
    L += ["", f"availability: {a['availability']['official_explicit_designations']} · misaligned {a['availability']['n_misaligned']}",
          f"   ruled-out rows not blocked: {a['availability']['ruled_out_rows_not_blocked']}", f"   blocked but not ruled out: {a['availability']['blocked_but_not_ruled_out']}"]
    if a["transactions"]:
        L += ["", "recent transactions touching these teams:"] + [f"   {x['date']} {x['team']}: {x['text']}" for x in a["transactions"][:25]]
    if a.get("transactions_about_new_team_players"):
        L += ["", f"transactions naming a 'New team' player (window: {a['transactions_window']}):"] + [f"   {x['date']} {x['team']}: {x['text']}" for x in a["transactions_about_new_team_players"][:40]]
    L += ["", f"GENUINE ROSTER / AVAILABILITY ERRORS: {a['genuine_roster_errors']}"] + [f"   - {e}" for e in a["errors"][:40]]
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--archive", required=True)
    ap.add_argument("--json", default=None)
    ap.add_argument("--season", default=None, help="league roster season, e.g. 2026-27 (default: from the slate date)")
    a = ap.parse_args(argv)
    feed = load_feed(a.archive)
    official = load_official(a.archive, feed.get("slate_date"))
    get = http_fetcher()
    yr = int((feed.get("slate_date") or "2026-10-20")[:4])
    season = a.season or (f"{yr}-{str(yr + 1)[2:]}" if int((feed.get("slate_date") or "2026-10-20")[5:7]) >= 8 else f"{yr - 1}-{str(yr)[2:]}")
    teams = sorted({p["team"] for p in feed["players"]})
    new_team_names = sorted({p["name"] for p in feed["players"] if p["family"] == "minutes" and any(x.startswith("New team") for x in p.get("adjustments", []))})
    indep = nba_rosters(get, teams, season)
    if not indep["teams"]:                       # the league host refuses cloud egress: fall back to a second, non-ESPN source
        alt = bbref_rosters(get, teams, yr + 1 if int((feed.get("slate_date") or "2026-10-20")[5:7]) >= 8 else yr)
        indep = {**alt, "status": f"basketball-reference: {alt['status']} (league host: {indep['status']})"}
    res = audit(feed, official, espn_rosters(get), indep, espn_transactions(get, new_team_names))
    print(render(res))
    if a.json:
        with open(a.json, "w") as f:
            json.dump(res, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
