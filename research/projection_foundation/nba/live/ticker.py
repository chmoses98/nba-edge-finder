"""Reliable tick for the NBA slots: decides which due slot is missing from the run ledger (pure; the workflow does the dispatching).

GitHub `schedule` events are delivered late or not at all (measured 2026-10-20: the 11:20 ET and 13:50 ET pregame slots, backups and the
sweep heartbeat produced no run for 3+ hours, while the market worker's own 10-minute cycle ran on time). The ticker is a self-renewing
long-lived job (like the capture worker) that wakes every few minutes, asks this module which slot is due and absent from the ledger, and
dispatches projection-foundation for exactly that slot. The slot guard and the write-once ledger keep every duplicate harmless.

    python -m nba.live.ticker [--now ISO] [--ledger-ref REF]       prints one `<kind> <slot_id> <lateness_min>` line per slot to dispatch
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone

from . import schedule_plan as SP

GRACE_MIN = {"pregame": 12, "settle": 12}              # give the cron/backup/heartbeat a moment before making up the slot
MAX_LATE_MIN = {"pregame": 8 * 60, "settle": 30 * 60}  # a slot older than this is not resurrected (later slots/runs own the data)


def due(now: datetime, ledger_has) -> list[dict]:
    out = []
    for kind in ("pregame", "settle"):
        inst, sid = SP.due_slot(kind, now)
        late = int((now - inst).total_seconds() // 60)
        if late < GRACE_MIN[kind] or late > MAX_LATE_MIN[kind] or ledger_has(sid, kind):
            continue
        out.append({"kind": kind, "slot_id": sid, "lateness_min": late})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--now", default=None)
    ap.add_argument("--ledger-ref", default=None)
    a = ap.parse_args(argv)
    now = datetime.fromisoformat(a.now.replace("Z", "+00:00")) if a.now else datetime.now(timezone.utc)
    for d in due(now, SP._ledger_lookup(a.ledger_ref)):
        print(f"{d['kind']} {d['slot_id']} {d['lateness_min']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
