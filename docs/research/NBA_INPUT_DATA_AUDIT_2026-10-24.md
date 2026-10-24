# NBA basketball-input audit — 2026-10-24 (Phase 5)

Companion to `NBA_COLLECTION_RELIABILITY_AUDIT_2026-10-24.md`. Read-only dataset audit; every number was recomputed from files on disk unless marked UNVERIFIED.
Archives audited: `data-archive` @ `9523c12`, `projection-data` @ `b1fad93`, repo `main` @ `8927d69`. Two items were re-verified independently by the lead author:
the `OnOffIndex` quarantine gap (section 2) and the shot-profile timestamp defect (section 5 #1, now **fixed** in PR-E; the committed parquet shows `tip_ts` max 1,781,397 and per-player decay in 0.07% of steps).
Section 2's quarantine gap and the stale lineup health report are fixed in PR-A (`nba_edge/pbp/stints.py`, `OnOffIndex` refuses uncertified rows, dashboard reads disk).

## 0. Bottom line

* Headline counts are TRUE but mean less than they sound. 4,160 games includes 198 preseason games and 1,383 games (all of
  2023-24) that have no play-by-play. Usable regular/play-in/playoff games: 3,962. Games with certified lineups: 2,400
  (57.7% of 4,160; 60.6% of 3,962).
* Point-in-time pregame availability exists for ONE historical season (2025-26, 1,322 games) plus 6 days of live capture.
  2023-24 and 2024-25 have none, so every multi-season minutes/participation model is trained on retrospective proxies.
* There is NO pregame starter source. The only wired candidate (ESPN summary starter flags) returned 0 starters in 52 probes.
  This is a research blocker (section 3).
* Lineup quarantine is a boolean column only. Nothing in code forces a consumer to honour it (section 2).
* Real defects found: 2025-26 shot-event table disagrees with box FGA (heaves), shot-profile `tip_ts` unit bug that silently
  disables recency decay, preseason leaking into league priors and two research tables, ESPN-vs-NBA team-id split,
  stale hard-coded "no stint data" health report (section 5).

## 1. Dataset inventory and verification of headline claims

| claim | verdict | measurement |
|---|---|---|
| ~4,160 games | VERIFIED (with caveat) | `data/history/espn/team_games_*.parquet` 8,320 rows / 4,160 unique game_id; 3 seasons |
| 112,427 player-game rows | VERIFIED | 37,445 + 37,836 + 37,146 = 112,427 (`espn/player_games_*.parquet`) |
| 137,059 Kalshi markets | VERIFIED | 137,059 lines = 137,059 unique tickers across 13 `markets_*.jsonl.gz` (KXNBAPRA file is empty, 0 rows) |
| 2,400 certified lineup games | VERIFIED | certification CSVs 1,207 (2024-25) + 1,193 (2025-26) = 2,400 of 2,643 (90.8%); stints parquet flag agrees 100% |
| (stale) 4,094 games / 110,714 rows | docs/HANDOFF.md:~70 still quotes these | superseded; not a data problem |

Box-score history (`data/history/espn/`, pulled 2026-09-19 per MANIFEST):

| season | regular | play-in | playoffs | preseason | games | player rows | date range |
|---|---:|---:|---:|---:|---:|---:|---|
| 2023-24 | 1,231 | 6 | 82 | 64 | 1,383 | 37,445 | 2023-10-05..2024-06-17 |
| 2024-25 | 1,231 | 6 | 84 | 69 | 1,390 | 37,836 | 2024-10-04..2025-06-22 |
| 2025-26 | 1,231 | 6 | 85 | 65 | 1,387 | 37,146 | 2025-10-02..2026-06-13 |
| total | 3,693 | 18 | 251 | 198 | 4,160 | 112,427 | |

Integrity checks on player_games:

| check | result |
|---|---|
| duplicate (game_id, nba_id) / full-row duplicates | 0 / 0 |
| null rate: minutes, started, played, pts, fga, plus_minus | 0.0000 each (DNP rows carry minutes = 0.0, not null; `played == (minutes>0)` for all 112,427) |
| `dnp_reason` null | 81.06% (= played rows, expected); 17,669 DNP rows are "COACH'S DECISION" |
| played / DNP-or-absent rows | 90,489 / 21,938 |
| starters per team-game | 5 in 8,319 of 8,320; ONE preseason game has 9 (`espn:401591936`, 2023-10-20, ATL) |
| `started` but `played` false | 2 rows (both Mikal Bridges, final-day games 2025-04-13 and 2026-04-12) |
| team minutes != 240+25*OT by more than 2 | 118 of 8,320 team-games (1.4%); by more than 5: 15, of which 14 are CHI 2025-26 (missing player, below) |
| player pts sum != team pts | 14 team-games, ALL CHI (12 regular, 2 preseason) in 2025-26 |
| `game_date_et` vs ET date of `start_time_utc` | 0 mismatches in 112,427 rows (UTC date would differ for 83,311 rows, so the ET key is correct) |
| one home team per game | 4,160 / 4,160 |
| `nba_id` sign | 100% NEGATIVE: the column holds `-espn_athlete_id` (934 distinct ids). There are no NBA ids anywhere in the box data |

ESPN omits at least one CHI player in 14 team-games (e.g. `espn:401810934` team minutes 217, -23 vs expected). `espn_pbp/pbp_box`
has Lachlan Olbrich (ESPN 5107156) in 10 of them, `player_games_2025-26` does not (34,767 vs 34,777 rows). Seven CHI games
are missing points in BOTH datasets (2-9 pts); the lineup certifier correctly quarantines those 7 and certifies the 5 where
pbp_box has the player.

Play-by-play / lineups (`data/history/espn_pbp/`, fetched 2026-10-11, one Actions run):

| | 2024-25 | 2025-26 | total |
|---|---:|---:|---:|
| PBP games (regular/play-in/playoffs only) | 1,321 | 1,322 | 2,643 |
| events | 624,638 | 642,354 | 1,266,992 |
| box games WITHOUT pbp | 69 (all preseason) | 65 (all preseason) | 134 preseason + 1,383 (all 2023-24) = 1,517 |
| PBP games without a box row in player_games | 0 | 0 | 0 |
| certified (CORE) | 1,207 (91.4%) | 1,193 (90.2%) | 2,400 (90.8%) |
| certified_strict (plus-minus exact + possessions + clock) | 1,056 (79.9%) | 1,012 (76.5%) | 2,068 (78.2%) |
| pbp games WITH PBP but NOT certified | 114 | 129 | 243 |
| stints rows (certified / all) | 36,683 / 40,263 | 38,677 / 42,914 | 75,360 / 83,177 |
| pbp_box starter flags per team-game | 5 for 2,642/2,642 | 5 for 2,644/2,644 | no nulls in starter/minutes/nba_id |
| pbp_box vs player_games common rows (minutes, starter) | | | 69,965 / 69,965 identical on both (doc claim verified) |

Certification rate by month is flat (0.887..0.947 for months with >30 games), so there is no drift in the recent past. The W1
holdout (2026-02-01..04-12, regular) is 448 of 501 certified, 390 strict (doc claim verified).

Other history: `shot_events_*` 305,420 / 308,339 / 313,590 rows (all 3 seasons, includes preseason: 14,575 / 15,589 / 15,250);
`injury_reports` 2025-26 only (section 3); Kalshi `MANIFEST.json` close dates 2025-10-01..2026-07-01.

Kalshi coverage that matters for projections:

| series | markets | events (games) | markets with candles |
|---|---:|---:|---:|
| KXNBAGAME | 2,898 | 1,449 | 100% |
| KXNBASPREAD / TOTAL / TEAMTOTAL | 16,937 / 14,787 / 9,486 | 1,324 / 1,324 / 529 | 32.9% / 15.1% / 14.8% |
| KXNBAPTS / REB / AST / 3PT | 23,562 / 22,656 / 17,745 / 16,619 | 1,096 / 1,069 / 1,056 / 1,029 | 14.9% / 14.5% / 14.6% / 14.3% |
| 1H* , WINS | 12,099 , 270 | 523 , 30 | 0% |

Settlement: 4.3% of PTS markets settle `scalar` (1,005 of 23,562). The labelled pregame table
`data/research/market_table.parquet` has 68,235 rows but only 33,111 are player-scope rows, covering **152 games** (140 regular,
12 playoffs; 2025-11-19..2026-05-28), 153 players, i.e. only 2.4% of 2025-26 regular-season played player-games have a priced
pregame prop row. Prop-market evidence is thin because candles were pulled for ~15% of markets, not because markets are missing.

## 2. Lineup / stint certification

How certification is decided (`src/nba_edge/pbp/lineups.py` header, `scripts/lineup_certify.py`): period-1 lineup = box starters;
periods 2+ inferred from first-appearance rules R2-R4 (no minutes used); CORE checks all required: five on court at every event,
five box starters, period starts resolved, every player's stint minutes within +/-1.0 min of box, final score equals box,
no off-court participation, substitutions consistent. STRICT (diagnostic only): plus-minus exact, possessions within 5%, clock.
Rules frozen before data (commit 174da1d per doc); one STRICT rule revised after seeing data (FT credit at foul).

Remeasured pass rates: see section 1 (90.8% CORE, 78.2% strict). Failure reasons (counts of games, may overlap): off-court
participation 97 + 93, inconsistent subs 37 + 11, unresolved subs 33 + 6, minutes >1.0 off 28 + 14, not-five-per-side 14 + 5,
score mismatch 11 + 5. Validation weakness: the minutes test has +/-1.0 min tolerance against whole-minute box minutes (cannot
discriminate inside 1 min), and 332 certified games fail strict (plus-minus exact for all players), so "certified" is weaker than
"strict". Certified stints are internally clean: 0 of 75,360 certified stints have !=5 players or null slots, and team seconds
= 2,880+300*OT in 100% of both certified and uncertified games.

Quarantine mechanism: **NONE enforced.** `scripts/lineup_certify.py:98,107` writes certified AND uncertified stints into the same
`stints_<season>.parquet` with a `certified` boolean. Uncertified stints look healthy: 89.9% (2025-26) and 95.6% (2024-25) of
uncertified games have only 5-man stints (3,580 + 4,237 = 7,817 uncertified stint rows). `pbp_events_*` and `pbp_box_*` hold all
2,643 games with no flag. Only a documentation instruction ("use `certified == True`", LINEUP_PBP_CERTIFICATION.md "Use").

Consumers of lineup / stint / pbp outputs (grep of src/nba_edge, research/, scripts/, tests/):

| consumer | reads | checks `certified`? | verdict |
|---|---|---|---|
| `scripts/nba_participation_study.py:69-78` (`load_onoff`) | stints_2025-26 | YES, `st = st[st["certified"]]` at :70 | OK |
| `src/nba_edge/research/participation.py:56-63` `OnOffIndex.from_stints` | stints DataFrame passed by caller | NO; docstring says "certified stint rows" only | RISK: any new caller that passes the raw file consumes uncertified games; no test enforces it (`tests/test_participation_w2.py:63` passes a hand-made frame) |
| `research/projection_foundation/nba/inventory.py:70-73` | row counts of both stints files | NO, counts all 83,177 rows | overstates usable rows by 9.4% (75,360 certified) in the data-availability matrix |
| `src/nba_edge/matchup/ingest.py:196` `quarantine_stints` | n/a | n/a: defined, called nowhere, no adapter implements `stints()`; checks only 5/5 sizes, duplicates and negative duration | dead code; its test would pass ~90% of uncertified games |
| `src/nba_edge/ops/evidence_health.py:165-172` | none | hard-coded `stint_data.state = "absent"`, `n_games_available = 0` | STALE: 2,643 games / 2,400 certified exist on disk. `da/EVIDENCE_HEALTH.json` repeats it. `research_export.py:1572` also says lineups UNAVAILABLE |
| projection-foundation live path (`research/projection_foundation/nba/live/*`, `nba/minutes.py`) | none | n/a | does NOT use stints/on-off at all |
| frozen champion sim (`src/nba_edge/features/build.py`, `sim/`) | none | n/a | does NOT use stints/on-off |

So today the only live exposure is `OnOffIndex`, used by a research study. But lineup data has zero prospective pipeline:
`full_pbp.yml` is pull_request / workflow_dispatch only, there is no `pbp` folder in `da` or `pd`, and no 2026-27 game has stints.

## 3. Pregame availability and starters

Sources present:

| source | where | point-in-time quality |
|---|---|---|
| Official NBA injury-report PDF, 2025-26 retro backfill | `data/history/injury_reports/` (1,353 reports, 167,101 rows: 159,829 player + 7,272 NOT-YET-SUBMITTED team rows) | per report: header `report_time_utc`, HTTP `last_modified_utc`, `fetched_at_utc`, sha256, parser version. Retrospective fetch (2026-10-11) but publish time is the PDF's own timestamp |
| Per-game snapshot table | `game_snapshots_2025-26.parquet` | `last_pre_tip` and `t_minus_60` locators with `*_pit_ok`, cutoff, lead |
| Official PDF live capture | `pd/availability` (source `nba_official_injury_report`), `da/context/injuries` (`nba_official_pdf`) | `captured_utc`, `source_updated_utc`, `report_time_utc` on every row |
| ESPN `/injuries` live | same two archives | NOT point-in-time at source: no history; `report_time_utc` in da is just the fetch instant; Day-To-Day is mapped to QUESTIONABLE (506 rows in pd) |
| ESPN box `dnp_reason` | player_games | post-game; retrospective only |
| Confirmed starters | none | see below |

2025-26 historical snapshot coverage (recomputed from the parquet): 1,322 games (1,231 regular, 85 playoff, 6 play-in);
`pit_ok` 1,320 (99.85%) for both last-pre-tip and T-60; the 2 failures are 2026-05-21/23 playoff games. Both teams listed in
1,279 (96.7%) / 1,277. Lead before tip: last_pre_tip median 15 min (q25 15, q75 30, max 60); T-60 median 75. Fallback-fetched
snapshots: 0. Coverage versus all box games: 1,322 / 4,160 = 31.8% (33.4% of non-preseason). 2023-24 and 2024-25: none.

Validation reproduced (Out 11,094 -> 0 played; doubtful 5 -> 0; questionable 57 -> 59.6%; probable 25 -> 96.0%; available 2,660
-> 86.8%). Gaps: coach's-decision DNPs are 4,868 rows, only 6.9% listed (unobservable); injury-type DNPs in the box are 1,318
rows, 90.4% listed at last pre-tip (about 126 late scratches/unlisted).
Identity: player mapping 97.24% (unmatched 4,419 rows = 2.76%, **94.5% of them "out"**, Irving 972, Haliburton 965, Sorber 1,003,
Djurisic 601, Exum 577, Yang 260). 3.5% of all Out rows are therefore invisible to any matched-only join, and
`research/projection_foundation/nba/injury.py:34` fills unmatched/unlisted with "AVAILABLE". The `game_box` identity tier
(27.6% of rows) uses the game's own post-game box (documented, id lookup only). 473 rows (0.28%) have null game_id.

Live capture, 2026-10-19..24 (`pd/availability`, 31 files, 9,421 rows, 36 games, dates 2026-10-20..25):

| item | measurement |
|---|---|
| rows by source | official 7,820 (1,511 explicit REPORTED + 6,309 implicit "not listed" = ACTIVE/PROJECTED), ESPN 1,601 (all PROJECTED) |
| regular-season games already tipped with availability rows | 28 of 28 (da schedule: 107 regular games listed, 66 preseason games Oct 3-16 have none because pd capture starts 10-19) |
| last official report before tip, lead | median 30 min (min 15, max 105); 5 of 28 games have the final report more than 60 min before tip |
| capture delay after PDF header time | median 9.3 min, p99 14.9; 0 rows captured at/after tip |
| 12 unmatched names | e.g. `unmatched:CLE:diop_khalifa` (two-ways), kept as `unmatched:*` entity ids |
| last pre-tip forecast participation basis (`pd/forecasts`, 1,197 player-games) | PROJECTED 827 (777 implicit-active), REPORTED 205 (17.1%), UNKNOWN 165 |
| forecasts | 83,362 rows, 86 files, 36 games, 593 players; `data_asof_utc` < game start on 100%; latest forecast per game median 34 min before tip |
| outcomes | 6,665 rows, 19 games (vs 28 tipped; the 9 missing reason is UNVERIFIED, likely collection lag) |

`da/context/injuries`: 371 snapshots 2026-09-18..10-24, 40,825 rows, official PDF present in only 86 of 371 snapshots (off-season/
no report), **game_id and nba_id are null on 100% of rows** (identity is joined later in pd). All of the above is 6 days of data.

Starter confirmation: **no source exists. RESEARCH BLOCKER.** Evidence:
* `docs/ops/FIRST_SLATE_CHECKLIST.md:157`: "Confirmed starters: unavailable ... Do not infer from projected lineups, never use post-game flags".
* `da/matchup/context`: `expected_home/away_starters` empty in 2,643 of 2,643 rows, `lineup_confidence = unknown` throughout.
* `research/projection_foundation/nba/live/availability.py:15,280-331` implements `espn_summary_starters` (pre-tip box starter flags, PROJECTED).
  Across the 32 pd run logs: 52 game-probes in state `pre`, 0 starters, 0 box players pre-tip; zero `kind: starter` rows in
  `pd/availability`. ESPN does not publish starters before tip in this payload (empirically).
* `docs/NBA_DATA_SOURCE_AUDIT.md:22` mentions Rotowire (HTTP 200, 343 KB HTML, `docs/probe/probe_results.md`) as "projected starting
  lineups; research-only fallback; not a production dependency". It is projected, not confirmed; no terms-of-use or licence
  review exists for it anywhere in the repo (grep: licence/terms discussed only for Basketball-Reference, which is excluded).
  `MATCHUP_SOURCE_AUDIT.md:30` lists "beat reporters; lineup aggregators" without assessing any.
* `docs/HANDOFF.md:187` item 8 proposes starter confirmation "from the official injury report near tip": the report has no
  starter field (`report_rows` columns: status, reason, team, player only), so that route does not exist.
* Official NBA CDN/stats (the usual starter source) are blocked from Actions (403 / timeout; SOURCE_AUDIT_GRANULAR.md,
  LINEUP_PBP_CERTIFICATION.md). ESPN endpoints have "no published terms for programmatic use" (MATCHUP_SOURCE_AUDIT.md:186).
* Value at stake: RESULTS_NBA.md priority 2 quantifies the oracle at -0.17 min beyond injuries, and the champion's starter MAE regressed
  (MINUTES_MODEL.md: 6.58 EWM-5 vs 7.85 new).

## 4. Observed fact vs modeled estimate (status per input)

| input | observed fact (exists?) | modeled estimate (exists?) | status |
|---|---|---|---|
| minutes / rotation | box minutes 2023-24..2025-26 (`espn/player_games`), reconstructed stint minutes 2 seasons (`espn_pbp/stints`) | EWM-5 and rotation PMF (`src/nba_edge/sim/rotation.py`, `sim/minutes.py`, `features/build.py:194-290`); LightGBM minutes (`research/projection_foundation/nba/minutes.py`) | exists; box minutes are whole minutes |
| starters | post-game flag only (`started`, `pbp_box.starter`) | `p_start` from recent start rate (`features/build.py:248`) | OBSERVED: retrospective only. PREGAME FACT: **missing** |
| injuries / late scratches | official PDF 2025-26 only (`data/history/injury_reports`); live from 2026-10-19 (`pd/availability`) | hand-set `STATUS_P_PLAY` constants (`features/build.py:34`: OUT 0, DOUBTFUL .15, QUESTIONABLE .5, PROBABLE .85) vs measured 0.0 / 0.0 / .596 / .960; fitted `nba/live/participation_calibration.json` | partial (1 season PIT; 0 for 2023-25) |
| participation probability | outcome `participated` (`pd/outcomes`, box) | hurdle P(play) (`pf-nba-participation` rows in pd/forecasts; `research/projection_foundation/nba/live/fit_participation.py`) | modeled only; 82-83% of unlisted players played so "unlisted = active" is an assumption |
| usage / shot volume | FGA/FTA/TOV in box; 927k shot events with zone and coordinates (`espn/shot_events`) | usage proxy FGA+.44FTA+TOV (`nba/features.py`); per-minute FGA rates (`features/build.py`); shot-profile zone rates (`data/research/shot_profile_pit_features_clean.parquet`, unused per inventory.py:89) | partial: true usage% needs on-court possessions (only 2 seasons) |
| opponent-adjusted off/def | none observed | `opponent_adjusted_ratings` (`features/build.py:107`), pf `team.py`; exp_ortg/drtg in pd/game_forecasts | modeled; exists |
| pace | team possessions per game = box formula estimate (`team_games.possessions`; PBP possessions exist for 2 seasons) | `exp_pace` (pd/game_forecasts) | estimate everywhere; PBP count is within +/-5% of the box estimate in 98.9-99.6% of games |
| rebounding / assist opportunity | rebounds, assists (box); missed-shot counts derivable from pbp events | none beyond rates | **missing**: no rebound chances, potential assists, tracking, or defender data (`DEFENDER_ATTRIBUTION_AVAILABLE = False`) |
| 3PA volume | `fg3a` box; shot zones (corner/above-break) 3 seasons | per-minute three share (`features/build.py`) | exists |
| lineup combinations | reconstructed 5-man stints, 2,400 certified games, 2 seasons | none in champion | partial; no 2023-24, no live 2026-27 |
| on/off effects | derivable from certified stints | `OnOffIndex` (`src/nba_edge/research/participation.py`), research arm `pit_lineup` only (dCRPS -0.042 vs `pit_prop`); impact_ppp = 0 | partial; research only, not in champion/live |
| rest / back-to-back / 3-in-4 | schedule dates (box history, `da/context/schedule`) | features `b2b`, `rest_days`, `three_in_four` (`nba/minutes.py:25`, pd context) | exists |
| travel / time zone / altitude | `da` schedule has `arena` name and `neutral_site` only | none | **missing**: no arena coordinates table (inventory.py:67-69 says so) |
| spreads / totals history | Kalshi 2025-26 only | none | missing before 2025-10 |

## 5. Quality defects (file:line)

| # | severity | defect | evidence / pointer |
|---|---|---|---|
| 1 | high | Shot-profile PIT `tip_ts` unit bug: `pd.to_datetime(...).astype("int64") // 10**9` yields kiloseconds under pandas 3.0.6 (pinned, pyproject.toml:14). Stored `tip_ts` is e.g. 1696521 for 2023-10-05T16:00Z (should be 1696521600). `decay_to` divides by 86,400 so the 45-day half-life is effectively ~45,000 days: recency decay is OFF. Prior attempts fell in only 58 of 84,974 consecutive steps (0.07%) | `src/nba_edge/research/shot_profile_features_pit.py:78` (also :109); output `data/research/shot_profile_pit_features*.parquet`. Features unused downstream (inventory.py:89) and `market_table.tip_ts` is in seconds, so a join on `tip_ts` between the two would silently mismatch |
| 2 | high | 2025-26 shot-event FGA disagrees with box: exact per-game match 36.1% vs 95.7% (2023-24) and 97.3% (2024-25); +0.90 FGA/game. Cause: 1,206 `Heave Jump Shot` events, an event type absent from the other two seasons; excluding them restores 95.0% exact. Whether ESPN box or event feed is "right" is UNVERIFIED | `data/history/espn/shot_events_2025-26.parquet`; no handling in `src/nba_edge/shotprofile/` (grep "heave" finds nothing) |
| 3 | high | Lineup quarantine not enforced (section 2): flag column only; unused/weak `quarantine_stints`; stale "absent" health report | `scripts/lineup_certify.py:98,107`; `src/nba_edge/matchup/ingest.py:196`; `src/nba_edge/ops/evidence_health.py:165-172`; `research/projection_foundation/nba/inventory.py:70-73` |
| 4 | medium | Preseason leaks into the league prior: team/player/ratings exclude preseason (`build.py:115,145,197`) but `league_rates(...)` at build.py:298 uses all rows before cutoff. Effect at season start: pace 97.18 vs 96.85, ppp 1.1622 vs 1.1669 (cutoff 2025-10-22); still +0.26 pace at 2026-01-15. Also `rest_days_for` (build.py:417-422) counts preseason and previous-season games: opening-night rest 4-8 days with preseason vs 121-192 without (no b2b flag changes) | `src/nba_edge/features/build.py:298,417` |
| 5 | medium | Preseason rows in research tables: `market_table.parquet` 325 rows (KXNBAGAME, 39 games, 2025-10-10..17), `market_table_scored.parquet` 78 rows; `shot_profile_pit_features.parquet` 5,442 of 85,846 rows (clean file has 80,404) | `data/research/*.parquet`; `src/nba_edge/research/market_table.py` has no season_type filter |
| 6 | medium | Team-id convention split: `shot_events_*` and `shot_profile_pit_features` use ESPN team ids 1-30 (0% overlap with the NBA ids 1610612737.. used by box/pbp/injury tables). `opponent_team_id` cannot be joined to `team_games` without a map | `data/history/espn/shot_events_*.parquet`, `data/research/shot_profile_pit_features.parquet` |
| 7 | medium | Column named `nba_id` holds negated ESPN athlete ids in 100% of rows (box, pbp, identity). Name-keyed joins are ambiguous for same-name players ("Jaylin Williams": ids -4432823 (OKC, 252 rows) and -4431776 (DEN, 2 rows)); `availability/identity.py` correctly refuses ambiguous matches | `data/history/espn/player_games_*`, `src/nba_edge/availability/identity.py:60-80` |
| 8 | medium | `data/identity/players.jsonl`: 175 rows, `team_id` null in all 175; only Kalshi-listed players (934 box players exist). All 175 uuids and espn ids resolve (0 unmapped, 80,574 of ~80,582 prop markets covered) but identity is not a general registry | `data/identity/players.jsonl`, `kalshi_players.json` |
| 9 | medium | Missing ESPN box player (CHI 2025-26, 14 team-games) silently shrinks team minutes by up to 23 and points by 2-9 in `player_games_2025-26`; no data-quality flag. Certification catches it, the box table does not | see section 1 |
| 10 | low | Retrospective name->id join leaks only the id mapping, not status: tiers use the same game's and full-season box (`availability/identity.py:70`); 6,781 of 6,783 eligible status rows resolve identically from prior rows (PARTICIPATION_MINUTES_W2.md) | documented, verified by doc only (UNVERIFIED by me) |
| 11 | low | Team-abbreviation drift is present only in raw `da/context/rosters` (GS, NO, NY, SA, UTAH, WSH = 6 non-canonical, all mapped by `teams.csv` alt_tricodes). `pd` availability/forecasts, injury rows, pbp and Kalshi codes are 100% canonical | no action |
| 12 | low | Date-key / timezone: no mistakes found. `game_date_et` equals ET of `start_time_utc` in 112,427 / 112,427 rows and da schedule rows; injury `game_date` equals snapshot `game_date_et` for 166,628 / 166,628. PIT uses the SCHEDULED tip, not the actual tip (documented) | n/a |
| 13 | low | Hand-set status->P(play) constants disagree with measurement (questionable .5 vs .596, probable .85 vs .96, doubtful .15 vs 0.0; small n=57/25/5) | `src/nba_edge/features/build.py:34` |
| 14 | low | ESPN-sourced `Day-To-Day` collapsed to QUESTIONABLE and unlisted -> ACTIVE/PROJECTED (6,309 of 9,421 pd rows = 67%); a consumer filtering on status alone cannot tell assumption from report. `certainty` and `detail.implicit` distinguish them | `pd/availability` |
| 15 | info | Leakage review of pregame features: `features/build.py` uses `game_date_et < cutoff` (strict) everywhere checked (lines 114,144,196,352,389,418); `started` is only used as lagged history (`build.py:248`); `nba/features.py` keeps `started` and `out_*` in separate oracle columns; PIT arms read only `pit_ok` snapshots and stints dated strictly before the game (`participation.py:aggregate` uses `bisect_left`). I found no final-data leakage into pregame features in the code paths read. Not audited: `nba/backtest.py` end to end | partial review |

## 6. What is missing (ordered by what blocks a better projection)

1. Pregame starters (confirmed or credibly projected) with timestamps and a clear licence. Nothing exists; see section 3.
2. Point-in-time availability before 2025-26 (2023-24, 2024-25). Not recoverable retroactively from the official PDF archive
   unless the PDF host serves older files (UNVERIFIED, nothing was fetched).
3. Prospective lineup/stint capture for 2026-27 (no pipeline, workflow is manual). Without it on/off effects cannot be used live.
4. Rebound/assist opportunity, tracking and defender data (blocked sources: stats.nba.com timeout, cdn.nba.com 403).
5. Travel/time-zone table (30 arena rows would suffice; `arena` already captured in the da schedule).
6. Prop-market pregame quote depth: candles for 14-15% of markets; 152 games in `market_table`.
7. Enforcement: a loader that returns only certified stints (and raises on the raw file), plus a test asserting every consumer uses it.
