"""Data-integrity section of the weekly report: for every regular-season game of a window, which pregame evidence actually exists.

Everything is read from the archives (never from a workflow's colour):
  schedule         data-archive context/schedule (every game once; newest observation wins)
  forecasts        challenger forecasts archived before tip (pf_core forecast archive)
  availability     observations captured before tip (official report / ESPN / starters) per game
  game_forecasts   team-points forecasts (sift.game_forecast.v1)
  market_snapshots board snapshots by horizon (OPEN, T-90, T-60, T-30, T-10, LAST_VALID) and their gap to target
  decisions        paper decisions (trade + pass), by strategy
  outcomes         final player outcomes, team outcomes, paper settlements
  ledger           pregame/settle slot records (expected vs executed)

A game is `COMPLETE` only if every required item exists; otherwise the missing items are listed explicitly (never silently dropped).
"""
from __future__ import annotations

import os
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Any


from pf_core import availability as av, prospective as pr

from ..live import ledger as LED, schedule_plan as SP, watchdog as WD
from ..live.sources import iso, parse_ts
from . import store

REQUIRED = ("forecast", "participation_forecast", "availability_obs", "game_forecast", "snapshot_T-60", "decisions", "outcome",
            "team_outcome", "paper_settlement")


def _et_date(ts: str) -> str:
    from zoneinfo import ZoneInfo
    return parse_ts(ts).astimezone(ZoneInfo("America/New_York")).date().isoformat()


def games_in_window(ctx: str, start_et: str, end_et: str, season_types=("regular",)) -> list[dict]:
    out = []
    for g in WD.load_schedule(ctx, season_types):
        d = g.get("game_date_et") or _et_date(g["start_time_utc"])
        if start_et <= d <= end_et:
            out.append({**g, "game_date_et": d})
    return sorted(out, key=lambda g: (g["start_time_utc"], g["game_id"]))


def _days_for(games: list[dict]) -> list[str]:
    ds = set()
    for g in games:
        t = parse_ts(g["start_time_utc"])
        ds |= {t.strftime("%Y-%m-%d"), (t - timedelta(days=1)).strftime("%Y-%m-%d")}
    return sorted(ds)


def build(archive: str, ctx: str, start_et: str, end_et: str, now: datetime, season_types=("regular",),
          replay_allowed: bool = False) -> dict[str, Any]:
    games = games_in_window(ctx, start_et, end_et, season_types)
    days = _days_for(games)
    gids = {g["game_id"] for g in games}
    f = pr.load_forecasts(archive, "NBA", [d for d in days if os.path.isdir(os.path.join(archive, "forecasts", "nba", d))])
    f = f[f["game_id"].isin(gids)] if len(f) else f
    obs = [o for o in av.load_snapshots(archive, "NBA") if o.get("event_id") in gids] if os.path.isdir(os.path.join(archive, "availability")) else []
    gf = [r for r in store.read(archive, "game_forecasts", days) if r["game_id"] in gids]
    snaps = [r for r in store.read(archive, "market_snapshots", days) if r.get("game_id") in gids and (replay_allowed or not r.get("replay"))]
    dec = [r for r in store.read(archive, "decisions", days) if r.get("game_id") in gids and (replay_allowed or not r.get("replay"))]
    outc = pr._read(archive, "outcomes", "NBA", days) if os.path.isdir(os.path.join(archive, "outcomes", "nba")) else []
    outc = [r for r in outc if r["game_id"] in gids]
    tout = [r for r in store.read(archive, "team_outcomes", days) if r["game_id"] in gids]
    pset = [r for r in store.read(archive, "settlements", days)]
    dec_game = {r["decision_id"]: r["game_id"] for r in dec}
    pset = [r for r in pset if r["decision_id"] in dec_game]

    fam_by_game: dict[str, set] = defaultdict(set)
    gen_by_game: dict[str, list] = defaultdict(list)
    if len(f):
        for gid, fam, role, gen in zip(f["game_id"], f["family"], f["model_role"], f["generated_utc"]):
            if role == "challenger":
                fam_by_game[gid].add(fam)
                gen_by_game[gid].append(gen)
    obs_by_game = Counter(o.get("event_id") for o in obs)
    gf_by_game = Counter(r["game_id"] for r in gf)
    snap_h: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for r in snaps:
        snap_h[r["game_id"]][r["horizon"]].append(r)
    dec_by = Counter((r["game_id"], r["strategy_id"], r["decision"]) for r in dec)
    out_g = Counter(r["game_id"] for r in outc)
    tout_g = Counter(r["game_id"] for r in tout)
    ps_g = Counter(dec_game[r["decision_id"]] for r in pset)

    rows, missing_counter = [], Counter()
    for g in games:
        gid = g["game_id"]
        tip = g["start_time_utc"]
        started = parse_ts(tip) < now
        sh = snap_h.get(gid, {})
        have = {
            "forecast": bool(fam_by_game.get(gid)),
            "participation_forecast": "participation" in fam_by_game.get(gid, set()),
            "availability_obs": obs_by_game.get(gid, 0) > 0,
            "game_forecast": gf_by_game.get(gid, 0) > 0,
            "snapshot_T-60": any(x.get("quote_class") != "MISSING" for x in sh.get("T-60", [])),
            "decisions": any(k[0] == gid for k in dec_by),
            "outcome": out_g.get(gid, 0) > 0,
            "team_outcome": tout_g.get(gid, 0) > 0,
            "paper_settlement": ps_g.get(gid, 0) > 0,
        }
        hours_to_tip = (parse_ts(tip) - now).total_seconds() / 3600
        if hours_to_tip > 36:
            need = []                                    # not due yet: evidence for games further ahead than the projection window is not missing
        elif parse_ts(tip) < now - timedelta(hours=8):
            need = list(REQUIRED)
        else:
            need = [k for k in REQUIRED if k in ("forecast", "participation_forecast", "availability_obs")]
        missing = [k for k in need if not have[k]]
        for k in missing:
            missing_counter[k] += 1
        gaps = {h: sorted(int(x.get("snapshot_gap_s") or 0) for x in v if x.get("quote_class") != "MISSING") for h, v in sh.items()}
        miss_snap = Counter(x.get("missing_cause") for v in sh.values() for x in v if x.get("quote_class") == "MISSING")
        rows.append({
            "game_id": gid, "away": g.get("away_tricode"), "home": g.get("home_tricode"), "start_utc": tip, "game_date_et": g["game_date_et"],
            "started": started, **{f"has_{k}": v for k, v in have.items()},
            "n_forecast_families": len(fam_by_game.get(gid, ())), "first_forecast_utc": min(gen_by_game[gid]) if gen_by_game.get(gid) else None,
            "last_forecast_utc": max(gen_by_game[gid]) if gen_by_game.get(gid) else None,
            "n_forecast_versions": len(set(gen_by_game.get(gid, []))), "n_availability_obs": obs_by_game.get(gid, 0),
            "snapshot_horizons": sorted(h for h, v in sh.items() if any(x.get("quote_class") != "MISSING" for x in v)),
            "snapshot_median_gap_s": {h: (v[len(v) // 2] if v else None) for h, v in gaps.items()},
            "missing_snapshot_causes": dict(miss_snap), "n_decisions": sum(c for k, c in dec_by.items() if k[0] == gid),
            "missing": missing, "scheduled_later": hours_to_tip > 36, "complete": not missing and started})
    led = LED.load_all(archive, (date.fromisoformat(start_et) - timedelta(days=3)).isoformat())      # slots serving the first games run the day before
    exp, done = _expected_slots(games, start_et, end_et, now, led)
    return {"schema": "sift.integrity.v1", "window": {"start_et": start_et, "end_et": end_et}, "generated_utc": iso(now),
            "n_games": len(games), "n_started": sum(1 for r in rows if r["started"]), "n_complete": sum(1 for r in rows if r["complete"]),
            "missing_counts": dict(missing_counter), "games": rows,
            "slots": {"expected": exp, "executed": done, "missed": [s for s in exp if s not in done]},
            "ledger_warnings": [w for r in led for w in r.get("warnings", [])],
            "replay_records_excluded": (not replay_allowed)}


def _expected_slots(games, start_et, end_et, now, ledger) -> tuple[list[str], list[str]]:
    """Pregame slots whose 30 h forward window contains a game of the window (and that are > 3 h old), and which the ledger covers
    (the slot itself, or any later pregame run: a later run supersedes an earlier slot)."""
    tips = [parse_ts(g["start_time_utc"]) for g in games]
    if not tips:
        return [], []
    lo, hi = min(tips) - timedelta(hours=30), max(tips)
    slots = {sid: inst for inst, sid in SP.slot_instants("pregame", min(tips), days_back=4) + SP.slot_instants("pregame", max(tips), days_back=1)}
    exp = sorted((sid for sid, inst in slots.items() if lo <= inst <= hi and inst < now - timedelta(hours=3)
                  and any(inst < t <= inst + timedelta(hours=30) for t in tips)), key=lambda x: slots[x])
    pre = [r for r in ledger if r.get("kind") == "pregame"]
    ids = {r.get("slot_id") for r in pre}
    fin = [parse_ts(r["finished_utc"]) for r in pre if r.get("finished_utc")]
    covered = [sid for sid in exp if sid in ids or any(t >= slots[sid] for t in fin)]
    return exp, covered


def markdown(rep: dict) -> str:
    L = [f"### Data integrity ({rep['window']['start_et']} .. {rep['window']['end_et']} ET)", "",
         f"- games scheduled: **{rep['n_games']}** ({sum(1 for g in rep['games'] if g.get('scheduled_later'))} beyond the 36 h projection window, not yet due), "
         f"started: {rep['n_started']}, fully complete evidence: **{rep['n_complete']}**",
         f"- missing evidence counts: {rep['missing_counts'] or 'none'}",
         f"- pregame slots expected {len(rep['slots']['expected'])}, executed/covered {len(rep['slots']['executed'])}, missed: "
         f"{rep['slots']['missed'] or 'none'}"]
    if rep.get("ledger_warnings"):
        L.append(f"- run warnings: {sorted(set(rep['ledger_warnings']))[:6]}")
    L += ["", "| game | tip (UTC) | forecasts | obs | game fc | snapshots | decisions | outcome | missing |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rep["games"]:
        if r.get("scheduled_later"):
            continue                                     # games beyond the projection window are counted, not listed as gaps
        L.append(f"| {r['away']}@{r['home']} | {r['start_utc'][5:16]} | {r['n_forecast_families']} fam / {r['n_forecast_versions']} v | "
                 f"{r['n_availability_obs']} | {'y' if r['has_game_forecast'] else 'n'} | {','.join(r['snapshot_horizons']) or '-'} | "
                 f"{r['n_decisions']} | {'y' if r['has_outcome'] else 'n'} | {', '.join(r['missing']) or '-'} |")
    return "\n".join(L) + "\n"
