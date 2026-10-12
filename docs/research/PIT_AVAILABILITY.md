# Point-in-time availability: official NBA injury reports, 2025-26 — certified data

**Status: 1,320 of 1,322 games (99.85%) have a certified point-in-time snapshot** — the latest
official injury report uploaded before tip, whose printed report time and upload instant both precede
the tip and which lists the game. T-60 snapshot: 1,320 (99.85%). No model was fitted.

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
  found), so misses are never cached. A re-run on 2026-10-12 (Actions run 38194230872) located 7 of the 9
  Dec 25-26 games left over by the first backfill (2 Dec 25 games still unlocated then). That run was then
  throttled by the CDN (every GET answered 403 after ~4,200 HEAD probes): one located report could not
  be downloaded, and its game now falls back to the latest *fetched* report of that day uploaded before
  the cutoff (`<tag>_fallback_fetched`; verified like every other snapshot). The next re-run (run
  38204511141, after the checks were moved ahead of the bulk probing) located every game, fetched 20
  more reports, and needed no fallback; 20 December games moved to a later, previously 403'd report
  (still uploaded before their cutoff).
* ESPN `/injuries` has no history (current statuses only, each with its own update `date` and the ESPN
  athlete id in the player-card link); it is captured prospectively, not backfilled.
* Parser alignment with production: when this was written, the production parser (`data/injuries.py`,
  context refresh) returned 0 rows on real 2025-26 reports (plain `extract_text` emits one token per
  line). #26 (merged) fixed production with the same positional method. This PR keeps its research
  parser (`availability/official_report.py`, `official-pdf-positional/2`) because the 167,101 committed
  rows are version-pinned to it and it emits columns production does not (page, team text, tricodes,
  NOT YET SUBMITTED rows, per-report diagnostics). `test_research_parser_agrees_with_production_parser`
  pins that both emit identical player rows (date, team, name, status, reason) on all four real report
  fixtures; a future change to either parser that breaks agreement fails CI.

## Backfill (bounded: 2025-26 regular season, play-in, playoffs)

For each game (schedule and scheduled tip from the committed ESPN team-games dataset):
`last_pre_tip` = latest report uploaded strictly before tip; `t_minus_60` = latest uploaded strictly
before tip − 60 min. `pit_ok` = header report time < tip AND upload instant < tip AND both precede the
snapshot's own cutoff (`<tag>_cutoff_utc`: the tip, or tip − 60 min for `t_minus_60`; flag
`<tag>_before_cutoff`) AND the report lists the game. Nothing uploaded at/after a snapshot's cutoff is
ever attached; no post-game source is an input to any status. (Review fix: the T-60 flag originally
re-checked only "< tip"; the locator already selected by upload < tip − 60, and re-verification on the
stored data found 0 of 1,312 located T-60 reports with header or upload ≥ tip − 60, so the tighter
flag changed no count; after the 2026-10-12 re-run, 0 of 1,320 / 1,320 pit_ok snapshots have a
header time or upload instant at or after their cutoff.)

| | last_pre_tip | t_minus_60 |
|---|---:|---:|
| games | 1,322 | 1,322 |
| report located | 1,322 | 1,322 |
| header time and upload < cutoff | 1,322 / 1,322 | 1,322 / 1,322 |
| game listed in that report | 1,320 | 1,320 |
| both teams listed | 1,279 | 1,277 |
| **pit_ok** | **1,320 (99.85%)** | **1,320 (99.85%)** |
| lead (tip − report time), q10 / q50 / q90 / q99 min | 15 / 15 / 30 / 60 | 75 / 75 / 90 / 120 |
| upload lag after report time, q50 / q99 s | 5 / 10 | 5 / 11 |

* By month (last_pre_tip pit_ok): Oct–Nov 1.000, Dec 1.000, Jan–Apr
  1.000, May 0.947, Jun 1.000. W1 holdout window (ET game dates 2026-02-01..04-12, regular, W1's definition): **501 / 501**
  (the first version said 498 / 498, counting by UTC date).
* The 2 May failures (espn:401873342, espn:401873343) are playoff games absent from the last pre-tip
  report (7:45 PM listed only the next day's game); they are not filled from an earlier report.
* "Both teams listed" < "game listed": a team with nothing to report can be absent from the report.

Reports: 1,353 PDFs, 0 fetch/parse errors; every row has team and game (0 missing); 310 hourly-era and
1,043 15-minute files. Each report row stores `url`, `fetched_at_utc` (2026-10-11 / -12), `last_modified_utc`,
`sha256`, `parser_version`.

## Rows and identity mapping

167,101 rows: 159,829 player rows + 7,272 `NOT YET SUBMITTED` team rows. Status mix: out 118,263,
available 17,394, questionable 15,814, probable 4,800, doubtful 3,558. Rows mapped to an ESPN game id:
99.72%.

Player → repo ESPN id (`nba_id = -espn_athlete_id`, candidates from the committed 2025-26 ESPN box
scores; tiers in `availability/identity.py`, never a guess): **97.24% of player rows** (game_box 44,069;
team_season 109,509; season_any_team 1,534; team_initial_last 298; unmatched 4,419), **98.61% of 647
distinct (team, name) pairs**. Unmatched are players with no 2025-26 box-score line (season-long
absences, e.g. Kyrie Irving, Tyrese Haliburton, Dante Exum; unsigned/two-way names).

**Identity mapping is a retrospective join, not point-in-time.** Name → id candidates come from the
2025-26 ESPN box scores, including the game's own box (`game_box`) and the full season
(`team_season`, `season_any_team`), i.e. box scores published after the report. Only the id lookup
uses them; the status, reason, report time and upload instant of every row come from the PDF alone.
Consequences for users: (1) the 2.76% unmatched rows are disproportionately players who never logged
a 2025-26 box line, so a matched-only join under-represents season-long absences; (2) a prospective
consumer must map names with rosters known before the cutoff (the prospective ESPN capture carries the
athlete id directly). Report rows link to their report's `url`, `fetched_at_utc`,
`last_modified_utc` and `sha256` through `slot_et`.

Validation only (post-game box read to check the parser and mapping, never as an input): of matched
players in the certified last-pre-tip report, **Out 11,094 → 0.0% played**, Doubtful 5 → 0%,
Questionable 57 → 59.6%, Probable 25 → 96.0%, Available 2,660 → 86.8%.

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

## Re-fetch spot-check

`scripts/pit_refetch_spotcheck.py` (workflow step on pull requests) re-downloads a seeded sample of
stored reports, including the T-60 reports of seeded games, and compares sha256, `Last-Modified`
and the parsed rows with the stored records; results in `docs/research/pit_availability/refetch_spotcheck.json`.
Runs 38195305077 and 38206776589 (2026-10-12; 9 reports each, the T-60 sample differing because the set
of pit_ok games grew between them): **sha256, Last-Modified and parsed rows identical 9/9 in both**, and
every re-fetched T-60 report's Last-Modified precedes its game's cutoff. (Run 38194230872 was throttled
by the CDN, 0/9 fetched; see above.)

## Files

`data/history/injury_reports/` (1.1 MB): `reports_2025-26.parquet`, `report_rows_2025-26.parquet`,
`game_snapshots_2025-26.parquet`, `probe_cache_2025-26.json`, `MANIFEST.json`;
`docs/research/pit_availability/coverage_2025-26.json`; fixtures `tests/fixtures/injury_reports/*.pdf`.

Reproduce: `python scripts/pit_injury_backfill.py --season 2025-26 --max-minutes 18` (Actions);
`python scripts/pit_injury_backfill.py --season 2025-26 --report-only` (offline coverage).
