"""Prospective NBA PURE shadow collector: slate -> projections, outcomes, market listings.

Order inside one capture is deliberate: projections are built and written FIRST from sports data
only; the market listing snapshot is read and written afterwards, by a separate function, into a
separate file family. Nothing in ``projections.py`` can see it.

Capture slots (one capture per game per slot; a missed slot is recorded as missed, never back-filled):

    morning   game day (ET), at least 4 h before the scheduled tip
    pretip    30-90 min before the scheduled tip ("T-60m", after the 5:00/30-min injury report). The
              champion has no point-in-time injury input yet (participation proxy), so a pretip capture
              differs from the morning one only if new box scores arrived; both are kept as captured.

Invariants enforced here (a violation raises; nothing is written):
  * live capture only strictly before the scheduled tip (``as_of < kickoff`` and wall clock < kickoff);
  * every input observed strictly before ``as_of`` (schedule fetch, committed history, shadow box rows);
  * the champion digest equals the frozen V1 digest and the baseline dispersion re-fits to its frozen values;
  * every projection file passes the vendored pure_gate ``validate --require-v1`` before it is written.

REPLAY mode (dry runs only): ``as_of`` is a past instant, inputs are cut to rows observed before it,
the schedule identity is fetched now (labelled), and the store must be a throwaway dry-run store.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import subprocess
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from nba_edge.data.history import (
    build_game_rows,
    load_player_games,
    load_team_games,
    scoreboard_events,
    scoreboard_url,
    summary_url,
)
from nba_edge.data.schedule import parse_espn_scoreboard
from nba_edge.shadow import projections as pj
from nba_edge.shadow.store import ShadowStore
from nba_edge.timeutil import ET, iso, parse_iso, utcnow

REPO = Path(__file__).resolve().parents[3]
GATE_PATH = REPO / "tools" / "pure_gate" / "pure_gate.py"
SLOTS = ("morning", "pretip")
MORNING_MIN_LEAD_MIN = 240.0
PRETIP_WINDOW_MIN = (30.0, 90.0)
LIVE_SEASON_TYPES = ("regular", "playin", "playoffs")
PROP_SERIES = {"KXNBAPTS": "points", "KXNBAREB": "rebounds", "KXNBAAST": "assists", "KXNBA3PT": "threes"}
GATE_STATS = {"minutes": "minutes", "points": "pts", "rebounds": "reb", "assists": "ast", "threes": "fg3m"}

Fetcher = Callable[[str], tuple[dict[str, Any], str]]  # url -> (payload, fetched_at ISO UTC)


def http_fetcher(url: str) -> tuple[dict[str, Any], str]:
    from nba_edge.data.http import PLAIN_HEADERS_OK, fetch

    f = fetch(url, headers=PLAIN_HEADERS_OK, ttl_s=None)
    return f.json(), f.fetched_at_utc


def load_gate():
    """The vendored shared gate (tools/pure_gate, pinned in VENDORED_FROM), imported from its file."""
    spec = importlib.util.spec_from_file_location("pure_gate_vendored", GATE_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def code_commit() -> str:
    try:
        return subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True, check=False).stdout.strip() or "unknown"
    except OSError:
        return "unknown"


def _ceil_second(t: datetime) -> datetime:
    return (t + timedelta(seconds=1)).replace(microsecond=0)


def _sha_files(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for p in sorted(paths):
        h.update(p.name.encode())
        h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


# --------------------------------------------------------------------------------------------------
# schedule
# --------------------------------------------------------------------------------------------------


def slate(dates: list[str], fetcher: Fetcher) -> tuple[list[tuple[pj.GameRef, str]], list[dict[str, Any]]]:
    """(GameRef, status) for every NBA game on the given ET dates, plus fetch provenance."""
    out, prov = [], []
    for d in dates:
        url = scoreboard_url(datetime.fromisoformat(d).date())
        payload, fetched_at = fetcher(url)
        games = parse_espn_scoreboard(payload)
        prov.append({"source": "espn_scoreboard", "date_et": d, "url": url, "fetched_at": fetched_at, "n_games": len(games)})
        for g in games:
            if g.game_date_et != d:
                continue
            ref = pj.GameRef(game_id=g.game_id, game_date_et=g.game_date_et, kickoff=iso(g.start_time_utc), home_team_id=g.home_team_id,
                             away_team_id=g.away_team_id, season_type=g.season_type.value, home_tricode=g.home_tricode, away_tricode=g.away_tricode)
            out.append((ref, g.status.value))
    return out, prov


def due_slot(g: pj.GameRef, now: datetime, slot: str) -> bool:
    lead = (parse_iso(g.kickoff) - now).total_seconds() / 60.0
    if slot == "morning":
        return lead >= MORNING_MIN_LEAD_MIN and g.game_date_et == now.astimezone(ET).date().isoformat()
    lo, hi = PRETIP_WINDOW_MIN
    return lo <= lead <= hi


def captured_keys(store: ShadowStore) -> set[tuple[str, str]]:
    """(game_id, slot) pairs already captured (any mode recorded in this store)."""
    out = set()
    for _e, r in store.iter_rows("captures"):
        for g in r.get("games", []):
            out.add((g["game_id"], r["slot"]))
    return out


# --------------------------------------------------------------------------------------------------
# history (inputs)
# --------------------------------------------------------------------------------------------------


def committed_history(data_root: Path) -> tuple[pd.DataFrame, pd.DataFrame, str, str]:
    """Committed ESPN box history (regular season), with the instant it was obtained."""
    hist = data_root / "history"
    files = sorted((hist / "espn").glob("team_games_*.parquet"))
    seasons = sorted(p.stem.split("_")[-1] for p in files)
    tg = load_team_games(hist, seasons)
    pg = load_player_games(hist, seasons)
    pulled = json.loads((hist / "espn" / "MANIFEST.json").read_text())["pulled_at"]
    tg = tg[tg["season_type"] == "regular"].copy()
    pg = pg[pg["season_type"] == "regular"].copy()
    pg["minutes"] = pd.to_numeric(pg["minutes"], errors="coerce").fillna(0.0)
    tg["observed_at"] = pulled
    pg["observed_at"] = pulled
    snap = _sha_files(sorted((hist / "espn").glob("player_games_*.parquet")) + files)
    return tg, pg, pulled, snap


def shadow_history(store: ShadowStore, as_of: datetime) -> tuple[pd.DataFrame, pd.DataFrame, str | None]:
    """Current-season regular-season box rows this collector fetched strictly before ``as_of``."""
    cut = iso(as_of)
    pr, tr, seen = [], [], {}
    for _e, r in store.iter_rows("outcomes/box"):
        if r.get("fetched_at", "9999") >= cut or r.get("season_type") != "regular":
            continue
        first = seen.setdefault(r["game_id"], r["fetched_at"])
        if r["fetched_at"] != first:
            continue  # first fetched version of a game stands; later refetches are ignored
        (pr if r["row_type"] == "player" else tr).append(r)
    mx = max(seen.values()) if seen else None
    pg = pd.DataFrame(pr)
    tg = pd.DataFrame(tr)
    for df in (pg, tg):
        if len(df):
            df["observed_at"] = df["fetched_at"]
    if len(pg):
        pg["minutes"] = pd.to_numeric(pg["minutes"], errors="coerce").fillna(0.0)
    return tg, pg, mx


def assemble_history(data_root: Path, store: ShadowStore, as_of: datetime) -> tuple[pd.DataFrame, pd.DataFrame, list[pj.Source], dict[str, Any]]:
    tg, pg, pulled, snap = committed_history(data_root)
    stg, spg, smax = shadow_history(store, as_of)
    if len(spg):
        known = set(tg["game_id"])
        stg = stg[~stg["game_id"].isin(known)]
        spg = spg[~spg["game_id"].isin(known)]
        tg = pd.concat([tg, stg[[c for c in stg.columns if c in tg.columns or c == "observed_at"]]], ignore_index=True)
        pg = pd.concat([pg, spg[[c for c in spg.columns if c in pg.columns or c == "observed_at"]]], ignore_index=True)
    hist_max = max(pulled, smax) if smax else pulled
    sources = [
        pj.Source("espn_player_games_history", hist_max, "data/history/espn/player_games_*.parquet + shadow outcomes/box (player rows)",
                  f"regular-season ESPN player box rows; committed backfill obtained {pulled}; current-season rows fetched by this collector "
                  f"before as_of (latest {smax or 'none'})", snap),
        pj.Source("espn_team_games_history", hist_max, "data/history/espn/team_games_*.parquet + shadow outcomes/box (team rows)",
                  "regular-season ESPN team box rows (pace, efficiency, rest), same cut as the player rows"),
    ]
    info = {"committed_obtained_at": pulled, "committed_snapshot_sha256": snap, "shadow_box_games": int(stg["game_id"].nunique()) if len(stg) else 0,
            "shadow_box_max_fetched_at": smax, "n_team_rows": int(len(tg)), "n_player_rows": int(len(pg))}
    return tg, pg, sources, info


# --------------------------------------------------------------------------------------------------
# capture
# --------------------------------------------------------------------------------------------------


def capture(store: ShadowStore, data_root: Path, slot: str, fetcher: Fetcher, dates: list[str] | None = None,
            now: datetime | None = None, replay_as_of: datetime | None = None, dry_run: bool = False,
            include_preseason: bool = False, n_sims: int = pj.N_SIMS, game_ids: list[str] | None = None,
            ignore_slot_window: bool = False) -> dict[str, Any]:
    if slot not in SLOTS:
        raise ValueError(f"slot must be one of {SLOTS}")
    if (replay_as_of is not None or ignore_slot_window) and not dry_run:
        raise RuntimeError("REPLAY captures and slot-window overrides are dry-run only; never written to the shadow store")
    clock = now or utcnow()
    dates = dates or [clock.astimezone(ET).date().isoformat()]
    games, sched_prov = slate(dates, fetcher)
    allowed = LIVE_SEASON_TYPES + (("preseason",) if include_preseason else ())
    done = captured_keys(store)
    mode = "REPLAY_DRY_RUN" if replay_as_of is not None else ("LIVE_DRY_RUN" if dry_run else "LIVE")
    skipped: list[dict[str, Any]] = []
    due: list[pj.GameRef] = []
    for g, status in games:
        why = None
        if game_ids and g.game_id not in game_ids:
            why = "not_selected"
        elif g.season_type not in allowed:
            why = f"season_type_{g.season_type}"
        elif (g.game_id, slot) in done:
            why = "already_captured"
        elif replay_as_of is None and status != "scheduled":
            why = f"status_{status}"
        elif replay_as_of is None and not ignore_slot_window and not due_slot(g, clock, slot):
            why = "outside_slot_window"
        if why:
            skipped.append({"game_id": g.game_id, "reason": why, "kickoff": g.kickoff})
        else:
            due.append(g)
    record: dict[str, Any] = {"record": "capture", "slot": slot, "mode": mode, "dates_et": dates, "schedule": sched_prov,
                              "skipped": skipped, "code_commit": code_commit(), "gate_vendored": GATE_PATH.relative_to(REPO).as_posix()}
    if not due:
        record.update({"as_of": iso(clock), "games": [], "refused": [], "files": {}})
        return record
    if replay_as_of is None:
        as_of = _ceil_second(utcnow())
        for p in sched_prov:
            if p["fetched_at"] >= iso(as_of):
                raise RuntimeError("schedule fetched at/after as_of")
    else:
        as_of = replay_as_of
    tg, pg, sources, hinfo = assemble_history(data_root, store, as_of)
    alpha = pj.assert_frozen(pg)
    res = pj.build_slate_projections(due, as_of, tg, pg, sources, alpha, n_sims=n_sims, now=None if replay_as_of is not None else utcnow())
    gate = load_gate()
    files, digests = {}, {}
    for (arm, cond), rows in res.rows.items():
        for r in rows:
            r["x_slot"], r["x_capture_mode"] = slot, mode
        if not rows:
            continue
        summary = gate.validate_file_summary(rows, require_v1=True)
        e = store.append_rows(f"projections/{arm}/{cond}", rows, observed_at=as_of,
                              meta={"slot": slot, "mode": mode, "arm": arm, "model_version": pj.MODEL_VERSION[arm], "conditional": cond == "conditional",
                                    "gate_validate": {k: summary[k] for k in ("passed", "n", "schema_versions", "warnings", "gate")}})
        files[f"{arm}/{cond}"] = {"path": e.path, "rows": e.rows, "sha256": e.sha256}
    for g in res.games:
        digests[g["game_id"]] = pj.projection_digest([r for rows in res.rows.values() for r in rows if r["game_id"] == g["game_id"]])
    record.update({"as_of": iso(as_of), "games": [dict(g, projection_digest=digests[g["game_id"]]) for g in res.games], "refused": res.refused,
                   "files": files, "inputs": hinfo, "n_sims": n_sims, "arms": {a: pj.MODEL_VERSION[a] for a in pj.ARMS},
                   "frozen_hashes": {a: pj.frozen_hash(a) for a in pj.ARMS}, "participation_source": pj.PARTICIPATION_SOURCE})
    store.append_rows("captures", [record], observed_at=as_of, meta={"slot": slot, "mode": mode, "n_games": len(res.games)})
    return record


# --------------------------------------------------------------------------------------------------
# outcomes (sports truth)
# --------------------------------------------------------------------------------------------------


def outcome_game_ids(store: ShadowStore) -> set[str]:
    return {r["game_id"] for _e, r in store.iter_rows("outcomes/box")}


def collect_outcomes(store: ShadowStore, dates: list[str], fetcher: Fetcher, include_preseason: bool = False,
                     game_ids: list[str] | None = None) -> dict[str, Any]:
    """Final ESPN box scores for completed games on ``dates`` not already stored. Idempotent."""
    allowed = LIVE_SEASON_TYPES + (("preseason",) if include_preseason else ())
    have = outcome_game_ids(store)
    box_rows, gate_rows, prov, errors = [], [], [], []
    for d in dates:
        url = scoreboard_url(datetime.fromisoformat(d).date())
        payload, sb_at = fetcher(url)
        evs = scoreboard_events(payload)
        prov.append({"date_et": d, "url": url, "fetched_at": sb_at, "n_completed": len(evs)})
        for ev in evs:
            if ev["season_type"] not in allowed or ev["game_id"] in have or (game_ids and ev["game_id"] not in game_ids):
                continue
            yr = ev.get("espn_season_year")
            season = f"{int(yr) - 1}-{str(yr)[2:]}" if yr else ""
            surl = summary_url(ev["event_id"])
            try:
                summ, fetched_at = fetcher(surl)
                prow, trow = build_game_rows(summ, {**ev, "season": season})
            except Exception as e:  # noqa: BLE001 - one bad game must not stop the rest
                errors.append({"game_id": ev["game_id"], "error": f"{type(e).__name__}: {e}"[:300]})
                continue
            if not trow:
                errors.append({"game_id": ev["game_id"], "error": "no team rows parsed"})
                continue
            meta = {"fetched_at": fetched_at, "source": "espn_summary", "source_uri": surl}
            box_rows.extend({**r, "row_type": "player", **meta} for r in prow)
            box_rows.extend({**r, "row_type": "team", **meta} for r in trow)
            for r in prow:
                for stat, key in GATE_STATS.items():
                    val = float(r[key]) if r["played"] else 0.0
                    gate_rows.append({"sport": pj.SPORT, "game_id": r["game_id"], "player_id": str(r["nba_id"]), "statistic": stat,
                                      "actual": val, "played": bool(r["played"]), "source": "espn_summary", "observed_at": fetched_at})
            have.add(ev["game_id"])
    out: dict[str, Any] = {"scoreboards": prov, "errors": errors, "n_games": len({r["game_id"] for r in box_rows}), "files": {}}
    if box_rows:
        at = parse_iso(max(r["fetched_at"] for r in box_rows))
        e1 = store.append_rows("outcomes/box", box_rows, observed_at=at, meta={"source": "espn_summary"})
        e2 = store.append_rows("outcomes/gate", gate_rows, observed_at=at, meta={"source": "espn_summary", "format": "pure_gate outcome"})
        out["files"] = {"box": e1.path, "gate": e2.path}
    return out


# --------------------------------------------------------------------------------------------------
# market listings (SEPARATE family, downstream of the projections; never read by a forecast)
# --------------------------------------------------------------------------------------------------


def _at_least(threshold: float | None, comparator: str | None) -> float | None:
    if threshold is None:
        return None
    if comparator == "gt":
        return float(math.floor(threshold) + 1)
    return float(threshold)


def capture_listings(store: ShadowStore, archive_root: Path | None, as_of: datetime, games: list[dict[str, Any]], pg: pd.DataFrame | None,
                     slot: str, mode: str) -> dict[str, Any]:
    """Reads the existing capture archive (data-archive branch, read-only) as of ``as_of`` and stores
    the player-prop listings for the captured games. The pregame-listed cohort is defined from these
    rows only: listed iff the market was on a board observed at or before as_of and opened by then."""
    from nba_edge.archive.reconstruct import reconstruct_at
    from nba_edge.identity.players import PlayerRegistry
    from nba_edge.identity.teams import registry
    from nba_edge.kalshi.contracts import build_contract
    from nba_edge.kalshi.ontology import Ontology
    from nba_edge.kalshi.ticker import parse_ticker
    from nba_edge.workflows.simulate import NameIndex

    status: dict[str, Any] = {"archive_root": str(archive_root) if archive_root else None, "as_of": iso(as_of)}
    if archive_root is None or not (Path(archive_root) / "manifest.jsonl").exists():
        status["status"] = "ARCHIVE_UNAVAILABLE"
        store.append_rows("market/listings_status", [status], observed_at=as_of, meta={"slot": slot, "mode": mode})
        return status
    try:
        board = reconstruct_at(Path(archive_root), as_of)
    except Exception as e:  # noqa: BLE001 - no board at/before as_of is a recorded state, not a crash
        status.update({"status": "NO_BOARD_AT_OR_BEFORE_AS_OF", "error": f"{type(e).__name__}: {e}"[:300]})
        store.append_rows("market/listings_status", [status], observed_at=as_of, meta={"slot": slot, "mode": mode})
        return status
    reg = registry()
    onto = Ontology.load()
    try:
        preg = PlayerRegistry.load()
        uuid_to_id = {r.aliases["kalshi_uuid"]: r.nba_id for r in preg.records.values() if "kalshi_uuid" in r.aliases}
    except Exception:  # noqa: BLE001
        uuid_to_id = {}
    names = NameIndex([], pg if pg is not None else pd.DataFrame())
    by_key = {}
    for g in games:
        h, a = reg.by_id(int(g["home_team_id"])).tricode, reg.by_id(int(g["away_team_id"])).tricode
        by_key[(g["game_date_et"], h, a)] = g
    rows = []
    for m in board.rows:
        series = m.get("series_ticker") or str(m.get("ticker", "")).split("-")[0]
        if series not in PROP_SERIES:
            continue
        pt = parse_ticker(m.get("ticker", ""), reg.tricodes)
        g = by_key.get((pt.game_date.isoformat() if pt.game_date else None, pt.home_tricode, pt.away_tricode))
        if g is None:
            continue
        c = build_contract(m, onto)
        pid, how = None, "none"
        if c.kalshi_entity_uuid and c.kalshi_entity_uuid in uuid_to_id:
            pid, how = uuid_to_id[c.kalshi_entity_uuid], "kalshi_uuid_alias"
        elif c.entity_name:
            for tid in (int(g["home_team_id"]), int(g["away_team_id"])):
                pid = names.resolve_name(c.entity_name, tid)
                if pid is not None:
                    how = "unique_name_on_team"
                    break
        q = m.get("_quote_cents") or {}
        open_time = m.get("open_time")
        rows.append({
            "record": "market_listing", "sport": pj.SPORT, "game_id": g["game_id"], "player_id": str(pid) if pid is not None else None,
            "identity_method": how, "statistic": PROP_SERIES[series], "at_least": _at_least(c.threshold, c.comparator),
            "venue": "kalshi", "ticker": m.get("ticker"), "event_ticker": m.get("event_ticker"), "series": series,
            "open_time": open_time, "created_time": m.get("created_time"), "close_time": m.get("close_time"), "status": m.get("status"),
            "board_observed_at": board.observed_at_utc, "row_observed_at": m.get("_observed_at_utc"), "pure_as_of": iso(as_of), "slot": slot,
            "listed_by_as_of": bool(open_time and open_time <= iso(as_of) and (m.get("_observed_at_utc") or board.observed_at_utc) <= iso(as_of)),
            "yes_bid_cents": q.get("yes_bid"), "yes_ask_cents": q.get("yes_ask"), "last_cents": q.get("last_price"),
            "volume_fp": m.get("volume_fp"), "open_interest_fp": m.get("open_interest_fp"),
        })
    status.update({"status": "OK", "board_observed_at": board.observed_at_utc, "board_source": board.source, "board_markets": board.n_markets,
                   "n_listings": len(rows), "n_unresolved_player": sum(1 for r in rows if r["player_id"] is None)})
    if rows:
        e = store.append_rows("market/listings", rows, observed_at=as_of, meta={"slot": slot, "mode": mode, **{k: status[k] for k in ("board_observed_at", "n_listings")}})
        status["path"] = e.path
    store.append_rows("market/listings_status", [status], observed_at=as_of, meta={"slot": slot, "mode": mode})
    return status


def default_dates(now: datetime, back: int = 3) -> list[str]:
    d0 = now.astimezone(ET).date()
    return [(d0 - timedelta(days=i)).isoformat() for i in range(back, -1, -1)]


def env_run_id() -> str | None:
    return os.environ.get("GITHUB_RUN_ID")


__all__ = ["capture", "collect_outcomes", "capture_listings", "slate", "http_fetcher", "load_gate", "default_dates"]
