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

| source | endpoint | result | usable? |
|---|---|---|---|
| **ESPN** *(CONTROL)* | `/nba/injuries` | **200**, 836 KB, 0.2s | ✅ — proves the probe is sound |
| **pbpstats** | `get-game-stats?Type=Lineup` | **200**, 180 KB, 2.6s | ✅ lineup-level data per game |
| pbpstats | `get-games`, `get-possessions` | timeout at 40s | ⏳ see §4 |
| **stats.nba.com** | `gamerotation`, `playbyplayv3`, `boxscoreadvancedv3` | **timeout at 40s** | ❌ |
| **cdn.nba.com** | `playbyplay`, `boxscore`, `schedule` | **403** (with honest UA) | ❌ |
| **hoopR-data** | GitHub repo | **200** | ⚠️ stale, see §3 |

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

1. Re-run the probe with a generous timeout to settle whether pbpstats' bulk endpoints are *slow*
   or *blocked*. A slow source is perfectly usable from a batch job; a blocked one is not, and a
   40-second timeout cannot tell the two apart.
2. If pbpstats is merely slow, validate one game end-to-end against a known box score: five players
   per side at every instant, lineup minutes reconciling to game minutes, scores reconciling.
3. Only then define the canonical schema and ingest — with bad games **quarantined explicitly**
   rather than silently included, as the brief requires.

Phase 9 stands regardless: this wave produces **coverage counts, not an impact model**. The daily
dashboard already reports `stint_data.state = "absent"` with the reason, so the gap is visible every
day rather than forgotten.
