# Kalshi NBA discovery summary

- discovered_at: `2026-10-28T19:55:55Z`  ontology: `2026.09.18.3`  requests: 617
- series enumerated: 15456; NBA series: 300; markets scanned: 14385

## Support states (coverage invariant)

| support | markets |
|---|---:|
| MODELABLE | 3207 |
| BUILDABLE | 3429 |
| RESEARCH | 1907 |
| UNMODELABLE | 1631 |
| UNRESOLVED | 4211 |

## NBA series

| series | family | support | fee | unopened | open | closed | settled | strike_types | parse |
|---|---|---|---|---:|---:|---:|---:|---|---|
| KXALBUMRELEASEDATENBAYOUNGBOY | non_basketball_or_offcourt | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXCITYNBAEXPAND | franchise_business | UNMODELABLE | quadratic/1 | 0 | 3 | 0 | 0 | custom | {'medium': 3} |
| KXCOACHOUTNBA | coaching | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXCOACHOUTNBADATE | coaching | UNMODELABLE | quadratic/1 | 0 | 6 | 0 | 0 | custom | {'low': 6} |
| KXESPYNBA | non_basketball_or_offcourt | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXFIRSTPICKNBA | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXKXSPOTIFYALBUMRELEASEDATESC | non_basketball_or_offcourt | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXLEADERNBA3PT | season_stat_leader | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXLEADERNBAAST | season_stat_leader | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXLEADERNBABLK | season_stat_leader | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXLEADERNBAPTS | season_stat_leader | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXLEADERNBAREB | season_stat_leader | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXLEADERNBASTL | season_stat_leader | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXMEDIACOVERNBA2K | non_basketball_or_offcourt | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXMVENBAMULTIGAMEEXTENDED | parlay_combo | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXMVENBASINGLEGAME | parlay_combo | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA | season_champion | RESEARCH | quadratic_with_maker_fees/1 | 0 | 30 | 0 | 0 | structured | {'low': 30} |
| KXNBA1H | period_winner | BUILDABLE | quadratic/1 | 0 | 42 | 0 | 0 | structured | {'high': 42} |
| KXNBA1HSPREAD | period_spread | BUILDABLE | quadratic/1 | 0 | 228 | 0 | 0 | greater | {'high': 228} |
| KXNBA1HTEAMTOTAL | period_team_total | BUILDABLE | quadratic/1 | 0 | 264 | 0 | 0 | greater | {'high': 264} |
| KXNBA1HTOTAL | period_total | BUILDABLE | quadratic/1 | 0 | 228 | 0 | 0 | greater | {'high': 228} |
| KXNBA1HWINNER | period_winner | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA1Q | period_winner | BUILDABLE | quadratic/1 | 0 | 42 | 0 | 0 | structured | {'high': 42} |
| KXNBA1QSPREAD | period_spread | BUILDABLE | quadratic/1 | 0 | 156 | 0 | 0 | greater | {'high': 156} |
| KXNBA1QTEAMTOTAL | period_team_total | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA1QTOTAL | period_total | BUILDABLE | quadratic/1 | 0 | 156 | 0 | 0 | greater | {'high': 156} |
| KXNBA1QWINNER | period_winner | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA1STTEAM | all_nba_selections | UNMODELABLE | quadratic/1 | 0 | 39 | 0 | 0 | structured | {'low': 39} |
| KXNBA1STTEAMDEF | all_nba_selections | UNMODELABLE | quadratic/1 | 0 | 41 | 0 | 0 | structured | {'low': 41} |
| KXNBA2D | player_double_double | BUILDABLE | quadratic/1 | 0 | 46 | 0 | 0 | greater | {'high': 46} |
| KXNBA2H | period_winner | BUILDABLE | quadratic/1 | 0 | 42 | 0 | 0 | structured | {'high': 42} |
| KXNBA2HSPREAD | period_spread | BUILDABLE | quadratic/1 | 0 | 228 | 0 | 0 | greater | {'high': 228} |
| KXNBA2HTEAMTOTAL | period_team_total | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA2HTOTAL | period_total | BUILDABLE | quadratic/1 | 0 | 228 | 0 | 0 | greater | {'high': 228} |
| KXNBA2HWINNER | period_winner | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA2KCOVER | non_basketball_or_offcourt | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA2NDTEAM | all_nba_selections | UNMODELABLE | quadratic/1 | 0 | 55 | 0 | 0 | structured | {'low': 55} |
| KXNBA2NDTEAMDEF | all_nba_selections | UNMODELABLE | quadratic/1 | 0 | 51 | 0 | 0 | structured | {'low': 51} |
| KXNBA2Q | period_winner | BUILDABLE | quadratic/1 | 0 | 42 | 0 | 0 | structured | {'high': 42} |
| KXNBA2QSPREAD | period_spread | BUILDABLE | quadratic/1 | 0 | 156 | 0 | 0 | greater | {'high': 156} |
| KXNBA2QTEAMTOTAL | period_team_total | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA2QTOTAL | period_total | BUILDABLE | quadratic/1 | 0 | 156 | 0 | 0 | greater | {'high': 156} |
| KXNBA2QWINNER | period_winner | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA30COMEBACK | series_props | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA3D | player_triple_double | BUILDABLE | quadratic/1 | 0 | 14 | 0 | 0 | greater | {'high': 14} |
| KXNBA3PEAT | champion_special | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA3PT | player_threes | MODELABLE | quadratic/1 | 4 | 559 | 0 | 0 | greater | {'high': 563} |
| KXNBA3PTALLGAMES | season_player_streak | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA3PTCONTEST | all_star_events | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA3PTPROT | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 563 | 0 | 0 | greater | {'high': 563} |
| KXNBA3Q | period_winner | BUILDABLE | quadratic/1 | 0 | 42 | 0 | 0 | structured | {'high': 42} |
| KXNBA3QSPREAD | period_spread | BUILDABLE | quadratic/1 | 0 | 156 | 0 | 0 | greater | {'high': 156} |
| KXNBA3QTEAMTOTAL | period_team_total | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA3QTOTAL | period_total | BUILDABLE | quadratic/1 | 0 | 156 | 0 | 0 | greater | {'high': 156} |
| KXNBA3QWINNER | period_winner | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA3RDTEAM | all_nba_selections | UNMODELABLE | quadratic/1 | 0 | 55 | 0 | 0 | structured | {'low': 55} |
| KXNBA4Q | period_winner | BUILDABLE | quadratic/1 | 0 | 42 | 0 | 0 | structured | {'high': 42} |
| KXNBA4QSPREAD | period_spread | BUILDABLE | quadratic/1 | 0 | 156 | 0 | 0 | greater | {'high': 156} |
| KXNBA4QTEAMTOTAL | period_team_total | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA4QTOTAL | period_total | BUILDABLE | quadratic/1 | 0 | 156 | 0 | 0 | greater | {'high': 156} |
| KXNBA4QWINNER | period_winner | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAALLSTAR | all_star_events | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAALLSTARGAME | all_star_events | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAALLSTARMVP | awards | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAALLSTARS | all_nba_selections | UNMODELABLE | quadratic/1 | 0 | 60 | 0 | 0 | structured | {'low': 60} |
| KXNBAAPOLOGY | non_basketball_or_offcourt | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAASSTARTERS | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAAST | player_assists | MODELABLE | quadratic/1 | 0 | 399 | 0 | 0 | greater | {'high': 399} |
| KXNBAASTPROT | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 399 | 0 | 0 | greater | {'high': 399} |
| KXNBAATLANTIC | division_winner | RESEARCH | quadratic/1 | 0 | 5 | 0 | 0 | structured | {'low': 5} |
| KXNBAATTEND | non_basketball_or_offcourt | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAAWARDFIN | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 303 | 0 | 0 | custom,structured | {'low': 303} |
| KXNBABENCHPTS | team_bench_points | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBABLK | player_blocks | BUILDABLE | quadratic/1 | 0 | 94 | 0 | 0 | greater | {'high': 94} |
| KXNBACELEBRITY3PT | non_basketball_or_offcourt | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBACELEBRITYGAME | non_basketball_or_offcourt | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBACENTRAL | division_winner | RESEARCH | quadratic/1 | 0 | 5 | 0 | 0 | structured | {'low': 5} |
| KXNBACITYEXPAND | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 7 | 0 | 0 | custom | {'medium': 7} |
| KXNBACLUTCH | awards | UNMODELABLE | quadratic/1 | 0 | 54 | 0 | 0 | structured | {'low': 54} |
| KXNBACOACHOUT | coaching | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBACOMPETE | transactions | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBACONF | champion_special | RESEARCH | quadratic/1 | 0 | 2 | 0 | 0 | structured | {'low': 2} |
| KXNBACOTM | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 30 | 0 | 0 | custom | {'low': 30} |
| KXNBACOY | awards | UNMODELABLE | quadratic_with_maker_fees/1 | 0 | 30 | 0 | 0 | custom | {'low': 30} |
| KXNBACUP | nba_cup | RESEARCH | quadratic/1 | 0 | 30 | 0 | 0 | structured | {'low': 30} |
| KXNBACUP1STTEAM | nba_cup | RESEARCH | quadratic/1 | 0 | 85 | 0 | 0 | structured | {'low': 85} |
| KXNBACUPGROUP | nba_cup | RESEARCH | quadratic/1 | 0 | 30 | 0 | 0 | structured | {'low': 30} |
| KXNBACUPGROUPWIN | nba_cup | RESEARCH | quadratic/1 | 0 | 6 | 0 | 0 | custom | {'low': 6} |
| KXNBACUPMVP | awards | UNMODELABLE | quadratic/1 | 0 | 75 | 0 | 0 | structured | {'low': 75} |
| KXNBACUPQUAL | nba_cup | RESEARCH | quadratic/1 | 0 | 60 | 0 | 0 | structured | {'low': 60} |
| KXNBADPOTM | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 120 | 0 | 0 | structured | {'low': 120} |
| KXNBADPOY | awards | UNMODELABLE | quadratic/1 | 0 | 48 | 0 | 0 | structured,custom | {'low': 48} |
| KXNBADRAFT1 | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFT10 | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFT2 | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFT3 | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFT4 | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFT5 | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFT6 | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFT7 | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFT8 | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFT9 | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFTCAT | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFTCOMP | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFTCONF | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFTINT | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFTMATCHUP | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFTOU | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFTPICK | draft | UNMODELABLE | quadratic/1 | 0 | 15 | 0 | 0 | custom | {'low': 15} |
| KXNBADRAFTTEAM | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFTTOP | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFTTOP10 | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFTTOP15 | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFTTOP20 | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFTTOP25 | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFTTOP30 | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFTTOP5 | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBADRAFTTRADE | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAEAST | conference_champion | RESEARCH | quadratic_with_maker_fees/1 | 0 | 15 | 0 | 0 | structured | {'low': 15} |
| KXNBAEAST1SEED | playoff_seed | RESEARCH | quadratic/1 | 0 | 15 | 0 | 0 | structured | {'low': 15} |
| KXNBAECFQUAL | playoff_round_reach | RESEARCH | quadratic/1 | 0 | 15 | 0 | 0 | structured | {'low': 15} |
| KXNBAEFINMVP | awards | UNMODELABLE | quadratic/1 | 0 | 50 | 0 | 0 | structured | {'low': 50} |
| KXNBAESCALATOR3PT | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAESCALATORPTS | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAEUROPEANNOUNCE | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 5 | 0 | 0 | custom | {'low': 5} |
| KXNBAEXEC | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 56 | 0 | 0 | custom | {'low': 56} |
| KXNBAEXTENSION | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAFINALSEXACT | series_winner | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAFINALSMENTION | non_basketball_or_offcourt | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAFINALSMVP | awards | UNMODELABLE | quadratic_with_maker_fees/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAFINALSOUTCOME | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 250 | 0 | 0 | custom | {'low': 250} |
| KXNBAFINALSPRICE | non_basketball_or_offcourt | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAFINALSVIEWER | non_basketball_or_offcourt | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAFINALSVIEWERGAME7 | non_basketball_or_offcourt | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAFINBLOWOUT | series_props | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAFINMVP | awards | UNMODELABLE | quadratic/1 | 0 | 75 | 0 | 0 | structured | {'low': 75} |
| KXNBAFIRST50PTS | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAFIRSTBASKET | first_basket | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAFIRSTOPPONENT | schedule_announcement | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAFRANCHISECOST | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 7 | 0 | 0 | greater | {'low': 7} |
| KXNBAFRANCHISEOWNER | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 3 | 0 | 0 | custom | {'low': 3} |
| KXNBAFTM | player_free_throws | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAGAME | game_winner | MODELABLE | quadratic_with_maker_fees/1 | 0 | 64 | 0 | 0 | structured | {'high': 64} |
| KXNBAGAME7 | series_winner | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAGAMEHIGHSCORE | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 9 | 0 | 0 | greater_or_equal | {'low': 9} |
| KXNBAGAMES | series_winner | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAGAMESPECIALS | season_specials | RESEARCH | quadratic/1 | 0 | 27 | 0 | 0 | custom | {'low': 27} |
| KXNBAH2H3PT | h2h_player_stat | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAH2HBENCHPTS | h2h_team_stat | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAH2HPRA | h2h_player_stat | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAH2HPTS | h2h_player_stat | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAH2HTEAM3PT | h2h_team_stat | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAH2HWINS | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 30 | 0 | 0 | structured | {'low': 30} |
| KXNBAHALLOFFAME | non_basketball_or_offcourt | UNMODELABLE | quadratic/1 | 0 | 28 | 0 | 0 | custom | {'low': 28} |
| KXNBAHIGHESTSCORING | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAHOMECLINCH | series_props | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAHUSTLE | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 75 | 0 | 0 | structured | {'low': 75} |
| KXNBAJOINCONF | franchise_business | UNMODELABLE | quadratic/1 | 0 | 1 | 0 | 0 | None | {'low': 1} |
| KXNBALADDER3PT | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBALADDERPTS | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBALASTTOLOSE | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 4 | 0 | 0 | structured | {'low': 4} |
| KXNBALASVEGAS | franchise_business | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBALOTTERY | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBALOTTERYODDS | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAMATCHUP | playoff_seed | RESEARCH | quadratic/1 | 0 | 660 | 0 | 0 | custom | {'low': 660} |
| KXNBAMENTION | non_basketball_or_offcourt | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAMIMP | awards | UNMODELABLE | quadratic/1 | 0 | 47 | 0 | 0 | structured | {'low': 47} |
| KXNBAMOSTWINS | season_record | RESEARCH | quadratic/1 | 0 | 4 | 0 | 0 | greater_or_equal | {'low': 4} |
| KXNBAMVP | awards | UNMODELABLE | quadratic_with_maker_fees/1 | 0 | 54 | 0 | 0 | structured,custom | {'low': 54} |
| KXNBAMVPDPOY | awards | UNMODELABLE | quadratic/1 | 0 | 1 | 0 | 0 | structured | {'low': 1} |
| KXNBANEWCHAMP | champion_special | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBANEWCHAMPION | champion_special | RESEARCH | quadratic/1 | 0 | 1 | 0 | 0 | None | {'low': 1} |
| KXNBANEXTCONTRACT | transactions | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBANEXTGOVERNOR | franchise_business | UNMODELABLE | quadratic/1 | 0 | 6 | 0 | 0 | custom | {'low': 6} |
| KXNBANEXTTEAM | transactions | UNMODELABLE | quadratic/1 | 0 | 434 | 0 | 0 | structured | {'low': 434} |
| KXNBANEXTTEAMCONF | transactions | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBANEXTTEAMOUTLET | transactions | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBANHL | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBANORTHWEST | division_winner | RESEARCH | quadratic/1 | 0 | 5 | 0 | 0 | structured | {'low': 5} |
| KXNBAONE3PT | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 7 | 0 | 0 | greater | {'low': 7} |
| KXNBAOT | game_overtime | BUILDABLE | quadratic/1 | 0 | 14 | 0 | 0 | greater | {'high': 14} |
| KXNBAOVERTIME | game_overtime | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAPA | player_pa | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAPACIFIC | division_winner | RESEARCH | quadratic/1 | 0 | 5 | 0 | 0 | structured | {'low': 5} |
| KXNBAPARTNERSHIP | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAPIADVANCE | playoffs_qualify | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAPICKTRADE | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAPLAYERDEAL | transactions | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAPLAYERHIGHSCORE | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 32 | 0 | 0 | greater,greater_or_equal | {'low': 32} |
| KXNBAPLAYERSPECIALS | season_specials | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAPLAYIN | playoffs_qualify | RESEARCH | quadratic/1 | 0 | 30 | 0 | 0 | structured | {'low': 30} |
| KXNBAPLAYOFF | playoffs_qualify | RESEARCH | quadratic/1 | 0 | 30 | 0 | 0 | structured | {'low': 30} |
| KXNBAPLAYOFF3D | series_player_stat | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAPLAYOFFPTS | series_player_stat | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAPLAYOFFWINS | series_props | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAPLAYTOGETHER | transactions | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAPOLOSE | series_props | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAPOSTASREC | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 30 | 0 | 0 | structured | {'low': 30} |
| KXNBAPOTM | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 120 | 0 | 0 | structured | {'low': 120} |
| KXNBAPR | player_pr | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAPRA | player_pra | BUILDABLE | quadratic/1 | 1 | 197 | 0 | 0 | greater | {'high': 198} |
| KXNBAPREPACK2ML | parlay_combo | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAPREPACK3ML | parlay_combo | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAPTS | player_points | MODELABLE | quadratic/1 | 4 | 457 | 0 | 0 | greater | {'high': 461} |
| KXNBAPTSALLGAMES | season_player_streak | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAPTSLEADER | game_points_leader | RESEARCH | quadratic/1 | 0 | 126 | 0 | 0 | structured | {'high': 126} |
| KXNBAPTSPROT | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 461 | 0 | 0 | greater | {'high': 461} |
| KXNBARA | player_ra | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBARACE | game_race_to | RESEARCH | quadratic/1 | 0 | 84 | 0 | 0 | custom | {'high': 84} |
| KXNBAREB | player_rebounds | MODELABLE | quadratic/1 | 4 | 516 | 0 | 0 | greater | {'high': 520} |
| KXNBAREBPROT | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 520 | 0 | 0 | greater | {'high': 520} |
| KXNBARECORD | season_record | RESEARCH | quadratic/1 | 0 | 60 | 0 | 0 | structured | {'low': 60} |
| KXNBARELOCATION | franchise_business | UNMODELABLE | quadratic/1 | 0 | 11 | 0 | 0 | custom | {'low': 11} |
| KXNBARETIRE | transactions | UNMODELABLE | quadratic/1 | 0 | 20 | 0 | 0 | structured | {'low': 20} |
| KXNBARETURN | transactions | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBARISINGSTARS | all_star_events | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAROOKIE1STTEAM | all_nba_selections | UNMODELABLE | quadratic/1 | 0 | 30 | 0 | 0 | structured | {'low': 30} |
| KXNBAROOKIE2NDTEAM | all_nba_selections | UNMODELABLE | quadratic/1 | 0 | 40 | 0 | 0 | structured | {'low': 40} |
| KXNBAROTM | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 60 | 0 | 0 | structured | {'low': 60} |
| KXNBAROY | awards | UNMODELABLE | quadratic_with_maker_fees/1 | 0 | 18 | 0 | 0 | structured,custom | {'low': 18} |
| KXNBARULE | franchise_business | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASEATTLE | franchise_business | UNMODELABLE | quadratic/1 | 0 | 1 | 0 | 0 | None | {'low': 1} |
| KXNBASEED | playoff_seed | RESEARCH | quadratic/1 | 0 | 210 | 0 | 0 | structured | {'low': 210} |
| KXNBASEEDOU | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 30 | 0 | 0 | less | {'low': 30} |
| KXNBASERIES | series_winner | RESEARCH | quadratic_with_maker_fees/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASERIES3PMLEADER | series_player_stat | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASERIESASTLEADER | series_player_stat | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASERIESCOMEBACK | series_props | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASERIESGAMES | series_winner | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASERIESGCOMEBACK | series_props | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASERIESOT | series_props | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASERIESPTS | series_player_stat | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASERIESPTSLEADER | series_player_stat | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASERIESPTSSPREAD | series_props | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASERIESREBLEADER | series_player_stat | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASERIESROADWIN | series_props | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASERIESROADWINS | series_props | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASERIESSCORE | series_winner | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASERIESSPREAD | series_props | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASERIESTOTALPTS | series_props | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASHOOTINGSTARS | all_star_events | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASIXTH | awards | UNMODELABLE | quadratic/1 | 0 | 82 | 0 | 0 | structured | {'low': 82} |
| KXNBASJC | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 75 | 0 | 0 | structured | {'low': 75} |
| KXNBASLAMDUNK | all_star_events | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASOUTHEAST | division_winner | RESEARCH | quadratic/1 | 0 | 5 | 0 | 0 | structured | {'low': 5} |
| KXNBASOUTHWEST | division_winner | RESEARCH | quadratic/1 | 0 | 5 | 0 | 0 | structured | {'low': 5} |
| KXNBASPORTSMANSHIP | awards | UNMODELABLE | quadratic/1 | 0 | 100 | 0 | 0 | structured | {'low': 100} |
| KXNBASPREAD | game_spread | MODELABLE | quadratic_with_maker_fees/1 | 0 | 396 | 0 | 0 | greater | {'high': 396} |
| KXNBASTADIUM | franchise_business | UNMODELABLE | quadratic/1 | 0 | 1 | 0 | 0 | None | {'low': 1} |
| KXNBASTAKESALE | franchise_business | UNMODELABLE | quadratic/1 | 0 | 1 | 0 | 0 | None | {'low': 1} |
| KXNBASTARTERS | starting_lineup | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASTATAVG | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 188 | 0 | 0 | greater_or_equal | {'low': 188} |
| KXNBASTATLEADER | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 692 | 0 | 0 | structured | {'low': 692} |
| KXNBASTL | player_steals | BUILDABLE | quadratic/1 | 0 | 207 | 0 | 0 | greater | {'high': 207} |
| KXNBASTOCK | player_stocks | BUILDABLE | quadratic/1 | 0 | 84 | 0 | 0 | greater | {'high': 84} |
| KXNBASTOCKS | player_stocks | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASUMMER | summer_league_season | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASUMMER1HSPREAD | summer_league_spread | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASUMMER1HTOTAL | summer_league_total | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASUMMER1HWINNER | summer_league_game | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASUMMERGAME | summer_league_game | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASUMMERMVP | awards | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASUMMERPTS | summer_league_player | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASUMMERSPREAD | summer_league_spread | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASUMMERTOTAL | summer_league_total | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASWEEP | series_winner | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBATEAM | franchise_business | UNMODELABLE | quadratic/1 | 0 | 1 | 0 | 0 | None | {'low': 1} |
| KXNBATEAMANNOUNCE | transactions | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBATEAMMATE | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 74 | 0 | 0 | structured | {'low': 74} |
| KXNBATEAMSALE | franchise_business | UNMODELABLE | quadratic/1 | 0 | 1 | 0 | 0 | structured | {'low': 1} |
| KXNBATEAMTOTAL | team_total | MODELABLE | quadratic/1 | 0 | 456 | 0 | 0 | greater | {'high': 456} |
| KXNBATEAMWINSTREAK | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 30 | 0 | 0 | structured | {'low': 30} |
| KXNBATOJOINCBA | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 25 | 0 | 0 | custom,structured | {'medium': 25} |
| KXNBATOP3 | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBATOP5ROTY | awards | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBATOPPICK | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBATOTAL | game_total | MODELABLE | quadratic_with_maker_fees/1 | 0 | 348 | 0 | 0 | greater | {'high': 348} |
| KXNBATRADE | transactions | UNMODELABLE | quadratic/1 | 0 | 46 | 0 | 0 | structured | {'medium': 46} |
| KXNBAUNBEATEN | series_props | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAUPSET | series_props | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAWCFQUAL | playoff_round_reach | RESEARCH | quadratic/1 | 0 | 15 | 0 | 0 | structured | {'low': 15} |
| KXNBAWEST | conference_champion | RESEARCH | quadratic_with_maker_fees/1 | 0 | 15 | 0 | 0 | structured | {'low': 15} |
| KXNBAWEST1SEED | playoff_seed | RESEARCH | quadratic/1 | 0 | 15 | 0 | 0 | structured | {'low': 15} |
| KXNBAWFINMVP | awards | UNMODELABLE | quadratic/1 | 0 | 50 | 0 | 0 | structured | {'low': 50} |
| KXNBAWHATTEND | non_basketball_or_offcourt | UNMODELABLE | quadratic/1 | 0 | 1 | 0 | 0 | None | {'low': 1} |
| KXNBAWINMARGIN | game_win_margin | BUILDABLE | quadratic/1 | 0 | 96 | 0 | 0 | custom | {'high': 96} |
| KXNBAWINRECORD | season_record | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAWINS | season_wins | RESEARCH | quadratic/1 | 0 | 312 | 0 | 0 | greater_or_equal | {'low': 312} |
| KXNBAWINSTREAK | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 6 | 0 | 0 | greater_or_equal | {'low': 6} |
| KXNBAXMASOPPONENT | schedule_announcement | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNEXTCOACHOUTNBA | coaching | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNEXTNBACOACH | coaching | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNEXTTEAMNBA | transactions | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNFLNBA | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXPLAYEROPTIONNBA | transactions | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXTEAMSINNBAEF | playoff_round_reach | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXTEAMSINNBAF | playoff_round_reach | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXTEAMSINNBAWF | playoff_round_reach | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXTOP3NBADRAFT | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXTRUMPNBAFINALS | non_basketball_or_offcourt | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |

## Title templates per series

### KXALBUMRELEASEDATENBAYOUNGBOY — Will NBA Youngboy release a new album?

### KXCITYNBAEXPAND — Cities NBA expand
- (3) NAME receive a NAME expansion team before Jan #, #?
- samples: KXCITYNBAEXPAND-28JAN01-CDMX, KXCITYNBAEXPAND-28JAN01-SEA, KXCITYNBAEXPAND-28JAN01-LV
- sample fields: `{"ticker": "KXCITYNBAEXPAND-28JAN01-CDMX", "event_ticker": "KXCITYNBAEXPAND-28JAN01", "market_type": "binary", "title": "Will Mexico City receive a Pro Basketball expansion team before Jan 1, 2028?", "yes_sub_title": "Mexico City", "no_sub_title": "Mexico City", "strike_type": "custom", "custom_strike": {"City": "Mexico City"}, "status": "active", "open_time": "2026-10-16T17:30:00Z", "close_time": "2028-01-01T04:59:00Z", "expected_expiration_time": "2028-01-01T15:00:00Z", "result": "", "rules_primary": "If Pro Basketball officially announces the award of an expansion team franchise to Mexico C`

### KXCOACHOUTNBA — NBA Coach Out

### KXCOACHOUTNBADATE — NBA Coach Out Date
- (3) NAME be out before Jul #, #?
- (2) NAME be out before Oct #, #?
- (1) NAME be out before Feb #, #?
- samples: KXCOACHOUTNBADATE-27NNUR-27JUL01, KXCOACHOUTNBADATE-27NNUR-27FEB12, KXCOACHOUTNBADATE-27MBRO-27OCT25, KXCOACHOUTNBADATE-27MBRO-27JUL01, KXCOACHOUTNBADATE-27SKER-27OCT25, KXCOACHOUTNBADATE-27SKER-27JUL01
- sample fields: `{"ticker": "KXCOACHOUTNBADATE-27NNUR-27JUL01", "event_ticker": "KXCOACHOUTNBADATE-27NNUR", "market_type": "binary", "title": "Will Nick Nurse be out before Jul 1, 2027?", "yes_sub_title": "Out before Jul 1, 2027", "no_sub_title": "Out before Jul 1, 2027", "strike_type": "custom", "custom_strike": {"Date": "Jul 1, 2027"}, "status": "active", "open_time": "2026-05-11T03:50:00Z", "close_time": "2027-07-01T03:59:00Z", "expected_expiration_time": "2027-10-25T14:00:00Z", "result": "", "rules_primary": "If the Head Coach of the Philadelphia Pro Basketball team leaves, or announces they will leave, af`

### KXESPYNBA — BEST NBA PLAYER‬

### KXFIRSTPICKNBA — NBA first pick

### KXKXSPOTIFYALBUMRELEASEDATESC — WILL NBA YOUNBOY RELEASE SLIME CRY 

### KXLEADERNBA3PT — NBA 3PG Leader

### KXLEADERNBAAST — NBA APG Leader

### KXLEADERNBABLK — NBA BPG Leader

### KXLEADERNBAPTS — NBA PPG Leader

### KXLEADERNBAREB — NBA RPG Leader

### KXLEADERNBASTL — NBA SPG Leader

### KXMEDIACOVERNBA2K — WHO WILL BE ON THE COVER OF NBA 2K

### KXMVENBAMULTIGAMEEXTENDED — MVE NBA Multi Game

### KXMVENBASINGLEGAME — MVE NBA Single Game

### KXNBA — Pro Basketball Champion
- (28) NAME win the # NAME?
- (1) NAME L win the # NAME?
- (1) NAME C win the # NAME?
- samples: KXNBA-27-WAS, KXNBA-27-UTA, KXNBA-27-TOR, KXNBA-27-SAS, KXNBA-27-SAC, KXNBA-27-POR
- sample fields: `{"ticker": "KXNBA-27-WAS", "event_ticker": "KXNBA-27", "market_type": "binary", "title": "Will Washington win the 2027 Pro Basketball Finals?", "yes_sub_title": "Washington", "no_sub_title": "Washington", "strike_type": "structured", "custom_strike": {"basketball_team": "0464e75c-8bc8-4f18-9ee2-577832b889d6"}, "status": "active", "open_time": "2026-06-14T08:00:00Z", "close_time": "2029-07-30T14:00:00Z", "expected_expiration_time": "2027-07-31T14:00:00Z", "result": "", "rules_primary": "If Washington wins the 2027 Pro Basketball Finals, then the market resolves to Yes."}`

### KXNBA1H — NBA 1st Half Winner
- (14) Tie in the #st half
- (6) NAME wins the #st half
- (1) Portland wins the #st half
- (1) Memphis wins the #st half
- (1) Sacramento wins the #st half
- (1) NAME L wins the #st half
- (1) NAME C wins the #st half
- (1) Dallas wins the #st half
- samples: KXNBA1H-26OCT29MEMPOR-TIE, KXNBA1H-26OCT29MEMPOR-POR, KXNBA1H-26OCT29MEMPOR-MEM, KXNBA1H-26OCT29SACNOP-TIE, KXNBA1H-26OCT29SACNOP-SAC, KXNBA1H-26OCT29SACNOP-NOP
- sample fields: `{"ticker": "KXNBA1H-26OCT29MEMPOR-TIE", "event_ticker": "KXNBA1H-26OCT29MEMPOR", "market_type": "binary", "title": "Tie in the 1st half", "yes_sub_title": "Tie", "no_sub_title": "Tie", "strike_type": "structured", "custom_strike": {"basketball_team": "1498b6a9-5f7f-4f60-9b4c-fa488a1e515c"}, "status": "active", "open_time": "2026-10-28T02:06:07.073132Z", "close_time": "2026-11-01T02:00:00Z", "expected_expiration_time": "2026-10-30T05:00:00Z", "result": "", "rules_primary": "If neither team wins the 1st half of the Memphis vs Portland Pro Basketball game originally scheduled for Oct 29, 2026, th`

### KXNBA1HSPREAD — NBA 1st Half Spread
- (53) NAME wins the #st half by over # points
- (12) Houston wins the #st half by over # points
- (12) Cleveland wins the #st half by over # points
- (11) NAME L wins the #st half by over # points
- (11) Denver wins the #st half by over # points
- (11) Toronto wins the #st half by over # points
- (11) Philadelphia wins the #st half by over # points
- (11) Detroit wins the #st half by over # points
- samples: KXNBA1HSPREAD-26OCT28LALLAC-LAL9, KXNBA1HSPREAD-26OCT28LALLAC-LAL7, KXNBA1HSPREAD-26OCT28LALLAC-LAL5, KXNBA1HSPREAD-26OCT28LALLAC-LAL3, KXNBA1HSPREAD-26OCT28LALLAC-LAL21, KXNBA1HSPREAD-26OCT28LALLAC-LAL2
- sample fields: `{"ticker": "KXNBA1HSPREAD-26OCT28LALLAC-LAL9", "event_ticker": "KXNBA1HSPREAD-26OCT28LALLAC", "market_type": "binary", "title": "Los Angeles L wins the 1st half by over 8.5 points", "yes_sub_title": "Los Angeles L wins by over 8.5 points", "no_sub_title": "Los Angeles L wins by over 8.5 points", "strike_type": "greater", "floor_strike": 8.5, "custom_strike": {"basketball_team": "2ef4d31c-0b46-4f43-a403-f44d62489034"}, "status": "active", "open_time": "2026-10-28T07:19:30.392614Z", "close_time": "2026-10-31T02:30:00Z", "expected_expiration_time": "2026-10-29T05:30:00Z", "result": "", "rules_pri`

### KXNBA1HTEAMTOTAL — NBA 1st Half Team Total
- (55) NAME over # #st half points scored
- (11) NAME L over # #st half points scored
- (11) NAME C over # #st half points scored
- (11) Dallas over # #st half points scored
- (11) Utah over # #st half points scored
- (11) Denver over # #st half points scored
- (11) Minnesota over # #st half points scored
- (11) Milwaukee over # #st half points scored
- samples: KXNBA1HTEAMTOTAL-26OCT28LALLAC-LAL70, KXNBA1HTEAMTOTAL-26OCT28LALLAC-LAL68, KXNBA1HTEAMTOTAL-26OCT28LALLAC-LAL66, KXNBA1HTEAMTOTAL-26OCT28LALLAC-LAL64, KXNBA1HTEAMTOTAL-26OCT28LALLAC-LAL62, KXNBA1HTEAMTOTAL-26OCT28LALLAC-LAL60
- sample fields: `{"ticker": "KXNBA1HTEAMTOTAL-26OCT28LALLAC-LAL70", "event_ticker": "KXNBA1HTEAMTOTAL-26OCT28LALLAC", "market_type": "binary", "title": "Los Angeles L over 69.5 1st half points scored", "yes_sub_title": "Los Angeles L over 69.5 points", "no_sub_title": "Los Angeles L over 69.5 points", "strike_type": "greater", "floor_strike": 69.5, "custom_strike": {"basketball_team": "2ef4d31c-0b46-4f43-a403-f44d62489034"}, "status": "active", "open_time": "2026-10-28T07:19:30.392614Z", "close_time": "2026-10-31T02:30:00Z", "expected_expiration_time": "2026-10-29T05:30:00Z", "result": "", "rules_primary": "If`

### KXNBA1HTOTAL — NBA 1st Half Total
- (228) #st Half: Over # points scored
- samples: KXNBA1HTOTAL-26OCT28LALLAC-136, KXNBA1HTOTAL-26OCT28LALLAC-134, KXNBA1HTOTAL-26OCT28LALLAC-132, KXNBA1HTOTAL-26OCT28LALLAC-130, KXNBA1HTOTAL-26OCT28LALLAC-128, KXNBA1HTOTAL-26OCT28LALLAC-126
- sample fields: `{"ticker": "KXNBA1HTOTAL-26OCT28LALLAC-136", "event_ticker": "KXNBA1HTOTAL-26OCT28LALLAC", "market_type": "binary", "title": "1st Half: Over 135.5 points scored", "yes_sub_title": "Over 135.5 points", "no_sub_title": "Over 135.5 points", "strike_type": "greater", "floor_strike": 135.5, "status": "active", "open_time": "2026-10-28T07:19:30.392614Z", "close_time": "2026-10-31T02:30:00Z", "expected_expiration_time": "2026-10-29T05:30:00Z", "result": "", "rules_primary": "If over 135.5 total points are scored in the 1st half of the Los Angeles L vs Los Angeles C Pro Basketball game originally sche`

### KXNBA1HWINNER — Pro Baskeball 1st Half Winner

### KXNBA1Q — NBA 1st Quarter Winner
- (14) #st quarter tie
- (6) NAME wins the #st quarter
- (1) Portland wins the #st quarter
- (1) Memphis wins the #st quarter
- (1) Sacramento wins the #st quarter
- (1) NAME L wins the #st quarter
- (1) NAME C wins the #st quarter
- (1) Dallas wins the #st quarter
- samples: KXNBA1Q-26OCT29MEMPOR-TIE, KXNBA1Q-26OCT29MEMPOR-POR, KXNBA1Q-26OCT29MEMPOR-MEM, KXNBA1Q-26OCT29SACNOP-TIE, KXNBA1Q-26OCT29SACNOP-SAC, KXNBA1Q-26OCT29SACNOP-NOP
- sample fields: `{"ticker": "KXNBA1Q-26OCT29MEMPOR-TIE", "event_ticker": "KXNBA1Q-26OCT29MEMPOR", "market_type": "binary", "title": "1st quarter tie", "yes_sub_title": "Tie", "no_sub_title": "Tie", "strike_type": "structured", "custom_strike": {"basketball_team": "1498b6a9-5f7f-4f60-9b4c-fa488a1e515c"}, "status": "active", "open_time": "2026-10-28T02:06:07.073132Z", "close_time": "2026-11-01T02:00:00Z", "expected_expiration_time": "2026-10-30T05:00:00Z", "result": "", "rules_primary": "If neither team wins the 1st quarter of the Memphis vs Portland Pro Basketball game originally scheduled for Oct 29, 2026, the`

### KXNBA1QSPREAD — NBA 1st Quarter Spread
- (36) NAME wins #Q by over # points
- (8) Houston wins #Q by over # points
- (8) Cleveland wins #Q by over # points
- (7) NAME L wins #Q by over # points
- (7) Denver wins #Q by over # points
- (7) Minnesota wins #Q by over # points
- (7) Toronto wins #Q by over # points
- (7) Philadelphia wins #Q by over # points
- samples: KXNBA1QSPREAD-26OCT28LALLAC-LAL8, KXNBA1QSPREAD-26OCT28LALLAC-LAL6, KXNBA1QSPREAD-26OCT28LALLAC-LAL4, KXNBA1QSPREAD-26OCT28LALLAC-LAL2, KXNBA1QSPREAD-26OCT28LALLAC-LAL14, KXNBA1QSPREAD-26OCT28LALLAC-LAL12
- sample fields: `{"ticker": "KXNBA1QSPREAD-26OCT28LALLAC-LAL8", "event_ticker": "KXNBA1QSPREAD-26OCT28LALLAC", "market_type": "binary", "title": "Los Angeles L wins 1Q by over 7.5 points", "yes_sub_title": "Los Angeles L wins by over 7.5 points", "no_sub_title": "Los Angeles L wins by over 7.5 points", "strike_type": "greater", "floor_strike": 7.5, "custom_strike": {"basketball_team": "2ef4d31c-0b46-4f43-a403-f44d62489034"}, "status": "active", "open_time": "2026-10-28T07:19:30.392614Z", "close_time": "2026-10-31T02:30:00Z", "expected_expiration_time": "2026-10-29T05:30:00Z", "result": "", "rules_primary": "If`

### KXNBA1QTEAMTOTAL — NBA 1st Quarter Team Total

### KXNBA1QTOTAL — NBA 1st Quarter Total
- (156) #st Quarter: Over # points scored
- samples: KXNBA1QTOTAL-26OCT28LALLAC-72, KXNBA1QTOTAL-26OCT28LALLAC-70, KXNBA1QTOTAL-26OCT28LALLAC-68, KXNBA1QTOTAL-26OCT28LALLAC-66, KXNBA1QTOTAL-26OCT28LALLAC-64, KXNBA1QTOTAL-26OCT28LALLAC-62
- sample fields: `{"ticker": "KXNBA1QTOTAL-26OCT28LALLAC-72", "event_ticker": "KXNBA1QTOTAL-26OCT28LALLAC", "market_type": "binary", "title": "1st Quarter: Over 71.5 points scored", "yes_sub_title": "Over 71.5 points", "no_sub_title": "Over 71.5 points", "strike_type": "greater", "floor_strike": 71.5, "status": "active", "open_time": "2026-10-28T07:19:30.392614Z", "close_time": "2026-10-31T02:30:00Z", "expected_expiration_time": "2026-10-29T05:30:00Z", "result": "", "rules_primary": "If over 71.5 total points are scored in the 1st quarter of the Los Angeles L vs Los Angeles C Pro Basketball game originally sche`

### KXNBA1QWINNER — NBA 1st Quarter Winner

### KXNBA1STTEAM — All-NBA 1st Team
- (34) NAME: NAME
- (1) NAME: Nikola Jokić
- (1) NAME: LeBron James
- (1) NAME: Luka Dončić
- (1) NAME: LaMelo Ball
- (1) NAME: AJ Dybantsa
- samples: KXNBA1STTEAM-27-VWEMBANYAMA1, KXNBA1STTEAM-27-TMAXEY0, KXNBA1STTEAM-27-THALIBURTON0, KXNBA1STTEAM-27-SGILGEOUSALEXANDER2, KXNBA1STTEAM-27-SCURRY30, KXNBA1STTEAM-27-SBARNES4
- sample fields: `{"ticker": "KXNBA1STTEAM-27-VWEMBANYAMA1", "event_ticker": "KXNBA1STTEAM-27", "market_type": "binary", "title": "All-Pro Basketball First Team Selection: Victor Wembanyama", "yes_sub_title": "Victor Wembanyama", "no_sub_title": "Victor Wembanyama", "strike_type": "structured", "custom_strike": {"basketball_player": "b269496a-6cdf-466d-aa1a-c648b20591ae"}, "status": "active", "open_time": "2026-09-14T21:00:00Z", "close_time": "2027-07-08T14:00:00Z", "expected_expiration_time": "2027-07-01T14:00:00Z", "result": "", "rules_primary": "If Victor Wembanyama is selected to the All-Pro Basketball Firs`

### KXNBA1STTEAMDEF — NBA All-Defensive 1st Team
- (38) NAME: NAME
- (1) NAME: OG Anunoby
- (1) NAME: Jaden McDaniels
- (1) NAME: NAME.
- samples: KXNBA1STTEAMDEF-27-ZEDEY14, KXNBA1STTEAMDEF-27-WKESSLER14, KXNBA1STTEAMDEF-27-VWEMBANYAMA1, KXNBA1STTEAMDEF-27-TCAMARA33, KXNBA1STTEAMDEF-27-SGILGEOUSALEXANDER2, KXNBA1STTEAMDEF-27-SCASTLE5
- sample fields: `{"ticker": "KXNBA1STTEAMDEF-27-ZEDEY14", "event_ticker": "KXNBA1STTEAMDEF-27", "market_type": "binary", "title": "All-Defensive First Team Selection: Zach Edey", "yes_sub_title": "Zach Edey", "no_sub_title": "Zach Edey", "strike_type": "structured", "custom_strike": {"basketball_player": "fe5a04a5-0dc7-4373-baf9-36c4bced83a5"}, "status": "active", "open_time": "2026-09-14T21:00:00Z", "close_time": "2027-07-08T14:00:00Z", "expected_expiration_time": "2027-07-01T14:00:00Z", "result": "", "rules_primary": "If Zach Edey is selected to the All-Defensive First Team in the 2026-27 Pro Basketball seas`

### KXNBA2D — NBA Player Double Double
- (39) NAME: NAME
- (2) NAME.: NAME
- (1) Luka Dončić: NAME
- (1) Nikola Jokić: NAME
- (1) Kel'el Ware: NAME
- (1) LaMelo Ball: NAME
- (1) LeBron James: NAME
- samples: KXNBA2D-26OCT28OKCDAL-DALDGAFFORD21, KXNBA2D-26OCT28OKCDAL-OKCIHARTENSTEIN55, KXNBA2D-26OCT28OKCDAL-OKCSGILGEOUSALEXANDER2, KXNBA2D-26OCT28LALLAC-LALWKESSLER14, KXNBA2D-26OCT28LALLAC-LALLDONCIC77, KXNBA2D-26OCT28SASUTA-SASSCASTLE5
- sample fields: `{"ticker": "KXNBA2D-26OCT28OKCDAL-DALDGAFFORD21", "event_ticker": "KXNBA2D-26OCT28OKCDAL", "market_type": "binary", "title": "Daniel Gafford: Double Double", "yes_sub_title": "Daniel Gafford", "no_sub_title": "Daniel Gafford", "strike_type": "greater", "floor_strike": 0.5, "custom_strike": {"basketball_player": "f7809899-1a37-42df-8c56-5029ca536e5b", "basketball_team": "36547ae6-f0fa-4d06-a6e5-5bfa64a217ed"}, "status": "active", "open_time": "2026-10-28T14:21:16Z", "close_time": "2026-10-31T01:30:00Z", "expected_expiration_time": "2026-10-29T07:30:00Z", "result": "", "rules_primary": "If Danie`

### KXNBA2H — NBA 2nd Half Winner
- (14) Tie in the #nd half
- (6) NAME wins the #nd half
- (1) Portland wins the #nd half
- (1) Memphis wins the #nd half
- (1) Sacramento wins the #nd half
- (1) NAME L wins the #nd half
- (1) NAME C wins the #nd half
- (1) Dallas wins the #nd half
- samples: KXNBA2H-26OCT29MEMPOR-TIE, KXNBA2H-26OCT29MEMPOR-POR, KXNBA2H-26OCT29MEMPOR-MEM, KXNBA2H-26OCT29SACNOP-TIE, KXNBA2H-26OCT29SACNOP-SAC, KXNBA2H-26OCT29SACNOP-NOP
- sample fields: `{"ticker": "KXNBA2H-26OCT29MEMPOR-TIE", "event_ticker": "KXNBA2H-26OCT29MEMPOR", "market_type": "binary", "title": "Tie in the 2nd half", "yes_sub_title": "Tie", "no_sub_title": "Tie", "strike_type": "structured", "custom_strike": {"basketball_team": "1498b6a9-5f7f-4f60-9b4c-fa488a1e515c"}, "status": "active", "open_time": "2026-10-28T02:06:07.073132Z", "close_time": "2026-11-01T02:00:00Z", "expected_expiration_time": "2026-10-30T05:00:00Z", "result": "", "rules_primary": "If neither team wins the 2nd half (including overtime) of the Memphis vs Portland Pro Basketball game originally scheduled`

### KXNBA2HSPREAD — NBA 2nd Half Spread
- (51) NAME wins the #nd half by over # points
- (12) Cleveland wins the #nd half by over # points
- (11) Houston wins the #nd half by over # points
- (11) NAME L wins the #nd half by over # points
- (11) Philadelphia wins the #nd half by over # points
- (11) Detroit wins the #nd half by over # points
- (10) Toronto wins the #nd half by over # points
- (10) Atlanta wins the #nd half by over # points
- samples: KXNBA2HSPREAD-26OCT28HOUMIL-MIL9, KXNBA2HSPREAD-26OCT28HOUMIL-MIL7, KXNBA2HSPREAD-26OCT28HOUMIL-MIL5, KXNBA2HSPREAD-26OCT28HOUMIL-MIL3, KXNBA2HSPREAD-26OCT28HOUMIL-MIL2, KXNBA2HSPREAD-26OCT28HOUMIL-MIL15
- sample fields: `{"ticker": "KXNBA2HSPREAD-26OCT28HOUMIL-MIL9", "event_ticker": "KXNBA2HSPREAD-26OCT28HOUMIL", "market_type": "binary", "title": "Milwaukee wins the 2nd half by over 8.5 points", "yes_sub_title": "Milwaukee wins by over 8.5 points", "no_sub_title": "Milwaukee wins by over 8.5 points", "strike_type": "greater", "floor_strike": 8.5, "custom_strike": {"basketball_team": "5dc3fe01-79a4-4f2f-a953-d922ea4a6dd3"}, "status": "active", "open_time": "2026-10-28T13:39:31.345882Z", "close_time": "2026-10-31T00:00:00Z", "expected_expiration_time": "2026-10-29T03:00:00Z", "result": "", "rules_primary": "If M`

### KXNBA2HTEAMTOTAL — NBA 2nd Half Team Total

### KXNBA2HTOTAL — NBA 2nd Half Total
- (228) #nd Half: Over # points scored
- samples: KXNBA2HTOTAL-26OCT28HOUMIL-99, KXNBA2HTOTAL-26OCT28HOUMIL-97, KXNBA2HTOTAL-26OCT28HOUMIL-133, KXNBA2HTOTAL-26OCT28HOUMIL-131, KXNBA2HTOTAL-26OCT28HOUMIL-129, KXNBA2HTOTAL-26OCT28HOUMIL-127
- sample fields: `{"ticker": "KXNBA2HTOTAL-26OCT28HOUMIL-99", "event_ticker": "KXNBA2HTOTAL-26OCT28HOUMIL", "market_type": "binary", "title": "2nd Half: Over 98.5 points scored", "yes_sub_title": "Over 98.5 points", "no_sub_title": "Over 98.5 points", "strike_type": "greater", "floor_strike": 98.5, "status": "active", "open_time": "2026-10-28T13:39:31.345882Z", "close_time": "2026-10-31T00:00:00Z", "expected_expiration_time": "2026-10-29T03:00:00Z", "result": "", "rules_primary": "If over 98.5 total points are scored in the 2nd half (including overtime) of the Houston vs Milwaukee Pro Basketball game originally`

### KXNBA2HWINNER — Pro Basketball 2nd Half Winner

### KXNBA2KCOVER — Who will be on the cover of NBA 2k?

### KXNBA2NDTEAM — All-NBA 2nd Team
- (48) NAME: NAME
- (1) NAME: NAME III
- (1) NAME: Nikola Jokić
- (1) NAME: LeBron James
- (1) NAME: Luka Dončić
- (1) NAME: LaMelo Ball
- (1) NAME: NAME.
- (1) NAME: AJ Dybantsa
- samples: KXNBA2NDTEAM-27-ZWILLIAMSON1, KXNBA2NDTEAM-27-VWEMBANYAMA1, KXNBA2NDTEAM-27-TYOUNG3, KXNBA2NDTEAM-27-TMURPHY25, KXNBA2NDTEAM-27-TMAXEY0, KXNBA2NDTEAM-27-THERRO11
- sample fields: `{"ticker": "KXNBA2NDTEAM-27-ZWILLIAMSON1", "event_ticker": "KXNBA2NDTEAM-27", "market_type": "binary", "title": "All-Pro Basketball Second Team Selection: Zion Williamson", "yes_sub_title": "Zion Williamson", "no_sub_title": "Zion Williamson", "strike_type": "structured", "custom_strike": {"basketball_player": "220527f6-f6e9-46b3-92b4-ccd8e37ad577"}, "status": "active", "open_time": "2026-09-14T21:00:00Z", "close_time": "2027-07-08T14:00:00Z", "expected_expiration_time": "2027-07-01T14:00:00Z", "result": "", "rules_primary": "If Zion Williamson is selected to the All-Pro Basketball Second Team`

### KXNBA2NDTEAMDEF — NBA All-Defensive 2nd Team
- (47) NAME: NAME
- (2) NAME: NAME.
- (1) NAME: OG Anunoby
- (1) NAME: Jaden McDaniels
- samples: KXNBA2NDTEAMDEF-27-ZEDEY14, KXNBA2NDTEAMDEF-27-WKESSLER14, KXNBA2NDTEAMDEF-27-WCARTER34, KXNBA2NDTEAMDEF-27-VWEMBANYAMA1, KXNBA2NDTEAMDEF-27-TEASON17, KXNBA2NDTEAMDEF-27-TCAMARA33
- sample fields: `{"ticker": "KXNBA2NDTEAMDEF-27-ZEDEY14", "event_ticker": "KXNBA2NDTEAMDEF-27", "market_type": "binary", "title": "All-Defensive Second Team Selection: Zach Edey", "yes_sub_title": "Zach Edey", "no_sub_title": "Zach Edey", "strike_type": "structured", "custom_strike": {"basketball_player": "fe5a04a5-0dc7-4373-baf9-36c4bced83a5"}, "status": "active", "open_time": "2026-09-14T18:00:00Z", "close_time": "2027-07-08T14:00:00Z", "expected_expiration_time": "2027-07-01T14:00:00Z", "result": "", "rules_primary": "If Zach Edey is selected to the All-Defensive Second Team in the 2026-27 Pro Basketball se`

### KXNBA2Q — NBA 2nd Quarter Winner
- (14) #nd quarter tie
- (6) NAME wins the #nd quarter
- (1) Portland wins the #nd quarter
- (1) Memphis wins the #nd quarter
- (1) Sacramento wins the #nd quarter
- (1) NAME L wins the #nd quarter
- (1) NAME C wins the #nd quarter
- (1) Dallas wins the #nd quarter
- samples: KXNBA2Q-26OCT29MEMPOR-TIE, KXNBA2Q-26OCT29MEMPOR-POR, KXNBA2Q-26OCT29MEMPOR-MEM, KXNBA2Q-26OCT29SACNOP-TIE, KXNBA2Q-26OCT29SACNOP-SAC, KXNBA2Q-26OCT29SACNOP-NOP
- sample fields: `{"ticker": "KXNBA2Q-26OCT29MEMPOR-TIE", "event_ticker": "KXNBA2Q-26OCT29MEMPOR", "market_type": "binary", "title": "2nd quarter tie", "yes_sub_title": "Tie", "no_sub_title": "Tie", "strike_type": "structured", "custom_strike": {"basketball_team": "1498b6a9-5f7f-4f60-9b4c-fa488a1e515c"}, "status": "active", "open_time": "2026-10-28T02:06:07.073132Z", "close_time": "2026-11-01T02:00:00Z", "expected_expiration_time": "2026-10-30T05:00:00Z", "result": "", "rules_primary": "If neither team wins the 2nd quarter of the Memphis vs Portland Pro Basketball game originally scheduled for Oct 29, 2026, the`

### KXNBA2QSPREAD — NBA 2nd Quarter Spread
- (34) NAME wins #Q by over # points
- (8) Cleveland wins #Q by over # points
- (7) Denver wins #Q by over # points
- (7) NAME L wins #Q by over # points
- (7) Minnesota wins #Q by over # points
- (7) Houston wins #Q by over # points
- (7) Toronto wins #Q by over # points
- (7) Philadelphia wins #Q by over # points
- samples: KXNBA2QSPREAD-26OCT28DENNOP-NOP9, KXNBA2QSPREAD-26OCT28DENNOP-NOP7, KXNBA2QSPREAD-26OCT28DENNOP-NOP5, KXNBA2QSPREAD-26OCT28DENNOP-NOP3, KXNBA2QSPREAD-26OCT28DENNOP-NOP2, KXNBA2QSPREAD-26OCT28DENNOP-NOP11
- sample fields: `{"ticker": "KXNBA2QSPREAD-26OCT28DENNOP-NOP9", "event_ticker": "KXNBA2QSPREAD-26OCT28DENNOP", "market_type": "binary", "title": "New Orleans wins 2Q by over 8.5 points", "yes_sub_title": "New Orleans wins by over 8.5 points", "no_sub_title": "New Orleans wins by over 8.5 points", "strike_type": "greater", "floor_strike": 8.5, "custom_strike": {"basketball_team": "d3c8c2ac-c4a0-4d67-8b16-53cb91118dfc"}, "status": "active", "open_time": "2026-10-28T13:23:29.558645Z", "close_time": "2026-10-31T00:00:00Z", "expected_expiration_time": "2026-10-29T03:00:00Z", "result": "", "rules_primary": "If New O`

### KXNBA2QTEAMTOTAL — NBA 2nd Quarter Team Total

### KXNBA2QTOTAL — NBA 2nd Quarter Total
- (156) #nd Quarter: Over # points scored
- samples: KXNBA2QTOTAL-26OCT28OKCDAL-67, KXNBA2QTOTAL-26OCT28OKCDAL-65, KXNBA2QTOTAL-26OCT28OKCDAL-63, KXNBA2QTOTAL-26OCT28OKCDAL-61, KXNBA2QTOTAL-26OCT28OKCDAL-59, KXNBA2QTOTAL-26OCT28OKCDAL-57
- sample fields: `{"ticker": "KXNBA2QTOTAL-26OCT28OKCDAL-67", "event_ticker": "KXNBA2QTOTAL-26OCT28OKCDAL", "market_type": "binary", "title": "2nd Quarter: Over 66.5 points scored", "yes_sub_title": "Over 66.5 points", "no_sub_title": "Over 66.5 points", "strike_type": "greater", "floor_strike": 66.5, "status": "active", "open_time": "2026-10-28T11:29:25.390447Z", "close_time": "2026-10-31T01:30:00Z", "expected_expiration_time": "2026-10-29T04:30:00Z", "result": "", "rules_primary": "If over 66.5 total points are scored in the 2nd quarter of the Oklahoma City vs Dallas Pro Basketball game originally scheduled f`

### KXNBA2QWINNER — NBA 2nd Quarter Winner

### KXNBA30COMEBACK — NBA 3-0 Series Comeback

### KXNBA3D — NBA Player Triple Double
- (10) NAME: NAME
- (1) Luka Dončić: NAME
- (1) Nikola Jokić: NAME
- (1) LaMelo Ball: NAME
- (1) LeBron James: NAME
- samples: KXNBA3D-26OCT28LALLAC-LALLDONCIC77, KXNBA3D-26OCT28SASUTA-SASSCASTLE5, KXNBA3D-26OCT28DENNOP-DENNJOKIC15, KXNBA3D-26OCT28GSWMIN-MINLBALL1, KXNBA3D-26OCT28CHADET-DETCCUNNINGHAM2, KXNBA3D-26OCT28NYKCHI-NYKJHART3
- sample fields: `{"ticker": "KXNBA3D-26OCT28LALLAC-LALLDONCIC77", "event_ticker": "KXNBA3D-26OCT28LALLAC", "market_type": "binary", "title": "Luka Don\u010di\u0107: Triple Double", "yes_sub_title": "Luka Don\u010di\u0107", "no_sub_title": "Luka Don\u010di\u0107", "strike_type": "greater", "floor_strike": 0.5, "custom_strike": {"basketball_player": "008856e0-b1ab-47f1-8df7-06e243f5f000", "basketball_team": "2ef4d31c-0b46-4f43-a403-f44d62489034"}, "status": "active", "open_time": "2026-10-28T12:06:09.363559Z", "close_time": "2026-10-31T02:30:00Z", "expected_expiration_time": "2026-10-29T05:30:00Z", "result": "",`

### KXNBA3PEAT — Pro Basketball Three-Peat Champion

### KXNBA3PT — NBA Player Threes
- (457) NAME: #+ threes
- (23) NAME.: #+ threes
- (5) Jared McCain: #+ threes
- (5) Luka Dončić: #+ threes
- (5) Jaden McDaniels: #+ threes
- (5) P.J. Washington: #+ threes
- (5) LaMelo Ball: #+ threes
- (5) OG Anunoby: #+ threes
- samples: KXNBA3PT-26OCT28CHADET-DETDROBINSON55-1, KXNBA3PT-26OCT28CHADET-DETDJENKINS24-5, KXNBA3PT-26OCT28CHADET-DETDJENKINS24-4, KXNBA3PT-26OCT28CHADET-DETDJENKINS24-3, KXNBA3PT-26OCT28CHADET-DETDJENKINS24-2, KXNBA3PT-26OCT28CHADET-DETDJENKINS24-1
- sample fields: `{"ticker": "KXNBA3PT-26OCT28CHADET-DETDROBINSON55-1", "event_ticker": "KXNBA3PT-26OCT28CHADET", "market_type": "binary", "title": "Duncan Robinson: 1+ threes", "yes_sub_title": "Duncan Robinson: 1+", "no_sub_title": "Duncan Robinson: 1+", "strike_type": "greater", "floor_strike": 0.5, "custom_strike": {"basketball_player": "74de2700-bb3b-4770-98b7-4c20677814cf", "basketball_team": "65569528-1888-40aa-9d62-2b0e8142a9b4"}, "status": "active", "open_time": "2026-10-28T19:21:06Z", "close_time": "2026-10-30T23:00:00Z", "expected_expiration_time": "2026-10-29T05:00:00Z", "result": "", "rules_primary`

### KXNBA3PTALLGAMES — Pro Basketball 3-Pointers in Every Game

### KXNBA3PTCONTEST — NBA 3-Point Contest Winner

### KXNBA3PTPROT — NBA Player Threes Protected
- (457) NAME: #+ threes
- (23) NAME.: #+ threes
- (5) Jared McCain: #+ threes
- (5) Luka Dončić: #+ threes
- (5) P.J. Washington: #+ threes
- (5) Jaden McDaniels: #+ threes
- (5) LaMelo Ball: #+ threes
- (5) Fred VanVleet: #+ threes
- samples: KXNBA3PTPROT-26OCT28WASCLE-WASBCOULIBALY0-4, KXNBA3PTPROT-26OCT28WASCLE-WASBCOULIBALY0-3, KXNBA3PTPROT-26OCT28WASCLE-WASBCOULIBALY0-2, KXNBA3PTPROT-26OCT28WASCLE-WASBCOULIBALY0-1, KXNBA3PTPROT-26OCT28CHADET-DETDROBINSON55-1, KXNBA3PTPROT-26OCT28CHADET-DETDJENKINS24-5
- sample fields: `{"ticker": "KXNBA3PTPROT-26OCT28WASCLE-WASBCOULIBALY0-4", "event_ticker": "KXNBA3PTPROT-26OCT28WASCLE", "market_type": "binary", "title": "Bilal Coulibaly: 4+ threes", "yes_sub_title": "Bilal Coulibaly: 4+", "no_sub_title": "Bilal Coulibaly: 4+", "strike_type": "greater", "floor_strike": 3.5, "custom_strike": {"basketball_player": "2b9b4c52-7963-4bbc-820a-787f29642aa0", "basketball_team": "0464e75c-8bc8-4f18-9ee2-577832b889d6"}, "status": "active", "open_time": "2026-10-28T19:51:10Z", "close_time": "2026-10-30T23:00:00Z", "expected_expiration_time": "2026-10-29T05:00:00Z", "result": "", "rules`

### KXNBA3Q — NBA 3rd Quarter Winner
- (14) #rd quarter tie
- (6) NAME wins the #rd quarter
- (1) Portland wins the #rd quarter
- (1) Memphis wins the #rd quarter
- (1) Sacramento wins the #rd quarter
- (1) NAME L wins the #rd quarter
- (1) NAME C wins the #rd quarter
- (1) Dallas wins the #rd quarter
- samples: KXNBA3Q-26OCT29MEMPOR-TIE, KXNBA3Q-26OCT29MEMPOR-POR, KXNBA3Q-26OCT29MEMPOR-MEM, KXNBA3Q-26OCT29SACNOP-TIE, KXNBA3Q-26OCT29SACNOP-SAC, KXNBA3Q-26OCT29SACNOP-NOP
- sample fields: `{"ticker": "KXNBA3Q-26OCT29MEMPOR-TIE", "event_ticker": "KXNBA3Q-26OCT29MEMPOR", "market_type": "binary", "title": "3rd quarter tie", "yes_sub_title": "Tie", "no_sub_title": "Tie", "strike_type": "structured", "custom_strike": {"basketball_team": "1498b6a9-5f7f-4f60-9b4c-fa488a1e515c"}, "status": "active", "open_time": "2026-10-28T02:06:07.073132Z", "close_time": "2026-11-01T02:00:00Z", "expected_expiration_time": "2026-10-30T05:00:00Z", "result": "", "rules_primary": "If neither team wins the 3rd quarter of the Memphis vs Portland Pro Basketball game originally scheduled for Oct 29, 2026, the`

### KXNBA3QSPREAD — NBA 3rd Quarter Spread
- (34) NAME wins #Q by over # points
- (8) Cleveland wins #Q by over # points
- (7) NAME L wins #Q by over # points
- (7) Denver wins #Q by over # points
- (7) Minnesota wins #Q by over # points
- (7) Houston wins #Q by over # points
- (7) Toronto wins #Q by over # points
- (7) Philadelphia wins #Q by over # points
- samples: KXNBA3QSPREAD-26OCT28LALLAC-LAL8, KXNBA3QSPREAD-26OCT28LALLAC-LAL6, KXNBA3QSPREAD-26OCT28LALLAC-LAL4, KXNBA3QSPREAD-26OCT28LALLAC-LAL2, KXNBA3QSPREAD-26OCT28LALLAC-LAL14, KXNBA3QSPREAD-26OCT28LALLAC-LAL12
- sample fields: `{"ticker": "KXNBA3QSPREAD-26OCT28LALLAC-LAL8", "event_ticker": "KXNBA3QSPREAD-26OCT28LALLAC", "market_type": "binary", "title": "Los Angeles L wins 3Q by over 7.5 points", "yes_sub_title": "Los Angeles L wins by over 7.5 points", "no_sub_title": "Los Angeles L wins by over 7.5 points", "strike_type": "greater", "floor_strike": 7.5, "custom_strike": {"basketball_team": "2ef4d31c-0b46-4f43-a403-f44d62489034"}, "status": "active", "open_time": "2026-10-28T07:19:30.392614Z", "close_time": "2026-10-31T02:30:00Z", "expected_expiration_time": "2026-10-29T05:30:00Z", "result": "", "rules_primary": "If`

### KXNBA3QTEAMTOTAL — NBA 3rd Quarter Team Total

### KXNBA3QTOTAL — NBA 3rd Quarter Total
- (156) #rd Quarter: Over # points scored
- samples: KXNBA3QTOTAL-26OCT28CHADET-68, KXNBA3QTOTAL-26OCT28CHADET-66, KXNBA3QTOTAL-26OCT28CHADET-64, KXNBA3QTOTAL-26OCT28CHADET-62, KXNBA3QTOTAL-26OCT28CHADET-60, KXNBA3QTOTAL-26OCT28CHADET-58
- sample fields: `{"ticker": "KXNBA3QTOTAL-26OCT28CHADET-68", "event_ticker": "KXNBA3QTOTAL-26OCT28CHADET", "market_type": "binary", "title": "3rd Quarter: Over 67.5 points scored", "yes_sub_title": "Over 67.5 points", "no_sub_title": "Over 67.5 points", "strike_type": "greater", "floor_strike": 67.5, "status": "active", "open_time": "2026-10-28T09:49:19.788522Z", "close_time": "2026-10-30T23:00:00Z", "expected_expiration_time": "2026-10-29T02:00:00Z", "result": "", "rules_primary": "If over 67.5 total points are scored in the 3rd quarter of the Charlotte vs Detroit Pro Basketball game originally scheduled for `

### KXNBA3QWINNER — NBA 3rd Quarter Winner

### KXNBA3RDTEAM — All-NBA 3rd Team
- (48) NAME: NAME
- (1) NAME: NAME III
- (1) NAME: Nikola Jokić
- (1) NAME: LeBron James
- (1) NAME: Luka Dončić
- (1) NAME: LaMelo Ball
- (1) NAME: NAME.
- (1) NAME: AJ Dybantsa
- samples: KXNBA3RDTEAM-27-ZWILLIAMSON1, KXNBA3RDTEAM-27-VWEMBANYAMA1, KXNBA3RDTEAM-27-TYOUNG3, KXNBA3RDTEAM-27-TMURPHY25, KXNBA3RDTEAM-27-TMAXEY0, KXNBA3RDTEAM-27-THERRO11
- sample fields: `{"ticker": "KXNBA3RDTEAM-27-ZWILLIAMSON1", "event_ticker": "KXNBA3RDTEAM-27", "market_type": "binary", "title": "All-Pro Basketball Third Team Selection: Zion Williamson", "yes_sub_title": "Zion Williamson", "no_sub_title": "Zion Williamson", "strike_type": "structured", "custom_strike": {"basketball_player": "220527f6-f6e9-46b3-92b4-ccd8e37ad577"}, "status": "active", "open_time": "2026-09-14T21:00:00Z", "close_time": "2027-07-08T14:00:00Z", "expected_expiration_time": "2027-07-01T14:00:00Z", "result": "", "rules_primary": "If Zion Williamson is selected to the All-Pro Basketball Third Team i`

### KXNBA4Q — NBA 4th Quarter Winner
- (14) #th quarter tie
- (6) NAME wins the #th quarter
- (1) Portland wins the #th quarter
- (1) Memphis wins the #th quarter
- (1) Sacramento wins the #th quarter
- (1) NAME L wins the #th quarter
- (1) NAME C wins the #th quarter
- (1) Dallas wins the #th quarter
- samples: KXNBA4Q-26OCT29MEMPOR-TIE, KXNBA4Q-26OCT29MEMPOR-POR, KXNBA4Q-26OCT29MEMPOR-MEM, KXNBA4Q-26OCT29SACNOP-TIE, KXNBA4Q-26OCT29SACNOP-SAC, KXNBA4Q-26OCT29SACNOP-NOP
- sample fields: `{"ticker": "KXNBA4Q-26OCT29MEMPOR-TIE", "event_ticker": "KXNBA4Q-26OCT29MEMPOR", "market_type": "binary", "title": "4th quarter tie", "yes_sub_title": "Tie", "no_sub_title": "Tie", "strike_type": "structured", "custom_strike": {"basketball_team": "1498b6a9-5f7f-4f60-9b4c-fa488a1e515c"}, "status": "active", "open_time": "2026-10-28T02:06:07.073132Z", "close_time": "2026-11-01T02:00:00Z", "expected_expiration_time": "2026-10-30T05:00:00Z", "result": "", "rules_primary": "If neither team wins the 4th quarter (excluding overtime) of the Memphis vs Portland Pro Basketball game originally scheduled `

### KXNBA4QSPREAD — NBA 4th Quarter Spread
- (34) NAME wins #Q by over # points
- (7) Toronto wins #Q by over # points
- (7) Detroit wins #Q by over # points
- (7) NAME L wins #Q by over # points
- (7) Denver wins #Q by over # points
- (7) Minnesota wins #Q by over # points
- (7) Houston wins #Q by over # points
- (7) Philadelphia wins #Q by over # points
- samples: KXNBA4QSPREAD-26OCT28ORLTOR-TOR8, KXNBA4QSPREAD-26OCT28ORLTOR-TOR6, KXNBA4QSPREAD-26OCT28ORLTOR-TOR4, KXNBA4QSPREAD-26OCT28ORLTOR-TOR2, KXNBA4QSPREAD-26OCT28ORLTOR-TOR14, KXNBA4QSPREAD-26OCT28ORLTOR-TOR12
- sample fields: `{"ticker": "KXNBA4QSPREAD-26OCT28ORLTOR-TOR8", "event_ticker": "KXNBA4QSPREAD-26OCT28ORLTOR", "market_type": "binary", "title": "Toronto wins 4Q by over 7.5 points", "yes_sub_title": "Toronto wins by over 7.5 points", "no_sub_title": "Toronto wins by over 7.5 points", "strike_type": "greater", "floor_strike": 7.5, "custom_strike": {"basketball_team": "96c447dd-2cdd-4c58-a151-ef0df87de981"}, "status": "active", "open_time": "2026-10-28T11:53:23.371524Z", "close_time": "2026-10-30T23:30:00Z", "expected_expiration_time": "2026-10-29T02:30:00Z", "result": "", "rules_primary": "If Toronto wins by m`

### KXNBA4QTEAMTOTAL — NBA 4th Quarter Team Total

### KXNBA4QTOTAL — NBA 4th Quarter Total
- (156) #th Quarter: Over # points scored
- samples: KXNBA4QTOTAL-26OCT28OKCDAL-70, KXNBA4QTOTAL-26OCT28OKCDAL-68, KXNBA4QTOTAL-26OCT28OKCDAL-66, KXNBA4QTOTAL-26OCT28OKCDAL-64, KXNBA4QTOTAL-26OCT28OKCDAL-62, KXNBA4QTOTAL-26OCT28OKCDAL-60
- sample fields: `{"ticker": "KXNBA4QTOTAL-26OCT28OKCDAL-70", "event_ticker": "KXNBA4QTOTAL-26OCT28OKCDAL", "market_type": "binary", "title": "4th Quarter: Over 69.5 points scored", "yes_sub_title": "Over 69.5 points", "no_sub_title": "Over 69.5 points", "strike_type": "greater", "floor_strike": 69.5, "status": "active", "open_time": "2026-10-28T15:55:32.347314Z", "close_time": "2026-10-31T01:30:00Z", "expected_expiration_time": "2026-10-29T04:30:00Z", "result": "", "rules_primary": "If over 69.5 total points are scored in the 4th quarter (excluding overtime) of the Oklahoma City vs Dallas Pro Basketball game o`

### KXNBA4QWINNER — NBA 4th Quarter Winner

### KXNBAALLSTAR — NBA All-Star game

### KXNBAALLSTARGAME — NBA All-Star Game Winner

### KXNBAALLSTARMVP — NBA All-Star Game MVP

### KXNBAALLSTARS — NBA All-Stars
- (52) NAME: NAME
- (2) NAME: NAME.
- (1) NAME: NAME III
- (1) NAME: Nikola Jokić
- (1) NAME: LeBron James
- (1) NAME: Luka Dončić
- (1) NAME: LaMelo Ball
- (1) NAME: AJ Dybantsa
- samples: KXNBAALLSTARS-27-ZWILLIAMSON1, KXNBAALLSTARS-27-VWEMBANYAMA1, KXNBAALLSTARS-27-TYOUNG3, KXNBAALLSTARS-27-TMURPHY25, KXNBAALLSTARS-27-TMAXEY0, KXNBAALLSTARS-27-THERRO11
- sample fields: `{"ticker": "KXNBAALLSTARS-27-ZWILLIAMSON1", "event_ticker": "KXNBAALLSTARS-27", "market_type": "binary", "title": "Pro Basketball All-Star Selection: Zion Williamson", "yes_sub_title": "Zion Williamson", "no_sub_title": "Zion Williamson", "strike_type": "structured", "custom_strike": {"basketball_player": "220527f6-f6e9-46b3-92b4-ccd8e37ad577"}, "status": "active", "open_time": "2026-09-14T21:00:00Z", "close_time": "2027-07-08T14:00:00Z", "expected_expiration_time": "2027-07-01T14:00:00Z", "result": "", "rules_primary": "If Zion Williamson is selected as a Pro Basketball All-Star in the 2026-2`

### KXNBAAPOLOGY — Pro Basketball Apology

### KXNBAASSTARTERS — NBA All-Star Starters

### KXNBAAST — NBA Player Assists
- (320) NAME: #+ assists
- (14) NAME.: #+ assists
- (5) Luka Dončić: #+ assists
- (5) LaMelo Ball: #+ assists
- (5) LeBron James: #+ assists
- (5) Nikola Jokić: #+ assists
- (4) Jared McCain: #+ assists
- (4) CJ McCollum: #+ assists
- samples: KXNBAAST-26OCT28CHADET-CHAGALLEN8-8, KXNBAAST-26OCT28CHADET-CHAGALLEN8-6, KXNBAAST-26OCT28CHADET-CHAGALLEN8-4, KXNBAAST-26OCT28CHADET-CHAGALLEN8-2, KXNBAAST-26OCT28CHADET-DETDJENKINS24-8, KXNBAAST-26OCT28CHADET-DETDJENKINS24-6
- sample fields: `{"ticker": "KXNBAAST-26OCT28CHADET-CHAGALLEN8-8", "event_ticker": "KXNBAAST-26OCT28CHADET", "market_type": "binary", "title": "Grayson Allen: 8+ assists", "yes_sub_title": "Grayson Allen: 8+", "no_sub_title": "Grayson Allen: 8+", "strike_type": "greater", "floor_strike": 7.5, "custom_strike": {"basketball_player": "07a246cd-1c40-42f1-849e-58fbd7696c30", "basketball_team": "7c980c51-fa76-4571-b165-242b2a00f3a1"}, "status": "active", "open_time": "2026-10-28T19:21:06Z", "close_time": "2026-10-30T23:00:00Z", "expected_expiration_time": "2026-10-29T05:00:00Z", "result": "", "rules_primary": "If Gr`

### KXNBAASTPROT — NBA Player Assists Protected
- (320) NAME: #+ assists
- (14) NAME.: #+ assists
- (5) Luka Dončić: #+ assists
- (5) LaMelo Ball: #+ assists
- (5) LeBron James: #+ assists
- (5) Nikola Jokić: #+ assists
- (4) Jared McCain: #+ assists
- (4) CJ McCollum: #+ assists
- samples: KXNBAASTPROT-26OCT28CHADET-CHAGALLEN8-8, KXNBAASTPROT-26OCT28CHADET-CHAGALLEN8-6, KXNBAASTPROT-26OCT28CHADET-CHAGALLEN8-4, KXNBAASTPROT-26OCT28CHADET-CHAGALLEN8-2, KXNBAASTPROT-26OCT28LALLAC-LALWKESSLER14-6, KXNBAASTPROT-26OCT28LALLAC-LALWKESSLER14-4
- sample fields: `{"ticker": "KXNBAASTPROT-26OCT28CHADET-CHAGALLEN8-8", "event_ticker": "KXNBAASTPROT-26OCT28CHADET", "market_type": "binary", "title": "Grayson Allen: 8+ assists", "yes_sub_title": "Grayson Allen: 8+", "no_sub_title": "Grayson Allen: 8+", "strike_type": "greater", "floor_strike": 7.5, "custom_strike": {"basketball_player": "07a246cd-1c40-42f1-849e-58fbd7696c30", "basketball_team": "7c980c51-fa76-4571-b165-242b2a00f3a1"}, "status": "active", "open_time": "2026-10-28T19:12:14Z", "close_time": "2026-10-30T23:00:00Z", "expected_expiration_time": "2026-10-29T05:00:00Z", "result": "", "rules_primary"`

### KXNBAATLANTIC — Pro Basketball Atlantic Division Winner
- (5) NAME be the NAME winner in the #-# season?
- samples: KXNBAATLANTIC-26-TOR, KXNBAATLANTIC-26-PHI, KXNBAATLANTIC-26-NYK, KXNBAATLANTIC-26-BOS, KXNBAATLANTIC-26-BKN
- sample fields: `{"ticker": "KXNBAATLANTIC-26-TOR", "event_ticker": "KXNBAATLANTIC-26", "market_type": "binary", "title": "Will Toronto be the Atlantic Division winner in the 2026-27 season?", "yes_sub_title": "Toronto", "no_sub_title": "Toronto", "strike_type": "structured", "custom_strike": {"basketball_team": "96c447dd-2cdd-4c58-a151-ef0df87de981"}, "status": "active", "open_time": "2026-07-01T21:00:00Z", "close_time": "2027-07-14T14:00:00Z", "expected_expiration_time": "2027-06-30T14:00:00Z", "result": "", "rules_primary": "If Toronto is the Atlantic Division winner in the 2026-27 Pro Basketball season, th`

### KXNBAATTEND — Who will attend the NBA game?

### KXNBAAWARDFIN — NBA Award Finalists
- (183) NAME of the NAME: NAME
- (63) NAME: NAME
- (17) NAME of the NAME: NAME.
- (3) NAME: NAME.
- (2) NAME of the NAME: NAME II
- (2) NAME of the NAME: P.J. Washington
- (2) NAME of the NAME: NAME III
- (2) NAME: NAME III
- samples: KXNBAAWARDFIN-27COY-WHAR, KXNBAAWARDFIN-27COY-TSPL, KXNBAAWARDFIN-27COY-TLUE, KXNBAAWARDFIN-27COY-TJEN, KXNBAAWARDFIN-27COY-TIIS, KXNBAAWARDFIN-27COY-SSWE
- sample fields: `{"ticker": "KXNBAAWARDFIN-27COY-WHAR", "event_ticker": "KXNBAAWARDFIN-27COY", "market_type": "binary", "title": "Pro Basketball Coach of the Year Finalists: Will Hardy", "yes_sub_title": "Will Hardy", "no_sub_title": "Will Hardy", "strike_type": "custom", "custom_strike": {"Entity": "Will Hardy"}, "status": "active", "open_time": "2026-10-07T18:30:00Z", "close_time": "2027-07-08T14:00:00Z", "expected_expiration_time": "2027-07-01T14:00:00Z", "result": "", "rules_primary": "If Will Hardy is selected as a finalist for Coach of the Year in the 2026-27 Pro Basketball season, then the market resolv`

### KXNBABENCHPTS — NBA Bench Points

### KXNBABLK — NBA Player Blocks
- (72) NAME: #+ blocks
- (7) NAME.: #+ blocks
- (3) Nikola Jokić: #+ blocks
- (2) Kel'el Ware: #+ blocks
- (2) Fred VanVleet: #+ blocks
- (2) Jaden McDaniels: #+ blocks
- (2) NAME III: #+ blocks
- (2) OG Anunoby: #+ blocks
- samples: KXNBABLK-26OCT28HOUMIL-MILTHERRO11-2, KXNBABLK-26OCT28HOUMIL-MILTHERRO11-1, KXNBABLK-26OCT28HOUMIL-MILRROLLINS13-2, KXNBABLK-26OCT28HOUMIL-MILRROLLINS13-1, KXNBABLK-26OCT28HOUMIL-MILMTURNER3-3, KXNBABLK-26OCT28HOUMIL-MILMTURNER3-2
- sample fields: `{"ticker": "KXNBABLK-26OCT28HOUMIL-MILTHERRO11-2", "event_ticker": "KXNBABLK-26OCT28HOUMIL", "market_type": "binary", "title": "Tyler Herro: 2+ blocks", "yes_sub_title": "Tyler Herro: 2+", "no_sub_title": "Tyler Herro: 2+", "strike_type": "greater", "floor_strike": 1.5, "custom_strike": {"basketball_player": "3e3ceeda-5f54-4aa0-9ced-e8ff6cbcadf2", "basketball_team": "5dc3fe01-79a4-4f2f-a953-d922ea4a6dd3"}, "status": "active", "open_time": "2026-10-28T19:46:01.700276Z", "close_time": "2026-10-31T00:00:00Z", "expected_expiration_time": "2026-10-29T03:00:00Z", "result": "", "rules_primary": "If T`

### KXNBACELEBRITY3PT — NBA Celebrity 3PT Contest

### KXNBACELEBRITYGAME — Pro Basketball All-Star Celebrity Game

### KXNBACENTRAL — Pro Basketball Central Division Winner
- (5) NAME be the NAME winner in the #-# season?
- samples: KXNBACENTRAL-26-MIL, KXNBACENTRAL-26-IND, KXNBACENTRAL-26-DET, KXNBACENTRAL-26-CLE, KXNBACENTRAL-26-CHI
- sample fields: `{"ticker": "KXNBACENTRAL-26-MIL", "event_ticker": "KXNBACENTRAL-26", "market_type": "binary", "title": "Will Milwaukee be the Central Division winner in the 2026-27 season?", "yes_sub_title": "Milwaukee", "no_sub_title": "Milwaukee", "strike_type": "structured", "custom_strike": {"basketball_team": "5dc3fe01-79a4-4f2f-a953-d922ea4a6dd3"}, "status": "active", "open_time": "2026-07-01T21:00:00Z", "close_time": "2027-07-14T14:00:00Z", "expected_expiration_time": "2027-06-30T14:00:00Z", "result": "", "rules_primary": "If Milwaukee is the Central Division winner in the 2026-27 Pro Basketball season`

### KXNBACITYEXPAND — NBA City Franchise Expansion
- (4) NAME expansion awarded before Jan #, #?
- (1) NAME expansion awarded before Nov #, #?
- (1) NAME expansion awarded before Feb #, #?
- (1) NAME expansion awarded before Dec #, #?
- samples: KXNBACITYEXPAND-01JAN30-01NOV26, KXNBACITYEXPAND-01JAN30-01JAN30, KXNBACITYEXPAND-01JAN30-01JAN29, KXNBACITYEXPAND-01JAN30-01JAN28, KXNBACITYEXPAND-01JAN30-01JAN27, KXNBACITYEXPAND-01JAN30-01FEB27
- sample fields: `{"ticker": "KXNBACITYEXPAND-01JAN30-01NOV26", "event_ticker": "KXNBACITYEXPAND-01JAN30", "market_type": "binary", "title": "Pro Basketball expansion awarded before Nov 1, 2026?", "yes_sub_title": "Before Nov 1, 2026", "no_sub_title": "Before Nov 1, 2026", "strike_type": "custom", "custom_strike": {"deadline": "2026-11-01"}, "status": "active", "open_time": "2026-09-30T16:00:00Z", "close_time": "2026-11-01T03:59:00Z", "expected_expiration_time": "2030-01-01T05:00:00Z", "result": "", "rules_primary": "If the National Basketball Association (NBA) officially announces the award of an expansion tea`

### KXNBACLUTCH — NBA Clutch Player of the Year
- (45) NAME of the Year: NAME
- (1) NAME of the Year: Zach LaVine
- (1) NAME of the Year: Nikola Jokić
- (1) NAME of the Year: NAME.
- (1) NAME of the Year: LeBron James
- (1) NAME of the Year: Luka Dončić
- (1) NAME of the Year: LaMelo Ball
- (1) NAME of the Year: NAME III
- samples: KXNBACLUTCH-27-ZWILLIAMSON1, KXNBACLUTCH-27-ZLAVINE8, KXNBACLUTCH-27-VWEMBANYAMA1, KXNBACLUTCH-27-TYOUNG3, KXNBACLUTCH-27-TMAXEY0, KXNBACLUTCH-27-THERRO11
- sample fields: `{"ticker": "KXNBACLUTCH-27-ZWILLIAMSON1", "event_ticker": "KXNBACLUTCH-27", "market_type": "binary", "title": "Pro Basketball Clutch Player of the Year: Zion Williamson", "yes_sub_title": "Zion Williamson", "no_sub_title": "Zion Williamson", "strike_type": "structured", "custom_strike": {"basketball_player": "220527f6-f6e9-46b3-92b4-ccd8e37ad577"}, "status": "active", "open_time": "2026-10-06T01:00:00Z", "close_time": "2027-07-07T14:00:00Z", "expected_expiration_time": "2027-07-30T14:00:00Z", "result": "", "rules_primary": "If Zion Williamson wins the Pro Basketball Clutch Player of the Year i`

### KXNBACOACHOUT — Pro Basketball Coaches Out

### KXNBACOMPETE — Pro Basketball Player to Compete

### KXNBACONF — NBA Conference to Win the Championship
- (2) Will any team from the NAME win the NAME in the #-# season?
- samples: KXNBACONF-27-WEST, KXNBACONF-27-EAST
- sample fields: `{"ticker": "KXNBACONF-27-WEST", "event_ticker": "KXNBACONF-27", "market_type": "binary", "title": "Will any team from the Western Conference win the Pro Basketball Finals in the 2026-27 season?", "subtitle": "Western Conference", "yes_sub_title": "Western Conference", "no_sub_title": "Western Conference", "strike_type": "structured", "custom_strike": {"basketball_team": "c198939d-6b0f-440b-a303-a31b4782204d"}, "status": "active", "open_time": "2026-07-05T18:25:00Z", "close_time": "2027-07-08T14:00:00Z", "expected_expiration_time": "2027-07-01T14:00:00Z", "result": "", "rules_primary": "If any `

### KXNBACOTM — NBA Coach of the Month
- (26) NAME of the Month in October/November: NAME
- (1) NAME of the Month in October/November: JJ Redick
- (1) NAME of the Month in October/November: Jordi Fernández
- (1) NAME of the Month in October/November: J.B. Bickerstaff
- (1) NAME of the Month in October/November: Darko Rajaković
- samples: KXNBACOTM-NOV26WEST-WHAR, KXNBACOTM-NOV26WEST-TLUE, KXNBACOTM-NOV26WEST-TIIS, KXNBACOTM-NOV26WEST-SKER, KXNBACOTM-NOV26WEST-MNOR, KXNBACOTM-NOV26WEST-MJOH
- sample fields: `{"ticker": "KXNBACOTM-NOV26WEST-WHAR", "event_ticker": "KXNBACOTM-NOV26WEST", "market_type": "binary", "title": "Western Conference Coach of the Month in October/November: Will Hardy", "yes_sub_title": "Will Hardy", "no_sub_title": "Will Hardy", "strike_type": "custom", "custom_strike": {"Entity": "Will Hardy"}, "status": "active", "open_time": "2026-10-21T20:00:00Z", "close_time": "2026-12-08T04:59:59Z", "expected_expiration_time": "2026-12-01T04:59:59Z", "result": "", "rules_primary": "If Will Hardy wins the Western Conference Coach of the Month award in October/November of the 2026-27 Pro B`

### KXNBACOY — NBA Coach of the Year
- (26) NAME of the Year: NAME
- (1) NAME of the Year: JJ Redick
- (1) NAME of the Year: Jordi Fernández
- (1) NAME of the Year: J.B. Bickerstaff
- (1) NAME of the Year: Darko Rajaković
- samples: KXNBACOY-27-WHAR, KXNBACOY-27-TSPL, KXNBACOY-27-TLUE, KXNBACOY-27-TJEN, KXNBACOY-27-TIIS, KXNBACOY-27-SSWE
- sample fields: `{"ticker": "KXNBACOY-27-WHAR", "event_ticker": "KXNBACOY-27", "market_type": "binary", "title": "Pro Basketball Coach of the Year: Will Hardy", "yes_sub_title": "Will Hardy", "no_sub_title": "Will Hardy", "strike_type": "custom", "custom_strike": {"Person": "Will Hardy"}, "status": "active", "open_time": "2026-09-09T17:00:00Z", "close_time": "2027-08-02T14:00:00Z", "expected_expiration_time": "2027-08-25T14:00:00Z", "result": "", "rules_primary": "If Will Hardy wins the Pro Basketball Coach of the Year award in the 2026-27 season, then the market resolves to Yes."}`

### KXNBACUP — Pro Basketball Cup Champion
- (28) NAME be the Emirates # NAME champion in the #-# season?
- (1) NAME L be the Emirates # NAME champion in the #-# season?
- (1) NAME C be the Emirates # NAME champion in the #-# season?
- samples: KXNBACUP-26-WAS, KXNBACUP-26-UTA, KXNBACUP-26-TOR, KXNBACUP-26-SAS, KXNBACUP-26-SAC, KXNBACUP-26-POR
- sample fields: `{"ticker": "KXNBACUP-26-WAS", "event_ticker": "KXNBACUP-26", "market_type": "binary", "title": "Will Washington be the Emirates 2026 Pro Basketball Cup champion in the 2026-27 season?", "yes_sub_title": "Washington", "no_sub_title": "Washington", "strike_type": "structured", "custom_strike": {"basketball_team": "0464e75c-8bc8-4f18-9ee2-577832b889d6"}, "status": "active", "open_time": "2026-07-01T18:00:00Z", "close_time": "2027-02-14T15:00:00Z", "expected_expiration_time": "2027-01-31T15:00:00Z", "result": "", "rules_primary": "If Washington is the Emirates 2026 Pro Basketball Cup champion in t`

### KXNBACUP1STTEAM — NBA Cup All-Tournament Team
- (73) NAME: NAME
- (2) NAME: NAME.
- (1) NAME: Zach LaVine
- (1) NAME: VJ Edgecombe
- (1) NAME: RJ Barrett
- (1) NAME: OG Anunoby
- (1) NAME: Nikola Jokić
- (1) NAME: LeBron James
- samples: KXNBACUP1STTEAM-26-ZWILLIAMSON1, KXNBACUP1STTEAM-26-ZLAVINE8, KXNBACUP1STTEAM-26-VWEMBANYAMA1, KXNBACUP1STTEAM-26-VEDGECOMBE77, KXNBACUP1STTEAM-26-TYOUNG3, KXNBACUP1STTEAM-26-TMAXEY0
- sample fields: `{"ticker": "KXNBACUP1STTEAM-26-ZWILLIAMSON1", "event_ticker": "KXNBACUP1STTEAM-26", "market_type": "binary", "title": "Pro Basketball Cup All-Tournament Team Selection: Zion Williamson", "yes_sub_title": "Zion Williamson", "no_sub_title": "Zion Williamson", "strike_type": "structured", "custom_strike": {"basketball_player": "220527f6-f6e9-46b3-92b4-ccd8e37ad577"}, "status": "active", "open_time": "2026-10-06T17:15:00Z", "close_time": "2027-01-07T15:00:00Z", "expected_expiration_time": "2026-12-31T15:00:00Z", "result": "", "rules_primary": "If Zion Williamson is selected to the Pro Basketball C`

### KXNBACUPGROUP — NBA Cup Group Winner
- (3) NAME B Winner: NAME
- (2) NAME C Winner: NAME
- (1) NAME C Winner: Sacramento
- (1) NAME C Winner: Portland
- (1) NAME C Winner: NAME L
- (1) NAME B Winner: Minnesota
- (1) NAME B Winner: Memphis
- (1) NAME B Winner: NAME C
- samples: KXNBACUPGROUP-26WESTC-SAS, KXNBACUPGROUP-26WESTC-SAC, KXNBACUPGROUP-26WESTC-POR, KXNBACUPGROUP-26WESTC-LAL, KXNBACUPGROUP-26WESTC-GSW, KXNBACUPGROUP-26WESTB-OKC
- sample fields: `{"ticker": "KXNBACUPGROUP-26WESTC-SAS", "event_ticker": "KXNBACUPGROUP-26WESTC", "market_type": "binary", "title": "Pro Basketball Cup West Group C Winner: San Antonio", "yes_sub_title": "San Antonio", "no_sub_title": "San Antonio", "strike_type": "structured", "custom_strike": {"basketball_team": "ad36c3e8-4194-4e63-920f-7c50f46191a6"}, "status": "active", "open_time": "2026-10-06T16:00:00Z", "close_time": "2026-12-05T15:00:00Z", "expected_expiration_time": "2026-11-28T15:00:00Z", "result": "", "rules_primary": "If San Antonio wins West Group C in the Pro Basketball Cup in the 2026-27 Pro Bas`

### KXNBACUPGROUPWIN — NBA Cup Group to Win
- (2) Group to Win: NAME C
- (2) Group to Win: NAME B
- (2) Group to Win: NAME A
- samples: KXNBACUPGROUPWIN-26-WESTC, KXNBACUPGROUPWIN-26-WESTB, KXNBACUPGROUPWIN-26-WESTA, KXNBACUPGROUPWIN-26-EASTC, KXNBACUPGROUPWIN-26-EASTB, KXNBACUPGROUPWIN-26-EASTA
- sample fields: `{"ticker": "KXNBACUPGROUPWIN-26-WESTC", "event_ticker": "KXNBACUPGROUPWIN-26", "market_type": "binary", "title": "Group to Win: West Group C", "yes_sub_title": "West Group C", "no_sub_title": "West Group C", "strike_type": "custom", "custom_strike": {"Entity": "West Group C"}, "status": "active", "open_time": "2026-10-07T21:00:00Z", "close_time": "2026-12-27T15:00:00Z", "expected_expiration_time": "2026-12-20T15:00:00Z", "result": "", "rules_primary": "If any team in West Group C wins the Pro Basketball Cup in the 2026-27 Pro Basketball season, then the market resolves to Yes."}`

### KXNBACUPMVP — NBA Cup Tournament MVP
- (65) NAME MVP: NAME
- (1) NAME MVP: VJ Edgecombe
- (1) NAME MVP: RJ Barrett
- (1) NAME MVP: OG Anunoby
- (1) NAME MVP: Nikola Jokić
- (1) NAME MVP: LeBron James
- (1) NAME MVP: Luka Dončić
- (1) NAME MVP: LaMelo Ball
- samples: KXNBACUPMVP-27-ZWILLIAMSON1, KXNBACUPMVP-27-VWEMBANYAMA1, KXNBACUPMVP-27-VEDGECOMBE77, KXNBACUPMVP-27-TYOUNG3, KXNBACUPMVP-27-TMAXEY0, KXNBACUPMVP-27-THALIBURTON0
- sample fields: `{"ticker": "KXNBACUPMVP-27-ZWILLIAMSON1", "event_ticker": "KXNBACUPMVP-27", "market_type": "binary", "title": "Pro Basketball Cup Tournament MVP: Zion Williamson", "yes_sub_title": "Zion Williamson", "no_sub_title": "Zion Williamson", "strike_type": "structured", "custom_strike": {"basketball_player": "220527f6-f6e9-46b3-92b4-ccd8e37ad577"}, "status": "active", "open_time": "2026-09-09T19:00:00Z", "close_time": "2027-02-18T15:00:00Z", "expected_expiration_time": "2027-03-13T15:00:00Z", "result": "", "rules_primary": "If Zion Williamson wins the Pro Basketball Cup Tournament MVP in the 2026-27 `

### KXNBACUPQUAL — Pro Basketball Cup Qualifiers
- (56) NAME qualify for the NAME in the #-# NAME season?
- (2) NAME L qualify for the NAME in the #-# NAME season?
- (2) NAME C qualify for the NAME in the #-# NAME season?
- samples: KXNBACUPQUAL-26FIN-WAS, KXNBACUPQUAL-26FIN-UTA, KXNBACUPQUAL-26FIN-TOR, KXNBACUPQUAL-26FIN-SAS, KXNBACUPQUAL-26FIN-SAC, KXNBACUPQUAL-26FIN-POR
- sample fields: `{"ticker": "KXNBACUPQUAL-26FIN-WAS", "event_ticker": "KXNBACUPQUAL-26FIN", "market_type": "binary", "title": "Will Washington qualify for the Pro Basketball Cup Finals in the 2026-27 Pro Basketball season?", "yes_sub_title": "Washington", "no_sub_title": "Washington", "strike_type": "structured", "custom_strike": {"basketball_team": "0464e75c-8bc8-4f18-9ee2-577832b889d6"}, "status": "active", "open_time": "2026-07-02T01:00:00Z", "close_time": "2027-02-14T15:00:00Z", "expected_expiration_time": "2027-01-31T15:00:00Z", "result": "", "rules_primary": "If Washington qualify for the Finals of the E`

### KXNBADPOTM — NBA Defensive Player of the Month
- (98) NAME of the Month in October/November: NAME
- (5) NAME of the Month in October/November: NAME.
- (2) NAME of the Month in October/November: NAME III
- (2) NAME of the Month in October/November: NAME II
- (1) NAME of the Month in October/November: P.J. Washington
- (1) NAME of the Month in October/November: Nikola Jokić
- (1) NAME of the Month in October/November: Luka Dončić
- (1) NAME of the Month in October/November: Kristaps Porziņģis
- samples: KXNBADPOTM-NOV26WEST-ZEDEY14, KXNBADPOTM-NOV26WEST-YMISSI21, KXNBADPOTM-NOV26WEST-WKESSLER14, KXNBADPOTM-NOV26WEST-VWEMBANYAMA1, KXNBADPOTM-NOV26WEST-TMURPHY25, KXNBADPOTM-NOV26WEST-TEASON17
- sample fields: `{"ticker": "KXNBADPOTM-NOV26WEST-ZEDEY14", "event_ticker": "KXNBADPOTM-NOV26WEST", "market_type": "binary", "title": "Western Conference Defensive Player of the Month in October/November: Zach Edey", "yes_sub_title": "Zach Edey", "no_sub_title": "Zach Edey", "strike_type": "structured", "custom_strike": {"basketball_player": "fe5a04a5-0dc7-4373-baf9-36c4bced83a5"}, "status": "active", "open_time": "2026-10-21T20:00:00Z", "close_time": "2026-12-08T04:59:59Z", "expected_expiration_time": "2026-12-01T04:59:59Z", "result": "", "rules_primary": "If Zach Edey wins the Western Conference Defensive Pl`

### KXNBADPOY — NBA Defensive Player of the Year
- (42) NAME win NAME of the Year?
- (2) NAME. win NAME of the Year?
- (1) NAME/NAME win NAME of the Year?
- (1) Will OG Anunoby win NAME of the Year?
- (1) Will LeBron James win NAME of the Year?
- (1) NAME McDaniels win NAME of the Year?
- samples: KXNBADPOY-27-ZEDEY14, KXNBADPOY-27-WKESSLER24, KXNBADPOY-27-WCARTER34, KXNBADPOY-27-VWEMBANYAMA1, KXNBADPOY-27-TIE, KXNBADPOY-27-TEASON17
- sample fields: `{"ticker": "KXNBADPOY-27-ZEDEY14", "event_ticker": "KXNBADPOY-27", "market_type": "binary", "title": "Will Zach Edey win Defensive Player of the Year?", "yes_sub_title": "Zach Edey", "no_sub_title": "Zach Edey", "strike_type": "structured", "custom_strike": {"basketball_player": "fe5a04a5-0dc7-4373-baf9-36c4bced83a5"}, "status": "active", "open_time": "2026-06-15T22:23:00Z", "close_time": "2028-06-30T22:23:00Z", "expected_expiration_time": "2027-07-31T22:23:00Z", "result": "", "rules_primary": "If Zach Edey wins Pro Basketball Defensive Player of the Year in the 2026-27 season, then the market`

### KXNBADRAFT1 — NBA Draft First Pick

### KXNBADRAFT10 — NBA Draft Tenth Pick

### KXNBADRAFT2 — NBA Draft Second Pick

### KXNBADRAFT3 — NBA Draft Third Pick

### KXNBADRAFT4 — NBA Draft Fourth Pick

### KXNBADRAFT5 — NBA Draft Fifth Pick

### KXNBADRAFT6 — NBA Draft Sixth Pick

### KXNBADRAFT7 — NBA Draft Seventh Pick

### KXNBADRAFT8 — NBA Draft Eighth Pick

### KXNBADRAFT9 — NBA Draft Ninth Pick

### KXNBADRAFTCAT — Pro Basketball Draft Category

### KXNBADRAFTCOMP — Pro Basketball Draft Comparison

### KXNBADRAFTCONF — Pro Basketball Players Drafted by Conference

### KXNBADRAFTINT — Pro Basketball International Players Drafted

### KXNBADRAFTMATCHUP — Pro Basketball Draft Matchup

### KXNBADRAFTOU — Pro Basketball Players Draft Position

### KXNBADRAFTPICK — Pro Basketball Draft Pick
- (11) NAME be picked #st in the NAME?
- (1) NAME II be picked #st in the NAME?
- (1) NAME. be picked #st in the NAME?
- (1) NAME McCoy be picked #st in the NAME?
- (1) NAME III be picked #st in the NAME?
- samples: KXNBADRAFTPICK-27-1-TSTO, KXNBADRAFTPICK-27-1-THAU, KXNBADRAFTPICK-27-1-PNGO, KXNBADRAFTPICK-27-1-MKRI, KXNBADRAFTPICK-27-1-JSMI, KXNBADRAFTPICK-27-1-HYIM
- sample fields: `{"ticker": "KXNBADRAFTPICK-27-1-TSTO", "event_ticker": "KXNBADRAFTPICK-27-1", "market_type": "binary", "title": "Will Tyran Stokes be picked 1st in the Pro Basketball Draft?", "subtitle": "Tyran Stokes", "yes_sub_title": "Tyran Stokes", "no_sub_title": "Tyran Stokes", "strike_type": "custom", "custom_strike": {"Count": "1", "Person": "Tyran Stokes"}, "status": "active", "open_time": "2026-06-25T14:56:00Z", "close_time": "2027-07-08T14:00:00Z", "expected_expiration_time": "2027-07-01T14:00:00Z", "result": "", "rules_primary": "If Tyran Stokes is selected as the 1st overall pick in the 2027 Pro `

### KXNBADRAFTTEAM — Pro Basketball Team to Draft

### KXNBADRAFTTOP — Pro Basketball Top Draft

### KXNBADRAFTTOP10 — NBA Draft Top 10 Pick

### KXNBADRAFTTOP15 — NBA Draft Top 15 Pick

### KXNBADRAFTTOP20 — NBA Draft Top 20 Pick

### KXNBADRAFTTOP25 — NBA Draft Top 25 Pick

### KXNBADRAFTTOP30 — NBA Draft Top 30 Pick

### KXNBADRAFTTOP5 — NBA Draft Top 5 Pick

### KXNBADRAFTTRADE — Pro Basketball Draft Trade

### KXNBAEAST — Pro Basketball Eastern Conference Champion
- (15) NAME win the NAME in the #-# season?
- samples: KXNBAEAST-27-WAS, KXNBAEAST-27-TOR, KXNBAEAST-27-PHI, KXNBAEAST-27-ORL, KXNBAEAST-27-NYK, KXNBAEAST-27-MIL
- sample fields: `{"ticker": "KXNBAEAST-27-WAS", "event_ticker": "KXNBAEAST-27", "market_type": "binary", "title": "Will Washington win the Pro Basketball Eastern Conference Finals in the 2026-27 season?", "yes_sub_title": "Washington", "no_sub_title": "Washington", "strike_type": "structured", "custom_strike": {"basketball_team": "0464e75c-8bc8-4f18-9ee2-577832b889d6"}, "status": "active", "open_time": "2026-06-16T20:00:00Z", "close_time": "2029-06-29T14:00:00Z", "expected_expiration_time": "2027-06-30T14:00:00Z", "result": "", "rules_primary": "If Washington wins the Pro Basketball Eastern Conference Finals i`

### KXNBAEAST1SEED — NBA Eastern Conference 1 Seed
- (15) NAME be the ## seed in the NAME at the conclusion of the #-# NAME regular season?
- samples: KXNBAEAST1SEED-26-WAS, KXNBAEAST1SEED-26-TOR, KXNBAEAST1SEED-26-PHI, KXNBAEAST1SEED-26-ORL, KXNBAEAST1SEED-26-NYK, KXNBAEAST1SEED-26-MIL
- sample fields: `{"ticker": "KXNBAEAST1SEED-26-WAS", "event_ticker": "KXNBAEAST1SEED-26", "market_type": "binary", "title": "Will Washington be the #1 seed in the Eastern Conference at the conclusion of the 2026-27 Pro Basketball regular season?", "subtitle": "Washington", "yes_sub_title": "Washington", "no_sub_title": "Washington", "strike_type": "structured", "custom_strike": {"basketball_team": "0464e75c-8bc8-4f18-9ee2-577832b889d6"}, "status": "active", "open_time": "2026-06-16T21:00:00Z", "close_time": "2027-06-15T14:00:00Z", "expected_expiration_time": "2027-06-01T14:00:00Z", "result": "", "rules_primary`

### KXNBAECFQUAL — NBA Eastern Conference Finals Qualifiers
- (1) Washington qualifies for the NAME
- (1) Toronto qualifies for the NAME
- (1) Philadelphia qualifies for the NAME
- (1) Orlando qualifies for the NAME
- (1) NAME qualifies for the NAME
- (1) Milwaukee qualifies for the NAME
- (1) Miami qualifies for the NAME
- (1) Indiana qualifies for the NAME
- samples: KXNBAECFQUAL-27-WAS, KXNBAECFQUAL-27-TOR, KXNBAECFQUAL-27-PHI, KXNBAECFQUAL-27-ORL, KXNBAECFQUAL-27-NYK, KXNBAECFQUAL-27-MIL
- sample fields: `{"ticker": "KXNBAECFQUAL-27-WAS", "event_ticker": "KXNBAECFQUAL-27", "market_type": "binary", "title": "Washington qualifies for the Eastern Conference Finals", "yes_sub_title": "Washington", "no_sub_title": "Washington", "strike_type": "structured", "custom_strike": {"basketball_team": "0464e75c-8bc8-4f18-9ee2-577832b889d6"}, "status": "active", "open_time": "2026-09-17T22:00:00Z", "close_time": "2027-07-07T14:00:00Z", "expected_expiration_time": "2027-06-30T14:00:00Z", "result": "", "rules_primary": "If Washington qualifies for the Eastern Conference Finals in the 2026-27 Pro Basketball seas`

### KXNBAEFINMVP — NBA Eastern Conference Finals MVP
- (42) NAME MVP: NAME
- (1) NAME MVP: VJ Edgecombe
- (1) NAME MVP: RJ Barrett
- (1) NAME MVP: OG Anunoby
- (1) NAME MVP: Nikola Vučević
- (1) NAME MVP: NAME.
- (1) NAME MVP: LeBron James
- (1) NAME MVP: CJ McCollum
- samples: KXNBAEFINMVP-27-VEDGECOMBE77, KXNBAEFINMVP-27-TYOUNG3, KXNBAEFINMVP-27-TMAXEY0, KXNBAEFINMVP-27-THERRO11, KXNBAEFINMVP-27-THALIBURTON0, KXNBAEFINMVP-27-SBARNES4
- sample fields: `{"ticker": "KXNBAEFINMVP-27-VEDGECOMBE77", "event_ticker": "KXNBAEFINMVP-27", "market_type": "binary", "title": "Pro Basketball Eastern Conference Finals MVP: VJ Edgecombe", "yes_sub_title": "VJ Edgecombe", "no_sub_title": "VJ Edgecombe", "strike_type": "structured", "custom_strike": {"basketball_player": "21e37a74-41d2-4c09-9f05-9b20a14ba88b"}, "status": "active", "open_time": "2026-09-09T19:00:00Z", "close_time": "2027-08-07T14:00:00Z", "expected_expiration_time": "2027-08-30T14:00:00Z", "result": "", "rules_primary": "If VJ Edgecombe wins the Pro Basketball Eastern Conference Finals MVP in `

### KXNBAESCALATOR3PT — NBA Player Threes Escalator

### KXNBAESCALATORPTS — NBA Player Points Escalator

### KXNBAEUROPEANNOUNCE — NBA Europe Inaugural Season Being Announced
- (2) NBA Europe's inaugural season announced before Jan #, #
- (1) NBA Europe's inaugural season announced before Oct #, #
- (1) NBA Europe's inaugural season announced before Jul #, #
- (1) NBA Europe's inaugural season announced before Apr #, #
- samples: KXNBAEUROPEANNOUNCE-26-28JAN01, KXNBAEUROPEANNOUNCE-26-27OCT01, KXNBAEUROPEANNOUNCE-26-27JUL01, KXNBAEUROPEANNOUNCE-26-27JAN01, KXNBAEUROPEANNOUNCE-26-27APR01
- sample fields: `{"ticker": "KXNBAEUROPEANNOUNCE-26-28JAN01", "event_ticker": "KXNBAEUROPEANNOUNCE-26", "market_type": "binary", "title": "NBA Europe's inaugural season announced before Jan 1, 2028", "yes_sub_title": "Before Jan 1, 2028", "no_sub_title": "Before Jan 1, 2028", "strike_type": "custom", "custom_strike": {"Date": "Jan 1, 2028"}, "status": "active", "open_time": "2026-10-09T16:01:00Z", "close_time": "2028-01-01T04:59:00Z", "expected_expiration_time": "2030-01-01T15:00:00Z", "result": "", "rules_primary": "If the National Basketball Association (NBA) officially announces a firm decision to establish`

### KXNBAEXEC — NBA Executive of the Year
- (53) NAME of the Year: NAME
- (1) NAME of the Year: R.C. Buford
- (1) NAME of the Year: Pete D'Alessandro
- (1) NAME of the Year: NAME.
- samples: KXNBAEXEC-27-ZKLE, KXNBAEXEC-27-WWES, KXNBAEXEC-27-WDAW, KXNBAEXEC-27-TWU, KXNBAEXEC-27-TWEA, KXNBAEXEC-27-TRED
- sample fields: `{"ticker": "KXNBAEXEC-27-ZKLE", "event_ticker": "KXNBAEXEC-27", "market_type": "binary", "title": "Pro Basketball Executive of the Year: Zach Kleiman", "yes_sub_title": "Zach Kleiman", "no_sub_title": "Zach Kleiman", "strike_type": "custom", "custom_strike": {"Person": "Zach Kleiman"}, "status": "active", "open_time": "2026-10-06T15:55:00Z", "close_time": "2027-07-07T14:00:00Z", "expected_expiration_time": "2027-07-30T14:00:00Z", "result": "", "rules_primary": "If Zach Kleiman wins the Pro Basketball Executive of the Year in the 2026-27 season, then the market resolves to Yes."}`

### KXNBAEXTENSION — NBA Player Contract Extension

### KXNBAFINALSEXACT — Pro Basketball Championship Series Score

### KXNBAFINALSMENTION — NBA Finals

### KXNBAFINALSMVP — Finals MVP

### KXNBAFINALSOUTCOME — NBA Finals Outcome
- (7) NAME: NAME beats NAME
- (4) NAME: NAME beats Toronto
- (4) NAME: NAME beats Philadelphia
- (4) NAME: NAME beats Miami
- (4) NAME: NAME beats Indiana
- (4) NAME: NAME beats Detroit
- (4) NAME: NAME beats Cleveland
- (4) NAME: NAME beats Boston
- samples: KXNBAFINALSOUTCOME-27-WASSAS, KXNBAFINALSOUTCOME-27-WASOKC, KXNBAFINALSOUTCOME-27-WASMIN, KXNBAFINALSOUTCOME-27-WASLAL, KXNBAFINALSOUTCOME-27-WASGSW, KXNBAFINALSOUTCOME-27-WASDEN
- sample fields: `{"ticker": "KXNBAFINALSOUTCOME-27-WASSAS", "event_ticker": "KXNBAFINALSOUTCOME-27", "market_type": "binary", "title": "Pro Basketball Finals: Washington beats San Antonio", "yes_sub_title": "Washington beats San Antonio", "no_sub_title": "Washington beats San Antonio", "strike_type": "custom", "custom_strike": {"Outcome": "Washington beats San Antonio"}, "status": "active", "open_time": "2026-10-20T20:30:00Z", "close_time": "2027-08-07T14:00:00Z", "expected_expiration_time": "2027-07-31T14:00:00Z", "result": "", "rules_primary": "If the Washington Pro Basketball team defeats San Antonio in the`

### KXNBAFINALSPRICE — NBA Finals Ticket Price

### KXNBAFINALSVIEWER — NBA finals viewership

### KXNBAFINALSVIEWERGAME7 — NBA finals viewership

### KXNBAFINBLOWOUT — Pro Basketball Finals Blowout

### KXNBAFINMVP — NBA Finals MVP
- (64) NAME MVP: NAME
- (1) NAME MVP: VJ Edgecombe
- (1) NAME MVP: RJ Barrett
- (1) NAME MVP: OG Anunoby
- (1) NAME MVP: Nikola Jokić
- (1) NAME MVP: LeBron James
- (1) NAME MVP: Luka Dončić
- (1) NAME MVP: LaMelo Ball
- samples: KXNBAFINMVP-27-ZWILLIAMSON1, KXNBAFINMVP-27-VWEMBANYAMA1, KXNBAFINMVP-27-VEDGECOMBE77, KXNBAFINMVP-27-TYOUNG3, KXNBAFINMVP-27-TMAXEY0, KXNBAFINMVP-27-THALIBURTON0
- sample fields: `{"ticker": "KXNBAFINMVP-27-ZWILLIAMSON1", "event_ticker": "KXNBAFINMVP-27", "market_type": "binary", "title": "Pro Basketball Finals MVP: Zion Williamson", "yes_sub_title": "Zion Williamson", "no_sub_title": "Zion Williamson", "strike_type": "structured", "custom_strike": {"basketball_player": "220527f6-f6e9-46b3-92b4-ccd8e37ad577"}, "status": "active", "open_time": "2026-09-09T19:00:00Z", "close_time": "2027-08-08T14:00:00Z", "expected_expiration_time": "2027-08-31T14:00:00Z", "result": "", "rules_primary": "If Zion Williamson wins the Pro Basketball Finals MVP in the 2026-27 season, then the`

### KXNBAFIRST50PTS — First NBA Player to Score 50 Points

### KXNBAFIRSTBASKET — Pro Basketball First Basket

### KXNBAFIRSTOPPONENT — Pro Basketball First Opponent of the Season

### KXNBAFRANCHISECOST — NBA Franchise Cost
- (7) NAME expansion franchise price above $# billion
- samples: KXNBAFRANCHISECOST-31DEC26LV-B9, KXNBAFRANCHISECOST-31DEC26LV-B8, KXNBAFRANCHISECOST-31DEC26LV-B15, KXNBAFRANCHISECOST-31DEC26LV-B13, KXNBAFRANCHISECOST-31DEC26LV-B12, KXNBAFRANCHISECOST-31DEC26LV-B11
- sample fields: `{"ticker": "KXNBAFRANCHISECOST-31DEC26LV-B9", "event_ticker": "KXNBAFRANCHISECOST-31DEC26LV", "market_type": "binary", "title": "Las Vegas Pro Basketball expansion franchise price above $9 billion", "yes_sub_title": "Above $9 billion", "no_sub_title": "Above $9 billion", "strike_type": "greater", "floor_strike": 9000000000, "status": "active", "open_time": "2026-09-30T15:30:00Z", "close_time": "2027-01-07T15:00:00Z", "expected_expiration_time": "2027-01-01T04:59:59Z", "result": "", "rules_primary": "If a qualifying sale of the Las Vegas NBA expansion franchise is publicly announced after Issua`

### KXNBAFRANCHISEOWNER — NBA Franchise Owner
- (3) NAME expansion franchise controlling owner
- samples: KXNBAFRANCHISEOWNER-01JAN28LV-LAURIE, KXNBAFRANCHISEOWNER-01JAN28LV-FOLCOL, KXNBAFRANCHISEOWNER-01JAN28LV-APOLAS
- sample fields: `{"ticker": "KXNBAFRANCHISEOWNER-01JAN28LV-LAURIE", "event_ticker": "KXNBAFRANCHISEOWNER-01JAN28LV", "market_type": "binary", "title": "Las Vegas Pro Basketball expansion franchise controlling owner", "yes_sub_title": "Nancy Walton Laurie and/or Bill Laurie", "no_sub_title": "Nancy Walton Laurie and/or Bill Laurie", "strike_type": "custom", "custom_strike": {"buyer": "Nancy Walton Laurie and/or Bill Laurie"}, "status": "active", "open_time": "2026-09-30T15:45:00Z", "close_time": "2028-01-01T04:59:00Z", "expected_expiration_time": "2028-01-01T05:00:00Z", "result": "", "rules_primary": "If Nancy `

### KXNBAFTM — NBA Player Free Throws Made

### KXNBAGAME — NBA Game
- (11) NAME wins
- (3) Houston wins
- (3) Minnesota wins
- (3) Cleveland wins
- (3) Atlanta wins
- (3) Philadelphia wins
- (3) Charlotte wins
- (2) Milwaukee wins
- samples: KXNBAGAME-26OCT31OKCHOU-OKC, KXNBAGAME-26OCT31OKCHOU-HOU, KXNBAGAME-26OCT31MINSAS-SAS, KXNBAGAME-26OCT31MINSAS-MIN, KXNBAGAME-26OCT31CLEMIL-MIL, KXNBAGAME-26OCT31CLEMIL-CLE
- sample fields: `{"ticker": "KXNBAGAME-26OCT31OKCHOU-OKC", "event_ticker": "KXNBAGAME-26OCT31OKCHOU", "market_type": "binary", "title": "Oklahoma City wins", "yes_sub_title": "Oklahoma City", "no_sub_title": "Oklahoma City", "strike_type": "structured", "custom_strike": {"basketball_team": "a85f6eca-2f3b-4f61-83ab-8d049f59ce2c"}, "status": "active", "open_time": "2026-10-28T00:36:22.599919Z", "close_time": "2026-11-03T00:30:00Z", "expected_expiration_time": "2026-11-01T03:30:00Z", "result": "", "rules_primary": "If Oklahoma City wins the Oklahoma City vs Houston Pro Basketball game originally scheduled for Oct`

### KXNBAGAME7 — NBA Series that Go to a Game 7

### KXNBAGAMEHIGHSCORE — NBA Highest Scoring Game of the Season
- (9) Highest scoring game: #+ points
- samples: KXNBAGAMEHIGHSCORE-27-325, KXNBAGAMEHIGHSCORE-27-320, KXNBAGAMEHIGHSCORE-27-315, KXNBAGAMEHIGHSCORE-27-310, KXNBAGAMEHIGHSCORE-27-305, KXNBAGAMEHIGHSCORE-27-300
- sample fields: `{"ticker": "KXNBAGAMEHIGHSCORE-27-325", "event_ticker": "KXNBAGAMEHIGHSCORE-27", "market_type": "binary", "title": "Highest scoring game: 325+ points", "yes_sub_title": "325+ points", "no_sub_title": "325+ points", "strike_type": "greater_or_equal", "floor_strike": 325, "status": "active", "open_time": "2026-10-08T19:30:00Z", "close_time": "2027-07-07T14:00:00Z", "expected_expiration_time": "2027-06-30T14:00:00Z", "result": "", "rules_primary": "If there is a game (including overtime) with at least 325 total points scored in the 2026-27 Pro Basketball regular season, then the market resolves t`

### KXNBAGAMES — NBA games

### KXNBAGAMESPECIALS — Pro Basketball Game Specials
- (5) Will any player record #+ points in any individual game during the #-# NAME regular season?
- (3) Will any player record #+ rebounds in any individual game during the #-# NAME regular season?
- (3) Will any player record #+ three pointers in any individual game during the #-# NAME regular season?
- (2) Will any player record #+ steals in any individual game during the #-# NAME regular season?
- (2) Will any player record #+ points in a single quarter in any individual game during the #-# NAME regular season?
- (2) Will any player record #+ points and a triple-double in any individual game during the #-# NAME regular season?
- (2) Will any player record #+ blocks in any individual game during the #-# NAME regular season?
- (2) Will any player record #+ assists in any individual game during the #-# NAME regular season?
- samples: KXNBAGAMESPECIALS-27-STLBLK15, KXNBAGAMESPECIALS-27-STL8, KXNBAGAMESPECIALS-27-STL5BLK5, KXNBAGAMESPECIALS-27-STL10, KXNBAGAMESPECIALS-27-REB30, KXNBAGAMESPECIALS-27-REB25
- sample fields: `{"ticker": "KXNBAGAMESPECIALS-27-STLBLK15", "event_ticker": "KXNBAGAMESPECIALS-27", "market_type": "binary", "title": "Will any player record 15+ steals and blocks combined in any individual game during the 2026-27 Pro Basketball regular season?", "yes_sub_title": "Any player to record 15+ steals and blocks combined in a game", "no_sub_title": "Any player to record 15+ steals and blocks combined in a game", "strike_type": "custom", "custom_strike": {"Entity": "Any player", "Stat": "15+ steals and blocks combined"}, "status": "active", "open_time": "2026-07-28T20:00:00Z", "close_time": "2027-05`

### KXNBAH2H3PT — NBA Head-to-Head Three Pointers

### KXNBAH2HBENCHPTS — NBA Head-to-Head Bench Points

### KXNBAH2HPRA — NBA Head-to-Head Points, Rebounds and Assists

### KXNBAH2HPTS — NBA Head-to-Head Points

### KXNBAH2HTEAM3PT — NBA H2H Team Three Pointers

### KXNBAH2HWINS — NBA Head to Head Win Total
- (6) NAME to record more wins than NAME in the #-# NAME regular season
- (2) NAME to record more wins than Philadelphia in the #-# NAME regular season
- (2) Philadelphia to record more wins than NAME in the #-# NAME regular season
- (1) Minnesota to record more wins than Denver in the #-# NAME regular season
- (1) Denver to record more wins than Minnesota in the #-# NAME regular season
- (1) NAME L to record more wins than NAME in the #-# NAME regular season
- (1) NAME to record more wins than NAME L in the #-# NAME regular season
- (1) Dallas to record more wins than Charlotte in the #-# NAME regular season
- samples: KXNBAH2HWINS-27PHISAS-SAS, KXNBAH2HWINS-27PHISAS-PHI, KXNBAH2HWINS-27NYKOKC-OKC, KXNBAH2HWINS-27NYKOKC-NYK, KXNBAH2HWINS-27NYKSAS-SAS, KXNBAH2HWINS-27NYKSAS-NYK
- sample fields: `{"ticker": "KXNBAH2HWINS-27PHISAS-SAS", "event_ticker": "KXNBAH2HWINS-27PHISAS", "market_type": "binary", "title": "San Antonio to record more wins than Philadelphia in the 2026-27 Pro Basketball regular season", "yes_sub_title": "San Antonio", "no_sub_title": "San Antonio", "strike_type": "structured", "custom_strike": {"basketball_team": "ad36c3e8-4194-4e63-920f-7c50f46191a6"}, "status": "active", "open_time": "2026-10-01T23:20:00Z", "close_time": "2027-07-03T14:00:00Z", "expected_expiration_time": "2027-07-01T14:00:00Z", "result": "", "rules_primary": "If San Antonio records more wins than `

### KXNBAHALLOFFAME — Pro Basketball Hall of Fame
- (13) NAME be announced as an inductee for the # NAME of Fame class?
- (13) NAME be announced as a finalist for the # NAME of Fame class?
- (1) Will LaMarcus Aldridge be announced as an inductee for the # NAME of Fame class?
- (1) Will LaMarcus Aldridge be announced as a finalist for the # NAME of Fame class?
- samples: KXNBAHALLOFFAME-27INDUCTEES-TSTO, KXNBAHALLOFFAME-27INDUCTEES-SMAR, KXNBAHALLOFFAME-27INDUCTEES-RWAL, KXNBAHALLOFFAME-27INDUCTEES-LALD, KXNBAHALLOFFAME-27INDUCTEES-KSAM, KXNBAHALLOFFAME-27INDUCTEES-JWAL
- sample fields: `{"ticker": "KXNBAHALLOFFAME-27INDUCTEES-TSTO", "event_ticker": "KXNBAHALLOFFAME-27INDUCTEES", "market_type": "binary", "title": "Will Terry Stotts be announced as an inductee for the 2027 Pro Basketball Hall of Fame class?", "yes_sub_title": "Terry Stotts", "no_sub_title": "Terry Stotts", "strike_type": "custom", "custom_strike": {"Participant": "Terry Stotts"}, "status": "active", "open_time": "2026-06-18T00:00:00Z", "close_time": "2028-03-31T14:00:00Z", "expected_expiration_time": "2027-04-01T14:00:00Z", "result": "", "rules_primary": "If Terry Stotts is announced as an inductee for the 2027`

### KXNBAHIGHESTSCORING — NBA Player with the Highest Scoring Game

### KXNBAHOMECLINCH — Pro Basketball Series Winner to Clinch at Home

### KXNBAHUSTLE — NBA Hustle Award
- (66) NAME: NAME
- (4) NAME: NAME.
- (1) NAME: VJ Edgecombe
- (1) NAME: P.J. Washington
- (1) NAME: OG Anunoby
- (1) NAME: Jaden McDaniels
- (1) NAME: Donte DiVincenzo
- samples: KXNBAHUSTLE-27-ZEDEY14, KXNBAHUSTLE-27-WKESSLER14, KXNBAHUSTLE-27-WCARTER34, KXNBAHUSTLE-27-VWEMBANYAMA1, KXNBAHUSTLE-27-VEDGECOMBE77, KXNBAHUSTLE-27-TEASON17
- sample fields: `{"ticker": "KXNBAHUSTLE-27-ZEDEY14", "event_ticker": "KXNBAHUSTLE-27", "market_type": "binary", "title": "Pro Basketball Hustle Award: Zach Edey", "yes_sub_title": "Zach Edey", "no_sub_title": "Zach Edey", "strike_type": "structured", "custom_strike": {"basketball_player": "fe5a04a5-0dc7-4373-baf9-36c4bced83a5"}, "status": "active", "open_time": "2026-10-06T15:15:00Z", "close_time": "2027-07-07T14:00:00Z", "expected_expiration_time": "2027-07-30T14:00:00Z", "result": "", "rules_primary": "If Zach Edey wins the Pro Basketball Hustle Award in the 2026-27 season, then the market resolves to Yes."`

### KXNBAJOINCONF — Pro Basketball Join Conference
- (1) Minnesota to join the NAME before the #-# regular season
- samples: KXNBAJOINCONF-29MIN-Y
- sample fields: `{"ticker": "KXNBAJOINCONF-29MIN-Y", "event_ticker": "KXNBAJOINCONF-29MIN", "market_type": "binary", "title": "Minnesota to join the Eastern Conference before the 2028-29 regular season", "yes_sub_title": "Minnesota to join the Eastern Conference", "no_sub_title": "Minnesota to join the Eastern Conference", "status": "active", "open_time": "2026-09-03T00:58:00Z", "close_time": "2029-01-08T15:00:00Z", "expected_expiration_time": "2029-01-01T15:00:00Z", "result": "", "rules_primary": "If the Minnesota Pro Basketball team joins the Eastern Conference before the 2028-29 Pro Basketball regular seaso`

### KXNBALADDER3PT — NBA Player Threes Ladder

### KXNBALADDERPTS — NBA Player Points Ladder

### KXNBALASTTOLOSE — NBA Last Undefeated Team
- (1) Last undefeated team: Portland
- (1) Last undefeated team: NAME
- (1) Last undefeated team: Memphis
- (1) Last undefeated team: Houston
- samples: KXNBALASTTOLOSE-27-POR, KXNBALASTTOLOSE-27-OKC, KXNBALASTTOLOSE-27-MEM, KXNBALASTTOLOSE-27-HOU
- sample fields: `{"ticker": "KXNBALASTTOLOSE-27-POR", "event_ticker": "KXNBALASTTOLOSE-27", "market_type": "binary", "title": "Last undefeated team: Portland", "yes_sub_title": "Portland", "no_sub_title": "Portland", "strike_type": "structured", "custom_strike": {"basketball_team": "2229b01e-68eb-46ad-adf4-71a9533c84fc"}, "status": "active", "open_time": "2026-10-16T19:15:00Z", "close_time": "2027-07-08T14:00:00Z", "expected_expiration_time": "2027-07-01T14:00:00Z", "result": "", "rules_primary": "If Portland is the last remaining undefeated team in the 2026-27 Pro Basketball regular season, then the market re`

### KXNBALASVEGAS — Las Vegas NBA team

### KXNBALOTTERY — NBA Draft Lottery Picks

### KXNBALOTTERYODDS — NBA Lottery Winner Odds

### KXNBAMATCHUP — NBA Matchup
- (14) NAME: NAME vs NAME
- (9) NAME: Milwaukee vs NAME
- (9) NAME: Miami vs NAME
- (9) NAME: Indiana vs NAME
- (9) NAME: Detroit vs NAME
- (9) NAME: Cleveland vs NAME
- (9) NAME: Chicago vs NAME
- (9) NAME: Charlotte vs NAME
- samples: KXNBAMATCHUP-26CUPFIN-WASUTA, KXNBAMATCHUP-26CUPFIN-WASSAS, KXNBAMATCHUP-26CUPFIN-WASSAC, KXNBAMATCHUP-26CUPFIN-WASPOR, KXNBAMATCHUP-26CUPFIN-WASPHX, KXNBAMATCHUP-26CUPFIN-WASOKC
- sample fields: `{"ticker": "KXNBAMATCHUP-26CUPFIN-WASUTA", "event_ticker": "KXNBAMATCHUP-26CUPFIN", "market_type": "binary", "title": "Pro Basketball Cup Finals Matchup: Washington vs Utah", "yes_sub_title": "Washington vs Utah", "no_sub_title": "Washington vs Utah", "strike_type": "custom", "custom_strike": {"Matchup": "Washington vs Utah"}, "status": "active", "open_time": "2026-10-23T02:00:00Z", "close_time": "2027-01-07T15:00:00Z", "expected_expiration_time": "2026-12-31T15:00:00Z", "result": "", "rules_primary": "If Washington vs Utah is confirmed to be the matchup in the Pro Basketball Cup Finals in the`

### KXNBAMENTION — NBA Mention

### KXNBAMIMP — NBA Most Improved Player
- (41) NAME: NAME
- (2) NAME: NAME.
- (1) NAME: VJ Edgecombe
- (1) NAME: Kel'el Ware
- (1) NAME: Jaden McDaniels
- (1) NAME: Egor Dëmin
- samples: KXNBAMIMP-27-LMILLER11, KXNBAMIMP-27-KELLIS1, KXNBAMIMP-27-ZEDEY14, KXNBAMIMP-27-WKESSLER14, KXNBAMIMP-27-VEDGECOMBE77, KXNBAMIMP-27-TSHANNON4
- sample fields: `{"ticker": "KXNBAMIMP-27-LMILLER11", "event_ticker": "KXNBAMIMP-27", "market_type": "binary", "title": "Pro Basketball Most Improved Player: Leonard Miller", "yes_sub_title": "Leonard Miller", "no_sub_title": "Leonard Miller", "strike_type": "structured", "custom_strike": {"basketball_player": "b20be183-d7e6-4970-ad6f-04ff489eb0d9"}, "status": "active", "open_time": "2026-10-20T17:15:00Z", "close_time": "2027-07-08T14:00:00Z", "expected_expiration_time": "2027-07-31T14:00:00Z", "result": "", "rules_primary": "If Leonard Miller wins the Pro Basketball Most Improved Player award in the 2026-27 s`

### KXNBAMOSTWINS — Pro Basketball Highest Win Total
- (4) Will any NAME team win at least # games in the #-# regular season?
- samples: KXNBAMOSTWINS-27-72, KXNBAMOSTWINS-27-70, KXNBAMOSTWINS-27-67, KXNBAMOSTWINS-27-65
- sample fields: `{"ticker": "KXNBAMOSTWINS-27-72", "event_ticker": "KXNBAMOSTWINS-27", "market_type": "binary", "title": "Will any Pro Basketball team win at least 72 games in the 2026-27 regular season?", "yes_sub_title": "72+ wins", "no_sub_title": "72+ wins", "strike_type": "greater_or_equal", "floor_strike": 72, "status": "active", "open_time": "2026-07-30T16:50:00Z", "close_time": "2027-05-08T14:00:00Z", "expected_expiration_time": "2027-05-01T14:00:00Z", "result": "", "rules_primary": "If any Pro Basketball team wins at least 72 games in the 2026-27 Pro Basketball regular season, then the market resolves`

### KXNBAMVP — NBA MVP
- (46) NAME win MVP?
- (1) NAME MVP: NAME
- (1) Will VJ Edgecombe win MVP?
- (1) NAME/NAME win MVP?
- (1) Will OG Anunoby win MVP?
- (1) NAME Jokić win MVP?
- (1) Will LeBron James win MVP?
- (1) Will LaMelo Ball win MVP?
- samples: KXNBAMVP-27-KLEONARD2, KXNBAMVP-27-DAVDIJA8, KXNBAMVP-27-ZWILLIAMSON1, KXNBAMVP-27-VWEMBANYAMA1, KXNBAMVP-27-VEDGECOMBE77, KXNBAMVP-27-TYOUNG3
- sample fields: `{"ticker": "KXNBAMVP-27-KLEONARD2", "event_ticker": "KXNBAMVP-27", "market_type": "binary", "title": "Pro Basketball MVP: Kawhi Leonard", "yes_sub_title": "Kawhi Leonard", "no_sub_title": "Kawhi Leonard", "strike_type": "structured", "custom_strike": {"basketball_player": "f2bfdc6c-0d84-4736-ba44-8cdbc196e0b3"}, "status": "active", "open_time": "2026-10-21T14:00:00Z", "close_time": "2028-06-30T14:00:00Z", "expected_expiration_time": "2027-07-31T14:00:00Z", "result": "", "rules_primary": "If Kawhi Leonard wins the Pro Basketball MVP in the 2026-27 season, then the market resolves to Yes."}`

### KXNBAMVPDPOY — Pro Basketball Player to Win MVP and DPOY
- (1) NAME win the NAME (MVP) and NAME of the Year (DPOY) awards in the #-# NAME season?
- samples: KXNBAMVPDPOY-27-VWEMBANYAMA1
- sample fields: `{"ticker": "KXNBAMVPDPOY-27-VWEMBANYAMA1", "event_ticker": "KXNBAMVPDPOY-27", "market_type": "binary", "title": "Will Victor Wembanyama win the Most Valuable Player (MVP) and Defensive Player of the Year (DPOY) awards in the 2026-27 Pro Basketball season?", "yes_sub_title": "Victor Wembanyama to win MVP and DPOY in 2026-27 season", "no_sub_title": "Victor Wembanyama to win MVP and DPOY in 2026-27 season", "strike_type": "structured", "custom_strike": {"basketball_player": "b269496a-6cdf-466d-aa1a-c648b20591ae"}, "status": "active", "open_time": "2026-06-01T01:00:00Z", "close_time": "2027-07-04`

### KXNBANEWCHAMP — NBA First-Time Champion

### KXNBANEWCHAMPION — Pro Basketball New Champion
- (1) Will a team who has not won a championship in the previous # seasons (#-# through #-#) win the championship in the #-# NAME season?
- samples: KXNBANEWCHAMPION-27-Y
- sample fields: `{"ticker": "KXNBANEWCHAMPION-27-Y", "event_ticker": "KXNBANEWCHAMPION-27", "market_type": "binary", "title": "Will a team who has not won a championship in the previous 8 seasons (2018-19 through 2025-26) win the championship in the 2026-27 Pro Basketball season?", "subtitle": "9th straight different Pro Basketball champion", "yes_sub_title": "9th straight different Pro Basketball champion", "no_sub_title": "9th straight different Pro Basketball champion", "status": "active", "open_time": "2026-06-22T22:00:00Z", "close_time": "2027-07-08T14:00:00Z", "expected_expiration_time": "2027-07-01T14:0`

### KXNBANEXTCONTRACT — Pro Basketball Next Contract Size

### KXNBANEXTGOVERNOR — Pro Basketball Next Governor
- (5) NAME to be the next governor of NAME L before Jan #, #
- (1) Any other person (excluding NAME) to be the next governor of NAME L before Jan #, #
- samples: KXNBANEXTGOVERNOR-27JAN01LAL-TBOE, KXNBANEXTGOVERNOR-27JAN01LAL-OTHER, KXNBANEXTGOVERNOR-27JAN01LAL-MWAL, KXNBANEXTGOVERNOR-27JAN01LAL-LRAM, KXNBANEXTGOVERNOR-27JAN01LAL-JKUS, KXNBANEXTGOVERNOR-27JAN01LAL-BIGE
- sample fields: `{"ticker": "KXNBANEXTGOVERNOR-27JAN01LAL-TBOE", "event_ticker": "KXNBANEXTGOVERNOR-27JAN01LAL", "market_type": "binary", "title": "Todd Boehly to be the next governor of Los Angeles L before Jan 1, 2027", "subtitle": "Todd Boehly", "yes_sub_title": "Todd Boehly", "no_sub_title": "Todd Boehly", "strike_type": "custom", "custom_strike": {"Entity": "Todd Boehly"}, "status": "active", "open_time": "2026-08-18T22:00:12Z", "close_time": "2027-01-08T05:00:00Z", "expected_expiration_time": "2027-01-08T05:00:00Z", "result": "", "rules_primary": "If Todd Boehly formally holds the position of team govern`

### KXNBANEXTTEAM — Pro Basketball Next Team
- (30) NAME's next team before Feb #, #: NAME
- (15) NAME' next team before Feb #, #: NAME
- (10) NAME.'s next team before Feb #, #: NAME
- (6) NAME's next team before Feb #, #: Washington
- (6) NAME's next team before Feb #, #: Utah
- (6) NAME's next team before Feb #, #: Toronto
- (6) NAME's next team before Feb #, #: Sacramento
- (6) NAME's next team before Feb #, #: Portland
- samples: KXNBANEXTTEAM-27PGEORGE13-WAS, KXNBANEXTTEAM-27PGEORGE13-UTA, KXNBANEXTTEAM-27PGEORGE13-TOR, KXNBANEXTTEAM-27PGEORGE13-SAS, KXNBANEXTTEAM-27PGEORGE13-SAC, KXNBANEXTTEAM-27PGEORGE13-POR
- sample fields: `{"ticker": "KXNBANEXTTEAM-27PGEORGE13-WAS", "event_ticker": "KXNBANEXTTEAM-27PGEORGE13", "market_type": "binary", "title": "Paul George's next team before Feb 12, 2027: Washington", "yes_sub_title": "Washington", "no_sub_title": "Washington", "strike_type": "structured", "custom_strike": {"basketball_team": "0464e75c-8bc8-4f18-9ee2-577832b889d6"}, "status": "active", "open_time": "2026-10-23T22:50:00Z", "close_time": "2027-02-12T04:59:00Z", "expected_expiration_time": "2027-02-12T15:00:00Z", "result": "", "rules_primary": "If Paul George's \nnext team is the Washington Pro Basketball team\n be`

### KXNBANEXTTEAMCONF — Pro Basketball Next Team Conference

### KXNBANEXTTEAMOUTLET — Pro Basketball Outlet to Announce Next Team

### KXNBANHL — NBA + NHL Champion Combo

### KXNBANORTHWEST — Pro Basketball Northwest Division Winner
- (5) NAME be the NAME winner in the #-# season?
- samples: KXNBANORTHWEST-26-UTA, KXNBANORTHWEST-26-POR, KXNBANORTHWEST-26-OKC, KXNBANORTHWEST-26-MIN, KXNBANORTHWEST-26-DEN
- sample fields: `{"ticker": "KXNBANORTHWEST-26-UTA", "event_ticker": "KXNBANORTHWEST-26", "market_type": "binary", "title": "Will Utah be the Northwest Division winner in the 2026-27 season?", "yes_sub_title": "Utah", "no_sub_title": "Utah", "strike_type": "structured", "custom_strike": {"basketball_team": "6f60dfb1-fda1-423f-b76f-67e9d24b9644"}, "status": "active", "open_time": "2026-07-01T21:00:00Z", "close_time": "2027-07-14T14:00:00Z", "expected_expiration_time": "2027-06-30T14:00:00Z", "result": "", "rules_primary": "If Utah is the Northwest Division winner in the 2026-27 Pro Basketball season, then the m`

### KXNBAONE3PT — NBA Players to Make One Three
- (7) NAME to make at least # three-pointer
- samples: KXNBAONE3PT-27-WKESSLER14, KXNBAONE3PT-27-RGOBERT27, KXNBAONE3PT-27-MROBINSON4, KXNBAONE3PT-27-IHARTENSTEIN55, KXNBAONE3PT-27-DGAFFORD21, KXNBAONE3PT-27-BJAMES9
- sample fields: `{"ticker": "KXNBAONE3PT-27-WKESSLER14", "event_ticker": "KXNBAONE3PT-27", "market_type": "binary", "title": "Walker Kessler to make at least 1 three-pointer", "yes_sub_title": "Walker Kessler", "no_sub_title": "Walker Kessler", "strike_type": "greater", "floor_strike": 0.5, "custom_strike": {"basketball_player": "fa781441-5e6a-4a3d-9a3f-0af9ee263945"}, "status": "active", "open_time": "2026-10-16T17:00:00Z", "close_time": "2027-07-07T14:00:00Z", "expected_expiration_time": "2027-06-30T14:00:00Z", "result": "", "rules_primary": "If Walker Kessler makes at least 1 three-pointer in the 2026-27 Pr`

### KXNBAOT — NBA Overtime
- (14) Game goes to overtime
- samples: KXNBAOT-26OCT29MEMPOR-1, KXNBAOT-26OCT29SACNOP-1, KXNBAOT-26OCT28LALLAC-1, KXNBAOT-26OCT28OKCDAL-1, KXNBAOT-26OCT28SASUTA-1, KXNBAOT-26OCT28DENNOP-1
- sample fields: `{"ticker": "KXNBAOT-26OCT29MEMPOR-1", "event_ticker": "KXNBAOT-26OCT29MEMPOR", "market_type": "binary", "title": "Game goes to overtime", "yes_sub_title": "Game goes to overtime", "no_sub_title": "Game goes to overtime", "strike_type": "greater", "floor_strike": 0.5, "status": "active", "open_time": "2026-10-28T02:06:07.073132Z", "close_time": "2026-11-01T02:00:00Z", "expected_expiration_time": "2026-10-30T05:00:00Z", "result": "", "rules_primary": "If at least 1 overtime period is played in the Memphis vs Portland Pro Basketball game originally scheduled for Oct 29, 2026, then the market reso`

### KXNBAOVERTIME — NBA Overtime

### KXNBAPA — Pro Basketball Player Points + Assists

### KXNBAPACIFIC — Pro Basketball Pacific Division Winner
- (3) NAME be the NAME winner in the #-# season?
- (1) NAME L be the NAME winner in the #-# season?
- (1) NAME C be the NAME winner in the #-# season?
- samples: KXNBAPACIFIC-26-SAC, KXNBAPACIFIC-26-PHX, KXNBAPACIFIC-26-LAL, KXNBAPACIFIC-26-LAC, KXNBAPACIFIC-26-GSW
- sample fields: `{"ticker": "KXNBAPACIFIC-26-SAC", "event_ticker": "KXNBAPACIFIC-26", "market_type": "binary", "title": "Will Sacramento be the Pacific Division winner in the 2026-27 season?", "yes_sub_title": "Sacramento", "no_sub_title": "Sacramento", "strike_type": "structured", "custom_strike": {"basketball_team": "ab9e2e9a-3243-41b6-a291-95f4d9c6edf7"}, "status": "active", "open_time": "2026-07-01T21:00:00Z", "close_time": "2027-07-14T14:00:00Z", "expected_expiration_time": "2027-06-30T14:00:00Z", "result": "", "rules_primary": "If Sacramento is the Pacific Division winner in the 2026-27 Pro Basketball se`

### KXNBAPARTNERSHIP — NBA Player Partnership Deal

### KXNBAPIADVANCE — NBA Play-In Team to Advance

### KXNBAPICKTRADE — Pro Basketball Pick Trade

### KXNBAPLAYERDEAL — Next Pro Basketball Brand Deal

### KXNBAPLAYERHIGHSCORE — NBA Highest Scoring Performance in Regular Season
- (17) NAME highest-scoring performance: #+ points
- (11) Highest scoring performance: #+ points
- (1) Nikola Jokić highest-scoring performance: #+ points
- (1) LeBron James highest-scoring performance: #+ points
- (1) Luka Dončić highest-scoring performance: #+ points
- (1) AJ Dybantsa highest-scoring performance: #+ points
- samples: KXNBAPLAYERHIGHSCORE-27-VWEMBANYAMA1-48, KXNBAPLAYERHIGHSCORE-27-TMAXEY0-50, KXNBAPLAYERHIGHSCORE-27-SGILGEOUSALEXANDER2-52, KXNBAPLAYERHIGHSCORE-27-SCURRY30-50, KXNBAPLAYERHIGHSCORE-27-NJOKIC15-47, KXNBAPLAYERHIGHSCORE-27-LJAMES23-45
- sample fields: `{"ticker": "KXNBAPLAYERHIGHSCORE-27-VWEMBANYAMA1-48", "event_ticker": "KXNBAPLAYERHIGHSCORE-27", "market_type": "binary", "title": "Victor Wembanyama highest-scoring performance: 48+ points", "yes_sub_title": "Victor Wembanyama: 48+ points", "no_sub_title": "Victor Wembanyama: 48+ points", "strike_type": "greater", "floor_strike": 47.5, "custom_strike": {"basketball_player": "b269496a-6cdf-466d-aa1a-c648b20591ae"}, "status": "active", "open_time": "2026-10-08T21:00:00Z", "close_time": "2027-07-07T14:00:00Z", "expected_expiration_time": "2027-06-30T14:00:00Z", "result": "", "rules_primary": "If`

### KXNBAPLAYERSPECIALS — Pro Basketball Player Specials

### KXNBAPLAYIN — Which Team Will Make the Play-In Tournament
- (28) NAME qualify for the NAME?
- (1) NAME L qualify for the NAME?
- (1) NAME C qualify for the NAME?
- samples: KXNBAPLAYIN-27WEST-UTA, KXNBAPLAYIN-27WEST-SAS, KXNBAPLAYIN-27WEST-SAC, KXNBAPLAYIN-27WEST-POR, KXNBAPLAYIN-27WEST-PHX, KXNBAPLAYIN-27WEST-OKC
- sample fields: `{"ticker": "KXNBAPLAYIN-27WEST-UTA", "event_ticker": "KXNBAPLAYIN-27WEST", "market_type": "binary", "title": "Will Utah qualify for the Pro Basketball Western Conference Play-In Tournament?", "yes_sub_title": "Utah", "no_sub_title": "Utah", "strike_type": "structured", "custom_strike": {"basketball_team": "6f60dfb1-fda1-423f-b76f-67e9d24b9644"}, "status": "active", "open_time": "2026-06-16T00:00:00Z", "close_time": "2027-06-15T14:00:00Z", "expected_expiration_time": "2027-06-01T14:00:00Z", "result": "", "rules_primary": "If Utah qualifies for the Pro Basketball Western Conference Play-In Tourn`

### KXNBAPLAYOFF — Pro Basketball Playoff Qualifier
- (30) NAME
- samples: KXNBAPLAYOFF-27-WAS, KXNBAPLAYOFF-27-UTA, KXNBAPLAYOFF-27-TOR, KXNBAPLAYOFF-27-SAS, KXNBAPLAYOFF-27-SAC, KXNBAPLAYOFF-27-POR
- sample fields: `{"ticker": "KXNBAPLAYOFF-27-WAS", "event_ticker": "KXNBAPLAYOFF-27", "market_type": "binary", "title": "Pro Basketball Playoff Qualifiers", "yes_sub_title": "Washington", "no_sub_title": "Washington", "strike_type": "structured", "custom_strike": {"basketball_team": "0464e75c-8bc8-4f18-9ee2-577832b889d6"}, "status": "active", "open_time": "2026-06-15T23:00:00Z", "close_time": "2027-06-01T14:00:00Z", "expected_expiration_time": "2027-06-01T14:00:00Z", "result": "", "rules_primary": "If Washington qualifies for the Pro Basketball Playoffs in the 2026-27 season, then the market resolves to Yes."}`

### KXNBAPLAYOFF3D — NBA Playoff Triple-Double

### KXNBAPLAYOFFPTS — NBA Playoffs Player Points

### KXNBAPLAYOFFWINS — NBA Playoff Wins by Team

### KXNBAPLAYTOGETHER — Pro Basketball Players to Play Together

### KXNBAPOLOSE — Pro Basketball Playoff Losses

### KXNBAPOSTASREC — NBA Best Record Post-All-Star Break
- (5) Best record going into the NAME break: NAME
- (1) Best record going into the NAME break: Washington
- (1) Best record going into the NAME break: Utah
- (1) Best record going into the NAME break: Toronto
- (1) Best record going into the NAME break: Sacramento
- (1) Best record going into the NAME break: Portland
- (1) Best record going into the NAME break: Phoenix
- (1) Best record going into the NAME break: Philadelphia
- samples: KXNBAPOSTASREC-27-WAS, KXNBAPOSTASREC-27-UTA, KXNBAPOSTASREC-27-TOR, KXNBAPOSTASREC-27-SAS, KXNBAPOSTASREC-27-SAC, KXNBAPOSTASREC-27-POR
- sample fields: `{"ticker": "KXNBAPOSTASREC-27-WAS", "event_ticker": "KXNBAPOSTASREC-27", "market_type": "binary", "title": "Best record going into the All-Star break: Washington", "yes_sub_title": "Washington", "no_sub_title": "Washington", "strike_type": "structured", "custom_strike": {"basketball_team": "0464e75c-8bc8-4f18-9ee2-577832b889d6"}, "status": "active", "open_time": "2026-10-08T18:30:00Z", "close_time": "2027-03-08T15:00:00Z", "expected_expiration_time": "2027-03-01T15:00:00Z", "result": "", "rules_primary": "If the Washington Pro Basketball team has the best winning percentage from the beginning `

### KXNBAPOTM — NBA Player of the Month
- (98) NAME of the Month in October/November: NAME
- (4) NAME of the Month in October/November: NAME.
- (1) NAME of the Month in October/November: Zach LaVine
- (1) NAME of the Month in October/November: NAME III
- (1) NAME of the Month in October/November: P.J. Washington
- (1) NAME of the Month in October/November: Nikola Jokić
- (1) NAME of the Month in October/November: Luka Dončić
- (1) NAME of the Month in October/November: LaMelo Ball
- samples: KXNBAPOTM-NOV26WEST-ZWILLIAMSON1, KXNBAPOTM-NOV26WEST-ZLAVINE8, KXNBAPOTM-NOV26WEST-VWEMBANYAMA1, KXNBAPOTM-NOV26WEST-TMURPHY25, KXNBAPOTM-NOV26WEST-TJEROME2, KXNBAPOTM-NOV26WEST-SSHARPE17
- sample fields: `{"ticker": "KXNBAPOTM-NOV26WEST-ZWILLIAMSON1", "event_ticker": "KXNBAPOTM-NOV26WEST", "market_type": "binary", "title": "Western Conference Player of the Month in October/November: Zion Williamson", "yes_sub_title": "Zion Williamson", "no_sub_title": "Zion Williamson", "strike_type": "structured", "custom_strike": {"basketball_player": "220527f6-f6e9-46b3-92b4-ccd8e37ad577"}, "status": "active", "open_time": "2026-10-21T20:00:00Z", "close_time": "2026-12-08T04:59:59Z", "expected_expiration_time": "2026-12-01T04:59:59Z", "result": "", "rules_primary": "If Zion Williamson wins the Western Confer`

### KXNBAPR — Pro Basketball Player Points + Rebounds

### KXNBAPRA — NBA Player Points + Rebounds + Assists
- (165) NAME: #+ points, rebounds, and assists
- (3) Luka Dončić: #+ points, rebounds, and assists
- (3) LaMelo Ball: #+ points, rebounds, and assists
- (3) OG Anunoby: #+ points, rebounds, and assists
- (3) RJ Barrett: #+ points, rebounds, and assists
- (3) LeBron James: #+ points, rebounds, and assists
- (3) VJ Edgecombe: #+ points, rebounds, and assists
- (3) DeMar DeRozan: #+ points, rebounds, and assists
- samples: KXNBAPRA-26OCT28PHIIND-INDPSIAKAM43-45, KXNBAPRA-26OCT28DENNOP-NOPZWILLIAMSON1-20, KXNBAPRA-26OCT28LALLAC-LACDGARLAND10-45, KXNBAPRA-26OCT28CHADET-CHABMILLER24-25, KXNBAPRA-26OCT28HOUMIL-HOUATHOMPSON1-40, KXNBAPRA-26OCT28WASCLE-CLEEMOBLEY4-40
- sample fields: `{"ticker": "KXNBAPRA-26OCT28PHIIND-INDPSIAKAM43-45", "event_ticker": "KXNBAPRA-26OCT28PHIIND", "market_type": "binary", "title": "Pascal Siakam: 45+ points, rebounds, and assists", "yes_sub_title": "Pascal Siakam: 45+", "no_sub_title": "Pascal Siakam: 45+", "strike_type": "greater", "floor_strike": 44.5, "custom_strike": {"basketball_player": "1c8ae3bd-88ae-4511-8622-9f9ac7d73de0", "basketball_team": "d059bab2-9fb5-42dd-8038-5a12474300ce"}, "status": "active", "open_time": "2026-10-28T18:20:41Z", "close_time": "2026-10-30T23:00:00Z", "expected_expiration_time": "2026-10-29T05:00:00Z", "result"`

### KXNBAPREPACK2ML — 2 ML Basketball Combo

### KXNBAPREPACK3ML — 3ML Basketball Combo

### KXNBAPTS — NBA Player Points
- (379) NAME: #+ points
- (16) NAME.: #+ points
- (4) Jared McCain: #+ points
- (4) Luka Dončić: #+ points
- (4) DeMar DeRozan: #+ points
- (4) P.J. Washington: #+ points
- (4) LaMelo Ball: #+ points
- (4) Jaden McDaniels: #+ points
- samples: KXNBAPTS-26OCT28CHADET-DETKHUERTERSF-15, KXNBAPTS-26OCT28CHADET-DETKHUERTERSF-10, KXNBAPTS-26OCT28CHADET-CHAGALLEN8-25, KXNBAPTS-26OCT28CHADET-CHAGALLEN8-20, KXNBAPTS-26OCT28SASUTA-UTAABAILEY19-25, KXNBAPTS-26OCT28CHADET-CHAGALLEN8-15
- sample fields: `{"ticker": "KXNBAPTS-26OCT28CHADET-DETKHUERTERSF-15", "event_ticker": "KXNBAPTS-26OCT28CHADET", "market_type": "binary", "title": "Kevin Huerter: 15+ points", "yes_sub_title": "Kevin Huerter: 15+", "no_sub_title": "Kevin Huerter: 15+", "strike_type": "greater", "floor_strike": 14.5, "custom_strike": {"basketball_player": "33c2e858-9265-47f1-b048-fbab4a62f9c8", "basketball_team": "65569528-1888-40aa-9d62-2b0e8142a9b4"}, "status": "active", "open_time": "2026-10-28T19:21:06Z", "close_time": "2026-10-30T23:00:00Z", "expected_expiration_time": "2026-10-29T05:00:00Z", "result": "", "rules_primary":`

### KXNBAPTSALLGAMES — Pro Basketball Points in Every Game

### KXNBAPTSLEADER — NBA Game Points Leader
- (102) NAME: Points leader
- (5) NAME.: Points leader
- (1) Jared McCain: Points leader
- (1) P.J. Washington: Points leader
- (1) Nikola Jokić: Points leader
- (1) LaMelo Ball: Points leader
- (1) Jaden McDaniels: Points leader
- (1) NAME III: Points leader
- samples: KXNBAPTSLEADER-26OCT28CHADET-CHAGALLEN8, KXNBAPTSLEADER-26OCT28MIAATL-ATLJLANDALE31, KXNBAPTSLEADER-26OCT28WASCLE-WASTJOHNSON12, KXNBAPTSLEADER-26OCT28WASCLE-WASDAYTON8, KXNBAPTSLEADER-26OCT28PHIIND-INDKOUBRE10, KXNBAPTSLEADER-26OCT28OKCDAL-OKCKWILLIAMSSF
- sample fields: `{"ticker": "KXNBAPTSLEADER-26OCT28CHADET-CHAGALLEN8", "event_ticker": "KXNBAPTSLEADER-26OCT28CHADET", "market_type": "binary", "title": "Grayson Allen: Points leader", "yes_sub_title": "Grayson Allen", "no_sub_title": "Grayson Allen", "strike_type": "structured", "custom_strike": {"basketball_player": "07a246cd-1c40-42f1-849e-58fbd7696c30", "basketball_team": "7c980c51-fa76-4571-b165-242b2a00f3a1"}, "status": "active", "open_time": "2026-10-28T19:40:41Z", "close_time": "2026-10-30T23:00:00Z", "expected_expiration_time": "2026-10-29T05:00:00Z", "result": "", "rules_primary": "If Grayson Allen r`

### KXNBAPTSPROT — NBA Player Points Protected
- (379) NAME: #+ points
- (16) NAME.: #+ points
- (4) Jared McCain: #+ points
- (4) Luka Dončić: #+ points
- (4) DeMar DeRozan: #+ points
- (4) P.J. Washington: #+ points
- (4) LaMelo Ball: #+ points
- (4) Jaden McDaniels: #+ points
- samples: KXNBAPTSPROT-26OCT28CHADET-CHARKALKBRENNER11-15, KXNBAPTSPROT-26OCT28CHADET-CHARKALKBRENNER11-10, KXNBAPTSPROT-26OCT28WASCLE-WASBCOULIBALY0-15, KXNBAPTSPROT-26OCT28WASCLE-WASBCOULIBALY0-10, KXNBAPTSPROT-26OCT28SASUTA-UTAABAILEY19-25, KXNBAPTSPROT-26OCT28CHADET-DETKHUERTERSF-15
- sample fields: `{"ticker": "KXNBAPTSPROT-26OCT28CHADET-CHARKALKBRENNER11-15", "event_ticker": "KXNBAPTSPROT-26OCT28CHADET", "market_type": "binary", "title": "Ryan Kalkbrenner: 15+ points", "yes_sub_title": "Ryan Kalkbrenner: 15+", "no_sub_title": "Ryan Kalkbrenner: 15+", "strike_type": "greater", "floor_strike": 14.5, "custom_strike": {"basketball_player": "88d788fe-5410-40c4-9193-b0e3e1af4f1f", "basketball_team": "7c980c51-fa76-4571-b165-242b2a00f3a1"}, "status": "active", "open_time": "2026-10-28T19:51:33Z", "close_time": "2026-10-30T23:00:00Z", "expected_expiration_time": "2026-10-29T05:00:00Z", "result":`

### KXNBARA — Pro Basketball Player Rebounds + Assists

### KXNBARACE — NBA Race to Points
- (18) NAME reaches # points first
- (3) Portland reaches # points first
- (3) Memphis reaches # points first
- (3) Sacramento reaches # points first
- (3) NAME L reaches # points first
- (3) NAME C reaches # points first
- (3) Dallas reaches # points first
- (3) Utah reaches # points first
- samples: KXNBARACE-26OCT29MEMPOR-30-POR, KXNBARACE-26OCT29MEMPOR-30-MEM, KXNBARACE-26OCT29MEMPOR-20-POR, KXNBARACE-26OCT29MEMPOR-20-MEM, KXNBARACE-26OCT29MEMPOR-10-POR, KXNBARACE-26OCT29MEMPOR-10-MEM
- sample fields: `{"ticker": "KXNBARACE-26OCT29MEMPOR-30-POR", "event_ticker": "KXNBARACE-26OCT29MEMPOR-30", "market_type": "binary", "title": "Portland reaches 30 points first", "yes_sub_title": "Portland", "no_sub_title": "Portland", "strike_type": "custom", "custom_strike": {"Points": "30", "basketball_team": "2229b01e-68eb-46ad-adf4-71a9533c84fc"}, "status": "active", "open_time": "2026-10-28T02:06:07.073132Z", "close_time": "2026-11-01T02:00:00Z", "expected_expiration_time": "2026-10-30T05:00:00Z", "result": "", "rules_primary": "If Portland is the first to score 30 points in the Memphis vs Portland Pro Ba`

### KXNBAREB — NBA Player Rebounds
- (426) NAME: #+ rebounds
- (18) NAME.: #+ rebounds
- (6) Moussa Diabaté: #+ rebounds
- (5) Luka Dončić: #+ rebounds
- (5) P.J. Washington: #+ rebounds
- (5) Kel'el Ware: #+ rebounds
- (5) Nikola Jokić: #+ rebounds
- (4) Jared McCain: #+ rebounds
- samples: KXNBAREB-26OCT28CHADET-CHARKALKBRENNER11-8, KXNBAREB-26OCT28CHADET-CHARKALKBRENNER11-6, KXNBAREB-26OCT28CHADET-CHARKALKBRENNER11-4, KXNBAREB-26OCT28CHADET-CHARKALKBRENNER11-2, KXNBAREB-26OCT28CHADET-CHAGALLEN8-6, KXNBAREB-26OCT28CHADET-CHAGALLEN8-4
- sample fields: `{"ticker": "KXNBAREB-26OCT28CHADET-CHARKALKBRENNER11-8", "event_ticker": "KXNBAREB-26OCT28CHADET", "market_type": "binary", "title": "Ryan Kalkbrenner: 8+ rebounds", "yes_sub_title": "Ryan Kalkbrenner: 8+", "no_sub_title": "Ryan Kalkbrenner: 8+", "strike_type": "greater", "floor_strike": 7.5, "custom_strike": {"basketball_player": "88d788fe-5410-40c4-9193-b0e3e1af4f1f", "basketball_team": "7c980c51-fa76-4571-b165-242b2a00f3a1"}, "status": "active", "open_time": "2026-10-28T19:21:06Z", "close_time": "2026-10-30T23:00:00Z", "expected_expiration_time": "2026-10-29T05:00:00Z", "result": "", "rules`

### KXNBAREBPROT — NBA Player Rebounds Protected
- (426) NAME: #+ rebounds
- (18) NAME.: #+ rebounds
- (6) Moussa Diabaté: #+ rebounds
- (5) Luka Dončić: #+ rebounds
- (5) P.J. Washington: #+ rebounds
- (5) Kel'el Ware: #+ rebounds
- (5) Nikola Jokić: #+ rebounds
- (4) Jared McCain: #+ rebounds
- samples: KXNBAREBPROT-26OCT28WASCLE-WASBCOULIBALY0-8, KXNBAREBPROT-26OCT28WASCLE-WASBCOULIBALY0-6, KXNBAREBPROT-26OCT28WASCLE-WASBCOULIBALY0-4, KXNBAREBPROT-26OCT28WASCLE-WASBCOULIBALY0-2, KXNBAREBPROT-26OCT28CHADET-CHARKALKBRENNER11-8, KXNBAREBPROT-26OCT28CHADET-CHARKALKBRENNER11-6
- sample fields: `{"ticker": "KXNBAREBPROT-26OCT28WASCLE-WASBCOULIBALY0-8", "event_ticker": "KXNBAREBPROT-26OCT28WASCLE", "market_type": "binary", "title": "Bilal Coulibaly: 8+ rebounds", "yes_sub_title": "Bilal Coulibaly: 8+", "no_sub_title": "Bilal Coulibaly: 8+", "strike_type": "greater", "floor_strike": 7.5, "custom_strike": {"basketball_player": "2b9b4c52-7963-4bbc-820a-787f29642aa0", "basketball_team": "0464e75c-8bc8-4f18-9ee2-577832b889d6"}, "status": "active", "open_time": "2026-10-28T19:50:47Z", "close_time": "2026-10-30T23:00:00Z", "expected_expiration_time": "2026-10-29T05:00:00Z", "result": "", "rul`

### KXNBARECORD — Pro Basketball Best/Worst Regular Season Record
- (28) NAME have the worst regular season record in the #-# season?
- (28) NAME have the best regular season record in the #-# season?
- (1) NAME L have the worst regular season record in the #-# season?
- (1) NAME C have the worst regular season record in the #-# season?
- (1) NAME L have the best regular season record in the #-# season?
- (1) NAME C have the best regular season record in the #-# season?
- samples: KXNBARECORD-27WORST-WAS, KXNBARECORD-27WORST-UTA, KXNBARECORD-27WORST-TOR, KXNBARECORD-27WORST-SAS, KXNBARECORD-27WORST-SAC, KXNBARECORD-27WORST-POR
- sample fields: `{"ticker": "KXNBARECORD-27WORST-WAS", "event_ticker": "KXNBARECORD-27WORST", "market_type": "binary", "title": "Will Washington have the worst regular season record in the 2026-27 season?", "yes_sub_title": "Washington", "no_sub_title": "Washington", "strike_type": "structured", "custom_strike": {"basketball_team": "0464e75c-8bc8-4f18-9ee2-577832b889d6"}, "status": "active", "open_time": "2026-07-09T19:00:00Z", "close_time": "2027-05-31T14:00:00Z", "expected_expiration_time": "2027-05-01T14:00:00Z", "result": "", "rules_primary": "If the Washington Pro Basketball team has the worst regular sea`

### KXNBARELOCATION — Pro Basketball Team Relocation
- (4) Will the NAME team announce they are relocating to NAME before the start of the #-# regular season?
- (1) Will the NAME team announce they are relocating to St. Louis before the start of the #-# regular season?
- (1) Will the NAME team announce they are relocating to Seattle before the start of the #-# regular season?
- (1) Will the NAME team announce they are relocating to Pittsburgh before the start of the #-# regular season?
- (1) Will the NAME team announce they are relocating to Nashville before the start of the #-# regular season?
- (1) Will the NAME team announce they are not relocating or stay in Portland before the start of the #-# regular season?
- (1) Will the NAME team announce they are relocating to Columbus before the start of the #-# regular season?
- (1) Will the NAME team announce they are relocating to Austin before the start of the #-# regular season?
- samples: KXNBARELOCATION-27POR-TB, KXNBARELOCATION-27POR-STL, KXNBARELOCATION-27POR-SEA, KXNBARELOCATION-27POR-SD, KXNBARELOCATION-27POR-PIT, KXNBARELOCATION-27POR-NSH
- sample fields: `{"ticker": "KXNBARELOCATION-27POR-TB", "event_ticker": "KXNBARELOCATION-27POR", "market_type": "binary", "title": "Will the Portland Pro Basketball team announce they are relocating to Tampa Bay before the start of the 2027-28 regular season?", "yes_sub_title": "Tampa Bay", "no_sub_title": "Tampa Bay", "strike_type": "custom", "custom_strike": {"Location": "Tampa Bay"}, "status": "active", "open_time": "2026-07-27T18:30:00Z", "close_time": "2027-12-01T04:59:00Z", "expected_expiration_time": "2027-12-01T15:00:00Z", "result": "", "rules_primary": "If the Portland Pro Basketball team relocates or`

### KXNBARETIRE — NBA Retirement
- (17) NAME announce his retirement before the #-# NBA season?
- (3) Will LeBron James announce his retirement before the #-# NBA season?
- samples: KXNBARETIRE-LJAMES23-2930, KXNBARETIRE-LJAMES23-2829, KXNBARETIRE-LJAMES23-2728, KXNBARETIRE-KIRVING11-3031, KXNBARETIRE-KIRVING11-2930, KXNBARETIRE-KIRVING11-2829
- sample fields: `{"ticker": "KXNBARETIRE-LJAMES23-2930", "event_ticker": "KXNBARETIRE-LJAMES23", "market_type": "binary", "title": "Will LeBron James announce his retirement before the 2029-30 NBA season?", "yes_sub_title": "Before the 2029-30 season", "no_sub_title": "Before the 2029-30 season", "strike_type": "structured", "custom_strike": {"basketball_player": "5631e46b-716c-4842-8607-a6ebf12fe029"}, "status": "active", "open_time": "2026-05-28T00:45:00Z", "close_time": "2029-11-15T04:59:00Z", "expected_expiration_time": "2029-11-15T15:00:00Z", "result": "", "rules_primary": "If LeBron James announces his r`

### KXNBARETURN — Pro Basketball Player to Return

### KXNBARISINGSTARS — Pro Basketball Rising Stars Tournament

### KXNBAROOKIE1STTEAM — NBA All-Rookie 1st Team
- (22) NAME: NAME
- (7) NAME: NAME.
- (1) NAME: AJ Dybantsa
- samples: KXNBAROOKIE1STTEAM-27-ZEJIOFOR20, KXNBAROOKIE1STTEAM-27-YLENDEBORG1, KXNBAROOKIE1STTEAM-27-TSORBER12, KXNBAROOKIE1STTEAM-27-TREED10, KXNBAROOKIE1STTEAM-27-SDELARREA55, KXNBAROOKIE1STTEAM-27-NAMENT15
- sample fields: `{"ticker": "KXNBAROOKIE1STTEAM-27-ZEJIOFOR20", "event_ticker": "KXNBAROOKIE1STTEAM-27", "market_type": "binary", "title": "All-Rookie First Team Selection: Zuby Ejiofor", "yes_sub_title": "Zuby Ejiofor", "no_sub_title": "Zuby Ejiofor", "strike_type": "structured", "custom_strike": {"basketball_player": "9322bbdb-9368-47c2-8568-8772d794466f"}, "status": "active", "open_time": "2026-09-14T21:00:00Z", "close_time": "2027-07-08T14:00:00Z", "expected_expiration_time": "2027-07-01T14:00:00Z", "result": "", "rules_primary": "If Zuby Ejiofor is selected to the All-Rookie First Team in the 2026-27 Pro `

### KXNBAROOKIE2NDTEAM — NBA All-Rookie 2nd Team
- (32) NAME: NAME
- (7) NAME: NAME.
- (1) NAME: AJ Dybantsa
- samples: KXNBAROOKIE2NDTEAM-27-ZEJIOFOR20, KXNBAROOKIE2NDTEAM-27-YLENDEBORG1, KXNBAROOKIE2NDTEAM-27-TSORBER12, KXNBAROOKIE2NDTEAM-27-TREED10, KXNBAROOKIE2NDTEAM-27-TNICKEL55, KXNBAROOKIE2NDTEAM-27-TBRAZILE7
- sample fields: `{"ticker": "KXNBAROOKIE2NDTEAM-27-ZEJIOFOR20", "event_ticker": "KXNBAROOKIE2NDTEAM-27", "market_type": "binary", "title": "All-Rookie Second Team Selection: Zuby Ejiofor", "yes_sub_title": "Zuby Ejiofor", "no_sub_title": "Zuby Ejiofor", "strike_type": "structured", "custom_strike": {"basketball_player": "9322bbdb-9368-47c2-8568-8772d794466f"}, "status": "active", "open_time": "2026-09-14T21:00:00Z", "close_time": "2027-07-08T14:00:00Z", "expected_expiration_time": "2027-07-01T14:00:00Z", "result": "", "rules_primary": "If Zuby Ejiofor is selected to the All-Rookie Second Team in the 2026-27 Pr`

### KXNBAROTM — NBA Rookie of the Month
- (49) NAME of the Month in October/November: NAME
- (9) NAME of the Month in October/November: NAME.
- (1) NAME of the Month in October/November: Bogoljub Marković
- (1) NAME of the Month in October/November: AJ Dybantsa
- samples: KXNBAROTM-NOV26WEST-YLENDEBORG1, KXNBAROTM-NOV26WEST-TSORBER12, KXNBAROTM-NOV26WEST-TREED10, KXNBAROTM-NOV26WEST-TBRAZILE7, KXNBAROTM-NOV26WEST-TBIBEROVIC13, KXNBAROTM-NOV26WEST-SDELARREA55
- sample fields: `{"ticker": "KXNBAROTM-NOV26WEST-YLENDEBORG1", "event_ticker": "KXNBAROTM-NOV26WEST", "market_type": "binary", "title": "Western Conference Rookie of the Month in October/November: Yaxel Lendeborg", "yes_sub_title": "Yaxel Lendeborg", "no_sub_title": "Yaxel Lendeborg", "strike_type": "structured", "custom_strike": {"basketball_player": "5471cc95-f2b0-41d8-8ec9-0424375746ea"}, "status": "active", "open_time": "2026-10-21T20:00:00Z", "close_time": "2026-12-08T04:59:59Z", "expected_expiration_time": "2026-12-01T04:59:59Z", "result": "", "rules_primary": "If Yaxel Lendeborg wins the Western Confere`

### KXNBAROY — NBA Rookie of the Year
- (12) NAME win Rookie of the Year?
- (3) NAME. win Rookie of the Year?
- (1) NAME of the Year: NAME
- (1) NAME/NAME win Rookie of the Year?
- (1) Will AJ Dybantsa win Rookie of the Year?
- samples: KXNBAROY-27-RCONWELL4, KXNBAROY-27-YLEN, KXNBAROY-27-TIE, KXNBAROY-27-NAME, KXNBAROY-27-MJOH, KXNBAROY-27-MBRO
- sample fields: `{"ticker": "KXNBAROY-27-RCONWELL4", "event_ticker": "KXNBAROY-27", "market_type": "binary", "title": "Pro Basketball Rookie of the Year: Ryan Conwell", "yes_sub_title": "Ryan Conwell", "no_sub_title": "Ryan Conwell", "strike_type": "structured", "custom_strike": {"basketball_player": "8bb5c4c3-444d-4718-80da-6350905f6c5b"}, "status": "active", "open_time": "2026-10-23T22:35:00Z", "close_time": "2027-07-08T14:00:00Z", "expected_expiration_time": "2027-07-31T14:00:00Z", "result": "", "rules_primary": "If Ryan Conwell wins the Pro Basketball Rookie of the Year in the 2026-27 season, then the mark`

### KXNBARULE — Pro Basketball Rule

### KXNBASEATTLE — Seattle NBA team
- (1) Will a Seattle NBA team play a game before #?
- samples: KXNBASEATTLE-30
- sample fields: `{"ticker": "KXNBASEATTLE-30", "event_ticker": "KXNBASEATTLE-30", "market_type": "binary", "title": "Will a Seattle NBA team play a game before 2030?", "yes_sub_title": "Before 2030", "no_sub_title": "Before 2030", "status": "active", "open_time": "2025-05-24T14:00:00Z", "close_time": "2030-01-01T15:00:00Z", "expected_expiration_time": "2030-01-01T15:00:00Z", "result": "", "rules_primary": "If a Seattle-based men's Pro Basketball team plays a game before Jan 1, 2030, then the market resolves to Yes."}`

### KXNBASEED — NBA Playoff Seed
- (35) NAME ## Seed: NAME
- (7) NAME ## Seed: Utah
- (7) NAME ## Seed: Sacramento
- (7) NAME ## Seed: Portland
- (7) NAME ## Seed: Phoenix
- (7) NAME ## Seed: Minnesota
- (7) NAME ## Seed: Memphis
- (7) NAME ## Seed: NAME L
- samples: KXNBASEED-27WEST8-UTA, KXNBASEED-27WEST8-SAS, KXNBASEED-27WEST8-SAC, KXNBASEED-27WEST8-POR, KXNBASEED-27WEST8-PHX, KXNBASEED-27WEST8-OKC
- sample fields: `{"ticker": "KXNBASEED-27WEST8-UTA", "event_ticker": "KXNBASEED-27WEST8", "market_type": "binary", "title": "Western Conference #8 Seed: Utah", "yes_sub_title": "Utah", "no_sub_title": "Utah", "strike_type": "structured", "custom_strike": {"basketball_team": "6f60dfb1-fda1-423f-b76f-67e9d24b9644"}, "status": "active", "open_time": "2026-09-18T16:45:00Z", "close_time": "2027-07-08T14:00:00Z", "expected_expiration_time": "2027-07-01T14:00:00Z", "result": "", "rules_primary": "If Utah is the #8 seed in the Western Conference Playoffs in the 2026-27 Pro Basketball season, then the market resolves t`

### KXNBASEEDOU — NBA Playoff Seed Over/Unders
- (5) NAME: ## seed or better
- (1) Washington: ## seed or better
- (1) Utah: ## seed or better
- (1) Toronto: ## seed or better
- (1) Sacramento: ## seed or better
- (1) Portland: ## seed or better
- (1) Phoenix: ## seed or better
- (1) Philadelphia: ## seed or better
- samples: KXNBASEEDOU-27-WAS10, KXNBASEEDOU-27-UTA9, KXNBASEEDOU-27-TOR5, KXNBASEEDOU-27-SAS2, KXNBASEEDOU-27-SAC10, KXNBASEEDOU-27-POR7
- sample fields: `{"ticker": "KXNBASEEDOU-27-WAS10", "event_ticker": "KXNBASEEDOU-27", "market_type": "binary", "title": "Washington: #10 seed or better", "yes_sub_title": "Washington: #10 seed or better", "no_sub_title": "Washington: #10 seed or better", "strike_type": "less", "cap_strike": 10.5, "custom_strike": {"basketball_team": "0464e75c-8bc8-4f18-9ee2-577832b889d6"}, "status": "active", "open_time": "2026-10-16T20:00:00Z", "close_time": "2027-07-08T14:00:00Z", "expected_expiration_time": "2027-07-01T14:00:00Z", "result": "", "rules_primary": "If the Washington Pro Basketball team is the #10 seed or bette`

### KXNBASERIES — NBA Series Winner

### KXNBASERIES3PMLEADER — Pro Basketball Series 3-Pointers Made Leader

### KXNBASERIESASTLEADER — Pro Basketball Series Assists Leader

### KXNBASERIESCOMEBACK — Pro Basketball Series Comeback

### KXNBASERIESGAMES — NBA Series Total Games

### KXNBASERIESGCOMEBACK — Pro Basketball Series Game Comeback

### KXNBASERIESOT — Pro Basketball Series Overtime

### KXNBASERIESPTS — Pro Basketball Series Player Points

### KXNBASERIESPTSLEADER — Pro Basketball Series Points Leader

### KXNBASERIESPTSSPREAD — Pro Basketball Series Points Spread

### KXNBASERIESREBLEADER — Pro Basketball Series Rebounds Leader

### KXNBASERIESROADWIN — NBA Series 1st Road Win

### KXNBASERIESROADWINS — Pro Basketball Series Total Road Wins

### KXNBASERIESSCORE — NBA Series Exact Score

### KXNBASERIESSPREAD — NBA Series Game Spread

### KXNBASERIESTOTALPTS — Pro Basketball Series Total Points

### KXNBASHOOTINGSTARS — Pro Basketball Shooting Stars Contest

### KXNBASIXTH — NBA Sixth Man of the Year
- (59) NAME win NAME of the Year in the #-# season?
- (7) NAME of the Year: NAME
- (5) NAME. win NAME of the Year in the #-# season?
- (1) NAME of the Year: NAME II
- (1) Will T.J. McConnell win NAME of the Year in the #-# season?
- (1) NAME/NAME win NAME of the Year in the #-# season?
- (1) Will P.J. Washington win NAME of the Year in the #-# season?
- (1) NAME McBride win NAME of the Year in the #-# season?
- samples: KXNBASIXTH-27-JCHAMPAGNIE9, KXNBASIXTH-27-JCHAMPAGNIE30, KXNBASIXTH-27-SMAMUKELASHVILI54, KXNBASIXTH-27-TJOHNSON12, KXNBASIXTH-27-PLARSSON9, KXNBASIXTH-27-ADOSUNMU13
- sample fields: `{"ticker": "KXNBASIXTH-27-JCHAMPAGNIE9", "event_ticker": "KXNBASIXTH-27", "market_type": "binary", "title": "Pro Basketball Sixth Man of the Year: Justin Champagnie", "yes_sub_title": "Justin Champagnie", "no_sub_title": "Justin Champagnie", "strike_type": "structured", "custom_strike": {"basketball_player": "d8d735de-7698-4bec-a77c-5e187aa5d8f6"}, "status": "active", "open_time": "2026-10-26T17:05:00Z", "close_time": "2027-07-08T14:00:00Z", "expected_expiration_time": "2027-07-31T14:00:00Z", "result": "", "rules_primary": "If Justin Champagnie wins the Pro Basketball Sixth Man of the Year in `

### KXNBASJC — NBA Social Justice Champion
- (64) NAME: NAME
- (4) NAME: NAME.
- (1) NAME: OG Anunoby
- (1) NAME: LeBron James
- (1) NAME: Fred VanVleet
- (1) NAME: DeAndre Jordan
- (1) NAME: DeMar DeRozan
- (1) NAME: CJ McCollum
- samples: KXNBASJC-27-WCARTER34, KXNBASJC-27-VWEMBANYAMA1, KXNBASJC-27-TYOUNG3, KXNBASJC-27-TMAXEY0, KXNBASJC-27-TMANN14, KXNBASJC-27-THARRIS23
- sample fields: `{"ticker": "KXNBASJC-27-WCARTER34", "event_ticker": "KXNBASJC-27", "market_type": "binary", "title": "Pro Basketball Kareem Abdul-Jabbar Social Justice Champion: Wendell Carter Jr.", "yes_sub_title": "Wendell Carter Jr.", "no_sub_title": "Wendell Carter Jr.", "strike_type": "structured", "custom_strike": {"basketball_player": "708d8ae3-92df-416c-9629-917d1d20edd6"}, "status": "active", "open_time": "2026-10-06T15:00:00Z", "close_time": "2027-07-07T14:00:00Z", "expected_expiration_time": "2027-07-30T14:00:00Z", "result": "", "rules_primary": "If Wendell Carter Jr. wins the Pro Basketball Kareem`

### KXNBASLAMDUNK — NBA Slam Dunk Contest Winner

### KXNBASOUTHEAST — Pro Basketball Southeast Division Winner
- (5) NAME be the NAME winner in the #-# season?
- samples: KXNBASOUTHEAST-26-WAS, KXNBASOUTHEAST-26-ORL, KXNBASOUTHEAST-26-MIA, KXNBASOUTHEAST-26-CHA, KXNBASOUTHEAST-26-ATL
- sample fields: `{"ticker": "KXNBASOUTHEAST-26-WAS", "event_ticker": "KXNBASOUTHEAST-26", "market_type": "binary", "title": "Will Washington be the Southeast Division winner in the 2026-27 season?", "yes_sub_title": "Washington", "no_sub_title": "Washington", "strike_type": "structured", "custom_strike": {"basketball_team": "0464e75c-8bc8-4f18-9ee2-577832b889d6"}, "status": "active", "open_time": "2026-07-01T21:00:00Z", "close_time": "2027-07-14T14:00:00Z", "expected_expiration_time": "2027-06-30T14:00:00Z", "result": "", "rules_primary": "If Washington is the Southeast Division winner in the 2026-27 Pro Baske`

### KXNBASOUTHWEST — Pro Basketball Southwest Division Winner
- (5) NAME be the NAME winner in the #-# season?
- samples: KXNBASOUTHWEST-26-SAS, KXNBASOUTHWEST-26-NOP, KXNBASOUTHWEST-26-MEM, KXNBASOUTHWEST-26-HOU, KXNBASOUTHWEST-26-DAL
- sample fields: `{"ticker": "KXNBASOUTHWEST-26-SAS", "event_ticker": "KXNBASOUTHWEST-26", "market_type": "binary", "title": "Will San Antonio be the Southwest Division winner in the 2026-27 season?", "subtitle": "San Antonio", "yes_sub_title": "San Antonio", "no_sub_title": "San Antonio", "strike_type": "structured", "custom_strike": {"basketball_team": "ad36c3e8-4194-4e63-920f-7c50f46191a6"}, "status": "active", "open_time": "2026-07-01T21:00:00Z", "close_time": "2027-07-14T14:00:00Z", "expected_expiration_time": "2027-06-30T14:00:00Z", "result": "", "rules_primary": "If San Antonio is the Southwest Division `

### KXNBASPORTSMANSHIP — NBA Sportsmanship Award
- (84) NAME: NAME
- (7) NAME: NAME.
- (1) NAME: T.J. McConnell
- (1) NAME: Nikola Vučević
- (1) NAME: Nikola Jokić
- (1) NAME: LeBron James
- (1) NAME: Luka Dončić
- (1) NAME: DeAndre Jordan
- samples: KXNBASPORTSMANSHIP-27-WCARTER34, KXNBASPORTSMANSHIP-27-VWEMBANYAMA1, KXNBASPORTSMANSHIP-27-TMCCONNELL9, KXNBASPORTSMANSHIP-27-TMAXEY0, KXNBASPORTSMANSHIP-27-TJONESPG, KXNBASPORTSMANSHIP-27-TJONES30
- sample fields: `{"ticker": "KXNBASPORTSMANSHIP-27-WCARTER34", "event_ticker": "KXNBASPORTSMANSHIP-27", "market_type": "binary", "title": "Pro Basketball Sportsmanship Award: Wendell Carter Jr.", "yes_sub_title": "Wendell Carter Jr.", "no_sub_title": "Wendell Carter Jr.", "strike_type": "structured", "custom_strike": {"basketball_player": "708d8ae3-92df-416c-9629-917d1d20edd6"}, "status": "active", "open_time": "2026-10-06T01:00:00Z", "close_time": "2027-07-07T14:00:00Z", "expected_expiration_time": "2027-07-30T14:00:00Z", "result": "", "rules_primary": "If Wendell Carter Jr. wins the Pro Basketball Sportsmans`

### KXNBASPREAD — NBA Spread
- (94) NAME wins by over # points
- (24) Houston wins by over # points
- (24) Cleveland wins by over # points
- (23) Detroit wins by over # points
- (21) NAME L wins by over # points
- (21) Denver wins by over # points
- (21) Minnesota wins by over # points
- (21) Toronto wins by over # points
- samples: KXNBASPREAD-26OCT28OKCDAL-OKC9, KXNBASPREAD-26OCT28OKCDAL-OKC8, KXNBASPREAD-26OCT28OKCDAL-OKC7, KXNBASPREAD-26OCT28OKCDAL-OKC6, KXNBASPREAD-26OCT28OKCDAL-OKC5, KXNBASPREAD-26OCT28OKCDAL-OKC4
- sample fields: `{"ticker": "KXNBASPREAD-26OCT28OKCDAL-OKC9", "event_ticker": "KXNBASPREAD-26OCT28OKCDAL", "market_type": "binary", "title": "Oklahoma City wins by over 8.5 points", "yes_sub_title": "Oklahoma City wins by over 8.5 points", "no_sub_title": "Oklahoma City wins by over 8.5 points", "strike_type": "greater", "floor_strike": 8.5, "custom_strike": {"basketball_team": "a85f6eca-2f3b-4f61-83ab-8d049f59ce2c"}, "status": "active", "open_time": "2026-10-28T00:07:43.012108Z", "close_time": "2026-10-31T01:30:00Z", "expected_expiration_time": "2026-10-29T04:30:00Z", "result": "", "rules_primary": "If Oklaho`

### KXNBASTADIUM — NBA Stadium Completion
- (1) NAME & Entertainment and NAME complete the new Flyers/NAME arena in the NAME before May #, #?
- samples: KXNBASTADIUM-30MAY01PHI-Y
- sample fields: `{"ticker": "KXNBASTADIUM-30MAY01PHI-Y", "event_ticker": "KXNBASTADIUM-30MAY01PHI", "market_type": "binary", "title": "Will Harris Blitzer Sports & Entertainment and Comcast Spectacor complete the new Flyers/Philadelphia Pro Basketball arena in the South Philadelphia Sports Complex before May 1, 2030?", "yes_sub_title": "Before May 1, 2030", "no_sub_title": "Before May 1, 2030", "status": "active", "open_time": "2026-09-08T17:00:00Z", "close_time": "2030-05-01T03:59:00Z", "expected_expiration_time": "2030-05-01T14:00:00Z", "result": "", "rules_primary": "If Harris Blitzer Sports & Entertainment`

### KXNBASTAKESALE — NBA Team Ownership Stake Sale Agreement
- (1) NAME agree to sell all of her remaining ownership interest in NAME L before Jan #, #?
- samples: KXNBASTAKESALE-27JAN01LAL-Y
- sample fields: `{"ticker": "KXNBASTAKESALE-27JAN01LAL-Y", "event_ticker": "KXNBASTAKESALE-27JAN01LAL", "market_type": "binary", "title": "Will Jeanie Buss agree to sell all of her remaining ownership interest in Los Angeles L before Jan 1, 2027?", "subtitle": "Agreement before Jan 1, 2027", "yes_sub_title": "Agreement before Jan 1, 2027", "no_sub_title": "Agreement before Jan 1, 2027", "status": "active", "open_time": "2026-08-19T00:00:35Z", "close_time": "2027-01-08T05:00:00Z", "expected_expiration_time": "2027-01-08T05:00:00Z", "result": "", "rules_primary": "If Jeanie Buss and/or any trust or legal entity `

### KXNBASTARTERS — Pro Basketball Starting Lineup

### KXNBASTATAVG — NBA Player Stat Average
- (66) NAME: #+ PPG
- (36) NAME: #+ RPG
- (32) NAME: #+ #PG
- (32) NAME: #+ APG
- (3) NAME.: #+ PPG
- (2) NAME III: #+ PPG
- (1) Zach LaVine: #+ #PG
- (1) NAME III: #+ #PG
- samples: KXNBASTATAVG-273PG-ZLAVINE8-2P6, KXNBASTATAVG-273PG-VWEMBANYAMA1-2P0, KXNBASTATAVG-273PG-TMURPHY25-2P8, KXNBASTATAVG-273PG-TMAXEY0-2P8, KXNBASTATAVG-273PG-THERRO11-2P9, KXNBASTATAVG-273PG-THALIBURTON0-2P8
- sample fields: `{"ticker": "KXNBASTATAVG-273PG-ZLAVINE8-2P6", "event_ticker": "KXNBASTATAVG-273PG", "market_type": "binary", "title": "Zach LaVine: 2.6+ 3PG", "yes_sub_title": "Zach LaVine: 2.6+ 3PG", "no_sub_title": "Zach LaVine: 2.6+ 3PG", "strike_type": "greater_or_equal", "floor_strike": 2.6, "custom_strike": {"basketball_player": "b02cbe96-1ddf-40bc-9dec-7146c3350d61"}, "status": "active", "open_time": "2026-10-08T22:15:00Z", "close_time": "2027-07-07T14:00:00Z", "expected_expiration_time": "2027-06-30T14:00:00Z", "result": "", "rules_primary": "If Zach LaVine records at least 2.6 three-pointers made per`

### KXNBASTATLEADER — NBA Regular Season League Leader
- (101) Total plus/minus leader in the #-# regular season: NAME
- (84) Efficiency leader in the #-# regular season: NAME
- (48) Steals per game leader in the #-# regular season: NAME
- (44) Three-pointers made per game leader in the #-# regular season: NAME
- (44) Points per game leader in the #-# regular season: NAME
- (43) Minutes played per game leader in the #-# regular season: NAME
- (43) Assists per game leader in the #-# regular season: NAME
- (41) Double doubles leader in the #-# regular season: NAME
- samples: KXNBASTATLEADER-27PM-WKESSLER14, KXNBASTATLEADER-27PM-WCARTER34, KXNBASTATLEADER-27PM-VWEMBANYAMA1, KXNBASTATLEADER-27PM-VEDGECOMBE77, KXNBASTATLEADER-27PM-TREED10, KXNBASTATLEADER-27PM-TMAXEY0
- sample fields: `{"ticker": "KXNBASTATLEADER-27PM-WKESSLER14", "event_ticker": "KXNBASTATLEADER-27PM", "market_type": "binary", "title": "Total plus/minus leader in the 2026-27 regular season: Walker Kessler", "yes_sub_title": "Walker Kessler", "no_sub_title": "Walker Kessler", "strike_type": "structured", "custom_strike": {"basketball_player": "fa781441-5e6a-4a3d-9a3f-0af9ee263945"}, "status": "active", "open_time": "2026-10-20T21:00:00Z", "close_time": "2027-07-07T14:00:00Z", "expected_expiration_time": "2027-06-30T14:00:00Z", "result": "", "rules_primary": "If Walker Kessler leads the NBA in total plus/minu`

### KXNBASTL — NBA Player Steals
- (174) NAME: #+ steals
- (4) NAME.: #+ steals
- (3) Fred VanVleet: #+ steals
- (3) Nikola Jokić: #+ steals
- (3) Jaden McDaniels: #+ steals
- (3) LaMelo Ball: #+ steals
- (3) NAME III: #+ steals
- (3) OG Anunoby: #+ steals
- samples: KXNBASTL-26OCT28CHADET-DETCCUNNINGHAM2-3, KXNBASTL-26OCT28CHADET-DETCCUNNINGHAM2-2, KXNBASTL-26OCT28CHADET-DETCCUNNINGHAM2-1, KXNBASTL-26OCT28CHADET-DETATHOMPSON9-3, KXNBASTL-26OCT28CHADET-DETATHOMPSON9-2, KXNBASTL-26OCT28CHADET-DETATHOMPSON9-1
- sample fields: `{"ticker": "KXNBASTL-26OCT28CHADET-DETCCUNNINGHAM2-3", "event_ticker": "KXNBASTL-26OCT28CHADET", "market_type": "binary", "title": "Cade Cunningham: 3+ steals", "yes_sub_title": "Cade Cunningham: 3+", "no_sub_title": "Cade Cunningham: 3+", "strike_type": "greater", "floor_strike": 2.5, "custom_strike": {"basketball_player": "0a8c3059-aa64-4871-8291-fff857a201af", "basketball_team": "65569528-1888-40aa-9d62-2b0e8142a9b4"}, "status": "active", "open_time": "2026-10-28T19:46:01.519704Z", "close_time": "2026-10-30T23:00:00Z", "expected_expiration_time": "2026-10-29T02:00:00Z", "result": "", "rules`

### KXNBASTOCK — NBA Player Steals + Blocks
- (67) NAME: #+ steals and blocks
- (4) NAME.: #+ steals and blocks
- (3) Nikola Jokić: #+ steals and blocks
- (3) Jaden McDaniels: #+ steals and blocks
- (3) OG Anunoby: #+ steals and blocks
- (2) Fred VanVleet: #+ steals and blocks
- (2) NAME III: #+ steals and blocks
- samples: KXNBASTOCK-26OCT28HOUMIL-MILTHERRO11-3, KXNBASTOCK-26OCT28HOUMIL-MILTHERRO11-2, KXNBASTOCK-26OCT28HOUMIL-MILRROLLINS13-3, KXNBASTOCK-26OCT28HOUMIL-MILRROLLINS13-2, KXNBASTOCK-26OCT28HOUMIL-MILMTURNER3-4, KXNBASTOCK-26OCT28HOUMIL-MILMTURNER3-3
- sample fields: `{"ticker": "KXNBASTOCK-26OCT28HOUMIL-MILTHERRO11-3", "event_ticker": "KXNBASTOCK-26OCT28HOUMIL", "market_type": "binary", "title": "Tyler Herro: 3+ steals and blocks", "yes_sub_title": "Tyler Herro: 3+", "no_sub_title": "Tyler Herro: 3+", "strike_type": "greater", "floor_strike": 2.5, "custom_strike": {"basketball_player": "3e3ceeda-5f54-4aa0-9ced-e8ff6cbcadf2", "basketball_team": "5dc3fe01-79a4-4f2f-a953-d922ea4a6dd3"}, "status": "active", "open_time": "2026-10-28T19:46:01.700276Z", "close_time": "2026-10-31T00:00:00Z", "expected_expiration_time": "2026-10-29T03:00:00Z", "result": "", "rules_`

### KXNBASTOCKS — NBA Player Steals and Blocks

### KXNBASUMMER — Pro Basketball Summer League Champion

### KXNBASUMMER1HSPREAD — Pro Basketball Summer League 1st Half Spread

### KXNBASUMMER1HTOTAL — Pro Basketball Summer League 1st Half Total

### KXNBASUMMER1HWINNER — Pro Basketball Summer League 1st Half Winner

### KXNBASUMMERGAME — Pro Basketball Summer League Game

### KXNBASUMMERMVP — Pro Basketball Summer League MVP

### KXNBASUMMERPTS — Pro Basketball Summer Player Points

### KXNBASUMMERSPREAD — Pro Basketball Summer League Spread

### KXNBASUMMERTOTAL — Pro Basketball Summer League Total

### KXNBASWEEP — NBA Teams to Have a Series Sweep

### KXNBATEAM — NBA team
- (1) Will the NBA approve a new franchise before #?
- samples: KXNBATEAM-30
- sample fields: `{"ticker": "KXNBATEAM-30", "event_ticker": "KXNBATEAM-30", "market_type": "binary", "title": "Will the NBA approve a new franchise before 2030?", "yes_sub_title": "Before 2030", "no_sub_title": "Before 2030", "status": "active", "open_time": "2024-12-19T15:00:00Z", "close_time": "2030-01-01T15:00:00Z", "expected_expiration_time": "2030-01-01T15:00:00Z", "result": "", "rules_primary": "If the Pro Basketball Board of Governors votes to approve a new franchise before Jan 1, 2030, then the market resolves to Yes."}`

### KXNBATEAMANNOUNCE — Pro Basketball New Team Announce

### KXNBATEAMMATE — NBA Teammate of the Year
- (65) NAME of the Year: NAME
- (2) NAME of the Year: NAME.
- (1) NAME of the Year: T.J. McConnell
- (1) NAME of the Year: LeBron James
- (1) NAME of the Year: Fred VanVleet
- (1) NAME of the Year: DeAndre Jordan
- (1) NAME of the Year: Donte DiVincenzo
- (1) NAME of the Year: DeMar DeRozan
- samples: KXNBATEAMMATE-27-TMCCONNELL9, KXNBATEAMMATE-27-TMAXEY0, KXNBATEAMMATE-27-TMANN14, KXNBATEAMMATE-27-TJONESPG, KXNBATEAMMATE-27-TJONES30, KXNBATEAMMATE-27-THARRIS23
- sample fields: `{"ticker": "KXNBATEAMMATE-27-TMCCONNELL9", "event_ticker": "KXNBATEAMMATE-27", "market_type": "binary", "title": "Pro Basketball Teammate of the Year: T.J. McConnell", "yes_sub_title": "T.J. McConnell", "no_sub_title": "T.J. McConnell", "strike_type": "structured", "custom_strike": {"basketball_player": "7c7401cb-1476-4a60-9101-d16b48924c02"}, "status": "active", "open_time": "2026-10-06T15:15:00Z", "close_time": "2027-07-07T14:00:00Z", "expected_expiration_time": "2027-07-30T14:00:00Z", "result": "", "rules_primary": "If T.J. McConnell wins the Pro Basketball Teammate of the Year in the 2026-`

### KXNBATEAMSALE — Pro Basketball Team to be Sold
- (1) Will the NAME team be sold after Issuance and before Jan #, #?
- samples: KXNBATEAMSALE-27JANPHX-Y
- sample fields: `{"ticker": "KXNBATEAMSALE-27JANPHX-Y", "event_ticker": "KXNBATEAMSALE-27JANPHX", "market_type": "binary", "title": "Will the Phoenix Pro Basketball team be sold after Issuance and before Jan 1, 2027?", "yes_sub_title": "Before Jan 1, 2027", "no_sub_title": "Before Jan 1, 2027", "strike_type": "structured", "custom_strike": {"basketball_team": "ace11dff-c5d1-4ab9-9452-5312253659fd"}, "status": "active", "open_time": "2026-08-21T19:00:00Z", "close_time": "2027-01-01T04:59:00Z", "expected_expiration_time": "2027-01-01T15:00:00Z", "result": "", "rules_primary": "If the Phoenix Pro Basketball team `

### KXNBATEAMTOTAL — NBA Team Total
- (95) NAME over # points scored
- (19) Toronto over # points scored
- (19) Orlando over # points scored
- (19) Dallas over # points scored
- (19) Utah over # points scored
- (19) NAME L over # points scored
- (19) NAME C over # points scored
- (19) Denver over # points scored
- samples: KXNBATEAMTOTAL-26OCT28ORLTOR-TOR99, KXNBATEAMTOTAL-26OCT28ORLTOR-TOR97, KXNBATEAMTOTAL-26OCT28ORLTOR-TOR133, KXNBATEAMTOTAL-26OCT28ORLTOR-TOR131, KXNBATEAMTOTAL-26OCT28ORLTOR-TOR129, KXNBATEAMTOTAL-26OCT28ORLTOR-TOR127
- sample fields: `{"ticker": "KXNBATEAMTOTAL-26OCT28ORLTOR-TOR99", "event_ticker": "KXNBATEAMTOTAL-26OCT28ORLTOR", "market_type": "binary", "title": "Toronto over 98.5 points scored", "yes_sub_title": "Toronto over 98.5 points", "no_sub_title": "Toronto over 98.5 points", "strike_type": "greater", "floor_strike": 98.5, "custom_strike": {"basketball_team": "96c447dd-2cdd-4c58-a151-ef0df87de981"}, "status": "active", "open_time": "2026-10-28T07:13:32.621096Z", "close_time": "2026-10-30T23:30:00Z", "expected_expiration_time": "2026-10-29T02:30:00Z", "result": "", "rules_primary": "If Toronto scores more than 98.5 `

### KXNBATEAMWINSTREAK — NBA Team with the Longest Winning Streak
- (5) Longest win streak: NAME
- (1) Longest win streak: Washington
- (1) Longest win streak: Utah
- (1) Longest win streak: Toronto
- (1) Longest win streak: Sacramento
- (1) Longest win streak: Portland
- (1) Longest win streak: Phoenix
- (1) Longest win streak: Philadelphia
- samples: KXNBATEAMWINSTREAK-27-WAS, KXNBATEAMWINSTREAK-27-UTA, KXNBATEAMWINSTREAK-27-TOR, KXNBATEAMWINSTREAK-27-SAS, KXNBATEAMWINSTREAK-27-SAC, KXNBATEAMWINSTREAK-27-POR
- sample fields: `{"ticker": "KXNBATEAMWINSTREAK-27-WAS", "event_ticker": "KXNBATEAMWINSTREAK-27", "market_type": "binary", "title": "Longest win streak: Washington", "yes_sub_title": "Washington", "no_sub_title": "Washington", "strike_type": "structured", "custom_strike": {"basketball_team": "0464e75c-8bc8-4f18-9ee2-577832b889d6"}, "status": "active", "open_time": "2026-10-08T18:45:00Z", "close_time": "2027-07-07T14:00:00Z", "expected_expiration_time": "2027-06-30T14:00:00Z", "result": "", "rules_primary": "If the Washington Pro Basketball team records the longest consecutive win streak in the 2026-27 Pro Bask`

### KXNBATOJOINCBA — NBA Players to Join the CBA
- (22) NAME to sign with a CBA team before Oct #, #
- (1) Mac McClung to sign with a CBA team before Oct #, #
- (1) Jonas Valančiūnas to sign with a CBA team before Oct #, #
- (1) Doug McDermott to sign with a CBA team before Oct #, #
- samples: KXNBATOJOINCBA-01OCT27-BSIMMONS, KXNBATOJOINCBA-01OCT27-YUKIKAWAMURA, KXNBATOJOINCBA-01OCT27-THANASISANTETOKOUNMPO, KXNBATOJOINCBA-01OCT27-SHARIFECOOPER, KXNBATOJOINCBA-01OCT27-SETHCURRY, KXNBATOJOINCBA-01OCT27-RYANNEMBHARD
- sample fields: `{"ticker": "KXNBATOJOINCBA-01OCT27-BSIMMONS", "event_ticker": "KXNBATOJOINCBA-01OCT27", "market_type": "binary", "title": "Ben Simmons to sign with a CBA team before Oct 1, 2027", "yes_sub_title": "Ben Simmons", "no_sub_title": "Ben Simmons", "strike_type": "custom", "custom_strike": {"Player": "Ben Simmons"}, "status": "active", "open_time": "2026-10-02T20:00:00Z", "close_time": "2027-10-08T14:00:00Z", "expected_expiration_time": "2027-10-01T04:00:00Z", "result": "", "rules_primary": "If Ben Simmons signs a contract with any team in the Chinese Basketball Association (CBA) after issuance and `

### KXNBATOP3 — Pro Basketball Draft Lottery Top 3

### KXNBATOP5ROTY — Top 5 NBA draft ROTY

### KXNBATOPPICK — Pro Basketball Draft Lottery Winner

### KXNBATOTAL — NBA Total
- (348) NAME: Over # points scored
- samples: KXNBATOTAL-26OCT28OKCDAL-259, KXNBATOTAL-26OCT28OKCDAL-257, KXNBATOTAL-26OCT28OKCDAL-255, KXNBATOTAL-26OCT28OKCDAL-253, KXNBATOTAL-26OCT28OKCDAL-251, KXNBATOTAL-26OCT28OKCDAL-249
- sample fields: `{"ticker": "KXNBATOTAL-26OCT28OKCDAL-259", "event_ticker": "KXNBATOTAL-26OCT28OKCDAL", "market_type": "binary", "title": "Full Game: Over 258.5 points scored", "yes_sub_title": "Over 258.5 points", "no_sub_title": "Over 258.5 points", "strike_type": "greater", "floor_strike": 258.5, "status": "active", "open_time": "2026-10-28T00:07:43.012108Z", "close_time": "2026-10-31T01:30:00Z", "expected_expiration_time": "2026-10-29T04:30:00Z", "result": "", "rules_primary": "If over 258.5 total points are scored in the Oklahoma City vs Dallas Pro Basketball game originally scheduled for Oct 28, 2026, th`

### KXNBATRADE — Pro Basketball Trade
- (39) NAME be traded after Issuance and before Feb #, #?
- (1) NAME Jokić be traded after Issuance and before Feb #, #?
- (1) NAME LaVine be traded after Issuance and before Feb #, #?
- (1) Will PJ Washington be traded after Issuance and before Feb #, #?
- (1) NAME. be traded after Issuance and before Feb #, #?
- (1) NAME McDaniels be traded after Issuance and before Feb #, #?
- (1) NAME DiVincenzo be traded after Issuance and before Feb #, #?
- (1) Will DeMar DeRozan be traded after Issuance and before Feb #, #?
- samples: KXNBATRADE-27FEB12-SCURRY30, KXNBATRADE-27FEB12-NJOKIC15, KXNBATRADE-27FEB12-AWIGGINS22, KXNBATRADE-27FEB12-JDUREN0, KXNBATRADE-27FEB12-ZWILLIAMSON1, KXNBATRADE-27FEB12-ZLAVINE8
- sample fields: `{"ticker": "KXNBATRADE-27FEB12-SCURRY30", "event_ticker": "KXNBATRADE-27FEB12", "market_type": "binary", "title": "Will Stephen Curry be traded after Issuance and before Feb 12, 2027?", "subtitle": ":: Golden State", "yes_sub_title": "Stephen Curry", "no_sub_title": "Stephen Curry", "strike_type": "structured", "custom_strike": {"basketball_player": "15cba021-5e04-44b0-95f9-9e975ec48697"}, "status": "active", "open_time": "2026-09-07T19:00:00Z", "close_time": "2027-02-12T04:59:00Z", "expected_expiration_time": "2027-02-12T15:00:00Z", "result": "", "rules_primary": "If Stephen Curry is traded a`

### KXNBAUNBEATEN — NBA Playoffs Team to go Undefeated

### KXNBAUPSET — NBA Number of Upsets per Round

### KXNBAWCFQUAL — NBA Western Conference Finals Qualifiers
- (4) NAME qualifies for the NAME
- (1) Utah qualifies for the NAME
- (1) Sacramento qualifies for the NAME
- (1) Portland qualifies for the NAME
- (1) Phoenix qualifies for the NAME
- (1) Minnesota qualifies for the NAME
- (1) Memphis qualifies for the NAME
- (1) NAME L qualifies for the NAME
- samples: KXNBAWCFQUAL-27-UTA, KXNBAWCFQUAL-27-SAS, KXNBAWCFQUAL-27-SAC, KXNBAWCFQUAL-27-POR, KXNBAWCFQUAL-27-PHX, KXNBAWCFQUAL-27-OKC
- sample fields: `{"ticker": "KXNBAWCFQUAL-27-UTA", "event_ticker": "KXNBAWCFQUAL-27", "market_type": "binary", "title": "Utah qualifies for the Western Conference Finals", "yes_sub_title": "Utah", "no_sub_title": "Utah", "strike_type": "structured", "custom_strike": {"basketball_team": "6f60dfb1-fda1-423f-b76f-67e9d24b9644"}, "status": "active", "open_time": "2026-09-17T22:00:00Z", "close_time": "2027-07-07T14:00:00Z", "expected_expiration_time": "2027-06-30T14:00:00Z", "result": "", "rules_primary": "If Utah qualifies for the Western Conference Finals in the 2026-27 Pro Basketball season, then the market reso`

### KXNBAWEST — Pro Basketball Western Conference Champion
- (13) NAME win the NAME in the #-# season?
- (1) NAME L win the NAME in the #-# season?
- (1) NAME C win the NAME in the #-# season?
- samples: KXNBAWEST-27-UTA, KXNBAWEST-27-SAS, KXNBAWEST-27-SAC, KXNBAWEST-27-POR, KXNBAWEST-27-PHX, KXNBAWEST-27-OKC
- sample fields: `{"ticker": "KXNBAWEST-27-UTA", "event_ticker": "KXNBAWEST-27", "market_type": "binary", "title": "Will Utah win the Pro Basketball Western Conference Finals in the 2026-27 season?", "yes_sub_title": "Utah", "no_sub_title": "Utah", "strike_type": "structured", "custom_strike": {"basketball_team": "6f60dfb1-fda1-423f-b76f-67e9d24b9644"}, "status": "active", "open_time": "2026-06-16T20:00:00Z", "close_time": "2029-06-29T14:00:00Z", "expected_expiration_time": "2027-06-30T14:00:00Z", "result": "", "rules_primary": "If Utah wins the Pro Basketball Western Conference Finals in the 2026-27 season, th`

### KXNBAWEST1SEED — NBA Western Conference 1 Seed
- (13) NAME be the ## seed in the NAME at the conclusion of the #-# NAME regular season?
- (1) NAME L be the ## seed in the NAME at the conclusion of the #-# NAME regular season?
- (1) NAME C be the ## seed in the NAME at the conclusion of the #-# NAME regular season?
- samples: KXNBAWEST1SEED-26-UTA, KXNBAWEST1SEED-26-SAS, KXNBAWEST1SEED-26-SAC, KXNBAWEST1SEED-26-POR, KXNBAWEST1SEED-26-PHX, KXNBAWEST1SEED-26-OKC
- sample fields: `{"ticker": "KXNBAWEST1SEED-26-UTA", "event_ticker": "KXNBAWEST1SEED-26", "market_type": "binary", "title": "Will Utah be the #1 seed in the Western Conference at the conclusion of the 2026-27 Pro Basketball regular season?", "yes_sub_title": "Utah", "no_sub_title": "Utah", "strike_type": "structured", "custom_strike": {"basketball_team": "6f60dfb1-fda1-423f-b76f-67e9d24b9644"}, "status": "active", "open_time": "2026-06-16T21:00:00Z", "close_time": "2027-06-15T14:00:00Z", "expected_expiration_time": "2027-06-01T14:00:00Z", "result": "", "rules_primary": "If Utah is the #1 seed in the Western Co`

### KXNBAWFINMVP — NBA Western Conference Finals MVP
- (40) NAME MVP: NAME
- (2) NAME MVP: NAME III
- (2) NAME MVP: NAME.
- (1) NAME MVP: Nikola Jokić
- (1) NAME MVP: Luka Dončić
- (1) NAME MVP: LaMelo Ball
- (1) NAME MVP: Kristaps Porziņģis
- (1) NAME MVP: Jaden McDaniels
- samples: KXNBAWFINMVP-27-ZWILLIAMSON1, KXNBAWFINMVP-27-VWEMBANYAMA1, KXNBAWFINMVP-27-TMURPHY25, KXNBAWFINMVP-27-SSHARPE17, KXNBAWFINMVP-27-SGILGEOUSALEXANDER2, KXNBAWFINMVP-27-SCURRY30
- sample fields: `{"ticker": "KXNBAWFINMVP-27-ZWILLIAMSON1", "event_ticker": "KXNBAWFINMVP-27", "market_type": "binary", "title": "Pro Basketball Western Conference Finals MVP: Zion Williamson", "yes_sub_title": "Zion Williamson", "no_sub_title": "Zion Williamson", "strike_type": "structured", "custom_strike": {"basketball_player": "220527f6-f6e9-46b3-92b4-ccd8e37ad577"}, "status": "active", "open_time": "2026-09-09T19:00:00Z", "close_time": "2027-08-07T14:00:00Z", "expected_expiration_time": "2027-08-30T14:00:00Z", "result": "", "rules_primary": "If Zion Williamson wins the Pro Basketball Western Conference Fi`

### KXNBAWHATTEND — Pro Basketball White House Attend
- (1) Will the NAME team visit the NAME before Dec #, #?
- samples: KXNBAWHATTEND-26NYK-Y
- sample fields: `{"ticker": "KXNBAWHATTEND-26NYK-Y", "event_ticker": "KXNBAWHATTEND-26NYK", "market_type": "binary", "title": "Will the New York Pro Basketball team visit the White House before Dec 31, 2026?", "yes_sub_title": "New York Pro Basketball team to visit the White House", "no_sub_title": "New York Pro Basketball team to visit the White House", "status": "active", "open_time": "2026-06-18T16:30:00Z", "close_time": "2026-12-31T04:59:00Z", "expected_expiration_time": "2026-12-31T15:00:00Z", "result": "", "rules_primary": "If the New York Pro Basketball team visits the White House in Washington D.C. and`

### KXNBAWINMARGIN — NBA Win Margin
- (16) NAME wins by # to # points
- (5) NAME wins by # or more points
- (3) Dallas wins by # to # points
- (3) Chicago wins by # to # points
- (3) NAME L wins by # to # points
- (3) NAME C wins by # to # points
- (3) Denver wins by # to # points
- (3) Detroit wins by # to # points
- samples: KXNBAWINMARGIN-26OCT28OKCDAL-OKC6TO10, KXNBAWINMARGIN-26OCT28OKCDAL-OKC21PLUS, KXNBAWINMARGIN-26OCT28OKCDAL-OKC1TO5, KXNBAWINMARGIN-26OCT28OKCDAL-OKC11TO20, KXNBAWINMARGIN-26OCT28OKCDAL-DAL6TO10, KXNBAWINMARGIN-26OCT28OKCDAL-DAL21PLUS
- sample fields: `{"ticker": "KXNBAWINMARGIN-26OCT28OKCDAL-OKC6TO10", "event_ticker": "KXNBAWINMARGIN-26OCT28OKCDAL", "market_type": "binary", "title": "Oklahoma City wins by 6 to 10 points", "yes_sub_title": "Oklahoma City wins by 6-10 points", "no_sub_title": "Oklahoma City wins by 6-10 points", "strike_type": "custom", "custom_strike": {"Winning Margin": "6 to 10", "basketball_team": "a85f6eca-2f3b-4f61-83ab-8d049f59ce2c"}, "status": "active", "open_time": "2026-10-28T00:08:27.693338Z", "close_time": "2026-10-31T01:30:00Z", "expected_expiration_time": "2026-10-29T04:30:00Z", "result": "", "rules_primary": "I`

### KXNBAWINRECORD — OKC NBA Win Record

### KXNBAWINS — Pro Basketball Win Totals
- (282) Will the NAME team win at least # games in the #-# regular season?
- (10) Will the NAME C NAME team win at least # games in the #-# regular season?
- (10) Will the NAME L NAME team win at least # games in the #-# regular season?
- (10) Will the NAME team record at least # wins in the #-# regular season?
- samples: KXNBAWINS-27UTA-60, KXNBAWINS-27UTA-55, KXNBAWINS-27UTA-50, KXNBAWINS-27UTA-45, KXNBAWINS-27UTA-40, KXNBAWINS-27UTA-35
- sample fields: `{"ticker": "KXNBAWINS-27UTA-60", "event_ticker": "KXNBAWINS-27UTA", "market_type": "binary", "title": "Will the Utah Pro Basketball team win at least 60 games in the 2026-27 regular season?", "yes_sub_title": "60+ wins", "no_sub_title": "60+ wins", "strike_type": "greater_or_equal", "floor_strike": 60, "custom_strike": {"basketball_team": "6f60dfb1-fda1-423f-b76f-67e9d24b9644"}, "status": "active", "open_time": "2026-07-09T21:00:00Z", "close_time": "2027-05-08T14:00:00Z", "expected_expiration_time": "2027-05-08T14:00:00Z", "result": "", "rules_primary": "If the Utah Pro Basketball team wins at`

### KXNBAWINSTREAK — NBA Longest Win Streak
- (6) Longest win streak: #+ games
- samples: KXNBAWINSTREAK-27-20, KXNBAWINSTREAK-27-18, KXNBAWINSTREAK-27-16, KXNBAWINSTREAK-27-14, KXNBAWINSTREAK-27-12, KXNBAWINSTREAK-27-10
- sample fields: `{"ticker": "KXNBAWINSTREAK-27-20", "event_ticker": "KXNBAWINSTREAK-27", "market_type": "binary", "title": "Longest win streak: 20+ games", "yes_sub_title": "20+ games", "no_sub_title": "20+ games", "strike_type": "greater_or_equal", "floor_strike": 20, "status": "active", "open_time": "2026-10-08T17:51:00Z", "close_time": "2027-07-07T14:00:00Z", "expected_expiration_time": "2027-06-30T14:00:00Z", "result": "", "rules_primary": "If any team in Pro Basketball records a win streak of at least 20 consecutive games in the 2026-27 Pro Basketball regular season, then the market resolves to Yes."}`

### KXNBAXMASOPPONENT — Pro Basketball Christmas Day Opponent

### KXNEXTCOACHOUTNBA — Next coach out NBA

### KXNEXTNBACOACH — Who is the Next NBA Coach of Team

### KXNEXTTEAMNBA — Next NBA Team

### KXNFLNBA — NFL and NBA Champion Combo

### KXPLAYEROPTIONNBA — player option nba

### KXTEAMSINNBAEF — Teams in NBA Eastern Conference Finals

### KXTEAMSINNBAF — Teams in NBA Finals

### KXTEAMSINNBAWF — Teams in NBA Western Conference Finals

### KXTOP3NBADRAFT — NBA Draft Top 3

### KXTRUMPNBAFINALS — Trump NBA finals

## UNRESOLVED samples

- `KXNBA3PTPROT-26OCT28WASCLE-WASBCOULIBALY0-4` — Bilal Coulibaly: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28WASCLE-WASBCOULIBALY0-3` — Bilal Coulibaly: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28WASCLE-WASBCOULIBALY0-2` — Bilal Coulibaly: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28WASCLE-WASBCOULIBALY0-1` — Bilal Coulibaly: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-DETDROBINSON55-1` — Duncan Robinson: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-DETDJENKINS24-5` — Daniss Jenkins: 5+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-DETDJENKINS24-4` — Daniss Jenkins: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-DETDJENKINS24-3` — Daniss Jenkins: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-DETDJENKINS24-2` — Daniss Jenkins: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-DETDJENKINS24-1` — Daniss Jenkins: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-DETKHUERTERSF-5` — Kevin Huerter: 5+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-DETKHUERTERSF-4` — Kevin Huerter: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-DETKHUERTERSF-3` — Kevin Huerter: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-DETKHUERTERSF-2` — Kevin Huerter: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-DETKHUERTERSF-1` — Kevin Huerter: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-CHAGALLEN8-5` — Grayson Allen: 5+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-CHAGALLEN8-4` — Grayson Allen: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-CHAGALLEN8-3` — Grayson Allen: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-CHAGALLEN8-2` — Grayson Allen: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-CHAGALLEN8-1` — Grayson Allen: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28MIAATL-ATLLDORT0-5` — Luguentz Dort: 5+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28MIAATL-ATLLDORT0-4` — Luguentz Dort: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28MIAATL-ATLLDORT0-3` — Luguentz Dort: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28MIAATL-ATLLDORT0-2` — Luguentz Dort: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28MIAATL-ATLLDORT0-1` — Luguentz Dort: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28DENNOP-NOPSBEY41-5` — Saddiq Bey: 5+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28DENNOP-NOPSBEY41-4` — Saddiq Bey: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28DENNOP-NOPSBEY41-3` — Saddiq Bey: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28DENNOP-NOPSBEY41-2` — Saddiq Bey: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28DENNOP-NOPSBEY41-1` — Saddiq Bey: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28MIAATL-ATLDDANIELS5-4` — Dyson Daniels: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28MIAATL-ATLDDANIELS5-3` — Dyson Daniels: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28MIAATL-ATLDDANIELS5-2` — Dyson Daniels: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28MIAATL-ATLDDANIELS5-1` — Dyson Daniels: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-DETDROBINSON55-6` — Duncan Robinson: 6+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-DETDROBINSON55-5` — Duncan Robinson: 5+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-DETDROBINSON55-4` — Duncan Robinson: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-DETDROBINSON55-3` — Duncan Robinson: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-DETDROBINSON55-2` — Duncan Robinson: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-DETJCOLLINS20-5` — John Collins: 5+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-DETJCOLLINS20-4` — John Collins: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-DETJCOLLINS20-3` — John Collins: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-DETJCOLLINS20-2` — John Collins: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28CHADET-DETJCOLLINS20-1` — John Collins: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28OKCDAL-OKCJMCCAIN3-6` — Jared McCain: 6+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28OKCDAL-OKCJMCCAIN3-5` — Jared McCain: 5+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28OKCDAL-OKCJMCCAIN3-4` — Jared McCain: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28OKCDAL-OKCJMCCAIN3-3` — Jared McCain: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28OKCDAL-OKCJMCCAIN3-2` — Jared McCain: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28OKCDAL-OKCAMITCHELL25-5` — Ajay Mitchell: 5+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28OKCDAL-OKCAMITCHELL25-4` — Ajay Mitchell: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28OKCDAL-OKCAMITCHELL25-3` — Ajay Mitchell: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28OKCDAL-OKCAMITCHELL25-2` — Ajay Mitchell: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28OKCDAL-OKCAMITCHELL25-1` — Ajay Mitchell: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28SASUTA-UTAABAILEY19-5` — Ace Bailey: 5+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28SASUTA-UTAABAILEY19-4` — Ace Bailey: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28SASUTA-UTAABAILEY19-3` — Ace Bailey: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28SASUTA-UTAABAILEY19-2` — Ace Bailey: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28SASUTA-UTAABAILEY19-1` — Ace Bailey: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT28LALLAC-LACDGARLAND10-1` — Darius Garland: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title

## Series decisions (basketball-related)

- skip `KXMARMADSEEDSUM` March Madness Sum of Seeds — no NBA marker
- NBA  `KXNBATOP3` Pro Basketball Draft Lottery Top 3 — ticker prefix KXNBA
- skip `KXLNBELITEGAME` LNB Elite Game — no NBA marker
- NBA  `KXNBA1HSPREAD` NBA 1st Half Spread — ticker prefix KXNBA
- skip `KXNCAAMBACC` ACC Conference Tournament — no NBA marker
- NBA  `KXNBAALLSTARS` NBA All-Stars — ticker prefix KXNBA
- NBA  `KXNBAHOMECLINCH` Pro Basketball Series Winner to Clinch at Home — ticker prefix KXNBA
- skip `KXZYNBAN` Zyn ban in the United States — no NBA marker
- NBA  `KXNBAMIMP` NBA Most Improved Player — ticker prefix KXNBA
- skip `KXFIBACHAMPTOTAL` FIBA Champions League Total — no NBA marker
- NBA  `KXNBA4QTEAMTOTAL` NBA 4th Quarter Team Total — ticker prefix KXNBA
- NBA  `KXNBASPORTSMANSHIP` NBA Sportsmanship Award — ticker prefix KXNBA
- skip `KXTNCBASKETBALL` TNC Basketball — no NBA marker
- skip `KXWNBASECONDTEAM` Women's Pro Basketball Second Team — non-NBA basketball marker 'WNBA'
- skip `KXEUROCUPGAME` EuroCup Basketball Game — no NBA marker
- skip `KXWNBAPTSRECORD` Women's Pro Basketball Single-Game Scoring Record — non-NBA basketball marker 'WNBA'
- skip `KXNBL` Australia NBL Champion — no NBA marker
- skip `KXRONENBAR` Ronen bar dismissed — no NBA marker
- skip `KXLEADERWNBAAST` WNBA APG Leader — non-NBA basketball marker 'WNBA'
- skip `KXDUNKMAN` Dunkman World Championships Winner — no NBA marker
- NBA  `KXTEAMSINNBAF` Teams in NBA Finals — title mentions NBA
- skip `KXQUADRUPLEDOUBLE` Quadruple Double — no NBA marker
- NBA  `KXNBAATLANTIC` Pro Basketball Atlantic Division Winner — ticker prefix KXNBA
- NBA  `KXNBAEXEC` NBA Executive of the Year — ticker prefix KXNBA
- skip `KXCZENBLGAME` Czech NBL Game — no NBA marker
- skip `KXESPYWNBA` BEST WNBA PLAYER‬‭ — non-NBA basketball marker 'WNBA'
- skip `CBVOLUME` Coinbase volume — no NBA marker
- skip `KXNCAAMBNEC` Northeast Conference Tournament — no NBA marker
- NBA  `KXNBASTATLEADER` NBA Regular Season League Leader — ticker prefix KXNBA
- skip `KXNCAAMBSUN` Atlantic Sun Conference Tournament — no NBA marker
- skip `KXNCAAWB1Q` Women's College Basketball 1st Quarter Winner — no NBA marker
- NBA  `KXNBADRAFTTOP5` NBA Draft Top 5 Pick — ticker prefix KXNBA
- NBA  `KXPLAYEROPTIONNBA` player option nba — title mentions NBA
- skip `KXNCAAMBCOTY` Men's College Basketball Naismith Coach of the Year — no NBA marker
- skip `KXWNBA3QWINNER` Women's Pro Basketball 3rd Quarter Winner — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAPLAYOFFPTS` NBA Playoffs Player Points — ticker prefix KXNBA
- NBA  `KXNBADRAFTTOP10` NBA Draft Top 10 Pick — ticker prefix KXNBA
- skip `KXNCAAMBBIGEASTQUAL` Men's College Basketball Big East Championship Qualifiers — no NBA marker
- skip `KXSLBTOTAL` England Super League Basketball Total — no NBA marker
- skip `KXISLSPREAD` Israel Super League Spread — no NBA marker
- NBA  `KXNBASEED` NBA Playoff Seed — ticker prefix KXNBA
- skip `KXNCAAMBTOPAPRANK` Men's College Basketball AP Poll Top Rank — no NBA marker
- skip `KXWCCREG` West Coast Conference Regular Season Champions — no NBA marker
- skip `KXNBLGAME` Australia NBL Game — no NBA marker
- NBA  `KXNBAPTSLEADER` NBA Game Points Leader — ticker prefix KXNBA
- NBA  `KXNBAGAMEHIGHSCORE` NBA Highest Scoring Game of the Season — ticker prefix KXNBA
- skip `KXNCAAMBMOP` Men's College Basketball Most Outstanding Player — no NBA marker
- skip `KXSLBSPREAD` England Super League Basketball Spread — no NBA marker
- skip `KXEUROCUPTOTAL` EuroCup Basketball Total — no NBA marker
- skip `KXNCAAWB2HTEAMTOTAL` Women's College Basketball 2nd Half Team Total — no NBA marker
- skip `KXBBINTLGAME` International Friendly Game — no NBA marker
- NBA  `KXNBA2H` NBA 2nd Half Winner — ticker prefix KXNBA
- skip `KXNCAAMBHOR` Horizon League Conference Tournament — no NBA marker
- NBA  `KXNBASERIESPTSSPREAD` Pro Basketball Series Points Spread — ticker prefix KXNBA
- skip `KXNCAAMBTOTAL` Men's College Basketball Total Points — no NBA marker
- skip `KXPBAGAME` Philippines PBA Game — no NBA marker
- NBA  `KXNBANEXTCONTRACT` Pro Basketball Next Contract Size — ticker prefix KXNBA
- skip `KXNCAABGAME` College Basketball Game — no NBA marker
- skip `KXCBA` China CBA Champion — no NBA marker
- skip `KXLPBGAME` Portugal LPB Game — no NBA marker
- NBA  `KXNBALASTTOLOSE` NBA Last Undefeated Team — ticker prefix KXNBA
- NBA  `KXNBASERIESPTSLEADER` Pro Basketball Series Points Leader — ticker prefix KXNBA
- skip `KXNCAAMBMW` Mountain West Conference Tournament — no NBA marker
- skip `KXNCAAMBWINMARGIN` Men's College Basketball Winning Margin — no NBA marker
- NBA  `KXNBASUMMER1HSPREAD` Pro Basketball Summer League 1st Half Spread — ticker prefix KXNBA
- NBA  `KXNBASUMMERGAME` Pro Basketball Summer League Game — ticker prefix KXNBA
- NBA  `KXNBAEUROPEANNOUNCE` NBA Europe Inaugural Season Being Announced — ticker prefix KXNBA
- NBA  `KXNBA3RDTEAM` All-NBA 3rd Team — ticker prefix KXNBA
- NBA  `KXNBA2QTEAMTOTAL` NBA 2nd Quarter Team Total — ticker prefix KXNBA
- NBA  `KXLEADERNBAAST` NBA APG Leader — title mentions NBA
- skip `KXWNBA3QSPREAD` Women's Pro Basketball 3rd Quarter Spread — non-NBA basketball marker 'WNBA'
- NBA  `KXNBADRAFT9` NBA Draft Ninth Pick — ticker prefix KXNBA
- NBA  `KXNBAPTSPROT` NBA Player Points Protected — ticker prefix KXNBA
- skip `KXSPBGAME` Venezuela Superliga Game — no NBA marker
- NBA  `KXNBACUPMVP` NBA Cup Tournament MVP — ticker prefix KXNBA
- skip `KXNCAAWBUNDEFEATEDHOME` Women's College Basketball Teams to go Undefeated at Home — no NBA marker
- skip `KXABA` Adriatic ABA Champion — no NBA marker
- skip `KXWFIBATOTAL` Women's FIBA Total — no NBA marker
- skip `KXVTBTOTAL` Russia VTB United Total — no NBA marker
- skip `KXLNBPSPREAD` LNBP Spread — no NBA marker
- skip `KXNCAAMBNAISMITH` Men's College Basketball Naismith — no NBA marker
- skip `KXBNXTDGAME` BNXT Dutch League Game — no NBA marker
- NBA  `KXNBADRAFTMATCHUP` Pro Basketball Draft Matchup — ticker prefix KXNBA
- skip `KXSBLGAME` Slovakia SBL Game — no NBA marker
- NBA  `KXNBARACE` NBA Race to Points — ticker prefix KXNBA
- NBA  `KXNBADRAFT6` NBA Draft Sixth Pick — ticker prefix KXNBA
- NBA  `KXNBASTOCK` NBA Player Steals + Blocks — ticker prefix KXNBA
- skip `KXCHINAUNBANBTC` Will China unban Bitcoin? — no NBA marker
- NBA  `KXNBADRAFTTOP25` NBA Draft Top 25 Pick — ticker prefix KXNBA
- skip `KXWNBANEXTCOMMISH` Women's Pro Basketball Next Commissioner — non-NBA basketball marker 'WNBA'
- NBA  `KXNBASERIESROADWIN` NBA Series 1st Road Win — ticker prefix KXNBA
- skip `KXKBLGAME` Korea KBL Game — no NBA marker
- NBA  `KXNBA3PTCONTEST` NBA 3-Point Contest Winner — ticker prefix KXNBA
- skip `KXNCAAMB1H` Men's College Basketball 1st Half Winner — no NBA marker
- skip `KXNCAAWB2Q` Women's College Basketball 2nd Quarter Winner — no NBA marker
- skip `KXEBBALLGAME` eBasketball Game — no NBA marker
- NBA  `KXNBADRAFTTOP15` NBA Draft Top 15 Pick — ticker prefix KXNBA
- skip `KXNCAABBIG12` Big 12 Men's Basketball Tournament — no NBA marker
- NBA  `KXNBA2HWINNER` Pro Basketball 2nd Half Winner — ticker prefix KXNBA
- NBA  `KXNBASERIESOT` Pro Basketball Series Overtime — ticker prefix KXNBA
- NBA  `KXNBAMATCHUP` NBA Matchup — ticker prefix KXNBA
- NBA  `KXNBAPLAYOFFWINS` NBA Playoff Wins by Team — ticker prefix KXNBA
- NBA  `KXNBAASSTARTERS` NBA All-Star Starters — ticker prefix KXNBA
- NBA  `KXNBAHIGHESTSCORING` NBA Player with the Highest Scoring Game — ticker prefix KXNBA
- skip `KXNCAAMBSTATLEADER` Men's College Basketball Stat Leader — no NBA marker
- NBA  `KXMEDIACOVERNBA2K` WHO WILL BE ON THE COVER OF NBA 2K — title mentions NBA
- NBA  `KXNBADPOY` NBA Defensive Player of the Year — ticker prefix KXNBA
- NBA  `KXNBATOPPICK` Pro Basketball Draft Lottery Winner — ticker prefix KXNBA
- skip `KXSNAPELECTIONBAHA` Bhamanian election — no NBA marker
- skip `KXNCAAMBSOCON` Southern Conference Tournament — no NBA marker
- skip `KXSHAI20PTREC` Shai 20+ Point Streak — no NBA marker
- skip `KXMARMADCONF` March Madness Conference — no NBA marker
- skip `KXWNBADPOY` WNBA Defensive Player of the Year — non-NBA basketball marker 'WNBA'
- NBA  `KXNBA30COMEBACK` NBA 3-0 Series Comeback — ticker prefix KXNBA
- NBA  `KXNBAROOKIE2NDTEAM` NBA All-Rookie 2nd Team — ticker prefix KXNBA
- skip `KXNCAAWBTOPAPRANK` Women's College Basketball AP Poll Top Rank — no NBA marker
- skip `KXWNBA7FIGS` 7 Figure WNBA salary — non-NBA basketball marker 'WNBA'
- NBA  `KXNBACENTRAL` Pro Basketball Central Division Winner — ticker prefix KXNBA
- NBA  `KXNBA3QWINNER` NBA 3rd Quarter Winner — ticker prefix KXNBA
- NBA  `KXNBAESCALATOR3PT` NBA Player Threes Escalator — ticker prefix KXNBA
- skip `KXWNBADRAFTTOP3` WNBA Draft Top 3 — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAREB` NBA Player Rebounds — ticker prefix KXNBA
- NBA  `KXNBANHL` NBA + NHL Champion Combo — ticker prefix KXNBA
- skip `KXBIG12REG` Big 12 Regular Season Champions — no NBA marker
- skip `KXWSBLGAME` Sweden SBL Game — no NBA marker
- skip `KXNCAAMBCBC` Men's College Basketball Crown Winner — no NBA marker
- NBA  `KXNBANEWCHAMP` NBA First-Time Champion — ticker prefix KXNBA
- skip `KXWNBADUNK` Women's Pro Basketball Player to Dunk — non-NBA basketball marker 'WNBA'
- skip `KXBSLTOTAL` Turkey BSL Total — no NBA marker
- NBA  `KXNBA2QSPREAD` NBA 2nd Quarter Spread — ticker prefix KXNBA
- skip `KXNCAAMBCONFLEADER` Men's College Basketball Conference Stat Leader — no NBA marker
- NBA  `KXMVENBAMULTIGAMEEXTENDED` MVE NBA Multi Game — title mentions NBA
- skip `KXLKLGAME` LKL Lithuania Game — no NBA marker
- NBA  `KXNBA3PTALLGAMES` Pro Basketball 3-Pointers in Every Game — ticker prefix KXNBA
- NBA  `KXTRUMPNBAFINALS` Trump NBA finals — title mentions NBA
- NBA  `KXNBA1QTEAMTOTAL` NBA 1st Quarter Team Total — ticker prefix KXNBA
- NBA  `KXNBAFINALSVIEWER` NBA finals viewership — ticker prefix KXNBA
- skip `KXWNBA3PT` Women's Pro Basketball Player Threes — non-NBA basketball marker 'WNBA'
- skip `KXNCAAWB2QSPREAD` Women's College Basketball 2nd Quarter Spread — no NBA marker
- skip `KXEBASKETBALLGAME` eBasketball Game — no NBA marker
- skip `KXEARNINGSMENTIONBAC` Bank of America Earnings Mention — no NBA marker
- NBA  `KXNBA2NDTEAM` All-NBA 2nd Team — ticker prefix KXNBA
- skip `KXWNBAGAME` Women's Pro Basketball Game — non-NBA basketball marker 'WNBA'
- skip `KXNCAAWB4QTOTAL` Women's College Basketball 4th Quarter Total — no NBA marker
- NBA  `KXNBASLAMDUNK` NBA Slam Dunk Contest Winner — ticker prefix KXNBA
- NBA  `KXNBAMOSTWINS` Pro Basketball Highest Win Total — ticker prefix KXNBA
- skip `KXWNBAALLROOKIE` Women's Pro Basketball All-Rookie Team — non-NBA basketball marker 'WNBA'
- skip `KXNCAAMBBSOU` Big South Conference Tournament — no NBA marker
- skip `KXNCAAMBWAC` Western Athletic Conference Tournament — no NBA marker
- NBA  `KXNBASERIESGAMES` NBA Series Total Games — ticker prefix KXNBA
- NBA  `KXNBASUMMERMVP` Pro Basketball Summer League MVP — ticker prefix KXNBA
- NBA  `KXNBALOTTERY` NBA Draft Lottery Picks — ticker prefix KXNBA
- skip `KXFIBAECUPSPREAD` FIBA Europe Cup Spread — no NBA marker
- NBA  `KXNBADRAFTINT` Pro Basketball International Players Drafted — ticker prefix KXNBA
- skip `KXNCAAMBMAA` Metro Atlantic Conference Tournament — no NBA marker
- skip `KXWNBASPREAD` Women's Pro Basketball Spread — non-NBA basketball marker 'WNBA'
- skip `KXBBLTOTAL` Germany BBL Total — no NBA marker
- NBA  `KXNBA1QTOTAL` NBA 1st Quarter Total — ticker prefix KXNBA
- skip `KXWNBLGAME` NBL Australia (W) Game — no NBA marker
- skip `KXNEXTTEAMLEBRON` Lebron's Next Team — no NBA marker
- skip `KXEUROLEAGUE` EuroLeague Champion — no NBA marker
- skip `KXFIBAGAME` FIBA Game — no NBA marker
- skip `KXWNBAOT` Women's Pro Basketball Overtime — non-NBA basketball marker 'WNBA'
- NBA  `KXNBA1HTOTAL` NBA 1st Half Total — ticker prefix KXNBA
- skip `KXMARMADSEEDWIN` March Madness Seed Win — no NBA marker
- skip `KXEUROLEAGUEGAME` Euroleague Game — no NBA marker
- NBA  `KXNFLNBA` NFL and NBA Champion Combo — title mentions NBA
- NBA  `KXNBA2HTOTAL` NBA 2nd Half Total — ticker prefix KXNBA
- skip `KXNCAAWB4Q` Women's College Basketball 4th Quarter Winner — no NBA marker
- NBA  `KXNBADRAFTPICK` Pro Basketball Draft Pick — ticker prefix KXNBA
- skip `KXWNBAROOKAS` Women's Pro Basketball Rookie to be an All-Star — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAEXTENSION` NBA Player Contract Extension — ticker prefix KXNBA
- NBA  `KXFIRSTPICKNBA` NBA first pick — title mentions NBA
- NBA  `KXNBA1HWINNER` Pro Baskeball 1st Half Winner — ticker prefix KXNBA
- skip `KXWNBA1HWINNER` Women's Pro Basketball 1st Half Winner — non-NBA basketball marker 'WNBA'
- skip `KXLEADERWNBAREB` WNBA RPG Leader — non-NBA basketball marker 'WNBA'
- NBA  `KXNBA` Pro Basketball Champion — ticker prefix KXNBA
- skip `KXNCAAWB2HSPREAD` Women's College Basketball 2nd Half Spread — no NBA marker
- skip `KXNCAAMBD3GAME` Men's College Basketball D3 Game — no NBA marker
- skip `KXMWIAINTCOMINBACK` I Ain’t Comin’ Back total streams — no NBA marker
- NBA  `KXNBASUMMER1HTOTAL` Pro Basketball Summer League 1st Half Total — ticker prefix KXNBA
- NBA  `KXNBA3Q` NBA 3rd Quarter Winner — ticker prefix KXNBA
- skip `KXPHKLGAME` Croatia Premijer Liga Game — no NBA marker
- skip `KXWNBAMIMP` WNBA Most Improved Player of the Year — non-NBA basketball marker 'WNBA'
- skip `KXNCAAMBIG12` Big 12 MEN'S BASKETBALL TOURNAMENT — no NBA marker
- skip `KXSECREG` SEC Regular Season Champions — no NBA marker
- skip `KXMWREG` Mountain West Regular Season Champions — no NBA marker
- skip `KXWNBA` WNBA Championship — non-NBA basketball marker 'WNBA'
- skip `KXNCAAWB1HSPREAD` Women's College Basketball 1st Half Spread — no NBA marker
- skip `KXWNBATOTAL` Women's Pro Basketball Total — non-NBA basketball marker 'WNBA'
- skip `KXNCAAMB2ML` College Basketball 2-Moneyline Combo — no NBA marker
- skip `KXKLSGAME` Serbia KLS Game — no NBA marker
- NBA  `KXNBAFTM` NBA Player Free Throws Made — ticker prefix KXNBA
- skip `KXNEXTTEAMCHRISPAUL` Next Team Chris Paul — no NBA marker
- skip `KXNCAAWBH` NCAA Women's Basketball Half Winners — no NBA marker
- NBA  `KXNBAPLAYERDEAL` Next Pro Basketball Brand Deal — ticker prefix KXNBA
- skip `KXWNBAWORSTREC` Women's Pro Basketball Worst Record — non-NBA basketball marker 'WNBA'
- skip `KXWNBALAWSUIT` Women's Pro Basketball Lawsuit — non-NBA basketball marker 'WNBA'
- skip `KXNCAAWBBBBB` NCAAWB Conference Champions — no NBA marker
- skip `KXNCAAMBRACE` Men's College Basketball Race to Points — no NBA marker
- skip `KXNCAAMBSBELT` Sun Belt Conference Tournament — no NBA marker
- skip `KXWNBA3PTROUND` Women's Pro Basketball 3-Point Contest Round Qualifiers — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAPR` Pro Basketball Player Points + Rebounds — ticker prefix KXNBA
- NBA  `KXALBUMRELEASEDATENBAYOUNGBOY` Will NBA Youngboy release a new album? — title mentions NBA
- NBA  `KXNBAPREPACK2ML` 2 ML Basketball Combo — ticker prefix KXNBA
- skip `KXARGLNBGAME` Liga Nacional de Basquetbol Game — no NBA marker
- skip `KXNCAAMBFIRST3PT` Men's College Basketball First Team to Make a Three — no NBA marker
- NBA  `KXNBASTARTERS` Pro Basketball Starting Lineup — ticker prefix KXNBA
- skip `KXWNBACCUP` WNBA Commissioner's Cup Winner — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAONE3PT` NBA Players to Make One Three — ticker prefix KXNBA
- NBA  `KXNBA1STTEAMDEF` NBA All-Defensive 1st Team — ticker prefix KXNBA
- skip `KXNCAAWBSEC` Women's College Basketball SEC Conference Tournament Champion — no NBA marker
- NBA  `KXNBAPOLOSE` Pro Basketball Playoff Losses — ticker prefix KXNBA
- skip `KXFIBACHAMPLEAGUEGAME` FIBA Champions League Game — no NBA marker
- skip `KXMAKEMARMAD` Make March Madness Tournament — no NBA marker
- NBA  `KXNBAUNBEATEN` NBA Playoffs Team to go Undefeated — ticker prefix KXNBA
- skip `KXWNBA1H` Women's Pro Basketball 1st Half Winner — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAWEST` Pro Basketball Western Conference Champion — ticker prefix KXNBA
- skip `KXNCAAMBOV` Ohio Valley Conference Tournament — no NBA marker
- skip `KXBIGEASTREG` Big East Regular Season Champions — no NBA marker
- skip `KXWNBAPORTNOY` WNBA Portnoy ban — non-NBA basketball marker 'WNBA'
- skip `KXEUROCUPSPREAD` EuroCup Basketball Spread — no NBA marker
- skip `KXWMARMADROUND` Reach March Madness Round — no NBA marker
- NBA  `KXNBARISINGSTARS` Pro Basketball Rising Stars Tournament — ticker prefix KXNBA
- skip `KXBBWSERIEAGAME` Italy Serie A (W) Game — no NBA marker
- NBA  `KXNBAPRA` NBA Player Points + Rebounds + Assists — ticker prefix KXNBA
- NBA  `KXNBAFINMVP` NBA Finals MVP — ticker prefix KXNBA
- NBA  `KXNBAFIRSTBASKET` Pro Basketball First Basket — ticker prefix KXNBA
- skip `KXWNBA2QTOTAL` Women's Pro Basketball 2nd Quarter Total — non-NBA basketball marker 'WNBA'
- NBA  `KXNBADRAFT10` NBA Draft Tenth Pick — ticker prefix KXNBA
- NBA  `KXNBACONF` NBA Conference to Win the Championship — ticker prefix KXNBA
- skip `KXWNBA1SEED` Women's Pro Basketball #1 Seed — non-NBA basketball marker 'WNBA'
- skip `KXWNBA4QSPREAD` Women's Pro Basketball 4th Quarter Spread — non-NBA basketball marker 'WNBA'
- skip `KXEARNINGSMENTIONBA` Boeing Earnings Call — no NBA marker
- skip `KXNCAAWBSPREAD` Women's College Basketball Spread — no NBA marker
- skip `KXLNBPGAME` LNBP Basketball Game — no NBA marker
- NBA  `KXNBAGAMES` NBA games — ticker prefix KXNBA
- skip `KXNCAAMBBSKY` Big Sky Conference Tournament — no NBA marker
- skip `KXNCAAMBCONFAWARD` Men's College Basketball Conference Awards — no NBA marker
- NBA  `KXNBA2D` NBA Player Double Double — ticker prefix KXNBA
- NBA  `KXNBACOTM` NBA Coach of the Month — ticker prefix KXNBA
- NBA  `KXNBANORTHWEST` Pro Basketball Northwest Division Winner — ticker prefix KXNBA
- NBA  `KXNBAPLAYTOGETHER` Pro Basketball Players to Play Together — ticker prefix KXNBA
- skip `KXNCAAMBA10` Atlantic-10 Conference Tournament — no NBA marker
- skip `KXWNBA1QWINNER` Women's Pro Basketball 1st Quarter Winner — non-NBA basketball marker 'WNBA'
- NBA  `KXNBASERIES` NBA Series Winner — ticker prefix KXNBA
- NBA  `KXNBAH2HBENCHPTS` NBA Head-to-Head Bench Points — ticker prefix KXNBA
- skip `KXWNBAWEST1` Women's Pro Basketball Western Conference #1 Seed — non-NBA basketball marker 'WNBA'
- skip `KXTRADEOFFNBA` Pro basketball trades offseason — no NBA marker
- NBA  `KXNBA3PEAT` Pro Basketball Three-Peat Champion — ticker prefix KXNBA
- skip `KXNCAABBIG10` Big Ten Men's Basketball Tournament — no NBA marker
- NBA  `KXNBATEAMANNOUNCE` Pro Basketball New Team Announce — ticker prefix KXNBA
- skip `KXWFIBAGAME` Women's FIBA Game — no NBA marker
- skip `KXFIBACHAMPGAME` FIBA Champions League Game — no NBA marker
- skip `KXBIHD1GAME` Bosnia Division I Game — no NBA marker
- skip `KXNCAAWBGAME` Women's College Basketball Game — no NBA marker
- skip `KXVBAGAME` Vietnam VBA Game — no NBA marker
- skip `KXNCAAMBCAA` Coastal Athletic Association Conference Tournament — no NBA marker
- skip `KXKYBOURBONBARRELS` Kentucky aging Bourbon-barrel inventory — no NBA marker
- skip `KXBALGAME` Basketball Africa League Game — no NBA marker
- skip `KXWMARMAD` March Tournament (W) — no NBA marker
- skip `KXSKLGAME` Slovenia 1. SKL Game — no NBA marker
- skip `KXCOVEREA` Cover EA college sports — no NBA marker
- skip `KXNCAAMBBOTHQUAL` Men's College Basketball Both Teams to Qualify — no NBA marker
- NBA  `KXNBASOUTHEAST` Pro Basketball Southeast Division Winner — ticker prefix KXNBA
- skip `KXWNBAH2HPTS` Women's Pro Basketball Head to Head Points — non-NBA basketball marker 'WNBA'
- skip `KXLNBELITETOTAL` LNB Elite Total — no NBA marker
- NBA  `KXNBASERIESREBLEADER` Pro Basketball Series Rebounds Leader — ticker prefix KXNBA
- NBA  `KXNBA2Q` NBA 2nd Quarter Winner — ticker prefix KXNBA
- skip `KXMARMADCONFWIN` March Madness Conference Winner — no NBA marker
- skip `KXNCAAMBFIRST10` Men's College Basketball Race to 10 Points — no NBA marker
- NBA  `KXNBAH2HPTS` NBA Head-to-Head Points — ticker prefix KXNBA
- skip `KXNCAAMBBIG10` Big Ten Conference Tournament — no NBA marker
- skip `KXNCAAMBNIT` Men's NIT Tournament Champion — no NBA marker
- NBA  `KXNBANEXTTEAMCONF` Pro Basketball Next Team Conference — ticker prefix KXNBA
- skip `KXNCAAMBUNDEFEATED` Undefeated in College Basketball Regular Season — no NBA marker
- skip `KXWNBAALLSTARS` Women's Pro Basketball All-Star Selections — non-NBA basketball marker 'WNBA'
- NBA  `KXNBACOACHOUT` Pro Basketball Coaches Out — ticker prefix KXNBA
- NBA  `KXNBARA` Pro Basketball Player Rebounds + Assists — ticker prefix KXNBA
- NBA  `KXNBABENCHPTS` NBA Bench Points — ticker prefix KXNBA
- skip `KXBSNGAME` Puerto Rico BSN Basketball Game — no NBA marker
- NBA  `KXNBASUMMER` Pro Basketball Summer League Champion — ticker prefix KXNBA
- skip `KXLUBGAME` Uruguay LUB Basketball Game — no NBA marker
- skip `KXWNBAALLTEAM` Women's Pro Basketball Teams — non-NBA basketball marker 'WNBA'
- NBA  `KXNBADRAFTOU` Pro Basketball Players Draft Position — ticker prefix KXNBA
- NBA  `KXNBACELEBRITYGAME` Pro Basketball All-Star Celebrity Game — ticker prefix KXNBA
- skip `KXBSLSPREAD` Turkey BSL Spread — no NBA marker
- skip `KXBBLSPREAD` Germany BBL Spread — no NBA marker
- skip `KXSOWBBALLGAME` Summer Olympics Women's Basketball Game — no NBA marker
- skip `KXNCAAMBBIG10REG` Men's College Basketball Big Ten Regular Season Champion — no NBA marker
- skip `KXGOLDENBACHELOR` who will win the gold bachelor — no NBA marker
- skip `KXWENBACONATOR` Average price of a Wendy's Baconator in [month] — no NBA marker
- skip `KXNCAAMBUSA` Conference USA Conference Tournament — no NBA marker
- skip `KXWNBADRAFT5` WNBA Draft 5th Pick — non-NBA basketball marker 'WNBA'
- skip `KXWNBA3QTOTAL` Women's Pro Basketball 3rd Quarter Total — non-NBA basketball marker 'WNBA'
- skip `KXCOINA` Coinbase Annual KPI — no NBA marker
- skip `KXNCAAMBIGTEN` big ten MEN'S BASKETBALL TOURNAMENT — no NBA marker
- skip `KXWNBACCUPMVP` WNBA Commissioner's Cup MVP — non-NBA basketball marker 'WNBA'
- skip `KXDBBGAME` Deutscher Basketball Bund (DBB) Game — no NBA marker
- skip `KXNCAAMIVYLEAGUE` Ivy League MEN'S BASKETBALL TOURNAMENT — no NBA marker
- skip `KXDBBFGAME` Denmark Basketligaen Game — no NBA marker
- skip `KXSPORTSIGNLBJ` LeBron James sign — no NBA marker
- skip `KXWMARMADSEED` Women's College Basketball Tournament Seeds — no NBA marker
- skip `KXBSLGAME` Turkey BSL Game — no NBA marker
- NBA  `KXNBACOY` NBA Coach of the Year — ticker prefix KXNBA
- skip `KXNCAAWB1HTOTAL` Women's College Basketball 1st Half Total — no NBA marker
- NBA  `KXCOACHOUTNBA` NBA Coach Out — title mentions NBA
- skip `KXOTDBASKETBALL` Off The Dribble Basketball — no NBA marker
- skip `KXSTEPHDEAL` Steph Curry Endorsement Deal — no NBA marker
- NBA  `KXNBAFINBLOWOUT` Pro Basketball Finals Blowout — ticker prefix KXNBA
- skip `KXABAGAME` Adriatic ABA Game — no NBA marker
- skip `KXNCAAWB3QSPREAD` Women's College Basketball 3rd Quarter Spread — no NBA marker
- NBA  `KXNBA2QWINNER` NBA 2nd Quarter Winner — ticker prefix KXNBA
- skip `KXGRAMBPRNBA` Best Progressive R&B Album — no NBA marker
- skip `KXNCAAMBGAME` Men's College Basketball Game — no NBA marker
- skip `KXNCAAMBBWEST` Big West Conference Tournament — no NBA marker
- NBA  `KXNBAWINS` Pro Basketball Win Totals — ticker prefix KXNBA
- NBA  `KXNBADRAFT5` NBA Draft Fifth Pick — ticker prefix KXNBA
- skip `KXAACREG` AAC Regular Season Champions — no NBA marker
- skip `KXNCAAMACC` ACC MEN'S BASKETBALL TOURNAMENT — no NBA marker
- skip `KXWNBA4QTOTAL` Women's Pro Basketball 4th Quarter Total — non-NBA basketball marker 'WNBA'
- NBA  `KXNBASJC` NBA Social Justice Champion — ticker prefix KXNBA
- NBA  `KXNBAPLAYIN` Which Team Will Make the Play-In Tournament — ticker prefix KXNBA
- NBA  `KXNBAWCFQUAL` NBA Western Conference Finals Qualifiers — ticker prefix KXNBA
- NBA  `KXNBAGAME7` NBA Series that Go to a Game 7 — ticker prefix KXNBA
- skip `KXABNBA` Airbnb Annual KPI — no NBA marker
- skip `KXEUROBASKETSPREAD` EuroBasket Spread — no NBA marker
- NBA  `KXNBASTL` NBA Player Steals — ticker prefix KXNBA
- skip `KXPLAYTOGETHERJBJT` Tatum and Brown Celtics — no NBA marker
- NBA  `KXNBAALLSTARGAME` NBA All-Star Game Winner — ticker prefix KXNBA
- skip `KXWNBAPLAYOFFHOST` Women's Pro Basketball Playoff Home Games — non-NBA basketball marker 'WNBA'
- skip `KXNCAAMBTEAMTOTAL` Men's College Basketball Team Total — no NBA marker
- skip `KXNCAAMBACCQUAL` Men's College Basketball ACC Championship Qualifiers — no NBA marker
- skip `KXLEBRONPLAY` LeBron Next Play — no NBA marker
- skip `KXNCAABMENTION` College Basketball — no NBA marker
- skip `KXNCAAMB1HWINNER` College Basketball 1H Winner — no NBA marker
- skip `KXMARMAD1SEED` March Madness 1 Seeds — no NBA marker
- NBA  `KXNBA4QTOTAL` NBA 4th Quarter Total — ticker prefix KXNBA
- skip `KXWNBA1QTOTAL` Women's Pro Basketball 1st Quarter Total — non-NBA basketball marker 'WNBA'
- NBA  `KXNBADRAFTTOP` Pro Basketball Top Draft — ticker prefix KXNBA
- NBA  `KXNBA3PT` NBA Player Threes — ticker prefix KXNBA
- skip `KXWNBA2HTOTAL` Women's Pro Basketball 2nd Half Total — non-NBA basketball marker 'WNBA'
- NBA  `KXLEADERNBABLK` NBA BPG Leader — title mentions NBA
- skip `KXWNBAASGAME` WNBA All Star Game — non-NBA basketball marker 'WNBA'
- skip `KXWMARMAD1SEED` Women's March Madness 1 Seeds — no NBA marker
- skip `KXLKLSPREAD` LKL Lithuania Spread — no NBA marker
- skip `KXWFIBAWC` Women's FIBA World Cup Winner — no NBA marker
- NBA  `KXNBAECFQUAL` NBA Eastern Conference Finals Qualifiers — ticker prefix KXNBA
- NBA  `KXNBASIXTH` NBA Sixth Man of the Year — ticker prefix KXNBA
- skip `KXWNBAWEST` Women's Pro Basketball Western Conference Champion — non-NBA basketball marker 'WNBA'
- skip `KXNCAAMBSGP` College Basketball Same Game Parlay — no NBA marker
- skip `KXNCAAMBPAT` Patriot League Conference Tournament — no NBA marker
- NBA  `KXNBAFIRST50PTS` First NBA Player to Score 50 Points — ticker prefix KXNBA
- NBA  `KXTEAMSINNBAWF` Teams in NBA Western Conference Finals — title mentions NBA
- skip `KXSPORTSOWNERLBJ` LBJ owning team — no NBA marker
- skip `KXWINSTREAKOKC` OKC Win Streak — no NBA marker
- skip `KXNCAAWB1QTOTAL` Women's College Basketball 1st Quarter Total — no NBA marker
- skip `KXCOINBASE` Coinbase KPI — no NBA marker
- NBA  `KXNBAWINMARGIN` NBA Win Margin — ticker prefix KXNBA
- skip `KXWNBAPLAYOFF` Women's Pro Basketball Playoff Qualifiers — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAALLSTARMVP` NBA All-Star Game MVP — ticker prefix KXNBA
- NBA  `KXNEXTNBACOACH` Who is the Next NBA Coach of Team — title mentions NBA
- skip `KXNCAAMBBIG10REGTOP` Men's College Basketball Big Ten Regular Season Top Finishers — no NBA marker
- skip `KXUNRIVALEDGAME` Unrivaled Basketball Game — no NBA marker
- NBA  `KXNBAPLAYOFF` Pro Basketball Playoff Qualifier — ticker prefix KXNBA
- skip `KXCEBLGAME` Canadian Elite Basketball League Game — no NBA marker
- NBA  `KXNBATEAMTOTAL` NBA Team Total — ticker prefix KXNBA
- NBA  `KXESPYNBA` BEST NBA PLAYER‬ — title mentions NBA
- skip `KXJBLEAGUEGAME` Japan B League Game — no NBA marker
- skip `KXAUTBSLGAME` Austria BSL Game — no NBA marker
- NBA  `KXNBA2HTEAMTOTAL` NBA 2nd Half Team Total — ticker prefix KXNBA
- skip `KXBANXNUBCAT` WILL NUCAT BE UNBANNED — no NBA marker
- skip `KXWNBANEXTTEAM` Women's Pro Basketball Next Team — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAASTPROT` NBA Player Assists Protected — ticker prefix KXNBA
- skip `KXNCAABBIGTEN` Big Ten Men's Basketball Tournament — no NBA marker
- NBA  `KXNBA3QTEAMTOTAL` NBA 3rd Quarter Team Total — ticker prefix KXNBA
- skip `KXBBSERIEATOTAL` Italy Serie A Total — no NBA marker
- NBA  `KXNBAFIRSTOPPONENT` Pro Basketball First Opponent of the Season — ticker prefix KXNBA
- NBA  `KXNBACUP1STTEAM` NBA Cup All-Tournament Team — ticker prefix KXNBA
- skip `KXNCAAMBBIGTENREGTOP` Men's College Basketball Big Ten Regular Season Top Finishers — no NBA marker
- NBA  `KXNBADRAFT3` NBA Draft Third Pick — ticker prefix KXNBA
- NBA  `KXNBAGAMESPECIALS` Pro Basketball Game Specials — ticker prefix KXNBA
- NBA  `KXNBAH2HPRA` NBA Head-to-Head Points, Rebounds and Assists — ticker prefix KXNBA
- NBA  `KXNBASUMMERTOTAL` Pro Basketball Summer League Total — ticker prefix KXNBA
- skip `KXWNBA2H` Women's Pro Basketball 2nd Half Winner — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAPIADVANCE` NBA Play-In Team to Advance — ticker prefix KXNBA
- skip `KXNCAAMBWCC` West Coast Conference Tournament — no NBA marker
- NBA  `KXNEXTCOACHOUTNBA` Next coach out NBA — title mentions NBA
- skip `KXWIBPLGAME` Women's Iceland Premier League Game — no NBA marker
- skip `KXNCAAWB2HTOTAL` Women's College Basketball 2nd Half Total — no NBA marker
- skip `KXNCAAMBBIG12REG` Men's College Basketball Big 12 Regular Season Champion — no NBA marker
- skip `KXNBLSPREAD` Australia NBL Spread — no NBA marker
- skip `KXBBSERIEA2GAME` Italy Serie A2 Game — no NBA marker
- NBA  `KXNBAMENTION` NBA Mention — ticker prefix KXNBA
- skip `KXWNBA2QWINNER` Women's Pro Basketball 2nd Quarter Winner — non-NBA basketball marker 'WNBA'
- skip `KXWNBADRAFTTOP5` WNBA Draft Top 5 — non-NBA basketball marker 'WNBA'
- skip `KXWNBAFINALLOC` WNBA Finals Location — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAPOTM` NBA Player of the Month — ticker prefix KXNBA
- NBA  `KXNBACOMPETE` Pro Basketball Player to Compete — ticker prefix KXNBA
- NBA  `KXCITYNBAEXPAND` Cities NBA expand — title mentions NBA
- NBA  `KXNBADRAFTTRADE` Pro Basketball Draft Trade — ticker prefix KXNBA
- skip `KXBBSERIEBGAME` Italy Serie B Basketball Game — no NBA marker
- skip `KXMARMADUPSET` March Madness Upsets — no NBA marker
- NBA  `KXNBAESCALATORPTS` NBA Player Points Escalator — ticker prefix KXNBA
- skip `KXKMLGAME` Estonia KML Game — no NBA marker
- skip `KXNCAAMBAWARD` Men's College Basketball Awards — no NBA marker
- NBA  `KXNBALOTTERYODDS` NBA Lottery Winner Odds — ticker prefix KXNBA
- skip `KXNCAAMB2HTOTAL` Men's College Basketball 2nd Half Total — no NBA marker
- NBA  `KXNBA1STTEAM` All-NBA 1st Team — ticker prefix KXNBA
- NBA  `KXLEADERNBASTL` NBA SPG Leader — title mentions NBA
- NBA  `KXNBAMVPDPOY` Pro Basketball Player to Win MVP and DPOY — ticker prefix KXNBA
- NBA  `KXNBADRAFTCOMP` Pro Basketball Draft Comparison — ticker prefix KXNBA
- NBA  `KXNBAROY` NBA Rookie of the Year — ticker prefix KXNBA
- skip `KXACCREG` ACC Regular Season Champions — no NBA marker
- skip `KXNCAAWBRACE` Women's College Basketball Race to Points — no NBA marker
- skip `KXLBLGAME` Latvia LBL Game — no NBA marker
- NBA  `KXNBA1HTEAMTOTAL` NBA 1st Half Team Total — ticker prefix KXNBA
- NBA  `KXNBAPLAYERHIGHSCORE` NBA Highest Scoring Performance in Regular Season — ticker prefix KXNBA
- NBA  `KXNBASEEDOU` NBA Playoff Seed Over/Unders — ticker prefix KXNBA
- skip `KXWSESBLGAME` Women's Sweden SBL Game — no NBA marker
- NBA  `KXNBARULE` Pro Basketball Rule — ticker prefix KXNBA
- skip `KXBBSERIEASPREAD` Italy Serie A Spread — no NBA marker
- skip `KXNCAAWBWINMARGIN` Women's College Basketball Winning Margin — no NBA marker
- NBA  `KXNBASWEEP` NBA Teams to Have a Series Sweep — ticker prefix KXNBA
- skip `KXNBLTOTAL` Australia NBL Total — no NBA marker
- NBA  `KXNBA3D` NBA Player Triple Double — ticker prefix KXNBA
- NBA  `KXNBALADDER3PT` NBA Player Threes Ladder — ticker prefix KXNBA
- NBA  `KXNBA1QWINNER` NBA 1st Quarter Winner — ticker prefix KXNBA
- NBA  `KXNBASERIESTOTALPTS` Pro Basketball Series Total Points — ticker prefix KXNBA
- skip `KXNCAAMBMAMER` Mid-American Conference Tournament — no NBA marker
- skip `KXNCAAMBHTEAMTOTAL` Mens College Basketball 1st Half Team Total — no NBA marker
- skip `ZYNBAN` Zyn ban in the United States — no NBA marker
- skip `KXFIBACHAMPSPREAD` FIBA Champions League Spread — no NBA marker
- skip `KXMARMAD` Men's College Basketball Tournament Champion — no NBA marker
- NBA  `KXNBAEAST` Pro Basketball Eastern Conference Champion — ticker prefix KXNBA
- skip `KXNCAAMBSECREGTOP` Men's College Basketball SEC Regular Season Top Finishers — no NBA marker
- skip `KXBIG3GAME` Big 3 Basketball Game — no NBA marker
- skip `KXNCAAMB1HSPREAD` Men's College Basketball 1st Half Spread — no NBA marker
- skip `KXWNBAROTY` Pro Women's Basketball Rookie of the Year — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAPARTNERSHIP` NBA Player Partnership Deal — ticker prefix KXNBA
- skip `KXKBLSPREAD` Korea KBL Spread — no NBA marker
- NBA  `KXLEADERNBAPTS` NBA PPG Leader — title mentions NBA
- skip `KXMVECBCHAMPIONSHIP` MVE College Basketball Championship — no NBA marker
- skip `KXBAN2XRAKAI` 2xRaKai BE UNBANNED — no NBA marker
- skip `KXNCAAWB1H` Women's College Basketball 1st Half Winner — no NBA marker
- NBA  `KXNBAFRANCHISECOST` NBA Franchise Cost — ticker prefix KXNBA
- NBA  `KXNBAREBPROT` NBA Player Rebounds Protected — ticker prefix KXNBA
- skip `KXWNBAAST` Women's Pro Basketball Player Assists — non-NBA basketball marker 'WNBA'
- skip `KXWEUROLEAGUEGAME` EuroLeague (W) Game — no NBA marker
- skip `KXWNBADELAY` WNBA Season Delay — non-NBA basketball marker 'WNBA'
- skip `KXSOWBBALLTOTAL` Summer Olympics Women's Basketball Total — no NBA marker
- NBA  `KXNBAHALLOFFAME` Pro Basketball Hall of Fame — ticker prefix KXNBA
- skip `KXWNBAGAMESPLAYED` WNBA Games Played in a Season — non-NBA basketball marker 'WNBA'
- skip `KXNCAAMBKENPOMTOP` Men's College Basketball KenPom Top Ratings — no NBA marker
- NBA  `KXNBA3QSPREAD` NBA 3rd Quarter Spread — ticker prefix KXNBA
- skip `KXNCAAWBOT` Women's College Basketball Overtime — no NBA marker
- skip `KXCBAGAME` Chinese Basketball Association Game  — no NBA marker
- skip `KXBBALLUSACOACH` Summer Olympics USA Men's Basketball Head Coach — no NBA marker
- skip `KXWNBAMVP` WNBA MVP — non-NBA basketball marker 'WNBA'
- skip `KXNCAAMBBIGTENQUAL` Men's College Basketball Big Ten Championship Qualifiers — no NBA marker
- NBA  `KXNBADRAFT7` NBA Draft Seventh Pick — ticker prefix KXNBA
- skip `KXBIG10REG` Big Ten Regular Season Champions — no NBA marker
- skip `KXWNBASERIESGAMES` WNBA Series Total Games — non-NBA basketball marker 'WNBA'
- NBA  `KXNBASPREAD` NBA Spread — ticker prefix KXNBA
- skip `KXISLGAME` Israel Super League Game — no NBA marker
- NBA  `KXNBAHUSTLE` NBA Hustle Award — ticker prefix KXNBA
- skip `KXNCAAMBBIGTENREG` Men's College Basketball Big Ten Regular Season Champion — no NBA marker
- skip `KXNCAAWBBIGEAST` Women's College Basketball Big East Conference Tournament Champion — no NBA marker
- skip `KXWNBARAISE` WNBA raise — non-NBA basketball marker 'WNBA'
- NBA  `KXNBADPOTM` NBA Defensive Player of the Month — ticker prefix KXNBA
- skip `KXBRIANBAUMGARTNER` How many receipts will Brian Baumgartner process in 8 hours? — no NBA marker
- NBA  `KXNBAFINALSVIEWERGAME7` NBA finals viewership — ticker prefix KXNBA
- NBA  `KXTEAMSINNBAEF` Teams in NBA Eastern Conference Finals — title mentions NBA
- NBA  `KXNBAFINALSEXACT` Pro Basketball Championship Series Score — ticker prefix KXNBA
- skip `KXWNBASERIESSPREAD` WNBA Series Game Spread — non-NBA basketball marker 'WNBA'
- skip `KXNCAAMBBIGEASTREGTOP` Men's College Basketball Big East Regular Season Top Finishers — no NBA marker
- NBA  `KXNBAOVERTIME` NBA Overtime — ticker prefix KXNBA
- skip `KXWNBAROY` WNBA Rookie of the Year — non-NBA basketball marker 'WNBA'
- skip `KXAMAFMRNBA` Favorite Male R&B Artist — no NBA marker
- skip `KXNCAAWB1HTEAMTOTAL` Women's College Basketball 1st Half Team Total — no NBA marker
- NBA  `KXNBADRAFTTOP20` NBA Draft Top 20 Pick — ticker prefix KXNBA
- skip `KXSONICS` Blazers become Sonics — no NBA marker
- NBA  `KXNBADRAFTCAT` Pro Basketball Draft Category — ticker prefix KXNBA
- skip `KXNCAAMBBIG12QUAL` Men's College Basketball Big 12 Championship Qualifiers — no NBA marker
- skip `KXNCAAMBFIRST50` Men's College Basketball Race to 50 Points — no NBA marker
- skip `KXPLEAGUEGAME` Taiwan P. League+ — no NBA marker
- skip `KXNCAABSEC` SEC Men's Basketball Tournament — no NBA marker
- NBA  `KXNBA4QWINNER` NBA 4th Quarter Winner — ticker prefix KXNBA
- NBA  `KXNBAPLAYOFF3D` NBA Playoff Triple-Double — ticker prefix KXNBA
- skip `KXWNBAH2HPRA` Women's Pro Basketball Head to Head Pts + Reb + Ast — non-NBA basketball marker 'WNBA'
- skip `KXWNBAFINALSMVP` WNBA Finals MVP — non-NBA basketball marker 'WNBA'
- skip `KXKNUEPPEL3PTREC` Kon Knueppel Rookie 3pt Record — no NBA marker
- NBA  `KXNBASERIESSPREAD` NBA Series Game Spread — ticker prefix KXNBA
- skip `KXNCAAWBTOTAL` Women's College Basketball Total Points — no NBA marker
- skip `KXKRAKENBANKPUBLIC` Kraken IPO — no NBA marker
- NBA  `KXNBASERIES3PMLEADER` Pro Basketball Series 3-Pointers Made Leader — ticker prefix KXNBA
- skip `KXCBVOLUME` Coinbase volume — no NBA marker
- skip `KXLEADERWNBA3PT` WNBA Total 3-Pointers Made Leader — non-NBA basketball marker 'WNBA'
- NBA  `KXNBASUMMERSPREAD` Pro Basketball Summer League Spread — ticker prefix KXNBA
- skip `KXWNBACOY` WNBA Coach of the Year — non-NBA basketball marker 'WNBA'
- skip `KXWNBAPTS` WNBA Player Points — non-NBA basketball marker 'WNBA'
- skip `KXNCAAWBCONFSTREAK` Women's College Basketball Conference Championship Streak — no NBA marker
- skip `KXNCAAWBSTATLEADER` Women's College Basketball Stat Leader — no NBA marker
- NBA  `KXNBADRAFT8` NBA Draft Eighth Pick — ticker prefix KXNBA
- skip `KXBNXTGAME` BNXT League Game — no NBA marker
- skip `KXGRAMBRNBA` Best R&B Album — no NBA marker
- skip `KXWNBAFINAL` Women's Pro Basketball Finals Qualifiers — non-NBA basketball marker 'WNBA'
- skip `KXNCAAMBAPANY` Men's College Basketball AP Rank Anytime in Season — no NBA marker
- NBA  `KXNBALASVEGAS` Las Vegas NBA team — ticker prefix KXNBA
- skip `KXWCBAGAME` China CBA (W) Game — no NBA marker
- NBA  `KXNBACUPGROUP` NBA Cup Group Winner — ticker prefix KXNBA
- skip `KXTRUMPCANBAN` Trump Canada ban — no NBA marker
- skip `KXNCAAWBNIT` Women's NIT Tournament Champion — no NBA marker
- NBA  `KXNBARELOCATION` Pro Basketball Team Relocation — ticker prefix KXNBA
- NBA  `KXNBANEXTTEAM` Pro Basketball Next Team — ticker prefix KXNBA
- skip `KXVTBGAME` Russia VTB United Game — no NBA marker
- skip `KXKORISLIIGAGAME` Finland Korisliiga Game — no NBA marker
- skip `KXFIBATOTAL` FIBA Total — no NBA marker
- NBA  `KXNBASERIESPTS` Pro Basketball Series Player Points — ticker prefix KXNBA
- skip `KXWNBA3PTCONTEST` Women's Pro Basketball 3-Point Contest — non-NBA basketball marker 'WNBA'
- skip `KXEUROLEAGUETOTAL` EuroLeague Total — no NBA marker
- skip `KXNCAAWBBIG12` Women's College Basketball Big 12 Conference Tournament Champion — no NBA marker
- skip `KXNCAAWBMOP` Women's College Basketball Most Outstanding Player — no NBA marker
- skip `KXNCAAMBSLC` Southland Conference Tournament — no NBA marker
- NBA  `KXNBAWEST1SEED` NBA Western Conference 1 Seed — ticker prefix KXNBA
- skip `KXWNBA2QSPREAD` Women's Pro Basketball 2nd Quarter Spread — non-NBA basketball marker 'WNBA'
- skip `KXA10REG` A10 Regular Season Champions — no NBA marker
- skip `KXWEUROBASKETGAME` EuroBasket (W) Game — no NBA marker
- skip `KXWNBAASGMVP` WNBA All-Star Game MVP — non-NBA basketball marker 'WNBA'
- skip `KXNCAAWB3Q` Women's College Basketball 3rd Quarter Winner — no NBA marker
- skip `KXRECORDNBABEST` Best Pro Basketball Record — no NBA marker
- NBA  `KXNBANEWCHAMPION` Pro Basketball New Champion — ticker prefix KXNBA
- skip `KXNCAAMBFIRST25` Men's College Basketball Race to 25 Points — no NBA marker
- NBA  `KXNBAFINALSOUTCOME` NBA Finals Outcome — ticker prefix KXNBA
- skip `KXNCAAMBSWAC` Southwestern Atlantic Conference Tournament — no NBA marker
- skip `KXNBIGAME` Hungary NB I. A Game — no NBA marker
- skip `KXNCAAWBACC` Women's College Basketball ACC Conference Tournament Champion — no NBA marker
- skip `KXNCAAMPAC12` PAC-12 MEN'S BASKETBALL TOURNAMENT — no NBA marker
- NBA  `KXNBA1H` NBA 1st Half Winner — ticker prefix KXNBA
- NBA  `KXNBASUMMER1HWINNER` Pro Basketball Summer League 1st Half Winner — ticker prefix KXNBA
- skip `KXWNBADRAFT4` WNBA Draft 4th Pick — non-NBA basketball marker 'WNBA'
- skip `KXWNBATEAMTOTAL` WNBA Team Totals — non-NBA basketball marker 'WNBA'
- skip `KXWNBADRAFT3` WNBA Draft 3rd Pick — non-NBA basketball marker 'WNBA'
- skip `KXNCAAWB2QTOTAL` Women's College Basketball 2nd Quarter Total — no NBA marker
- skip `KXNCAAMBACCREGTOP` Men's College Basketball ACC Regular Season Top Finishers — no NBA marker
- skip `KXNCAAMBWINS` Men's College Basketball Win Totals — no NBA marker
- skip `KXNCAAWB3QTOTAL` Women's College Basketball 3rd Quarter Total — no NBA marker
- NBA  `KXNBAFINALSMENTION` NBA Finals — ticker prefix KXNBA
- skip `KXWNBAEAST1` Women's Pro Basketball Eastern Conference #1 Seed — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAPA` Pro Basketball Player Points + Assists — ticker prefix KXNBA
- NBA  `KXNBATEAMSALE` Pro Basketball Team to be Sold — ticker prefix KXNBA
- NBA  `KXNBAOT` NBA Overtime — ticker prefix KXNBA
- skip `KXNBBGAME` Brazil NBB Basketball Game — no NBA marker
- skip `KXMARMADSEEDROUND` March Madness Seed Round — no NBA marker
- NBA  `KXNBAPICKTRADE` Pro Basketball Pick Trade — ticker prefix KXNBA
- skip `KXVTBSPREAD` Russia VTB United Spread — no NBA marker
- NBA  `KXNBAROOKIE1STTEAM` NBA All-Rookie 1st Team — ticker prefix KXNBA
- NBA  `KXNBAH2HWINS` NBA Head to Head Win Total — ticker prefix KXNBA
- NBA  `KXNBADRAFTTEAM` Pro Basketball Team to Draft — ticker prefix KXNBA
- NBA  `KXCOACHOUTNBADATE` NBA Coach Out Date — title mentions NBA
- skip `KXFIBAECUPTOTAL` FIBA Europe Cup Total — no NBA marker
- skip `KXNCAAMBBIG12` Big 12 Conference Tournament — no NBA marker
- skip `KXWNBA1QSPREAD` Women's Pro Basketball 1st Quarter Spread — non-NBA basketball marker 'WNBA'
- NBA  `KXNBA1QSPREAD` NBA 1st Quarter Spread — ticker prefix KXNBA
- skip `KXISL` Israeli Super League Champion — no NBA marker
- NBA  `KXNBALADDERPTS` NBA Player Points Ladder — ticker prefix KXNBA
- NBA  `KXNBAFINALSMVP` Finals MVP — ticker prefix KXNBA
- NBA  `KXNBAPTS` NBA Player Points — ticker prefix KXNBA
- NBA  `KXNBAH2H3PT` NBA Head-to-Head Three Pointers — ticker prefix KXNBA
- skip `KXMARMADHIGHSEED` March Madness Highest Seed to Reach Round — no NBA marker
- NBA  `KXNBAFRANCHISEOWNER` NBA Franchise Owner — ticker prefix KXNBA
- skip `KXVTB` Russia VTB United Champion — no NBA marker
- skip `KXNCAAMB1HTEAMTOTAL` Men's College Basketball 1st Half Team Total — no NBA marker
- skip `KXNCAAMBSUM` Summit League Conference Tournament — no NBA marker
- skip `KXWNBAALLDEFENSE` Women's Pro Basketball All-Defensive Teams — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAPLAYERSPECIALS` Pro Basketball Player Specials — ticker prefix KXNBA
- skip `KXWFIBASPREAD` Women's FIBA Spread — no NBA marker
- NBA  `KXNBAMVP` NBA MVP — ticker prefix KXNBA
- skip `KXLNBELITESPREAD` LNB Elite Spread — no NBA marker
- skip `KXLBJRETIRE` LBJ Retire — no NBA marker
- skip `KXNCAAMBBIGEASTREG` Men's College Basketball Big East Regular Season Champion — no NBA marker
- skip `KXNCAAWBUNDEFEATED` Undefeated in Women's College Basketball Regular Season — no NBA marker
- skip `KXNCAAMBSEC` SEC Conference Tournament — no NBA marker
- skip `KXLNBELITE2GAME` LNB Elite 2 Game — no NBA marker
- NBA  `KXNBAJOINCONF` Pro Basketball Join Conference — ticker prefix KXNBA
- skip `KXNCAAMBMVAL` Missouri Valley Conference Tournament — no NBA marker
- skip `KXWDBBLGAME` Women's Bundesliga Basketball Game — no NBA marker
- NBA  `KXNBA1Q` NBA 1st Quarter Winner — ticker prefix KXNBA
- NBA  `KXNBAPOSTASREC` NBA Best Record Post-All-Star Break — ticker prefix KXNBA
- NBA  `KXNBASERIESCOMEBACK` Pro Basketball Series Comeback — ticker prefix KXNBA
- skip `KXNEXTTEAMGIANNIS` Giannis next team — no NBA marker
- NBA  `KXNBARETIRE` NBA Retirement — ticker prefix KXNBA
- NBA  `KXNBADRAFT2` NBA Draft Second Pick — ticker prefix KXNBA
- NBA  `KXNBAPACIFIC` Pro Basketball Pacific Division Winner — ticker prefix KXNBA
- skip `KXJCOLECBA` J Cole CBA — no NBA marker
- skip `KXWNBASSTARS` Women's Pro Basketball Shooting Stars Contest — non-NBA basketball marker 'WNBA'
- skip `KXFIBASPREAD` FIBA Spread — no NBA marker
- skip `KXABATOTAL` Adriatic ABA Total — no NBA marker
- skip `KXNCAAMB1HTOTAL` Men's College Basketball 1st Half Total — no NBA marker
- skip `KXNCAABIVY` Ivy League Men's Basketball Tournament — no NBA marker
- NBA  `KXNBA3QTOTAL` NBA 3rd Quarter Total — ticker prefix KXNBA
- skip `KXEUROLEAGUESPREAD` EuroLeague Spread — no NBA marker
- NBA  `KXNBACUPQUAL` Pro Basketball Cup Qualifiers — ticker prefix KXNBA
- skip `KXWNBA2HSPREAD` Women's Pro Basketball 2nd Half Spread — non-NBA basketball marker 'WNBA'
- skip `KXSTEPHSHOEDEAL` Steph Curry Shoe Deal — no NBA marker
- skip `KXNCAAMB2HSPREAD` Men's College Basketball 2nd Half Spread — no NBA marker
- skip `KXWNBA6POY` WNBA Sixth Player of the Year — non-NBA basketball marker 'WNBA'
- skip `KXNCAAMBSECQUAL` Men's College Basketball SEC Championship Qualifiers — no NBA marker
- skip `KXNCAAMBPAC12` Pac-12 Conference Tournament — no NBA marker
- NBA  `KXNBAGAME` NBA Game — ticker prefix KXNBA
- skip `KXBDS3PTOU` Bob Does Sports Made 3-Pointers — no NBA marker
- skip `KXSTEPHPARTERNSHIP` Stephen Curry Partnership — no NBA marker
- NBA  `KXLEADERNBAREB` NBA RPG Leader — title mentions NBA
- skip `KXNCAAWB2H` Women's College Basketball 2nd Half Winner — no NBA marker
- skip `KXNCAAWBFIRST3PT` Women's College Basketball First Team to Make a Three — no NBA marker
- skip `KXBILGAME` Ball is Life Basketball Game — no NBA marker
- skip `KXNCAAWBBIGTEN` Women's College Basketball Big Ten Conference Tournament Champion — no NBA marker
- NBA  `KXNBAWHATTEND` Pro Basketball White House Attend — ticker prefix KXNBA
- skip `KXISLTOTAL` Israel Super League Total — no NBA marker
- skip `KXAMAFRNBA` Favorite R&B Album — no NBA marker
- skip `KXFIBAECUPGAME` FIBA Europe Cup Game — no NBA marker
- skip `KXMARMAD3D` Men's March Madness Triple Double — no NBA marker
- skip `KXEUROBASKETTOTAL` EuroBasket Total — no NBA marker
- skip `KXNCAAMBKENPOMRANK` Men's College Basketball KenPom Ratings — no NBA marker
- skip `KXCBATOTAL` Chinese Basketball Association Total  — no NBA marker
- skip `KXJUDGEMENTDAYGAME` Ballislife x OTD | Judgement Day 1v1 Game — no NBA marker
- NBA  `KXNEXTTEAMNBA` Next NBA Team — title mentions NBA
- skip `KXKBLTOTAL` Korea KBL Total — no NBA marker
- NBA  `KXNBATEAMMATE` NBA Teammate of the Year — ticker prefix KXNBA
- NBA  `KXNBASERIESSCORE` NBA Series Exact Score — ticker prefix KXNBA
- skip `KXEARNINGSMENTIONCOINBASE` coinbase earnings mention — no NBA marker
- NBA  `KXKXSPOTIFYALBUMRELEASEDATESC` WILL NBA YOUNBOY RELEASE SLIME CRY  — title mentions NBA
- skip `KXWNBAREB` Women's Pro Basketball Player Rebounds — non-NBA basketball marker 'WNBA'
- skip `KXALBUMRELEASENBAYB` WILL YOUNGBOY RELEASE ANOTHER ALBUM THIS YEAR? — no NBA marker
- skip `KXEUROBASKETGAME` EuroBasket Game — no NBA marker
- skip `KXMARMADSEEDDIF` March Madness Biggest Upset — no NBA marker
- NBA  `KXNBAEAST1SEED` NBA Eastern Conference 1 Seed — ticker prefix KXNBA
- skip `KXNCAAWB4QSPREAD` Women's College Basketball 4th Quarter Spread — no NBA marker
- NBA  `KXNBADRAFT1` NBA Draft First Pick — ticker prefix KXNBA
- NBA  `KXNBASEATTLE` Seattle NBA team — ticker prefix KXNBA
- skip `KXWNBAEAST` Women's Pro Basketball Eastern Conference Champion — non-NBA basketball marker 'WNBA'
- skip `KXNCAANIT` NIT Champion — no NBA marker
- NBA  `KXNBATEAMWINSTREAK` NBA Team with the Longest Winning Streak — ticker prefix KXNBA
- NBA  `KXNBAWINRECORD` OKC NBA Win Record — ticker prefix KXNBA
- skip `KXMARMADREGION` March Madness Region Winner — no NBA marker
- skip `KXNCAAMBUAC` United Athletic Conference Conference Tournament — no NBA marker
- NBA  `KXNBABLK` NBA Player Blocks — ticker prefix KXNBA
- NBA  `KXNBASHOOTINGSTARS` Pro Basketball Shooting Stars Contest — ticker prefix KXNBA
- NBA  `KXNBARECORD` Pro Basketball Best/Worst Regular Season Record — ticker prefix KXNBA
- skip `KXLNBP` Mexico LNBP Champion — no NBA marker
- NBA  `KXTOP3NBADRAFT` NBA Draft Top 3 — title mentions NBA
- skip `KXBDSFTCHALLENGE` Bob Does Sports Free Throw Challenge — no NBA marker
- NBA  `KXNBASOUTHWEST` Pro Basketball Southwest Division Winner — ticker prefix KXNBA
- skip `KXNCAAMBOT` Men's College Basketball Overtime — no NBA marker
- skip `KXNCAAMBSECREG` Men's College Basketball SEC Regular Season Champion — no NBA marker
- NBA  `KXNBATOTAL` NBA Total — ticker prefix KXNBA
- skip `KXJOINBARSTOOL` Will Shannon sharpe join meta — no NBA marker
- NBA  `KXNBAPTSALLGAMES` Pro Basketball Points in Every Game — ticker prefix KXNBA
- skip `KXNCAAMBSPREAD` Men's College Basketball Spread — no NBA marker
- NBA  `KXNBATOJOINCBA` NBA Players to Join the CBA — ticker prefix KXNBA
- skip `KXNCAAMBNEXTCOACH` Men's College Basketball Next Coach — no NBA marker
- NBA  `KXNBAWINSTREAK` NBA Longest Win Streak — ticker prefix KXNBA
- skip `KXFBUGAME` Ukraine SuperLeague Game — no NBA marker
- NBA  `KXNBAH2HTEAM3PT` NBA H2H Team Three Pointers — ticker prefix KXNBA
- skip `KXNCAAMBIGEAST` Big East Men's basketball tournament — no NBA marker
- NBA  `KXNBAALLSTAR` NBA All-Star game — ticker prefix KXNBA
- NBA  `KXNBASTATAVG` NBA Player Stat Average — ticker prefix KXNBA
- skip `KXNCAAMBACCREG` Men's College Basketball ACC Regular Season Champion — no NBA marker
- skip `KXNCAAMB2HTEAMTOTAL` Men's College Basketball 2nd Half Team Total — no NBA marker
- skip `KXWNBASEMIFINAL` Women's Pro Basketball Semifinals Qualifiers — non-NBA basketball marker 'WNBA'
- skip `KXWNBA40PTS` Women's Pro Basketball Player to Score 40 Points — non-NBA basketball marker 'WNBA'
- skip `KXWNBAWINS` WNBA Win Totals — non-NBA basketball marker 'WNBA'
- NBA  `KXNBASERIESASTLEADER` Pro Basketball Series Assists Leader — ticker prefix KXNBA
- skip `KXNCAAWBAWARD` Women's College Basketball Awards — no NBA marker
- skip `KXPLKGAME` Poland PLK Game — no NBA marker
- skip `KXIBPLGAME` Men's Iceland Basketball Premier League Game — no NBA marker
- NBA  `KXNBADRAFTTOP30` NBA Draft Top 30 Pick — ticker prefix KXNBA
- skip `KXBDS3PT` Bob Does Sports 3pt Shootout — no NBA marker
- NBA  `KXNBATOP5ROTY` Top 5 NBA draft ROTY — ticker prefix KXNBA
- skip `KXTBTGAME` TBT Hoops Game — no NBA marker
- skip `KXWNBA1HSPREAD` Women's Pro Basketball 1st Half Spread — non-NBA basketball marker 'WNBA'
- skip `KXGBLGAME` GBL Basketball Game — no NBA marker
- skip `KXSHEINBAUMOUT` Claudia Sheinbaum out as President of Mexico? — no NBA marker
- skip `KXDBBSUPERGAME` DBB Supercup Game — no NBA marker
- skip `KXNCAABACC` ACC Men's Basketball Tournament — no NBA marker
- NBA  `KXNBATRADE` Pro Basketball Trade — ticker prefix KXNBA
- skip `KXNCAAWBAPRANK` Women's College Basketball AP Poll — no NBA marker
- NBA  `KXNBAAST` NBA Player Assists — ticker prefix KXNBA
- skip `KXWNBA4QWINNER` Women's Pro Basketball 4th Quarter Winner — non-NBA basketball marker 'WNBA'
- skip `KXNCAAWBTEAMTOTAL` Women's College Basketball Team Total — no NBA marker
- skip `KXNCAAWB` Women's March Madness Champion — no NBA marker
- NBA  `KXNBARETURN` Pro Basketball Player to Return — ticker prefix KXNBA
- skip `KXNCAAMBTEAMSQUAL` Men's College Basketball Teams to Qualify — no NBA marker
- NBA  `KXNBADRAFTCONF` Pro Basketball Players Drafted by Conference — ticker prefix KXNBA
- NBA  `KXNBASUMMERPTS` Pro Basketball Summer Player Points — ticker prefix KXNBA
- NBA  `KXNBASERIESROADWINS` Pro Basketball Series Total Road Wins — ticker prefix KXNBA
- skip `KXNCAAMBASUN` Atlantic Sun Conference Tournament — no NBA marker
- skip `KXWKBLGAME` Korea KBL (W) Game — no NBA marker
- skip `KXNCAAMSEC` SEC MEN'S BASKETBALL TOURNAMENT — no NBA marker
- skip `KXACQUIRECOINBASE` Will Coinbase announce another acquisition in 2025? — no NBA marker
- skip `KXNCAAMBIVY` Ivy League Conference Tournament — no NBA marker
- skip `KXWNBASERIES` WNBA Playoff Series Winner — non-NBA basketball marker 'WNBA'
- skip `KXSPORTSIGNAHOR` Al Horford — no NBA marker
- skip `KXWNBAMATCHUP` WNBA Finals Matchup — non-NBA basketball marker 'WNBA'
- skip `KXLKLTOTAL` LKL Lithuania Total — no NBA marker
- skip `KXNCAAWBWBIT` WBIT Winner — no NBA marker
- skip `KXNCAAMBUNDEFEATEDHOME` Men's College Basketball Teams to go Undefeated at Home — no NBA marker
- skip `KXNCAAMBAMER` American Conference Tournament — no NBA marker
- skip `KXSBLSPREAD` Slovakia SBL Spread — no NBA marker
- NBA  `KXNBACUPGROUPWIN` NBA Cup Group to Win — ticker prefix KXNBA
- skip `KXNCAAMBAE` American East Conference Tournament — no NBA marker
- skip `KXBBALLTEAMUSA` Summer Olympics USA Men's Basketball Team — no NBA marker
- skip `KXNEWCOACHLAL` New Lakers coach — no NBA marker
- NBA  `KXNBAEFINMVP` NBA Eastern Conference Finals MVP — ticker prefix KXNBA
- skip `KXSLBGAME` England Super League Basketball Game — no NBA marker
- skip `KXLEADERWNBAPTS` WNBA PPG Leader — non-NBA basketball marker 'WNBA'
- skip `KXWNBAFIRSTTEAM` Women's Pro Basketball First Team — non-NBA basketball marker 'WNBA'
- skip `KXWNBASERIESSCORE` WNBA Series Exact Score — non-NBA basketball marker 'WNBA'
- skip `KXWNBADRAFT1` WNBA Draft 1st Pick — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAUPSET` NBA Number of Upsets per Round — ticker prefix KXNBA
- NBA  `KXNBA2QTOTAL` NBA 2nd Quarter Total — ticker prefix KXNBA
- NBA  `KXNBAAPOLOGY` Pro Basketball Apology — ticker prefix KXNBA
- NBA  `KXNBANEXTTEAMOUTLET` Pro Basketball Outlet to Announce Next Team — ticker prefix KXNBA
- skip `KXSESBLGAME` Sweden SBL Game — no NBA marker
- NBA  `KXNBA2HSPREAD` NBA 2nd Half Spread — ticker prefix KXNBA
- NBA  `KXNBACUP` Pro Basketball Cup Champion — ticker prefix KXNBA
- NBA  `KXNBAXMASOPPONENT` Pro Basketball Christmas Day Opponent — ticker prefix KXNBA
- NBA  `KXNBAFINALSPRICE` NBA Finals Ticket Price — ticker prefix KXNBA
- NBA  `KXNBACITYEXPAND` NBA City Franchise Expansion — ticker prefix KXNBA
- skip `KXSBLTOTAL` Slovakia SBL Total — no NBA marker
- NBA  `KXNBA4QSPREAD` NBA 4th Quarter Spread — ticker prefix KXNBA
- NBA  `KXNBASTADIUM` NBA Stadium Completion — ticker prefix KXNBA
- NBA  `KXNBAROTM` NBA Rookie of the Month — ticker prefix KXNBA
- NBA  `KXNBAAWARDFIN` NBA Award Finalists — ticker prefix KXNBA
- skip `KXNCAAMBBIG12REGTOP` Men's College Basketball Big 12 Regular Season Top Finishers — no NBA marker
- skip `KXWNBA2HWINNER` Women's Pro Basketball 2nd Half Winner — non-NBA basketball marker 'WNBA'
- skip `KXTATUMRETURN` When Will Jayson Tatum Play His Next Game — no NBA marker
- skip `KXCBASPREAD` Chinese Basketball Association Spread  — no NBA marker
- skip `KXNCAAWB1QSPREAD` Women's College Basketball 1st Quarter Spread — no NBA marker
- NBA  `KXNBAPREPACK3ML` 3ML Basketball Combo — ticker prefix KXNBA
- NBA  `KXNBADRAFT4` NBA Draft Fourth Pick — ticker prefix KXNBA
- skip `KXLBPGAME` Colombia LBP Basketball Game — no NBA marker
- skip `KXNCAAMBHL` Horizon League conference tournament winner — no NBA marker
- skip `KXNCAAMBAPRANK` Men's College Basketball AP Poll — no NBA marker
- skip `KXCAATOURNAMENT` CAA Tournament — no NBA marker
- skip `KXNCAAMBMEAC` Mid-Eastern Conference Tournament — no NBA marker
- NBA  `KXNBA2KCOVER` Who will be on the cover of NBA 2k? — ticker prefix KXNBA
- skip `KXBBSERIEAGAME` Italy Serie A Game — no NBA marker
- skip `KXBSOUTOURNAMENT` Big South Tournament — no NBA marker
- skip `KXWNBAMENTION` WNBA Mentions — non-NBA basketball marker 'WNBA'
- NBA  `KXNBA4Q` NBA 4th Quarter Winner — ticker prefix KXNBA
- skip `KXWNBA3PTCONTESTOU` Women's Pro Basketball 3-Point Contest Threes Made — non-NBA basketball marker 'WNBA'
- skip `KXMARMADPTS` Men's March Madness Points — no NBA marker
- skip `KXACBGAME` Spain Liga ACB Game — no NBA marker
- skip `KXWNBACOMPETE` Women's Pro Basketball Player to Compete — non-NBA basketball marker 'WNBA'
- skip `KXMARMADROUND` Reach March Madness Round — no NBA marker
- skip `KXBIG3` BIG3 Champion — no NBA marker
- skip `KXMARMADSEED` Men's College Basketball Tournament Seeds — no NBA marker
- NBA  `KXNBAATTEND` Who will attend the NBA game? — ticker prefix KXNBA
- NBA  `KXLEADERNBA3PT` NBA 3PG Leader — title mentions NBA
- NBA  `KXNBA3PTPROT` NBA Player Threes Protected — ticker prefix KXNBA
- NBA  `KXNBANEXTGOVERNOR` Pro Basketball Next Governor — ticker prefix KXNBA
- skip `KXABASPREAD` Adriatic ABA Spread — no NBA marker
- NBA  `KXNBACELEBRITY3PT` NBA Celebrity 3PT Contest — ticker prefix KXNBA
- skip `KXSOBBALLGAME` Summer Olympics Men's Basketball Game — no NBA marker
- skip `KXWNBADRAFT2` WNBA Draft 2nd Pick — non-NBA basketball marker 'WNBA'
- skip `KXNCAAMB2H` Men's College Basketball 2nd Half Winner — no NBA marker
- skip `KXNCAABBIGEAST` Big East Men's Basketball Tournament — no NBA marker
- NBA  `KXNBATEAM` NBA team — ticker prefix KXNBA
- skip `KXACBTOTAL` Spain Liga ACB Total — no NBA marker
- skip `KXBILBASKETBALL` Ball is Life Basketball Game — no NBA marker
- NBA  `KXNBASERIESGCOMEBACK` Pro Basketball Series Game Comeback — ticker prefix KXNBA
- skip `KXNZNBLGAME` New Zealand NBL Game — no NBA marker
- skip `KXWNBA1HTOTAL` WNBA 1st Half Total — non-NBA basketball marker 'WNBA'
- skip `KXNCAAMBBIGEAST` Big East Conference Tournament — no NBA marker
- skip `KXAMAFFRNBA` Favorite Female R&B Artist — no NBA marker
- skip `KXLNBPTOTAL` LNBP Total — no NBA marker
- NBA  `KXNBA2NDTEAMDEF` NBA All-Defensive 2nd Team — ticker prefix KXNBA
- NBA  `KXNBASTAKESALE` NBA Team Ownership Stake Sale Agreement — ticker prefix KXNBA
- skip `KXSOWBBALLSPREAD` Summer Olympics Women's Basketball Spread — no NBA marker
- skip `KXACBSPREAD` Spain Liga ACB Spread — no NBA marker
- skip `KXNCAAWBWINS` Women's College Basketball Win Totals — no NBA marker
- skip `KXBBLGAME` Bundesliga Basketball Game — no NBA marker
- NBA  `KXNBASTOCKS` NBA Player Steals and Blocks — ticker prefix KXNBA
- NBA  `KXMVENBASINGLEGAME` MVE NBA Single Game — title mentions NBA
- skip `KXBBL` Germany BBL Champion — no NBA marker
- skip `KXNCAAMBTEAMMOSTPTS` College Basketball Team with the Most Points Scored — no NBA marker
- NBA  `KXNBAWFINMVP` NBA Western Conference Finals MVP — ticker prefix KXNBA
- NBA  `KXNBACLUTCH` NBA Clutch Player of the Year — ticker prefix KXNBA
