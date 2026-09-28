"""Empirically establish what ESPN play-by-play coordinates actually mean.

Phase 5 of the shot-profile mission, and it exists because the alternative is guessing. The source
audit already measured that `plays` carries a `coordinate` on most events and that many hold
ESPN's int32 sentinel rather than a location. What it did NOT establish is the *geometry*: the
range, the orientation, whether the two teams shoot at opposite ends, whether the ends swap at
half-time, and which event types legitimately carry no location at all.

Every one of those is a question a zone classifier silently answers wrong if nobody asks it. A
classifier built on an assumed origin would put corner threes in the paint and nobody would notice,
because the output still looks like a shot chart.

Runs on a GitHub-hosted runner: `site.api.espn.com` is denied by the build container's egress
policy (403 on CONNECT) and answers fine from Actions, which is the same split the granular source
audit documented.

It reports statistics. It does not decide the transform -- that judgement belongs in a document a
person can disagree with.
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from typing import Any

import httpx

from nba_edge.data.boxscore import ESPN_SUMMARY_URL
from nba_edge.data.http import PLAIN_HEADERS_OK

# ESPN encodes "no location recorded" as an int32-derived sentinel, not as a null. Anything beyond
# court-plausible bounds is treated as missing rather than as a coordinate.
SENTINEL_ABS = 100_000


def usable(c: Any) -> bool:
    if not isinstance(c, dict):
        return False
    x, y = c.get("x"), c.get("y")
    return all(isinstance(v, (int, float)) and abs(v) < SENTINEL_ABS for v in (x, y))


def fetch(event_id: str, client: httpx.Client) -> dict[str, Any] | None:
    try:
        r = client.get(ESPN_SUMMARY_URL.format(event_id=event_id))
        if r.status_code != 200:
            print(f"  {event_id}: HTTP {r.status_code}")
            return None
        return r.json()
    except Exception as e:  # noqa: BLE001 - one bad game must not end the probe
        print(f"  {event_id}: {type(e).__name__}: {str(e)[:100]}")
        return None


def analyse(payload: dict[str, Any], acc: dict[str, Any]) -> None:
    plays = payload.get("plays")
    if not isinstance(plays, list):
        acc["games_without_plays"] += 1
        return
    acc["games_with_plays"] += 1
    acc["n_plays"] += len(plays)

    # Which teams are home/away, so orientation can be tested per team rather than in aggregate.
    home_id = away_id = None
    for t in (payload.get("header", {}).get("competitions") or [{}])[0].get("competitors", []):
        if t.get("homeAway") == "home":
            home_id = str(t.get("id"))
        elif t.get("homeAway") == "away":
            away_id = str(t.get("id"))

    for p in plays:
        if not isinstance(p, dict):
            continue
        ptype = (p.get("type") or {}).get("text") or "?"
        shooting = bool(p.get("shootingPlay"))
        scoring = bool(p.get("scoringPlay"))
        coord = p.get("coordinate")
        has_key = isinstance(coord, dict)
        good = usable(coord)
        text = (p.get("text") or "").lower()
        is_ft = "free throw" in text or "free throw" in ptype.lower()

        acc["type_counts"][ptype] += 1
        if shooting:
            acc["shooting_types"][ptype] += 1
        if has_key and not good:
            acc["sentinel_types"][ptype] += 1
            if isinstance(coord, dict):
                acc["sentinel_values"][f"{coord.get('x')},{coord.get('y')}"] += 1
        if not has_key:
            acc["no_coord_key_types"][ptype] += 1

        if is_ft:
            acc["ft_total"] += 1
            acc["ft_with_usable_coord"] += int(good)

        if not good:
            continue

        x, y = float(coord["x"]), float(coord["y"])
        acc["xs"].append(x)
        acc["ys"].append(y)
        acc["usable"] += 1
        acc["usable_shooting"] += int(shooting)
        acc["usable_nonshooting_types"][ptype] += int(not shooting)

        period = (p.get("period") or {}).get("number")
        team = str((p.get("team") or {}).get("id") or "")
        if team and period:
            half = 1 if period <= 2 else 2
            side = "home" if team == home_id else ("away" if team == away_id else "?")
            if side != "?":
                acc["by_side_half"][(side, half)].append(x)

        if scoring:
            acc["made_xs"].append(x)
        elif shooting:
            acc["miss_xs"].append(x)

        sv = p.get("scoreValue")
        if isinstance(sv, int) and sv in (2, 3) and shooting:
            acc["by_value"][sv].append((x, y))


def describe(vals: list[float], name: str) -> str:
    if not vals:
        return f"  {name}: (none)"
    q = statistics.quantiles(vals, n=20) if len(vals) > 20 else []
    return (f"  {name}: n={len(vals)} min={min(vals):.1f} p5={q[0]:.1f} median={statistics.median(vals):.1f} "
            f"p95={q[-1]:.1f} max={max(vals):.1f}" if q else
            f"  {name}: n={len(vals)} min={min(vals):.1f} max={max(vals):.1f}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", default="2024-25")
    ap.add_argument("--games", type=int, default=12)
    ap.add_argument("--events", default="data/history/espn/done_events_{season}.json")
    args = ap.parse_args()

    path = args.events.format(season=args.season)
    ids = [e.split(":")[-1] for e in json.load(open(path))["events"]]
    # Spread across the season rather than taking the first N: early-season and late-season games
    # sit in different parts of ESPN's own data history and may not be encoded identically.
    step = max(1, len(ids) // args.games)
    sample = ids[::step][: args.games]
    print(f"probing {len(sample)} games from {args.season} (of {len(ids)} known)")

    acc: dict[str, Any] = {
        "games_with_plays": 0, "games_without_plays": 0, "n_plays": 0, "usable": 0,
        "usable_shooting": 0, "ft_total": 0, "ft_with_usable_coord": 0,
        "xs": [], "ys": [], "made_xs": [], "miss_xs": [],
        "type_counts": Counter(), "shooting_types": Counter(), "sentinel_types": Counter(),
        "sentinel_values": Counter(), "no_coord_key_types": Counter(),
        "usable_nonshooting_types": Counter(),
        "by_side_half": defaultdict(list), "by_value": defaultdict(list),
    }

    with httpx.Client(timeout=40, follow_redirects=True, headers=PLAIN_HEADERS_OK) as client:
        for eid in sample:
            payload = fetch(eid, client)
            if payload:
                analyse(payload, acc)

    print("\n== coverage ==")
    print(f"  games with plays      : {acc['games_with_plays']}")
    print(f"  games WITHOUT plays   : {acc['games_without_plays']}")
    print(f"  play events           : {acc['n_plays']}")
    print(f"  usable coordinates    : {acc['usable']} ({100*acc['usable']/max(1,acc['n_plays']):.1f}%)")
    print(f"  of those, shootingPlay: {acc['usable_shooting']}")

    print("\n== coordinate range ==")
    print(describe(acc["xs"], "x"))
    print(describe(acc["ys"], "y"))

    print("\n== orientation: does x separate the two teams, and does it flip at half? ==")
    for (side, half), xs in sorted(acc["by_side_half"].items()):
        if xs:
            print(f"  {side:4s} half {half}: n={len(xs):5d} mean_x={statistics.mean(xs):6.1f} median_x={statistics.median(xs):6.1f}")

    print("\n== 2PT vs 3PT geometry (sanity: 3s should sit farther from a basket) ==")
    for v, pts in sorted(acc["by_value"].items()):
        if pts:
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            print(f"  {v}PT: n={len(pts)} mean_x={statistics.mean(xs):.1f} mean_y={statistics.mean(ys):.1f} "
                  f"x_range=({min(xs):.0f},{max(xs):.0f}) y_range=({min(ys):.0f},{max(ys):.0f})")

    print("\n== free throws ==")
    print(f"  free-throw events: {acc['ft_total']}, with a usable coordinate: {acc['ft_with_usable_coord']}")

    print("\n== sentinel values seen ==")
    for val, n in acc["sentinel_values"].most_common(5):
        print(f"  {val}: {n}")

    print("\n== event types that legitimately carry NO usable coordinate ==")
    for t, n in acc["sentinel_types"].most_common(12):
        print(f"  sentinel  {n:5d}  {t}")
    for t, n in acc["no_coord_key_types"].most_common(6):
        print(f"  no key    {n:5d}  {t}")

    print("\n== non-shooting events that DO carry a usable coordinate ==")
    for t, n in acc["usable_nonshooting_types"].most_common(12):
        if n:
            print(f"  {n:5d}  {t}")

    print("\n== made vs missed ==")
    print(describe(acc["made_xs"], "made x"))
    print(describe(acc["miss_xs"], "miss x"))

    print("\nPROBE_JSON " + json.dumps({
        "games_with_plays": acc["games_with_plays"],
        "n_plays": acc["n_plays"],
        "usable": acc["usable"],
        "x_min": min(acc["xs"]) if acc["xs"] else None, "x_max": max(acc["xs"]) if acc["xs"] else None,
        "y_min": min(acc["ys"]) if acc["ys"] else None, "y_max": max(acc["ys"]) if acc["ys"] else None,
        "ft_total": acc["ft_total"], "ft_with_coord": acc["ft_with_usable_coord"],
        "side_half_mean_x": {f"{s}_{h}": statistics.mean(v) for (s, h), v in acc["by_side_half"].items() if v},
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
