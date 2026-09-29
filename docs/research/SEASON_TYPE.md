# Season type: persistence, migration, and the research population

**Authority: RESEARCH.** Nothing here changes `NBA_BASELINE_2026_PRESEASON_V1`, V1 simulation parameters,
pricing, hybrid weights, MATCHUP_AWARE_V2 (`effects_version = neutral-0`) or any betting behaviour.

## The gap

Shot-event rows written under schema `shotevent/1` carried no season field of any kind. Verified directly
against `shot_events_2024-25.parquet` before any change: `season_type present: False`, and no column whose
name contained "season" at all.

Nothing downstream could therefore distinguish a camp game from a real one, and nothing did. Across the three
backfilled seasons the stored corpus is 927,349 shot events, of which **45,414 (4.9%) are preseason**.

## What the label is, and what it is not

The label comes from ESPN's own `season.type` on the game's scoreboard entry, mapped through the authoritative
table that already existed in `data/history.py`:

| ESPN `season.type` | canonical `SeasonType` |
|---|---|
| 1 | `preseason` |
| 2 | `regular` |
| 3 | `playoffs` |
| 5 | `playin` |
| anything else | `other`, with the raw code kept in `espn_season_type` |

It is **not** inferred from the calendar. An October game that ESPN calls a regular-season game stays
`regular`; a game whose code is missing or unrecognised becomes `other`, never a guess. An unknown code is
retained rather than dropped, so a change upstream shows up in the data instead of quietly deleting games from
every study.

Schema `shotevent/2` adds three columns:

- `season_type` — the canonical value above
- `espn_season_type` — the raw upstream code, so a surprise is auditable
- `season_type_source` — `espn-scoreboard` (attached during the pull) or `espn-player-games` (joined by the
  migration). Both mean "ESPN's own field"; neither is a date inference, and no date-inference source exists.

`espn_season_type` is deliberately left null on backfilled rows rather than reconstructed by inverting the
mapping. That column's job is to surface codes the mapping does not know; a value derived from the mapped
label could never be one, so inverting it would turn an early-warning field into a tautology.

## Migration

`nba shot-events-migrate` backfills the label onto files written before `shotevent/2`. It joins
`player_games_{season}.parquet`, which already carries ESPN's `season_type` and covers **100% of shot-event
games (4,160 / 4,160)**, so no network round-trip is needed.

The migration is additive by construction and proves it rather than asserting it:

- per-column digests are taken before and after, over rows in canonical `(game_id, sequence, event_id)` order;
- it **refuses to write** if any pre-existing column's digest moves (`status: REFUSED_DRIFT`);
- the written file is read back and re-fingerprinted, because the in-memory gate does not cover the write;
- verified independently against the git blobs, column by column.

Result across all three seasons: row counts identical, `added = [season_type, espn_season_type,
season_type_source]`, `removed = []`, and of the pre-existing columns only `schema_version` changed.
Game ids, event ids, coordinates, validity flags, zones, distances, results, points values and player/team
identities are all identical.

`schema_version` moves `shotevent/1 -> shotevent/2` because it describes the row *shape*, which is what
changed. `ingest_version` deliberately does **not**: a backfilled row was still produced by `espn-pbp/1`, and
rewriting it would erase where the coordinates actually came from. It stays inside the drift gate; a test pins
that `schema_version` is the only pre-existing column exempt.

A second run is **byte-identical** to the first (`sha256` over all three Parquet files), and reports
`newly_labelled: 0`. A row that already carries a label keeps it — a scoreboard label is no less authoritative
than the join — but a disagreement is *counted*, not silently overwritten.

## Classification audit

`scripts/season_type_audit.py` cross-checks the labels against the league's own (Eastern) calendar. The labels
come from ESPN; the dates come from the schedule; if they disagreed, the blocks would overlap. They do not.

| season | type | games | shot events | first (ET) | last (ET) |
|---|---|---:|---:|---|---|
| 2023-24 | preseason | 64 | 14,575 | 2023-10-05 | 2023-10-20 |
| 2023-24 | regular | 1,231 | 272,368 | 2023-10-24 | 2024-04-14 |
| 2023-24 | playin | 6 | 1,300 | 2024-04-16 | 2024-04-19 |
| 2023-24 | playoffs | 82 | 17,177 | 2024-04-20 | 2024-06-17 |
| 2024-25 | preseason | 69 | 15,589 | 2024-10-04 | 2024-10-18 |
| 2024-25 | regular | 1,231 | 273,048 | 2024-10-22 | 2025-04-13 |
| 2024-25 | playin | 6 | 1,328 | 2025-04-15 | 2025-04-18 |
| 2024-25 | playoffs | 84 | 18,374 | 2025-04-19 | 2025-06-22 |
| 2025-26 | preseason | 65 | 15,250 | 2025-10-02 | 2025-10-17 |
| 2025-26 | regular | 1,231 | 278,277 | 2025-10-21 | 2026-04-12 |
| 2025-26 | playin | 6 | 1,320 | 2026-04-14 | 2026-04-17 |
| 2025-26 | playoffs | 85 | 18,743 | 2026-04-18 | 2026-06-13 |

`status: OK`, zero violations. Two independent checks land:

- **Strict block ordering.** Each block starts strictly after the previous one ends, in all three seasons.
  Read in UTC the play-in and playoff blocks appeared to share a day; that was an artifact of evening ET tips
  rolling over midnight UTC, not a classification error, and the audit reads in ET for that reason.
- **Game counts.** Every season shows exactly **1,231** regular-season games: the 1,230-game schedule plus the
  NBA Cup final, which is labelled regular but does not count in the standings. Three seasons landing on the
  same number by accident is not plausible.

Representative games check out against the real calendar: opening night 2023-10-24 / 2024-10-22 / 2025-10-21,
and the last playoff game 2024-06-17 / 2025-06-22 / 2026-06-13.

## Default research population

`load_shot_events` now returns **regular + play-in + playoffs** by default. Play-in is counted as postseason:
the same rotations play it under real stakes and it settles real markets.

Preseason, All-Star and `other` are **stored and retained** but excluded unless asked for:

- `include_preseason=True` — the narrow opt-in, widening the default set
- `season_types=(...)` — an explicit set, replacing it
- `all_season_types=True` — the raw read, for auditing and migration rather than studies

`other` is excluded by default too: it means the authoritative code was missing or unrecognised, which is not
a licence to assume the game counted.

A frame with **no** `season_type` column, or with any missing value in it, **raises**
`UnlabelledPopulationError` rather than passing through. Defaulting to permissive on a missing column is
precisely how the contamination happened the first time, and it is the one case where a permissive default
reproduces the original bug exactly.

## Tests

`tests/test_season_type.py`. Six deliberate mutations were introduced and all six were caught:

| mutation | caught by |
|---|---|
| preseason added to the default population | `test_load_shot_events_filters_by_default_...` |
| missing `season_type` column passes through instead of raising | `test_an_unlabelled_frame_raises_...` |
| drift gate disabled so the migration writes anyway | `test_migrate_season_refuses_to_write_...` |
| migration overwrites an existing scoreboard label | `test_migration_keeps_a_scoreboard_label_...` |
| `ingest_version` removed from the drift gate | `test_migration_moves_schema_version_forward_...` |
| `_row` falls back to `regular` instead of `other` | `test_ingested_rows_carry_the_games_season_type_verbatim` |
