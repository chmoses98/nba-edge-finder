"""Canonical market-observation research table: contemporaneous Kalshi prices joined to outcomes.

This is the substrate for every market-vs-model study. One row per (ticker, pregame horizon), carrying the
*executable* prices that were actually available at that moment, the authoritative tip time, and the realised
outcome. Model probabilities are joined in later by the studies (``p_data_only`` / ``p_hybrid`` columns are
nullable here) so that this table stays a pure record of what the market said and what happened.

Sources
- ``data/history/kalshi/candles_<SERIES>.jsonl.gz``: hourly candles with ``yes_bid``/``yes_ask`` sub-objects
  (dollar strings, keys open/high/low/close) plus ``volume`` and ``open_interest``. ``price.close`` is often
  null (no trade that hour), which is exactly why the bid/ask is the right source rather than last trade.
- ``data/history/kalshi/markets_<SERIES>.jsonl.gz``: settled markets with ``result`` and strike fields.
- ``data/history/espn/team_games_*.parquet``: authoritative ``start_time_utc`` per game (the tip). Kalshi's
  ``close_time`` is AFTER the final buzzer and must never be used as the tip.

Executable-price convention (Kalshi):
- to buy YES you pay the YES ask;
- to buy NO you pay ``100 - yes_bid`` cents (the NO ask is the complement of the YES bid).
Both are recorded. The midpoint is recorded SEPARATELY and labelled as analysis-only: it is not a price anyone
can trade at, and using it as an entry price would manufacture edge that does not exist.

Horizons: for each of ``T-24h, T-6h, T-90m, T-30m`` we take the last candle ending at or before that instant,
plus ``final`` = the last candle ending strictly before tip. A market that had not opened yet at a horizon
simply has no row for it (recorded as missing, never back-filled from a later observation).
"""

from __future__ import annotations

import argparse
import ast
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from nba_edge.config import REPO_ROOT
from nba_edge.identity.players import PlayerRegistry
from nba_edge.identity.teams import TeamIdentityError, registry
from nba_edge.kalshi.contracts import build_contract
from nba_edge.kalshi.ontology import Ontology
from nba_edge.kalshi.ticker import parse_ticker
from nba_edge.log import get_logger, kv
from nba_edge.timeutil import parse_iso

log = get_logger(__name__)

# seconds before tip; ``None`` means "last observation strictly before tip"
HORIZONS: dict[str, int | None] = {
    "T-24h": 24 * 3600,
    "T-6h": 6 * 3600,
    "T-90m": 90 * 60,
    "T-30m": 30 * 60,
    "final": None,
}

COLUMNS = [
    "season", "game_id", "game_date_et", "away", "home", "tip_utc", "tip_ts",
    "ticker", "series", "family", "scope", "stat", "period", "threshold", "comparator",
    "team_id", "player_id", "player_name",
    "horizon", "prediction_ts", "market_ts", "seconds_before_tip",
    "yes_bid_cents", "yes_ask_cents", "exec_yes_cents", "exec_no_cents", "mid_cents_analysis_only",
    "spread_cents", "volume", "open_interest",
    "p_market", "p_market_exec_yes", "outcome", "result_raw", "settlement_value_dollars",
    "p_data_only", "p_hybrid", "model_version",
]


def _cents(v: Any) -> int | None:
    """Kalshi dollar string/float -> integer cents. Values <= 1 are dollars; larger are already cents."""
    if v is None or v == "":
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return int(round(f * 100)) if f <= 1.0 else int(round(f))


def _num(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def tip_index(hist_root: Path) -> dict[tuple[str, str, str], dict[str, Any]]:
    """(game_date_et, away_tricode, home_tricode) -> game metadata incl. authoritative tip."""
    from nba_edge.data.history import load_team_games

    seasons = sorted({p.stem.split("_")[-1] for p in (hist_root / "espn").glob("team_games_*.parquet")})
    tg = load_team_games(hist_root, seasons)
    if tg.empty:
        return {}
    reg = registry()
    out: dict[tuple[str, str, str], dict[str, Any]] = {}
    home_rows = tg[tg["home"] == True]  # noqa: E712
    for _, r in home_rows.iterrows():
        try:
            home = reg.by_id(int(r["team_id"])).tricode
            away = reg.by_id(int(r["opp_team_id"])).tricode
        except (TeamIdentityError, ValueError, TypeError):
            continue
        tip_raw = r.get("start_time_utc")
        if tip_raw in (None, "") or (isinstance(tip_raw, float) and pd.isna(tip_raw)):
            continue
        try:
            tip = parse_iso(str(tip_raw))
        except ValueError:
            continue
        out[(str(r["game_date_et"]), away, home)] = {
            "game_id": r["game_id"], "season": r["season"], "tip_utc": str(tip_raw), "tip_ts": int(tip.timestamp()),
            "home_team_id": int(r["team_id"]), "away_team_id": int(r["opp_team_id"]), "home": home, "away": away,
            "game_date_et": str(r["game_date_et"]),
        }
    return out


def _load_markets(kdir: Path, series: str) -> dict[str, dict[str, Any]]:
    fp = kdir / f"markets_{series}.jsonl.gz"
    if not fp.exists():
        return {}
    out = {}
    with gzip.open(fp, "rt") as f:
        for line in f:
            if line.strip():
                m = json.loads(line)
                if m.get("ticker"):
                    out[m["ticker"]] = m
    return out


def _load_candles(kdir: Path, series: str) -> dict[str, list[dict[str, Any]]]:
    fp = kdir / f"candles_{series}.jsonl.gz"
    if not fp.exists():
        return {}
    by: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with gzip.open(fp, "rt") as f:
        for line in f:
            if line.strip():
                c = json.loads(line)
                tk = c.get("ticker")
                ts = c.get("end_period_ts")
                if tk and ts is not None:
                    by[tk].append(c)
    for tk in by:
        by[tk].sort(key=lambda c: int(c["end_period_ts"]))
    return by


def _player_uuid(m: dict[str, Any]) -> str | None:
    cs = m.get("custom_strike")
    if isinstance(cs, str):
        try:
            cs = ast.literal_eval(cs)
        except (ValueError, SyntaxError):
            return None
    return (cs or {}).get("basketball_player") if isinstance(cs, dict) else None


def _pick(candles: list[dict[str, Any]], cutoff_ts: int) -> dict[str, Any] | None:
    """Last candle ending at or before ``cutoff_ts`` that carries a usable two-sided quote."""
    best = None
    for c in candles:
        ts = int(c["end_period_ts"])
        if ts > cutoff_ts:
            break
        bid = _cents((c.get("yes_bid") or {}).get("close"))
        ask = _cents((c.get("yes_ask") or {}).get("close"))
        if bid is None or ask is None:
            continue
        if bid <= 0 or ask >= 100 or ask < bid:  # degenerate/crossed: not an executable market
            continue
        best = c
    return best


def build_market_table(
    kdir: Path,
    hist_root: Path,
    out_path: Path | None = None,
    series: list[str] | None = None,
    max_spread_cents: int = 15,
) -> pd.DataFrame:
    onto = Ontology.load()
    preg = PlayerRegistry.load()
    uuid_to_id = {r.aliases["kalshi_uuid"]: r.nba_id for r in preg.records.values() if "kalshi_uuid" in r.aliases}
    id_to_name = {r.nba_id: r.full_name for r in preg.records.values()}
    tips = tip_index(hist_root)
    reg = registry()
    tricodes = reg.tricodes
    available = sorted(p.stem.split("_", 1)[1].replace(".jsonl", "") for p in kdir.glob("candles_*.jsonl.gz"))
    todo = [s for s in (series or available) if (kdir / f"candles_{s}.jsonl.gz").exists()]
    log.info(kv(event="market_table_start", series=",".join(todo), n_tips=len(tips)))

    rows: list[dict[str, Any]] = []
    stats: dict[str, dict[str, int]] = {}
    for s in todo:
        markets = _load_markets(kdir, s)
        candles = _load_candles(kdir, s)
        st = {"candle_tickers": len(candles), "no_market_row": 0, "no_tip": 0, "no_outcome": 0, "no_quote": 0, "rows": 0}
        for tk, cs in candles.items():
            m = markets.get(tk)
            if m is None:
                st["no_market_row"] += 1
                continue
            pt = parse_ticker(tk, tricodes)
            key = (pt.game_date.isoformat(), pt.away_tricode, pt.home_tricode) if pt.game_date else None
            g = tips.get(key) if key else None
            if g is None:
                st["no_tip"] += 1
                continue
            result = m.get("result")
            if result not in ("yes", "no"):
                st["no_outcome"] += 1  # 'scalar' (DNP) and unsettled markets have no binary outcome
                continue
            c = build_contract(m, onto)
            pid = uuid_to_id.get(_player_uuid(m) or "")
            wrote = 0
            for label, back in HORIZONS.items():
                cutoff = g["tip_ts"] - 1 if back is None else g["tip_ts"] - back
                pick = _pick(cs, cutoff)
                if pick is None:
                    continue
                bid = _cents((pick.get("yes_bid") or {}).get("close"))
                ask = _cents((pick.get("yes_ask") or {}).get("close"))
                spread = ask - bid
                if spread > max_spread_cents:
                    continue
                mts = int(pick["end_period_ts"])
                rows.append(
                    {
                        "season": g["season"], "game_id": g["game_id"], "game_date_et": g["game_date_et"],
                        "away": g["away"], "home": g["home"], "tip_utc": g["tip_utc"], "tip_ts": g["tip_ts"],
                        "ticker": tk, "series": s, "family": c.family, "scope": c.scope, "stat": c.stat,
                        "period": c.period, "threshold": c.threshold, "comparator": c.comparator,
                        "team_id": c.team_id, "player_id": pid, "player_name": id_to_name.get(pid) if pid else None,
                        "horizon": label, "prediction_ts": cutoff, "market_ts": mts,
                        "seconds_before_tip": g["tip_ts"] - mts,
                        "yes_bid_cents": bid, "yes_ask_cents": ask,
                        "exec_yes_cents": ask, "exec_no_cents": 100 - bid,
                        "mid_cents_analysis_only": (bid + ask) / 2.0, "spread_cents": spread,
                        "volume": _num(pick.get("volume")), "open_interest": _num(pick.get("open_interest")),
                        "p_market": (bid + ask) / 200.0, "p_market_exec_yes": ask / 100.0,
                        "outcome": 1.0 if result == "yes" else 0.0, "result_raw": result,
                        "settlement_value_dollars": _num(m.get("settlement_value_dollars")),
                        "p_data_only": None, "p_hybrid": None, "model_version": None,
                    }
                )
                wrote += 1
            if wrote == 0:
                st["no_quote"] += 1
            st["rows"] += wrote
        stats[s] = st
        log.info(kv(event="market_table_series", series=s, **st))

    df = pd.DataFrame(rows, columns=COLUMNS)
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out_path, engine="pyarrow", index=False)
        (out_path.parent / "market_table_manifest.json").write_text(
            json.dumps({"rows": len(df), "series": stats, "horizons": list(HORIZONS)}, indent=1)
        )
    return df


def summarize(df: pd.DataFrame) -> str:
    if df.empty:
        return "market table is EMPTY"
    L = ["| family | horizon | rows | tickers | games | base rate | mean p_market | med spread |",
         "|---|---|---:|---:|---:|---:|---:|---:|"]
    for (fam, hz), g in df.groupby(["family", "horizon"], observed=True):
        L.append(
            f"| {fam} | {hz} | {len(g)} | {g.ticker.nunique()} | {g.game_id.nunique()} | "
            f"{g.outcome.mean():.3f} | {g.p_market.mean():.3f} | {g.spread_cents.median():.0f} |"
        )
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build the canonical market-observation research table")
    ap.add_argument("--kdir", default=str(REPO_ROOT / "data" / "history" / "kalshi"))
    ap.add_argument("--hist", default=str(REPO_ROOT / "data" / "history"))
    ap.add_argument("--out", default=str(REPO_ROOT / "data" / "research" / "market_table.parquet"))
    ap.add_argument("--series", default=None, help="Comma list; default = every series that has candles")
    a = ap.parse_args(argv)
    df = build_market_table(
        Path(a.kdir), Path(a.hist), Path(a.out), [s for s in (a.series or "").split(",") if s] or None
    )
    print(f"rows={len(df)} tickers={df.ticker.nunique() if not df.empty else 0} -> {a.out}")
    print(summarize(df))
    return 0


if __name__ == "__main__":
    sys.exit(main())
