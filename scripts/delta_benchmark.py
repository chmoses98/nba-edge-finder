"""Benchmark the delta-encoded archive against the real archived boards.

Everything here runs on boards actually captured from Kalshi and stored on the `data-archive`
branch. Where a measurement needs conditions the real archive does not provide -- notably a chain
deep enough to time reconstruction at realistic depth -- the board CONTENT stays real and only the
capture instants are synthesised, and the output says so. No synthetic market data is used for any
size or change-rate figure.

Run: python scripts/delta_benchmark.py --archive <checkout of data-archive> [--json out.json]
"""

from __future__ import annotations

import argparse
import gzip
import json
import statistics as st
import tempfile
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from nba_edge.archive.delta import (
    DeltaChainError,
    board_sha256,
    build_delta,
    canonical_board,
    read_rows,
)
from nba_edge.archive.ledger import Ledger
from nba_edge.archive.reconstruct import chain_tip, reconstruct_at, verify_archive, write_board
from nba_edge.timeutil import parse_iso

# The cadence the capture worker implements, integrated over a ~16h active day: 15 min far from tip,
# tightening to 5 min inside T-30m. 98 ticks/day is the figure the storage projection uses.
TICKS_PER_DAY = 98
SEASON_DAYS = 180


def load_boards(archive: Path) -> list[tuple[str, datetime, dict, int]]:
    out = []
    for p in sorted((archive / "kalshi" / "markets").rglob("*.jsonl*")):
        rows = read_rows(p)
        stamp = rows[0].get("_observed_at_utc") if rows else None
        if stamp is None:
            continue
        out.append((p.name, parse_iso(stamp), canonical_board(rows), p.stat().st_size))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True, type=Path)
    ap.add_argument("--json", default=None, type=Path)
    a = ap.parse_args()

    boards = load_boards(a.archive)
    if len(boards) < 2:
        print(f"need at least 2 real boards, found {len(boards)}")
        return 1
    report: dict = {"n_real_boards": len(boards)}

    # 1. bytes per full snapshot -----------------------------------------------------------------
    sizes = [sz for _n, _t, _b, sz in boards]
    counts = [len(b) for _n, _t, b, _sz in boards]
    report["full_snapshot_bytes"] = {
        "mean": round(st.mean(sizes)), "median": round(st.median(sizes)),
        "min": min(sizes), "max": max(sizes),
        "markets_mean": round(st.mean(counts)),
        "bytes_per_market": round(st.mean(sizes) / st.mean(counts), 1),
    }
    print("\n=== 1. bytes per FULL snapshot (real boards) ===")
    for _n, t, b, sz in boards:
        print(f"  {t.strftime('%m-%d %H:%M:%S')}  markets={len(b):>5}  {sz:>8,} B")
    print(f"  mean {st.mean(sizes):,.0f} B over {len(sizes)} boards, {st.mean(sizes)/st.mean(counts):.1f} B/market")

    # 2-3. change rate and delta size between consecutive real boards ----------------------------
    steps = []
    for i in range(1, len(boards)):
        (_n0, t0, b0, _), (_n1, t1, b1, sz1) = boards[i - 1], boards[i]
        d = build_delta(b0, b1, captured_at=t1, run_id="bench", seq=i,
                        base_path="bench", base_sha256="x", base_captured_at="y")
        raw = len(gzip.compress(d.to_bytes()))
        gap_min = (t1 - t0).total_seconds() / 60
        steps.append({
            "from": t0.isoformat(), "to": t1.isoformat(), "gap_minutes": round(gap_min, 1),
            "n_markets": len(b1), "n_changed": d.n_changed,
            "changed_pct": round(100 * d.n_changed / len(b1), 3),
            "delta_bytes": raw, "full_bytes": sz1, "ratio": round(raw / sz1, 5),
            "intraday": gap_min <= 60,
        })
    print("\n=== 2-3. change rate and delta size between consecutive real boards ===")
    print(f"  {'gap':>8}  {'changed':>8}  {'pct':>7}  {'delta B':>9}  {'full B':>9}  {'ratio':>8}")
    for s in steps:
        tag = "" if s["intraday"] else "   (days apart -- upper bound, not a tick)"
        print(f"  {s['gap_minutes']:>6.1f}m  {s['n_changed']:>8}  {s['changed_pct']:>6.2f}%  "
              f"{s['delta_bytes']:>9,}  {s['full_bytes']:>9,}  {s['ratio']:>8.4f}{tag}")

    intraday = [s for s in steps if s["intraday"]]
    report["steps"] = steps
    if intraday:
        report["intraday"] = {
            "n_steps": len(intraday),
            "changed_pct_mean": round(st.mean([s["changed_pct"] for s in intraday]), 3),
            "changed_pct_median": round(st.median([s["changed_pct"] for s in intraday]), 3),
            "delta_bytes_mean": round(st.mean([s["delta_bytes"] for s in intraday])),
            "delta_bytes_median": round(st.median([s["delta_bytes"] for s in intraday])),
            "ratio_mean": round(st.mean([s["ratio"] for s in intraday]), 5),
        }
        print(f"\n  intraday steps (<=60 min apart): n={len(intraday)}, "
              f"changed {report['intraday']['changed_pct_mean']:.2f}% mean, "
              f"delta {report['intraday']['delta_bytes_mean']:,} B mean, "
              f"{report['intraday']['ratio_mean']:.4f} of a full snapshot")

    # 4. seasonal projection ---------------------------------------------------------------------
    full_b = st.mean(sizes)
    delta_b = report["intraday"]["delta_bytes_mean"] if intraday else st.mean([s["delta_bytes"] for s in steps])
    ck_every = 24
    before_gb = full_b * TICKS_PER_DAY * SEASON_DAYS / 1024**3
    # One checkpoint per `ck_every` ticks, deltas for the rest.
    per_day = (TICKS_PER_DAY / ck_every) * full_b + (TICKS_PER_DAY - TICKS_PER_DAY / ck_every) * delta_b
    after_gb = per_day * SEASON_DAYS / 1024**3
    report["projection"] = {
        "ticks_per_day": TICKS_PER_DAY, "season_days": SEASON_DAYS, "checkpoint_every": ck_every,
        "before_gb": round(before_gb, 3), "after_gb": round(after_gb, 3),
        "reduction_pct": round(100 * (1 - after_gb / before_gb), 2),
        "factor": round(before_gb / after_gb, 1),
    }
    print("\n=== 4. projected seasonal storage (markets board only) ===")
    print(f"  before (full every tick) : {before_gb:7.3f} GB")
    print(f"  after  (ck every {ck_every} + deltas): {after_gb:7.3f} GB")
    print(f"  reduction: {report['projection']['reduction_pct']:.1f}%  ({report['projection']['factor']}x smaller)")

    # 5-6. reconstruction: correctness against real snapshots, then speed -----------------------
    print("\n=== 5-6. reconstruction against REAL boards ===")
    same_day: dict[str, list] = {}
    for n, t, b, sz in boards:
        same_day.setdefault(t.strftime("%Y-%m-%d"), []).append((n, t, b, sz))
    chain_day = max(same_day.values(), key=len)
    print(f"  using the {len(chain_day)} real boards from {chain_day[0][1].date()} "
          f"(one UTC day, genuine capture instants)")

    integrity = {"ticks_verified": 0, "hash_matches": 0, "field_for_field_matches": 0, "failures": []}
    timings = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        raw_by_ts = {}
        for name, t, _b, _sz in chain_day:
            src = next(p for p in (a.archive / "kalshi" / "markets").rglob(name))
            rows = read_rows(src)
            raw_by_ts[t] = rows
            # One ledger per board, carrying that capture's REAL run id.
            write_board(Ledger(root, run_id=str(rows[0].get("_run_id", "bench"))), rows,
                        observed_at=t, checkpoint_every=999)
        lg = Ledger(root, run_id="bench")
        ck, deltas = chain_tip(lg)
        print(f"  wrote 1 checkpoint + {len(deltas)} delta(s); "
              f"checkpoint {(root / ck.path).stat().st_size:,} B, "
              f"deltas {sum((root / e.path).stat().st_size for e in deltas):,} B total")

        for t, rows in sorted(raw_by_ts.items()):
            t1 = time.perf_counter()
            r = reconstruct_at(root, t)
            timings.append(time.perf_counter() - t1)
            integrity["ticks_verified"] += 1
            want, got = canonical_board(rows), canonical_board(r.rows)
            if board_sha256(want) == board_sha256(got):
                integrity["hash_matches"] += 1
            else:
                integrity["failures"].append(f"{t.isoformat()}: canonical hash mismatch")
            by_ticker = sorted(rows, key=lambda x: str(x.get("ticker")))
            got_rows = sorted(r.rows, key=lambda x: str(x.get("ticker")))
            if by_ticker == got_rows:
                integrity["field_for_field_matches"] += 1
            else:
                integrity["failures"].append(f"{t.isoformat()}: field-for-field mismatch")
            print(f"    {t.strftime('%H:%M:%S')}  source={r.source:<18} deltas={r.n_deltas_applied}  "
                  f"hash={'OK' if board_sha256(want) == board_sha256(got) else 'MISMATCH'}  "
                  f"fields={'OK' if by_ticker == got_rows else 'MISMATCH'}")

        # Depth is measured twice, because the two answers differ several-fold and only one of them
        # is the number you would actually see. Cost is driven by how many markets each delta
        # TOUCHES -- every touched market is re-digested -- so cycling boards that include the
        # 100%-change transition measures a pathological case rather than a tick.
        ordered_boards = [rows for _t, rows in sorted(raw_by_ts.items())]
        scenarios = {
            # The two boards 4 minutes apart: ~17% of markets change per tick, the steady-state rate.
            "typical_tick": [ordered_boards[0], ordered_boards[1]],
            # Includes the step where a capture-code change added a field to every market, so every
            # delta rewrites the whole board. An upper bound.
            "worst_case_full_churn": ordered_boards,
        }
        deep_report = {}
        for label, cycle in scenarios.items():
            sub = Path(td) / f"deep_{label}"
            sub.mkdir()
            base_t = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)
            for i in range(25):
                rows = cycle[i % len(cycle)]
                write_board(Ledger(sub, run_id=str(rows[0].get("_run_id", "bench"))), rows,
                            observed_at=base_t + timedelta(minutes=10 * i), checkpoint_every=999)
            times = []
            for _ in range(5):
                t1 = time.perf_counter()
                reconstruct_at(sub, base_t + timedelta(minutes=10 * 24))
                times.append(time.perf_counter() - t1)
            _ck2, d2 = chain_tip(Ledger(sub, run_id="bench"))
            changed = [int((e.meta or {}).get("n_changed", 0)) for e in d2]
            deep_report[label] = {
                "n_deltas": len(d2),
                "mean_markets_touched_per_delta": round(st.mean(changed)) if changed else 0,
                "seconds_median": round(st.median(times), 4),
                "seconds_max": round(max(times), 4),
            }
            print(f"  {len(d2)}-delta chain, {label:<22}: {st.median(times) * 1000:>6.0f} ms median "
                  f"({deep_report[label]['mean_markets_touched_per_delta']:>5} markets touched/delta)")
        report["reconstruction"] = {
            "real_chain_ticks": len(raw_by_ts),
            "real_chain_seconds_mean": round(st.mean(timings), 4),
            "deep": deep_report,
        }
        print(f"  real 3-tick chain, genuine instants   : {st.mean(timings) * 1000:>6.0f} ms mean")

    report["integrity"] = integrity
    print(f"\n=== 6. integrity: {integrity['hash_matches']}/{integrity['ticks_verified']} hash, "
          f"{integrity['field_for_field_matches']}/{integrity['ticks_verified']} field-for-field ===")
    for f in integrity["failures"]:
        print("  FAILURE:", f)

    # 7. failure and recovery --------------------------------------------------------------------
    print("\n=== 7. failure / recovery behaviour ===")
    behaviours = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lg = Ledger(root, run_id="bench")
        for name, t, _b, _sz in chain_day:
            src = next(p for p in (a.archive / "kalshi" / "markets").rglob(name))
            rows = read_rows(src)
            write_board(Ledger(root, run_id=str(rows[0].get("_run_id", "bench"))), rows,
                        observed_at=t, checkpoint_every=999)
        _ck, deltas = chain_tip(lg)
        tip = max(parse_iso(e.observed_at_utc) for e in deltas)

        ok_before = verify_archive(root)
        behaviours.append({"case": "healthy chain", "verify_ok": ok_before["n_ok"], "verify_broken": ok_before["n_broken"]})
        print(f"  healthy chain              : verify n_ok={ok_before['n_ok']} n_broken={ok_before['n_broken']}")

        target = root / deltas[0].path
        payload = json.loads(gzip.decompress(target.read_bytes()))
        payload["changed"] = {**payload.get("changed", {}), "__INJECTED__": {"x": 1}}
        target.write_bytes(gzip.compress(json.dumps(payload).encode()))
        try:
            reconstruct_at(root, tip)
            behaviours.append({"case": "corrupted delta", "result": "DID NOT FAIL -- BUG"})
            print("  corrupted delta            : DID NOT FAIL -- BUG")
        except DeltaChainError as exc:
            behaviours.append({"case": "corrupted delta", "result": "failed closed", "error": str(exc)[:110]})
            print(f"  corrupted delta            : failed closed -- {str(exc)[:80]}")
        rep = verify_archive(root)
        print(f"  verify after corruption    : n_ok={rep['n_ok']} n_broken={rep['n_broken']} (reports, does not raise)")

        target.unlink()
        try:
            reconstruct_at(root, tip)
            behaviours.append({"case": "deleted delta", "result": "DID NOT FAIL -- BUG"})
            print("  deleted delta              : DID NOT FAIL -- BUG")
        except DeltaChainError as exc:
            behaviours.append({"case": "deleted delta", "result": "failed closed", "error": str(exc)[:110]})
            print(f"  deleted delta              : failed closed -- {str(exc)[:80]}")

        res = write_board(lg, read_rows(next(p for p in (a.archive / "kalshi" / "markets").rglob(chain_day[0][0]))),
                          observed_at=tip + timedelta(minutes=10), checkpoint_every=999)
        behaviours.append({"case": "next capture after corruption", "encoding": res["encoding"], "reason": res.get("reason")})
        print(f"  next capture after damage  : wrote a {res['encoding']} -- {str(res.get('reason'))[:70]}")
        r = reconstruct_at(root, tip + timedelta(minutes=10))
        print(f"  reconstruct after recovery : source={r.source} markets={r.n_markets} (archive reconstructible again)")
        behaviours.append({"case": "recovered", "source": r.source, "n_markets": r.n_markets})
    report["failure_recovery"] = behaviours

    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(report, indent=2, default=str) + "\n")
        print(f"\nwrote {a.json}")
    return 0 if not integrity["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
