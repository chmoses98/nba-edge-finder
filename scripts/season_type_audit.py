"""RESEARCH: audit the season_type labels now carried by every shot event.

Two things are checked. First the counts, per season and season type, so the size of the preseason block that
was silently inside every earlier study is visible. Second the CALENDAR ORDER, which is the part that can
actually fail: the labels come from ESPN's season.type and the dates come from the schedule, so if the two
disagree -- a "regular" game before the preseason ends, a "playoff" game before the play-in -- the labels are
wrong and the ordering check says so. That is a real test precisely because nothing here derives a label from
a date; date inference is what this whole migration exists to avoid.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ORDER = ["preseason", "regular", "playin", "playoffs", "allstar", "other"]
# The types whose calendar blocks must not overlap, in the order the NBA plays them. allstar sits inside the
# regular season and other is a catch-all, so neither belongs in an ordering check.
ORDERED = ["preseason", "regular", "playin", "playoffs"]


def audit(out_root: Path, seasons: list[str]) -> dict:
    import pandas as pd

    from nba_edge.shotprofile.ingest import _paths

    report: dict = {"seasons": {}, "violations": []}
    for season in seasons:
        p = _paths(out_root, season)["events"]
        if not p.exists():
            report["seasons"][season] = {"status": "MISSING"}
            continue
        d = pd.read_parquet(p, columns=["game_id", "event_time_utc", "season_type",
                                        "espn_season_type", "season_type_source"])
        # Dates are taken in EASTERN time, not UTC. A 7:30pm ET tip is the next UTC day, so a UTC calendar
        # makes the last play-in game and the first playoff game look like they share a date and turns a clean
        # block boundary into a spurious one-day overlap. The league schedules in ET, so the audit reads in ET.
        from nba_edge.timeutil import et_date, parse_iso

        def _et(v: object) -> str:
            try:
                return et_date(parse_iso(str(v)))
            except (TypeError, ValueError):
                return ""

        d["date"] = d["event_time_utc"].map(_et)
        games = d.drop_duplicates("game_id")

        blocks = {}
        for st in ORDER:
            g = games[games.season_type == st]
            if len(g) == 0:
                continue
            blocks[st] = {
                "games": int(len(g)),
                "shot_events": int((d.season_type == st).sum()),
                "first_date": str(g["date"].min()),
                "last_date": str(g["date"].max()),
            }

        # Calendar order: each block must start no earlier than the previous block ends.
        present = [st for st in ORDERED if st in blocks]
        for a, b in zip(present, present[1:], strict=False):
            if blocks[b]["first_date"] <= blocks[a]["last_date"]:
                report["violations"].append({
                    "season": season, "earlier": a, "later": b,
                    "detail": f"{b} starts {blocks[b]['first_date']} before {a} ends {blocks[a]['last_date']}",
                })

        unlabelled = int((games.season_type.isna() | (games.season_type == "")).sum())
        if unlabelled:
            report["violations"].append({"season": season, "detail": f"{unlabelled} games carry no season_type"})

        report["seasons"][season] = {
            "status": "OK", "games": int(len(games)), "shot_events": int(len(d)),
            "by_season_type": blocks,
            "sources": {str(k): int(v) for k, v in d.season_type_source.value_counts(dropna=False).items()},
            "espn_raw_codes": {str(k): int(v) for k, v in games.espn_season_type.value_counts(dropna=False).items()},
            "representative": _representative(games, blocks),
        }
    report["status"] = "OK" if not report["violations"] else "VIOLATIONS"
    return report


def _representative(games, blocks: dict) -> dict:
    """One named game per boundary the brief asks to see checked by hand."""
    picks: dict = {}

    def one(st: str, which: str) -> dict | None:
        g = games[games.season_type == st]
        if len(g) == 0:
            return None
        g = g.sort_values("date", kind="mergesort")
        r = (g.iloc[0] if which == "first" else g.iloc[-1])
        return {"game_id": str(r.game_id), "date": str(r.date), "season_type": str(r.season_type)}

    for label, st, which in [
        ("preseason_first", "preseason", "first"),
        ("opening_night", "regular", "first"),
        ("regular_season_last", "regular", "last"),
        ("playin_first", "playin", "first"),
        ("playoffs_first_round", "playoffs", "first"),
        ("finals_last", "playoffs", "last"),
    ]:
        v = one(st, which)
        if v:
            picks[label] = v
    _ = blocks
    return picks


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "data/history")
    seasons = (sys.argv[2] if len(sys.argv) > 2 else "2023-24,2024-25,2025-26").split(",")
    rep = audit(root, [s.strip() for s in seasons])
    print(json.dumps(rep, indent=1))
    return 0 if rep["status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
