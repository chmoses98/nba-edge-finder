"""Slot-based scheduling for the NBA live workflow (pure functions; no network, no wall clock unless asked).

Why this exists
  GitHub `schedule` events are delivered late (measured here: 1.5 h to 5 h) and sometimes not at all. The previous plan job read the
  WALL-CLOCK hour when the delayed event finally ran and compared it with the intended ET hour, so a late event concluded
  "nothing to do" and the workflow finished green with every job skipped. This module replaces that with SLOTS:

    * a slot is an intended ET instant (e.g. 11:20 ET) for a kind of work (pregame | settle), identified by its ET date and time;
    * whatever event arrives (primary cron, backup cron, DST alternate, a very late delivery) works out the most recent slot that
      is due and RUNS it unless the ledger already holds that slot (a valid, explicit skip: `already_done`);
    * a failed run writes no ledger entry, so the next backup firing retries the same slot;
    * the only valid reasons to skip are listed in VALID_SKIP_REASONS; the workflow's final `outcome` job fails on any other.

  Every instant is computed with zoneinfo, so EDT/EST transitions never move a slot, and the cron table lists both UTC hours of
  every ET target (one of each pair is the intended one, the other is a free backup that the ledger turns into a no-op).
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
UTC = timezone.utc

# kind -> ET (hour, minute) slots. 13:50 ET covers the afternoon tips (the 2026 opener has a 15:00 ET game); 17:20 follows the 17:00 official
# injury-report update; 18:20 / 19:50 / 21:20 put a fresh forecast roughly 40-100 min before the 19:00 / 20:30-21:30 / 22:00+ ET tips.
SLOTS: dict[str, list[tuple[int, int]]] = {
    "pregame": [(11, 20), (13, 50), (17, 20), (18, 20), (19, 50), (21, 20)],
    "settle": [(6, 40)],
}
BACKUP_DELAY_MIN = 25          # every slot also has a backup cron this many minutes later
MONTHS = "1-6,10-12"           # regular season + preseason + playoffs months; the offseason is not scheduled at all
SWEEP_CRON = f"50 15-23,0-3 * {MONTHS} *"

VALID_SKIP_REASONS = {
    "already_done": "the slot is already in the run ledger (a duplicate, backup or DST-alternate firing)",
    "sweep_not_due": "n/a",
}


def _utc_hours(h: int, m: int) -> list[int]:
    """The UTC hours an ET wall time lands on across DST states (EDT = UTC-4, EST = UTC-5)."""
    return sorted({(h + 4) % 24, (h + 5) % 24})


def _cron(minute: int, hours: list[int]) -> str:
    return f"{minute} {','.join(str(x) for x in hours)} * {MONTHS} *"


def cron_table() -> dict[str, str]:
    """cron string -> kind. The workflow file must list exactly these (tests enforce it)."""
    t: dict[str, str] = {}
    for kind, slots in SLOTS.items():
        for h, m in slots:
            t[_cron(m, _utc_hours(h, m))] = kind
            bm = m + BACKUP_DELAY_MIN
            bh = h + bm // 60
            t[_cron(bm % 60, _utc_hours(bh % 24, 0))] = kind
    t[SWEEP_CRON] = "sweep"
    return t


@dataclass
class Plan:
    mode: str                  # pregame | settle | sweep | dry | skip
    stage: str                 # comma separated stage list for run.py
    kind: str | None           # pregame | settle | None
    slot_id: str | None        # e.g. 2026-10-20@1120 (ET) or manual-<utc>
    slot_utc: str | None
    lateness_min: int | None
    trigger: str               # event name
    cron: str | None
    reason: str                # why this mode (explicit for skips)
    skip_valid: bool = True
    research_stage: str = ""   # comma separated research stages (run after the critical commit)

    def as_dict(self) -> dict:
        return asdict(self)


def slot_instants(kind: str, around: datetime, days_back: int = 3) -> list[tuple[datetime, str]]:
    """Every slot instant of `kind` for ET dates around `around` (sorted), as (utc instant, slot id)."""
    et0 = around.astimezone(ET).date()
    out = []
    for k in range(-days_back, 2):
        d = et0 + timedelta(days=k)
        for h, m in SLOTS[kind]:
            inst = datetime(d.year, d.month, d.day, h, m, tzinfo=ET)
            out.append((inst.astimezone(UTC), f"{d.isoformat()}@{h:02d}{m:02d}"))
    return sorted(out)


def due_slot(kind: str, now: datetime) -> tuple[datetime, str]:
    """The most recent slot of `kind` that is due at `now` (never a future one, however late `now` is)."""
    past = [x for x in slot_instants(kind, now) if x[0] <= now]
    return past[-1]


def slot_stages(kind: str) -> str:
    """Critical stages: forecast archiving, results, settlement, ledger. Committed on their own, before any research stage runs."""
    return "capture,project,publish,results,settle,score,ledger,guard" if kind == "pregame" else "results,settle,score,ledger,guard"


def research_stages(kind: str | None) -> str:
    """Paper trading, scorecards and the weekly report: separate step, so a research bug can never block or lose the critical evidence
    (the job still goes red and the problem is named)."""
    if kind == "pregame":
        return "paper,paper_replay,expressions,paper_settle,guard"
    if kind == "settle":
        return "paper_replay,expressions,paper_settle,daily,report,guard"
    return ""


def make_plan(event: str, cron: str | None, now: datetime, dry_run: bool = False, stage_in: str = "all",
              ledger_has=lambda slot_id, kind: False) -> Plan:
    """The decision. `ledger_has(slot_id, kind)` says whether the slot is already recorded in the archive's run ledger."""
    now = now.astimezone(UTC)
    if event == "pull_request" or (event == "workflow_dispatch" and dry_run):
        return Plan("dry", "all", None, None, None, None, event, cron, "dry run on a copy of the archive")
    if event == "workflow_dispatch":
        sid = "manual-" + now.strftime("%Y%m%dT%H%M%SZ")
        if (stage_in or "all") == "all":
            return Plan("pregame", slot_stages("pregame"), "pregame", sid, now.isoformat(), 0, event, cron, "manual dispatch always runs",
                        research_stage=research_stages("pregame"))
        return Plan("pregame", stage_in, "pregame", sid, now.isoformat(), 0, event, cron, "manual dispatch (explicit stages)")
    if event != "schedule":
        return Plan("skip", "", None, None, None, None, event, cron, f"unsupported event {event!r}", skip_valid=False)
    kind = cron_table().get(cron or "")
    if kind is None:
        return Plan("skip", "", None, None, None, None, event, cron, f"unknown cron {cron!r}: not in schedule_plan.cron_table()",
                    skip_valid=False)
    if kind == "sweep":
        # the hourly sweep is also a heartbeat: when a pregame slot is due and not in the ledger (its own crons were late or lost), run it
        inst, sid = due_slot("pregame", now)
        late = int((now - inst).total_seconds() // 60)
        if late <= 360 and not ledger_has(sid, "pregame"):
            return Plan("pregame", slot_stages("pregame"), "pregame", sid, inst.isoformat(), late, event, cron,
                        f"sweep heartbeat: pregame slot {sid} is due and not in the ledger ({late} min after the slot)",
                        research_stage=research_stages("pregame"))
        return Plan("sweep", "incumbent,guard", None, None, None, None, event, cron, "hourly incumbent sweep")
    inst, sid = due_slot(kind, now)
    late = int((now - inst).total_seconds() // 60)
    if ledger_has(sid, kind):
        return Plan("skip", "", kind, sid, inst.isoformat(), late, event, cron,
                    f"already_done: slot {sid} is in the run ledger (duplicate, backup or DST-alternate firing)")
    why = f"slot {sid} due; event arrived {late} min after the slot" + (" (late delivery: executed anyway)" if late > 45 else "")
    return Plan(kind, slot_stages(kind), kind, sid, inst.isoformat(), late, event, cron, why, research_stage=research_stages(kind))


def skip_is_valid(reason: str) -> bool:
    return any(reason.startswith(k) for k in VALID_SKIP_REASONS)


# ----------------------------------------------------------------------------------------------- CLI used by the workflow
def _ledger_lookup(ref: str | None):
    """Read-only check of the ledger on a fetched branch ref (cheap: ls-tree, no checkout)."""
    if not ref:
        return lambda sid, kind: False
    import subprocess

    def has(sid: str, kind: str) -> bool:
        day, hm = sid.split("@")
        try:
            out = subprocess.check_output(["git", "ls-tree", "--name-only", ref, f"ops/nba/slots/{day}/"], text=True, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            return False
        return f"ops/nba/slots/{day}/{hm}_{kind}.json" in out.split()
    return has


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="decide what a workflow event should do (prints key=value lines for $GITHUB_OUTPUT)")
    ap.add_argument("--event", required=True)
    ap.add_argument("--cron", default="")
    ap.add_argument("--dry-run", default="false")
    ap.add_argument("--stage", default="all")
    ap.add_argument("--now", default=None, help="ISO UTC (tests)")
    ap.add_argument("--ledger-ref", default=None, help="git ref holding the projection-data branch (e.g. FETCH_HEAD)")
    a = ap.parse_args(argv)
    now = datetime.fromisoformat(a.now.replace("Z", "+00:00")) if a.now else datetime.now(UTC)
    p = make_plan(a.event, a.cron or None, now, a.dry_run == "true", a.stage, _ledger_lookup(a.ledger_ref))
    d = p.as_dict()
    print(json.dumps(d), file=sys.stderr)
    for k in ("mode", "stage", "research_stage", "kind", "slot_id", "slot_utc", "lateness_min", "reason", "skip_valid"):
        v = str(d[k] if d[k] is not None else "").replace("\n", " ")
        if not re.fullmatch(r"[\w@:+.\- ,()/'=]*", v):
            v = re.sub(r"[^\w@:+.\- ,()/'=]", "_", v)
        print(f"{k}={v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
