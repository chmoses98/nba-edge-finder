# T-60 strict control vs T-45 availability study (research only; descriptive; lanes are never pooled)

Retrospective reconstruction of both lanes' sealers over the games since 2026-10-20 on the final archives (uncounted, descriptive) plus two matched comparators that change one thing at a time; prospective, counted evidence is read only from each lane's own sealed ledger and is not available yet (control start 2026-10-24T06:00Z; T-45 start 2026-10-27T06:00Z, after approval).

## Coverage

| lane (source) | games | evaluated | traded | excluded by archive latency | excluded no data | share evaluated | decision instants usable |
|---|---|---|---|---|---|---|---|
| control_T60_strict (RETROSPECTIVE_RECONSTRUCTION) | 14 | 5 | 4 | 9 | 0 | 0.357 | 4 / 9 |
| t45_T45_available (RETROSPECTIVE_RECONSTRUCTION) | 14 | 14 | 9 | 0 | 0 | 1.0 | 9 / 9 |
| comparator_T60_available (RETROSPECTIVE_COMPARATOR) | 14 | 14 | 9 | 0 | 0 | 1.0 | 9 / 9 |
| comparator_T45_strict (RETROSPECTIVE_COMPARATOR) | 14 | 5 | 4 | 9 | 0 | 0.357 | 4 / 9 |

## Predicted EV, closing-line value, settled performance (retrospective rows are descriptive; counted evidence only comes from the sealed ledgers)

| lane | trades | mean predicted EV | settled | net P&L | ROI on outlay | hit rate | CLV mean (c, n valid) | board age median / p90 (s) | ask drift mean (c) |
|---|---|---|---|---|---|---|---|---|---|
| control_T60_strict | 15 | 0.1651 | 15 | 0.8000000000000003 | 0.11111111111111117 | 0.5333333333333333 | -1.0333333333333334 (15) | 724.0 / 724.0 | 0.07 |
| t45_T45_available | 36 | 0.1769 | 36 | -1.61 | -0.09692956050571944 | 0.4166666666666667 | 0.05555555555555555 (36) | 497.0 / 724.0 | 0.61 |
| comparator_T60_available | 36 | 0.1787 | 36 | 0.40000000000000036 | 0.024096385542168693 | 0.4722222222222222 | 0.9583333333333334 (36) | 557.0 / 724.0 | 1.36 |
| comparator_T45_strict | 15 | 0.171 | 15 | 0.9700000000000002 | 0.13798008534850645 | 0.5333333333333333 | -1.2666666666666666 (15) | 724.0 / 724.0 | 1.4 |

Selection overlap (control vs T-45, retrospective): {"contracts_both": 14, "control_only": 1, "t45_only": 22, "games_traded_both": 4, "games_control_only": 0, "games_t45_only": 5, "reading": "descriptive; each lane keeps its own ledger and exposure caps, so a shared contract is two separate shadow positions"}

## Projection accuracy on all eligible games (independent of trades, markets and lanes)

* eligible games with settled forecasts: 14; challenger forecasts scored: 2739
* eligible games by lane status: {"control_T60_strict": {"EXCLUDED_ARCHIVE_LATENCY": 9, "EVALUATED_NO_TRADE": 1, "TRADED": 4}, "t45_T45_available": {"TRADED": 9, "EVALUATED_NO_TRADE": 5}, "comparator_T60_available": {"TRADED": 9, "EVALUATED_NO_TRADE": 5}, "comparator_T45_strict": {"EXCLUDED_ARCHIVE_LATENCY": 9, "EVALUATED_NO_TRADE": 1, "TRADED": 4}}
* the denominator is every game with settled forecasts. TRADED, EVALUATED_NO_TRADE, EXCLUDED_* and NO_SEAL games are all scored; a trade decision, a missing board or a lane exclusion never removes a game from the accuracy evaluation

## Caveats

* a handful of games: no interval, no inference; the coverage columns are mechanics, the P&L columns are anecdotes
* the availability rule trades on a board that is on average ~8 minutes old at the decision instant (executability block); the control's board is younger but loses most games to commit latency
* T-45 differs from the control in two things (offset AND board rule); the matched comparators (T-60 available, T-45 strict) separate them
* settled P&L, CLV and drift use the final archives; none of it was available to the selection
* retrospective reconstruction runs the sealer at the first minute of each window with commit-time filters, so it reproduces what a live sealer would have written; it is still uncounted
