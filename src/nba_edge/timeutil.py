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


def et_midnight_utc(date_et: str) -> datetime:
    """Start of an ET calendar day as a real UTC instant.

    The ET offset is -04:00 in October and -05:00 in January, so a hardcoded offset is wrong for most of an NBA
    season. This is used as a prediction's data cutoff, which is recorded immutably, so being an hour out would
    misstate what the model was allowed to know.
    """
    return datetime.fromisoformat(f"{date_et}T00:00:00").replace(tzinfo=ET).astimezone(UTC)


def minutes_until(target: datetime, now: datetime | None = None) -> float:
    now = now or utcnow()
    return (target - now) / timedelta(minutes=1)
