"""Read-only rolling NBA all-contract market-family scorecards from day-scoped PIT audits.

Only latest valid pre-tip forecast per (ET game date, ticker) is scored. Related
ladder contracts share the game cluster. Missing audited *game* dates, partial
quote joins and unsupported/scalar contracts are shown explicitly, not hidden.
No bets, market authority, price invention, or archive writes.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from nba_edge.archive.ledger import Ledger
from nba_edge.audit.markets import _family_table, _latest


def _number(raw: Any) -> float | None:
    if raw in (None, ""):
        return None
    try:
        return float(raw)
    except (ValueError, TypeError):
        return None


def _daily_final_rows(path: Path, date_et: str) -> list[dict[str, Any]]:
    """Deduplicate frozen horizons by ticker, choosing latest pre-tip timestamp."""
    latest: dict[str, tuple[str, dict[str, Any]]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            tk = row.get("ticker")
            ts = row.get("predicted_at_utc") or ""
            y, p = row.get("outcome_yes"), _number(row.get("p_model"))
            if not tk or y not in ("0", "1") or p is None or not (0.0 <= p <= 1.0):
                continue
            r = {
                "ticker": tk,
                "game_id": f"{date_et}|{row.get('game_id', '')}",
                "family": row.get("family") or "unknown",
                "p_model": p,
                "outcome_yes": int(y),
                "p_market_mid": _number(row.get("p_market_mid")),
                "pick_positive_ev": row.get("pick_positive_ev") == "True",
                "pick_pnl": _number(row.get("pick_pnl")),
                "pick_stake": _number(row.get("pick_stake")),
                "clv_quoted_exec": _number(row.get("clv_quoted_exec")),
                "clv_selection": _number(row.get("clv_selection")),
            }
            old = latest.get(tk)
            if old is None or ts > old[0]:
                latest[tk] = (ts, r)
    return [entry[1] for _, entry in sorted(latest.items())]


def rolling_scorecards(
    archive: Path, out_dir: Path, anchor_et: str, periods: tuple[int, ...] = (7, 14, 30),
) -> dict[str, dict[str, Any]]:
    """Recombine existing daily audits. Missing dates with *games* => INCOMPLETE.

    A day with no NBA game is not a missing audit. No market is falsely called
    gradeable if it lacks settlement, binary semantics, or a valid PIT forecast.
    Only complete windows can support rolling-sample comparisons.
    """
    archive, out_dir = Path(archive), Path(out_dir)
    anchor = date.fromisoformat(anchor_et)
    schedule = _latest(Ledger(archive).iter_rows("context/schedule"), "game_id")
    game_dates = {g.get("game_date_et") for g in schedule.values() if g.get("game_date_et")}
    result: dict[str, dict[str, Any]] = {}

    for days in periods:
        if days <= 0:
            raise ValueError("rolling window must have a positive day count")
        start = anchor - timedelta(days=days - 1)
        required = sorted(d.isoformat() for offset in range(days)
                          if (d := start + timedelta(days=offset)).isoformat() in game_dates)
        rows: list[dict[str, Any]] = []
        audited_dates: list[str] = []
        missing_dates: list[str] = []
        degraded_dates: list[str] = []
        total, graded, no_quote = 0, 0, 0
        reasons: dict[str, int] = defaultdict(int)
        for date_et in required:
            report_path = out_dir / date_et / "report.json"
            csv_path = out_dir / date_et / "horizon_rows.csv"
            if not report_path.is_file() or not csv_path.is_file():
                missing_dates.append(date_et)
                continue
            report = json.loads(report_path.read_text())
            if report.get("status") != "OK":
                degraded_dates.append(date_et)
            coverage = report.get("coverage") or {}
            total += int(coverage.get("universe") or 0)
            graded += int(coverage.get("graded") or 0)
            no_quote += int(coverage.get("forecast_rows_without_any_executable_quote") or 0)
            for reason, count in (coverage.get("ungraded_by_reason") or {}).items():
                reasons[reason] += int(count)
            rows.extend(_daily_final_rows(csv_path, date_et))
            audited_dates.append(date_et)

        # The statistical unit of uncertainty is the game, not each ticker/rung.
        fams = _family_table(rows, "family")
        status = ("COMPLETE" if required and not missing_dates and not degraded_dates
                  else "INCOMPLETE")
        entry = {
            "schema": "nba.market_family_rolling.v1",
            "status": status,
            "authority": "RESEARCH_ONLY",
            "anchor_date_et": anchor_et,
            "window_start_et": start.isoformat(),
            "calendar_days": days,
            "expected_active_game_dates": required,
            "audited_game_dates": audited_dates,
            "missing_game_dates": missing_dates,
            "degraded_game_dates": degraded_dates,
            "coverage": {
                "market_universe": total,
                "graded": graded,
                "ungraded": total - graded,
                "ungraded_by_reason": dict(sorted(reasons.items())),
                "latest_pretip_graded_rows": len(rows),
                "latest_pretip_unpriced_rows": no_quote,
            },
            "families": fams,
            "notes": [
                "Exactly one latest valid pre-tip forecast per (date, ticker), with all graded family scores game-clustered.",
                "Brier calibration, YES/NO direction and hypothetical after-fee ROI are different diagnostics.",
                "Protected/scalar/unsettleable/no-model contracts count in universe and ungraded reasons; not in binary Brier.",
                "Actual-fill CLV is unavailable without verifiable fills. Do not treat quoted asks as fills.",
                "INCOMPLETE windows must not be interpreted as evidence of a rolling profitable advantage.",
            ],
        }
        folder = out_dir / "rolling" / f"{days}d"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "report.json").write_text(json.dumps(entry, indent=2, sort_keys=True) + "\n")
        lines = [
            f"# NBA rolling market-family audit — last {days} calendar days — {status}",
            "",
            f"ET window: {start.isoformat()} to {anchor_et}; RESEARCH_ONLY",
            f"Dates with NBA games: {len(required)}, audited: {len(audited_dates)}, missing: {missing_dates}, degraded: {degraded_dates}",
            f"Universe = {total} contracts = {graded} graded + {total - graded} ungraded.",
            f"Ungraded by reason: {dict(sorted(reasons.items()))}",
            f"Latest pre-tip unpriced: {no_quote}",
            "",
            "| family | contracts graded | games | model Brier | market Brier | model direction hit | market direction hit | hypothetical ROI after fee |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for f in fams:
            def fmt(v: Any) -> str:
                return "-" if v is None else f"{v:.4f}" if isinstance(v, float) else str(v)

            lines.append(
                f"| {f['family']} | {f['n']} | {f['n_games']} | {fmt(f['brier_model'])} | "
                f"{fmt(f['brier_market_mid'])} | {fmt(f['model_direction_hit_rate'])} | "
                f"{fmt(f['market_direction_hit_rate'])} | {fmt(f['pick_roi_after_fee']['mean'])} |"
            )
        lines += ["", *[f"- {note}" for note in entry["notes"]], ""]
        (folder / "report.md").write_text("\n".join(lines))
        result[f"{days}d"] = entry
    return result
