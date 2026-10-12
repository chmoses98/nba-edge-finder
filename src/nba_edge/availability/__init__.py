"""Point-in-time player availability (official NBA injury reports) -- research data only.

* :mod:`nba_edge.availability.official_report` -- report URLs, positional PDF word extraction and the
  row parser (player, team, game, status, reason, report_time).
* :mod:`nba_edge.availability.identity` -- report names -> the repo's ESPN player ids, and report
  matchups -> ESPN game ids.
* :mod:`nba_edge.availability.backfill` -- bounded historical backfill with report_time < tip checks.
* :mod:`nba_edge.availability.capture` -- append-only prospective capture of the latest report.

Nothing in the simulator, capture worker or settlement imports this package.
"""
