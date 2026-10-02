"""Edge Finder app export: the archive -> the ``edge_finder.app.v1`` contract, published to ``app/latest``.

A PURE ADAPTER. It reads what the production pipeline already wrote (the immutable archive on the
``data-archive`` branch, the latest slate when one exists, and the routed-wager accounting ledger
when a checkout of ``accounting-data`` is supplied) and re-expresses it as contract objects. It
changes no model, price, gate, threshold or authority: every NBA family stays RESEARCH, which the
export reports as ``bet_authority="RESEARCH_ONLY"`` and ``status="RESEARCH_CANDIDATE"``.

Sources (all read-only)
    events          latest schedule row per game (``context/schedule``), via ``workflows.settle.latest_schedule``
    markets         the newest captured board, via ``archive.reconstruct.latest_board`` (checkpoint + deltas)
    semantics       ``kalshi.contracts.build_contract`` + ``kalshi.ticker.parse_ticker`` (the simulate job's own)
    model prices    ``slates/latest/slate.json`` contracts[] joined to the ``predictions`` ledger kind
    recommendations slate contracts with gate == OK (research candidates, never bets)
    wagers          ``<accounting-dir>/data/accounting/{wagers,settlements}.jsonl`` (router deliveries)
    health          STATUS_capture / STATUS_simulate / LEASE_capture breadcrumbs

Failure contract: ``export`` never leaves a half-written tree. Any exception in the build writes
``health.json`` alone (``export_failed=True``, last-known-good payload untouched) and returns 1.

The contract package is stdlib-only and vendored at ``<repo>/contract``; it is put on ``sys.path``
here because the worker runs from an editable install that does not include it.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from nba_edge import MODEL_VERSION
from nba_edge.config import REPO_ROOT
from nba_edge.timeutil import parse_iso, utcnow

CONTRACT_DIR = REPO_ROOT / "contract"
if str(CONTRACT_DIR) not in sys.path:
    sys.path.insert(0, str(CONTRACT_DIR))

from edge_finder_contract import board as c_board  # noqa: E402
from edge_finder_contract import build, freshness, health, linkage, performance, publish  # noqa: E402
from edge_finder_contract import timeutil as c_time  # noqa: E402
from edge_finder_contract.routed_ledger import read_jsonl  # noqa: E402

SPORT = "NBA"
SOURCE_REPO = "chmoses98/nba-edge-finder"
SOURCE_BRANCH = "data-archive"
BET_AUTHORITY = "RESEARCH_ONLY"
DEFAULT_DATA_ROOT = "data/archive"
DEFAULT_OUT = "data/archive/app/latest"

# Capture cadence (worker/plan.py): 15 min far from tip, down to 5 min inside T-30m, when a game is
# within the active window; otherwise the conductor's daily futures snapshot. 20 min therefore means
# "the worker is on cadence"; 3 h means "something has stopped" during a game window. Off-window the
# board is legitimately a day old, and the export says STALE rather than pretending otherwise.
MARKET_THRESHOLDS = freshness.Thresholds(20 * 60, 3 * 60 * 60)
# Simulate runs when a not-started game tips within 26h and the last slate is older than 55 min.
MODEL_THRESHOLDS = freshness.Thresholds(60 * 60, 6 * 60 * 60)
THRESHOLDS = {"market_data": MARKET_THRESHOLDS, "model": MODEL_THRESHOLDS}

#: Games older than this (by tip) leave the board; markets that still reference them keep them on.
EVENT_LOOKBACK = timedelta(hours=48)

_EVENT_STATUS = {
    "scheduled": "SCHEDULED", "not_started": "SCHEDULED", "pregame": "SCHEDULED", "pre": "SCHEDULED",
    "in_progress": "LIVE", "live": "LIVE", "in": "LIVE", "halftime": "LIVE",
    "final": "FINAL", "post": "FINAL", "off": "FINAL", "completed": "FINAL",
    "postponed": "POSTPONED", "cancelled": "CANCELLED", "canceled": "CANCELLED",
}
_MARKET_STATUS = {"active": "OPEN", "open": "OPEN", "closed": "CLOSED", "settled": "SETTLED",
                  "finalized": "SETTLED", "determined": "SETTLED", "unopened": "UNOPENED"}
_GATE_QUALITY = {"OK": "OK", "NO_EDGE": "OK", "CANNOT_TRUST_INPUTS": "CANNOT_TRUST_INPUTS",
                 "UNSUPPORTED": "UNSUPPORTED"}


class ExportError(RuntimeError):
    """The inputs cannot be turned into a consistent payload (nothing is published)."""


@dataclass
class Inputs:
    """Everything the builder reads, loaded once so the build itself is a pure function."""

    schedule: dict[str, dict[str, Any]]
    board_rows: list[dict[str, Any]]
    board_observed_at: str | None
    board_provenance: str | None
    slate: dict[str, Any] | None
    predictions: dict[str, dict[str, Any]]
    wagers: list[dict[str, Any]]
    settlements: list[dict[str, Any]]
    status_capture: dict[str, Any]
    status_simulate: dict[str, Any]
    lease: dict[str, Any]
    warnings: list[str] = field(default_factory=list)


@dataclass
class Documents:
    run_id: str
    generated_at: str
    documents: dict[str, dict]
    health: dict
    manifest_freshness: dict
    warnings: list[str]
    counts: dict[str, int]


# ----------------------------------------------------------------------------------------- loading
def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _ts(value: Any) -> str | None:
    """A timezone-aware ISO string or None. A naive timestamp is refused (never emitted)."""
    if value in (None, ""):
        return None
    return c_time.to_iso(value)


def load_inputs(data_root: Path, accounting_dir: Path | None = None) -> Inputs:
    from nba_edge.archive.ledger import Ledger
    from nba_edge.archive.reconstruct import latest_board
    from nba_edge.workflows.settle import latest_schedule

    data_root = Path(data_root)
    warnings: list[str] = []
    if not (data_root / "manifest.jsonl").exists():
        raise ExportError(f"{data_root} holds no archive manifest (is the data-archive branch checked out?)")
    ledger = Ledger(data_root)
    schedule = latest_schedule(ledger)
    board = latest_board(ledger)
    rows = list(board.rows) if board else []
    if board is None:
        warnings.append("no market board has been captured yet")

    slate_path = data_root / "slates" / "latest" / "slate.json"
    slate = _read_json(slate_path) if slate_path.exists() else None
    predictions: dict[str, dict[str, Any]] = {}
    entry = ledger.latest("predictions")
    if entry is not None:
        from nba_edge.archive.delta import read_rows

        for row in read_rows(data_root / entry.path):
            pid = row.get("prediction_id")
            if pid:
                predictions[pid] = row

    wagers: list[dict[str, Any]] = []
    settlements: list[dict[str, Any]] = []
    if accounting_dir is not None:
        from nba_edge.accounting import SPEC

        wagers = read_jsonl(SPEC.wagers_path(Path(accounting_dir)))
        settlements = read_jsonl(SPEC.settlements_path(Path(accounting_dir)))

    return Inputs(
        schedule=schedule, board_rows=rows,
        board_observed_at=board.observed_at_utc if board else None,
        board_provenance=board.provenance() if board else None,
        slate=slate, predictions=predictions, wagers=wagers, settlements=settlements,
        status_capture=_read_json(data_root / "STATUS_capture.json"),
        status_simulate=_read_json(data_root / "STATUS_simulate.json"),
        lease=_read_json(data_root / "LEASE_capture.json"),
        warnings=warnings,
    )


# ---------------------------------------------------------------------------------------- identity
def event_source(game_id: str) -> tuple[str, str]:
    """``espn:401902644`` -> (espn_event_id, 401902644); a bare 10-digit NBA id -> (nba_game_id, id)."""
    gid = str(game_id)
    if gid.startswith("espn:"):
        return "espn_event_id", gid.split(":", 1)[1]
    return "nba_game_id", gid


def _team_participant(reg, team_id: Any, tricode: str | None) -> dict | None:
    team = None
    if team_id not in (None, ""):
        try:
            team = reg.by_id(int(team_id))
        except (KeyError, ValueError):
            team = None
    if team is None and tricode:
        try:
            team = reg.by_tricode(tricode)
        except KeyError:
            team = None
    if team is None:
        return None
    return build.participant(sport=SPORT, participant_type="TEAM", source="nba_team_id", source_id=team.team_id,
                             display_name=team.name, short_name=team.tricode,
                             source_ids={"tricode": team.tricode},
                             metadata={"conference": team.conference, "division": team.division})


def build_events(schedule: dict[str, dict[str, Any]], now: datetime, keep_game_ids: set[str]) -> tuple[list[dict], dict[str, str]]:
    """Events for every game tipping within the lookback or later, plus any game a market references.
    Returns (events, game_id -> event_id)."""
    from nba_edge.identity.teams import registry

    reg = registry()
    floor = now - EVENT_LOOKBACK
    events: list[dict] = []
    by_game: dict[str, str] = {}
    for gid, row in sorted(schedule.items()):
        start = row.get("start_time_utc")
        if not start:
            continue
        tip = parse_iso(start)
        if tip < floor and gid not in keep_game_ids:
            continue
        source, source_id = event_source(gid)
        home = _team_participant(reg, row.get("home_team_id"), row.get("home_tricode"))
        away = _team_participant(reg, row.get("away_team_id"), row.get("away_tricode"))
        participants = [p for p in (home, away) if p is not None]
        observed = _ts(row.get("_observed_at_utc"))
        ev = build.event(
            sport=SPORT, source=source, source_id=source_id, start_time_utc=start, participants=participants,
            home_participant=home["participant_id"] if home else None,
            away_participant=away["participant_id"] if away else None,
            league="NBA", season=row.get("season"), competition=row.get("season_type"),
            status=_EVENT_STATUS.get(str(row.get("status") or "").lower(), "UNKNOWN"),
            start_time_source=row.get("source"), start_time_confidence="SCHEDULED",
            effective_start_time_utc=row.get("actual_tip_utc"), venue=row.get("arena"),
            source_ids={"nba_edge_game_id": gid, "home_team_id": row.get("home_team_id"),
                        "away_team_id": row.get("away_team_id"), "home_tricode": row.get("home_tricode"),
                        "away_tricode": row.get("away_tricode")},
            schedule_updated_at=observed, last_updated_at=observed or start,
            extensions={"game_date_et": row.get("game_date_et"), "neutral_site": row.get("neutral_site"),
                        "schedule_status": row.get("status")},
        )
        events.append(ev)
        by_game[gid] = ev["event_id"]
    return events, by_game


def game_key(schedule_row: dict[str, Any]) -> tuple[str, str, str]:
    """The join key ``workflows.simulate.markets_for_game`` uses: ET date + home + away tricode."""
    return (str(schedule_row.get("game_date_et")), str(schedule_row.get("home_tricode")), str(schedule_row.get("away_tricode")))


class _Players:
    """Kalshi player uuid / display name -> registry record, via the identity registry's own rules."""

    def __init__(self) -> None:
        from nba_edge.identity.players import PlayerIdentityError, PlayerRegistry

        self._err = PlayerIdentityError
        try:
            self.reg = PlayerRegistry.load()
        except (OSError, ValueError):
            self.reg = None
        self.participants: dict[str, dict] = {}

    def resolve(self, uuid: str | None, name: str | None, team_id: int | None) -> dict | None:
        if self.reg is None:
            return None
        res = None
        for source, key in (("kalshi_uuid", uuid), ("kalshi", name)):
            if not key:
                continue
            try:
                res = self.reg.resolve(source, key, team_id)
                break
            except self._err:
                continue
        if res is None:
            return None
        rec = self.reg.records[res.nba_id]
        p = build.participant(
            sport=SPORT, participant_type="PLAYER", source="nba_player_id", source_id=rec.nba_id,
            display_name=rec.full_name, short_name=None,
            source_ids={"espn_athlete_id": rec.aliases.get("espn"), "kalshi_player_uuid": rec.aliases.get("kalshi_uuid")},
            metadata={"resolution": res.method, "provisional": res.provisional},
        )
        self.participants.setdefault(p["participant_id"], p)
        return p


def _compact(ext: dict[str, Any]) -> dict[str, Any]:
    """Extensions carry only what is known: 4,000 markets x a dozen nulls is dead weight in markets.json."""
    return {k: v for k, v in ext.items() if v is not None}


def _side(contract, game: dict[str, Any] | None) -> str | None:
    if contract.scope == "game" and contract.stat == "winner" and contract.team_id is not None:
        if game is not None and contract.team_id == game.get("home_team_id"):
            return "HOME"
        if game is not None and contract.team_id == game.get("away_team_id"):
            return "AWAY"
        return "PARTICIPANT"
    if contract.stat in ("total", "team_total", "margin", "pts", "reb", "ast", "fg3m", "stl", "blk", "pra", "pr", "pa", "ra"):
        if contract.comparator in ("gt", "ge"):
            return "OVER"
        if contract.comparator in ("lt", "le"):
            return "UNDER"
    if contract.scope == "player":
        return "PARTICIPANT"
    return None


def build_markets(inputs: Inputs, by_game: dict[str, str], team_participant_ids: dict[int, str]) -> tuple[list[dict], _Players, list[str]]:
    from nba_edge.identity.teams import registry
    from nba_edge.kalshi.contracts import build_contract
    from nba_edge.kalshi.ontology import Ontology
    from nba_edge.kalshi.ticker import parse_ticker

    reg = registry()
    onto = Ontology.load()
    players = _Players()
    games_by_key = {game_key(row): gid for gid, row in inputs.schedule.items() if gid in by_game}
    warnings: list[str] = []
    out: list[dict] = []
    skipped = 0
    for m in inputs.board_rows:
        ticker = m.get("ticker")
        if not ticker:
            skipped += 1
            continue
        try:
            contract = build_contract(m, onto, reg)
        except Exception as exc:  # noqa: BLE001 - one odd market must not sink the whole board
            skipped += 1
            warnings.append(f"market {ticker}: semantics failed ({type(exc).__name__})")
            continue
        pt = parse_ticker(ticker, reg.tricodes)
        gid = None
        if pt.game_date and pt.home_tricode and pt.away_tricode:
            gid = games_by_key.get((pt.game_date.isoformat(), pt.home_tricode, pt.away_tricode))
        game = inputs.schedule.get(gid) if gid else None
        quote = m.get("_quote_cents") or {}
        player = players.resolve(contract.kalshi_entity_uuid, contract.entity_name, contract.team_id) if contract.scope == "player" else None
        line = contract.threshold if contract.stat in ("total", "team_total", "margin") else None
        out.append(build.market(
            sport=SPORT, kalshi_ticker=ticker, market_family=contract.family,
            yes_description=str(m.get("title") or ticker), source="kalshi",
            event_id=by_game.get(gid) if gid else None,
            kalshi_event_ticker=m.get("event_ticker"), kalshi_series_ticker=m.get("series_ticker"),
            market_type=m.get("market_type"), period=contract.period,
            participant_id=team_participant_ids.get(contract.team_id) if contract.team_id is not None else None,
            player_id=player["participant_id"] if player else None,
            side=_side(contract, game), line=line, threshold=contract.threshold,
            no_description=m.get("no_sub_title"),
            yes_bid=build.from_cents(quote.get("yes_bid")), yes_ask=build.from_cents(quote.get("yes_ask")),
            no_bid=build.from_cents(quote.get("no_bid")), no_ask=build.from_cents(quote.get("no_ask")),
            last_price=build.from_cents(quote.get("last_price")),
            volume=m.get("volume_fp"), open_interest=m.get("open_interest_fp"),
            market_status=_MARKET_STATUS.get(str(m.get("status") or "").lower(), "UNKNOWN"),
            close_time_utc=m.get("expected_expiration_time") or m.get("close_time"),
            captured_at=m.get("_observed_at_utc") or inputs.board_observed_at,
            raw_market_reference=inputs.board_provenance,
            extensions=_compact({
                "support": str(contract.support), "scope": contract.scope, "stat": contract.stat,
                "semantics_confidence": contract.semantics_confidence, "comparator": contract.comparator,
                "upper": contract.upper, "strike_type": m.get("strike_type"), "yes_sub_title": m.get("yes_sub_title"),
                "entity_name": contract.entity_name, "kalshi_entity_uuid": contract.kalshi_entity_uuid,
                "player_display_name": player["display_name"] if player else None,
                "nba_edge_game_id": gid,
            }),
        ))
    if skipped:
        warnings.append(f"{skipped} board row(s) skipped (no ticker or unreadable semantics)")
    return out, players, warnings


def _slate_contracts(inputs: Inputs) -> list[dict[str, Any]]:
    slate = inputs.slate or {}
    rows = slate.get("contracts")
    return [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []


def build_model_prices(inputs: Inputs, run_id: str, market_ids: set[str], by_game: dict[str, str], now: datetime) -> tuple[list[dict], list[str]]:
    from edge_finder_contract import ids

    warnings: list[str] = []
    out: list[dict] = []
    seen: set[str] = set()
    missing = 0
    for row in _slate_contracts(inputs):
        ticker, p = row.get("ticker"), row.get("p_production")
        if not ticker or p is None:
            continue
        mid = ids.market_id(ticker)
        if mid not in market_ids:
            missing += 1
            continue
        if mid in seen:
            continue
        seen.add(mid)
        pred = inputs.predictions.get(str(row.get("prediction_id") or ""), {})
        generated = row.get("model_ts") or pred.get("predicted_at_utc") or (inputs.slate or {}).get("generated_at_utc")
        inputs_as_of = pred.get("data_cutoff_utc") or row.get("market_ts")
        gate = str(row.get("gate") or "UNSUPPORTED")
        se = row.get("mc_se") if row.get("mc_se") is not None else pred.get("p_data_only_se")
        out.append(build.model_price(
            run_id=run_id, market_id=mid, fair_probability=p, generated_at=generated,
            event_id=by_game.get(row.get("game_id")), model_version=MODEL_VERSION,
            uncertainty=se, market_probability=row.get("p_market"),
            inputs_as_of=inputs_as_of,
            freshness_status=freshness.status_for(generated, component="model", now=now, thresholds=MODEL_THRESHOLDS),
            data_quality_status=_GATE_QUALITY.get(gate, "UNKNOWN"), support_status=row.get("support"),
            extensions={"p_hybrid": row.get("p_hybrid"), "p_data_only": row.get("p_data_only"), "p_market": row.get("p_market"),
                        "gate": gate, "gate_reasons": list(row.get("gate_reasons") or [])[:4],
                        "authority": "RESEARCH", "prediction_id": row.get("prediction_id"),
                        "sim_version": (inputs.slate or {}).get("sim_version"), "feature_version": (inputs.slate or {}).get("feature_version")},
        ))
    if missing:
        warnings.append(f"{missing} slate contract(s) priced a market no longer on the board; not exported")
    return out, warnings


def build_theses(inputs: Inputs, run_id: str, by_game: dict[str, str], generated_at: str) -> tuple[list[dict], dict[str, str]]:
    """One thesis per event from the slate's structured thesis groups. No prose exists, so summary is None.
    Returns (theses, game_id -> thesis_id)."""
    slate = inputs.slate or {}
    groups = [t for t in (slate.get("theses") or []) if isinstance(t, dict)]
    by_event: dict[str, list[dict]] = {}
    for t in groups:
        eid = by_game.get(t.get("game_id"))
        if eid:
            by_event.setdefault(eid, []).append(t)
    out: list[dict] = []
    thesis_by_game: dict[str, str] = {}
    for eid, ts in sorted(by_event.items()):
        supporting = [f"{t.get('thesis')}: {t.get('best')} {t.get('best_side')}" for t in ts]
        opposing = [str(t["warning"]) for t in ts if t.get("warning")]
        deps = sorted({str(a.get("ticker")) for t in ts for a in (t.get("alternatives") or []) if a.get("ticker")})
        thesis = build.thesis(
            sport=SPORT, run_id=run_id, event_id=eid, generated_at=slate.get("generated_at_utc") or generated_at,
            summary=None, primary_game_script=None, supporting_factors=supporting, opposing_factors=opposing,
            key_dependencies=deps,
            context_notes={"injuries": slate.get("injury_snapshot")},
            confidence_label=None,
            evidence={"theses": [{"thesis": t.get("thesis"), "best": t.get("best"), "best_side": t.get("best_side"),
                                  "best_ev": t.get("best_ev"), "alternatives": t.get("alternatives") or []} for t in ts],
                      "market_snapshot": slate.get("market_snapshot"), "authority_note": slate.get("authority_note")},
        )
        out.append(thesis)
        for gid, e in by_game.items():
            if e == eid:
                thesis_by_game[gid] = thesis["thesis_id"]
    return out, thesis_by_game


def build_recommendations(inputs: Inputs, run_id: str, markets: dict[str, dict], by_game: dict[str, str],
                          thesis_by_game: dict[str, str], now: datetime) -> list[dict]:
    from edge_finder_contract import ids

    out: list[dict] = []
    seen: set[str] = set()
    for row in _slate_contracts(inputs):
        if str(row.get("gate")) != "OK" or not row.get("best_side") or not row.get("ticker"):
            continue
        mid = ids.market_id(row["ticker"])
        market = markets.get(mid)
        eid = by_game.get(row.get("game_id"))
        if market is None or eid is None:
            continue
        selection = str(row["best_side"]).upper()
        if selection not in ("YES", "NO"):
            continue
        p_yes = row.get("p_production")
        fair = None if p_yes is None else (p_yes if selection == "YES" else 1.0 - p_yes)
        ask = row.get("yes_ask") if selection == "YES" else row.get("no_ask")
        ev = row.get("ev_yes") if selection == "YES" else row.get("ev_no")
        bet_up_to = row.get("bet_up_to_yes") if selection == "YES" else row.get("bet_up_to_no")
        created = row.get("model_ts") or (inputs.slate or {}).get("generated_at_utc")
        native_id = f"{row.get('prediction_id')}:{selection}" if row.get("prediction_id") else None
        rec = build.recommendation(
            sport=SPORT, source_repo=SOURCE_REPO, event_id=eid, market_id=mid, run_id=run_id,
            selection=selection, market_description=f"{selection} on {row.get('title') or row['ticker']}",
            created_at=created, status="RESEARCH_CANDIDATE", authority=BET_AUTHORITY, research_only=True,
            native_id=native_id, current_probability=row.get("p_market"), current_price=build.from_cents(ask),
            fair_probability=fair, edge=ev, bet_up_to_price=build.from_cents(bet_up_to),
            bet_up_to_probability=build.from_cents(bet_up_to),
            confidence=row.get("semantics"), thesis_id=thesis_by_game.get(row.get("game_id")),
            data_freshness=freshness.status_for(created, component="model", now=now, thresholds=MODEL_THRESHOLDS),
            injury_flags=[f for f in (row.get("flags") or []) if isinstance(f, str)][:6],
            source_ids={"prediction_id": row.get("prediction_id"), "nba_edge_game_id": row.get("game_id")},
            extensions={"ev_per_contract_dollars": ev, "spread_cents": row.get("spread_cents"), "support": row.get("support"),
                        "family": row.get("family"), "thesis": row.get("thesis"), "authority_native": row.get("authority"),
                        "note": "research candidate from a RESEARCH-authority slate; not a bet"},
        )
        if rec["recommendation_id"] in seen:
            continue
        seen.add(rec["recommendation_id"])
        out.append(rec)
    return out


def _settlement_result(row: dict[str, Any]) -> str:
    return {"WON": "WON", "LOST": "LOST"}.get(str(row.get("result") or ""), "UNKNOWN")


def _settlement_doc(w: dict, s: dict[str, Any]) -> dict:
    established = s.get("gross_return") is not None and s.get("net_profit_loss") is not None
    result = _settlement_result(s)
    winning = None
    if result in ("WON", "LOST"):
        winning = w["selection"] if result == "WON" else ("NO" if w["selection"] == "YES" else "YES")
    return build.settlement(
        wager_id=w["wager_id"], market_id=w["market_id"], result=result, settled_at=s["settled_at"],
        source="KALSHI_ROUTER", verification_status="EXCHANGE_CONFIRMED" if established else "REFUSED",
        winning_side=winning, gross_payout=s.get("gross_return"), net_pnl=s.get("net_profit_loss"),
        refusals=s.get("refusals") or [], source_ids={"ledger_settlement_id": s.get("settlement_id")},
        extensions={"economics_version": s.get("economics_version"), "schema_version": s.get("schema_version")},
    )


def build_wagers(inputs: Inputs, markets: dict[str, dict], model_prices: list[dict], recommendations: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """Router-delivered wagers and settlements. Returns (wagers, settlements, market stubs added).

    Links to model prices / recommendations are applied TEMPORALLY by the contract (records that
    predate ``placed_at`` only); nothing is linked by hand. A wager whose market has left the board
    gets a price-less stub so every ``wager.market_id`` exists in markets.json."""
    from edge_finder_contract import ids

    stubs: list[dict] = []
    wagers: list[dict] = []
    settlements: list[dict] = []
    settlements_by_key = {s.get("source_bet_key"): s for s in inputs.settlements}
    for row in inputs.wagers:
        ticker = row["market_ticker"]
        mid = ids.market_id(ticker)
        market = markets.get(mid)
        if market is None:
            market = build.market_stub(sport=SPORT, kalshi_ticker=ticker, market_family="unknown",
                                       yes_description=f"YES on {ticker}", source="accounting_ledger",
                                       market_status="UNKNOWN")
            markets[mid] = market
            stubs.append(market)
        w = build.wager(
            sport=SPORT, kalshi_ticker=ticker, selection=row["side"], contracts=row["contracts"], stake=row["stake"],
            average_price=row["execution_price"], placed_at=row["executed_at"], source="KALSHI_ROUTER",
            destination_repo=SOURCE_REPO, source_bet_key=row["source_bet_key"], event_id=market.get("event_id"),
            side=row.get("execution_action"), fees=row.get("fees_paid"),
            source_ids={"ledger_wager_id": row.get("wager_id"), "import_batch_id": row.get("import_batch_id")},
            extensions={"game_date": row.get("game_date"), "fee_state": row.get("fee_state"),
                        "entry_method": row.get("entry_method"), "schema_version": row.get("schema_version")},
        )
        w = linkage.apply_links(w, model_prices, recommendations, list(markets.values()))
        s = settlements_by_key.get(row["source_bet_key"])
        if s is not None:
            st = _settlement_doc(w, s)
            w["settlement_id"] = st["settlement_id"]
            w["settlement_status"] = "SETTLED"
            w["payout"] = st["gross_payout"]
            w["profit_loss"] = st["net_pnl"]
            settlements.append(st)
        wagers.append(w)
    return wagers, settlements, stubs


# ------------------------------------------------------------------------------------------ build
def native_run_id(inputs: Inputs) -> str:
    sim = inputs.status_simulate
    if sim.get("simulated_at_utc") and (inputs.slate or {}).get("generated_at_utc"):
        return f"simulate:{sim.get('slate_dir') or sim.get('simulated_at_utc')}"
    cap = inputs.status_capture
    if cap.get("run_id") and cap.get("last_capture_utc"):
        return f"capture:{cap['run_id']}:{cap['last_capture_utc']}"
    if inputs.board_observed_at:
        return f"board:{inputs.board_observed_at}"
    return "no-capture"


def build_documents(inputs: Inputs, *, now: datetime, commit_sha: str | None = None,
                    workflow_run_id: str | None = None, accounting_present: bool = False) -> Documents:
    if now.tzinfo is None:
        raise ExportError("now must be timezone-aware")
    generated_at = c_time.to_iso(now)
    warnings = list(inputs.warnings)

    # The run id is THE id of every document; deterministic from the native run and the clock.
    run_doc = build.run(sport=SPORT, repo=SOURCE_REPO, completed_at=now, scope="app_export", status="SUCCESS",
                        native_run_id=native_run_id(inputs), commit_sha=commit_sha, workflow_run_id=workflow_run_id,
                        model_version=MODEL_VERSION)
    run_id = run_doc["run_id"]

    # Games a market references must stay on the board even once they are past the lookback.
    keyed = {game_key(row): gid for gid, row in inputs.schedule.items()}
    keep: set[str] = set()
    from nba_edge.identity.teams import registry
    from nba_edge.kalshi.ticker import parse_ticker

    tricodes = registry().tricodes
    for m in inputs.board_rows:
        pt = parse_ticker(m.get("ticker") or "", tricodes)
        if pt.game_date and pt.home_tricode and pt.away_tricode:
            gid = keyed.get((pt.game_date.isoformat(), pt.home_tricode, pt.away_tricode))
            if gid:
                keep.add(gid)
    events, by_game = build_events(inputs.schedule, now, keep)
    team_pids: dict[int, str] = {}
    for ev in events:
        for p in ev["participants"]:
            team_pids[int(p["source_ids"]["nba_team_id"])] = p["participant_id"]

    markets_list, _players, mwarn = build_markets(inputs, by_game, team_pids)
    warnings.extend(mwarn)
    markets = {m["market_id"]: m for m in markets_list}

    model_prices, pwarn = build_model_prices(inputs, run_id, set(markets), by_game, now)
    warnings.extend(pwarn)
    theses, thesis_by_game = build_theses(inputs, run_id, by_game, generated_at)
    recommendations = build_recommendations(inputs, run_id, markets, by_game, thesis_by_game, now)
    wagers, settlements, _stubs = build_wagers(inputs, markets, model_prices, recommendations)
    markets_list = list(markets.values())

    last_capture = _ts(inputs.board_observed_at or inputs.status_capture.get("last_capture_utc"))
    last_model = None
    if inputs.slate and inputs.slate.get("generated_at_utc") and inputs.status_simulate.get("simulated_at_utc"):
        last_model = _ts(inputs.slate.get("generated_at_utc"))
    if last_model is None:
        warnings.append("no slate has been produced yet (simulate has not run this season); model_prices and "
                        "recommendations are empty and model_status is UNAVAILABLE")
    if not events:
        warnings.append("no games on the board")
    next_run = _ts(inputs.lease.get("expected_next_capture_at"))
    settlement_as_of = max((s["settled_at"] for s in settlements), default=None)

    health_doc = health.build_health(
        sport=SPORT, run_id=run_id, bet_authority=BET_AUTHORITY, last_market_capture=last_capture,
        last_model_generated=last_model, last_successful_run=generated_at, payload_run_id=run_id,
        payload_available=True, export_failed=False, commit_sha=commit_sha, next_scheduled_run=next_run,
        router_as_of=None, settlement_as_of=settlement_as_of, model_required=True,
        router_applicable=accounting_present, settlement_applicable=accounting_present,
        thresholds=THRESHOLDS, warnings=warnings, errors=[], now=now, generated_at=now,
    )
    run_doc = build.run(
        sport=SPORT, repo=SOURCE_REPO, completed_at=now, scope="app_export", status="SUCCESS",
        native_run_id=native_run_id(inputs), commit_sha=commit_sha, workflow_run_id=workflow_run_id,
        model_version=MODEL_VERSION, events_requested=len(inputs.schedule), events_processed=len(events),
        markets_discovered=len(inputs.board_rows), markets_priced=len(model_prices),
        recommendations_created=len(recommendations),
        data_sources=["kalshi", "espn_scoreboard", "nba_edge.archive", "slates/latest"] + (["accounting-data"] if accounting_present else []),
        input_freshness={"kalshi": last_capture, "schedule": _ts(max((r.get("_observed_at_utc") or "" for r in inputs.schedule.values()), default=None) or None),
                         "model": last_model},
        warnings=warnings,
    )
    assert run_doc["run_id"] == run_id

    def coll(kind: str, items: list[dict]) -> dict:
        return build.collection(kind, SPORT, run_id, now, items)

    board_doc = c_board.build_board(sport=SPORT, run_id=run_id, generated_at=now, events=events, markets=markets_list,
                                    model_prices=model_prices, recommendations=recommendations, wagers=wagers,
                                    health=health_doc, thresholds=THRESHOLDS, now=now)
    perf_doc = performance.build_performance(
        sport=SPORT, run_id=run_id, generated_at=now, wagers=wagers, settlements=settlements, markets=markets_list,
        recommendations=recommendations,
        notes=["accounting ledger only; every NBA model family is RESEARCH_ONLY", "CLV is not computed by this export"],
    )
    documents: dict[str, dict] = {
        "events": coll("events", events), "markets": coll("markets", markets_list),
        "model_prices": coll("model_prices", model_prices), "recommendations": coll("recommendations", recommendations),
        "theses": coll("theses", theses), "wagers": coll("wagers", wagers), "settlements": coll("settlements", settlements),
        "runs": coll("runs", [run_doc]), "board": board_doc, "performance": perf_doc,
    }
    freshness_row = {r["event_id"]: r["data_freshness"] for r in board_doc["items"]}
    for ev in events:
        documents[f"event_detail/{ev['event_id']}"] = c_board.build_event_detail(
            sport=SPORT, run_id=run_id, generated_at=now, event=ev, markets=markets_list, model_prices=model_prices,
            recommendations=recommendations, theses=theses, wagers=wagers, settlements=settlements,
            context={"board_provenance": inputs.board_provenance, "slate": (inputs.slate or {}).get("date_et")},
            data_freshness=freshness_row.get(ev["event_id"], "UNKNOWN"),
        )
    manifest_freshness = {
        "kalshi": {"as_of": last_capture, "status": freshness.classify(c_time.age_seconds(last_capture, now), MARKET_THRESHOLDS)},
        "model": {"as_of": last_model, "status": freshness.classify(c_time.age_seconds(last_model, now), MODEL_THRESHOLDS)},
        "schedule": {"as_of": run_doc["input_freshness"].get("schedule"),
                     "status": freshness.status_for(run_doc["input_freshness"].get("schedule"), component="schedule", now=now)},
    }
    counts = {"events": len(events), "markets": len(markets_list), "model_prices": len(model_prices),
              "recommendations": len(recommendations), "theses": len(theses), "wagers": len(wagers),
              "settlements": len(settlements)}
    return Documents(run_id=run_id, generated_at=generated_at, documents=documents, health=health_doc,
                     manifest_freshness=manifest_freshness, warnings=warnings, counts=counts)


# ---------------------------------------------------------------------------------------- export
def export(out: Path, data_root: Path, *, accounting_dir: Path | None = None, now: datetime | None = None,
           commit_sha: str | None = None, workflow_run_id: str | None = None) -> int:
    """Build and publish. Returns 0 on success; on any failure writes health.json only and returns 1."""
    out = Path(out)
    now = now or utcnow()
    try:
        inputs = load_inputs(Path(data_root), accounting_dir)
        docs = build_documents(inputs, now=now, commit_sha=commit_sha, workflow_run_id=workflow_run_id,
                               accounting_present=accounting_dir is not None)
        publish.publish(root=out, sport=SPORT, run_id=docs.run_id, generated_at=now, documents=docs.documents,
                        source_repo=SOURCE_REPO, source_branch=SOURCE_BRANCH, commit_sha=commit_sha,
                        model_version=MODEL_VERSION, status="SUCCESS", freshness=docs.manifest_freshness,
                        warnings=docs.warnings, health=docs.health)
    except Exception as exc:  # noqa: BLE001 - the failure path must cover everything
        _write_failure_health(out, exc, now=now, commit_sha=commit_sha)
        print(f"app_export: FAILED ({type(exc).__name__}: {exc}); health.json written, payload untouched", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 1
    print(f"app_export: published run {docs.run_id} to {out} "
          f"({', '.join(f'{k}={v}' for k, v in docs.counts.items())}; overall={docs.health['overall_status']})")
    return 0


def _write_failure_health(out: Path, exc: BaseException, *, now: datetime, commit_sha: str | None) -> None:
    previous = publish.read_manifest(out)
    payload_run = previous.get("run_id") if previous else None
    prev_health = _read_json(out / publish.HEALTH_NAME)
    doc = health.build_health(
        sport=SPORT, run_id=payload_run or "run_exportfailed00000000", bet_authority=BET_AUTHORITY,
        last_market_capture=prev_health.get("last_market_capture"), last_model_generated=prev_health.get("last_model_generated"),
        last_successful_run=prev_health.get("last_successful_run"), payload_run_id=payload_run,
        payload_available=previous is not None, export_failed=True, commit_sha=commit_sha,
        thresholds=THRESHOLDS, warnings=[], errors=[f"{type(exc).__name__}: {exc}"[:500]], now=now, generated_at=now,
    )
    publish.write_health_only(out, doc)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Publish the Edge Finder app export (edge_finder.app.v1) from the NBA archive.")
    ap.add_argument("--out", default=DEFAULT_OUT, help="app root to publish into (default data/archive/app/latest)")
    ap.add_argument("--data-root", default=DEFAULT_DATA_ROOT, help="archive root: a checkout of data-archive")
    ap.add_argument("--accounting-dir", default=None, help="optional checkout of the accounting-data branch")
    ap.add_argument("--now", default=None, help="ISO-8601 UTC instant (tests / determinism); default: wall clock")
    ap.add_argument("--commit-sha", default=os.environ.get("GITHUB_SHA") or None)
    ap.add_argument("--workflow-run-id", default=os.environ.get("GITHUB_RUN_ID") or None)
    a = ap.parse_args(argv)
    now = c_time.parse_ts(a.now) if a.now else None
    return export(Path(a.out), Path(a.data_root), accounting_dir=Path(a.accounting_dir) if a.accounting_dir else None,
                  now=now, commit_sha=a.commit_sha, workflow_run_id=a.workflow_run_id)


if __name__ == "__main__":
    raise SystemExit(main())
