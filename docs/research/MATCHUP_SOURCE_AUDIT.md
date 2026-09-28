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
| **hoopR-data** | reachable, but **stops at 2022-23** and stores no lineups — and see §3 |

### 2.2 The matchup endpoints, measured

`stats.nba.com` hosts **five of the seven** candidate sources in §1 — matchups, shot defence, shot
charts, synergy play types and rotations. If it is blocked, V2 has no defender data. That is the
whole audit in one sentence.

But the earlier measurement covered three `stats.nba.com` paths, and the matchup arm depends on
different ones. *"The host was blocked for another path"* is inference, not measurement, and this
project has already been burned once by a probe reporting confident negatives it had manufactured
itself. So the matchup paths were measured on their own.

**Run 36438057935**, 2026-09-28, GitHub-hosted runner, 2 rounds ~9 minutes apart
(`source-probe --samples 2 --interval 120`). Reproduce with the same dispatch.

**The control passed both rounds** — `espn/injuries`, 200, 781,293 B, 0.09 s and 0.10 s. Without
that the negatives below would mean nothing.

| endpoint | rounds OK | result | latency |
|---|---|---|---|
| **espn injuries (CONTROL)** | **2/2** | 200, 781,293 B | 0.09–0.10 s |
| espn game summary | **2/2** | 200, ~383 KB | 0.25–0.30 s |
| pbpstats `get-game-stats?Type=Lineup` | **2/2** | 200, 180,014 B | 1.30–1.38 s |
| pbpstats `get-games` | **2/2** | 200, 283,880 B | 2.32–2.81 s |
| pbpstats `get-possessions` | 0/2 | **HTTP 422** (see below) | 0.25–0.36 s |
| **stats.nba `boxscorematchupsv3`** | **0/2** | **ReadTimeout** | 40.08, 40.09 s |
| **stats.nba `leagueseasonmatchups`** | **0/2** | **ReadTimeout** | 40.15, 40.16 s |
| **stats.nba `playerdashptshotdefend`** | **0/2** | **ReadTimeout** | 40.06, 40.08 s |
| **stats.nba `synergyplaytypes`** | **0/2** | **ReadTimeout** | 40.07, 40.12 s |
| stats.nba `gamerotation` | 0/2 | ReadTimeout | 180.04, 180.08 s |
| stats.nba `playbyplayv3`, `boxscoreadvancedv3` | 0/2 | ReadTimeout | ~40 s |
| cdn.nba (3 paths) | 0/2 | **HTTP 403** | 0.04–0.12 s |
| hoopR releases index | 2/2 | 200 but **empty** (see §3) | 0.19 s |

**Every `stats.nba.com` path fails identically, now measured across seven of them** — including all
four the matchup arm actually needs. The defender-attribution source V2 is designed around,
`boxscorematchupsv3`, does not answer from this egress. That is the finding, and it is why the arm
ships neutral.

One caveat stated rather than buried: the four new paths were given a **40-second** budget, while
`gamerotation` got 180 seconds and still returned nothing. Forty seconds distinguishes *blocked*
from *fast* but not from *very slow*. They have since been added to the probe's `SLOW` set so the
next run answers that at 180 s too. The conclusion is not expected to move — the same host held a
connection open for a full three minutes twice in this run — but it is not yet measured at that
budget, and this document does not report an expectation as a finding.

### 2.2b Two corrections this run forced

**pbpstats is not, on this evidence, intermittent.** The earlier audit found the lineup endpoint
returning 200 in one round and timing out in the next, and called it unreliable. In this run
`get-game-stats?Type=Lineup` returned **200 twice**, 180 KB, in 1.3 s, and `get-games` returned
**200 twice**. Two rounds is not a reliability measurement either, so the honest statement is that
pbpstats' reliability remains **uncharacterised in both directions** — the earlier run is not
evidence that it is flaky any more than this one is evidence that it is sound.

**The 422 on `get-possessions` is probably ours, not theirs.** It returned HTTP 422 twice in
0.25–0.36 s — a deterministic, fast rejection, which is the signature of a bad parameter, not of a
block or an outage. The probe asks for `GameId=0022500001`. Recording it as "the endpoint errors"
would blame the source for the probe's own request; it is listed here as **unresolved, our side
suspected**.

### 2.3 The ESPN angle is real, and narrower than I claimed

ESPN is the one host that answers from this egress, and its game summary is comfortably reachable —
200 in both rounds, ~383 KB, 0.25–0.30 s.

**What it carries is still unmeasured.** The run reported top-level keys `boxscore`, `format`,
`gameInfo`, `leaders`, `seasonseries`, `injuries` — and that list is **truncated to six** by the
probe's generic shape reporter, so it is not evidence that a `plays` array is absent. It is evidence
that the probe could not answer the question.

An earlier draft of this document asserted the summary "carries play-by-play with shot coordinates".
That was written from memory, and nothing measured supports or refutes it. The probe now has a
targeted shape check for this endpoint that reports the `plays` count and how many entries carry a
`coordinate`, so the next run answers it directly. Until then: **reachable, contents unconfirmed.**

The asymmetry that motivated looking is still worth naming, and is now conditional: **if** a
reachable source yields shot locations, V2 could learn *how a player shoots* long before it can
learn *who made him shoot that way*. That is why the shot-profile layer is built to stand alone and
`MatchupAdjustment` carries `rim_rate_delta` / `pullup_rate_delta` / `catch_shoot_rate_delta` as
first-class fields even though V1 has nowhere to apply them —
`transform.UNAPPLICABLE_FIELDS` reports them rather than dropping them silently.

### 2.4 hoopR's release index came back empty

The releases API returned **200 with a 2-byte body** — `[]` — in both rounds: zero NBA tags, zero
assets. `SOURCE_AUDIT_GRANULAR.md` recorded this same endpoint serving season-level parquet.

Either the assets moved or the index no longer lists them. Two identical empty responses are enough
to stop treating hoopR releases as an available fallback and not enough to say why, so it is
recorded as **regressed, cause unknown** rather than written off. It was already unusable for
current-season work (it stops at 2022-23 and stores no lineups), so nothing in V2's plan depended on
it — but a source quietly going from "has data" to "returns an empty list" is exactly the kind of
change that is only ever noticed by a probe that keeps running.

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
