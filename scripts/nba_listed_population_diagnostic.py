"""DIAGNOSTIC ONLY: which eligible player-games had a listed player-prop contract.

This is the one place in the W1-C experiment that opens a market file, and it reads exactly two
things from it: the ticker (game identity) and the player uuid. No price, quote, settlement value
or volume is read. The output is a set of (game_id, player_id) keys used solely to show how a
*listing-selected* evaluation population differs from the complete eligible population -- the
observation-choice question in WAVE1 W1-C step 3. It never feeds a forecast, a fit or a selection
of the scored population.

    python scripts/nba_listed_population_diagnostic.py --out $SCRATCH/nba/run/listed.parquet
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nba_edge.data.history import load_team_games  # noqa: E402
from nba_edge.identity.players import PlayerRegistry  # noqa: E402
from nba_edge.identity.teams import registry  # noqa: E402
from nba_edge.kalshi.ticker import parse_ticker  # noqa: E402

SERIES = ("KXNBAPTS", "KXNBAREB", "KXNBAAST", "KXNBA3PT")


def listed_keys(data_root: Path) -> tuple[pd.DataFrame, dict]:
    reg = registry()
    preg = PlayerRegistry.load()
    uuid_to_id = {r.aliases["kalshi_uuid"]: r.nba_id for r in preg.records.values() if "kalshi_uuid" in r.aliases}
    tg = load_team_games(data_root / "history", ["2025-26"])
    home = tg[tg["home"] == True]  # noqa: E712
    gid = {}
    for r in home.itertuples(index=False):
        try:
            gid[(str(r.game_date_et), reg.by_id(int(r.team_id)).tricode, reg.by_id(int(r.opp_team_id)).tricode)] = str(r.game_id)
        except Exception:  # noqa: BLE001 - unknown team id: counted below as unmatched
            continue
    rows, stats = set(), {"markets": 0, "unparsed": 0, "no_game": 0, "no_player": 0}
    for s in SERIES:
        fp = data_root / "history" / "kalshi" / f"markets_{s}.jsonl.gz"
        if not fp.exists():
            continue
        with gzip.open(fp, "rt") as fh:
            for line in fh:
                m = json.loads(line)
                stats["markets"] += 1
                pt = parse_ticker(m.get("ticker", ""), reg.tricodes)
                if not pt.game_date or not pt.home_tricode:
                    stats["unparsed"] += 1
                    continue
                g = gid.get((pt.game_date.isoformat(), pt.home_tricode, pt.away_tricode))
                if g is None:
                    stats["no_game"] += 1
                    continue
                pid = uuid_to_id.get(((m.get("custom_strike") or {}).get("basketball_player")) or "")
                if pid is None:
                    stats["no_player"] += 1
                    continue
                rows.add((g, int(pid)))
    df = pd.DataFrame(sorted(rows), columns=["game_id", "player_id"])
    stats["listed_player_games"] = len(df)
    return df, stats


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=ROOT / "data")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    df, stats = listed_keys(a.data)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(a.out, index=False)
    print(json.dumps(stats, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
