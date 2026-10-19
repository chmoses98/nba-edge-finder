"""Build the small REAL fixture of the paper-engine tests: a mini capture archive (checkpoint + verifiable deltas) holding the real Kalshi
boards of the three 2026-10-20 opening-night games (BOS@DET, PHI@NYK, OKC@SAS; every series Kalshi listed for them) as captured on
2026-10-19 (13:03Z checkpoint and the ticks 16:48Z..18:24Z of the capture worker), with the capture STAMPS shifted forward by exactly one day
(SHIFT) so the boards play the role of "game day, 13:03Z .. T-36min before the 19:00Z tip of BOS@DET": the real horizon geometry the
engine meets on opening day. Row contents are untouched.

    python tests/fixtures/paper/build_fixtures.py <data-archive checkout> [<out dir>]

The deltas are rebuilt with nba_edge.archive.delta.build_delta between the real filtered boards, so the chain verifies (hashes) exactly like
the real archive does. Nothing is invented: rows are the captured rows, restricted to the three games' events.
"""
from __future__ import annotations

import gzip
import sys
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
PF = HERE.parents[2]
sys.path.insert(0, str(PF))

from nba.paper import markets as MK  # noqa: E402
from nba_edge.archive.delta import board_sha256, build_delta, canonical_board  # noqa: E402

SHIFT = timedelta(days=1)
EVENT_KEYS = ("26OCT20BOSDET", "26OCT20PHINYK", "26OCT20OKCSAS")
PICK = ["2026-10-19T13:03:59Z", "2026-10-19T16:48:59Z", "2026-10-19T17:03:59Z", "2026-10-19T17:24:36Z", "2026-10-19T17:54:36Z",
        "2026-10-19T18:09:36Z", "2026-10-19T18:24:36Z"]


def write_chain(root: Path, boards: list[tuple[datetime, dict]], run_id: str = "fixture") -> None:
    """checkpoint for boards[0], deltas (seq 1..) for the rest, in the capture archive layout."""
    import json
    t0, b0 = boards[0]
    day = t0.strftime("%Y-%m-%d")
    stamp = t0.strftime("%Y%m%dT%H%M%SZ")
    rel = f"kalshi/markets/dt={day}/kalshi_markets_{stamp}_{run_id}.jsonl.gz"
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(p, "wt") as f:
        for tk in sorted(b0):
            f.write(json.dumps(b0[tk], sort_keys=True) + "\n")
    base_sha = ""
    prev = b0
    for seq, (t, b) in enumerate(boards[1:], 1):
        d = build_delta(prev, b, captured_at=t, run_id=run_id, seq=seq, base_path=rel, base_sha256=base_sha,
                        base_captured_at=t0.strftime("%Y-%m-%dT%H:%M:%SZ"))
        q = root / f"kalshi/markets_delta/dt={t.strftime('%Y-%m-%d')}/kalshi_markets_delta_{t.strftime('%Y%m%dT%H%M%SZ')}_{run_id}.json.gz"
        q.parent.mkdir(parents=True, exist_ok=True)
        q.write_bytes(gzip.compress(d.to_bytes()))
        prev = b


def main() -> None:
    src = sys.argv[1]
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "market_archive"
    reader = MK.ChainReader(src, "markets")
    want = {MK.parse_ts(x) for x in PICK}
    boards = []
    for dt, b in reader.walk(min(want), max(want)):
        if dt in want and b is not None:
            rows = {tk: dict(r) for tk, r in b.items() if any(k in (r.get("event_ticker") or "") for k in EVENT_KEYS)}
            boards.append((dt, canonical_board(rows.values())))
    boards.sort(key=lambda x: x[0])
    assert len(boards) == len(PICK), (len(boards), len(PICK))
    write_chain(out, [(t + SHIFT, b) for t, b in boards])
    print("wrote", out, [len(b) for _, b in boards], board_sha256(boards[-1][1])[:12])


if __name__ == "__main__":
    main()
