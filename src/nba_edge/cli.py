"""Command-line entry: ``nba <command>``. Each command is a thin wrapper around a module function so the
same code runs locally, in tests, and in GitHub Actions."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from nba_edge.log import get_logger

log = get_logger("nba")


def cmd_discover(args: argparse.Namespace) -> int:
    from nba_edge.config import settings
    from nba_edge.kalshi.client import KalshiClient
    from nba_edge.kalshi.discovery import discover, summary_markdown
    from nba_edge.kalshi.ontology import Ontology

    cfg = settings()
    onto = Ontology.load()
    client = KalshiClient(cfg)
    raw_dir = Path(args.raw_dir) if args.raw_dir else None
    statuses = tuple(args.statuses.split(",")) if args.statuses else ("unopened", "open", "closed", "settled")
    summary = discover(client, onto, raw_dir=raw_dir, statuses=statuses, max_pages_per_status=args.max_pages,
                       include_series=args.include.split(",") if args.include else None)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "discovery_summary.json").write_text(summary.to_json())
    (out / "discovery_summary.md").write_text(summary_markdown(summary))
    print(summary_markdown(summary))
    return 0


def cmd_capture(args: argparse.Namespace) -> int:
    from nba_edge.archive.capture import run_capture
    from nba_edge.archive.reconstruct import DEFAULT_CHECKPOINT_EVERY

    return run_capture(out_root=Path(args.out), statuses=args.statuses.split(","), with_orderbook=args.orderbook,
                       max_orderbooks=args.max_orderbooks, series_filter=args.series.split(",") if args.series else None,
                       delta_encode=not args.full_snapshots,
                       checkpoint_every=args.checkpoint_every or DEFAULT_CHECKPOINT_EVERY)


def cmd_reconstruct(args: argparse.Namespace) -> int:
    """Rebuild the market board as it stood at any past instant, from checkpoint + deltas.

    Fails closed: an incomplete, reordered or corrupt chain raises rather than returning a board
    that cannot be proved. A silently-wrong historical price is worse than no price.
    """
    import gzip
    import json

    from nba_edge.archive.delta import board_sha256, canonical_board, read_rows
    from nba_edge.archive.reconstruct import reconstruct_at
    from nba_edge.timeutil import parse_iso

    r = reconstruct_at(Path(args.archive), parse_iso(args.at))
    print(json.dumps(r.summary(), indent=2))

    if args.compare:
        # Field-for-field against a real full snapshot, not merely hash-for-hash: the hash proves
        # the boards agree, the row comparison proves the reconstruction is usable in its place.
        truth = read_rows(Path(args.compare))
        h1 = board_sha256(canonical_board(r.rows))
        h2 = board_sha256(canonical_board(truth))
        same_hash = h1 == h2
        by_ticker = lambda x: str(x.get("ticker"))  # noqa: E731
        exact = sorted(r.rows, key=by_ticker) == sorted(truth, key=by_ticker)
        print(json.dumps({"compare": str(args.compare), "canonical_hash_match": same_hash,
                          "field_for_field_match": exact, "reconstructed_sha256": h1,
                          "snapshot_sha256": h2}, indent=2))
        if not (same_hash and exact):
            print("reconstruct: MISMATCH against the full snapshot")
            return 1

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(out, "wt", encoding="utf-8") as f:
            for row in r.rows:
                f.write(json.dumps(row, separators=(",", ":"), default=str) + "\n")
        print(f"wrote {len(r.rows)} rows to {out}")
    return 0


def cmd_delta_verify(args: argparse.Namespace) -> int:
    """Walk every delta chain on the archive and report which reconstruct and which do not."""
    import json

    from nba_edge.archive.reconstruct import verify_archive

    report = verify_archive(Path(args.archive))
    print(json.dumps(report, indent=2))
    if report["n_broken"]:
        print(f"delta-verify: {report['n_broken']} chain(s) FAILED")
        return 1
    return 0


def cmd_worker(args: argparse.Namespace) -> int:
    """Run one long-lived capture worker, then hand over to its successor.

    GitHub's scheduler delivered ~3.9% of this repository's ``*/10`` wakes over six days, so
    cadence cannot come from cron. It comes from inside this process instead.
    """
    import os

    from nba_edge.worker.run import Worker, dispatch_successor_via_api

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    ref = os.environ.get("GITHUB_REF_NAME", "main")
    worker_id = os.environ.get("GITHUB_RUN_ID") or f"local-{os.getpid()}"

    dispatch = None
    if repo and token and not args.no_successor:
        def dispatch(nonce: str) -> bool:
            return dispatch_successor_via_api(repo, ref, token, args.workflow, nonce)

    w = Worker(
        data_root=Path(args.data), archive_root=Path(args.out), worker_id=str(worker_id),
        successor_token=args.successor_token or None, dispatch_fn=dispatch,
        lifetime_minutes=args.lifetime_minutes,
    )
    result = w.run()
    print(result.to_json())
    publish_worker_health(result.as_dict(), os.environ)
    # Exit 0 whatever the verdict: this step does the work and REPORTS. The workflow's single final
    # enforcement step reads the `health_state` output and fails the run only for FAILED, so a
    # fail-closed stand-down or a quiet off-season shift stays green and a broken one goes red once.
    return 0


def publish_worker_health(result: dict, env) -> str:
    """Surface the shift verdict: step summary, annotations, and step outputs. Returns the state.

    Outputs: ``health_state`` (HEALTHY/DEGRADED/FAILED/NOT_APPLICABLE) and ``final_push``
    (ok/failed/skipped). A missing GITHUB_* file simply means we are not on a runner.
    """
    from nba_edge.worker.health import annotations, classify_shift, render_summary

    health = result.get("health") or classify_shift(result)
    for line in annotations(health):
        print(line)
    fp = result.get("final_push_ok")
    final_push = "skipped" if fp is None else ("ok" if fp else "failed")
    summary_path = env.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a") as f:
            f.write(render_summary(health, result))
    output_path = env.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a") as f:
            f.write(f"health_state={health['state']}\nfinal_push={final_push}\n")
    return health["state"]


def cmd_capture_health(args: argparse.Namespace) -> int:
    """Grade capture cadence against the DATA, not against workflow exit codes."""
    import json

    from nba_edge.ops.capture_health import run_capture_health

    report = run_capture_health(Path(args.archive), Path(args.out) if args.out else None, days=args.days)
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    # Exit non-zero only when asked to gate, so the report can be produced routinely without
    # painting an unattended workflow red every day of the off-season.
    if args.gate and report["summary"]["acceptance"]["verdict"] != "PASS":
        print("capture-health: ACCEPTANCE FAILED")
        return 1
    return 0


def cmd_evidence_health(args: argparse.Namespace) -> int:
    """The daily dataset-completeness dashboard."""
    import json

    from nba_edge.ops.evidence_health import run_evidence_health

    report = run_evidence_health(Path(args.archive), Path(args.out) if args.out else None)
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return 0


def cmd_context(args: argparse.Namespace) -> int:
    from nba_edge.data.context import run_context_refresh

    return run_context_refresh(out_root=Path(args.out), season=args.season)


def cmd_shot_events(args: argparse.Namespace) -> int:
    """RESEARCH: ingest ESPN play-by-play shot events into a point-in-time dataset.

    Descriptive only. It records where attempts were taken and whether they went in; it carries no
    defender, because no reachable source supplies one.
    """
    from nba_edge.shotprofile.ingest import run_shot_event_pull

    return run_shot_event_pull(
        Path(args.out), [s.strip() for s in args.seasons.split(",")],
        max_games=args.max_games or None,
    )


def cmd_shot_events_migrate(args: argparse.Namespace) -> int:
    """RESEARCH: backfill the season-type triplet onto shot-event files written before shotevent/2.

    Additive only. The label is joined from the ESPN box-score dataset's own ``season_type``, never inferred
    from a game's date, and the migration refuses to write if any pre-existing column's digest moves.
    """
    from nba_edge.shotprofile.migrate import run_migration

    return run_migration(
        Path(args.out), [s.strip() for s in args.seasons.split(",")], write=not args.dry_run,
    )


def cmd_matchup_shadow(args: argparse.Namespace) -> int:
    """Record what was knowable about each upcoming game's matchups, when it was knowable.

    Writes an append-only research ledger kind and nothing else. No prediction, price, or authority
    reads it; MATCHUP_AWARE_V2 is RESEARCH and its effects are neutral.
    """
    from nba_edge.matchup.shadow import run_matchup_shadow

    return run_matchup_shadow(Path(args.out), horizon_hours=args.horizon_hours)


def cmd_simulate(args: argparse.Namespace) -> int:
    from nba_edge.workflows.simulate import run_simulate

    return run_simulate(out_root=Path(args.out), data_root=Path(args.data), date=args.date, n_sims=args.sims, seed=args.seed)


def cmd_settle(args: argparse.Namespace) -> int:
    from nba_edge.workflows.settle import run_settle

    return run_settle(out_root=Path(args.out), data_root=Path(args.data))


def cmd_evaluate(args: argparse.Namespace) -> int:
    from nba_edge.workflows.evaluate import run_evaluate

    return run_evaluate(out_root=Path(args.out), data_root=Path(args.data))


def cmd_app_export(args: argparse.Namespace) -> int:
    from nba_edge.app_export import export
    from nba_edge.timeutil import parse_iso

    return export(
        Path(args.out), Path(args.data_root),
        accounting_dir=Path(args.accounting_dir) if args.accounting_dir else None,
        now=parse_iso(args.now) if args.now else None,
        commit_sha=args.commit_sha, workflow_run_id=args.workflow_run_id,
    )


def cmd_conductor(args: argparse.Namespace) -> int:
    from nba_edge.workflows.conductor import run_conductor

    return run_conductor(data_root=Path(args.data), github_output=args.github_output)


def cmd_history(args: argparse.Namespace) -> int:
    from nba_edge.data.history import run_history_pull

    return run_history_pull(out_root=Path(args.out), seasons=args.seasons.split(","), what=args.what.split(","))


def cmd_kalshi_history(args: argparse.Namespace) -> int:
    from nba_edge.kalshi.history import run_kalshi_history

    return run_kalshi_history(
        out_root=Path(args.out), series=[s for s in args.series.split(",") if s], min_close=args.min_close,
        max_close=args.max_close, with_candles=args.candles, candle_interval=args.candle_interval,
        max_markets_for_candles=args.max_candle_markets, sample_games=args.sample_games or None,
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="nba", description="NBA Edge Finder")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("discover", help="Discover Kalshi NBA series/markets and build the catalog")
    d.add_argument("--out", default="data/catalog")
    d.add_argument("--raw-dir", default=None, help="Directory for raw compressed market dumps")
    d.add_argument("--statuses", default=None, help="Comma list of unopened,open,closed,settled")
    d.add_argument("--max-pages", type=int, default=60, help="Max pages (1000 markets each) per series/status")
    d.add_argument("--include", default=None, help="Comma list of series tickers to force-include")
    d.set_defaults(func=cmd_discover)

    c = sub.add_parser("capture", help="Append-only snapshot of all NBA markets (prices, books)")
    c.add_argument("--out", default="data/archive")
    c.add_argument("--statuses", default="open,unopened")
    c.add_argument("--orderbook", action="store_true")
    c.add_argument("--max-orderbooks", type=int, default=400)
    c.add_argument("--series", default=None)
    c.add_argument("--full-snapshots", action="store_true",
                   help="Disable delta encoding and write a full board every tick (the old behaviour)")
    c.add_argument("--checkpoint-every", type=int, default=None,
                   help="Deltas per checkpoint before a fresh full board is written")
    c.set_defaults(func=cmd_capture)

    w = sub.add_parser("worker", help="Long-lived capture worker that owns its own cadence and hands over")
    w.add_argument("--data", default="data")
    w.add_argument("--out", default="data/archive")
    w.add_argument("--lifetime-minutes", type=float, default=None,
                   help="Override the planned lifetime (default: worker.plan.PLANNED_LIFETIME_MINUTES)")
    w.add_argument("--successor-token", default=None,
                   help="Nonce proving we are the successor our predecessor dispatched")
    w.add_argument("--workflow", default="capture_worker.yml", help="Workflow file to dispatch as successor")
    w.add_argument("--no-successor", action="store_true", help="Run one lifetime and stop the chain")
    w.set_defaults(func=cmd_worker)

    ch = sub.add_parser("capture-health", help="Measure capture cadence from the archive's snapshots")
    ch.add_argument("--archive", default="data/archive")
    ch.add_argument("--out", default=None, help="Write the full per-game report here")
    ch.add_argument("--days", type=int, default=30, help="Only grade games tipped within N days")
    ch.add_argument("--gate", action="store_true", help="Exit 1 if the Phase 5 acceptance criteria fail")
    ch.set_defaults(func=cmd_capture_health)

    eh = sub.add_parser("evidence-health", help="Daily dataset-completeness dashboard")
    eh.add_argument("--archive", default="data/archive")
    eh.add_argument("--out", default=None)
    eh.set_defaults(func=cmd_evidence_health)

    rc = sub.add_parser("reconstruct", help="Rebuild the board at a past instant from checkpoint + deltas")
    rc.add_argument("--archive", default="data/archive")
    rc.add_argument("--at", required=True, help="ISO-8601 instant; returns the latest tick at or before it")
    rc.add_argument("--out", default=None, help="Write the reconstructed board here as gzip JSONL")
    rc.add_argument("--compare", default=None,
                    help="Verify field-for-field and hash-for-hash against this full snapshot")
    rc.set_defaults(func=cmd_reconstruct)

    dv = sub.add_parser("delta-verify", help="Verify every delta chain on the archive")
    dv.add_argument("--archive", default="data/archive")
    dv.set_defaults(func=cmd_delta_verify)

    x = sub.add_parser("context", help="Refresh schedule/rosters/injuries snapshot (point-in-time)")
    x.add_argument("--out", default="data/archive")
    x.add_argument("--season", default=None)
    x.set_defaults(func=cmd_context)

    se = sub.add_parser(
        "shot-events",
        help="RESEARCH: ingest ESPN shot events (locations + outcomes; never defenders)",
    )
    se.add_argument("--out", default="data/history")
    se.add_argument("--seasons", default="2024-25")
    se.add_argument("--max-games", type=int, default=0, help="cap NEW games per run; 0 = no cap")
    se.set_defaults(func=cmd_shot_events)

    sem = sub.add_parser(
        "shot-events-migrate",
        help="RESEARCH: backfill season_type onto existing shot-event files (additive, verified)",
    )
    sem.add_argument("--out", default="data/history")
    sem.add_argument("--seasons", default="2023-24,2024-25,2025-26")
    sem.add_argument("--dry-run", action="store_true", help="report only; write nothing")
    sem.set_defaults(func=cmd_shot_events_migrate)

    ms = sub.add_parser(
        "matchup-shadow",
        help="RESEARCH: record point-in-time matchup context for upcoming games (no predictions)",
    )
    ms.add_argument("--out", default="data/archive")
    ms.add_argument("--horizon-hours", type=float, default=36.0)
    ms.set_defaults(func=cmd_matchup_shadow)

    s = sub.add_parser("simulate", help="Simulate not-started games and price supported contracts")
    s.add_argument("--out", default="out/slate")
    s.add_argument("--data", default="data")
    s.add_argument("--date", default=None, help="ET date YYYY-MM-DD; default today")
    s.add_argument("--sims", type=int, default=0, help="0 = auto (convergence-driven)")
    s.add_argument("--seed", type=int, default=None)
    s.set_defaults(func=cmd_simulate)

    t = sub.add_parser("settle", help="Settle completed games against authoritative box scores")
    t.add_argument("--out", default="data/archive")
    t.add_argument("--data", default="data")
    t.set_defaults(func=cmd_settle)

    e = sub.add_parser("evaluate", help="Calibration / Brier / CLV / authority ledger")
    e.add_argument("--out", default="out/eval")
    e.add_argument("--data", default="data")
    e.set_defaults(func=cmd_evaluate)

    ax = sub.add_parser("app-export", help="Publish the Edge Finder app export (edge_finder.app.v1) from the archive")
    ax.add_argument("--out", default="data/archive/app/latest")
    ax.add_argument("--data-root", default="data/archive")
    ax.add_argument("--accounting-dir", default=None, help="optional checkout of the accounting-data branch")
    ax.add_argument("--now", default=None, help="ISO-8601 UTC instant; default wall clock")
    ax.add_argument("--commit-sha", default=os.environ.get("GITHUB_SHA") or None)
    ax.add_argument("--workflow-run-id", default=os.environ.get("GITHUB_RUN_ID") or None)
    ax.set_defaults(func=cmd_app_export)

    k = sub.add_parser("conductor", help="Decide which jobs are worth running now")
    k.add_argument("--data", default="data")
    k.add_argument("--github-output", default=None)
    k.set_defaults(func=cmd_conductor)

    h = sub.add_parser("history", help="Pull historical NBA data (game logs, box scores) for research")
    h.add_argument("--out", default="data/history")
    h.add_argument("--seasons", default="2023-24,2024-25,2025-26")
    h.add_argument("--what", default="team_logs,player_logs")
    h.set_defaults(func=cmd_history)

    kh = sub.add_parser("kalshi-history", help="Pull settled Kalshi NBA markets (+ candlesticks) from the historical API")
    kh.add_argument("--out", default="data/history")
    kh.add_argument(
        "--series",
        default="KXNBAGAME,KXNBASPREAD,KXNBATOTAL,KXNBATEAMTOTAL,KXNBAPTS,KXNBAREB,KXNBAAST,KXNBA3PT,KXNBAPRA,"
        "KXNBA1HSPREAD,KXNBA1HTOTAL,KXNBA1HWINNER,KXNBAWINS",
    )
    kh.add_argument("--min-close", default="2025-10-01", help="Earliest close date (YYYY-MM-DD or ISO-8601)")
    kh.add_argument("--max-close", default="2026-07-01", help="Latest close date (YYYY-MM-DD or ISO-8601)")
    kh.add_argument("--candles", action="store_true", help="Also pull candlesticks for the top markets")
    kh.add_argument("--candle-interval", type=int, default=60, help="Candle period in minutes: 1, 60 or 1440")
    kh.add_argument("--max-candle-markets", type=int, default=3000, help="Hard cap on candle fetches this run")
    kh.add_argument(
        "--sample-games", type=int, default=0,
        help="Pull candles for EVERY market of N games spread across the window (0 = global priority budget). "
             "Use this for cross-family market-vs-model research: it guarantees contemporaneous prices for "
             "spreads/totals/props on the same games.",
    )
    kh.set_defaults(func=cmd_kalshi_history)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
