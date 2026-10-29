# Kalshi NBA discovery summary

- discovered_at: `2026-10-29T19:08:42Z`  ontology: `2026.09.18.3`  requests: 608
- series enumerated: 15476; NBA series: 300; markets scanned: 9137

## Support states (coverage invariant)

| support | markets |
|---|---:|
| MODELABLE | 1587 |
| BUILDABLE | 1222 |
| RESEARCH | 1815 |
| UNMODELABLE | 1631 |
| UNRESOLVED | 2882 |

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
| KXNBA1HSPREAD | period_spread | BUILDABLE | quadratic/1 | 0 | 57 | 0 | 0 | greater | {'high': 57} |
| KXNBA1HTEAMTOTAL | period_team_total | BUILDABLE | quadratic/1 | 0 | 66 | 0 | 0 | greater | {'high': 66} |
| KXNBA1HTOTAL | period_total | BUILDABLE | quadratic/1 | 0 | 57 | 0 | 0 | greater | {'high': 57} |
| KXNBA1HWINNER | period_winner | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA1Q | period_winner | BUILDABLE | quadratic/1 | 0 | 42 | 0 | 0 | structured | {'high': 42} |
| KXNBA1QSPREAD | period_spread | BUILDABLE | quadratic/1 | 0 | 39 | 0 | 0 | greater | {'high': 39} |
| KXNBA1QTEAMTOTAL | period_team_total | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA1QTOTAL | period_total | BUILDABLE | quadratic/1 | 0 | 39 | 0 | 0 | greater | {'high': 39} |
| KXNBA1QWINNER | period_winner | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA1STTEAM | all_nba_selections | UNMODELABLE | quadratic/1 | 0 | 39 | 0 | 0 | structured | {'low': 39} |
| KXNBA1STTEAMDEF | all_nba_selections | UNMODELABLE | quadratic/1 | 0 | 41 | 0 | 0 | structured | {'low': 41} |
| KXNBA2D | player_double_double | BUILDABLE | quadratic/1 | 0 | 15 | 0 | 0 | greater | {'high': 15} |
| KXNBA2H | period_winner | BUILDABLE | quadratic/1 | 0 | 42 | 0 | 0 | structured | {'high': 42} |
| KXNBA2HSPREAD | period_spread | BUILDABLE | quadratic/1 | 0 | 57 | 0 | 0 | greater | {'high': 57} |
| KXNBA2HTEAMTOTAL | period_team_total | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA2HTOTAL | period_total | BUILDABLE | quadratic/1 | 0 | 57 | 0 | 0 | greater | {'high': 57} |
| KXNBA2HWINNER | period_winner | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA2KCOVER | non_basketball_or_offcourt | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA2NDTEAM | all_nba_selections | UNMODELABLE | quadratic/1 | 0 | 55 | 0 | 0 | structured | {'low': 55} |
| KXNBA2NDTEAMDEF | all_nba_selections | UNMODELABLE | quadratic/1 | 0 | 51 | 0 | 0 | structured | {'low': 51} |
| KXNBA2Q | period_winner | BUILDABLE | quadratic/1 | 0 | 42 | 0 | 0 | structured | {'high': 42} |
| KXNBA2QSPREAD | period_spread | BUILDABLE | quadratic/1 | 0 | 39 | 0 | 0 | greater | {'high': 39} |
| KXNBA2QTEAMTOTAL | period_team_total | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA2QTOTAL | period_total | BUILDABLE | quadratic/1 | 0 | 39 | 0 | 0 | greater | {'high': 39} |
| KXNBA2QWINNER | period_winner | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA30COMEBACK | series_props | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA3D | player_triple_double | BUILDABLE | quadratic/1 | 0 | 5 | 0 | 0 | greater | {'high': 5} |
| KXNBA3PEAT | champion_special | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA3PT | player_threes | MODELABLE | quadratic/1 | 9 | 161 | 0 | 0 | greater | {'high': 170} |
| KXNBA3PTALLGAMES | season_player_streak | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA3PTCONTEST | all_star_events | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA3PTPROT | UNRESOLVED | UNRESOLVED | quadratic/1 | 9 | 161 | 0 | 0 | greater | {'high': 170} |
| KXNBA3Q | period_winner | BUILDABLE | quadratic/1 | 0 | 42 | 0 | 0 | structured | {'high': 42} |
| KXNBA3QSPREAD | period_spread | BUILDABLE | quadratic/1 | 0 | 39 | 0 | 0 | greater | {'high': 39} |
| KXNBA3QTEAMTOTAL | period_team_total | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA3QTOTAL | period_total | BUILDABLE | quadratic/1 | 0 | 39 | 0 | 0 | greater | {'high': 39} |
| KXNBA3QWINNER | period_winner | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA3RDTEAM | all_nba_selections | UNMODELABLE | quadratic/1 | 0 | 55 | 0 | 0 | structured | {'low': 55} |
| KXNBA4Q | period_winner | BUILDABLE | quadratic/1 | 0 | 42 | 0 | 0 | structured | {'high': 42} |
| KXNBA4QSPREAD | period_spread | BUILDABLE | quadratic/1 | 0 | 39 | 0 | 0 | greater | {'high': 39} |
| KXNBA4QTEAMTOTAL | period_team_total | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBA4QTOTAL | period_total | BUILDABLE | quadratic/1 | 0 | 39 | 0 | 0 | greater | {'high': 39} |
| KXNBA4QWINNER | period_winner | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAALLSTAR | all_star_events | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAALLSTARGAME | all_star_events | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAALLSTARMVP | awards | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAALLSTARS | all_nba_selections | UNMODELABLE | quadratic/1 | 0 | 60 | 0 | 0 | structured | {'low': 60} |
| KXNBAAPOLOGY | non_basketball_or_offcourt | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAASSTARTERS | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAAST | player_assists | MODELABLE | quadratic/1 | 0 | 123 | 0 | 0 | greater | {'high': 123} |
| KXNBAASTPROT | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 123 | 0 | 0 | greater | {'high': 123} |
| KXNBAATLANTIC | division_winner | RESEARCH | quadratic/1 | 0 | 5 | 0 | 0 | structured | {'low': 5} |
| KXNBAATTEND | non_basketball_or_offcourt | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAAWARDFIN | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 303 | 0 | 0 | custom,structured | {'low': 303} |
| KXNBABENCHPTS | team_bench_points | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBABLK | player_blocks | BUILDABLE | quadratic/1 | 0 | 47 | 0 | 0 | greater | {'high': 47} |
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
| KXNBAESCALATOR3PT | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 16 | 0 | 0 | custom | {'high': 16} |
| KXNBAESCALATORPTS | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 17 | 0 | 0 | custom | {'high': 17} |
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
| KXNBAGAME | game_winner | MODELABLE | quadratic_with_maker_fees/1 | 0 | 48 | 0 | 0 | structured | {'high': 48} |
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
| KXNBAPRA | player_pra | BUILDABLE | quadratic/1 | 1 | 66 | 0 | 0 | greater | {'high': 67} |
| KXNBAPREPACK2ML | parlay_combo | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAPREPACK3ML | parlay_combo | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAPTS | player_points | MODELABLE | quadratic/1 | 2 | 131 | 0 | 0 | greater | {'high': 133} |
| KXNBAPTSALLGAMES | season_player_streak | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAPTSLEADER | game_points_leader | RESEARCH | quadratic/1 | 0 | 34 | 0 | 0 | structured | {'high': 34} |
| KXNBAPTSPROT | UNRESOLVED | UNRESOLVED | quadratic/1 | 2 | 131 | 0 | 0 | greater | {'high': 133} |
| KXNBARA | player_ra | BUILDABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBARACE | game_race_to | RESEARCH | quadratic/1 | 0 | 84 | 0 | 0 | custom | {'high': 84} |
| KXNBAREB | player_rebounds | MODELABLE | quadratic/1 | 1 | 154 | 0 | 0 | greater | {'high': 155} |
| KXNBAREBPROT | UNRESOLVED | UNRESOLVED | quadratic/1 | 1 | 154 | 0 | 0 | greater | {'high': 155} |
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
| KXNBASPREAD | game_spread | MODELABLE | quadratic_with_maker_fees/1 | 0 | 429 | 0 | 0 | greater | {'high': 429} |
| KXNBASTADIUM | franchise_business | UNMODELABLE | quadratic/1 | 0 | 1 | 0 | 0 | None | {'low': 1} |
| KXNBASTAKESALE | franchise_business | UNMODELABLE | quadratic/1 | 0 | 1 | 0 | 0 | None | {'low': 1} |
| KXNBASTARTERS | starting_lineup | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBASTATAVG | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 188 | 0 | 0 | greater_or_equal | {'low': 188} |
| KXNBASTATLEADER | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 692 | 0 | 0 | structured | {'low': 692} |
| KXNBASTL | player_steals | BUILDABLE | quadratic/1 | 0 | 67 | 0 | 0 | greater | {'high': 67} |
| KXNBASTOCK | player_stocks | BUILDABLE | quadratic/1 | 0 | 45 | 0 | 0 | greater | {'high': 45} |
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
| KXNBATEAMTOTAL | team_total | MODELABLE | quadratic/1 | 0 | 152 | 0 | 0 | greater | {'high': 152} |
| KXNBATEAMWINSTREAK | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 30 | 0 | 0 | structured | {'low': 30} |
| KXNBATOJOINCBA | UNRESOLVED | UNRESOLVED | quadratic/1 | 0 | 25 | 0 | 0 | custom,structured | {'medium': 25} |
| KXNBATOP3 | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBATOP5ROTY | awards | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBATOPPICK | draft | UNMODELABLE | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBATOTAL | game_total | MODELABLE | quadratic_with_maker_fees/1 | 0 | 377 | 0 | 0 | greater | {'high': 377} |
| KXNBATRADE | transactions | UNMODELABLE | quadratic/1 | 0 | 46 | 0 | 0 | structured | {'medium': 46} |
| KXNBAUNBEATEN | series_props | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAUPSET | series_props | RESEARCH | quadratic/1 | 0 | 0 | 0 | 0 |  | {} |
| KXNBAWCFQUAL | playoff_round_reach | RESEARCH | quadratic/1 | 0 | 15 | 0 | 0 | structured | {'low': 15} |
| KXNBAWEST | conference_champion | RESEARCH | quadratic_with_maker_fees/1 | 0 | 15 | 0 | 0 | structured | {'low': 15} |
| KXNBAWEST1SEED | playoff_seed | RESEARCH | quadratic/1 | 0 | 15 | 0 | 0 | structured | {'low': 15} |
| KXNBAWFINMVP | awards | UNMODELABLE | quadratic/1 | 0 | 50 | 0 | 0 | structured | {'low': 50} |
| KXNBAWHATTEND | non_basketball_or_offcourt | UNMODELABLE | quadratic/1 | 0 | 1 | 0 | 0 | None | {'low': 1} |
| KXNBAWINMARGIN | game_win_margin | BUILDABLE | quadratic/1 | 0 | 104 | 0 | 0 | custom | {'high': 104} |
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
- (3) NAME wins the #st half
- (2) Portland wins the #st half
- (1) Utah wins the #st half
- (1) Cleveland wins the #st half
- (1) Atlanta wins the #st half
- (1) Phoenix wins the #st half
- (1) Denver wins the #st half
- samples: KXNBA1H-26OCT31PORUTA-UTA, KXNBA1H-26OCT31PORUTA-TIE, KXNBA1H-26OCT31PORUTA-POR, KXNBA1H-26OCT29CLEATL-TIE, KXNBA1H-26OCT29CLEATL-CLE, KXNBA1H-26OCT29CLEATL-ATL
- sample fields: `{"ticker": "KXNBA1H-26OCT31PORUTA-UTA", "event_ticker": "KXNBA1H-26OCT31PORUTA", "market_type": "binary", "title": "Utah wins the 1st half", "yes_sub_title": "Utah", "no_sub_title": "Utah", "strike_type": "structured", "custom_strike": {"basketball_team": "6f60dfb1-fda1-423f-b76f-67e9d24b9644"}, "status": "active", "open_time": "2026-10-29T19:05:50.454764Z", "close_time": "2026-11-02T19:00:00Z", "expected_expiration_time": "2026-10-31T22:00:00Z", "result": "", "rules_primary": "If Utah wins the 1st half of the Portland vs Utah Pro Basketball game originally scheduled for Oct 31, 2026, then the`

### KXNBA1HSPREAD — NBA 1st Half Spread
- (11) Portland wins the #st half by over # points
- (11) NAME wins the #st half by over # points
- (10) Atlanta wins the #st half by over # points
- (9) Cleveland wins the #st half by over # points
- (8) Memphis wins the #st half by over # points
- (8) Sacramento wins the #st half by over # points
- samples: KXNBA1HSPREAD-26OCT29CLEATL-CLE9, KXNBA1HSPREAD-26OCT29CLEATL-CLE7, KXNBA1HSPREAD-26OCT29CLEATL-CLE5, KXNBA1HSPREAD-26OCT29CLEATL-CLE3, KXNBA1HSPREAD-26OCT29CLEATL-CLE2, KXNBA1HSPREAD-26OCT29CLEATL-CLE17
- sample fields: `{"ticker": "KXNBA1HSPREAD-26OCT29CLEATL-CLE9", "event_ticker": "KXNBA1HSPREAD-26OCT29CLEATL", "market_type": "binary", "title": "Cleveland wins the 1st half by over 8.5 points", "yes_sub_title": "Cleveland wins by over 8.5 points", "no_sub_title": "Cleveland wins by over 8.5 points", "strike_type": "greater", "floor_strike": 8.5, "custom_strike": {"basketball_team": "90381a35-42a6-4975-851f-175418e4271a"}, "status": "active", "open_time": "2026-10-29T13:51:19.449053Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T03:00:00Z", "result": "", "rules_primary": "If C`

### KXNBA1HTEAMTOTAL — NBA 1st Half Team Total
- (11) Cleveland over # #st half points scored
- (11) Atlanta over # #st half points scored
- (11) Portland over # #st half points scored
- (11) Memphis over # #st half points scored
- (11) Sacramento over # #st half points scored
- (11) NAME over # #st half points scored
- samples: KXNBA1HTEAMTOTAL-26OCT29CLEATL-CLE68, KXNBA1HTEAMTOTAL-26OCT29CLEATL-CLE66, KXNBA1HTEAMTOTAL-26OCT29CLEATL-CLE64, KXNBA1HTEAMTOTAL-26OCT29CLEATL-CLE62, KXNBA1HTEAMTOTAL-26OCT29CLEATL-CLE60, KXNBA1HTEAMTOTAL-26OCT29CLEATL-CLE58
- sample fields: `{"ticker": "KXNBA1HTEAMTOTAL-26OCT29CLEATL-CLE68", "event_ticker": "KXNBA1HTEAMTOTAL-26OCT29CLEATL", "market_type": "binary", "title": "Cleveland over 67.5 1st half points scored", "yes_sub_title": "Cleveland over 67.5 points", "no_sub_title": "Cleveland over 67.5 points", "strike_type": "greater", "floor_strike": 67.5, "custom_strike": {"basketball_team": "90381a35-42a6-4975-851f-175418e4271a"}, "status": "active", "open_time": "2026-10-29T13:49:19.159301Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T03:00:00Z", "result": "", "rules_primary": "If Cleveland s`

### KXNBA1HTOTAL — NBA 1st Half Total
- (57) #st Half: Over # points scored
- samples: KXNBA1HTOTAL-26OCT29CLEATL-99, KXNBA1HTOTAL-26OCT29CLEATL-135, KXNBA1HTOTAL-26OCT29CLEATL-133, KXNBA1HTOTAL-26OCT29CLEATL-131, KXNBA1HTOTAL-26OCT29CLEATL-129, KXNBA1HTOTAL-26OCT29CLEATL-127
- sample fields: `{"ticker": "KXNBA1HTOTAL-26OCT29CLEATL-99", "event_ticker": "KXNBA1HTOTAL-26OCT29CLEATL", "market_type": "binary", "title": "1st Half: Over 98.5 points scored", "yes_sub_title": "Over 98.5 points", "no_sub_title": "Over 98.5 points", "strike_type": "greater", "floor_strike": 98.5, "status": "active", "open_time": "2026-10-29T13:51:19.449053Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T03:00:00Z", "result": "", "rules_primary": "If over 98.5 total points are scored in the 1st half of the Cleveland vs Atlanta Pro Basketball game originally scheduled for Oct 29`

### KXNBA1HWINNER — Pro Baskeball 1st Half Winner

### KXNBA1Q — NBA 1st Quarter Winner
- (14) #st quarter tie
- (3) NAME wins the #st quarter
- (2) Portland wins the #st quarter
- (1) Utah wins the #st quarter
- (1) Cleveland wins the #st quarter
- (1) Atlanta wins the #st quarter
- (1) Phoenix wins the #st quarter
- (1) Denver wins the #st quarter
- samples: KXNBA1Q-26OCT31PORUTA-UTA, KXNBA1Q-26OCT31PORUTA-TIE, KXNBA1Q-26OCT31PORUTA-POR, KXNBA1Q-26OCT29CLEATL-TIE, KXNBA1Q-26OCT29CLEATL-CLE, KXNBA1Q-26OCT29CLEATL-ATL
- sample fields: `{"ticker": "KXNBA1Q-26OCT31PORUTA-UTA", "event_ticker": "KXNBA1Q-26OCT31PORUTA", "market_type": "binary", "title": "Utah wins the 1st quarter", "yes_sub_title": "Utah", "no_sub_title": "Utah", "strike_type": "structured", "custom_strike": {"basketball_team": "6f60dfb1-fda1-423f-b76f-67e9d24b9644"}, "status": "active", "open_time": "2026-10-29T19:05:50.454764Z", "close_time": "2026-11-02T19:00:00Z", "expected_expiration_time": "2026-10-31T22:00:00Z", "result": "", "rules_primary": "If Utah wins the 1st quarter of the Portland vs Utah Pro Basketball game originally scheduled for Oct 31, 2026, th`

### KXNBA1QSPREAD — NBA 1st Quarter Spread
- (7) Atlanta wins #Q by over # points
- (7) Portland wins #Q by over # points
- (7) NAME wins #Q by over # points
- (6) Cleveland wins #Q by over # points
- (6) Memphis wins #Q by over # points
- (6) Sacramento wins #Q by over # points
- samples: KXNBA1QSPREAD-26OCT29CLEATL-CLE9, KXNBA1QSPREAD-26OCT29CLEATL-CLE7, KXNBA1QSPREAD-26OCT29CLEATL-CLE5, KXNBA1QSPREAD-26OCT29CLEATL-CLE3, KXNBA1QSPREAD-26OCT29CLEATL-CLE2, KXNBA1QSPREAD-26OCT29CLEATL-CLE11
- sample fields: `{"ticker": "KXNBA1QSPREAD-26OCT29CLEATL-CLE9", "event_ticker": "KXNBA1QSPREAD-26OCT29CLEATL", "market_type": "binary", "title": "Cleveland wins 1Q by over 8.5 points", "yes_sub_title": "Cleveland wins by over 8.5 points", "no_sub_title": "Cleveland wins by over 8.5 points", "strike_type": "greater", "floor_strike": 8.5, "custom_strike": {"basketball_team": "90381a35-42a6-4975-851f-175418e4271a"}, "status": "active", "open_time": "2026-10-29T13:51:19.449053Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T03:00:00Z", "result": "", "rules_primary": "If Cleveland w`

### KXNBA1QTEAMTOTAL — NBA 1st Quarter Team Total

### KXNBA1QTOTAL — NBA 1st Quarter Total
- (39) #st Quarter: Over # points scored
- samples: KXNBA1QTOTAL-26OCT29CLEATL-71, KXNBA1QTOTAL-26OCT29CLEATL-69, KXNBA1QTOTAL-26OCT29CLEATL-67, KXNBA1QTOTAL-26OCT29CLEATL-65, KXNBA1QTOTAL-26OCT29CLEATL-63, KXNBA1QTOTAL-26OCT29CLEATL-61
- sample fields: `{"ticker": "KXNBA1QTOTAL-26OCT29CLEATL-71", "event_ticker": "KXNBA1QTOTAL-26OCT29CLEATL", "market_type": "binary", "title": "1st Quarter: Over 70.5 points scored", "yes_sub_title": "Over 70.5 points", "no_sub_title": "Over 70.5 points", "strike_type": "greater", "floor_strike": 70.5, "status": "active", "open_time": "2026-10-29T13:51:19.449053Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T03:00:00Z", "result": "", "rules_primary": "If over 70.5 total points are scored in the 1st quarter of the Cleveland vs Atlanta Pro Basketball game originally scheduled for `

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
- (14) NAME: NAME
- (1) NAME.: NAME
- samples: KXNBA2D-26OCT29CLEATL-CLEJHARDEN1, KXNBA2D-26OCT29CLEATL-CLEJALLEN31, KXNBA2D-26OCT29CLEATL-CLEEMOBLEY4, KXNBA2D-26OCT29CLEATL-ATLOOKONGWU17, KXNBA2D-26OCT29CLEATL-ATLNALEXANDERWALKER7, KXNBA2D-26OCT29CLEATL-ATLJJOHNSON1
- sample fields: `{"ticker": "KXNBA2D-26OCT29CLEATL-CLEJHARDEN1", "event_ticker": "KXNBA2D-26OCT29CLEATL", "market_type": "binary", "title": "James Harden: Double Double", "yes_sub_title": "James Harden", "no_sub_title": "James Harden", "strike_type": "greater", "floor_strike": 0.5, "custom_strike": {"basketball_player": "d5324b8e-901b-404d-bfef-a5f5d62bed85", "basketball_team": "90381a35-42a6-4975-851f-175418e4271a"}, "status": "active", "open_time": "2026-10-29T14:06:26.671303Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T03:00:00Z", "result": "", "rules_primary": "If James `

### KXNBA2H — NBA 2nd Half Winner
- (14) Tie in the #nd half
- (3) NAME wins the #nd half
- (2) Portland wins the #nd half
- (1) Utah wins the #nd half
- (1) Cleveland wins the #nd half
- (1) Atlanta wins the #nd half
- (1) Phoenix wins the #nd half
- (1) Denver wins the #nd half
- samples: KXNBA2H-26OCT31PORUTA-UTA, KXNBA2H-26OCT31PORUTA-TIE, KXNBA2H-26OCT31PORUTA-POR, KXNBA2H-26OCT29CLEATL-TIE, KXNBA2H-26OCT29CLEATL-CLE, KXNBA2H-26OCT29CLEATL-ATL
- sample fields: `{"ticker": "KXNBA2H-26OCT31PORUTA-UTA", "event_ticker": "KXNBA2H-26OCT31PORUTA", "market_type": "binary", "title": "Utah wins the 2nd half", "yes_sub_title": "Utah", "no_sub_title": "Utah", "strike_type": "structured", "custom_strike": {"basketball_team": "6f60dfb1-fda1-423f-b76f-67e9d24b9644"}, "status": "active", "open_time": "2026-10-29T19:05:50.454764Z", "close_time": "2026-11-02T19:00:00Z", "expected_expiration_time": "2026-10-31T22:00:00Z", "result": "", "rules_primary": "If Utah wins the 2nd half (including overtime) of the Portland vs Utah Pro Basketball game originally scheduled for O`

### KXNBA2HSPREAD — NBA 2nd Half Spread
- (11) Portland wins the #nd half by over # points
- (11) NAME wins the #nd half by over # points
- (10) Cleveland wins the #nd half by over # points
- (9) Atlanta wins the #nd half by over # points
- (8) Memphis wins the #nd half by over # points
- (8) Sacramento wins the #nd half by over # points
- samples: KXNBA2HSPREAD-26OCT29CLEATL-CLE8, KXNBA2HSPREAD-26OCT29CLEATL-CLE6, KXNBA2HSPREAD-26OCT29CLEATL-CLE4, KXNBA2HSPREAD-26OCT29CLEATL-CLE20, KXNBA2HSPREAD-26OCT29CLEATL-CLE2, KXNBA2HSPREAD-26OCT29CLEATL-CLE18
- sample fields: `{"ticker": "KXNBA2HSPREAD-26OCT29CLEATL-CLE8", "event_ticker": "KXNBA2HSPREAD-26OCT29CLEATL", "market_type": "binary", "title": "Cleveland wins the 2nd half by over 7.5 points", "yes_sub_title": "Cleveland wins by over 7.5 points", "no_sub_title": "Cleveland wins by over 7.5 points", "strike_type": "greater", "floor_strike": 7.5, "custom_strike": {"basketball_team": "90381a35-42a6-4975-851f-175418e4271a"}, "status": "active", "open_time": "2026-10-29T13:51:19.449053Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T03:00:00Z", "result": "", "rules_primary": "If C`

### KXNBA2HTEAMTOTAL — NBA 2nd Half Team Total

### KXNBA2HTOTAL — NBA 2nd Half Total
- (57) #nd Half: Over # points scored
- samples: KXNBA2HTOTAL-26OCT29CLEATL-140, KXNBA2HTOTAL-26OCT29CLEATL-138, KXNBA2HTOTAL-26OCT29CLEATL-136, KXNBA2HTOTAL-26OCT29CLEATL-134, KXNBA2HTOTAL-26OCT29CLEATL-132, KXNBA2HTOTAL-26OCT29CLEATL-130
- sample fields: `{"ticker": "KXNBA2HTOTAL-26OCT29CLEATL-140", "event_ticker": "KXNBA2HTOTAL-26OCT29CLEATL", "market_type": "binary", "title": "2nd Half: Over 139.5 points scored", "yes_sub_title": "Over 139.5 points", "no_sub_title": "Over 139.5 points", "strike_type": "greater", "floor_strike": 139.5, "status": "active", "open_time": "2026-10-29T13:51:19.449053Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T03:00:00Z", "result": "", "rules_primary": "If over 139.5 total points are scored in the 2nd half (including overtime) of the Cleveland vs Atlanta Pro Basketball game orig`

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
- (3) NAME wins the #nd quarter
- (2) Portland wins the #nd quarter
- (1) Utah wins the #nd quarter
- (1) Cleveland wins the #nd quarter
- (1) Atlanta wins the #nd quarter
- (1) Phoenix wins the #nd quarter
- (1) Denver wins the #nd quarter
- samples: KXNBA2Q-26OCT31PORUTA-UTA, KXNBA2Q-26OCT31PORUTA-TIE, KXNBA2Q-26OCT31PORUTA-POR, KXNBA2Q-26OCT29CLEATL-TIE, KXNBA2Q-26OCT29CLEATL-CLE, KXNBA2Q-26OCT29CLEATL-ATL
- sample fields: `{"ticker": "KXNBA2Q-26OCT31PORUTA-UTA", "event_ticker": "KXNBA2Q-26OCT31PORUTA", "market_type": "binary", "title": "Utah wins the 2nd quarter", "yes_sub_title": "Utah", "no_sub_title": "Utah", "strike_type": "structured", "custom_strike": {"basketball_team": "6f60dfb1-fda1-423f-b76f-67e9d24b9644"}, "status": "active", "open_time": "2026-10-29T19:05:50.454764Z", "close_time": "2026-11-02T19:00:00Z", "expected_expiration_time": "2026-10-31T22:00:00Z", "result": "", "rules_primary": "If Utah wins the 2nd quarter of the Portland vs Utah Pro Basketball game originally scheduled for Oct 31, 2026, th`

### KXNBA2QSPREAD — NBA 2nd Quarter Spread
- (8) Portland wins #Q by over # points
- (7) Atlanta wins #Q by over # points
- (7) NAME wins #Q by over # points
- (6) Cleveland wins #Q by over # points
- (6) Sacramento wins #Q by over # points
- (5) Memphis wins #Q by over # points
- samples: KXNBA2QSPREAD-26OCT29CLEATL-CLE9, KXNBA2QSPREAD-26OCT29CLEATL-CLE7, KXNBA2QSPREAD-26OCT29CLEATL-CLE5, KXNBA2QSPREAD-26OCT29CLEATL-CLE3, KXNBA2QSPREAD-26OCT29CLEATL-CLE2, KXNBA2QSPREAD-26OCT29CLEATL-CLE11
- sample fields: `{"ticker": "KXNBA2QSPREAD-26OCT29CLEATL-CLE9", "event_ticker": "KXNBA2QSPREAD-26OCT29CLEATL", "market_type": "binary", "title": "Cleveland wins 2Q by over 8.5 points", "yes_sub_title": "Cleveland wins by over 8.5 points", "no_sub_title": "Cleveland wins by over 8.5 points", "strike_type": "greater", "floor_strike": 8.5, "custom_strike": {"basketball_team": "90381a35-42a6-4975-851f-175418e4271a"}, "status": "active", "open_time": "2026-10-29T13:51:19.449053Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T03:00:00Z", "result": "", "rules_primary": "If Cleveland w`

### KXNBA2QTEAMTOTAL — NBA 2nd Quarter Team Total

### KXNBA2QTOTAL — NBA 2nd Quarter Total
- (39) #nd Quarter: Over # points scored
- samples: KXNBA2QTOTAL-26OCT29CLEATL-70, KXNBA2QTOTAL-26OCT29CLEATL-68, KXNBA2QTOTAL-26OCT29CLEATL-66, KXNBA2QTOTAL-26OCT29CLEATL-64, KXNBA2QTOTAL-26OCT29CLEATL-62, KXNBA2QTOTAL-26OCT29CLEATL-60
- sample fields: `{"ticker": "KXNBA2QTOTAL-26OCT29CLEATL-70", "event_ticker": "KXNBA2QTOTAL-26OCT29CLEATL", "market_type": "binary", "title": "2nd Quarter: Over 69.5 points scored", "yes_sub_title": "Over 69.5 points", "no_sub_title": "Over 69.5 points", "strike_type": "greater", "floor_strike": 69.5, "status": "active", "open_time": "2026-10-29T13:51:19.449053Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T03:00:00Z", "result": "", "rules_primary": "If over 69.5 total points are scored in the 2nd quarter of the Cleveland vs Atlanta Pro Basketball game originally scheduled for `

### KXNBA2QWINNER — NBA 2nd Quarter Winner

### KXNBA30COMEBACK — NBA 3-0 Series Comeback

### KXNBA3D — NBA Player Triple Double
- (5) NAME: NAME
- samples: KXNBA3D-26OCT29CLEATL-CLEJHARDEN1, KXNBA3D-26OCT29CLEATL-ATLJJOHNSON1, KXNBA3D-26OCT29CLEATL-ATLDDANIELS5, KXNBA3D-26OCT29MEMPOR-PORDAVDIJA8, KXNBA3D-26OCT29SACNOP-SACDSABONIS11
- sample fields: `{"ticker": "KXNBA3D-26OCT29CLEATL-CLEJHARDEN1", "event_ticker": "KXNBA3D-26OCT29CLEATL", "market_type": "binary", "title": "James Harden: Triple Double", "yes_sub_title": "James Harden", "no_sub_title": "James Harden", "strike_type": "greater", "floor_strike": 0.5, "custom_strike": {"basketball_player": "d5324b8e-901b-404d-bfef-a5f5d62bed85", "basketball_team": "90381a35-42a6-4975-851f-175418e4271a"}, "status": "active", "open_time": "2026-10-29T14:06:26.671303Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T03:00:00Z", "result": "", "rules_primary": "If James `

### KXNBA3PEAT — Pro Basketball Three-Peat Champion

### KXNBA3PT — NBA Player Threes
- (149) NAME: #+ threes
- (6) Zach LaVine: #+ threes
- (5) CJ McCollum: #+ threes
- (5) NAME.: #+ threes
- (5) NAME III: #+ threes
- samples: KXNBA3PT-26OCT29CLEATL-ATLLDORT0-5, KXNBA3PT-26OCT29CLEATL-ATLLDORT0-4, KXNBA3PT-26OCT29CLEATL-ATLLDORT0-3, KXNBA3PT-26OCT29CLEATL-ATLLDORT0-2, KXNBA3PT-26OCT29CLEATL-ATLLDORT0-1, KXNBA3PT-26OCT29CLEATL-CLEJTYSON20-5
- sample fields: `{"ticker": "KXNBA3PT-26OCT29CLEATL-ATLLDORT0-5", "event_ticker": "KXNBA3PT-26OCT29CLEATL", "market_type": "binary", "title": "Luguentz Dort: 5+ threes", "yes_sub_title": "Luguentz Dort: 5+", "no_sub_title": "Luguentz Dort: 5+", "strike_type": "greater", "floor_strike": 4.5, "custom_strike": {"basketball_player": "c5345be3-57de-4b6e-9089-5b7cbbf7f74c", "basketball_team": "e0729403-9c95-4ee2-b5d4-f704d8322570"}, "status": "active", "open_time": "2026-10-29T18:20:36Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T06:00:00Z", "result": "", "rules_primary": "If Lugu`

### KXNBA3PTALLGAMES — Pro Basketball 3-Pointers in Every Game

### KXNBA3PTCONTEST — NBA 3-Point Contest Winner

### KXNBA3PTPROT — NBA Player Threes Protected
- (149) NAME: #+ threes
- (6) Zach LaVine: #+ threes
- (5) CJ McCollum: #+ threes
- (5) NAME.: #+ threes
- (5) NAME III: #+ threes
- samples: KXNBA3PTPROT-26OCT29CLEATL-ATLLDORT0-5, KXNBA3PTPROT-26OCT29CLEATL-ATLLDORT0-4, KXNBA3PTPROT-26OCT29CLEATL-ATLLDORT0-3, KXNBA3PTPROT-26OCT29CLEATL-ATLLDORT0-2, KXNBA3PTPROT-26OCT29CLEATL-ATLLDORT0-1, KXNBA3PTPROT-26OCT29CLEATL-CLEJTYSON20-5
- sample fields: `{"ticker": "KXNBA3PTPROT-26OCT29CLEATL-ATLLDORT0-5", "event_ticker": "KXNBA3PTPROT-26OCT29CLEATL", "market_type": "binary", "title": "Luguentz Dort: 5+ threes", "yes_sub_title": "Luguentz Dort: 5+", "no_sub_title": "Luguentz Dort: 5+", "strike_type": "greater", "floor_strike": 4.5, "custom_strike": {"basketball_player": "c5345be3-57de-4b6e-9089-5b7cbbf7f74c", "basketball_team": "e0729403-9c95-4ee2-b5d4-f704d8322570"}, "status": "active", "open_time": "2026-10-29T18:11:39Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T06:00:00Z", "result": "", "rules_primary": `

### KXNBA3Q — NBA 3rd Quarter Winner
- (14) #rd quarter tie
- (3) NAME wins the #rd quarter
- (2) Portland wins the #rd quarter
- (1) Utah wins the #rd quarter
- (1) Cleveland wins the #rd quarter
- (1) Atlanta wins the #rd quarter
- (1) Phoenix wins the #rd quarter
- (1) Denver wins the #rd quarter
- samples: KXNBA3Q-26OCT31PORUTA-UTA, KXNBA3Q-26OCT31PORUTA-TIE, KXNBA3Q-26OCT31PORUTA-POR, KXNBA3Q-26OCT29CLEATL-TIE, KXNBA3Q-26OCT29CLEATL-CLE, KXNBA3Q-26OCT29CLEATL-ATL
- sample fields: `{"ticker": "KXNBA3Q-26OCT31PORUTA-UTA", "event_ticker": "KXNBA3Q-26OCT31PORUTA", "market_type": "binary", "title": "Utah wins the 3rd quarter", "yes_sub_title": "Utah", "no_sub_title": "Utah", "strike_type": "structured", "custom_strike": {"basketball_team": "6f60dfb1-fda1-423f-b76f-67e9d24b9644"}, "status": "active", "open_time": "2026-10-29T19:05:50.454764Z", "close_time": "2026-11-02T19:00:00Z", "expected_expiration_time": "2026-10-31T22:00:00Z", "result": "", "rules_primary": "If Utah wins the 3rd quarter of the Portland vs Utah Pro Basketball game originally scheduled for Oct 31, 2026, th`

### KXNBA3QSPREAD — NBA 3rd Quarter Spread
- (8) Portland wins #Q by over # points
- (7) Atlanta wins #Q by over # points
- (7) NAME wins #Q by over # points
- (6) Cleveland wins #Q by over # points
- (6) Sacramento wins #Q by over # points
- (5) Memphis wins #Q by over # points
- samples: KXNBA3QSPREAD-26OCT29CLEATL-CLE9, KXNBA3QSPREAD-26OCT29CLEATL-CLE7, KXNBA3QSPREAD-26OCT29CLEATL-CLE5, KXNBA3QSPREAD-26OCT29CLEATL-CLE3, KXNBA3QSPREAD-26OCT29CLEATL-CLE2, KXNBA3QSPREAD-26OCT29CLEATL-CLE11
- sample fields: `{"ticker": "KXNBA3QSPREAD-26OCT29CLEATL-CLE9", "event_ticker": "KXNBA3QSPREAD-26OCT29CLEATL", "market_type": "binary", "title": "Cleveland wins 3Q by over 8.5 points", "yes_sub_title": "Cleveland wins by over 8.5 points", "no_sub_title": "Cleveland wins by over 8.5 points", "strike_type": "greater", "floor_strike": 8.5, "custom_strike": {"basketball_team": "90381a35-42a6-4975-851f-175418e4271a"}, "status": "active", "open_time": "2026-10-29T13:51:19.449053Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T03:00:00Z", "result": "", "rules_primary": "If Cleveland w`

### KXNBA3QTEAMTOTAL — NBA 3rd Quarter Team Total

### KXNBA3QTOTAL — NBA 3rd Quarter Total
- (39) #rd Quarter: Over # points scored
- samples: KXNBA3QTOTAL-26OCT29CLEATL-74, KXNBA3QTOTAL-26OCT29CLEATL-72, KXNBA3QTOTAL-26OCT29CLEATL-70, KXNBA3QTOTAL-26OCT29CLEATL-68, KXNBA3QTOTAL-26OCT29CLEATL-66, KXNBA3QTOTAL-26OCT29CLEATL-64
- sample fields: `{"ticker": "KXNBA3QTOTAL-26OCT29CLEATL-74", "event_ticker": "KXNBA3QTOTAL-26OCT29CLEATL", "market_type": "binary", "title": "3rd Quarter: Over 73.5 points scored", "yes_sub_title": "Over 73.5 points", "no_sub_title": "Over 73.5 points", "strike_type": "greater", "floor_strike": 73.5, "status": "active", "open_time": "2026-10-29T13:51:19.449053Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T03:00:00Z", "result": "", "rules_primary": "If over 73.5 total points are scored in the 3rd quarter of the Cleveland vs Atlanta Pro Basketball game originally scheduled for `

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
- (3) NAME wins the #th quarter
- (2) Portland wins the #th quarter
- (1) Utah wins the #th quarter
- (1) Cleveland wins the #th quarter
- (1) Atlanta wins the #th quarter
- (1) Phoenix wins the #th quarter
- (1) Denver wins the #th quarter
- samples: KXNBA4Q-26OCT31PORUTA-UTA, KXNBA4Q-26OCT31PORUTA-TIE, KXNBA4Q-26OCT31PORUTA-POR, KXNBA4Q-26OCT29CLEATL-TIE, KXNBA4Q-26OCT29CLEATL-CLE, KXNBA4Q-26OCT29CLEATL-ATL
- sample fields: `{"ticker": "KXNBA4Q-26OCT31PORUTA-UTA", "event_ticker": "KXNBA4Q-26OCT31PORUTA", "market_type": "binary", "title": "Utah wins the 4th quarter", "yes_sub_title": "Utah", "no_sub_title": "Utah", "strike_type": "structured", "custom_strike": {"basketball_team": "6f60dfb1-fda1-423f-b76f-67e9d24b9644"}, "status": "active", "open_time": "2026-10-29T19:05:50.454764Z", "close_time": "2026-11-02T19:00:00Z", "expected_expiration_time": "2026-10-31T22:00:00Z", "result": "", "rules_primary": "If Utah wins the 4th quarter (excluding overtime) of the Portland vs Utah Pro Basketball game originally scheduled`

### KXNBA4QSPREAD — NBA 4th Quarter Spread
- (7) Cleveland wins #Q by over # points
- (7) Portland wins #Q by over # points
- (7) NAME wins #Q by over # points
- (6) Atlanta wins #Q by over # points
- (6) Memphis wins #Q by over # points
- (6) Sacramento wins #Q by over # points
- samples: KXNBA4QSPREAD-26OCT29CLEATL-CLE8, KXNBA4QSPREAD-26OCT29CLEATL-CLE6, KXNBA4QSPREAD-26OCT29CLEATL-CLE4, KXNBA4QSPREAD-26OCT29CLEATL-CLE2, KXNBA4QSPREAD-26OCT29CLEATL-CLE14, KXNBA4QSPREAD-26OCT29CLEATL-CLE12
- sample fields: `{"ticker": "KXNBA4QSPREAD-26OCT29CLEATL-CLE8", "event_ticker": "KXNBA4QSPREAD-26OCT29CLEATL", "market_type": "binary", "title": "Cleveland wins 4Q by over 7.5 points", "yes_sub_title": "Cleveland wins by over 7.5 points", "no_sub_title": "Cleveland wins by over 7.5 points", "strike_type": "greater", "floor_strike": 7.5, "custom_strike": {"basketball_team": "90381a35-42a6-4975-851f-175418e4271a"}, "status": "active", "open_time": "2026-10-29T13:51:19.449053Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T03:00:00Z", "result": "", "rules_primary": "If Cleveland w`

### KXNBA4QTEAMTOTAL — NBA 4th Quarter Team Total

### KXNBA4QTOTAL — NBA 4th Quarter Total
- (39) #th Quarter: Over # points scored
- samples: KXNBA4QTOTAL-26OCT29CLEATL-72, KXNBA4QTOTAL-26OCT29CLEATL-70, KXNBA4QTOTAL-26OCT29CLEATL-68, KXNBA4QTOTAL-26OCT29CLEATL-66, KXNBA4QTOTAL-26OCT29CLEATL-64, KXNBA4QTOTAL-26OCT29CLEATL-62
- sample fields: `{"ticker": "KXNBA4QTOTAL-26OCT29CLEATL-72", "event_ticker": "KXNBA4QTOTAL-26OCT29CLEATL", "market_type": "binary", "title": "4th Quarter: Over 71.5 points scored", "yes_sub_title": "Over 71.5 points", "no_sub_title": "Over 71.5 points", "strike_type": "greater", "floor_strike": 71.5, "status": "active", "open_time": "2026-10-29T13:51:19.449053Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T03:00:00Z", "result": "", "rules_primary": "If over 71.5 total points are scored in the 4th quarter (excluding overtime) of the Cleveland vs Atlanta Pro Basketball game orig`

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
- (108) NAME: #+ assists
- (4) Zach LaVine: #+ assists
- (4) NAME.: #+ assists
- (4) NAME III: #+ assists
- (3) CJ McCollum: #+ assists
- samples: KXNBAAST-26OCT29SACNOP-NOPDQUEEN22-6, KXNBAAST-26OCT29SACNOP-NOPDQUEEN22-4, KXNBAAST-26OCT29SACNOP-NOPDQUEEN22-2, KXNBAAST-26OCT29CLEATL-ATLAWIGGINS2-6, KXNBAAST-26OCT29CLEATL-ATLAWIGGINS2-4, KXNBAAST-26OCT29CLEATL-ATLAWIGGINS2-2
- sample fields: `{"ticker": "KXNBAAST-26OCT29SACNOP-NOPDQUEEN22-6", "event_ticker": "KXNBAAST-26OCT29SACNOP", "market_type": "binary", "title": "Derik Queen: 6+ assists", "yes_sub_title": "Derik Queen: 6+", "no_sub_title": "Derik Queen: 6+", "strike_type": "greater", "floor_strike": 5.5, "custom_strike": {"basketball_player": "1397dd83-6f8b-4ca4-85d8-4ddee4d50e42", "basketball_team": "d3c8c2ac-c4a0-4d67-8b16-53cb91118dfc"}, "status": "active", "open_time": "2026-10-29T18:40:44Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T06:00:00Z", "result": "", "rules_primary": "If Derik Q`

### KXNBAASTPROT — NBA Player Assists Protected
- (108) NAME: #+ assists
- (4) Zach LaVine: #+ assists
- (4) NAME.: #+ assists
- (4) NAME III: #+ assists
- (3) CJ McCollum: #+ assists
- samples: KXNBAASTPROT-26OCT29SACNOP-NOPDQUEEN22-6, KXNBAASTPROT-26OCT29SACNOP-NOPDQUEEN22-4, KXNBAASTPROT-26OCT29SACNOP-NOPDQUEEN22-2, KXNBAASTPROT-26OCT29CLEATL-ATLAWIGGINS2-6, KXNBAASTPROT-26OCT29CLEATL-ATLAWIGGINS2-4, KXNBAASTPROT-26OCT29CLEATL-ATLAWIGGINS2-2
- sample fields: `{"ticker": "KXNBAASTPROT-26OCT29SACNOP-NOPDQUEEN22-6", "event_ticker": "KXNBAASTPROT-26OCT29SACNOP", "market_type": "binary", "title": "Derik Queen: 6+ assists", "yes_sub_title": "Derik Queen: 6+", "no_sub_title": "Derik Queen: 6+", "strike_type": "greater", "floor_strike": 5.5, "custom_strike": {"basketball_player": "1397dd83-6f8b-4ca4-85d8-4ddee4d50e42", "basketball_team": "d3c8c2ac-c4a0-4d67-8b16-53cb91118dfc"}, "status": "active", "open_time": "2026-10-29T18:31:12Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T06:00:00Z", "result": "", "rules_primary": "If`

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
- (39) NAME: #+ blocks
- (2) Zach LaVine: #+ blocks
- (2) NAME.: #+ blocks
- (2) NAME III: #+ blocks
- (2) CJ McCollum: #+ blocks
- samples: KXNBABLK-26OCT29SACNOP-SACZLAVINE8-2, KXNBABLK-26OCT29SACNOP-SACZLAVINE8-1, KXNBABLK-26OCT29SACNOP-SACPACHIUWA9-3, KXNBABLK-26OCT29SACNOP-SACPACHIUWA9-2, KXNBABLK-26OCT29SACNOP-SACPACHIUWA9-1, KXNBABLK-26OCT29SACNOP-SACDSABONIS11-2
- sample fields: `{"ticker": "KXNBABLK-26OCT29SACNOP-SACZLAVINE8-2", "event_ticker": "KXNBABLK-26OCT29SACNOP", "market_type": "binary", "title": "Zach LaVine: 2+ blocks", "yes_sub_title": "Zach LaVine: 2+", "no_sub_title": "Zach LaVine: 2+", "strike_type": "greater", "floor_strike": 1.5, "custom_strike": {"basketball_player": "b02cbe96-1ddf-40bc-9dec-7146c3350d61", "basketball_team": "ab9e2e9a-3243-41b6-a291-95f4d9c6edf7"}, "status": "active", "open_time": "2026-10-29T19:06:19.035546Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T03:00:00Z", "result": "", "rules_primary": "If Z`

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
- (12) NAME player threes escalator
- (1) Zach LaVine player threes escalator
- (1) NAME. player threes escalator
- (1) NAME III player threes escalator
- (1) CJ McCollum player threes escalator
- samples: KXNBAESCALATOR3PT-26OCT29MEMPOR-PORTCAMARA33, KXNBAESCALATOR3PT-26OCT29MEMPOR-PORJMORANT1, KXNBAESCALATOR3PT-26OCT29MEMPOR-PORDLILLARD0, KXNBAESCALATOR3PT-26OCT29MEMPOR-PORDCLINGAN23, KXNBAESCALATOR3PT-26OCT29MEMPOR-PORDAVDIJA8, KXNBAESCALATOR3PT-26OCT29MEMPOR-MEMTJEROME2
- sample fields: `{"ticker": "KXNBAESCALATOR3PT-26OCT29MEMPOR-PORTCAMARA33", "event_ticker": "KXNBAESCALATOR3PT-26OCT29MEMPOR", "market_type": "binary", "title": "Toumani Camara player threes escalator", "yes_sub_title": "Toumani Camara", "no_sub_title": "Toumani Camara", "strike_type": "custom", "custom_strike": {"Payout Per Unit": "0 threes, $0.0000; 1, $0.0010; 2, $0.0080; 3, $0.0270; 4, $0.0640; 5, $0.1250; 6, $0.2160; 7, $0.3430; 8, $0.5120; 9, $0.7290; and 10 or more, $1.0000.", "Payout formula": "floor(10000 x (y / 10)^3) / 10000", "basketball_player": "0ff276a5-115b-4407-94b7-37e21c11454a", "basketball_`

### KXNBAESCALATORPTS — NBA Player Points Escalator
- (13) NAME player points escalator
- (1) Zach LaVine player points escalator
- (1) NAME. player points escalator
- (1) NAME III player points escalator
- (1) CJ McCollum player points escalator
- samples: KXNBAESCALATORPTS-26OCT29MEMPOR-PORJMORANT1, KXNBAESCALATORPTS-26OCT29MEMPOR-PORDLILLARD0, KXNBAESCALATORPTS-26OCT29MEMPOR-PORDAVDIJA8, KXNBAESCALATORPTS-26OCT29MEMPOR-MEMTJEROME2, KXNBAESCALATORPTS-26OCT29MEMPOR-MEMCBOOZER27, KXNBAESCALATORPTS-26OCT29SACNOP-SACZLAVINE8
- sample fields: `{"ticker": "KXNBAESCALATORPTS-26OCT29MEMPOR-PORJMORANT1", "event_ticker": "KXNBAESCALATORPTS-26OCT29MEMPOR", "market_type": "binary", "title": "Ja Morant player points escalator", "yes_sub_title": "Ja Morant", "no_sub_title": "Ja Morant", "strike_type": "custom", "custom_strike": {"Payout Per Unit": "0\u20131 points, $0.0000; 2\u20133, $0.0000; 4\u20135, $0.0005; 6\u20137, $0.0017; 8\u20139, $0.0040; 10\u201311, $0.0080; 12\u201313, $0.0138; 14\u201315, $0.0219; 16\u201317, $0.0327; 18\u201319, $0.0466; 20\u201321, $0.0640; 22\u201323, $0.0851; 24\u201325, $0.1105; 26\u201327, $0.1406; 28\u201`

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
- (7) NAME wins
- (2) Toronto wins
- (2) NAME L wins
- (2) NAME C wins
- (2) Indiana wins
- (2) Brooklyn wins
- (2) Orlando wins
- (2) Boston wins
- samples: KXNBAGAME-26NOV01TORLAL-TOR, KXNBAGAME-26NOV01TORLAL-LAL, KXNBAGAME-26NOV01LACGSW-LAC, KXNBAGAME-26NOV01LACGSW-GSW, KXNBAGAME-26NOV01BKNIND-IND, KXNBAGAME-26NOV01BKNIND-BKN
- sample fields: `{"ticker": "KXNBAGAME-26NOV01TORLAL-TOR", "event_ticker": "KXNBAGAME-26NOV01TORLAL", "market_type": "binary", "title": "Toronto wins", "yes_sub_title": "Toronto", "no_sub_title": "Toronto", "strike_type": "structured", "custom_strike": {"basketball_team": "96c447dd-2cdd-4c58-a151-ef0df87de981"}, "status": "active", "open_time": "2026-10-29T02:06:53.882204Z", "close_time": "2026-11-04T02:00:00Z", "expected_expiration_time": "2026-11-02T05:00:00Z", "result": "", "rules_primary": "If Toronto wins the Toronto vs Los Angeles L Pro Basketball game originally scheduled for Nov 1, 2026, then the marke`

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
- samples: KXNBAOT-26OCT31PORUTA-1, KXNBAOT-26OCT29CLEATL-1, KXNBAOT-26OCT30DENPHX-1, KXNBAOT-26OCT30LALGSW-1, KXNBAOT-26OCT30HOUDAL-1, KXNBAOT-26OCT30LACMIN-1
- sample fields: `{"ticker": "KXNBAOT-26OCT31PORUTA-1", "event_ticker": "KXNBAOT-26OCT31PORUTA", "market_type": "binary", "title": "Game goes to overtime", "yes_sub_title": "Game goes to overtime", "no_sub_title": "Game goes to overtime", "strike_type": "greater", "floor_strike": 0.5, "status": "active", "open_time": "2026-10-29T19:05:50.454764Z", "close_time": "2026-11-02T19:00:00Z", "expected_expiration_time": "2026-10-31T22:00:00Z", "result": "", "rules_primary": "If at least 1 overtime period is played in the Portland vs Utah Pro Basketball game originally scheduled for Oct 31, 2026, then the market resolve`

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
- (54) NAME: #+ points, rebounds, and assists
- (4) CJ McCollum: #+ points, rebounds, and assists
- (3) Zach LaVine: #+ points, rebounds, and assists
- (3) NAME.: #+ points, rebounds, and assists
- (3) NAME III: #+ points, rebounds, and assists
- samples: KXNBAPRA-26OCT29CLEATL-ATLDDANIELS5-15, KXNBAPRA-26OCT29CLEATL-CLEEMOBLEY4-40, KXNBAPRA-26OCT29CLEATL-ATLCMCCOLLUM3-30, KXNBAPRA-26OCT29CLEATL-CLEJHARDEN1-35, KXNBAPRA-26OCT29CLEATL-CLEJHARDEN1-30, KXNBAPRA-26OCT29CLEATL-CLEJHARDEN1-25
- sample fields: `{"ticker": "KXNBAPRA-26OCT29CLEATL-ATLDDANIELS5-15", "event_ticker": "KXNBAPRA-26OCT29CLEATL", "market_type": "binary", "title": "Dyson Daniels: 15+ points, rebounds, and assists", "yes_sub_title": "Dyson Daniels: 15+", "no_sub_title": "Dyson Daniels: 15+", "strike_type": "greater", "floor_strike": 14.5, "custom_strike": {"basketball_player": "f61bdc80-8315-4d93-a488-71dc37ee3e8f", "basketball_team": "e0729403-9c95-4ee2-b5d4-f704d8322570"}, "status": "active", "open_time": "2026-10-29T18:20:36Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T06:00:00Z", "result"`

### KXNBAPREPACK2ML — 2 ML Basketball Combo

### KXNBAPREPACK3ML — 3ML Basketball Combo

### KXNBAPTS — NBA Player Points
- (116) NAME: #+ points
- (5) NAME.: #+ points
- (4) CJ McCollum: #+ points
- (4) Zach LaVine: #+ points
- (4) NAME III: #+ points
- samples: KXNBAPTS-26OCT29MEMPOR-MEMISTEWART28-15, KXNBAPTS-26OCT29SACNOP-NOPBMATHURIN9-20, KXNBAPTS-26OCT29MEMPOR-MEMISTEWART28-10, KXNBAPTS-26OCT29SACNOP-NOPBMATHURIN9-15, KXNBAPTS-26OCT29SACNOP-NOPBMATHURIN9-10, KXNBAPTS-26OCT29SACNOP-NOPDQUEEN22-20
- sample fields: `{"ticker": "KXNBAPTS-26OCT29MEMPOR-MEMISTEWART28-15", "event_ticker": "KXNBAPTS-26OCT29MEMPOR", "market_type": "binary", "title": "Isaiah Stewart: 15+ points", "yes_sub_title": "Isaiah Stewart: 15+", "no_sub_title": "Isaiah Stewart: 15+", "strike_type": "greater", "floor_strike": 14.5, "custom_strike": {"basketball_player": "60e91db8-8128-4e53-9b13-eabdf6913ab5", "basketball_team": "1cfe70b8-4dfc-47dc-acca-b68d4a725972"}, "status": "active", "open_time": "2026-10-29T19:00:56Z", "close_time": "2026-11-01T02:00:00Z", "expected_expiration_time": "2026-10-30T08:00:00Z", "result": "", "rules_primar`

### KXNBAPTSALLGAMES — Pro Basketball Points in Every Game

### KXNBAPTSLEADER — NBA Game Points Leader
- (29) NAME: Points leader
- (2) NAME III: Points leader
- (1) CJ McCollum: Points leader
- (1) Zach LaVine: Points leader
- (1) NAME.: Points leader
- samples: KXNBAPTSLEADER-26OCT29CLEATL-CLESMERRILL5, KXNBAPTSLEADER-26OCT29CLEATL-CLEPWATSON8, KXNBAPTSLEADER-26OCT29CLEATL-CLEJHARDEN1, KXNBAPTSLEADER-26OCT29CLEATL-CLEJALLEN31, KXNBAPTSLEADER-26OCT29CLEATL-CLEEMOBLEY4, KXNBAPTSLEADER-26OCT29CLEATL-CLEDMITCHELL45
- sample fields: `{"ticker": "KXNBAPTSLEADER-26OCT29CLEATL-CLESMERRILL5", "event_ticker": "KXNBAPTSLEADER-26OCT29CLEATL", "market_type": "binary", "title": "Sam Merrill: Points leader", "yes_sub_title": "Sam Merrill", "no_sub_title": "Sam Merrill", "strike_type": "structured", "custom_strike": {"basketball_player": "5e64b57d-17f7-46e7-af61-b749c276591f", "basketball_team": "90381a35-42a6-4975-851f-175418e4271a"}, "status": "active", "open_time": "2026-10-29T14:06:26.671303Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T03:00:00Z", "result": "", "rules_primary": "If Sam Merrill `

### KXNBAPTSPROT — NBA Player Points Protected
- (116) NAME: #+ points
- (5) NAME.: #+ points
- (4) CJ McCollum: #+ points
- (4) Zach LaVine: #+ points
- (4) NAME III: #+ points
- samples: KXNBAPTSPROT-26OCT29MEMPOR-MEMISTEWART28-15, KXNBAPTSPROT-26OCT29MEMPOR-MEMISTEWART28-10, KXNBAPTSPROT-26OCT29SACNOP-NOPBMATHURIN9-20, KXNBAPTSPROT-26OCT29SACNOP-NOPBMATHURIN9-15, KXNBAPTSPROT-26OCT29SACNOP-NOPBMATHURIN9-10, KXNBAPTSPROT-26OCT29SACNOP-NOPDQUEEN22-20
- sample fields: `{"ticker": "KXNBAPTSPROT-26OCT29MEMPOR-MEMISTEWART28-15", "event_ticker": "KXNBAPTSPROT-26OCT29MEMPOR", "market_type": "binary", "title": "Isaiah Stewart: 15+ points", "yes_sub_title": "Isaiah Stewart: 15+", "no_sub_title": "Isaiah Stewart: 15+", "strike_type": "greater", "floor_strike": 14.5, "custom_strike": {"basketball_player": "60e91db8-8128-4e53-9b13-eabdf6913ab5", "basketball_team": "1cfe70b8-4dfc-47dc-acca-b68d4a725972"}, "status": "active", "open_time": "2026-10-29T18:50:43Z", "close_time": "2026-11-01T02:00:00Z", "expected_expiration_time": "2026-10-30T08:00:00Z", "result": "", "rule`

### KXNBARA — Pro Basketball Player Rebounds + Assists

### KXNBARACE — NBA Race to Points
- (9) NAME reaches # points first
- (6) Portland reaches # points first
- (3) Utah reaches # points first
- (3) Cleveland reaches # points first
- (3) Atlanta reaches # points first
- (3) Phoenix reaches # points first
- (3) Denver reaches # points first
- (3) NAME L reaches # points first
- samples: KXNBARACE-26OCT31PORUTA-30-UTA, KXNBARACE-26OCT31PORUTA-30-POR, KXNBARACE-26OCT31PORUTA-20-UTA, KXNBARACE-26OCT31PORUTA-20-POR, KXNBARACE-26OCT31PORUTA-10-UTA, KXNBARACE-26OCT31PORUTA-10-POR
- sample fields: `{"ticker": "KXNBARACE-26OCT31PORUTA-30-UTA", "event_ticker": "KXNBARACE-26OCT31PORUTA-30", "market_type": "binary", "title": "Utah reaches 30 points first", "yes_sub_title": "Utah", "no_sub_title": "Utah", "strike_type": "custom", "custom_strike": {"Points": "30", "basketball_team": "6f60dfb1-fda1-423f-b76f-67e9d24b9644"}, "status": "active", "open_time": "2026-10-29T19:05:50.454764Z", "close_time": "2026-11-02T19:00:00Z", "expected_expiration_time": "2026-10-31T22:00:00Z", "result": "", "rules_primary": "If Utah is the first to score 30 points in the Portland vs Utah Pro Basketball game origi`

### KXNBAREB — NBA Player Rebounds
- (141) NAME: #+ rebounds
- (4) Zach LaVine: #+ rebounds
- (4) NAME III: #+ rebounds
- (3) CJ McCollum: #+ rebounds
- (3) NAME.: #+ rebounds
- samples: KXNBAREB-26OCT29MEMPOR-MEMISTEWART28-8, KXNBAREB-26OCT29MEMPOR-MEMISTEWART28-6, KXNBAREB-26OCT29MEMPOR-MEMISTEWART28-4, KXNBAREB-26OCT29MEMPOR-MEMISTEWART28-2, KXNBAREB-26OCT29SACNOP-NOPDQUEEN22-12, KXNBAREB-26OCT29CLEATL-ATLDDANIELS5-2
- sample fields: `{"ticker": "KXNBAREB-26OCT29MEMPOR-MEMISTEWART28-8", "event_ticker": "KXNBAREB-26OCT29MEMPOR", "market_type": "binary", "title": "Isaiah Stewart: 8+ rebounds", "yes_sub_title": "Isaiah Stewart: 8+", "no_sub_title": "Isaiah Stewart: 8+", "strike_type": "greater", "floor_strike": 7.5, "custom_strike": {"basketball_player": "60e91db8-8128-4e53-9b13-eabdf6913ab5", "basketball_team": "1cfe70b8-4dfc-47dc-acca-b68d4a725972"}, "status": "active", "open_time": "2026-10-29T19:00:56Z", "close_time": "2026-11-01T02:00:00Z", "expected_expiration_time": "2026-10-30T08:00:00Z", "result": "", "rules_primary":`

### KXNBAREBPROT — NBA Player Rebounds Protected
- (141) NAME: #+ rebounds
- (4) Zach LaVine: #+ rebounds
- (4) NAME III: #+ rebounds
- (3) CJ McCollum: #+ rebounds
- (3) NAME.: #+ rebounds
- samples: KXNBAREBPROT-26OCT29MEMPOR-MEMISTEWART28-8, KXNBAREBPROT-26OCT29MEMPOR-MEMISTEWART28-6, KXNBAREBPROT-26OCT29MEMPOR-MEMISTEWART28-4, KXNBAREBPROT-26OCT29MEMPOR-MEMISTEWART28-2, KXNBAREBPROT-26OCT29SACNOP-NOPDQUEEN22-12, KXNBAREBPROT-26OCT29CLEATL-ATLDDANIELS5-2
- sample fields: `{"ticker": "KXNBAREBPROT-26OCT29MEMPOR-MEMISTEWART28-8", "event_ticker": "KXNBAREBPROT-26OCT29MEMPOR", "market_type": "binary", "title": "Isaiah Stewart: 8+ rebounds", "yes_sub_title": "Isaiah Stewart: 8+", "no_sub_title": "Isaiah Stewart: 8+", "strike_type": "greater", "floor_strike": 7.5, "custom_strike": {"basketball_player": "60e91db8-8128-4e53-9b13-eabdf6913ab5", "basketball_team": "1cfe70b8-4dfc-47dc-acca-b68d4a725972"}, "status": "active", "open_time": "2026-10-29T18:50:54Z", "close_time": "2026-11-01T02:00:00Z", "expected_expiration_time": "2026-10-30T08:00:00Z", "result": "", "rules_p`

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
- (54) NAME wins by over # points
- (27) Boston wins by over # points
- (24) Detroit wins by over # points
- (24) Portland wins by over # points
- (23) Minnesota wins by over # points
- (21) Houston wins by over # points
- (20) Denver wins by over # points
- (20) Miami wins by over # points
- samples: KXNBASPREAD-26OCT30DENPHX-PHX8, KXNBASPREAD-26OCT30DENPHX-PHX6, KXNBASPREAD-26OCT30DENPHX-PHX4, KXNBASPREAD-26OCT30DENPHX-PHX3, KXNBASPREAD-26OCT30DENPHX-PHX24, KXNBASPREAD-26OCT30DENPHX-PHX22
- sample fields: `{"ticker": "KXNBASPREAD-26OCT30DENPHX-PHX8", "event_ticker": "KXNBASPREAD-26OCT30DENPHX", "market_type": "binary", "title": "Phoenix wins by over 7.5 points", "yes_sub_title": "Phoenix wins by over 7.5 points", "no_sub_title": "Phoenix wins by over 7.5 points", "strike_type": "greater", "floor_strike": 7.5, "custom_strike": {"basketball_team": "ace11dff-c5d1-4ab9-9452-5312253659fd"}, "status": "active", "open_time": "2026-10-29T16:53:33.352189Z", "close_time": "2026-11-02T02:00:00Z", "expected_expiration_time": "2026-10-31T05:00:00Z", "result": "", "rules_primary": "If Phoenix wins by more tha`

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
- (58) NAME: #+ steals
- (3) NAME III: #+ steals
- (2) Zach LaVine: #+ steals
- (2) NAME.: #+ steals
- (2) CJ McCollum: #+ steals
- samples: KXNBASTL-26OCT29SACNOP-SACZLAVINE8-2, KXNBASTL-26OCT29SACNOP-SACZLAVINE8-1, KXNBASTL-26OCT29SACNOP-SACPACHIUWA9-3, KXNBASTL-26OCT29SACNOP-SACPACHIUWA9-2, KXNBASTL-26OCT29SACNOP-SACPACHIUWA9-1, KXNBASTL-26OCT29SACNOP-SACDSABONIS11-2
- sample fields: `{"ticker": "KXNBASTL-26OCT29SACNOP-SACZLAVINE8-2", "event_ticker": "KXNBASTL-26OCT29SACNOP", "market_type": "binary", "title": "Zach LaVine: 2+ steals", "yes_sub_title": "Zach LaVine: 2+", "no_sub_title": "Zach LaVine: 2+", "strike_type": "greater", "floor_strike": 1.5, "custom_strike": {"basketball_player": "b02cbe96-1ddf-40bc-9dec-7146c3350d61", "basketball_team": "ab9e2e9a-3243-41b6-a291-95f4d9c6edf7"}, "status": "active", "open_time": "2026-10-29T19:06:19.035546Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T03:00:00Z", "result": "", "rules_primary": "If Z`

### KXNBASTOCK — NBA Player Steals + Blocks
- (37) NAME: #+ steals and blocks
- (2) Zach LaVine: #+ steals and blocks
- (2) NAME.: #+ steals and blocks
- (2) NAME III: #+ steals and blocks
- (2) CJ McCollum: #+ steals and blocks
- samples: KXNBASTOCK-26OCT29SACNOP-SACZLAVINE8-3, KXNBASTOCK-26OCT29SACNOP-SACZLAVINE8-2, KXNBASTOCK-26OCT29SACNOP-SACPACHIUWA9-4, KXNBASTOCK-26OCT29SACNOP-SACPACHIUWA9-3, KXNBASTOCK-26OCT29SACNOP-SACPACHIUWA9-2, KXNBASTOCK-26OCT29SACNOP-SACDSABONIS11-3
- sample fields: `{"ticker": "KXNBASTOCK-26OCT29SACNOP-SACZLAVINE8-3", "event_ticker": "KXNBASTOCK-26OCT29SACNOP", "market_type": "binary", "title": "Zach LaVine: 3+ steals and blocks", "yes_sub_title": "Zach LaVine: 3+", "no_sub_title": "Zach LaVine: 3+", "strike_type": "greater", "floor_strike": 2.5, "custom_strike": {"basketball_player": "b02cbe96-1ddf-40bc-9dec-7146c3350d61", "basketball_team": "ab9e2e9a-3243-41b6-a291-95f4d9c6edf7"}, "status": "active", "open_time": "2026-10-29T19:06:19.035546Z", "close_time": "2026-11-01T00:00:00Z", "expected_expiration_time": "2026-10-30T03:00:00Z", "result": "", "rules_`

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
- (19) Minnesota over # points scored
- (19) NAME C over # points scored
- (19) Cleveland over # points scored
- (19) Atlanta over # points scored
- (19) Sacramento over # points scored
- (19) NAME over # points scored
- (19) Portland over # points scored
- (19) Memphis over # points scored
- samples: KXNBATEAMTOTAL-26OCT30LACMIN-MIN98, KXNBATEAMTOTAL-26OCT30LACMIN-MIN134, KXNBATEAMTOTAL-26OCT30LACMIN-MIN132, KXNBATEAMTOTAL-26OCT30LACMIN-MIN130, KXNBATEAMTOTAL-26OCT30LACMIN-MIN128, KXNBATEAMTOTAL-26OCT30LACMIN-MIN126
- sample fields: `{"ticker": "KXNBATEAMTOTAL-26OCT30LACMIN-MIN98", "event_ticker": "KXNBATEAMTOTAL-26OCT30LACMIN", "market_type": "binary", "title": "Minnesota over 97.5 points scored", "yes_sub_title": "Minnesota over 97.5 points", "no_sub_title": "Minnesota over 97.5 points", "strike_type": "greater", "floor_strike": 97.5, "custom_strike": {"basketball_team": "29e3c04e-fadb-4006-be20-cbb8c159ce0e"}, "status": "active", "open_time": "2026-10-29T16:33:29.525875Z", "close_time": "2026-11-02T00:00:00Z", "expected_expiration_time": "2026-10-31T03:00:00Z", "result": "", "rules_primary": "If Minnesota scores more th`

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
- (377) NAME: Over # points scored
- samples: KXNBATOTAL-26OCT30DENPHX-256, KXNBATOTAL-26OCT30DENPHX-254, KXNBATOTAL-26OCT30DENPHX-252, KXNBATOTAL-26OCT30DENPHX-250, KXNBATOTAL-26OCT30DENPHX-248, KXNBATOTAL-26OCT30DENPHX-246
- sample fields: `{"ticker": "KXNBATOTAL-26OCT30DENPHX-256", "event_ticker": "KXNBATOTAL-26OCT30DENPHX", "market_type": "binary", "title": "Full Game: Over 255.5 points scored", "yes_sub_title": "Over 255.5 points", "no_sub_title": "Over 255.5 points", "strike_type": "greater", "floor_strike": 255.5, "status": "active", "open_time": "2026-10-29T16:53:33.352189Z", "close_time": "2026-11-02T02:00:00Z", "expected_expiration_time": "2026-10-31T05:00:00Z", "result": "", "rules_primary": "If over 255.5 total points are scored in the Denver vs Phoenix Pro Basketball game originally scheduled for Oct 30, 2026, then the`

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
- (9) NAME wins by # to # points
- (4) Boston wins by # to # points
- (3) Phoenix wins by # to # points
- (3) Denver wins by # to # points
- (3) Minnesota wins by # to # points
- (3) NAME C wins by # to # points
- (3) NAME L wins by # to # points
- (3) NAME wins by # or more points
- samples: KXNBAWINMARGIN-26OCT30DENPHX-PHX6TO10, KXNBAWINMARGIN-26OCT30DENPHX-PHX21PLUS, KXNBAWINMARGIN-26OCT30DENPHX-PHX1TO5, KXNBAWINMARGIN-26OCT30DENPHX-PHX11TO20, KXNBAWINMARGIN-26OCT30DENPHX-DEN6TO10, KXNBAWINMARGIN-26OCT30DENPHX-DEN21PLUS
- sample fields: `{"ticker": "KXNBAWINMARGIN-26OCT30DENPHX-PHX6TO10", "event_ticker": "KXNBAWINMARGIN-26OCT30DENPHX", "market_type": "binary", "title": "Phoenix wins by 6 to 10 points", "yes_sub_title": "Phoenix wins by 6-10 points", "no_sub_title": "Phoenix wins by 6-10 points", "strike_type": "custom", "custom_strike": {"Winning Margin": "6 to 10", "basketball_team": "ace11dff-c5d1-4ab9-9452-5312253659fd"}, "status": "active", "open_time": "2026-10-29T16:54:15.274513Z", "close_time": "2026-11-02T02:00:00Z", "expected_expiration_time": "2026-10-31T05:00:00Z", "result": "", "rules_primary": "If Phoenix wins the`

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

- `KXNBA3PTPROT-26OCT29CLEATL-ATLLDORT0-5` — Luguentz Dort: 5+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLLDORT0-4` — Luguentz Dort: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLLDORT0-3` — Luguentz Dort: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLLDORT0-2` — Luguentz Dort: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLLDORT0-1` — Luguentz Dort: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEJTYSON20-5` — Jaylon Tyson: 5+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEJTYSON20-4` — Jaylon Tyson: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEJTYSON20-3` — Jaylon Tyson: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEJTYSON20-2` — Jaylon Tyson: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEJTYSON20-1` — Jaylon Tyson: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLESMERRILL5-5` — Sam Merrill: 5+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLESMERRILL5-4` — Sam Merrill: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLESMERRILL5-3` — Sam Merrill: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLESMERRILL5-2` — Sam Merrill: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLESMERRILL5-1` — Sam Merrill: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEPWATSON8-5` — Peyton Watson: 5+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEPWATSON8-4` — Peyton Watson: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEPWATSON8-3` — Peyton Watson: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEPWATSON8-2` — Peyton Watson: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEPWATSON8-1` — Peyton Watson: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEJHARDEN1-5` — James Harden: 5+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEJHARDEN1-4` — James Harden: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEJHARDEN1-3` — James Harden: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEJHARDEN1-2` — James Harden: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEJHARDEN1-1` — James Harden: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEEMOBLEY4-5` — Evan Mobley: 5+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEEMOBLEY4-4` — Evan Mobley: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEEMOBLEY4-3` — Evan Mobley: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEEMOBLEY4-2` — Evan Mobley: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEEMOBLEY4-1` — Evan Mobley: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEDMITCHELL45-5` — Donovan Mitchell: 5+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEDMITCHELL45-4` — Donovan Mitchell: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEDMITCHELL45-3` — Donovan Mitchell: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEDMITCHELL45-2` — Donovan Mitchell: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-CLEDMITCHELL45-1` — Donovan Mitchell: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLOOKONGWU17-5` — Onyeka Okongwu: 5+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLOOKONGWU17-4` — Onyeka Okongwu: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLOOKONGWU17-3` — Onyeka Okongwu: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLOOKONGWU17-2` — Onyeka Okongwu: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLOOKONGWU17-1` — Onyeka Okongwu: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLNALEXANDERWALKER7-5` — Nickeil Alexander-Walker: 5+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLNALEXANDERWALKER7-4` — Nickeil Alexander-Walker: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLNALEXANDERWALKER7-3` — Nickeil Alexander-Walker: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLNALEXANDERWALKER7-2` — Nickeil Alexander-Walker: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLNALEXANDERWALKER7-1` — Nickeil Alexander-Walker: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLJJOHNSON1-5` — Jalen Johnson: 5+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLJJOHNSON1-4` — Jalen Johnson: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLJJOHNSON1-3` — Jalen Johnson: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLJJOHNSON1-2` — Jalen Johnson: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLJJOHNSON1-1` — Jalen Johnson: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLDDANIELS5-4` — Dyson Daniels: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLDDANIELS5-3` — Dyson Daniels: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLDDANIELS5-2` — Dyson Daniels: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLDDANIELS5-1` — Dyson Daniels: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLCMCCOLLUM3-5` — CJ McCollum: 5+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLCMCCOLLUM3-4` — CJ McCollum: 4+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLCMCCOLLUM3-3` — CJ McCollum: 3+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLCMCCOLLUM3-2` — CJ McCollum: 2+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLCMCCOLLUM3-1` — CJ McCollum: 1+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title
- `KXNBA3PTPROT-26OCT29CLEATL-ATLAWIGGINS2-5` — Aaron Wiggins: 5+ threes — series KXNBA3PTPROT not in ontology; player-stat words in title

## Series decisions (basketball-related)

- NBA  `KXNBAH2HPTS` NBA Head-to-Head Points — ticker prefix KXNBA
- skip `KXNCAAMBSUM` Summit League Conference Tournament — no NBA marker
- NBA  `KXNBA3PTPROT` NBA Player Threes Protected — ticker prefix KXNBA
- NBA  `KXNBAEAST` Pro Basketball Eastern Conference Champion — ticker prefix KXNBA
- NBA  `KXNBA2D` NBA Player Double Double — ticker prefix KXNBA
- NBA  `KXNBADRAFT7` NBA Draft Seventh Pick — ticker prefix KXNBA
- skip `KXWNBAPORTNOY` WNBA Portnoy ban — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAHOMECLINCH` Pro Basketball Series Winner to Clinch at Home — ticker prefix KXNBA
- skip `KXWFIBAWC` Women's FIBA World Cup Winner — no NBA marker
- skip `KXEUROLEAGUE` EuroLeague Champion — no NBA marker
- skip `KXNBIGAME` Hungary NB I. A Game — no NBA marker
- NBA  `KXNBASUMMER1HTOTAL` Pro Basketball Summer League 1st Half Total — ticker prefix KXNBA
- skip `KXSPORTSIGNLBJ` LeBron James sign — no NBA marker
- NBA  `KXNBASUMMERSPREAD` Pro Basketball Summer League Spread — ticker prefix KXNBA
- skip `KXNCAAWBSEC` Women's College Basketball SEC Conference Tournament Champion — no NBA marker
- NBA  `KXNBATOTAL` NBA Total — ticker prefix KXNBA
- skip `KXNCAAMBUAC` United Athletic Conference Conference Tournament — no NBA marker
- skip `KXBAN2XRAKAI` 2xRaKai BE UNBANNED — no NBA marker
- NBA  `KXNBASERIESASTLEADER` Pro Basketball Series Assists Leader — ticker prefix KXNBA
- skip `KXNCAAMBOT` Men's College Basketball Overtime — no NBA marker
- skip `KXLBLGAME` Latvia LBL Game — no NBA marker
- skip `KXWNBASSTARS` Women's Pro Basketball Shooting Stars Contest — non-NBA basketball marker 'WNBA'
- NBA  `KXMVENBASINGLEGAME` MVE NBA Single Game — title mentions NBA
- NBA  `KXNBASHOOTINGSTARS` Pro Basketball Shooting Stars Contest — ticker prefix KXNBA
- skip `KXLEADERWNBAREB` WNBA RPG Leader — non-NBA basketball marker 'WNBA'
- skip `KXWNBA3PTCONTEST` Women's Pro Basketball 3-Point Contest — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAFINALSEXACT` Pro Basketball Championship Series Score — ticker prefix KXNBA
- NBA  `KXNBA1HSPREAD` NBA 1st Half Spread — ticker prefix KXNBA
- NBA  `KXNBASOUTHWEST` Pro Basketball Southwest Division Winner — ticker prefix KXNBA
- skip `KXEUROBASKETGAME` EuroBasket Game — no NBA marker
- NBA  `KXNBAWHATTEND` Pro Basketball White House Attend — ticker prefix KXNBA
- skip `KXNCAABBIGEAST` Big East Men's Basketball Tournament — no NBA marker
- NBA  `KXNBAATLANTIC` Pro Basketball Atlantic Division Winner — ticker prefix KXNBA
- skip `KXNCAAMBNEC` Northeast Conference Tournament — no NBA marker
- NBA  `KXNBASEATTLE` Seattle NBA team — ticker prefix KXNBA
- skip `KXWNBAH2HPTS` Women's Pro Basketball Head to Head Points — non-NBA basketball marker 'WNBA'
- skip `KXNCAAMBSTATLEADER` Men's College Basketball Stat Leader — no NBA marker
- NBA  `KXNBA2H` NBA 2nd Half Winner — ticker prefix KXNBA
- NBA  `KXNBASERIES` NBA Series Winner — ticker prefix KXNBA
- NBA  `KXNBATEAMTOTAL` NBA Team Total — ticker prefix KXNBA
- skip `KXTRUMPCANBAN` Trump Canada ban — no NBA marker
- NBA  `KXNBAALLSTAR` NBA All-Star game — ticker prefix KXNBA
- skip `KXNCAAWB1HTOTAL` Women's College Basketball 1st Half Total — no NBA marker
- NBA  `KXNBAAST` NBA Player Assists — ticker prefix KXNBA
- skip `KXNEWCOACHLAL` New Lakers coach — no NBA marker
- skip `KXNCAAWBOT` Women's College Basketball Overtime — no NBA marker
- NBA  `KXNBAWINSTREAK` NBA Longest Win Streak — ticker prefix KXNBA
- skip `KXEARNINGSMENTIONBAC` Bank of America Earnings Mention — no NBA marker
- skip `KXNCAAWBWINMARGIN` Women's College Basketball Winning Margin — no NBA marker
- skip `KXMARMADSEEDSUM` March Madness Sum of Seeds — no NBA marker
- NBA  `KXNBAOVERTIME` NBA Overtime — ticker prefix KXNBA
- skip `KXCBVOLUME` Coinbase volume — no NBA marker
- NBA  `KXNBAXMASOPPONENT` Pro Basketball Christmas Day Opponent — ticker prefix KXNBA
- skip `KXNCAAMBSWAC` Southwestern Atlantic Conference Tournament — no NBA marker
- NBA  `KXNBANEXTCONTRACT` Pro Basketball Next Contract Size — ticker prefix KXNBA
- NBA  `KXNBALASTTOLOSE` NBA Last Undefeated Team — ticker prefix KXNBA
- skip `KXNCAAWBFIRST3PT` Women's College Basketball First Team to Make a Three — no NBA marker
- skip `KXBIG3` BIG3 Champion — no NBA marker
- skip `KXOTDBASKETBALL` Off The Dribble Basketball — no NBA marker
- skip `KXJOINBARSTOOL` Will Shannon sharpe join meta — no NBA marker
- skip `KXCHINAUNBANBTC` Will China unban Bitcoin? — no NBA marker
- NBA  `KXNBAPA` Pro Basketball Player Points + Assists — ticker prefix KXNBA
- skip `KXLUBGAME` Uruguay LUB Basketball Game — no NBA marker
- NBA  `KXNBAEXTENSION` NBA Player Contract Extension — ticker prefix KXNBA
- NBA  `KXNBASUMMER` Pro Basketball Summer League Champion — ticker prefix KXNBA
- NBA  `KXNBASERIESCOMEBACK` Pro Basketball Series Comeback — ticker prefix KXNBA
- skip `KXWNBAEAST1` Women's Pro Basketball Eastern Conference #1 Seed — non-NBA basketball marker 'WNBA'
- skip `KXWNBA1QWINNER` Women's Pro Basketball 1st Quarter Winner — non-NBA basketball marker 'WNBA'
- skip `KXMARMADCONFWIN` March Madness Conference Winner — no NBA marker
- skip `KXNBLGAME` Australia NBL Game — no NBA marker
- skip `KXMARMADROUND` Reach March Madness Round — no NBA marker
- NBA  `KXNBASERIESROADWINS` Pro Basketball Series Total Road Wins — ticker prefix KXNBA
- NBA  `KXNBARECORD` Pro Basketball Best/Worst Regular Season Record — ticker prefix KXNBA
- skip `KXNEXTTEAMGIANNIS` Giannis next team — no NBA marker
- skip `KXNCAAMBBIG12REG` Men's College Basketball Big 12 Regular Season Champion — no NBA marker
- NBA  `KXNBARETURN` Pro Basketball Player to Return — ticker prefix KXNBA
- skip `KXBIG3GAME` Big 3 Basketball Game — no NBA marker
- skip `KXWCBAGAME` China CBA (W) Game — no NBA marker
- skip `KXNCAAWB1HSPREAD` Women's College Basketball 1st Half Spread — no NBA marker
- skip `KXNCAAWBBIG12` Women's College Basketball Big 12 Conference Tournament Champion — no NBA marker
- NBA  `KXNBASUMMER1HSPREAD` Pro Basketball Summer League 1st Half Spread — ticker prefix KXNBA
- skip `KXMARMADSEEDDIF` March Madness Biggest Upset — no NBA marker
- NBA  `KXNBAUNBEATEN` NBA Playoffs Team to go Undefeated — ticker prefix KXNBA
- skip `KXSBLTOTAL` Slovakia SBL Total — no NBA marker
- NBA  `KXMEDIACOVERNBA2K` WHO WILL BE ON THE COVER OF NBA 2K — title mentions NBA
- skip `KXNCAAWB3Q` Women's College Basketball 3rd Quarter Winner — no NBA marker
- skip `KXKYBOURBONBARRELS` Kentucky aging Bourbon-barrel inventory — no NBA marker
- NBA  `KXNBADRAFT1` NBA Draft First Pick — ticker prefix KXNBA
- skip `KXISL` Israeli Super League Champion — no NBA marker
- NBA  `KXNBAROOKIE2NDTEAM` NBA All-Rookie 2nd Team — ticker prefix KXNBA
- skip `KXSBLGAME` Slovakia SBL Game — no NBA marker
- skip `KXLNBELITEGAME` LNB Elite Game — no NBA marker
- skip `KXFIBACHAMPLEAGUEGAME` FIBA Champions League Game — no NBA marker
- NBA  `KXNBASTATLEADER` NBA Regular Season League Leader — ticker prefix KXNBA
- skip `KXTRADEOFFNBA` Pro basketball trades offseason — no NBA marker
- skip `KXNCAAMBNEXTCOACH` Men's College Basketball Next Coach — no NBA marker
- NBA  `KXNBA30COMEBACK` NBA 3-0 Series Comeback — ticker prefix KXNBA
- skip `KXNCAAMBFIRST50` Men's College Basketball Race to 50 Points — no NBA marker
- NBA  `KXNBA2Q` NBA 2nd Quarter Winner — ticker prefix KXNBA
- NBA  `KXNBARACE` NBA Race to Points — ticker prefix KXNBA
- skip `KXEUROLEAGUEGAME` Euroleague Game — no NBA marker
- skip `KXNCAAWBBBBB` NCAAWB Conference Champions — no NBA marker
- NBA  `KXNBADRAFT2` NBA Draft Second Pick — ticker prefix KXNBA
- NBA  `KXNBACUP` Pro Basketball Cup Champion — ticker prefix KXNBA
- skip `KXMARMAD3D` Men's March Madness Triple Double — no NBA marker
- NBA  `KXNBAEUROPEANNOUNCE` NBA Europe Inaugural Season Being Announced — ticker prefix KXNBA
- skip `KXISLTOTAL` Israel Super League Total — no NBA marker
- skip `KXMARMAD1SEED` March Madness 1 Seeds — no NBA marker
- skip `KXSPORTSIGNAHOR` Al Horford — no NBA marker
- NBA  `KXNBAPTSALLGAMES` Pro Basketball Points in Every Game — ticker prefix KXNBA
- skip `KXSNAPELECTIONBAHA` Bhamanian election — no NBA marker
- NBA  `KXNBAESCALATORPTS` NBA Player Points Escalator — ticker prefix KXNBA
- skip `KXWNBADRAFT5` WNBA Draft 5th Pick — non-NBA basketball marker 'WNBA'
- skip `KXSKLGAME` Slovenia 1. SKL Game — no NBA marker
- skip `KXIBPLGAME` Men's Iceland Basketball Premier League Game — no NBA marker
- skip `KXWCCREG` West Coast Conference Regular Season Champions — no NBA marker
- NBA  `KXNBA4QTOTAL` NBA 4th Quarter Total — ticker prefix KXNBA
- NBA  `KXNBADRAFTCOMP` Pro Basketball Draft Comparison — ticker prefix KXNBA
- skip `KXNCAAMBCONFLEADER` Men's College Basketball Conference Stat Leader — no NBA marker
- NBA  `KXNBAWEST` Pro Basketball Western Conference Champion — ticker prefix KXNBA
- skip `KXNCAAMBBIGEASTQUAL` Men's College Basketball Big East Championship Qualifiers — no NBA marker
- skip `KXNCAAWB4QTOTAL` Women's College Basketball 4th Quarter Total — no NBA marker
- skip `KXNCAAMBSLC` Southland Conference Tournament — no NBA marker
- skip `KXNCAAMBSECQUAL` Men's College Basketball SEC Championship Qualifiers — no NBA marker
- skip `KXNCAAWBNIT` Women's NIT Tournament Champion — no NBA marker
- skip `KXWNBAPTS` WNBA Player Points — non-NBA basketball marker 'WNBA'
- skip `KXNCAAMB1HSPREAD` Men's College Basketball 1st Half Spread — no NBA marker
- NBA  `KXNBA4QSPREAD` NBA 4th Quarter Spread — ticker prefix KXNBA
- skip `KXWNBA3PTCONTESTOU` Women's Pro Basketball 3-Point Contest Threes Made — non-NBA basketball marker 'WNBA'
- NBA  `KXNBATOJOINCBA` NBA Players to Join the CBA — ticker prefix KXNBA
- NBA  `KXNBASERIESPTS` Pro Basketball Series Player Points — ticker prefix KXNBA
- NBA  `KXNBATEAMANNOUNCE` Pro Basketball New Team Announce — ticker prefix KXNBA
- skip `KXWNBA1HSPREAD` Women's Pro Basketball 1st Half Spread — non-NBA basketball marker 'WNBA'
- skip `KXNCAABACC` ACC Men's Basketball Tournament — no NBA marker
- skip `KXWNBA2QSPREAD` Women's Pro Basketball 2nd Quarter Spread — non-NBA basketball marker 'WNBA'
- skip `KXVBAGAME` Vietnam VBA Game — no NBA marker
- NBA  `KXNBAMENTION` NBA Mention — ticker prefix KXNBA
- NBA  `KXNBANEWCHAMP` NBA First-Time Champion — ticker prefix KXNBA
- skip `KXBBLGAME` Bundesliga Basketball Game — no NBA marker
- skip `KXVTBSPREAD` Russia VTB United Spread — no NBA marker
- skip `KXNCAAMBUNDEFEATED` Undefeated in College Basketball Regular Season — no NBA marker
- skip `KXNCAAMBMAA` Metro Atlantic Conference Tournament — no NBA marker
- skip `KXLEADERWNBA3PT` WNBA Total 3-Pointers Made Leader — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAFINBLOWOUT` Pro Basketball Finals Blowout — ticker prefix KXNBA
- skip `KXNCAAWB2QTOTAL` Women's College Basketball 2nd Quarter Total — no NBA marker
- skip `KXNCAAMACC` ACC MEN'S BASKETBALL TOURNAMENT — no NBA marker
- skip `KXWNBASERIESSCORE` WNBA Series Exact Score — non-NBA basketball marker 'WNBA'
- skip `KXWNBAFINALLOC` WNBA Finals Location — non-NBA basketball marker 'WNBA'
- skip `KXGRAMBPRNBA` Best Progressive R&B Album — no NBA marker
- NBA  `KXNBAFIRST50PTS` First NBA Player to Score 50 Points — ticker prefix KXNBA
- skip `KXCBA` China CBA Champion — no NBA marker
- NBA  `KXNBAPOLOSE` Pro Basketball Playoff Losses — ticker prefix KXNBA
- skip `KXWNBA3QSPREAD` Women's Pro Basketball 3rd Quarter Spread — non-NBA basketball marker 'WNBA'
- skip `KXLPBGAME` Portugal LPB Game — no NBA marker
- NBA  `KXNBAPLAYERHIGHSCORE` NBA Highest Scoring Performance in Regular Season — ticker prefix KXNBA
- skip `KXNCAAWB4QSPREAD` Women's College Basketball 4th Quarter Spread — no NBA marker
- NBA  `KXNBARA` Pro Basketball Player Rebounds + Assists — ticker prefix KXNBA
- NBA  `KXNBAFINMVP` NBA Finals MVP — ticker prefix KXNBA
- skip `KXNCAAMBACC` ACC Conference Tournament — no NBA marker
- skip `KXMWREG` Mountain West Regular Season Champions — no NBA marker
- skip `KXSLBSPREAD` England Super League Basketball Spread — no NBA marker
- NBA  `KXNBASERIESGAMES` NBA Series Total Games — ticker prefix KXNBA
- NBA  `KXNBACUPGROUP` NBA Cup Group Winner — ticker prefix KXNBA
- NBA  `KXNBAPLAYOFFWINS` NBA Playoff Wins by Team — ticker prefix KXNBA
- NBA  `KXNBASERIESSCORE` NBA Series Exact Score — ticker prefix KXNBA
- NBA  `KXNBAROY` NBA Rookie of the Year — ticker prefix KXNBA
- NBA  `KXNBADRAFTTOP30` NBA Draft Top 30 Pick — ticker prefix KXNBA
- skip `ZYNBAN` Zyn ban in the United States — no NBA marker
- NBA  `KXNBASTARTERS` Pro Basketball Starting Lineup — ticker prefix KXNBA
- NBA  `KXESPYNBA` BEST NBA PLAYER‬ — title mentions NBA
- skip `KXRECORDNBABEST` Best Pro Basketball Record — no NBA marker
- NBA  `KXNBAEXEC` NBA Executive of the Year — ticker prefix KXNBA
- skip `KXNCAAMBMAMER` Mid-American Conference Tournament — no NBA marker
- skip `KXAMAFFRNBA` Favorite Female R&B Artist — no NBA marker
- NBA  `KXNBAPLAYERSPECIALS` Pro Basketball Player Specials — ticker prefix KXNBA
- NBA  `KXNBADPOTM` NBA Defensive Player of the Month — ticker prefix KXNBA
- skip `KXWNBAROTY` Pro Women's Basketball Rookie of the Year — non-NBA basketball marker 'WNBA'
- skip `KXWSESBLGAME` Women's Sweden SBL Game — no NBA marker
- skip `KXNCAAMB2HTOTAL` Men's College Basketball 2nd Half Total — no NBA marker
- NBA  `KXNBA1QSPREAD` NBA 1st Quarter Spread — ticker prefix KXNBA
- NBA  `KXNBA3PEAT` Pro Basketball Three-Peat Champion — ticker prefix KXNBA
- NBA  `KXNBAALLSTARS` NBA All-Stars — ticker prefix KXNBA
- skip `KXNCAAMBTOTAL` Men's College Basketball Total Points — no NBA marker
- NBA  `KXNBA2QSPREAD` NBA 2nd Quarter Spread — ticker prefix KXNBA
- skip `KXAUTBSLGAME` Austria BSL Game — no NBA marker
- NBA  `KXNBATOPPICK` Pro Basketball Draft Lottery Winner — ticker prefix KXNBA
- skip `KXNCAAMB2HSPREAD` Men's College Basketball 2nd Half Spread — no NBA marker
- NBA  `KXNBAEAST1SEED` NBA Eastern Conference 1 Seed — ticker prefix KXNBA
- NBA  `KXNBADRAFTTRADE` Pro Basketball Draft Trade — ticker prefix KXNBA
- skip `KXNCAAMBBIG10` Big Ten Conference Tournament — no NBA marker
- skip `KXNCAABBIG12` Big 12 Men's Basketball Tournament — no NBA marker
- skip `KXWNBADRAFT4` WNBA Draft 4th Pick — non-NBA basketball marker 'WNBA'
- skip `KXWNBAFINAL` Women's Pro Basketball Finals Qualifiers — non-NBA basketball marker 'WNBA'
- skip `KXNCAAMBCBC` Men's College Basketball Crown Winner — no NBA marker
- NBA  `KXNBATOP5ROTY` Top 5 NBA draft ROTY — ticker prefix KXNBA
- skip `KXWKBLGAME` Korea KBL (W) Game — no NBA marker
- skip `KXNCAAMBKENPOMTOP` Men's College Basketball KenPom Top Ratings — no NBA marker
- NBA  `KXNBAPARTNERSHIP` NBA Player Partnership Deal — ticker prefix KXNBA
- NBA  `KXNBA2HTOTAL` NBA 2nd Half Total — ticker prefix KXNBA
- NBA  `KXNBASOUTHEAST` Pro Basketball Southeast Division Winner — ticker prefix KXNBA
- skip `KXNCAAMBMOP` Men's College Basketball Most Outstanding Player — no NBA marker
- NBA  `KXNBAPLAYOFF3D` NBA Playoff Triple-Double — ticker prefix KXNBA
- skip `KXNCAAWBUNDEFEATED` Undefeated in Women's College Basketball Regular Season — no NBA marker
- skip `KXPHKLGAME` Croatia Premijer Liga Game — no NBA marker
- skip `KXWNBACCUP` WNBA Commissioner's Cup Winner — non-NBA basketball marker 'WNBA'
- NBA  `KXNBADRAFTTOP` Pro Basketball Top Draft — ticker prefix KXNBA
- skip `KXWNBAASGAME` WNBA All Star Game — non-NBA basketball marker 'WNBA'
- skip `KXSOBBALLGAME` Summer Olympics Men's Basketball Game — no NBA marker
- skip `KXEBASKETBALLGAME` eBasketball Game — no NBA marker
- skip `KXNCAAWBACC` Women's College Basketball ACC Conference Tournament Champion — no NBA marker
- skip `KXNCAAWBH` NCAA Women's Basketball Half Winners — no NBA marker
- skip `KXNCAAMBAMER` American Conference Tournament — no NBA marker
- NBA  `KXNBALASVEGAS` Las Vegas NBA team — ticker prefix KXNBA
- skip `KXBBSERIEATOTAL` Italy Serie A Total — no NBA marker
- skip `KXNCAAMBAPRANK` Men's College Basketball AP Poll — no NBA marker
- skip `KXWNBADPOY` WNBA Defensive Player of the Year — non-NBA basketball marker 'WNBA'
- skip `KXSHEINBAUMOUT` Claudia Sheinbaum out as President of Mexico? — no NBA marker
- skip `KXWNBANEXTTEAM` Women's Pro Basketball Next Team — non-NBA basketball marker 'WNBA'
- skip `KXFIBACHAMPGAME` FIBA Champions League Game — no NBA marker
- NBA  `KXNBAPOSTASREC` NBA Best Record Post-All-Star Break — ticker prefix KXNBA
- skip `KXBNXTGAME` BNXT League Game — no NBA marker
- skip `KXLNBPTOTAL` LNBP Total — no NBA marker
- NBA  `KXTEAMSINNBAEF` Teams in NBA Eastern Conference Finals — title mentions NBA
- skip `KXNCAAMBMVAL` Missouri Valley Conference Tournament — no NBA marker
- skip `KXWNBAGAME` Women's Pro Basketball Game — non-NBA basketball marker 'WNBA'
- NBA  `KXNBABLK` NBA Player Blocks — ticker prefix KXNBA
- skip `KXNCAAMB1HTOTAL` Men's College Basketball 1st Half Total — no NBA marker
- skip `KXBBINTLGAME` International Friendly Game — no NBA marker
- NBA  `KXNBA3PTALLGAMES` Pro Basketball 3-Pointers in Every Game — ticker prefix KXNBA
- NBA  `KXNBAJOINCONF` Pro Basketball Join Conference — ticker prefix KXNBA
- skip `KXNCAAMBRACE` Men's College Basketball Race to Points — no NBA marker
- NBA  `KXNBAGAMES` NBA games — ticker prefix KXNBA
- skip `KXMARMADSEEDWIN` March Madness Seed Win — no NBA marker
- NBA  `KXNBABENCHPTS` NBA Bench Points — ticker prefix KXNBA
- NBA  `KXNBA1STTEAMDEF` NBA All-Defensive 1st Team — ticker prefix KXNBA
- NBA  `KXNBA3QTOTAL` NBA 3rd Quarter Total — ticker prefix KXNBA
- skip `KXWNBADELAY` WNBA Season Delay — non-NBA basketball marker 'WNBA'
- skip `KXWNBAMENTION` WNBA Mentions — non-NBA basketball marker 'WNBA'
- skip `KXWFIBASPREAD` Women's FIBA Spread — no NBA marker
- skip `KXBSNGAME` Puerto Rico BSN Basketball Game — no NBA marker
- skip `KXLKLGAME` LKL Lithuania Game — no NBA marker
- NBA  `KXNBASEED` NBA Playoff Seed — ticker prefix KXNBA
- skip `KXWNBA1HWINNER` Women's Pro Basketball 1st Half Winner — non-NBA basketball marker 'WNBA'
- skip `KXBBL` Germany BBL Champion — no NBA marker
- skip `KXNCAAMBBOTHQUAL` Men's College Basketball Both Teams to Qualify — no NBA marker
- NBA  `KXNBASTATAVG` NBA Player Stat Average — ticker prefix KXNBA
- skip `KXNCAAWBGAME` Women's College Basketball Game — no NBA marker
- NBA  `KXNBASPORTSMANSHIP` NBA Sportsmanship Award — ticker prefix KXNBA
- skip `KXDUNKMAN` Dunkman World Championships Winner — no NBA marker
- skip `KXABATOTAL` Adriatic ABA Total — no NBA marker
- skip `KXAMAFMRNBA` Favorite Male R&B Artist — no NBA marker
- NBA  `KXNBAFINALSVIEWER` NBA finals viewership — ticker prefix KXNBA
- NBA  `KXNBASJC` NBA Social Justice Champion — ticker prefix KXNBA
- NBA  `KXNBA2NDTEAMDEF` NBA All-Defensive 2nd Team — ticker prefix KXNBA
- skip `KXSOWBBALLGAME` Summer Olympics Women's Basketball Game — no NBA marker
- NBA  `KXNBANEXTTEAMCONF` Pro Basketball Next Team Conference — ticker prefix KXNBA
- skip `KXDBBSUPERGAME` DBB Supercup Game — no NBA marker
- skip `KXRONENBAR` Ronen bar dismissed — no NBA marker
- skip `KXWNBAMVP` WNBA MVP — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAFINALSMVP` Finals MVP — ticker prefix KXNBA
- skip `KXNCAABBIG10` Big Ten Men's Basketball Tournament — no NBA marker
- NBA  `KXNBACOTM` NBA Coach of the Month — ticker prefix KXNBA
- skip `KXLEADERWNBAPTS` WNBA PPG Leader — non-NBA basketball marker 'WNBA'
- NBA  `KXNBARULE` Pro Basketball Rule — ticker prefix KXNBA
- skip `KXWNBAALLSTARS` Women's Pro Basketball All-Star Selections — non-NBA basketball marker 'WNBA'
- skip `KXNCAAMBBIGEAST` Big East Conference Tournament — no NBA marker
- NBA  `KXNBA2HSPREAD` NBA 2nd Half Spread — ticker prefix KXNBA
- NBA  `KXNBALADDERPTS` NBA Player Points Ladder — ticker prefix KXNBA
- skip `KXNCAABSEC` SEC Men's Basketball Tournament — no NBA marker
- skip `KXMARMADSEED` Men's College Basketball Tournament Seeds — no NBA marker
- skip `KXWNBAWINS` WNBA Win Totals — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAH2HTEAM3PT` NBA H2H Team Three Pointers — ticker prefix KXNBA
- NBA  `KXCOACHOUTNBADATE` NBA Coach Out Date — title mentions NBA
- skip `KXLNBPSPREAD` LNBP Spread — no NBA marker
- skip `KXWNBAROOKAS` Women's Pro Basketball Rookie to be an All-Star — non-NBA basketball marker 'WNBA'
- skip `KXWNBA3PTROUND` Women's Pro Basketball 3-Point Contest Round Qualifiers — non-NBA basketball marker 'WNBA'
- skip `KXWNBAASGMVP` WNBA All-Star Game MVP — non-NBA basketball marker 'WNBA'
- skip `KXWINSTREAKOKC` OKC Win Streak — no NBA marker
- skip `KXNCAAWBBIGEAST` Women's College Basketball Big East Conference Tournament Champion — no NBA marker
- NBA  `KXNBASERIESOT` Pro Basketball Series Overtime — ticker prefix KXNBA
- skip `KXNCAAMBMEAC` Mid-Eastern Conference Tournament — no NBA marker
- NBA  `KXNBASTAKESALE` NBA Team Ownership Stake Sale Agreement — ticker prefix KXNBA
- skip `KXSTEPHPARTERNSHIP` Stephen Curry Partnership — no NBA marker
- skip `KXSTEPHSHOEDEAL` Steph Curry Shoe Deal — no NBA marker
- NBA  `KXNBA1Q` NBA 1st Quarter Winner — ticker prefix KXNBA
- NBA  `KXNBACUPMVP` NBA Cup Tournament MVP — ticker prefix KXNBA
- skip `KXWNBLGAME` NBL Australia (W) Game — no NBA marker
- NBA  `KXNBADRAFTINT` Pro Basketball International Players Drafted — ticker prefix KXNBA
- skip `KXWFIBAGAME` Women's FIBA Game — no NBA marker
- skip `KXGBLGAME` GBL Basketball Game — no NBA marker
- skip `KXNCAAMB2HTEAMTOTAL` Men's College Basketball 2nd Half Team Total — no NBA marker
- skip `KXWNBACOMPETE` Women's Pro Basketball Player to Compete — non-NBA basketball marker 'WNBA'
- skip `KXWNBA2QWINNER` Women's Pro Basketball 2nd Quarter Winner — non-NBA basketball marker 'WNBA'
- skip `KXCBAGAME` Chinese Basketball Association Game  — no NBA marker
- NBA  `KXNEXTCOACHOUTNBA` Next coach out NBA — title mentions NBA
- skip `KXWDBBLGAME` Women's Bundesliga Basketball Game — no NBA marker
- NBA  `KXLEADERNBAAST` NBA APG Leader — title mentions NBA
- skip `KXBBSERIEAGAME` Italy Serie A Game — no NBA marker
- skip `KXNEXTTEAMCHRISPAUL` Next Team Chris Paul — no NBA marker
- NBA  `KXNBAPTSPROT` NBA Player Points Protected — ticker prefix KXNBA
- skip `KXWNBADRAFT2` WNBA Draft 2nd Pick — non-NBA basketball marker 'WNBA'
- skip `KXWNBA1QSPREAD` Women's Pro Basketball 1st Quarter Spread — non-NBA basketball marker 'WNBA'
- skip `KXNCAAWBBIGTEN` Women's College Basketball Big Ten Conference Tournament Champion — no NBA marker
- NBA  `KXNBA2QTEAMTOTAL` NBA 2nd Quarter Team Total — ticker prefix KXNBA
- skip `KXMWIAINTCOMINBACK` I Ain’t Comin’ Back total streams — no NBA marker
- NBA  `KXNBAREBPROT` NBA Player Rebounds Protected — ticker prefix KXNBA
- skip `KXNCAAMBCAA` Coastal Athletic Association Conference Tournament — no NBA marker
- NBA  `KXNBADRAFT10` NBA Draft Tenth Pick — ticker prefix KXNBA
- NBA  `KXNBASUMMERGAME` Pro Basketball Summer League Game — ticker prefix KXNBA
- NBA  `KXNBASERIES3PMLEADER` Pro Basketball Series 3-Pointers Made Leader — ticker prefix KXNBA
- NBA  `KXNBA2HTEAMTOTAL` NBA 2nd Half Team Total — ticker prefix KXNBA
- skip `KXAACREG` AAC Regular Season Champions — no NBA marker
- NBA  `KXNBAWINRECORD` OKC NBA Win Record — ticker prefix KXNBA
- skip `KXWNBARAISE` WNBA raise — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAASTPROT` NBA Player Assists Protected — ticker prefix KXNBA
- skip `KXNBL` Australia NBL Champion — no NBA marker
- skip `KXWENBACONATOR` Average price of a Wendy's Baconator in [month] — no NBA marker
- skip `KXWNBA6POY` WNBA Sixth Player of the Year — non-NBA basketball marker 'WNBA'
- skip `KXBDSFTCHALLENGE` Bob Does Sports Free Throw Challenge — no NBA marker
- skip `KXNCAAMBNAISMITH` Men's College Basketball Naismith — no NBA marker
- skip `KXWIBPLGAME` Women's Iceland Premier League Game — no NBA marker
- skip `KXNCAAMBACCREG` Men's College Basketball ACC Regular Season Champion — no NBA marker
- skip `KXNCAAWBCONFSTREAK` Women's College Basketball Conference Championship Streak — no NBA marker
- skip `KXNCAAMBMW` Mountain West Conference Tournament — no NBA marker
- skip `KXBDS3PT` Bob Does Sports 3pt Shootout — no NBA marker
- skip `KXNCAAMBCONFAWARD` Men's College Basketball Conference Awards — no NBA marker
- NBA  `KXNBADRAFT9` NBA Draft Ninth Pick — ticker prefix KXNBA
- skip `KXLEBRONPLAY` LeBron Next Play — no NBA marker
- skip `KXNCAAMSEC` SEC MEN'S BASKETBALL TOURNAMENT — no NBA marker
- NBA  `KXNBAPICKTRADE` Pro Basketball Pick Trade — ticker prefix KXNBA
- NBA  `KXNBASIXTH` NBA Sixth Man of the Year — ticker prefix KXNBA
- NBA  `KXCITYNBAEXPAND` Cities NBA expand — title mentions NBA
- skip `KXNZNBLGAME` New Zealand NBL Game — no NBA marker
- skip `KXBANXNUBCAT` WILL NUCAT BE UNBANNED — no NBA marker
- NBA  `KXNBASERIESPTSSPREAD` Pro Basketball Series Points Spread — ticker prefix KXNBA
- NBA  `KXNBADRAFTTOP20` NBA Draft Top 20 Pick — ticker prefix KXNBA
- NBA  `KXNBASERIESROADWIN` NBA Series 1st Road Win — ticker prefix KXNBA
- NBA  `KXNBAPTS` NBA Player Points — ticker prefix KXNBA
- NBA  `KXNBA2HWINNER` Pro Basketball 2nd Half Winner — ticker prefix KXNBA
- NBA  `KXNBARELOCATION` Pro Basketball Team Relocation — ticker prefix KXNBA
- skip `KXWNBALAWSUIT` Women's Pro Basketball Lawsuit — non-NBA basketball marker 'WNBA'
- NBA  `KXNBA1HTOTAL` NBA 1st Half Total — ticker prefix KXNBA
- skip `KXNCAAMB1HWINNER` College Basketball 1H Winner — no NBA marker
- skip `KXWNBAWORSTREC` Women's Pro Basketball Worst Record — non-NBA basketball marker 'WNBA'
- NBA  `KXNBA2QTOTAL` NBA 2nd Quarter Total — ticker prefix KXNBA
- skip `KXLNBELITETOTAL` LNB Elite Total — no NBA marker
- NBA  `KXLEADERNBABLK` NBA BPG Leader — title mentions NBA
- NBA  `KXNBAROTM` NBA Rookie of the Month — ticker prefix KXNBA
- skip `KXPBAGAME` Philippines PBA Game — no NBA marker
- skip `KXNCAAMBTEAMTOTAL` Men's College Basketball Team Total — no NBA marker
- skip `KXLNBPGAME` LNBP Basketball Game — no NBA marker
- skip `KXKBLGAME` Korea KBL Game — no NBA marker
- skip `KXWNBA3PT` Women's Pro Basketball Player Threes — non-NBA basketball marker 'WNBA'
- NBA  `KXNBACUPGROUPWIN` NBA Cup Group to Win — ticker prefix KXNBA
- skip `KXNCAAWBUNDEFEATEDHOME` Women's College Basketball Teams to go Undefeated at Home — no NBA marker
- skip `KXWNBA2QTOTAL` Women's Pro Basketball 2nd Quarter Total — non-NBA basketball marker 'WNBA'
- skip `KXWMARMADSEED` Women's College Basketball Tournament Seeds — no NBA marker
- NBA  `KXNBALOTTERY` NBA Draft Lottery Picks — ticker prefix KXNBA
- NBA  `KXNBAFINALSPRICE` NBA Finals Ticket Price — ticker prefix KXNBA
- skip `KXWNBAALLDEFENSE` Women's Pro Basketball All-Defensive Teams — non-NBA basketball marker 'WNBA'
- NBA  `KXNBACOACHOUT` Pro Basketball Coaches Out — ticker prefix KXNBA
- NBA  `KXNBA1QTOTAL` NBA 1st Quarter Total — ticker prefix KXNBA
- NBA  `KXNBASTOCK` NBA Player Steals + Blocks — ticker prefix KXNBA
- skip `KXNCAAWB4Q` Women's College Basketball 4th Quarter Winner — no NBA marker
- skip `KXWNBA1H` Women's Pro Basketball 1st Half Winner — non-NBA basketball marker 'WNBA'
- skip `KXTBTGAME` TBT Hoops Game — no NBA marker
- NBA  `KXNBADRAFTTOP10` NBA Draft Top 10 Pick — ticker prefix KXNBA
- NBA  `KXNBA4Q` NBA 4th Quarter Winner — ticker prefix KXNBA
- skip `KXBSLTOTAL` Turkey BSL Total — no NBA marker
- skip `KXPLKGAME` Poland PLK Game — no NBA marker
- NBA  `KXNBANHL` NBA + NHL Champion Combo — ticker prefix KXNBA
- NBA  `KXNBASERIESREBLEADER` Pro Basketball Series Rebounds Leader — ticker prefix KXNBA
- skip `KXWNBAROY` WNBA Rookie of the Year — non-NBA basketball marker 'WNBA'
- NBA  `KXNBASPREAD` NBA Spread — ticker prefix KXNBA
- skip `KXWNBAFINALSMVP` WNBA Finals MVP — non-NBA basketball marker 'WNBA'
- skip `KXNCAAMBGAME` Men's College Basketball Game — no NBA marker
- skip `KXWNBASEMIFINAL` Women's Pro Basketball Semifinals Qualifiers — non-NBA basketball marker 'WNBA'
- NBA  `KXNBACELEBRITYGAME` Pro Basketball All-Star Celebrity Game — ticker prefix KXNBA
- NBA  `KXNBANEWCHAMPION` Pro Basketball New Champion — ticker prefix KXNBA
- skip `KXWNBAPLAYOFF` Women's Pro Basketball Playoff Qualifiers — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAHIGHESTSCORING` NBA Player with the Highest Scoring Game — ticker prefix KXNBA
- skip `KXMVECBCHAMPIONSHIP` MVE College Basketball Championship — no NBA marker
- skip `KXBBALLUSACOACH` Summer Olympics USA Men's Basketball Head Coach — no NBA marker
- NBA  `KXNBAAPOLOGY` Pro Basketball Apology — ticker prefix KXNBA
- skip `KXBNXTDGAME` BNXT Dutch League Game — no NBA marker
- NBA  `KXLEADERNBASTL` NBA SPG Leader — title mentions NBA
- NBA  `KXMVENBAMULTIGAMEEXTENDED` MVE NBA Multi Game — title mentions NBA
- NBA  `KXCOACHOUTNBA` NBA Coach Out — title mentions NBA
- skip `KXFIBACHAMPSPREAD` FIBA Champions League Spread — no NBA marker
- skip `KXNCAAWB1H` Women's College Basketball 1st Half Winner — no NBA marker
- skip `KXWNBA1QTOTAL` Women's Pro Basketball 1st Quarter Total — non-NBA basketball marker 'WNBA'
- skip `KXBBLTOTAL` Germany BBL Total — no NBA marker
- skip `KXLEADERWNBAAST` WNBA APG Leader — non-NBA basketball marker 'WNBA'
- skip `KXWEUROBASKETGAME` EuroBasket (W) Game — no NBA marker
- skip `KXNCAAWB2H` Women's College Basketball 2nd Half Winner — no NBA marker
- skip `KXARGLNBGAME` Liga Nacional de Basquetbol Game — no NBA marker
- NBA  `KXNBAFINALSVIEWERGAME7` NBA finals viewership — ticker prefix KXNBA
- skip `KXNCAAMBSECREG` Men's College Basketball SEC Regular Season Champion — no NBA marker
- skip `KXWNBA4QWINNER` Women's Pro Basketball 4th Quarter Winner — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAPTSLEADER` NBA Game Points Leader — ticker prefix KXNBA
- skip `KXWNBAOT` Women's Pro Basketball Overtime — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAFINALSMENTION` NBA Finals — ticker prefix KXNBA
- skip `KXWNBAGAMESPLAYED` WNBA Games Played in a Season — non-NBA basketball marker 'WNBA'
- skip `KXSECREG` SEC Regular Season Champions — no NBA marker
- skip `KXSBLSPREAD` Slovakia SBL Spread — no NBA marker
- NBA  `KXNBAH2HWINS` NBA Head to Head Win Total — ticker prefix KXNBA
- NBA  `KXNBADRAFTTEAM` Pro Basketball Team to Draft — ticker prefix KXNBA
- skip `KXLBJRETIRE` LBJ Retire — no NBA marker
- skip `KXSPBGAME` Venezuela Superliga Game — no NBA marker
- NBA  `KXNBAMATCHUP` NBA Matchup — ticker prefix KXNBA
- NBA  `KXNBAFIRSTBASKET` Pro Basketball First Basket — ticker prefix KXNBA
- skip `KXNCAAMBACCQUAL` Men's College Basketball ACC Championship Qualifiers — no NBA marker
- skip `KXNCAAMBFIRST3PT` Men's College Basketball First Team to Make a Three — no NBA marker
- skip `KXEUROCUPSPREAD` EuroCup Basketball Spread — no NBA marker
- skip `KXCEBLGAME` Canadian Elite Basketball League Game — no NBA marker
- skip `KXMARMADUPSET` March Madness Upsets — no NBA marker
- NBA  `KXNBAPLAYOFF` Pro Basketball Playoff Qualifier — ticker prefix KXNBA
- skip `KXKRAKENBANKPUBLIC` Kraken IPO — no NBA marker
- skip `KXKBLSPREAD` Korea KBL Spread — no NBA marker
- skip `KXMARMADREGION` March Madness Region Winner — no NBA marker
- skip `KXWNBADRAFTTOP3` WNBA Draft Top 3 — non-NBA basketball marker 'WNBA'
- skip `KXBIG12REG` Big 12 Regular Season Champions — no NBA marker
- NBA  `KXNBA1HTEAMTOTAL` NBA 1st Half Team Total — ticker prefix KXNBA
- skip `KXWNBAMIMP` WNBA Most Improved Player of the Year — non-NBA basketball marker 'WNBA'
- skip `KXVTBTOTAL` Russia VTB United Total — no NBA marker
- skip `KXMARMADHIGHSEED` March Madness Highest Seed to Reach Round — no NBA marker
- skip `KXESPYWNBA` BEST WNBA PLAYER‬‭ — non-NBA basketball marker 'WNBA'
- skip `KXMARMAD` Men's College Basketball Tournament Champion — no NBA marker
- skip `KXWNBAH2HPRA` Women's Pro Basketball Head to Head Pts + Reb + Ast — non-NBA basketball marker 'WNBA'
- skip `KXNBLTOTAL` Australia NBL Total — no NBA marker
- skip `KXNCAAWBMOP` Women's College Basketball Most Outstanding Player — no NBA marker
- skip `KXNCAAMBAE` American East Conference Tournament — no NBA marker
- skip `KXNCAAMBHOR` Horizon League Conference Tournament — no NBA marker
- skip `KXWNBATOTAL` Women's Pro Basketball Total — non-NBA basketball marker 'WNBA'
- skip `KXWNBADRAFT3` WNBA Draft 3rd Pick — non-NBA basketball marker 'WNBA'
- skip `KXNCAAMB1HTEAMTOTAL` Men's College Basketball 1st Half Team Total — no NBA marker
- NBA  `KXNBAREB` NBA Player Rebounds — ticker prefix KXNBA
- NBA  `KXNBASTL` NBA Player Steals — ticker prefix KXNBA
- skip `KXNCAAMBBSKY` Big Sky Conference Tournament — no NBA marker
- skip `KXWNBAWEST` Women's Pro Basketball Western Conference Champion — non-NBA basketball marker 'WNBA'
- skip `KXWMARMADROUND` Reach March Madness Round — no NBA marker
- skip `KXNCAAMBIVY` Ivy League Conference Tournament — no NBA marker
- skip `KXNCAAMBUSA` Conference USA Conference Tournament — no NBA marker
- NBA  `KXNBAMVP` NBA MVP — ticker prefix KXNBA
- skip `KXNCAAMBBIGEASTREG` Men's College Basketball Big East Regular Season Champion — no NBA marker
- skip `KXBSOUTOURNAMENT` Big South Tournament — no NBA marker
- NBA  `KXNBASLAMDUNK` NBA Slam Dunk Contest Winner — ticker prefix KXNBA
- NBA  `KXNBAATTEND` Who will attend the NBA game? — ticker prefix KXNBA
- skip `KXNCAAMBBSOU` Big South Conference Tournament — no NBA marker
- skip `KXNCAAWBTEAMTOTAL` Women's College Basketball Team Total — no NBA marker
- NBA  `KXNBAPLAYOFFPTS` NBA Playoffs Player Points — ticker prefix KXNBA
- skip `KXBRIANBAUMGARTNER` How many receipts will Brian Baumgartner process in 8 hours? — no NBA marker
- NBA  `KXNBAALLSTARMVP` NBA All-Star Game MVP — ticker prefix KXNBA
- skip `KXEBBALLGAME` eBasketball Game — no NBA marker
- skip `KXWNBA` WNBA Championship — non-NBA basketball marker 'WNBA'
- NBA  `KXNBADRAFT4` NBA Draft Fourth Pick — ticker prefix KXNBA
- NBA  `KXNBAPREPACK3ML` 3ML Basketball Combo — ticker prefix KXNBA
- NBA  `KXNBAMOSTWINS` Pro Basketball Highest Win Total — ticker prefix KXNBA
- skip `KXBIHD1GAME` Bosnia Division I Game — no NBA marker
- NBA  `KXLEADERNBA3PT` NBA 3PG Leader — title mentions NBA
- skip `KXWNBA2HSPREAD` Women's Pro Basketball 2nd Half Spread — non-NBA basketball marker 'WNBA'
- skip `KXNCAAWB` Women's March Madness Champion — no NBA marker
- NBA  `KXNBAALLSTARGAME` NBA All-Star Game Winner — ticker prefix KXNBA
- skip `KXLNBELITESPREAD` LNB Elite Spread — no NBA marker
- skip `KXEUROLEAGUESPREAD` EuroLeague Spread — no NBA marker
- NBA  `KXNBA2QWINNER` NBA 2nd Quarter Winner — ticker prefix KXNBA
- skip `KXMARMADPTS` Men's March Madness Points — no NBA marker
- NBA  `KXNBACELEBRITY3PT` NBA Celebrity 3PT Contest — ticker prefix KXNBA
- NBA  `KXNBA1QWINNER` NBA 1st Quarter Winner — ticker prefix KXNBA
- skip `KXNCAAWB3QSPREAD` Women's College Basketball 3rd Quarter Spread — no NBA marker
- NBA  `KXNBAH2H3PT` NBA Head-to-Head Three Pointers — ticker prefix KXNBA
- skip `KXNCAAMBSGP` College Basketball Same Game Parlay — no NBA marker
- skip `KXWNBA4QSPREAD` Women's Pro Basketball 4th Quarter Spread — non-NBA basketball marker 'WNBA'
- skip `KXGRAMBRNBA` Best R&B Album — no NBA marker
- NBA  `KXNBAROOKIE1STTEAM` NBA All-Rookie 1st Team — ticker prefix KXNBA
- NBA  `KXNBACLUTCH` NBA Clutch Player of the Year — ticker prefix KXNBA
- NBA  `KXNBASUMMER1HWINNER` Pro Basketball Summer League 1st Half Winner — ticker prefix KXNBA
- skip `KXNCAAWBTOTAL` Women's College Basketball Total Points — no NBA marker
- skip `KXWNBASERIES` WNBA Playoff Series Winner — non-NBA basketball marker 'WNBA'
- skip `KXNCAAWB1HTEAMTOTAL` Women's College Basketball 1st Half Team Total — no NBA marker
- skip `KXNCAAMBSBELT` Sun Belt Conference Tournament — no NBA marker
- NBA  `KXFIRSTPICKNBA` NBA first pick — title mentions NBA
- NBA  `KXNBA4QTEAMTOTAL` NBA 4th Quarter Team Total — ticker prefix KXNBA
- skip `KXBBSERIEASPREAD` Italy Serie A Spread — no NBA marker
- skip `KXWNBADRAFT1` WNBA Draft 1st Pick — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAHUSTLE` NBA Hustle Award — ticker prefix KXNBA
- skip `KXLKLSPREAD` LKL Lithuania Spread — no NBA marker
- NBA  `KXNBANORTHWEST` Pro Basketball Northwest Division Winner — ticker prefix KXNBA
- skip `KXWFIBATOTAL` Women's FIBA Total — no NBA marker
- skip `KXVTBGAME` Russia VTB United Game — no NBA marker
- NBA  `KXNBAFIRSTOPPONENT` Pro Basketball First Opponent of the Season — ticker prefix KXNBA
- skip `KXABA` Adriatic ABA Champion — no NBA marker
- skip `KXSPORTSOWNERLBJ` LBJ owning team — no NBA marker
- skip `KXBSLSPREAD` Turkey BSL Spread — no NBA marker
- skip `KXWNBAAST` Women's Pro Basketball Player Assists — non-NBA basketball marker 'WNBA'
- skip `KXNCAAWB2HTOTAL` Women's College Basketball 2nd Half Total — no NBA marker
- skip `KXNCAAMBWAC` Western Athletic Conference Tournament — no NBA marker
- skip `KXWNBAWEST1` Women's Pro Basketball Western Conference #1 Seed — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAPRA` NBA Player Points + Rebounds + Assists — ticker prefix KXNBA
- skip `KXKORISLIIGAGAME` Finland Korisliiga Game — no NBA marker
- NBA  `KXNBALADDER3PT` NBA Player Threes Ladder — ticker prefix KXNBA
- NBA  `KXNBAEFINMVP` NBA Eastern Conference Finals MVP — ticker prefix KXNBA
- skip `KXNCAAMBD3GAME` Men's College Basketball D3 Game — no NBA marker
- NBA  `KXNBADRAFT5` NBA Draft Fifth Pick — ticker prefix KXNBA
- skip `KXBILBASKETBALL` Ball is Life Basketball Game — no NBA marker
- skip `KXWNBA2HTOTAL` Women's Pro Basketball 2nd Half Total — non-NBA basketball marker 'WNBA'
- skip `KXNCAAMIVYLEAGUE` Ivy League MEN'S BASKETBALL TOURNAMENT — no NBA marker
- skip `KXNEXTTEAMLEBRON` Lebron's Next Team — no NBA marker
- skip `KXBBWSERIEAGAME` Italy Serie A (W) Game — no NBA marker
- skip `KXNCAAMBBIG10REGTOP` Men's College Basketball Big Ten Regular Season Top Finishers — no NBA marker
- NBA  `KXNEXTNBACOACH` Who is the Next NBA Coach of Team — title mentions NBA
- NBA  `KXNBA3QTEAMTOTAL` NBA 3rd Quarter Team Total — ticker prefix KXNBA
- NBA  `KXNBADRAFTCONF` Pro Basketball Players Drafted by Conference — ticker prefix KXNBA
- NBA  `KXNBAASSTARTERS` NBA All-Star Starters — ticker prefix KXNBA
- skip `KXNCAAMBWINS` Men's College Basketball Win Totals — no NBA marker
- NBA  `KXNBAPOTM` NBA Player of the Month — ticker prefix KXNBA
- skip `KXUNRIVALEDGAME` Unrivaled Basketball Game — no NBA marker
- skip `KXCOINA` Coinbase Annual KPI — no NBA marker
- skip `KXACCREG` ACC Regular Season Champions — no NBA marker
- skip `KXSTEPHDEAL` Steph Curry Endorsement Deal — no NBA marker
- NBA  `KXNBAECFQUAL` NBA Eastern Conference Finals Qualifiers — ticker prefix KXNBA
- skip `KXWNBAPTSRECORD` Women's Pro Basketball Single-Game Scoring Record — non-NBA basketball marker 'WNBA'
- NBA  `KXPLAYEROPTIONNBA` player option nba — title mentions NBA
- skip `KXSOWBBALLSPREAD` Summer Olympics Women's Basketball Spread — no NBA marker
- skip `KXMARMADSEEDROUND` March Madness Seed Round — no NBA marker
- skip `KXALBUMRELEASENBAYB` WILL YOUNGBOY RELEASE ANOTHER ALBUM THIS YEAR? — no NBA marker
- NBA  `KXNBA1STTEAM` All-NBA 1st Team — ticker prefix KXNBA
- NBA  `KXNBASEEDOU` NBA Playoff Seed Over/Unders — ticker prefix KXNBA
- NBA  `KXNBACUPQUAL` Pro Basketball Cup Qualifiers — ticker prefix KXNBA
- skip `KXWNBADRAFTTOP5` WNBA Draft Top 5 — non-NBA basketball marker 'WNBA'
- skip `KXNCAAMBKENPOMRANK` Men's College Basketball KenPom Ratings — no NBA marker
- skip `KXBBLSPREAD` Germany BBL Spread — no NBA marker
- NBA  `KXNBADRAFT8` NBA Draft Eighth Pick — ticker prefix KXNBA
- skip `KXTATUMRETURN` When Will Jayson Tatum Play His Next Game — no NBA marker
- skip `KXNCAABGAME` College Basketball Game — no NBA marker
- skip `KXSOWBBALLTOTAL` Summer Olympics Women's Basketball Total — no NBA marker
- skip `KXNCAAWB1QSPREAD` Women's College Basketball 1st Quarter Spread — no NBA marker
- skip `KXA10REG` A10 Regular Season Champions — no NBA marker
- NBA  `KXNBASERIESGCOMEBACK` Pro Basketball Series Game Comeback — ticker prefix KXNBA
- skip `KXNBLSPREAD` Australia NBL Spread — no NBA marker
- NBA  `KXNBAGAMEHIGHSCORE` NBA Highest Scoring Game of the Season — ticker prefix KXNBA
- NBA  `KXNBASERIESTOTALPTS` Pro Basketball Series Total Points — ticker prefix KXNBA
- NBA  `KXNBATEAM` NBA team — ticker prefix KXNBA
- skip `KXKNUEPPEL3PTREC` Kon Knueppel Rookie 3pt Record — no NBA marker
- skip `KXBBSERIEBGAME` Italy Serie B Basketball Game — no NBA marker
- skip `KXLNBP` Mexico LNBP Champion — no NBA marker
- skip `KXFIBATOTAL` FIBA Total — no NBA marker
- skip `KXCOVEREA` Cover EA college sports — no NBA marker
- NBA  `KXNBATOP3` Pro Basketball Draft Lottery Top 3 — ticker prefix KXNBA
- NBA  `KXNBASERIESSPREAD` NBA Series Game Spread — ticker prefix KXNBA
- NBA  `KXNBAMVPDPOY` Pro Basketball Player to Win MVP and DPOY — ticker prefix KXNBA
- skip `KXWNBAMATCHUP` WNBA Finals Matchup — non-NBA basketball marker 'WNBA'
- skip `KXFIBAGAME` FIBA Game — no NBA marker
- NBA  `KXNBA3D` NBA Player Triple Double — ticker prefix KXNBA
- skip `KXKBLTOTAL` Korea KBL Total — no NBA marker
- skip `KXFIBAECUPGAME` FIBA Europe Cup Game — no NBA marker
- skip `KXNCAAMBOV` Ohio Valley Conference Tournament — no NBA marker
- NBA  `KXNBA4QWINNER` NBA 4th Quarter Winner — ticker prefix KXNBA
- skip `KXNCAAMBCOTY` Men's College Basketball Naismith Coach of the Year — no NBA marker
- skip `KXWNBA2HWINNER` Women's Pro Basketball 2nd Half Winner — non-NBA basketball marker 'WNBA'
- NBA  `KXNBASUMMERPTS` Pro Basketball Summer Player Points — ticker prefix KXNBA
- skip `KXWMARMAD1SEED` Women's March Madness 1 Seeds — no NBA marker
- skip `KXNCAAMBSPREAD` Men's College Basketball Spread — no NBA marker
- NBA  `KXNBAPIADVANCE` NBA Play-In Team to Advance — ticker prefix KXNBA
- skip `KXNCAAMBBIG12QUAL` Men's College Basketball Big 12 Championship Qualifiers — no NBA marker
- NBA  `KXNBACUP1STTEAM` NBA Cup All-Tournament Team — ticker prefix KXNBA
- skip `KXNCAAMBBIGTENREG` Men's College Basketball Big Ten Regular Season Champion — no NBA marker
- skip `KXDBBGAME` Deutscher Basketball Bund (DBB) Game — no NBA marker
- skip `KXMARMADCONF` March Madness Conference — no NBA marker
- skip `KXPLEAGUEGAME` Taiwan P. League+ — no NBA marker
- NBA  `KXNBADRAFTTOP25` NBA Draft Top 25 Pick — ticker prefix KXNBA
- skip `KXNCAAMBAPANY` Men's College Basketball AP Rank Anytime in Season — no NBA marker
- skip `KXNCAAWB2HTEAMTOTAL` Women's College Basketball 2nd Half Team Total — no NBA marker
- NBA  `KXNBAESCALATOR3PT` NBA Player Threes Escalator — ticker prefix KXNBA
- skip `KXWNBAEAST` Women's Pro Basketball Eastern Conference Champion — non-NBA basketball marker 'WNBA'
- NBA  `KXNBALOTTERYODDS` NBA Lottery Winner Odds — ticker prefix KXNBA
- skip `KXZYNBAN` Zyn ban in the United States — no NBA marker
- skip `KXNCAAWBRACE` Women's College Basketball Race to Points — no NBA marker
- skip `KXWNBACOY` WNBA Coach of the Year — non-NBA basketball marker 'WNBA'
- skip `KXLKLTOTAL` LKL Lithuania Total — no NBA marker
- NBA  `KXNBANEXTGOVERNOR` Pro Basketball Next Governor — ticker prefix KXNBA
- skip `KXEUROLEAGUETOTAL` EuroLeague Total — no NBA marker
- skip `KXNCAAMBTOPAPRANK` Men's College Basketball AP Poll Top Rank — no NBA marker
- skip `KXCZENBLGAME` Czech NBL Game — no NBA marker
- skip `KXWNBAPLAYOFFHOST` Women's Pro Basketball Playoff Home Games — non-NBA basketball marker 'WNBA'
- skip `KXSONICS` Blazers become Sonics — no NBA marker
- skip `KXFIBAECUPTOTAL` FIBA Europe Cup Total — no NBA marker
- skip `KXBDS3PTOU` Bob Does Sports Made 3-Pointers — no NBA marker
- skip `KXWNBASPREAD` Women's Pro Basketball Spread — non-NBA basketball marker 'WNBA'
- skip `KXWNBANEXTCOMMISH` Women's Pro Basketball Next Commissioner — non-NBA basketball marker 'WNBA'
- NBA  `KXNEXTTEAMNBA` Next NBA Team — title mentions NBA
- NBA  `KXNBAMIMP` NBA Most Improved Player — ticker prefix KXNBA
- skip `KXEUROCUPGAME` EuroCup Basketball Game — no NBA marker
- skip `KXNCAAMBBIGTENQUAL` Men's College Basketball Big Ten Championship Qualifiers — no NBA marker
- skip `KXNCAAMBTEAMSQUAL` Men's College Basketball Teams to Qualify — no NBA marker
- skip `KXBBSERIEA2GAME` Italy Serie A2 Game — no NBA marker
- skip `KXSHAI20PTREC` Shai 20+ Point Streak — no NBA marker
- NBA  `KXNBAPLAYERDEAL` Next Pro Basketball Brand Deal — ticker prefix KXNBA
- skip `KXQUADRUPLEDOUBLE` Quadruple Double — no NBA marker
- NBA  `KXNBASUMMERMVP` Pro Basketball Summer League MVP — ticker prefix KXNBA
- NBA  `KXNBA3QWINNER` NBA 3rd Quarter Winner — ticker prefix KXNBA
- skip `KXTNCBASKETBALL` TNC Basketball — no NBA marker
- NBA  `KXNBAGAMESPECIALS` Pro Basketball Game Specials — ticker prefix KXNBA
- skip `KXNBBGAME` Brazil NBB Basketball Game — no NBA marker
- skip `KXLBPGAME` Colombia LBP Basketball Game — no NBA marker
- skip `KXEARNINGSMENTIONBA` Boeing Earnings Call — no NBA marker
- NBA  `KXNBADRAFTMATCHUP` Pro Basketball Draft Matchup — ticker prefix KXNBA
- skip `KXNCAAMBSOCON` Southern Conference Tournament — no NBA marker
- skip `KXWNBATEAMTOTAL` WNBA Team Totals — non-NBA basketball marker 'WNBA'
- skip `KXJBLEAGUEGAME` Japan B League Game — no NBA marker
- skip `KXWSBLGAME` Sweden SBL Game — no NBA marker
- NBA  `KXNBACONF` NBA Conference to Win the Championship — ticker prefix KXNBA
- skip `KXNCAAWB1Q` Women's College Basketball 1st Quarter Winner — no NBA marker
- NBA  `KXNBACENTRAL` Pro Basketball Central Division Winner — ticker prefix KXNBA
- skip `KXNCAAMB1H` Men's College Basketball 1st Half Winner — no NBA marker
- NBA  `KXNBAOT` NBA Overtime — ticker prefix KXNBA
- NBA  `KXNFLNBA` NFL and NBA Champion Combo — title mentions NBA
- NBA  `KXNBADRAFTTOP5` NBA Draft Top 5 Pick — ticker prefix KXNBA
- NBA  `KXNBADPOY` NBA Defensive Player of the Year — ticker prefix KXNBA
- NBA  `KXNBAH2HPRA` NBA Head-to-Head Points, Rebounds and Assists — ticker prefix KXNBA
- skip `KXNCAAMBIG12` Big 12 MEN'S BASKETBALL TOURNAMENT — no NBA marker
- skip `KXNCAAWB2HSPREAD` Women's College Basketball 2nd Half Spread — no NBA marker
- NBA  `KXNBADRAFT6` NBA Draft Sixth Pick — ticker prefix KXNBA
- skip `KXWNBA40PTS` Women's Pro Basketball Player to Score 40 Points — non-NBA basketball marker 'WNBA'
- skip `KXNCAAWB1QTOTAL` Women's College Basketball 1st Quarter Total — no NBA marker
- NBA  `KXNBAWCFQUAL` NBA Western Conference Finals Qualifiers — ticker prefix KXNBA
- skip `KXWNBAALLROOKIE` Women's Pro Basketball All-Rookie Team — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAWFINMVP` NBA Western Conference Finals MVP — ticker prefix KXNBA
- NBA  `KXNBAFRANCHISECOST` NBA Franchise Cost — ticker prefix KXNBA
- NBA  `KXNBADRAFTCAT` Pro Basketball Draft Category — ticker prefix KXNBA
- NBA  `KXNBAONE3PT` NBA Players to Make One Three — ticker prefix KXNBA
- skip `KXNCAAMBBIGTENREGTOP` Men's College Basketball Big Ten Regular Season Top Finishers — no NBA marker
- skip `KXNCAAWBAWARD` Women's College Basketball Awards — no NBA marker
- NBA  `KXNBA1QTEAMTOTAL` NBA 1st Quarter Team Total — ticker prefix KXNBA
- skip `KXWNBA2H` Women's Pro Basketball 2nd Half Winner — non-NBA basketball marker 'WNBA'
- skip `KXBIGEASTREG` Big East Regular Season Champions — no NBA marker
- skip `KXWNBA7FIGS` 7 Figure WNBA salary — non-NBA basketball marker 'WNBA'
- skip `KXNCAAMBPAT` Patriot League Conference Tournament — no NBA marker
- NBA  `KXKXSPOTIFYALBUMRELEASEDATESC` WILL NBA YOUNBOY RELEASE SLIME CRY  — title mentions NBA
- NBA  `KXNBATEAMMATE` NBA Teammate of the Year — ticker prefix KXNBA
- NBA  `KXNBACOY` NBA Coach of the Year — ticker prefix KXNBA
- skip `KXBBALLTEAMUSA` Summer Olympics USA Men's Basketball Team — no NBA marker
- NBA  `KXTOP3NBADRAFT` NBA Draft Top 3 — title mentions NBA
- skip `KXKMLGAME` Estonia KML Game — no NBA marker
- skip `KXLNBELITE2GAME` LNB Elite 2 Game — no NBA marker
- skip `KXACBTOTAL` Spain Liga ACB Total — no NBA marker
- skip `KXWEUROLEAGUEGAME` EuroLeague (W) Game — no NBA marker
- skip `KXNCAAMBWINMARGIN` Men's College Basketball Winning Margin — no NBA marker
- skip `KXSLBTOTAL` England Super League Basketball Total — no NBA marker
- skip `KXNCAAMBACCREGTOP` Men's College Basketball ACC Regular Season Top Finishers — no NBA marker
- skip `KXNCAAMB2ML` College Basketball 2-Moneyline Combo — no NBA marker
- skip `KXBIG10REG` Big Ten Regular Season Champions — no NBA marker
- NBA  `KXNBASUMMERTOTAL` Pro Basketball Summer League Total — ticker prefix KXNBA
- skip `KXABASPREAD` Adriatic ABA Spread — no NBA marker
- skip `KXNCAAMBUNDEFEATEDHOME` Men's College Basketball Teams to go Undefeated at Home — no NBA marker
- skip `KXNCAAMBNIT` Men's NIT Tournament Champion — no NBA marker
- skip `KXEUROCUPTOTAL` EuroCup Basketball Total — no NBA marker
- NBA  `KXNBA3RDTEAM` All-NBA 3rd Team — ticker prefix KXNBA
- skip `KXNCAAMBFIRST10` Men's College Basketball Race to 10 Points — no NBA marker
- NBA  `KXNBA2NDTEAM` All-NBA 2nd Team — ticker prefix KXNBA
- NBA  `KXNBASTOCKS` NBA Player Steals and Blocks — ticker prefix KXNBA
- skip `KXEUROBASKETSPREAD` EuroBasket Spread — no NBA marker
- NBA  `KXNBA3PTCONTEST` NBA 3-Point Contest Winner — ticker prefix KXNBA
- skip `KXSLBGAME` England Super League Basketball Game — no NBA marker
- NBA  `KXNBAWINS` Pro Basketball Win Totals — ticker prefix KXNBA
- skip `KXNCAAMBCONF` NCAAMB Conference to Win Championship  — no NBA marker
- skip `KXDBBFGAME` Denmark Basketligaen Game — no NBA marker
- NBA  `KXLEADERNBAPTS` NBA PPG Leader — title mentions NBA
- skip `KXNCAAWB3QTOTAL` Women's College Basketball 3rd Quarter Total — no NBA marker
- skip `KXNCAAMB2H` Men's College Basketball 2nd Half Winner — no NBA marker
- skip `KXNCAAMBHTEAMTOTAL` Mens College Basketball 1st Half Team Total — no NBA marker
- skip `KXNCAAMBWCC` West Coast Conference Tournament — no NBA marker
- NBA  `KXNBA1HWINNER` Pro Baskeball 1st Half Winner — ticker prefix KXNBA
- NBA  `KXNBAHALLOFFAME` Pro Basketball Hall of Fame — ticker prefix KXNBA
- skip `KXWNBASERIESSPREAD` WNBA Series Game Spread — non-NBA basketball marker 'WNBA'
- skip `KXABNBA` Airbnb Annual KPI — no NBA marker
- skip `KXABAGAME` Adriatic ABA Game — no NBA marker
- skip `KXSESBLGAME` Sweden SBL Game — no NBA marker
- skip `KXNCAAMPAC12` PAC-12 MEN'S BASKETBALL TOURNAMENT — no NBA marker
- skip `KXFIBASPREAD` FIBA Spread — no NBA marker
- NBA  `KXNBAPLAYTOGETHER` Pro Basketball Players to Play Together — ticker prefix KXNBA
- skip `KXNCAABMENTION` College Basketball — no NBA marker
- skip `KXNCAAMBBIG10REG` Men's College Basketball Big Ten Regular Season Champion — no NBA marker
- NBA  `KXNBARETIRE` NBA Retirement — ticker prefix KXNBA
- NBA  `KXNBA2KCOVER` Who will be on the cover of NBA 2k? — ticker prefix KXNBA
- skip `KXCAATOURNAMENT` CAA Tournament — no NBA marker
- NBA  `KXNBACOMPETE` Pro Basketball Player to Compete — ticker prefix KXNBA
- NBA  `KXNBAAWARDFIN` NBA Award Finalists — ticker prefix KXNBA
- skip `KXNCAAMBPAC12` Pac-12 Conference Tournament — no NBA marker
- skip `CBVOLUME` Coinbase volume — no NBA marker
- NBA  `KXNBAUPSET` NBA Number of Upsets per Round — ticker prefix KXNBA
- skip `KXNCAAWBWBIT` WBIT Winner — no NBA marker
- skip `KXFIBACHAMPTOTAL` FIBA Champions League Total — no NBA marker
- skip `KXWNBA1HTOTAL` WNBA 1st Half Total — non-NBA basketball marker 'WNBA'
- skip `KXACQUIRECOINBASE` Will Coinbase announce another acquisition in 2025? — no NBA marker
- skip `KXJCOLECBA` J Cole CBA — no NBA marker
- skip `KXPLAYTOGETHERJBJT` Tatum and Brown Celtics — no NBA marker
- skip `KXNCAAMBBIG12REGTOP` Men's College Basketball Big 12 Regular Season Top Finishers — no NBA marker
- skip `KXWNBASERIESGAMES` WNBA Series Total Games — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAFTM` NBA Player Free Throws Made — ticker prefix KXNBA
- skip `KXNCAAMBBWEST` Big West Conference Tournament — no NBA marker
- skip `KXVTB` Russia VTB United Champion — no NBA marker
- skip `KXWNBA3QTOTAL` Women's Pro Basketball 3rd Quarter Total — non-NBA basketball marker 'WNBA'
- skip `KXNCAABBIGTEN` Big Ten Men's Basketball Tournament — no NBA marker
- skip `KXNCAABIVY` Ivy League Men's Basketball Tournament — no NBA marker
- skip `KXBILGAME` Ball is Life Basketball Game — no NBA marker
- NBA  `KXNBAFRANCHISEOWNER` NBA Franchise Owner — ticker prefix KXNBA
- skip `KXNCAAWBSTATLEADER` Women's College Basketball Stat Leader — no NBA marker
- skip `KXNCAAWBSPREAD` Women's College Basketball Spread — no NBA marker
- skip `KXWNBA1SEED` Women's Pro Basketball #1 Seed — non-NBA basketball marker 'WNBA'
- skip `KXNCAAWBWINS` Women's College Basketball Win Totals — no NBA marker
- skip `KXWNBA4QTOTAL` Women's Pro Basketball 4th Quarter Total — non-NBA basketball marker 'WNBA'
- NBA  `KXALBUMRELEASEDATENBAYOUNGBOY` Will NBA Youngboy release a new album? — title mentions NBA
- NBA  `KXLEADERNBAREB` NBA RPG Leader — title mentions NBA
- NBA  `KXNBARISINGSTARS` Pro Basketball Rising Stars Tournament — ticker prefix KXNBA
- skip `KXACBGAME` Spain Liga ACB Game — no NBA marker
- NBA  `KXNBAPR` Pro Basketball Player Points + Rebounds — ticker prefix KXNBA
- skip `KXNCAAMBSEC` SEC Conference Tournament — no NBA marker
- skip `KXCBATOTAL` Chinese Basketball Association Total  — no NBA marker
- NBA  `KXNBADRAFTPICK` Pro Basketball Draft Pick — ticker prefix KXNBA
- skip `KXNCAAMBAWARD` Men's College Basketball Awards — no NBA marker
- skip `KXEUROBASKETTOTAL` EuroBasket Total — no NBA marker
- skip `KXISLSPREAD` Israel Super League Spread — no NBA marker
- NBA  `KXNBASTADIUM` NBA Stadium Completion — ticker prefix KXNBA
- NBA  `KXNBATEAMSALE` Pro Basketball Team to be Sold — ticker prefix KXNBA
- NBA  `KXNBAH2HBENCHPTS` NBA Head-to-Head Bench Points — ticker prefix KXNBA
- skip `KXNCAAMBFIRST25` Men's College Basketball Race to 25 Points — no NBA marker
- skip `KXNCAAMBIGTEN` big ten MEN'S BASKETBALL TOURNAMENT — no NBA marker
- skip `KXWNBAFIRSTTEAM` Women's Pro Basketball First Team — non-NBA basketball marker 'WNBA'
- skip `KXWNBAALLTEAM` Women's Pro Basketball Teams — non-NBA basketball marker 'WNBA'
- skip `KXISLGAME` Israel Super League Game — no NBA marker
- skip `KXNCAAMBSUN` Atlantic Sun Conference Tournament — no NBA marker
- NBA  `KXNBASWEEP` NBA Teams to Have a Series Sweep — ticker prefix KXNBA
- NBA  `KXNBAPACIFIC` Pro Basketball Pacific Division Winner — ticker prefix KXNBA
- skip `KXBSLGAME` Turkey BSL Game — no NBA marker
- skip `KXNCAAMBSECREGTOP` Men's College Basketball SEC Regular Season Top Finishers — no NBA marker
- skip `KXCOINBASE` Coinbase KPI — no NBA marker
- NBA  `KXTEAMSINNBAF` Teams in NBA Finals — title mentions NBA
- NBA  `KXNBAPLAYIN` Which Team Will Make the Play-In Tournament — ticker prefix KXNBA
- skip `KXBALGAME` Basketball Africa League Game — no NBA marker
- skip `KXFBUGAME` Ukraine SuperLeague Game — no NBA marker
- NBA  `KXNBAPREPACK2ML` 2 ML Basketball Combo — ticker prefix KXNBA
- NBA  `KXNBATRADE` Pro Basketball Trade — ticker prefix KXNBA
- skip `KXNCAAMBASUN` Atlantic Sun Conference Tournament — no NBA marker
- NBA  `KXNBADRAFTTOP15` NBA Draft Top 15 Pick — ticker prefix KXNBA
- skip `KXNCAAMBTEAMMOSTPTS` College Basketball Team with the Most Points Scored — no NBA marker
- NBA  `KXNBASERIESPTSLEADER` Pro Basketball Series Points Leader — ticker prefix KXNBA
- skip `KXNCAAWB2Q` Women's College Basketball 2nd Quarter Winner — no NBA marker
- skip `KXKLSGAME` Serbia KLS Game — no NBA marker
- skip `KXCBASPREAD` Chinese Basketball Association Spread  — no NBA marker
- skip `KXEARNINGSMENTIONCOINBASE` coinbase earnings mention — no NBA marker
- NBA  `KXNBA` Pro Basketball Champion — ticker prefix KXNBA
- NBA  `KXTRUMPNBAFINALS` Trump NBA finals — title mentions NBA
- NBA  `KXNBATEAMWINSTREAK` NBA Team with the Longest Winning Streak — ticker prefix KXNBA
- skip `KXGOLDENBACHELOR` who will win the gold bachelor — no NBA marker
- skip `KXJUDGEMENTDAYGAME` Ballislife x OTD | Judgement Day 1v1 Game — no NBA marker
- skip `KXWNBACCUPMVP` WNBA Commissioner's Cup MVP — non-NBA basketball marker 'WNBA'
- NBA  `KXNBAGAME` NBA Game — ticker prefix KXNBA
- skip `KXWNBASECONDTEAM` Women's Pro Basketball Second Team — non-NBA basketball marker 'WNBA'
- NBA  `KXNBADRAFT3` NBA Draft Third Pick — ticker prefix KXNBA
- skip `KXFIBAECUPSPREAD` FIBA Europe Cup Spread — no NBA marker
- skip `KXNCAAWB2QSPREAD` Women's College Basketball 2nd Quarter Spread — no NBA marker
- NBA  `KXNBAWEST1SEED` NBA Western Conference 1 Seed — ticker prefix KXNBA
- NBA  `KXNBAFINALSOUTCOME` NBA Finals Outcome — ticker prefix KXNBA
- NBA  `KXNBA1H` NBA 1st Half Winner — ticker prefix KXNBA
- skip `KXNCAAMBBIG12` Big 12 Conference Tournament — no NBA marker
- NBA  `KXNBACITYEXPAND` NBA City Franchise Expansion — ticker prefix KXNBA
- NBA  `KXNBA3PT` NBA Player Threes — ticker prefix KXNBA
- skip `KXNCAAMBBIGEASTREGTOP` Men's College Basketball Big East Regular Season Top Finishers — no NBA marker
- skip `KXAMAFRNBA` Favorite R&B Album — no NBA marker
- NBA  `KXNBAWINMARGIN` NBA Win Margin — ticker prefix KXNBA
- skip `KXNCAAWBAPRANK` Women's College Basketball AP Poll — no NBA marker
- skip `KXACBSPREAD` Spain Liga ACB Spread — no NBA marker
- NBA  `KXNBANEXTTEAMOUTLET` Pro Basketball Outlet to Announce Next Team — ticker prefix KXNBA
- NBA  `KXNBANEXTTEAM` Pro Basketball Next Team — ticker prefix KXNBA
- NBA  `KXTEAMSINNBAWF` Teams in NBA Western Conference Finals — title mentions NBA
- skip `KXWMARMAD` March Tournament (W) — no NBA marker
- skip `KXWNBA3QWINNER` Women's Pro Basketball 3rd Quarter Winner — non-NBA basketball marker 'WNBA'
- NBA  `KXNBADRAFTOU` Pro Basketball Players Draft Position — ticker prefix KXNBA
- skip `KXNCAAMBIGEAST` Big East Men's basketball tournament — no NBA marker
- skip `KXNCAANIT` NIT Champion — no NBA marker
- skip `KXMAKEMARMAD` Make March Madness Tournament — no NBA marker
- NBA  `KXNBAGAME7` NBA Series that Go to a Game 7 — ticker prefix KXNBA
- skip `KXWNBAREB` Women's Pro Basketball Player Rebounds — non-NBA basketball marker 'WNBA'
- skip `KXNCAAMBHL` Horizon League conference tournament winner — no NBA marker
- skip `KXNCAAMBA10` Atlantic-10 Conference Tournament — no NBA marker
- NBA  `KXNBA3QSPREAD` NBA 3rd Quarter Spread — ticker prefix KXNBA
- NBA  `KXNBA3Q` NBA 3rd Quarter Winner — ticker prefix KXNBA
- skip `KXNCAAWBTOPAPRANK` Women's College Basketball AP Poll Top Rank — no NBA marker
- skip `KXWNBADUNK` Women's Pro Basketball Player to Dunk — non-NBA basketball marker 'WNBA'
