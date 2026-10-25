# D5 same-slate roster audit: slate 2026-10-25 (7 games, 14 teams)

Research only. Nothing here activates the joint rotation model (JRM), changes a production projection, a gate, a threshold, a stake or a route.

## What was run

A dry run of the live publisher chain (stages `capture, project, publish`) on a throwaway branch, `PF_NBA_MINUTES_ENGINE=jrm`, against the live feeds (ESPN rosters, official NBA injury report,
league transactions, an independent roster page). The projection was generated 2026-10-25T03:41:11Z, the official report was published 0.2 h before the capture, and the audit and the activation checker ran
on the same archive. The dry run used the **existing** stat models (configuration P1), not the refit challenger R1. The full chain (including the settle and outcome stages) exceeds the 30-minute job
limit on the accumulated data, so the audit used the three stages above. A dry run is not live evidence, and the checker says so.

## Result

**Genuine roster / availability errors: 0.** Availability misaligned with the feed: 0. Ruled-out rows not blocked: none. Blocked rows that are not ruled out: none.

| item | result |
|---|---|
| teams / games | 14 / 7; all 7 on the official report (A4) |
| report freshness (A3) | published 0.2 h before the capture, not from the future |
| player-level designations (A5) | 41 explicit; 2 of 14 teams still "NOT YET SUBMITTED" (26 UNVERIFIED rows, all REVIEW) |
| identity (B1, B2) | 0 of 41 designated players off the ESPN rosters; 0 surname collisions; 0 wrong-team rows |
| availability in the feed | OUT 227, ACTIVE 45, PROBABLE 5, DOUBTFUL 4, QUESTIONABLE 15 rows; misaligned 0 |
| participation | LIKELY_ACTIVE 170, UNCERTAIN 11, CONFIRMED_OUT 29, UNVERIFIED 26, LIKELY_OUT 7 |
| ruled-out players withheld (D3) | 252 rows of ruled-out players, 0 not BLOCK (6 ESPN-only OUT + 1 official DOUBTFUL LIKELY_OUT + 29 CONFIRMED_OUT all BLOCK) |
| uncertain / unverified never PASS (D4) | 259 rows, 0 wrongly PASS |
| eligible players through the quality gate (D5) | 1,190 eligible rows: clean PASS 670 (56%), documented early-season roster uncertainty 165 (14%, Low reliability), other REVIEW 355 (30%, never accepted), BLOCKED 0; not blocked 100% (need 95%), accepted 70% (need 50%) |
| gate counts, all rows | PASS 670 / REVIEW 779 / BLOCK 252 |
| minutes model labels (D1, D2) | 207 players resolved from the report, 207 with report-recalibrated P(play), 207 `E_inj` rows, 0 disagree with their participation source |
| team minutes (F1) | every team: sum of p x E[min] = 241.5, none normalised (worst deviation 1.23% from the rounding of p) |
| pre-tip integrity (E1, E2, D7) | 7 games projected and archived, 0 written at or after the start; 11,623 availability observations archived; newest used 03:41:10Z, forecast generated 03:41:11Z; every archived observation reached its row |
| activation checker | **READY** (A1-A6, B, C, D1-D7, F1, E1, E2 all PASS) |
| SIFT verifier (`verify-nba-activation.ts`) on the feed | ready = true (S1-S10 PASS, including S4 and S10) |

## Projected rotations against the official report

* The one rule added in PR #47 held in this run: an official DOUBTFUL player whose report-recalibrated P(play) falls below the LIKELY_OUT line is withheld (`gate_injury_status = OUT`, reason `withheld:`).
  All 7 LIKELY_OUT rows are BLOCK in every family.
* Every ESPN-only OUT (6 players, not on the official report) is blocked and its minutes are redistributed through the budget constraint; no team sum moved from 241.5.
* Players "from a new team" carry a large share of expected minutes on several teams (LAL 160.8 of 241.5, PHI 111.2, MEM 109.2, LAC 84.1, MIN 79.2). This is the documented early-season roster uncertainty. Their rows
  are REVIEW (Low reliability) by design, not a defect; their forecasts remain the main source of early-season error (see the cohort tables in `DOWNSTREAM_PROSPECTIVE_DIAGNOSIS.md`).
* UTA and IND are REVIEW at team level (new-to-team minutes 60.2 and 26.6 of 241.5, several players named on the injury report but missing from the independent roster page).

## Remaining roster-data defects (all minor, none blocks the checks)

1. **Two teams have not submitted** player-level designations for games not yet started (26 UNVERIFIED rows). Handled correctly (REVIEW). Re-running closer to tip would reduce it; the live ticker already does.
2. **43 players are not listed by the independent roster page** (18 with no corroboration beyond the ESPN roster). All are two-way contracts or recent waivers/signings (e.g. LAL Okereke/Manon/Kaluma, OKC Dix/Barnhizer,
   PHI Love/Rupert). The independent page lags transactions; the audit found no identity error among them.
3. **Four non-two-way players on the league roster page are absent from the projection feed** and could not be verified: Nick Smith Jr. (LAL), Nicolas Batum (LAC), Killian Hayes (SAC), Ron Holland (DET; the
   ESPN roster spells it "Ronald Holland II"). Watch-list: if one of them is active he would take minutes the projection assigns to teammates. Holland is probably a name variant ("Ronald Holland II" on the ESPN roster); for the others the
   audit could not establish why the feed lacks them (not verified from this sandbox, which cannot reach the league sites).
4. **Transaction lag**: Sean Pedulla (signed by SAC on 10-23 after HOU waived him) and Cam Christie (LAC two-way, 10-17) appear in transactions before the independent page lists them (the audit lists them as unconfirmed by that page, not as errors).

## What this audit cannot show

* It is a dry run; it is not live evidence and does not count toward any pre-registered verdict.
* The report was read 0.2 h before the capture, early in the day; the picture closer to tip, when the remaining teams have submitted, is what the three-times-daily snapshots archive.
* The audit used the P1 configuration (JRM minutes with the existing stat models). The stat-side question is answered by the forward validation of R1 (`PREREG_STAT_REFIT.md`), not by this audit.
* It checks identity, availability and integrity, not forecast accuracy.

## Conclusion

D5 passes on the same slate: availability is aligned with the feed, no ruled-out player is projected, rotations conserve the 241.5-minute budget in every game, pre-tip integrity holds, and the readiness checker and
the SIFT verifier agree. The roster-data defects above are documented, bounded and handled by REVIEW; none is a reason to withhold the minutes engine.
