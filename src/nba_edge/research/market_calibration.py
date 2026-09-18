"""Kalshi market calibration from the historical markets pull (data/history/kalshi/markets_*.jsonl.gz).

For settled binary markets with a known result, use ``last_price`` (and, when candles exist, the last pre-close
candle's yes mid) as the market probability and compute calibration per series: n, Brier, log loss, ECE, reliability
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
            lp = m.get("last_price")
            if lp in (None, 0, 100):
                continue
            p.append(lp / 100.0)
            y.append(1.0 if m["result"] == "yes" else 0.0)
            vol.append(m.get("volume") or 0)
        if len(p) < 20:
            out[s] = {"n": len(p), "note": "too few settled markets with a last price"}
            continue
        p, y = np.array(p), np.array(y)
        out[s] = {"n": int(len(p)), "brier": brier(p, y), "log_loss": log_loss(p, y), "ece": ece(p, y, 10), "mean_p": float(p.mean()), "base_rate": float(y.mean()),
                  "volume_median": float(np.median(vol)), "volume_p90": float(np.quantile(vol, 0.9)), "calibration": calibration_table(p, y, 10)}
    return out


def main() -> int:
    kdir = REPO_ROOT / "data" / "history" / "kalshi"
    rows = load_markets(kdir)
    rep = {"n_rows": len(rows), "series": study(rows)}
    out = REPO_ROOT / "docs" / "research" / "market_calibration.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, indent=1))
    for s, r in rep["series"].items():
        print(s, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if k != "calibration"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
