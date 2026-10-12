# Full play-by-play + five-man lineup certification (2024-25, 2025-26)

**Status: lineup data CERTIFIED for 2,400 of 2,643 games (90.8%), with per-game pass flags.**
No injury-impact, RAPM or any other model was fitted. This document certifies (or quarantines) data.

It answers the data gap recorded in `LINEUP_FEASIBILITY_R1.md` (zero substitution events committed,
lineups impossible to reconstruct). That gate is now re-measured on real full play-by-play.

## What was fetched, from where, when

| | 2025-26 | 2024-25 |
|---|---:|---:|
| games ingested (regular / play-in / playoffs) | 1,322 (1,231 / 6 / 85) | 1,321 (1,231 / 6 / 84) |
| preseason games skipped (not research population) | 65 | 69 |
| play-by-play events (all types) | 642,354 | 624,638 |
| substitution events | 82,649 (62.5 / game) | 76,019 (57.6 / game) |
| fetch errors | 0 | 0 |
| `fetched_at_utc` range | 2026-10-11 02:13:38Z – 02:21:52Z | 2026-10-11 02:22:04Z – 02:30:12Z |

* Source: ESPN `site.api.espn.com/.../nba/summary?event=<id>` (`plays` + `boxscore` from the SAME payload),
  fetched on GitHub Actions run 38104275276 (`full-pbp-backfill`, PR branch). Every game row carries
  `source`, `source_url`, `fetched_at_utc`, `from_cache`, `payload_sha256`, `ingest_version`.
* cdn.nba.com (`liveData/playbyplay`, `boxscore`, schedule) was re-probed from Actions with both the
  project's NBA and plain headers: **403 Access Denied** on every request (run 38103761758). NBA
  stats/cdn data is therefore not used; ESPN is the only source. Nothing was substituted from another
  source or from post-game derived data.
* This is a retrospective backfill: `fetched_at` is after every game. It is fit for historical
  research; it is not point-in-time captured evidence.

Files (`data/history/espn_pbp/`, zstd Parquet, **21 MB total**):
`pbp_events_<season>` (game_id, event_id, seq, order, period, clock_s, wallclock_utc, type_id,
type_text, text, team_id, p1–p3, scoring/shooting flags, score), `pbp_box_<season>` (starter,
minutes, plus-minus from the same payload), `pbp_games_<season>` (provenance), `stints_<season>`
(both five-man units, seconds, points, possessions, the game's `certified` flag),
`pbp_done_<season>.json`, `PBP_MANIFEST.json`. Per-game flags: `docs/research/lineup_pbp/certification_<season>.csv`;
aggregates: `docs/research/lineup_pbp/summary.json`.

The existing shot-event / box-score datasets (`data/history/espn/`) are untouched; the new ingest is
a separate module (`src/nba_edge/pbp/`).

## Rules (frozen in commit 174da1d before any backfilled data existed)

Period-start lineup inference (`src/nba_edge/pbp/lineups.py`, R1–R4): period 1 = the box score's five
starters; periods 2+ = players whose first appearance in the period is as the exiting player of a
substitution or as a participant in any non-substitution event (technical fouls, ejections,
delay-of-game, challenges and timeouts are not evidence); if fewer than five, fill from the previous
period's ending lineup only when the unseen candidates number exactly the shortfall (`carryover`);
otherwise the game fails. No candidate is ever chosen using minutes, so the minutes check stays an
independent test.

CORE checks (all required for `certified`): five per side after every event; five box starters per
team; every period start resolved; every player's stint minutes within **±1.0 min** of box minutes
(ESPN prints whole minutes); final pbp score = box score; no player participating in an evidence
event while reconstructed off court; no substitution removing an off-court player / adding an
on-court player / missing a participant.
STRICT (diagnostic) checks: plus-minus exact for every player; pbp possessions within **±5%** of the
box estimate 0.96·(FGA+0.44·FTA−OREB+TOV); game clock present and non-increasing.

One rule was revised after seeing data, and only a STRICT one: crediting free-throw points to the
lineup on court at the free throw matched the box plus-minus for only 37.8% / 42.0% of players.
Crediting them to the lineup on court at the **foul** (substitutions happen between foul and
shots) matches **95.9% / 97.2%**. The revised rule is used for plus-minus and stint points; the
at-event figure is still reported (`plus_minus_players_exact_event_rule`). `certified` counts are
identical under both rules (1,193 and 1,207 before and after).

## Results

| check (share of games passing) | 2025-26 | 2024-25 |
|---|---:|---:|
| five on court at every event | 0.9894 | 0.9962 |
| five box starters per team | 1.0000 | 1.0000 |
| period starts resolved | 0.9955 | 0.9992 |
| minutes within ±1.0 of box (every player) | 0.9788 | 0.9894 |
| final score reconciles | 0.9917 | 0.9962 |
| no off-court participation | 0.9266 | 0.9296 |
| substitutions consistent | 0.9720 | 0.9917 |
| **CERTIFIED (all CORE)** | **1,193 / 1,322 = 0.9024** | **1,207 / 1,321 = 0.9137** |
| plus-minus exact, every player (STRICT) | 0.8283 | 0.8562 |
| possessions within ±5% (STRICT) | 0.9887 | 0.9962 |
| clock present + monotone (STRICT) | 1.0000 | 1.0000 |
| **CERTIFIED_STRICT** | **1,012 = 0.7655** | **1,056 = 0.7994** |

By season type (certified / games): 2025-26 regular 1,107/1,231 (0.899), playoffs 80/85, play-in 6/6;
2024-25 regular 1,127/1,231 (0.916), playoffs 76/84, play-in 4/6.
Holdout window used by the W1 matched scorecard (regular season, ET game dates 2026-02-01..2026-04-12,
the W1 definition): **448 of 501 games certified** (390 strict) — versus 0 reconstructable in
`LINEUP_FEASIBILITY_R1.md`. (Review correction: the first version counted 444 of 498 by UTC start
date, which shifts evening games across the window edges.)

Reconciliation detail:

* **Minutes.** Stint minus box minutes, all players: 99.41% / 99.84% within ±1.0; 99.18% / 99.66%
  within ±0.5; quantiles q01 −0.50, q50 0.00, q99 +0.48. The ±0.5 envelope is exactly ESPN's
  round-to-nearest-minute, i.e. the reconstruction agrees with the box to the box's own resolution.
  In certified games the max absolute difference is 0.52 (2025-26) / 1.00 (2024-25).
  Team stint seconds equal 2,880 + 300·OT in **100%** of certified games, and stint points sum to the
  final score in **100%** of certified games.
* **Plus-minus (foul rule).** Players exact: 95.86% / 97.17% overall; 96.7% / 97.8% in certified games.
* **Possessions.** pbp count / box estimate: mean 1.017 / 1.016, q05 0.990, q95 1.042 / 1.039. The
  ~1.6% excess is the 0.96 factor's known undercount; the play-by-play counts possession changes.
* **Period starts.** 16 / 11 period-starts needed the `carryover` rule (5 / 8 of those games
  certified); period-1 inference from events alone agreed with the box starters in 99.85% / 100%.
* **Timestamp fidelity.** Game clock present on 100% of events and non-increasing within every
  period (100%). ESPN `wallclock` present on 100% of events (contrary to the shot-only ingest, which
  stamped every event with the scheduled tip), non-decreasing for 99.2%. Substitutions: clock and
  wallclock present 100%; both participants present 99.99%; clock equal to the preceding play's
  clock (a dead ball) or the period start in 95.9%; wallclock gap from a substitution to the next
  play median 33 s (q05 −1 s, q95 ~175 s), i.e. subs are logged at the stoppage, before play resumes.

Why games fail (2025-26 / 2024-25 game counts; a game can have several): off-court participation
97 / 93 (spread over ordinary events — jump shots, rebounds, turnovers, fouls — i.e. a substitution
ESPN never logged or logged late); inconsistent substitutions 37 / 11; substitutions with a missing
participant 33 / 6 (e.g. `"Zach Edey enters the game for "` with no exiting player, espn:401809807 OT);
minutes outside ±1.0 28 / 14; not five per side 14 / 5; final-score mismatch 11 / 5; over-full
period start 6 / 1. Failing games are quarantined (`certified = false` with `reasons`), never repaired.

## Provenance re-verification (review, 2026-10-12)

* **Re-fetch spot-check** (`scripts/pbp_refetch_spotcheck.py`, workflow step; Actions runs
  38193844683 and 38194259669 — the committed `docs/research/lineup_pbp/refetch_spotcheck.json` is the
  second; later no-op runs keep their result in the run log/artifact only): 8 seeded games (4 per season)
  downloaded again on 2026-10-12 02:00Z, ~24 h after the backfill, and parsed with the same parser:
  **8 / 8 identical** in every stored event field (3,936 events) and every box line. Raw payload sha256
  differs for all 8, as expected (the summary also carries volatile news/odds/standings sections, which
  are not parsed); the parsed play-by-play and box content is what is compared. The same run re-ran
  the backfill (0 new games) and the certification; the committed stints / certification / summary
  files came out byte-identical (deterministic).
* **Independent earlier fetch** (offline): the committed box-score history
  `data/history/espn/player_games_<season>` (pulled 2026-09-19) agrees with this PR's same-payload box
  lines on **69,965 / 69,965 common player-game rows** (minutes and points exact; 34,767 in 2025-26,
  35,198 in 2024-25). The committed shot-event dataset (observed 2026-09-28/29) matches this PR's
  shooting plays by ESPN event id on **591,089 rows** (2025-26: 298,340 of 298,340; 2024-25: 292,749 of
  292,750) with identical shooter, period and type; clocks agree to float32 precision; the only
  semantic difference is that missed free throws carry `score_value` 0 here and an attempt value of 1
  there. One gap belongs to the older dataset, not this one: 10 2025-26 box lines for Lachlan Olbrich
  (CHI, ESPN 5107156) are in this PR's box but missing from `player_games_2025-26`.

## Use

For R1-style work: use `stints_<season>.parquet` rows with `certified == True` (38,677 / 36,683
stints). Do not fit on uncertified games. This PR fits nothing; `impact_ppp` remains 0.

## Reproduce

```
python scripts/pbp_backfill.py --seasons 2025-26,2024-25 --max-minutes 17   # Actions only (ESPN)
python scripts/lineup_certify.py --seasons 2025-26,2024-25                  # offline, deterministic
pytest tests/test_pbp_lineups.py
```
