"""Archive-latency diagnosis for the Issue #53 executable studies (RESEARCH ONLY; read-only on every archive; descriptive, never an input to a trading rule).

Four clocks decide whether a market snapshot can be used for a decision at instant D (= tip - offset):
  1. OBSERVED  - the capture tick stamp (file name `kalshi_markets*_<stamp>_*`): when the capture worker finished its Kalshi fetch (the quotes are at most this old);
  2. COMMITTED - the git commit time of the commit that ADDED the tick's file to the capture branch (`data-archive`): the independent archive clock;
  3. VISIBLE   - when a sealer can read it: commit time + push/fetch propagation + (for a polling sealer) up to one poll interval; this is not recorded anywhere, so it is
                 bounded here by the commit time (lower bound) and the poll interval (90 s) of the chain;
  4. DECISION  - the checkpoint D at which an order could really be placed.
The strict control (PF_EDGE_STRICT_T60_EXEC_V1) uses the latest tick OBSERVED <= D and requires it to be COMMITTED <= D. Because ticks reach the branch ~3.5 minutes after they are
observed, that rule fails whenever the latest tick is younger than its own lag, whatever the checkpoint minute is. The alternative studied here uses the latest tick COMMITTED <= D
(what a trader running at D could actually have read) and bounds its staleness.

    python -m nba.paper.latency_diag --repo <git repo with origin/data-archive> --out results/issue53_t45 [--since 2026-10-18] [--forecast-archive <projection-data checkout>]
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from . import exec_shadow as X
from . import markets as MK
from . import seal_windows as SW

UTC = timezone.utc
OFFSETS_MIN = (30, 35, 40, 45, 50, 55, 60)
MAX_AGE_S = 900                      # the paper system's CLOSING_MAX_AGE_S / the protocol's max_quote_age_s (pre-existing constant, not tuned here)
LIVE_MAX_LAG_S = 3600                # commits further than this after the stamp are archive rewrites / backfills, not live captures


def q(a: list[float], p: float) -> float | None:
    return None if not a else sorted(a)[int(p * (len(a) - 1))]


def load_ticks(repo: str, ref: str, since: datetime) -> list[dict]:
    idx = X.board_commit_index(repo, ref)
    out = []
    for k, v in idx.items():
        t, c = MK.parse_ts(k), MK.parse_ts(v)
        if t < since:
            continue
        lag = (c - t).total_seconds()
        out.append({"observed": t, "committed": c, "lag_s": lag, "live": 0 < lag < LIVE_MAX_LAG_S})
    return sorted(out, key=lambda r: r["observed"])


def describe(ticks: list[dict], game_hours: tuple[int, int] = (17, 3)) -> dict[str, Any]:
    live = [t for t in ticks if t["live"]]
    lag = [t["lag_s"] for t in live]
    gh = [t for t in live if t["observed"].hour >= game_hours[0] or t["observed"].hour <= game_hours[1]]
    gap = [(gh[i + 1]["observed"] - gh[i]["observed"]).total_seconds() for i in range(len(gh) - 1)]
    gap = [g for g in gap if g < 3600]
    ph = Counter(int(((t["observed"].minute * 60 + t["observed"].second) % 300) // 60) for t in live)
    return {"n_ticks": len(ticks), "n_live": len(live), "n_rewritten_or_backfilled_excluded": len(ticks) - len(live),
            "first_live": MK.iso(live[0]["observed"]) if live else None, "last_live": MK.iso(live[-1]["observed"]) if live else None,
            "observed_to_committed_lag_s": {"min": min(lag), "p10": q(lag, .1), "median": q(lag, .5), "p90": q(lag, .9), "p99": q(lag, .99), "max": max(lag)} if lag else None,
            "game_hours_utc": f"{game_hours[0]:02d}:00-{game_hours[1]:02d}:59",
            "tick_spacing_game_hours_s": {"p10": q(gap, .1), "median": q(gap, .5), "p90": q(gap, .9), "max": max(gap) if gap else None,
                                          "histogram_minutes": dict(sorted(Counter(int(g // 60) for g in gap).items()))},
            "stamp_phase_within_5min_grid_minutes": dict(sorted(ph.items())),
            "reading": "ticks are observed every 5-15 minutes (irregular, uniform phase) and reach the capture branch a median ~3.5 minutes later; the checkpoint minute therefore has no systematic "
                       "relation to the tick grid, and a larger or smaller offset cannot change the strict rule's coverage"}


def strict_ok(ticks: list[dict], d: datetime) -> dict[str, Any]:
    """Control rule: latest tick observed <= d (within the gap) must be committed <= d. No fallback."""
    cand = [t for t in ticks if t["observed"] <= d and (d - t["observed"]).total_seconds() <= 1800]
    if not cand:
        return {"ok": False, "reason": "NO_BOARD_WITHIN_GAP"}
    t = cand[-1]
    if t["committed"] > d:
        return {"ok": False, "reason": "BOARD_COMMITTED_AFTER_CHECKPOINT", "late_by_s": (t["committed"] - d).total_seconds(), "age_s": (d - t["observed"]).total_seconds()}
    return {"ok": True, "age_s": (d - t["observed"]).total_seconds()}


def available_ok(ticks: list[dict], d: datetime, max_age_s: int = MAX_AGE_S) -> dict[str, Any]:
    """Availability rule: latest tick COMMITTED <= d; its age (d - observed) must not exceed max_age_s. No grace window, nothing committed after d is ever used."""
    cand = [t for t in ticks if t["committed"] <= d and t["observed"] <= d]
    if not cand:
        return {"ok": False, "reason": "NO_COMMITTED_BOARD"}
    t = max(cand, key=lambda r: r["observed"])
    age = (d - t["observed"]).total_seconds()
    if age > max_age_s:
        return {"ok": False, "reason": "STALE_BOARD", "age_s": age}
    return {"ok": True, "age_s": age}


def coverage_by_instant(ticks: list[dict], days: list[datetime], hours=range(17, 28), step_min: int = 5) -> dict[str, Any]:
    """Rule success over every checkpoint instant of the game hours (descriptive: not tied to the real schedule)."""
    live = [t for t in ticks if t["live"]]
    res: dict[str, Any] = {}
    for rule, fn in (("strict_observed_and_committed", strict_ok), ("available_latest_committed", available_ok)):
        ok, n, ages = 0, 0, []
        for day in days:
            for h in hours:
                for m in range(0, 60, step_min):
                    d = day.replace(hour=0, minute=0, second=0) + timedelta(hours=h, minutes=m)
                    if not any(t["observed"] <= d for t in live) or d > live[-1]["observed"]:
                        continue
                    r = fn(live, d)
                    n += 1
                    ok += 1 if r["ok"] else 0
                    if r["ok"]:
                        ages.append(r["age_s"])
        res[rule] = {"n_instants": n, "share_ok": round(ok / n, 3) if n else None, "age_s_median": q(ages, .5), "age_s_p90": q(ages, .9)}
    return res


def coverage_by_game(ticks: list[dict], games: list[dict], forecast_commit: dict[str, str] | None = None, fc_by_game: dict[str, list[str]] | None = None) -> dict[str, Any]:
    live = [t for t in ticks if t["live"]]
    out: dict[str, Any] = {}
    for off in OFFSETS_MIN:
        rows = []
        for g in games:
            tip = MK.parse_ts(g["start_utc"])
            d = tip - timedelta(minutes=off)
            if not live or d < live[0]["observed"] or d > live[-1]["observed"]:
                continue
            s, a = strict_ok(live, d), available_ok(live, d)
            row = {"game_id": g["game_id"], "tip_utc": g["start_utc"], "strict": s, "available": a}
            if forecast_commit is not None and fc_by_game is not None:
                ids = fc_by_game.get(g["game_id"]) or []
                row["forecast_committed_by_decision"] = any(forecast_commit.get(i) and MK.parse_ts(forecast_commit[i]) <= d for i in ids)
            rows.append(row)
        n = len(rows)
        out[f"T-{off}"] = {"n_games": n, "strict_ok": sum(1 for r in rows if r["strict"]["ok"]), "available_ok": sum(1 for r in rows if r["available"]["ok"]),
                           "strict_reasons": dict(Counter(r["strict"].get("reason", "OK") for r in rows)),
                           "available_reasons": dict(Counter(r["available"].get("reason", "OK") for r in rows)),
                           "available_age_s_median": q([r["available"]["age_s"] for r in rows if r["available"]["ok"]], .5),
                           "forecast_committed_by_decision": (sum(1 for r in rows if r.get("forecast_committed_by_decision")) if forecast_commit is not None else None),
                           "games": rows if off in (45, 60) else None}
    return out


def markdown(rep: dict) -> str:
    L = ["# Archive-latency diagnosis (Issue #53; research only, descriptive)", "", rep["clocks_note"], ""]
    d = rep["ticks"]
    lg = d["observed_to_committed_lag_s"]
    L += [f"* live capture ticks analysed: {d['n_live']} ({d['first_live']} .. {d['last_live']}); {d['n_rewritten_or_backfilled_excluded']} rewritten / backfilled commits excluded",
          f"* observed -> committed lag (s): min {lg['min']:.0f}, p10 {lg['p10']:.0f}, median {lg['median']:.0f}, p90 {lg['p90']:.0f}, max {lg['max']:.0f}",
          f"* tick spacing in game hours (s): p10 {d['tick_spacing_game_hours_s']['p10']:.0f}, median {d['tick_spacing_game_hours_s']['median']:.0f}, p90 {d['tick_spacing_game_hours_s']['p90']:.0f}", ""]
    L += ["## Coverage of a usable board by rule (all game-hour instants, descriptive)", "", "| rule | instants | share ok | median board age (s) | p90 age (s) |", "|---|---|---|---|---|"]
    for k, v in rep["coverage_by_instant"].items():
        L.append(f"| {k} | {v['n_instants']} | {v['share_ok']} | {v['age_s_median']} | {v['age_s_p90']} |")
    L += ["", "## Coverage by real game and checkpoint offset (regular-season games with live ticks)", "", "| offset | games | strict (control rule) ok | available-board rule ok | fcst committed by D | median age of available board (s) |", "|---|---|---|---|---|---|"]
    for k, v in rep["coverage_by_game"].items():
        L.append(f"| {k} | {v['n_games']} | {v['strict_ok']} | {v['available_ok']} | {v['forecast_committed_by_decision']} | {v['available_age_s_median']} |")
    L += ["", rep["reading"]]
    return "\n".join(L) + "\n"


def run(repo: str, out: str, since: str, ref: str, context: str, forecast_archive: str | None, forecast_ref: str, season_types=("regular",)) -> dict[str, Any]:
    ticks = load_ticks(repo, ref, MK.parse_ts(since))
    desc = describe(ticks)
    live = [t for t in ticks if t["live"]]
    games = [g for g in SW.schedule_games(context, None, season_types=season_types, all_history=True) if live and live[0]["observed"] <= MK.parse_ts(g["start_utc"]) <= live[-1]["observed"]]
    days = sorted({t["observed"].replace(hour=0, minute=0, second=0, microsecond=0) for t in live})
    fc_commit, fc_by_game = None, None
    if forecast_archive:
        fc_commit = X.forecast_commit_index(forecast_archive, repo, forecast_ref)
        fc_by_game = defaultdict(list)
        import glob
        import gzip
        for sub, field in (("forecasts/nba", "forecast_id"),):
            for p in glob.glob(os.path.join(forecast_archive, sub, "*", "*.jsonl.gz")):
                with gzip.open(p, "rt") as f:
                    for line in f:
                        if line.strip():
                            r = json.loads(line)
                            if r.get("game_id") and r.get(field):
                                fc_by_game[r["game_id"]].append(r[field])
    rep = {"schema": "issue53.latency_diag.v1", "authority": "research_only", "since": since, "clocks_note": __doc__.split("\n\n")[1].strip(),
           "ticks": desc, "coverage_by_instant": coverage_by_instant(ticks, days), "coverage_by_game": coverage_by_game(ticks, games, fc_commit, fc_by_game),
           "max_age_s": MAX_AGE_S, "reading": "Under the strict rule the usable share is set by tick spacing and lag, not by the checkpoint minute (the T-60 and T-45 rows are alike); "
                                              "reading the latest tick COMMITTED by the decision instant removes the commit-latency exclusion at the price of an older quote (the age column), "
                                              "which the executable-price check and the 900 s age guard bound."}
    os.makedirs(out, exist_ok=True)
    json.dump(rep, open(os.path.join(out, "latency_diagnosis.json"), "w"), indent=1, sort_keys=True, default=str)
    open(os.path.join(out, "latency_diagnosis.md"), "w").write(markdown(rep))
    return rep


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--since", default="2026-10-18")
    ap.add_argument("--ref", default="origin/data-archive")
    ap.add_argument("--context", required=True, help="data-archive checkout with context/schedule")
    ap.add_argument("--forecast-archive", default=None)
    ap.add_argument("--forecast-ref", default="origin/projection-data")
    a = ap.parse_args(argv)
    rep = run(a.repo, a.out, a.since, a.ref, a.context, a.forecast_archive, a.forecast_ref)
    print(markdown(rep))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
