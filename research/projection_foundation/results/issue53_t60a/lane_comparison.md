# Strict T-60 control vs T-60 availability study (research only; descriptive; lanes are never pooled)

Retrospective reconstruction of the control and of the PRIMARY T-60 availability lane over the games since 2026-10-20 on the final archives (uncounted, descriptive); the two share the T-60 checkpoint, the thresholds, the costs and the caps, so the board-selection rule is the only difference. Prospective, counted evidence is read only from each lane's own sealed ledger (control start 2026-10-24T06:00Z; t60a start 2026-10-27T06:00:00Z); archival quotes are displayed quotes, not proven live fills.

## Primary comparison: coverage, predicted EV, CLV, settled performance, quote freshness and price drift

| lane (source) | games | evaluated | traded | excluded by archive latency | excluded no data | share evaluated | decision instants usable |
|---|---|---|---|---|---|---|---|
| control_T60_strict (RETROSPECTIVE_RECONSTRUCTION) | 16 | 6 | 5 | 10 | 0 | 0.375 | 5 / 11 |
| t60a_T60_available (RETROSPECTIVE_RECONSTRUCTION) | 16 | 16 | 11 | 0 | 0 | 1.0 | 11 / 11 |

| lane | trades | mean predicted EV | settled | net P&L | ROI on outlay | hit rate | CLV mean (c, n valid) | quote age at decision median / p90 (s) | ask drift mean (c) | adverse drift share |
|---|---|---|---|---|---|---|---|---|---|---|
| control_T60_strict | 18 | 0.156 | 18 | -0.62 | -0.072 | 0.444 | -1.14 (18) | 724.0 / 724.0 | -0.11 | 0.056 |
| t60a_T60_available | 42 | 0.168 | 42 | 0.36 | 0.018 | 0.476 | 0.63 (42) | 557.0 / 724.0 | 1.07 | 0.143 |

## Paired differences (control vs t60a, same games)

* games evaluated by both lanes: 6; only by the availability lane (recovered): 10; only by the control: 0
* identical selections on the common games: True (the availability rule is a superset of the strict rule: games_only_control_evaluated must be 0 and the common games must agree contract for contract)
* common games: {"control": {"games": 6, "mean_clv_cents": -1.139, "n_clv": 18, "net_pnl": -0.62, "trades": 18}, "t60a": {"games": 6, "mean_clv_cents": -1.139, "n_clv": 18, "net_pnl": -0.62, "trades": 18}}
* recovered games: {"t60a": {"games": 10, "mean_clv_cents": 1.958, "n_clv": 24, "net_pnl": 0.98, "trades": 24}}
* per-game net P&L difference: n=16, mean=0.0612, bootstrap {"hi95": 0.3263, "lo95": -0.2144, "method": "game-clustered bootstrap of the per-game mean difference", "n_boot": 2000, "seed": 53, "status": "OK"}; unsettled trades excluded: 0
* t60a minus control, summed over a game's settled trades (0 for a game a lane did not evaluate); descriptive, not evidence of an edge until the sealed ledgers carry it

Selection overlap (control vs t60a, retrospective): {"contracts_both": 18, "control_only": 0, "games_control_only": 0, "games_t60a_only": 6, "games_traded_both": 5, "reading": "descriptive; each lane keeps its own ledger and exposure caps, so a shared contract is two separate shadow positions", "t60a_only": 24}

## Projection accuracy on all eligible games (independent of trades, markets and lanes)

* eligible games with settled forecasts: 16; challenger forecasts scored: 3122
* eligible games by lane status: {"control_T60_strict": {"EVALUATED_NO_TRADE": 1, "EXCLUDED_ARCHIVE_LATENCY": 10, "TRADED": 5}, "t60a_T60_available": {"EVALUATED_NO_TRADE": 5, "TRADED": 11}}
* the denominator is every game with settled forecasts. TRADED, EVALUATED_NO_TRADE, EXCLUDED_* and NO_SEAL games are all scored; a trade decision, a missing board or a lane exclusion never removes a game from the accuracy evaluation

## EXPLORATORY ONLY: T-45 availability (inactive; not part of the primary comparison, never pooled, not an evidence line)

| lane (source) | games | evaluated | traded | excluded by archive latency | excluded no data | share evaluated | decision instants usable |
|---|---|---|---|---|---|---|---|
| comparator_T45_strict (RETROSPECTIVE_COMPARATOR) | 16 | 5 | 4 | 11 | 0 | 0.312 | 4 / 11 |
| t45_T45_available (RETROSPECTIVE_RECONSTRUCTION) | 16 | 16 | 10 | 0 | 0 | 1.0 | 11 / 11 |

| lane | trades | mean predicted EV | settled | net P&L | ROI on outlay | hit rate | CLV mean (c, n valid) | quote age at decision median / p90 (s) | ask drift mean (c) | adverse drift share |
|---|---|---|---|---|---|---|---|---|---|---|
| comparator_T45_strict | 15 | 0.171 | 15 | 0.97 | 0.138 | 0.533 | -1.27 (15) | 724.0 / 724.0 | 1.4 | 0.2 |
| t45_T45_available | 39 | 0.171 | 39 | -0.22 | -0.012 | 0.462 | 0.0 (39) | 497.0 / 724.0 | 0.56 | 0.154 |

* T-45 changes two things relative to the control (the offset AND the board rule); it is inactive, kept only as a labelled exploratory option, and is excluded from the overlap, the paired differences and the accuracy table above.

## Caveats

* a handful of games: no inference; the coverage columns are mechanics, the P&L and CLV columns are anecdotes
* the availability rule trades on a board that is older at the decision instant than the few boards the control can use (quote age block); the 900 s guard bounds it, the drift is reported
* archival quotes are displayed quotes: nothing here shows that an order would have filled at the sealed price or size
* settled P&L, CLV and drift use the final archives; none of it was available to the selection
* retrospective reconstruction runs the sealer at the first minute of each window with commit-time filters, so it reproduces what a live sealer would have written; it is still uncounted
