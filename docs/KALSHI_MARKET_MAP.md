# Kalshi NBA market map

Discovery run: `2026-09-18T07:06:30Z` · ontology `2026.09.18.3` · 14154 series enumerated on Kalshi · 256 NBA-related series · 5552 NBA markets scanned (all lifecycle statuses, live API).

Off-season caveat: game/player series had 0 live markets on the discovery date (season starts 2026-10-20; last season's markets are archived to the historical API). Market counts for those families come from the summer-league analogues and from `data/history/kalshi` once the historical pull lands.

## Coverage invariant

| support | series | markets (live scan) |
|---|---:|---:|
| MODELABLE | 8 | 6 |
| BUILDABLE | 54 | 2 |
| RESEARCH | 82 | 2856 |
| UNMODELABLE | 112 | 2688 |
| UNRESOLVED | 0 | 0 |

## Families

### MODELABLE

**game_winner** — scope `game`, stat `winner`, period `FULL`. Which team wins the game (incl. OT). YES on a team-specific market.
  - settlement: Settles on final score incl. overtime. Postponed games: Kalshi typically extends or voids; treat as UNRESOLVED until market result field says so.
  - series observed: `KXNBAGAME` (6)

**game_spread** — scope `game`, stat `margin`, period `FULL`. Team wins by more than X points (X from floor_strike / yes_sub_title). Includes alternate spreads (one market per line).
  - settlement: Margin incl. OT. Half-point lines have no push; integer lines: check rules_primary for push handling.
  - series observed: `KXNBASPREAD` (0)

**game_total** — scope `game`, stat `total`, period `FULL`. Combined points over X (incl. OT). Alternate totals are separate markets in the same event.
  - settlement: Total incl. OT.
  - series observed: `KXNBATOTAL` (0)

**team_total** — scope `game`, stat `team_total`, period `FULL`. Single team points over X (incl. OT).
  - settlement: Team points incl. OT.
  - series observed: `KXNBATEAMTOTAL` (0)

**player_points** — scope `player`, stat `pts`, period `FULL`. Player scores X+ points (threshold from floor_strike/custom_strike/yes_sub_title). Ladder markets share an event.
  - settlement: DNP: typically market resolves NO or void per rules_primary; engine fails closed unless rules parsed.
  - series observed: `KXNBAPTS` (0)

**player_rebounds** — scope `player`, stat `reb`, period `FULL`. 
  - series observed: `KXNBAREB` (0)

**player_assists** — scope `player`, stat `ast`, period `FULL`. 
  - series observed: `KXNBAAST` (0)

**player_threes** — scope `player`, stat `fg3m`, period `FULL`. 
  - series observed: `KXNBA3PT` (0)

### BUILDABLE

**period_winner** — scope `game`, stat `winner`, period `PATTERN`. Team leads after a specific quarter/half (period from series ticker: KXNBA1Q, KXNBA1H, KXNBA1HWINNER, ...). Quarter/half markets exclude OT.
  - settlement: Ties: consult rules_primary (may settle NO for both or void).
  - patterns: `^KXNBA(1Q|2Q|3Q|4Q|1H|2H)(WINNER|GAME|ML|MONEYLINE)?$`
  - series observed: `KXNBA1H` (0), `KXNBA1HWINNER` (0), `KXNBA1Q` (0), `KXNBA1QWINNER` (0), `KXNBA2H` (0), `KXNBA2HWINNER` (0), `KXNBA2Q` (0), `KXNBA2QWINNER` (0), `KXNBA3Q` (0), `KXNBA3QWINNER` (0), `KXNBA4Q` (0), `KXNBA4QWINNER` (0)

**period_spread** — scope `game`, stat `margin`, period `PATTERN`. Period margin threshold (KXNBA1HSPREAD, KXNBA3QSPREAD, ...). Period points only; OT excluded.
  - patterns: `^KXNBA(1Q|2Q|3Q|4Q|1H|2H)SPREAD$`
  - series observed: `KXNBA1HSPREAD` (0), `KXNBA1QSPREAD` (0), `KXNBA2HSPREAD` (0), `KXNBA2QSPREAD` (0), `KXNBA3QSPREAD` (0), `KXNBA4QSPREAD` (0)

**period_total** — scope `game`, stat `total`, period `PATTERN`. Period combined points threshold (KXNBA1QTOTAL, KXNBA1HTOTAL, ...). OT excluded.
  - patterns: `^KXNBA(1Q|2Q|3Q|4Q|1H|2H)TOTAL$`
  - series observed: `KXNBA1HTOTAL` (0), `KXNBA1QTOTAL` (0), `KXNBA2HTOTAL` (0), `KXNBA2QTOTAL` (0), `KXNBA3QTOTAL` (0), `KXNBA4QTOTAL` (0)

**period_team_total** — scope `game`, stat `team_total`, period `PATTERN`. Period single-team points threshold (KXNBA1QTEAMTOTAL, KXNBA2HTEAMTOTAL, ...). OT excluded.
  - patterns: `^KXNBA(1Q|2Q|3Q|4Q|1H|2H)TEAMTOTAL$`
  - series observed: `KXNBA1HTEAMTOTAL` (0), `KXNBA1QTEAMTOTAL` (0), `KXNBA2HTEAMTOTAL` (0), `KXNBA2QTEAMTOTAL` (0), `KXNBA3QTEAMTOTAL` (0), `KXNBA4QTEAMTOTAL` (0)

**game_win_margin** — scope `game`, stat `margin_bucket`, period `FULL`. Winning margin falls in a bucket (e.g. 'Boston by 1-5'). Sim margin distribution gives it directly; bucket parsing not wired.
  - series observed: `KXNBAWINMARGIN` (0)

**game_overtime** — scope `game`, stat `overtime`, period `FULL`. Game goes to overtime (yes/no). Sim emits regulation tie probability.
  - series observed: `KXNBAOT` (0), `KXNBAOVERTIME` (0)

**team_bench_points** — scope `game`, stat `bench_pts`, period `FULL`. Team bench points threshold. Needs starter/bench split from lineup model; sim has per-player points.
  - series observed: `KXNBABENCHPTS` (0)

**h2h_player_stat** — scope `player`, stat `h2h`, period `FULL`. Player A records more of a stat than player B (points, threes, PRA...). Needs two-entity joint pricing from the same sim draw.
  - settlement: Ties: consult rules_primary.
  - patterns: `^KXNBAH2H(PTS|REB|AST|3PT|PRA|PR|PA|RA|STL|BLK|TOV|FTM)$`
  - series observed: `KXNBAH2HPRA` (2), `KXNBAH2H3PT` (0), `KXNBAH2HPTS` (0)

**h2h_team_stat** — scope `game`, stat `h2h`, period `FULL`. Team A records more of a stat than team B (threes, bench points). Needs joint pricing of both teams' stat draws.
  - patterns: `^KXNBAH2HTEAM`
  - series observed: `KXNBAH2HBENCHPTS` (0), `KXNBAH2HTEAM3PT` (0)

**parlay_combo** — scope `other`, stat `parlay`, period `FULL`. Pre-packaged combos / multivariate event contracts (2-3 leg moneyline parlays, MVE single/multi game). Price from joint sim once legs are parsed.
  - patterns: `^KXNBAPREPACK`, `^KXMVENBA`
  - series observed: `KXMVENBAMULTIGAMEEXTENDED` (0), `KXMVENBASINGLEGAME` (0), `KXNBAPREPACK2ML` (0), `KXNBAPREPACK3ML` (0)

**player_pra** — scope `player`, stat `pra`, period `FULL`. 
  - series observed: `KXNBAPRA` (0)

**player_steals** — scope `player`, stat `stl`, period `FULL`. 
  - series observed: `KXNBASTL` (0)

**player_blocks** — scope `player`, stat `blk`, period `FULL`. 
  - series observed: `KXNBABLK` (0)

**player_turnovers** — scope `player`, stat `tov`, period `FULL`. 
  - series observed: none yet (ontology entry ahead of the board)

**player_stocks** — scope `player`, stat `stocks`, period `FULL`. Steals + blocks combined threshold (Kalshi titles: 'NBA Player Steals + Blocks').
  - series observed: `KXNBASTOCK` (0), `KXNBASTOCKS` (0)

**player_free_throws** — scope `player`, stat `ftm`, period `FULL`. Free throws made threshold.
  - series observed: `KXNBAFTM` (0)

**player_pr** — scope `player`, stat `pr`, period `FULL`. 
  - series observed: `KXNBAPR` (0)

**player_pa** — scope `player`, stat `pa`, period `FULL`. 
  - series observed: `KXNBAPA` (0)

**player_ra** — scope `player`, stat `ra`, period `FULL`. 
  - series observed: `KXNBARA` (0)

**player_double_double** — scope `player`, stat `double_double`, period `FULL`. 
  - series observed: `KXNBA2D` (0)

**player_triple_double** — scope `player`, stat `triple_double`, period `FULL`. 
  - series observed: `KXNBA3D` (0)

### RESEARCH

**game_points_leader** — scope `game`, stat `pts_leader`, period `FULL`. Which player scores the most points in the game. Needs joint player-points draw with correlations validated; not built.
  - series observed: `KXNBAPTSLEADER` (0)

**game_race_to** — scope `game`, stat `race_to`, period `FULL`. First team to reach X points. Requires play-by-play (possession-level) simulation.
  - series observed: `KXNBARACE` (0)

**first_basket** — scope `player`, stat `first_basket`, period `FULL`. First field goal of the game. Requires opening-tip + first-possession model; not built.
  - series observed: `KXNBAFIRSTBASKET` (0)

**starting_lineup** — scope `player`, stat `starter`, period `FULL`. Player starts a specific game (often the season opener). Lineup model could price these later; treat as research until the lineup model is validated.
  - series observed: `KXNBASTARTERS` (133)

**season_champion** — scope `season`, stat `champion`, period `SEASON`. NBA champion. Needs season simulator (not one-game engine).
  - series observed: `KXNBA` (30)

**champion_special** — scope `season`, stat `champion_derived`, period `SEASON`. Championship-derived propositions: first-time champion, three-peat, which conference the champion comes from. Derived from a season simulator's champion distribution.
  - series observed: `KXNBACONF` (2), `KXNBANEWCHAMPION` (1), `KXNBA3PEAT` (0), `KXNBANEWCHAMP` (0)

**conference_champion** — scope `season`, stat `conference`, period `SEASON`. 
  - series observed: `KXNBAEAST` (15), `KXNBAWEST` (15)

**playoff_round_reach** — scope `season`, stat `round_reach`, period `SEASON`. Team reaches a playoff round (conference finals / Finals qualifiers).
  - patterns: `^KXTEAMSINNBA`
  - series observed: `KXNBAECFQUAL` (15), `KXNBAWCFQUAL` (15), `KXTEAMSINNBAEF` (0), `KXTEAMSINNBAF` (0), `KXTEAMSINNBAWF` (0)

**division_winner** — scope `season`, stat `division`, period `SEASON`. 
  - series observed: `KXNBAATLANTIC` (5), `KXNBACENTRAL` (5), `KXNBANORTHWEST` (5), `KXNBAPACIFIC` (5), `KXNBASOUTHEAST` (5), `KXNBASOUTHWEST` (5)

**season_wins** — scope `season`, stat `wins`, period `SEASON`. 
  - series observed: `KXNBAWINS` (312)

**season_record** — scope `season`, stat `record`, period `SEASON`. League-wide record propositions: best/worst regular-season record, any team reaching X wins, single-team win record.
  - series observed: `KXNBARECORD` (60), `KXNBAMOSTWINS` (4), `KXNBAWINRECORD` (0)

**playoffs_qualify** — scope `season`, stat `playoffs`, period `SEASON`. Make the playoffs / play-in, advance from play-in.
  - series observed: `KXNBAPLAYIN` (30), `KXNBAPLAYOFF` (30), `KXNBAPIADVANCE` (0)

**playoff_seed** — scope `season`, stat `seed`, period `SEASON`. Final regular-season seeding (1 seed by conference, exact seed) and resulting first-round matchup.
  - series observed: `KXNBAEAST1SEED` (15), `KXNBAWEST1SEED` (15), `KXNBAMATCHUP` (0), `KXNBASEED` (0)

**nba_cup** — scope `season`, stat `cup`, period `SEASON`. In-season tournament (Emirates NBA Cup) champion / knockout qualifiers. Needs group-stage tiebreak model.
  - patterns: `^KXNBACUP(?!MVP)`
  - series observed: `KXNBACUPQUAL` (60), `KXNBACUP` (30)

**series_winner** — scope `season`, stat `series`, period `SEASON`. Playoff series winner / series length / exact series score / sweep / game 7.
  - series observed: `KXNBAFINALSEXACT` (0), `KXNBAGAME7` (0), `KXNBAGAMES` (0), `KXNBASERIES` (0), `KXNBASERIESGAMES` (0), `KXNBASERIESSCORE` (0), `KXNBASWEEP` (0)

**series_props** — scope `season`, stat `series_prop`, period `SEASON`. Playoff series propositions: series spreads/totals, road wins, comebacks (3-0), clinch at home, overtime in series, blowouts, undefeated runs, upsets per round, team playoff win/loss counts.
  - patterns: `^KXNBASERIES`
  - series observed: `KXNBA30COMEBACK` (0), `KXNBAFINBLOWOUT` (0), `KXNBAHOMECLINCH` (0), `KXNBAPLAYOFFWINS` (0), `KXNBAPOLOSE` (0), `KXNBASERIESCOMEBACK` (0), `KXNBASERIESGCOMEBACK` (0), `KXNBASERIESOT` (0), `KXNBASERIESPTSSPREAD` (0), `KXNBASERIESROADWIN` (0), `KXNBASERIESROADWINS` (0), `KXNBASERIESSPREAD` (0), `KXNBASERIESTOTALPTS` (0), `KXNBAUNBEATEN` (0), `KXNBAUPSET` (0)

**series_player_stat** — scope `player`, stat `series_player`, period `SEASON`. Player stat aggregated over a playoff series / playoffs (series points, series stat leaders, playoff points, playoff triple-doubles).
  - series observed: `KXNBAPLAYOFF3D` (0), `KXNBAPLAYOFFPTS` (0), `KXNBASERIES3PMLEADER` (0), `KXNBASERIESASTLEADER` (0), `KXNBASERIESPTS` (0), `KXNBASERIESPTSLEADER` (0), `KXNBASERIESREBLEADER` (0)

**season_stat_leader** — scope `player`, stat `season_leader`, period `SEASON`. Regular-season per-game stat leader (PPG, RPG, APG, BPG, SPG, 3PG).
  - patterns: `^KXLEADERNBA`
  - series observed: `KXLEADERNBA3PT` (0), `KXLEADERNBAAST` (0), `KXLEADERNBABLK` (0), `KXLEADERNBAPTS` (0), `KXLEADERNBAREB` (0), `KXLEADERNBASTL` (0)

**season_player_streak** — scope `player`, stat `all_games`, period `SEASON`. Player hits a threshold in every game of a span (points / threes in every game).
  - series observed: `KXNBA3PTALLGAMES` (0), `KXNBAPTSALLGAMES` (0)

**season_specials** — scope `season`, stat `special`, period `SEASON`. Season-long 'any player/game records X' propositions (e.g. any player 70+ points this season).
  - series observed: `KXNBAGAMESPECIALS` (27), `KXNBAPLAYERSPECIALS` (0)

**summer_league_game** — scope `game`, stat `winner`, period `FULL`. Summer League game / half winner. Not NBA regular season; excluded from training.
  - series observed: `KXNBASUMMER1HWINNER` (108), `KXNBASUMMERGAME` (98)

**summer_league_spread** — scope `game`, stat `margin`, period `FULL`. Summer League full-game / half spread. Not NBA regular season; excluded from training.
  - series observed: `KXNBASUMMERSPREAD` (619), `KXNBASUMMER1HSPREAD` (273)

**summer_league_total** — scope `game`, stat `total`, period `FULL`. Summer League full-game / half total. Not NBA regular season; excluded from training.
  - series observed: `KXNBASUMMERTOTAL` (595), `KXNBASUMMER1HTOTAL` (294)

**summer_league_player** — scope `player`, stat `pts`, period `FULL`. Summer League player props. Not NBA regular season; excluded from training.
  - series observed: `KXNBASUMMERPTS` (0)

**summer_league_season** — scope `season`, stat `champion`, period `SEASON`. Summer League champion and any other summer-league series not listed explicitly. Not NBA regular season; excluded from training.
  - patterns: `^KXNBASUMMER(?!MVP)`
  - series observed: `KXNBASUMMER` (30)

### UNMODELABLE

**awards** — scope `season`, stat `award`, period `SEASON`. Voting outcomes (MVP, DPOY, ROY, MIP, 6MOY, COY, Finals/conference-finals/Cup/Summer/All-Star MVP, Clutch POY, Sportsmanship). Not a basketball-simulation quantity.
  - series observed: `KXNBACUPMVP` (75), `KXNBAFINMVP` (75), `KXNBASIXTH` (74), `KXNBAMVP` (53), `KXNBAEFINMVP` (50), `KXNBAWFINMVP` (50), `KXNBADPOY` (48), `KXNBAMIMP` (45), `KXNBASUMMERMVP` (33), `KXNBACOY` (30), `KXNBAROY` (17), `KXNBAMVPDPOY` (1), `KXNBAALLSTARMVP` (0), `KXNBACLUTCH` (0), `KXNBAFINALSMVP` (0), `KXNBASPORTSMANSHIP` (0), `KXNBATOP5ROTY` (0)

**all_nba_selections** — scope `season`, stat `selection`, period `SEASON`. All-NBA / All-Defensive / All-Rookie team selections and All-Star selections (voting).
  - patterns: `^KXNBA(1ST|2ND|3RD)TEAM(DEF)?$`, `^KXNBAROOKIE(1ST|2ND)TEAM$`
  - series observed: `KXNBAALLSTARS` (60), `KXNBA2NDTEAM` (55), `KXNBA3RDTEAM` (55), `KXNBA2NDTEAMDEF` (51), `KXNBA1STTEAMDEF` (41), `KXNBAROOKIE2NDTEAM` (40), `KXNBA1STTEAM` (39), `KXNBAROOKIE1STTEAM` (30)

**all_star_events** — scope `other`, stat `exhibition`, period `SEASON`. All-Star weekend exhibitions: All-Star game, Rising Stars, Shooting Stars, dunk / 3-point / skills contests.
  - patterns: `^KXNBAALLSTAR`
  - series observed: `KXNBA3PTCONTEST` (0), `KXNBAALLSTAR` (0), `KXNBAALLSTARGAME` (0), `KXNBARISINGSTARS` (0), `KXNBASHOOTINGSTARS` (0), `KXNBASLAMDUNK` (0)

**draft** — scope `other`, stat `draft`, period `SEASON`. Draft position, lottery, draft-night trades and draft category propositions.
  - patterns: `^KXNBADRAFT`, `^KXNBALOTTERY`
  - series observed: `KXNBADRAFTPICK` (15), `KXNBADRAFT2` (12), `KXFIRSTPICKNBA` (0), `KXNBADRAFT1` (0), `KXNBADRAFT10` (0), `KXNBADRAFT3` (0), `KXNBADRAFT4` (0), `KXNBADRAFT5` (0), `KXNBADRAFT6` (0), `KXNBADRAFT7` (0), `KXNBADRAFT8` (0), `KXNBADRAFT9` (0), `KXNBADRAFTCAT` (0), `KXNBADRAFTCOMP` (0), `KXNBADRAFTCONF` (0), `KXNBADRAFTINT` (0), `KXNBADRAFTMATCHUP` (0), `KXNBADRAFTOU` (0), `KXNBADRAFTTEAM` (0), `KXNBADRAFTTOP` (0), `KXNBADRAFTTOP10` (0), `KXNBADRAFTTOP15` (0), `KXNBADRAFTTOP20` (0), `KXNBADRAFTTOP25` (0), `KXNBADRAFTTOP30` (0), `KXNBADRAFTTOP5` (0), `KXNBADRAFTTRADE` (0), `KXNBALOTTERY` (0), `KXNBALOTTERYODDS` (0), `KXNBAPICKTRADE` (0), `KXNBATOP3` (0), `KXNBATOPPICK` (0), `KXTOP3NBADRAFT` (0)

**transactions** — scope `other`, stat `transaction`, period `SEASON`. Player movement and contracts: trades, next team, contract size, retirement, return, playing together, brand deals, player options, team announcements.
  - patterns: `^KXNBANEXTTEAM`, `^KXNEXTTEAMNBA`
  - series observed: `KXNEXTTEAMNBA` (853), `KXNBANEXTTEAM` (280), `KXNBATRADE` (53), `KXNBARETIRE` (29), `KXNBATEAMANNOUNCE` (24), `KXNBANEXTCONTRACT` (19), `KXNBANEXTTEAMOUTLET` (10), `KXNBANEXTTEAMCONF` (3), `KXNBACOMPETE` (1), `KXNBAPLAYERDEAL` (1), `KXNBAPLAYTOGETHER` (0), `KXNBARETURN` (0), `KXPLAYEROPTIONNBA` (0)

**coaching** — scope `other`, stat `coach`, period `SEASON`. Coach firings / hirings.
  - patterns: `^KXCOACHOUTNBA`, `^KXNEXTCOACHOUTNBA`, `^KXNEXTNBACOACH`
  - series observed: `KXNEXTNBACOACH` (14), `KXCOACHOUTNBADATE` (9), `KXCOACHOUTNBA` (0), `KXNBACOACHOUT` (0), `KXNEXTCOACHOUTNBA` (0)

**franchise_business** — scope `other`, stat `business`, period `SEASON`. League/franchise business: expansion cities, relocation, team/stake sales, governors, new franchises, conference realignment, rule changes, arena completion.
  - series observed: `KXNBARELOCATION` (11), `KXNBANEXTGOVERNOR` (6), `KXCITYNBAEXPAND` (2), `KXNBAJOINCONF` (1), `KXNBARULE` (1), `KXNBASEATTLE` (1), `KXNBASTADIUM` (1), `KXNBASTAKESALE` (1), `KXNBATEAM` (1), `KXNBATEAMSALE` (1), `KXNBALASVEGAS` (0)

**schedule_announcement** — scope `other`, stat `schedule`, period `SEASON`. Schedule-release propositions (season-opening opponent, Christmas Day opponent). Determined by the league office, not on-court play.
  - series observed: `KXNBAXMASOPPONENT` (150), `KXNBAFIRSTOPPONENT` (145)

**non_basketball_or_offcourt** — scope `other`, stat `None`, period `SEASON`. NBA-tagged series that are not basketball outcomes: music releases, video-game covers, politics, broadcast mentions, viewership, ticket prices, apologies, ESPYs, White House visits, Hall of Fame, celebrity events, attendance.
  - patterns: `^KXNBAFINALSVIEWER`, `^KXNBACELEBRITY`
  - series observed: `KXNBAMENTION` (52), `KXNBAHALLOFFAME` (28), `KXNBAFINALSPRICE` (21), `KXNBA2KCOVER` (20), `KXNBAWHATTEND` (1), `KXALBUMRELEASEDATENBAYOUNGBOY` (0), `KXESPYNBA` (0), `KXKXSPOTIFYALBUMRELEASEDATESC` (0), `KXMEDIACOVERNBA2K` (0), `KXNBAAPOLOGY` (0), `KXNBAATTEND` (0), `KXNBACELEBRITY3PT` (0), `KXNBACELEBRITYGAME` (0), `KXNBAFINALSMENTION` (0), `KXNBAFINALSVIEWER` (0), `KXNBAFINALSVIEWERGAME7` (0), `KXTRUMPNBAFINALS` (0)


## Ticker anatomy (observed)

- Game markets: `KXNBAGAME-26OCT20OKCSAS-SAS` = series, `YYMMMDD` + AWAY + HOME, then the YES team.
- Spreads: `KXNBASPREAD-<event>-DEN16` with `strike_type=greater`, `floor_strike='15.5'` (YES iff team margin > 15.5).
- Totals: `KXNBATOTAL-<event>-200` with `floor_strike='199.5'` (YES iff total > 199.5).
- Season wins: `KXNBAWINS-27UTA-60` with `strike_type=greater_or_equal`, `floor_strike='60'`.
- Entities: `custom_strike.basketball_team` / `basketball_player` carry stable Kalshi UUIDs (mapped in `data/history/kalshi/kalshi_team_uuids.json`).
- `close_time` is not the tip time (observed 3 days after the game); the schedule is authoritative for pregame labelling.
