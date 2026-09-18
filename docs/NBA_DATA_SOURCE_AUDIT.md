# NBA data-source audit (as of 2026-09-18)

Method: every candidate source was probed **from a GitHub Actions runner** (`scripts/probe_sources.py`, results in
`docs/probe/probe_results.md`), because production runs there. The development sandbox used for this build has
no outbound access to any sports host, so nothing below is based on local access; local machines (residential
IPs) generally have *more* access than what is listed (notably stats.nba.com and cdn.nba.com).

## Summary table

| Source | Provides | Reachable from Actions | Verdict |
|---|---|---|---|
| Kalshi Trade API v2 (`api.elections.kalshi.com`) | series/events/markets, order books, trades, candlesticks | **yes** (200, ~0.2–1.3 s) | **production** — market truth |
| Kalshi historical API (`external-api.kalshi.com/trade-api/v2/historical`) | archived (settled) markets, candlesticks, trades | not yet probed (job `kalshi_history.yml` written) | production for research once verified |
| ESPN site API (`site.api.espn.com`) | scoreboard by date, game summary/box score with period line scores, injuries, teams, rosters | **yes** (200) | **production** (primary schedule/box/roster source from cloud) |
| ESPN core API (`sports.core.api.espn.com`) | athlete game logs, odds, win probabilities | not probed | research adapter candidate |
| Official NBA injury report PDF (`ak-static.cms.nba.com/referee/injury/...`) | league injury report, published on a 15-minute grid | **yes** (200, 85 KB PDF) | **production** for availability (parsed with pypdf) |
| NBA CDN (`cdn.nba.com/static/json/...`) | official schedule (with game ids + season type), live box scores, PBP | **403 Access Denied** from Actions | local-only fallback; adapter kept |
| NBA Stats (`stats.nba.com/stats/...`) | everything (game logs, rotations, tracking, on/off, lineups) | **timeout** from Actions (cloud IP block, known nba_api issue) | local-only; adapter via `nba_api` for research pulls run from a residential machine |
| official.nba.com pages (injury index, referee assignments) | HTML | 403 | not used |
| pbpstats API (`api.pbpstats.com`) | possessions, on/off, lineups, game logs from PBP | **yes** (200) | research candidate (undocumented public API; use gently) |
| Basketball-Reference | HTML tables | 200 | **do not depend**: terms forbid building a competing datastore; 20 req/min hard limit; HTML scraping brittle |
| Rotowire lineups page | projected starting lineups (HTML) | 200 | research-only fallback for starters; not a production dependency |
| The Odds API | sportsbook lines | 401 without key (free tier 500 req/month with key) | optional adapter later; **not** required, never fabricated |
| Kaggle daily box-score dataset | historical player/team box scores | needs Kaggle credentials | optional bootstrap for research |

## Per-source notes

### Kalshi Trade API (production)
- What: 14,154 series enumerated; 256 NBA-related series; 5,552 NBA markets scanned on 2026-09-18 (off-season).
- Identifiers: series ticker, event ticker, market ticker; `custom_strike.basketball_team` / `basketball_player` UUIDs
  (stable entity ids — captured into `data/history/kalshi/kalshi_team_uuids.json` by the history job).
- Latency: sub-second; rate limit basic tier (client throttles to 5 req/s with backoff on 429).
- Point-in-time: every capture row carries the observation timestamp; `close_time` is NOT the tip time (observed
  3 days after the game); tip time must come from the schedule; pregame labelling happens at evaluation time.
- Fees: `fee_type` ∈ {quadratic, quadratic_with_maker_fees}, `fee_multiplier` = 1 (× base 0.07 taker / 0.0175 maker).
- Settlement: player props settle at the pre-game fair price if the player never enters (NOT void) — the settlement
  engine therefore fails closed on DNP unless the Kalshi result is known.
- Live API retention: last season's game markets are no longer served by `/markets?status=settled`; use the historical API.

### ESPN site API (production from cloud)
- Schedule/scoreboard: `scoreboard?dates=YYYYMMDD` gives events with `season.type` (1 pre, 2 regular, 3 post), UTC
  `date`, competitors with `homeAway`, abbreviations, line scores, status. ESPN event ids are stored as `espn:<id>`.
- Box score: `summary?event=<id>` gives player lines (minutes, made-attempted strings, rebounds, assists, steals,
  blocks, turnovers, points, starter, didNotPlay + reason) and team line scores incl. OT.
- Injuries: `/injuries` is team-level with statuses (Out, Day-To-Day, ...); less precise than the official report.
- Identifiers: ESPN athlete ids; our registry stores them as negative `nba_id` placeholders until an NBA id alias
  exists. Abbreviation quirks (GS, NY, SA, NO, UTAH, WSH) are handled by `alt_tricodes` in `data/identity/teams.csv`.
- Reliability/licensing: undocumented public endpoints; can change without notice; keep parsers defensive and
  archive raw payloads. Latency ~0.1–3 s.
- Historical depth: at least the last several seasons via date iteration (verified on first history run).

### Official NBA injury report PDF (production)
- URL grid: `Injury-Report_YYYY-MM-DD_HH_MMAM.pdf` (2025-26 format) and older `Injury-Report_YYYY-MM-DD_HHAM.pdf`.
- Provides per game: team, player, Current Status (Out/Doubtful/Questionable/Probable/Available), reason.
- Published roughly hourly on game days from ~1 PM ET; final ~90 min before tip. The context job scans the last
  6 hours of 15-minute slots and archives the newest existing report.
- Point-in-time: the report time is in the file name — the archive key. Never use a later report for an earlier
  prediction.

### NBA CDN / stats.nba.com (local only)
- Highest-quality identifiers (10-digit game ids encode season type; NBA person ids). Blocked from cloud IPs.
- Adapters exist (`data/schedule.py`, `data/boxscore.py`, `nba_api` pin) for local research pulls; a self-hosted
  runner or a small proxy would make them production-viable — listed in the handoff as a high-value task.

### pbpstats (research)
- Possession-level totals and on/off data that would improve pace and lineup features. Public API is undocumented;
  respect it (low request rates, cache everything). Not on the production path yet.

## Decisions
1. Production data path from Actions: **Kalshi API + ESPN + official injury PDF**. Everything is archived raw.
2. Research dataset: ESPN box scores for 2023-24 → 2025-26 (`history.yml`), Kalshi historical markets/candles for
   2025-26 (`kalshi_history.yml`). stats.nba.com pulls are a local-machine task.
3. No sportsbook baseline is fabricated. `MARKET_BASELINE` is the Kalshi price itself.
