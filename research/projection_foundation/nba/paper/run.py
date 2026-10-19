"""Stage functions of the paper system (all idempotent, offline, PAPER ONLY).

    python -m nba.paper.run --stage paper|paper_replay|paper_settle --archive <projection-data> --market-archive <data-archive> [--now ISO]

  game_forecasts   `challenger_game_records(res)` / `stage_game_forecasts(res, archive, now)`: the team-points pmfs of the projection run
                   (res["game_forecasts"], emitted by nba.project.project_slate) -> `game_forecasts/nba/...`, only for games not yet started
  paper            contemporaneous decisions as of `now` on the newest captured board (horizon LIVE) for games starting inside the window
  paper_replay     for every game whose horizons (T-90 / T-60 / T-30 / T-10 / LAST_VALID / OPEN) have passed and are not archived yet: rebuild the
                   board as of that horizon from the immutable capture archive, the forecasts as of that board, and decide (decision_mode
                   `asof_replay`); a horizon no valid board can serve is archived as a MISSING snapshot with its cause
  paper_settle     `settle.settle_paper`

Idempotence: every written row has a deterministic id (snapshot_id, decision_id, decision_id of the settlement, correction_id) and
`store.write_new` skips ids already archived; re-running adds nothing.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from pf_core import prospective as pr

from . import config as CFG
from . import engine as EN
from . import markets as MK
from . import probability as PR
from . import schema as S
from . import settle as ST
from . import store

OPEN_LOOKBACK_H = 72


# ------------------------------------------------------------------------------------------------------------------ game forecasts
def challenger_game_records(res: dict, now: datetime | None = None) -> list[dict[str, Any]]:
    """`res["game_forecasts"]` (nba.project.project_slate) -> archive records (id + model fields), only for games that have not started."""
    gen = MK.parse_ts(res["generated_utc"])
    out = []
    for g in res.get("game_forecasts") or []:
        if MK.parse_ts(g["game_start_utc"]) <= (now or gen):
            continue
        r = dict(g)
        r["schema"] = S.GAME_FORECAST_SCHEMA
        r["game_forecast_id"] = S.sha(["gf", g["game_id"], g["generated_utc"], g.get("model_version")])
        out.append(r)
    return out


def stage_game_forecasts(res: dict, archive: str, now: datetime) -> dict[str, Any]:
    recs = challenger_game_records(res, now)
    by_day: dict[str, list[dict]] = defaultdict(list)
    for r in recs:
        r["archived_utc"] = MK.iso(now)
        by_day[MK.parse_ts(r["game_start_utc"]).strftime("%Y-%m-%d")].append(r)
    st = {"games": len(recs), "written": 0, "duplicates": 0}
    for day, rows in sorted(by_day.items()):
        w = store.write_new(archive, "game_forecasts", day, rows, "game_forecast_id", now)
        st["written"] += w["written"]
        st["duplicates"] += w["duplicates"]
    return st


# ------------------------------------------------------------------------------------------------------------------ inputs
def _day_range(now: datetime, back: int, fwd: int) -> list[str]:
    d0 = now.date()
    return [(d0 + timedelta(days=k)).isoformat() for k in range(-back, fwd + 1)]


def load_inputs(archive: str, now: datetime, back_days: int = 4, fwd_days: int = 3) -> tuple[list[dict], list[dict]]:
    days = _day_range(now, back_days, fwd_days)
    fc = pr._read(archive, "forecasts", "NBA", days)
    gf = store.read(archive, "game_forecasts", [d for d in days if d in set(store.days(archive, "game_forecasts"))])
    return fc, gf


def discover_games(fc_records: list[dict], gf_records: list[dict]) -> dict[str, MK.Game]:
    """Games the forecast archive knows (start time from the forecasts; home/away from game forecasts when present)."""
    start: dict[str, str] = {}
    teams: dict[str, set[str]] = defaultdict(set)
    for r in fc_records:
        if r.get("model_role") != "challenger":
            continue
        start[r["game_id"]] = r["game_start_utc"]
        if r.get("team"):
            teams[r["game_id"]].add(MK.canon_tri(r["team"]) or r["team"])
    ha = {g["game_id"]: (g["home"], g["away"]) for g in gf_records}
    out = {}
    for gid, st in start.items():
        if gid in ha:
            home, away = ha[gid]
        else:
            ts = sorted(teams.get(gid, []))
            if len(ts) != 2:
                continue
            home, away = ts[1], ts[0]           # unordered fallback: the index matches on the pair
        out[gid] = MK.Game.from_dict({"game_id": gid, "start_utc": st, "home": home, "away": away})
    return out


def _fill_player_ids(rows: list[dict], players: MK.PlayerIndex) -> None:
    for r in rows:
        if r.get("scope") == "player":
            r["player_id"], _ = players.resolve(r.get("team"), r.get("player_name"))


def _write_snapshots(archive: str, rows: list[dict], now: datetime) -> dict[str, int]:
    by_day: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_day[MK.parse_ts(r["game_start_utc"]).strftime("%Y-%m-%d")].append(r)
    st = {"written": 0, "duplicates": 0}
    for day, rs in sorted(by_day.items()):
        w = store.write_new(archive, "market_snapshots", day, rs, "snapshot_id", now)
        st["written"] += w["written"]
        st["duplicates"] += w["duplicates"]
    return st


def _write_decisions(archive: str, rows: list[dict], now: datetime) -> dict[str, int]:
    for r in rows:
        bad = EN.validate_row(r)
        if bad:
            raise ValueError(f"invalid decision row {r.get('decision_id')}: {bad}")
    by_day: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_day[MK.parse_ts(r["game_start_utc"]).strftime("%Y-%m-%d")].append(r)
    st = {"written": 0, "duplicates": 0}
    for day, rs in sorted(by_day.items()):
        w = store.write_new(archive, "decisions", day, rs, "decision_id", now)
        st["written"] += w["written"]
        st["duplicates"] += w["duplicates"]
    return st


def _book_at(ob: MK.ChainReader | None, cache: dict, dt: datetime) -> dict[str, dict] | None:
    if ob is None:
        return None
    if dt not in cache:
        got = None
        try:
            for d, b in ob.walk(dt, dt):
                if d == dt and b is not None:
                    got = {k: dict(v) for k, v in b.items()}
        except Exception:                       # noqa: BLE001  depth is optional evidence; never fail a decision on it
            got = None
        cache[dt] = got
    return cache[dt]


# ------------------------------------------------------------------------------------------------------------------ paper (contemporaneous)
def stage_paper(archive: str, market_archive: str, now: datetime, window_hours: float = 30.0, *, replay: bool = False,
                cfg: dict | None = None) -> dict[str, Any]:
    cfg = cfg or CFG.load()
    fc_rec, gf_rec = load_inputs(archive, now)
    games = {g: x for g, x in discover_games(fc_rec, gf_rec).items() if now < x.tip <= now + timedelta(hours=window_hours)}
    st: dict[str, Any] = {"mode": "contemporaneous", "games": len(games), "game_ids": sorted(games)}
    if not games:
        st["status"] = "NO_GAMES_WITH_FORECASTS"
        return st
    reader = MK.ChainReader(market_archive, "markets")
    got = reader.board_at(now)
    if got is None or got[1] is None:
        st["status"] = "NO_BOARD" if got is None else "CHAIN_BROKEN"
        return st
    board_dt, board = got
    st["board_observed_utc"] = MK.iso(board_dt)
    st["board_age_s"] = (now - board_dt).total_seconds()
    gi = MK.GameIndex(games.values())
    players = MK.PlayerIndex(fc_rec)
    fc, gfc = PR.Forecasts(fc_rec, now), PR.GameForecasts(gf_rec, now)
    ob = MK.ChainReader(market_archive, "orderbooks")
    book = _book_at(ob, {}, board_dt)
    snaps: list[dict] = []
    cov: Counter = Counter()
    for g in games.values():
        rows, c = MK.snapshot_rows(board, gi, g, "LIVE", now, board_dt, book=book, replay=replay)
        _fill_player_ids(rows, players)
        snaps += rows
        cov.update(c)
    res = EN.decide(snaps, fc, gfc, players, as_of=now, decided=now, mode="contemporaneous", replay=replay, cfg=cfg)
    st["snapshots"] = _write_snapshots(archive, snaps, now)
    st["decisions"] = _write_decisions(archive, res["decisions"], now)
    st["counts"] = res["counts"]
    st["coverage"] = dict(cov)
    st["forecasts_ignored_late"] = fc.ignored_late
    st["status"] = "ok"
    return st


# ------------------------------------------------------------------------------------------------------------------ paper (as-of replay)
def stage_paper_replay(archive: str, market_archive: str, now: datetime, *, lookback_days: int = 4, cfg: dict | None = None) -> dict[str, Any]:
    cfg = cfg or CFG.load()
    fc_rec, gf_rec = load_inputs(archive, now, back_days=lookback_days, fwd_days=2)
    games = discover_games(fc_rec, gf_rec)
    due = {g: x for g, x in games.items() if x.tip - timedelta(minutes=90) <= now and x.tip >= now - timedelta(days=lookback_days)}
    st: dict[str, Any] = {"mode": "asof_replay", "games_due": len(due), "horizons_archived": Counter(), "missing": Counter(),
                          "decisions": {"written": 0, "duplicates": 0}, "snapshots": {"written": 0, "duplicates": 0}, "pass_reasons": Counter()}
    if not due:
        st["status"] = "NOTHING_DUE"
        _fin(st)
        return st
    reader = MK.ChainReader(market_archive, "markets")
    ticks = reader.ticks()
    have: set[tuple[str, str]] = set()
    snap_days = sorted({x.tip.strftime("%Y-%m-%d") for x in due.values()})
    for r in store.read(archive, "market_snapshots", snap_days):
        have.add((r["game_id"], r["horizon"]))
    gi = MK.GameIndex(due.values())
    players = MK.PlayerIndex(fc_rec)
    ob = MK.ChainReader(market_archive, "orderbooks")
    ob_cache: dict = {}
    plan: dict[tuple[str, str], dict] = {}
    missing_rows: list[dict] = []
    for gid, g in due.items():
        ch = MK.choose_ticks(ticks, g.tip, now)
        for h, c in ch.items():
            if (gid, h) in have:
                continue
            if c["board_dt"] is None:
                missing_rows.append(MK.missing_row(g, h, c["target"], c["cause"], c["gap_s"]))
                st["missing"][c["cause"]] += 1
            else:
                plan[(gid, h)] = c
        if (gid, "OPEN") not in have:
            plan[(gid, "OPEN")] = {"board_dt": None, "target": None, "gap_s": None, "cause": None, "open": True}
    # one pass over the capture chain: pick up the boards we need (and discover OPEN)
    need: dict[datetime, list[tuple[str, str]]] = defaultdict(list)
    for (gid, h), c in plan.items():
        if c["board_dt"] is not None:
            need[c["board_dt"]].append((gid, h))
    open_needed = {gid for (gid, h) in plan if h == "OPEN"}
    extracted: dict[tuple[str, str], tuple[datetime, list[dict], Counter]] = {}
    if need or open_needed:
        lo = min(list(need) + [due[g].tip - timedelta(hours=OPEN_LOOKBACK_H) for g in open_needed])
        hi = max(list(need) + [min(now, due[g].tip) - timedelta(seconds=1) for g in open_needed])
        for dt, board in reader.walk(lo, hi):
            if board is None:
                for (gid, h) in need.get(dt, []):
                    missing_rows.append(MK.missing_row(due[gid], h, plan[(gid, h)]["target"], "CHAIN_BROKEN", plan[(gid, h)]["gap_s"]))
                    st["missing"]["CHAIN_BROKEN"] += 1
                continue
            for (gid, h) in need.get(dt, []):
                g = due[gid]
                rows, cov = MK.snapshot_rows(board, gi, g, h, plan[(gid, h)]["target"], dt, book=_book_at(ob, ob_cache, dt))
                extracted[(gid, h)] = (dt, rows, cov)
            for gid in list(open_needed):
                g = due[gid]
                if dt >= g.tip:
                    continue
                rows, cov = MK.snapshot_rows(board, gi, g, "OPEN", dt, dt, book=_book_at(ob, ob_cache, dt))
                if any(r["quote_class"] == "TWO_SIDED" and r["support"] == "MODELED" for r in rows):
                    extracted[(gid, "OPEN")] = (dt, rows, cov)
                    open_needed.discard(gid)
    for gid in open_needed:
        st["missing"]["OPEN_NOT_LISTED_YET"] += 1               # not archived: it will be found on a later run
    # decisions per horizon group (day / game caps look across games of the same horizon)
    by_h: dict[str, list[dict]] = defaultdict(list)
    snaps_all: list[dict] = list(missing_rows)
    for (gid, h), (dt, rows, cov) in sorted(extracted.items()):
        g = due[gid]
        _fill_player_ids(rows, players)
        snaps_all += rows
        fc, gfc = PR.Forecasts(fc_rec, dt), PR.GameForecasts(gf_rec, dt)
        by_h[h] += EN.candidates_for(rows, fc, gfc, players, as_of=dt, decided=now, mode="asof_replay", cfg=cfg)
        st["horizons_archived"][h] += 1
    all_dec: list[dict] = []
    for h, cands in by_h.items():
        strat = EN.apply_strategies(cands, cfg)
        all_dec += cands + strat
        for r in cands + strat:
            if r["decision"] == "PASS":
                st["pass_reasons"][f"{r['strategy_id']}|{r['reason']}"] += 1
        st[f"trades:{h}"] = sum(1 for r in strat if r["decision"] == "TRADE")
    ws = _write_snapshots(archive, snaps_all, now)
    wd = _write_decisions(archive, all_dec, now)
    st["snapshots"], st["decisions"] = ws, wd
    st["status"] = "ok"
    _fin(st)
    return st


def _fin(st: dict) -> None:
    for k, v in list(st.items()):
        if isinstance(v, Counter):
            st[k] = dict(v)


# ------------------------------------------------------------------------------------------------------------------ settle
def stage_paper_settle(archive: str, market_archive: str | None, now: datetime, cfg: dict | None = None) -> dict[str, Any]:
    return ST.settle_paper(archive, market_archive, now, cfg=cfg)


# ------------------------------------------------------------------------------------------------------------------ CLI
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", required=True, choices=["paper", "paper_replay", "paper_settle"])
    ap.add_argument("--archive", required=True, help="projection-data checkout")
    ap.add_argument("--market-archive", required=True, help="data-archive checkout (kalshi/markets*, kalshi/orderbooks*)")
    ap.add_argument("--now", default=None)
    ap.add_argument("--window-hours", type=float, default=30.0)
    a = ap.parse_args(argv)
    now = MK.parse_ts(a.now) if a.now else datetime.now(timezone.utc).replace(microsecond=0)
    if a.stage == "paper":
        st = stage_paper(a.archive, a.market_archive, now, a.window_hours)
    elif a.stage == "paper_replay":
        st = stage_paper_replay(a.archive, a.market_archive, now)
    else:
        st = stage_paper_settle(a.archive, a.market_archive, now)
    print(json.dumps(st, indent=1, default=str, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
