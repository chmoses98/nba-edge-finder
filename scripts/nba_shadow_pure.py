"""NBA PURE shadow collection CLI (research only). See docs/research/SHADOW_PURE_NBA.md.

    # live (the scheduled workflow): store = checkout of the nba-shadow-pure data branch
    python scripts/nba_shadow_pure.py outcomes --store data/shadow_pure/nba
    python scripts/nba_shadow_pure.py capture  --store data/shadow_pure/nba --slot auto --archive data/archive
    python scripts/nba_shadow_pure.py evaluate --store data/shadow_pure/nba --archive data/archive
    python scripts/nba_shadow_pure.py verify   --store data/shadow_pure/nba --base-ref origin/nba-shadow-pure

    # dry run (pull_request / dispatch): throwaway store, nothing committed
    python scripts/nba_shadow_pure.py dry-run --out shadow_dry --archive data/archive [--replay-date 2026-10-10]
"""

from __future__ import annotations

import argparse
import gzip
import json
import subprocess
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nba_edge.shadow import collect as C  # noqa: E402
from nba_edge.shadow import evaluate as E  # noqa: E402
from nba_edge.shadow.store import ShadowStore, check_immutable  # noqa: E402
from nba_edge.timeutil import ET, iso, parse_iso, utcnow  # noqa: E402


def _dump(obj) -> None:
    print(json.dumps(obj, indent=1, default=str)[:20000])


def _listings_after(store: ShadowStore, rec: dict, archive: Path | None, data_root: Path) -> dict | None:
    """Market listing snapshot at the capture's as_of -- strictly after the projections were written."""
    if not rec.get("games"):
        return None
    tg, pg, _src, _info = C.assemble_history(data_root, store, parse_iso(rec["as_of"]))
    return C.capture_listings(store, archive, parse_iso(rec["as_of"]), rec["games"], pg, rec["slot"], rec["mode"])


def cmd_capture(a) -> int:
    store = ShadowStore(a.store)
    slots = C.SLOTS if a.slot == "auto" else (a.slot,)
    out = []
    for slot in slots:
        rec = C.capture(store, a.data, slot, C.http_fetcher, dates=a.dates.split(",") if a.dates else None, include_preseason=a.include_preseason,
                        n_sims=a.sims)
        rec["market_listings"] = _listings_after(store, rec, a.archive, a.data)
        out.append({k: rec.get(k) for k in ("slot", "mode", "as_of", "games", "refused", "files", "market_listings")} | {"n_skipped": len(rec.get("skipped", []))})
    _dump(out)
    return 0


def cmd_outcomes(a) -> int:
    store = ShadowStore(a.store)
    dates = a.dates.split(",") if a.dates else C.default_dates(utcnow(), back=a.back)
    _dump(C.collect_outcomes(store, dates, C.http_fetcher, include_preseason=a.include_preseason))
    return 0


def cmd_evaluate(a) -> int:
    store = ShadowStore(a.store)
    rep = E.evaluate(store, utcnow(), include_replay=a.include_replay, n_boot=a.boot, archive_root=a.archive)
    _dump({k: rep[k] for k in ("evaluated_at", "n_projection_rows", "n_outcome_rows", "n_listing_rows", "written", "reconciliation_summary")}
          | {"slots": {s: {c: v[c].get("n_player_game_stat_rows") for c in ("all_eligible", "pregame_market_listed")} for s, v in rep["by_slot"].items()}})
    return 0


def _gate_cli_validate(store: ShadowStore) -> list[dict]:
    """Run the vendored gate's own CLI (``validate --require-v1``) on every stored projection file."""
    res = []
    with tempfile.TemporaryDirectory() as td:
        for e in store.entries("projections/"):
            plain = Path(td) / (Path(e.path).name.replace(".gz", ""))
            plain.write_bytes(gzip.decompress((store.root / e.path).read_bytes()))
            p = subprocess.run([sys.executable, "-I", str(C.GATE_PATH), "validate", "--forecasts", str(plain), "--require-v1"],
                               capture_output=True, text=True, check=False)
            summ = json.loads(p.stdout) if p.stdout.strip().startswith("{") else {"raw": p.stdout[-500:], "stderr": p.stderr[-500:]}
            res.append({"path": e.path, "exit": p.returncode, "n": summ.get("n"), "passed": summ.get("passed"), "warnings": summ.get("warnings")})
    return res


def cmd_verify(a) -> int:
    store = ShadowStore(a.store)
    problems = store.verify()
    rep = {"internal_problems": problems}
    if a.base_ref:
        im = check_immutable(Path(a.store), a.base_ref)
        rep["immutability"] = {"base_ref": im.base_ref, "checked_files": im.checked_files, "problems": im.problems}
        problems = problems + im.problems
    if a.gate:
        rep["gate_validate"] = _gate_cli_validate(store)
        problems = problems + [f"gate refused {g['path']}" for g in rep["gate_validate"] if g["exit"] != 0]
    _dump(rep)
    return 1 if problems else 0


def cmd_dry_run(a) -> int:
    """Everything the live job does, against a throwaway store: live capture of today's not-yet-started
    slate (slot window ignored; still refuses at/after tip), a REPLAY capture of a recent completed date,
    outcomes for that date, the market snapshot, evaluation, verification and gate validation."""
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    store = ShadowStore(out_dir / "store", run_id="dryrun")
    now = utcnow()
    today = now.astimezone(ET).date()
    summary: dict = {"started_at": iso(now), "today_et": today.isoformat(), "steps": {}}
    # 1. live capture (as_of = now, strictly before every tip) of today's not-yet-started games and
    #    tomorrow's slate, any season type; the slot window is ignored, the kickoff rule is not
    live = C.capture(store, a.data, "morning", C.http_fetcher, dates=[today.isoformat(), (today + timedelta(days=1)).isoformat()],
                     dry_run=True, include_preseason=True, ignore_slot_window=True, n_sims=a.sims)
    live["market_listings"] = _listings_after(store, live, a.archive, a.data)
    summary["steps"]["live_capture_today"] = {k: live.get(k) for k in ("mode", "as_of", "games", "refused", "files", "market_listings")} | {
        "skipped": live.get("skipped"), "schedule": live.get("schedule")}
    # 2. replay of the most recent date (<= yesterday) with completed games
    replay_dates = [a.replay_date] if a.replay_date else [(today - timedelta(days=i)).isoformat() for i in range(1, 8)]
    replay_date, rec = None, None
    for d in replay_dates:
        games, _prov = C.slate([d], C.http_fetcher)
        if any(st == "final" for _g, st in games):
            replay_date = d
            break
    if replay_date:
        as_of = datetime.fromisoformat(replay_date).replace(hour=15, tzinfo=UTC)  # 11:00 ET: the morning slot
        rec = C.capture(store, a.data, "morning", C.http_fetcher, dates=[replay_date], replay_as_of=as_of, dry_run=True, include_preseason=True,
                        n_sims=a.sims)
        rec["market_listings"] = _listings_after(store, rec, a.archive, a.data)
        summary["steps"]["replay_capture"] = {k: rec.get(k) for k in ("mode", "as_of", "games", "refused", "files", "market_listings", "skipped")}
        # 3. outcomes for the replayed date (fetched now, after as_of: never inputs to the replay)
        summary["steps"]["outcomes"] = C.collect_outcomes(store, [replay_date], C.http_fetcher, include_preseason=True)
    else:
        summary["steps"]["replay_capture"] = {"status": "NO_COMPLETED_GAMES_IN_LAST_7_DAYS"}
    # 4. evaluation over everything matured (replay rows included and labelled)
    rep = E.evaluate(store, utcnow(), include_replay=True, n_boot=a.boot, archive_root=a.archive)
    summary["steps"]["evaluate"] = {k: rep.get(k) for k in ("n_projection_rows", "n_outcome_rows", "n_listing_rows", "written", "reconciliation_summary")}
    summary["steps"]["evaluate"]["by_slot"] = {
        s: {"matured_games": v["matured_games"], **{c: {"n_rows": v[c].get("n_player_game_stat_rows"), "n_games": v[c].get("n_games"),
                                                         "points_unc": (v[c].get("final_stats", {}).get("points", {}).get("unc") or {}).get("sim_rotation"),
                                                         "gate_coverage": {k: g["coverage"] for k, g in v[c].get("pure_gate_compare_champion_vs_ewm5", {}).items()}}
                                                     for c in ("all_eligible", "pregame_market_listed")},
            "non_eligible_participants": v.get("non_eligible_participants")}
        for s, v in rep["by_slot"].items()}
    # 5. verification: internal hash chain, gate CLI on every projection file
    summary["steps"]["verify"] = {"internal_problems": store.verify(), "gate_validate": _gate_cli_validate(store)}
    (out_dir / "evaluation.json").write_text(json.dumps(rep, indent=1, default=str))
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1, default=str))
    _dump(summary)
    bad = summary["steps"]["verify"]["internal_problems"] or any(g["exit"] != 0 for g in summary["steps"]["verify"]["gate_validate"])
    return 1 if bad else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("capture", "outcomes", "evaluate", "verify", "dry-run"):
        s = sub.add_parser(name)
        s.add_argument("--data", type=Path, default=ROOT / "data")
        s.add_argument("--archive", type=Path, default=None, help="read-only checkout of the data-archive branch (market listings)")
        if name != "dry-run":
            s.add_argument("--store", type=Path, required=True)
        if name in ("capture", "outcomes"):
            s.add_argument("--dates", default="", help="comma list of ET dates (default: today / last --back days)")
            s.add_argument("--include-preseason", action="store_true")
        if name == "capture":
            s.add_argument("--slot", choices=("auto", *C.SLOTS), default="auto")
            s.add_argument("--sims", type=int, default=2000)
        if name == "outcomes":
            s.add_argument("--back", type=int, default=3)
        if name in ("evaluate", "dry-run"):
            s.add_argument("--boot", type=int, default=1000)
        if name == "evaluate":
            s.add_argument("--include-replay", action="store_true")
        if name == "verify":
            s.add_argument("--base-ref", default="")
            s.add_argument("--gate", action="store_true")
        if name == "dry-run":
            s.add_argument("--out", required=True)
            s.add_argument("--replay-date", default="")
            s.add_argument("--sims", type=int, default=2000)
    a = ap.parse_args(argv)
    return {"capture": cmd_capture, "outcomes": cmd_outcomes, "evaluate": cmd_evaluate, "verify": cmd_verify, "dry-run": cmd_dry_run}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
