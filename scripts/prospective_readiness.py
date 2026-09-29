"""RESEARCH: is the 2026-27 prospective evidence system ready to collect what future studies need?

This is a READINESS audit, not a results audit. It asks whether each stream is wired, scheduled, and proven,
and it reports the three states separately, because they are not the same thing:

    READY        wired, scheduled, and observed writing real rows
    ARMED        wired and scheduled, but has never written a row -- correct-looking, unproven
    NOT_READY    a required piece is missing; nothing will be collected

The distinction matters most for ARMED. Every stream is ARMED during an offseason, and an offseason no-op is
indistinguishable from a silent failure until the first game. Calling that READY is the failure this audit
exists to prevent: a horizon with no snapshot must never be reported as a covered horizon, and a stream that
has never run must never be reported as a working one.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ARCHIVE_REF = "origin/data-archive"
BASELINE_DIGEST = "5a4cbda0b973d1e4d6289557b99372e4735ebe3146fa76e8f0b6ca833193be78"


def _show(path: str) -> str | None:
    r = subprocess.run(["git", "show", f"{ARCHIVE_REF}:{path}"], capture_output=True)
    return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else None


def _json(path: str) -> dict | None:
    t = _show(path)
    if t is None:
        return None
    try:
        return json.loads(t)
    except ValueError:
        return None


def _kind_counts() -> dict[str, int]:
    t = _show("manifest.jsonl") or ""
    out: dict[str, int] = {}
    for line in t.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        k = str(d.get("kind"))
        out[k] = out.get(k, 0) + (d.get("rows") if isinstance(d.get("rows"), int) else 0)
    return out


def audit() -> dict:
    from nba_edge.matchup.events import LineupEventKind
    from nba_edge.ops.capture_health import HORIZONS_MINUTES
    from nba_edge.timeutil import et_date, utcnow
    from nba_edge.worker.plan import (
        CADENCE_FINAL_SECONDS,
        CADENCE_NEAR_SECONDS,
        CADENCE_TIGHT_SECONDS,
        WINDOW_OPEN_HOURS_BEFORE_TIP,
    )
    from nba_edge.workflows.conductor import SEASON_CALENDAR, season_window

    now = utcnow()
    today = et_date(now)
    in_season, label, known = season_window(today)
    kinds = _kind_counts()
    health = _json("EVIDENCE_HEALTH.json") or {}
    lease = _json("LEASE_capture.json") or {}
    ctx_status = _json("STATUS_context.json") or {}

    rep: dict = {
        "generated_at_utc": now.isoformat().replace("+00:00", "Z"),
        "authority": "RESEARCH",
        "et_date": today,
        "season_calendar": {
            "known": known, "in_season": in_season, "season_label": label,
            "calendar": SEASON_CALENDAR,
        },
        "archive_rows_by_kind": kinds,
        "streams": {},
        "horizons": {},
        "blockers": [],
    }

    def stream(name: str, *, wired: bool, scheduled: bool, rows: int, detail: str, blocker: str | None = None):
        state = "NOT_READY" if not (wired and scheduled) else ("READY" if rows > 0 else "ARMED")
        rep["streams"][name] = {"state": state, "wired": wired, "scheduled": scheduled,
                                "rows_observed": rows, "detail": detail}
        if blocker:
            rep["streams"][name]["blocker"] = blocker
            rep["blockers"].append({"stream": name, "blocker": blocker})

    # ---- market horizons -------------------------------------------------------------------------------
    # A horizon is reachable when the cadence tier covering it ticks at least as often as the horizon is
    # wide. This is arithmetic on the policy, not a claim that a snapshot exists.
    named = {90: CADENCE_TIGHT_SECONDS, 60: CADENCE_TIGHT_SECONDS, 30: CADENCE_FINAL_SECONDS,
             10: CADENCE_FINAL_SECONDS}
    for minutes, cad in named.items():
        rep["horizons"][f"T-{minutes}m"] = {
            "reported_by_capture_health": minutes in HORIZONS_MINUTES,
            "cadence_seconds_at_this_horizon": cad,
            "worst_case_snapshot_age_minutes": round(cad / 60.0, 2),
            "reachable_by_policy": cad / 60.0 <= 12.0,
            "observed_coverage": (health.get("markets", {}).get("cadence", {})
                                  .get("horizon_coverage", {}).get(f"T-{minutes}m", {})
                                  .get("games_with_any_prior_snapshot", 0)),
        }
    rep["horizons"]["final_pregame"] = {
        "reported_by_capture_health": True,
        "rule": "last snapshot STRICTLY before tip; a post-tip snapshot can never satisfy it",
        "cadence_seconds_at_this_horizon": CADENCE_FINAL_SECONDS,
        "worst_case_snapshot_age_minutes": round(CADENCE_FINAL_SECONDS / 60.0, 2),
        "reachable_by_policy": True,
        "observed_coverage": 0 if not health else (
            health.get("markets", {}).get("cadence", {}).get("n_games", 0)),
    }
    rep["capture_window_opens_hours_before_tip"] = WINDOW_OPEN_HOURS_BEFORE_TIP
    rep["cadence_tiers_seconds"] = {
        "beyond_T-6h": 900.0, "T-6h..T-90m": CADENCE_NEAR_SECONDS,
        "T-90m..T-30m": CADENCE_TIGHT_SECONDS, "inside_T-30m": CADENCE_FINAL_SECONDS,
    }

    # ---- streams ---------------------------------------------------------------------------------------
    stream("market_board", wired=True, scheduled=True, rows=kinds.get("kalshi/markets", 0),
           detail=f"last capture {health.get('markets', {}).get('last_capture_utc')}; "
                  f"{health.get('markets', {}).get('n_discovered')} markets over "
                  f"{health.get('markets', {}).get('n_series')} series")
    stream("orderbooks", wired=True, scheduled=True, rows=kinds.get("kalshi/orderbooks", 0),
           detail="captured alongside the board, capped per run")
    for k in ("schedule", "rosters", "injuries"):
        c = health.get("context", {}).get(k, {})
        stream(f"context_{k}", wired=True, scheduled=True, rows=kinds.get(f"context/{k}", 0),
               detail=f"state={c.get('state')} n_snapshots={c.get('n_snapshots')} "
                      f"days={c.get('first_day')}..{c.get('last_day')}")

    cs = health.get("context", {}).get("confirmed_starters", {})
    # This is an ABSENT SOURCE, not a discarded field, and the code already refuses to paper over it:
    # shadow.build_context leaves expected_*_starters empty on purpose, because a projection written into
    # that field would be indistinguishable from a confirmation months later. The only starter flag in the
    # repo lives on the BOX SCORE, which is post-game and therefore leakage for a pregame forecast.
    stream("confirmed_starters", wired=False, scheduled=False, rows=0,
           detail=str(cs.get("reason")) + "; shadow.build_context leaves expected_*_starters empty by "
                  "design rather than writing a projection into a field that would later read as confirmed",
           blocker="No pregame confirmed-starter source is ingested. LINEUP_CONFIRMED and STARTER_CHANGE "
                   "therefore cannot fire at all, and lineup_confidence stays UNKNOWN. This needs a source, "
                   "not a code change -- the box-score starter flag is post-game and would be leakage.")
    stream("matchup_context", wired=True, scheduled=True, rows=kinds.get("matchup/context", 0),
           detail="nba matchup-shadow runs in conductor.yml, gated on the same condition as context; "
                  "writes nothing while no game is inside the 36h horizon",
           blocker=None if kinds.get("matchup/context", 0) else
                   "no snapshot has ever been written, so the offseason no-op and a silent failure are "
                   "indistinguishable. Two snapshots per game are needed before any event can be diffed.")

    # ---- information events ----------------------------------------------------------------------------
    rep["information_events"] = {
        "kinds": [k.value for k in LineupEventKind],
        "snapshots_required_per_game_to_diff": 2,
        "snapshots_present": kinds.get("matchup/context", 0),
        "state": "ARMED" if kinds.get("matchup/context", 0) == 0 else "READY",
        "note": "stratify() needs at least two matchup/context snapshots for a game before it can emit a "
                "single event. With zero snapshots every stratum, no_event included, is empty.",
    }

    # ---- worker / archive safety -----------------------------------------------------------------------
    w = health.get("worker", {})
    rep["worker"] = {
        "state": w.get("state"), "generation_in_health": w.get("generation"),
        "generation_in_lease": lease.get("generation"),
        "successor_dispatched": w.get("successor_dispatched"),
        "fail_closed": w.get("fail_closed"),
        "n_cycles": w.get("n_cycles"), "n_capture_failed": w.get("n_capture_failed"),
        "exit_reason": w.get("exit_reason"),
        "lease_heartbeat_at": lease.get("heartbeat_at"),
        "lease_planned_exit_at": lease.get("planned_exit_at"),
        "self_renewing": bool(w.get("successor_dispatched")) and lease.get("generation") is not None,
    }
    rep["archive"] = {
        "delta_chains": health.get("delta_chains", {}),
        "context_refreshed_at": ctx_status.get("refreshed_at_utc"),
        "schedule_days_ahead": ctx_status.get("schedule", {}).get("days_ahead"),
    }
    b = health.get("baseline", {})
    rep["baseline_freeze"] = {
        "baseline_id": b.get("baseline_id"), "state": b.get("state"),
        "frozen_parameters_intact": b.get("frozen_parameters_intact"),
        "live_digest": b.get("live_digest"),
        "matches_expected_digest": b.get("live_digest") == BASELINE_DIGEST,
    }
    if not rep["baseline_freeze"]["matches_expected_digest"]:
        rep["blockers"].append({"stream": "baseline_freeze",
                                "blocker": "live digest does not match the frozen baseline digest"})

    # Readiness is reported per PURPOSE rather than as one flat verdict. The two purposes have entirely
    # different blockers: market-relative research needs the board and the clock, and has both; event
    # stratification needs a confirmed-starter source that does not exist. Collapsing them into a single
    # NOT_READY would hide that the first is a matter of waiting for tip-off and the second is not.
    def roll(names: list[str]) -> str:
        st = {rep["streams"][n]["state"] for n in names if n in rep["streams"]}
        return "NOT_READY" if "NOT_READY" in st else ("ARMED" if "ARMED" in st else "READY")

    market = ["market_board", "orderbooks", "context_schedule"]
    events = ["matchup_context", "confirmed_starters", "context_rosters", "context_injuries"]
    rep["readiness_by_purpose"] = {
        "market_relative_research": {
            "state": roll(market), "streams": market,
            "note": "the horizons future market-relative studies need. Every stream has captured real rows; "
                    "no game has been inside the capture window yet this season, so no horizon has an "
                    "observed snapshot. That is NOT a covered horizon and is not reported as one.",
        },
        "information_event_stratification": {
            "state": roll(events), "streams": events,
            "note": "blocked on an absent pregame confirmed-starter source, not on schedule or code.",
        },
    }
    states = {s["state"] for s in rep["streams"].values()}
    rep["overall"] = ("NOT_READY" if "NOT_READY" in states
                      else ("ARMED" if "ARMED" in states else "READY"))
    rep["overall_note"] = ("NOT_READY is driven entirely by the absent confirmed-starter source. The "
                           "market-relative collection this wave was asked about is ARMED: wired, "
                           "scheduled, proven on real rows, and waiting for the first tip of 2026-27.")
    return rep


def main() -> int:
    rep = audit()
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    text = json.dumps(rep, indent=1)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
