"""Kalshi market layer for the paper system: board-as-of reader, contract normalisation, identity mapping, quote model, horizon snapshots.

Everything is read from the capture archive (a checkout of `data-archive`: `kalshi/markets`, `kalshi/markets_delta`, `kalshi/orderbooks`,
`kalshi/orderbooks_delta`). No network. Point in time: a board "as of t" is the checkpoint + deltas whose capture stamp is <= t; nothing
later is ever read into it.

Real shapes (inspected 2026-10-19, see docs/research/PAPER_ENGINE_SPEC.md):
  * prices are dollar strings (`yes_bid_dollars`, `yes_ask_dollars`, `no_bid_dollars`, `no_ask_dollars`), top-of-book sizes `*_size_fp`;
    `no_ask = 1 - yes_bid`, `no_bid = 1 - yes_ask`. A freshly listed market carries a PLACEHOLDER quote (0.00-0.02 / 0.98-1.00): never a price.
  * `yes_ask_size_fp` is the resting size at the best YES ask (= the best NO bid); buying NO consumes `yes_bid_size_fp`.
  * event suffix `{YY}{MON}{DD}{AWAY}{HOME}` (ET date). Game-level contracts name their team in the market suffix (`-SAC8`, `-SAS99`);
    player contracts carry `{TEAM}{PLAYERTOKEN}-{k}` and `yes_sub_title` "Name: k+".
  * `strike_type=greater`, `floor_strike=f`  =>  YES iff X > f, i.e. X >= floor(f)+1 (for the x.5 ladders Kalshi lists).
  * orderbooks (`kalshi/orderbooks*`) are sampled (~300 priority markets): cents levels `yes`/`no` bids, best first; depth for a buy of YES
    at ask `a` cents is the sum of NO-bid sizes at price >= 100 - a (and symmetrically for NO).
  * finalized markets carry `result` in yes|no|scalar and `settlement_value_dollars` (see settle.py).
"""
from __future__ import annotations

import glob
import gzip
import json
import math
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Iterator
from zoneinfo import ZoneInfo

from .. import data
from . import config as CFG
from . import schema as S

ROOT = data.ROOT
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from nba_edge.archive.delta import SCHEMA as DELTA_SCHEMA, BoardHash, Delta, DeltaChainError, apply_delta_in_place, canonical_board  # noqa: E402

ET = ZoneInfo("America/New_York")
SUPPORTED_SERIES = {
    "KXNBAGAME": ("game", "winner", "game_winner"),
    "KXNBASPREAD": ("game", "spread", "game_spread"),
    "KXNBATOTAL": ("game", "total", "game_total"),
    "KXNBATEAMTOTAL": ("team", "team_total", "team_total"),
    "KXNBAPTS": ("player", "points", "player_points"),
    "KXNBAREB": ("player", "rebounds", "player_rebounds"),
    "KXNBAAST": ("player", "assists", "player_assists"),
    "KXNBA3PT": ("player", "threes", "player_threes"),
    "KXNBAPRA": ("player", "pra", "player_pra"),
}
PERIOD_RE = re.compile(r"^KXNBA(?P<per>1H|2H|[1-4]Q)(?P<kind>SPREAD|TOTAL|WINNER)?$")
EVENT_RE = re.compile(r"^(?P<yy>\d{2})(?P<mon>[A-Z]{3})(?P<dd>\d{2})(?P<teams>[A-Z]{4,8})$")
_MON = {m: i + 1 for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"])}
_STAMP = re.compile(r"_(\d{8}T\d{6}Z)(?:_|\.)")

PLACEHOLDER, TWO_SIDED, ONE_SIDED, NO_QUOTE, INVALID = "PLACEHOLDER", "TWO_SIDED", "ONE_SIDED", "NO_QUOTE", "INVALID"


def iso(d: datetime) -> str:
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_ts(x: str) -> datetime:
    d = datetime.fromisoformat(str(x).replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _f(x: Any) -> float | None:
    try:
        v = None if x in (None, "") else float(x)
    except (TypeError, ValueError):
        return None
    return v if v is None or math.isfinite(v) else None          # NaN / inf are missing data, never a price or a size


# ------------------------------------------------------------------------------------------------------------------ chain reader
@dataclass(frozen=True)
class Tick:
    dt: datetime
    kind: str            # checkpoint | delta
    path: str            # absolute


class ChainReader:
    """Boards of one Kalshi capture family ("markets" | "orderbooks") reconstructed from checkpoints + deltas, strictly as-of.

    `ticks()` lists capture instants from file names only (cheap). `walk(since, until)` yields (dt, board) for every tick in the window in
    order, where `board` is the LIVE running {ticker: row} dict (copy what you need before advancing) or None when the tick cannot be
    reconstructed (chain broken). A delta is applied only to the checkpoint named in its own `base_path`, in `seq` order with no gaps."""

    def __init__(self, root: str, family: str = "markets"):
        self.root, self.family = root, family
        self._ck: list[Tick] | None = None
        self._dl: list[Tick] | None = None

    def _scan(self) -> None:
        if self._ck is not None:
            return
        fam = self.family
        ck, dl = [], []
        for p in glob.glob(os.path.join(self.root, "kalshi", fam, "dt=*", f"kalshi_{fam}_*.jsonl.gz")):
            m = _STAMP.search(os.path.basename(p))
            if m:
                ck.append(Tick(datetime.strptime(m.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc), "checkpoint", p))
        for p in glob.glob(os.path.join(self.root, "kalshi", f"{fam}_delta", "dt=*", f"kalshi_{fam}_delta_*.json.gz")):
            m = _STAMP.search(os.path.basename(p))
            if m:
                dl.append(Tick(datetime.strptime(m.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc), "delta", p))
        self._ck, self._dl = sorted(ck, key=lambda t: t.dt), sorted(dl, key=lambda t: t.dt)

    def ticks(self, since: datetime | None = None, until: datetime | None = None) -> list[datetime]:
        self._scan()
        ts = sorted({t.dt for t in self._ck + self._dl})
        return [t for t in ts if (since is None or t >= since) and (until is None or t <= until)]

    def walk(self, since: datetime, until: datetime) -> Iterator[tuple[datetime, dict[str, dict] | None]]:
        self._scan()
        cks = [c for c in self._ck if c.dt <= until]
        if not cks:
            return
        # the newest checkpoint at/before `since` starts the first chain; later checkpoints start later chains
        start = max([i for i, c in enumerate(cks) if c.dt <= since] or [0])
        for i in range(start, len(cks)):
            ck = cks[i]
            nxt = cks[i + 1].dt if i + 1 < len(cks) else None
            if ck.dt > until:
                break
            rel = os.path.relpath(ck.path, self.root)
            try:
                with gzip.open(ck.path, "rt") as f:
                    board = canonical_board([json.loads(x) for x in f if x.strip()])
            except (OSError, ValueError):
                yield ck.dt, None
                continue
            if since <= ck.dt <= until:
                yield ck.dt, board
            deltas: list[tuple[Tick, Delta]] = []
            for t in self._dl:
                if t.dt <= ck.dt or t.dt > until or (nxt is not None and t.dt >= nxt):
                    continue
                try:
                    with open(t.path, "rb") as f:
                        d = Delta.from_bytes(f.read())
                except (OSError, ValueError, DeltaChainError):
                    deltas.append((t, None))      # type: ignore[arg-type]
                    continue
                if d.base_path == rel:
                    deltas.append((t, d))
            deltas.sort(key=lambda x: (x[1].seq if x[1] is not None else 10 ** 9, x[0].dt))
            seq = 0
            broken = False
            seen: set[int] = set()
            hasher = BoardHash(board)
            running_hash = hasher.hexdigest()
            prev_at: datetime | None = None
            for t, d in deltas:
                if d is None or broken:
                    broken = True
                    if since <= t.dt <= until:
                        yield t.dt, None
                    continue
                if d.seq in seen:
                    continue                    # byte-identical retry already applied
                seen.add(d.seq)
                if d.seq != seq + 1:
                    broken = True
                    if since <= t.dt <= until:
                        yield t.dt, None
                    continue
                # the same checks as nba_edge.archive.delta.verify_chain, applied tick by tick: schema, parent hash, strictly increasing
                # capture instants, recorded result hash and market count. Any defect breaks the chain FROM THIS TICK ON (earlier ticks
                # were verified when they were yielded); a broken tick is reported as None, never guessed.
                try:
                    if d.schema != DELTA_SCHEMA or d.parent_board_sha256 != running_hash or (prev_at is not None and t.dt <= prev_at):
                        raise DeltaChainError("link check failed")
                    touched = apply_delta_in_place(board, d)
                    hasher.touch(board, touched)
                    running_hash = hasher.hexdigest()
                    if running_hash != d.board_sha256 or len(board) != d.n_markets_after:
                        raise DeltaChainError("result hash check failed")
                except DeltaChainError:
                    broken = True
                    if since <= t.dt <= until:
                        yield t.dt, None
                    continue
                prev_at = t.dt
                seq = d.seq
                if since <= t.dt <= until:
                    yield t.dt, board

    def board_at(self, at: datetime, lookback: timedelta = timedelta(hours=6)) -> tuple[datetime, dict[str, dict] | None] | None:
        """The newest reconstructable board observed at or before `at` (copy), or None when no tick exists in the lookback."""
        ts = self.ticks(at - lookback, at)
        if not ts:
            return None
        want = ts[-1]
        out = None
        for dt, b in self.walk(want, want):
            if dt == want:
                out = (dt, None if b is None else {k: dict(v) for k, v in b.items()})
        return out


# ------------------------------------------------------------------------------------------------------------------ identity
def canon_tri(code: str | None) -> str | None:
    if not code:
        return None
    from nba_edge.identity.teams import TeamIdentityError, registry
    try:
        return registry().by_tricode(code).tricode
    except (KeyError, TeamIdentityError):
        return None


def _known_tricodes() -> set[str]:
    from nba_edge.identity.teams import registry
    return set(registry().tricodes)


@dataclass
class Game:
    game_id: str
    start_utc: str
    home: str
    away: str
    game_date_et: str

    @classmethod
    def from_dict(cls, g: dict) -> Game:
        start = g.get("start_utc") or g.get("game_start_utc") or g.get("start_time_utc")
        et = g.get("game_date_et") or parse_ts(start).astimezone(ET).strftime("%Y-%m-%d")
        return cls(g["game_id"], iso(parse_ts(start)), canon_tri(g["home"]) or g["home"], canon_tri(g["away"]) or g["away"], str(et))

    @property
    def tip(self) -> datetime:
        return parse_ts(self.start_utc)


class GameIndex:
    """(ET date, {team, team}) -> Game, with a parse cache for Kalshi event tickers. Keyed by the unordered pair: two clubs never meet
    twice on one ET date, and the forecast archive may not know which side is home."""

    def __init__(self, games: Iterable[Game]):
        self.by_key = {(g.game_date_et, frozenset((g.away, g.home))): g for g in games}
        self._known = _known_tricodes()
        self._cache: dict[str, tuple[Game | None, tuple[str, str, str] | None]] = {}

    def match(self, event_ticker: str) -> tuple[Game | None, tuple[str, str, str] | None]:
        """(game, (date, away, home)) for an event ticker; game None when the event is not one of ours (or not a game event)."""
        if event_ticker in self._cache:
            return self._cache[event_ticker]
        parsed = parse_event(event_ticker, self._known)
        g = self.by_key.get((parsed[0], frozenset(parsed[1:]))) if parsed else None
        self._cache[event_ticker] = (g, parsed)
        return g, parsed


def parse_event(event_ticker: str, known: set[str]) -> tuple[str, str, str] | None:
    suffix = event_ticker.split("-", 1)[1] if "-" in event_ticker else ""
    m = EVENT_RE.match(suffix)
    if not m or m["mon"] not in _MON:
        return None
    teams = m["teams"]
    best = None
    for cut in range(2, len(teams) - 1):
        a, h = teams[:cut], teams[cut:]
        ca, ch = canon_tri(a), canon_tri(h)
        if ca and ch:
            best = (ca, ch)
            break
    if best is None:
        return None
    return (f"20{m['yy']}-{_MON[m['mon']]:02d}-{m['dd']}", best[0], best[1])


def norm_name(s: str) -> str:
    from nba_edge.identity.normalize import normalize_name
    return normalize_name(s)


class PlayerIndex:
    """Forecast-archive identities: (team, normalised name) -> entity_id (unique league-wide name as a second tier). Never guesses."""

    def __init__(self, forecasts: Iterable[dict]):
        self.by_team: dict[tuple[str, str], set[str]] = {}
        self.by_name: dict[str, set[str]] = {}
        self.name_of: dict[str, str] = {}
        for r in forecasts:
            k = norm_name(r.get("entity_name") or "")
            if not k:
                continue
            eid = r["entity_id"]
            self.name_of[eid] = r.get("entity_name")
            self.by_team.setdefault((r.get("team") or "", k), set()).add(eid)
            self.by_name.setdefault(k, set()).add(eid)

    def resolve(self, team: str | None, name: str | None) -> tuple[str | None, str]:
        k = norm_name(name or "")
        if not k:
            return None, "empty_name"
        ids = self.by_team.get((team or "", k))
        if ids and len(ids) == 1:
            return next(iter(ids)), "team_name"
        if not team:
            ids = self.by_name.get(k)
            if ids and len(ids) == 1:
                return next(iter(ids)), "league_name"
        return None, "unmatched" if not ids else "ambiguous"


_PLAYER_SUB = re.compile(r"^(?P<name>.+?):\s*\d")


def player_name(row: dict) -> str | None:
    m = _PLAYER_SUB.match(row.get("yes_sub_title") or "")
    if m:
        return m["name"].strip()
    from nba_edge.kalshi.contracts import player_name_from_title
    return player_name_from_title(row.get("title") or "", row.get("yes_sub_title") or "")


# ------------------------------------------------------------------------------------------------------------------ contracts
def classify_series(series: str) -> tuple[str, str | None, str | None, str]:
    """(scope, stat, family, period) for a series; scope 'unsupported' when we do not model or evaluate it."""
    if series in SUPPORTED_SERIES:
        sc, stat, fam = SUPPORTED_SERIES[series]
        return sc, stat, fam, "FULL"
    m = PERIOD_RE.match(series)
    if m:
        kind = (m["kind"] or "WINNER").lower()
        return "period", kind, f"period_{kind}", m["per"]
    return "unsupported", None, None, "FULL"


def contract_from_row(row: dict, gi: GameIndex) -> dict[str, Any] | None:
    """Normalise one board row for a game we track. None when the row is not a contract of a tracked game."""
    tk = row.get("ticker") or ""
    series = row.get("series_ticker") or tk.split("-")[0]
    ev = row.get("event_ticker") or "-".join(tk.split("-")[:2])
    game, parsed = gi.match(ev)
    if game is None:
        return None
    scope, stat, fam, period = classify_series(series)
    suffix = "-".join(tk.split("-")[2:])
    side_team = None
    for code in (game.away, game.home):
        if suffix.upper().startswith(code):
            side_team = code
    # (dual-suffix tricodes such as a 3-letter prefix of another cannot occur between the two clubs of one game)
    st, floor = row.get("strike_type"), _f(row.get("floor_strike"))
    comparator = k = None
    if st == "greater" and floor is not None:
        comparator, k = "gt", math.floor(floor) + 1
    elif st == "greater_or_equal" and floor is not None:
        comparator, k = "ge", math.ceil(floor)
    c = {"ticker": tk, "event_ticker": ev, "series": series, "family": fam, "scope": scope, "stat": stat, "period": period,
         "game_id": game.game_id, "game_start_utc": game.start_utc, "game_date_et": game.game_date_et, "away": game.away, "home": game.home,
         "side_team": side_team, "threshold": floor, "comparator": comparator, "k": k, "player_name": None, "team": None, "opponent": None,
         "status": row.get("status"), "support": "MODELED" if scope in ("game", "team", "player") else (
             "NO_PERIOD_MODEL" if scope == "period" else "UNSUPPORTED_SERIES")}
    if scope == "player":
        c["player_name"] = player_name(row)
        c["team"] = side_team
        c["opponent"] = None if side_team is None else (game.home if side_team == game.away else game.away)
    elif scope in ("game", "team", "period") and side_team:
        c["team"] = side_team
        c["opponent"] = game.home if side_team == game.away else game.away
    if scope in ("game", "team", "player") and (comparator is None and stat != "winner"):
        c["support"] = "UNRESOLVED_SEMANTICS"
    if stat == "winner" and scope == "game":
        c["comparator"], c["k"] = "winner", None
    return c


# ------------------------------------------------------------------------------------------------------------------ quotes
def classify_quote(row: dict) -> str:
    """Quality of the displayed YES quote (same rules as nba.live.kalshi_report.classify_quote; kept local so the paper layer has no
    import cycle with the live package)."""
    bid, ask = _f(row.get("yes_bid_dollars")), _f(row.get("yes_ask_dollars"))
    if bid is None and ask is None:
        return NO_QUOTE
    bid, ask = bid or 0.0, ask if ask is not None else 1.0
    if ask < bid or ask > 1.0 or bid < 0.0:
        return INVALID
    if bid <= 0.0 and (ask <= 0.0 or ask >= 1.0):
        return NO_QUOTE
    if bid <= 0.02 and ask >= 0.98:
        return PLACEHOLDER
    if bid <= 0.0 or ask >= 1.0:
        return ONE_SIDED
    return TWO_SIDED


def quote(row: dict) -> dict[str, Any]:
    """Quote model of one market row (dollars). no_bid / no_ask are derived from the YES book so the two sides can never disagree."""
    cls = classify_quote(row)
    yb, ya = _f(row.get("yes_bid_dollars")), _f(row.get("yes_ask_dollars"))
    ybs, yas = _f(row.get("yes_bid_size_fp")), _f(row.get("yes_ask_size_fp"))
    ok = cls in (TWO_SIDED, ONE_SIDED)
    return {"quote_class": cls, "yes_bid": yb if ok else None, "yes_ask": ya if ok else None,
            "no_bid": round(1 - ya, 4) if ok and ya is not None else None, "no_ask": round(1 - yb, 4) if ok and yb is not None else None,
            "yes_bid_size": ybs, "yes_ask_size": yas, "volume": _f(row.get("volume_fp")), "open_interest": _f(row.get("open_interest_fp")),
            "last_price": _f(row.get("last_price_dollars"))}


def depth(book_row: dict | None, side: str, entry_cents: int) -> float | None:
    """Contracts available at or better than `entry_cents` for a BUY of `side` from a sampled orderbook row (cents levels)."""
    if not book_row:
        return None
    opp = "no" if side == "YES" else "yes"
    lv = book_row.get(opp) or []
    thr = 100 - int(entry_cents)
    return float(sum(q for p, q in lv if p >= thr))


# ------------------------------------------------------------------------------------------------------------------ horizons
def choose_ticks(ticks: list[datetime], tip: datetime, now: datetime, min_gap_s: int = S.MAX_SNAPSHOT_GAP_S) -> dict[str, dict[str, Any]]:
    """Horizon -> {board_dt | None, target, gap_s, cause} for every horizon that is due at `now` (OPEN is resolved by the caller).

    The snapshot for a target is the latest tick at or before it; if the nearest such tick is more than `min_gap_s` earlier it is MISSED
    (recorded with a cause) and the horizon is never labelled with a staler board."""
    out: dict[str, dict[str, Any]] = {}
    for h, mins in S.HORIZON_MINUTES.items():
        target = tip - timedelta(minutes=mins)
        if target > now:
            continue
        prior = [t for t in ticks if t <= target]
        if not prior:
            out[h] = {"board_dt": None, "target": target, "gap_s": None, "cause": "NO_BOARD"}
            continue
        gap = (target - prior[-1]).total_seconds()
        out[h] = {"board_dt": prior[-1] if gap <= min_gap_s else None, "target": target, "gap_s": gap,
                  "cause": None if gap <= min_gap_s else "GAP_TOO_LARGE"}
    if now >= tip:
        prior = [t for t in ticks if t < tip]
        if not prior:
            out["LAST_VALID"] = {"board_dt": None, "target": tip, "gap_s": None, "cause": "NO_BOARD"}
        else:
            gap = (tip - prior[-1]).total_seconds()
            out["LAST_VALID"] = {"board_dt": prior[-1], "target": tip, "gap_s": gap, "cause": None}
    return out


def snapshot_rows(board: dict[str, dict], gi: GameIndex, game: Game, horizon: str, target: datetime, board_dt: datetime, *,
                  run_id: str | None = None, book: dict[str, dict] | None = None, replay: bool = False,
                  ) -> tuple[list[dict[str, Any]], Counter]:
    """sift.market_snapshot.v1 rows (supported + period series) for one game from one board, plus coverage counts (incl. unsupported)."""
    rows: list[dict[str, Any]] = []
    cov: Counter = Counter()
    bdt = iso(board_dt)
    for tk, r in board.items():
        ev = r.get("event_ticker") or "-".join(tk.split("-")[:2])
        g, _ = gi.match(ev)
        if g is None or g.game_id != game.game_id:
            continue
        c = contract_from_row(r, gi)
        if c is None:
            continue
        if c["support"] == "UNSUPPORTED_SERIES":
            cov["UNSUPPORTED_SERIES:" + c["series"]] += 1
            continue
        q = quote(r)
        cov["markets"] += 1
        cov["quote:" + q["quote_class"]] += 1
        ya, yb = q["yes_ask"], q["yes_bid"]
        bk = (book or {}).get(tk)
        rows.append({
            "schema": S.SNAPSHOT_SCHEMA, "snapshot_id": S.snapshot_id(bdt, tk, horizon), "board_observed_utc": bdt, "horizon": horizon,
            "horizon_target_utc": iso(target), "snapshot_gap_s": (target - board_dt).total_seconds(), "game_id": game.game_id,
            "game_start_utc": game.start_utc, "ticker": tk, "event_ticker": c["event_ticker"], "series": c["series"], "family": c["family"],
            "scope": c["scope"], "stat": c["stat"], "period": c["period"], "player_id": None, "player_name": c["player_name"],
            "team": c["team"], "opponent": c["opponent"], "threshold": c["threshold"], "k": c["k"], "comparator": c["comparator"],
            "status": c["status"], "yes_bid": q["yes_bid"], "yes_ask": q["yes_ask"], "no_bid": q["no_bid"], "no_ask": q["no_ask"],
            "yes_bid_size": q["yes_bid_size"], "yes_ask_size": q["yes_ask_size"],
            "depth_yes_ask": depth(bk, "YES", round(ya * 100)) if (bk and ya is not None) else None,
            "depth_no_ask": depth(bk, "NO", round((1 - yb) * 100)) if (bk and yb is not None) else None,
            "depth_source": "orderbook_sample" if bk else "top_of_book_only", "volume": q["volume"], "open_interest": q["open_interest"],
            "last_price": q["last_price"], "quote_class": q["quote_class"], "missing_cause": None, "replay": replay,
            "source_run_id": run_id, "support": c["support"], "side_team": c["side_team"], "authority": "research_only",
            "fee_multiplier_row": _f(r.get("fee_multiplier"))})
    return rows, cov


def missing_row(game: Game, horizon: str, target: datetime, cause: str, gap_s: float | None, replay: bool = False) -> dict[str, Any]:
    """A MISSING snapshot (one per game and horizon): the horizon was due and no valid board could serve it."""
    return {"schema": S.SNAPSHOT_SCHEMA, "snapshot_id": S.snapshot_id("MISSING", game.game_id, horizon), "board_observed_utc": None,
            "horizon": horizon, "horizon_target_utc": iso(target), "snapshot_gap_s": gap_s, "game_id": game.game_id,
            "game_start_utc": game.start_utc, "ticker": None, "quote_class": "MISSING", "missing_cause": cause, "replay": replay,
            "status": "MISSING", "authority": "research_only"}


def is_closing_line(board_dt: datetime, tip: datetime) -> bool:
    return 0 <= (tip - board_dt).total_seconds() <= S.CLOSING_MAX_AGE_S


def fee_multiplier(row_mult: float | None, cfg: dict) -> tuple[float, str]:
    """Taker multiplier for a series: the market row's `fee_multiplier` when present (nba_edge.kalshi.fees heuristic), else the base 0.07."""
    from nba_edge.kalshi.fees import FeeSchedule
    if cfg["execution"].get("fee_use_series_multiplier") and row_mult is not None:
        fs = FeeSchedule.from_series({"fee_multiplier": row_mult})
        return fs.taker_multiplier, fs.source
    return float(cfg["execution"]["fee_taker_multiplier"]), "default"


__all__ = ["ChainReader", "Game", "GameIndex", "PlayerIndex", "choose_ticks", "snapshot_rows", "missing_row", "contract_from_row",
           "quote", "classify_quote", "depth", "iso", "parse_ts", "is_closing_line", "fee_multiplier", "CFG"]
