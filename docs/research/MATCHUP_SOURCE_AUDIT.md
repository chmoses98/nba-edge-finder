# Matchup data: what V2 needs, and what is actually reachable

**Verdict up front: every field MATCHUP_AWARE_V2 would need to learn a defender effect lives on a
host this project cannot reach from GitHub Actions. The arm therefore ships with its machinery
complete and its effects neutral, and `matchup-shadow` records only what is genuinely knowable —
schedule, rosters, and the absence of everything else, stated as provenance rather than left blank.**

This is the audit the mission asks for: *"what granular data would be needed, which is reachable,
which is not, and what a functioning ingestion would require."* It is deliberately a statement of
absence. The alternative — filling `PlayerDefenderExposure` from position labels and calling it a
matchup — would produce a research arm that looks operational and is measuring nothing.

Companion documents: `SOURCE_AUDIT_GRANULAR.md` (the reachability probe this builds on) and
`MATCHUP_AWARE_V2.md` (what the machinery does with the data once it exists).

---

## 1. What each V2 component needs

The schemas in `src/nba_edge/matchup/schemas.py` are the specification. Each row names the data a
field cannot be populated without.

| V2 component | field | required granularity | candidate source |
|---|---|---|---|
| `PlayerDefenderExposure` | `shares` | **possession-level defender attribution** per offensive player | `stats.nba.com/stats/boxscorematchupsv3`; tracking vendors |
| `PlayerDefenderExposure` | `switch_share` (via `SWITCH_OTHER`) | screen/switch events, or possession-level assignment changes | play-by-play + tracking |
| `DefenderArchetype` | `dfg_pct_at_rim`, `dfg_pct_3pt` | shots faced, by zone, **by defender** | `playerdashptshotdefend` |
| `OffensiveArchetype` | `rim_rate`, `pullup_rate`, `catch_shoot_rate` | shot location + shot type per attempt | `shotchartdetail`; hoopR pbp (coords only) |
| `TeamDefensiveScheme` | `SWITCH_FREQUENCY`, `DROP_COVERAGE_RATE`, … | screen-coverage classification | `synergyplaytypes` (proxy only) |
| `GameMatchupContext` | `expected_*_starters` | confirmed starters before tip | beat reporters; lineup aggregators |
| `LineupStintRecord` | `home_lineup` / `away_lineup` | five-on-five intervals | `gamerotation`; pbpstats lineups |

Two entries deserve emphasis because they are the ones a hurried implementation would fake.

**Defender attribution is not derivable from a box score, a play-by-play stream, or a position
label.** A play-by-play tells you who shot and sometimes who blocked; it does not tell you who was
guarding. The assignment model in `matchup/assignment.py` exists precisely so that positional
evidence cannot silently become a named defender: it returns `POSITION` refs at confidence 0.25 and
is structurally incapable of emitting a `PLAYER` share from positional input.

**Scheme is a classification, not a statistic.** `synergyplaytypes` reports *outcomes* by play type,
from which a coverage rate can be inferred but not observed. Anything ingested from it must be
`Availability.ESTIMATED`, and the `Measure` type makes that distinction unavoidable rather than
optional.

---

## 2. Reachability

### 2.1 What was measured, in `SOURCE_AUDIT_GRANULAR.md`

Run on a GitHub-hosted runner with the project's own HTTP client and a known-good control:

| host | verdict |
|---|---|
| **stats.nba.com** | **blocked** — `gamerotation` held the connection 180.2s and returned nothing |
| **cdn.nba.com** | **blocked** — 403 on every path |
| **pbpstats** | reachable but **intermittent** — the same lineup endpoint returned 200 in 2.6s and then timed out |
| **ESPN** | **reachable** — the control, fetched by `nba context` several times a day |
| **hoopR-data** | reachable, but **stops at 2022-23** and stores no lineups |

### 2.2 What that implies, and what it does not

`stats.nba.com` hosts **five of the seven** candidate sources in §1 — matchups, shot defence, shot
charts, synergy play types and rotations. If it is blocked, V2 has no defender data. That is the
whole audit in one sentence.

But the measurement covered three `stats.nba.com` paths, and the matchup arm depends on different
ones. *"The host was blocked for another path"* is inference, not measurement, and this project has
already been burned once by a probe that reported confident negatives it had manufactured itself.
So `scripts/probe_granular_sources.py` now also probes `boxscorematchupsv3`,
`leagueseasonmatchups`, `playerdashptshotdefend`, `synergyplaytypes`, and the ESPN game summary.

**Those five have not yet been run.** This document will state their results when the `source-probe`
workflow has produced them; until then the expectation is a block, and an expectation is not
recorded here as a finding.

### 2.3 The ESPN angle, which is real but narrow

ESPN is the one host known to answer from this egress, and its game summary carries play-by-play
with shot coordinates. Coordinates give **shot zones**, which populate `OffensiveArchetype` — the
offensive half of a matchup. They give nothing at all about the defender.

That asymmetry is worth naming plainly: a reachable source for shot profile plus no source for
defender attribution means V2 could learn *how a player shoots* long before it can learn *who made
him shoot that way*. The shot-profile layer is therefore built to stand alone, and
`MatchupAdjustment` carries `rim_rate_delta` / `pullup_rate_delta` / `catch_shoot_rate_delta` as
first-class fields even though the current V1 parameter set has nowhere to apply them —
`transform.UNAPPLICABLE_FIELDS` reports them rather than dropping them silently.

---

## 3. What a functioning ingestion would require

Ranked by what it would cost to make real, not by how much anyone would like it.

**1. A residential or proxied egress path to `stats.nba.com`.** This is the only option that
unlocks defender attribution at the source, and it is an infrastructure decision with a cost and a
terms-of-service question, not a coding task. `boxscorematchupsv3` returns per-game player-vs-player
partial possessions — exactly the `DefenderShare` distribution `PlayerDefenderExposure` expects, no
inference layer needed.

**2. A characterised pbpstats client.** pbpstats answers *most* of the time. The audit's standing
position is that a source cannot back an archive of record until its failure modes are measured
rather than guessed, and `source-probe --samples N` exists to do that measurement. pbpstats supplies
lineups and possessions — which supports an **opponent-on-floor** exposure model, weaker than
assignment but honest, and already expressible: `SWITCH_OTHER` and `POSITION` buckets carry the
unidentified mass instead of rounding it into a name.

**3. ESPN shot coordinates for the offensive half.** Reachable today, and the cheapest real progress
available. It populates shot profile and nothing else, and should be labelled as such.

**4. A confirmed-starters source.** `GameMatchupContext.expected_*_starters` is deliberately empty
today: a projected five written into that field would be indistinguishable from a confirmed one six
months later, which is the exact confusion the point-in-time discipline exists to prevent. Any
source here must carry `LineupConfidence` honestly.

Whatever is ingested, the gate does not move: an effect earns influence only after leakage-free,
out-of-sample evidence shows it improves predictions beyond **both V1 and the market**
(`research/matchup_walkforward.residual_value_test`). Reaching the data is the beginning of that
test, not the end of it.

---

## 4. What is being collected in the meantime

`nba matchup-shadow` runs after every context refresh (a worker `SLOW_JOB` and a `conductor.yml`
step) and writes one `matchup/context` row per game within 36 hours of tip.

Verified against the real archive on 2026-09-28: 17 upcoming games, 561 captured roster rows,
17/17 contexts populated with both rosters resolved.

Each row carries the schedule and both rosters as they stood at that instant, and then says, in
`provenance`, exactly what it does **not** have:

```json
"exposures": "none: no defensive-assignment source is reachable; see MATCHUP_SOURCE_AUDIT.md",
"starters":  "none: no confirmed-starter source ingested yet",
"scheme":    "none: no scheme-proxy source ingested yet"
```

The value of this is narrow and real. When a defender source does become reachable, the roster and
availability state *as it was knowable before each game* will already exist, prospectively recorded.
Reconstructing it later from hindsight is the leak the whole arm is built to avoid.

The first run of this capture got its roster join wrong — captured roster rows carry ESPN keys while
the schedule carries NBA team ids, so all 17 contexts were written with empty rotations. It is worth
recording because the failure mode is the one this document is about: a record that looks written
and holds nothing is worse than no record, since only the second one prompts anybody to look.
