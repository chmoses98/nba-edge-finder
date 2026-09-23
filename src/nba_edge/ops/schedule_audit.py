"""Did the scheduler actually deliver the slots it promised?

The conductor declares ``*/10 * * * *``. Whether GitHub delivers that is an empirical question, and
the answer decides whether a 5-10 minute capture objective is reachable on GitHub-native scheduling
at all. This module answers it from the Actions API: no external service, no new dependency, no
state beyond an append-only JSONL file.

Method. A cron expression defines the *nominal* slots in a window. Each delivered scheduled run is
matched to the latest nominal slot at or before its ``created_at`` -- GitHub never fires a slot
early, only late or not at all -- and at most one run is credited per slot. Slots left with no run
are missing. Delay is ``created_at - nominal``, and queue time is ``started_at - created_at``, which
are different things: the first is the scheduler being late, the second is a runner being busy.

Deliberately not a service. It reads history, so a single run recovers everything back to the
retention window; there is nothing to keep alive and nothing to lose if it stops.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

# A minimal cron reader: enough for the shapes a scheduler audit actually sees, and it refuses
# anything it does not fully understand rather than silently mis-expanding a field.
_FIELDS = ("minute", "hour", "dom", "month", "dow")
_RANGES = {"minute": (0, 59), "hour": (0, 23), "dom": (1, 31), "month": (1, 12), "dow": (0, 6)}


def _expand(spec: str, lo: int, hi: int) -> set[int]:
    out: set[int] = set()
    for part in spec.split(","):
        step = 1
        if "/" in part:
            part, step_s = part.split("/", 1)
            step = int(step_s)
        if part in ("*", ""):
            start, end = lo, hi
        elif "-" in part:
            a, b = part.split("-", 1)
            start, end = int(a), int(b)
        else:
            start = end = int(part)
            if step != 1:  # "5/10" is not a form we want to guess at
                raise ValueError(f"unsupported cron part {part!r}/{step}")
        out |= set(range(start, end + 1, step))
    if not out or min(out) < lo or max(out) > hi:
        raise ValueError(f"cron field out of range: {spec!r}")
    return out


def cron_slots(expr: str, start: datetime, end: datetime) -> list[datetime]:
    """Every nominal UTC slot the cron expression defines in [start, end]."""
    parts = expr.split()
    if len(parts) != 5:
        raise ValueError(f"expected a 5-field cron expression, got {expr!r}")
    sets = {f: _expand(p, *_RANGES[f]) for f, p in zip(_FIELDS, parts, strict=True)}
    t = start.replace(second=0, microsecond=0, tzinfo=UTC)
    slots = []
    while t <= end:
        if (
            t.minute in sets["minute"]
            and t.hour in sets["hour"]
            and t.day in sets["dom"]
            and t.month in sets["month"]
            and (t.weekday() + 1) % 7 in sets["dow"]
        ):
            slots.append(t)
        t += timedelta(minutes=1)
    return slots


@dataclass
class SlotRecord:
    nominal_utc: str
    delivered: bool
    run_id: int | None = None
    created_at: str | None = None
    started_at: str | None = None
    delay_s: float | None = None
    queue_s: float | None = None
    conclusion: str | None = None


@dataclass
class ScheduleAudit:
    cron: str
    window_start: str
    window_end: str
    expected: int
    delivered: int
    missing: int
    delivery_rate: float
    delay_median_s: float | None
    delay_p90_s: float | None
    delay_max_s: float | None
    longest_gap_min: float | None
    effective_interval_min: float | None
    conclusions: dict[str, int] = field(default_factory=dict)
    slots: list[SlotRecord] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        d = {k: v for k, v in self.__dict__.items() if k != "slots"}
        d["slots"] = [s.__dict__ for s in self.slots]
        return d


def _pct(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        raise ValueError("no values")
    i = min(len(sorted_vals) - 1, int(round(q * (len(sorted_vals) - 1))))
    return sorted_vals[i]


def audit(cron: str, runs: list[dict[str, Any]], start: datetime, end: datetime) -> ScheduleAudit:
    """Match delivered scheduled runs to nominal slots.

    ``runs`` are Actions API objects already filtered to ``event == "schedule"``. A run is credited
    to the latest slot at or before its creation, and each slot takes at most one run, so a burst of
    catch-up runs cannot paper over the slots they were catching up on.
    """
    slots = cron_slots(cron, start, end)
    by_slot: dict[datetime, dict[str, Any]] = {}
    for r in sorted(runs, key=lambda r: r["created_at"]):
        created = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
        earlier = [s for s in slots if s <= created]
        if not earlier:
            continue
        slot = earlier[-1]
        by_slot.setdefault(slot, r)  # first run to claim a slot keeps it

    recs, delays = [], []
    conclusions: dict[str, int] = {}
    for s in slots:
        r = by_slot.get(s)
        if r is None:
            recs.append(SlotRecord(nominal_utc=s.isoformat().replace("+00:00", "Z"), delivered=False))
            continue
        created = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
        started = (
            datetime.fromisoformat(r["run_started_at"].replace("Z", "+00:00"))
            if r.get("run_started_at")
            else None
        )
        delay = (created - s).total_seconds()
        delays.append(delay)
        c = str(r.get("conclusion"))
        conclusions[c] = conclusions.get(c, 0) + 1
        recs.append(SlotRecord(
            nominal_utc=s.isoformat().replace("+00:00", "Z"), delivered=True, run_id=r["id"],
            created_at=r["created_at"], started_at=r.get("run_started_at"), delay_s=delay,
            queue_s=None if started is None else (started - created).total_seconds(),
            conclusion=r.get("conclusion"),
        ))

    delivered_times = sorted(
        datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")) for r in by_slot.values()
    )
    gaps = [
        (delivered_times[i + 1] - delivered_times[i]).total_seconds() / 60
        for i in range(len(delivered_times) - 1)
    ]
    ds = sorted(delays)
    n_exp = len(slots)
    span_min = (end - start).total_seconds() / 60
    return ScheduleAudit(
        cron=cron,
        window_start=start.isoformat().replace("+00:00", "Z"),
        window_end=end.isoformat().replace("+00:00", "Z"),
        expected=n_exp,
        delivered=len(by_slot),
        missing=n_exp - len(by_slot),
        delivery_rate=(len(by_slot) / n_exp) if n_exp else 0.0,
        delay_median_s=_pct(ds, 0.5) if ds else None,
        delay_p90_s=_pct(ds, 0.9) if ds else None,
        delay_max_s=max(ds) if ds else None,
        longest_gap_min=max(gaps) if gaps else None,
        effective_interval_min=(span_min / len(by_slot)) if by_slot else None,
        conclusions=dict(sorted(conclusions.items())),
        slots=recs,
    )


def append_jsonl(path: Path, rec: dict[str, Any]) -> None:
    """Append-only: every audit run is kept, so reliability can be tracked as the season approaches."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")


def summarize(a: ScheduleAudit) -> str:
    def m(s: float | None) -> str:
        return "n/a" if s is None else f"{s / 60:.1f} min"

    lines = [
        f"cron `{a.cron}` over {a.window_start} .. {a.window_end}",
        "",
        "| metric | value |",
        "|---|---:|",
        f"| expected slots | {a.expected} |",
        f"| delivered | {a.delivered} |",
        f"| missing | {a.missing} |",
        f"| delivery rate | {a.delivery_rate:.1%} |",
        f"| median delay | {m(a.delay_median_s)} |",
        f"| p90 delay | {m(a.delay_p90_s)} |",
        f"| max delay | {m(a.delay_max_s)} |",
        f"| longest gap between runs | {a.longest_gap_min:.1f} min |" if a.longest_gap_min else "| longest gap | n/a |",
        f"| effective interval | {a.effective_interval_min:.1f} min |" if a.effective_interval_min else "| effective interval | n/a |",
    ]
    if a.conclusions:
        lines += ["", f"conclusions: {a.conclusions}"]
    return "\n".join(lines)
