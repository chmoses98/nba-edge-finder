"""Kalshi market calibration from the historical markets pull (data/history/kalshi/markets_*.jsonl.gz).

RESULT OF THE FIRST RUN (2026-09-18): the ``previous_*_dollars`` quotes on settled markets are NOT pregame prices —
they are the last quotes before settlement, i.e. after in-game trading (KXNBAGAME "calibration" came out at Brier
0.016, which is impossible for pregame moneylines). Those numbers are therefore reported under ``contaminated_post_tip``
and must not be cited as market calibration. True pregame closes need the hourly candlesticks joined to tip times
(``candles_<series>.jsonl.gz`` + ESPN schedule); ``study_candles`` does that when both are present and compute calibration per series: n, Brier, log loss, ECE, reliability
table, plus volume/liquidity summaries. This is the MARKET_BASELINE benchmark the model must beat prospectively.
Run: ``python -m nba_edge.research.market_calibration``.
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np

from nba_edge.config import REPO_ROOT
from nba_edge.evaluation.metrics import brier, calibration_table, ece, log_loss
from nba_edge.kalshi.normalize import market_to_cents


def load_markets(kdir: Path) -> list[dict]:
    rows = []
    for fp in sorted(kdir.glob("markets_*.jsonl.gz")):
        with gzip.open(fp, "rt") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
    return rows


def study(rows: list[dict]) -> dict:
    out = {}
    by_series: dict[str, list[dict]] = {}
    for m in rows:
        if m.get("result") not in ("yes", "no"):
            continue
        by_series.setdefault(m.get("series_ticker") or m.get("ticker", "").split("-")[0], []).append(m)
    for s, ms in sorted(by_series.items()):
        p, y, vol = [], [], []
        for m in ms:
            c = market_to_cents(m)
            pb, pa = c.get("previous_yes_bid"), c.get("previous_yes_ask")
            if pb is not None and pa is not None and 0 < pb <= pa < 100 and pa - pb <= 10:
                q = (pb + pa) / 2.0
            else:
                q = c.get("previous_price")
                if q in (None, 0, 100):
                    continue
            p.append(q / 100.0)
            y.append(1.0 if m["result"] == "yes" else 0.0)
            vol.append(c.get("volume") or 0)
        if len(p) < 20:
            out[s] = {"n": len(p), "note": "too few settled markets with a last price"}
            continue
        p, y = np.array(p), np.array(y)
        out[s] = {"n": int(len(p)), "brier": brier(p, y), "log_loss": log_loss(p, y), "ece": ece(p, y, 10), "mean_p": float(p.mean()), "base_rate": float(y.mean()),
                  "volume_median": float(np.median(vol)), "volume_p90": float(np.quantile(vol, 0.9)), "calibration": calibration_table(p, y, 10)}
    return out


def load_tip_times() -> dict[tuple[str, str, str], str]:
    """(game_date_et, away_tricode, home_tricode) -> tip ISO from the ESPN history parquet (if it has start_time_utc)."""
    try:
        from nba_edge.data.history import load_team_games
        from nba_edge.identity.teams import registry

        hist = REPO_ROOT / "data" / "history"
        seasons = sorted({p.stem.split("_")[-1] for p in (hist / "espn").glob("team_games_*.parquet")})
        tg = load_team_games(hist, seasons)
    except Exception:  # noqa: BLE001
        return {}
    if tg.empty or "start_time_utc" not in tg.columns:
        return {}
    reg = registry()
    out = {}
    for _, r in tg[tg["home"] == True].iterrows():  # noqa: E712
        try:
            out[(str(r["game_date_et"]), reg.by_id(int(r["opp_team_id"])).tricode, reg.by_id(int(r["team_id"])).tricode)] = str(r["start_time_utc"])
        except Exception:  # noqa: BLE001
            continue
    return out


def study_candles(kdir: Path) -> dict | None:
    """Pregame calibration from hourly candles: last candle whose end_period_ts < tip, price = yes bid/ask mid."""
    from nba_edge.kalshi.ticker import parse_ticker
    from nba_edge.timeutil import parse_iso

    tips = load_tip_times()
    files = sorted(kdir.glob("candles_*.jsonl.gz"))
    if not files or not tips:
        return None
    results = {}
    for fp in sorted(kdir.glob("markets_*.jsonl.gz")):
        with gzip.open(fp, "rt") as f:
            for line in f:
                if line.strip():
                    m = json.loads(line)
                    results[m["ticker"]] = m.get("result")
    out = {}
    for fp in files:
        series = fp.stem.split("_", 1)[1]
        last_pre: dict[str, tuple[int, float]] = {}
        with gzip.open(fp, "rt") as f:
            for line in f:
                if not line.strip():
                    continue
                c = json.loads(line)
                t = c.get("ticker")
                pt = parse_ticker(t)
                if not pt.game_date:
                    continue
                tip = tips.get((pt.game_date.isoformat(), pt.away_tricode, pt.home_tricode))
                if not tip:
                    continue
                ts = c.get("end_period_ts")
                try:
                    ts = int(ts)
                except (TypeError, ValueError):
                    continue
                if ts >= int(parse_iso(tip).timestamp()):
                    continue
                yb, ya = c.get("yes_bid") or {}, c.get("yes_ask") or {}
                bid, ask = _cents(yb.get("close")), _cents(ya.get("close"))
                if bid is None or ask is None or bid <= 0 or ask >= 100 or ask - bid > 10:
                    continue
                if t not in last_pre or ts > last_pre[t][0]:
                    last_pre[t] = (ts, (bid + ask) / 200.0)
        p, y = [], []
        for t, (_, q) in last_pre.items():
            r = results.get(t)
            if r in ("yes", "no"):
                p.append(q)
                y.append(1.0 if r == "yes" else 0.0)
        if len(p) >= 30:
            p, y = np.array(p), np.array(y)
            out[series] = {"n": int(len(p)), "brier": brier(p, y), "log_loss": log_loss(p, y), "ece": ece(p, y, 10), "mean_p": float(p.mean()), "base_rate": float(y.mean()), "calibration": calibration_table(p, y, 10)}
        else:
            out[series] = {"n": len(p), "note": "too few candles joined to tip times"}
    return out


def _cents(v) -> int | None:
    if v is None:
        return None
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return int(round(v * 100)) if v <= 1.0 else int(round(v))


def main() -> int:
    kdir = REPO_ROOT / "data" / "history" / "kalshi"
    rows = load_markets(kdir)
    rep = {"n_rows": len(rows), "contaminated_post_tip": study(rows), "note": "previous_* quotes are post-tip; see module docstring. Pregame calibration requires candles + tip times."}
    candles = study_candles(kdir)
    if candles:
        rep["pregame_from_candles"] = candles
    out = REPO_ROOT / "docs" / "research" / "market_calibration.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, indent=1))
    print("NOTE:", rep["note"])
    for key in ("pregame_from_candles",):
        for s, r in (rep.get(key) or {}).items():
            print(key, s, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if k != "calibration"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
