# Point-in-time availability: official NBA injury reports, 2025-26 — certified data

**Status: 1,311 of 1,322 games (99.17%) have a certified point-in-time snapshot** — the latest
official injury report uploaded before tip, whose printed report time and upload instant both precede
the tip and which lists the game. Same coverage for a T-60 snapshot (1,310). No model was fitted.

## Source and what was learned about it

* Official NBA injury report PDFs, `https://ak-static.cms.nba.com/referee/injury/Injury-Report_<file>.pdf`,
  fetched on GitHub Actions (the dev container cannot reach the host). A missing file answers 403.
  The `official.nba.com` season index page loads (browser headers) but exposes no static PDF links.
* **Cadence and naming changed mid-season** (measured from HEAD `Last-Modified` and the PDF headers):
  * to 2025-12-21: files are hourly `_HHPM`, but the file named `_06PM` is the **6:30 PM** report
    (to 12-18) or the **6:45 PM** report (12-19..21) — the header and Last-Modified agree;
  * from 2025-12-22: a report every 15 minutes, `_HH_MMPM`, uploaded ~5 s after the slot.
  The filename is therefore only a locator. **`report_time_utc` is the time printed in the PDF header**;
  the upload instant is the HTTP `Last-Modified`.
* The CDN returns 403 transiently for files that exist (a first run "lost" Dec 25-31 that a later run
  found), so misses are never cached; 9 games (Dec 25-26) were still unlocated in the final run.
* ESPN `/injuries` has no history (current statuses only, each with its own update `date` and the ESPN
  athlete id in the player-card link); it is captured prospectively, not backfilled.
* The repo's existing official-report parser (`data/injuries.py`, used by the context refresh) returns
  **0 rows** on a real 2025-26 report: plain `extract_text` emits one token per line. A positional parser
  (`availability/official_report.py`, pypdf text-visitor coordinates) was written instead; a test pins
  the legacy behaviour. Fixing production is out of scope (separate task suggested).

## Backfill (bounded: 2025-26 regular season, play-in, playoffs)

For each game (schedule and scheduled tip from the committed ESPN team-games dataset):
`last_pre_tip` = latest report uploaded strictly before tip; `t_minus_60` = latest uploaded strictly
before tip − 60 min. `pit_ok` = header report time < tip AND upload instant < tip AND the report lists
the game. Nothing uploaded at/after tip is ever attached; no post-game source is an input.

| | last_pre_tip | t_minus_60 |
|---|---:|---:|
| games | 1,322 | 1,322 |
| report located | 1,313 | 1,312 |
| header time < tip / upload < tip | 1,313 / 1,313 | 1,312 / 1,312 |
| game listed in that report | 1,311 | 1,310 |
| both teams listed | 1,270 | 1,267 |
| **pit_ok** | **1,311 (99.17%)** | **1,310 (99.09%)** |
| lead (tip − report time), q10 / q50 / q90 min | 15 / 15 / 45 | 75 / 75 / 105 |
| upload lag after report time, q50 / q99 s | 5 / 10 | 5 / 11 |

* By month (last_pre_tip pit_ok): Oct–Nov 1.000, Dec 0.955 (9 unlocated Dec 25-26 games), Jan–Apr
  1.000, May 0.947, Jun 1.000. W1 holdout window (2026-02-01..04-12, regular): **498 / 498**.
* The 2 May failures (espn:401873342, espn:401873343) are playoff games absent from the last pre-tip
  report (7:45 PM listed only the next day's game); they are not filled from an earlier report.
* "Both teams listed" < "game listed": a team with nothing to report can be absent from the report.

Reports: 1,333 PDFs, 0 fetch/parse errors; every row has team and game (0 missing); 310 hourly-era and
1,023 15-minute files. Each report row stores `url`, `fetched_at_utc` (2026-10-11), `last_modified_utc`,
`sha256`, `parser_version`.

## Rows and identity mapping

164,314 rows: 157,164 player rows + 7,150 `NOT YET SUBMITTED` team rows. Status mix: out 116,341,
available 16,929, questionable 15,631, probable 4,728, doubtful 3,535. Rows mapped to an ESPN game id:
99.71%.

Player → repo ESPN id (`nba_id = -espn_athlete_id`, candidates from the committed 2025-26 ESPN box
scores; tiers in `availability/identity.py`, never a guess): **97.24% of player rows** (game_box 43,261;
team_season 107,753; season_any_team 1,534; team_initial_last 281; unmatched 4,335), **98.61% of 647
distinct (team, name) pairs**. Unmatched are players with no 2025-26 box-score line (season-long
absences, e.g. Kyrie Irving, Tyrese Haliburton, Dante Exum; unsigned/two-way names).

Validation only (post-game box read to check the parser and mapping, never as an input): of matched
players in the certified last-pre-tip report, **Out 11,017 → 0.0% played**, Doubtful 7 → 0%,
Questionable 66 → 60.6%, Probable 25 → 96%, Available 2,619 → 86.7%.

## Prospective capture (append-only)

`scripts/pit_capture.py` / `availability/capture.py`, workflow job `capture` (hourly at :41 + dispatch,
only once on the default branch): latest official report (if new slot/sha) + an ESPN `/injuries`
snapshot, each a write-once `jsonl.gz` (mode `xb`) under `injury_pit/` on the dedicated
`data-injury-pit` branch (never main, never `data-archive`), every row with `fetched_at_utc`, a
`MANIFEST.jsonl` sha256 hash chain verified before and after each run, one constant concurrency group.
Every capture first self-tests the parser on a known report (151 rows). PR runs are DRY-RUN: run
38105674909 fetched live, self-test 151 rows / 0 missing team, found no official report in the last 6
hours (off-season), captured 134 ESPN injury rows (134 with athlete id), chain verified, artifact
uploaded, nothing committed.

## Files

`data/history/injury_reports/` (1.1 MB): `reports_2025-26.parquet`, `report_rows_2025-26.parquet`,
`game_snapshots_2025-26.parquet`, `probe_cache_2025-26.json`, `MANIFEST.json`;
`docs/research/pit_availability/coverage_2025-26.json`; fixtures `tests/fixtures/injury_reports/*.pdf`.

Reproduce: `python scripts/pit_injury_backfill.py --season 2025-26 --max-minutes 18` (Actions);
`python scripts/pit_injury_backfill.py --season 2025-26 --report-only` (offline coverage).
