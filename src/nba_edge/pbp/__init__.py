"""Full play-by-play (every event type) and five-man lineup reconstruction -- research data only.

Additive to :mod:`nba_edge.shotprofile`, whose shot-event datasets are left untouched. Nothing in the
simulator, capture or settlement path imports this package.

* :mod:`nba_edge.pbp.espn_full` -- pure parsing of one ESPN ``summary`` payload into event, box and game rows.
* :mod:`nba_edge.pbp.ingest` -- the resumable backfill that writes ``data/history/espn_pbp/``.
* :mod:`nba_edge.pbp.lineups` -- lineup / stint / possession reconstruction and per-game certification.
"""
