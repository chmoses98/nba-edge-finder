"""Prospective ("shadow") capture of matchup inputs during normal capture runs.

The point is narrow and worth stating precisely: **record what was knowable, when it was knowable.**
Six months from now a matchup study will want the roster and lineup state as it stood at T-90 before
a specific game. Reconstructing that from hindsight is exactly the leak this whole arm is built to
avoid, so it has to be written down prospectively or it does not exist.

This changes no prediction. It writes an additional, append-only ledger kind and nothing else reads
it yet. It also does not invent matchup data: with no defensive-assignment source reachable today
(see ``docs/research/MATCHUP_SOURCE_AUDIT.md``), contexts are written with **no exposures** and a
provenance reason saying so, rather than with fabricated or positional-guess assignments.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from nba_edge.archive.ledger import Ledger
from nba_edge.identity.teams import registry
from nba_edge.matchup.schemas import GameMatchupContext, LineupConfidence
from nba_edge.matchup.version import MATCHUP_SCHEMA_VERSION, describe
from nba_edge.timeutil import iso, parse_iso, utcnow

MATCHUP_CONTEXT_KIND = "matchup/context"

# Only games within this horizon are worth a context: further out, rosters churn and the record is
# noise rather than evidence about the game.
HORIZON_HOURS = 36.0


def _latest_rows(ledger: Ledger, kind: str) -> list[dict[str, Any]]:
    entry = ledger.latest(kind)
    if not entry:
        return []
    import gzip

    with gzip.open(ledger.root / entry.path, "rt") as f:
        return [json.loads(line) for line in f if line.strip()]


def build_context(
    game: dict[str, Any],
    rosters: list[dict[str, Any]],
    now: datetime,
    *,
    source: str = "shadow/v1",
) -> GameMatchupContext | None:
    """A point-in-time matchup context for one game, from data already captured.

    Returns None when the game cannot be identified well enough to be worth a record. Starters are
    left empty unless a source actually reports them: a projected five written into the
    ``expected_*_starters`` field would be indistinguishable later from a confirmed one.
    """
    gid = str(game.get("game_id") or "")
    if not gid:
        return None
    try:
        tip = parse_iso(game["start_time_utc"])
    except (KeyError, TypeError, ValueError):
        return None

    reg = registry()
    home_id = game.get("home_team_id")
    away_id = game.get("away_team_id")
    if home_id is None or away_id is None:
        return None

    def rotation_for(team_id: Any) -> tuple[int, ...]:
        """The captured roster for a team, using production's own identity convention.

        The join is deliberately the one ``workflows.simulate`` already uses: captured roster rows
        carry ESPN keys (``team_abbreviation``, ``espn_athlete_id``), the schedule carries NBA team
        ids, and an ESPN-sourced player is given the provisional id ``-espn_athlete_id``. Matching
        on a ``team_id``/``nba_id`` field that captured rosters do not have silently produced an
        empty rotation for every game -- a record that looks written but holds nothing.
        """
        try:
            tid = int(team_id)
        except (TypeError, ValueError):
            return ()
        ids = []
        for r in rosters:
            tricode = r.get("team_abbreviation") or ""
            try:
                if reg.by_tricode(tricode).team_id != tid:
                    continue
                ids.append(-int(r["espn_athlete_id"]))
            except Exception:  # noqa: BLE001 - an unresolvable row is skipped, never guessed
                continue
        return tuple(sorted(set(ids)))

    return GameMatchupContext(
        game_id=gid,
        observed_at_utc=now,
        home_team_id=int(home_id),
        away_team_id=int(away_id),
        tip_utc=tip,
        # Deliberately empty: no source reports expected starters today, and a projection written
        # here would be indistinguishable from a confirmation later.
        expected_home_starters=(),
        expected_away_starters=(),
        expected_home_rotation=rotation_for(home_id),
        expected_away_rotation=rotation_for(away_id),
        lineup_confidence=LineupConfidence.UNKNOWN,
        exposures=(),
        home_scheme=None,
        away_scheme=None,
        source=source,
        provenance={
            "schema": MATCHUP_SCHEMA_VERSION,
            "exposures": "none: no defensive-assignment source is reachable; see MATCHUP_SOURCE_AUDIT.md",
            "starters": "none: no confirmed-starter source ingested yet",
            "scheme": "none: no scheme-proxy source ingested yet",
            "roster_basis": (
                "latest captured context/rosters snapshot -- the full captured roster, NOT a "
                "projected rotation; no minutes model is consulted here"
            ),
            "player_id_convention": "ESPN-sourced players carry the provisional id -espn_athlete_id",
        },
    )


def run_matchup_shadow(out_root: Path, horizon_hours: float = HORIZON_HOURS) -> int:
    """Write a matchup context per upcoming game. Never touches predictions or production state."""
    ledger = Ledger(Path(out_root))
    now = utcnow()
    schedule = _latest_rows(ledger, "context/schedule")
    rosters = _latest_rows(ledger, "context/rosters")

    contexts: list[GameMatchupContext] = []
    for g in schedule:
        try:
            tip = parse_iso(g["start_time_utc"])
        except (KeyError, TypeError, ValueError):
            continue
        hours = (tip - now).total_seconds() / 3600
        if not (0 < hours <= horizon_hours):
            continue
        ctx = build_context(g, rosters, now)
        if ctx is not None:
            contexts.append(ctx)

    status: dict[str, Any] = {
        "shadow_at_utc": iso(now),
        "n_games_in_horizon": len(contexts),
        "n_schedule_rows": len(schedule),
        "n_roster_rows": len(rosters),
        "horizon_hours": horizon_hours,
        **describe(),
    }
    if contexts:
        entry = ledger.append_rows(
            MATCHUP_CONTEXT_KIND,
            [json.loads(c.model_dump_json()) for c in contexts],
            observed_at=now,
            meta={"schema": MATCHUP_SCHEMA_VERSION, "n": len(contexts)},
        )
        status["path"] = entry.path
        status["rows"] = entry.rows
    else:
        status["path"] = None
        status["note"] = "no games within the horizon; nothing written"

    (Path(out_root) / "STATUS_matchup_shadow.json").write_text(json.dumps(status, indent=1, default=str))
    print(json.dumps(status, indent=1, default=str))
    return 0
