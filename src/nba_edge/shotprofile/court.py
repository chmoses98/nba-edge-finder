"""Court geometry for ESPN shot coordinates, and the zone classification built on it.

Every constant here was measured by ``scripts/probe_shot_coordinates.py`` against real games and is
recorded in ``docs/research/ESPN_SHOT_COORDINATES.md``. None of it is assumed, and one of the
measurements contradicted the physically intuitive guess outright -- see ``HOOP_Y``.
"""

from __future__ import annotations

import math
from enum import StrEnum

# == measured geometry =========================================================================
#
# ESPN's play coordinates are HALF-COURT NORMALISED: both teams' attempts land on one half-court,
# so x carries no information about which basket and needs no flip between halves. Measured over
# 20 games: mean x was 24.7-25.2 for home and away alike, in both halves, with median exactly 25.
#
# x runs 0..50 -- the court's 50-foot width, with 25 on the centre line.
HOOP_X = 25.0

# y is measured from the BASKET, not from the baseline.
#
# This is the one that caught me out. An NBA hoop sits 5.25 ft in from the baseline, so measuring y
# from the baseline is the physically natural reading, and it is wrong. Scored against the known
# three-point line (2023-24, 25 games, 2,069 attempts with a recorded value):
#
#     origin (25, 5.25):  3PT beyond the arc  342/638 ( 53.6%)
#     origin (25, 4.75):  3PT beyond the arc  395/638 ( 61.9%)
#     origin (25, 0.00):  3PT beyond the arc  638/638 (100.0%)   2PT inside 1431/1431 (100.0%)
#     transposed (0, 25): 3PT beyond the arc  385/638 ( 60.3%)   2PT inside    78/1431 (  5.5%)
#
# It also explains y running down to -5: those are attempts from behind the backboard.
#
# LIMITATION, because it bounds what the zones below can claim. The arc test scores a perfect
# 1.0000 for every y in [-1, +2] and only degrades at -2, so it locates the origin to a band of
# roughly three feet rather than to a point. That is ample for the 2PT/3PT split -- measured
# separation under this origin is clean, max 2PT distance 21.5 ft against min 3PT distance 22.0 ft,
# with no overlap -- but it is NOT ample for RIM_MAX_FT, a 4-foot radius that the same uncertainty
# could shift by a third. Rim-versus-paint is therefore the softest boundary in this module, and a
# study that leans on it should treat the split as approximate rather than as measured fact.
HOOP_Y = 0.0

# The three-point line, as the rulebook defines it rather than as the data suggests.
CORNER_THREE_DISTANCE_FT = 22.0
ABOVE_BREAK_THREE_DISTANCE_FT = 23.75
CORNER_X_HALF_WIDTH = 22.0
# Where the arc meets the sideline, and the corner stops being a corner:
# sqrt(23.75^2 - 22^2) = 8.94 ft from the basket. Above that the line curves and the shot is
# above-the-break even at the same x.
#
# The first version tested only |x - 25| >= 22 and put 12.8% of attempts in the corners against a
# league rate near 8% -- it was catching wing threes taken near the sideline. Measured on 26,767
# located attempts; see SHOT_PROFILE.md.
CORNER_MAX_Y_FT = 8.94

# The paint is a RECTANGLE, not a radius. The lane is 16 ft wide and runs 19 ft from the baseline,
# which is 19 - 5.25 = 13.75 ft from the basket in these coordinates.
#
# The first version used a 14-ft radius and put 21.6% of attempts in the non-rim paint against a
# league rate near 12%, while starving midrange at 7.4% against 13%: a radius sweeps in the
# baseline and elbow jumpers that sit outside the lane but close to the basket.
PAINT_HALF_WIDTH_FT = 8.0
PAINT_DEPTH_FT = 13.75

# Zone boundaries, in feet from the basket.
RIM_MAX_FT = 4.0        # restricted-area scale

# Court-plausible bounds, from the measured ranges (x 0..50, y -5..71) with headroom. A coordinate
# outside these is data corruption, not a shot.
X_BOUNDS = (-2.0, 52.0)
Y_BOUNDS = (-10.0, 94.0)


class ShotZone(StrEnum):
    """Where an attempt was taken from. ``UNKNOWN`` is a real answer, not a placeholder."""

    RIM = "rim"
    PAINT_NON_RIM = "paint_non_rim"
    MIDRANGE = "midrange"
    CORNER_THREE = "corner_three"
    ABOVE_BREAK_THREE = "above_break_three"
    UNKNOWN = "unknown"


THREE_ZONES = (ShotZone.CORNER_THREE, ShotZone.ABOVE_BREAK_THREE)
TWO_ZONES = (ShotZone.RIM, ShotZone.PAINT_NON_RIM, ShotZone.MIDRANGE)


def in_bounds(x: float | None, y: float | None) -> bool:
    if x is None or y is None:
        return False
    if x != x or y != y:  # NaN
        return False
    return X_BOUNDS[0] <= x <= X_BOUNDS[1] and Y_BOUNDS[0] <= y <= Y_BOUNDS[1]


def distance_ft(x: float, y: float) -> float:
    """Straight-line distance from the basket, in feet."""
    return math.hypot(x - HOOP_X, y - HOOP_Y)


def is_corner(x: float, y: float) -> bool:
    """Whether an attempt sits in a true corner: wide enough AND below where the arc begins.

    Both conditions matter. Width alone classifies wing threes taken near the sideline as corners,
    which measured 12.8% of attempts against a league corner rate near 8%.
    """
    return abs(x - HOOP_X) >= CORNER_X_HALF_WIDTH and y <= CORNER_MAX_Y_FT


def three_point_distance(x: float, y: float) -> float:
    return CORNER_THREE_DISTANCE_FT if is_corner(x, y) else ABOVE_BREAK_THREE_DISTANCE_FT


def in_paint(x: float, y: float) -> bool:
    """Inside the lane: a rectangle, which is what the painted area actually is."""
    return abs(x - HOOP_X) <= PAINT_HALF_WIDTH_FT and y <= PAINT_DEPTH_FT


def classify(
    x: float | None, y: float | None, *, points_value: int | None = None
) -> ShotZone:
    """Assign a zone from a coordinate, deferring to the scoreboard on 2 vs 3.

    ``points_value`` is ESPN's own record of what the shot was worth, and where it disagrees with
    the geometry it wins. Coordinates are integer-valued, so an attempt within a foot of the arc is
    genuinely ambiguous on distance alone -- but never ambiguous on the scoreboard. Using geometry
    to overrule a recorded 3 would move real attempts across the most important boundary in the
    whole profile.
    """
    if not in_bounds(x, y):
        return ShotZone.UNKNOWN
    assert x is not None and y is not None  # narrowed by in_bounds

    d = distance_ft(x, y)
    corner = is_corner(x, y)

    def two_point_zone() -> ShotZone:
        if d <= RIM_MAX_FT:
            return ShotZone.RIM
        if in_paint(x, y):
            return ShotZone.PAINT_NON_RIM
        return ShotZone.MIDRANGE

    if points_value == 3:
        return ShotZone.CORNER_THREE if corner else ShotZone.ABOVE_BREAK_THREE
    if points_value == 2:
        return two_point_zone()

    # No recorded value: fall back to geometry alone.
    if d >= three_point_distance(x, y):
        return ShotZone.CORNER_THREE if corner else ShotZone.ABOVE_BREAK_THREE
    return two_point_zone()
