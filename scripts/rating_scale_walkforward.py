"""Phase 8: re-estimate `rating_scale` with tuning and evaluation on disjoint seasons.

`rating_scale` (currently 1.6) multiplies each team's opponent-adjusted rating deviation from the
league mean, so it controls how far apart the simulator spreads team strength. It was set from a
note that "sim margins correlate 0.96 with Elo but are compressed ~0.6x" -- and, critically, it was
fitted on the same ~300 games it was then reported on. Roughly 0.047 nats of the reported
0.569 -> 0.522 gain is therefore in-sample, which is larger than the sim-vs-Elo gap it was cited to
support. That is not a basis for a production constant.

This script fixes the methodology rather than the number:

  TUNE     seasons 2023-24 + 2024-25, evaluated on the tail of 2024-25
  HOLDOUT  seasons 2023-24 + 2024-25 + 2025-26, evaluated on the tail of 2025-26

The two evaluation sets are in different seasons and share no games. The grid is searched on TUNE
only; the winner and the incumbent 1.6 are then run once on HOLDOUT. Whatever HOLDOUT says is the
answer, including "the incumbent was fine" or "none of these helps".

This also tests the under-dispersion diagnosed in MONEYLINE_MODEL_VS_MARKET.md: the model's win
probabilities are shrunk toward 0.5, and a larger rating_scale is the most direct lever on that. If
under-dispersion is really a rating_scale problem, a larger value should win on the holdout.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nba_edge.config import REPO_ROOT  # noqa: E402
from nba_edge.research.walk_forward import run  # noqa: E402

TUNE_SEASONS = ["2023-24", "2024-25"]
HOLDOUT_SEASONS = ["2023-24", "2024-25", "2025-26"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", default="1.0,1.3,1.6,1.9,2.2")
    ap.add_argument("--games", type=int, default=400)
    ap.add_argument("--sims", type=int, default=8000)
    ap.add_argument("--warmup", type=int, default=300)
    ap.add_argument("--hist", default=str(REPO_ROOT / "data" / "history"))
    ap.add_argument("--out", default=str(REPO_ROOT / "docs" / "research" / "rating_scale.json"))
    a = ap.parse_args(argv)

    grid = [float(x) for x in a.grid.split(",")]
    scratch = Path(a.out).parent / "_rs"
    scratch.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    tune = {}
    for s in grid:
        rep = run(TUNE_SEASONS, a.games, a.sims, a.warmup, Path(a.hist), scratch / f"tune_{s}.json", rating_scale=s)
        tune[s] = rep
        print(f"[tune] rating_scale={s}: n={rep.get('n')} log_loss={rep['sim']['log_loss']:.4f} "
              f"brier={rep['sim']['brier']:.4f} ece={rep['sim']['ece']:.4f} "
              f"margin_slope={rep['margin_slope_on_sim']:.3f} ({time.time()-t0:.0f}s)", flush=True)

    best = min(grid, key=lambda s: tune[s]["sim"]["log_loss"])
    print(f"\n[tune] best on TUNE = {best}; now evaluating it and the incumbent 1.6 on the HOLDOUT season", flush=True)

    holdout = {}
    for s in sorted({best, 1.6}):
        rep = run(HOLDOUT_SEASONS, a.games, a.sims, a.warmup, Path(a.hist), scratch / f"hold_{s}.json", rating_scale=s)
        holdout[s] = rep
        print(f"[holdout] rating_scale={s}: n={rep.get('n')} log_loss={rep['sim']['log_loss']:.4f} "
              f"brier={rep['sim']['brier']:.4f} ece={rep['sim']['ece']:.4f} "
              f"elo={rep['elo']['log_loss']:.4f} margin_slope={rep['margin_slope_on_sim']:.3f}", flush=True)

    def slim(r):
        return {k: r[k] for k in ("n", "seasons", "date_range", "rating_scale", "margin_slope_on_sim",
                                  "m_sim_sd_across_games", "sim_margin_mae", "margin_80pct_coverage")} | {
            "sim": {k: r["sim"][k] for k in ("log_loss", "brier", "ece")},
            "elo": {k: r["elo"][k] for k in ("log_loss", "brier", "ece")},
        }

    out = {
        "method": "grid searched on TUNE (tail of 2024-25); winner and incumbent evaluated once on HOLDOUT (tail of 2025-26); the two evaluation sets share no games",
        "grid": grid, "games_per_run": a.games, "n_sims": a.sims,
        "tune": {str(s): slim(r) for s, r in tune.items()},
        "best_on_tune": best,
        "holdout": {str(s): slim(r) for s, r in holdout.items()},
    }
    Path(a.out).write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
