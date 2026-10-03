"""Edge Finder research explorer (contract 1.1.0 research graph) for the NBA: ``app/latest/explorer/``.

A PURE ADAPTER beside ``app_export``. It reads only what this repository already commits or captures and
re-expresses it as explorer documents (``contract/edge_finder_contract/research.py``). It changes no model,
price, gate, threshold or authority; every model output stays RESEARCH.

Sources (all read-only)
    v1 payload       ``<app_root>/{manifest,events,markets,model_prices,recommendations,wagers}.json`` (the run id,
                     the clock, the events and markets this explorer must describe)
    team games       ``data/history/espn/team_games_*.parquet`` (3 seasons, ``nba history``)
    player games     ``data/history/espn/player_games_*.parquet``
    shot events      ``data/history/espn/shot_events_<current season>.parquet`` (zone shares only)
    market table     ``data/research/market_table.parquet`` (settled outcomes at five pre-tip horizons)
    candles          ``data/history/kalshi/candles_KXNBAGAME.jsonl.gz`` (hourly moneyline candles)
    exhibit          ``docs/research/market_vs_model.json`` (the frozen model-vs-market walk-forward)
    identity         ``data/identity/{teams.csv,players.jsonl}`` via ``identity.teams`` / ``identity.players``
    archive          the data-archive checkout: board ticks (``archive.reconstruct.iter_board_ticks``),
                     ``context/rosters``, ``context/injuries``, ``predictions``, ``slates/latest/{slate,packet}.json``

What is computed here is arithmetic over stored rows (per-game means, sums of points over stored
possessions, win rates, rolling means, rankings, de-laddered market residuals) plus ONE call into the repo's
own feature code, ``features.build.opponent_adjusted_ratings``, with the frozen ``BuildConfig`` exactly as
``build_game_params`` applies it; that output is published as RESEARCH (audit 2026-10-03 §10.4).

Failure contract: ``export_explorer`` publishes through ``research.publish_explorer`` (staged, validated,
graph-checked, swapped in with ``index.json`` last), so any failure leaves the previous explorer untouched
and never touches the v1 files. The CLI exits 1 on failure.
"""

from __future__ import annotations

import argparse
import gzip
import json
import statistics
import sys
import traceback
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from nba_edge import __version__
from nba_edge.config import REPO_ROOT

CONTRACT_DIR = REPO_ROOT / "contract"
if str(CONTRACT_DIR) not in sys.path:
    sys.path.insert(0, str(CONTRACT_DIR))

from edge_finder_contract import build, ids  # noqa: E402
from edge_finder_contract import research as R  # noqa: E402
from edge_finder_contract import timeutil as c_time  # noqa: E402

SPORT = "NBA"
AUDIT_DATE = "2026-10-03"
METHODOLOGY_VERSION = f"nba_edge.research_export/1.0.0 (nba-edge-finder {__version__})"
DEFAULT_DATA_ROOT = "data/archive"
DEFAULT_OUT = "data/archive/app/latest"
DEFAULT_HISTORY_ROOT = str(REPO_ROOT / "data")
DEFAULT_DOCS_ROOT = str(REPO_ROOT / "docs")

#: Per-entity per-game caps (series points, game lists, game logs).
SERIES_CAP = 82
#: Recent-form windows, in games.
FORM_WINDOWS = (10, 5, 3)
#: Non-preseason season types (the research population; preseason is systems validation only).
FORM_TYPES = ("regular", "playin", "playoffs")
#: Horizon used for market residual metrics; the five horizons the market table stores.
MARKET_HORIZON = "T-30m"
HORIZONS = ("T-24h", "T-6h", "T-90m", "T-30m", "final")
#: Historical moneyline hourly candles are published for each team's last N games of the current season.
CANDLE_GAMES_PER_TEAM = 5
#: Player ranking universe: players with at least this many played regular-season games.
PLAYER_RANK_MIN_GAMES = 20
#: Profile `games` lists: the last N historical games (the full logs are in extensions.game_log).
PLAYER_GAME_REFS = 10
TEAM_GAME_REFS = 20
#: Team game logs (extensions.game_log) carry the most recent N stored seasons.
GAME_LOG_SEASONS = 3

# ------------------------------------------------------------------------------------- audit text
# Verbatim from scratchpad/phase2/audit_nba.md (2026-10-03); the capability manifest quotes these.
A_SCHEDULE = ("Nothing that feeds the research tables runs on a schedule; the ESPN history was last pulled 2026-09-19 "
              "(box scores) and 2026-09-29 (shot events), Kalshi history 2026-09-19.")
A_TEAM_METRICS = "Only persisted per run in `slates/*/packet.json` `home/away` blocks; never as a series"
A_PLAYER_METRICS = "stored only in packet `players[]` per run"
A_FORM = "L3/L5 not stored; trivially derivable from game logs"
A_USAGE = "no possessions-per-player, no usage % column"
A_REGISTRY = ("player registry covers only 175 prop-market players (40.6 % of 2025-26 played rows)")
A_SPLITS = "computed nowhere; derivable"
A_ADJ = ("ratings ignore roster/injury composition (`impact_ppp = 0`, SIMULATION.md L2); `rating_scale` fitted on 2023-25 and "
         "checked once on 2025-26, and is frozen under the baseline.")
A_ADJ_TEST = "No test pins the adjustment's values, iteration count or symmetry"
A_SOS = "no explicit SOS output"
A_CANDLES = "`price.close` is frequently null (no trade in the hour), so bid/ask is the usable series"
A_HISTORY_MKT = "PARTIAL (2025-26 only; props from 2025-11-19; team totals/1H from Feb 2026)"
A_PRICES = "scheduled, tested, 16 days of rows — but pre-season only"
A_LIVE = "PARTIAL (16 days, preseason)"
A_INJURIES = ("official NBA PDF **never captured** (`missing: true` on every snapshot, `slots_tried: 8`); `nba_id` null on all rows")
A_PROJ = ("RESEARCH and gated (`CANNOT_TRUST_INPUTS` until official injury report + regular season), and note the §5.14 quote "
          "defect until fixed.")
A_DEFECT = ("§5.14 defect: `workflows/simulate.py:290` strips the captured `*_dollars`/`_quote_cents` quote fields before "
            "normalisation, so all 73 contracts of the first real slate carry `p_market = null`, `p_production = null`, and the "
            "app export has 0 model prices.")
A_SHOTS = ("Shot profiles by zone ... label RESEARCH (walk-forward showed no market value).")
A_SHOT_IDS = "Shot events key teams by ESPN ids (1–30) while every other table uses NBA ids."
A_PBP = "non-shooting plays not ingested"
A_MATCHUP = "every adjustment is the identity by construction"
A_VERDICT = "market beats model in all 8 families"
A_ACCURACY = "all negative vs market"
A_LINEUPS = ("`EVIDENCE_HEALTH.context.lineups: absent`, `confirmed_starters: absent`; stats.nba/cdn.nba blocked "
             "(`docs/research/MATCHUP_SOURCE_AUDIT.md:54-59`)")


class ResearchExportError(RuntimeError):
    """The inputs cannot be turned into an explorer (nothing is published)."""


# ----------------------------------------------------------------------------------------- inputs
@dataclass
class ResearchInputs:
    """Everything the builder reads, loaded once so ``build_explorer`` is a pure function."""

    manifest: dict[str, Any]
    events: list[dict]
    markets: list[dict]
    model_prices: list[dict]
    recommendations: list[dict]
    wagers: list[dict]
    team_games: list[dict]
    player_games: list[dict]
    history_pulled_at: str | None
    shot_pulled_at: str | None
    kalshi_pulled_at: str | None
    shot_zones: list[dict]  # {game_id, is_home, zone, fga, fgm} for the current season's regular season
    market_rows: list[dict]  # market_table rows: game_winner at every horizon, everything else at MARKET_HORIZON
    candles: dict[str, list[dict]]  # ticker -> hourly candles (moneyline tickers of the selected games)
    adjusted: dict[int, tuple[float, float, float]]  # team_id -> (off_ppp, def_ppp, eff_n), rating_scale applied
    adjusted_meta: dict[str, Any]
    registry_players: list[dict]  # {nba_id, full_name, espn, kalshi_uuid, active}
    teams: list[Any]  # identity.teams.Team
    rosters: list[dict]
    rosters_at: str | None
    injuries: list[dict]
    injuries_at: str | None
    injuries_official_missing: bool | None
    price_paths: dict[str, list[dict]]  # ticker -> price points from the archive's board ticks
    board_ticks: int
    slate: dict | None
    packet: dict | None
    predictions: list[dict]  # every predictions row for tickers on v1 events, all runs
    exhibit: dict | None  # docs/research/market_vs_model.json
    warnings: list[str] = field(default_factory=list)


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _items(app_root: Path, name: str) -> list[dict]:
    doc = _read_json(app_root / f"{name}.json")
    return list(doc.get("items") or []) if isinstance(doc, dict) else []


def _parquet_rows(paths: list[Path], columns: list[str] | None = None) -> list[dict]:
    import pyarrow.parquet as pq

    rows: list[dict] = []
    for p in sorted(paths):
        rows.extend(pq.read_table(p, columns=columns).to_pylist())
    return rows


def _iso_epoch(ts: int | float) -> str:
    return c_time.to_iso(datetime.fromtimestamp(int(ts), tz=UTC))


def _f(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _cents(v: Any) -> float | None:
    return None if v is None else round(float(v) / 100.0, 6)


def _current_season(team_games: list[dict]) -> str | None:
    seasons = sorted({r["season"] for r in team_games if r.get("season_type") == "regular"})
    return seasons[-1] if seasons else None


def _select_candle_games(team_games: list[dict], market_rows: list[dict], season: str | None) -> dict[str, str]:
    """ticker -> game_id for the moneyline tickers of each team's last CANDLE_GAMES_PER_TEAM games."""
    ml = {}
    for r in market_rows:
        if r["family"] == "game_winner" and r.get("team_id") is not None:
            ml.setdefault(r["game_id"], set()).add(r["ticker"])
    by_team: dict[int, list[dict]] = {}
    for r in team_games:
        if r["season"] == season and r["season_type"] in FORM_TYPES and r["game_id"] in ml:
            by_team.setdefault(r["team_id"], []).append(r)
    out: dict[str, str] = {}
    for rows in by_team.values():
        for r in sorted(rows, key=lambda x: (x["start_time_utc"], x["game_id"]))[-CANDLE_GAMES_PER_TEAM:]:
            for t in ml[r["game_id"]]:
                out[t] = r["game_id"]
    return out


def _load_candles(path: Path, tickers: set[str]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    if not path.exists() or not tickers:
        return out
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("ticker") in tickers:
                out.setdefault(row["ticker"], []).append(row)
    return out


def _adjusted_ratings(team_games: list[dict]) -> tuple[dict[int, tuple[float, float, float]], dict[str, Any]]:
    """The repo's own opponent adjustment, called exactly as ``features.build.build_game_params`` calls it
    (league rates before the cutoff, frozen ``BuildConfig``, then the ``rating_scale`` spread)."""
    import pandas as pd

    from nba_edge.features.build import FEATURE_VERSION, BuildConfig, league_rates, opponent_adjusted_ratings

    if not team_games:
        return {}, {}
    df = pd.DataFrame(team_games)
    last = max(r["game_date_et"] for r in team_games)
    cutoff = (date.fromisoformat(last) + timedelta(days=1)).isoformat()
    cfg = BuildConfig()
    league = league_rates(df[df["game_date_et"] < cutoff])
    raw = opponent_adjusted_ratings(df, cutoff, cfg.team_half_life, cfg.team_prior_games, league,
                                    include_preseason=cfg.include_preseason)
    lg = league["ppp"]
    scaled = {int(t): (lg + (o - lg) * cfg.rating_scale, lg + (d - lg) * cfg.rating_scale, n) for t, (o, d, n) in raw.items()}
    meta = {"cutoff_date": cutoff, "feature_version": FEATURE_VERSION, "half_life_games": cfg.team_half_life,
            "prior_games": cfg.team_prior_games, "rating_scale": cfg.rating_scale, "n_iter": 6,
            "league_ppp": round(lg, 6), "include_preseason": cfg.include_preseason}
    return scaled, meta


def _price_paths(data_root: Path, tickers: set[str]) -> tuple[dict[str, list[dict]], int]:
    """Every captured tick of the given tickers (checkpoint + deltas, via the repo's own replay)."""
    from nba_edge.archive.ledger import Ledger
    from nba_edge.archive.reconstruct import iter_board_ticks

    out: dict[str, list[dict]] = {}
    n = 0
    if not tickers:
        return out, 0
    for at, _run, board, raw in iter_board_ticks(Ledger(data_root)):
        n += 1
        src = "kalshi/markets checkpoint" if raw is not None else "kalshi/markets_delta"
        for t in tickers:
            row = board.get(t)
            if row is None:
                continue
            q = row.get("_quote_cents") or {}
            out.setdefault(t, []).append({
                "captured_at": c_time.to_iso(at), "yes_bid": _cents(q.get("yes_bid")), "yes_ask": _cents(q.get("yes_ask")),
                "last_price": _cents(q.get("last_price")), "volume": _f(row.get("volume_fp")),
                "open_interest": _f(row.get("open_interest_fp")), "source": src})
    return out, n


def load_inputs(app_root: Path, data_root: Path, history_root: Path | None = None, docs_root: Path | None = None) -> ResearchInputs:
    from nba_edge.identity.players import PlayerRegistry
    from nba_edge.identity.teams import registry

    app_root, data_root = Path(app_root), Path(data_root)
    history_root = Path(history_root or DEFAULT_HISTORY_ROOT)
    docs_root = Path(docs_root or DEFAULT_DOCS_ROOT)
    warnings: list[str] = []
    manifest = _read_json(app_root / "manifest.json")
    if not isinstance(manifest, dict) or not manifest.get("run_id"):
        raise ResearchExportError(f"{app_root} holds no v1 manifest.json; run the app export first")
    events, markets = _items(app_root, "events"), _items(app_root, "markets")

    espn = history_root / "history" / "espn"
    team_games = _parquet_rows(list(espn.glob("team_games_*.parquet")))
    player_games = _parquet_rows(list(espn.glob("player_games_*.parquet")))
    if not team_games:
        raise ResearchExportError(f"no team game history under {espn}")
    season = _current_season(team_games)
    hman = _read_json(espn / "MANIFEST.json") or {}
    sman = _read_json(espn / "SHOT_EVENTS_MANIFEST.json") or {}
    kman = _read_json(history_root / "history" / "kalshi" / "MANIFEST.json") or {}

    shot_zones: list[dict] = []
    shot_path = espn / f"shot_events_{season}.parquet"
    if shot_path.exists():
        import pyarrow.compute as pc
        import pyarrow.parquet as pq

        t = pq.read_table(shot_path, columns=["game_id", "is_home", "zone", "shot_made", "is_free_throw", "season_type"])
        t = t.filter(pc.and_(pc.and_(pc.equal(t["season_type"], "regular"), pc.invert(t["is_free_throw"])),
                             pc.not_equal(t["zone"], "unknown")))
        t = t.append_column("made", pc.cast(t["shot_made"], "int64"))
        g = t.group_by(["game_id", "is_home", "zone"]).aggregate([("made", "count"), ("made", "sum")])
        shot_zones = [{"game_id": r["game_id"], "is_home": r["is_home"], "zone": r["zone"], "fga": r["made_count"],
                       "fgm": r["made_sum"]} for r in g.to_pylist()]
    else:
        warnings.append(f"no shot events for {season}")

    market_rows: list[dict] = []
    mt = history_root / "research" / "market_table.parquet"
    if mt.exists():
        cols = ["season", "game_id", "tip_utc", "ticker", "family", "team_id", "player_id", "threshold", "comparator",
                "period", "horizon", "p_market", "exec_yes_cents", "outcome"]
        game_type = {r["game_id"]: r["season_type"] for r in team_games}
        for r in _parquet_rows([mt], cols):
            if r["season"] != season or r["period"] != "FULL" or r["outcome"] is None or game_type.get(r["game_id"]) not in FORM_TYPES:
                continue
            if r["horizon"] == MARKET_HORIZON or r["family"] == "game_winner":
                r["team_id"] = None if r["team_id"] is None else int(r["team_id"])
                r["player_id"] = None if r["player_id"] is None else int(r["player_id"])
                market_rows.append(r)
    else:
        warnings.append("no market table (data/research/market_table.parquet)")
    candle_games = _select_candle_games(team_games, market_rows, season)
    candles = _load_candles(history_root / "history" / "kalshi" / "candles_KXNBAGAME.jsonl.gz", set(candle_games))

    adjusted, adjusted_meta = _adjusted_ratings(team_games)

    reg = PlayerRegistry.load()
    registry_players = [{"nba_id": r.nba_id, "full_name": r.full_name, "espn": r.aliases.get("espn"),
                         "kalshi_uuid": r.aliases.get("kalshi_uuid"), "active": r.active}
                        for r in sorted(reg.records.values(), key=lambda x: x.nba_id)]

    rosters: list[dict] = []
    injuries: list[dict] = []
    rosters_at = injuries_at = None
    official_missing = None
    price_paths: dict[str, list[dict]] = {}
    n_ticks = 0
    predictions: list[dict] = []
    event_tickers = {m["kalshi_ticker"] for m in markets if m.get("event_id")}
    if (data_root / "manifest.jsonl").exists():
        from nba_edge.archive.delta import read_rows
        from nba_edge.archive.ledger import Ledger

        ledger = Ledger(data_root)
        e = ledger.latest("context/rosters")
        if e is not None:
            rosters = read_rows(data_root / e.path)
            rosters_at = c_time.to_iso(e.observed_at_utc or e.written_at_utc)
        e = ledger.latest("context/injuries")
        if e is not None:
            injuries = read_rows(data_root / e.path)
            injuries_at = c_time.to_iso(e.observed_at_utc or e.written_at_utc)
            official_missing = bool(((e.meta or {}).get("official") or {}).get("missing", True))
        for entry in ledger.manifest():
            if entry.kind == "predictions":
                predictions.extend(r for r in read_rows(data_root / entry.path) if r.get("ticker") in event_tickers)
        price_paths, n_ticks = _price_paths(data_root, event_tickers)
    else:
        warnings.append(f"{data_root} holds no archive manifest; no rosters, injuries, price paths or predictions")
    slate = _read_json(data_root / "slates" / "latest" / "slate.json")
    packet = _read_json(data_root / "slates" / "latest" / "packet.json")
    return ResearchInputs(
        manifest=manifest, events=events, markets=markets, model_prices=_items(app_root, "model_prices"),
        recommendations=_items(app_root, "recommendations"), wagers=_items(app_root, "wagers"),
        team_games=team_games, player_games=player_games, history_pulled_at=hman.get("pulled_at"),
        shot_pulled_at=sman.get("pulled_at"), kalshi_pulled_at=kman.get("pulled_at"), shot_zones=shot_zones,
        market_rows=market_rows, candles=candles, adjusted=adjusted, adjusted_meta=adjusted_meta,
        registry_players=registry_players, teams=list(registry().teams), rosters=rosters, rosters_at=rosters_at,
        injuries=injuries, injuries_at=injuries_at, injuries_official_missing=official_missing,
        price_paths=price_paths, board_ticks=n_ticks, slate=slate if isinstance(slate, dict) else None,
        packet=packet if isinstance(packet, dict) else None, predictions=predictions,
        exhibit=_read_json(docs_root / "research" / "market_vs_model.json"), warnings=warnings,
    )


# ------------------------------------------------------------------------------------- arithmetic
def _mean(xs: list[float]) -> float | None:
    return round(statistics.fmean(xs), 4) if xs else None


def _ratio(num: float, den: float, scale: float = 1.0) -> float | None:
    return round(scale * num / den, 4) if den else None


def _team_agg(slug: str, rows: list[dict]) -> float | None:
    if not rows:
        return None
    poss = sum(r["possessions"] for r in rows)
    if slug == "pts":
        return _mean([r["pts"] for r in rows])
    if slug == "opp_pts":
        return _mean([r["opp_pts"] for r in rows])
    if slug == "margin":
        return _mean([r["margin"] for r in rows])
    if slug == "total":
        return _mean([r["total"] for r in rows])
    if slug == "possessions":
        return _mean([r["possessions"] for r in rows])
    if slug == "off_rtg":
        return _ratio(sum(r["pts"] for r in rows), poss, 100.0)
    if slug == "def_rtg":
        return _ratio(sum(r["opp_pts"] for r in rows), poss, 100.0)
    if slug == "net_rtg":
        return _ratio(sum(r["pts"] - r["opp_pts"] for r in rows), poss, 100.0)
    if slug == "win_pct":
        return round(sum(1 for r in rows if r["won"]) / len(rows), 4)
    if slug == "first_half_pts":
        return _mean([r["q1"] + r["q2"] for r in rows])
    if slug == "tov_rate":
        return _ratio(sum(r["tov"] for r in rows), poss, 100.0)
    if slug == "fta_rate":
        return _ratio(sum(r["fta"] for r in rows), sum(r["fga"] for r in rows))
    raise KeyError(slug)


def _team_game_value(slug: str, r: dict) -> float | None:
    if slug in ("pts", "opp_pts", "margin", "total", "possessions"):
        return round(float(r[slug]), 4)
    return _team_agg(slug, [r])


def _player_agg(slug: str, rows: list[dict]) -> float | None:
    if not rows:
        return None
    if slug in ("min",):
        return _mean([r["minutes"] for r in rows])
    if slug in ("pts", "reb", "ast", "fg3m", "stl", "blk", "tov", "plus_minus", "fga", "fta"):
        return _mean([r[slug] for r in rows])
    if slug == "fg_pct":
        return _ratio(sum(r["fgm"] for r in rows), sum(r["fga"] for r in rows))
    if slug == "fg3_pct":
        return _ratio(sum(r["fg3m"] for r in rows), sum(r["fg3a"] for r in rows))
    if slug == "ft_pct":
        return _ratio(sum(r["ftm"] for r in rows), sum(r["fta"] for r in rows))
    if slug == "start_rate":
        return round(sum(1 for r in rows if r["started"]) / len(rows), 4)
    raise KeyError(slug)


def _player_game_value(slug: str, r: dict) -> float | None:
    return round(float(r["minutes"] if slug == "min" else r[slug]), 4)


def _sort_games(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=lambda r: (r["start_time_utc"], r["game_id"]))


def _evt(game_id: str) -> str:
    gid = str(game_id)
    if gid.startswith("espn:"):
        return ids.event_id(SPORT, "espn_event_id", gid.split(":", 1)[1])
    return ids.event_id(SPORT, "nba_game_id", gid)


def _team_pid(team_id: int) -> str:
    return ids.participant_id(SPORT, "TEAM", "nba_team_id", int(team_id))


def _player_pid(nba_id: int) -> str:
    return ids.participant_id(SPORT, "PLAYER", "nba_player_id", int(nba_id))


def _delaldered(rows: list[dict]) -> dict[tuple, dict]:
    """One market per (entity, game): the line nearest 50c (docs/research/ALL_FAMILIES_MODEL_VS_MARKET.md:
    "one row per entity-game (the line nearest 50¢, so rows are independent)"); ties take the lower line."""
    best: dict[tuple, dict] = {}
    for r in rows:
        if r["p_market"] is None:
            continue
        key = (r["_entity"], r["game_id"])
        cur = best.get(key)
        score = (abs(r["p_market"] - 0.5), r["threshold"] if r["threshold"] is not None else 0.0, r["ticker"])
        if cur is None or score < cur["_score"]:
            best[key] = dict(r, _score=score)
    return best


# ------------------------------------------------------------------------------------- definitions
@dataclass(frozen=True)
class MetricDef:
    slug: str
    name: str
    short: str
    description: str
    unit: str | None
    stat_type: str
    hib: bool | None
    category: str
    windows: tuple[str, ...]
    split: bool = False
    series: bool = False


TEAM_BOX = (
    MetricDef("pts", "Points per game", "PTS", "Mean points scored per game (ESPN box score `pts`).", "points", "RATE", True,
              "scoring", ("SEASON", "L10", "L5", "L3"), True, True),
    MetricDef("opp_pts", "Points allowed per game", "OPP PTS", "Mean points allowed per game (`opp_pts`).", "points", "RATE", False,
              "defense", ("SEASON", "L10", "L5", "L3"), True, True),
    MetricDef("margin", "Average margin", "MARGIN", "Mean final margin per game (`pts - opp_pts`, stored as `margin`).", "points",
              "RATE", True, "overall", ("SEASON", "L10", "L5", "L3"), True, True),
    MetricDef("total", "Average game total", "TOTAL", "Mean combined points per game (`total`); neutral by design.", "points", "RATE",
              None, "pace", ("SEASON", "L10", "L5", "L3"), True, True),
    MetricDef("possessions", "Possessions per game", "POSS", "Mean estimated possessions per game, the stored "
              "`possessions = fga + 0.44*fta - oreb + tov` (data/history.py:278); a pace proxy, neutral.", "possessions", "RATE",
              None, "pace", ("SEASON", "L10", "L5", "L3"), True, True),
    MetricDef("off_rtg", "Offensive rating", "ORTG", "Points scored per 100 stored possessions: 100*sum(pts)/sum(possessions). "
              "Raw (not opponent-adjusted).", "points/100 poss", "RATING", True, "efficiency", ("SEASON", "L10", "L5", "L3"), True),
    MetricDef("def_rtg", "Defensive rating", "DRTG", "Points allowed per 100 stored possessions: 100*sum(opp_pts)/sum(possessions). "
              "Raw (not opponent-adjusted).", "points/100 poss", "RATING", False, "efficiency", ("SEASON", "L10", "L5", "L3"), True),
    MetricDef("net_rtg", "Net rating", "NET", "Point differential per 100 stored possessions: 100*sum(pts - opp_pts)/sum(possessions).",
              "points/100 poss", "RATING", True, "efficiency", ("SEASON", "L10", "L5", "L3"), True),
    MetricDef("win_pct", "Win percentage", "W%", "Share of games won (`won`).", "fraction", "PERCENT", True, "overall",
              ("SEASON", "L10", "L5", "L3"), True),
    MetricDef("first_half_pts", "First-half points per game", "1H PTS", "Mean of `q1 + q2` per game.", "points", "RATE", True,
              "scoring", ("SEASON", "L10", "L5", "L3")),
    MetricDef("tov_rate", "Turnovers per 100 possessions", "TOV/100", "100*sum(tov)/sum(possessions).", "turnovers/100 poss",
              "RATE", False, "ball security", ("SEASON", "L10", "L5", "L3")),
    MetricDef("fta_rate", "Free-throw rate", "FTr", "sum(fta)/sum(fga): free-throw attempts per field-goal attempt.", "ratio",
              "RATE", True, "shooting", ("SEASON", "L10", "L5", "L3")),
)
TEAM_HEADLINE_SERIES = ("pts", "opp_pts", "margin", "total", "possessions")

ADJ_DEFS = (
    MetricDef("adj_off_ppp", "Opponent-adjusted offense (model input)", "adj ORTG",
              "features.build.opponent_adjusted_ratings: EWM (half-life 25 games) offensive points per 100 possessions with the "
              "opponent's defensive strength and half the home edge removed, shrunk to the league with 4 prior games, 6 "
              "synchronous iterations, then spread by rating_scale 1.9 exactly as build_game_params does. x100.",
              "points/100 poss", "RATING", True, "model inputs", ("ADJ",)),
    MetricDef("adj_def_ppp", "Opponent-adjusted defense (model input)", "adj DRTG",
              "Same function, defensive points allowed per 100 possessions (lower is better). x100.", "points/100 poss", "RATING",
              False, "model inputs", ("ADJ",)),
    MetricDef("adj_net_ppp", "Opponent-adjusted net (model input)", "adj NET",
              "adj_off_ppp - adj_def_ppp from the same call.", "points/100 poss", "RATING", True, "model inputs", ("ADJ",)),
)
SOS_DEF = MetricDef("sos_opp_net_rtg", "Strength of schedule (opponents' net rating)", "SOS",
                    "Mean, over a team's regular-season games, of each opponent's SEASON net rating (this registry's "
                    "met_nba.team_net_rtg). Arithmetic over stored values; not opponent-adjusted.", "points/100 poss", "RATING",
                    True, "schedule", ("SEASON",))
TEAM_MARKET = (
    MetricDef("mkt_ml_implied_win_prob", "Pre-tip moneyline implied win probability", "ML P(win)",
              "Mean of the team's own KXNBAGAME market mid (market_table `p_market`, analysis-only mid) at the T-30m horizon.",
              "probability", "PROBABILITY", True, "markets", ("SEASON",), False, True),
    MetricDef("mkt_ml_win_minus_implied", "Wins minus moneyline-implied", "W - mkt",
              "Mean of (won - T-30m implied win probability) over the team's settled KXNBAGAME markets: how far results "
              "beat (+) or trailed (-) the pre-tip price. Descriptive, not predictive.", "probability", "PROBABILITY", None,
              "markets", ("SEASON",)),
    MetricDef("mkt_spread_cover_minus_implied", "Spread YES minus implied", "ATS - mkt",
              "Mean of (settled YES - T-30m mid) over the team's KXNBASPREAD markets, de-laddered to one line per team-game "
              "(the line nearest 50c).", "probability", "PROBABILITY", None, "markets", ("SEASON",)),
    MetricDef("mkt_total_over_minus_implied", "Game total OVER minus implied", "O - mkt",
              "Mean of (settled OVER - T-30m mid) over KXNBATOTAL markets of the team's games, de-laddered to one line per "
              "game (nearest 50c).", "probability", "PROBABILITY", None, "markets", ("SEASON",)),
    MetricDef("mkt_team_total_over_minus_implied", "Team total OVER minus implied", "TT O - mkt",
              "Mean of (settled OVER - T-30m mid) over the team's KXNBATEAMTOTAL markets, de-laddered (nearest 50c). Team-total "
              "markets exist from 2026-02-10 only.", "probability", "PROBABILITY", None, "markets", ("SEASON",)),
)
SHOT_ZONES = ("rim", "paint_non_rim", "midrange", "corner_three", "above_break_three")
SHOT_DEFS = tuple(
    MetricDef(f"shot_share_{z}", f"Shot share: {z.replace('_', ' ')}", f"{z[:4].upper()}%",
              f"Share of the team's located non-free-throw shot attempts in the `{z}` zone (shotprofile/court.py zones), "
              "regular season. Shot events are keyed by ESPN team ids; mapped to NBA ids through the game's home flag in "
              "team_games.", "fraction", "PERCENT", None, "shot profile", ("SEASON",))
    for z in SHOT_ZONES)

PLAYER_BOX = (
    MetricDef("min", "Minutes per game", "MIN", "Mean minutes over games played (`minutes`, played rows only).", "minutes", "RATE",
              True, "usage", ("SEASON", "L10", "L5", "L3"), True),
    MetricDef("pts", "Points per game", "PTS", "Mean points over games played.", "points", "RATE", True, "scoring",
              ("SEASON", "L10", "L5", "L3"), True, True),
    MetricDef("reb", "Rebounds per game", "REB", "Mean rebounds over games played.", "rebounds", "RATE", True, "rebounding",
              ("SEASON", "L10", "L5", "L3"), True),
    MetricDef("ast", "Assists per game", "AST", "Mean assists over games played.", "assists", "RATE", True, "playmaking",
              ("SEASON", "L10", "L5", "L3"), True),
    MetricDef("fg3m", "Threes made per game", "3PM", "Mean three-pointers made over games played.", "threes", "RATE", True,
              "shooting", ("SEASON", "L10", "L5", "L3")),
    MetricDef("plus_minus", "Plus-minus per game", "+/-", "Mean on-court plus-minus over games played (ESPN box `plus_minus`).",
              "points", "RATE", True, "impact", ("SEASON", "L10", "L5", "L3")),
    MetricDef("stl", "Steals per game", "STL", "Mean steals over games played.", "steals", "RATE", True, "defense", ("SEASON",)),
    MetricDef("blk", "Blocks per game", "BLK", "Mean blocks over games played.", "blocks", "RATE", True, "defense", ("SEASON",)),
    MetricDef("tov", "Turnovers per game", "TOV", "Mean turnovers over games played.", "turnovers", "RATE", False, "ball security",
              ("SEASON",)),
    MetricDef("fga", "Field-goal attempts per game", "FGA", "Mean field-goal attempts over games played (usage proxy).",
              "attempts", "RATE", None, "usage", ("SEASON",)),
    MetricDef("fta", "Free-throw attempts per game", "FTA", "Mean free-throw attempts over games played (usage proxy).",
              "attempts", "RATE", None, "usage", ("SEASON",)),
    MetricDef("fg_pct", "Field-goal percentage", "FG%", "sum(fgm)/sum(fga) over games played.", "fraction", "PERCENT", True,
              "shooting", ("SEASON",)),
    MetricDef("fg3_pct", "Three-point percentage", "3P%", "sum(fg3m)/sum(fg3a) over games played.", "fraction", "PERCENT", True,
              "shooting", ("SEASON",)),
    MetricDef("ft_pct", "Free-throw percentage", "FT%", "sum(ftm)/sum(fta) over games played.", "fraction", "PERCENT", True,
              "shooting", ("SEASON",)),
    MetricDef("start_rate", "Start rate", "GS%", "Share of games played in which the player started (`started`).", "fraction",
              "PERCENT", None, "role", ("SEASON",)),
)
PLAYER_RANKED = ("min", "pts", "reb", "ast", "fg3m", "plus_minus", "stl", "blk")
PROP_FAMILIES = (("player_points", "pts", "points"), ("player_rebounds", "reb", "rebounds"),
                 ("player_assists", "ast", "assists"), ("player_threes", "fg3m", "threes"))
PLAYER_PROP = tuple(
    MetricDef(f"prop_{stat}_over_minus_implied", f"{label.title()} prop OVER minus implied", f"{stat.upper()} O - mkt",
              f"Mean of (settled YES - T-30m mid) over the player's {fam} markets (KXNBA{ {'pts': 'PTS', 'reb': 'REB', 'ast': 'AST', 'fg3m': '3PT'}[stat]}), "
              "de-laddered to one line per player-game (nearest 50c). DNP markets that settled as scalars are absent from "
              "the market table.", "probability", "PROBABILITY", None, "props", ("SEASON",))
    for fam, stat, label in PROP_FAMILIES)
MODEL_P = MetricDef("model_p_data_only", "Model probability (DATA_ONLY) per run", "P model",
                    "The simulator's `p_data_only` for one contract, one point per simulate run (predictions ledger). Gated: "
                    "every row carries the run's gate and is RESEARCH authority.", "probability", "PROBABILITY", None, "model",
                    ("RUN",))


# ------------------------------------------------------------------------------------------ build
class _Ctx:
    """Shared state for one build: identities, quality objects, the run envelope."""

    def __init__(self, inp: ResearchInputs, run_id: str, generated_at: str):
        self.inp, self.run_id, self.now = inp, run_id, generated_at
        self.season = _current_season(inp.team_games)
        self.teams = {t.team_id: t for t in inp.teams}
        self.team_part = {tid: build.participant(sport=SPORT, participant_type="TEAM", source="nba_team_id", source_id=tid,
                                                 display_name=t.name, short_name=t.tricode, source_ids={"tricode": t.tricode},
                                                 metadata={"conference": t.conference, "division": t.division})
                          for tid, t in self.teams.items()}
        self.v1_events = {e["event_id"]: e for e in inp.events}
        self.event_by_game = {e["source_ids"].get("nba_edge_game_id"): e["event_id"] for e in inp.events
                              if e.get("source_ids", {}).get("nba_edge_game_id")}
        self.hist_as_of = max(r["start_time_utc"] for r in inp.team_games)
        stamps = [self.hist_as_of, inp.manifest.get("generated_at")]
        stamps += [m["captured_at"] for m in inp.markets if m.get("captured_at")]
        stamps += [x for x in (inp.rosters_at, inp.injuries_at) if x]
        self.as_of = max(c_time.to_iso(s) for s in stamps if s)
        self.metrics: dict[str, dict] = {}
        self.rankings: dict[tuple[str, str], dict] = {}
        self.docs: list[dict] = []
        self.published_event_ids = set(self.v1_events)
        self.hist_mh: dict[int, list[str]] = {}  # team_id -> historical event ids with published market history
        cov_box = f"{min(r['game_date_et'] for r in inp.team_games)}..{max(r['game_date_et'] for r in inp.team_games)}"
        self.q_box = R.quality(status="PARTIAL", source="ESPN box scores (data/history/espn, `nba history`)", generated_at=generated_at,
                               production=False, data_as_of=self.hist_as_of, source_version=inp.history_pulled_at,
                               methodology_version=METHODOLOGY_VERSION, coverage=f"3 seasons, {cov_box}",
                               sample_size=len(inp.team_games),
                               limitations=[A_SCHEDULE, A_TEAM_METRICS + " (derived here on export by arithmetic over stored rows)",
                                            "preseason excluded (systems validation only)",
                                            f"per-entity series capped at the last {SERIES_CAP} games; profile game lists at the last {TEAM_GAME_REFS} "
                                            "(the full stored log is in extensions.game_log)"])
        self.q_player = R.quality(status="PARTIAL", source="ESPN box scores (data/history/espn player_games)", generated_at=generated_at,
                                  production=False, data_as_of=self.hist_as_of, source_version=inp.history_pulled_at,
                                  methodology_version=METHODOLOGY_VERSION, coverage=f"3 seasons, {cov_box}",
                                  sample_size=len(inp.player_games),
                                  limitations=[A_SCHEDULE, A_PLAYER_METRICS + " (derived here on export)", A_REGISTRY, A_USAGE,
                                               f"player profiles only for the identity registry; series and logs capped at the last "
                                               f"{SERIES_CAP} games"])
        self.q_adj = R.quality(status="RESEARCH", source="features.build.opponent_adjusted_ratings over data/history/espn team_games",
                               generated_at=generated_at, production=False, data_as_of=self.hist_as_of,
                               source_version=inp.adjusted_meta.get("feature_version"), methodology_version=METHODOLOGY_VERSION,
                               coverage=f"cutoff {inp.adjusted_meta.get('cutoff_date')}",
                               limitations=[A_ADJ, A_ADJ_TEST, "features-0.1.0, frozen baseline parameters "
                                            "(NBA_BASELINE_2026_PRESEASON_V1); computed on export, no stored history"])
        self.q_market = R.quality(status="PARTIAL", source="data/research/market_table.parquet (Kalshi settled markets + hourly candles)",
                                  generated_at=generated_at, production=False, data_as_of=self.hist_as_of,
                                  source_version=inp.kalshi_pulled_at, methodology_version=METHODOLOGY_VERSION,
                                  coverage=f"{self.season}", sample_size=len(inp.market_rows),
                                  limitations=[A_HISTORY_MKT, A_CANDLES, A_SCHEDULE,
                                               f"residual metrics use the {MARKET_HORIZON} horizon mid (analysis-only) and one line "
                                               "per entity-game (nearest 50c)"])
        self.q_shot = R.quality(status="RESEARCH", source="data/history/espn shot_events (ESPN summary play-by-play, shooting plays)",
                                generated_at=generated_at, production=False, data_as_of=self.hist_as_of,
                                source_version=inp.shot_pulled_at, methodology_version=METHODOLOGY_VERSION,
                                coverage=f"{self.season} regular season",
                                limitations=[A_SHOTS, A_SHOT_IDS, A_PBP])

    def link(self, rel: str, kind: str, label: str, target_id: str | None, path: str | None) -> dict:
        return R.link(rel=rel, target_kind=kind, label=label, target_id=target_id, path=path)

    def metric(self, d: MetricDef, *, entity: str, quality: dict, source: str, supports: dict, comparison: str | None,
               windows: list[str], splits: list[str], hist_start: str | None, freshness: str, update: str,
               limitations: list[str], related: list[str] | None = None, extensions: dict | None = None) -> str:
        prefix = {"TEAM": "team_", "PLAYER": "player_", "MARKET": ""}[entity]
        m = R.metric(sport=SPORT, slug=prefix + d.slug, name=d.name, short_name=d.short, description=d.description, entity_type=entity,
                     category=d.category, stat_type=d.stat_type, source=source, quality=quality, freshness=freshness,
                     higher_is_better=d.hib, unit=d.unit, comparison_universe=comparison, supports=supports, windows=windows,
                     splits=splits, methodology_version=METHODOLOGY_VERSION, historical_start=hist_start, update_frequency=update,
                     known_limitations=limitations, related_metrics=related, extensions=extensions)
        self.metrics[m["metric_id"]] = m
        return m["metric_id"]


def _window_for(label: str, rows: list[dict]) -> dict:
    start = rows[0]["start_time_utc"] if rows else None
    end = rows[-1]["start_time_utc"] if rows else None
    if label == "SEASON":
        return R.window("SEASON", start=start, end=end)
    n = int(label[1:])
    return R.window("LAST_N", n=n, start=start, end=end)


def _rank_window(label: str) -> dict:
    return R.window("SEASON") if label == "SEASON" else R.window("LAST_N", n=int(label[1:]))


def _windows_rows(rows_form: list[dict], rows_season: list[dict]) -> dict[str, list[dict]]:
    out = {"SEASON": rows_season}
    for n in FORM_WINDOWS:
        out[f"L{n}"] = rows_form[-n:]
    return out


def _team_rows(ctx: _Ctx) -> tuple[dict[int, list[dict]], dict[int, list[dict]], dict[int, list[dict]]]:
    """team_id -> (all rows, non-preseason rows, current-season regular rows), each in time order."""
    allr: dict[int, list[dict]] = {}
    for r in ctx.inp.team_games:
        allr.setdefault(r["team_id"], []).append(r)
    allr = {t: _sort_games(v) for t, v in allr.items()}
    form = {t: [r for r in v if r["season_type"] in FORM_TYPES] for t, v in allr.items()}
    season = {t: [r for r in v if r["season"] == ctx.season and r["season_type"] == "regular"] for t, v in allr.items()}
    return allr, form, season


def _ranking(ctx: _Ctx, metric_id: str, *, universe: str, etype: str, window: dict, values: list[dict], hib: bool | None,
             quality: dict, season: str | None, ufilter: str | None, path_for: Any) -> dict:
    rk = R.ranking(sport=SPORT, metric_id=metric_id, universe_label=universe, entity_type=etype, window=window, as_of=ctx.hist_as_of,
                   higher_is_better=hib, values=values, run_id=ctx.run_id, generated_at=ctx.now, quality=quality, season=season,
                   universe_filter=ufilter, path_for=path_for,
                   links=[ctx.link("METRIC", "metric_registry", "metric registry", metric_id, R.app_path(R.METRICS_NAME))])
    ctx.rankings[(metric_id, window["label"])] = rk
    ctx.docs.append(rk)
    return rk


def _obs(ctx: _Ctx, metric_id: str, entity_id: str, etype: str, value: Any, window: dict, *, source: str, status: str,
         unit: str | None, sample: int | None, season: str | None, ranking: dict | None = None, sp: dict | None = None,
         adjusted: Any = None, as_of: str | None = None, extensions: dict | None = None) -> dict:
    return R.observation(sport=SPORT, metric_id=metric_id, entity_id=entity_id, entity_type=etype, value=value, window=window,
                         as_of=as_of or ctx.hist_as_of, source=source, quality_status=status, unit=unit, adjusted_value=adjusted,
                         split=sp, sample_size=sample, season=season,
                         context=R.context_from_ranking(ranking, entity_id) if ranking else None, extensions=extensions)


def _ranking_ref(rk: dict) -> dict:
    return {"ranking_id": rk["ranking_id"], "metric_id": rk["metric_id"], "window_label": rk["window"]["label"], "split": None,
            "path": R.ranking_path(rk["ranking_id"])}


def _series_ref(ser: dict) -> dict:
    return {"series_id": ser["series_id"], "metric_id": ser["metric_id"], "x_axis": ser["x_axis"], "split": None,
            "path": R.series_path(ser["series_id"])}


def _game_ref(ctx: _Ctx, r: dict) -> dict:
    """A historical team-game row as a game reference (no path: historical games have no event document)."""
    eid = ctx.event_by_game.get(r["game_id"]) or _evt(r["game_id"])
    opp = ctx.teams.get(r["opp_team_id"])
    return R.game_ref(event_id=eid, start_time_utc=r["start_time_utc"], status="FINAL",
                      opponent_id=_team_pid(r["opp_team_id"]), opponent_name=opp.name if opp else None,
                      home_away="HOME" if r["home"] else "AWAY",
                      result={"for": float(r["pts"]), "against": float(r["opp_pts"]), "outcome": "W" if r["won"] else "L"},
                      competition=f"{r['season']} {r['season_type']}",
                      path=R.event_path(eid) if eid in ctx.published_event_ids else None)


def _upcoming_refs(ctx: _Ctx, pid: str) -> list[dict]:
    out = []
    for ev in ctx.inp.events:
        parts = [p["participant_id"] for p in ev["participants"]]
        if pid not in parts:
            continue
        opp = next((p for p in ev["participants"] if p["participant_id"] != pid), None)
        ha = "HOME" if ev.get("home_participant") == pid else ("AWAY" if ev.get("away_participant") == pid else None)
        out.append(R.game_ref(event_id=ev["event_id"], start_time_utc=ev["start_time_utc"], status=ev["status"],
                              opponent_id=opp["participant_id"] if opp else None, opponent_name=opp["display_name"] if opp else None,
                              home_away=ha, competition=f"{ev.get('season')} {ev.get('competition')}",
                              path=R.event_path(ev["event_id"])))
    return out


# ---------------------------------------------------------------------------------------- teams
def _build_teams(ctx: _Ctx) -> dict[str, dict]:
    """Team metrics, rankings, series and profiles. Returns participant_id -> profile."""
    inp = ctx.inp
    allr, form, season_rows = _team_rows(ctx)
    tids = sorted(t for t in ctx.teams if t in allr)
    hist_start = min(r["game_date_et"] for r in inp.team_games)
    universe_season = f"NBA teams, {ctx.season} regular season"
    sup_box = {d.slug: R.supports(rank=True, percentile=True, time_series=d.series, windows=True, splits=d.split, home_away=d.split)
               for d in TEAM_BOX}
    source_box = "espn team_games"
    obs: dict[int, list[dict]] = {t: [] for t in tids}
    splits: dict[int, list[dict]] = {t: [] for t in tids}
    refs: dict[int, list[dict]] = {t: [] for t in tids}
    sers: dict[int, list[dict]] = {t: [] for t in tids}
    tp = lambda t: R.team_path(_team_pid(t))  # noqa: E731

    def team_values(fn: Any) -> list[dict]:
        out = []
        for t in tids:
            v, n = fn(t)
            out.append({"entity_id": _team_pid(t), "display_name": ctx.teams[t].name, "short_name": ctx.teams[t].tricode,
                        "value": v, "sample_size": n})
        return out

    for d in TEAM_BOX:
        mid = ctx.metric(d, entity="TEAM", quality=ctx.q_box, source=source_box, supports=sup_box[d.slug],
                         comparison=universe_season, windows=list(d.windows), splits=["home_away"] if d.split else [],
                         hist_start=hist_start, freshness="STALE", update="manual history pull (history.yml)",
                         limitations=[A_TEAM_METRICS, A_SCHEDULE, "L-windows are each team's last N non-preseason games "
                                      "(regular + play-in + playoffs), so they end on different dates"])
        for wl in d.windows:
            wrows = {t: _windows_rows(form[t], season_rows[t])[wl] for t in tids}
            universe = universe_season if wl == "SEASON" else f"NBA teams, last {wl[1:]} non-preseason games"
            rk = _ranking(ctx, mid, universe=universe, etype="TEAM", window=_rank_window(wl),
                          values=team_values(lambda t, wrows=wrows, slug=d.slug: (_team_agg(slug, wrows[t]), len(wrows[t]))),
                          hib=d.hib, quality=ctx.q_box, season=ctx.season, ufilter="all 30 NBA teams" if wl == "SEASON" else
                          f"each team's last {wl[1:]} non-preseason games", path_for=R.team_path)
            for t in tids:
                obs[t].append(_obs(ctx, mid, _team_pid(t), "TEAM", _team_agg(d.slug, wrows[t]), _window_for(wl, wrows[t]),
                                   source=source_box, status="PARTIAL", unit=d.unit, sample=len(wrows[t]), season=ctx.season,
                                   ranking=rk))
                refs[t].append(_ranking_ref(rk))
        if d.split:
            for t in tids:
                for side, flag in (("HOME", True), ("AWAY", False)):
                    rows = [r for r in season_rows[t] if r["home"] is flag]
                    splits[t].append(_obs(ctx, mid, _team_pid(t), "TEAM", _team_agg(d.slug, rows), _window_for("SEASON", rows),
                                          source=source_box, status="PARTIAL", unit=d.unit, sample=len(rows),
                                          season=ctx.season, sp=R.split("home_away", side)))
        if d.series:
            for t in tids:
                rows = form[t][-SERIES_CAP:]
                pts = [R.point(x=r["game_id"], t=r["start_time_utc"], value=_team_game_value(d.slug, r), quality_status="PARTIAL",
                               event_id=ctx.event_by_game.get(r["game_id"]) or _evt(r["game_id"]), opponent_id=_team_pid(r["opp_team_id"]),
                               sample_size=1, source="espn team_games") for r in rows]
                ser = R.time_series(sport=SPORT, metric_id=mid, entity_id=_team_pid(t), entity_type="TEAM", x_axis="GAME",
                                    points=R.rolling(pts, 10), as_of=ctx.hist_as_of, run_id=ctx.run_id, generated_at=ctx.now,
                                    quality=ctx.q_box, unit=d.unit, rolling_window=10,
                                    links=[ctx.link("TEAM", "entity_profile", ctx.teams[t].name, _team_pid(t), tp(t))])
                ctx.docs.append(ser)
                sers[t].append(_series_ref(ser))

    # Opponent-adjusted ratings (RESEARCH): the repo's own function, one cutoff.
    adj = inp.adjusted
    if adj:
        wl = f"EWM to {inp.adjusted_meta['cutoff_date']}"
        w = R.window("CUSTOM", label=wl, end=inp.adjusted_meta["cutoff_date"] + "T00:00:00Z")
        vals = {"adj_off_ppp": lambda t: adj[t][0] * 100, "adj_def_ppp": lambda t: adj[t][1] * 100,
                "adj_net_ppp": lambda t: (adj[t][0] - adj[t][1]) * 100}
        for d in ADJ_DEFS:
            mid = ctx.metric(d, entity="TEAM", quality=ctx.q_adj, source="nba_edge.features.build.opponent_adjusted_ratings",
                             supports=R.supports(rank=True, percentile=True, opponent_adjustment=True, schedule_adjustment=True),
                             comparison="NBA teams", windows=[wl], splits=[], hist_start=hist_start, freshness="STALE",
                             update="per export (recomputed from the stored history)", limitations=[A_ADJ, A_ADJ_TEST],
                             related=[ids.metric_id(SPORT, "team_off_rtg"), ids.metric_id(SPORT, "team_def_rtg")],
                             extensions={"parameters": inp.adjusted_meta})
            rk = _ranking(ctx, mid, universe="NBA teams", etype="TEAM", window=w,
                          values=team_values(lambda t, f=vals[d.slug]: (round(f(t), 4) if t in adj else None, None)),
                          hib=d.hib, quality=ctx.q_adj, season=ctx.season, ufilter="all teams with history", path_for=R.team_path)
            for t in tids:
                if t not in adj:
                    continue
                obs[t].append(_obs(ctx, mid, _team_pid(t), "TEAM", round(vals[d.slug](t), 4), w, source="features.build",
                                   status="RESEARCH", unit=d.unit, sample=None, season=ctx.season, ranking=rk,
                                   adjusted=round(vals[d.slug](t), 4), extensions={"effective_n": round(adj[t][2], 3)}))
                refs[t].append(_ranking_ref(rk))

    # Strength of schedule (PARTIAL): mean opponent SEASON net rating.
    net = {t: _team_agg("net_rtg", season_rows[t]) for t in tids}
    sos = {}
    for t in tids:
        vals_ = [net[r["opp_team_id"]] for r in season_rows[t] if net.get(r["opp_team_id"]) is not None]
        sos[t] = (_mean(vals_), len(vals_))
    mid = ctx.metric(SOS_DEF, entity="TEAM", quality=ctx.q_box, source=source_box, supports=R.supports(rank=True, percentile=True,
                     schedule_adjustment=False), comparison=universe_season, windows=["SEASON"], splits=[], hist_start=hist_start,
                     freshness="STALE", update="manual history pull", limitations=[A_SOS + " in the repo; arithmetic here",
                                                                                     A_SCHEDULE],
                     related=[ids.metric_id(SPORT, "team_net_rtg")])
    rk = _ranking(ctx, mid, universe=universe_season, etype="TEAM", window=R.window("SEASON"), values=team_values(lambda t: sos[t]),
                  hib=True, quality=ctx.q_box, season=ctx.season, ufilter="all 30 NBA teams", path_for=R.team_path)
    for t in tids:
        obs[t].append(_obs(ctx, mid, _team_pid(t), "TEAM", sos[t][0], _window_for("SEASON", season_rows[t]), source=source_box,
                           status="PARTIAL", unit=SOS_DEF.unit, sample=sos[t][1], season=ctx.season, ranking=rk))
        refs[t].append(_ranking_ref(rk))

    # Market residuals (PARTIAL), from the market table at the T-30m horizon.
    home_of = {}
    for r in inp.team_games:
        if r["home"]:
            home_of[r["game_id"]] = (r["team_id"], r["opp_team_id"])
    rows_t30 = [r for r in inp.market_rows if r["horizon"] == MARKET_HORIZON]
    fam_rows: dict[str, list[dict]] = {"game_winner": [], "game_spread": [], "game_total": [], "team_total": []}
    for r in rows_t30:
        if r["family"] in ("game_winner", "game_spread", "team_total") and r["team_id"] is not None:
            fam_rows[r["family"]].append(dict(r, _entity=r["team_id"]))
        elif r["family"] == "game_total" and r["game_id"] in home_of:
            for t in home_of[r["game_id"]]:
                fam_rows["game_total"].append(dict(r, _entity=t))
    ml = {}
    for r in fam_rows["game_winner"]:
        if r["p_market"] is not None:
            ml.setdefault(r["_entity"], []).append(r)
    resid = {"game_spread": _delaldered(fam_rows["game_spread"]), "game_total": _delaldered(fam_rows["game_total"]),
             "team_total": _delaldered(fam_rows["team_total"])}
    mvals: dict[str, dict[int, tuple[float | None, int]]] = {}
    mvals["mkt_ml_implied_win_prob"] = {t: (_mean([r["p_market"] for r in ml.get(t, [])]), len(ml.get(t, []))) for t in tids}
    mvals["mkt_ml_win_minus_implied"] = {t: (_mean([r["outcome"] - r["p_market"] for r in ml.get(t, [])]), len(ml.get(t, [])))
                                         for t in tids}
    for slug, fam in (("mkt_spread_cover_minus_implied", "game_spread"), ("mkt_total_over_minus_implied", "game_total"),
                      ("mkt_team_total_over_minus_implied", "team_total")):
        per: dict[int, list[float]] = {}
        for (ent, _g), r in resid[fam].items():
            per.setdefault(ent, []).append(r["outcome"] - r["p_market"])
        mvals[slug] = {t: (_mean(per.get(t, [])), len(per.get(t, []))) for t in tids}
    mkt_start = min((r["tip_utc"] for r in inp.market_rows), default=None)
    for d in TEAM_MARKET:
        if not any(v[0] is not None for v in mvals[d.slug].values()):
            continue
        mid = ctx.metric(d, entity="TEAM", quality=ctx.q_market, source="data/research/market_table.parquet",
                         supports=R.supports(rank=True, percentile=True, time_series=d.series), comparison=f"NBA teams, {ctx.season}",
                         windows=["SEASON"], splits=[], hist_start=mkt_start, freshness="STALE", update="manual Kalshi history pull",
                         limitations=[A_HISTORY_MKT, A_CANDLES])
        rk = _ranking(ctx, mid, universe=f"NBA teams, {ctx.season} settled Kalshi markets", etype="TEAM", window=R.window("SEASON"),
                      values=team_values(lambda t, s=d.slug: mvals[s][t]), hib=d.hib, quality=ctx.q_market, season=ctx.season,
                      ufilter=f"teams with settled markets at {MARKET_HORIZON}", path_for=R.team_path)
        for t in tids:
            v, n = mvals[d.slug][t]
            if v is None:
                continue
            obs[t].append(_obs(ctx, mid, _team_pid(t), "TEAM", v, R.window("SEASON"), source="market_table", status="PARTIAL",
                               unit=d.unit, sample=n, season=ctx.season, ranking=rk))
            refs[t].append(_ranking_ref(rk))
        if d.series:
            for t in tids:
                rows = sorted(ml.get(t, []), key=lambda r: (r["tip_utc"], r["ticker"]))[-SERIES_CAP:]
                opp_of = {r["game_id"]: r["opp_team_id"] for r in allr.get(t, [])}
                pts = [R.point(x=r["game_id"], t=r["tip_utc"], value=r["p_market"], quality_status="PARTIAL",
                               event_id=ctx.event_by_game.get(r["game_id"]) or _evt(r["game_id"]),
                               opponent_id=_team_pid(opp_of[r["game_id"]]) if r["game_id"] in opp_of else None,
                               source=f"market_table {MARKET_HORIZON} mid") for r in rows]
                if not pts:
                    continue
                ser = R.time_series(sport=SPORT, metric_id=mid, entity_id=_team_pid(t), entity_type="TEAM", x_axis="GAME",
                                    points=R.rolling(pts, 10), as_of=ctx.hist_as_of, run_id=ctx.run_id, generated_at=ctx.now,
                                    quality=ctx.q_market, unit=d.unit, rolling_window=10,
                                    links=[ctx.link("TEAM", "entity_profile", ctx.teams[t].name, _team_pid(t), tp(t))])
                ctx.docs.append(ser)
                sers[t].append(_series_ref(ser))

    # Shot-zone shares (RESEARCH).
    if inp.shot_zones:
        game_team = {}
        for r in inp.team_games:
            game_team[(r["game_id"], bool(r["home"]))] = r["team_id"]
        zt: dict[int, dict[str, int]] = {}
        zg: dict[int, set] = {}
        for z in inp.shot_zones:
            t = game_team.get((z["game_id"], bool(z["is_home"])))
            if t is None:
                continue
            zt.setdefault(t, {}).setdefault(z["zone"], 0)
            zt[t][z["zone"]] += int(z["fga"])
            zg.setdefault(t, set()).add(z["game_id"])
        for d, zone in zip(SHOT_DEFS, SHOT_ZONES):
            mid = ctx.metric(d, entity="TEAM", quality=ctx.q_shot, source=f"data/history/espn/shot_events_{ctx.season}.parquet",
                             supports=R.supports(rank=True, percentile=True), comparison=universe_season, windows=["SEASON"],
                             splits=[], hist_start=None, freshness="STALE", update="manual shot-event pull (shot_events.yml)",
                             limitations=[A_SHOTS, A_SHOT_IDS])

            def zval(t: int, zone: str = zone) -> tuple[float | None, int]:
                tot = sum(zt.get(t, {}).values())
                return (_ratio(zt.get(t, {}).get(zone, 0), tot), tot)

            rk = _ranking(ctx, mid, universe=universe_season, etype="TEAM", window=R.window("SEASON"), values=team_values(zval),
                          hib=None, quality=ctx.q_shot, season=ctx.season, ufilter="all 30 NBA teams (located FGA)", path_for=R.team_path)
            for t in tids:
                v, n = zval(t)
                obs[t].append(_obs(ctx, mid, _team_pid(t), "TEAM", v, R.window("SEASON"), source="shot_events", status="RESEARCH",
                                   unit=d.unit, sample=n, season=ctx.season, ranking=rk,
                                   extensions={"games": len(zg.get(t, ()))}))
                refs[t].append(_ranking_ref(rk))

    # Historical market history (hourly moneyline candles) for each team's last games.
    for t in tids:
        ctx.hist_mh[t] = []
    by_game_tickers: dict[str, list[str]] = {}
    for r in inp.market_rows:
        if r["family"] == "game_winner" and r["ticker"] in inp.candles:
            by_game_tickers.setdefault(r["game_id"], [])
            if r["ticker"] not in by_game_tickers[r["game_id"]]:
                by_game_tickers[r["game_id"]].append(r["ticker"])
    q_candles = R.quality(status="PARTIAL", source="data/history/kalshi/candles_KXNBAGAME.jsonl.gz (hourly)", generated_at=ctx.now,
                          production=False, data_as_of=ctx.hist_as_of, source_version=inp.kalshi_pulled_at,
                          methodology_version=METHODOLOGY_VERSION, coverage=f"{ctx.season}, each team's last {CANDLE_GAMES_PER_TEAM} games",
                          limitations=[A_CANDLES, A_HISTORY_MKT, f"published for each team's last {CANDLE_GAMES_PER_TEAM} games only "
                                       "(the full 653,308-row candle history stays in the repository)"])
    for gid, tickers in sorted(by_game_tickers.items()):
        eid = _evt(gid)
        if eid in ctx.published_event_ids:
            continue
        series = []
        for tk in sorted(tickers):
            pts = [R.price_point(captured_at=_iso_epoch(c["end_period_ts"]), yes_bid=(c.get("yes_bid") or {}).get("close"),
                                 yes_ask=(c.get("yes_ask") or {}).get("close"), last_price=(c.get("price") or {}).get("close"),
                                 volume=c.get("volume"), open_interest=c.get("open_interest"), source="kalshi candles 1h")
                   for c in inp.candles[tk]]
            series.append({"market_id": ids.market_id(tk), "kalshi_ticker": tk, "points": pts})
        teams_in = [t for t in home_of.get(gid, ()) if t in ctx.teams]
        mh = R.market_history(sport=SPORT, run_id=ctx.run_id, generated_at=ctx.now, event_id=eid, as_of=ctx.hist_as_of, series=series,
                              quality=q_candles, links=[ctx.link("TEAM", "entity_profile", ctx.teams[t].name, _team_pid(t), tp(t))
                                                        for t in teams_in])
        ctx.docs.append(mh)
        for t in teams_in:
            ctx.hist_mh[t].append(eid)

    # Profiles.
    profiles = {}
    market_log = _team_market_log(ctx, allr)
    log_seasons = set(sorted({r["season"] for r in inp.team_games})[-GAME_LOG_SEASONS:])
    for t in tids:
        pid = _team_pid(t)
        hist = [_game_ref(ctx, r) for r in form[t][-TEAM_GAME_REFS:]]
        upcoming = _upcoming_refs(ctx, pid)
        games = hist + upcoming
        opp: dict[str, dict] = {}
        for g in games:
            if g["opponent_id"]:
                o = opp.setdefault(g["opponent_id"], {"participant_id": g["opponent_id"], "display_name": g["opponent_name"] or "",
                                                      "event_ids": [], "path": R.team_path(g["opponent_id"])})
                o["event_ids"].append(g["event_id"])
        links = [ctx.link("CAPABILITIES", "capability_manifest", "capabilities", None, R.app_path(R.CAPABILITIES_NAME)),
                 ctx.link("METRIC", "metric_registry", "metric registry", None, R.app_path(R.METRICS_NAME))]
        links += [ctx.link("EVENT", "event_research", f"next: {g['opponent_name']}", g["event_id"], g["path"]) for g in upcoming]
        links += [ctx.link("MARKET_HISTORY", "market_history", "hourly moneyline candles", e, R.market_history_path(e))
                  for e in ctx.hist_mh.get(t, [])]
        mk = [R.market_ref(m) for m in inp.markets if m.get("participant_id") == pid]
        mk_ids = {m["market_id"] for m in mk}
        profiles[pid] = dict(
            pid=pid, team_id=t, obs=obs[t], splits=splits[t], refs=refs[t], sers=sers[t], games=games,
            opponents=sorted(opp.values(), key=lambda o: o["display_name"]), links=links, markets=mk,
            projections=[_proj_ref(ctx, mp) for mp in inp.model_prices if mp["market_id"] in mk_ids],
            game_log=_team_game_log(ctx, [r for r in allr[t] if r["season"] in log_seasons]), market_log=market_log.get(t))
    return profiles


def _proj_ref(ctx: _Ctx, mp: dict) -> dict:
    rec = next((r for r in ctx.inp.recommendations if r["market_id"] == mp["market_id"]), None)
    return R.projection_ref(mp, research_only=True, authority=rec["authority"] if rec else "RESEARCH_ONLY", quality_status="RESEARCH")


def _team_game_log(ctx: _Ctx, rows: list[dict]) -> dict:
    cols = ["date_et", "event_id", "season", "season_type", "home", "opp", "pts", "opp_pts", "q1", "q2", "q3", "q4", "ot_pts",
            "n_ot", "won", "margin", "total", "possessions", "fga", "fta", "oreb", "tov"]
    out = []
    for r in rows:
        opp = ctx.teams.get(r["opp_team_id"])
        out.append([r["game_date_et"], ctx.event_by_game.get(r["game_id"]) or _evt(r["game_id"]), r["season"], r["season_type"],
                    bool(r["home"]), opp.tricode if opp else str(r["opp_team_id"]), r["pts"], r["opp_pts"], r["q1"], r["q2"], r["q3"],
                    r["q4"], r["ot_pts"], r["n_ot"], bool(r["won"]), r["margin"], r["total"], round(r["possessions"], 3), r["fga"],
                    r["fta"], r["oreb"], r["tov"]])
    return {"columns": cols, "rows": out, "source": "data/history/espn/team_games_*.parquet", "quality_status": "PARTIAL",
            "coverage": f"every stored game of the last {GAME_LOG_SEASONS} seasons, preseason included (labelled by season_type)"}


def _team_market_log(ctx: _Ctx, allr: dict[int, list[dict]]) -> dict[int, dict]:
    """Per team: its moneyline mid at each stored pre-tip horizon and the settled outcome, one row per game."""
    by: dict[tuple[int, str], dict] = {}
    for r in ctx.inp.market_rows:
        if r["family"] != "game_winner" or r["team_id"] is None:
            continue
        row = by.setdefault((r["team_id"], r["game_id"]), {"tip": r["tip_utc"], "ticker": r["ticker"], "outcome": r["outcome"]})
        row[r["horizon"]] = r["p_market"]
    out: dict[int, dict] = {}
    for (t, gid), row in sorted(by.items(), key=lambda kv: (kv[0][0], kv[1]["tip"], kv[0][1])):
        out.setdefault(t, {"columns": ["tip_utc", "event_id", "ticker", *HORIZONS, "outcome"], "rows": [],
                           "source": "data/research/market_table.parquet (game_winner; analysis-only mid per horizon)",
                           "quality_status": "PARTIAL", "limitations": [A_HISTORY_MKT, A_CANDLES]})
        out[t]["rows"].append([row["tip"], ctx.event_by_game.get(gid) or _evt(gid), row["ticker"], *[row.get(h) for h in HORIZONS],
                               row["outcome"]])
    for t in out:
        out[t]["rows"] = out[t]["rows"][-SERIES_CAP:]
    return out


# -------------------------------------------------------------------------------------- players
def _current_teams(ctx: _Ctx) -> tuple[dict[int, int], dict[int, str]]:
    """nba_id -> current team id and position, from the newest roster snapshot (ESPN athlete id = -nba_id)."""
    from nba_edge.identity.teams import TeamIdentityError, registry

    reg = registry()
    team: dict[int, int] = {}
    pos: dict[int, str] = {}
    for r in ctx.inp.rosters:
        try:
            nba_id = -int(r["espn_athlete_id"])
            t = reg.by_tricode(r["team_abbreviation"])
        except (KeyError, ValueError, TypeError, TeamIdentityError):
            continue
        team[nba_id] = t.team_id
        if r.get("position"):
            pos[nba_id] = str(r["position"])
    return team, pos


def _norm(name: str) -> str:
    from nba_edge.identity.normalize import normalize_name

    return normalize_name(name)


_INJ_STATUS = {"out": "OUT", "questionable": "QUESTIONABLE", "doubtful": "DOUBTFUL", "probable": "PROBABLE",
               "day-to-day": "DAY_TO_DAY", "day_to_day": "DAY_TO_DAY", "available": "ACTIVE"}


def _availability(ctx: _Ctx, row: dict, event_id: str | None = None) -> dict:
    status = _INJ_STATUS.get(str(row.get("status") or "").lower(), str(row.get("status") or "UNKNOWN").upper())
    reason = f" ({row['reason']})" if row.get("reason") else ""
    return {"status": status, "detail": f"{row.get('player_name_raw')}{reason}", "as_of": ctx.inp.injuries_at,
            "source": f"{row.get('source') or 'espn_injuries'} (official NBA report not captured)", "event_id": event_id}


def _build_players(ctx: _Ctx) -> dict[str, dict]:
    inp = ctx.inp
    reg = {p["nba_id"]: p for p in inp.registry_players}
    by_player: dict[int, list[dict]] = {}
    for r in inp.player_games:
        by_player.setdefault(r["nba_id"], []).append(r)
    by_player = {k: _sort_games(v) for k, v in by_player.items()}
    market_players = {m["player_id"] for m in inp.markets if m.get("player_id")}
    wanted = sorted(n for n in reg if any(r["season"] == ctx.season for r in by_player.get(n, []))
                    or _player_pid(n) in market_players)
    if not wanted:
        return {}
    played = {n: [r for r in v if r["played"] and r["season_type"] in FORM_TYPES] for n, v in by_player.items()}
    season_played = {n: [r for r in v if r["played"] and r["season"] == ctx.season and r["season_type"] == "regular"]
                     for n, v in by_player.items()}
    cur_team, position = _current_teams(ctx)
    hist_start = min(r["game_date_et"] for r in inp.player_games)
    wanted_set = set(wanted)
    wanted_pids = {_player_pid(n) for n in wanted}
    pp = lambda n: R.player_path(_player_pid(n)) if n in wanted_set else None  # noqa: E731
    pp_e = lambda eid: R.player_path(eid) if eid in wanted_pids else None  # noqa: E731
    universe = f"NBA players, {ctx.season} regular season"
    ufilter = f">= {PLAYER_RANK_MIN_GAMES} games played, {ctx.season} regular season (all players, not only profiled ones)"
    ranked_pool = sorted(n for n, rows in season_played.items() if len(rows) >= PLAYER_RANK_MIN_GAMES)
    latest_name = {n: v[-1]["player_name"] for n, v in by_player.items()}
    obs: dict[int, list[dict]] = {n: [] for n in wanted}
    splits: dict[int, list[dict]] = {n: [] for n in wanted}
    refs: dict[int, list[dict]] = {n: [] for n in wanted}
    sers: dict[int, list[dict]] = {n: [] for n in wanted}
    src = "espn player_games"
    for d in PLAYER_BOX:
        ranked = d.slug in PLAYER_RANKED
        mid = ctx.metric(d, entity="PLAYER", quality=ctx.q_player, source=src,
                         supports=R.supports(rank=ranked, percentile=ranked, time_series=d.series, windows=len(d.windows) > 1,
                                             splits=d.split, home_away=d.split),
                         comparison=universe if ranked else None, windows=list(d.windows), splits=["home_away"] if d.split else [],
                         hist_start=hist_start, freshness="STALE", update="manual history pull (history.yml)",
                         limitations=[A_PLAYER_METRICS, A_REGISTRY, A_SCHEDULE] + ([A_USAGE] if d.category == "usage" else []))
        rk = None
        if ranked:
            rk = _ranking(ctx, mid, universe=universe, etype="PLAYER", window=R.window("SEASON"),
                          values=[{"entity_id": _player_pid(n), "display_name": latest_name[n], "value": _player_agg(d.slug, season_played[n]),
                                   "sample_size": len(season_played[n])} for n in ranked_pool],
                          hib=d.hib, quality=ctx.q_player, season=ctx.season, ufilter=ufilter, path_for=pp_e)
        for n in wanted:
            wr = _windows_rows(played.get(n, []), season_played.get(n, []))
            for wl in d.windows:
                rows = wr[wl]
                if not rows:
                    continue
                use_rk = rk if (wl == "SEASON" and rk and any(e["entity_id"] == _player_pid(n) for e in rk["entries"])) else None
                obs[n].append(_obs(ctx, mid, _player_pid(n), "PLAYER", _player_agg(d.slug, rows), _window_for(wl, rows), source=src,
                                   status="PARTIAL", unit=d.unit, sample=len(rows), season=ctx.season, ranking=use_rk))
            if rk:
                refs[n].append(_ranking_ref(rk))
            if d.split:
                for side, flag in (("HOME", True), ("AWAY", False)):
                    rows = [r for r in season_played.get(n, []) if r["home"] is flag]
                    if rows:
                        splits[n].append(_obs(ctx, mid, _player_pid(n), "PLAYER", _player_agg(d.slug, rows), _window_for("SEASON", rows),
                                              source=src, status="PARTIAL", unit=d.unit, sample=len(rows), season=ctx.season,
                                              sp=R.split("home_away", side)))
            if d.series:
                rows = played.get(n, [])[-SERIES_CAP:]
                if rows:
                    pts = [R.point(x=r["game_id"], t=r["start_time_utc"], value=_player_game_value(d.slug, r), quality_status="PARTIAL",
                                   event_id=ctx.event_by_game.get(r["game_id"]) or _evt(r["game_id"]),
                                   opponent_id=_team_pid(r["opp_team_id"]), sample_size=1, source="espn player_games") for r in rows]
                    ser = R.time_series(sport=SPORT, metric_id=mid, entity_id=_player_pid(n), entity_type="PLAYER", x_axis="GAME",
                                        points=R.rolling(pts, 10), as_of=ctx.hist_as_of, run_id=ctx.run_id, generated_at=ctx.now,
                                        quality=ctx.q_player, unit=d.unit, rolling_window=10,
                                        links=[ctx.link("PLAYER", "entity_profile", reg[n]["full_name"], _player_pid(n), pp(n))])
                    ctx.docs.append(ser)
                    sers[n].append(_series_ref(ser))

    # Prop residuals (PARTIAL), de-laddered, T-30m.
    prop_rows: dict[str, list[dict]] = {fam: [] for fam, _, _ in PROP_FAMILIES}
    for r in inp.market_rows:
        if r["horizon"] == MARKET_HORIZON and r["family"] in prop_rows and r["player_id"] in wanted_set:
            prop_rows[r["family"]].append(dict(r, _entity=r["player_id"]))
    prop_log: dict[int, list[list]] = {}
    for d, (fam, stat, _label) in zip(PLAYER_PROP, PROP_FAMILIES):
        dl = _delaldered(prop_rows[fam])
        per: dict[int, list[dict]] = {}
        for (ent, _g), r in dl.items():
            per.setdefault(ent, []).append(r)
        if not per:
            continue
        mid = ctx.metric(d, entity="PLAYER", quality=ctx.q_market, source="data/research/market_table.parquet",
                         supports=R.supports(), comparison=None, windows=["SEASON"], splits=[],
                         hist_start=min((r["tip_utc"] for r in prop_rows[fam]), default=None), freshness="STALE",
                         update="manual Kalshi history pull", limitations=[A_HISTORY_MKT, A_CANDLES, A_REGISTRY],
                         related=[ids.metric_id(SPORT, f"player_{stat}")])
        for n, rows in per.items():
            rows = sorted(rows, key=lambda r: (r["tip_utc"], r["ticker"]))
            obs[n].append(_obs(ctx, mid, _player_pid(n), "PLAYER", _mean([r["outcome"] - r["p_market"] for r in rows]), R.window("SEASON"),
                               source="market_table", status="PARTIAL", unit=d.unit, sample=len(rows), season=ctx.season,
                               extensions={"mean_implied": _mean([r["p_market"] for r in rows]),
                                           "yes_rate": _mean([r["outcome"] for r in rows])}))
            for r in rows:
                prop_log.setdefault(n, []).append([r["tip_utc"], ctx.event_by_game.get(r["game_id"]) or _evt(r["game_id"]), stat,
                                                   r["ticker"], r["threshold"], r["p_market"],
                                                   _cents(r["exec_yes_cents"]), r["outcome"]])

    profiles = {}
    for n in wanted:
        rec = reg[n]
        pid = _player_pid(n)
        last_team = by_player[n][-1]["team_id"] if by_player.get(n) else None
        tid = cur_team.get(n, last_team)
        team = ctx.teams.get(tid) if tid is not None else None
        rows_all = by_player.get(n, [])
        hist = [_game_ref(ctx, dict(r, won=r["team_pts"] > r["opp_pts"], pts=r["team_pts"])) for r in rows_all[-PLAYER_GAME_REFS:]]
        upcoming = _upcoming_refs(ctx, _team_pid(tid)) if team else []
        avail = [_availability(ctx, r) for r in inp.injuries if r.get("player_name_raw") and _norm(r["player_name_raw"]) == _norm(rec["full_name"])
                 and (r.get("team_id") in (None, tid))]
        log_cols = ["date_et", "event_id", "season", "season_type", "team", "opp", "home", "started", "played", "dnp_reason",
                    "min", "pts", "reb", "ast", "fg3m", "stl", "blk", "tov", "fgm", "fga", "fg3a", "ftm", "fta", "oreb", "dreb",
                    "pf", "plus_minus"]
        log_rows = []
        for r in rows_all[-SERIES_CAP:]:
            tm, op = ctx.teams.get(r["team_id"]), ctx.teams.get(r["opp_team_id"])
            log_rows.append([r["game_date_et"], ctx.event_by_game.get(r["game_id"]) or _evt(r["game_id"]), r["season"], r["season_type"],
                             tm.tricode if tm else str(r["team_id"]), op.tricode if op else str(r["opp_team_id"]), bool(r["home"]),
                             bool(r["started"]), bool(r["played"]), r["dnp_reason"], r["minutes"], r["pts"], r["reb"], r["ast"],
                             r["fg3m"], r["stl"], r["blk"], r["tov"], r["fgm"], r["fga"], r["fg3a"], r["ftm"], r["fta"], r["oreb"],
                             r["dreb"], r["pf"], r["plus_minus"]])
        links = [ctx.link("CAPABILITIES", "capability_manifest", "capabilities", None, R.app_path(R.CAPABILITIES_NAME))]
        if team:
            links.append(ctx.link("TEAM", "entity_profile", team.name, _team_pid(tid), R.team_path(_team_pid(tid))))
        links += [ctx.link("EVENT", "event_research", f"next: {g['opponent_name']}", g["event_id"], g["path"]) for g in upcoming]
        mk = [R.market_ref(m) for m in inp.markets if m.get("player_id") == pid]
        mk_ids = {m["market_id"] for m in mk}
        profiles[pid] = dict(
            pid=pid, nba_id=n, rec=rec, team_id=tid, position=position.get(n), obs=obs[n], splits=splits[n], refs=refs[n],
            sers=sers[n], games=hist + upcoming, links=links, markets=mk, availability=avail,
            projections=[_proj_ref(ctx, mp) for mp in inp.model_prices if mp["market_id"] in mk_ids],
            game_log={"columns": log_cols, "rows": log_rows, "source": "data/history/espn/player_games_*.parquet",
                      "quality_status": "PARTIAL", "coverage": f"last {SERIES_CAP} team games with a box-score row, DNP rows included"},
            prop_log={"columns": ["tip_utc", "event_id", "stat", "ticker", "line", "mid_t30m", "exec_yes_t30m", "outcome"],
                      "rows": prop_log.get(n, [])[-4 * SERIES_CAP:],
                      "source": "data/research/market_table.parquet (one line per player-game, nearest 50c)",
                      "quality_status": "PARTIAL", "limitations": [A_HISTORY_MKT]} if prop_log.get(n) else None)
    return profiles


# ---------------------------------------------------------------------------------------- events
def _distributions(ctx: _Ctx, ev: dict, gid: str, metric_ids: set[str]) -> tuple[list[dict], dict | None, list[str]]:
    """Slate packet quantiles for this game (RESEARCH), the slate's point projection, and gating notes."""
    pk = ctx.inp.packet or {}
    game = next((g for g in pk.get("games", []) if (g.get("game") or {}).get("game_id") == gid), None)
    if game is None:
        return [], None, []
    slate = ctx.inp.slate or {}
    sg = next((g for g in slate.get("games", []) if g.get("game_id") == gid), {})
    gen = slate.get("generated_at_utc") or ctx.inp.manifest.get("generated_at")
    n_sims = sg.get("n_sims")
    sd = {"margin": sg.get("margin_sd"), "total": sg.get("total_sd")}
    out = []
    sim = game.get("sim") or {}
    for key in ("margin", "total", "home_pts", "away_pts", "first_half_total", "first_quarter_total"):
        q = sim.get(key)
        if not isinstance(q, dict):
            continue
        out.append({"market_id": None, "metric_id": None, "entity_id": None, "label": f"game {key} (home perspective)" if key == "margin" else f"game {key}",
                    "quantiles": {k: float(v) for k, v in sorted(q.items()) if k.startswith("q") and v is not None},
                    "mean": _f(q.get("mean")), "stdev": _f(sd.get(key)), "samples": n_sims, "run_id": None, "generated_at": c_time.to_iso(gen),
                    "source": "slates/latest/packet.json games[].sim", "quality_status": "RESEARCH"})
    stat_metric = {"pts": "player_pts", "min": "player_min", "reb": "player_reb", "ast": "player_ast", "fg3m": "player_fg3m"}
    regs = {p["nba_id"] for p in ctx.inp.registry_players}
    for side in ("home", "away"):
        for p in (game.get(side) or {}).get("players", []):
            pid = _player_pid(p["nba_id"]) if p.get("nba_id") is not None and p["nba_id"] in regs else None
            for stat, q in sorted((p.get("sim") or {}).items()):
                if not isinstance(q, dict) or stat not in stat_metric:
                    continue
                mid = ids.metric_id(SPORT, stat_metric[stat]) if stat in stat_metric else None
                out.append({"market_id": None, "metric_id": mid if mid in metric_ids else None, "entity_id": pid,
                            "label": f"{p.get('name')} {stat}", "mean": _f(q.get("mean")), "stdev": None, "samples": n_sims,
                            "quantiles": {k: float(v) for k, v in sorted(q.items()) if k.startswith("q") and v is not None},
                            "run_id": None, "generated_at": c_time.to_iso(gen), "source": "slates/latest/packet.json players[].sim",
                            "quality_status": "RESEARCH"})
    raw = {k: sg.get(k) for k in ("p_home_win", "margin_mean", "margin_sd", "total_mean", "total_sd", "home_pts_mean",
                                  "away_pts_mean", "ot_rate", "n_sims", "converged", "inputs_trusted", "input_reasons")}
    raw.update({"generated_at": c_time.to_iso(gen), "model_version": slate.get("model_version"), "quality_status": "RESEARCH",
                "home_params": sg.get("home_params"), "away_params": sg.get("away_params"),
                "source": "slates/latest/slate.json games[]"})
    notes = []
    if sg.get("inputs_trusted") is False:
        notes.append("Projection inputs NOT trusted (gate CANNOT_TRUST_INPUTS): " + "; ".join(sg.get("input_reasons") or []))
    notes.append("Projection quality: " + A_DEFECT)
    return out, raw, notes


def _verdict(ctx: _Ctx) -> tuple[str | None, dict | None]:
    ex = ctx.inp.exhibit
    if not isinstance(ex, dict):
        return None, None
    fams = {k: v for k, v in ex.items() if k != "overall" and isinstance(v, dict)}
    table = {}
    beats = 0
    for fam, v in sorted(fams.items()):
        oos = v.get("oos") or {}
        mk, mo, hy = (oos.get("market_raw") or {}), (oos.get("data_only") or {}), (oos.get("hybrid") or {})
        table[fam] = {"n_oos": v.get("n_oos"), "market_log_loss": mk.get("log_loss"), "data_only_log_loss": mo.get("log_loss"),
                      "hybrid_log_loss": hy.get("log_loss"), "hybrid_beats_calibrated_market": v.get("hybrid_beats_calibrated_market")}
        if mk.get("log_loss") is not None and mo.get("log_loss") is not None and mk["log_loss"] < mo["log_loss"]:
            beats += 1
    verdict = (f"Model-vs-market (docs/research/market_vs_model.json, out-of-sample walk-forward): the raw Kalshi price has lower "
               f"log loss than the model (DATA_ONLY) in {beats} of {len(table)} families"
               + (f" -- {A_VERDICT}." if beats == len(table) == 8 else ".")
               + " Every NBA family is RESEARCH authority.")
    return verdict, {"families": table, "source": "docs/research/market_vs_model.json", "verdict": verdict, "quality_status": "RESEARCH"}


def _event_tickers_by_event(ctx: _Ctx) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for m in ctx.inp.markets:
        if m.get("event_id") in ctx.v1_events:
            out.setdefault(m["event_id"], []).append(m)
    return out


def _build_events(ctx: _Ctx, team_profiles: dict[str, dict], player_profiles: dict[str, dict]) -> list[str]:
    inp = ctx.inp
    names = {mid: m["name"] for mid, m in ctx.metrics.items()}
    matchup_slugs = ["team_net_rtg", "team_off_rtg", "team_def_rtg", "team_pts", "team_opp_pts", "team_total", "team_possessions",
                     "team_win_pct", "team_adj_net_ppp", "team_sos_opp_net_rtg", "team_mkt_ml_implied_win_prob"]
    by_event = _event_tickers_by_event(ctx)
    verdict, exhibit = _verdict(ctx)
    preds: dict[str, list[dict]] = {}
    for r in inp.predictions:
        preds.setdefault(r["ticker"], []).append(r)
    q_run = R.quality(status="RESEARCH", source="predictions ledger (data-archive)", generated_at=ctx.now, production=True,
                      data_as_of=max((r["predicted_at_utc"] for r in inp.predictions), default=None),
                      methodology_version=METHODOLOGY_VERSION, coverage=f"{len({r['_run_id'] for r in inp.predictions if r.get('_run_id')})} run(s)",
                      limitations=[A_PROJ, A_DEFECT])
    q_live = R.quality(status="PARTIAL", source="data-archive kalshi/markets checkpoints + deltas (archive.reconstruct)",
                       generated_at=ctx.now, production=True, data_as_of=ctx.as_of, methodology_version=METHODOLOGY_VERSION,
                       coverage=f"{inp.board_ticks} board ticks", limitations=[A_LIVE, A_PRICES,
                       "consecutive identical observations are collapsed: the first, every change and the latest are kept"])
    q_live_empty = R.quality(status="UNAVAILABLE", source="data-archive kalshi/markets", generated_at=ctx.now, production=True,
                             data_as_of=ctx.as_of, limitations=["no captured market of this event yet"])
    q_event = R.quality(status="PARTIAL", source="v1 app export + data/history + data-archive", generated_at=ctx.now, production=True,
                        data_as_of=ctx.as_of, methodology_version=METHODOLOGY_VERSION, coverage="v1 events (10-day schedule window)",
                        limitations=[A_PRICES, A_INJURIES, A_DEFECT, "team evidence is the most recent stored season; the "
                                     "current season has no games in the history yet"])
    if ctx.metrics.get(ids.metric_id(SPORT, MODEL_P.slug)) is None and preds:
        ctx.metric(MODEL_P, entity="MARKET", quality=q_run, source="data-archive predictions", supports=R.supports(time_series=True),
                   comparison=None, windows=["RUN"], splits=[], hist_start=min(r["predicted_at_utc"] for r in inp.predictions),
                   freshness="FRESH", update="per simulate run", limitations=[A_PROJ, A_DEFECT])
    eids = []
    metric_ids = set(ctx.metrics)
    for eid, ev in sorted(ctx.v1_events.items(), key=lambda kv: (kv[1]["start_time_utc"], kv[0])):
        gid = ev["source_ids"].get("nba_edge_game_id")
        home, away = ev.get("home_participant"), ev.get("away_participant")
        parts = []
        for p in ev["participants"]:
            ha = "HOME" if p["participant_id"] == home else ("AWAY" if p["participant_id"] == away else None)
            parts.append({"participant_id": p["participant_id"], "display_name": p["display_name"], "home_away": ha,
                          "path": R.team_path(p["participant_id"]) if p["participant_id"] in team_profiles else None})
        matchup = []
        if home in team_profiles and away in team_profiles:
            hobs = {o["metric_id"]: o for o in team_profiles[home]["obs"] if o["window"]["kind"] != "LAST_N"}
            aobs = {o["metric_id"]: o for o in team_profiles[away]["obs"] if o["window"]["kind"] != "LAST_N"}
            for slug in matchup_slugs:
                mid = ids.metric_id(SPORT, slug)
                if mid in hobs or mid in aobs:
                    matchup.append({"metric_id": mid, "name": names[mid], "home": hobs.get(mid), "away": aobs.get(mid),
                                    "note": None if ctx.metrics[mid]["quality"]["status"] != "RESEARCH" else "RESEARCH"})
        team_ids = {p["participant_id"] for p in ev["participants"]}
        players = sorted(({"participant_id": pp["pid"], "display_name": pp["rec"]["full_name"], "team_id": _team_pid(pp["team_id"]),
                           "role": pp["position"], "path": R.player_path(pp["pid"])}
                          for pp in player_profiles.values() if pp["team_id"] is not None and _team_pid(pp["team_id"]) in team_ids),
                         key=lambda x: (x["team_id"], x["display_name"]))
        mkts = sorted(by_event.get(eid, []), key=lambda m: (m["market_family"], m["kalshi_ticker"]))
        mk_ids = {m["market_id"] for m in mkts}
        dists, raw, gate_notes = _distributions(ctx, ev, gid, metric_ids)
        inj_teams = {int(p["source_ids"].get("nba_team_id")) for p in ev["participants"] if p["source_ids"].get("nba_team_id")}
        injuries = [_availability(ctx, r, eid) for r in sorted(inp.injuries, key=lambda r: (r.get("team_id") or 0, r.get("player_name_raw") or ""))
                    if r.get("team_id") in inj_teams]
        notes = []
        if verdict:
            notes.append(verdict)
        notes += gate_notes
        if not inp.model_prices:
            notes.append("No model prices in this publication (" + A_DEFECT.split(":")[0] + ").")
        if inp.injuries_official_missing:
            notes.append("Injuries are ESPN's feed only: the official NBA injury report has never been captured.")
        notes.append("No lineups or confirmed starters exist in this repository (" + A_LINEUPS.split(";")[0] + ").")
        if ev.get("competition") == "preseason":
            notes.append("Preseason game: rotations/minutes are not representative.")
        links = [ctx.link("MARKET_HISTORY", "market_history", "captured price path", eid, R.market_history_path(eid)),
                 ctx.link("CAPABILITIES", "capability_manifest", "capabilities", None, R.app_path(R.CAPABILITIES_NAME))]
        for m in mkts:
            if m["kalshi_ticker"] in preds:
                sid = ids.series_id(SPORT, ids.metric_id(SPORT, MODEL_P.slug), m["market_id"], "RUN", None)
                links.append(ctx.link("SERIES", "time_series", f"model probability per run: {m['kalshi_ticker']}", sid, R.series_path(sid)))
                pts = [R.point(x=str(r["predicted_at_utc"]), t=r["predicted_at_utc"], value=r.get("p_data_only"), quality_status="RESEARCH",
                               event_id=eid, sample_size=r.get("n_sims"), source=f"predictions gate={r.get('gate')}",
                               path=R.event_path(eid)) for r in preds[m["kalshi_ticker"]]]
                ctx.docs.append(R.time_series(sport=SPORT, metric_id=ids.metric_id(SPORT, MODEL_P.slug), entity_id=m["market_id"],
                                              entity_type="MARKET", x_axis="RUN", points=pts, as_of=ctx.as_of, run_id=ctx.run_id,
                                              generated_at=ctx.now, quality=q_run, unit="probability",
                                              links=[ctx.link("EVENT_RESEARCH", "event_research", "event", eid, R.event_path(eid))]))
        venue = {"arena": ev.get("venue"), "neutral_site": (ev.get("extensions") or {}).get("neutral_site"),
                 "source": "context/schedule (ESPN scoreboard)", "effects": None} if ev.get("venue") else None
        ext: dict[str, Any] = {"model_vs_market": exhibit} if exhibit else {}
        if raw:
            ext["raw_projection"] = raw
        doc = R.event_research(
            sport=SPORT, run_id=ctx.run_id, generated_at=ctx.now, event=ev, quality=q_event, participants=parts, matchup=matchup,
            players=players, projections=[_proj_ref(ctx, mp) for mp in inp.model_prices if mp["market_id"] in mk_ids],
            distributions=dists, markets=[R.market_ref(m) for m in mkts], market_history_path=R.market_history_path(eid),
            context={"injuries": injuries, "lineups": [], "weather": None, "venue": venue, "notes": notes},
            wagers=sorted(w["wager_id"] for w in inp.wagers if w.get("market_id") in mk_ids), links=links, extensions=ext)
        ctx.docs.append(doc)
        series = []
        for m in mkts:
            pts = _collapse(inp.price_paths.get(m["kalshi_ticker"], []))
            if pts:
                series.append({"market_id": m["market_id"], "kalshi_ticker": m["kalshi_ticker"],
                               "points": [R.price_point(**p) for p in pts]})
        ctx.docs.append(R.market_history(sport=SPORT, run_id=ctx.run_id, generated_at=ctx.now, event_id=eid, as_of=ctx.as_of,
                                         series=series, quality=q_live if series else q_live_empty,
                                         links=[ctx.link("EVENT_RESEARCH", "event_research", "event", eid, R.event_path(eid))]))
        eids.append(eid)
    return eids


def _collapse(points: list[dict]) -> list[dict]:
    """Keep the first observation, every change, and the latest."""
    out: list[dict] = []
    key = lambda p: (p["yes_bid"], p["yes_ask"], p["last_price"], p["volume"], p["open_interest"])  # noqa: E731
    pts = sorted(points, key=lambda p: p["captured_at"])
    for i, p in enumerate(pts):
        if not out or key(p) != key(out[-1]) or i == len(pts) - 1:
            out.append(p)
    return out


# ------------------------------------------------------------------------------------- assembly
def _team_profile_doc(ctx: _Ctx, p: dict, players: list[dict]) -> dict:
    team = ctx.teams[p["team_id"]]
    avail = [_availability(ctx, r) for r in sorted(ctx.inp.injuries, key=lambda r: r.get("player_name_raw") or "")
             if r.get("team_id") == p["team_id"]]
    ext = {"game_log": p["game_log"], "notes": [A_SCHEDULE]}
    if p["market_log"]:
        ext["market_log"] = p["market_log"]
    return R.entity_profile(
        sport=SPORT, run_id=ctx.run_id, generated_at=ctx.now, entity=ctx.team_part[p["team_id"]], entity_type="TEAM", quality=ctx.q_box,
        season=ctx.season, league="NBA", metrics=p["obs"], splits={"home_away": p["splits"]} if p["splits"] else {},
        series=p["sers"], rankings=p["refs"], games=p["games"], players=players, opponents=p["opponents"], markets=p["markets"],
        projections=p["projections"], availability=avail, links=p["links"],
        extensions=dict(ext, tricode=team.tricode))


def _player_profile_doc(ctx: _Ctx, p: dict) -> dict:
    rec = p["rec"]
    team = ctx.teams.get(p["team_id"]) if p["team_id"] is not None else None
    entity = build.participant(sport=SPORT, participant_type="PLAYER", source="nba_player_id", source_id=rec["nba_id"],
                               display_name=rec["full_name"], short_name=None,
                               source_ids={"espn_athlete_id": rec["espn"], "kalshi_player_uuid": rec["kalshi_uuid"]},
                               metadata={"position": p["position"], "registry_active": rec["active"],
                                         "current_team_source": "context/rosters" if ctx.inp.rosters else "last box-score row"})
    ext = {"game_log": p["game_log"]}
    if p["prop_log"]:
        ext["prop_log"] = p["prop_log"]
    return R.entity_profile(
        sport=SPORT, run_id=ctx.run_id, generated_at=ctx.now, entity=entity, entity_type="PLAYER", quality=ctx.q_player,
        season=ctx.season, league="NBA",
        team={"participant_id": _team_pid(team.team_id), "display_name": team.name, "short_name": team.tricode,
              "path": R.team_path(_team_pid(team.team_id))} if team else None,
        metrics=p["obs"], splits={"home_away": p["splits"]} if p["splits"] else {}, series=p["sers"], rankings=p["refs"],
        games=p["games"], markets=p["markets"], projections=p["projections"], availability=p["availability"], links=p["links"],
        extensions=ext)


def _capabilities(ctx: _Ctx, *, team_path: str, player_path: str | None, event_path: str | None, mh_paths: list[str],
                  mh_coverage: str, mh_since: str | None,
                  ranking_path: str, series_path: str, player_ranking_path: str | None, injuries: bool, dists: bool,
                  raw_proj: bool, adj: bool, shots: bool, model_series: bool, hist_mh: bool, market_metrics: bool,
                  props: bool, team_props: bool) -> dict:
    inp = ctx.inp
    C = R.capability
    met = lambda *slugs: [ids.metric_id(SPORT, s) for s in slugs if ids.metric_id(SPORT, s) in ctx.metrics]  # noqa: E731
    first_season = min(r["game_date_et"] for r in inp.team_games)
    cov3 = f"{len(inp.team_games):,} team-game rows, 3 seasons ({first_season}..{max(r['game_date_et'] for r in inp.team_games)})"
    n_players = sum(1 for d in ctx.docs if d["kind"] == "entity_profile" and d["entity_type"] == "PLAYER")
    p_first = min((r["game_date_et"] for r in inp.player_games), default=None)
    cov_p = f"{n_players} profiled players; {len(inp.player_games):,} player-game rows stored ({p_first}..)"
    fam_since = {}
    fam_n: dict[str, int] = {}
    for r in inp.market_rows:
        if r["horizon"] == MARKET_HORIZON:
            fam_since[r["family"]] = min(fam_since.get(r["family"], r["tip_utc"]), r["tip_utc"])
            fam_n[r["family"]] = fam_n.get(r["family"], 0) + 1
    ev_markets = [m for m in inp.markets if m.get("event_id") in ctx.v1_events]
    n_kind = lambda k: sum(1 for d in ctx.docs if d["kind"] == k)  # noqa: E731
    season_start = min((r["game_date_et"] for r in inp.team_games if r["season"] == ctx.season), default=None)
    caps = [
        C(capability="team_profiles", status="PARTIAL", summary=f"{len(ctx.teams)} team profiles: windowed box metrics, splits, "
          "rankings, 3-season game logs, moneyline horizon log", entity_types=["TEAM"], evidence=[team_path],
          limitations=[A_SCHEDULE, A_TEAM_METRICS], coverage=cov3, since=first_season),
        C(capability="team_metrics", status="PARTIAL", summary="pace/efficiency/scoring per game, derived on export from stored rows",
          entity_types=["TEAM"], evidence=[team_path, ranking_path], limitations=[A_TEAM_METRICS, A_SCHEDULE], coverage=cov3,
          since=first_season, metrics=met(*("team_" + d.slug for d in TEAM_BOX)), windows=["SEASON", "L10", "L5", "L3"]),
        C(capability="team_game_logs", status="PARTIAL", summary="every stored team game (q1-q4, OT, possessions, margin, total) "
          "in each team profile's extensions.game_log", entity_types=["TEAM"], evidence=[team_path],
          limitations=[A_SCHEDULE], coverage=cov3, since=first_season),
        C(capability="historical_results", status="PARTIAL", summary="final scores and W/L on every game reference and game-log row",
          entity_types=["TEAM"], evidence=[team_path], limitations=[A_SCHEDULE], coverage=cov3, since=first_season),
        C(capability="opponents", status="PARTIAL", summary="opponent id on every game reference; opponents list per team",
          entity_types=["TEAM"], evidence=[team_path], limitations=[A_SCHEDULE], coverage=cov3, since=first_season),
        C(capability="recent_form_windows", status="PARTIAL", summary="L10/L5/L3 over each entity's last non-preseason games, derived",
          entity_types=["TEAM", "PLAYER"], evidence=[team_path], limitations=[A_FORM + " (derived here)"], windows=["L10", "L5", "L3"],
          metrics=met("team_net_rtg", "team_pts", "player_pts", "player_min")),
        C(capability="situational_splits", status="PARTIAL", summary="home/away splits of the season window", entity_types=["TEAM", "PLAYER"],
          evidence=[team_path], limitations=[A_SPLITS + " (home/away derived here; season_type is labelled in the game logs)"],
          splits=["home_away"]),
        C(capability="schedule_strength", status="PARTIAL", summary="mean opponent season net rating", entity_types=["TEAM"],
          evidence=[team_path], limitations=[A_SOS + " in the repo; this is arithmetic over the published net ratings"],
          metrics=met("team_sos_opp_net_rtg")),
        C(capability="rankings", status="PARTIAL", summary=f"{len(ctx.rankings)} rankings over full universes (30 teams; players "
          f"with >= {PLAYER_RANK_MIN_GAMES} games)", entity_types=["TEAM", "PLAYER"], evidence=[ranking_path],
          limitations=["rankings inherit the PARTIAL/RESEARCH status of their metric", A_SCHEDULE],
          coverage=f"{len(ctx.rankings)} rankings", since=season_start),
        C(capability="time_series", status="PARTIAL", summary="per-game team and player series (points link event and opponent), "
          "per-run model probability series", entity_types=["TEAM", "PLAYER", "MARKET"], evidence=[series_path],
          limitations=[f"capped at the last {SERIES_CAP} games", A_SCHEDULE], coverage=f"{n_kind('time_series')} series",
          since=min((d["points"][0]["t"] for d in ctx.docs if d["kind"] == "time_series" and d["points"]), default=None)),
        C(capability="comparisons", status="PARTIAL", summary="side-by-side home/away observations of the same metric in each event",
          entity_types=["MATCHUP"], evidence=[event_path] if event_path else [team_path],
          limitations=["the current season has no games in the history; comparisons use the latest stored season"]),
        C(capability="advanced_stats", status="PARTIAL", summary="possession-based ratings (stored possessions estimate)"
          + ("; shot-zone shares (RESEARCH)" if shots else ""), entity_types=["TEAM"], evidence=[team_path],
          limitations=["basketball analogues only: no on/off, RAPM rejected (`docs/research/INJURY_IMPACT.md`)"],
          metrics=met("team_off_rtg", "team_def_rtg", "team_net_rtg", *(f"team_shot_share_{z}" for z in SHOT_ZONES))),
        C(capability="matchup_metrics", status="RESEARCH", summary="MATCHUP_AWARE_V2 effects are neutral; event matchup rows only "
          "juxtapose the two teams' published metrics", reasons=[A_MATCHUP], limitations=[A_MATCHUP]),
        C(capability="lineups", status="UNAVAILABLE", summary="no lineup, stint, on/off or tracking data", reasons=[A_LINEUPS]),
        C(capability="weather", status="UNAVAILABLE", summary="indoor sport; nothing in repo", reasons=["indoor sport; nothing in repo"]),
        C(capability="venue_effects", status="UNAVAILABLE", summary="arena name and neutral_site only (event context.venue); no "
          "venue effect is estimated", reasons=["Venue / park effects: PARTIAL (field only) -- no venue table; history has `home` only; "
                                                "audit §10 marks venue effects UNAVAILABLE"]),
        C(capability="clv", status="UNAVAILABLE", summary="evaluate has never run; CLV is not computed",
          reasons=["`evaluation/clv.py` functions exist; `evaluate` never ran; app export `clv.available=false`"]),
        C(capability="wager_history", status="UNAVAILABLE", summary="accounting-data wagers/settlements are empty",
          reasons=["`accounting-data` wagers/settlements 0 bytes"]),
    ]
    if player_path:
        caps += [
            C(capability="player_profiles", status="PARTIAL", summary="identity-registry players who played this season or appear "
              "in current markets", entity_types=["PLAYER"], evidence=[player_path], limitations=[A_REGISTRY, A_SCHEDULE],
              coverage=cov_p, since=p_first),
            C(capability="player_metrics", status="PARTIAL", summary="per-game box averages and shooting rates", entity_types=["PLAYER"],
              evidence=[player_path] + ([player_ranking_path] if player_ranking_path else []), limitations=[A_PLAYER_METRICS, A_REGISTRY],
              metrics=met(*("player_" + d.slug for d in PLAYER_BOX)), windows=["SEASON", "L10", "L5", "L3"], coverage=cov_p,
              since=p_first),
            C(capability="player_game_logs", status="PARTIAL", summary=f"last {SERIES_CAP} box-score rows per profiled player "
              "(minutes, box, started/played/DNP reason, plus_minus) in extensions.game_log", entity_types=["PLAYER"],
              evidence=[player_path], limitations=[A_REGISTRY, f"capped at the last {SERIES_CAP} games"], coverage=cov_p, since=p_first),
            C(capability="usage", status="PARTIAL", summary="minutes, FGA, FTA per game", entity_types=["PLAYER"], evidence=[player_path],
              limitations=[A_USAGE], metrics=met("player_min", "player_fga", "player_fta"), coverage=cov_p, since=p_first),
        ]
    else:
        caps += [C(capability=c, status="UNAVAILABLE", summary="no registry player in this publication", reasons=["no player rows"])
                 for c in ("player_profiles", "player_metrics", "player_game_logs", "usage")]
    caps.append(C(capability="opponent_adjustment", status="RESEARCH", summary="features.build.opponent_adjusted_ratings at one cutoff",
                  entity_types=["TEAM"], evidence=[team_path] if adj else [], limitations=[A_ADJ, A_ADJ_TEST],
                  metrics=met("team_adj_off_ppp", "team_adj_def_ppp", "team_adj_net_ppp"))
                if adj else C(capability="opponent_adjustment", status="UNAVAILABLE", summary="no history", reasons=["no team history"]))
    caps.append(C(capability="injuries", status="PARTIAL", summary="ESPN injury feed (latest snapshot) in event context and profiles",
                  entity_types=["TEAM", "PLAYER"], evidence=[event_path or team_path], limitations=[A_INJURIES],
                  coverage=f"latest snapshot {inp.injuries_at}: {len(inp.injuries)} rows", since=inp.injuries_at)
                if injuries else C(capability="injuries", status="UNAVAILABLE", summary="no injury snapshot in this archive",
                                   reasons=["no context/injuries partition"]))
    caps.append(C(capability="projection_distributions", status="RESEARCH", summary="slate packet quantiles (game and player)",
                  entity_types=["EVENT", "PLAYER"], evidence=[event_path] if event_path else [], limitations=[A_PROJ, A_DEFECT])
                if dists else C(capability="projection_distributions", status="UNAVAILABLE",
                                summary="no slate packet for a published event", reasons=["no slates/latest/packet.json for these events"]))
    caps.append(C(capability="raw_projections", status="RESEARCH", summary="slate point projections (p_home_win, margin/total means) "
                  "and per-run model probabilities", entity_types=["EVENT", "MARKET"], evidence=[event_path] if event_path else [],
                  limitations=[A_PROJ, A_DEFECT])
                if (raw_proj or model_series) else C(capability="raw_projections", status="UNAVAILABLE", summary="no slate yet",
                                                      reasons=["no slate for a published event"]))
    caps.append(C(capability="market_prices", status="PARTIAL", summary="every v1 market of each event (bid/ask, captured_at)",
                  entity_types=["MARKET"], evidence=[event_path] if event_path else [team_path], limitations=[A_PRICES],
                  coverage=f"{len(ev_markets)} markets on {len(ctx.v1_events)} v1 events",
                  since=min((m["captured_at"] for m in ev_markets if m.get("captured_at")), default=None)))
    caps.append(C(capability="market_price_history", status="PARTIAL", summary="captured price path per v1 event (archive ticks)"
                  + (f"; hourly moneyline candles for each team's last {CANDLE_GAMES_PER_TEAM} games" if hist_mh else ""),
                  entity_types=["MARKET"], evidence=mh_paths, limitations=[A_LIVE, A_CANDLES,
                  f"historical candles published for each team's last {CANDLE_GAMES_PER_TEAM} games only",
                  "consecutive identical archive observations are collapsed (first, every change, latest kept)"],
                  coverage=mh_coverage, since=mh_since))
    caps.append(C(capability="game_markets", status="PARTIAL", summary="current game markets per event; settled moneyline/spread/total "
                  "residuals and the moneyline horizon log per team", entity_types=["TEAM", "MARKET"],
                  evidence=[event_path or team_path] + ([team_path] if market_metrics else []), limitations=[A_HISTORY_MKT],
                  metrics=met("team_mkt_ml_implied_win_prob", "team_mkt_ml_win_minus_implied", "team_mkt_spread_cover_minus_implied",
                              "team_mkt_total_over_minus_implied"),
                  coverage=", ".join(f"{f} {fam_n.get(f, 0):,}" for f in ("game_winner", "game_spread", "game_total"))
                  + f" settled rows at {MARKET_HORIZON}", since=fam_since.get("game_winner")))
    caps.append(C(capability="team_props", status="PARTIAL", summary="settled team-total residual per team", entity_types=["TEAM"],
                  evidence=[team_path], limitations=[A_HISTORY_MKT], metrics=met("team_mkt_team_total_over_minus_implied"),
                  coverage=f"team_total {fam_n.get('team_total', 0):,} settled rows at {MARKET_HORIZON}", since=fam_since.get("team_total"))
                if team_props else C(capability="team_props", status="UNAVAILABLE", summary="no team-total rows", reasons=["none stored"]))
    caps.append(C(capability="player_props", status="PARTIAL", summary="settled prop residuals and a per-player prop log "
                  "(historical); model prop prices are RESEARCH and absent", entity_types=["PLAYER"], evidence=[player_path] if player_path else [],
                  limitations=[A_HISTORY_MKT, "PRA series empty (0 rows)", A_REGISTRY],
                  metrics=met(*(f"player_prop_{s}_over_minus_implied" for _, s, _ in PROP_FAMILIES)),
                  coverage=", ".join(f"{f} {fam_n.get(f, 0):,}" for f, _, _ in PROP_FAMILIES) + f" settled rows at {MARKET_HORIZON}",
                  since=min((fam_since[f] for f, _, _ in PROP_FAMILIES if f in fam_since), default=None))
                if (props and player_path) else C(capability="player_props", status="UNAVAILABLE", summary="no prop rows",
                                                  reasons=["no settled prop rows for profiled players"]))
    caps.append(C(capability="play_by_play", status="PARTIAL", summary="shooting plays only, aggregated to team zone shares (RESEARCH)",
                  entity_types=["TEAM"], evidence=[team_path], limitations=[A_PBP, A_SHOT_IDS],
                  metrics=met(*(f"team_shot_share_{z}" for z in SHOT_ZONES)),
                  coverage=f"{sum(z['fga'] for z in inp.shot_zones):,} located non-FT {ctx.season} regular-season shots aggregated")
                if shots else C(capability="play_by_play", status="UNAVAILABLE", summary="no shot events", reasons=["none stored"]))
    verdict, _ = _verdict(ctx)
    caps.append(C(capability="calibration", status="RESEARCH", summary="frozen one-off model-vs-market study, reproduced as each "
                  "event's extensions.model_vs_market", reasons=[verdict or "no exhibit"],
                  limitations=["one-off research output (docs/research/market_vs_model.json), not a scheduled evaluation"]))
    caps.append(C(capability="historical_accuracy", status="RESEARCH", summary=verdict or "research walk-forwards",
                  reasons=[A_ACCURACY], limitations=[A_ACCURACY, A_VERDICT]))
    caps.append(C(capability="event_research", status="PARTIAL", summary="one document per v1 event", entity_types=["EVENT"],
                  evidence=[event_path] if event_path else [], limitations=[A_PRICES, A_DEFECT],
                  coverage=f"{len(ctx.v1_events)} events", since=min((e["start_time_utc"] for e in inp.events), default=None))
                if event_path else C(capability="event_research", status="UNAVAILABLE", summary="no v1 events", reasons=["no events"]))
    caps.append(C(capability="search", status="PARTIAL", summary="teams, players, events, metrics and rankings",
                  evidence=[R.app_path(R.SEARCH_NAME)], limitations=["indexes the published (capped) entities only"],
                  coverage=f"{len(ctx.teams)} teams, {n_players} players, {len(ctx.v1_events)} events, {len(ctx.metrics)} metrics, "
                           f"{len(ctx.rankings)} rankings"))
    split_dims = [{"dimension": "home_away", "values": ["HOME", "AWAY"], "status": "PARTIAL"}]
    windows = [R.window("SEASON")] + [R.window("LAST_N", n=n) for n in FORM_WINDOWS]
    notes = [A_SCHEDULE, f"{A_DEFECT}", "Not published: lineups, confirmed starters, official injury report, CLV, wagers, "
             "settlements/evaluations, weather, venue effects, play-by-play beyond shots, PRA markets (0 rows), positive NBA person ids."]
    if verdict:
        notes.insert(0, verdict)
    return R.capability_manifest(sport=SPORT, run_id=ctx.run_id, generated_at=ctx.now, capabilities=caps, audit_date=AUDIT_DATE,
                                 split_dimensions=split_dims, windows=windows, notes=notes)


def build_explorer(inputs: ResearchInputs, *, run_id: str, generated_at: object) -> list[dict]:
    """Inputs in, explorer documents out (pure)."""
    now = c_time.to_iso(generated_at)
    ctx = _Ctx(inputs, run_id, now)
    team_profiles = _build_teams(ctx)
    player_profiles = _build_players(ctx)
    # Projection metric ids referenced by distributions must exist before events are built.
    event_ids = _build_events(ctx, team_profiles, player_profiles)

    players_by_team: dict[str, list[dict]] = {}
    for pp in player_profiles.values():
        if pp["team_id"] is not None:
            players_by_team.setdefault(_team_pid(pp["team_id"]), []).append(
                {"participant_id": pp["pid"], "display_name": pp["rec"]["full_name"], "role": pp["position"],
                 "path": R.player_path(pp["pid"])})
    for pid, p in sorted(team_profiles.items()):
        ctx.docs.append(_team_profile_doc(ctx, p, sorted(players_by_team.get(pid, []), key=lambda x: x["display_name"])))
    for _pid, p in sorted(player_profiles.items()):
        ctx.docs.append(_player_profile_doc(ctx, p))

    registry = R.metric_registry(sport=SPORT, run_id=run_id, generated_at=now, metrics=list(ctx.metrics.values()))
    first_team = sorted(team_profiles)[0]
    first_player = sorted(player_profiles)[0] if player_profiles else None
    rk_team = ctx.rankings[(ids.metric_id(SPORT, "team_net_rtg"), "SEASON")]
    rk_player = ctx.rankings.get((ids.metric_id(SPORT, "player_pts"), "SEASON"))
    ser = next(d for d in ctx.docs if d["kind"] == "time_series" and d["entity_id"] == first_team)
    mh_docs = [d for d in ctx.docs if d["kind"] == "market_history"]
    mh_live = [d for d in mh_docs if d["event_id"] in ctx.v1_events and d["series"]]
    mh_hist = [d for d in mh_docs if d["event_id"] not in ctx.v1_events]
    mh_paths = [R.market_history_path(d["event_id"]) for d in (mh_live[:1] + mh_hist[:1])] or \
        [R.market_history_path(d["event_id"]) for d in mh_docs[:1]]
    live_pts = [p for d in mh_live for s_ in d["series"] for p in s_["points"]]
    first_event = event_ids[0] if event_ids else None
    has_dist = any(d["kind"] == "event_research" and d["distributions"] for d in ctx.docs)
    has_raw = any(d["kind"] == "event_research" and d["extensions"].get("raw_projection") for d in ctx.docs)
    dist_event = next((d["event"]["event_id"] for d in ctx.docs if d["kind"] == "event_research" and d["distributions"]), first_event)
    caps = _capabilities(
        ctx, team_path=R.team_path(first_team), player_path=R.player_path(first_player) if first_player else None,
        event_path=R.event_path(dist_event) if dist_event else None, mh_paths=mh_paths,
        mh_coverage=(f"{inputs.board_ticks} archive board ticks -> {len(live_pts)} price points across "
                     f"{sum(len(d['series']) for d in mh_live)} tickers of {len(mh_live)} v1 events; hourly candles for "
                     f"{len(mh_hist)} historical games"),
        mh_since=min([p["captured_at"] for p in live_pts] + [p["captured_at"] for d in mh_hist for s_ in d["series"]
                                                              for p in s_["points"]], default=None),
        ranking_path=R.ranking_path(rk_team["ranking_id"]), series_path=R.series_path(ser["series_id"]),
        player_ranking_path=R.ranking_path(rk_player["ranking_id"]) if rk_player else None,
        injuries=bool(inputs.injuries), dists=has_dist, raw_proj=has_raw, adj=bool(inputs.adjusted), shots=bool(inputs.shot_zones),
        model_series=any(d["kind"] == "time_series" and d["x_axis"] == "RUN" for d in ctx.docs),
        hist_mh=any(ctx.hist_mh.values()), market_metrics=bool(inputs.market_rows),
        props=any(m.startswith("met_nba.player_prop_") for m in ctx.metrics),
        team_props=ids.metric_id(SPORT, "team_mkt_team_total_over_minus_implied") in ctx.metrics)

    entries = []
    for pid, p in sorted(team_profiles.items()):
        t = ctx.teams[p["team_id"]]
        entries.append(R.search_entry(id=pid, kind="TEAM", label=t.name, path=R.team_path(pid), sport=SPORT, secondary=t.tricode,
                                      aliases=[t.tricode, t.city, t.nickname, *t.alt_tricodes], league="NBA", season=ctx.season))
    for pid, p in sorted(player_profiles.items()):
        team = ctx.teams.get(p["team_id"]) if p["team_id"] is not None else None
        entries.append(R.search_entry(id=pid, kind="PLAYER", label=p["rec"]["full_name"], path=R.player_path(pid), sport=SPORT,
                                      secondary=team.tricode if team else None, team=team.name if team else None,
                                      position=p["position"], league="NBA", season=ctx.season))
    for eid in event_ids:
        ev = ctx.v1_events[eid]
        names = {x["participant_id"]: x for x in ev["participants"]}
        a, h = names.get(ev.get("away_participant")), names.get(ev.get("home_participant"))
        label = f"{a['display_name']} @ {h['display_name']}" if a and h else " vs ".join(x["display_name"] for x in ev["participants"])
        entries.append(R.search_entry(id=eid, kind="EVENT", label=label, path=R.event_path(eid), sport=SPORT,
                                      secondary=f"{c_time.to_date(ev['start_time_utc'])} {ev.get('competition') or ''}".strip(),
                                      aliases=[f"{a['short_name']} @ {h['short_name']}"] if a and h else [], league="NBA",
                                      season=ev.get("season")))
    for mid, m in sorted(ctx.metrics.items()):
        entries.append(R.search_entry(id=mid, kind="METRIC", label=m["name"], path=R.app_path(R.METRICS_NAME), sport=SPORT,
                                      secondary=m["entity_type"], aliases=[m["short_name"]]))
    for (mid, wl), rk in sorted(ctx.rankings.items()):
        entries.append(R.search_entry(id=rk["ranking_id"], kind="RANKING", label=f"{ctx.metrics[mid]['name']} ranking ({wl})",
                                      path=R.ranking_path(rk["ranking_id"]), sport=SPORT, secondary=rk["universe"]["label"]))
    search = R.search_index(sport=SPORT, run_id=run_id, generated_at=now, entries=entries)
    return ctx.docs + [registry, caps, search]


def index_quality(inputs: ResearchInputs, generated_at: object) -> dict:
    return R.quality(status="PARTIAL", source="nba-edge-finder data/history + data/research + data-archive + app/latest",
                     generated_at=generated_at, production=True, data_as_of=max(r["start_time_utc"] for r in inputs.team_games),
                     methodology_version=METHODOLOGY_VERSION, coverage="see capabilities.json",
                     limitations=[A_SCHEDULE, "explorer derived on export; see each document's quality"])


def explorer_as_of(inputs: ResearchInputs) -> str:
    stamps = [max(r["start_time_utc"] for r in inputs.team_games)]
    stamps += [m["captured_at"] for m in inputs.markets if m.get("captured_at")]
    stamps += [x for x in (inputs.rosters_at, inputs.injuries_at, inputs.manifest.get("generated_at")) if x]
    return max(c_time.to_iso(s) for s in stamps)


# ----------------------------------------------------------------------------------------- export
def export_explorer(app_root: Path, data_root: Path, *, history_root: Path | None = None, docs_root: Path | None = None,
                    now: object = None, commit_sha: str | None = None) -> dict:
    """Load, build and publish. ``now`` defaults to the v1 manifest's ``generated_at`` (the same publication)."""
    inputs = load_inputs(Path(app_root), Path(data_root), history_root, docs_root)
    run_id = inputs.manifest["run_id"]
    generated_at = c_time.to_iso(now) if now is not None else inputs.manifest["generated_at"]
    docs = build_explorer(inputs, run_id=run_id, generated_at=generated_at)
    return R.publish_explorer(app_root=Path(app_root), sport=SPORT, run_id=run_id, generated_at=generated_at, documents=docs,
                              quality=index_quality(inputs, generated_at), as_of=explorer_as_of(inputs),
                              commit_sha=commit_sha or inputs.manifest.get("commit_sha"), base_manifest_run_id=run_id,
                              windows=[R.window("SEASON")] + [R.window("LAST_N", n=n) for n in FORM_WINDOWS],
                              warnings=inputs.warnings)


def run(out: Path, data_root: Path, *, history_root: Path | None = None, docs_root: Path | None = None, now: object = None,
        commit_sha: str | None = None, min_interval_seconds: float = 0) -> int:
    """Build and publish; returns 0 on success (or when the refresh gate says not due), 1 on failure.

    ``min_interval_seconds > 0`` gates the rebuild with ``research.refresh_due``: the explorer is rebuilt only
    when missing, when the v1 events changed, or when it is at least that old (measured at ``now``, default the
    v1 manifest's ``generated_at``). A skipped run touches nothing under ``explorer/``."""
    if min_interval_seconds > 0:
        manifest = _read_json(Path(out) / "manifest.json")
        clock = now if now is not None else (manifest or {}).get("generated_at")
        if clock is not None:
            due, why = R.refresh_due(Path(out), now=clock, min_interval_seconds=min_interval_seconds)
            if not due:
                print(f"research_export: skipped ({why}); explorer left as published")
                return 0
            print(f"research_export: rebuilding ({why})")
    try:
        index = export_explorer(out, data_root, history_root=history_root, docs_root=docs_root, now=now, commit_sha=commit_sha)
    except Exception as exc:  # noqa: BLE001 - a research failure must never touch the v1 payload
        print(f"research_export: FAILED ({type(exc).__name__}: {str(exc)[:500]}); previous explorer left untouched", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 1
    sizes = R.tree_bytes(Path(out))
    print(f"research_export: published explorer for run {index['run_id']} to {Path(out) / R.EXPLORER_DIR} "
          f"({', '.join(f'{k}={v}' for k, v in index['counts'].items())}; bytes {sum(sizes.values()):,})")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Publish the Edge Finder research explorer (contract 1.1.0) beside app/latest.")
    ap.add_argument("--out", default=DEFAULT_OUT, help="app root that already holds the v1 export (default data/archive/app/latest)")
    ap.add_argument("--data-root", default=DEFAULT_DATA_ROOT, help="archive root: a checkout of data-archive")
    ap.add_argument("--history-root", default=DEFAULT_HISTORY_ROOT, help="the repository's data/ (history, research, identity)")
    ap.add_argument("--now", default=None, help="ISO-8601 UTC instant; default: the v1 manifest's generated_at")
    ap.add_argument("--commit-sha", default=None)
    ap.add_argument("--min-interval-minutes", type=float, default=0,
                    help="rebuild only if the explorer is missing, the v1 events changed, or it is this old (0 = always)")
    a = ap.parse_args(argv)
    return run(Path(a.out), Path(a.data_root), history_root=Path(a.history_root), now=c_time.parse_ts(a.now) if a.now else None,
               commit_sha=a.commit_sha, min_interval_seconds=a.min_interval_minutes * 60)


if __name__ == "__main__":
    raise SystemExit(main())
