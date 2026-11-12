"""What a capture worker should do next: lifetime, cadence, active window, rollover.

Every constant here is derived from something measured on this repository's own Actions history
(39 ``conductor/run`` jobs, 93 ``ci/test`` jobs) or from a chainlab experiment, and the derivation
is recorded next to the constant. Nothing here is a guess dressed as a default.

Stdlib-only, deliberately (see ``worker/lease.py`` for why).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from nba_edge.timeutil import parse_iso

# ---------------------------------------------------------------------------------------------
# Worker lifetime (Phase 2)
# ---------------------------------------------------------------------------------------------
# GitHub caps a hosted JOB at 6 hours. That figure could not be re-verified against
# docs.github.com from the build environment (the host is denied by network policy) and a
# six-hour empirical probe was not worth the wall-clock, so the design is built to never depend on
# knowing it precisely: the worker retires itself on its OWN clock with an hour of headroom, and
# the workflow timeout sits between the two purely as a backstop.
#
# The brief's instruction is the binding one: "A timeout must never be the normal rollover
# mechanism." So:
#     planned lifetime   300 min  (this constant)   <- the normal mechanism
#     workflow timeout   330 min  (capture_worker.yml)
#     platform cap       360 min  (documented)
#
# Measured rollover cost, i.e. how much of that 30-minute backstop a worst-case retirement can
# actually consume: successor dispatch 1s (E1) + parent teardown ~2s + successor queue-to-running
# 2-7s (E1: parent completed :16, successor job started :19). Under a minute, against a 30-minute
# backstop and a 60-minute cushion beneath the platform cap.
PLANNED_LIFETIME_MINUTES = 300.0

# Reserved at the end of life so retirement never has to interrupt work in flight. Budget:
# one whole capture cycle at its measured worst (capture max 186s, p90 181s) + an archive push
# that exhausts its retry backoff (~62s of sleeps) + teardown. Rounded up hard.
RETIREMENT_RESERVE_MINUTES = 8.0

# ---------------------------------------------------------------------------------------------
# Capture cadence (Phase 11)
# ---------------------------------------------------------------------------------------------
# Tiered by how fast the information actually moves, NOT by what sounds thorough. The brief is
# explicit: "Do not implement 5-minute cadence merely because it sounds better." The tightest tier
# is 5 minutes and it is confined to the last half hour before tip, where starter confirmations and
# late scratches land. Note the duty cycle that buys: a capture measured at p90 181s / max 186s
# inside a 300s tick leaves ~114s of slack, so a slow capture degrades the tick rather than
# colliding with the next one -- which is why the loop schedules from cycle START, not cycle end.
CADENCE_FAR_SECONDS = 900.0  # beyond T-6h: 15 min
CADENCE_NEAR_SECONDS = 600.0  # T-6h .. T-90m: 10 min
CADENCE_TIGHT_SECONDS = 420.0  # T-90m .. T-30m: 7 min
CADENCE_FINAL_SECONDS = 300.0  # inside T-30m: 5 min

# How far before the first tip the worker starts capturing, and how long after the last tip it
# keeps going. Post-tip capture is NOT pregame data and is labelled accordingly by the capture
# layer; it is kept because settlement and late-market behaviour need it.
WINDOW_OPEN_HOURS_BEFORE_TIP = 8.0
WINDOW_CLOSE_HOURS_AFTER_TIP = 4.5


@dataclass(frozen=True)
class Cycle:
    """One iteration's decision."""

    should_capture: bool
    cadence_seconds: float
    next_cycle_at: datetime
    hours_to_next_tip: float | None
    reason: str


def tip_times(schedule_rows: list[dict]) -> list[datetime]:
    """Tip-off times from a schedule snapshot, ignoring rows we cannot parse.

    Unparseable rows are dropped rather than raising: a single malformed game must not be able to
    blind the worker to the rest of the slate.
    """
    out = []
    for g in schedule_rows:
        try:
            out.append(parse_iso(g["start_time_utc"]))
        except (KeyError, TypeError, ValueError):
            continue
    return sorted(out)


def hours_to_next_tip(now: datetime, tips: list[datetime]) -> float | None:
    upcoming = [t for t in tips if t > now]
    return (upcoming[0] - now).total_seconds() / 3600 if upcoming else None


def in_active_window(now: datetime, tips: list[datetime]) -> tuple[bool, str]:
    """Is there a game close enough, ahead or behind, to be worth capturing?"""
    for t in tips:
        delta_h = (t - now).total_seconds() / 3600
        if -WINDOW_CLOSE_HOURS_AFTER_TIP <= delta_h <= WINDOW_OPEN_HOURS_BEFORE_TIP:
            return True, f"game at {t.isoformat()} is T{delta_h:+.2f}h"
    return False, "no game within the active window"


def cadence_seconds(hours_to_tip: float | None) -> float:
    """Seconds between captures, from the nearest tip ahead."""
    if hours_to_tip is None:
        return CADENCE_FAR_SECONDS
    minutes = hours_to_tip * 60
    if minutes <= 30:
        return CADENCE_FINAL_SECONDS
    if minutes <= 90:
        return CADENCE_TIGHT_SECONDS
    if hours_to_tip <= 6:
        return CADENCE_NEAR_SECONDS
    return CADENCE_FAR_SECONDS


def plan_cycle(now: datetime, tips: list[datetime]) -> Cycle:
    active, why = in_active_window(now, tips)
    h = hours_to_next_tip(now, tips)
    cad = cadence_seconds(h)
    # Scheduled from the START of this cycle, not from its end. If a capture runs long, the next
    # tick is late by the overrun rather than late by the overrun PLUS a full cadence -- the
    # difference between a cadence that degrades gracefully and one that drifts without bound.
    return Cycle(
        should_capture=active,
        cadence_seconds=cad,
        next_cycle_at=now + timedelta(seconds=cad),
        hours_to_next_tip=h,
        reason=why,
    )


def planned_exit(started_at: datetime, lifetime_minutes: float = PLANNED_LIFETIME_MINUTES) -> datetime:
    return started_at + timedelta(minutes=lifetime_minutes)


def should_retire(now: datetime, exit_at: datetime, next_cycle_cost_seconds: float = 0.0) -> bool:
    """Retire once there is no longer room for another honest cycle plus the reserve.

    Taking the cost of the next cycle into account is the point: a worker that starts a 3-minute
    capture 2 minutes before its deadline has chosen to overrun, and overrunning is how a planned
    retirement degenerates into a timeout kill.
    """
    remaining = (exit_at - now).total_seconds()
    return remaining <= (RETIREMENT_RESERVE_MINUTES * 60 + next_cycle_cost_seconds)


# ---------------------------------------------------------------------------------------------
# Tip-aware handover placement (proposal; inert unless NBA_EDGE_TIP_AWARE_RETIREMENT=1)
# ---------------------------------------------------------------------------------------------
# A handover costs a gap with no writer. Measured over 25 handovers (2026-10-19..24): median 0.9 min, but 6 exceeded 7 min (24.4, 15.3, 63.1, 8.6, 7.6, 18.3);
# the long ones are hosted-runner queue time, outside our control and unpredictable. What IS in our control is WHERE the gap lands: retirement is purely
# lifetime-based (300 min), blind to the slate. This picks the retirement instant, inside a safe band, that keeps the expected gap clear of the windows that
# matter most -- from T-75m (the last 5-minute cadence zone incl. the T-60 capture) to T+5m of any tip.
#
# Safety rails, all preserving the existing contract: one writer (a handover is still retire -> successor, nothing overlaps); the band's upper end stays 18 min
# under the workflow's 330-min backstop; the choice is made once at shift start and recorded in the lease's planned_exit_at; with no schedule it is exactly the
# nominal lifetime. It does not touch the Issue #53 sealing control or any lane.
TIP_AWARE_MIN_LIFETIME_MINUTES = 210.0
TIP_AWARE_MAX_LIFETIME_MINUTES = 312.0
HANDOVER_GUARD_MINUTES = 30.0  # planning allowance for queue time; measured p80 of gaps is ~2.5 min but the tail is 15-63 min
CRITICAL_BEFORE_TIP_MINUTES = 75.0
CRITICAL_AFTER_TIP_MINUTES = 5.0
_NOMINAL_PREFERENCE_PER_MINUTE = 0.01  # tie-break toward the measured 300-min lifetime


def critical_windows(tips: list[datetime]) -> list[tuple[datetime, datetime]]:
    """Merged [tip-75m, tip+5m] windows."""
    raw = sorted((t - timedelta(minutes=CRITICAL_BEFORE_TIP_MINUTES), t + timedelta(minutes=CRITICAL_AFTER_TIP_MINUTES)) for t in tips)
    merged: list[tuple[datetime, datetime]] = []
    for a, b in raw:
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    return merged


def _overlap_minutes(a: datetime, b: datetime, windows: list[tuple[datetime, datetime]]) -> float:
    return sum(max(0.0, (min(b, d) - max(a, c)).total_seconds() / 60) for c, d in windows)


def tip_aware_exit(
    started_at: datetime,
    tips: list[datetime],
    *,
    nominal_minutes: float = PLANNED_LIFETIME_MINUTES,
    min_minutes: float = TIP_AWARE_MIN_LIFETIME_MINUTES,
    max_minutes: float = TIP_AWARE_MAX_LIFETIME_MINUTES,
    guard_minutes: float = HANDOVER_GUARD_MINUTES,
) -> datetime:
    """The ``exit_at`` (see ``should_retire``) whose handover gap is least likely to land in a critical window.

    The worker actually retires ``RETIREMENT_RESERVE_MINUTES`` before ``exit_at``, so the handover instant evaluated is ``exit_at - reserve`` .. ``+ guard``.
    Ties and no-tips resolve to the nominal lifetime.
    """
    nominal = planned_exit(started_at, nominal_minutes)
    windows = critical_windows(tips)
    if not windows:
        return nominal
    reserve = timedelta(minutes=RETIREMENT_RESERVE_MINUTES)
    best_cost, best = None, nominal
    m = int(min_minutes)
    while m <= int(max_minutes):
        exit_at = started_at + timedelta(minutes=m)
        h0 = exit_at - reserve
        cost = _overlap_minutes(h0, h0 + timedelta(minutes=guard_minutes), windows) + abs(m - nominal_minutes) * _NOMINAL_PREFERENCE_PER_MINUTE
        if best_cost is None or cost < best_cost - 1e-9:
            best_cost, best = cost, exit_at
        m += 1
    return best
