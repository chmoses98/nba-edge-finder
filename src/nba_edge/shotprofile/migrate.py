"""Backfill the season-type triplet onto shot-event Parquet written before schema ``shotevent/2``.

The label is not re-derived and it is not guessed from the calendar: it is *joined* from
``player_games_{season}.parquet``, which already carries ESPN's own ``season.type`` mapped through
``ESPN_SEASON_TYPES``. Both datasets key on the same ``espn:<event id>`` game id, so the join is exact and
needs no network call.

The migration is additive by construction. Every column that existed before is copied through untouched, and
the caller can prove it: :func:`fingerprint` is taken before and after, and :func:`migrate_season` refuses to
write unless every preserved column's digest is unchanged.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from nba_edge.log import get_logger, kv
from nba_edge.schemas.core import SeasonType
from nba_edge.shotprofile.events import SHOT_EVENT_SCHEMA_VERSION
from nba_edge.shotprofile.ingest import (
    COLUMNS,
    SEASON_TYPE_SOURCE_BACKFILL,
    _paths,
)

log = get_logger(__name__)

# The three columns schema shotevent/2 adds. Everything else in COLUMNS is pre-existing and must survive the
# migration bit for bit -- that is what the fingerprint gate checks.
NEW_COLUMNS = ("season_type", "espn_season_type", "season_type_source")
# schema_version describes the row SHAPE, and the shape is what this migration changes, so it moves forward
# with the row. It is therefore excluded from the drift gate -- but it is the ONLY pre-existing column that
# is, and the migration reports its before/after counts so the change is visible rather than assumed.
# ingest_version stays in the gate: a backfilled row was still produced by the old pull, and rewriting that
# would erase the fact that its coordinates came through espn-pbp/1.
VERSION_COLUMNS = ("schema_version",)
PRESERVED_COLUMNS = tuple(c for c in COLUMNS if c not in NEW_COLUMNS and c not in VERSION_COLUMNS)

# Sort key for fingerprinting. Parquet row order is an implementation detail; the identity of a shot event is
# (game, sequence, event id), so the digest is taken over rows in that order and is immune to a reordering
# write that changes nothing semantically.
SORT_KEY = ("game_id", "sequence", "event_id")

MIGRATION_ID = "season_type_backfill/1"


NULL_TOKEN = "\x00NULL"


def _canon(series: Any) -> list[str]:
    """A column as canonical strings, so one digest covers ints, floats, bools, nulls and objects alike.

    Nulls get their own token rather than falling back to ``str(None)`` or ``str(nan)``: a column holding the
    literal text "None" must not digest the same as a column holding a missing value, or the gate below would
    wave through exactly the substitution it exists to catch.
    """
    return [NULL_TOKEN if v is None or v != v else str(v) for v in series.tolist()]


def fingerprint(df: Any) -> dict[str, str]:
    """Per-column digests over rows in canonical order. Only columns present are digested."""
    keys = [c for c in SORT_KEY if c in df.columns]
    d = df.sort_values(keys, kind="mergesort").reset_index(drop=True) if keys else df.reset_index(drop=True)
    out: dict[str, str] = {}
    for col in d.columns:
        joined = "\x1f".join(_canon(d[col]))
        out[col] = hashlib.sha256(joined.encode("utf-8")).hexdigest()
    out["__rows__"] = hashlib.sha256(str(len(d)).encode()).hexdigest()
    return out


def season_type_lookup(out_root: Path, season: str) -> dict[str, str]:
    """``game_id -> season_type`` from the ESPN box-score dataset. Empty when that dataset is absent."""
    import pandas as pd

    p = Path(out_root) / "espn" / f"player_games_{season}.parquet"
    if not p.exists():
        return {}
    pg = pd.read_parquet(p, columns=["game_id", "season_type"])
    pg = pg.dropna(subset=["game_id", "season_type"]).drop_duplicates("game_id")
    return {str(g): str(s) for g, s in zip(pg["game_id"], pg["season_type"], strict=True)}


def migrate_frame(df: Any, lookup: dict[str, str]) -> tuple[Any, dict[str, Any]]:
    """Add the season-type triplet to ``df``. Returns the new frame and a report.

    A row that already carries a season_type keeps it: a label attached at pull time came straight off the
    game's own scoreboard entry and is no less authoritative than this join, so re-running the migration over
    a mixed file is a no-op on the rows it has already covered. Where the two disagree the existing value is
    still kept, but the disagreement is *counted* -- a silent overwrite would hide exactly the kind of upstream
    change this column exists to expose.
    """
    import pandas as pd

    d = df.copy()
    had = "season_type" in d.columns
    existing = d["season_type"].astype("object") if had else pd.Series([None] * len(d), index=d.index, dtype="object")
    existing = existing.where(existing.notna() & (existing != "") & (existing != "None"), other=None)

    joined = d["game_id"].astype(str).map(lookup)
    filled = existing.where(existing.notna(), other=joined)
    # A game missing from the box-score dataset is labelled OTHER, never guessed from its date. OTHER is a
    # real value in SeasonType and is excluded from the default research population just like preseason is.
    unmatched = int(filled.isna().sum())
    filled = filled.where(filled.notna(), other=SeasonType.OTHER.value)

    both = existing.notna() & joined.notna()
    conflicts = int((both & (existing != joined)).sum())

    newly = existing.isna()
    if "season_type_source" in d.columns:
        src = d["season_type_source"].astype("object")
        src = src.where(src.notna() & (src != "") & (src != "None"), other=None)
    else:
        src = pd.Series([None] * len(d), index=d.index, dtype="object")
    src = src.where(~newly, other=SEASON_TYPE_SOURCE_BACKFILL)

    # espn_season_type is deliberately NOT reconstructed by inverting ESPN_SEASON_TYPES. That column exists to
    # surface raw codes the mapping does not know; a value derived from the mapped label could never be one,
    # so inverting it would turn an early-warning field into a tautology. The box-score dataset did not carry
    # the raw code, so for backfilled rows it stays null and season_type_source says why.
    if "espn_season_type" not in d.columns:
        d["espn_season_type"] = None

    d["season_type"] = filled.astype("object")
    d["season_type_source"] = src.astype("object")

    schema_before = {str(k): int(v) for k, v in d["schema_version"].value_counts().items()} \
        if "schema_version" in d.columns else {}
    if "schema_version" in d.columns:
        d["schema_version"] = d["schema_version"].astype("object").where(~newly, other=SHOT_EVENT_SCHEMA_VERSION)

    report = {
        "rows": int(len(d)),
        "already_labelled": int(existing.notna().sum()),
        "newly_labelled": int(newly.sum()),
        "unmatched_games": sorted({str(g) for g, f in zip(d["game_id"], joined.isna(), strict=True) if f}),
        "unmatched_rows": unmatched,
        "conflicts": conflicts,
        "by_season_type": {str(k): int(v) for k, v in d["season_type"].value_counts().items()},
        "schema_version_before": schema_before,
        "schema_version_after": {str(k): int(v) for k, v in d["schema_version"].value_counts().items()}
        if "schema_version" in d.columns else {},
    }
    return d, report


def migrate_season(out_root: Path, season: str, *, write: bool = True) -> dict[str, Any]:
    """Migrate one season's shot-event file in place. Refuses to write if any pre-existing column changed."""
    import pandas as pd

    p = _paths(Path(out_root), season)["events"]
    if not p.exists():
        return {"season": season, "status": "MISSING", "path": str(p)}

    before_df = pd.read_parquet(p)
    before = fingerprint(before_df)
    lookup = season_type_lookup(Path(out_root), season)
    after_df, report = migrate_frame(before_df, lookup)
    after = fingerprint(after_df)

    drift = {c: [before.get(c), after.get(c)] for c in PRESERVED_COLUMNS
             if c in before and before.get(c) != after.get(c)}
    if before.get("__rows__") != after.get("__rows__"):
        drift["__rows__"] = [before.get("__rows__"), after.get("__rows__")]

    status = "OK" if not drift else "REFUSED_DRIFT"
    result = {
        "season": season, "status": status, "path": str(p), "migration": MIGRATION_ID,
        "lookup_games": len(lookup), "drift": drift, **report,
    }
    if drift:
        log.error(kv(event="shot_events_migration_refused", season=season, drifted=",".join(sorted(drift))))
        return result

    if write:
        # Written straight from the frame rather than via a dict round-trip: going through records lets pandas
        # re-infer every dtype, which can turn a nullable int column into float and would be a real change to
        # the data dressed up as a no-op. The file is then read back and re-fingerprinted, because the gate
        # above only proves the in-memory frame is faithful -- the write itself has to be checked too.
        after_df[list(COLUMNS)].to_parquet(p, engine="pyarrow", index=False)
        reread = fingerprint(pd.read_parquet(p))
        rt = {c: [after.get(c), reread.get(c)] for c in after if after.get(c) != reread.get(c)}
        result["written"] = True
        result["roundtrip_drift"] = rt
        if rt:
            result["status"] = "ROUNDTRIP_DRIFT"
            log.error(kv(event="shot_events_migration_roundtrip_drift", season=season,
                         drifted=",".join(sorted(rt))))
            return result
    log.info(kv(event="shot_events_migrated", season=season, rows=report["rows"],
                newly=report["newly_labelled"], conflicts=report["conflicts"]))
    return result


def run_migration(out_root: Path, seasons: list[str], *, write: bool = True) -> int:
    out_root = Path(out_root)
    results = [migrate_season(out_root, s.strip(), write=write) for s in seasons if s.strip()]
    payload = {"migration": MIGRATION_ID, "write": write, "seasons": results}
    print(json.dumps(payload, indent=1, default=str))
    return 0 if all(r["status"] in ("OK", "MISSING") for r in results) else 1
