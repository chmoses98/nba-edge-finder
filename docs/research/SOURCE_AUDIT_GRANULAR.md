# Lineup/stint data sources: what is actually reachable (Phase 7)

**Verdict up front: the single best stint source is unusable from GitHub Actions, and no reliable
current-season lineup pipeline exists yet. The Phase 8 canonical stint dataset is therefore NOT
built in this wave** — the brief's instruction is *"do not assume a source is suitable merely
because it exists"*, and the evidence below says two of the three candidates are not.

---

## 1. A methodological note, because the first run was wrong

The first version of this probe sent a **spoofed Chrome User-Agent** via `urllib` and reported
403/timeout for *every* host — including ESPN, which `nba context` fetches successfully from this
exact workflow environment several times a day.

The control failing was the tell. A spoofed browser UA arriving from a datacenter IP is *more*
suspicious to bot detection than an honest one, so the probe was manufacturing the blocks it then
reported. **Probing with anything other than the client we actually ingest with measures the probe,
not the source.**

The results below come from a rewritten probe that uses the project's own `httpx` client and its
own `PLAIN_HEADERS_OK` / `NBA_HEADERS`, run on a GitHub-hosted runner, with a known-good control
that passes. Any future probe must keep a passing control or its negative results mean nothing.

## 2. Reachability from a GitHub-hosted runner

Two runs, the second giving the previously-timing-out endpoints a **180-second** budget so that
*slow* could be told apart from *blocked* — a distinction a 40-second timeout cannot make, and one
that decides whether a source is usable from a batch job.

| source | endpoint | run 1 (40s) | run 2 (180s) | verdict |
|---|---|---|---|---|
| **ESPN** *(CONTROL)* | `/nba/injuries` | 200, 836 KB, 0.2s | 200, 0.35s | ✅ probe is sound |
| **stats.nba.com** | `gamerotation` | timeout | **timeout at 180.2s** | ❌ **blocked** |
| stats.nba.com | `playbyplayv3`, `boxscoreadvancedv3` | timeout | timeout | ❌ blocked |
| **cdn.nba.com** | `playbyplay`, `boxscore`, `schedule` | 403 | 403 | ❌ blocked |
| **pbpstats** | `get-games` | timeout | **200**, 284 KB, 5.2s | ⚠️ reachable |
| **pbpstats** | `get-game-stats?Type=Lineup` | **200**, 180 KB, 2.6s | **timeout at 40s** | ⚠️ **intermittent** |
| **pbpstats** | `get-possessions` | timeout | **502** after 91.3s | ⚠️ erroring |
| **hoopR-data** | GitHub repo | 200 | 200 | ⚠️ stale, see §3 |

Two findings decide everything below.

**`stats.nba.com` is blocked, not slow.** `gamerotation` held the connection open for a full 180
seconds and returned nothing. The ideal stint source is simply unavailable from Azure egress.

**`pbpstats` is reachable but unreliable.** The *same* lineup endpoint returned 200 in 2.6s on one
run and timed out on the next; `get-games` did the reverse; `get-possessions` returned a 502 after
91 seconds. Intermittency of this kind is precisely what the brief means by *"do not assume a source
is suitable merely because it exists"*. A source that answers most of the time is fine for a
research query and is **not** fine, unqualified, as the backing store for an archive of record --
not before its failure modes are characterised and a retry/backoff policy is written against them.

**`stats.nba.com/stats/gamerotation` is the ideal source** — it returns exact stint start/end per
player per game, which is precisely the Phase 8 row shape, with no lineup reconstruction needed at
all. It times out from Azure egress. This is the well-known cloud-IP block, and it is fatal to any
design that depends on it from Actions.

## 3. hoopR-data — the right *shape*, the wrong *freshness*

`sportsdataverse/hoopR-data` mirrors NBA data into a **GitHub repository**, which is exactly the
property a source of record wants and a live JSON API lacks: reachable from a runner, effectively
unrate-limited, versioned, and byte-for-byte reproducible.

| dataset | coverage | format |
|---|---|---|
| `nba_stats/pbp/{csv,parquet}` | **1996-97 → 2022-23** (27 seasons) | NBA Stats play-by-play |
| `nba/pbp/{csv,parquet}` | 2002 → 2023 (22 seasons) | ESPN-derived play-by-play |
| `nba_stats/json/pbp` | 35,738 per-game JSON files | raw |

Two problems:

1. **It stops at 2022-23** — roughly three seasons stale. It cannot support current-season work,
   which is the entire point of building a prospective evidence base for 2026-27.
2. **It does not store lineups.** `R/nba_stats_02_scrape_pbp_to_lineup.R` *derives* them at
   runtime — and derives them by scraping `stats.nba.com/stats/playbyplayv2`, which is the host we
   just established is unreachable from Actions.

That script also shows the reconstruction hazard the brief asks about under "reconstructed lineup
accuracy": it initialises each period's lineup to `NA` and fills it in from substitution events, so
**a player who is on court for a whole period without appearing in any event is never identified**.
Lineup reconstruction from play-by-play alone is not sound without a period-start source.

## 4. What would have to be true for Phase 8 to proceed

A canonical stint dataset needs all three, and today we have at most one:

1. **Period-start lineups**, not just substitutions — otherwise reconstruction silently drops
   players (§3). `gamerotation` supplies this directly and is unreachable.
2. **Current-season latency**, since the object is prospective evidence for 2026-27. hoopR is three
   seasons stale; pbpstats is live but only one of its endpoints answered.
3. **Stable identifiers** mapping to this project's existing player/game identity, which is
   unverified for pbpstats because the bulk endpoints did not return.

## 5. Recommendation

**Do not build the stint dataset yet.** Do this first, in order:

1. **Characterise pbpstats' intermittency before depending on it.** Sample one endpoint on a fixed
   game repeatedly over a day and record the success rate, the latency distribution and the error
   mix (timeout vs 502). Write the retry/backoff policy against *that*, not against a guess. If the
   success rate cannot be driven near 1.0 with bounded retries, the source is not suitable and the
   honest answer is to say so.
2. **Then validate one game end-to-end** against a known box score: five players per side at every
   instant, lineup minutes reconciling to game minutes, scores reconciling, overtime handled.
3. **Only then** define the canonical schema and ingest — with bad games **quarantined explicitly**
   rather than silently included, as the brief requires.

Note that ingestion would be a *backfill* job, not part of the capture worker's cadence path. An
intermittent source must never be able to stall the thing that captures markets.

Phase 9 stands regardless: this wave produces **coverage counts, not an impact model**. The daily
dashboard already reports `stint_data.state = "absent"` with the reason, so the gap is visible every
day rather than forgotten.
