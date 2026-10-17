"""NBA Projection Foundation live shadow operation (research only; authority research_only).

  sources         network layer (ESPN scoreboard / rosters / injuries / summary, official injury-report PDF) with
                  injectable replacements so every stage can run offline against recorded payloads
  availability    point-in-time availability observations (official injury report, ESPN injuries, starters)
  participation   as-of resolution of those observations into the published participation + P(play)
  reconcile       team reconciliation (player minutes / points normalised to the team projection)
  incumbent       archives the incumbent simulator's own pregame output (PURE shadow store) unchanged
  results         final ESPN box scores -> outcomes (participated=False for DNP / inactive)
  kalshi_report   reporting-only audit of Kalshi NBA player-prop listings (placeholders are never prices)
  run             `python -m nba.live.run --stage all|capture|project|publish|results|settle|score|guard`
"""
SPORT = "NBA"
