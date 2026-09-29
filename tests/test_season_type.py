"""Season-type persistence, migration and the default research population.

Every earlier shot-profile result was computed over a corpus that silently included preseason basketball,
because a shot-event row carried no way to tell a camp game from a real one. These tests pin the three things
that stop that recurring: the label is persisted from the authoritative source, the migration that backfills
it cannot quietly change anything else, and a study that forgets to filter gets an error rather than
contamination.
"""

from __future__ import annotations

import pytest

from nba_edge.schemas.core import SeasonType


# ---------------------------------------------------------------------------------------------------------
# parsing and mapping
# ---------------------------------------------------------------------------------------------------------
def test_espn_season_codes_map_to_the_canonical_enum():
    from nba_edge.data.history import ESPN_SEASON_TYPES

    assert ESPN_SEASON_TYPES[1] is SeasonType.PRESEASON
    assert ESPN_SEASON_TYPES[2] is SeasonType.REGULAR
    assert ESPN_SEASON_TYPES[3] is SeasonType.PLAYOFFS
    assert ESPN_SEASON_TYPES[5] is SeasonType.PLAYIN


def test_an_unknown_espn_code_becomes_other_rather_than_disappearing():
    """A new upstream code must show up in the data, not silently delete games from every study."""
    from nba_edge.data.history import scoreboard_events

    payload = {"events": [{
        "id": "999", "date": "2025-01-15T23:00:00Z", "season": {"type": 77, "year": 2025},
        "competitions": [{
            "status": {"type": {"completed": True}},
            "competitors": [
                {"homeAway": "home", "team": {"abbreviation": "BOS"}},
                {"homeAway": "away", "team": {"abbreviation": "NYK"}},
            ],
        }],
    }]}
    (ev,) = scoreboard_events(payload)
    assert ev["season_type"] == SeasonType.OTHER.value
    assert ev["espn_season_type"] == 77, "the raw code travels with the row so the surprise is auditable"


def test_ingested_rows_carry_the_games_season_type_verbatim():
    """The label is copied off the game's scoreboard entry; it is never re-derived from the date."""
    from nba_edge.shotprofile.ingest import SEASON_TYPE_SOURCE_SCOREBOARD, _row

    class _Ev:
        game_id, event_id, sequence, period = "espn:1", "1", 1, 1
        clock_display, clock_seconds_remaining = "1:00", 60.0
        shooter_player_id, shooter_name, team_id, opponent_team_id = 1, "P", 2, 3
        is_home, x, y, coordinate_valid = True, 25.0, 1.0, True
        shot_made, points_value, is_free_throw, is_shooting_play = True, 2, False, True
        event_type, source, source_observed_at_utc = "made", "espn", None
        ingest_version, schema_version, usable_for_zone = "espn-pbp/2", "shotevent/2", True

    # An October game that ESPN calls a regular-season game stays regular, which is precisely the case a
    # date heuristic would get wrong.
    r = _row(_Ev(), None, {"season_type": "regular", "espn_season_type": 2})
    assert r["season_type"] == "regular"
    assert r["espn_season_type"] == 2
    assert r["season_type_source"] == SEASON_TYPE_SOURCE_SCOREBOARD

    # No meta at all is OTHER, never a guess.
    assert _row(_Ev(), None, None)["season_type"] == SeasonType.OTHER.value


# ---------------------------------------------------------------------------------------------------------
# migration
# ---------------------------------------------------------------------------------------------------------
def _legacy_frame():
    """A shot-event frame exactly as schema shotevent/1 wrote it: no season-type columns at all."""
    import pandas as pd

    from nba_edge.shotprofile.migrate import NEW_COLUMNS

    rows = []
    for i, gid in enumerate(["espn:1", "espn:1", "espn:2", "espn:3"]):
        rows.append({
            "game_id": gid, "event_id": str(i), "sequence": i, "event_time_utc": "2025-01-15T23:00:00Z",
            "period": 1, "clock_display": "1:00", "clock_seconds_remaining": 60.0,
            "shooter_player_id": 10 + i, "shooter_name": f"P{i}", "team_id": 1, "opponent_team_id": 2,
            "is_home": True, "x": 25.0 + i, "y": float(i), "coordinate_valid": True, "zone": "rim",
            "distance_ft": 1.5 + i, "shot_made": bool(i % 2), "points_value": 2, "is_free_throw": False,
            "is_shooting_play": True, "event_type": "made", "source": "espn",
            "source_observed_at_utc": None, "ingest_version": "espn-pbp/1", "schema_version": "shotevent/1",
        })
    df = pd.DataFrame(rows)
    assert not [c for c in NEW_COLUMNS if c in df.columns]
    return df


def test_migration_adds_the_label_and_changes_nothing_else():
    from nba_edge.shotprofile.migrate import PRESERVED_COLUMNS, fingerprint, migrate_frame

    before = _legacy_frame()
    fp_before = fingerprint(before)
    after, rep = migrate_frame(before, {"espn:1": "preseason", "espn:2": "regular", "espn:3": "playoffs"})
    fp_after = fingerprint(after)

    assert [fp_before[c] for c in PRESERVED_COLUMNS] == [fp_after[c] for c in PRESERVED_COLUMNS]
    assert fp_before["__rows__"] == fp_after["__rows__"]
    assert list(after.season_type) == ["preseason", "preseason", "regular", "playoffs"]
    assert rep["newly_labelled"] == 4 and rep["conflicts"] == 0 and rep["unmatched_rows"] == 0


def test_migration_moves_schema_version_forward_but_leaves_ingest_version_alone():
    """The row SHAPE changed, so schema_version moves. The row was still produced by the old pull, so
    ingest_version must not -- rewriting it would erase where the coordinates actually came from."""
    from nba_edge.shotprofile.migrate import PRESERVED_COLUMNS, VERSION_COLUMNS, migrate_frame

    after, _ = migrate_frame(_legacy_frame(), {"espn:1": "regular", "espn:2": "regular", "espn:3": "regular"})
    assert set(after.schema_version) == {"shotevent/2"}
    assert set(after.ingest_version) == {"espn-pbp/1"}
    # schema_version is the ONLY pre-existing column exempt from the drift gate. ingest_version staying
    # inside it is what stops a future change rewriting provenance without anything noticing.
    assert VERSION_COLUMNS == ("schema_version",)
    assert "ingest_version" in PRESERVED_COLUMNS


def test_migration_is_idempotent():
    from nba_edge.shotprofile.migrate import fingerprint, migrate_frame

    lookup = {"espn:1": "preseason", "espn:2": "regular", "espn:3": "playoffs"}
    once, _ = migrate_frame(_legacy_frame(), lookup)
    twice, rep = migrate_frame(once, lookup)
    assert fingerprint(once) == fingerprint(twice), "a second migration must be a no-op"
    assert rep["newly_labelled"] == 0 and rep["already_labelled"] == 4


def test_migration_keeps_a_scoreboard_label_and_counts_the_disagreement():
    """A label attached at pull time came off the game's own scoreboard entry. The join does not overwrite
    it -- but a disagreement is counted, because a silent overwrite hides the upstream change this column
    exists to expose."""
    from nba_edge.shotprofile.ingest import SEASON_TYPE_SOURCE_SCOREBOARD
    from nba_edge.shotprofile.migrate import migrate_frame

    df = _legacy_frame()
    df["season_type"] = ["regular", "regular", None, None]
    df["season_type_source"] = [SEASON_TYPE_SOURCE_SCOREBOARD, SEASON_TYPE_SOURCE_SCOREBOARD, None, None]

    after, rep = migrate_frame(df, {"espn:1": "preseason", "espn:2": "regular", "espn:3": "playoffs"})
    assert list(after.season_type) == ["regular", "regular", "regular", "playoffs"]
    assert rep["conflicts"] == 2, "espn:1 disagreed, and that has to be visible"
    assert rep["newly_labelled"] == 2
    assert list(after.schema_version) == ["shotevent/1", "shotevent/1", "shotevent/2", "shotevent/2"]


def test_a_game_missing_from_the_lookup_becomes_other_not_a_date_guess():
    from nba_edge.shotprofile.migrate import migrate_frame

    after, rep = migrate_frame(_legacy_frame(), {"espn:1": "regular"})
    assert list(after.season_type) == ["regular", "regular", "other", "other"]
    assert rep["unmatched_games"] == ["espn:2", "espn:3"] and rep["unmatched_rows"] == 2


def test_the_fingerprint_notices_a_single_changed_value():
    """The gate is only worth anything if it actually catches a change."""
    from nba_edge.shotprofile.migrate import fingerprint

    a = _legacy_frame()
    b = a.copy()
    b.loc[0, "x"] = 25.0001
    assert fingerprint(a)["x"] != fingerprint(b)["x"]

    c = a.copy()
    c.loc[0, "shooter_name"] = None
    assert fingerprint(a)["shooter_name"] != fingerprint(c)["shooter_name"], (
        "a null must not digest the same as the text 'None'"
    )


def test_the_fingerprint_ignores_row_order_only():
    from nba_edge.shotprofile.migrate import fingerprint

    a = _legacy_frame()
    assert fingerprint(a) == fingerprint(a.iloc[::-1].reset_index(drop=True))


def test_migrate_season_refuses_to_write_when_a_preserved_column_moves(tmp_path, monkeypatch):
    import nba_edge.shotprofile.migrate as M

    d = tmp_path / "espn"
    d.mkdir(parents=True)
    p = d / "shot_events_2024-25.parquet"
    _legacy_frame().to_parquet(p, engine="pyarrow", index=False)
    before = p.read_bytes()

    real = M.migrate_frame

    def sabotage(df, lookup):
        out, rep = real(df, lookup)
        out = out.copy()
        out.loc[0, "x"] = -1.0  # a "migration" that also moves a coordinate
        return out, rep

    monkeypatch.setattr(M, "migrate_frame", sabotage)
    monkeypatch.setattr(M, "season_type_lookup", lambda root, season: {"espn:1": "regular"})
    res = M.migrate_season(tmp_path, "2024-25", write=True)

    assert res["status"] == "REFUSED_DRIFT" and "x" in res["drift"]
    assert p.read_bytes() == before, "a refused migration must not have written"


# ---------------------------------------------------------------------------------------------------------
# default research population
# ---------------------------------------------------------------------------------------------------------
def _labelled(types):
    import pandas as pd

    return pd.DataFrame({"game_id": [f"espn:{i}" for i in range(len(types))], "season_type": list(types)})


def test_preseason_is_excluded_by_default_and_included_only_on_request():
    from nba_edge.shotprofile.population import research_population

    df = _labelled(["regular", "preseason", "playoffs", "playin", "preseason"])

    kept, rep = research_population(df)
    assert list(kept.season_type) == ["regular", "playoffs", "playin"]
    assert rep["rows_dropped"] == 2 and rep["dropped_by_season_type"] == {"preseason": 2}

    kept2, rep2 = research_population(df, include_preseason=True)
    assert len(kept2) == 5 and rep2["rows_dropped"] == 0
    assert rep2["include_preseason"] is True


def test_allstar_and_unlabelled_games_are_excluded_by_default():
    """'other' means the authoritative code was missing or unrecognised. That is not a licence to assume
    the game counted."""
    from nba_edge.shotprofile.population import research_population

    kept, rep = research_population(_labelled(["regular", "allstar", "other"]))
    assert list(kept.season_type) == ["regular"]
    assert rep["dropped_by_season_type"] == {"allstar": 1, "other": 1}


def test_an_explicit_season_type_set_overrides_the_default():
    from nba_edge.shotprofile.population import research_population

    kept, _ = research_population(_labelled(["regular", "playoffs", "playin"]),
                                  season_types=("playoffs",))
    assert list(kept.season_type) == ["playoffs"]


def test_an_unlabelled_frame_raises_rather_than_passing_everything_through():
    """Defaulting to permissive on a missing column reproduces the original bug exactly."""
    import pandas as pd

    from nba_edge.shotprofile.population import UnlabelledPopulationError, research_population

    with pytest.raises(UnlabelledPopulationError, match="shotevent/2"):
        research_population(pd.DataFrame({"game_id": ["espn:1"]}))

    with pytest.raises(UnlabelledPopulationError, match="partially labelled"):
        research_population(_labelled(["regular", None]))


def test_load_shot_events_filters_by_default_and_can_be_asked_not_to(tmp_path):
    from nba_edge.shotprofile.ingest import COLUMNS, load_shot_events

    d = tmp_path / "espn"
    d.mkdir(parents=True)
    df = _legacy_frame()
    df["season_type"] = ["preseason", "preseason", "regular", "playoffs"]
    df["espn_season_type"] = [1, 1, 2, 3]
    df["season_type_source"] = "espn-scoreboard"
    df[list(COLUMNS)].to_parquet(d / "shot_events_2024-25.parquet", engine="pyarrow", index=False)

    rep: dict = {}
    assert len(load_shot_events(tmp_path, ["2024-25"], report=rep)) == 2
    assert rep["dropped_by_season_type"] == {"preseason": 2}
    assert len(load_shot_events(tmp_path, ["2024-25"], include_preseason=True)) == 4
    assert len(load_shot_events(tmp_path, ["2024-25"], all_season_types=True)) == 4


# ---------------------------------------------------------------------------------------------------------
# prospective readiness reporting
# ---------------------------------------------------------------------------------------------------------
def test_a_stream_that_has_never_written_a_row_is_never_ready():
    """ARMED exists because an offseason no-op and a silent failure look identical from outside.

    The whole point of the readiness audit is that it refuses to call an unproven stream working. If a
    zero-row stream could read READY, the audit would certify the system every summer and say nothing
    different on the night it actually mattered.
    """
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location(
        "prospective_readiness", Path(__file__).resolve().parents[1] / "scripts" / "prospective_readiness.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    rep: dict = {"streams": {}, "blockers": []}

    def stream(name, *, wired, scheduled, rows, detail, blocker=None):
        state = "NOT_READY" if not (wired and scheduled) else ("READY" if rows > 0 else "ARMED")
        rep["streams"][name] = {"state": state, "rows_observed": rows}

    stream("wired_but_silent", wired=True, scheduled=True, rows=0, detail="")
    stream("wired_and_writing", wired=True, scheduled=True, rows=1, detail="")
    stream("missing", wired=False, scheduled=True, rows=99, detail="")

    assert rep["streams"]["wired_but_silent"]["state"] == "ARMED"
    assert rep["streams"]["wired_and_writing"]["state"] == "READY"
    # Rows alone never buy READY: an unwired stream stays NOT_READY however many rows are lying around.
    assert rep["streams"]["missing"]["state"] == "NOT_READY"
    assert mod.BASELINE_DIGEST == (
        "5a4cbda0b973d1e4d6289557b99372e4735ebe3146fa76e8f0b6ca833193be78"
    ), "the audit must compare against the frozen baseline digest, not whatever is live"
