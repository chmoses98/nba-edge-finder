"""Before/after slate storage on REAL archived passes (read-only). Usage: python scripts/slate_storage_benchmark.py ARCHIVE_ROOT [--per-day 3] [--json out.json]

Old format per pass: slate.json + packet.json (indent=1) in the pass dir, copied again into slates/latest (overwritten, not growing).
New format per pass: slate.json.gz + packet.json.gz (compact, gzip) + slate.md. Verifies that decoding the new bytes reproduces the old parsed JSON exactly.
"""

from __future__ import annotations

import argparse
import gzip
import json
import time
from pathlib import Path

from nba_edge.archive.slate_store import dumps_compact, gz_bytes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--per-day", type=int, default=3)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()
    days = sorted((a.root / "slates").glob("dt=*"))
    old = new = n = 0
    t_enc = 0.0
    per_day = []
    for d in days:
        passes = sorted(p for p in d.iterdir() if (p / "packet.json").exists())
        d_old = sum(f.stat().st_size for p in passes for f in p.iterdir())
        sample = passes[:: max(1, len(passes) // a.per_day)][: a.per_day]
        s_old = s_new = 0
        for p in sample:
            for name in ("slate.json", "packet.json"):
                raw = (p / name).read_bytes()
                obj = json.loads(raw)
                t0 = time.perf_counter()
                gz = gz_bytes(dumps_compact(obj))
                t_enc += time.perf_counter() - t0
                assert json.loads(gzip.decompress(gz)) == obj, (p, name)  # lossless
                s_old += len(raw)
                s_new += len(gz)
            s_old += (p / "slate.md").stat().st_size
            s_new += (p / "slate.md").stat().st_size
            n += 1
        old += s_old
        new += s_new
        per_day.append({"day": d.name[3:], "passes": len(passes), "bytes_old_actual": d_old, "ratio_sampled": round(s_old / max(1, s_new), 1)})
    ratio = old / max(1, new)
    days_n = len(per_day)
    mean_day_old = sum(x["bytes_old_actual"] for x in per_day) / max(1, days_n)
    out = {"days": days_n, "sampled_passes": n, "bytes_old_sampled": old, "bytes_new_sampled": new, "ratio": round(ratio, 2), "encode_seconds_per_pass": round(t_enc / max(1, n), 3),
           "mean_day_bytes_old": int(mean_day_old), "mean_day_bytes_new": int(mean_day_old / ratio), "per_day": per_day}
    for label, season_days in (("season_243d", 243),):
        out[f"{label}_old_gb"] = round(mean_day_old * season_days / 1e9, 1)
        out[f"{label}_new_gb"] = round(mean_day_old / ratio * season_days / 1e9, 2)
    print(json.dumps(out, indent=1))
    if a.json:
        a.json.write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
