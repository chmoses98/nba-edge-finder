"""Command-line entry: ``nba <command>``. Each command is a thin wrapper around a module function so the
same code runs locally, in tests, and in GitHub Actions."""

from __future__ import annotations

import argparse
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

    return run_capture(out_root=Path(args.out), statuses=args.statuses.split(","), with_orderbook=args.orderbook,
                       max_orderbooks=args.max_orderbooks, series_filter=args.series.split(",") if args.series else None)


def cmd_context(args: argparse.Namespace) -> int:
    from nba_edge.data.context import run_context_refresh

    return run_context_refresh(out_root=Path(args.out), season=args.season)


def cmd_simulate(args: argparse.Namespace) -> int:
    from nba_edge.workflows.simulate import run_simulate

    return run_simulate(out_root=Path(args.out), data_root=Path(args.data), date=args.date, n_sims=args.sims, seed=args.seed)


def cmd_settle(args: argparse.Namespace) -> int:
    from nba_edge.workflows.settle import run_settle

    return run_settle(out_root=Path(args.out), data_root=Path(args.data))


def cmd_evaluate(args: argparse.Namespace) -> int:
    from nba_edge.workflows.evaluate import run_evaluate

    return run_evaluate(out_root=Path(args.out), data_root=Path(args.data))


def cmd_conductor(args: argparse.Namespace) -> int:
    from nba_edge.workflows.conductor import run_conductor

    return run_conductor(data_root=Path(args.data), github_output=args.github_output)


def cmd_history(args: argparse.Namespace) -> int:
    from nba_edge.data.history import run_history_pull

    return run_history_pull(out_root=Path(args.out), seasons=args.seasons.split(","), what=args.what.split(","))


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
    c.set_defaults(func=cmd_capture)

    x = sub.add_parser("context", help="Refresh schedule/rosters/injuries snapshot (point-in-time)")
    x.add_argument("--out", default="data/archive")
    x.add_argument("--season", default=None)
    x.set_defaults(func=cmd_context)

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

    k = sub.add_parser("conductor", help="Decide which jobs are worth running now")
    k.add_argument("--data", default="data")
    k.add_argument("--github-output", default=None)
    k.set_defaults(func=cmd_conductor)

    h = sub.add_parser("history", help="Pull historical NBA data (game logs, box scores) for research")
    h.add_argument("--out", default="data/history")
    h.add_argument("--seasons", default="2023-24,2024-25,2025-26")
    h.add_argument("--what", default="team_logs,player_logs")
    h.set_defaults(func=cmd_history)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
