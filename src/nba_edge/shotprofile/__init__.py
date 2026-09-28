"""Shot-profile research: what a player shoots and where, and what an opponent allows.

The first MATCHUP_AWARE_V2 data arm backed by a source this project can actually reach. Read
``DEFENDER_ATTRIBUTION_AVAILABLE`` before using anything here in a matchup argument: ESPN gives shot
LOCATIONS, never who was guarding. The two are not interchangeable and this package refuses to let
them be confused.
"""

from nba_edge.shotprofile.events import (
    DEFENDER_ATTRIBUTION_AVAILABLE,
    SHOT_EVENT_SCHEMA_VERSION,
    ShotEvent,
)

__all__ = ["DEFENDER_ATTRIBUTION_AVAILABLE", "SHOT_EVENT_SCHEMA_VERSION", "ShotEvent"]
