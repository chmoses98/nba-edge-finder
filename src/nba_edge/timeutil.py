"""Time helpers. All internal timestamps are timezone-aware UTC datetimes or ISO-8601 strings with offset."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")


def utcnow() -> datetime:
    return datetime.now(tz=UTC)


def iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        raise ValueError("naive datetime not allowed")
    return dt.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_iso(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        raise ValueError(f"naive timestamp not allowed: {s}")
    return dt.astimezone(UTC)


def et_date(dt: datetime) -> str:
    """NBA 'game date' is an Eastern-time calendar date."""
    return dt.astimezone(ET).date().isoformat()


def minutes_until(target: datetime, now: datetime | None = None) -> float:
    now = now or utcnow()
    return (target - now) / timedelta(minutes=1)
