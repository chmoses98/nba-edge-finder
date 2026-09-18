"""Does DATA_ONLY add information beyond the Kalshi pregame price? (research questions 17-19)

Joins the walk-forward per-game CSV (sim + Elo probabilities) with Kalshi pregame moneyline prices derived from
hourly candles (last candle strictly before tip, home-team market). Reports log loss / Brier for market, sim, Elo,
and an IN-SAMPLE logistic blend of market and sim (weight reported for reference only — not a production weight).
Run: ``python -m nba_edge.research.market_vs_sim --wf docs/research/wf_v5.csv``.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from nba_edge.config import REPO_ROOT
from nba_edge.data.history import load_team_games
from nba_edge.evaluation.metrics import brier, ece, log_loss
from nba_edge.identity.teams import registry
from nba_edge.kalshi.ticker import parse_ticker
from nba_edge.research.market_calibration import _cents, load_tip_times
from nba_edge.timeutil import parse_iso


def pregame_prices(kdir: Path) -> pd.DataFrame:
    tips = load_tip_times()
    last: dict[str, tuple[int, float]] = {}
    with gzip.open(kdir / "candles_KXNBAGAME.jsonl.gz", "rt") as f:
        for line in f:
            c = json.loads(line)
            pt = parse_ticker(c["ticker"], registry().tricodes)
            if not pt.game_date:
                continue
            tip = tips.get((pt.game_date.isoformat(), pt.away_tricode, pt.home_tricode))
            if not tip:
                continue
            try:
                ts = int(c.get("end_period_ts"))
            except (TypeError, ValueError):
                continue
            if ts >= int(parse_iso(tip).timestamp()):
                continue
            bid, ask = _cents((c.get("yes_bid") or {}).get("close")), _cents((c.get("yes_ask") or {}).get("close"))
            if bid is None or ask is None or bid <= 0 or ask >= 100 or ask - bid > 10:
                continue
            if c["ticker"] not in last or ts > last[c["ticker"]][0]:
                last[c["ticker"]] = (ts, (bid + ask) / 200.0, pt.game_date.isoformat(), pt.home_tricode, pt.away_tricode, pt.market_suffix.upper())
    rows = []
    for t, (ts, p, d, h, a, suffix) in last.items():
        if suffix == h:  # home-team market -> P(home win)
            rows.append({"date": d, "home": h, "away": a, "p_market": p, "ticker": t, "ts": ts})
    return pd.DataFrame(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wf", default=str(REPO_ROOT / "docs" / "research" / "wf_v5.csv"))
    ap.add_argument("--out", default=str(REPO_ROOT / "docs" / "research" / "market_vs_sim.json"))
    a = ap.parse_args(argv)
    wf = pd.read_csv(a.wf)
    hist = REPO_ROOT / "data" / "history"
    seasons = sorted({p.stem.split("_")[-1] for p in (hist / "espn").glob("team_games_*.parquet")})
    tg = load_team_games(hist, seasons)
    reg = registry()
    home_rows = tg[tg["home"] == True][["game_id", "team_id", "opp_team_id"]]  # noqa: E712
    home_rows = home_rows.assign(home=[reg.by_id(int(t)).tricode for t in home_rows["team_id"]], away=[reg.by_id(int(t)).tricode for t in home_rows["opp_team_id"]])
    wf = wf.merge(home_rows[["game_id", "home", "away"]], on="game_id", how="left")
    mk = pregame_prices(hist / "kalshi")
    df = wf.merge(mk, on=["date", "home", "away"], how="inner")
    y = df["y"].to_numpy()
    out = {"n_joined": int(len(df)), "n_walk_forward": int(len(wf))}
    for name, col in (("market", "p_market"), ("sim", "p_sim"), ("elo", "p_elo")):
        p = np.clip(df[col].to_numpy(), 1e-3, 1 - 1e-3)
        out[name] = {"log_loss": log_loss(p, y), "brier": brier(p, y), "ece": ece(p, y, 10)}
    # in-sample logistic blend on the logit scale: z = a + w*logit(market) + (1-w)*logit(sim)
    lm, ls = np.log(df.p_market / (1 - df.p_market)), np.log(np.clip(df.p_sim, 1e-3, 1 - 1e-3) / (1 - np.clip(df.p_sim, 1e-3, 1 - 1e-3)))
    best = None
    for w in np.linspace(0, 1, 21):
        z = w * lm + (1 - w) * ls
        p = 1 / (1 + np.exp(-z))
        ll = log_loss(np.clip(p, 1e-3, 1 - 1e-3), y)
        if best is None or ll < best[1]:
            best = (float(w), ll)
    out["in_sample_blend"] = {"market_weight": best[0], "log_loss": best[1], "note": "in-sample on the same games; reference only, not a production weight"}
    out["corr_sim_market_logit"] = float(np.corrcoef(lm, ls)[0, 1])
    Path(a.out).write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
