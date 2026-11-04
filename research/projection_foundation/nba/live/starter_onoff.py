"""Controlled starter-input ON/OFF experiment on the REAL participation code path (no network, deterministic).

For each availability scenario one player-game is resolved twice by `participation.resolve_event`: OFF (no starter observation) and ON
(a fresh CONFIRMED starter observation 20 minutes before tip). Everything else is identical. We then evaluate exactly what `project.py`
does with the result: the calibrated P(play) and which minutes model publishes (E_inj when the OFFICIAL report covers the player,
else E). The legacy rule keyed the minutes model on `participation.source`; the fixed rule keys it on `report_source` (the injury
source), so a starter row cannot switch it.

This shows that a CONFIRMED starter row sets P(play) and (with the fix) does not switch the minutes model. It stops at P(play)/minutes-model choice: reconcile scaling,
expected_mean, actionable and gate status are downstream of P(play)/participation and are NOT exercised, and the ON row is hypothetical (the archived summary source emitted PROJECTED rows).
It does not measure predictive value
(no pregame starter history exists; see RESULTS_NBA.md: the oracle upper bound is -0.17 min MAE beyond E_inj)."""
from __future__ import annotations

import json
from typing import Any

import numpy as np

from . import participation as PART
from .availability import SRC_ESPN_INJ, SRC_OFFICIAL, SRC_STARTERS

EVENT, PLAYER = "espn:401000001", "espn:1"
TIP = "2026-11-05T00:00:00Z"
CAPTURED_INJ = "2026-11-04T18:00:00Z"
CAPTURED_START = "2026-11-04T23:40:00Z"
NOW = "2026-11-04T23:45:00Z"


def _row(kind, status, certainty, source, captured, detail=None):
    return {"sport": "NBA", "event_id": EVENT, "event_start_utc": TIP, "entity_id": PLAYER, "entity_name": "X", "team": "AAA", "kind": kind, "status": status, "certainty": certainty,
            "source": source, "captured_utc": captured, "source_updated_utc": captured, "source_url": None, "detail": detail or {}}


SCENARIOS = {
    "listed_ACTIVE_on_official_report": [_row("injury", "ACTIVE", "REPORTED", SRC_OFFICIAL, CAPTURED_INJ)],
    "listed_PROBABLE_on_official_report": [_row("injury", "PROBABLE", "REPORTED", SRC_OFFICIAL, CAPTURED_INJ)],
    "listed_QUESTIONABLE_on_official_report": [_row("injury", "QUESTIONABLE", "REPORTED", SRC_OFFICIAL, CAPTURED_INJ)],
    "not_listed_implicit_available": [_row("injury", "ACTIVE", "PROJECTED", SRC_OFFICIAL, CAPTURED_INJ, {"implicit": True})],
    "espn_injuries_only_no_official_report": [_row("injury", "PROBABLE", "REPORTED", SRC_ESPN_INJ, CAPTURED_INJ)],
    "no_injury_observation_at_all": [],
}
STARTER = _row("starter", "STARTING", "CONFIRMED", SRC_STARTERS, CAPTURED_START)


def decide(rows, p_hurdle, calib, legacy: bool):
    from datetime import datetime
    now = datetime.fromisoformat(NOW.replace("Z", "+00:00"))
    part = PART.resolve_event(rows, EVENT, TIP, [PLAYER], now)[PLAYER]
    p = float(PART.calibrated_p_play([p_hurdle], [part.get("_class")], calib)[0]) if part.get("_class") is not None or calib else p_hurdle
    p = float(PART.enforce_confirmed_out(np.array([p]), [part])[0])
    src = part.get("source") if legacy else part.get("report_source", part.get("source"))
    return {"participation_status": part["status"], "class": part.get("_class"), "participation_source": part.get("source"), "report_source": part.get("report_source"),
            "p_play": round(p, 4), "minutes_model": "E_inj" if src == SRC_OFFICIAL else "E"}


def run() -> dict[str, Any]:
    calib = PART.load_calibration()
    out: dict[str, Any] = {"schema": "nba_starter_onoff/1.0", "calibration": {"fit_rows": calib["n_rows"]}, "confirmed_starter_p": PART.CONFIRMED_STARTER_P, "scenarios": {}}
    for name, base in SCENARIOS.items():
        ent: dict[str, Any] = {}
        for p_h in (0.6, 0.9):
            off = decide(base, p_h, calib, legacy=False)
            on = decide(base + [STARTER], p_h, calib, legacy=False)
            on_legacy = decide(base + [STARTER], p_h, calib, legacy=True)
            off_legacy = decide(base, p_h, calib, legacy=True)
            ent[f"p_hurdle_{p_h}"] = {"OFF": off, "ON_fixed_rule": on, "OFF_legacy_rule": off_legacy, "ON_legacy_rule": on_legacy,
                                      "delta_p_play": round(on["p_play"] - off["p_play"], 4), "minutes_model_changes_fixed": on["minutes_model"] != off["minutes_model"],
                                      "minutes_model_changes_legacy": on_legacy["minutes_model"] != off_legacy["minutes_model"]}
        out["scenarios"][name] = ent
    flips = [n for n, e in out["scenarios"].items() if any(v["minutes_model_changes_legacy"] for v in e.values())]
    out["legacy_rule_flips_minutes_model_in"] = flips
    out["fixed_rule_flips_minutes_model_in"] = [n for n, e in out["scenarios"].items() if any(v["minutes_model_changes_fixed"] for v in e.values())]
    return out


if __name__ == "__main__":
    print(json.dumps(run(), indent=1))
