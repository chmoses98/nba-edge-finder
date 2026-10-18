"""NBA Projection Foundation challenger (research only; never touches production code paths).

Modules
  data          ESPN box scores (sportsdataverse/hoopR release mirror + in-repo history), normalisation,
                pregame candidate pool, conversion to the production schema (for incumbent reproduction)
  features      point-in-time features (lagged player history, rest, team pace/efficiency ratings,
                opponent factors, teammate-absence) -- every feature uses strictly earlier dates
  minutes       minutes ladder A..F with a participation hurdle
  stats         stat-family ladder A..F (points, rebounds, assists, threes, FGA, PRA)
  team          team points / pace x efficiency and player-vs-team reconciliation
  distributions distribution families, threshold rungs and minutes-uncertainty propagation
  incumbent     walk-forward reproduction of the production simulator (src/nba_edge, read-only)
  evaluate      metrics + game-clustered bootstrap comparisons in the CONTRACT.md schema
  project       forward projections in sift.projections.v1
"""
SPORT = "NBA"
MODEL_ID = "pf-nba"
